#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/retrieve_conductor_earth_sound_effects_friendship_foreshadowing.py
================================================================================================

A standalone story world for a tiny nursery-rhyme-like domain:

Two friends make a little band. One child is the conductor. During their music,
a precious music thing tumbles into soft earth. A clue about the earth appears
early (foreshadowing), the friends try to retrieve the lost thing with a chosen
tool, and either they lift it out together or a nearby grown-up helper joins in.
The ending proves what changed: the friends play on more gently, sharing the
music and remembering to ask for help.

Run it
------
    python storyworlds/worlds/gpt-5.4/retrieve_conductor_earth_sound_effects_friendship_foreshadowing.py
    python storyworlds/worlds/gpt-5.4/retrieve_conductor_earth_sound_effects_friendship_foreshadowing.py --place garden --spot pumpkin_patch --tool spoon
    python storyworlds/worlds/gpt-5.4/retrieve_conductor_earth_sound_effects_friendship_foreshadowing.py --tool bare_hands
    python storyworlds/worlds/gpt-5.4/retrieve_conductor_earth_sound_effects_friendship_foreshadowing.py --all
    python storyworlds/worlds/gpt-5.4/retrieve_conductor_earth_sound_effects_friendship_foreshadowing.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/retrieve_conductor_earth_sound_effects_friendship_foreshadowing.py --verify
