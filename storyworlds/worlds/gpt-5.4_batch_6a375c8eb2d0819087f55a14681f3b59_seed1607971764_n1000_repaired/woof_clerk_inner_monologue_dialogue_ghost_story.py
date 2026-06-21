#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/woof_clerk_inner_monologue_dialogue_ghost_story.py
=============================================================================

A standalone storyworld for a child-safe ghost story: a child and a little dog
spend an evening in an old public place, something cold and ghostly stirs, the
dog gives a sharp woof, and a kind clerk helps uncover the missing object that
the ghost has been searching for.

The domain is built around a small stateful model:

- typed entities with physical meters and emotional memes
- a reasonableness gate over which ghost belongs in which venue, which missing
  object the ghost wants, where that object could plausibly be hidden, and which
  clerk action can sensibly reach it
- a tiny causal system:
    unrest in the ghost -> cold room + strange sound + fear/alert
    alert dog + strange sound -> a woof
    found object returned -> ghost settles, room calms, everyone feels relief
- prose that follows the changing world, with dialogue and inner monologue

Run it
------
    python storyworlds/worlds/gpt-5.4/woof_clerk_inner_monologue_dialogue_ghost_story.py
    python storyworlds/worlds/gpt-5.4/woof_clerk_inner_monologue_dialogue_ghost_story.py --venue inn --ghost bellhop
    python storyworlds/worlds/gpt-5.4/woof_clerk_inner_monologue_dialogue_ghost_story.py --action shake_furniture
    python storyworlds/worlds/gpt-5.4/woof_clerk_inner_monologue_dialogue_ghost_story.py --all
    python storyworlds/worlds/gpt-5.4/woof_clerk_inner_monologue_dialogue_ghost_story.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/woof_clerk_inner_monologue_dialogue_ghost_story.py --verify
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
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman"}
        male = {"boy", "man"}
        neutral_it = {"dog", "ghost", "thing", "item", "room"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in neutral_it:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
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

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Venue:
    id: str
    label: str
    opening: str
    counter: str
    hush: str
    affords: set[str] = field(default_factory=set)
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
class GhostRole:
    id: str
    label: str
    venue: str
    anchor: str
    opening: str
    whisper: str
    farewell: str
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
class Anchor:
    id: str
    label: str
    phrase: str
    shine: str
    fits: set[str] = field(default_factory=set)
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
class Spot:
    id: str
    label: str
    phrase: str
    reveal: str
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
class Action:
    id: str
    label: str
    sense: int
    reaches: set[str] = field(default_factory=set)
    lead: str = ""
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


@dataclass
class StoryParams:
    venue: str
    ghost: str
    anchor: str
    spot: str
    action: str
    child_name: str
    child_gender: str
    dog_name: str
    clerk_name: str
    trait: str
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


def _r_haunt(world: World) -> list[str]:
    ghost = world.get("ghost")
    room = world.get("room")
    child = world.get("child")
    dog = world.get("dog")
    if ghost.meters["unrest"] < THRESHOLD:
        return []
    sig = ("haunt",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    room.meters["cold"] += 1
    room.meters["sound"] += 1
    child.memes["fear"] += 1
    dog.memes["alert"] += 1
    return ["__haunt__"]


def _r_woof(world: World) -> list[str]:
    dog = world.get("dog")
    room = world.get("room")
    if dog.memes["alert"] < THRESHOLD or room.meters["sound"] < THRESHOLD:
        return []
    sig = ("woof",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    dog.meters["woof"] += 1
    return ["__woof__"]


def _r_peace(world: World) -> list[str]:
    ghost = world.get("ghost")
    room = world.get("room")
    child = world.get("child")
    clerk = world.get("clerk")
    dog = world.get("dog")
    if ghost.meters["unrest"] >= THRESHOLD:
        return []
    if ghost.meters["seen"] < THRESHOLD or world.facts.get("returned") is not True:
        return []
    sig = ("peace",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    room.meters["cold"] = 0.0
    room.meters["sound"] = 0.0
    room.meters["calm"] += 1
    child.memes["relief"] += 1
    child.memes["wonder"] += 1
    clerk.memes["relief"] += 1
    clerk.memes["belief"] += 1
    dog.memes["calm"] += 1
    return ["__peace__"]


CAUSAL_RULES: list[Rule] = [
    Rule(name="haunt", tag="physical", apply=_r_haunt),
    Rule(name="woof", tag="physical", apply=_r_woof),
    Rule(name="peace", tag="emotional", apply=_r_peace),
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


VENUES = {
    "inn": Venue(
        id="inn",
        label="the Moonlit Inn",
        opening="an old inn where the lamps always seemed dimmer after sunset",
        counter="the front desk",
        hush="the hallway smelled of polish and rain, and the shadows looked longer than they should",
        affords={"desk_drawer", "mail_cubby"},
        tags={"inn", "clerk", "desk"},
    ),
    "station": Venue(
        id="station",
        label="the Willow Street Station",
        opening="a small station where the last train had already gone",
        counter="the ticket counter",
        hush="the waiting room clock ticked so loudly that every pause felt important",
        affords={"mail_cubby", "high_locker"},
        tags={"station", "clerk", "counter"},
    ),
    "bookshop": Venue(
        id="bookshop",
        label="the Lantern Bookshop",
        opening="a narrow old bookshop with creaky floorboards and sleepy lamps",
        counter="the little counter",
        hush="the air smelled like paper and dust, and every shelf made its own tiny shadow",
        affords={"desk_drawer", "ledger_shelf"},
        tags={"bookshop", "clerk", "shelf"},
    ),
}

GHOSTS = {
    "bellhop": GhostRole(
        id="bellhop",
        label="bellhop ghost",
        venue="inn",
        anchor="brass_key",
        opening="Once, long ago, a bellhop had worked there and hurried through the halls with soft shoes and bright buttons.",
        whisper='"My key... I cannot finish my rounds without my key," the pale figure whispered.',
        farewell='"Thank you for hearing me," the ghost said, and the words sounded lighter than the cold air had been.',
        tags={"ghost", "key"},
    ),
    "porter": GhostRole(
        id="porter",
        label="porter ghost",
        venue="station",
        anchor="silver_whistle",
        opening="The old station had once been watched over by a porter who knew every suitcase and every sleepy traveler.",
        whisper='"My whistle... I have been searching for it through every quiet night," the ghost murmured.',
        farewell='"Now the platform can rest," the ghost said, with a gentle nod.',
        tags={"ghost", "whistle"},
    ),
    "page": GhostRole(
        id="page",
        label="page ghost",
        venue="bookshop",
        anchor="blue_card",
        opening="Years before, a young page had shelved books there and tucked notes into ledgers for the clerk to find in the morning.",
        whisper='"My card... my little blue card is missing, and I have looked for it in every rustle," the ghost breathed.',
        farewell='"The books may sleep now," the ghost said, smiling like a lantern behind fog.',
        tags={"ghost", "card"},
    ),
}

ANCHORS = {
    "brass_key": Anchor(
        id="brass_key",
        label="brass key",
        phrase="a small brass key",
        shine="it flashed like a tiny drop of moonlight",
        fits={"desk_drawer", "mail_cubby"},
        tags={"key", "metal"},
    ),
    "silver_whistle": Anchor(
        id="silver_whistle",
        label="silver whistle",
        phrase="a silver whistle on a faded cord",
        shine="it gleamed cold and bright in the clerk's hand",
        fits={"mail_cubby", "high_locker"},
        tags={"whistle", "metal"},
    ),
    "blue_card": Anchor(
        id="blue_card",
        label="blue library card",
        phrase="a blue library card with curled corners",
        shine="its worn edge caught the lamplight",
        fits={"desk_drawer", "ledger_shelf"},
        tags={"card", "paper"},
    ),
}

SPOTS = {
    "desk_drawer": Spot(
        id="desk_drawer",
        label="desk drawer",
        phrase="the narrow drawer built into the old desk",
        reveal="behind a tangle of string and chalk",
        tags={"drawer"},
    ),
    "mail_cubby": Spot(
        id="mail_cubby",
        label="mail cubby",
        phrase="one of the wooden cubbies behind the counter",
        reveal="under a stack of yellowed envelopes",
        tags={"cubby"},
    ),
    "high_locker": Spot(
        id="high_locker",
        label="high locker",
        phrase="the high locker over the counter",
        reveal="beside a forgotten timetable",
        tags={"locker"},
    ),
    "ledger_shelf": Spot(
        id="ledger_shelf",
        label="ledger shelf",
        phrase="the highest ledger shelf",
        reveal="between two thick cracked ledgers",
        tags={"shelf"},
    ),
}

ACTIONS = {
    "ring_keys": Action(
        id="ring_keys",
        label="tried the little ring of desk keys",
        sense=3,
        reaches={"desk_drawer"},
        lead="The clerk took down a ring of little keys that jingled like careful bells.",
        text="tried the little ring of desk keys until the old drawer gave a soft click",
        qa_text="used the little ring of keys to open the drawer",
        tags={"keys", "drawer"},
    ),
    "slide_cubby": Action(
        id="slide_cubby",
        label="slid open the cubby door",
        sense=3,
        reaches={"mail_cubby"},
        lead="The clerk leaned over the counter and found the loose wooden cubby door.",
        text="slid the cubby door open with a patient hand",
        qa_text="slid open the cubby door",
        tags={"cubby"},
    ),
    "fetch_stool": Action(
        id="fetch_stool",
        label="fetched the step stool",
        sense=3,
        reaches={"high_locker", "ledger_shelf"},
        lead="The clerk fetched the step stool from the corner and set it down carefully.",
        text="climbed the step stool and reached into the high place without knocking anything over",
        qa_text="used a step stool to reach the high place",
        tags={"stool", "high"},
    ),
    "shake_furniture": Action(
        id="shake_furniture",
        label="shook the furniture",
        sense=1,
        reaches={"desk_drawer", "high_locker"},
        lead="The idea was to shake something until it rattled loose.",
        text="shook the old furniture and listened for a clatter",
        qa_text="shook the furniture",
        tags={"bad_idea"},
    ),
}

GIRL_NAMES = ["Mina", "Lucy", "Nora", "Eva", "Iris", "June"]
BOY_NAMES = ["Owen", "Max", "Theo", "Eli", "Leo", "Sam"]
DOG_NAMES = ["Pebble", "Moss", "Pip", "Button", "Dottie", "Socks"]
CLERK_NAMES = ["Mr. Vale", "Ms. Wren", "Mr. North", "Ms. Bell", "Mr. Reed"]
TRAITS = ["brave", "curious", "careful", "quiethearted", "thoughtful"]


def ghost_belongs(ghost_id: str, venue_id: str) -> bool:
    return GHOSTS[ghost_id].venue == venue_id


def anchor_matches(ghost_id: str, anchor_id: str) -> bool:
    return GHOSTS[ghost_id].anchor == anchor_id


def anchor_fits(anchor_id: str, spot_id: str) -> bool:
    return spot_id in ANCHORS[anchor_id].fits


def venue_supports(venue_id: str, spot_id: str) -> bool:
    return spot_id in VENUES[venue_id].affords


def action_reaches(action_id: str, spot_id: str) -> bool:
    return spot_id in ACTIONS[action_id].reaches


def sensible_actions() -> list[Action]:
    return [a for a in ACTIONS.values() if a.sense >= SENSE_MIN]


def valid_combo(venue_id: str, ghost_id: str, anchor_id: str, spot_id: str, action_id: str) -> bool:
    return (
        ghost_belongs(ghost_id, venue_id)
        and anchor_matches(ghost_id, anchor_id)
        and venue_supports(venue_id, spot_id)
        and anchor_fits(anchor_id, spot_id)
        and action_reaches(action_id, spot_id)
        and ACTIONS[action_id].sense >= SENSE_MIN
    )


def valid_combos() -> list[tuple[str, str, str, str, str]]:
    combos: list[tuple[str, str, str, str, str]] = []
    for venue_id in VENUES:
        for ghost_id in GHOSTS:
            for anchor_id in ANCHORS:
                for spot_id in SPOTS:
                    for action_id in ACTIONS:
                        if valid_combo(venue_id, ghost_id, anchor_id, spot_id, action_id):
                            combos.append((venue_id, ghost_id, anchor_id, spot_id, action_id))
    return combos


def explain_rejection(venue_id: str, ghost_id: str, anchor_id: str, spot_id: str, action_id: str) -> str:
    if not ghost_belongs(ghost_id, venue_id):
        return (
            f"(No story: a {GHOSTS[ghost_id].label} does not belong in {VENUES[venue_id].label}. "
            f"Pick the venue that ghost haunts.)"
        )
    if not anchor_matches(ghost_id, anchor_id):
        return (
            f"(No story: the {GHOSTS[ghost_id].label} is searching for {ANCHORS[GHOSTS[ghost_id].anchor].phrase}, "
            f"not {ANCHORS[anchor_id].phrase}.)"
        )
    if not venue_supports(venue_id, spot_id):
        return (
            f"(No story: {VENUES[venue_id].label} has no plausible {SPOTS[spot_id].label} for this mystery.)"
        )
    if not anchor_fits(anchor_id, spot_id):
        return (
            f"(No story: {ANCHORS[anchor_id].phrase} would not plausibly be hidden in {SPOTS[spot_id].phrase}.)"
        )
    if ACTIONS[action_id].sense < SENSE_MIN:
        return (
            f"(Refusing action '{action_id}': it scores too low on common sense "
            f"(sense={ACTIONS[action_id].sense} < {SENSE_MIN}). Try a calmer, more careful clerk action.)"
        )
    if not action_reaches(action_id, spot_id):
        return (
            f"(No story: {ACTIONS[action_id].label} cannot sensibly reach {SPOTS[spot_id].phrase}.)"
        )
    return "(No story: this combination is not reasonable.)"


def predict_haunting(world: World) -> dict:
    sim = world.copy()
    sim.get("ghost").meters["unrest"] += 1
    propagate(sim, narrate=False)
    return {
        "cold": sim.get("room").meters["cold"] >= THRESHOLD,
        "woof": sim.get("dog").meters["woof"] >= THRESHOLD,
        "fear": sim.get("child").memes["fear"],
    }


def inner_line(name: str, text: str) -> str:
    return f'{name} thought, "{text}"'


def introduce(world: World, venue: Venue, child: Entity, dog: Entity, clerk: Entity, ghost: GhostRole) -> None:
    child.memes["curiosity"] += 1
    world.say(
        f"One evening, {child.id} and the little dog {dog.id} stepped into {venue.label}, "
        f"{venue.opening}. Behind {venue.counter}, the clerk {clerk.id} looked up and smiled."
    )
    world.say(
        f"{venue.hush}. {dog.id} padded close to {child.id}'s shoes, nose twitching."
    )
    world.say(ghost.opening)


def settle_in(world: World, child: Entity, clerk: Entity, venue: Venue) -> None:
    world.say(
        f'"You may wait here while the rain passes," {clerk.id} said. "{venue.label.split()[-1]} is quiet at this hour."'
    )
    world.say(
        inner_line(child.id, "Quiet is nice, but this place feels as if it is listening back.")
    )


def stirring(world: World, child: Entity, dog: Entity, clerk: Entity, ghost_cfg: GhostRole) -> None:
    ghost = world.get("ghost")
    ghost.meters["unrest"] += 1
    propagate(world, narrate=False)
    room = world.get("room")
    child.memes["courage"] += 1 if "brave" in child.traits else 0.0
    if room.meters["cold"] >= THRESHOLD:
        world.say(
            "Then the lamp flame thinned, and a cold breath slid through the room as if a window had opened by itself."
        )
    if room.meters["sound"] >= THRESHOLD:
        world.say(
            f"Something gave a tiny rattle behind {clerk.attrs['counter_noun']}, though nobody had touched it."
        )
    if dog.meters["woof"] >= THRESHOLD:
        world.say(f'{dog.id} stiffened and gave one clear woof into the hush.')
    world.say(
        inner_line(child.id, "That woof was not for nothing. Pebbles do not bark at empty air." if dog.id == "Pebble" else "That woof was not for nothing. The dog hears something I cannot.")
    )
    world.say(
        f'"Did you hear that?" {child.id} whispered.'
    )
    world.say(
        f'"I did," {clerk.id} said, and for the first time the clerk\'s voice was not cheerful. "That sound comes on certain nights."'
    )
    world.say(
        f"A pale shape gathered near the far wall, thin as mist and clear enough now to show a face."
    )
    world.get("ghost").meters["seen"] += 1
    world.say(ghost_cfg.whisper)


def consult(world: World, child: Entity, clerk: Entity, dog: Entity, anchor: Anchor, spot: Spot, action: Action) -> None:
    pred = predict_haunting(world)
    world.facts["predicted_cold"] = pred["cold"]
    world.facts["predicted_woof"] = pred["woof"]
    world.facts["predicted_fear"] = pred["fear"]
    child.memes["fear"] += 1
    world.say(
        inner_line(child.id, f"If we can find {anchor.phrase}, maybe the cold will stop.")
    )
    world.say(
        f'"A missing thing is keeping the ghost here," {child.id} said softly. '
        f'"Could it be in {spot.phrase}?"'
    )
    world.say(
        f'{clerk.id} glanced toward {spot.phrase}. "{action.lead} If anything is hidden there, we\'ll look gently," the clerk said.'
    )
    dog.memes["trust"] += 1
    clerk.memes["care"] += 1


def retrieve_anchor(world: World, clerk: Entity, anchor: Anchor, spot: Spot, action: Action) -> None:
    item = world.get("anchor")
    item.meters["found"] += 1
    world.facts["found"] = True
    world.say(
        f"{action.lead} Then {clerk.id} {action.text}."
    )
    world.say(
        f"There, {spot.reveal}, lay {anchor.phrase}; {anchor.shine}."
    )


def return_anchor(world: World, child: Entity, dog: Entity, ghost_cfg: GhostRole, anchor: Anchor) -> None:
    ghost = world.get("ghost")
    child.memes["courage"] += 1
    world.say(
        f'{child.id} took a careful breath, held out {anchor.phrase}, and said, '
        f'"Is this yours?"'
    )
    world.say(
        f"The ghost reached for it with hands pale as frost. When those fingers closed around the {anchor.label}, the room gave a long, soft sigh."
    )
    ghost.meters["unrest"] = 0.0
    world.facts["returned"] = True
    propagate(world, narrate=False)
    world.say(ghost_cfg.farewell)
    if dog.memes["calm"] >= THRESHOLD:
        world.say(f"{dog.id} lowered {dog.pronoun('possessive')} ears, sniffed once, and stopped growling at the dark.")


def close_story(world: World, venue: Venue, child: Entity, dog: Entity, clerk: Entity, ghost_cfg: GhostRole) -> None:
    world.say(
        f'The cold faded from {venue.label}, and the shadows turned ordinary again.'
    )
    world.say(
        f'"I have worked here a long time," {clerk.id} said, "but I have never seen the place rest like this."'
    )
    world.say(
        inner_line(child.id, "It is still a ghost story, but it does not feel scary now. It feels finished.")
    )
    world.say(
        f"As the rain eased outside, {child.id} and {dog.id} stepped back toward the door. "
        f"Behind them, the clerk set the lamp straight, and the old room stayed warm and still."
    )


def tell(
    venue: Venue,
    ghost_cfg: GhostRole,
    anchor: Anchor,
    spot: Spot,
    action: Action,
    child_name: str,
    child_gender: str,
    dog_name: str,
    clerk_name: str,
    trait: str,
) -> World:
    world = World()

    child = world.add(Entity(
        id=child_name,
        kind="character",
        type=child_gender,
        label=child_name,
        role="child",
        traits=[trait],
        attrs={},
    ))
    dog = world.add(Entity(
        id=dog_name,
        kind="character",
        type="dog",
        label=dog_name,
        role="dog",
        traits=["small", "loyal"],
        attrs={},
    ))
    clerk = world.add(Entity(
        id=clerk_name,
        kind="character",
        type="woman" if clerk_name.startswith("Ms.") else "man",
        label="the clerk",
        role="clerk",
        traits=["kind", "patient"],
        attrs={"counter_noun": venue.counter},
    ))
    ghost = world.add(Entity(
        id="ghost",
        kind="character",
        type="ghost",
        label=ghost_cfg.label,
        role="ghost",
        traits=["lonely"],
        attrs={"wants": ghost_cfg.anchor},
    ))
    room = world.add(Entity(
        id="room",
        kind="thing",
        type="room",
        label=venue.label,
        role="room",
        traits=[],
        attrs={},
    ))
    item = world.add(Entity(
        id="anchor",
        kind="thing",
        type="item",
        label=anchor.label,
        role="anchor",
        traits=[],
        attrs={"spot": spot.id},
    ))

    world.facts.update(
        venue=venue,
        ghost_cfg=ghost_cfg,
        anchor_cfg=anchor,
        spot_cfg=spot,
        action_cfg=action,
        child=child,
        dog=dog,
        clerk=clerk,
        ghost=ghost,
        anchor=item,
        returned=False,
        found=False,
    )

    child.memes["fear"] = 0.0
    child.memes["courage"] = 0.0
    dog.memes["alert"] = 0.0
    dog.meters["woof"] = 0.0
    clerk.memes["belief"] = 0.0
    ghost.meters["unrest"] = 0.0
    ghost.meters["seen"] = 0.0
    room.meters["cold"] = 0.0
    room.meters["sound"] = 0.0
    room.meters["calm"] = 0.0
    item.meters["found"] = 0.0

    introduce(world, venue, child, dog, clerk, ghost_cfg)
    settle_in(world, child, clerk, venue)

    world.para()
    stirring(world, child, dog, clerk, ghost_cfg)
    consult(world, child, clerk, dog, anchor, spot, action)

    world.para()
    retrieve_anchor(world, clerk, anchor, spot, action)
    return_anchor(world, child, dog, ghost_cfg, anchor)

    world.para()
    close_story(world, venue, child, dog, clerk, ghost_cfg)

    world.facts["resolved"] = world.facts["returned"] and room.meters["calm"] >= THRESHOLD
    return world


KNOWLEDGE = {
    "ghost": [(
        "What is a ghost story?",
        "A ghost story is a story about something spooky or mysterious, often a spirit or a strange old place. In a child-safe ghost story, the scary feeling usually leads to a gentle answer instead of real harm."
    )],
    "clerk": [(
        "What does a clerk do?",
        "A clerk helps take care of a place like a shop, inn, or station desk. A clerk may answer questions, keep things in order, and help people find what they need."
    )],
    "woof": [(
        "What does 'woof' mean?",
        "Woof is a word people use for a dog's bark. A dog may give a woof when it hears something strange or wants to warn someone."
    )],
    "key": [(
        "What is a brass key for?",
        "A brass key is used to open a lock, such as a drawer or a door. Small keys are easy to misplace, so people often keep them on a ring."
    )],
    "whistle": [(
        "What is a whistle?",
        "A whistle is a small thing that makes a sharp sound when you blow into it. Porters and guards once used whistles to signal people."
    )],
    "card": [(
        "What is a library card?",
        "A library card shows that a person can borrow books from a library. It helps keep track of which books go out and come back."
    )],
    "stool": [(
        "What is a step stool for?",
        "A step stool helps someone safely reach a high shelf or locker. It is steadier and wiser than climbing on furniture."
    )],
    "drawer": [(
        "Why do people keep things in drawers and cubbies?",
        "Drawers and cubbies help sort small objects so they do not get lost. If a place is old and busy, little things can still slip behind papers or string."
    )],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    dog = f["dog"]
    venue = f["venue"]
    ghost_cfg = f["ghost_cfg"]
    anchor = f["anchor_cfg"]
    return [
        f'Write a child-safe ghost story that includes the words "woof" and "clerk" and takes place in {venue.label}.',
        f"Tell a spooky but gentle story where {child.id} and a dog named {dog.id} hear a strange sound, speak with a clerk, and help a {ghost_cfg.label} find {anchor.phrase}.",
        "Write a story with dialogue and inner monologue in which a barking dog leads a child toward the answer to a ghostly mystery.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    dog = f["dog"]
    clerk = f["clerk"]
    venue = f["venue"]
    ghost_cfg = f["ghost_cfg"]
    anchor = f["anchor_cfg"]
    spot = f["spot_cfg"]
    action = f["action_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, the little dog {dog.id}, and the clerk {clerk.id} in {venue.label}. Together they meet a lonely {ghost_cfg.label}."
        ),
        (
            f"Why did {dog.id} give a woof?",
            f"{dog.id} gave a woof when the room turned cold and something rattled in the old place. The dog noticed the ghostly stirring before the others fully understood it."
        ),
        (
            f"What did {child.id} think when the strange sounds began?",
            f"{child.id} felt that the place was listening back, and then guessed the woof must mean something real was there. That inner thought helped {child.pronoun('object')} act bravely instead of freezing."
        ),
        (
            f"What did the ghost want?",
            f"The ghost wanted {anchor.phrase}. It had been lost, so the spirit could not rest and kept making the room cold and uneasy."
        ),
        (
            f"How did the clerk help solve the mystery?",
            f"The clerk {action.qa_text} and searched {spot.phrase}. That careful action let them find the missing object instead of making the old place messier."
        ),
        (
            "How did the story end?",
            f"{child.id} returned {anchor.phrase} to the ghost, and the cold feeling left {venue.label}. In the last image, the clerk straightened the lamp while the room stayed warm and still, showing that the haunting was over."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"ghost", "clerk", "woof"}
    tags |= set(f["ghost_cfg"].tags)
    tags |= set(f["action_cfg"].tags)
    if "drawer" in f["spot_cfg"].tags or "cubby" in f["spot_cfg"].tags:
        tags.add("drawer")
    out: list[tuple[str, str]] = []
    order = ["ghost", "clerk", "woof", "key", "whistle", "card", "stool", "drawer"]
    for tag in order:
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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:12} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(x[0] for x in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        venue="inn",
        ghost="bellhop",
        anchor="brass_key",
        spot="desk_drawer",
        action="ring_keys",
        child_name="Nora",
        child_gender="girl",
        dog_name="Pebble",
        clerk_name="Mr. Vale",
        trait="curious",
    ),
    StoryParams(
        venue="inn",
        ghost="bellhop",
        anchor="brass_key",
        spot="mail_cubby",
        action="slide_cubby",
        child_name="Owen",
        child_gender="boy",
        dog_name="Moss",
        clerk_name="Ms. Wren",
        trait="careful",
    ),
    StoryParams(
        venue="station",
        ghost="porter",
        anchor="silver_whistle",
        spot="high_locker",
        action="fetch_stool",
        child_name="Lucy",
        child_gender="girl",
        dog_name="Pip",
        clerk_name="Mr. North",
        trait="brave",
    ),
    StoryParams(
        venue="bookshop",
        ghost="page",
        anchor="blue_card",
        spot="ledger_shelf",
        action="fetch_stool",
        child_name="Theo",
        child_gender="boy",
        dog_name="Button",
        clerk_name="Ms. Bell",
        trait="thoughtful",
    ),
    StoryParams(
        venue="bookshop",
        ghost="page",
        anchor="blue_card",
        spot="desk_drawer",
        action="ring_keys",
        child_name="Iris",
        child_gender="girl",
        dog_name="Dottie",
        clerk_name="Mr. Reed",
        trait="quiethearted",
    ),
]


ASP_RULES = r"""
belongs_in(G, V) :- haunts(G, V).
matches(G, A)    :- wants(G, A).
sensible(Act)    :- action(Act), sense(Act, S), sense_min(M), S >= M.
valid(V, G, A, S, Act) :-
    venue(V), ghost(G), anchor(A), spot(S), action(Act),
    belongs_in(G, V), matches(G, A),
    affords(V, S), fits(A, S), reaches(Act, S), sensible(Act).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for venue_id, venue in VENUES.items():
        lines.append(asp.fact("venue", venue_id))
        for spot_id in sorted(venue.affords):
            lines.append(asp.fact("affords", venue_id, spot_id))
    for ghost_id, ghost in GHOSTS.items():
        lines.append(asp.fact("ghost", ghost_id))
        lines.append(asp.fact("haunts", ghost_id, ghost.venue))
        lines.append(asp.fact("wants", ghost_id, ghost.anchor))
    for anchor_id, anchor in ANCHORS.items():
        lines.append(asp.fact("anchor", anchor_id))
        for spot_id in sorted(anchor.fits):
            lines.append(asp.fact("fits", anchor_id, spot_id))
    for spot_id in SPOTS:
        lines.append(asp.fact("spot", spot_id))
    for action_id, action in ACTIONS.items():
        lines.append(asp.fact("action", action_id))
        lines.append(asp.fact("sense", action_id, action.sense))
        for spot_id in sorted(action.reaches):
            lines.append(asp.fact("reaches", action_id, spot_id))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/5."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible_actions() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(a for (a,) in asp.atoms(model, "sensible"))


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a child, a dog, a clerk, and a gentle ghostly mystery."
    )
    ap.add_argument("--venue", choices=VENUES)
    ap.add_argument("--ghost", choices=GHOSTS)
    ap.add_argument("--anchor", choices=ANCHORS)
    ap.add_argument("--spot", choices=SPOTS)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--child-name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--dog-name")
    ap.add_argument("--clerk-name")
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program (facts + inline rules)")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.venue and args.ghost and not ghost_belongs(args.ghost, args.venue):
        anchor_id = args.anchor or GHOSTS[args.ghost].anchor
        spot_id = args.spot or next(iter(sorted(VENUES[args.venue].affords)))
        action_id = args.action or next(iter(sorted(ACTIONS)))
        raise StoryError(explain_rejection(args.venue, args.ghost, anchor_id, spot_id, action_id))

    if args.ghost and args.anchor and not anchor_matches(args.ghost, args.anchor):
        venue_id = args.venue or GHOSTS[args.ghost].venue
        spot_id = args.spot or next(iter(sorted(VENUES[venue_id].affords)))
        action_id = args.action or next(iter(sorted(ACTIONS)))
        raise StoryError(explain_rejection(venue_id, args.ghost, args.anchor, spot_id, action_id))

    if args.action and ACTIONS[args.action].sense < SENSE_MIN:
        venue_id = args.venue or next(iter(sorted(VENUES)))
        ghost_id = args.ghost or next(iter(sorted(GHOSTS)))
        anchor_id = args.anchor or GHOSTS[ghost_id].anchor
        spot_id = args.spot or next(iter(sorted(SPOTS)))
        raise StoryError(explain_rejection(venue_id, ghost_id, anchor_id, spot_id, args.action))

    combos = [
        combo for combo in valid_combos()
        if (args.venue is None or combo[0] == args.venue)
        and (args.ghost is None or combo[1] == args.ghost)
        and (args.anchor is None or combo[2] == args.anchor)
        and (args.spot is None or combo[3] == args.spot)
        and (args.action is None or combo[4] == args.action)
    ]
    if not combos:
        venue_id = args.venue or next(iter(sorted(VENUES)))
        ghost_id = args.ghost or next(iter(sorted(GHOSTS)))
        anchor_id = args.anchor or GHOSTS[ghost_id].anchor
        spot_id = args.spot or next(iter(sorted(SPOTS)))
        action_id = args.action or next(iter(sorted(a.id for a in sensible_actions())))
        raise StoryError(explain_rejection(venue_id, ghost_id, anchor_id, spot_id, action_id))

    venue_id, ghost_id, anchor_id, spot_id, action_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    child_name = args.child_name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    dog_name = args.dog_name or rng.choice(DOG_NAMES)
    clerk_name = args.clerk_name or rng.choice(CLERK_NAMES)
    trait = args.trait or rng.choice(TRAITS)

    return StoryParams(
        venue=venue_id,
        ghost=ghost_id,
        anchor=anchor_id,
        spot=spot_id,
        action=action_id,
        child_name=child_name,
        child_gender=gender,
        dog_name=dog_name,
        clerk_name=clerk_name,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    for key, registry in (
        ("venue", VENUES),
        ("ghost", GHOSTS),
        ("anchor", ANCHORS),
        ("spot", SPOTS),
        ("action", ACTIONS),
    ):
        value = getattr(params, key)
        if value not in registry:
            raise StoryError(f"(Invalid {key}: {value})")
    if not valid_combo(params.venue, params.ghost, params.anchor, params.spot, params.action):
        raise StoryError(explain_rejection(params.venue, params.ghost, params.anchor, params.spot, params.action))

    world = tell(
        venue=VENUES[params.venue],
        ghost_cfg=GHOSTS[params.ghost],
        anchor=ANCHORS[params.anchor],
        spot=SPOTS[params.spot],
        action=ACTIONS[params.action],
        child_name=params.child_name,
        child_gender=params.child_gender,
        dog_name=params.dog_name,
        clerk_name=params.clerk_name,
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
    clingo_set = set(asp_valid_combos())
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

    c_sens = set(asp_sensible_actions())
    p_sens = {a.id for a in sensible_actions()}
    if c_sens == p_sens:
        print(f"OK: sensible actions match ({sorted(c_sens)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible actions: clingo={sorted(c_sens)} python={sorted(p_sens)}")

    try:
        smoke = generate(CURATED[0])
        buf = io.StringIO()
        old = sys.stdout
        sys.stdout = buf
        try:
            emit(smoke, trace=False, qa=False, header="### smoke")
        finally:
            sys.stdout = old
        if not smoke.story.strip():
            raise StoryError("smoke story was empty")
        print("OK: generate()/emit() smoke test passed.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    parser = build_parser()
    for seed in range(10):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
            params.seed = seed
            sample = generate(params)
            if not sample.story.strip():
                raise StoryError(f"empty story for seed {seed}")
        except Exception as err:
            rc = 1
            print(f"RANDOM GENERATION FAILED at seed {seed}: {err}")
            break
    else:
        print("OK: random generation smoke tests passed.")
    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show sensible/1.\n#show valid/5."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible actions: {', '.join(asp_sensible_actions())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (venue, ghost, anchor, spot, action) combos:\n")
        for venue_id, ghost_id, anchor_id, spot_id, action_id in combos:
            print(f"  {venue_id:8} {ghost_id:8} {anchor_id:14} {spot_id:12} {action_id}")
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
            header = f"### {p.child_name} at {p.venue}: {p.ghost} / {p.spot} / {p.action}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
