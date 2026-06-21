#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/dam_inner_monologue_mystery_to_solve_heartwarming.py
===============================================================================

A standalone story world about a child, a small dam, and a gentle mystery:
why won't the little pond behind the dam stay full?

The world models a tiny waterway, a handmade dam, a visible clue, a hidden
cause, and the right kind of repair. The child notices the clue, thinks the
problem through in an inner monologue, and solves the mystery with a caring
helper. Different materials fail in different ways, and only a compatible fix
is accepted.

Run it
------
    python storyworlds/worlds/gpt-5.4/dam_inner_monologue_mystery_to_solve_heartwarming.py
    python storyworlds/worlds/gpt-5.4/dam_inner_monologue_mystery_to_solve_heartwarming.py --dam_style pebble_wall --cause side_gap
    python storyworlds/worlds/gpt-5.4/dam_inner_monologue_mystery_to_solve_heartwarming.py --dam_style clay_bank --cause underflow
    python storyworlds/worlds/gpt-5.4/dam_inner_monologue_mystery_to_solve_heartwarming.py --all
    python storyworlds/worlds/gpt-5.4/dam_inner_monologue_mystery_to_solve_heartwarming.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/dam_inner_monologue_mystery_to_solve_heartwarming.py --verify
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
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "grandmother", "aunt", "woman"}
        male = {"boy", "father", "grandfather", "uncle", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {
            "grandmother": "grandma",
            "grandfather": "grandpa",
            "mother": "mom",
            "father": "dad",
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
    waterway: str
    shine: str
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


@dataclass
class DamStyle:
    id: str
    label: str
    build_text: str
    texture: str
    supports: set[str] = field(default_factory=set)
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
class Cause:
    id: str
    clue: str
    symptom: str
    leak_line: str
    thought: str
    under_or_side: str
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
class Fix:
    id: str
    label: str
    handles: set[str] = field(default_factory=set)
    action_text: str = ""
    qa_text: str = ""
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
class Goal:
    id: str
    wish: str
    object_label: str
    start_line: str
    success_line: str
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


def _r_leak(world: World) -> list[str]:
    pond = world.get("pond")
    dam = world.get("dam")
    if dam.meters["leaking"] < THRESHOLD:
        return []
    sig = ("leak", world.facts.get("cause_id", "?"))
    if sig in world.fired:
        return []
    world.fired.add(sig)
    pond.meters["depth"] -= 1
    pond.meters["low"] += 1
    hero = world.get("hero")
    hero.memes["worry"] += 1
    return ["__low_pond__"]


def _r_fix_holds(world: World) -> list[str]:
    dam = world.get("dam")
    pond = world.get("pond")
    if dam.meters["sealed"] < THRESHOLD:
        return []
    sig = ("fill", world.facts.get("fix_id", "?"))
    if sig in world.fired:
        return []
    world.fired.add(sig)
    dam.meters["leaking"] = 0.0
    pond.meters["depth"] += 2
    pond.meters["low"] = 0.0
    hero = world.get("hero")
    helper = world.get("helper")
    hero.memes["relief"] += 1
    hero.memes["joy"] += 1
    helper.memes["pride"] += 1
    return ["__pond_full__"]


CAUSAL_RULES: list[Rule] = [
    Rule(name="leak", tag="physical", apply=_r_leak),
    Rule(name="fix_holds", tag="physical", apply=_r_fix_holds),
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


def cause_fits(style: DamStyle, cause: Cause) -> bool:
    return cause.id in style.supports


def fix_fits(cause: Cause, fix: Fix) -> bool:
    return cause.id in fix.handles


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for setting_id in SETTINGS:
        for style_id, style in DAM_STYLES.items():
            for cause_id, cause in CAUSES.items():
                if not cause_fits(style, cause):
                    continue
                for fix_id, fix in FIXES.items():
                    if fix_fits(cause, fix):
                        combos.append((setting_id, style_id, cause_id, fix_id))
    return combos


def explain_combo(style: DamStyle, cause: Cause) -> str:
    return (
        f"(No story: {style.label} does not usually fail with {cause.id.replace('_', ' ')}. "
        f"This world only tells mysteries where the clue honestly fits the kind of dam.)"
    )


def explain_fix(cause: Cause, fix: Fix) -> str:
    return (
        f"(No story: {fix.label} would not solve {cause.id.replace('_', ' ')}. "
        f"The repair must match the real path the water is taking.)"
    )


def predict_cause(world: World, cause_id: str) -> dict:
    sim = world.copy()
    sim.facts["cause_id"] = cause_id
    sim.get("dam").meters["leaking"] += 1
    propagate(sim, narrate=False)
    pond = sim.get("pond")
    return {
        "pond_low": pond.meters["low"] >= THRESHOLD,
        "depth": pond.meters["depth"],
    }


def build_memory_line(goal: Goal, hero: Entity) -> str:
    keep = {
        "boats": f"{hero.id} had folded {goal.object_label} the night before and could still feel the neat little creases in {hero.pronoun('possessive')} fingers.",
        "ducks": f"{hero.id} had been hoping the calm water would make a quiet sipping place for the ducks that waddled past every morning.",
        "mill": f"{hero.id} had promised to show the tiny turning {goal.object_label} to the next child who came by the path.",
    }
    return keep[goal.id]


def introduce(world: World, hero: Entity, helper: Entity, goal: Goal, style: DamStyle) -> None:
    world.say(
        f"On a soft morning at {world.setting.place}, {hero.id} came with {hero.pronoun('possessive')} "
        f"{helper.label_word} to visit the little {world.setting.waterway}."
    )
    world.say(
        f"Yesterday they had built a small {style.label} dam there. {style.build_text} "
        f"It had made a quiet pool, and {goal.start_line}"
    )
    world.say(build_memory_line(goal, hero))


def discover_problem(world: World, hero: Entity, goal: Goal, cause: Cause) -> None:
    dam = world.get("dam")
    pond = world.get("pond")
    dam.meters["leaking"] += 1
    world.facts["cause_id"] = cause.id
    propagate(world, narrate=False)
    world.say(
        f"But this morning the pond behind the dam was not round and shining anymore. "
        f"It was shallow, and {cause.symptom}"
    )
    world.say(
        f"{hero.id} stopped on the stones and felt a small squeeze in {hero.pronoun('possessive')} chest. "
        f'"Oh," {hero.pronoun()} whispered, "what happened to our dam?"'
    )
    pond.meters["mystery"] += 1
    hero.memes["care"] += 1


def inspect(world: World, hero: Entity, cause: Cause, goal: Goal) -> None:
    pred = predict_cause(world, cause.id)
    world.facts["predicted_depth"] = pred["depth"]
    world.facts["predicted_low"] = pred["pond_low"]
    hero.memes["thinking"] += 1
    world.say(
        f"{hero.id} crouched close and watched. {cause.clue}"
    )
    world.say(
        f'{hero.pronoun().capitalize()} thought, "If {cause.thought}, that must be why the water will not stay for {goal.wish}."'
    )


def share_theory(world: World, hero: Entity, helper: Entity, cause: Cause) -> None:
    helper.memes["attention"] += 1
    world.say(
        f'"I think I found it," {hero.id} said. "{cause.leak_line}"'
    )
    world.say(
        f"{helper.label_word.capitalize()} knelt beside {hero.pronoun('object')} and followed the tiny moving line with warm, careful eyes."
    )


def repair(world: World, hero: Entity, helper: Entity, fix: Fix, cause: Cause) -> None:
    dam = world.get("dam")
    world.facts["fix_id"] = fix.id
    dam.meters["sealed"] += 1
    world.say(
        f'"Then let\'s help the water stay where it belongs," {helper.label_word} said.'
    )
    world.say(
        f"Together they {fix.action_text}."
    )
    propagate(world, narrate=False)
    hero.memes["trust"] += 1


def ending(world: World, hero: Entity, helper: Entity, goal: Goal) -> None:
    pond = world.get("pond")
    if pond.meters["depth"] < THRESHOLD:
        raise StoryError("(Story bug: the pond never filled after the repair.)")
    world.say(
        f"Soon the water gathered behind the dam again, bright and still. {goal.success_line}"
    )
    world.say(
        f"{helper.label_word.capitalize()} smiled at {hero.id}. "
        f'"You solved the mystery by looking closely," {helper.pronoun()} said.'
    )
    world.say(
        f"{hero.id} leaned against {helper.label_word} for one happy moment, watching {world.setting.ending_image}."
    )


def tell(
    setting: Setting,
    style: DamStyle,
    cause: Cause,
    fix: Fix,
    goal: Goal,
    hero_name: str = "Nora",
    hero_type: str = "girl",
    helper_type: str = "grandfather",
) -> World:
    if not cause_fits(style, cause):
        raise StoryError(explain_combo(style, cause))
    if not fix_fits(cause, fix):
        raise StoryError(explain_fix(cause, fix))

    world = World(setting=setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, role="hero"))
    helper = world.add(Entity(id="Helper", kind="character", type=helper_type, role="helper", label="the helper"))
    dam = world.add(Entity(id="dam", type="dam", label=f"{style.label} dam"))
    pond = world.add(Entity(id="pond", type="pond", label="the little pond"))

    pond.meters["depth"] = 1.0
    dam.meters["leaking"] = 0.0
    dam.meters["sealed"] = 0.0
    pond.meters["low"] = 0.0
    pond.meters["mystery"] = 0.0
    hero.memes["worry"] = 0.0
    hero.memes["thinking"] = 0.0
    hero.memes["joy"] = 0.0
    helper.memes["attention"] = 0.0
    helper.memes["pride"] = 0.0
    world.facts["cause_id"] = cause.id
    world.facts["fix_id"] = fix.id

    introduce(world, hero, helper, goal, style)
    world.para()
    discover_problem(world, hero, goal, cause)
    inspect(world, hero, cause, goal)
    world.para()
    share_theory(world, hero, helper, cause)
    repair(world, hero, helper, fix, cause)
    world.para()
    ending(world, hero, helper, goal)

    world.facts.update(
        hero=hero,
        helper=helper,
        setting=setting,
        dam_style=style,
        cause=cause,
        fix=fix,
        goal=goal,
        solved=dam.meters["sealed"] >= THRESHOLD and pond.meters["depth"] >= THRESHOLD,
        mystery_seen=pond.meters["mystery"] >= THRESHOLD,
    )
    return world


SETTINGS = {
    "garden_creek": Setting(
        id="garden_creek",
        place="the community garden",
        waterway="narrow creek",
        shine="the wet leaves looked silver",
        ending_image="two paper boats rocking without tipping",
        tags={"creek", "garden"},
    ),
    "park_brook": Setting(
        id="park_brook",
        place="the park",
        waterway="murmuring brook",
        shine="the water flashed between round stones",
        ending_image="a duck dipping its beak at the calm edge",
        tags={"brook", "park"},
    ),
    "orchard_rill": Setting(
        id="orchard_rill",
        place="the old orchard",
        waterway="thin rill",
        shine="apple leaves made green shadows on the water",
        ending_image="a little pinwheel mill turning and a robin hopping near it",
        tags={"orchard", "rill"},
    ),
}

DAM_STYLES = {
    "pebble_wall": DamStyle(
        id="pebble_wall",
        label="pebble wall",
        build_text="They had stacked smooth gray pebbles in a tidy line, pressing the biggest ones at the bottom.",
        texture="smooth pebbles",
        supports={"side_gap", "low_top"},
        tags={"stones", "dam"},
    ),
    "stick_weir": DamStyle(
        id="stick_weir",
        label="stick-and-leaf",
        build_text="They had woven twigs and broad leaves together until the little barrier looked almost like a beaver had smiled on it.",
        texture="sticks and leaves",
        supports={"side_gap", "underflow"},
        tags={"sticks", "dam"},
    ),
    "clay_bank": DamStyle(
        id="clay_bank",
        label="clay-and-stone",
        build_text="They had pressed cool brown clay between flat stones and patted the whole small ridge smooth with their palms.",
        texture="clay and stones",
        supports={"low_top", "underflow"},
        tags={"clay", "dam"},
    ),
}

CAUSES = {
    "side_gap": Cause(
        id="side_gap",
        clue="At one edge, a silver thread of water was sneaking around the side where two stones no longer touched.",
        symptom="the edge mud looked darker than the middle",
        leak_line="The water is slipping around the side.",
        thought="water keeps sneaking around that edge",
        under_or_side="side",
        tags={"leak", "water"},
    ),
    "low_top": Cause(
        id="low_top",
        clue="Across the middle, the stones wore a wet stripe, as if the water had been quietly climbing over the top all night.",
        symptom="the center of the dam shone with a fresh wet line",
        leak_line="The middle is too low, so the water keeps topping the dam.",
        thought="the middle stays lower than the rest",
        under_or_side="top",
        tags={"spill", "water"},
    ),
    "underflow": Cause(
        id="underflow",
        clue="At the bottom, tiny bubbles popped and a cool trickle showed itself under the dam before sliding away downstream.",
        symptom="small bubbles winked in the mud below the dam",
        leak_line="The water is going under the dam.",
        thought="the water can hide under the bottom",
        under_or_side="under",
        tags={"under", "water"},
    ),
}

FIXES = {
    "clay_wedge": Fix(
        id="clay_wedge",
        label="a clay wedge",
        handles={"side_gap"},
        action_text="pressed a thick thumbful of cool clay into the open side and tucked two little pebbles against it so it could not wash away",
        qa_text="pressed cool clay into the open side of the dam and held it in place with pebbles",
        tags={"clay", "repair"},
    ),
    "flat_stone": Fix(
        id="flat_stone",
        label="a flat capstone",
        handles={"low_top"},
        action_text="laid one flat stone across the low middle and patted smaller stones snugly around it",
        qa_text="set a flat stone on the low middle to make the top of the dam higher",
        tags={"stone", "repair"},
    ),
    "mud_packing": Fix(
        id="mud_packing",
        label="packed mud at the base",
        handles={"underflow"},
        action_text="pressed sticky mud along the bottom edge, tucking it under the dam until the bubbles stopped",
        qa_text="packed sticky mud along the bottom so the water could not slip under the dam",
        tags={"mud", "repair"},
    ),
}

GOALS = {
    "boats": Goal(
        id="boats",
        wish="floating the paper boats",
        object_label="two tiny paper boats",
        start_line="today they had planned to float two tiny paper boats in it",
        success_line="The two paper boats drifted out, touched noses, and floated side by side.",
        tags={"boats"},
    ),
    "ducks": Goal(
        id="ducks",
        wish="making a calm place for the ducks to sip",
        object_label="that quiet sipping place",
        start_line="today they had hoped to make a calm place where the ducks could stop and sip",
        success_line="A duck waddled near, tipped its beak into the still patch, and drank without hurrying.",
        tags={"ducks"},
    ),
    "mill": Goal(
        id="mill",
        wish="letting the little pinwheel mill turn beside the pool",
        object_label="the pinwheel mill",
        start_line="today they had planned to set a little pinwheel mill beside the pool and watch it turn",
        success_line="The pinwheel mill began to spin, and the water beside it stayed clear and bright.",
        tags={"mill"},
    ),
}

GIRL_NAMES = ["Nora", "Lily", "Maya", "Ella", "Zoe", "Anna", "Lucy", "Ivy"]
BOY_NAMES = ["Ben", "Theo", "Max", "Finn", "Sam", "Eli", "Leo", "Noah"]


@dataclass
class StoryParams:
    setting: str
    dam_style: str
    cause: str
    fix: str
    goal: str
    hero_name: str
    hero_gender: str
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
    "dam": [
        (
            "What is a dam?",
            "A dam is something that holds water back so it gathers in one place instead of rushing away. Big dams are built by people, and little ones can be made with stones, sticks, or mud.",
        )
    ],
    "leak": [
        (
            "What does it mean when water leaks?",
            "A leak means water is finding a little way out through, around, or under something. Even a tiny leak can slowly empty a pond if it keeps going.",
        )
    ],
    "spill": [
        (
            "Why does water go over the top if a dam is too low?",
            "Water keeps rising until it reaches the lowest high point. If one part of the dam is lower, the water spills over there first.",
        )
    ],
    "clay": [
        (
            "Why can clay help stop water?",
            "Clay is sticky and smooth, so when you press it into a gap it can block little spaces where water would slip through. That is why people use clay to seal small leaks.",
        )
    ],
    "mud": [
        (
            "Why does packed mud help under a dam?",
            "Packed mud can fill hidden spaces under the bottom and slow the water down. When the spaces are filled, the water has a harder time sneaking away.",
        )
    ],
    "stone": [
        (
            "Why does adding a flat stone help a low dam?",
            "A flat stone can make the top higher and straighter. Then the water does not spill over the low spot so easily.",
        )
    ],
    "boats": [
        (
            "Why do paper boats float?",
            "Paper boats float because their shape spreads their weight over the water instead of letting them sink straight down. They float best on calm water.",
        )
    ],
    "ducks": [
        (
            "Why do ducks like calm water?",
            "Calm water is easy to sip from and paddle through. When the water is not rushing fast, ducks can rest and drink more comfortably.",
        )
    ],
    "mill": [
        (
            "What is a pinwheel water mill?",
            "A pinwheel water mill is a small toy or craft that turns when water moves past it. Children can watch it spin to see where the water is flowing.",
        )
    ],
}
KNOWLEDGE_ORDER = ["dam", "leak", "spill", "clay", "mud", "stone", "boats", "ducks", "mill"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    goal = f["goal"]
    setting = f["setting"]
    style = f["dam_style"]
    cause = f["cause"]
    return [
        f'Write a heartwarming story for a 3-to-5-year-old that includes the word "dam" and follows a child solving a gentle water mystery at {setting.place}.',
        f"Tell a story where a {hero.type} named {hero.id} notices that a small {style.label} dam is not holding water, thinks the problem through in an inner monologue, and solves it with help.",
        f"Write a cozy mystery story where the clue is that {cause.clue.lower()} and the happy ending includes {goal.wish}.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    setting = f["setting"]
    style = f["dam_style"]
    cause = f["cause"]
    fix = f["fix"]
    goal = f["goal"]
    hw = helper.label_word
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, a child visiting {setting.place}, and {hero.pronoun('possessive')} {hw} who helps listen and repair the dam.",
        ),
        (
            "What was the mystery in the story?",
            f"The mystery was why the little pond behind the dam would not stay full. {hero.id} had come back expecting calm water for {goal.wish}, but the water had slipped away.",
        ),
        (
            f"What clue helped {hero.id} solve the mystery?",
            f"The clue was that {cause.clue.lower()} That showed exactly where the water was escaping, so the problem was not magic at all.",
        ),
        (
            f"What did {hero.id} think to {hero.pronoun('object')}self?",
            f'{hero.pronoun().capitalize()} thought, "If {cause.thought}, that must be why the water will not stay for {goal.wish}." That inner thought helped {hero.pronoun("object")} turn the clue into an answer.',
        ),
        (
            f"How did they fix the dam?",
            f"They {fix.qa_text}. That repair matched the real path the water was taking, so the pond could fill again.",
        ),
        (
            "How did the story end?",
            f"The water gathered behind the dam again, and {goal.success_line.lower()} The ending shows that the mystery was solved and the small plan became joyful again.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"dam", "leak"}
    tags |= set(f["cause"].tags)
    tags |= set(f["fix"].tags)
    tags |= set(f["goal"].tags)
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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:8} ({ent.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="garden_creek",
        dam_style="pebble_wall",
        cause="side_gap",
        fix="clay_wedge",
        goal="boats",
        hero_name="Nora",
        hero_gender="girl",
        helper_type="grandfather",
    ),
    StoryParams(
        setting="park_brook",
        dam_style="pebble_wall",
        cause="low_top",
        fix="flat_stone",
        goal="ducks",
        hero_name="Ben",
        hero_gender="boy",
        helper_type="grandmother",
    ),
    StoryParams(
        setting="orchard_rill",
        dam_style="stick_weir",
        cause="underflow",
        fix="mud_packing",
        goal="mill",
        hero_name="Maya",
        hero_gender="girl",
        helper_type="grandfather",
    ),
    StoryParams(
        setting="garden_creek",
        dam_style="clay_bank",
        cause="underflow",
        fix="mud_packing",
        goal="boats",
        hero_name="Theo",
        hero_gender="boy",
        helper_type="grandmother",
    ),
    StoryParams(
        setting="park_brook",
        dam_style="stick_weir",
        cause="side_gap",
        fix="clay_wedge",
        goal="ducks",
        hero_name="Lucy",
        hero_gender="girl",
        helper_type="grandmother",
    ),
]


ASP_RULES = r"""
% valid cause for this kind of dam
valid_cause(D, C) :- supports(D, C).

% valid fix for the actual cause
valid_fix(C, F) :- handles(F, C).

valid(S, D, C, F) :- setting(S), dam_style(D), cause(C), fix(F),
                     valid_cause(D, C), valid_fix(C, F).

solved :- chosen_dam(D), chosen_cause(C), chosen_fix(F),
          valid_cause(D, C), valid_fix(C, F).

#show valid/4.
#show solved/0.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for did, style in DAM_STYLES.items():
        lines.append(asp.fact("dam_style", did))
        for cid in sorted(style.supports):
            lines.append(asp.fact("supports", did, cid))
    for cid in CAUSES:
        lines.append(asp.fact("cause", cid))
    for fid, fix in FIXES.items():
        lines.append(asp.fact("fix", fid))
        for cid in sorted(fix.handles):
            lines.append(asp.fact("handles", fid, cid))
    return "\n".join(lines)


def asp_program(extra: str = "") -> str:
    return f"{asp_facts()}\n{extra}\n{ASP_RULES}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_solved(params: StoryParams) -> bool:
    import asp

    scenario = "\n".join(
        [
            asp.fact("chosen_dam", params.dam_style),
            asp.fact("chosen_cause", params.cause),
            asp.fact("chosen_fix", params.fix),
        ]
    )
    model = asp.one_model(asp_program(scenario))
    return bool(asp.atoms(model, "solved"))


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if cl - py:
            print("  only in clingo:", sorted(cl - py))
        if py - cl:
            print("  only in python:", sorted(py - cl))

    smoke_params = CURATED[0]
    try:
        sample = generate(smoke_params)
        if not sample.story.strip():
            raise StoryError("(Smoke test failed: empty story.)")
        emit(sample, trace=False, qa=False, header="")
        print("OK: smoke generation succeeded.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(50):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
            cases.append(params)
        except StoryError:
            rc = 1
            print(f"Unexpected random-resolution failure at seed {seed}.")
            break

    mismatches = []
    for params in cases:
        py_ok = (params.setting, params.dam_style, params.cause, params.fix) in py
        cl_ok = asp_solved(params)
        if py_ok != cl_ok:
            mismatches.append(params)
    if not mismatches:
        print(f"OK: solved parity matched on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {len(mismatches)} solved checks differed.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A heartwarming tiny mystery about a child solving why a small dam will not hold water."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--dam_style", choices=DAM_STYLES)
    ap.add_argument("--cause", choices=CAUSES)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--goal", choices=GOALS)
    ap.add_argument("--hero_gender", choices=["girl", "boy"])
    ap.add_argument("--hero_name")
    ap.add_argument("--helper_type", choices=["grandmother", "grandfather", "mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible stories derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.dam_style and args.cause:
        if not cause_fits(DAM_STYLES[args.dam_style], CAUSES[args.cause]):
            raise StoryError(explain_combo(DAM_STYLES[args.dam_style], CAUSES[args.cause]))
    if args.cause and args.fix:
        if not fix_fits(CAUSES[args.cause], FIXES[args.fix]):
            raise StoryError(explain_fix(CAUSES[args.cause], FIXES[args.fix]))

    combos = [
        combo
        for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.dam_style is None or combo[1] == args.dam_style)
        and (args.cause is None or combo[2] == args.cause)
        and (args.fix is None or combo[3] == args.fix)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, dam_style_id, cause_id, fix_id = rng.choice(sorted(combos))
    goal_id = args.goal or rng.choice(sorted(GOALS))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    hero_name = args.hero_name or rng.choice(GIRL_NAMES if hero_gender == "girl" else BOY_NAMES)
    helper_type = args.helper_type or rng.choice(["grandmother", "grandfather", "mother", "father"])
    return StoryParams(
        setting=setting_id,
        dam_style=dam_style_id,
        cause=cause_id,
        fix=fix_id,
        goal=goal_id,
        hero_name=hero_name,
        hero_gender=hero_gender,
        helper_type=helper_type,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting: {params.setting})")
    if params.dam_style not in DAM_STYLES:
        raise StoryError(f"(Unknown dam_style: {params.dam_style})")
    if params.cause not in CAUSES:
        raise StoryError(f"(Unknown cause: {params.cause})")
    if params.fix not in FIXES:
        raise StoryError(f"(Unknown fix: {params.fix})")
    if params.goal not in GOALS:
        raise StoryError(f"(Unknown goal: {params.goal})")

    world = tell(
        setting=SETTINGS[params.setting],
        style=DAM_STYLES[params.dam_style],
        cause=CAUSES[params.cause],
        fix=FIXES[params.fix],
        goal=GOALS[params.goal],
        hero_name=params.hero_name,
        hero_type=params.hero_gender,
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
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, dam_style, cause, fix) combos:\n")
        for setting_id, dam_style_id, cause_id, fix_id in combos:
            print(f"  {setting_id:13} {dam_style_id:12} {cause_id:10} {fix_id}")
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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero_name}: {p.dam_style} / {p.cause} / {p.fix} at {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
