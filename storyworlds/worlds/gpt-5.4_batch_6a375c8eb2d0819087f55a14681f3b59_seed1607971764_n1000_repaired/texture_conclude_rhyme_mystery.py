#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/texture_conclude_rhyme_mystery.py
============================================================

A standalone storyworld for a gentle mystery built from rhyme clues and texture.

Premise
-------
A small beloved item goes missing just before a happy moment. The hero first
suspects a friend, then discovers a rhyming clue about texture. By following
the clue to the right hiding place, the hero finds the missing item, learns the
friend was innocent, and can finally conclude what really happened.

This world models:
- physical state: item missing/found, searched places, paper clue, safe hiding
- emotional state: worry, suspicion, hope, relief, trust
- a reasonableness gate: only hiding spots that exist in the place and safely
  fit the item are allowed
- an inline ASP twin for the gate

Run it
------
python storyworlds/worlds/gpt-5.4/texture_conclude_rhyme_mystery.py
python storyworlds/worlds/gpt-5.4/texture_conclude_rhyme_mystery.py --all
python storyworlds/worlds/gpt-5.4/texture_conclude_rhyme_mystery.py --qa --json
python storyworlds/worlds/gpt-5.4/texture_conclude_rhyme_mystery.py --verify
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
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "teacher", "woman", "grandmother"}
        male = {"boy", "father", "man", "grandfather"}
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
            "teacher": "teacher",
            "grandmother": "grandma",
            "grandfather": "grandpa",
        }.get(self.type, self.type)
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
    event: str
    adult_pool: list[str]
    spots: set[str]
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
class MissingItem:
    id: str
    label: str
    phrase: str
    sound: str
    owner_use: str
    safe_spots: set[str]
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
    texture: str
    texture_line: str
    clue_a: str
    clue_b: str
    places: set[str]
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


