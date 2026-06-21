#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/legendary_rocky_shore_quest_happy_ending_slice.py
============================================================================

A standalone story world for a small, slice-of-life quest on a rocky shore.

A child and a grown-up go looking for one little shore treasure that has been
talked up as "legendary" in the family. The quest feels grand to the child, but
the day itself stays ordinary and cozy: pockets, tea towels, wet stones, and a
walk home with a small prize.

The world model enforces a reasonableness rule:
    a retrieval tool must work for the treasure's spot,
    and fragile treasures need a gentle method.

So a hook can fetch a sturdy lucky stone from a rock crevice, but it is refused
for a delicate spiral shell. A net can scoop from a tide pool. Waiting is only
a real method at the wave line, where the sea itself can slide the treasure
closer.

Run it
------
    python storyworlds/worlds/gpt-5.4/legendary_rocky_shore_quest_happy_ending_slice.py
    python storyworlds/worlds/gpt-5.4/legendary_rocky_shore_quest_happy_ending_slice.py --item spiral_shell --spot crevice --tool hook
    python storyworlds/worlds/gpt-5.4/legendary_rocky_shore_quest_happy_ending_slice.py --all
    python storyworlds/worlds/gpt-5.4/legendary_rocky_shore_quest_happy_ending_slice.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/legendary_rocky_shore_quest_happy_ending_slice.py --verify
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
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    fragile: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "grandmother", "woman"}
        male = {"boy", "father", "grandfather", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        mapping = {
            "mother": "mom",
            "father": "dad",
            "grandmother": "grandma",
            "grandfather": "grandpa",
        }
        return mapping.get(self.type, self.type)
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
class ShoreItem:
    id: str
    label: str
    phrase: str
    legend: str
    color: str
    fragile: bool = False
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
    slippery: bool
    surfy: bool
    sight: str
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
class Tool:
    id: str
    label: str
    phrase: str
    gentle: bool
    works_on: set[str] = field(default_factory=set)
    action: str = ""
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
class Quest:
    id: str
    want: str
    ending: str
    keep_place: str
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
    item: str
    spot: str
    tool: str
    quest: str
    child_name: str
    child_gender: str
    helper_name: str
    helper_type: str
    child_trait: str
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


def _r_wobble(world: World) -> list[str]:
    hero = world.get("child")
    shore = world.get("shore")
    if hero.memes["bare_reach"] < THRESHOLD or shore.meters["slippery"] < THRESHOLD:
        return []
    sig = ("wobble",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.meters["wobble"] += 1
    world.get("helper").memes["worry"] += 1
    return ["__wobble__"]


def _r_drift(world: World) -> list[str]:
    hero = world.get("child")
    shore = world.get("shore")
    item = world.get("item")
    if hero.memes["bare_reach"] < THRESHOLD or shore.meters["surge"] < THRESHOLD:
        return []
    sig = ("drift",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    item.meters["drifting"] += 1
    world.get("helper").memes["worry"] += 1
    return ["__drift__"]


def _r_chip(world: World) -> list[str]:
    item = world.get("item")
    if not item.fragile or item.meters["jostled"] < THRESHOLD:
        return []
    sig = ("chip",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    item.meters["chipped"] += 1
    world.get("child").memes["sad"] += 1
    return ["__chip__"]


def _r_hope(world: World) -> list[str]:
    item = world.get("item")
    if item.meters["found"] < THRESHOLD:
        return []
    sig = ("hope",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    world.get("child").memes["hope"] += 1
    world.get("helper").memes["relief"] += 1
    return []


def _r_joy(world: World) -> list[str]:
    item = world.get("item")
    if item.meters["kept"] < THRESHOLD:
        return []
    sig = ("joy",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    world.get("child").memes["joy"] += 1
    world.get("helper").memes["joy"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="wobble", tag="physical", apply=_r_wobble),
    Rule(name="drift", tag="physical", apply=_r_drift),
    Rule(name="chip", tag="physical", apply=_r_chip),
    Rule(name="hope", tag="emotional", apply=_r_hope),
    Rule(name="joy", tag="emotional", apply=_r_joy),
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
    if narrate:
        for line in produced:
            if not line.startswith("__"):
                world.say(line)
    return produced


ITEMS = {
    "sea_glass": ShoreItem(
        id="sea_glass",
        label="sea glass",
        phrase="a piece of green sea glass",
        legend="some families said the smoothest piece was a legendary bit of old bottle turned kind by the sea",
        color="green",
        fragile=False,
        tags={"sea_glass", "shore_treasure"},
    ),
    "spiral_shell": ShoreItem(
        id="spiral_shell",
        label="spiral shell",
        phrase="a small cream spiral shell",
        legend="grandparents liked to call the prettiest one a legendary shell because children always remembered the day they found it",
        color="cream",
        fragile=True,
        tags={"shell", "shore_treasure"},
    ),
    "lucky_stone": ShoreItem(
        id="lucky_stone",
        label="lucky stone",
        phrase="a round gray lucky stone with a white stripe",
        legend="the old shore story said a striped stone could be a legendary lucky stone if you noticed it before the gulls did",
        color="gray",
        fragile=False,
        tags={"stone", "shore_treasure"},
    ),
}

SPOTS = {
    "tide_pool": Spot(
        id="tide_pool",
        label="tide pool",
        phrase="a clear tide pool between two dark rocks",
        slippery=True,
        surfy=False,
        sight="There it was, shining under a skin of still water.",
        tags={"tide_pool", "rocky_shore"},
    ),
    "crevice": Spot(
        id="crevice",
        label="rock crevice",
        phrase="a narrow rock crevice lined with damp seaweed",
        slippery=True,
        surfy=False,
        sight="There it was, tucked where the rocks met in a dark little crack.",
        tags={"crevice", "rocky_shore"},
    ),
    "wave_line": Spot(
        id="wave_line",
        label="wave line",
        phrase="the place where the foam slid up and back over the stones",
        slippery=False,
        surfy=True,
        sight="There it was, appearing and hiding again each time the foam ran over the stones.",
        tags={"wave_line", "rocky_shore"},
    ),
}

TOOLS = {
    "net": Tool(
        id="net",
        label="net",
        phrase="a little beach net",
        gentle=True,
        works_on={"tide_pool", "wave_line"},
        action="slid the little beach net under it and lifted carefully",
        tags={"net", "tool"},
    ),
    "cloth_hand": Tool(
        id="cloth_hand",
        label="tea towel",
        phrase="a folded tea towel",
        gentle=True,
        works_on={"crevice"},
        action="wrapped a folded tea towel around a careful hand and eased it free without scraping it",
        tags={"cloth", "tool"},
    ),
    "hook": Tool(
        id="hook",
        label="driftwood hook",
        phrase="a driftwood hook",
        gentle=False,
        works_on={"crevice", "wave_line"},
        action="reached in with the driftwood hook and nudged it into the open",
        tags={"hook", "tool"},
    ),
    "wait": Tool(
        id="wait",
        label="waiting",
        phrase="a little patient waiting",
        gentle=True,
        works_on={"wave_line"},
        action="waited for the next soft wash of water to slide it closer, then picked it up at the dry edge",
        tags={"waiting", "tool"},
    ),
}

QUESTS = {
    "windowsill": Quest(
        id="windowsill",
        want="to find one shore treasure for the sunny windowsill at home",
        ending="set it on the windowsill in a little saucer, where the late light made it glow",
        keep_place="windowsill",
        tags={"home", "keepsake"},
    ),
    "gift": Quest(
        id="gift",
        want="to find one small shore treasure to give away after supper",
        ending="wrapped it in a napkin and laid it beside a teacup as a tiny gift",
        keep_place="gift table",
        tags={"gift", "home"},
    ),
    "pocket": Quest(
        id="pocket",
        want="to find one lucky treasure to keep in a coat pocket for ordinary brave days",
        ending="slipped it into a pocket and patted it there all through the walk home",
        keep_place="pocket",
        tags={"pocket", "home"},
    ),
}

GIRL_NAMES = ["Lina", "Maya", "Nora", "Tess", "Ruby", "Ivy", "Anna", "Wren"]
BOY_NAMES = ["Owen", "Ben", "Milo", "Finn", "Eli", "Theo", "Sam", "Noah"]
CHILD_TRAITS = ["patient", "eager", "careful", "bright-eyed", "curious"]
HELPERS = ["mother", "father", "grandmother", "grandfather"]


def tool_fits(item: ShoreItem, spot: Spot, tool: Tool) -> bool:
    if spot.id not in tool.works_on:
        return False
    if item.fragile and not tool.gentle:
        return False
    return True


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for item_id, item in ITEMS.items():
        for spot_id, spot in SPOTS.items():
            for tool_id, tool in TOOLS.items():
                if tool_fits(item, spot, tool):
                    combos.append((item_id, spot_id, tool_id))
    return combos


def explain_rejection(item: ShoreItem, spot: Spot, tool: Tool) -> str:
    if spot.id not in tool.works_on:
        works = ", ".join(sorted(tool.works_on))
        return (
            f"(No story: {tool.phrase} does not honestly solve {spot.phrase}. "
            f"It works at: {works}.)"
        )
    if item.fragile and not tool.gentle:
        return (
            f"(No story: {item.label} is delicate, and {tool.phrase} is too rough. "
            f"Pick a gentler method.)"
        )
    return "(No story: that combination is not reasonable here.)"


def predict_bare_reach(world: World) -> dict:
    sim = world.copy()
    child = sim.get("child")
    item = sim.get("item")
    child.memes["bare_reach"] += 1
    if item.fragile:
        item.meters["jostled"] += 1
    propagate(sim, narrate=False)
    return {
        "wobble": child.meters["wobble"] >= THRESHOLD,
        "drift": item.meters["drifting"] >= THRESHOLD,
        "chip": item.meters["chipped"] >= THRESHOLD,
    }


def introduce(world: World, child: Entity, helper: Entity) -> None:
    world.say(
        f"After breakfast, {child.id} and {helper.label_word} walked down to the rocky shore. "
        f"The stones were dark from the tide, gulls were stepping about like busy neighbors, "
        f"and the sea kept breathing in and out beside them."
    )
    world.say(
        f"{child.id} was a {child.traits[0]} little {child.type}, the kind who noticed "
        f"bright things between plain ones."
    )


def quest_setup(world: World, child: Entity, helper: Entity, item_cfg: ShoreItem, quest: Quest) -> None:
    child.memes["questing"] += 1
    world.say(
        f"They had a small quest that morning: {quest.want}. "
        f'{helper.label_word.capitalize()} smiled and called it their "legendary shore quest," '
        f"which made {child.id} stand a little taller."
    )
    world.say(item_cfg.legend[0].upper() + item_cfg.legend[1:] + ".")


def discover(world: World, child: Entity, item_cfg: ShoreItem, spot: Spot) -> None:
    child.memes["wonder"] += 1
    world.say(
        f"They looked among barnacled rocks and strings of seaweed until {child.id} saw "
        f"{item_cfg.phrase} in {spot.phrase}. {spot.sight}"
    )


def warn(world: World, child: Entity, helper: Entity, item_cfg: ShoreItem, spot: Spot) -> None:
    pred = predict_bare_reach(world)
    world.facts["predicted_wobble"] = pred["wobble"]
    world.facts["predicted_drift"] = pred["drift"]
    world.facts["predicted_chip"] = pred["chip"]

    parts = []
    if pred["wobble"]:
        parts.append("the wet rock could make you wobble")
    if pred["drift"]:
        parts.append("the next wash could pull it away")
    if pred["chip"]:
        parts.append(f"you might crack the {item_cfg.label}")
    if not parts:
        parts.append("rushing would be a poor way to begin")

    if len(parts) == 1:
        risk = parts[0]
    elif len(parts) == 2:
        risk = f"{parts[0]}, and {parts[1]}"
    else:
        risk = f"{parts[0]}, {parts[1]}, and {parts[2]}"

    helper.memes["care"] += 1
    world.say(
        f'{child.id} took one eager step forward, but {helper.label_word} touched '
        f'{child.pronoun("possessive")} sleeve. "Slowly," {helper.pronoun()} said. '
        f'"If you grab at it now, {risk}."'
    )


def choose_method(world: World, child: Entity, helper: Entity, tool: Tool) -> None:
    child.memes["listening"] += 1
    world.say(
        f'That made {child.id} stop and think. "{tool.phrase}?" {child.pronoun()} asked.'
    )
    world.say(
        f'"Yes," said {helper.label_word}. "A small quest still deserves a sensible way."'
    )


def collect(world: World, child: Entity, helper: Entity, tool: Tool, item_cfg: ShoreItem) -> None:
    item = world.get("item")
    world.say(
        f"So they tried the careful plan. {helper.label_word.capitalize()} {tool.action}. "
        f"A second later, {item_cfg.phrase} was safe in {child.id}'s palm."
    )
    item.meters["found"] += 1
    item.meters["dry"] += 1
    item.meters["kept"] += 1
    propagate(world, narrate=False)
    helper.memes["pride"] += 1
    child.memes["relief"] += 1


def celebrate(world: World, child: Entity, helper: Entity, item_cfg: ShoreItem, quest: Quest) -> None:
    world.say(
        f"{child.id} rinsed the little treasure in a splash of clean water and held it up. "
        f'In the gray shore light, it really did look a bit legendary.'
    )
    world.say(
        f"On the walk home, the rocks no longer felt like a puzzle to beat, only part of the story "
        f"they had just solved together."
    )
    world.say(
        f"At home, they {quest.ending}. {child.id} looked at {item_cfg.label} once more and smiled, "
        f"because the best part of the quest was not only finding it, but finding it carefully."
    )


def tell(
    item_cfg: ShoreItem,
    spot: Spot,
    tool: Tool,
    quest: Quest,
    child_name: str = "Nora",
    child_gender: str = "girl",
    helper_name: str = "Grandpa",
    helper_type: str = "grandfather",
    child_trait: str = "curious",
) -> World:
    world = World()

    child = world.add(
        Entity(
            id="child",
            kind="character",
            type=child_gender,
            label=child_name,
            role="child",
            traits=[child_trait],
            attrs={},
        )
    )
    helper = world.add(
        Entity(
            id="helper",
            kind="character",
            type=helper_type,
            label=helper_name,
            role="helper",
            traits=["calm"],
            attrs={},
        )
    )
    shore = world.add(
        Entity(
            id="shore",
            kind="thing",
            type="shore",
            label="rocky shore",
            attrs={"spot": spot.id},
        )
    )
    item = world.add(
        Entity(
            id="item",
            kind="thing",
            type="treasure",
            label=item_cfg.label,
            attrs={"color": item_cfg.color, "spot": spot.id},
            fragile=item_cfg.fragile,
        )
    )
    world.add(
        Entity(
            id="tool",
            kind="thing",
            type="tool",
            label=tool.label,
            attrs={"tool_id": tool.id},
        )
    )

    if spot.slippery:
        shore.meters["slippery"] = 1
    if spot.surfy:
        shore.meters["surge"] = 1

    child.memes["questing"] = 0.0
    child.memes["bare_reach"] = 0.0
    child.memes["joy"] = 0.0
    helper.memes["worry"] = 0.0
    item.meters["jostled"] = 0.0
    item.meters["found"] = 0.0
    item.meters["kept"] = 0.0

    introduce(world, child, helper)
    quest_setup(world, child, helper, item_cfg, quest)

    world.para()
    discover(world, child, item_cfg, spot)
    warn(world, child, helper, item_cfg, spot)
    choose_method(world, child, helper, tool)

    world.para()
    collect(world, child, helper, tool, item_cfg)
    celebrate(world, child, helper, item_cfg, quest)

    world.facts.update(
        child=child,
        helper=helper,
        item_cfg=item_cfg,
        spot=spot,
        tool=tool,
        quest=quest,
        found=item.meters["found"] >= THRESHOLD,
        kept=item.meters["kept"] >= THRESHOLD,
        helper_pride=helper.memes["pride"] >= THRESHOLD,
        child_joy=child.memes["joy"] >= THRESHOLD,
    )
    return world


KNOWLEDGE = {
    "sea_glass": [
        (
            "What is sea glass?",
            "Sea glass is a piece of old glass that the sea has rolled around until it feels smooth. The edges wear down in the water, so it no longer feels sharp.",
        )
    ],
    "shell": [
        (
            "Why can a shell crack easily?",
            "A shell can be thin and brittle, so a rough poke or squeeze can break it. That is why gentle hands matter.",
        )
    ],
    "stone": [
        (
            "Why are some beach stones smooth?",
            "Beach stones get bumped and rolled by water for a long time. The rough corners wear away until they feel smooth.",
        )
    ],
    "tide_pool": [
        (
            "What is a tide pool?",
            "A tide pool is a little pocket of seawater left behind among rocks when the tide goes out. Small sea creatures and shiny pebbles can be seen there.",
        )
    ],
    "crevice": [
        (
            "What is a rock crevice?",
            "A rock crevice is a narrow crack between rocks. Things can get tucked inside where fingers do not fit well.",
        )
    ],
    "wave_line": [
        (
            "What is the wave line?",
            "The wave line is the place where the sea keeps washing up and sliding back. Things there can move each time the water comes in.",
        )
    ],
    "net": [
        (
            "What is a beach net for?",
            "A beach net can help you lift something from shallow water without splashing your whole hand in. It lets you reach a little farther in a careful way.",
        )
    ],
    "cloth": [
        (
            "Why would someone use a cloth to pick up something delicate?",
            "A cloth can soften your grip and protect a fragile thing from scraping. It also helps keep a damp rock from slipping against your skin.",
        )
    ],
    "hook": [
        (
            "Why can a hook be too rough for delicate things?",
            "A hook pushes and tugs from one point, so it can scratch or crack something fragile. It is better for sturdy things.",
        )
    ],
    "waiting": [
        (
            "Why can waiting sometimes be the best way to get something by the sea?",
            "The sea keeps moving things a little at a time. If you wait, the water may bring the thing closer without any grabbing at all.",
        )
    ],
}
KNOWLEDGE_ORDER = [
    "sea_glass",
    "shell",
    "stone",
    "tide_pool",
    "crevice",
    "wave_line",
    "net",
    "cloth",
    "hook",
    "waiting",
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    item_cfg = f["item_cfg"]
    spot = f["spot"]
    quest = f["quest"]
    return [
        'Write a gentle slice-of-life story for a 3-to-5-year-old set on a rocky shore that uses the word "legendary".',
        f"Tell a happy little quest where {child.label} and {helper.label_word} look for {item_cfg.label} at {spot.label} and choose patience over grabbing.",
        f"Write a homey story where a child goes on a tiny beach quest {quest.want} and ends by bringing the treasure safely home.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    item_cfg = f["item_cfg"]
    spot = f["spot"]
    tool = f["tool"]
    quest = f["quest"]

    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.label}, a little {child.type}, and {helper.label_word}. They go together to the rocky shore for a small quest.",
        ),
        (
            "What was their quest?",
            f"They wanted {quest.want}. The quest felt grand to {child.label}, even though it was one small family errand on an ordinary morning.",
        ),
        (
            f"Where did {child.label} find the {item_cfg.label}?",
            f"{child.pronoun('subject').capitalize()} saw it in {spot.phrase}. That spot mattered because it was not easy to reach safely.",
        ),
    ]

    risks = []
    if f.get("predicted_wobble"):
        risks.append("the wet rocks could make the child wobble")
    if f.get("predicted_drift"):
        risks.append("the water could pull the treasure away")
    if f.get("predicted_chip"):
        risks.append(f"the {item_cfg.label} could crack")

    if risks:
        if len(risks) == 1:
            risk_text = risks[0]
        elif len(risks) == 2:
            risk_text = f"{risks[0]}, and {risks[1]}"
        else:
            risk_text = f"{risks[0]}, {risks[1]}, and {risks[2]}"
        qa.append(
            (
                f"Why did {helper.label_word} tell {child.label} not to grab right away?",
                f"{helper.label_word.capitalize()} could see that {risk_text}. That warning changed the story because it turned a rush into a careful plan.",
            )
        )

    qa.append(
        (
            "How did they solve the problem?",
            f"They used {tool.phrase} and worked slowly. That method matched the place and let them bring the treasure out without spoiling the quest.",
        )
    )
    qa.append(
        (
            "How did the story end?",
            f"It ended happily at home, where they {quest.ending}. The ending shows that the quest was successful because the treasure became part of ordinary family life.",
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["item_cfg"].tags) | set(f["spot"].tags) | set(f["tool"].tags)
    out: list[tuple[str, str]] = []
    for key in KNOWLEDGE_ORDER:
        if key in tags and key in KNOWLEDGE:
            out.extend(KNOWLEDGE[key])
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
        if e.fragile:
            bits.append("fragile=True")
        if e.role:
            bits.append(f"role={e.role}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:8} ({e.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        item="sea_glass",
        spot="tide_pool",
        tool="net",
        quest="windowsill",
        child_name="Nora",
        child_gender="girl",
        helper_name="Grandpa",
        helper_type="grandfather",
        child_trait="curious",
    ),
    StoryParams(
        item="spiral_shell",
        spot="crevice",
        tool="cloth_hand",
        quest="gift",
        child_name="Lina",
        child_gender="girl",
        helper_name="Grandma",
        helper_type="grandmother",
        child_trait="patient",
    ),
    StoryParams(
        item="lucky_stone",
        spot="crevice",
        tool="hook",
        quest="pocket",
        child_name="Owen",
        child_gender="boy",
        helper_name="Dad",
        helper_type="father",
        child_trait="eager",
    ),
    StoryParams(
        item="sea_glass",
        spot="wave_line",
        tool="wait",
        quest="gift",
        child_name="Milo",
        child_gender="boy",
        helper_name="Mom",
        helper_type="mother",
        child_trait="bright-eyed",
    ),
    StoryParams(
        item="spiral_shell",
        spot="wave_line",
        tool="net",
        quest="windowsill",
        child_name="Ruby",
        child_gender="girl",
        helper_name="Grandpa",
        helper_type="grandfather",
        child_trait="careful",
    ),
]


ASP_RULES = r"""
allowed_gentleness(I,T) :- item(I), tool(T), not fragile(I).
allowed_gentleness(I,T) :- item(I), tool(T), fragile(I), gentle(T).

valid(I,S,T) :- item(I), spot(S), tool(T), works(T,S), allowed_gentleness(I,T).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for item_id, item in ITEMS.items():
        lines.append(asp.fact("item", item_id))
        if item.fragile:
            lines.append(asp.fact("fragile", item_id))
    for spot_id in SPOTS:
        lines.append(asp.fact("spot", spot_id))
    for tool_id, tool in TOOLS.items():
        lines.append(asp.fact("tool", tool_id))
        if tool.gentle:
            lines.append(asp.fact("gentle", tool_id))
        for spot_id in sorted(tool.works_on):
            lines.append(asp.fact("works", tool_id, spot_id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0

    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: ASP gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH between ASP and valid_combos():")
        if clingo_set - python_set:
            print("  only in ASP:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in Python:", sorted(python_set - clingo_set))

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("empty story")
        if not sample.prompts or not sample.story_qa or not sample.world_qa:
            raise StoryError("missing prompts or QA")
        with contextlib.redirect_stdout(io.StringIO()):
            emit(sample, trace=True, qa=True)
        args = build_parser().parse_args([])
        params = resolve_params(args, random.Random(123))
        params.seed = 123
        sample2 = generate(params)
        if not sample2.story.strip():
            raise StoryError("empty random story")
        with contextlib.redirect_stdout(io.StringIO()):
            emit(sample2, trace=False, qa=False)
        print("OK: smoke-tested generate() and emit() on curated and default params.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a tiny legendary quest on a rocky shore."
    )
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--spot", choices=SPOTS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--helper-type", choices=HELPERS)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combos from clingo")
    ap.add_argument("--verify", action="store_true", help="verify ASP parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the ASP program")
    return ap


def choose_child_name(rng: random.Random, gender: str) -> str:
    return rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)


def choose_helper_name(helper_type: str) -> str:
    return {
        "mother": "Mom",
        "father": "Dad",
        "grandmother": "Grandma",
        "grandfather": "Grandpa",
    }[helper_type]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.item is not None and args.item not in ITEMS:
        raise StoryError(f"(Unknown item: {args.item})")
    if args.spot is not None and args.spot not in SPOTS:
        raise StoryError(f"(Unknown spot: {args.spot})")
    if args.tool is not None and args.tool not in TOOLS:
        raise StoryError(f"(Unknown tool: {args.tool})")
    if args.quest is not None and args.quest not in QUESTS:
        raise StoryError(f"(Unknown quest: {args.quest})")

    if args.item and args.spot and args.tool:
        item = ITEMS[args.item]
        spot = SPOTS[args.spot]
        tool = TOOLS[args.tool]
        if not tool_fits(item, spot, tool):
            raise StoryError(explain_rejection(item, spot, tool))

    combos = [
        combo
        for combo in valid_combos()
        if (args.item is None or combo[0] == args.item)
        and (args.spot is None or combo[1] == args.spot)
        and (args.tool is None or combo[2] == args.tool)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    item_id, spot_id, tool_id = rng.choice(sorted(combos))
    quest_id = args.quest or rng.choice(sorted(QUESTS))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    helper_type = args.helper_type or rng.choice(HELPERS)
    child_name = choose_child_name(rng, child_gender)
    helper_name = choose_helper_name(helper_type)
    child_trait = rng.choice(CHILD_TRAITS)

    return StoryParams(
        item=item_id,
        spot=spot_id,
        tool=tool_id,
        quest=quest_id,
        child_name=child_name,
        child_gender=child_gender,
        helper_name=helper_name,
        helper_type=helper_type,
        child_trait=child_trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.item not in ITEMS:
        raise StoryError(f"(Unknown item: {params.item})")
    if params.spot not in SPOTS:
        raise StoryError(f"(Unknown spot: {params.spot})")
    if params.tool not in TOOLS:
        raise StoryError(f"(Unknown tool: {params.tool})")
    if params.quest not in QUESTS:
        raise StoryError(f"(Unknown quest: {params.quest})")
    if params.child_gender not in {"girl", "boy"}:
        raise StoryError(f"(Unknown child gender: {params.child_gender})")
    if params.helper_type not in HELPERS:
        raise StoryError(f"(Unknown helper type: {params.helper_type})")

    item_cfg = ITEMS[params.item]
    spot = SPOTS[params.spot]
    tool = TOOLS[params.tool]
    quest = QUESTS[params.quest]

    if not tool_fits(item_cfg, spot, tool):
        raise StoryError(explain_rejection(item_cfg, spot, tool))

    world = tell(
        item_cfg=item_cfg,
        spot=spot,
        tool=tool,
        quest=quest,
        child_name=params.child_name,
        child_gender=params.child_gender,
        helper_name=params.helper_name,
        helper_type=params.helper_type,
        child_trait=params.child_trait,
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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (item, spot, tool) combos:\n")
        for item, spot, tool in combos:
            print(f"  {item:12} {spot:10} {tool}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

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
            header = f"### {p.child_name}: {p.item} at {p.spot} with {p.tool}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
