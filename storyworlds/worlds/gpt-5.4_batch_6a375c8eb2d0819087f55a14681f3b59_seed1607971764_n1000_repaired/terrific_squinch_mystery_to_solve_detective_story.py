#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/terrific_squinch_mystery_to_solve_detective_story.py
================================================================================

A standalone storyworld for a small child-facing detective mystery.

Premise
-------
A young detective is getting ready for a little club activity when an important
object goes missing. The disappearance is not mean or magical; it comes from a
plausible culprit with a simple motive. The detective notices a clue, gives one
eye a tiny squinch, follows the trail, and solves the mystery.

The world model enforces common sense:

- a culprit must actually be present in the setting
- the culprit must be tempted by the item's motive (shiny / hungry / cozy)
- the culprit must be strong enough to move the item
- the setting must have a matching hideout for that motive

The story always resolves, but the path to the solution is state-driven by the
culprit, clue, motive, and hideout.

Run it
------
    python storyworlds/worlds/gpt-5.4/terrific_squinch_mystery_to_solve_detective_story.py
    python storyworlds/worlds/gpt-5.4/terrific_squinch_mystery_to_solve_detective_story.py --setting backyard --item silver_whistle --culprit magpie
    python storyworlds/worlds/gpt-5.4/terrific_squinch_mystery_to_solve_detective_story.py --setting classroom --culprit squirrel
    python storyworlds/worlds/gpt-5.4/terrific_squinch_mystery_to_solve_detective_story.py --all
    python storyworlds/worlds/gpt-5.4/terrific_squinch_mystery_to_solve_detective_story.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/terrific_squinch_mystery_to_solve_detective_story.py --verify
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
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
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Setting:
    id: str
    label: str
    opening: str
    hideouts: dict[str, str] = field(default_factory=dict)
    culprits: set[str] = field(default_factory=set)
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
class Item:
    id: str
    label: str
    phrase: str
    size: int
    motive: str
    importance: str
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
    phrase: str
    verb: str
    clue: str
    clue_detail: str
    sound: str
    max_size: int
    likes: set[str] = field(default_factory=set)
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
    scene: str
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


def _r_missing_mystery(world: World) -> list[str]:
    out: list[str] = []
    item = world.get("item")
    detective = world.get("detective")
    room = world.get("room")
    if item.meters["missing"] >= THRESHOLD and ("missing_mystery",) not in world.fired:
        world.fired.add(("missing_mystery",))
        room.meters["mystery"] += 1
        detective.memes["curiosity"] += 1
        detective.memes["worry"] += 1
        out.append("__mystery__")
    return out


def _r_clue_visible(world: World) -> list[str]:
    out: list[str] = []
    culprit = world.get("culprit")
    clue = world.get("clue")
    detective = world.get("detective")
    if culprit.meters["carried_item"] >= THRESHOLD and clue.meters["visible"] < THRESHOLD:
        world.fired.add(("clue_visible",))
        clue.meters["visible"] += 1
        detective.memes["curiosity"] += 1
        out.append("__clue__")
    return out


def _r_track_to_find(world: World) -> list[str]:
    out: list[str] = []
    detective = world.get("detective")
    item = world.get("item")
    clue = world.get("clue")
    room = world.get("room")
    if detective.meters["tracking"] >= THRESHOLD and clue.meters["visible"] >= THRESHOLD:
        sig = ("found_item",)
        if sig not in world.fired:
            world.fired.add(sig)
            item.meters["missing"] = 0.0
            item.meters["found"] += 1
            detective.memes["confidence"] += 1
            detective.memes["relief"] += 1
            detective.memes["worry"] = 0.0
            room.meters["mystery"] = 0.0
            out.append("__found__")
    return out


