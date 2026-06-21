#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/clumsy_zest_mystery_to_solve_adventure.py
====================================================================

A standalone story world for a tiny Adventure-style "mystery to solve" domain.

Premise
-------
A child adventurer is a little clumsy but full of zest. Just as a small
expedition is about to begin, an important object goes missing. The child first
blames the wrong thing -- usually a tumble or a breeze -- but then notices a
real clue in the world. By following that clue and using the right helper tool,
the children solve the mystery and recover the missing object.

Reasonableness constraint
-------------------------
Not every culprit, missing object, setting, and helper tool make sense together.

- A culprit only steals things it is actually attracted to.
- The setting must contain the culprit's hiding spot.
- The helper tool must reach or safely access that hiding spot.

So the world refuses combinations like:
- a crow stealing a jam tart for a high branch at the river dock
- a fishing net used to recover something from a thorny bush
- a goat mystery in a place with no bushes to hide in

Run it
------
python storyworlds/worlds/gpt-5.4/clumsy_zest_mystery_to_solve_adventure.py
python storyworlds/worlds/gpt-5.4/clumsy_zest_mystery_to_solve_adventure.py --place orchard --item tart --culprit goat --helper broom
python storyworlds/worlds/gpt-5.4/clumsy_zest_mystery_to_solve_adventure.py --item compass --culprit crow
python storyworlds/worlds/gpt-5.4/clumsy_zest_mystery_to_solve_adventure.py --all
python storyworlds/worlds/gpt-5.4/clumsy_zest_mystery_to_solve_adventure.py -n 5 --seed 7 --qa
python storyworlds/worlds/gpt-5.4/clumsy_zest_mystery_to_solve_adventure.py --verify
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
    phrase: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    tags: set[str] = field(default_factory=set)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Setting:
    id: str
    place: str
    scene: str
    path_word: str
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
class MissingItem:
    id: str
    label: str
    phrase: str
    need: str
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
class Culprit:
    id: str
    label: str
    likes: set[str]
    clue_name: str
    clue_text: str
    stash: str
    stash_text: str
    movement: str
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
class Helper:
    id: str
    label: str
    phrase: str
    reaches: set[str]
    action_text: str
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
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
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

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"hero", "friend"}]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.setting)
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


def _r_missing_makes_mystery(world: World) -> list[str]:
    item = world.get("item")
    if item.meters["lost"] < THRESHOLD:
        return []
    sig = ("mystery", "item")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    world.get("camp").meters["mystery"] += 1
    for kid in world.kids():
        kid.memes["worry"] += 1
    return []


def _r_clue_builds_confidence(world: World) -> list[str]:
    clue = world.get("clue")
    hero = world.get("hero")
    if clue.meters["visible"] < THRESHOLD or hero.memes["care"] < THRESHOLD:
        return []
    sig = ("confidence", "hero")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["confidence"] += 1
    hero.memes["focus"] += 1
    return []


def _r_recovery_resolves(world: World) -> list[str]:
    item = world.get("item")
    if item.meters["found"] < THRESHOLD:
        return []
    sig = ("relief", "all")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    world.get("camp").meters["mystery"] = 0.0
    for kid in world.kids():
        kid.memes["worry"] = 0.0
        kid.memes["joy"] += 1
        kid.memes["pride"] += 1
    return []


