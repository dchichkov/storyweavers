#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/picnic_kindness_suspense_surprise_mystery.py
=======================================================================

A small story world about a picnic mystery: something tiny goes missing, the
children follow a clue with growing suspense, and the surprise ending turns the
"thief" into someone who needs kindness.

The world model enforces a simple reasonableness rule:
- the guest must plausibly appear in the chosen place,
- the clue must fit that guest,
- the missing picnic food must be something that guest would plausibly take,
- and the kindness action must suit that guest.

Run it
------
    python storyworlds/worlds/gpt-5.4/picnic_kindness_suspense_surprise_mystery.py
    python storyworlds/worlds/gpt-5.4/picnic_kindness_suspense_surprise_mystery.py --place park --guest duckling
    python storyworlds/worlds/gpt-5.4/picnic_kindness_suspense_surprise_mystery.py --guest shy_child --clue pawprints
    python storyworlds/worlds/gpt-5.4/picnic_kindness_suspense_surprise_mystery.py --all
    python storyworlds/worlds/gpt-5.4/picnic_kindness_suspense_surprise_mystery.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/picnic_kindness_suspense_surprise_mystery.py --verify
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


# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
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
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


# ---------------------------------------------------------------------------
# Domain configuration
# ---------------------------------------------------------------------------
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
    opening: str
    hush: str
    trail_to: str
    supports: set[str] = field(default_factory=set)
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
class MissingThing:
    id: str
    label: str
    phrase: str
    plural: bool = False
    edible_tags: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)

    def it(self) -> str:
        return "them" if self.plural else "it"
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
class Clue:
    id: str
    noun: str
    phrase: str
    discover: str
    follow: str
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
class Guest:
    id: str
    label: str
    type: str
    reveal_place: str
    reveal_line: str
    clue_ids: set[str] = field(default_factory=set)
    likes_food: set[str] = field(default_factory=set)
    place_ids: set[str] = field(default_factory=set)
    action_ids: set[str] = field(default_factory=set)
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
class KindAction:
    id: str
    label: str
    line: str
    comfort: str
    ending: str
    guest_ids: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


# ---------------------------------------------------------------------------
# World and rules
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


