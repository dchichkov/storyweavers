#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/macrame_bravery_kindness_mystery.py
==============================================================

A standalone story world about a small mystery in a place with macrame decor:
a child hears a strange clue from a shadowy spot, chooses bravery over fear,
and solves the mystery with kindness.

The core domain is intentionally narrow and constraint-checked:

- a place affords only certain hiding spots
- a clue must plausibly come from the hidden creature
- the creature must fit in the hiding spot
- the chosen response must make sense for that situation

The story itself is always driven by simulated state: a hidden creature causes a
mystery, the children react emotionally, bravery carries the hero closer, and a
kind response resolves the problem.

Run it
------
    python storyworlds/worlds/gpt-5.4/macrame_bravery_kindness_mystery.py
    python storyworlds/worlds/gpt-5.4/macrame_bravery_kindness_mystery.py --place library_nook --clue jingle
    python storyworlds/worlds/gpt-5.4/macrame_bravery_kindness_mystery.py --creature puppy --hideout yarn_basket
    python storyworlds/worlds/gpt-5.4/macrame_bravery_kindness_mystery.py --all
    python storyworlds/worlds/gpt-5.4/macrame_bravery_kindness_mystery.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/macrame_bravery_kindness_mystery.py --verify
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
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "grandma"}
        male = {"boy", "father", "dad", "man", "grandpa"}
        neutral = {"teacher", "librarian", "grownup"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in neutral:
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.type.replace("_", " ")
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
    macrame_item: str
    afford_hideouts: set[str] = field(default_factory=set)
    adult_type: str = "grownup"
    adult_label: str = "the grown-up"
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
    hear: str
    source: str
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
class CreatureCfg:
    id: str
    label: str
    phrase: str
    size: int
    shy: int
    sounds: set[str] = field(default_factory=set)
    food_motivated: bool = False
    owner_kind: str = "child"
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
class Hideout:
    id: str
    label: str
    phrase: str
    capacity: int
    difficulty: int
    tangled: bool = False
    shadow_text: str = ""
    reveal_text: str = ""
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
    text: str
    qa_text: str
    needs_tangled: bool = False
    needs_plain: bool = False
    requires_food: bool = False
    only_hideout: str = ""
    works_any: bool = False
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


def _r_hidden_mystery(world: World) -> list[str]:
    out: list[str] = []
    creature = world.get("creature")
    room = world.get("room")
    if creature.meters["hidden"] >= THRESHOLD and creature.meters["making_clue"] >= THRESHOLD:
        sig = ("mystery",)
        if sig not in world.fired:
            world.fired.add(sig)
            room.meters["mystery"] += 1
            for child in (world.get("hero"), world.get("friend")):
                child.memes["curiosity"] += 1
                child.memes["unease"] += 1
            out.append("__mystery__")
    return out


def _r_tangle_fear(world: World) -> list[str]:
    out: list[str] = []
    creature = world.get("creature")
    if creature.meters["tangled"] >= THRESHOLD:
        sig = ("fear",)
        if sig not in world.fired:
            world.fired.add(sig)
            creature.memes["fear"] += 1
            out.append("__fear__")
    return out


def _r_kind_rescue(world: World) -> list[str]:
    out: list[str] = []
    creature = world.get("creature")
    hero = world.get("hero")
    if creature.meters["found"] >= THRESHOLD and creature.meters["helped"] >= THRESHOLD:
        sig = ("rescue",)
        if sig not in world.fired:
            world.fired.add(sig)
            creature.meters["hidden"] = 0.0
            creature.meters["tangled"] = 0.0
            creature.memes["fear"] = 0.0
            creature.memes["relief"] += 1
            hero.memes["relief"] += 1
            hero.memes["kindness"] += 1
            out.append("__rescued__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="hidden_mystery", tag="social", apply=_r_hidden_mystery),
    Rule(name="tangle_fear", tag="emotional", apply=_r_tangle_fear),
    Rule(name="kind_rescue", tag="resolution", apply=_r_kind_rescue),
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


PLACES = {
    "craft_room": Place(
        id="craft_room",
        label="the craft room",
        scene="a small craft room that smelled like paper and glue",
        macrame_item="a big macrame rainbow hanging by the window",
        afford_hideouts={"behind_macrame", "yarn_basket"},
        adult_type="teacher",
        adult_label="the teacher",
        tags={"craft_room", "macrame"},
    ),
    "library_nook": Place(
        id="library_nook",
        label="the library nook",
        scene="a quiet reading nook with soft rugs and low shelves",
        macrame_item="a sleepy macrame owl above the book bins",
        afford_hideouts={"yarn_basket", "coat_cubby"},
        adult_type="librarian",
        adult_label="the librarian",
        tags={"library", "macrame"},
    ),
    "porch": Place(
        id="porch",
        label="the back porch",
        scene="a shady back porch with flower pots and a creaky bench",
        macrame_item="a swaying macrame plant hanger near the door",
        afford_hideouts={"behind_macrame", "coat_cubby"},
        adult_type="grandpa",
        adult_label="Grandpa",
        tags={"porch", "macrame"},
    ),
}

CLUES = {
    "scratch": Clue(
        id="scratch",
        hear="a tiny scratch-scratch",
        source="something was scratching softly in the dark",
        tags={"sound"},
    ),
    "sneeze": Clue(
        id="sneeze",
        hear="a small little achoo",
        source="someone gave a surprised sneeze",
        tags={"sound"},
    ),
    "jingle": Clue(
        id="jingle",
        hear="a faint jingle-jingle",
        source="something metal was tapping with a tiny jingle",
        tags={"sound", "collar"},
    ),
    "whimper": Clue(
        id="whimper",
        hear="a worried little whimper",
        source="something sounded lonely and scared",
        tags={"sound"},
    ),
}

CREATURES = {
    "kitten": CreatureCfg(
        id="kitten",
        label="kitten",
        phrase="a small gray kitten",
        size=1,
        shy=1,
        sounds={"scratch", "jingle"},
        food_motivated=True,
        owner_kind="neighbor",
        tags={"kitten", "pet"},
    ),
    "rabbit": CreatureCfg(
        id="rabbit",
        label="rabbit",
        phrase="a soft brown rabbit",
        size=1,
        shy=2,
        sounds={"scratch", "sneeze"},
        food_motivated=True,
        owner_kind="child",
        tags={"rabbit", "pet"},
    ),
    "puppy": CreatureCfg(
        id="puppy",
        label="puppy",
        phrase="a floppy-eared puppy",
        size=2,
        shy=1,
        sounds={"jingle", "whimper"},
        food_motivated=True,
        owner_kind="neighbor",
        tags={"puppy", "pet"},
    ),
}

HIDEOUTS = {
    "behind_macrame": Hideout(
        id="behind_macrame",
        label="behind the macrame",
        phrase="behind the hanging macrame cords",
        capacity=1,
        difficulty=2,
        tangled=True,
        shadow_text="the shadows behind the macrame looked deeper than they should have",
        reveal_text="two bright eyes blinked through the hanging knots",
        tags={"macrame", "tangled"},
    ),
    "yarn_basket": Hideout(
        id="yarn_basket",
        label="the yarn basket",
        phrase="inside the tall basket of yarn",
        capacity=1,
        difficulty=1,
        tangled=False,
        shadow_text="the basket of yarn looked still, but now and then something inside it gave a tiny twitch",
        reveal_text="a little nose poked out between the yarn balls",
        tags={"basket", "yarn"},
    ),
    "coat_cubby": Hideout(
        id="coat_cubby",
        label="the coat cubby",
        phrase="inside the low coat cubby",
        capacity=2,
        difficulty=2,
        tangled=False,
        shadow_text="the coat cubby was dark enough to look like a secret cave",
        reveal_text="a small face peeped out between scarves and mittens",
        tags={"cubby"},
    ),
}

RESPONSES = {
    "gentle_untangle": Response(
        id="gentle_untangle",
        sense=3,
        power=2,
        text="used careful fingers to loosen the knots one by one while speaking in a soft voice",
        qa_text="used careful fingers to loosen the knots while speaking softly",
        needs_tangled=True,
        tags={"untangle", "kindness"},
    ),
    "trail_of_treats": Response(
        id="trail_of_treats",
        sense=3,
        power=2,
        text="set a tiny trail of treats on the floor and waited quietly until the little animal hopped or padded out",
        qa_text="made a tiny trail of treats and waited quietly",
        needs_plain=True,
        requires_food=True,
        tags={"treats", "kindness"},
    ),
    "open_cubby": Response(
        id="open_cubby",
        sense=2,
        power=2,
        text="knelt down, opened the cubby all the way, and stepped back so the little animal had room to come out",
        qa_text="opened the cubby wide and gave the animal room to come out",
        needs_plain=True,
        only_hideout="coat_cubby",
        tags={"cubby", "space"},
    ),
    "call_grownup": Response(
        id="call_grownup",
        sense=3,
        power=3,
        text="called for a grown-up right away and stayed nearby so the scared little animal would not feel alone",
        qa_text="called for a grown-up right away and stayed nearby",
        works_any=True,
        tags={"grownup_help", "safety"},
    ),
    "grab_fast": Response(
        id="grab_fast",
        sense=1,
        power=1,
        text="reached in fast and grabbed",
        qa_text="grabbed too fast",
        works_any=True,
        tags={"rough"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Anna", "Maya", "Nora", "Rose"]
BOY_NAMES = ["Tom", "Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Noah", "Eli", "Theo"]
TRAITS = ["brave", "careful", "gentle", "thoughtful", "steady", "kind"]
FRIEND_TRAITS = ["nervous", "curious", "quiet", "careful", "hopeful"]


def clue_matches(clue: Clue, creature: CreatureCfg) -> bool:
    return clue.id in creature.sounds


def hideout_fits(creature: CreatureCfg, hideout: Hideout) -> bool:
    return creature.size <= hideout.capacity


def response_works(response: Response, creature: CreatureCfg, hideout: Hideout) -> bool:
    if response.sense < SENSE_MIN:
        return False
    if response.works_any:
        return response.power >= hideout.difficulty
    if response.only_hideout and response.only_hideout != hideout.id:
        return False
    if response.needs_tangled and not hideout.tangled:
        return False
    if response.needs_plain and hideout.tangled:
        return False
    if response.requires_food and not creature.food_motivated:
        return False
    return response.power >= hideout.difficulty


def valid_combos() -> list[tuple[str, str, str, str, str]]:
    combos: list[tuple[str, str, str, str, str]] = []
    for place_id, place in PLACES.items():
        for clue_id, clue in CLUES.items():
            for creature_id, creature in CREATURES.items():
                if not clue_matches(clue, creature):
                    continue
                for hideout_id, hideout in HIDEOUTS.items():
                    if hideout_id not in place.afford_hideouts:
                        continue
                    if not hideout_fits(creature, hideout):
                        continue
                    for response_id, response in RESPONSES.items():
                        if response_works(response, creature, hideout):
                            combos.append((place_id, clue_id, creature_id, hideout_id, response_id))
    return combos


@dataclass
class StoryParams:
    place: str
    clue: str
    creature: str
    hideout: str
    response: str
    hero: str
    hero_gender: str
    friend: str
    friend_gender: str
    trait: str
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


def describe_rejection(place: Place, clue: Clue, creature: CreatureCfg, hideout: Hideout) -> str:
    if hideout.id not in place.afford_hideouts:
        return (
            f"(No story: {place.label.capitalize()} does not have {hideout.label}, "
            f"so the mystery has nowhere sensible to happen there.)"
        )
    if not clue_matches(clue, creature):
        return (
            f"(No story: {clue.hear} does not fit a {creature.label} in this world. "
            f"Pick a clue the creature could really make.)"
        )
    if not hideout_fits(creature, hideout):
        return (
            f"(No story: a {creature.label} would not fit in {hideout.label}. "
            f"Pick a roomier hiding spot.)"
        )
    return "(No story: this combination does not make a plausible mystery.)"


def explain_response(response: Response, creature: CreatureCfg, hideout: Hideout) -> str:
    if response.sense < SENSE_MIN:
        return (
            f"(Refusing response '{response.id}': it is too rough for this world. "
            f"A mystery story here should solve the problem with kindness and care.)"
        )
    if not response_works(response, creature, hideout):
        return (
            f"(No story: response '{response.id}' does not fit a {creature.label} in {hideout.label}. "
            f"Pick a gentler or more suitable way to help.)"
        )
    return ""


def outcome_of(params: StoryParams) -> str:
    if params.response == "call_grownup":
        return "adult_help"
    return "direct_help"


def _pick_name(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def introduce(world: World, hero: Entity, friend: Entity, place: Place) -> None:
    world.say(
        f"After the busy part of the day was over, {hero.id} and {friend.id} stayed in "
        f"{place.scene}. On one wall hung {place.macrame_item}, and its knotted shadows "
        f"made the room feel full of tiny secrets."
    )
    world.say(
        f"{hero.id} liked secrets when they were kind ones. {friend.id} stayed close, "
        f"looking up at the macrame and then back at the quiet corners of the room."
    )


def hear_mystery(world: World, hero: Entity, friend: Entity, clue: Clue, hideout: Hideout) -> None:
    creature = world.get("creature")
    creature.meters["making_clue"] = 1.0
    propagate(world, narrate=False)
    world.say(
        f"Then they heard {clue.hear}. It came from {hideout.label}, and all at once "
        f"the room no longer felt merely quiet. It felt mysterious."
    )
    world.say(
        f'"Did you hear that?" {friend.id} whispered. {hideout.shadow_text.capitalize()}.'
    )


def choose_bravery(world: World, hero: Entity, friend: Entity) -> None:
    hero.memes["fear"] += 1
    hero.memes["bravery"] += 1
    friend.memes["fear"] += 1
    world.say(
        f"{hero.id}'s tummy fluttered for a moment. Still, {hero.pronoun()} took a slow breath, "
        f"remembered to be brave, and said, \"Let's look carefully. A scared sound might mean "
        f"someone needs help.\""
    )


def investigate(world: World, hero: Entity, friend: Entity, hideout: Hideout) -> None:
    hero.meters["near_hideout"] += 1
    friend.meters["near_hideout"] += 1
    world.say(
        f"Step by step, {hero.id} walked closer while {friend.id} came just behind. "
        f"The closer they got, the more the mystery stopped feeling spooky and started "
        f"feeling sad."
    )
    world.say(hideout.reveal_text.capitalize() + ".")


def discover(world: World, hero: Entity, creature_cfg: CreatureCfg, hideout: Hideout) -> None:
    creature = world.get("creature")
    creature.meters["found"] = 1.0
    if hideout.tangled:
        creature.meters["tangled"] = 1.0
    propagate(world, narrate=False)
    if hideout.tangled:
        world.say(
            f"It was {creature_cfg.phrase}, caught in the loose cords. The mystery was not a ghost at all. "
            f"It was a frightened little creature that needed patient hands."
        )
    else:
        world.say(
            f"It was {creature_cfg.phrase}, tucked inside and trembling. The mystery was not a monster at all. "
            f"It was just a little creature hiding where it hoped to feel safe."
        )
    world.facts["mystery_solved"] = True


def help_direct(world: World, hero: Entity, friend: Entity, response: Response, creature_cfg: CreatureCfg) -> None:
    creature = world.get("creature")
    creature.meters["helped"] = 1.0
    hero.memes["kindness"] += 1
    friend.memes["kindness"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{hero.id} knelt down and {response.text}. {friend.id} did not run away. "
        f"{friend.pronoun().capitalize()} stayed nearby and spoke in the gentlest voice {friend.pronoun()} could."
    )
    if creature_cfg.id == "rabbit":
        world.say("Soon the rabbit's nose stopped twitching so fast, and its body softened from a tight little ball into a calm one.")
    elif creature_cfg.id == "kitten":
        world.say("Soon the kitten gave one tiny mew instead of another frightened scratch, as if it understood that the children were there to help.")
    else:
        world.say("Soon the puppy's worried sound faded, and its tail gave one hopeful thump against the floor.")


def help_with_adult(world: World, hero: Entity, friend: Entity, response: Response, place: Place) -> None:
    creature = world.get("creature")
    adult = world.get("adult")
    hero.memes["kindness"] += 1
    hero.memes["bravery"] += 1
    friend.memes["trust"] += 1
    world.say(
        f"{hero.id} knew kindness sometimes meant asking for bigger hands. So {hero.pronoun()} {response.text}."
    )
    creature.meters["helped"] = 1.0
    propagate(world, narrate=False)
    world.say(
        f"Soon {adult.label} hurried over, saw the problem at once, and helped without any scolding. "
        f"{adult.pronoun('subject').capitalize()} thanked the children for listening closely and telling a grown-up quickly."
    )


def reunion(world: World, place: Place, creature_cfg: CreatureCfg) -> None:
    creature = world.get("creature")
    owner = world.get("owner")
    adult = world.get("adult")
    creature.memes["safe"] += 1
    owner.memes["relief"] += 1
    if creature_cfg.owner_kind == "child":
        world.say(
            f"A little while later, the owner came running back with wet eyes and a hopeful face. "
            f"When {owner.pronoun()} saw the {creature_cfg.label}, the whole mystery melted into relief."
        )
    else:
        world.say(
            f"A little while later, a worried neighbor came to {place.label} asking if anyone had seen a missing {creature_cfg.label}. "
            f"When the little animal was brought out safely, the worried face turned bright with relief."
        )
    world.say(
        f'The owner thanked {world.get("hero").id} and {world.get("friend").id} again and again. '
        f'Even {adult.label if adult.type != "grandpa" else adult.id} smiled and said, "Brave hearts listen carefully, and kind hands make mysteries smaller."'
    )


def close_story(world: World, hero: Entity, friend: Entity, place: Place) -> None:
    hero.memes["joy"] += 1
    friend.memes["joy"] += 1
    world.say(
        f"When the room grew quiet again, {place.macrame_item} did not look spooky anymore. "
        f"Its knots looked like a hundred little reminders that brave children can be gentle, too."
    )
    world.say(
        f"{hero.id} and {friend.id} looked at each other and smiled. The mystery had begun in shadows, "
        f"but it ended with kindness."
    )


def tell(
    place: Place,
    clue: Clue,
    creature_cfg: CreatureCfg,
    hideout: Hideout,
    response: Response,
    hero_name: str = "Lily",
    hero_gender: str = "girl",
    friend_name: str = "Tom",
    friend_gender: str = "boy",
    trait: str = "brave",
    friend_trait: str = "careful",
) -> World:
    world = World(place)
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_gender,
        label=hero_name,
        role="hero",
        traits=[trait],
    ))
    friend = world.add(Entity(
        id=friend_name,
        kind="character",
        type=friend_gender,
        label=friend_name,
        role="friend",
        traits=[friend_trait],
    ))
    adult = world.add(Entity(
        id=place.adult_label if place.adult_type != "grandpa" else "Grandpa",
        kind="character",
        type=place.adult_type,
        label=place.adult_label,
        role="adult",
    ))
    owner = world.add(Entity(
        id="Owner",
        kind="character",
        type="child" if creature_cfg.owner_kind == "child" else "grownup",
        label="the owner",
        role="owner",
    ))
    room = world.add(Entity(
        id="room",
        kind="thing",
        type="room",
        label=place.label,
    ))
    creature = world.add(Entity(
        id="creature",
        kind="thing",
        type=creature_cfg.id,
        label=creature_cfg.label,
        attrs={"cfg_id": creature_cfg.id},
    ))

    hero.memes["bravery"] = 1.0 if trait == "brave" else 0.5
    hero.memes["kindness"] = 1.0 if trait == "kind" else 0.5
    hero.memes["fear"] = 0.0
    friend.memes["fear"] = 0.0
    friend.memes["trust"] = 0.0
    creature.meters["hidden"] = 1.0
    creature.meters["making_clue"] = 0.0
    creature.meters["found"] = 0.0
    creature.meters["helped"] = 0.0
    creature.meters["tangled"] = 1.0 if hideout.tangled else 0.0
    creature.memes["fear"] = 0.0
    room.meters["mystery"] = 0.0
    world.facts["mystery_solved"] = False
    world.facts["owner_kind"] = creature_cfg.owner_kind

    introduce(world, hero, friend, place)

    world.para()
    hear_mystery(world, hero, friend, clue, hideout)
    choose_bravery(world, hero, friend)

    world.para()
    investigate(world, hero, friend, hideout)
    discover(world, hero, creature_cfg, hideout)

    world.para()
    if response.id == "call_grownup":
        help_with_adult(world, hero, friend, response, place)
        outcome = "adult_help"
    else:
        help_direct(world, hero, friend, response, creature_cfg)
        outcome = "direct_help"

    world.para()
    reunion(world, place, creature_cfg)
    close_story(world, hero, friend, place)

    world.facts.update(
        place=place,
        clue=clue,
        creature_cfg=creature_cfg,
        hideout=hideout,
        response=response,
        hero=hero,
        friend=friend,
        adult=adult,
        owner=owner,
        creature=creature,
        outcome=outcome,
        tangled=hideout.tangled,
        brave_choice=hero.memes["bravery"] >= THRESHOLD,
        kind_choice=hero.memes["kindness"] >= THRESHOLD,
    )
    return world


KNOWLEDGE = {
    "macrame": [
        (
            "What is macrame?",
            "Macrame is a way of making decorations by tying cords into knots. People use it to make hangings, plant holders, and other soft woven shapes.",
        )
    ],
    "mystery": [
        (
            "What is a mystery?",
            "A mystery is something you do not understand yet, so you look for clues to learn the truth. A good mystery becomes less scary when you notice what is really happening.",
        )
    ],
    "bravery": [
        (
            "What is bravery?",
            "Bravery means doing the right thing even when you feel a little afraid. It does not mean being wild or rough.",
        )
    ],
    "kindness": [
        (
            "What is kindness?",
            "Kindness means noticing that someone needs care and choosing gentle help. Kind hands and soft voices can make scared creatures feel safer.",
        )
    ],
    "kitten": [
        (
            "How should you help a scared kitten?",
            "Move slowly and speak softly so the kitten does not feel chased. If it is stuck or very frightened, get a grown-up to help.",
        )
    ],
    "rabbit": [
        (
            "Why do rabbits hide when they are scared?",
            "Rabbits are prey animals, so hiding can make them feel safer. A quiet place and a gentle helper can help them calm down.",
        )
    ],
    "puppy": [
        (
            "What should you do if you find a lost puppy?",
            "Stay calm and get help from a grown-up so the puppy can be returned safely. A lost puppy may be friendly, but it may also be frightened and confused.",
        )
    ],
    "grownup_help": [
        (
            "When should a child call a grown-up for help with an animal?",
            "A child should call a grown-up if an animal is stuck, hurt, tangled, or too frightened to come out. Asking for help is a brave choice.",
        )
    ],
    "untangle": [
        (
            "Why should knots be loosened gently?",
            "Gentle fingers keep the knots from pulling tighter and keep the animal from being hurt. Going slowly is often the kindest and safest way.",
        )
    ],
    "treats": [
        (
            "Why can treats help a shy animal come out?",
            "A tiny treat can make a hidden animal feel curious and safer. Waiting quietly matters too, because rushing can frighten it again.",
        )
    ],
    "cubby": [
        (
            "Why is giving an animal space helpful?",
            "A scared animal may come out more easily when it has room and does not feel trapped. Stepping back can be a kind way to help.",
        )
    ],
}
KNOWLEDGE_ORDER = [
    "macrame",
    "mystery",
    "bravery",
    "kindness",
    "kitten",
    "rabbit",
    "puppy",
    "grownup_help",
    "untangle",
    "treats",
    "cubby",
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    place = f["place"]
    clue = f["clue"]
    creature = f["creature_cfg"]
    response = f["response"]
    outcome = f["outcome"]
    hero = f["hero"]
    if outcome == "adult_help":
        return [
            'Write a short mystery story for a 3-to-5-year-old that includes the word "macrame" and shows bravery and kindness.',
            f"Tell a gentle mystery where {hero.id} hears {clue.hear} near {place.macrame_item}, discovers a hidden {creature.label}, and bravely calls a grown-up for help.",
            f'Write a child-facing mystery that begins with a spooky clue and ends by proving that kindness solves the mystery. Include the word "macrame".',
        ]
    return [
        'Write a short mystery story for a 3-to-5-year-old that includes the word "macrame" and shows bravery and kindness.',
        f"Tell a gentle mystery where {hero.id} hears {clue.hear} near {place.macrame_item}, discovers a hidden {creature.label}, and helps it with patient kindness.",
        f"Write a cozy mystery where a strange sound seems spooky at first, but brave and gentle children solve it in a caring way using {response.id.replace('_', ' ')}.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    place = f["place"]
    clue = f["clue"]
    creature = f["creature_cfg"]
    hideout = f["hideout"]
    response = f["response"]
    adult = f["adult"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id} and {friend.id} in {place.label}. They hear a strange clue and decide to find out what is really there.",
        ),
        (
            "What made the room feel mysterious?",
            f"The children heard {clue.hear} coming from {hideout.label}. Because they did not know the cause yet, the quiet room suddenly felt like a mystery.",
        ),
        (
            f"Why was {hero.id} brave?",
            f"{hero.id} felt a little scared, but still walked closer instead of running away. {hero.pronoun('subject').capitalize()} chose to look carefully because the strange sound might mean someone needed help.",
        ),
        (
            f"How did kindness help solve the mystery?",
            f"Kindness kept the children from acting rough or wild. Their gentle help made the hidden {creature.label} feel safe enough for the mystery to end.",
        ),
    ]
    if hideout.tangled:
        qa.append(
            (
                f"Why was the {creature.label} in trouble?",
                f"The {creature.label} was caught in the cords behind the macrame. That is why the clue sounded worried instead of playful.",
            )
        )
    else:
        qa.append(
            (
                f"Why was the {creature.label} hiding?",
                f"The {creature.label} had tucked itself into {hideout.label} because it was frightened. The mystery felt spooky at first, but really it was just a scared little animal hiding.",
            )
        )
    if outcome == "adult_help":
        qa.append(
            (
                f"Why did {hero.id} call {adult.label_word}?",
                f"{hero.id} understood that bravery does not always mean doing everything alone. Calling {adult.label_word} was the kind and safe choice because bigger hands were needed to help properly.",
            )
        )
    else:
        qa.append(
            (
                f"How did {hero.id} help the {creature.label}?",
                f"{hero.id} {response.qa_text}. The slow, gentle method worked because it matched what the frightened animal needed.",
            )
        )
    qa.append(
        (
            "How did the story end?",
            f"It ended with relief instead of fear. The mystery was solved, the {creature.label} was safe, and even the macrame looked friendly again.",
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"macrame", "mystery", "bravery", "kindness", f["creature_cfg"].id}
    tags |= set(f["response"].tags)
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
        if ent.traits:
            bits.append(f"traits={ent.traits}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v != ""}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:12} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
fits(C,H) :- creature_size(C,S), hideout_capacity(H,Ca), S <= Ca.
matches(C,Cl) :- creature_sound(C,Cl).
scenario(P,Cl,C,H) :- place(P), clue(Cl), creature(C), hideout(H),
                      affords(P,H), matches(C,Cl), fits(C,H).

sensible(R) :- response(R), sense(R,S), sense_min(M), S >= M.

works(R,C,H) :- response(R), works_any(R).
works(R,C,H) :- response(R), needs_tangled(R), tangled(H),
                not requires_food(R).
works(R,C,H) :- response(R), needs_tangled(R), tangled(H),
                requires_food(R), food_motivated(C).
works(R,C,H) :- response(R), needs_plain(R), plain(H),
                not only_hideout(R,_), not requires_food(R).
works(R,C,H) :- response(R), needs_plain(R), plain(H),
                not only_hideout(R,_), requires_food(R), food_motivated(C).
works(R,C,H) :- response(R), needs_plain(R), plain(H),
                only_hideout(R,H), not requires_food(R).
works(R,C,H) :- response(R), needs_plain(R), plain(H),
                only_hideout(R,H), requires_food(R), food_motivated(C).

valid(P,Cl,C,H,R) :- scenario(P,Cl,C,H), sensible(R),
                     hideout_difficulty(H,D), response_power(R,Po), Po >= D,
                     works(R,C,H).

outcome(adult_help) :- chosen_response(call_grownup).
outcome(direct_help) :- chosen_response(R), R != call_grownup.

#show valid/5.
#show sensible/1.
#show outcome/1.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        for hideout_id in sorted(place.afford_hideouts):
            lines.append(asp.fact("affords", place_id, hideout_id))
    for clue_id in CLUES:
        lines.append(asp.fact("clue", clue_id))
    for creature_id, creature in CREATURES.items():
        lines.append(asp.fact("creature", creature_id))
        lines.append(asp.fact("creature_size", creature_id, creature.size))
        if creature.food_motivated:
            lines.append(asp.fact("food_motivated", creature_id))
        for sound in sorted(creature.sounds):
            lines.append(asp.fact("creature_sound", creature_id, sound))
    for hideout_id, hideout in HIDEOUTS.items():
        lines.append(asp.fact("hideout", hideout_id))
        lines.append(asp.fact("hideout_capacity", hideout_id, hideout.capacity))
        lines.append(asp.fact("hideout_difficulty", hideout_id, hideout.difficulty))
        if hideout.tangled:
            lines.append(asp.fact("tangled", hideout_id))
        else:
            lines.append(asp.fact("plain", hideout_id))
    for response_id, response in RESPONSES.items():
        lines.append(asp.fact("response", response_id))
        lines.append(asp.fact("sense", response_id, response.sense))
        lines.append(asp.fact("response_power", response_id, response.power))
        if response.needs_tangled:
            lines.append(asp.fact("needs_tangled", response_id))
        if response.needs_plain:
            lines.append(asp.fact("needs_plain", response_id))
        if response.requires_food:
            lines.append(asp.fact("requires_food", response_id))
        if response.only_hideout:
            lines.append(asp.fact("only_hideout", response_id, response.only_hideout))
        if response.works_any:
            lines.append(asp.fact("works_any", response_id))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str = "") -> str:
    return f"{asp_facts()}\n{extra}\n{ASP_RULES}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join([
        asp.fact("chosen_response", params.response),
    ])
    model = asp.one_model(asp_program(extra))
    found = asp.atoms(model, "outcome")
    return found[0][0] if found else "?"


CURATED = [
    StoryParams(
        place="craft_room",
        clue="scratch",
        creature="kitten",
        hideout="behind_macrame",
        response="gentle_untangle",
        hero="Lily",
        hero_gender="girl",
        friend="Tom",
        friend_gender="boy",
        trait="brave",
        friend_trait="careful",
    ),
    StoryParams(
        place="library_nook",
        clue="sneeze",
        creature="rabbit",
        hideout="yarn_basket",
        response="trail_of_treats",
        hero="Mia",
        hero_gender="girl",
        friend="Ben",
        friend_gender="boy",
        trait="kind",
        friend_trait="quiet",
    ),
    StoryParams(
        place="porch",
        clue="jingle",
        creature="kitten",
        hideout="behind_macrame",
        response="call_grownup",
        hero="Sam",
        hero_gender="boy",
        friend="Nora",
        friend_gender="girl",
        trait="steady",
        friend_trait="hopeful",
    ),
    StoryParams(
        place="library_nook",
        clue="whimper",
        creature="puppy",
        hideout="coat_cubby",
        response="open_cubby",
        hero="Ella",
        hero_gender="girl",
        friend="Max",
        friend_gender="boy",
        trait="brave",
        friend_trait="curious",
    ),
    StoryParams(
        place="porch",
        clue="jingle",
        creature="puppy",
        hideout="coat_cubby",
        response="call_grownup",
        hero="Theo",
        hero_gender="boy",
        friend="Lucy",
        friend_gender="girl",
        trait="gentle",
        friend_trait="careful",
    ),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: a macrame mystery solved with bravery and kindness."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--creature", choices=CREATURES)
    ap.add_argument("--hideout", choices=HIDEOUTS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set")
    ap.add_argument("--trace", action="store_true", help="dump the world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible scenarios from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.clue and args.creature and args.hideout:
        place = PLACES[args.place]
        clue = CLUES[args.clue]
        creature = CREATURES[args.creature]
        hideout = HIDEOUTS[args.hideout]
        if not (
            args.hideout in place.afford_hideouts
            and clue_matches(clue, creature)
            and hideout_fits(creature, hideout)
        ):
            raise StoryError(describe_rejection(place, clue, creature, hideout))
    if args.response and args.creature and args.hideout:
        response = RESPONSES[args.response]
        creature = CREATURES[args.creature]
        hideout = HIDEOUTS[args.hideout]
        if not response_works(response, creature, hideout):
            raise StoryError(explain_response(response, creature, hideout))
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        dummy_creature = CREATURES[args.creature] if args.creature else next(iter(CREATURES.values()))
        dummy_hideout = HIDEOUTS[args.hideout] if args.hideout else next(iter(HIDEOUTS.values()))
        raise StoryError(explain_response(RESPONSES[args.response], dummy_creature, dummy_hideout))

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.clue is None or combo[1] == args.clue)
        and (args.creature is None or combo[2] == args.creature)
        and (args.hideout is None or combo[3] == args.hideout)
        and (args.response is None or combo[4] == args.response)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, clue_id, creature_id, hideout_id, response_id = rng.choice(sorted(combos))
    hero, hero_gender = _pick_name(rng)
    friend, friend_gender = _pick_name(rng, avoid=hero)
    trait = rng.choice(TRAITS)
    friend_trait = rng.choice(FRIEND_TRAITS)
    return StoryParams(
        place=place_id,
        clue=clue_id,
        creature=creature_id,
        hideout=hideout_id,
        response=response_id,
        hero=hero,
        hero_gender=hero_gender,
        friend=friend,
        friend_gender=friend_gender,
        trait=trait,
        friend_trait=friend_trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.clue not in CLUES:
        raise StoryError(f"(Unknown clue: {params.clue})")
    if params.creature not in CREATURES:
        raise StoryError(f"(Unknown creature: {params.creature})")
    if params.hideout not in HIDEOUTS:
        raise StoryError(f"(Unknown hideout: {params.hideout})")
    if params.response not in RESPONSES:
        raise StoryError(f"(Unknown response: {params.response})")

    place = PLACES[params.place]
    clue = CLUES[params.clue]
    creature = CREATURES[params.creature]
    hideout = HIDEOUTS[params.hideout]
    response = RESPONSES[params.response]

    if not (
        params.hideout in place.afford_hideouts
        and clue_matches(clue, creature)
        and hideout_fits(creature, hideout)
    ):
        raise StoryError(describe_rejection(place, clue, creature, hideout))
    if not response_works(response, creature, hideout):
        raise StoryError(explain_response(response, creature, hideout))

    world = tell(
        place=place,
        clue=clue,
        creature_cfg=creature,
        hideout=hideout,
        response=response,
        hero_name=params.hero,
        hero_gender=params.hero_gender,
        friend_name=params.friend,
        friend_gender=params.friend_gender,
        trait=params.trait,
        friend_trait=params.friend_trait,
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
        print(f"OK: ASP valid set matches Python ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if asp_valid - py_valid:
            print("  only in ASP:", sorted(asp_valid - py_valid))
        if py_valid - asp_valid:
            print("  only in Python:", sorted(py_valid - asp_valid))

    py_sens = {rid for rid, response in RESPONSES.items() if response.sense >= SENSE_MIN}
    asp_sens = set(asp_sensible())
    if py_sens == asp_sens:
        print(f"OK: sensible responses match ({sorted(py_sens)}).")
    else:
        rc = 1
        print("MISMATCH in sensible responses:")
        print("  python:", sorted(py_sens))
        print("  asp:   ", sorted(asp_sens))

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(30):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
        except StoryError:
            continue
        params.seed = seed
        cases.append(params)
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
            raise StoryError("(Smoke test failed: generated empty story.)")
        print("OK: smoke-tested normal generation.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

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
        print(f"{len(combos)} compatible (place, clue, creature, hideout, response) combos:\n")
        for place, clue, creature, hideout, response in combos:
            print(f"  {place:13} {clue:8} {creature:8} {hideout:15} {response}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        attempts = 0
        while len(samples) < args.n and attempts < max(args.n * 50, 50):
            seed = base_seed + attempts
            attempts += 1
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
            header = (
                f"### {p.hero} & {p.friend}: {p.creature} in {p.hideout} "
                f"at {p.place} ({p.response}, {outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