CAUSAL_RULES: list[Rule] = [
    Rule(name="missing_makes_mystery", tag="social", apply=_r_missing_makes_mystery),
    Rule(name="clue_builds_confidence", tag="social", apply=_r_clue_builds_confidence),
    Rule(name="recovery_resolves", tag="social", apply=_r_recovery_resolves),
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
            world.say(sent)
    return produced


def culprit_likes_item(culprit: Culprit, item: MissingItem) -> bool:
    return bool(culprit.likes & item.tags)


def helper_fits(helper: Helper, culprit: Culprit) -> bool:
    return culprit.stash in helper.reaches


def valid_story_combo(setting: Setting, item: MissingItem, culprit: Culprit, helper: Helper) -> bool:
    return (
        culprit_likes_item(culprit, item)
        and culprit.stash in setting.affords
        and helper_fits(helper, culprit)
    )


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for place_id, setting in SETTINGS.items():
        for item_id, item in ITEMS.items():
            for culprit_id, culprit in CULPRITS.items():
                for helper_id, helper in HELPERS.items():
                    if valid_story_combo(setting, item, culprit, helper):
                        combos.append((place_id, item_id, culprit_id, helper_id))
    return sorted(combos)


def predict_clue(world: World) -> dict:
    sim = world.copy()
    clue = sim.get("clue")
    hero = sim.get("hero")
    clue.meters["visible"] += 1
    hero.memes["care"] += 1
    propagate(sim, narrate=False)
    return {
        "visible": clue.meters["visible"] >= THRESHOLD,
        "confidence": hero.memes["confidence"],
    }


def explain_rejection(setting: Setting, item: MissingItem, culprit: Culprit, helper: Helper) -> str:
    if not culprit_likes_item(culprit, item):
        return (
            f"(No story: a {culprit.label} would not sensibly steal {item.phrase}. "
            f"It is not attracted to the right kind of object for this mystery.)"
        )
    if culprit.stash not in setting.affords:
        return (
            f"(No story: {setting.place} has no plausible place for a {culprit.label} "
            f"to hide something at {culprit.stash_text}.)"
        )
    if not helper_fits(helper, culprit):
        return (
            f"(No story: {helper.phrase} cannot reach something hidden {culprit.stash_text}. "
            f"Pick a helper that actually fits the hiding place.)"
        )
    return "(No story: this combination is not reasonable.)"


def intro(world: World, hero: Entity, friend: Entity, item: MissingItem, mission_name: str) -> None:
    hero.memes["zest"] += 1
    friend.memes["joy"] += 1
    world.say(
        f"On a bright afternoon at {world.setting.place}, {hero.id} and {friend.id} "
        f"started the {mission_name}. {hero.id} was a little clumsy, but full of zest, "
        f"and that made every ordinary path feel like the start of an adventure."
    )
    world.say(
        f"They had packed {item.phrase}, because they needed it to {item.need}. "
        f"{world.setting.scene}"
    )


def ready_for_quest(world: World, hero: Entity, friend: Entity, item_ent: Entity, item: MissingItem) -> None:
    item_ent.meters["ready"] = 1.0
    world.say(
        f'{friend.id} spread out their plan and said, "As soon as we have the '
        f'{item.label}, we can begin."'
    )


def clumsy_turn(world: World, hero: Entity, item: MissingItem) -> None:
    hero.memes["embarrassed"] += 1
    hero.meters["stumble"] += 1
    world.say(
        f"But just then {hero.id} caught a toe on a root and almost tumbled. "
        f'"Oh no," {hero.pronoun()} gasped. "Did I knock the {item.label} away?"'
    )


def discover_loss(world: World, hero: Entity, friend: Entity, item_ent: Entity, item: MissingItem) -> None:
    item_ent.meters["lost"] = 1.0
    propagate(world, narrate=False)
    world.say(
        f"They looked under the crate, inside the satchel, and along the {world.setting.path_word}, "
        f"but {item.phrase} was gone. At once, their easy game turned into a real mystery to solve."
    )
    world.say(
        f'{friend.id} frowned. "Maybe the wind took it." But {hero.id} took a slower breath and looked again.'
    )


def reveal_clue(world: World, hero: Entity, culprit: Culprit) -> None:
    pred = predict_clue(world)
    clue = world.get("clue")
    hero.memes["care"] = 1.0
    clue.meters["visible"] = 1.0
    propagate(world, narrate=False)
    world.facts["predicted_confidence"] = pred["confidence"]
    world.say(
        f"Near the empty spot, {hero.id} noticed {culprit.clue_text}. "
        f'"That is not wind," {hero.pronoun()} whispered. "That is a clue."'
    )


def follow_trail(world: World, hero: Entity, friend: Entity, culprit: Culprit) -> None:
    hero.memes["focus"] += 1
    friend.memes["trust"] += 1
    world.say(
        f"Together they followed the sign of the thief, moving past {culprit.movement}. "
        f"The farther they went, the more the mystery felt like a true expedition."
    )
    world.say(
        f"{friend.id} stopped blaming the breeze and began watching wherever {hero.id} pointed."
    )


def find_stash(world: World, hero: Entity, culprit: Culprit, item: MissingItem) -> None:
    world.say(
        f"At last they found it: {item.phrase} was hidden {culprit.stash_text}. "
        f"The little thief had tucked it away as if it were treasure."
    )


def retrieve(world: World, hero: Entity, friend: Entity, helper: Helper, item_ent: Entity, item: MissingItem) -> None:
    item_ent.meters["found"] = 1.0
    propagate(world, narrate=False)
    world.say(
        f"{friend.id} fetched {helper.phrase}, and {hero.id} {helper.action_text}. "
        f"In another moment, {item.phrase} was safe in {hero.pronoun('possessive')} hands again."
    )


def lesson_and_end(world: World, hero: Entity, friend: Entity, culprit: Culprit, item: MissingItem, mission_name: str) -> None:
    hero.memes["embarrassed"] = 0.0
    hero.memes["confidence"] += 1
    hero.memes["lesson"] += 1
    world.say(
        f'"So it was a {culprit.label}!" {friend.id} said. {hero.id} grinned. '
        f'{hero.pronoun().capitalize()} had been clumsy at the start, but careful eyes solved the mystery.'
    )
    world.say(
        f"They set off at last on the {mission_name}, with {item.phrase} tucked safely away. "
        f"From then on, whenever something small went wrong, {hero.id} tried looking for clues before blaming {hero.pronoun('possessive')} own feet."
    )


def tell(
    setting: Setting,
    item: MissingItem,
    culprit: Culprit,
    helper: Helper,
    hero_name: str = "Nora",
    hero_gender: str = "girl",
    friend_name: str = "Leo",
    friend_gender: str = "boy",
    parent_type: str = "mother",
    mission_name: str = "Map-and-Moonlight Expedition",
) -> World:
    world = World(setting)

    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_gender,
        label=hero_name,
        role="hero",
        traits=["clumsy", "eager"],
    ))
    friend = world.add(Entity(
        id=friend_name,
        kind="character",
        type=friend_gender,
        label=friend_name,
        role="friend",
        traits=["steady"],
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=parent_type,
        label="the parent",
        role="parent",
        traits=["calm"],
    ))
    camp = world.add(Entity(
        id="camp",
        kind="thing",
        type="camp",
        label="camp",
    ))
    item_ent = world.add(Entity(
        id="item",
        kind="thing",
        type="item",
        label=item.label,
        phrase=item.phrase,
        tags=set(item.tags),
    ))
    clue = world.add(Entity(
        id="clue",
        kind="thing",
        type="clue",
        label=culprit.clue_name,
        phrase=culprit.clue_text,
    ))
    culprit_ent = world.add(Entity(
        id="culprit",
        kind="thing",
        type="animal",
        label=culprit.label,
        attrs={"stash": culprit.stash},
        tags=set(culprit.tags),
    ))
    helper_ent = world.add(Entity(
        id="helper",
        kind="thing",
        type="tool",
        label=helper.label,
        phrase=helper.phrase,
        attrs={"reaches": set(helper.reaches)},
        tags=set(helper.tags),
    ))

    for e in (hero, friend):
        e.memes["worry"] = 0.0
        e.memes["joy"] = 0.0
        e.memes["pride"] = 0.0
        e.memes["focus"] = 0.0
        e.memes["confidence"] = 0.0
        e.memes["care"] = 0.0
    hero.memes["embarrassed"] = 0.0
    hero.memes["zest"] = 0.0
    hero.meters["stumble"] = 0.0
    camp.meters["mystery"] = 0.0
    item_ent.meters["ready"] = 0.0
    item_ent.meters["lost"] = 0.0
    item_ent.meters["found"] = 0.0
    clue.meters["visible"] = 0.0

    world.facts.update(
        setting=setting,
        item_cfg=item,
        culprit_cfg=culprit,
        helper_cfg=helper,
        hero=hero,
        friend=friend,
        parent=parent,
        mission_name=mission_name,
        clue_name=culprit.clue_name,
    )

    intro(world, hero, friend, item, mission_name)
    ready_for_quest(world, hero, friend, item_ent, item)
    world.para()
    clumsy_turn(world, hero, item)
    discover_loss(world, hero, friend, item_ent, item)
    reveal_clue(world, hero, culprit)
    follow_trail(world, hero, friend, culprit)
    world.para()
    find_stash(world, hero, culprit, item)
    retrieve(world, hero, friend, helper, item_ent, item)
    lesson_and_end(world, hero, friend, culprit, item, mission_name)

    world.facts.update(
        item_found=item_ent.meters["found"] >= THRESHOLD,
        mystery_active=camp.meters["mystery"] >= THRESHOLD,
        helper_used=helper.label,
        stash=culprit.stash,
    )
    return world