def _r_missing_stirs(world: World) -> list[str]:
    hero = world.get("hero")
    snack = world.get("snack")
    if snack.meters["missing"] < THRESHOLD:
        return []
    sig = ("missing_stirs", snack.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["curiosity"] += 1
    hero.memes["suspense"] += 1
    if "friend" in world.entities:
        world.get("friend").memes["suspense"] += 1
    return []


def _r_clue_tenses(world: World) -> list[str]:
    clue = world.get("clue")
    if clue.meters["noticed"] < THRESHOLD:
        return []
    sig = ("clue_tenses", clue.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    world.get("hero").memes["suspense"] += 1
    if "friend" in world.entities:
        world.get("friend").memes["curiosity"] += 1
    return []


def _r_kindness_heals(world: World) -> list[str]:
    guest = world.get("guest")
    if guest.meters["helped"] < THRESHOLD:
        return []
    sig = ("kindness_heals", guest.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    guest.meters["hidden"] = 0.0
    guest.meters["hungry"] = 0.0
    guest.memes["relief"] += 1
    world.get("hero").memes["kindness"] += 1
    world.get("hero").memes["joy"] += 1
    if "friend" in world.entities:
        world.get("friend").memes["joy"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="missing_stirs", tag="emotional", apply=_r_missing_stirs),
    Rule(name="clue_tenses", tag="emotional", apply=_r_clue_tenses),
    Rule(name="kindness_heals", tag="social", apply=_r_kindness_heals),
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
            elif any(sig[0] == rule.name for sig in world.fired):
                # state may still have changed even without narrative
                changed = changed or False
    if narrate:
        for sent in produced:
            world.say(sent)
    return produced


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
PLACES = {
    "park": Place(
        id="park",
        label="the park",
        opening="The park was bright with sun, but the willow trees made cool green shadows.",
        hush="A little breeze moved the grass, and every rustle sounded as if it might be a clue.",
        trail_to="toward the reeds by the pond",
        supports={"duckling", "puppy", "shy_child"},
        tags={"park", "pond"},
    ),
    "garden": Place(
        id="garden",
        label="the garden",
        opening="The garden smelled like warm soil and mint, and the flowers nodded over the path.",
        hush="Between the bushes, every tiny shake of a leaf seemed to whisper a secret.",
        trail_to="past the rose bush and the little gate",
        supports={"puppy", "shy_child", "cat"},
        tags={"garden"},
    ),
    "lakeside": Place(
        id="lakeside",
        label="the lakeside meadow",
        opening="The lakeside meadow glittered beside the water, and the picnic blanket looked like a bright little island in the grass.",
        hush="The lake lapped softly, and now and then the reeds clicked together in a way that made the mystery feel real.",
        trail_to="along the stones near the water",
        supports={"duckling", "shy_child", "cat"},
        tags={"lake"},
    ),
}

MISSING_THINGS = {
    "apple_slices": MissingThing(
        id="apple_slices",
        label="apple slices",
        phrase="a little box of apple slices",
        plural=True,
        edible_tags={"fruit", "child", "duckling"},
        tags={"fruit"},
    ),
    "bread_roll": MissingThing(
        id="bread_roll",
        label="bread roll",
        phrase="a soft bread roll",
        plural=False,
        edible_tags={"bread", "child", "duckling", "puppy"},
        tags={"bread"},
    ),
    "berry_muffin": MissingThing(
        id="berry_muffin",
        label="berry muffin",
        phrase="a berry muffin",
        plural=False,
        edible_tags={"sweet", "child"},
        tags={"muffin"},
    ),
    "cheese_sandwich": MissingThing(
        id="cheese_sandwich",
        label="cheese sandwich",
        phrase="a small cheese sandwich",
        plural=False,
        edible_tags={"savory", "child", "puppy"},
        tags={"sandwich"},
    ),
}

CLUES = {
    "tiny_footprints": Clue(
        id="tiny_footprints",
        noun="tiny footprints",
        phrase="a line of tiny footprints",
        discover="At the edge of the blanket, there was a line of tiny footprints pressed into the dust.",
        follow="The little marks wandered away from the picnic blanket as if they had their own quiet plan.",
        tags={"footprints"},
    ),
    "wet_feather": Clue(
        id="wet_feather",
        noun="wet feather",
        phrase="a wet feather",
        discover="Beside the basket lay a wet feather, shining like a small clue in the sun.",
        follow="It pointed the children toward the water, and the mystery seemed to hold its breath.",
        tags={"feather"},
    ),
    "red_ribbon": Clue(
        id="red_ribbon",
        noun="red ribbon",
        phrase="a twist of red ribbon",
        discover="Caught on the corner of the blanket was a twist of red ribbon.",
        follow="It fluttered once in the breeze, pointing the way like a secret arrow.",
        tags={"ribbon"},
    ),
    "crumb_trail": Clue(
        id="crumb_trail",
        noun="crumb trail",
        phrase="a trail of crumbs",
        discover="Near the basket, a trail of crumbs led away one tiny piece at a time.",
        follow="The crumbs made a crooked path that was impossible not to follow.",
        tags={"crumbs"},
    ),
}

GUESTS = {
    "duckling": Guest(
        id="duckling",
        label="duckling",
        type="animal",
        reveal_place="a patch of reeds",
        reveal_line="A small duckling stood there, peeping in a worried voice.",
        clue_ids={"wet_feather", "tiny_footprints", "crumb_trail"},
        likes_food={"fruit", "bread"},
        place_ids={"park", "lakeside"},
        action_ids={"share_plate"},
        tags={"duck", "animal"},
    ),
    "puppy": Guest(
        id="puppy",
        label="puppy",
        type="animal",
        reveal_place="behind a bush",
        reveal_line="A fluffy puppy peeked out with wide eyes and one paw on the missing food.",
        clue_ids={"tiny_footprints", "crumb_trail"},
        likes_food={"bread", "savory"},
        place_ids={"park", "garden"},
        action_ids={"share_plate"},
        tags={"puppy", "animal"},
    ),
    "shy_child": Guest(
        id="shy_child",
        label="child",
        type="child",
        reveal_place="behind a tree trunk",
        reveal_line="A small child sat there hugging their knees, looking hungry and too shy to ask for anything.",
        clue_ids={"red_ribbon", "crumb_trail", "tiny_footprints"},
        likes_food={"fruit", "bread", "sweet", "savory"},
        place_ids={"park", "garden", "lakeside"},
        action_ids={"invite_in"},
        tags={"child", "friend"},
    ),
    "cat": Guest(
        id="cat",
        label="cat",
        type="animal",
        reveal_place="under a low bench",
        reveal_line="A thin gray cat blinked from the shadows with the missing food beside its paws.",
        clue_ids={"tiny_footprints", "crumb_trail"},
        likes_food={"savory", "bread"},
        place_ids={"garden", "lakeside"},
        action_ids={"share_plate"},
        tags={"cat", "animal"},
    ),
}

ACTIONS = {
    "share_plate": KindAction(
        id="share_plate",
        label="share on a small plate",
        line="made a small plate from the picnic food and set it down gently",
        comfort="No one scolded. Instead, the children spoke in soft voices and moved slowly so the frightened guest would feel safe.",
        ending="Soon the mystery was not about stealing at all. It was about someone small being hungry and someone else choosing to be kind.",
        guest_ids={"duckling", "puppy", "cat"},
        tags={"share", "kindness"},
    ),
    "invite_in": KindAction(
        id="invite_in",
        label="invite to join the picnic",
        line="opened the basket, spread the napkin wider, and invited the guest to sit with them",
        comfort="The children smiled instead of staring, and that gentle welcome made the shy guest stop hiding.",
        ending="Soon the mystery turned into a new friendship, right there in the middle of the picnic.",
        guest_ids={"shy_child"},
        tags={"share", "friendship"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Nora", "Rose"]
BOY_NAMES = ["Tom", "Ben", "Max", "Sam", "Leo", "Finn", "Noah", "Eli"]
TRAITS = ["careful", "curious", "gentle", "thoughtful", "brave", "observant"]


# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    missing: str
    clue: str
    guest: str
    action: str
    hero: str
    hero_gender: str
    friend: str
    friend_gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Reasonableness gate
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


def clue_matches(guest: Guest, clue: Clue) -> bool:
    return clue.id in guest.clue_ids


def food_matches(guest: Guest, missing: MissingThing) -> bool:
    return bool(guest.likes_food & missing.edible_tags)


def place_matches(place: Place, guest: Guest) -> bool:
    return guest.id in place.supports and place.id in guest.place_ids


def action_matches(guest: Guest, action: KindAction) -> bool:
    return action.id in guest.action_ids and guest.id in action.guest_ids


def valid_combos() -> list[tuple[str, str, str, str, str]]:
    combos: list[tuple[str, str, str, str, str]] = []
    for place_id, place in PLACES.items():
        for guest_id, guest in GUESTS.items():
            if not place_matches(place, guest):
                continue
            for clue_id, clue in CLUES.items():
                if not clue_matches(guest, clue):
                    continue
                for missing_id, missing in MISSING_THINGS.items():
                    if not food_matches(guest, missing):
                        continue
                    for action_id, action in ACTIONS.items():
                        if action_matches(guest, action):
                            combos.append((place_id, missing_id, clue_id, guest_id, action_id))
    return sorted(combos)


def explain_rejection(place: Place, missing: MissingThing, clue: Clue, guest: Guest,
                      action: KindAction) -> str:
    if not place_matches(place, guest):
        return (
            f"(No story: {guest.label} is not a good fit for {place.label}. "
            f"The mystery needs a guest who could really be there.)"
        )
    if not clue_matches(guest, clue):
        return (
            f"(No story: {clue.phrase} does not fit a {guest.label}. "
            f"The clue must honestly point to the hidden guest.)"
        )
    if not food_matches(guest, missing):
        return (
            f"(No story: {missing.label} is not something this {guest.label} would plausibly take. "
            f"The missing picnic item must match the reveal.)"
        )
    if not action_matches(guest, action):
        return (
            f"(No story: '{action.label}' does not suit a {guest.label}. "
            f"The kind ending must fit who is found at the end of the mystery.)"
        )
    return "(No story: this combination does not make a reasonable picnic mystery.)"


# ---------------------------------------------------------------------------
# Screenplay verbs
# ---------------------------------------------------------------------------
def setup_picnic(world: World, place: Place, hero: Entity, friend: Entity,
                 parent: Entity, missing: MissingThing) -> None:
    hero.memes["joy"] += 1
    friend.memes["joy"] += 1
    world.say(
        f"One bright day, {hero.id} and {friend.id} spread a picnic blanket in {place.label} while "
        f"{hero.id}'s {parent.label_word} unpacked fruit, cups, and {missing.phrase}."
    )
    world.say(place.opening)
    world.say(
        f"{hero.id} loved mysteries, and {friend.id} said that even an ordinary picnic could feel "
        f"like the beginning of one if everyone listened carefully."
    )


def vanish(world: World, hero: Entity, friend: Entity, missing: MissingThing, place: Place) -> None:
    snack = world.get("snack")
    snack.meters["missing"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then, just as the children reached for {missing.phrase}, it was gone."
    )
    world.say(
        f'"Wait," whispered {friend.id}. "Did you see that?" {place.hush}'
    )
    world.say(
        f"{hero.id} looked under the cups, under the napkin, and even under the edge of the blanket, "
        f"but {missing.it()} had truly disappeared."
    )


def find_clue(world: World, hero: Entity, friend: Entity, clue: Clue) -> None:
    clue_ent = world.get("clue")
    clue_ent.meters["noticed"] += 1
    propagate(world, narrate=False)
    world.say(clue.discover)
    world.say(
        f'"A clue," {hero.id} said softly, and now the picnic felt like a real mystery.'
    )
    world.say(clue.follow)


def follow_path(world: World, hero: Entity, friend: Entity, place: Place) -> None:
    world.say(
        f"Step by step, the children followed the trail {place.trail_to}. They did not run. "
        f"They listened."
    )
    world.say(
        f"Every rustle made {friend.id} squeeze closer, and every quiet step made {hero.id}'s heart beat a little faster."
    )


def reveal_guest(world: World, guest_cfg: Guest, hero: Entity, friend: Entity) -> None:
    guest = world.get("guest")
    world.say(
        f"At last they peered into {guest_cfg.reveal_place}. {guest_cfg.reveal_line}"
    )
    if guest_cfg.id == "shy_child":
        guest.meters["hungry"] += 1
        guest.meters["hidden"] += 1
        guest.memes["worry"] += 1
        world.say(
            f"So that was the surprise: not a sneaky picnic thief at all, but a child who had been too shy to ask for help."
        )
    else:
        guest.meters["hungry"] += 1
        guest.meters["hidden"] += 1
        guest.memes["fear"] += 1
        world.say(
            f"So that was the surprise: not a scary thief, only a small hungry {guest_cfg.label}."
        )


def choose_kindness(world: World, action: KindAction, hero: Entity, friend: Entity,
                    guest_cfg: Guest, missing: MissingThing, parent: Entity) -> None:
    guest = world.get("guest")
    guest.meters["helped"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{hero.id} did not snatch the food back. Instead, {hero.pronoun()} {action.line}."
    )
    world.say(action.comfort)
    if guest_cfg.id == "shy_child":
        world.say(
            f'{friend.id} patted the blanket and said, "You can share our picnic with us."'
        )
    else:
        world.say(
            f'{parent.label_word.capitalize()} nodded and said, "A hungry creature needs gentleness more than scolding."'
        )
    world.say(
        f"The tense little feeling in the air melted away, and the mystery was solved with kindness."
    )


def ending(world: World, place: Place, hero: Entity, friend: Entity,
           guest_cfg: Guest, action: KindAction, missing: MissingThing) -> None:
    if guest_cfg.id == "shy_child":
        world.say(
            f"Soon the children were sitting close together on the blanket, sharing crumbs and stories while the sun moved across {place.label}."
        )
    else:
        world.say(
            f"Soon the little {guest_cfg.label} was calm, and the children watched it nibble beside the blanket instead of hiding."
        )
    world.say(action.ending)
    world.say(
        f"When the picnic was packed up at last, {hero.id} knew the best part had not been the missing {missing.label}. "
        f"It had been discovering that a soft heart can solve a mystery better than suspicion can."
    )


# ---------------------------------------------------------------------------
# Story assembly
# ---------------------------------------------------------------------------
def tell(place: Place, missing: MissingThing, clue: Clue, guest_cfg: Guest,
         action: KindAction, hero_name: str, hero_gender: str,
         friend_name: str, friend_gender: str, parent_type: str, trait: str) -> World:
    world = World()
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_gender,
        role="hero",
        traits=[trait],
        attrs={"trait": trait},
    ))
    friend = world.add(Entity(
        id=friend_name,
        kind="character",
        type=friend_gender,
        role="friend",
        traits=["steady"],
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=parent_type,
        role="parent",
        label="the parent",
    ))
    snack = world.add(Entity(
        id="snack",
        type="food",
        label=missing.label,
        tags=set(missing.edible_tags),
    ))
    clue_ent = world.add(Entity(
        id="clue",
        type="clue",
        label=clue.noun,
        tags=set(clue.tags),
    ))
    guest = world.add(Entity(
        id="guest",
        kind="character",
        type=guest_cfg.type,
        label=guest_cfg.label,
        role="guest",
        tags=set(guest_cfg.tags),
    ))

    world.facts.update(
        place=place,
        missing_cfg=missing,
        clue_cfg=clue,
        guest_cfg=guest_cfg,
        action_cfg=action,
        hero=hero,
        friend=friend,
        parent=parent,
        snack=snack,
        clue=clue_ent,
        guest=guest,
    )

    setup_picnic(world, place, hero, friend, parent, missing)
    world.para()
    vanish(world, hero, friend, missing, place)
    find_clue(world, hero, friend, clue)
    follow_path(world, hero, friend, place)
    world.para()
    reveal_guest(world, guest_cfg, hero, friend)
    choose_kindness(world, action, hero, friend, guest_cfg, missing, parent)
    world.para()
    ending(world, place, hero, friend, guest_cfg, action, missing)

    world.facts.update(
        solved=guest.meters["helped"] >= THRESHOLD,
        surprise_reveal=guest_cfg.id,
        suspense=hero.memes["suspense"],
        kindness=hero.memes["kindness"],
    )
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
KNOWLEDGE = {
    "picnic": [(
        "What is a picnic?",
        "A picnic is a meal you eat outside, often on a blanket. People bring food and sit together in a park, garden, or another open place."
    )],
    "clue": [(
        "What is a clue?",
        "A clue is a small sign that helps you figure something out. In a mystery, clues point toward the answer step by step."
    )],
    "mystery": [(
        "What is a mystery?",
        "A mystery is something hidden or not understood at first. You solve it by noticing details and putting the clues together."
    )],
    "kindness": [(
        "What is kindness?",
        "Kindness means choosing to help, share, or comfort someone. It can turn a tense moment into a gentle one."
    )],
    "duck": [(
        "Why do ducklings stay near water?",
        "Ducklings feel safest near water and reeds because that is where they often find their family and food. A small duckling can get scared if it is alone."
    )],
    "puppy": [(
        "Why should you move gently around a scared puppy?",
        "A scared puppy may not understand what people are doing. Gentle voices and slow movements help it feel safe."
    )],
    "cat": [(
        "Why do cats hide when they feel unsure?",
        "Cats often hide when they are frightened or unsure of a place. A quiet, patient approach helps them relax."
    )],
    "friend": [(
        "How can you help a shy child feel welcome?",
        "You can smile, make room, and invite the child to join you. A friendly welcome helps shy feelings shrink."
    )],
}
KNOWLEDGE_ORDER = ["picnic", "clue", "mystery", "kindness", "duck", "puppy", "cat", "friend"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    place = f["place"]
    guest_cfg = f["guest_cfg"]
    missing = f["missing_cfg"]
    clue = f["clue_cfg"]
    hero = f["hero"]
    return [
        f'Write a short mystery story for a 3-to-5-year-old about a picnic where {missing.label} goes missing and a clue leads to a surprising, kind ending.',
        f"Tell a gentle suspense story where {hero.id} follows {clue.phrase} during a picnic in {place.label} and discovers a hidden {guest_cfg.label}.",
        'Write a child-facing mystery that includes the word "picnic", builds suspense with a small clue, and ends with kindness instead of blame.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    parent = f["parent"]
    place = f["place"]
    missing = f["missing_cfg"]
    clue = f["clue_cfg"]
    guest_cfg = f["guest_cfg"]
    action = f["action_cfg"]

    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id} and {friend.id} at a picnic in {place.label}. They begin with lunch on a blanket, but soon they have a mystery to solve."
        ),
        (
            "What made the picnic feel mysterious?",
            f"{missing.phrase.capitalize()} disappeared from the blanket, and then the children found {clue.phrase}. The missing food and the clue together made the picnic feel like a real mystery."
        ),
        (
            f"Why did {hero.id} and {friend.id} feel suspense?",
            f"They did not know who had taken the food or where the trail would lead. Every rustle and quiet step made the answer feel close, but still hidden."
        ),
        (
            "What was the surprise at the end?",
            f"The children did not find a mean thief at all. They found {guest_cfg.reveal_line.lower()} The surprise was that the mystery came from hunger or shyness, not meanness."
        ),
        (
            "How did kindness solve the problem?",
            f"{hero.id} {action.line} instead of grabbing the food back. That gentle choice calmed the hidden guest and turned fear into relief."
        ),
    ]
    if guest_cfg.id == "shy_child":
        qa.append((
            "Why was inviting the hidden guest the right thing to do?",
            f"The hidden guest was a shy child who needed welcome more than blame. By making room on the blanket, the children solved the mystery and gave the child a safe place in the picnic."
        ))
    else:
        qa.append((
            f"Why did {parent.label_word} approve of what the children did?",
            f"{parent.label_word.capitalize()} could see the guest was small and frightened, not naughty in a mean way. Sharing calmly was kinder and safer than scaring it."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    guest_cfg = world.facts["guest_cfg"]
    tags = {"picnic", "clue", "mystery", "kindness"} | set(guest_cfg.tags)
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
        if ent.traits:
            bits.append(f"traits={ent.traits}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(sig[0] for sig in world.fired))}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
clue_ok(G,C) :- guest(G), clue(C), clue_for(G,C).
food_ok(G,M) :- guest(G), missing(M), likes(G,T), food_tag(M,T).
place_ok(P,G) :- place(P), guest(G), supports(P,G), appears_in(G,P).
action_ok(G,A) :- guest(G), action(A), action_for(G,A), guest_for(A,G).

valid(P,M,C,G,A) :- place_ok(P,G), clue_ok(G,C), food_ok(G,M), action_ok(G,A).

#show valid/5.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        for guest_id in sorted(place.supports):
            lines.append(asp.fact("supports", place_id, guest_id))
    for missing_id, missing in MISSING_THINGS.items():
        lines.append(asp.fact("missing", missing_id))
        for tag in sorted(missing.edible_tags):
            lines.append(asp.fact("food_tag", missing_id, tag))
    for clue_id in CLUES:
        lines.append(asp.fact("clue", clue_id))
    for guest_id, guest in GUESTS.items():
        lines.append(asp.fact("guest", guest_id))
        for clue_id in sorted(guest.clue_ids):
            lines.append(asp.fact("clue_for", guest_id, clue_id))
        for tag in sorted(guest.likes_food):
            lines.append(asp.fact("likes", guest_id, tag))
        for place_id in sorted(guest.place_ids):
            lines.append(asp.fact("appears_in", guest_id, place_id))
        for action_id in sorted(guest.action_ids):
            lines.append(asp.fact("action_for", guest_id, action_id))
    for action_id, action in ACTIONS.items():
        lines.append(asp.fact("action", action_id))
        for guest_id in sorted(action.guest_ids):
            lines.append(asp.fact("guest_for", action_id, guest_id))
    return "\n".join(lines)


def asp_program(extra: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid picnic mystery combos:")
        if cl - py:
            print("  only in clingo:", sorted(cl - py))
        if py - cl:
            print("  only in python:", sorted(py - cl))

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("smoke test generated an empty story")
        print("OK: smoke-test story generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


# ---------------------------------------------------------------------------
# CLI and standard interface
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(
        place="park",
        missing="apple_slices",
        clue="wet_feather",
        guest="duckling",
        action="share_plate",
        hero="Lily",
        hero_gender="girl",
        friend="Tom",
        friend_gender="boy",
        parent="mother",
        trait="observant",
    ),
    StoryParams(
        place="garden",
        missing="cheese_sandwich",
        clue="tiny_footprints",
        guest="cat",
        action="share_plate",
        hero="Ben",
        hero_gender="boy",
        friend="Mia",
        friend_gender="girl",
        parent="father",
        trait="gentle",
    ),
    StoryParams(
        place="garden",
        missing="berry_muffin",
        clue="red_ribbon",
        guest="shy_child",
        action="invite_in",
        hero="Ava",
        hero_gender="girl",
        friend="Sam",
        friend_gender="boy",
        parent="mother",
        trait="curious",
    ),
    StoryParams(
        place="park",
        missing="bread_roll",
        clue="crumb_trail",
        guest="puppy",
        action="share_plate",
        hero="Noah",
        hero_gender="boy",
        friend="Ella",
        friend_gender="girl",
        parent="father",
        trait="brave",
    ),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a picnic mystery solved with kindness."
    )
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--missing", choices=sorted(MISSING_THINGS))
    ap.add_argument("--clue", choices=sorted(CLUES))
    ap.add_argument("--guest", choices=sorted(GUESTS))
    ap.add_argument("--action", choices=sorted(ACTIONS))
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = PLACES.get(args.place) if args.place else None
    missing = MISSING_THINGS.get(args.missing) if args.missing else None
    clue = CLUES.get(args.clue) if args.clue else None
    guest = GUESTS.get(args.guest) if args.guest else None
    action = ACTIONS.get(args.action) if args.action else None

    if all(x is not None for x in (place, missing, clue, guest, action)):
        if not (place_matches(place, guest) and clue_matches(guest, clue)
                and food_matches(guest, missing) and action_matches(guest, action)):
            raise StoryError(explain_rejection(place, missing, clue, guest, action))

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.missing is None or combo[1] == args.missing)
        and (args.clue is None or combo[2] == args.clue)
        and (args.guest is None or combo[3] == args.guest)
        and (args.action is None or combo[4] == args.action)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, missing_id, clue_id, guest_id, action_id = rng.choice(sorted(combos))
    hero_name, hero_gender = _pick_name(rng)
    friend_name, friend_gender = _pick_name(rng, avoid=hero_name)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(
        place=place_id,
        missing=missing_id,
        clue=clue_id,
        guest=guest_id,
        action=action_id,
        hero=hero_name,
        hero_gender=hero_gender,
        friend=friend_name,
        friend_gender=friend_gender,
        parent=parent,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    place = PLACES.get(params.place)
    missing = MISSING_THINGS.get(params.missing)
    clue = CLUES.get(params.clue)
    guest = GUESTS.get(params.guest)
    action = ACTIONS.get(params.action)

    if place is None or missing is None or clue is None or guest is None or action is None:
        raise StoryError("(Invalid params: unknown registry key.)")
    if not (place_matches(place, guest) and clue_matches(guest, clue)
            and food_matches(guest, missing) and action_matches(guest, action)):
        raise StoryError(explain_rejection(place, missing, clue, guest, action))

    world = tell(
        place=place,
        missing=missing,
        clue=clue,
        guest_cfg=guest,
        action=action,
        hero_name=params.hero,
        hero_gender=params.hero_gender,
        friend_name=params.friend,
        friend_gender=params.friend_gender,
        parent_type=params.parent,
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, missing, clue, guest, action) combos:\n")
        for place_id, missing_id, clue_id, guest_id, action_id in combos:
            print(f"  {place_id:8} {missing_id:15} {clue_id:15} {guest_id:10} {action_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(params) for params in CURATED]
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero} & {p.friend}: {p.missing} at {p.place} ({p.guest}, {p.clue})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
