#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/vague_wipe_twist_bravery_animal_story.py
===================================================================

A standalone story world for a small animal tale shaped around a smudged clue,
a brave crossing, and a gentle twist.

Reference seed
--------------
Write a story that includes the words "vague" and "wipe", with the features
Twist and Bravery, in the style of an Animal Story.

This world turns that seed into a tiny simulated domain:

- a young animal finds a vague, rain-smeared clue
- the clue points toward a friend across some small obstacle
- the hero must choose a brave, sensible way to cross
- the ending turns on what the friend was really doing there:
  either a sweet surprise, or a real small problem that still ends safely

Run it
------
    python storyworlds/worlds/gpt-5.4/vague_wipe_twist_bravery_animal_story.py
    python storyworlds/worlds/gpt-5.4/vague_wipe_twist_bravery_animal_story.py --place pond --obstacle stream
    python storyworlds/worlds/gpt-5.4/vague_wipe_twist_bravery_animal_story.py --tool umbrella_leaf
    python storyworlds/worlds/gpt-5.4/vague_wipe_twist_bravery_animal_story.py --all
    python storyworlds/worlds/gpt-5.4/vague_wipe_twist_bravery_animal_story.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/vague_wipe_twist_bravery_animal_story.py --verify
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
BRAVE_ENOUGH = 2.0


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
        female = {"girl", "mother", "hen"}
        male = {"boy", "father"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
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
class Animal:
    id: str
    kind_name: str
    home: str
    snack: str
    tail_word: str
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
class Place:
    id: str
    label: str
    path: str
    weather: str
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
class Obstacle:
    id: str
    label: str
    fear_text: str
    arrival_text: str
    risk: str
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
class Tool:
    id: str
    label: str
    phrase: str
    method: str
    solves: set[str] = field(default_factory=set)
    wipe_style: str = ""
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
class Reveal:
    id: str
    clue_hint: str
    expectation: str
    ending_kind: str
    turn_text: str
    ending_image: str
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


def _r_worry_to_bravery(world: World) -> list[str]:
    hero = world.get("hero")
    if hero.memes["worry"] < THRESHOLD:
        return []
    sig = ("bravery", hero.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["bravery"] += 1
    return []


def _r_cross_success(world: World) -> list[str]:
    hero = world.get("hero")
    obstacle = world.get("obstacle")
    tool = world.get("tool")
    if hero.memes["bravery"] < BRAVE_ENOUGH:
        return []
    if tool.attrs.get("fits") != obstacle.id:
        return []
    sig = ("cross", obstacle.id, tool.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.meters["crossed"] += 1
    hero.meters["safe"] += 1
    return []


CAUSAL_RULES: list[Rule] = [
    Rule(name="worry_to_bravery", tag="emotional", apply=_r_worry_to_bravery),
    Rule(name="cross_success", tag="physical", apply=_r_cross_success),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            out = rule.apply(world)
            if out:
                changed = True
                produced.extend(out)
            elif any(sig[0] == rule.name for sig in world.fired):
                changed = changed or False
    if narrate:
        for line in produced:
            world.say(line)
    return produced


def compatible(place: Place, obstacle: Obstacle, tool: Tool) -> bool:
    return obstacle.id in place.affords and obstacle.id in tool.solves


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place_id, place in PLACES.items():
        for obstacle_id in sorted(place.affords):
            obstacle = OBSTACLES[obstacle_id]
            for tool_id, tool in TOOLS.items():
                if compatible(place, obstacle, tool):
                    combos.append((place_id, obstacle_id, tool_id))
    return sorted(combos)


def explain_rejection(place: Place, obstacle: Obstacle, tool: Tool) -> str:
    if obstacle.id not in place.affords:
        return (
            f"(No story: {place.label} does not have {obstacle.label}, so the hero "
            f"has no reason to use {tool.label} there.)"
        )
    return (
        f"(No story: {tool.label} is not a sensible way to get across {obstacle.label}. "
        f"Pick a tool that really helps with that obstacle.)"
    )


def predict_cross(world: World) -> dict:
    sim = world.copy()
    propagate(sim, narrate=False)
    hero = sim.get("hero")
    return {
        "crossed": hero.meters["crossed"] >= THRESHOLD,
        "bravery": hero.memes["bravery"],
    }


def introduce(world: World, hero: Entity, friend: Entity, animal: Animal, place: Place) -> None:
    hero.memes["calm"] += 1
    friend.memes["fondness"] += 1
    world.say(
        f"In {place.label}, {hero.id} the little {animal.kind_name} liked to follow "
        f"{place.path} and notice small things. {animal.home.capitalize()} stood nearby, "
        f"and the air smelled of {animal.snack} and {place.weather}."
    )
    world.say(
        f"{friend.id}, {hero.id}'s friend, had gone ahead that morning with a bright secret smile."
    )


def discover_clue(world: World, hero: Entity, reveal: Reveal) -> None:
    hero.memes["curiosity"] += 1
    hero.memes["worry"] += 1
    world.say(
        f"By a stump, {hero.id} found a leaf note spotted with rain and berry juice. "
        f"The writing looked vague at first, and only {reveal.clue_hint} could be made out."
    )


def wipe_clue(world: World, hero: Entity, tool: Tool, reveal: Reveal) -> None:
    hero.meters["clue_cleared"] += 1
    world.facts["clue_text"] = reveal.expectation
    world.say(
        f"{hero.id} used {tool.wipe_style} to wipe the wet smears away. "
        f"After that, the note seemed to say, \"{reveal.expectation}\""
    )


def decide(world: World, hero: Entity, obstacle: Obstacle) -> None:
    propagate(world, narrate=False)
    world.say(
        f"{hero.id}'s paws felt small for a moment. {obstacle.fear_text}, and the idea of "
        f"{obstacle.risk} made the path feel bigger than before."
    )
    world.say(
        f"But {hero.pronoun('possessive').capitalize()} worry turned into bravery, and {hero.pronoun()} "
        f"hurried on because a friend might need help."
    )


def cross(world: World, hero: Entity, obstacle: Obstacle, tool: Tool) -> None:
    pred = predict_cross(world)
    if not pred["crossed"]:
        raise StoryError(
            f"(No story: {tool.label} does not let the hero cross {obstacle.label} safely.)"
        )
    hero.attrs["location"] = "far_side"
    hero.memes["bravery"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{hero.id} took {tool.phrase} and {tool.method}. Soon {hero.pronoun()} was past "
        f"{obstacle.label}, with {obstacle.arrival_text} behind {hero.pronoun('object')}."
    )


def reveal_turn(world: World, hero: Entity, friend: Entity, reveal: Reveal) -> None:
    hero.memes["surprise"] += 1
    friend.memes["joy"] += 1
    if reveal.ending_kind == "twist":
        hero.memes["worry"] = 0.0
    else:
        hero.memes["relief"] += 1
    world.say(reveal.turn_text.replace("{hero}", hero.id).replace("{friend}", friend.id))


def ending(world: World, hero: Entity, friend: Entity, animal: Animal, reveal: Reveal) -> None:
    hero.memes["joy"] += 1
    hero.memes["relief"] += 1
    hero.memes["worry"] = 0.0
    world.say(
        reveal.ending_image.replace("{hero}", hero.id).replace("{friend}", friend.id)
    )
    world.say(
        f"As they walked home, {hero.id}'s steps felt lighter. Being brave had carried "
        f"{hero.pronoun('object')} through the frightening part and into something good."
    )
    if animal.tail_word:
        world.say(
            f"{hero.id}'s {animal.tail_word} gave a happy flick all the way back."
        )


def tell(
    animal: Animal,
    friend_animal: Animal,
    place: Place,
    obstacle: Obstacle,
    tool: Tool,
    reveal: Reveal,
    hero_name: str = "Moss",
    friend_name: str = "Pip",
) -> World:
    world = World(place)
    hero = world.add(
        Entity(
            id=hero_name,
            kind="character",
            type=animal.kind_name,
            label=hero_name,
            role="hero",
            attrs={"location": "near_side"},
        )
    )
    friend = world.add(
        Entity(
            id=friend_name,
            kind="character",
            type=friend_animal.kind_name,
            label=friend_name,
            role="friend",
            attrs={"location": "far_side"},
        )
    )
    obstacle_ent = world.add(
        Entity(
            id="obstacle",
            kind="thing",
            type="obstacle",
            label=obstacle.label,
            role="obstacle",
        )
    )
    tool_ent = world.add(
        Entity(
            id="tool",
            kind="thing",
            type="tool",
            label=tool.label,
            role="tool",
            attrs={"fits": next(iter(tool.solves)) if tool.solves else ""},
        )
    )
    tool_ent.attrs["fits"] = obstacle.id if obstacle.id in tool.solves else ""
    world.facts.update(
        animal=animal,
        friend_animal=friend_animal,
        place=place,
        obstacle_cfg=obstacle,
        tool_cfg=tool,
        reveal=reveal,
        hero=hero,
        friend=friend,
    )

    introduce(world, hero, friend, animal, place)
    world.para()
    discover_clue(world, hero, reveal)
    wipe_clue(world, hero, tool, reveal)
    decide(world, hero, obstacle)
    world.para()
    cross(world, hero, obstacle, tool)
    reveal_turn(world, hero, friend, reveal)
    world.para()
    ending(world, hero, friend, animal, reveal)

    world.facts["outcome"] = reveal.ending_kind
    world.facts["crossed"] = hero.meters["crossed"] >= THRESHOLD
    world.facts["brave"] = hero.memes["bravery"] >= BRAVE_ENOUGH
    return world


PLACES = {
    "meadow": Place(
        id="meadow",
        label="the ferny meadow",
        path="soft paths between buttercups",
        weather="cool rain",
        affords={"stream", "log"},
        tags={"meadow"},
    ),
    "pond": Place(
        id="pond",
        label="the silver pond edge",
        path="little muddy paths beside the reeds",
        weather="misty wind",
        affords={"stream", "brambles"},
        tags={"pond"},
    ),
    "grove": Place(
        id="grove",
        label="the hazel grove",
        path="curled roots under leaf shade",
        weather="sweet damp earth",
        affords={"log", "brambles"},
        tags={"grove"},
    ),
}

OBSTACLES = {
    "stream": Obstacle(
        id="stream",
        label="the chattery stream",
        fear_text="The water made quick bright sounds over the stones",
        arrival_text="the splashy water",
        risk="slipping into the cold current",
        tags={"stream"},
    ),
    "brambles": Obstacle(
        id="brambles",
        label="the prickly bramble patch",
        fear_text="The thorns hooked at every passing breeze",
        arrival_text="the whispering thorns",
        risk="getting snagged and scratched",
        tags={"brambles"},
    ),
    "log": Obstacle(
        id="log",
        label="the mossy fallen log",
        fear_text="The log sat over a dip in the ground like a narrow bridge",
        arrival_text="the wobbling log",
        risk="losing balance on the slick bark",
        tags={"log"},
    ),
}

TOOLS = {
    "stepping_stones": Tool(
        id="stepping_stones",
        label="stepping stones",
        phrase="the round stepping stones",
        method="placed each paw carefully from one stone to the next",
        solves={"stream"},
        wipe_style="the dry edge of a dock leaf",
        tags={"stones"},
    ),
    "umbrella_leaf": Tool(
        id="umbrella_leaf",
        label="a broad umbrella leaf",
        phrase="the broad umbrella leaf",
        method="held it in front and pushed a safe little tunnel through the thorns",
        solves={"brambles"},
        wipe_style="the smooth clean side of the leaf",
        tags={"leaf"},
    ),
    "balance_stick": Tool(
        id="balance_stick",
        label="a straight balance stick",
        phrase="the straight balance stick",
        method="stretched it wide and padded slowly along the bark",
        solves={"log"},
        wipe_style="a corner of moss wrapped around the stick",
        tags={"stick"},
    ),
}

REVEALS = {
    "lanterns": Reveal(
        id="lanterns",
        clue_hint="the words help and hill",
        expectation="Help near the hill!",
        ending_kind="twist",
        turn_text=(
            "On the other side, {hero} stopped short. There was no emergency at all. "
            "{friend} had hung dew-bright lantern shells in a ring and laughed, "
            "\"I wrote, 'Come help with the hill surprise,' but the rain swallowed the middle!\""
        ),
        ending_image=(
            "{hero} laughed then, and together {hero} and {friend} lit the tiny lanterns "
            "until the damp grass shone like stars."
        ),
        tags={"lantern"},
    ),
    "berry_cake": Reveal(
        id="berry_cake",
        clue_hint="the words come and hollow",
        expectation="Come to the hollow fast!",
        ending_kind="twist",
        turn_text=(
            "{hero} hurried into the hollow and blinked. {friend} was safe beside a flat stone, "
            "patting berries into a little cake. \"Oh!\" said {friend}. "
            "\"I meant fast before the cream fern droops, not because I was in danger.\""
        ),
        ending_image=(
            "Soon {hero} and {friend} were sharing berry cake from acorn caps, and the worry "
            "melted away like rain drying on a leaf."
        ),
        tags={"berries"},
    ),
    "stuck_kite": Reveal(
        id="stuck_kite",
        clue_hint="the words help and tree",
        expectation="Help by the tree!",
        ending_kind="rescue",
        turn_text=(
            "This time the worry was true, though smaller than {hero} had feared. "
            "{friend}'s paper kite was tangled low in a bush, and {friend} said, "
            "\"I was safe, but I really did need another pair of paws.\""
        ),
        ending_image=(
            "{hero} and {friend} eased the kite free together, and when it rose at last, "
            "it tugged a bright tail across the clearing."
        ),
        tags={"kite"},
    ),
}

ANIMALS = {
    "rabbit": Animal(
        id="rabbit",
        kind_name="rabbit",
        home="a mossy burrow",
        snack="clover",
        tail_word="tail",
        tags={"rabbit"},
    ),
    "squirrel": Animal(
        id="squirrel",
        kind_name="squirrel",
        home="an oak nook",
        snack="hazelnuts",
        tail_word="tail",
        tags={"squirrel"},
    ),
    "hedgehog": Animal(
        id="hedgehog",
        kind_name="hedgehog",
        home="a leaf nest",
        snack="apples",
        tail_word="back",
        tags={"hedgehog"},
    ),
    "mouse": Animal(
        id="mouse",
        kind_name="mouse",
        home="a tiny seed house",
        snack="grain",
        tail_word="tail",
        tags={"mouse"},
    ),
}

NAMES = {
    "rabbit": ["Moss", "Poppy", "Clover", "Tumble"],
    "squirrel": ["Pip", "Hazel", "Nutkin", "Bramble"],
    "hedgehog": ["Nib", "Pine", "Pebble", "Thimble"],
    "mouse": ["Pip", "Midge", "Whisk", "Seed"],
}


@dataclass
class StoryParams:
    animal: str
    friend_animal: str
    place: str
    obstacle: str
    tool: str
    reveal: str
    hero_name: str
    friend_name: str
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
    "stream": [
        (
            "Why can a small stream feel scary to a little animal?",
            "Even a shallow stream can push hard against tiny paws. Wet stones can also be slippery, so crossing carefully matters."
        )
    ],
    "brambles": [
        (
            "What are brambles?",
            "Brambles are thorny plants with long bendy stems. Their prickles can snag fur and scratch skin."
        )
    ],
    "log": [
        (
            "Why can a fallen log be hard to walk across?",
            "A log can be round, wet, and wobbly. That makes balancing on it trickier than walking on flat ground."
        )
    ],
    "leaf": [
        (
            "How can a big leaf help a small animal?",
            "A broad leaf can shield a little body from pokes and drips. It can also be used gently, like a tiny cover or cloth."
        )
    ],
    "stones": [
        (
            "What do stepping stones do?",
            "Stepping stones give you dry places to put your feet. They help you cross water without walking straight through it."
        )
    ],
    "stick": [
        (
            "Why does a balance stick help?",
            "A stick stretched wide helps a body stay steady. It makes it easier to feel where your balance is."
        )
    ],
    "lantern": [
        (
            "Why do surprises sometimes feel scary before they are explained?",
            "When you do not know what is happening, your mind may guess something worse. Clear words often make a surprise feel kind instead of frightening."
        )
    ],
    "berries": [
        (
            "Why can rain make writing hard to read?",
            "Water can blur ink or berry juice and smear the letters together. Then the message may look vague until it is cleaned."
        )
    ],
    "kite": [
        (
            "Why is asking a friend for help a good idea?",
            "Some jobs are easier with two sets of paws. Asking for help is wise, not weak."
        )
    ],
}
KNOWLEDGE_ORDER = ["stream", "brambles", "log", "stones", "leaf", "stick", "lantern", "berries", "kite"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    animal = f["animal"]
    place = f["place"]
    obstacle = f["obstacle_cfg"]
    reveal = f["reveal"]
    return [
        f'Write a short animal story for a 3-to-5-year-old that includes the words "vague" and "wipe".',
        f"Tell a gentle story about {hero.id} the little {animal.kind_name}, who finds a vague note in {place.label} and bravely crosses {obstacle.label}.",
        f"Write an animal story with bravery and a twist ending, where a scary-looking clue turns out to mean {reveal.id.replace('_', ' ')}.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    animal = f["animal"]
    place = f["place"]
    obstacle = f["obstacle_cfg"]
    tool = f["tool_cfg"]
    reveal = f["reveal"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, a little {animal.kind_name}, and {friend.id}, {hero.id}'s friend. The story begins with {hero.id} alone in {place.label}, trying to understand a smeared note."
        ),
        (
            "Why did the note seem confusing at first?",
            f"The writing was wet and smeared with berry juice, so it looked vague at first. {hero.id} had to wipe the note clean before the message could be guessed."
        ),
        (
            f"Why was {hero.id} brave?",
            f"{hero.id} thought a friend might need help, even though {obstacle.label} looked frightening. {hero.pronoun('subject').capitalize()} kept going because kindness mattered more than staying comfortable."
        ),
        (
            f"How did {hero.id} get across {obstacle.label}?",
            f"{hero.pronoun('subject').capitalize()} used {tool.phrase} and {tool.method}. That method fit the obstacle, so it helped {hero.pronoun('object')} cross safely."
        ),
    ]
    if reveal.ending_kind == "twist":
        qa.append(
            (
                "What was the twist at the end?",
                f"The note made {hero.id} expect trouble, but {friend.id} was safe all along. The real surprise was {reveal.id.replace('_', ' ')}, so the scary feeling turned into delight."
            )
        )
    else:
        qa.append(
            (
                "Was there really a problem at the end?",
                f"Yes, but it was a small one. {friend.id} was safe, and the real trouble was only {reveal.id.replace('_', ' ')}, which the two friends could fix together."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["obstacle_cfg"].tags) | set(f["tool_cfg"].tags) | set(f["reveal"].tags)
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
        lines.append(f"  {ent.id:10} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(sig[0] for sig in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        animal="rabbit",
        friend_animal="squirrel",
        place="meadow",
        obstacle="stream",
        tool="stepping_stones",
        reveal="lanterns",
        hero_name="Moss",
        friend_name="Hazel",
    ),
    StoryParams(
        animal="mouse",
        friend_animal="hedgehog",
        place="pond",
        obstacle="brambles",
        tool="umbrella_leaf",
        reveal="berry_cake",
        hero_name="Midge",
        friend_name="Pebble",
    ),
    StoryParams(
        animal="squirrel",
        friend_animal="rabbit",
        place="grove",
        obstacle="log",
        tool="balance_stick",
        reveal="stuck_kite",
        hero_name="Pip",
        friend_name="Clover",
    ),
]


ASP_RULES = r"""
valid(P,O,T) :- place(P), obstacle(O), tool(T), affords(P,O), solves(T,O).

twist_reveal(R) :- reveal(R), ending_kind(R,twist).
rescue_reveal(R) :- reveal(R), ending_kind(R,rescue).

outcome(twist) :- chosen_reveal(R), twist_reveal(R).
outcome(rescue) :- chosen_reveal(R), rescue_reveal(R).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        for obstacle_id in sorted(place.affords):
            lines.append(asp.fact("affords", place_id, obstacle_id))
    for obstacle_id in OBSTACLES:
        lines.append(asp.fact("obstacle", obstacle_id))
    for tool_id, tool in TOOLS.items():
        lines.append(asp.fact("tool", tool_id))
        for obstacle_id in sorted(tool.solves):
            lines.append(asp.fact("solves", tool_id, obstacle_id))
    for reveal_id, reveal in REVEALS.items():
        lines.append(asp.fact("reveal", reveal_id))
        lines.append(asp.fact("ending_kind", reveal_id, reveal.ending_kind))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = asp.fact("chosen_reveal", params.reveal)
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    outs = asp.atoms(model, "outcome")
    return outs[0][0] if outs else "?"


def outcome_of(params: StoryParams) -> str:
    if params.reveal not in REVEALS:
        raise StoryError(f"(No story: unknown reveal '{params.reveal}'.)")
    return REVEALS[params.reveal].ending_kind


def asp_verify() -> int:
    rc = 0
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: valid combo gate matches ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(30):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(params)

    bad = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcome cases differ.")

    try:
        smoke = generate(cases[0])
        if not smoke.story.strip():
            raise StoryError("(Smoke test failed: generated empty story.)")
        print("OK: smoke test generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Animal story world: a vague clue, a brave crossing, and a gentle twist."
    )
    ap.add_argument("--animal", choices=ANIMALS)
    ap.add_argument("--friend-animal", choices=ANIMALS)
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--obstacle", choices=OBSTACLES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--reveal", choices=REVEALS)
    ap.add_argument("--hero-name")
    ap.add_argument("--friend-name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible (place, obstacle, tool) combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, animal_id: str, avoid: str = "") -> str:
    pool = [n for n in NAMES[animal_id] if n != avoid]
    return rng.choice(pool)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.obstacle and args.tool:
        place = PLACES[args.place]
        obstacle = OBSTACLES[args.obstacle]
        tool = TOOLS[args.tool]
        if not compatible(place, obstacle, tool):
            raise StoryError(explain_rejection(place, obstacle, tool))

    combos = [
        combo
        for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.obstacle is None or combo[1] == args.obstacle)
        and (args.tool is None or combo[2] == args.tool)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, obstacle_id, tool_id = rng.choice(sorted(combos))
    animal_id = args.animal or rng.choice(sorted(ANIMALS))
    friend_animal_id = args.friend_animal or rng.choice(sorted(ANIMALS))
    reveal_id = args.reveal or rng.choice(sorted(REVEALS))
    hero_name = args.hero_name or _pick_name(rng, animal_id)
    friend_name = args.friend_name or _pick_name(rng, friend_animal_id, avoid=hero_name)

    return StoryParams(
        animal=animal_id,
        friend_animal=friend_animal_id,
        place=place_id,
        obstacle=obstacle_id,
        tool=tool_id,
        reveal=reveal_id,
        hero_name=hero_name,
        friend_name=friend_name,
    )


def generate(params: StoryParams) -> StorySample:
    missing = [
        name
        for name, registry in (
            ("animal", ANIMALS),
            ("friend_animal", ANIMALS),
            ("place", PLACES),
            ("obstacle", OBSTACLES),
            ("tool", TOOLS),
            ("reveal", REVEALS),
        )
        if getattr(params, name) not in registry
    ]
    if missing:
        raise StoryError(f"(No story: invalid parameter value for {', '.join(missing)}.)")

    place = PLACES[params.place]
    obstacle = OBSTACLES[params.obstacle]
    tool = TOOLS[params.tool]
    if not compatible(place, obstacle, tool):
        raise StoryError(explain_rejection(place, obstacle, tool))

    world = tell(
        animal=ANIMALS[params.animal],
        friend_animal=ANIMALS[params.friend_animal],
        place=place,
        obstacle=obstacle,
        tool=tool,
        reveal=REVEALS[params.reveal],
        hero_name=params.hero_name,
        friend_name=params.friend_name,
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
        print(f"{len(combos)} compatible (place, obstacle, tool) combos:\n")
        for place, obstacle, tool in combos:
            print(f"  {place:8} {obstacle:9} {tool}")
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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero_name}: {p.obstacle} at {p.place} with {p.tool} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