SETTINGS = {
    "orchard": Setting(
        id="orchard",
        place="the orchard",
        scene="Tall grass brushed their knees, and rows of trees made green archways over the trail.",
        path_word="grass path",
        affords={"low_bush"},
        tags={"orchard", "outside"},
    ),
    "treehouse_yard": Setting(
        id="treehouse_yard",
        place="the treehouse yard",
        scene="A rope ladder swung near the old oak, and the yard looked large enough for secret kingdoms.",
        path_word="dirt path",
        affords={"high_branch", "low_bush"},
        tags={"yard", "outside"},
    ),
    "river_dock": Setting(
        id="river_dock",
        place="the river dock",
        scene="Boards creaked softly over the shining water, and every mooring post felt like part of a harbor map.",
        path_word="wooden boards",
        affords={"under_dock"},
        tags={"river", "dock"},
    ),
}

ITEMS = {
    "compass": MissingItem(
        id="compass",
        label="compass",
        phrase="the brass compass",
        need="find the hidden turning on their map",
        tags={"shiny", "adventure"},
    ),
    "map_tube": MissingItem(
        id="map_tube",
        label="map tube",
        phrase="the paper map tube",
        need="carry their secret trail map without tearing it",
        tags={"crinkly", "paper", "adventure"},
    ),
    "tart": MissingItem(
        id="tart",
        label="jam tart",
        phrase="the jam tart",
        need="eat their explorers' snack at the halfway stump",
        tags={"tasty", "food"},
    ),
}