"""

from __future__ import annotations

import argparse
import contextlib
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
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "teacher"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad", "teacher": "teacher", "gardener": "gardener"}.get(
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
class Place:
    id: str
    label: str
    helper_type: str
    afford_spots: set[str] = field(default_factory=set)
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
class Music:
    id: str
    game_name: str
    beat: str
    call: str
    close: str
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
class LostItem:
    id: str
    label: str
    phrase: str
    sound: str
    hold: str
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
    depth_word: str
    difficulty: int
    foreshadow: str
    fall_text: str
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
    sense: int
    power: int
    swish: str
    good_text: str
    fail_text: str
    qa_text: str
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

    def children(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"leader", "friend"}]

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


def _r_loss_worry(world: World) -> list[str]:
    item = world.get("item")
    if item.meters["lost"] < THRESHOLD:
        return []
    sig = ("loss_worry",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    for child in world.children():
        child.memes["worry"] += 1
    return ["__lost__"]


def _r_buried_care(world: World) -> list[str]:
    item = world.get("item")
    if item.meters["buried"] < THRESHOLD:
        return []
    sig = ("buried_care",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    world.get("friend").memes["care"] += 1
    world.get("place").meters["disturbed"] += 1
    return ["__buried__"]


def _r_found_relief(world: World) -> list[str]:
    item = world.get("item")
    if item.meters["found"] < THRESHOLD:
        return []
    if world.get("leader").memes["teamwork"] < THRESHOLD or world.get("friend").memes["teamwork"] < THRESHOLD:
        return []
    sig = ("found_relief",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    for child in world.children():
        child.memes["relief"] += 1
        child.memes["joy"] += 1
        child.memes["friendship"] += 1
    return ["__found__"]


CAUSAL_RULES = [
    Rule(name="loss_worry", tag="emotion", apply=_r_loss_worry),
    Rule(name="buried_care", tag="emotion", apply=_r_buried_care),
    Rule(name="found_relief", tag="emotion", apply=_r_found_relief),
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


def sensible_tools() -> list[Tool]:
    return [tool for tool in TOOLS.values() if tool.sense >= SENSE_MIN]


def valid_combos() -> list[tuple[str, str, str, str, str]]:
    combos: list[tuple[str, str, str, str, str]] = []
    for place_id, place in PLACES.items():
        for music_id in MUSICS:
            for item_id in ITEMS:
                for spot_id in sorted(place.afford_spots):
                    for tool in sensible_tools():
                        combos.append((place_id, music_id, item_id, spot_id, tool.id))
    return combos


def retrieval_outcome(spot: Spot, tool: Tool) -> str:
    return "together" if tool.power >= spot.difficulty else "helper"


def predict_retrieval(world: World, spot_id: str, tool_id: str) -> dict:
    sim = world.copy()
    spot = SPOTS[spot_id]
    tool = TOOLS[tool_id]
    return {
        "depth": spot.depth_word,
        "difficulty": spot.difficulty,
        "outcome": retrieval_outcome(spot, tool),
        "needs_helper": retrieval_outcome(spot, tool) == "helper",
    }


def setup_play(world: World, leader: Entity, friend: Entity, music: Music, item: LostItem) -> None:
    leader.memes["joy"] += 1
    friend.memes["joy"] += 1
    world.say(
        f"{leader.id} and {friend.id} were little friends in {world.place.label}. "
        f"{world.place.opening}"
    )
    world.say(
        f'{leader.id} was the conductor of their {music.game_name}, and {friend.id} kept the beat: '
        f'"{music.beat}"'
    )
    world.say(
        f"{leader.id} waved {item.hold} high and sang, {music.call}"
    )


def foreshadow(world: World, friend: Entity, spot: Spot) -> None:
    friend.memes["care"] += 1
    world.say(
        f"Near them, {spot.foreshadow} {friend.id} noticed it, though the game still skipped along."
    )


def tumble(world: World, leader: Entity, friend: Entity, item: LostItem, spot: Spot) -> None:
    item_ent = world.get("item")
    item_ent.meters["lost"] += 1
    item_ent.meters["buried"] += 1
    item_ent.attrs["spot"] = spot.id
    propagate(world, narrate=False)
    world.say(
        f"Then came a twirl, a hop, a little surprise — {item.sound}! "
        f"{item.phrase} slipped from {leader.id}'s hand and {spot.fall_text}"
    )
    if friend.memes["worry"] >= THRESHOLD or leader.memes["worry"] >= THRESHOLD:
        world.say(
            f'{leader.id} gasped. "Oh dear! How shall we retrieve it from the earth?"'
        )


def plan(world: World, leader: Entity, friend: Entity, helper: Entity, spot: Spot, tool: Tool) -> None:
    pred = predict_retrieval(world, spot.id, tool.id)
    world.facts["predicted_outcome"] = pred["outcome"]
    world.facts["predicted_depth"] = pred["depth"]
    if pred["needs_helper"]:
        world.say(
            f'{friend.id} knelt beside the {spot.label}. "The earth is {spot.depth_word}," '
            f'{friend.pronoun()} said softly. "We can try with {tool.phrase}, and if it is still tucked too deep, '
            f'we will ask the {helper.label_word}."'
        )
    else:
        world.say(
            f'{friend.id} knelt beside the {spot.label}. "The earth is {spot.depth_word}," '
            f'{friend.pronoun()} said softly. "Let us try {tool.phrase} together."'
        )


def try_retrieve(world: World, leader: Entity, friend: Entity, item: LostItem, spot: Spot, tool: Tool) -> None:
    leader.memes["teamwork"] += 1
    friend.memes["teamwork"] += 1
    world.say(
        f"So side by side they bent down low — {tool.swish} — and {tool.good_text if retrieval_outcome(spot, tool) == 'together' else tool.fail_text}"
    )
    if retrieval_outcome(spot, tool) == "together":
        item_ent = world.get("item")
        item_ent.meters["lost"] = 0.0
        item_ent.meters["buried"] = 0.0
        item_ent.meters["found"] += 1
        propagate(world, narrate=False)


def helper_retrieves(world: World, helper: Entity, item: LostItem, spot: Spot, tool: Tool) -> None:
    helper.memes["care"] += 1
    item_ent = world.get("item")
    item_ent.meters["lost"] = 0.0
    item_ent.meters["buried"] = 0.0
    item_ent.meters["found"] += 1
    propagate(world, narrate=False)
    who = helper.label_word.capitalize()
    world.say(
        f"{who} came with a patient smile, looked at the {spot.label}, and used a steadier hand. "
        f"In one careful lift, {helper.pronoun()} brought {item.phrase} back out of the earth."
    )


def ending(world: World, leader: Entity, friend: Entity, helper: Entity, music: Music, item: LostItem, outcome: str) -> None:
    if outcome == "helper":
        world.say(
            f'"Thank you," said {leader.id} and {friend.id} together. Their hands found each other first, '
            f"and that was the finest part."
        )
    else:
        world.say(
            f'{friend.id} brushed the crumbs of earth away, and {leader.id} smiled so wide that worry could not stay.'
        )
    leader.memes["gentle"] += 1
    friend.memes["gentle"] += 1
    world.say(
        f"Soon the little band began again — {music.close} — only now the conductor stepped more gently, "
        f"and the two friends kept close as clover."
    )
    world.say(
        f"Their music was sweeter for it, because friendship had helped them retrieve not only {item.label}, "
        f"but also their cheer."
    )


def tell(
    place: Place,
    music: Music,
    item_cfg: LostItem,
    spot: Spot,
    tool: Tool,
    leader_name: str = "Lina",
    leader_gender: str = "girl",
    friend_name: str = "Toby",
    friend_gender: str = "boy",
    helper_type: str = "gardener",
) -> World:
    world = World(place)

    leader = world.add(
        Entity(
            id=leader_name,
            kind="character",
            type=leader_gender,
            label=leader_name,
            role="leader",
            traits=["bright", "musical"],
            attrs={},
        )
    )
    friend = world.add(
        Entity(
            id=friend_name,
            kind="character",
            type=friend_gender,
            label=friend_name,
            role="friend",
            traits=["kind", "steady"],
            attrs={},
        )
    )
    helper = world.add(
        Entity(
            id="Helper",
            kind="character",
            type=helper_type,
            label="the helper",
            role="helper",
            traits=["patient"],
            attrs={},
        )
    )
    world.add(Entity(id="place", kind="thing", type="place", label=place.label, role="place", attrs={}))
    world.add(
        Entity(
            id="item",
            kind="thing",
            type="music_item",
            label=item_cfg.label,
            role="item",
            attrs={"spot": ""},
        )
    )

    world.facts.update(
        place=place,
        music=music,
        item_cfg=item_cfg,
        spot_cfg=spot,
        tool=tool,
        leader=leader,
        friend=friend,
        helper=helper,
        predicted_outcome="",
        predicted_depth="",
    )

    setup_play(world, leader, friend, music, item_cfg)
    foreshadow(world, friend, spot)

    world.para()
    tumble(world, leader, friend, item_cfg, spot)
    plan(world, leader, friend, helper, spot, tool)

    world.para()
    outcome = retrieval_outcome(spot, tool)
    try_retrieve(world, leader, friend, item_cfg, spot, tool)
    if outcome == "helper":
        helper_retrieves(world, helper, item_cfg, spot, tool)

    world.para()
    ending(world, leader, friend, helper, music, item_cfg, outcome)

    world.facts.update(
        outcome=outcome,
        retrieved=world.get("item").meters["found"] >= THRESHOLD,
        helper_used=outcome == "helper",
    )
    return world


PLACES = {
    "garden": Place(
        id="garden",
        label="the garden",
        helper_type="gardener",
        afford_spots={"marigold_bed", "pumpkin_patch"},
        opening="Bees hummed, leaves nodded, and the path made a tiny ring through the green.",
        tags={"earth", "garden"},
    ),
    "park": Place(
        id="park",
        label="the park",
        helper_type="gardener",
        afford_spots={"oak_root", "duck_bank"},
        opening="The swings whispered, the sparrows hopped, and the wind smelled of grass.",
        tags={"earth", "park"},
    ),
    "schoolyard": Place(
        id="schoolyard",
        label="the schoolyard",
        helper_type="teacher",
        afford_spots={"planter_box", "bean_patch"},
        opening="A bell had already rung once, and the sun made gold ladders on the ground.",
        tags={"earth", "school"},
    ),
}

MUSICS = {
    "parade": Music(
        id="parade",
        game_name="parade band",
        beat="tum-ta-tum, tum-ta-tum!",
        call='"March, little feet, and follow the tune!"',
        close="tum-ta-tum, bright and slow",
        tags={"music", "march"},
    ),
    "raindrop_song": Music(
        id="raindrop_song",
        game_name="raindrop song",
        beat="plink-plink, pat-a-ping!",
        call='"Raindrops ring and ribbons sing!"',
        close="plink-plink, soft and sweet",
        tags={"music", "rain_song"},
    ),
    "moon_march": Music(
        id="moon_march",
        game_name="moon march",
        beat="clink-clink, boom-a-boom!",
        call='"Step to the moon in the afternoon!"',
        close="clink-clink, under blue",
        tags={"music", "moon"},
    ),
}

ITEMS = {
    "baton": LostItem(
        id="baton",
        label="the baton",
        phrase="the little baton",
        sound="tap-tink",
        hold="a striped baton",
        tags={"conductor", "baton"},
    ),
    "bell": LostItem(
        id="bell",
        label="the bell",
        phrase="the silver bell",
        sound="jingle-jing",
        hold="a silver bell on a ribbon",
        tags={"bell", "music"},
    ),
    "whistle": LostItem(
        id="whistle",
        label="the whistle",
        phrase="the round whistle",
        sound="peep-pip",
        hold="a round whistle on a cord",
        tags={"whistle", "music"},
    ),
}

SPOTS = {
    "marigold_bed": Spot(
        id="marigold_bed",
        label="marigold bed",
        depth_word="loose and crumbly",
        difficulty=1,
        foreshadow="the marigold bed looked soft, as if the earth might gulp a dropped thing",
        fall_text="nestled right into the marigold bed, where the earth puffed up in a brown little cloud.",
        tags={"earth", "flowers"},
    ),
    "pumpkin_patch": Spot(
        id="pumpkin_patch",
        label="pumpkin patch",
        depth_word="soft and deep",
        difficulty=2,
        foreshadow="the pumpkin patch looked dark and deep, and the earth there seemed ready to keep small treasures",
        fall_text="slid into the pumpkin patch and vanished halfway under the soft earth by a curling vine.",
        tags={"earth", "pumpkins"},
    ),
    "oak_root": Spot(
        id="oak_root",
        label="oak root",
        depth_word="packed but pockety",
        difficulty=2,
        foreshadow="the old oak root had little pockets of earth under it, just right for hiding marbles or mistakes",
        fall_text="skipped once, twice, and tucked itself beside the oak root in a pocket of earth.",
        tags={"earth", "tree"},
    ),
    "duck_bank": Spot(
        id="duck_bank",
        label="duck pond bank",
        depth_word="damp and yielding",
        difficulty=1,
        foreshadow="the duck pond bank was damp, and the earth there squished if a shoe came too near",
        fall_text="plopped by the duck pond bank, where the damp earth held it with a soft little sigh.",
        tags={"earth", "pond"},
    ),
    "planter_box": Spot(
        id="planter_box",
        label="planter box",
        depth_word="light and sandy",
        difficulty=1,
        foreshadow="the planter box looked fluffy, and the earth sat so light that a pebble could disappear in it",
        fall_text="dropped into the planter box and half-hid itself in the sandy earth.",
        tags={"earth", "school_garden"},
    ),
    "bean_patch": Spot(
        id="bean_patch",
        label="bean patch",
        depth_word="soft and deep",
        difficulty=2,
        foreshadow="the bean patch had been watered, and the earth looked soft enough to hug anything that fell",
        fall_text="slipped into the bean patch and tucked itself under the soft earth near a bean leaf.",
        tags={"earth", "beans"},
    ),
}

TOOLS = {
    "spoon": Tool(
        id="spoon",
        label="spoon",
        phrase="a spoon",
        sense=2,
        power=1,
        swish="scrape-scrape",
        good_text="the spoon kissed the soil, lifted a small curl of earth, and up came the treasure.",
        fail_text="the spoon made a tiny path, but the lost thing was still tucked too snugly below.",
        qa_text="used a spoon to scrape the earth back",
        tags={"spoon", "retrieve"},
    ),
    "toy_shovel": Tool(
        id="toy_shovel",
        label="toy shovel",
        phrase="the toy shovel",
        sense=2,
        power=2,
        swish="scoop-scoop",
        good_text="the toy shovel scooped a neat little moon of soil, and the lost thing peeped free at once.",
        fail_text="the toy shovel moved some earth, but not enough to free the buried thing all the way.",
        qa_text="used the toy shovel to scoop the earth aside",
        tags={"shovel", "retrieve"},
    ),
    "hand_trowel": Tool(
        id="hand_trowel",
        label="hand trowel",
        phrase="the hand trowel",
        sense=3,
        power=3,
        swish="scritch-scritch",
        good_text="the hand trowel slipped under the clump of soil, and the lost thing came up bright as a wink.",
        fail_text="the hand trowel loosened the earth, though a grown-up still had to make the final careful lift.",
        qa_text="used a hand trowel to loosen the earth",
        tags={"trowel", "retrieve"},
    ),
    "bare_hands": Tool(
        id="bare_hands",
        label="bare hands",
        phrase="bare hands",
        sense=1,
        power=1,
        swish="pat-pat",
        good_text="little fingers brushed the topsoil back and found the lost thing.",
        fail_text="little fingers brushed at the earth, but the buried thing stayed hidden.",
        qa_text="used bare hands",
        tags={"hands"},
    ),
}

GIRL_NAMES = ["Lina", "Mila", "Nora", "Daisy", "Ivy", "June", "Tess", "Poppy"]
BOY_NAMES = ["Toby", "Milo", "Ben", "Finn", "Owen", "Jude", "Kit", "Theo"]


@dataclass
class StoryParams:
    place: str
    music: str
    item: str
    spot: str
    tool: str
    leader: str
    leader_gender: str
    friend: str
    friend_gender: str
    helper_type: str
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
    "conductor": [
        (
            "What does a conductor do?",
            "A conductor leads the music with hands or a baton. The conductor helps everyone stay together at the same time."
        )
    ],
    "earth": [
        (
            "What is earth?",
            "Earth is the soft ground or soil where plants grow. When it is loose or wet, small things can sink into it."
        )
    ],
    "retrieve": [
        (
            "What does retrieve mean?",
            "Retrieve means to get something back after it has been lost or dropped. You retrieve a thing by finding it and bringing it back."
        )
    ],
    "bell": [
        (
            "How does a little bell make a sound?",
            "A little bell rings when it shakes and the metal inside taps the sides. That is why it goes jingle-jing."
        )
    ],
    "whistle": [
        (
            "How does a whistle work?",
            "A whistle makes a sound when air moves through it in a special way. That is why a whistle can go peep or pip."
        )
    ],
    "baton": [
        (
            "What is a baton?",
            "A baton is a small stick a conductor waves to lead music. It is light, so it can slip if a hand twirls too fast."
        )
    ],
    "spoon": [
        (
            "Why can a spoon move soft soil?",
            "A spoon can scrape and lift a little bit of loose earth. It works best when the buried thing is not very deep."
        )
    ],
    "shovel": [
        (
            "What is a shovel for?",
            "A shovel scoops earth and sand. A small toy shovel can help lift loose soil away from a buried thing."
        )
    ],
    "trowel": [
        (
            "What is a hand trowel?",
            "A hand trowel is a small garden tool for digging and lifting soil. Grown-ups and careful children use it for little garden jobs."
        )
    ],
    "friendship": [
        (
            "What does friendship look like?",
            "Friendship looks like staying close when something goes wrong and helping kindly. A good friend does not run away from another friend's worry."
        )
    ],
}
KNOWLEDGE_ORDER = ["conductor", "earth", "retrieve", "bell", "whistle", "baton", "spoon", "shovel", "trowel", "friendship"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    leader = f["leader"]
    friend = f["friend"]
    place = f["place"]
    item = f["item_cfg"]
    music = f["music"]
    spot = f["spot_cfg"]
    outcome = f["outcome"]
    base = (
        f'Write a short nursery-rhyme-style story for a 3-to-5-year-old that uses the words '
        f'"retrieve", "conductor", and "earth". The story should include sound effects, friendship, and foreshadowing.'
    )
    if outcome == "helper":
        return [
            base,
            f"Tell a gentle story where {leader.id} is the conductor of a {music.game_name} in {place.label}, "
            f"but {item.label} falls into the {spot.label}. {friend.id} stays kind, they try to retrieve it, "
            f"and then a grown-up helps.",
            f"Write a child-facing rhyme where early clues show that the earth is soft, something musical drops, "
            f"and friendship matters more than hurrying."
        ]
    return [
        base,
        f"Tell a playful rhyme where {leader.id} and {friend.id} make music in {place.label}, "
        f"{item.label} slips into the earth, and the two friends retrieve it together.",
        f"Write a simple story with sound words and a foreshadowing clue about soft earth, ending with friends "
        f"playing more gently than before."
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    leader = f["leader"]
    friend = f["friend"]
    helper = f["helper"]
    place = f["place"]
    music = f["music"]
    item = f["item_cfg"]
    spot = f["spot_cfg"]
    tool = f["tool"]
    outcome = f["outcome"]

    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about two friends, {leader.id} and {friend.id}, making music together in {place.label}. "
            f"{leader.id} is the conductor, and {friend.id} stays close when the trouble begins."
        ),
        (
            f"What clue hinted that {item.label} might get stuck?",
            f"The story says the {spot.label} already looked {spot.depth_word} before anything fell. "
            f"That early clue foreshadowed that the earth could hold on to a dropped thing."
        ),
        (
            f"Why did {item.label} need to be retrieved?",
            f"{item.phrase.capitalize()} slipped from {leader.id}'s hand during the music and fell into the earth. "
            f"Once it was buried in the {spot.label}, the game could not go on until someone brought it back."
        ),
    ]
    if outcome == "together":
        qa.append(
            (
                f"How did {leader.id} and {friend.id} retrieve {item.label}?",
                f"They worked together and {tool.qa_text}. Because the {spot.label} was only {spot.depth_word}, "
                f"their careful teamwork was enough to free it."
            )
        )
    else:
        qa.append(
            (
                f"Why did they ask the {helper.label_word} for help?",
                f"They tried kindly and carefully with {tool.phrase}, but {item.label} was still tucked too deep in the {spot.label}. "
                f"So they asked the {helper.label_word}, because waiting for steady help was wiser than digging in a rush."
            )
        )
    qa.append(
        (
            "How did friendship matter in the story?",
            f"{friend.id} did not tease or leave when {leader.id} got worried. "
            f"By kneeling beside {leader.pronoun('object')} and helping retrieve the lost thing, {friend.pronoun()} turned the scary moment back into a shared song."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"earth", "retrieve", "friendship"}
    tags |= set(f["item_cfg"].tags)
    tags |= set(f["tool"].tags)
    if "conductor" in f["item_cfg"].tags or f["item_cfg"].id == "baton":
        tags.add("conductor")
    else:
        tags.add("conductor")
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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:8} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="garden",
        music="parade",
        item="baton",
        spot="marigold_bed",
        tool="spoon",
        leader="Lina",
        leader_gender="girl",
        friend="Toby",
        friend_gender="boy",
        helper_type="gardener",
    ),
    StoryParams(
        place="garden",
        music="moon_march",
        item="bell",
        spot="pumpkin_patch",
        tool="spoon",
        leader="Mila",
        leader_gender="girl",
        friend="Finn",
        friend_gender="boy",
        helper_type="gardener",
    ),
    StoryParams(
        place="park",
        music="raindrop_song",
        item="whistle",
        spot="duck_bank",
        tool="toy_shovel",
        leader="Nora",
        leader_gender="girl",
        friend="Kit",
        friend_gender="boy",
        helper_type="gardener",
    ),
    StoryParams(
        place="park",
        music="parade",
        item="bell",
        spot="oak_root",
        tool="toy_shovel",
        leader="Theo",
        leader_gender="boy",
        friend="Daisy",
        friend_gender="girl",
        helper_type="gardener",
    ),
    StoryParams(
        place="schoolyard",
        music="moon_march",
        item="baton",
        spot="bean_patch",
        tool="hand_trowel",
        leader="June",
        leader_gender="girl",
        friend="Ben",
        friend_gender="boy",
        helper_type="teacher",
    ),
]


def explain_spot(place: str, spot: str) -> str:
    return (
        f"(No story: {SPOTS[spot].label} is not part of {PLACES[place].label} here. "
        f"Choose one of: {', '.join(sorted(PLACES[place].afford_spots))}.)"
    )


def explain_tool(tool_id: str) -> str:
    tool = TOOLS[tool_id]
    better = ", ".join(sorted(t.id for t in sensible_tools()))
    return (
        f"(Refusing tool '{tool_id}': it scores too low on common sense "
        f"(sense={tool.sense} < {SENSE_MIN}). A careful story should use a safer retrieval tool. "
        f"Try: {better}.)"
    )


def outcome_of(params: StoryParams) -> str:
    return retrieval_outcome(SPOTS[params.spot], TOOLS[params.tool])


ASP_RULES = r"""
sensible_tool(T) :- tool(T), sense(T, S), sense_min(M), S >= M.
valid(P, M, I, S, T) :- place(P), music(M), item(I), affords(P, S), sensible_tool(T).

