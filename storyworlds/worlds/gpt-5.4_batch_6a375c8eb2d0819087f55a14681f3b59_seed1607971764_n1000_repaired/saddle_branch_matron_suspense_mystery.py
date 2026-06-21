#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/saddle_branch_matron_suspense_mystery.py
===================================================================

A standalone storyworld for a small child-facing mystery with suspense:
a child discovers that a pony's saddle is missing from the tack room,
a branch scratches in the dark, and the stable matron helps solve the
mystery calmly.

The world model prefers a few plausible combinations over broad coverage.
A real culprit must be able to move the saddle, the clue must honestly fit
that culprit, and the method used to recover the saddle must match the animal.
The prose is driven by simulated state: worry rises when the saddle is gone,
suspense rises when the branch scrapes the window, clues shift the search,
and the ending image proves that the mystery has been understood.

Run it
------
    python storyworlds/worlds/gpt-5.4/saddle_branch_matron_suspense_mystery.py
    python storyworlds/worlds/gpt-5.4/saddle_branch_matron_suspense_mystery.py --culprit goat --clue hoofprints
    python storyworlds/worlds/gpt-5.4/saddle_branch_matron_suspense_mystery.py --all
    python storyworlds/worlds/gpt-5.4/saddle_branch_matron_suspense_mystery.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/saddle_branch_matron_suspense_mystery.py --verify
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "matron"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class Place:
    id: str
    label: str
    branch_kind: str
    hideouts: set[str]
    wind_levels: set[str]
    opening: str
    ending: str
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
class Culprit:
    id: str
    label: str
    kind: str
    clues: set[str]
    hideouts: set[str]
    lures: set[str]
    move_text: str
    reveal_text: str
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
    text: str
    qa: str
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
class Lure:
    id: str
    label: str
    text: str
    qa: str
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
class Hideout:
    id: str
    label: str
    text: str
    ending: str
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
class Wind:
    id: str
    label: str
    suspense: int
    scrape: str
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


def _r_missing_saddle(world: World) -> list[str]:
    child = world.get("child")
    room = world.get("room")
    saddle = world.get("saddle")
    if saddle.attrs.get("location") != "hook":
        sig = ("missing", saddle.attrs.get("location"))
        if sig not in world.fired:
            world.fired.add(sig)
            child.memes["worry"] += 1
            room.meters["mystery"] += 1
    return []


def _r_branch_scrape(world: World) -> list[str]:
    room = world.get("room")
    branch = world.get("branch")
    child = world.get("child")
    if branch.meters["scraping"] >= THRESHOLD:
        sig = ("branch_scrape", int(branch.meters["scraping"]))
        if sig not in world.fired:
            world.fired.add(sig)
            room.meters["suspense"] += branch.meters["scraping"]
            child.memes["fear"] += 1
    return []


def _r_clue_found(world: World) -> list[str]:
    child = world.get("child")
    room = world.get("room")
    if world.facts.get("clue_found"):
        sig = ("clue_found", world.facts.get("clue_id"))
        if sig not in world.fired:
            world.fired.add(sig)
            child.memes["curiosity"] += 1
            if room.meters["mystery"] >= THRESHOLD:
                room.meters["mystery"] -= 1
    return []


def _r_matron_steadies(world: World) -> list[str]:
    child = world.get("child")
    matron = world.get("matron")
    if matron.memes["steadying"] >= THRESHOLD and child.memes["fear"] >= THRESHOLD:
        sig = ("steady", int(child.memes["fear"]))
        if sig not in world.fired:
            world.fired.add(sig)
            child.memes["fear"] = max(0.0, child.memes["fear"] - 1)
            child.memes["trust"] += 1
    return []