CAUSAL_RULES = [
    Rule(name="missing_mystery", tag="story", apply=_r_missing_mystery),
    Rule(name="clue_visible", tag="story", apply=_r_clue_visible),
    Rule(name="track_to_find", tag="story", apply=_r_track_to_find),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            res = rule.apply(world)
            if res:
                changed = True
                produced.extend(res)
    if narrate:
        for item in produced:
            if not item.startswith("__"):
                world.say(item)
    return produced


SETTINGS = {
    "clubhouse": Setting(
        id="clubhouse",
        label="the mystery clubhouse",
        opening="The little mystery clubhouse smelled of paper, crayons, and old wooden boards.",
        hideouts={"shiny": "window_ledge", "hungry": "snack_bench", "cozy": "blanket_nest"},
        culprits={"puppy", "magpie", "toddler"},
        tags={"clubhouse"},
    ),
    "backyard": Setting(
        id="backyard",
        label="the backyard",
        opening="The backyard was bright with daisies, fence shadows, and one crooked birdbath.",
        hideouts={"shiny": "flowerpot", "hungry": "garden_step", "cozy": "blanket_nest"},
        culprits={"puppy", "magpie", "squirrel"},
        tags={"backyard"},
    ),
    "classroom": Setting(
        id="classroom",
        label="the classroom reading corner",
        opening="The classroom reading corner was quiet except for the soft rustle of picture-book pages.",
        hideouts={"shiny": "window_ledge", "hungry": "snack_bench", "cozy": "blanket_nest"},
        culprits={"puppy", "toddler"},
        tags={"classroom"},
    ),
}

ITEMS = {
    "silver_whistle": Item(
        id="silver_whistle",
        label="silver whistle",
        phrase="the silver whistle with the blue cord",
        size=1,
        motive="shiny",
        importance="It was the whistle Detective Club used to open every case.",
        tags={"whistle", "shiny"},
    ),
    "jam_tart": Item(
        id="jam_tart",
        label="jam tart",
        phrase="the little jam tart on the paper plate",
        size=1,
        motive="hungry",
        importance="It was the snack prize for whoever solved the first clue.",
        tags={"tart", "food"},
    ),
    "velvet_scarf": Item(
        id="velvet_scarf",
        label="velvet scarf",
        phrase="the soft velvet scarf from the costume box",
        size=2,
        motive="cozy",
        importance="It was the detective cape for the grand pretend reveal.",
        tags={"scarf", "soft"},
    ),
}

CULPRITS = {
    "puppy": Culprit(
        id="puppy",
        label="puppy",
        phrase="a wiggly brown puppy",
        verb="trotted off with it",
        clue="muddy paw prints",
        clue_detail="four tiny muddy paw prints dotted the floor",
        sound="a happy little snuffle",
        max_size=2,
        likes={"cozy", "hungry"},
        tags={"puppy", "paw_prints"},
    ),
    "magpie": Culprit(
        id="magpie",
        label="magpie",
        phrase="a glossy black-and-white magpie",
        verb="snatched it in its beak and fluttered away",
        clue="one black feather",
        clue_detail="one black feather lay by the open window, gleaming at the edge",
        sound="a scratchy clack from above",
        max_size=1,
        likes={"shiny"},
        tags={"magpie", "feather"},
    ),
    "squirrel": Culprit(
        id="squirrel",
        label="squirrel",
        phrase="a stripe-tailed squirrel",
        verb="nipped it up and scampered away",
        clue="a trail of tiny crumbs",
        clue_detail="a trail of tiny crumbs led away in a neat, greedy zigzag",
        sound="a quick rustle in the leaves",
        max_size=1,
        likes={"hungry"},
        tags={"squirrel", "crumbs"},
    ),
    "toddler": Culprit(
        id="toddler",
        label="toddler",
        phrase="a tiny toddler with round cheeks",
        verb="carried it away in both hands",
        clue="sticky finger marks",
        clue_detail="sticky little finger marks shone on the table edge",
        sound="a muffled giggle behind something soft",
        max_size=2,
        likes={"shiny", "cozy", "hungry"},
        tags={"toddler", "fingerprints"},
    ),
}

HIDEOUTS = {
    "window_ledge": Hideout(
        id="window_ledge",
        label="window ledge",
        phrase="the sunny window ledge",
        scene="where sunbeams made bright squares on the wood",
        tags={"window"},
    ),
    "flowerpot": Hideout(
        id="flowerpot",
        label="flowerpot",
        phrase="the biggest flowerpot by the fence",
        scene="where marigolds leaned over the rim",
        tags={"flowerpot"},
    ),
    "snack_bench": Hideout(
        id="snack_bench",
        label="bench",
        phrase="the shadow under the snack bench",
        scene="where crumbs liked to hide in the cracks",
        tags={"bench"},
    ),
    "garden_step": Hideout(
        id="garden_step",
        label="garden step",
        phrase="the warm garden step",
        scene="where dropped crumbs could rest in the sun",
        tags={"step"},
    ),
    "blanket_nest": Hideout(
        id="blanket_nest",
        label="blanket nest",
        phrase="the blanket nest in the corner",
        scene="where soft blankets made a sleepy heap",
        tags={"blanket"},
    ),
}


@dataclass
class StoryParams:
    setting: str
    item: str
    culprit: str
    detective: str
    detective_gender: str
    helper: str
    helper_gender: str
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


CURATED = [
    StoryParams(
        setting="backyard",
        item="silver_whistle",
        culprit="magpie",
        detective="Nora",
        detective_gender="girl",
        helper="Ben",
        helper_gender="boy",
    ),
    StoryParams(
        setting="clubhouse",
        item="velvet_scarf",
        culprit="puppy",
        detective="Theo",
        detective_gender="boy",
        helper="Maya",
        helper_gender="girl",
    ),
    StoryParams(
        setting="classroom",
        item="jam_tart",
        culprit="toddler",
        detective="Lily",
        detective_gender="girl",
        helper="Max",
        helper_gender="boy",
    ),
    StoryParams(
        setting="backyard",
        item="jam_tart",
        culprit="squirrel",
        detective="Eli",
        detective_gender="boy",
        helper="Zoe",
        helper_gender="girl",
    ),
]

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Anna", "Maya", "Nora", "Rose"]
BOY_NAMES = ["Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Noah", "Eli", "Theo", "Owen"]


def select_hideout(setting_id: str, item_id: str) -> Hideout:
    if setting_id not in SETTINGS or item_id not in ITEMS:
        raise StoryError("(No story: unknown setting or item.)")
    motive = ITEMS[item_id].motive
    hide_id = SETTINGS[setting_id].hideouts.get(motive)
    if hide_id is None or hide_id not in HIDEOUTS:
        raise StoryError("(No story: this setting has nowhere plausible to hide that item.)")
    return HIDEOUTS[hide_id]


def culprit_can_take(culprit_id: str, item_id: str) -> bool:
    culprit = CULPRITS[culprit_id]
    item = ITEMS[item_id]
    return item.size <= culprit.max_size and item.motive in culprit.likes


def valid_combo(setting_id: str, item_id: str, culprit_id: str) -> bool:
    if setting_id not in SETTINGS or item_id not in ITEMS or culprit_id not in CULPRITS:
        return False
    setting = SETTINGS[setting_id]
    if culprit_id not in setting.culprits:
        return False
    if not culprit_can_take(culprit_id, item_id):
        return False
    motive = ITEMS[item_id].motive
    return motive in setting.hideouts and setting.hideouts[motive] in HIDEOUTS


def valid_combos() -> list[tuple[str, str, str]]:
    out: list[tuple[str, str, str]] = []
    for setting_id in SETTINGS:
        for item_id in ITEMS:
            for culprit_id in CULPRITS:
                if valid_combo(setting_id, item_id, culprit_id):
                    out.append((setting_id, item_id, culprit_id))
    return out


def explain_rejection(setting_id: str, item_id: str, culprit_id: str) -> str:
    if setting_id not in SETTINGS:
        return f"(No story: unknown setting '{setting_id}'.)"
    if item_id not in ITEMS:
        return f"(No story: unknown item '{item_id}'.)"
    if culprit_id not in CULPRITS:
        return f"(No story: unknown culprit '{culprit_id}'.)"
    setting = SETTINGS[setting_id]
    item = ITEMS[item_id]
    culprit = CULPRITS[culprit_id]
    if culprit_id not in setting.culprits:
        return (
            f"(No story: {setting.label} does not plausibly include a {culprit.label}, "
            f"so there is no fair mystery to solve there.)"
        )
    if item.motive not in culprit.likes:
        return (
            f"(No story: a {culprit.label} would not be tempted by {item.phrase}. "
            f"The culprit needs a clear reason to take the missing item.)"
        )
    if item.size > culprit.max_size:
        return (
            f"(No story: {item.phrase} is too bulky for a {culprit.label} to carry away, "
            f"so the disappearance would not make sense.)"
        )
    if item.motive not in setting.hideouts:
        return (
            f"(No story: {setting.label} has no plausible hiding place for something "
            f"taken for a {item.motive} reason.)"
        )
    return "(No story: that combination is not reasonable.)"


def motive_reason(item: Item, culprit: Culprit) -> str:
    if item.motive == "shiny":
        return f"The {culprit.label} had been dazzled by the sparkle."
    if item.motive == "hungry":
        return f"The {culprit.label} had followed the sweet smell."
    return f"The {culprit.label} only wanted something soft and snug."


def ending_fix(item: Item, culprit: Culprit, hideout: Hideout) -> str:
    if item.motive == "shiny":
        return (
            f"After that, the club hung the {item.label} on a hook instead of leaving it to glitter by itself, "
            f"and the {culprit.label} stayed busy pecking at bottle-cap toys near {hideout.phrase}."
        )
    if item.motive == "hungry":
        return (
            f"After that, the snack stayed on a high shelf until the game was over, "
            f"and a proper crumb corner was set far away from {hideout.phrase}."
        )
    return (
        f"After that, the soft things for animals and the costume things for detectives lived in different places, "
        f"so no one mixed up a nest with a cape again."
    )


def _do_theft(world: World) -> None:
    culprit = world.get("culprit")
    item = world.get("item")
    culprit.meters["carried_item"] += 1
    item.meters["missing"] += 1
    item.attrs["hidden_by"] = culprit.id
    propagate(world, narrate=False)


def open_case(world: World, detective: Entity, helper: Entity, item: Item) -> None:
    world.say(
        f"{world.setting.opening} {detective.id} and {helper.id} had planned a terrific morning for Detective Club."
    )
    world.say(
        f'"First we open the case with {item.phrase}," {helper.id} said.'
    )
    world.say(item.importance)


def discover_loss(world: World, detective: Entity, helper: Entity, item_ent: Entity, item: Item) -> None:
    _do_theft(world)
    world.say(
        f"But when {detective.id} reached for {item.phrase}, it was gone."
    )
    world.say(
        f"{helper.id} looked under the table and inside the supply box, but {item_ent.label} was nowhere."
    )
    world.say(
        f'{detective.id} straightened up and whispered, "A real mystery to solve."'
    )


def inspect_clue(world: World, detective: Entity, helper: Entity, culprit: Culprit, hideout: Hideout) -> None:
    detective.meters["inspecting"] += 1
    world.say(
        f"{detective.id} made a tiny squinch with one eye and studied the room."
    )
    world.say(
        f"There it was: {culprit.clue_detail}."
    )
    world.say(
        f'"That clue points toward {hideout.label}," {detective.id} said, tapping the air softly.'
    )
    helper.memes["trust"] += 1


def track_clue(world: World, detective: Entity, helper: Entity, culprit: Culprit, hideout: Hideout) -> None:
    detective.meters["tracking"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{detective.id} and {helper.id} followed the sign past chair legs and boxes until they reached {hideout.phrase}, {hideout.scene}."
    )
    world.say(
        f"From there came {culprit.sound}."
    )


def reveal(world: World, detective: Entity, helper: Entity, culprit_ent: Entity,
           item_ent: Entity, culprit: Culprit, item: Item, hideout: Hideout) -> None:
    culprit_ent.memes["startled"] += 1
    detective.memes["kindness"] += 1
    world.say(
        f"And there was the culprit: {culprit.phrase}, with the {item.label} beside it."
    )
    world.say(
        f'{helper.id} gasped. "{culprit.label.capitalize()}!"'
    )
    world.say(
        f'{detective.id} smiled instead of scolding. "{motive_reason(item, culprit)}"'
    )


def resolve_case(world: World, detective: Entity, helper: Entity, culprit_ent: Entity,
                 item_ent: Entity, culprit: Culprit, item: Item, hideout: Hideout) -> None:
    item_ent.attrs["hidden_by"] = ""
    item_ent.attrs["location"] = "returned"
    culprit_ent.memes["calm"] += 1
    detective.memes["pride"] += 1
    helper.memes["joy"] += 1
    world.say(
        f"{detective.id} picked up the {item.label}, brushed it clean, and handed it to {helper.id}."
    )
    world.say(
        f'"Case closed," {detective.pronoun()} said. "{helper.id}, our clue was fair, our guess was careful, and the mystery is solved."'
    )
    world.say(ending_fix(item, culprit, hideout))


def tell(setting: Setting, item: Item, culprit: Culprit, hideout: Hideout,
         detective_name: str = "Nora", detective_gender: str = "girl",
         helper_name: str = "Ben", helper_gender: str = "boy") -> World:
    world = World(setting)
    detective = world.add(Entity(
        id=detective_name,
        kind="character",
        type=detective_gender,
        label=detective_name,
        role="detective",
    ))
    helper = world.add(Entity(
        id=helper_name,
        kind="character",
        type=helper_gender,
        label=helper_name,
        role="helper",
    ))
    culprit_ent = world.add(Entity(
        id="culprit",
        kind="character",
        type="animal" if culprit.id in {"puppy", "magpie", "squirrel"} else "child",
        label=culprit.label,
        phrase=culprit.phrase,
        role="culprit",
    ))
    item_ent = world.add(Entity(
        id="item",
        type="item",
        label=item.label,
        phrase=item.phrase,
        attrs={"hidden_by": "", "location": "table"},
    ))
    clue = world.add(Entity(
        id="clue",
        type="clue",
        label=culprit.clue,
        phrase=culprit.clue,
    ))
    world.add(Entity(id="room", type="place", label=setting.label))
    world.add(Entity(id="hideout", type="place", label=hideout.label, phrase=hideout.phrase))

    world.facts.update(
        setting=setting,
        item_cfg=item,
        culprit_cfg=culprit,
        hideout_cfg=hideout,
        detective=detective,
        helper=helper,
        culprit=culprit_ent,
        item=item_ent,
        clue=clue,
    )

    open_case(world, detective, helper, item)
    world.para()
    discover_loss(world, detective, helper, item_ent, item)
    world.para()
    inspect_clue(world, detective, helper, culprit, hideout)
    track_clue(world, detective, helper, culprit, hideout)
    world.para()
    reveal(world, detective, helper, culprit_ent, item_ent, culprit, item, hideout)
    resolve_case(world, detective, helper, culprit_ent, item_ent, culprit, item, hideout)

    world.facts.update(
        solved=item_ent.meters["found"] >= THRESHOLD,
        mystery_open=world.get("room").meters["mystery"] >= THRESHOLD,
        returned=item_ent.attrs.get("location") == "returned",
        reason=motive_reason(item, culprit),
    )
    return world


KNOWLEDGE = {
    "detective": [
        (
            "What does a detective do?",
            "A detective notices clues, asks careful questions, and uses those clues to solve a mystery. Good detectives do not just guess wildly."
        )
    ],
    "clue": [
        (
            "What is a clue?",
            "A clue is a small sign that helps you understand what happened. It can point your thinking in the right direction."
        )
    ],
    "puppy": [
        (
            "Why do puppies carry things away?",
            "Puppies explore with their mouths and noses, so they often carry soft or tasty things away. They are usually being curious, not mean."
        )
    ],
    "magpie": [
        (
            "Why might a magpie take a shiny thing?",
            "Magpies notice bright, glittery objects very quickly. A shiny thing can catch a bird's eye and make it want to peck or carry it."
        )
    ],
    "squirrel": [
        (
            "Why do squirrels chase food?",
            "Squirrels are always looking for something to nibble or store. If they smell a treat, they hurry toward it."
        )
    ],
    "toddler": [
        (
            "Why do toddlers move things around?",
            "Toddlers like to pick things up, carry them, and put them in new places. They are learning how the world works."
        )
    ],
    "whistle": [
        (
            "What is a whistle for?",
            "A whistle makes a strong sharp sound that people can hear easily. It can be used to start a game or get attention."
        )
    ],
    "tart": [
        (
            "What is a jam tart?",
            "A jam tart is a small pastry with sweet fruit jam inside. It is soft, sticky, and smells good."
        )
    ],
    "scarf": [
        (
            "What is a scarf?",
            "A scarf is a soft piece of cloth you can wear or wrap around something. It can feel warm and cozy."
        )
    ],
}
KNOWLEDGE_ORDER = ["detective", "clue", "puppy", "magpie", "squirrel", "toddler", "whistle", "tart", "scarf"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    detective = f["detective"]
    helper = f["helper"]
    item = f["item_cfg"]
    setting = f["setting"]
    culprit = f["culprit_cfg"]
    return [
        f'Write a short Detective Story for a 3-to-5-year-old that includes the words "terrific" and "squinch" and centers on a mystery to solve.',
        f"Tell a gentle detective story where {detective.id} and {helper.id} notice that {item.phrase} is missing in {setting.label}, then solve the mystery by following a fair clue.",
        f"Write a child-friendly mystery in which the culprit is a {culprit.label}, the missing object matters to a little club, and the ending is kind instead of angry.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    detective = f["detective"]
    helper = f["helper"]
    item = f["item_cfg"]
    culprit = f["culprit_cfg"]
    hideout = f["hideout_cfg"]
    out = [
        (
            "Who is the story about?",
            f"It is about {detective.id}, a child detective, and {helper.id}, the helper on the case. Together they try to find the missing {item.label}."
        ),
        (
            f"Why did the missing {item.label} matter?",
            f"It mattered because {item.importance.lower()} That made the disappearance feel like a real case instead of a small mix-up."
        ),
        (
            f"What clue did {detective.id} notice?",
            f"{detective.id} noticed {culprit.clue}. That clue mattered because it pointed the search away from guessing and toward {hideout.phrase}."
        ),
        (
            f"How did {detective.id} solve the mystery?",
            f"{detective.id} gave one eye a little squinch, studied the clue carefully, and followed it with {helper.id}. They found the missing {item.label} at {hideout.phrase} because the clue led them there."
        ),
        (
            f"Why had the {culprit.label} taken the {item.label}?",
            f"{motive_reason(item, culprit)} It was not trying to ruin the game; it was following its own simple wish."
        ),
        (
            "How did the story end?",
            f"The {item.label} was returned, the case was closed, and everyone understood what had happened. The ending proves things changed because the club made a better plan so the same mix-up would not happen again."
        ),
    ]
    return out


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"detective", "clue"} | set(f["item_cfg"].tags) | set(f["culprit_cfg"].tags)
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
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
tempted(C, I) :- likes(C, M), motive(I, M).
movable(C, I) :- max_size(C, MC), size(I, SI), SI <= MC.
valid(S, I, C) :- setting(S), item(I), culprit(C),
                  present(S, C), tempted(C, I), movable(C, I),
                  motive(I, M), hideout_for(S, M, _).

chosen_hideout(H) :- chosen_setting(S), chosen_item(I), motive(I, M), hideout_for(S, M, H).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for setting_id, setting in SETTINGS.items():
        lines.append(asp.fact("setting", setting_id))
        for culprit_id in sorted(setting.culprits):
            lines.append(asp.fact("present", setting_id, culprit_id))
        for motive, hideout_id in sorted(setting.hideouts.items()):
            lines.append(asp.fact("hideout_for", setting_id, motive, hideout_id))
    for item_id, item in ITEMS.items():
        lines.append(asp.fact("item", item_id))
        lines.append(asp.fact("size", item_id, item.size))
        lines.append(asp.fact("motive", item_id, item.motive))
    for culprit_id, culprit in CULPRITS.items():
        lines.append(asp.fact("culprit", culprit_id))
        lines.append(asp.fact("max_size", culprit_id, culprit.max_size))
        for motive in sorted(culprit.likes):
            lines.append(asp.fact("likes", culprit_id, motive))
    for hideout_id in HIDEOUTS:
        lines.append(asp.fact("hideout", hideout_id))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_hideout(setting_id: str, item_id: str) -> str:
    import asp

    extra = "\n".join([
        asp.fact("chosen_setting", setting_id),
        asp.fact("chosen_item", item_id),
    ])
    model = asp.one_model(asp_program(extra, "#show chosen_hideout/1."))
    atoms = asp.atoms(model, "chosen_hideout")
    return atoms[0][0] if atoms else ""


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Storyworld: a gentle detective mystery with a fair clue and a kind solution."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--culprit", choices=CULPRITS)
    ap.add_argument("--detective")
    ap.add_argument("--helper")
    ap.add_argument("--detective-gender", choices=["girl", "boy"])
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combinations from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: Optional[str], avoid: str = "") -> tuple[str, str]:
    chosen_gender = gender or rng.choice(["girl", "boy"])
    pool = GIRL_NAMES if chosen_gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices), chosen_gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.item and args.culprit:
        if not valid_combo(args.setting, args.item, args.culprit):
            raise StoryError(explain_rejection(args.setting, args.item, args.culprit))

    combos = [
        combo for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.item is None or combo[1] == args.item)
        and (args.culprit is None or combo[2] == args.culprit)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, item_id, culprit_id = rng.choice(sorted(combos))
    detective_name, detective_gender = _pick_name(rng, args.detective_gender)
    helper_name, helper_gender = _pick_name(rng, args.helper_gender, avoid=detective_name)
    if args.detective:
        detective_name = args.detective
    if args.helper:
        helper_name = args.helper
        if helper_name == detective_name:
            helper_name = f"{helper_name} Junior"

    return StoryParams(
        setting=setting_id,
        item=item_id,
        culprit=culprit_id,
        detective=detective_name,
        detective_gender=detective_gender,
        helper=helper_name,
        helper_gender=helper_gender,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(No story: unknown setting '{params.setting}'.)")
    if params.item not in ITEMS:
        raise StoryError(f"(No story: unknown item '{params.item}'.)")
    if params.culprit not in CULPRITS:
        raise StoryError(f"(No story: unknown culprit '{params.culprit}'.)")
    if not valid_combo(params.setting, params.item, params.culprit):
        raise StoryError(explain_rejection(params.setting, params.item, params.culprit))

    hideout = select_hideout(params.setting, params.item)
    world = tell(
        setting=SETTINGS[params.setting],
        item=ITEMS[params.item],
        culprit=CULPRITS[params.culprit],
        hideout=hideout,
        detective_name=params.detective,
        detective_gender=params.detective_gender,
        helper_name=params.helper,
        helper_gender=params.helper_gender,
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

    py_combos = set(valid_combos())
    clingo_combos = set(asp_valid_combos())
    if py_combos == clingo_combos:
        print(f"OK: valid_combos matches ASP ({len(py_combos)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combinations:")
        if clingo_combos - py_combos:
            print("  only in clingo:", sorted(clingo_combos - py_combos))
        if py_combos - clingo_combos:
            print("  only in python:", sorted(py_combos - clingo_combos))

    cases = list(CURATED)
    for s in range(50):
        try:
            p = resolve_params(build_parser().parse_args([]), random.Random(s))
        except StoryError:
            continue
        p.seed = s
        cases.append(p)

    bad_hideouts = []
    for params in cases:
        py_hideout = select_hideout(params.setting, params.item).id
        clingo_hideout = asp_hideout(params.setting, params.item)
        if py_hideout != clingo_hideout:
            bad_hideouts.append((params.setting, params.item, py_hideout, clingo_hideout))
    if not bad_hideouts:
        print(f"OK: hideout inference matches ASP on {len(cases)} scenarios.")
    else:
        rc = 1
        print("MISMATCH in hideout inference:")
        for row in bad_hideouts[:10]:
            print(" ", row)

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("empty story")
        with contextlib.redirect_stdout(io.StringIO()):
            emit(smoke, trace=True, qa=True, header="### smoke")
        _ = smoke.to_json()
        print("OK: smoke test generate/emit/json succeeded.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show chosen_hideout/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, item, culprit) combos:\n")
        for setting_id, item_id, culprit_id in combos:
            hideout = asp_hideout(setting_id, item_id)
            print(f"  {setting_id:10} {item_id:14} {culprit_id:8} -> {hideout}")
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
            header = f"### {p.detective}: {p.item} in {p.setting} ({p.culprit})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