together :- chosen_spot(S), chosen_tool(T), power(T, P), difficulty(S, D), P >= D.
helper   :- chosen_spot(S), chosen_tool(T), power(T, P), difficulty(S, D), P < D.

outcome(together) :- together.
outcome(helper)   :- helper.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        for spot_id in sorted(place.afford_spots):
            lines.append(asp.fact("affords", pid, spot_id))
    for mid in MUSICS:
        lines.append(asp.fact("music", mid))
    for iid in ITEMS:
        lines.append(asp.fact("item", iid))
    for sid, spot in SPOTS.items():
        lines.append(asp.fact("spot", sid))
        lines.append(asp.fact("difficulty", sid, spot.difficulty))
    for tid, tool in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        lines.append(asp.fact("sense", tid, tool.sense))
        lines.append(asp.fact("power", tid, tool.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/5."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_spot", params.spot),
            asp.fact("chosen_tool", params.tool),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: gate matches valid_combos() ({len(python_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    cases = list(CURATED)
    for seed in range(100):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        params.seed = seed
        cases.append(params)

    bad = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(cases[0])
        if not sample.story.strip():
            raise StoryError("Generated empty story.")
        sink = io.StringIO()
        with contextlib.redirect_stdout(sink):
            emit(sample, trace=True, qa=True, header="### smoke")
        print("OK: generate()/emit() smoke test passed.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a tiny music game, soft earth, and a kind retrieval."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--music", choices=MUSICS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--spot", choices=SPOTS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--leader")
    ap.add_argument("--friend")
    ap.add_argument("--leader-gender", choices=["girl", "boy"])
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program (facts + inline rules)")
    return ap


def pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.spot and args.spot not in PLACES[args.place].afford_spots:
        raise StoryError(explain_spot(args.place, args.spot))
    if args.tool and TOOLS[args.tool].sense < SENSE_MIN:
        raise StoryError(explain_tool(args.tool))

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.music is None or combo[1] == args.music)
        and (args.item is None or combo[2] == args.item)
        and (args.spot is None or combo[3] == args.spot)
        and (args.tool is None or combo[4] == args.tool)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, music_id, item_id, spot_id, tool_id = rng.choice(sorted(combos))
    place = PLACES[place_id]

    leader_gender = args.leader_gender or rng.choice(["girl", "boy"])
    friend_gender = args.friend_gender or rng.choice(["girl", "boy"])
    leader = args.leader or pick_name(rng, leader_gender)
    friend = args.friend or pick_name(rng, friend_gender, avoid=leader)

    return StoryParams(
        place=place_id,
        music=music_id,
        item=item_id,
        spot=spot_id,
        tool=tool_id,
        leader=leader,
        leader_gender=leader_gender,
        friend=friend,
        friend_gender=friend_gender,
        helper_type=place.helper_type,
    )


def _need(mapping: dict, key: str, kind: str):
    if key not in mapping:
        raise StoryError(f"(No story: unknown {kind} '{key}'.)")
    return mapping[key]


def generate(params: StoryParams) -> StorySample:
    place = _need(PLACES, params.place, "place")
    music = _need(MUSICS, params.music, "music")
    item = _need(ITEMS, params.item, "item")
    spot = _need(SPOTS, params.spot, "spot")
    tool = _need(TOOLS, params.tool, "tool")

    if params.spot not in place.afford_spots:
        raise StoryError(explain_spot(params.place, params.spot))
    if tool.sense < SENSE_MIN:
        raise StoryError(explain_tool(params.tool))
    if params.helper_type not in {"gardener", "teacher"}:
        raise StoryError(f"(No story: unknown helper type '{params.helper_type}'.)")
    if not params.leader or not params.friend:
        raise StoryError("(No story: both children need names.)")

    world = tell(
        place=place,
        music=music,
        item_cfg=item,
        spot=spot,
        tool=tool,
        leader_name=params.leader,
        leader_gender=params.leader_gender,
        friend_name=params.friend,
        friend_gender=params.friend_gender,
        helper_type=params.helper_type,
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
        print(asp_program("", "#show valid/5.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, music, item, spot, tool) combos:\n")
        for place, music, item, spot, tool in combos:
            outcome = retrieval_outcome(SPOTS[spot], TOOLS[tool])
            print(f"  {place:10} {music:13} {item:8} {spot:13} {tool:11} -> {outcome}")
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
            header = (
                f"### {p.leader} & {p.friend}: {p.item} in {p.spot} "
                f"({p.place}, {p.music}, {outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