CULPRITS = {
    "crow": Culprit(
        id="crow",
        label="crow",
        likes={"shiny"},
        clue_name="feather",
        clue_text="a black feather and two pecks in the dust",
        stash="high_branch",
        stash_text="high on a branch above their heads",
        movement="the oak roots and around the trunk",
        tags={"bird", "feather"},
    ),
    "goat": Culprit(
        id="goat",
        label="goat",
        likes={"tasty", "paper", "crinkly"},
        clue_name="hoofprints",
        clue_text="small hoofprints and one chewed corner of a leaf",
        stash="low_bush",
        stash_text="deep inside a thorny low bush",
        movement="a gap in the hedge and around a berry patch",
        tags={"goat", "hoofprints"},
    ),
    "otter": Culprit(
        id="otter",
        label="otter",
        likes={"shiny", "food"},
        clue_name="water drops",
        clue_text="wet paw marks and a little shining smear on the boards",
        stash="under_dock",
        stash_text="on a beam under the dock",
        movement="the dock posts and along the water's edge",
        tags={"otter", "water"},
    ),
}

HELPERS = {
    "stool": Helper(
        id="stool",
        label="stool",
        phrase="a small wooden stool",
        reaches={"high_branch"},
        action_text="climbed onto the stool and reached up as high as she could" if False else "climbed onto the stool and reached up as high as possible",
        qa_text="used a small wooden stool to reach the branch",
        tags={"stool", "reach"},
    ),
    "broom": Helper(
        id="broom",
        label="broom",
        phrase="a long broom",
        reaches={"low_bush"},
        action_text="slid the broom gently through the prickles and nudged the prize free",
        qa_text="used a long broom to push the hidden item out of the bush",
        tags={"broom", "bush"},
    ),
    "net": Helper(
        id="net",
        label="fishing net",
        phrase="a fishing net",
        reaches={"under_dock"},
        action_text="lay on the boards and hooked it up with the fishing net",
        qa_text="used a fishing net to lift the hidden item from under the dock",
        tags={"net", "water"},
    ),
}