CAUSAL_RULES: list[Rule] = [
    Rule(name="missing_saddle", tag="physical", apply=_r_missing_saddle),
    Rule(name="branch_scrape", tag="physical", apply=_r_branch_scrape),
    Rule(name="clue_found", tag="social", apply=_r_clue_found),
    Rule(name="matron_steadies", tag="social", apply=_r_matron_steadies),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            lines = rule.apply(world)
            if lines:
                changed = True
                produced.extend(lines)
    if narrate:
        for line in produced:
            world.say(line)
    return produced


PLACES = {
    "orchard_stable": Place(
        id="orchard_stable",
        label="the orchard stable",
        branch_kind="apple-tree branch",
        hideouts={"hay_corner", "wash_stall"},
        wind_levels={"breezy", "windy"},
        opening="lamplight made soft gold squares on the stable floor",
        ending="Outside, the orchard leaves finally stopped whispering.",
        tags={"stable", "orchard"},
    ),
    "school_stable": Place(
        id="school_stable",
        label="the riding-school stable",
        branch_kind="elm branch",
        hideouts={"hay_corner", "wash_stall", "feed_room"},
        wind_levels={"still", "breezy", "windy"},
        opening="the long aisle smelled of straw and soap",
        ending="The quiet stable sounded friendly again.",
        tags={"stable", "school"},
    ),
    "fair_stable": Place(
        id="fair_stable",
        label="the fairground stable",
        branch_kind="poplar branch",
        hideouts={"wash_stall", "feed_room"},
        wind_levels={"breezy", "windy"},
        opening="the lantern by the door swung in a small yellow circle",
        ending="Far away, the last fair music faded into the dark.",
        tags={"stable", "fair"},
    ),
}

CULPRITS = {
    "pony": Culprit(
        id="pony",
        label="the pony",
        kind="animal",
        clues={"hoofprints", "straw_trail"},
        hideouts={"hay_corner", "wash_stall"},
        lures={"apple", "quiet_voice"},
        move_text="had wriggled free, rubbed against the hook, and nudged the saddle away",
        reveal_text="The pony only wanted the softest place to stand and the kindest voice to follow.",
        tags={"pony", "animal"},
    ),
    "goat": Culprit(
        id="goat",
        label="the little goat",
        kind="animal",
        clues={"nibbled_strap", "straw_trail"},
        hideouts={"feed_room", "hay_corner"},
        lures={"grain", "quiet_voice"},
        move_text="had worried the leather with curious teeth and tugged the saddle along",
        reveal_text="The goat had not meant any harm; it simply followed the smell of grain and the fun of a dangling strap.",
        tags={"goat", "animal"},
    ),
}

CLUES = {
    "hoofprints": Clue(
        id="hoofprints",
        label="hoofprints",
        text="On the dusty floor, a neat line of small hoofprints pointed away from the empty hook.",
        qa="They found hoofprints on the dusty floor, and the prints pointed away from the hook where the saddle should have been.",
        tags={"hoofprints", "tracks"},
    ),
    "straw_trail": Clue(
        id="straw_trail",
        label="a straw trail",
        text="A crooked little trail of straw lay where something had been dragged through the aisle.",
        qa="They noticed a crooked trail of straw, which showed that something had been dragged instead of quietly carried away.",
        tags={"straw", "tracks"},
    ),
    "nibbled_strap": Clue(
        id="nibbled_strap",
        label="a nibbled strap",
        text="One loose saddle strap was damp and nibbled, with tiny tooth marks along the edge.",
        qa="They found a nibbled strap with little tooth marks, so they knew some small mouth had been chewing on the leather.",
        tags={"strap", "bite"},
    ),
}

LURES = {
    "apple": Lure(
        id="apple",
        label="an apple slice",
        text='The matron lifted an apple slice and said, "No thief would come for fruit, but a pony might."',
        qa="The matron used an apple slice, because a pony is likely to follow that smell and step out gently.",
        tags={"apple", "food"},
    ),
    "grain": Lure(
        id="grain",
        label="a scoop of grain",
        text='The matron rattled a scoop of grain and said, "Curious teeth often belong to a hungry goat."',
        qa="The matron shook a scoop of grain, because a goat would know that sound and come trotting for supper.",
        tags={"grain", "food"},
    ),
    "quiet_voice": Lure(
        id="quiet_voice",
        label="a quiet voice",
        text='The matron cupped her hands and called in a soft, sure voice that made the dark corners feel smaller.',
        qa="The matron used a quiet voice so the frightened animal would come out instead of shying deeper into the shadows.",
        tags={"voice", "calm"},
    ),
}

HIDEOUTS = {
    "hay_corner": Hideout(
        id="hay_corner",
        label="the hay corner",
        text="The hay corner made a lumpy golden cave behind stacked bales.",
        ending="There, half hidden in sweet-smelling hay, lay the saddle.",
        tags={"hay"},
    ),
    "wash_stall": Hideout(
        id="wash_stall",
        label="the wash stall",
        text="The wash stall gleamed with damp boards and smelled faintly of soap.",
        ending="There, propped against the rail as if waiting to be found, stood the saddle.",
        tags={"wash"},
    ),
    "feed_room": Hideout(
        id="feed_room",
        label="the feed room",
        text="The feed room was full of sacks, scoops, and shadows that looked bigger than they were.",
        ending="There, leaning against a grain bin, was the saddle at last.",
        tags={"feed"},
    ),
}

WINDS = {
    "still": Wind(
        id="still",
        label="still air",
        suspense=0,
        scrape="Outside, the branch only brushed the window once, like a finger testing the glass.",
        tags={"wind"},
    ),
    "breezy": Wind(
        id="breezy",
        label="a breezy night",
        suspense=1,
        scrape="A branch tapped and scraped across the window, making the dark outside sound busy and secretive.",
        tags={"wind"},
    ),
    "windy": Wind(
        id="windy",
        label="a windy night",
        suspense=2,
        scrape="The wind shoved a branch hard against the window again and again, and each scrape made the shadows jump.",
        tags={"wind"},
    ),
}

GIRL_NAMES = ["Mira", "Lila", "Nora", "Tess", "Ruby", "June", "Ada", "Elsie"]
BOY_NAMES = ["Owen", "Finn", "Leo", "Sam", "Ben", "Eli", "Theo", "Max"]
TRAITS = {
    "brave": 2,
    "careful": 1,
    "jumpy": 0,
    "curious": 1,
    "steady": 2,
}


def valid_combo(place_id: str, culprit_id: str, clue_id: str, lure_id: str, hideout_id: str, wind_id: str) -> bool:
    place = PLACES[place_id]
    culprit = CULPRITS[culprit_id]
    return (
        clue_id in culprit.clues
        and lure_id in culprit.lures
        and hideout_id in culprit.hideouts
        and hideout_id in place.hideouts
        and wind_id in place.wind_levels
    )


def valid_combos() -> list[tuple[str, str, str, str, str, str]]:
    combos: list[tuple[str, str, str, str, str, str]] = []
    for place_id in PLACES:
        for culprit_id in CULPRITS:
            for clue_id in CLUES:
                for lure_id in LURES:
                    for hideout_id in HIDEOUTS:
                        for wind_id in WINDS:
                            if valid_combo(place_id, culprit_id, clue_id, lure_id, hideout_id, wind_id):
                                combos.append((place_id, culprit_id, clue_id, lure_id, hideout_id, wind_id))
    return combos


def child_copes(trait: str, wind_id: str) -> bool:
    courage = TRAITS[trait]
    suspense = WINDS[wind_id].suspense
    return courage >= suspense


@dataclass
class StoryParams:
    place: str
    culprit: str
    clue: str
    lure: str
    hideout: str
    wind: str
    child_name: str
    child_gender: str
    pony_name: str
    matron_name: str = "Mrs. Vale"
    trait: str = "careful"
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


def introduction(world: World, child: Entity, matron: Entity, pony: Entity, place: Place) -> None:
    child.memes["joy"] += 1
    world.say(
        f"At dusk in {place.label}, {place.opening}. {child.id} had stayed behind to wipe down {pony.id}'s little saddle before morning riding time."
    )
    world.say(
        f"The stable matron, {matron.id}, moved from stall to stall with a ring of keys and the sort of calm that made every horse lower its head."
    )


def discover_missing(world: World, child: Entity, saddle: Entity) -> None:
    saddle.attrs["location"] = "missing"
    propagate(world, narrate=False)
    world.say(
        f"But when {child.id} reached for the saddle hook, {child.pronoun('possessive')} hand closed on empty air. The hook rocked once, and the saddle was gone."
    )


def branch_scrapes(world: World, child: Entity, branch: Entity, wind: Wind, place: Place) -> None:
    branch.attrs["kind"] = place.branch_kind
    branch.meters["scraping"] = float(wind.suspense)
    propagate(world, narrate=False)
    world.say(
        f"{wind.scrape} It was only a {place.branch_kind}, but in that moment it sounded almost like someone hiding and listening."
    )
    if child.memes["fear"] >= THRESHOLD:
        world.say(f"{child.id} took one step backward and hugged {child.pronoun('possessive')} elbows tight.")


def ask_matron(world: World, child: Entity, matron: Entity) -> None:
    world.say(
        f'"Mrs. Vale," {child.id} whispered, "what if someone took it?"'
    )
    world.say(
        f'{matron.id} set down her lantern. "Mysteries feel bigger in the dark," {matron.pronoun()} said. "So we will make the dark smaller, one true thing at a time."'
    )


def steady_child(world: World, child: Entity, matron: Entity, trait: str, wind_id: str) -> None:
    if child_copes(trait, wind_id):
        child.memes["bravery"] += 1
        child.memes["trust"] += 1
        world.say(
            f"{child.id} nodded and stayed close to the lantern light, listening instead of running."
        )
    else:
        child.memes["fear"] += 1
        matron.memes["steadying"] += 1
        propagate(world, narrate=False)
        world.say(
            f"For one quick second, {child.id} wanted to bolt for the door. Then the matron's warm hand rested on {child.pronoun('possessive')} shoulder, and the scary feeling loosened a little."
        )


def find_clue(world: World, clue: Clue) -> None:
    world.facts["clue_found"] = True
    world.facts["clue_id"] = clue.id
    propagate(world, narrate=False)
    world.say(clue.text)


def reason_from_clue(world: World, matron: Entity, culprit: Culprit, hideout: Hideout) -> None:
    if culprit.id == "pony":
        line = f'"That is no stranger\'s trick," said {matron.id}. "Those signs belong to a restless pony, and restless ponies go where they feel safe."'
    else:
        line = f'"That is no stranger\'s trick," said {matron.id}. "Those signs belong to a nosy little goat, and nosy goats wander where the feed smells strongest."'
    world.say(line)
    world.say(f"Together they turned toward {hideout.label}.")


def use_lure(world: World, matron: Entity, lure: Lure) -> None:
    world.say(lure.text)
    world.facts["used_lure"] = lure.id


def reveal(world: World, child: Entity, matron: Entity, pony: Entity, saddle: Entity,
           culprit: Culprit, hideout: Hideout) -> None:
    saddle.attrs["location"] = hideout.id
    world.say(hideout.text)
    world.say(hideout.ending)
    world.say(
        f"Beside it was {culprit.label}, looking surprised to be the center of such a grand mystery. {culprit.reveal_text}"
    )
    saddle.attrs["location"] = "hook"
    child.memes["relief"] += 1
    child.memes["wonder"] += 1
    matron.memes["care"] += 1
    world.say(
        f'{matron.id} lifted the saddle back onto its hook and checked every strap. Then {pony.id} blew a warm breath into {child.id}\'s sleeve, as if asking whether the case was closed.'
    )


def ending(world: World, child: Entity, matron: Entity, place: Place, trait: str, wind_id: str) -> None:
    if child_copes(trait, wind_id):
        world.say(
            f'"I thought the branch was warning us," {child.id} admitted. "{matron.id}," said the matron, smiling, "sometimes a mystery begins with a sound and ends with a better question."'
        )
    else:
        world.say(
            f'"I thought the branch meant something terrible," {child.id} admitted. "It meant the wind was noisy," said {matron.id}, "and that is why we look before we fear."'
        )
    world.say(
        f"Soon the lantern shone on polished leather, quiet stalls, and one ordinary hook holding the saddle exactly where it belonged. {place.ending}"
    )


def tell(place: Place, culprit: Culprit, clue: Clue, lure: Lure, hideout: Hideout,
         wind: Wind, child_name: str, child_gender: str, pony_name: str,
         matron_name: str, trait: str) -> World:
    world = World()
    child = world.add(Entity(
        id=child_name,
        kind="character",
        type=child_gender,
        label=child_name,
        role="child",
        traits=[trait],
    ))
    matron = world.add(Entity(
        id=matron_name,
        kind="character",
        type="matron",
        label="the matron",
        role="matron",
        traits=["calm", "watchful"],
    ))
    pony = world.add(Entity(
        id=pony_name,
        kind="thing",
        type="pony",
        label=pony_name,
        role="pony",
        tags={"pony"},
    ))
    saddle = world.add(Entity(
        id="saddle",
        kind="thing",
        type="saddle",
        label="the saddle",
        role="saddle",
        attrs={"location": "hook"},
        tags={"saddle"},
    ))
    branch = world.add(Entity(
        id="branch",
        kind="thing",
        type="branch",
        label="the branch",
        role="branch",
        attrs={"kind": place.branch_kind},
        tags={"branch"},
    ))
    room = world.add(Entity(
        id="room",
        kind="thing",
        type="stable",
        label=place.label,
        role="room",
    ))

    world.facts.update(
        place=place,
        culprit=culprit,
        clue=clue,
        lure=lure,
        hideout=hideout,
        wind=wind,
        child=child,
        matron=matron,
        pony=pony,
        saddle=saddle,
        clue_found=False,
        clue_id="",
        used_lure="",
        outcome="steady" if child_copes(trait, wind.id) else "shaky",
    )

    introduction(world, child, matron, pony, place)
    world.para()
    discover_missing(world, child, saddle)
    branch_scrapes(world, child, branch, wind, place)
    ask_matron(world, child, matron)

    world.para()
    steady_child(world, child, matron, trait, wind.id)
    find_clue(world, clue)
    reason_from_clue(world, matron, culprit, hideout)

    world.para()
    use_lure(world, matron, lure)
    reveal(world, child, matron, pony, saddle, culprit, hideout)
    ending(world, child, matron, place, trait, wind.id)

    world.facts.update(
        mystery_started=room.meters["mystery"] >= THRESHOLD,
        suspense_level=room.meters["suspense"],
        relieved=child.memes["relief"] >= THRESHOLD,
    )
    return world


KNOWLEDGE = {
    "saddle": [
        ("What is a saddle?",
         "A saddle is the seat that goes on a horse or pony's back so a rider can sit safely. It has straps to hold it in place.")
    ],
    "branch": [
        ("Why can a branch sound spooky at night?",
         "A branch can tap or scrape on a window when the wind moves it. In the dark, a simple sound can seem much bigger than it really is.")
    ],
    "matron": [
        ("What is a matron?",
         "A matron is a grown-up woman who looks after a place and the people or animals in it. She keeps things orderly and helps when something is wrong.")
    ],
    "hoofprints": [
        ("What can hoofprints tell you?",
         "Hoofprints can show where a horse or pony walked. They help you follow a path without seeing the animal move.")
    ],
    "goat": [
        ("Why do goats nibble things?",
         "Goats explore with their mouths and often nibble things out of curiosity. That is why straps, paper, and cloth should be kept away from them.")
    ],
    "pony": [
        ("Why might a pony move toward a quiet place?",
         "A pony may walk toward a calm, familiar corner when it feels restless or uncertain. Animals often choose places that feel safe to them.")
    ],
    "calm": [
        ("Why does staying calm help solve a mystery?",
         "Staying calm helps you notice true clues instead of guessing wildly. When you slow down, small details start to make sense.")
    ],
}
KNOWLEDGE_ORDER = ["saddle", "branch", "matron", "hoofprints", "pony", "goat", "calm"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    place = f["place"]
    culprit = f["culprit"]
    return [
        f'Write a short mystery for a 3-to-5-year-old set in {place.label} that includes the words "saddle", "branch", and "matron".',
        f"Tell a gentle suspense story where {child.id} finds a saddle missing in the dark, hears a branch at the window, and the matron solves the mystery calmly.",
        f"Write a child-friendly stable mystery in which a missing saddle seems frightening at first, but the clue leads to {culprit.label} and a safe explanation.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    matron = f["matron"]
    culprit = f["culprit"]
    clue = f["clue"]
    lure = f["lure"]
    hideout = f["hideout"]
    place = f["place"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, a child in {place.label}, and {matron.id}, the stable matron who helps solve the mystery. The missing thing was the pony's saddle."
        ),
        (
            "What made the story feel suspenseful?",
            f"The saddle was suddenly gone, and a branch kept scraping at the window in the dark. Those two things made {child.id} imagine something hidden before any clue had been found."
        ),
        (
            "What clue did they find?",
            f"{clue.qa} That true clue helped the matron stop guessing and choose where to look next."
        ),
        (
            "How did the matron solve the mystery?",
            f"{matron.id} stayed calm, followed the clue, and used {lure.label}. {lure.qa}"
        ),
        (
            "Where was the saddle, and why was it there?",
            f"They found the saddle in {hideout.label}. It was there because {culprit.label} {culprit.move_text}."
        ),
    ]
    if f["outcome"] == "shaky":
        qa.append(
            (
                f"How did {child.id} change by the end?",
                f"At first {child.id} almost ran because the dark noise felt terrible. By the end, {child.pronoun()} had seen that the branch and the missing saddle had an ordinary explanation, so {child.pronoun()} felt relieved and steadier."
            )
        )
    else:
        qa.append(
            (
                f"How did {child.id} help solve the mystery?",
                f"{child.id} stayed beside the lantern and kept looking instead of panicking. That calm helped {child.pronoun('object')} notice the clue and trust the matron's careful reasoning."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"saddle", "branch", "matron", "calm"}
    clue = world.facts["clue"]
    culprit = world.facts["culprit"]
    if clue.id == "hoofprints":
        tags.add("hoofprints")
    if culprit.id == "pony":
        tags.add("pony")
    if culprit.id == "goat":
        tags.add("goat")
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
        if ent.traits:
            bits.append(f"traits={ent.traits}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v or v == 0}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:12} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


def explain_rejection(place_id: str, culprit_id: str, clue_id: str, lure_id: str, hideout_id: str, wind_id: str) -> str:
    problems: list[str] = []
    if culprit_id in CULPRITS:
        culprit = CULPRITS[culprit_id]
        if clue_id in CLUES and clue_id not in culprit.clues:
            problems.append(f"{CLUES[clue_id].label} does not honestly fit {culprit.label}")
        if lure_id in LURES and lure_id not in culprit.lures:
            problems.append(f"{LURES[lure_id].label} is not a sensible way to coax {culprit.label}")
        if hideout_id in HIDEOUTS and hideout_id not in culprit.hideouts:
            problems.append(f"{culprit.label} would not likely leave the saddle in {HIDEOUTS[hideout_id].label}")
    if place_id in PLACES:
        place = PLACES[place_id]
        if hideout_id in HIDEOUTS and hideout_id not in place.hideouts:
            problems.append(f"{place.label} does not have {HIDEOUTS[hideout_id].label}")
        if wind_id in WINDS and wind_id not in place.wind_levels:
            problems.append(f"{place.label} does not suit the wind setting '{wind_id}'")
    if not problems:
        return "(No valid mystery matches the given options.)"
    return "(No story: " + "; ".join(problems) + ".)"


ASP_RULES = r"""
compatible_clue(Culprit, Clue) :- culprit(Culprit), clue(Clue), culprit_clue(Culprit, Clue).
compatible_lure(Culprit, Lure) :- culprit(Culprit), lure(Lure), culprit_lure(Culprit, Lure).
compatible_hideout(Culprit, Hideout) :- culprit(Culprit), hideout(Hideout), culprit_hideout(Culprit, Hideout).
place_has_hideout(Place, Hideout) :- place(Place), hideout(Hideout), place_hideout(Place, Hideout).
place_has_wind(Place, Wind) :- place(Place), wind(Wind), place_wind(Place, Wind).

valid(Place, Culprit, Clue, Lure, Hideout, Wind) :-
    place(Place), culprit(Culprit), clue(Clue), lure(Lure), hideout(Hideout), wind(Wind),
    compatible_clue(Culprit, Clue),
    compatible_lure(Culprit, Lure),
    compatible_hideout(Culprit, Hideout),
    place_has_hideout(Place, Hideout),
    place_has_wind(Place, Wind).

copes :- chosen_trait(T), courage(T, C), chosen_wind(W), suspense(W, S), C >= S.
outcome(steady) :- copes.
outcome(shaky) :- not copes.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        for hideout_id in sorted(place.hideouts):
            lines.append(asp.fact("place_hideout", place_id, hideout_id))
        for wind_id in sorted(place.wind_levels):
            lines.append(asp.fact("place_wind", place_id, wind_id))
    for culprit_id, culprit in CULPRITS.items():
        lines.append(asp.fact("culprit", culprit_id))
        for clue_id in sorted(culprit.clues):
            lines.append(asp.fact("culprit_clue", culprit_id, clue_id))
        for lure_id in sorted(culprit.lures):
            lines.append(asp.fact("culprit_lure", culprit_id, lure_id))
        for hideout_id in sorted(culprit.hideouts):
            lines.append(asp.fact("culprit_hideout", culprit_id, hideout_id))
    for clue_id in CLUES:
        lines.append(asp.fact("clue", clue_id))
    for lure_id in LURES:
        lines.append(asp.fact("lure", lure_id))
    for hideout_id in HIDEOUTS:
        lines.append(asp.fact("hideout", hideout_id))
    for wind_id, wind in WINDS.items():
        lines.append(asp.fact("wind", wind_id))
        lines.append(asp.fact("suspense", wind_id, wind.suspense))
    for trait_id, score in TRAITS.items():
        lines.append(asp.fact("trait", trait_id))
        lines.append(asp.fact("courage", trait_id, score))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/6."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join([
        asp.fact("chosen_trait", params.trait),
        asp.fact("chosen_wind", params.wind),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def outcome_of(params: StoryParams) -> str:
    return "steady" if child_copes(params.trait, params.wind) else "shaky"


CURATED = [
    StoryParams(
        place="orchard_stable",
        culprit="pony",
        clue="hoofprints",
        lure="apple",
        hideout="wash_stall",
        wind="windy",
        child_name="Mira",
        child_gender="girl",
        pony_name="Bramble",
        matron_name="Mrs. Vale",
        trait="careful",
    ),
    StoryParams(
        place="school_stable",
        culprit="pony",
        clue="straw_trail",
        lure="quiet_voice",
        hideout="hay_corner",
        wind="breezy",
        child_name="Finn",
        child_gender="boy",
        pony_name="Pip",
        matron_name="Mrs. Vale",
        trait="steady",
    ),
    StoryParams(
        place="school_stable",
        culprit="goat",
        clue="nibbled_strap",
        lure="grain",
        hideout="feed_room",
        wind="still",
        child_name="Ruby",
        child_gender="girl",
        pony_name="Clover",
        matron_name="Mrs. Vale",
        trait="jumpy",
    ),
    StoryParams(
        place="fair_stable",
        culprit="goat",
        clue="straw_trail",
        lure="quiet_voice",
        hideout="feed_room",
        wind="windy",
        child_name="Leo",
        child_gender="boy",
        pony_name="Daisy",
        matron_name="Mrs. Vale",
        trait="brave",
    ),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a missing saddle, a scraping branch, and a matron-led mystery."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--culprit", choices=CULPRITS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--lure", choices=LURES)
    ap.add_argument("--hideout", choices=HIDEOUTS)
    ap.add_argument("--wind", choices=WINDS)
    ap.add_argument("--trait", choices=sorted(TRAITS))
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--pony")
    ap.add_argument("--matron", default="Mrs. Vale")
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if all(getattr(args, key) is not None for key in ("place", "culprit", "clue", "lure", "hideout", "wind")):
        if not valid_combo(args.place, args.culprit, args.clue, args.lure, args.hideout, args.wind):
            raise StoryError(explain_rejection(args.place, args.culprit, args.clue, args.lure, args.hideout, args.wind))

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.culprit is None or combo[1] == args.culprit)
        and (args.clue is None or combo[2] == args.clue)
        and (args.lure is None or combo[3] == args.lure)
        and (args.hideout is None or combo[4] == args.hideout)
        and (args.wind is None or combo[5] == args.wind)
    ]
    if not combos:
        place_id = args.place or next(iter(PLACES))
        culprit_id = args.culprit or next(iter(CULPRITS))
        clue_id = args.clue or next(iter(CLUES))
        lure_id = args.lure or next(iter(LURES))
        hideout_id = args.hideout or next(iter(HIDEOUTS))
        wind_id = args.wind or next(iter(WINDS))
        raise StoryError(explain_rejection(place_id, culprit_id, clue_id, lure_id, hideout_id, wind_id))

    place_id, culprit_id, clue_id, lure_id, hideout_id, wind_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    pony_name = args.pony or rng.choice(["Bramble", "Pip", "Daisy", "Maple", "Star", "Moss"])
    trait = args.trait or rng.choice(sorted(TRAITS))
    return StoryParams(
        place=place_id,
        culprit=culprit_id,
        clue=clue_id,
        lure=lure_id,
        hideout=hideout_id,
        wind=wind_id,
        child_name=name,
        child_gender=gender,
        pony_name=pony_name,
        matron_name=args.matron,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.culprit not in CULPRITS:
        raise StoryError(f"(Unknown culprit: {params.culprit})")
    if params.clue not in CLUES:
        raise StoryError(f"(Unknown clue: {params.clue})")
    if params.lure not in LURES:
        raise StoryError(f"(Unknown lure: {params.lure})")
    if params.hideout not in HIDEOUTS:
        raise StoryError(f"(Unknown hideout: {params.hideout})")
    if params.wind not in WINDS:
        raise StoryError(f"(Unknown wind: {params.wind})")
    if params.trait not in TRAITS:
        raise StoryError(f"(Unknown trait: {params.trait})")
    if not valid_combo(params.place, params.culprit, params.clue, params.lure, params.hideout, params.wind):
        raise StoryError(explain_rejection(params.place, params.culprit, params.clue, params.lure, params.hideout, params.wind))

    world = tell(
        place=PLACES[params.place],
        culprit=CULPRITS[params.culprit],
        clue=CLUES[params.clue],
        lure=LURES[params.lure],
        hideout=HIDEOUTS[params.hideout],
        wind=WINDS[params.wind],
        child_name=params.child_name,
        child_gender=params.child_gender,
        pony_name=params.pony_name,
        matron_name=params.matron_name,
        trait=params.trait,
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

    py_valid = set(valid_combos())
    asp_valid = set(asp_valid_combos())
    if py_valid == asp_valid:
        print(f"OK: valid_combos matches ASP ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid_combos:")
        if py_valid - asp_valid:
            print("  only in python:", sorted(py_valid - asp_valid))
        if asp_valid - py_valid:
            print("  only in asp:", sorted(asp_valid - py_valid))

    cases = list(CURATED)
    parser = build_parser()
    for s in range(30):
        try:
            p = resolve_params(parser.parse_args([]), random.Random(s))
            p.seed = s
            cases.append(p)
        except StoryError:
            rc = 1
            print(f"Unexpected resolve_params failure at seed {s}.")
            break

    bad = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcome differences.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("empty story")
        print("OK: smoke generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/6.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible mysteries:\n")
        for place_id, culprit_id, clue_id, lure_id, hideout_id, wind_id in combos:
            print(
                f"  {place_id:14} {culprit_id:5} {clue_id:13} {lure_id:11} {hideout_id:10} {wind_id}"
            )
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = (
                f"### {p.child_name}: {p.culprit} in {p.place} "
                f"({p.clue}, {p.lure}, {outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
