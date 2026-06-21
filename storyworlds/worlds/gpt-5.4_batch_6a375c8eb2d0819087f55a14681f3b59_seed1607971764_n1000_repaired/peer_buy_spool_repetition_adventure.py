#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/peer_buy_spool_repetition_adventure.py
=================================================================

A standalone story world about two children setting off on a tiny adventure with
a bought spool of trail-string. The world is built around a concrete planning
idea: if a winding place can swallow your turns, you can tie bright string at
the entrance, unspool it as you go, and follow it back.

Reference seed premise:
- include the words "peer", "buy", and "spool"
- use repetition
- keep the style close to adventure

This script turns that seed into a small simulation:
- children choose a setting and a spool to buy
- a reasonableness gate only allows spools that are long enough and easy enough
  to see in that setting
- pace affects whether the spool holds or snaps
- the ending is either a safe self-return or a calm helper-led rescue

Run it
------
python storyworlds/worlds/gpt-5.4/peer_buy_spool_repetition_adventure.py
python storyworlds/worlds/gpt-5.4/peer_buy_spool_repetition_adventure.py --setting fern_maze --spool red_string
python storyworlds/worlds/gpt-5.4/peer_buy_spool_repetition_adventure.py --setting sea_cave --spool silver_thread
python storyworlds/worlds/gpt-5.4/peer_buy_spool_repetition_adventure.py --all
python storyworlds/worlds/gpt-5.4/peer_buy_spool_repetition_adventure.py -n 5 --seed 7 --qa
python storyworlds/worlds/gpt-5.4/peer_buy_spool_repetition_adventure.py --verify
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
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "lady"}
        male = {"boy", "father", "man"}
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
class Setting:
    id: str
    label: str
    entry: str
    bends: str
    goal: str
    ending_image: str
    helper: str
    helper_kind: str
    depth_need: int
    dimness: int
    snag: int
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
class SpoolCfg:
    id: str
    label: str
    phrase: str
    color: str
    length: int
    visibility: int
    strength: int
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
class Pace:
    id: str
    line: str
    risk_add: int
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
        return [e for e in self.entities.values() if e.role in {"leader", "peer"}]

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