GIRL_NAMES = ["Nora", "Lily", "Mia", "Ava", "Ella", "Lucy", "Zoe", "Maya"]
BOY_NAMES = ["Leo", "Ben", "Max", "Sam", "Finn", "Theo", "Jack", "Eli"]
MISSION_NAMES = [
    "Map-and-Moonlight Expedition",
    "Lost Lantern Trail",
    "Golden Acorn Quest",
    "Captain Fern Adventure",
]


@dataclass
class StoryParams:
    place: str
    item: str
    culprit: str
    helper: str
    hero_name: str
    hero_gender: str
    friend_name: str
    friend_gender: str
    parent: str
    mission_name: str
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
    "feather": [
        (
            "Why might a black feather be a clue?",
            "A feather can show that a bird was nearby. If something shiny is missing, a bird clue can help you guess where it went."
        )
    ],
    "hoofprints": [
        (
            "What can hoofprints tell you?",
            "Hoofprints show that a hoofed animal walked there. They can point you toward the direction the animal went."
        )
    ],
    "water": [
        (
            "What can wet paw marks tell you in a mystery?",
            "Wet paw marks show that an animal came from the water or stepped in water. They can help you follow a trail without guessing."
        )
    ],
    "stool": [
        (
            "What is a stool used for?",
            "A stool is a small seat you can stand on to reach something a little higher. A grown-up should help if the place is wobbly or too tall."
        )
    ],
    "broom": [
        (
            "How can a broom help without sweeping?",
            "A broom can gently push or pull something that is hard to reach. That way your hands do not have to go into prickles or dirt first."
        )
    ],
    "net": [
        (
            "What is a fishing net good for?",
            "A fishing net can scoop or lift something from water or from under a dock. Its long handle helps you reach where your arm cannot."
        )
    ],
    "compass": [
        (
            "What does a compass do?",
            "A compass helps people tell direction, like north and south. Explorers use it when they do not want to get lost."
        )
    ],
    "map_tube": [
        (
            "Why would explorers use a map tube?",
            "A map tube keeps a paper map rolled up and safer from tears. It makes carrying the map much easier on an adventure."
        )
    ],
    "tart": [
        (
            "Why would explorers pack a snack?",
            "A snack gives you energy on a long walk or game. It also gives the group a cheerful place to stop and rest."
        )
    ],
}
KNOWLEDGE_ORDER = ["compass", "map_tube", "tart", "feather", "hoofprints", "water", "stool", "broom", "net"]


