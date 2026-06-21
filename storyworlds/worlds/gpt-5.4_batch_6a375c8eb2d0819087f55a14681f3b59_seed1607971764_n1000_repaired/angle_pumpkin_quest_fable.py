#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/angle_pumpkin_quest_fable.py
=======================================================

A small story world for a gentle fable-like quest: a little animal must bring a
pumpkin to a harvest place, meets an obstacle on the road, and learns that a
wise path depends on choosing the right angle.

The core reasonableness rule is simple:
a rolling pumpkin can only be moved up an obstacle safely when the chosen tool
makes a gentle enough ramp angle AND is sturdy enough for that pumpkin's weight.

Run it
------
    python storyworlds/worlds/gpt-5.4/angle_pumpkin_quest_fable.py
    python storyworlds/worlds/gpt-5.4/angle_pumpkin_quest_fable.py --obstacle creek_bank --tool straw_bundle
    python storyworlds/worlds/gpt-5.4/angle_pumpkin_quest_fable.py --asp
    python storyworlds/worlds/gpt-5.4/angle_pumpkin_quest_fable.py --verify
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
    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "hen", "doe"}
        male = {"boy", "fox", "mole", "badger"}
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


@dataclass
class Destination:
    id: str
    label: str
    purpose: str
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
class Obstacle:
    id: str
    label: str
    rise: int
    min_run: int
    scene: str
    setback: str
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
    run: int
    strength: int
    build_text: str
    qa_text: str
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
class PumpkinKind:
    id: str
    label: str
    weight: int
    color: str
    finish: str
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
        self.facts: dict = {
            "attempt_direct": False,
            "ramp_built": False,
            "safe_angle": False,
            "sturdy": False,
            "delivered": False,
            "shared": False,
            "predicted_safe": False,
            "predicted_angle_ok": False,
            "predicted_sturdy": False,
        }

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


