#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/wool_john_friendship_cautionary_inner_monologue_rhyming.py
======================================================================================

A standalone story world for a small rhyming, cautionary friendship tale about
John, a ball of wool, and the difference between a clever-looking idea and a
safe one.

World premise
-------------
John and a friend want to make their play space feel magical by stretching wool
for a game. The unsafe version lays wool low across a walking path, where it can
catch a foot. The safer version lifts the wool onto a wall, rail, or table as a
friendship decoration instead. The world model tracks when a walkway is blocked,
when someone stumbles, and how care, trust, and caution affect whether John
listens before the mishap happens.

The prose stays close to a child-facing rhyming style, and it includes John's
inner monologue as part of the state-driven turn.

Run it
------
    python storyworlds/worlds/gpt-5.4/wool_john_friendship_cautionary_inner_monologue_rhyming.py
    python storyworlds/worlds/gpt-5.4/wool_john_friendship_cautionary_inner_monologue_rhyming.py --place playroom --plan web --anchor doorway
    python storyworlds/worlds/gpt-5.4/wool_john_friendship_cautionary_inner_monologue_rhyming.py --anchor bookshelf
    python storyworlds/worlds/gpt-5.4/wool_john_friendship_cautionary_inner_monologue_rhyming.py --all --qa
    python storyworlds/worlds/gpt-5.4/wool_john_friendship_cautionary_inner_monologue_rhyming.py --verify
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
JOHN_URGE = 6
CAUTIOUS_TRAITS = {"careful", "cautious", "thoughtful", "gentle"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    age: int = 0
    attrs: dict = field(default_factory=dict)
    walkway: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "aunt"}
        male = {"boy", "father", "man", "uncle"}
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
            "aunt": "aunt",
            "uncle": "uncle",
        }.get(self.type, self.type)
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
    place: str
    scene: str
    surfaces: set[str] = field(default_factory=set)
    affords: set[str] = field(default_factory=set)
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


@dataclass
class Plan:
    id: str
    name: str
    wish: str
    pattern: str
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
class Anchor:
    id: str
    label: str
    phrase: str
    walkway: bool = True
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
class SafeMake:
    id: str
    label: str
    needs: set[str] = field(default_factory=set)
    works_for: set[str] = field(default_factory=set)
    offer: str = ""
    ending: str = ""
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
        clone.facts = dict(self.facts)
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