def _r_missing_worry(world: World) -> list[str]:
    item = world.get("item")
    hero = world.get("hero")
    if item.meters["missing"] < THRESHOLD:
        return []
    sig = ("missing_worry",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["worry"] += 1
    return []


def _r_suspect_friend(world: World) -> list[str]:
    item = world.get("item")
    hero = world.get("hero")
    friend = world.get("friend")
    if item.meters["missing"] < THRESHOLD:
        return []
    if not world.facts.get("friend_was_nearby", False):
        return []
    sig = ("suspect_friend",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["suspicion"] += 1
    friend.memes["uneasy"] += 1
    return []


def _r_clue_changes_mood(world: World) -> list[str]:
    clue = world.get("clue")
    hero = world.get("hero")
    if clue.meters["read"] < THRESHOLD:
        return []
    sig = ("clue_changes_mood",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["hope"] += 1
    hero.memes["curiosity"] += 1
    return []


def _r_found_relief(world: World) -> list[str]:
    item = world.get("item")
    hero = world.get("hero")
    friend = world.get("friend")
    if item.meters["found"] < THRESHOLD:
        return []
    sig = ("found_relief",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    item.meters["missing"] = 0.0
    hero.memes["relief"] += 1
    friend.memes["relief"] += 1
    return []


def _r_conclude(world: World) -> list[str]:
    item = world.get("item")
    hero = world.get("hero")
    friend = world.get("friend")
    adult = world.get("adult")
    if item.meters["found"] < THRESHOLD:
        return []
    if not world.facts.get("planned_game", False):
        return []
    sig = ("conclude",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["trust"] += 1
    hero.memes["lesson"] += 1
    hero.memes["suspicion"] = 0.0
    friend.memes["ease"] += 1
    adult.memes["pride"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="missing_worry", tag="emotion", apply=_r_missing_worry),
    Rule(name="suspect_friend", tag="emotion", apply=_r_suspect_friend),
    Rule(name="clue_changes_mood", tag="emotion", apply=_r_clue_changes_mood),
    Rule(name="found_relief", tag="emotion", apply=_r_found_relief),
    Rule(name="conclude", tag="social", apply=_r_conclude),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            out = rule.apply(world)
            if out:
                produced.extend(out)
                changed = True
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def safe_combo(place_id: str, item_id: str, spot_id: str) -> bool:
    if place_id not in PLACES or item_id not in ITEMS or spot_id not in SPOTS:
        return False
    place = PLACES[place_id]
    item = ITEMS[item_id]
    spot = SPOTS[spot_id]
    return spot_id in place.spots and place_id in spot.places and spot_id in item.safe_spots


def valid_combos() -> list[tuple[str, str, str]]:
    out: list[tuple[str, str, str]] = []
    for place_id in sorted(PLACES):
        for item_id in sorted(ITEMS):
            for spot_id in sorted(SPOTS):
                if safe_combo(place_id, item_id, spot_id):
                    out.append((place_id, item_id, spot_id))
    return out


def clue_text(spot: Spot) -> str:
    return f'"{spot.clue_a}\n{spot.clue_b}"'


def introduce(world: World, hero: Entity, friend: Entity, place: Place, item: MissingItem) -> None:
    world.say(
        f"{hero.id} and {friend.id} were in {place.label}, where {place.opening}."
    )
    world.say(
        f"That day they were waiting for {place.event}, and {hero.id} kept close to "
        f"{item.phrase}. {item.sound.capitalize()} seemed to promise that something lovely was about to begin."
    )


def discover_missing(world: World, hero: Entity, friend: Entity, item: Entity, cfg: MissingItem) -> None:
    item.meters["missing"] = 1.0
    propagate(world, narrate=False)
    world.say(
        f"But when {hero.id} reached for {cfg.phrase}, it was gone."
    )
    world.say(
        f"{hero.id}'s chest gave a little jump. {hero.pronoun('possessive').capitalize()} special {cfg.label} was missing."
    )
    if hero.memes["suspicion"] >= THRESHOLD:
        world.say(
            f"{friend.id} had been near the shelf a moment before, so for one prickly second "
            f"{hero.id} wondered if {friend.pronoun()} had taken it."
        )


def find_clue(world: World, hero: Entity, spot: Spot) -> None:
    clue = world.get("clue")
    clue.meters["read"] = 1.0
    propagate(world, narrate=False)
    world.say(
        f"Then {hero.id} noticed a folded paper with a penciled rhyme."
    )
    world.say(
        f"{hero.pronoun('possessive').capitalize()} finger brushed the paper and the word texture stood out in {hero.pronoun('possessive')} mind."
    )
    world.say(clue_text(spot))


def search_spot(world: World, hero: Entity, item: Entity, item_cfg: MissingItem, spot_cfg: Spot) -> None:
    item.meters["searched"] += 1
    world.facts["searched_spot"] = spot_cfg.id
    world.say(
        f"{hero.id} whispered the lines again and looked for the {spot_cfg.texture} clue."
    )
    world.say(
        f"{hero.pronoun().capitalize()} padded over to {spot_cfg.phrase} and felt its {spot_cfg.texture} texture with careful fingertips."
    )
    item.meters["found"] = 1.0
    item.attrs["location"] = spot_cfg.label
    propagate(world, narrate=False)
    world.say(
        f"There, tucked safely inside, was {item_cfg.phrase}."
    )


def adult_explains(world: World, adult: Entity, hero: Entity, friend: Entity, place: Place, item_cfg: MissingItem, spot_cfg: Spot) -> None:
    world.say(
        f'Just then {adult.label_word} came back and smiled in surprise. '
        f'"You found it!" {adult.pronoun()} said.'
    )
    world.say(
        f'{adult.pronoun().capitalize()} had hidden the {item_cfg.label} in {spot_cfg.label} as a tiny rhyme game, '
        f'but had been called away before {adult.pronoun()} could explain it.'
    )
    world.say(
        f"{hero.id} could finally conclude that {friend.id} had not taken anything at all."
    )
    world.say(
        f"{friend.id}'s shoulders dropped, and then both children laughed at how spooky the little mystery had seemed."
    )


def ending(world: World, hero: Entity, friend: Entity, adult: Entity, place: Place, item_cfg: MissingItem) -> None:
    world.say(
        f"Soon {hero.id} was using the {item_cfg.label} for {place.event}, and the room felt bright again."
    )
    world.say(
        f"After that, whenever {hero.id} and {friend.id} wanted a mystery, they asked for a clue first and made up soft little rhymes of their own."
    )
    if hero.memes["lesson"] >= THRESHOLD:
        world.say(
            f"{hero.id} remembered to look for signs before blaming anyone, and that made the ending feel warm instead of cold."
        )


def tell(
    *,
    place: Place,
    item_cfg: MissingItem,
    spot_cfg: Spot,
    hero_name: str,
    hero_gender: str,
    friend_name: str,
    friend_gender: str,
    adult_type: str,
) -> World:
    world = World()
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender, role="hero"))
    friend = world.add(Entity(id=friend_name, kind="character", type=friend_gender, role="friend"))
    adult = world.add(Entity(id="Adult", kind="character", type=adult_type, role="adult", label="the grown-up"))
    item = world.add(Entity(id="item", type="item", label=item_cfg.label, role="missing_item"))
    clue = world.add(Entity(id="clue", type="paper", label="the rhyme clue", role="clue"))
    spot = world.add(
        Entity(
            id="spot",
            type="spot",
            label=spot_cfg.label,
            role="spot",
            attrs={"texture": spot_cfg.texture},
            tags=set(spot_cfg.tags),
        )
    )
    room = world.add(Entity(id="room", type="place", label=place.label, role="place"))

    hero.memes["care"] = 1.0
    friend.memes["friendliness"] = 1.0
    adult.memes["kindness"] = 1.0
    item.attrs["location"] = ""
    world.facts["friend_was_nearby"] = True
    world.facts["planned_game"] = True
    world.facts["place"] = place
    world.facts["item_cfg"] = item_cfg
    world.facts["spot_cfg"] = spot_cfg
    world.facts["hero"] = hero
    world.facts["friend"] = friend
    world.facts["adult"] = adult
    world.facts["item"] = item
    world.facts["room"] = room
    world.facts["clue_text"] = clue_text(spot_cfg)

    introduce(world, hero, friend, place, item_cfg)
    world.para()
    discover_missing(world, hero, friend, item, item_cfg)
    find_clue(world, hero, spot_cfg)
    world.para()
    search_spot(world, hero, item, item_cfg, spot_cfg)
    adult_explains(world, adult, hero, friend, place, item_cfg, spot_cfg)
    world.para()
    ending(world, hero, friend, adult, place, item_cfg)

    world.facts["found"] = item.meters["found"] >= THRESHOLD
    world.facts["concluded_innocence"] = hero.memes["lesson"] >= THRESHOLD
    world.facts["suspected_friend"] = True
    return world


PLACES = {
    "classroom": Place(
        id="classroom",
        label="the classroom",
        opening="sunlight lay in neat squares on the floor",
        event="the morning song",
        adult_pool=["teacher"],
        spots={"wicker_basket", "tin_box"},
        tags={"school"},
    ),
    "playroom": Place(
        id="playroom",
        label="the playroom",
        opening="pillows leaned against a small rug and dress-up capes hung from hooks",
        event="the puppet show",
        adult_pool=["mother", "father"],
        spots={"velvet_pouch", "tin_box"},
        tags={"home"},
    ),
    "porch": Place(
        id="porch",
        label="the porch",
        opening="boots lined the wall and the air smelled like warm wood",
        event="tea with cookies",
        adult_pool=["grandmother", "grandfather"],
        spots={"mitten_drawer", "wicker_basket"},
        tags={"home"},
    ),
}

ITEMS = {
    "bell": MissingItem(
        id="bell",
        label="bell",
        phrase="the little silver bell",
        sound="its small ring",
        owner_use="to start the song",
        safe_spots={"wicker_basket", "tin_box", "velvet_pouch"},
        tags={"bell", "sound"},
    ),
    "key": MissingItem(
        id="key",
        label="key",
        phrase="the shiny story key",
        sound="its soft clink",
        owner_use="to open the puppet chest",
        safe_spots={"tin_box", "velvet_pouch", "mitten_drawer"},
        tags={"key", "metal"},
    ),
    "ribbon": MissingItem(
        id="ribbon",
        label="ribbon",
        phrase="the star ribbon",
        sound="its silky swish",
        owner_use="to mark the winner's seat",
        safe_spots={"wicker_basket", "velvet_pouch", "mitten_drawer"},
        tags={"ribbon", "cloth"},
    ),
}

SPOTS = {
    "velvet_pouch": Spot(
        id="velvet_pouch",
        label="the velvet pouch",
        phrase="the velvet costume pouch by the capes",
        texture="soft",
        texture_line="soft",
        clue_a="Find what is missing where softness keeps,",
        clue_b="in velvet folds where costume treasure sleeps.",
        places={"playroom"},
        tags={"velvet", "soft"},
    ),
    "wicker_basket": Spot(
        id="wicker_basket",
        label="the wicker basket",
        phrase="the wicker basket by the books",
        texture="rough",
        texture_line="rough",
        clue_a="Follow the rough little ridges and trace,",
        clue_b="the woven round basket is the hiding place.",
        places={"classroom", "porch"},
        tags={"wicker", "rough"},
    ),
    "tin_box": Spot(
        id="tin_box",
        label="the tin box",
        phrase="the moon-bright tin box on the shelf",
        texture="smooth",
        texture_line="smooth",
        clue_a="Seek the smooth shine, cool and small,",
        clue_b="inside the tin box by the wall.",
        places={"classroom", "playroom"},
        tags={"tin", "smooth"},
    ),
    "mitten_drawer": Spot(
        id="mitten_drawer",
        label="the mitten drawer",
        phrase="the mitten drawer under the bench",
        texture="fuzzy",
        texture_line="fuzzy",
        clue_a="Where fuzzy wool in winter lies,",
        clue_b="your missing treasure waits in disguise.",
        places={"porch"},
        tags={"mittens", "fuzzy"},
    ),
}

GIRL_NAMES = ["Mina", "Lila", "Tessa", "Ruby", "Nora", "Ivy", "Cora", "Ella"]
BOY_NAMES = ["Oren", "Finn", "Milo", "Theo", "Jude", "Eli", "Noah", "Bram"]


@dataclass
class StoryParams:
    place: str
    item: str
    spot: str
    hero: str
    hero_gender: str
    friend: str
    friend_gender: str
    adult_type: str
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
    "texture": [
        (
            "What does texture mean?",
            "Texture means how something feels when you touch it. Something can feel soft, rough, smooth, or fuzzy."
        )
    ],
    "rhyme": [
        (
            "What is a rhyme?",
            "A rhyme is when words have matching end sounds, like wall and small. Rhymes can make clues easier to remember."
        )
    ],
    "mystery": [
        (
            "What is a mystery?",
            "A mystery is a problem with hidden facts that you have to figure out. You solve it by noticing clues and thinking carefully."
        )
    ],
    "velvet": [
        (
            "How does velvet usually feel?",
            "Velvet usually feels very soft and smooth to your fingers. That soft texture is why people use it for fancy cloth things."
        )
    ],
    "wicker": [
        (
            "What is wicker?",
            "Wicker is made by weaving thin pieces of wood or reed together. That is why a wicker basket feels bumpy and rough."
        )
    ],
    "tin": [
        (
            "How does a tin box feel?",
            "A tin box often feels hard and smooth. Metal can also feel cool when you touch it."
        )
    ],
    "mittens": [
        (
            "Why do mittens feel fuzzy?",
            "Mittens are often made from wool or soft yarn. The tiny fibers make them feel fuzzy and warm."
        )
    ],
    "bell": [
        (
            "Why does a bell make a ringing sound?",
            "A bell rings because metal shakes fast when it is tapped or swung. That shaking makes sound in the air."
        )
    ],
    "key": [
        (
            "What is a key for?",
            "A key is used to open a lock. The right shape helps it turn the lock safely."
        )
    ],
    "ribbon": [
        (
            "What does a ribbon feel like?",
            "A ribbon often feels smooth and light. Cloth ribbons can swish softly when they move."
        )
    ],
}
KNOWLEDGE_ORDER = ["texture", "rhyme", "mystery", "velvet", "wicker", "tin", "mittens", "bell", "key", "ribbon"]


def generation_prompts(world: World) -> list[str]:
    place = world.facts["place"]
    item_cfg = world.facts["item_cfg"]
    hero = world.facts["hero"]
    friend = world.facts["friend"]
    spot_cfg = world.facts["spot_cfg"]
    return [
        f'Write a gentle mystery for a 3-to-5-year-old that uses the words "texture" and "conclude" and includes a rhyming clue.',
        f"Tell a small mystery where {hero.id} first worries that {friend.id} took a missing {item_cfg.label}, then solves the puzzle by following a clue about {spot_cfg.texture} texture in {place.label}.",
        f"Write a child-facing story with rhyme, a missing {item_cfg.label}, and a happy ending where the hero learns to conclude carefully instead of guessing too fast.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    hero = world.facts["hero"]
    friend = world.facts["friend"]
    adult = world.facts["adult"]
    place = world.facts["place"]
    item_cfg = world.facts["item_cfg"]
    spot_cfg = world.facts["spot_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, {friend.id}, and {adult.label_word}. The mystery begins when {hero.id}'s special {item_cfg.label} goes missing in {place.label}."
        ),
        (
            f"Why did {hero.id} feel worried?",
            f"{hero.id} felt worried because the {item_cfg.label} disappeared right before {place.event}. For a moment {hero.pronoun()} did not know if it was lost, hidden, or taken."
        ),
        (
            f"Why did {hero.id} suspect {friend.id} at first?",
            f"{hero.id} suspected {friend.id} because {friend.pronoun()} had been near the shelf just before the {item_cfg.label} vanished. That quick guess came from worry, not from real proof."
        ),
        (
            "How did the clue help solve the mystery?",
            f"The clue used a rhyme to point toward {spot_cfg.phrase} and its {spot_cfg.texture} texture. That gave {hero.id} a careful way to search instead of only guessing."
        ),
        (
            f"Where was the missing {item_cfg.label}?",
            f"It was hidden in {spot_cfg.label}. {hero.id} found it there after following the rhyme and touching the place that matched the clue."
        ),
        (
            f"What did {hero.id} conclude at the end?",
            f"{hero.id} could conclude that {friend.id} had been innocent all along. {adult.label_word.capitalize()} had hidden the {item_cfg.label} as a rhyme game and simply forgot to explain it first."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    item_cfg = world.facts["item_cfg"]
    spot_cfg = world.facts["spot_cfg"]
    tags = {"texture", "rhyme", "mystery"} | set(item_cfg.tags) | set(spot_cfg.tags)
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
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
        bits: list[str] = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v or v == 0}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        lines.append(f"  {ent.id:8} ({ent.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="classroom",
        item="bell",
        spot="wicker_basket",
        hero="Mina",
        hero_gender="girl",
        friend="Oren",
        friend_gender="boy",
        adult_type="teacher",
    ),
    StoryParams(
        place="playroom",
        item="key",
        spot="velvet_pouch",
        hero="Ruby",
        hero_gender="girl",
        friend="Finn",
        friend_gender="boy",
        adult_type="mother",
    ),
    StoryParams(
        place="playroom",
        item="bell",
        spot="tin_box",
        hero="Theo",
        hero_gender="boy",
        friend="Lila",
        friend_gender="girl",
        adult_type="father",
    ),
    StoryParams(
        place="porch",
        item="ribbon",
        spot="mitten_drawer",
        hero="Nora",
        hero_gender="girl",
        friend="Milo",
        friend_gender="boy",
        adult_type="grandmother",
    ),
    StoryParams(
        place="porch",
        item="bell",
        spot="wicker_basket",
        hero="Eli",
        hero_gender="boy",
        friend="Cora",
        friend_gender="girl",
        adult_type="grandfather",
    ),
]


def explain_rejection(place_id: str, item_id: str, spot_id: str) -> str:
    if place_id not in PLACES:
        return f"(No story: unknown place '{place_id}'.)"
    if item_id not in ITEMS:
        return f"(No story: unknown item '{item_id}'.)"
    if spot_id not in SPOTS:
        return f"(No story: unknown spot '{spot_id}'.)"
    place = PLACES[place_id]
    item = ITEMS[item_id]
    spot = SPOTS[spot_id]
    if spot_id not in place.spots or place_id not in spot.places:
        return (
            f"(No story: {spot.label} is not a real hiding place in {place.label}. "
            f"Pick a spot that belongs in that place.)"
        )
    return (
        f"(No story: {item.phrase} is not safely hidden in {spot.label} in this world. "
        f"Pick a spot that fits the item and the clue honestly.)"
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Gentle mystery storyworld with rhyme clues and texture."
    )
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--item", choices=sorted(ITEMS))
    ap.add_argument("--spot", choices=sorted(SPOTS))
    ap.add_argument("--hero")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--friend")
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
    ap.add_argument("--adult", dest="adult_type", choices=["mother", "father", "teacher", "grandmother", "grandfather"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed")
    ap.add_argument("--all", action="store_true", help="render the curated set")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include Q&A")
    ap.add_argument("--json", action="store_true", help="emit JSON")
    ap.add_argument("--asp", action="store_true", help="list valid combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check Python/ASP parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.item and args.spot and not safe_combo(args.place, args.item, args.spot):
        raise StoryError(explain_rejection(args.place, args.item, args.spot))

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.item is None or combo[1] == args.item)
        and (args.spot is None or combo[2] == args.spot)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, item_id, spot_id = rng.choice(sorted(combos))
    place = PLACES[place_id]
    adult_type = args.adult_type or rng.choice(place.adult_pool)
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    friend_gender = args.friend_gender or rng.choice(["girl", "boy"])
    hero = args.hero or _pick_name(rng, hero_gender)
    friend = args.friend or _pick_name(rng, friend_gender, avoid=hero)

    return StoryParams(
        place=place_id,
        item=item_id,
        spot=spot_id,
        hero=hero,
        hero_gender=hero_gender,
        friend=friend,
        friend_gender=friend_gender,
        adult_type=adult_type,
    )


def generate(params: StoryParams) -> StorySample:
    if not safe_combo(params.place, params.item, params.spot):
        raise StoryError(explain_rejection(params.place, params.item, params.spot))
    if params.place not in PLACES or params.item not in ITEMS or params.spot not in SPOTS:
        raise StoryError("(No story: one or more parameters are unknown.)")
    if params.adult_type not in {"mother", "father", "teacher", "grandmother", "grandfather"}:
        raise StoryError(f"(No story: unknown adult type '{params.adult_type}').")
    world = tell(
        place=PLACES[params.place],
        item_cfg=ITEMS[params.item],
        spot_cfg=SPOTS[params.spot],
        hero_name=params.hero,
        hero_gender=params.hero_gender,
        friend_name=params.friend,
        friend_gender=params.friend_gender,
        adult_type=params.adult_type,
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


ASP_RULES = r"""
valid(P,I,S) :- place(P), item(I), spot(S), in_place(S,P), safe_for(S,I).
#show valid/3.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        for spot_id in sorted(place.spots):
            lines.append(asp.fact("offers", place_id, spot_id))
    for item_id, item in ITEMS.items():
        lines.append(asp.fact("item", item_id))
        for spot_id in sorted(item.safe_spots):
            lines.append(asp.fact("safe_for", spot_id, item_id))
    for spot_id, spot in SPOTS.items():
        lines.append(asp.fact("spot", spot_id))
        for place_id in sorted(spot.places):
            lines.append(asp.fact("in_place", spot_id, place_id))
    return "\n".join(lines)


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: gate matches valid_combos() ({len(python_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))

    try:
        sample = generate(CURATED[0])
        if not sample.story or "texture" not in sample.story.lower() or "conclude" not in sample.story.lower():
            raise StoryError("Smoke test story missing required seed words.")
        emit(sample, trace=False, qa=False, header="### smoke test")
        print("OK: smoke test generate/emit passed.")
    except Exception as err:  # pragma: no cover - verify path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    try:
        params = resolve_params(build_parser().parse_args([]), random.Random(0))
        params.seed = 0
        sample2 = generate(params)
        if not sample2.story:
            raise StoryError("Random resolved story was empty.")
        print("OK: default resolution smoke test passed.")
    except Exception as err:  # pragma: no cover - verify path
        rc = 1
        print(f"DEFAULT RESOLUTION FAILED: {err}")

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
        print(f"{len(combos)} valid (place, item, spot) combos:\n")
        for place_id, item_id, spot_id in combos:
            print(f"  {place_id:10} {item_id:8} {spot_id}")
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
            header = f"### {p.hero} and {p.friend}: {p.item} in {p.place} ({p.spot})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