def _r_low_string(world: World) -> list[str]:
    spool = world.get("spool")
    place = world.get("place")
    if spool.meters["remaining"] > 2:
        return []
    sig = ("low_string",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    for kid in world.kids():
        kid.memes["worry"] += 1
    place.meters["risk"] += 1
    return ["__low__"]


def _r_break_means_lost(world: World) -> list[str]:
    spool = world.get("spool")
    place = world.get("place")
    if spool.meters["broken"] < THRESHOLD:
        return []
    sig = ("broken_lost",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    place.meters["lost"] += 1
    place.meters["risk"] += 1
    for kid in world.kids():
        kid.memes["fear"] += 1
    return ["__lost__"]


CAUSAL_RULES: list[Rule] = [
    Rule(name="low_string", tag="physical", apply=_r_low_string),
    Rule(name="broken_lost", tag="physical", apply=_r_break_means_lost),
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


def usable_spool(setting: Setting, spool: SpoolCfg) -> bool:
    return spool.length >= setting.depth_need and spool.visibility >= setting.dimness


def effective_risk(setting: Setting, pace: Pace) -> int:
    return setting.snag + pace.risk_add


def intact_return(setting: Setting, spool: SpoolCfg, pace: Pace) -> bool:
    return spool.strength >= effective_risk(setting, pace)


def predict_path(world: World, setting: Setting, spool: SpoolCfg, pace: Pace) -> dict:
    sim = world.copy()
    sim_spool = sim.get("spool")
    sim_spool.meters["remaining"] = float(spool.length - setting.depth_need)
    sim_spool.meters["trail"] = float(setting.depth_need)
    if not intact_return(setting, spool, pace):
        sim_spool.meters["broken"] += 1
    propagate(sim, narrate=False)
    return {
        "remaining": sim_spool.meters["remaining"],
        "broken": sim_spool.meters["broken"] >= THRESHOLD,
        "lost": sim.get("place").meters["lost"] >= THRESHOLD,
    }


def introduce(world: World, leader: Entity, peer: Entity, setting: Setting) -> None:
    leader.memes["wonder"] += 1
    peer.memes["wonder"] += 1
    world.say(
        f"{leader.id} and {peer.id} loved small adventures. On this bright morning, "
        f"they stood at {setting.entry}, staring at {setting.label} and wondering what "
        f"waited near {setting.goal}."
    )
    world.say(
        f"The path twisted so much that each turn seemed to swallow the one before it. "
        f"{peer.id} had to peer between leaves and stones just to see the next bend."
    )


def buy_spool(world: World, leader: Entity, peer: Entity, spool: SpoolCfg) -> None:
    leader.meters["coins"] = 1.0
    world.say(
        f'At a little stall nearby, {leader.id} said, "We should buy {spool.phrase}." '
        f'{peer.id} nodded at once. "A spool can show the way home."'
    )
    world.say(
        f"So they traded one shining coin for the {spool.label}, tucked it under "
        f"{leader.pronoun('possessive')} arm, and hurried back to the entrance."
    )


def make_plan(world: World, leader: Entity, peer: Entity, setting: Setting, spool: SpoolCfg, pace: Pace) -> None:
    pred = predict_path(world, setting, spool, pace)
    world.facts["predicted_remaining"] = pred["remaining"]
    world.facts["predicted_broken"] = pred["broken"]
    world.say(
        f'{peer.id} tied the end of the string to a root by the gate. '
        f'"Step by step, pull and peer. Step by step, pull and peer," '
        f'{peer.pronoun()} whispered, making the plan sound like a marching song.'
    )
    if pred["broken"]:
        world.say(
            f'{peer.id} glanced at the {spool.label} and added, '
            f'"If the path snags too hard, we stop and stay together."'
        )
    else:
        world.say(
            f'The {spool.color} string looked bright against the ground, and the plan '
            f'felt brave instead of scary.'
        )


def go_in(world: World, leader: Entity, peer: Entity, setting: Setting, spool: SpoolCfg, pace: Pace) -> None:
    world.say(
        f'They stepped into {setting.label}. {pace.line} '
        f'Behind them, the {spool.color} string slipped from the spool in a neat line.'
    )
    spool_ent = world.get("spool")
    spool_ent.meters["trail"] = float(setting.depth_need)
    spool_ent.meters["remaining"] = float(max(0, spool.length - setting.depth_need))
    if not intact_return(setting, spool, pace):
        spool_ent.meters["broken"] += 1
    propagate(world, narrate=False)


def repeated_progress(world: World, leader: Entity, peer: Entity, setting: Setting, spool: SpoolCfg) -> None:
    remaining = int(world.get("spool").meters["remaining"])
    world.say(
        f"First came a crooked bend, then a fern arch, then a low stone gap. "
        f'Each time they said it again: "Step by step, pull and peer. Step by step, pull and peer."'
    )
    if remaining <= 2:
        world.say(
            f"By the last bend, only a little string still sat on the spool. "
            f"{leader.id} held it more carefully, and even the adventure sounded softer."
        )
    else:
        world.say(
            f"The string kept whispering off the spool, bright and sure, and the turns no longer felt greedy."
        )


def reach_goal(world: World, leader: Entity, peer: Entity, setting: Setting) -> None:
    leader.memes["joy"] += 1
    peer.memes["joy"] += 1
    world.say(
        f"At last they reached {setting.goal}. For one happy breath they forgot every twist behind them."
    )


def return_safely(world: World, leader: Entity, peer: Entity, setting: Setting, spool: SpoolCfg) -> None:
    for kid in (leader, peer):
        kid.memes["relief"] += 1
        kid.memes["confidence"] += 1
    world.say(
        f"Then {peer.id} touched the line and smiled. "
        f'"Back we go. Step by step, pull and peer."'
    )
    world.say(
        f"They followed the {spool.color} trail home through every bend until {setting.entry} opened wide again. "
        f"{setting.ending_image}"
    )


def snap_and_wait(world: World, leader: Entity, peer: Entity, setting: Setting, spool: SpoolCfg) -> None:
    for kid in (leader, peer):
        kid.memes["fear"] += 1
    world.say(
        f"Then came a hard snag under a thorny branch. Snap! The line jumped, the string broke, "
        f"and the loose end curled back onto the spool."
    )
    world.say(
        f"For a moment the turns all looked the same. {leader.id} squeezed the spool, but {peer.id} remembered the plan. "
        f'"Do not run. Stay here. Stay together," {peer.pronoun()} said.'
    )


def helper_rescue(world: World, leader: Entity, peer: Entity, setting: Setting) -> None:
    helper = world.get("helper")
    for kid in (leader, peer):
        kid.memes["relief"] += 1
        kid.memes["lesson"] += 1
        kid.memes["fear"] = 0.0
    world.say(
        f"So they called, and soon the {helper.label} answered from the path outside. "
        f"{helper.label.capitalize()} followed the last bright loops of string and found them."
    )
    world.say(
        f'Together they walked back to {setting.entry}. {helper.label.capitalize()} said, '
        f'"A plan is brave, and going slowly helps a brave plan work."'
    )
    world.say(setting.ending_image)


def tell(
    setting: Setting,
    spool: SpoolCfg,
    pace: Pace,
    leader_name: str = "Mina",
    leader_type: str = "girl",
    peer_name: str = "Tom",
    peer_type: str = "boy",
) -> World:
    world = World()
    leader = world.add(Entity(id=leader_name, kind="character", type=leader_type, role="leader"))
    peer = world.add(Entity(id=peer_name, kind="character", type=peer_type, role="peer"))
    place = world.add(Entity(id="place", kind="thing", type="place", label=setting.label))
    spool_ent = world.add(Entity(id="spool", kind="thing", type="spool", label=spool.label))
    helper = world.add(
        Entity(id="helper", kind="character", type=setting.helper_kind, label=setting.helper)
    )

    place.meters["risk"] = 0.0
    place.meters["lost"] = 0.0
    spool_ent.meters["remaining"] = float(spool.length)
    spool_ent.meters["trail"] = 0.0
    spool_ent.meters["broken"] = 0.0
    leader.memes["wonder"] = 0.0
    leader.memes["fear"] = 0.0
    leader.memes["joy"] = 0.0
    leader.memes["relief"] = 0.0
    leader.memes["confidence"] = 0.0
    leader.memes["lesson"] = 0.0
    peer.memes["wonder"] = 0.0
    peer.memes["fear"] = 0.0
    peer.memes["joy"] = 0.0
    peer.memes["relief"] = 0.0
    peer.memes["confidence"] = 0.0
    peer.memes["lesson"] = 0.0
    helper.memes["calm"] = 1.0

    introduce(world, leader, peer, setting)
    world.para()
    buy_spool(world, leader, peer, spool)
    make_plan(world, leader, peer, setting, spool, pace)
    world.para()
    go_in(world, leader, peer, setting, spool, pace)
    repeated_progress(world, leader, peer, setting, spool)
    reach_goal(world, leader, peer, setting)
    world.para()

    if intact_return(setting, spool, pace):
        return_safely(world, leader, peer, setting, spool)
        outcome = "returned"
    else:
        snap_and_wait(world, leader, peer, setting, spool)
        helper_rescue(world, leader, peer, setting)
        outcome = "rescued"

    world.facts.update(
        setting=setting,
        spool_cfg=spool,
        pace=pace,
        leader=leader,
        peer=peer,
        helper=helper,
        outcome=outcome,
        broken=world.get("spool").meters["broken"] >= THRESHOLD,
        remaining=int(world.get("spool").meters["remaining"]),
        trail=int(world.get("spool").meters["trail"]),
    )
    return world


SETTINGS = {
    "fern_maze": Setting(
        id="fern_maze",
        label="the fern maze",
        entry="the green garden gate",
        bends="leafy turns",
        goal="the mossy center stone",
        ending_image="At the gate, they looked back and laughed, because the maze no longer seemed bigger than they were.",
        helper="gardener",
        helper_kind="man",
        depth_need=6,
        dimness=1,
        snag=2,
        tags={"maze", "path"},
    ),
    "sea_cave": Setting(
        id="sea_cave",
        label="the sea cave",
        entry="the tide-smoothed arch",
        bends="echoing turns",
        goal="a pool where a tiny starfish shone like a badge",
        ending_image="Outside, the waves kept booming, but now the cave felt like a place to respect, not a place to rush.",
        helper="beach ranger",
        helper_kind="man",
        depth_need=7,
        dimness=2,
        snag=3,
        tags={"cave", "path", "sea"},
    ),
    "reed_paths": Setting(
        id="reed_paths",
        label="the reed paths",
        entry="the little dock",
        bends="whispering turns",
        goal="a hidden pool full of silver minnows",
        ending_image="Back at the dock, the reeds still rustled, but the children stood taller because they had brought home a real adventure and a real lesson.",
        helper="boat keeper",
        helper_kind="man",
        depth_need=5,
        dimness=1,
        snag=1,
        tags={"marsh", "path"},
    ),
}

SPOOLS = {
    "red_string": SpoolCfg(
        id="red_string",
        label="red string spool",
        phrase="a red string spool",
        color="red",
        length=8,
        visibility=2,
        strength=2,
        tags={"spool", "string"},
    ),
    "gold_twine": SpoolCfg(
        id="gold_twine",
        label="gold twine spool",
        phrase="a gold twine spool",
        color="gold",
        length=10,
        visibility=1,
        strength=3,
        tags={"spool", "twine"},
    ),
    "blue_ribbon": SpoolCfg(
        id="blue_ribbon",
        label="blue ribbon spool",
        phrase="a blue ribbon spool",
        color="blue",
        length=6,
        visibility=3,
        strength=1,
        tags={"spool", "ribbon"},
    ),
    "silver_thread": SpoolCfg(
        id="silver_thread",
        label="silver thread spool",
        phrase="a silver thread spool",
        color="silver",
        length=4,
        visibility=2,
        strength=1,
        tags={"spool", "thread"},
    ),
}

PACES = {
    "careful": Pace(
        id="careful",
        line="They went carefully, hand to stone and hand to root, letting the string settle before taking the next step.",
        risk_add=0,
        tags={"careful"},
    ),
    "rush": Pace(
        id="rush",
        line="They rushed from turn to turn as if treasure might run away, and the string skipped over rocks instead of resting on them.",
        risk_add=1,
        tags={"rush"},
    ),
}

GIRL_NAMES = ["Mina", "Lily", "Ava", "Zoe", "Nora", "Ella", "Lucy", "Maya"]
BOY_NAMES = ["Tom", "Ben", "Max", "Eli", "Finn", "Noah", "Theo", "Sam"]


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for setting_id, setting in SETTINGS.items():
        for spool_id, spool in SPOOLS.items():
            if usable_spool(setting, spool):
                combos.append((setting_id, spool_id))
    return combos


@dataclass
class StoryParams:
    setting: str
    spool: str
    pace: str
    leader_name: str
    leader_type: str
    peer_name: str
    peer_type: str
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
    "maze": [
        (
            "Why can a maze feel confusing?",
            "A maze has many turns that look alike, so it is easy to forget which way you came. A clear marker helps your eyes and memory work together.",
        )
    ],
    "cave": [
        (
            "Why should children move slowly in a cave?",
            "Caves can be dim, slippery, and echoey, so moving slowly helps you notice rocks, water, and the way back. Slow steps make good choices easier.",
        )
    ],
    "path": [
        (
            "Why is it helpful to mark a path on an adventure?",
            "A marker shows where you have already been, so you can follow it back instead of guessing. That makes getting home much safer.",
        )
    ],
    "spool": [
        (
            "What is a spool?",
            "A spool is a round holder with thread, string, ribbon, or twine wrapped around it. You can pull the material off a little at a time.",
        )
    ],
    "string": [
        (
            "Why would someone use string as a trail marker?",
            "String can make a bright line from one place to another. If you leave it carefully, you can follow it back the same way you came.",
        )
    ],
    "twine": [
        (
            "What is twine?",
            "Twine is a strong kind of string made for tying things. It is useful when you need something tougher than thin thread.",
        )
    ],
    "ribbon": [
        (
            "What is ribbon?",
            "Ribbon is a soft strip of cloth or shiny material. It is easy to see, but it may not be as strong as twine.",
        )
    ],
    "thread": [
        (
            "What is thread used for?",
            "Thread is a very thin string often used for sewing. It is good for stitches, but not always strong enough for rough outdoor pulling.",
        )
    ],
    "careful": [
        (
            "Why is going carefully brave?",
            "Going carefully is brave because you are thinking about what could happen and choosing the safe way anyway. Brave does not mean hurrying.",
        )
    ],
    "rush": [
        (
            "What can happen if you rush on an adventure?",
            "When you rush, you miss details and make more mistakes. A good plan can fail if you move faster than your eyes and hands can follow.",
        )
    ],
}
KNOWLEDGE_ORDER = ["maze", "cave", "path", "spool", "string", "twine", "ribbon", "thread", "careful", "rush"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    setting = f["setting"]
    spool = f["spool_cfg"]
    pace = f["pace"]
    leader = f["leader"]
    peer = f["peer"]
    outcome = f["outcome"]
    if outcome == "returned":
        return [
            f'Write a short adventure story for a 3-to-5-year-old that includes the words "buy", "peer", and "spool". Two children explore {setting.label} after they buy {spool.phrase}.',
            f"Tell a gentle adventure where {leader.id} and {peer.id} use a spool of string to mark their way, repeating the line 'Step by step, pull and peer.'",
            f"Write a child-facing story where a careful plan turns a twisty place into a safe adventure and the children find their way home by following string.",
        ]
    return [
        f'Write a short adventure story for a 3-to-5-year-old that includes the words "buy", "peer", and "spool". Two children explore {setting.label} after they buy {spool.phrase}, but the string snaps.',
        f"Tell a gentle cautionary adventure where {peer.id} remembers the safety plan, the children stay together, and a calm helper leads them back out.",
        f"Write a story with repetition in which a trail-string plan partly fails because the children move too fast, but the ending still feels safe and warm.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    leader = f["leader"]
    peer = f["peer"]
    setting = f["setting"]
    spool = f["spool_cfg"]
    pace = f["pace"]
    helper = f["helper"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {leader.id} and {peer.id}, two children who wanted a real little adventure together. Their trip began at {setting.entry}, where the winding place looked exciting and tricky.",
        ),
        (
            f"Why did {leader.id} and {peer.id} buy a spool?",
            f"They wanted a trail they could follow home, so they decided to buy {spool.phrase}. The turns in {setting.label} looked easy to lose, and the spool gave them a plan.",
        ),
        (
            "What words did the children repeat as they walked?",
            'They kept saying, "Step by step, pull and peer." The repeated line helped them remember to watch the path and use the string carefully.',
        ),
        (
            f"What did they find at the end of the path?",
            f"They reached {setting.goal}. Getting there made the adventure feel real, but it also reminded them they still needed a safe way back.",
        ),
    ]
    if outcome == "returned":
        qa.append(
            (
                "How did they get back out?",
                f"They followed the {spool.color} string back through each turn until they reached {setting.entry} again. Because the spool was easy to see and strong enough for the trip, their plan worked all the way home.",
            )
        )
        qa.append(
            (
                f"Why did going {pace.id}ly help?",
                f"Going {pace.id}ly kept the string from jerking too hard against stones and branches. Their patient steps helped the adventure stay exciting without becoming frightening.",
            )
        )
    else:
        qa.append(
            (
                "What went wrong with the string?",
                f"The string snagged and snapped, so the children could not follow one full line home. It broke because the path was rougher than the spool could handle at that pace.",
            )
        )
        qa.append(
            (
                f"How did {peer.id} help when things got scary?",
                f"{peer.id} told them not to run and to stay together where they were. That calm choice mattered because it let the {helper.label} find them quickly and lead them out.",
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended safely with the {helper.label} bringing them back to {setting.entry}. The children still had an adventure, but they also learned that a brave plan works best when brave feet go slowly.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["setting"].tags) | set(f["spool_cfg"].tags) | set(f["pace"].tags)
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
        parts = []
        if ent.role:
            parts.append(f"role={ent.role}")
        if meters:
            parts.append(f"meters={dict(meters)}")
        if memes:
            parts.append(f"memes={dict(memes)}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                parts.append(f"attrs={shown}")
        lines.append(f"  {ent.id:8} ({ent.type:10}) {' '.join(parts)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="fern_maze",
        spool="red_string",
        pace="careful",
        leader_name="Mina",
        leader_type="girl",
        peer_name="Tom",
        peer_type="boy",
    ),
    StoryParams(
        setting="sea_cave",
        spool="red_string",
        pace="rush",
        leader_name="Ava",
        leader_type="girl",
        peer_name="Ben",
        peer_type="boy",
    ),
    StoryParams(
        setting="reed_paths",
        spool="blue_ribbon",
        pace="careful",
        leader_name="Nora",
        leader_type="girl",
        peer_name="Eli",
        peer_type="boy",
    ),
    StoryParams(
        setting="sea_cave",
        spool="blue_ribbon",
        pace="rush",
        leader_name="Lucy",
        leader_type="girl",
        peer_name="Max",
        peer_type="boy",
    ),
    StoryParams(
        setting="fern_maze",
        spool="gold_twine",
        pace="careful",
        leader_name="Sam",
        leader_type="boy",
        peer_name="Maya",
        peer_type="girl",
    ),
]


def explain_rejection(setting: Setting, spool: SpoolCfg) -> str:
    if spool.length < setting.depth_need:
        return (
            f"(No story: {spool.phrase} is too short for {setting.label}. "
            f"It would run out before the children reached {setting.goal}, so it cannot honestly guide them back.)"
        )
    if spool.visibility < setting.dimness:
        return (
            f"(No story: {spool.phrase} would be too hard to see in {setting.label}. "
            f"A trail marker has to be visible enough to work as a real plan.)"
        )
    return "(No story: that setting and spool do not make a reasonable adventure.)"


def outcome_of(params: StoryParams) -> str:
    if params.setting not in SETTINGS or params.spool not in SPOOLS or params.pace not in PACES:
        raise StoryError("(No story: the requested parameters are not in this world.)")
    return "returned" if intact_return(SETTINGS[params.setting], SPOOLS[params.spool], PACES[params.pace]) else "rescued"


ASP_RULES = r"""
usable_spool(S, Sp) :- setting(S), spool(Sp), need(S, N), length(Sp, L), L >= N,
                       dimness(S, D), visibility(Sp, V), V >= D.
valid(S, Sp) :- usable_spool(S, Sp).

risk(S, P, R) :- snag(S, A), risk_add(P, B), R = A + B.
returned(S, Sp, P) :- valid(S, Sp), risk(S, P, R), strength(Sp, T), T >= R.
rescued(S, Sp, P) :- valid(S, Sp), not returned(S, Sp, P).

outcome(returned) :- chosen_setting(S), chosen_spool(Sp), chosen_pace(P), returned(S, Sp, P).
outcome(rescued) :- chosen_setting(S), chosen_spool(Sp), chosen_pace(P), rescued(S, Sp, P).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for setting_id, setting in SETTINGS.items():
        lines.append(asp.fact("setting", setting_id))
        lines.append(asp.fact("need", setting_id, setting.depth_need))
        lines.append(asp.fact("dimness", setting_id, setting.dimness))
        lines.append(asp.fact("snag", setting_id, setting.snag))
    for spool_id, spool in SPOOLS.items():
        lines.append(asp.fact("spool", spool_id))
        lines.append(asp.fact("length", spool_id, spool.length))
        lines.append(asp.fact("visibility", spool_id, spool.visibility))
        lines.append(asp.fact("strength", spool_id, spool.strength))
    for pace_id, pace in PACES.items():
        lines.append(asp.fact("pace", pace_id))
        lines.append(asp.fact("risk_add", pace_id, pace.risk_add))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_setting", params.setting),
            asp.fact("chosen_spool", params.spool),
            asp.fact("chosen_pace", params.pace),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: two children buy a spool and mark their way through a tiny adventure."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--spool", choices=SPOOLS)
    ap.add_argument("--pace", choices=PACES)
    ap.add_argument("--leader-name")
    ap.add_argument("--peer-name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible setting/spool pairs derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    names = GIRL_NAMES if gender == "girl" else BOY_NAMES
    pool = [name for name in names if name != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.spool:
        if not usable_spool(SETTINGS[args.setting], SPOOLS[args.spool]):
            raise StoryError(explain_rejection(SETTINGS[args.setting], SPOOLS[args.spool]))

    combos = [
        combo
        for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.spool is None or combo[1] == args.spool)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, spool_id = rng.choice(sorted(combos))
    pace_id = args.pace or rng.choice(sorted(PACES))
    leader_name, leader_type = _pick_name(rng)
    peer_name, peer_type = _pick_name(rng, avoid=leader_name)
    if args.leader_name:
        leader_name = args.leader_name
    if args.peer_name:
        peer_name = args.peer_name
        if peer_name == leader_name:
            raise StoryError("(No story: the two children need different names.)")
    return StoryParams(
        setting=setting_id,
        spool=spool_id,
        pace=pace_id,
        leader_name=leader_name,
        leader_type=leader_type,
        peer_name=peer_name,
        peer_type=peer_type,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(No story: unknown setting '{params.setting}'.)")
    if params.spool not in SPOOLS:
        raise StoryError(f"(No story: unknown spool '{params.spool}'.)")
    if params.pace not in PACES:
        raise StoryError(f"(No story: unknown pace '{params.pace}'.)")
    setting = SETTINGS[params.setting]
    spool = SPOOLS[params.spool]
    pace = PACES[params.pace]
    if not usable_spool(setting, spool):
        raise StoryError(explain_rejection(setting, spool))
    if params.leader_name == params.peer_name:
        raise StoryError("(No story: the two children need different names.)")

    world = tell(
        setting=setting,
        spool=spool,
        pace=pace,
        leader_name=params.leader_name,
        leader_type=params.leader_type,
        peer_name=params.peer_name,
        peer_type=params.peer_type,
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

    python_pairs = set(valid_combos())
    clingo_pairs = set(asp_valid_combos())
    if python_pairs == clingo_pairs:
        print(f"OK: gate matches valid_combos() ({len(python_pairs)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if python_pairs - clingo_pairs:
            print("  only in python:", sorted(python_pairs - clingo_pairs))
        if clingo_pairs - python_pairs:
            print("  only in clingo:", sorted(clingo_pairs - python_pairs))

    cases = list(CURATED)
    for seed in range(100):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(params)

    mismatches = 0
    for params in cases:
        try:
            py = outcome_of(params)
            cl = asp_outcome(params)
        except StoryError:
            mismatches += 1
            continue
        if py != cl:
            mismatches += 1
    if mismatches == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {mismatches}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("(Verify failed: generated an empty story.)")
        emit(smoke, trace=False, qa=False, header="")
        print("OK: smoke test generated and emitted a normal story.")
    except Exception as err:  # pragma: no cover - verify path
        rc = 1
        print(f"VERIFY SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/2.\n#show returned/3.\n#show rescued/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        pairs = asp_valid_combos()
        print(f"{len(pairs)} compatible (setting, spool) pairs:\n")
        for setting_id, spool_id in pairs:
            print(f"  {setting_id:10} {spool_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

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
            header = f"### {p.leader_name} & {p.peer_name}: {p.setting}, {p.spool}, {p.pace}, {outcome_of(p)}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