def _r_block(world: World) -> list[str]:
    wool = world.get("wool")
    anchor = world.get("anchor")
    if wool.meters["stretched_low"] < THRESHOLD or not anchor.walkway:
        return []
    sig = ("block", anchor.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    anchor.meters["blocked"] += 1
    world.get("room").meters["risk"] += 1
    return []


def _r_stumble(world: World) -> list[str]:
    anchor = world.get("anchor")
    friend = world.get("friend")
    wool = world.get("wool")
    if anchor.meters["blocked"] < THRESHOLD or friend.meters["walking"] < THRESHOLD:
        return []
    sig = ("stumble", friend.id, anchor.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    friend.meters["stumble"] += 1
    wool.meters["tangled"] += 1
    friend.memes["fear"] += 1
    world.get("john").memes["guilt"] += 1
    return ["__stumble__"]


CAUSAL_RULES = [
    Rule(name="block", tag="physical", apply=_r_block),
    Rule(name="stumble", tag="physical", apply=_r_stumble),
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


def risky_anchor(anchor: Anchor) -> bool:
    return anchor.walkway


def compatible_safe_makes(setting: Setting, plan: Plan) -> list[SafeMake]:
    out = []
    for maker in SAFE_MAKES.values():
        if plan.id in maker.works_for and maker.needs.issubset(setting.surfaces):
            out.append(maker)
    return out


def best_safe_make(setting: Setting, plan: Plan) -> Optional[SafeMake]:
    options = compatible_safe_makes(setting, plan)
    return options[0] if options else None


def caution_strength(trait: str) -> int:
    return 4 if trait in CAUTIOUS_TRAITS else 2


def would_avert(friendship: int, john_age: int, friend_age: int, trait: str) -> bool:
    older_bonus = 3 if friend_age > john_age else 0
    trust_bonus = 2 if friendship >= 6 else 0
    return caution_strength(trait) + older_bonus + trust_bonus > JOHN_URGE


def _stretch_wool(world: World, narrate: bool = True) -> None:
    wool = world.get("wool")
    wool.meters["stretched_low"] += 1
    propagate(world, narrate=narrate)


def predict_trouble(world: World) -> dict:
    sim = world.copy()
    _stretch_wool(sim, narrate=False)
    sim.get("friend").meters["walking"] += 1
    propagate(sim, narrate=False)
    return {
        "blocked": sim.get("anchor").meters["blocked"] >= THRESHOLD,
        "stumble": sim.get("friend").meters["stumble"] >= THRESHOLD,
        "risk": sim.get("room").meters["risk"],
    }


def introduce(world: World, john: Entity, friend: Entity, setting: Setting) -> None:
    john.memes["joy"] += 1
    friend.memes["joy"] += 1
    world.say(
        f"In {setting.place}, where soft afternoon light lay low, "
        f"John and {friend.id} played where warm small imaginations grow."
    )
    world.say(
        f"{setting.scene} Between them sat a round ball of wool, red-gold and bright, "
        f"the sort that makes a simple room feel full of make-believe delight."
    )


def plan_game(world: World, john: Entity, friend: Entity, plan: Plan, anchor: Anchor) -> None:
    john.memes["desire"] += 1
    world.say(
        f'"Let us make {plan.pattern}," said John, with cheeks aglow. '
        f'"From here to {anchor.phrase}, the wool can twist and softly flow."'
    )
    world.say(
        f"To John the idea seemed grand and cool, a shining little crown: "
        f"{plan.wish} using only friendship, hands, and wool wound round and down."
    )


def inner_monologue(world: World, john: Entity, anchor: Anchor) -> None:
    john.memes["thinking"] += 1
    world.say(
        f'Inside his head John sang a thought: '
        f'"This stripe of wool will look so fine; '
        f'it may be low, yet still, perhaps, no foot will cross the line."'
    )
    if anchor.walkway:
        world.say(
            f'But then another quieter thought came tiptoeing through his mind: '
            f'"A path is for quick passing feet. If wool lies there, what will they find?"'
        )


def warn(world: World, friend: Entity, john: Entity, anchor: Anchor) -> None:
    pred = predict_trouble(world)
    friend.memes["care"] += 1
    world.facts["predicted_stumble"] = bool(pred["stumble"])
    world.facts["predicted_risk"] = int(pred["risk"])
    extra = ""
    if friend.age > john.age:
        extra = f" Being a little older, {friend.pronoun()} spoke with extra steadiness."
    world.say(
        f'{friend.id} held the wool and paused. "{anchor.label.capitalize()}s are for walking," '
        f'{friend.pronoun()} said. "If we stretch it low, a shoe could catch, '
        f'and one small trip could turn our fun to fright."{extra}'
    )


def back_down(world: World, john: Entity, friend: Entity, maker: SafeMake) -> None:
    john.memes["relief"] += 1
    friend.memes["relief"] += 1
    john.memes["care"] += 1
    world.say(
        f'John looked at the wool, then looked at {friend.id}, and breathed before he moved. '
        f'"A game that scares my friend is not the game I want," he thought, and that thought proved true.'
    )
    world.say(
        f'Together they chose {maker.label} instead. {maker.offer} '
        f'The wool stayed high, their feet stayed free, and the room stayed bright with trust.'
    )


def defy(world: World, john: Entity) -> None:
    john.memes["defiance"] += 1
    world.say(
        f'John bit his lip and tugged the strand. "Just one quick try," he thought. '
        f'"If we are quick and light and neat, no trouble will be brought."'
    )


def stretch_across(world: World, anchor: Anchor) -> None:
    _stretch_wool(world, narrate=False)
    world.say(
        f"So John drew the wool from hand to hand and laid it low across {anchor.phrase}. "
        f"It looked like a magic silver line, thin-spun and fine and sly."
    )


def stumble(world: World, friend: Entity, anchor: Anchor) -> None:
    friend.meters["walking"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then {friend.id} turned to fetch the next bright loop and caught a toe at {anchor.phrase}. "
        f"{friend.pronoun().capitalize()} bobbled, grabbed the air, and landed with a startled face."
    )
    world.say(
        f"The wool flew wild, the neat ball rolled, and little loops knotted into a heap. "
        f"No bones were hurt, but both children felt a sudden hush run deep."
    )


def apology_and_lesson(world: World, john: Entity, friend: Entity, grownup: Entity) -> None:
    john.memes["care"] += 1
    john.memes["guilt"] += 1
    friend.memes["care"] += 1
    john.memes["relief"] += 1
    friend.memes["relief"] += 1
    world.say(
        f'{grownup.label_word.capitalize()} came over at once and helped {friend.id} sit up straight. '
        f'"I am glad it was only a stumble," {grownup.pronoun()} said. '
        f'"Wool belongs in hands or high on walls, not where busy feet must wait."'
    )
    world.say(
        f'John swallowed hard and thought, "A pretty plan can still be wrong." '
        f'Out loud he said, "I am sorry, {friend.id}. I should have listened sooner."'
    )
    world.say(
        f'{friend.id} gave a small nod back. "{friend.pronoun("subject").capitalize()} was scared, not mad," '
        f'{friend.pronoun()} said, and their friendship held fast instead of fraying.'
    )


def safe_finish(world: World, john: Entity, friend: Entity, maker: SafeMake) -> None:
    john.memes["joy"] += 1
    friend.memes["joy"] += 1
    world.say(
        f"After that they used the wool a safer way. {maker.offer} "
        f"Their hands moved high, not low; their craft grew where no shoe would sweep."
    )
    world.say(
        f"{maker.ending} John smiled at {friend.id} and thought, "
        f'"Good friends help fun grow wise and kind; that is the brightest design."'
    )


def tell(
    setting: Setting,
    plan: Plan,
    anchor_cfg: Anchor,
    maker: SafeMake,
    *,
    friend_name: str = "Mia",
    friend_gender: str = "girl",
    friend_trait: str = "careful",
    grownup_type: str = "mother",
    friendship: int = 7,
    john_age: int = 5,
    friend_age: int = 6,
) -> World:
    world = World(setting)
    john = world.add(
        Entity(
            id="John",
            kind="character",
            type="boy",
            role="john",
            age=john_age,
            traits=["eager"],
            attrs={"friendship": friendship},
        )
    )
    friend = world.add(
        Entity(
            id=friend_name,
            kind="character",
            type=friend_gender,
            role="friend",
            age=friend_age,
            traits=[friend_trait],
            attrs={"friendship": friendship},
        )
    )
    grownup = world.add(
        Entity(
            id="Grownup",
            kind="character",
            type=grownup_type,
            role="grownup",
            label="the grownup",
        )
    )
    room = world.add(Entity(id="room", type="room", label=setting.place))
    wool = world.add(Entity(id="wool", type="wool", label="wool"))
    anchor = world.add(
        Entity(
            id="anchor",
            type="path",
            label=anchor_cfg.label,
            walkway=anchor_cfg.walkway,
        )
    )

    room.meters["risk"] = 0.0
    anchor.meters["blocked"] = 0.0
    wool.meters["stretched_low"] = 0.0
    wool.meters["tangled"] = 0.0
    friend.meters["walking"] = 0.0
    friend.meters["stumble"] = 0.0
    john.memes["guilt"] = 0.0
    john.memes["care"] = 0.0
    friend.memes["care"] = 0.0
    friend.memes["fear"] = 0.0

    introduce(world, john, friend, setting)
    plan_game(world, john, friend, plan, anchor_cfg)

    world.para()
    inner_monologue(world, john, anchor_cfg)
    warn(world, friend, john, anchor_cfg)

    averted = would_avert(friendship, john_age, friend_age, friend_trait)
    world.facts["averted"] = averted

    world.para()
    if averted:
        back_down(world, john, friend, maker)
        outcome = "averted"
    else:
        defy(world, john)
        stretch_across(world, anchor_cfg)
        stumble(world, friend, anchor_cfg)
        world.para()
        apology_and_lesson(world, john, friend, grownup)
        world.para()
        safe_finish(world, john, friend, maker)
        outcome = "stumble"

    if averted:
        world.para()
        safe_finish(world, john, friend, maker)

    world.facts.update(
        john=john,
        friend=friend,
        grownup=grownup,
        setting=setting,
        plan=plan,
        anchor_cfg=anchor_cfg,
        maker=maker,
        friendship=friendship,
        outcome=outcome,
        stumbled=friend.meters["stumble"] >= THRESHOLD,
        tangled=wool.meters["tangled"] >= THRESHOLD,
        listened=averted,
    )
    return world


SETTINGS = {
    "playroom": Setting(
        id="playroom",
        place="the playroom",
        scene="Blocks slept in a basket, and a low table waited like a tiny stage.",
        surfaces={"wall", "table"},
        affords={"web", "maze", "line"},
    ),
    "hall": Setting(
        id="hall",
        place="the hall",
        scene="Coats hung quiet by the door, and the long bright floor begged for games.",
        surfaces={"wall"},
        affords={"maze", "line"},
    ),
    "porch": Setting(
        id="porch",
        place="the porch",
        scene="A wooden rail looked out at the yard where sparrows hopped and peeped.",
        surfaces={"rail", "wall"},
        affords={"line", "web"},
    ),
}

PLANS = {
    "web": Plan(
        id="web",
        name="friendship web",
        wish="to spin a friendship web between two places",
        pattern="a web of secret strings",
        tags={"wool", "craft"},
    ),
    "maze": Plan(
        id="maze",
        name="wool maze",
        wish="to build a tiny maze for their toy animals",
        pattern="a maze of soft red paths",
        tags={"wool", "maze"},
    ),
    "line": Plan(
        id="line",
        name="finish line",
        wish="to make a grand finish line for racing toy boats and socks",
        pattern="a fluttering finish line",
        tags={"wool", "line"},
    ),
}

ANCHORS = {
    "doorway": Anchor(
        id="doorway",
        label="doorway",
        phrase="the doorway",
        walkway=True,
        tags={"walkway", "trip"},
    ),
    "hallway": Anchor(
        id="hallway",
        label="hallway",
        phrase="the middle of the hall",
        walkway=True,
        tags={"walkway", "trip"},
    ),
    "bottom_step": Anchor(
        id="bottom_step",
        label="bottom step",
        phrase="the bottom step",
        walkway=True,
        tags={"walkway", "stairs", "trip"},
    ),
    "bookshelf": Anchor(
        id="bookshelf",
        label="bookshelf",
        phrase="the side of the bookshelf",
        walkway=False,
        tags={"safeish", "not_walkway"},
    ),
}

SAFE_MAKES = {
    "wall_garland": SafeMake(
        id="wall_garland",
        label="a wall garland",
        needs={"wall"},
        works_for={"web", "maze", "line"},
        offer="They pinned the wool into loops along the wall and tucked paper stars between the bends.",
        ending="Soon a bright friendship garland climbed the wall, high above the floor like a happy song.",
        tags={"wall", "garland", "safe_craft"},
    ),
    "table_braid": SafeMake(
        id="table_braid",
        label="a braided table trail",
        needs={"table"},
        works_for={"maze", "line"},
        offer="They braided the wool over the table edge and made turning paths for their toy mice.",
        ending="On the table the wool curled in neat bright rivers, safe for hands and safe for toes.",
        tags={"table", "braid", "safe_craft"},
    ),
    "rail_wrap": SafeMake(
        id="rail_wrap",
        label="a porch rail wrap",
        needs={"rail"},
        works_for={"web", "line"},
        offer="They wrapped the wool high around the porch rail, crisscrossing it like little sunrise stripes.",
        ending="The porch rail glowed with wooly bands while the boards below stayed open for walking.",
        tags={"rail", "safe_craft"},
    ),
}

FRIEND_NAMES = {
    "girl": ["Mia", "Lily", "Nora", "Zoe", "Ava", "Ella"],
    "boy": ["Ben", "Max", "Leo", "Finn", "Theo", "Sam"],
}
FRIEND_TRAITS = ["careful", "cautious", "gentle", "thoughtful", "playful", "curious"]

KNOWLEDGE = {
    "wool": [
        (
            "What is wool?",
            "Wool is a soft fiber that can be spun into yarn for knitting or craft work. It bends easily, which is nice for making things, but that also means it should be kept out of busy walking paths.",
        )
    ],
    "trip": [
        (
            "Why is it unsafe to stretch string or wool across a walkway?",
            "A walkway is for moving feet, so a low strand can catch a shoe or toe. Even a soft thing can make someone stumble if it is in the wrong place.",
        )
    ],
    "garland": [
        (
            "What is a garland?",
            "A garland is a line of decorations hung up high or along a wall. It lets people enjoy pretty shapes without putting things where someone might trip.",
        )
    ],
    "friendship": [
        (
            "How can a good friend help when a game seems risky?",
            "A good friend can pause, warn kindly, and help think of a safer way to keep the fun. That protects both the game and the friendship.",
        )
    ],
    "stairs": [
        (
            "Why do steps need to stay clear?",
            "People need steady footing on steps. If something lies across a step, it is easier to lose balance and fall.",
        )
    ],
}


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place_id, setting in SETTINGS.items():
        for plan_id in setting.affords:
            plan = PLANS[plan_id]
            for anchor_id, anchor in ANCHORS.items():
                if risky_anchor(anchor) and best_safe_make(setting, plan):
                    combos.append((place_id, plan_id, anchor_id))
    return sorted(combos)


@dataclass
class StoryParams:
    place: str
    plan: str
    anchor: str
    maker: str
    friend_name: str
    friend_gender: str
    friend_trait: str
    grownup: str
    friendship: int = 7
    john_age: int = 5
    friend_age: int = 6
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


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    friend = f["friend"]
    plan = f["plan"]
    maker = f["maker"]
    outcome = f["outcome"]
    if outcome == "averted":
        return [
            'Write a short rhyming story for a 3-to-5-year-old that includes the word "wool" and a boy named John.',
            f"Tell a friendship story in rhyme where John wants to make {plan.name} with wool, but {friend.id} warns him and he listens before anyone gets hurt.",
            f"Write a cautionary story with inner monologue where John chooses {maker.label} instead of laying wool across a path.",
        ]
    return [
        'Write a short rhyming story for a 3-to-5-year-old that includes the word "wool" and a boy named John.',
        f"Tell a friendship-and-caution story in rhyme where John ignores {friend.id}'s warning about wool across a walkway, someone stumbles, and they fix the problem together.",
        f"Write a story with inner monologue where John first chooses the risky idea, then learns to use {maker.label} instead.",
    ]


def pair_phrase(friend: Entity) -> str:
    if friend.type == "boy":
        return "two friends, John and his boyhood pal"
    return "two friends, John and his dear friend"


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    john = f["john"]
    friend = f["friend"]
    grownup = f["grownup"]
    plan = f["plan"]
    anchor = f["anchor_cfg"]
    maker = f["maker"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair_phrase(friend)} {friend.id}. They are playing together, and John has to decide whether to choose a clever-looking idea or a safe one.",
        ),
        (
            "What did John want to make with the wool?",
            f"John wanted to make {plan.name} with the wool. He thought it would make the room feel magical and fun.",
        ),
        (
            f"Why did {friend.id} warn John?",
            f"{friend.id} warned John because the wool would lie low across {anchor.phrase}, which is a place for walking. {friend.pronoun().capitalize()} could imagine a foot catching there, and the world model in the story marks that spot as risky.",
        ),
    ]
    if f["outcome"] == "averted":
        qa.append(
            (
                "What happened after John listened?",
                f"John stopped before stretching the wool across the path, so nobody stumbled and the wool never tangled. Then the friends used {maker.label}, which kept the fun while leaving the floor clear.",
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended with John and {friend.id} making something beautiful in a safer place. The ending image proves the change: the wool is up high for hands and eyes, not down low for feet.",
            )
        )
    else:
        qa.append(
            (
                f"What happened when John stretched the wool across {anchor.phrase}?",
                f"{friend.id} caught a toe and stumbled, and the ball of wool tangled into a heap. No one was badly hurt, but the scare showed John that a pretty idea can still be unsafe.",
            )
        )
        qa.append(
            (
                f"What did John learn after {friend.id} stumbled?",
                f"John learned that wool should not be stretched low across a walkway, even if the game looks exciting. He also learned that listening to a caring friend sooner can stop fear before it starts.",
            )
        )
        qa.append(
            (
                f"How did John and {friend.id} fix the problem?",
                f"With help from {grownup.label_word}, they moved to {maker.label} instead. That kept their friendship strong because they solved the mistake together instead of letting it fray into blame.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"wool", "trip", "friendship"}
    if world.facts["anchor_cfg"].id == "bottom_step":
        tags.add("stairs")
    if world.facts["maker"].id == "wall_garland":
        tags.add("garland")
    out: list[tuple[str, str]] = []
    order = ["wool", "trip", "friendship", "stairs", "garland"]
    for tag in order:
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
        if ent.walkway:
            bits.append("walkway=True")
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.age:
            bits.append(f"age={ent.age}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v or v == 0}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


def explain_rejection(anchor: Anchor) -> str:
    return (
        f"(No story: {anchor.phrase} is not a real walking path here, so wool laid there "
        f"would not make an honest tripping risk. Pick a doorway, hallway, or bottom step.)"
    )


def explain_combo(place: str, plan: str) -> str:
    return (
        f"(No story: {SETTINGS[place].place} has no compatible safe wool craft for plan "
        f"'{plan}'. This world only tells stories where the children can end with a truly safer alternative.)"
    )


ASP_RULES = r"""
risky(A) :- anchor(A), walkway(A).
compatible_safe(S, P, M) :- setting(S), plan(P), maker(M),
                            works_for(M, P),
                            needs_ok(S, M).

needs_ok(S, M) :- maker(M), not maker_need(M, _), setting(S).
needs_ok(S, M) :- maker(M), setting(S), surface(S, wall), maker_need(M, wall),
                  not maker_need(M, table), not maker_need(M, rail).
needs_ok(S, M) :- maker(M), setting(S), surface(S, table), maker_need(M, table),
                  not maker_need(M, wall), not maker_need(M, rail).
needs_ok(S, M) :- maker(M), setting(S), surface(S, rail), maker_need(M, rail),
                  not maker_need(M, wall), not maker_need(M, table).
needs_ok(S, M) :- maker(M), setting(S), surface(S, wall), maker_need(M, wall),
                  surface(S, table), maker_need(M, table),
                  not maker_need(M, rail).
needs_ok(S, M) :- maker(M), setting(S), surface(S, wall), maker_need(M, wall),
                  surface(S, rail), maker_need(M, rail),
                  not maker_need(M, table).
needs_ok(S, M) :- maker(M), setting(S), surface(S, table), maker_need(M, table),
                  surface(S, rail), maker_need(M, rail),
                  not maker_need(M, wall).
needs_ok(S, M) :- maker(M), setting(S), surface(S, wall), maker_need(M, wall),
                  surface(S, table), maker_need(M, table),
                  surface(S, rail), maker_need(M, rail).

has_safe(S, P) :- compatible_safe(S, P, _).
valid(S, P, A) :- affords(S, P), risky(A), has_safe(S, P).

older_friend :- friend_age(FA), john_age(JA), FA > JA.
high_friendship :- friendship(F), F >= 6.
cautious_friend :- trait(T), is_cautious(T).

averted :- cautious_friend, older_friend.
averted :- cautious_friend, high_friendship.

outcome(averted) :- averted.
outcome(stumble) :- not averted.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for surf in sorted(setting.surfaces):
            lines.append(asp.fact("surface", sid, surf))
        for pid in sorted(setting.affords):
            lines.append(asp.fact("affords", sid, pid))
    for pid in PLANS:
        lines.append(asp.fact("plan", pid))
    for aid, anchor in ANCHORS.items():
        lines.append(asp.fact("anchor", aid))
        if anchor.walkway:
            lines.append(asp.fact("walkway", aid))
    for mid, maker in SAFE_MAKES.items():
        lines.append(asp.fact("maker", mid))
        for need in sorted(maker.needs):
            lines.append(asp.fact("maker_need", mid, need))
        for works in sorted(maker.works_for):
            lines.append(asp.fact("works_for", mid, works))
    for trait in sorted(CAUTIOUS_TRAITS):
        lines.append(asp.fact("is_cautious", trait))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join(
        [
            asp.fact("trait", params.friend_trait),
            asp.fact("friendship", params.friendship),
            asp.fact("john_age", params.john_age),
            asp.fact("friend_age", params.friend_age),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


CURATED = [
    StoryParams(
        place="playroom",
        plan="web",
        anchor="doorway",
        maker="wall_garland",
        friend_name="Mia",
        friend_gender="girl",
        friend_trait="careful",
        grownup="mother",
        friendship=8,
        john_age=5,
        friend_age=6,
    ),
    StoryParams(
        place="hall",
        plan="maze",
        anchor="hallway",
        maker="wall_garland",
        friend_name="Ben",
        friend_gender="boy",
        friend_trait="playful",
        grownup="father",
        friendship=4,
        john_age=6,
        friend_age=5,
    ),
    StoryParams(
        place="porch",
        plan="line",
        anchor="bottom_step",
        maker="rail_wrap",
        friend_name="Nora",
        friend_gender="girl",
        friend_trait="thoughtful",
        grownup="aunt",
        friendship=7,
        john_age=5,
        friend_age=7,
    ),
    StoryParams(
        place="playroom",
        plan="line",
        anchor="doorway",
        maker="table_braid",
        friend_name="Max",
        friend_gender="boy",
        friend_trait="curious",
        grownup="mother",
        friendship=3,
        john_age=5,
        friend_age=5,
    ),
]


def outcome_of(params: StoryParams) -> str:
    return "averted" if would_avert(params.friendship, params.john_age, params.friend_age, params.friend_trait) else "stumble"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: John, wool, friendship, caution, and a safer choice in a rhyming style."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--plan", choices=PLANS)
    ap.add_argument("--anchor", choices=ANCHORS)
    ap.add_argument("--maker", choices=SAFE_MAKES)
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
    ap.add_argument("--friend-name")
    ap.add_argument("--friend-trait", choices=FRIEND_TRAITS)
    ap.add_argument("--grownup", choices=["mother", "father", "aunt", "uncle"])
    ap.add_argument("--friendship", type=int, choices=list(range(0, 11)))
    ap.add_argument("--john-age", type=int, choices=[4, 5, 6, 7])
    ap.add_argument("--friend-age", type=int, choices=[4, 5, 6, 7])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible (place, plan, anchor) combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.anchor and not ANCHORS[args.anchor].walkway:
        raise StoryError(explain_rejection(ANCHORS[args.anchor]))

    combos = [
        combo
        for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.plan is None or combo[1] == args.plan)
        and (args.anchor is None or combo[2] == args.anchor)
    ]
    if not combos:
        if args.place and args.plan and best_safe_make(SETTINGS[args.place], PLANS[args.plan]) is None:
            raise StoryError(explain_combo(args.place, args.plan))
        raise StoryError("(No valid combination matches the given options.)")

    place, plan, anchor = rng.choice(combos)
    setting = SETTINGS[place]
    plan_cfg = PLANS[plan]
    makers = compatible_safe_makes(setting, plan_cfg)
    if not makers:
        raise StoryError(explain_combo(place, plan))

    if args.maker is not None:
        if args.maker not in [m.id for m in makers]:
            raise StoryError(
                f"(No story: maker '{args.maker}' does not fit {plan} in {place}. "
                f"Choose one of: {', '.join(m.id for m in makers)}.)"
            )
        maker_id = args.maker
    else:
        maker_id = rng.choice([m.id for m in makers])

    friend_gender = args.friend_gender or rng.choice(["girl", "boy"])
    friend_name = args.friend_name or rng.choice(FRIEND_NAMES[friend_gender])
    friend_trait = args.friend_trait or rng.choice(FRIEND_TRAITS)
    grownup = args.grownup or rng.choice(["mother", "father", "aunt", "uncle"])
    friendship = args.friendship if args.friendship is not None else rng.randint(3, 9)
    john_age = args.john_age if args.john_age is not None else rng.choice([4, 5, 6, 7])
    friend_age = args.friend_age if args.friend_age is not None else rng.choice([4, 5, 6, 7])

    return StoryParams(
        place=place,
        plan=plan,
        anchor=anchor,
        maker=maker_id,
        friend_name=friend_name,
        friend_gender=friend_gender,
        friend_trait=friend_trait,
        grownup=grownup,
        friendship=friendship,
        john_age=john_age,
        friend_age=friend_age,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in SETTINGS:
        raise StoryError(f"(Invalid place: {params.place})")
    if params.plan not in PLANS:
        raise StoryError(f"(Invalid plan: {params.plan})")
    if params.anchor not in ANCHORS:
        raise StoryError(f"(Invalid anchor: {params.anchor})")
    if params.maker not in SAFE_MAKES:
        raise StoryError(f"(Invalid maker: {params.maker})")
    if params.anchor not in ANCHORS or not ANCHORS[params.anchor].walkway:
        raise StoryError(explain_rejection(ANCHORS[params.anchor]))
    if (params.place, params.plan, params.anchor) not in valid_combos():
        raise StoryError("(The requested place, plan, and anchor do not form a valid story.)")
    allowed = {m.id for m in compatible_safe_makes(SETTINGS[params.place], PLANS[params.plan])}
    if params.maker not in allowed:
        raise StoryError(
            f"(Maker '{params.maker}' is not compatible with {params.plan} in {params.place}.)"
        )

    world = tell(
        SETTINGS[params.place],
        PLANS[params.plan],
        ANCHORS[params.anchor],
        SAFE_MAKES[params.maker],
        friend_name=params.friend_name,
        friend_gender=params.friend_gender,
        friend_trait=params.friend_trait,
        grownup_type=params.grownup,
        friendship=params.friendship,
        john_age=params.john_age,
        friend_age=params.friend_age,
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
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: ASP gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    cases = list(CURATED)
    for s in range(40):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(s))
        except StoryError:
            continue
        params.seed = s
        cases.append(params)

    bad = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            bad += 1
    if bad == 0:
        print(f"OK: ASP outcome matches Python on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(cases[0])
        if not smoke.story.strip():
            raise StoryError("empty story")
        print("OK: smoke-test generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, plan, anchor) combos:\n")
        for place, plan, anchor in combos:
            makers = ", ".join(m.id for m in compatible_safe_makes(SETTINGS[place], PLANS[plan]))
            print(f"  {place:9} {plan:6} {anchor:11} [{makers}]")
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
            header = f"### John & {p.friend_name}: {p.plan} at {p.place} near {p.anchor} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