CURATED = [
    StoryParams(
        place="treehouse_yard",
        item="compass",
        culprit="crow",
        helper="stool",
        hero_name="Nora",
        hero_gender="girl",
        friend_name="Leo",
        friend_gender="boy",
        parent="mother",
        mission_name="Golden Acorn Quest",
    ),
    StoryParams(
        place="orchard",
        item="map_tube",
        culprit="goat",
        helper="broom",
        hero_name="Mia",
        hero_gender="girl",
        friend_name="Sam",
        friend_gender="boy",
        parent="father",
        mission_name="Captain Fern Adventure",
    ),
    StoryParams(
        place="river_dock",
        item="tart",
        culprit="otter",
        helper="net",
        hero_name="Ben",
        hero_gender="boy",
        friend_name="Ava",
        friend_gender="girl",
        parent="mother",
        mission_name="Lost Lantern Trail",
    ),
    StoryParams(
        place="river_dock",
        item="compass",
        culprit="otter",
        helper="net",
        hero_name="Ella",
        hero_gender="girl",
        friend_name="Finn",
        friend_gender="boy",
        parent="father",
        mission_name="Map-and-Moonlight Expedition",
    ),
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    item = f["item_cfg"]
    culprit = f["culprit_cfg"]
    setting = f["setting"]
    return [
        f'Write an adventure story for a 3-to-5-year-old with a mystery to solve, and include the words "clumsy" and "zest".',
        f"Tell a gentle adventure where {hero.id}, a clumsy but eager child, notices a clue after {item.phrase} goes missing at {setting.place}, and solves the mystery with {friend.id}.",
        f"Write a short explorer story where a {culprit.label} steals {item.phrase}, the children follow a clue, and the ending shows they learned to look carefully before guessing.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    item = f["item_cfg"]
    culprit = f["culprit_cfg"]
    helper = f["helper_cfg"]
    setting = f["setting"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id} and {friend.id}, two children setting out on a little adventure at {setting.place}. {hero.id} is clumsy but eager, and that matters because the mystery begins right after a stumble."
        ),
        (
            f"What went missing before the adventure could begin?",
            f"{item.phrase.capitalize()} went missing just when the children needed it to {item.need}. That loss is what turns the game into a mystery to solve."
        ),
        (
            f"Why did {hero.id} stop blaming the fall and start looking around carefully?",
            f"{hero.id} noticed {culprit.clue_text}. That clue showed the missing item had been taken by some creature, not simply knocked away by accident."
        ),
        (
            "How did they solve the mystery?",
            f"They followed the clue trail until they found the hiding place {culprit.stash_text}. Then they {helper.qa_text}, which let them get the item back safely."
        ),
        (
            "What changed by the end of the story?",
            f"At the beginning, {hero.id} thought the problem might just be {hero.pronoun('possessive')} own clumsy mistake. By the end, {hero.pronoun()} had learned to slow down, look for evidence, and solve the mystery with care."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    item = f["item_cfg"]
    culprit = f["culprit_cfg"]
    helper = f["helper_cfg"]
    tags = {item.id, helper.id}
    if culprit.id == "crow":
        tags.add("feather")
    if culprit.id == "goat":
        tags.add("hoofprints")
    if culprit.id == "otter":
        tags.add("water")
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
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:8} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
likes_item(C, I) :- likes(C, T), item_tag(I, T).
helper_fits(H, C) :- helper_reaches(H, S), culprit_stash(C, S).
setting_fits(P, C) :- affords(P, S), culprit_stash(C, S).

valid(P, I, C, H) :- place(P), item(I), culprit(C), helper(H),
                     likes_item(C, I), setting_fits(P, C), helper_fits(H, C).

solved(P, I, C, H) :- valid(P, I, C, H).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id, setting in SETTINGS.items():
        lines.append(asp.fact("place", place_id))
        for stash in sorted(setting.affords):
            lines.append(asp.fact("affords", place_id, stash))
    for item_id, item in ITEMS.items():
        lines.append(asp.fact("item", item_id))
        for tag in sorted(item.tags):
            lines.append(asp.fact("item_tag", item_id, tag))
    for culprit_id, culprit in CULPRITS.items():
        lines.append(asp.fact("culprit", culprit_id))
        lines.append(asp.fact("culprit_stash", culprit_id, culprit.stash))
        for tag in sorted(culprit.likes):
            lines.append(asp.fact("likes", culprit_id, tag))
    for helper_id, helper in HELPERS.items():
        lines.append(asp.fact("helper", helper_id))
        for stash in sorted(helper.reaches):
            lines.append(asp.fact("helper_reaches", helper_id, stash))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_solved(params: StoryParams) -> bool:
    import asp

    extra = "\n".join([
        asp.fact("chosen_place", params.place),
        asp.fact("chosen_item", params.item),
        asp.fact("chosen_culprit", params.culprit),
        asp.fact("chosen_helper", params.helper),
        "selected :- valid(P,I,C,H), chosen_place(P), chosen_item(I), chosen_culprit(C), chosen_helper(H).",
        "done :- solved(P,I,C,H), chosen_place(P), chosen_item(I), chosen_culprit(C), chosen_helper(H).",
    ])
    model = asp.one_model(asp_program(extra, "#show done/0."))
    return bool(model)


def outcome_of(params: StoryParams) -> str:
    setting = SETTINGS[params.place]
    item = ITEMS[params.item]
    culprit = CULPRITS[params.culprit]
    helper = HELPERS[params.helper]
    return "solved" if valid_story_combo(setting, item, culprit, helper) else "invalid"


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

    cases: list[StoryParams] = list(CURATED)
    parser = build_parser()
    for s in range(50):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(s))
        except StoryError:
            continue
        params.seed = s
        cases.append(params)

    bad = 0
    for params in cases:
        asp_ok = asp_solved(params)
        py_ok = outcome_of(params) == "solved"
        if asp_ok != py_ok:
            bad += 1
    if bad == 0:
        print(f"OK: ASP solved-state matches Python on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} solved-state checks differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("Smoke test generated an empty story.")
        print("OK: smoke test generated a normal story.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Adventure storyworld: a clumsy child with zest solves a small mystery by following a real clue."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--culprit", choices=CULPRITS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--hero-name")
    ap.add_argument("--friend-name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combos derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test story generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    explicit_place = args.place
    explicit_item = args.item
    explicit_culprit = args.culprit
    explicit_helper = args.helper

    if explicit_place and explicit_item and explicit_culprit and explicit_helper:
        setting = SETTINGS[explicit_place]
        item = ITEMS[explicit_item]
        culprit = CULPRITS[explicit_culprit]
        helper = HELPERS[explicit_helper]
        if not valid_story_combo(setting, item, culprit, helper):
            raise StoryError(explain_rejection(setting, item, culprit, helper))

    combos = [
        combo for combo in valid_combos()
        if (explicit_place is None or combo[0] == explicit_place)
        and (explicit_item is None or combo[1] == explicit_item)
        and (explicit_culprit is None or combo[2] == explicit_culprit)
        and (explicit_helper is None or combo[3] == explicit_helper)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, item_id, culprit_id, helper_id = rng.choice(combos)

    hero_gender = rng.choice(["girl", "boy"])
    friend_gender = "boy" if hero_gender == "girl" else "girl"
    hero_name = args.hero_name or _pick_name(rng, hero_gender)
    friend_name = args.friend_name or _pick_name(rng, friend_gender, avoid=hero_name)
    parent = args.parent or rng.choice(["mother", "father"])
    mission_name = rng.choice(MISSION_NAMES)

    return StoryParams(
        place=place_id,
        item=item_id,
        culprit=culprit_id,
        helper=helper_id,
        hero_name=hero_name,
        hero_gender=hero_gender,
        friend_name=friend_name,
        friend_gender=friend_gender,
        parent=parent,
        mission_name=mission_name,
    )


def generate(params: StoryParams) -> StorySample:
    missing = [field for field, table in (
        ("place", SETTINGS),
        ("item", ITEMS),
        ("culprit", CULPRITS),
        ("helper", HELPERS),
    ) if getattr(params, field) not in table]
    if missing:
        raise StoryError(f"(Invalid params: unknown {', '.join(missing)}.)")

    setting = SETTINGS[params.place]
    item = ITEMS[params.item]
    culprit = CULPRITS[params.culprit]
    helper = HELPERS[params.helper]

    if not valid_story_combo(setting, item, culprit, helper):
        raise StoryError(explain_rejection(setting, item, culprit, helper))

    world = tell(
        setting=setting,
        item=item,
        culprit=culprit,
        helper=helper,
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        friend_name=params.friend_name,
        friend_gender=params.friend_gender,
        parent_type=params.parent,
        mission_name=params.mission_name,
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
        print(asp_program("", "#show valid/4.\n#show solved/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid (place, item, culprit, helper) combos:\n")
        for place, item, culprit, helper in combos:
            print(f"  {place:14} {item:10} {culprit:8} {helper}")
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
            header = f"### {p.hero_name} & {p.friend_name}: {p.item} / {p.culprit} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