def _r_direct_push(world: World) -> list[str]:
    if not world.facts["attempt_direct"] or world.facts["ramp_built"]:
        return []
    sig = ("direct_push",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero = world.get("hero")
    pumpkin = world.get("pumpkin")
    pumpkin.meters["stuck"] += 1
    hero.memes["worry"] += 1
    hero.memes["effort"] += 1
    return ["__stuck__"]


def _r_wobble(world: World) -> list[str]:
    if not world.facts["ramp_built"] or world.facts["safe_angle"] or not world.facts["sturdy"]:
        return []
    sig = ("wobble",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero = world.get("hero")
    pumpkin = world.get("pumpkin")
    pumpkin.meters["wobble"] += 1
    hero.memes["fear"] += 1
    return ["__wobble__"]


def _r_break(world: World) -> list[str]:
    if not world.facts["ramp_built"] or not world.facts["safe_angle"] or world.facts["sturdy"]:
        return []
    sig = ("break",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero = world.get("hero")
    pumpkin = world.get("pumpkin")
    pumpkin.meters["stuck"] += 1
    pumpkin.meters["bruise"] += 1
    hero.memes["fear"] += 1
    return ["__break__"]


def _r_roll_up(world: World) -> list[str]:
    if not world.facts["ramp_built"] or not world.facts["safe_angle"] or not world.facts["sturdy"]:
        return []
    sig = ("roll_up",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero = world.get("hero")
    helper = world.get("helper")
    pumpkin = world.get("pumpkin")
    pumpkin.meters["progress"] += 1
    hero.memes["hope"] += 1
    helper.memes["care"] += 1
    return ["__rolled__"]


def _r_deliver(world: World) -> list[str]:
    if world.get("pumpkin").meters["progress"] < THRESHOLD:
        return []
    sig = ("deliver",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero = world.get("hero")
    helper = world.get("helper")
    pumpkin = world.get("pumpkin")
    pumpkin.meters["shared"] += 1
    hero.memes["joy"] += 1
    hero.memes["lesson"] += 1
    helper.memes["joy"] += 1
    world.facts["delivered"] = True
    world.facts["shared"] = True
    return ["__delivered__"]


CAUSAL_RULES = [
    Rule(name="direct_push", tag="physical", apply=_r_direct_push),
    Rule(name="wobble", tag="physical", apply=_r_wobble),
    Rule(name="break", tag="physical", apply=_r_break),
    Rule(name="roll_up", tag="physical", apply=_r_roll_up),
    Rule(name="deliver", tag="social", apply=_r_deliver),
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
                produced.extend(s for s in out if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


DESTINATIONS = {
    "feast": Destination(
        id="feast",
        label="the hill lantern feast",
        purpose="so everyone could have pumpkin soup before the lanterns were lit",
        ending="the pumpkin sat in the middle of the table, warm light shining on its orange skin",
        tags={"feast", "sharing"},
    ),
    "grandmother": Destination(
        id="grandmother",
        label="Badger Grandmother's cottage",
        purpose="so Badger Grandmother could cook her first autumn pie",
        ending="the pumpkin rested beside the black kettle while the cottage windows glowed gold",
        tags={"grandmother", "sharing"},
    ),
    "square": Destination(
        id="square",
        label="the village square",
        purpose="so the neighbors could carve it and laugh together at dusk",
        ending="the pumpkin gleamed on the long table while sparrows hopped near the crumbs",
        tags={"village", "sharing"},
    ),
}

OBSTACLES = {
    "stone_step": Obstacle(
        id="stone_step",
        label="a stone step",
        rise=1,
        min_run=2,
        scene="a stone step as high as the hero's knee blocked the path",
        setback="The pumpkin bumped the step and rolled back against the hero's paws.",
        tags={"step"},
    ),
    "creek_bank": Obstacle(
        id="creek_bank",
        label="a creek bank",
        rise=2,
        min_run=3,
        scene="a little creek cut across the road, and the far bank stood steep above the water",
        setback="The pumpkin slid down the damp bank and stopped in the reeds.",
        tags={"creek"},
    ),
    "root_ledge": Obstacle(
        id="root_ledge",
        label="a root ledge",
        rise=2,
        min_run=4,
        scene="an old tree root made a hard ledge across the woodland trail",
        setback="The pumpkin thumped the root and wobbled back into the leaves.",
        tags={"ledge"},
    ),
    "cart_rut": Obstacle(
        id="cart_rut",
        label="a cart rut",
        rise=1,
        min_run=1,
        scene="a deep cart rut cut the lane and left one side higher than the other",
        setback="The pumpkin dipped into the rut and would not climb out in one push.",
        tags={"rut"},
    ),
}

TOOLS = {
    "long_board": Tool(
        id="long_board",
        label="a long board",
        run=4,
        strength=3,
        build_text="laid a long board from the ground to the top and steadied it with two stones",
        qa_text="used a long board to make a gentle ramp",
        tags={"board", "ramp"},
    ),
    "flat_stones": Tool(
        id="flat_stones",
        label="flat stones",
        run=3,
        strength=3,
        build_text="set flat stones one after another until they made a low, patient ramp",
        qa_text="stacked flat stones into a low ramp",
        tags={"stones", "ramp"},
    ),
    "straw_bundle": Tool(
        id="straw_bundle",
        label="a straw bundle",
        run=2,
        strength=1,
        build_text="packed a straw bundle against the rise and tried to use it as a short ramp",
        qa_text="tried to use a straw bundle as a ramp",
        tags={"straw", "ramp"},
    ),
    "twig_sled": Tool(
        id="twig_sled",
        label="a twig sled",
        run=2,
        strength=2,
        build_text="tied the pumpkin onto a twig sled and tipped the front up toward the rise",
        qa_text="used a twig sled to guide the pumpkin upward",
        tags={"sled", "ramp"},
    ),
}

PUMPKINS = {
    "small": PumpkinKind(
        id="small",
        label="a small pumpkin",
        weight=1,
        color="bright orange",
        finish="smooth as a polished bowl",
        tags={"pumpkin"},
    ),
    "striped": PumpkinKind(
        id="striped",
        label="a striped pumpkin",
        weight=2,
        color="orange and pale gold",
        finish="round and glossy",
        tags={"pumpkin"},
    ),
    "giant": PumpkinKind(
        id="giant",
        label="a giant pumpkin",
        weight=3,
        color="deep orange",
        finish="broad and heavy",
        tags={"pumpkin"},
    ),
}

HELPERS = {
    "mole": {
        "type": "mole",
        "name": "Mole",
        "advice": "Mole squinted at the rise and said that a pumpkin likes a gentle angle better than a proud shove.",
        "tags": {"mole", "angle"},
    },
    "crow": {
        "type": "crow",
        "name": "Crow",
        "advice": "Crow cocked his head and said the road must be persuaded at the right angle, not fought.",
        "tags": {"crow", "angle"},
    },
    "badger": {
        "type": "badger",
        "name": "Badger",
        "advice": "Badger tapped the ground and said that even a round pumpkin will climb if the angle is kind.",
        "tags": {"badger", "angle"},
    },
}

HEROES = [
    {"name": "Pip", "type": "fox", "traits": ["little", "earnest", "brave"]},
    {"name": "Nell", "type": "hen", "traits": ["little", "careful", "kind"]},
    {"name": "Tavi", "type": "mouse", "traits": ["little", "hopeful", "busy"]},
    {"name": "Brin", "type": "mole", "traits": ["little", "steady", "humble"]},
]


def angle_ok(obstacle: Obstacle, tool: Tool) -> bool:
    return tool.run >= obstacle.min_run


def sturdy_enough(tool: Tool, pumpkin: PumpkinKind) -> bool:
    return tool.strength >= pumpkin.weight


def combo_ok(obstacle: Obstacle, tool: Tool, pumpkin: PumpkinKind) -> bool:
    return angle_ok(obstacle, tool) and sturdy_enough(tool, pumpkin)


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for oid, obstacle in OBSTACLES.items():
        for tid, tool in TOOLS.items():
            for pid, pumpkin in PUMPKINS.items():
                if combo_ok(obstacle, tool, pumpkin):
                    out.append((oid, tid, pid))
    return sorted(out)


def explain_rejection(obstacle: Obstacle, tool: Tool, pumpkin: PumpkinKind) -> str:
    problems: list[str] = []
    if not angle_ok(obstacle, tool):
        problems.append(
            f"{tool.label} makes too steep an angle for {obstacle.label}"
        )
    if not sturdy_enough(tool, pumpkin):
        problems.append(
            f"{tool.label} is too flimsy for {pumpkin.label}"
        )
    if not problems:
        return "(No story: this combination is not reasonable.)"
    return "(No story: " + " and ".join(problems) + ".)"


def predict(world: World, obstacle: Obstacle, tool: Tool, pumpkin_cfg: PumpkinKind) -> dict:
    sim = world.copy()
    sim.facts["ramp_built"] = True
    sim.facts["safe_angle"] = angle_ok(obstacle, tool)
    sim.facts["sturdy"] = sturdy_enough(tool, pumpkin_cfg)
    propagate(sim, narrate=False)
    pumpkin = sim.get("pumpkin")
    return {
        "safe": pumpkin.meters["progress"] >= THRESHOLD and pumpkin.meters["wobble"] < THRESHOLD,
        "angle_ok": sim.facts["safe_angle"],
        "sturdy": sim.facts["sturdy"],
        "wobble": pumpkin.meters["wobble"] >= THRESHOLD,
        "bruised": pumpkin.meters["bruise"] >= THRESHOLD,
    }


def introduce(world: World, hero: Entity, pumpkin_cfg: PumpkinKind, destination: Destination) -> None:
    world.say(
        f"In the first cool days of autumn, {hero.id} found {pumpkin_cfg.label}, "
        f"{pumpkin_cfg.finish} and {pumpkin_cfg.color}, under the vines."
    )
    world.say(
        f"{hero.pronoun().capitalize()} set out on a quest to carry it to {destination.label} "
        f"{destination.purpose}."
    )


def road_appears(world: World, hero: Entity, obstacle: Obstacle) -> None:
    hero.memes["resolve"] += 1
    world.say(
        f"{hero.id} followed the brown road through the fields until {obstacle.scene}."
    )


def direct_try(world: World, hero: Entity, obstacle: Obstacle) -> None:
    world.facts["attempt_direct"] = True
    propagate(world, narrate=False)
    world.say(
        f"{hero.id} lowered {hero.pronoun('possessive')} shoulder and pushed with all "
        f"{hero.pronoun('possessive')} might."
    )
    world.say(obstacle.setback)


def helper_arrives(world: World, helper: Entity) -> None:
    helper.memes["care"] += 1
    world.say(
        f"Just then {helper.id} came along the path and stopped to watch."
    )


def counsel(world: World, helper: Entity, hero: Entity, obstacle: Obstacle, tool: Tool, pumpkin_cfg: PumpkinKind) -> None:
    pred = predict(world, obstacle, tool, pumpkin_cfg)
    world.facts["predicted_safe"] = pred["safe"]
    world.facts["predicted_angle_ok"] = pred["angle_ok"]
    world.facts["predicted_sturdy"] = pred["sturdy"]
    world.say(helper.attrs["advice"])
    if pred["safe"]:
        world.say(
            f'"If we make a longer climb instead of a steeper one," {helper.pronoun()} said, '
            f'"the pumpkin will roll upward without slipping."'
        )


def build_ramp(world: World, hero: Entity, helper: Entity, tool: Tool, obstacle: Obstacle, pumpkin_cfg: PumpkinKind) -> None:
    world.facts["ramp_built"] = True
    world.facts["safe_angle"] = angle_ok(obstacle, tool)
    world.facts["sturdy"] = sturdy_enough(tool, pumpkin_cfg)
    world.say(
        f"So {hero.id} and {helper.id} {tool.build_text}."
    )
    world.say(
        f"The angle from the road to the rise was no longer sharp and proud, but low and friendly."
    )
    propagate(world, narrate=False)


def crossing(world: World, hero: Entity, helper: Entity, pumpkin_cfg: PumpkinKind, destination: Destination) -> None:
    pumpkin = world.get("pumpkin")
    if pumpkin.meters["progress"] >= THRESHOLD:
        world.say(
            f"Together they rolled the pumpkin up the ramp, slow as a song and steady as a moon."
        )
        world.say(
            f"By sunset they reached {destination.label}, and {destination.ending}."
        )


def moral(world: World, hero: Entity, helper: Entity) -> None:
    hero.memes["gratitude"] += 1
    world.say(
        f'{hero.id} thanked {helper.id} and remembered the lesson all winter: '
        f'"A hard quest is often eased not by more force, but by a wiser angle."'
    )


def tell(
    *,
    destination: Destination,
    obstacle: Obstacle,
    tool: Tool,
    pumpkin_cfg: PumpkinKind,
    hero_name: str,
    hero_type: str,
    hero_traits: list[str],
    helper_name: str,
    helper_type: str,
    helper_advice: str,
    helper_tags: set[str],
) -> World:
    world = World()
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_type,
        label=hero_name,
        role="hero",
        traits=list(hero_traits),
        attrs={},
        tags={"hero", "quest"},
    ))
    helper = world.add(Entity(
        id=helper_name,
        kind="character",
        type=helper_type,
        label=helper_name,
        role="helper",
        traits=["wise"],
        attrs={"advice": helper_advice},
        tags=set(helper_tags),
    ))
    pumpkin = world.add(Entity(
        id="pumpkin",
        kind="thing",
        type="pumpkin",
        label=pumpkin_cfg.label,
        role="prize",
        attrs={"weight": pumpkin_cfg.weight, "color": pumpkin_cfg.color},
        tags=set(pumpkin_cfg.tags),
    ))

    introduce(world, hero, pumpkin_cfg, destination)
    road_appears(world, hero, obstacle)

    world.para()
    direct_try(world, hero, obstacle)
    helper_arrives(world, helper)
    counsel(world, helper, hero, obstacle, tool, pumpkin_cfg)

    world.para()
    build_ramp(world, hero, helper, tool, obstacle, pumpkin_cfg)
    crossing(world, hero, helper, pumpkin_cfg, destination)

    world.para()
    moral(world, hero, helper)

    world.facts.update(
        hero=hero,
        helper=helper,
        pumpkin_cfg=pumpkin_cfg,
        destination=destination,
        obstacle=obstacle,
        tool=tool,
        delivered=world.facts["delivered"],
        shared=world.facts["shared"],
        learned=hero.memes["lesson"] >= THRESHOLD,
    )
    return world


KNOWLEDGE = {
    "angle": [
        (
            "What is an angle?",
            "An angle is the shape made when two lines meet. A ramp with a gentle angle is easier to climb than one that is steep."
        )
    ],
    "pumpkin": [
        (
            "What is a pumpkin?",
            "A pumpkin is a round autumn fruit with a thick skin and seeds inside. People use pumpkins for soup, pie, and lanterns."
        )
    ],
    "ramp": [
        (
            "Why does a ramp help move something heavy?",
            "A ramp spreads the climb out over a longer distance, so the lift feels gentler. That is why a round object can be rolled instead of heaved straight up."
        )
    ],
    "sharing": [
        (
            "Why do fables often end with sharing?",
            "Fables often show that good things grow when they are shared. The ending turns a private prize into a common joy."
        )
    ],
    "board": [
        (
            "What can a long board be used for?",
            "A long board can bridge a gap or make a simple ramp. Its length helps make the angle less steep."
        )
    ],
    "stones": [
        (
            "Why can flat stones make a good path?",
            "Flat stones can be placed one after another to make small steps or a low ramp. They spread a climb into easier parts."
        )
    ],
    "straw": [
        (
            "Why is straw not very strong for heavy lifting?",
            "Straw bends and squishes easily. It can help with padding, but it is not the best support for a heavy load."
        )
    ],
    "sled": [
        (
            "What is a sled for?",
            "A sled helps something slide while staying together in one place. It can guide a load, but it still must be strong enough and set at a safe angle."
        )
    ],
}

KNOWLEDGE_ORDER = ["angle", "pumpkin", "ramp", "sharing", "board", "stones", "straw", "sled"]


def generation_prompts(world: World) -> list[str]:
    hero = world.facts["hero"]
    destination = world.facts["destination"]
    obstacle = world.facts["obstacle"]
    return [
        f'Write a short fable about a quest with the words "angle" and "pumpkin".',
        f"Tell a gentle quest story where {hero.id} must bring a pumpkin to {destination.label} and learns to solve {obstacle.label} with wisdom instead of force.",
        "Write a child-friendly fable in which a small traveler succeeds by choosing a kinder angle."
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    hero = world.facts["hero"]
    helper = world.facts["helper"]
    destination = world.facts["destination"]
    obstacle = world.facts["obstacle"]
    tool = world.facts["tool"]
    pumpkin_cfg = world.facts["pumpkin_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "What was the quest in the story?",
            f"{hero.id}'s quest was to bring {pumpkin_cfg.label} to {destination.label}. {destination.purpose[0].upper() + destination.purpose[1:]}."
        ),
        (
            f"Why could {hero.id} not simply push the pumpkin over {obstacle.label}?",
            f"{obstacle.label.capitalize()} was too high for a straight shove, so the pumpkin rolled or slid back. The trouble was not only strength, but the shape of the climb."
        ),
        (
            f"How did {helper.id} help?",
            f"{helper.id} told {hero.id} to think about the angle instead of pushing harder. Then they {tool.qa_text}, which turned the rise into a gentler path."
        ),
    ]
    if world.facts["delivered"]:
        qa.append(
            (
                "Why did the ramp work?",
                f"It worked because {tool.label} made a gentle enough angle and was sturdy enough for the pumpkin. That let the pumpkin move upward slowly instead of slipping or breaking through."
            )
        )
        qa.append(
            (
                "What lesson did the hero learn?",
                f"{hero.id} learned that wisdom can make a hard quest easier. A better plan changed the road before more force was needed."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = {"angle", "pumpkin", "sharing", "ramp"}
    tool = world.facts["tool"]
    if "board" in tool.tags:
        tags.add("board")
    if "stones" in tool.tags:
        tags.add("stones")
    if "straw" in tool.tags:
        tags.add("straw")
    if "sled" in tool.tags:
        tags.add("sled")
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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.attrs:
            bits.append(f"attrs={ent.attrs}")
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(bits)}")
    lines.append(
        "  facts: "
        + json.dumps(
            {
                "attempt_direct": world.facts["attempt_direct"],
                "ramp_built": world.facts["ramp_built"],
                "safe_angle": world.facts["safe_angle"],
                "sturdy": world.facts["sturdy"],
                "predicted_safe": world.facts["predicted_safe"],
                "delivered": world.facts["delivered"],
            },
            ensure_ascii=False,
        )
    )
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


@dataclass
class StoryParams:
    destination: str
    obstacle: str
    tool: str
    pumpkin: str
    helper: str
    hero_name: str
    hero_type: str
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


CURATED = [
    StoryParams(
        destination="feast",
        obstacle="stone_step",
        tool="flat_stones",
        pumpkin="striped",
        helper="mole",
        hero_name="Pip",
        hero_type="fox",
        trait="earnest",
    ),
    StoryParams(
        destination="grandmother",
        obstacle="creek_bank",
        tool="long_board",
        pumpkin="giant",
        helper="crow",
        hero_name="Nell",
        hero_type="hen",
        trait="careful",
    ),
    StoryParams(
        destination="square",
        obstacle="cart_rut",
        tool="twig_sled",
        pumpkin="striped",
        helper="badger",
        hero_name="Tavi",
        hero_type="mouse",
        trait="hopeful",
    ),
    StoryParams(
        destination="feast",
        obstacle="root_ledge",
        tool="long_board",
        pumpkin="small",
        helper="mole",
        hero_name="Brin",
        hero_type="mole",
        trait="steady",
    ),
]


ASP_RULES = r"""
angle_ok(O,T) :- obstacle(O), tool(T), min_run(O,Need), run(T,Have), Have >= Need.
sturdy(T,P)   :- tool(T), pumpkin(P), strength(T,S), weight(P,W), S >= W.
valid(O,T,P)  :- angle_ok(O,T), sturdy(T,P).

#show valid/3.
#show angle_ok/2.
#show sturdy/2.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for oid, obstacle in OBSTACLES.items():
        lines.append(asp.fact("obstacle", oid))
        lines.append(asp.fact("min_run", oid, obstacle.min_run))
    for tid, tool in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        lines.append(asp.fact("run", tid, tool.run))
        lines.append(asp.fact("strength", tid, tool.strength))
    for pid, pumpkin in PUMPKINS.items():
        lines.append(asp.fact("pumpkin", pid))
        lines.append(asp.fact("weight", pid, pumpkin.weight))
    return "\n".join(lines)


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH between ASP and Python gate:")
        if cl - py:
            print("  only in ASP:", sorted(cl - py))
        if py - cl:
            print("  only in Python:", sorted(py - cl))

    smoke_cases = list(CURATED[:2])
    try:
        default_params = resolve_params(build_parser().parse_args([]), random.Random(0))
        smoke_cases.append(default_params)
    except StoryError as err:
        rc = 1
        print(f"Smoke setup failed: {err}")
        smoke_cases = []

    for params in smoke_cases:
        try:
            sample = generate(params)
            if not sample.story.strip():
                raise StoryError("generated story was empty")
            _ = sample.to_json()
            buf = io.StringIO()
            old = sys.stdout
            try:
                sys.stdout = buf
                emit(sample, trace=False, qa=False, header="")
            finally:
                sys.stdout = old
        except Exception as err:  # pragma: no cover
            rc = 1
            print(f"Smoke generation failed for {params}: {err}")
    if rc == 0:
        print(f"OK: smoke-tested {len(smoke_cases)} generated stories.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A tiny fable-like pumpkin quest story world. Unspecified choices are picked at random (seeded)."
    )
    ap.add_argument("--destination", choices=DESTINATIONS)
    ap.add_argument("--obstacle", choices=OBSTACLES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--pumpkin", choices=PUMPKINS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-type", choices=sorted({h["type"] for h in HEROES}))
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid obstacle/tool/pumpkin combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.obstacle and args.tool and args.pumpkin:
        obstacle = OBSTACLES[args.obstacle]
        tool = TOOLS[args.tool]
        pumpkin = PUMPKINS[args.pumpkin]
        if not combo_ok(obstacle, tool, pumpkin):
            raise StoryError(explain_rejection(obstacle, tool, pumpkin))

    combos = [
        combo
        for combo in valid_combos()
        if (args.obstacle is None or combo[0] == args.obstacle)
        and (args.tool is None or combo[1] == args.tool)
        and (args.pumpkin is None or combo[2] == args.pumpkin)
    ]
    if not combos:
        if args.obstacle and args.tool and args.pumpkin:
            raise StoryError(explain_rejection(OBSTACLES[args.obstacle], TOOLS[args.tool], PUMPKINS[args.pumpkin]))
        raise StoryError("(No valid combination matches the given options.)")

    obstacle_id, tool_id, pumpkin_id = rng.choice(combos)
    destination_id = args.destination or rng.choice(sorted(DESTINATIONS))
    helper_id = args.helper or rng.choice(sorted(HELPERS))

    hero_pool = [
        h for h in HEROES
        if (args.hero_type is None or h["type"] == args.hero_type)
        and (args.hero_name is None or h["name"] == args.hero_name)
    ]
    if not hero_pool:
        raise StoryError("(No hero matches the given --hero-name/--hero-type filters.)")
    hero = rng.choice(hero_pool)

    return StoryParams(
        destination=destination_id,
        obstacle=obstacle_id,
        tool=tool_id,
        pumpkin=pumpkin_id,
        helper=helper_id,
        hero_name=args.hero_name or hero["name"],
        hero_type=hero["type"],
        trait=hero["traits"][1] if len(hero["traits"]) > 1 else "little",
    )


def generate(params: StoryParams) -> StorySample:
    if params.destination not in DESTINATIONS:
        raise StoryError(f"(Unknown destination: {params.destination})")
    if params.obstacle not in OBSTACLES:
        raise StoryError(f"(Unknown obstacle: {params.obstacle})")
    if params.tool not in TOOLS:
        raise StoryError(f"(Unknown tool: {params.tool})")
    if params.pumpkin not in PUMPKINS:
        raise StoryError(f"(Unknown pumpkin: {params.pumpkin})")
    if params.helper not in HELPERS:
        raise StoryError(f"(Unknown helper: {params.helper})")

    obstacle = OBSTACLES[params.obstacle]
    tool = TOOLS[params.tool]
    pumpkin_cfg = PUMPKINS[params.pumpkin]
    if not combo_ok(obstacle, tool, pumpkin_cfg):
        raise StoryError(explain_rejection(obstacle, tool, pumpkin_cfg))

    helper_cfg = HELPERS[params.helper]
    world = tell(
        destination=DESTINATIONS[params.destination],
        obstacle=obstacle,
        tool=tool,
        pumpkin_cfg=pumpkin_cfg,
        hero_name=params.hero_name,
        hero_type=params.hero_type,
        hero_traits=["little", params.trait, "brave"],
        helper_name=helper_cfg["name"],
        helper_type=helper_cfg["type"],
        helper_advice=helper_cfg["advice"],
        helper_tags=set(helper_cfg["tags"]),
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
        print(f"{len(combos)} valid (obstacle, tool, pumpkin) combos:\n")
        for obstacle, tool, pumpkin in combos:
            print(f"  {obstacle:11} {tool:12} {pumpkin}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples: list[StorySample] = []
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
            header = f"### {p.hero_name}: {p.pumpkin} pumpkin via {p.tool} over {p.obstacle}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
