#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/spaghetti_rhyme_mystery_to_solve_surprise_slice.py
==============================================================================

A small storyworld about an ordinary spaghetti night that turns into a rhyming
kitchen mystery. A child cannot find the tool needed for dinner, follows one or
two little rhyme notes, solves the mystery, and discovers a warm surprise slice
waiting with the missing tool.

The world is deliberately narrow and state-driven:
- a needed pasta tool goes missing
- the pot has to wait, which can make the noodles a little too soft
- rhyme clues turn worry into curiosity
- finding the tool resolves dinner
- finding the surprise slice changes the feeling of the whole evening

Run it
------
python storyworlds/worlds/gpt-5.4/spaghetti_rhyme_mystery_to_solve_surprise_slice.py
python storyworlds/worlds/gpt-5.4/spaghetti_rhyme_mystery_to_solve_surprise_slice.py --tool colander --hideout lower_cabinet
python storyworlds/worlds/gpt-5.4/spaghetti_rhyme_mystery_to_solve_surprise_slice.py -n 5 --seed 7 --qa
python storyworlds/worlds/gpt-5.4/spaghetti_rhyme_mystery_to_solve_surprise_slice.py --all
python storyworlds/worlds/gpt-5.4/spaghetti_rhyme_mystery_to_solve_surprise_slice.py --verify
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "grandmother", "woman"}
        male = {"boy", "father", "grandfather", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {
            "mother": "mom",
            "father": "dad",
            "grandmother": "grandma",
            "grandfather": "grandpa",
        }.get(self.type, self.type)
    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    job: str
    urgency: int
    compatible_hideouts: set[str] = field(default_factory=set)
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
    distance: int
    first_rhyme: str
    final_rhyme: str
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
class Surprise:
    id: str
    label: str
    phrase: str
    taste: str
    closing_image: str
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


def _r_waiting_worry(world: World) -> list[str]:
    tool = world.get("tool")
    pot = world.get("pot")
    child = world.get("child")
    helper = world.get("helper")
    if tool.meters["missing"] < THRESHOLD or pot.meters["waiting"] < THRESHOLD:
        return []
    sig = ("waiting_worry",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["worry"] += 1
    helper.memes["hurry"] += 1
    return []


def _r_clue_curiosity(world: World) -> list[str]:
    notes = world.get("notes")
    tool = world.get("tool")
    child = world.get("child")
    if notes.meters["found"] < THRESHOLD or tool.meters["missing"] < THRESHOLD:
        return []
    sig = ("clue_curiosity", int(notes.meters["found"]))
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["curiosity"] += 1
    if child.memes["worry"] >= THRESHOLD:
        child.memes["relief"] += 0.5
    return []


def _r_pasta_softens(world: World) -> list[str]:
    pot = world.get("pot")
    if pot.meters["waiting"] < THRESHOLD or pot.meters["delay"] < 2:
        return []
    sig = ("pasta_softens",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    pot.meters["soft"] += 1
    return []


def _r_found_tool(world: World) -> list[str]:
    tool = world.get("tool")
    child = world.get("child")
    if tool.meters["found"] < THRESHOLD:
        return []
    sig = ("found_tool",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["relief"] += 1
    child.memes["worry"] = 0.0
    return []


def _r_reveal_surprise(world: World) -> list[str]:
    surprise = world.get("surprise")
    child = world.get("child")
    helper = world.get("helper")
    if surprise.meters["revealed"] < THRESHOLD:
        return []
    sig = ("reveal_surprise",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["joy"] += 1
    child.memes["love"] += 1
    helper.memes["love"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="waiting_worry", tag="emotion", apply=_r_waiting_worry),
    Rule(name="clue_curiosity", tag="emotion", apply=_r_clue_curiosity),
    Rule(name="pasta_softens", tag="physical", apply=_r_pasta_softens),
    Rule(name="found_tool", tag="emotion", apply=_r_found_tool),
    Rule(name="reveal_surprise", tag="emotion", apply=_r_reveal_surprise),
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


TOOLS = {
    "colander": Tool(
        id="colander",
        label="colander",
        phrase="the silver colander",
        job="drain the spaghetti",
        urgency=2,
        compatible_hideouts={"dish_rack", "lower_cabinet"},
        tags={"pasta_tool", "drain"},
    ),
    "server": Tool(
        id="server",
        label="pasta server",
        phrase="the pasta server with the little claws",
        job="lift the spaghetti into bowls",
        urgency=1,
        compatible_hideouts={"utensil_drawer", "utensil_crock"},
        tags={"pasta_tool", "serve"},
    ),
    "grater": Tool(
        id="grater",
        label="cheese grater",
        phrase="the small cheese grater",
        job="snow a little cheese over the spaghetti",
        urgency=1,
        compatible_hideouts={"utensil_drawer", "dish_rack"},
        tags={"pasta_tool", "cheese"},
    ),
    "tongs": Tool(
        id="tongs",
        label="kitchen tongs",
        phrase="the springy kitchen tongs",
        job="turn the warm garlic bread",
        urgency=1,
        compatible_hideouts={"utensil_drawer", "counter_hook"},
        tags={"kitchen_tool", "bread"},
    ),
}

HIDEOUTS = {
    "dish_rack": Hideout(
        id="dish_rack",
        label="dish rack",
        phrase="the dish rack beside the sink",
        distance=1,
        first_rhyme='A paper note said, "If dinner seems a little slack, look by the cups in the dish rack."',
        final_rhyme='On the second slip were the words, "Where clean things dry and drip-drop clack, your noodle helper waits out back."',
        tags={"near", "sink"},
    ),
    "lower_cabinet": Hideout(
        id="lower_cabinet",
        label="lower cabinet",
        phrase="the lower cabinet by the sink",
        distance=2,
        first_rhyme='A paper note said, "First check the towels in their stack; the next small clue points down, not back."',
        final_rhyme='Tucked near the folded cloths was another rhyme: "Below the counter, dark and neat, the pasta helper hides by your feet."',
        tags={"farther", "sink"},
    ),
    "utensil_drawer": Hideout(
        id="utensil_drawer",
        label="utensil drawer",
        phrase="the long utensil drawer",
        distance=1,
        first_rhyme='A paper note said, "If forks and spoons make a click-clack choir, slide open the place where helpers retire."',
        final_rhyme='Inside was a final rhyme: "Past the napkins, smooth and square, the missing kitchen friend is there."',
        tags={"near", "drawer"},
    ),
    "utensil_crock": Hideout(
        id="utensil_crock",
        label="utensil crock",
        phrase="the blue crock by the stove",
        distance=1,
        first_rhyme='A paper note said, "When sauce gives off a tomato steam, look where tall spoons stand up and dream."',
        final_rhyme='Behind the big wooden spoon was one more slip: "In the jar where helpers lean, your dinner answer can be seen."',
        tags={"near", "counter"},
    ),
    "counter_hook": Hideout(
        id="counter_hook",
        label="counter hook",
        phrase="the little hook under the counter shelf",
        distance=2,
        first_rhyme='A paper note said, "Follow the smell of bread so nice, then look where shadows hang like ice."',
        final_rhyme='Near the bread box waited a second rhyme: "Under the shelf where small tools swing, your missing helper makes no ping."',
        tags={"farther", "counter"},
    ),
}

SURPRISES = {
    "garlic_bread": Surprise(
        id="garlic_bread",
        label="garlic-bread slice",
        phrase="a warm garlic-bread slice cut into a triangle",
        taste="buttery and crisp at the edge",
        closing_image="a buttery triangle of garlic bread",
        tags={"bread", "surprise_slice"},
    ),
    "apple_pie": Surprise(
        id="apple_pie",
        label="apple-pie slice",
        phrase="a small apple-pie slice on a blue plate",
        taste="sweet with cinnamon",
        closing_image="a little blue plate holding apple pie",
        tags={"dessert", "surprise_slice"},
    ),
    "orange_slice_cake": Surprise(
        id="orange_slice_cake",
        label="orange cake slice",
        phrase="a soft orange-cake slice with a tiny curl of peel",
        taste="bright and sunny",
        closing_image="a soft slice of orange cake",
        tags={"dessert", "surprise_slice"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Ava", "Nora", "Lucy", "Ella", "Maya", "Rose"]
BOY_NAMES = ["Ben", "Leo", "Sam", "Theo", "Max", "Eli", "Noah", "Finn"]
TRAITS = ["careful", "curious", "chatty", "patient", "bright-eyed", "gentle"]
HELPERS = ["mother", "father", "grandmother", "grandfather"]


def valid_combo(tool_id: str, hideout_id: str) -> bool:
    return hideout_id in TOOLS[tool_id].compatible_hideouts


def valid_combos() -> list[tuple[str, str]]:
    combos: list[tuple[str, str]] = []
    for tool_id in TOOLS:
        for hideout_id in HIDEOUTS:
            if valid_combo(tool_id, hideout_id):
                combos.append((tool_id, hideout_id))
    return combos


@dataclass
class StoryParams:
    tool: str
    hideout: str
    surprise: str
    child_name: str
    child_gender: str
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


CURATED = [
    StoryParams(
        tool="server",
        hideout="utensil_crock",
        surprise="garlic_bread",
        child_name="Lily",
        child_gender="girl",
        helper_type="father",
        child_trait="curious",
        seed=1,
    ),
    StoryParams(
        tool="colander",
        hideout="lower_cabinet",
        surprise="apple_pie",
        child_name="Ben",
        child_gender="boy",
        helper_type="grandmother",
        child_trait="patient",
        seed=2,
    ),
    StoryParams(
        tool="grater",
        hideout="dish_rack",
        surprise="orange_slice_cake",
        child_name="Maya",
        child_gender="girl",
        helper_type="mother",
        child_trait="bright-eyed",
        seed=3,
    ),
    StoryParams(
        tool="tongs",
        hideout="counter_hook",
        surprise="garlic_bread",
        child_name="Theo",
        child_gender="boy",
        helper_type="grandfather",
        child_trait="chatty",
        seed=4,
    ),
]


def explain_rejection(tool_id: str, hideout_id: str) -> str:
    tool = TOOLS[tool_id]
    hideout = HIDEOUTS[hideout_id]
    allowed = ", ".join(sorted(tool.compatible_hideouts))
    return (
        f"(No story: {tool.label} would not reasonably be tucked in {hideout.label}. "
        f"That tool belongs in one of these places: {allowed}.)"
    )


def outcome_of(params: StoryParams) -> str:
    tool = TOOLS[params.tool]
    hideout = HIDEOUTS[params.hideout]
    return "soft" if tool.urgency + hideout.distance >= 4 else "ontime"


def helper_intro(helper: Entity) -> str:
    if helper.type in {"grandmother", "grandfather"}:
        return f"{helper.label_word.capitalize()} was visiting for dinner"
    return f"{helper.label_word.capitalize()} was making dinner"


def start_evening(world: World, child: Entity, helper: Entity) -> None:
    world.say(
        f"On a cozy evening at home, {child.id} padded into the kitchen while {helper_intro(helper)}."
    )
    world.say(
        "A pot of spaghetti bobbed in hot water, the sauce made slow red bubbles, "
        "and the whole room smelled like tomatoes and toast."
    )


def assign_job(world: World, child: Entity, helper: Entity, tool: Tool) -> None:
    child.memes["proud"] += 1
    world.say(
        f'"Can you help me {tool.job}?" {helper.label_word.capitalize()} asked. '
        f"{child.id} nodded so quickly that {child.pronoun('possessive')} hair bounced."
    )


def notice_missing(world: World, child: Entity, helper: Entity, tool_cfg: Tool, hideout_cfg: Hideout) -> None:
    tool = world.get("tool")
    pot = world.get("pot")
    tool.meters["missing"] += 1
    pot.meters["waiting"] += 1
    pot.meters["delay"] = float(hideout_cfg.distance)
    world.facts["mystery_started"] = True
    propagate(world, narrate=False)
    world.say(
        f"But when {child.id} reached for {tool_cfg.phrase}, it was not on the counter."
    )
    world.say(
        f'"The {tool_cfg.label} is missing," {child.id} said, stopping with both hands in the air.'
    )
    if world.get("pot").meters["soft"] >= THRESHOLD:
        world.say(
            f"{helper.label_word.capitalize()} glanced at the pot and said they had better solve the mystery quickly."
        )
    else:
        world.say(
            f"{helper.label_word.capitalize()} smiled in a secret little way instead of looking upset."
        )


def invite_mystery(world: World, helper: Entity) -> None:
    world.say(
        f'"Then maybe the kitchen is speaking in rhyme tonight," {helper.label_word} said.'
    )


def read_first_clue(world: World, child: Entity, hideout_cfg: Hideout) -> None:
    notes = world.get("notes")
    notes.meters["found"] += 1
    world.facts["clues_read"] = int(notes.meters["found"])
    propagate(world, narrate=False)
    world.say(
        f"Near the cutting board, {child.id} found a folded note. {hideout_cfg.first_rhyme}"
    )
    if child.memes["curiosity"] >= THRESHOLD:
        world.say(
            f"{child.id}'s worried face changed. Now {child.pronoun()} looked more puzzled than scared."
        )


def read_second_clue(world: World, child: Entity, hideout_cfg: Hideout) -> None:
    notes = world.get("notes")
    if hideout_cfg.distance < 2:
        return
    notes.meters["found"] += 1
    world.facts["clues_read"] = int(notes.meters["found"])
    propagate(world, narrate=False)
    world.say(
        f"The first place held another tiny slip of paper. {hideout_cfg.final_rhyme}"
    )


def final_find(world: World, child: Entity, tool_cfg: Tool, hideout_cfg: Hideout, surprise_cfg: Surprise) -> None:
    tool = world.get("tool")
    pot = world.get("pot")
    surprise = world.get("surprise")
    tool.meters["missing"] = 0.0
    tool.meters["found"] += 1
    pot.meters["waiting"] = 0.0
    surprise.meters["revealed"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{child.id} opened {hideout_cfg.phrase} and found {tool_cfg.phrase} at last."
    )
    world.say(
        f"Beside it was {surprise_cfg.phrase}, wrapped in a napkin."
    )


def reveal_reason(world: World, child: Entity, helper: Entity, surprise_cfg: Surprise) -> None:
    world.say(
        f'"I hid it after lunch," {helper.label_word} admitted. '
        f'"You have been such a good kitchen helper this week that I wanted to leave you a small surprise."'
    )
    world.say(
        f'{child.id} laughed. "A mystery and a snack?" {child.pronoun().capitalize()} said. '
        f'"That is two good things."'
    )
    world.say(
        f'The little treat smelled {surprise_cfg.taste}, and even the waiting spaghetti seemed friendlier now.'
    )


def finish_dinner(world: World, child: Entity, helper: Entity, tool_cfg: Tool, surprise_cfg: Surprise) -> None:
    pot = world.get("pot")
    if tool_cfg.id == "colander":
        action = "They hurried to drain the spaghetti together"
    elif tool_cfg.id == "server":
        action = "They twirled the spaghetti into bowls together"
    elif tool_cfg.id == "grater":
        action = "They shook a snowy drift of cheese over the spaghetti together"
    else:
        action = "They turned the garlic bread and set the spaghetti bowls on the table together"
    world.say(action + ".")
    if pot.meters["soft"] >= THRESHOLD:
        world.say(
            "The noodles were a little softer than they had meant to make them, but the sauce still shone red and warm."
        )
    else:
        world.say(
            "Everything reached the table just in time, with steam curling up from the bowls."
        )
    world.say(
        f"By the end of dinner, {child.id} was still smiling at {surprise_cfg.closing_image}, "
        "and the missing-tool mystery had become the best part of spaghetti night."
    )


def tell(
    tool_cfg: Tool,
    hideout_cfg: Hideout,
    surprise_cfg: Surprise,
    *,
    child_name: str,
    child_gender: str,
    helper_type: str,
    child_trait: str,
) -> World:
    world = World()
    child = world.add(
        Entity(
            id=child_name,
            kind="character",
            type=child_gender,
            role="child",
            traits=["little", child_trait],
        )
    )
    helper = world.add(
        Entity(
            id="Helper",
            kind="character",
            type=helper_type,
            role="helper",
            label="the helper",
        )
    )
    pot = world.add(
        Entity(
            id="pot",
            type="pot",
            label="spaghetti pot",
            phrase="a pot of spaghetti",
        )
    )
    tool = world.add(
        Entity(
            id="tool",
            type="tool",
            label=tool_cfg.label,
            phrase=tool_cfg.phrase,
            attrs={"job": tool_cfg.job},
        )
    )
    notes = world.add(
        Entity(
            id="notes",
            type="notes",
            label="rhyme notes",
        )
    )
    surprise = world.add(
        Entity(
            id="surprise",
            type="food",
            label=surprise_cfg.label,
            phrase=surprise_cfg.phrase,
        )
    )

    pot.meters["boiling"] = 1.0
    pot.meters["delay"] = 0.0
    tool.meters["missing"] = 0.0
    tool.meters["found"] = 0.0
    notes.meters["found"] = 0.0
    surprise.meters["revealed"] = 0.0
    child.memes["worry"] = 0.0
    child.memes["curiosity"] = 0.0
    child.memes["joy"] = 0.0
    helper.memes["hurry"] = 0.0

    world.facts.update(
        child=child,
        helper=helper,
        pot=pot,
        tool_cfg=tool_cfg,
        hideout_cfg=hideout_cfg,
        surprise_cfg=surprise_cfg,
        clues_read=0,
        mystery_started=False,
    )

    start_evening(world, child, helper)
    assign_job(world, child, helper, tool_cfg)

    world.para()
    notice_missing(world, child, helper, tool_cfg, hideout_cfg)
    invite_mystery(world, helper)
    read_first_clue(world, child, hideout_cfg)
    if hideout_cfg.distance >= 2:
        read_second_clue(world, child, hideout_cfg)

    world.para()
    final_find(world, child, tool_cfg, hideout_cfg, surprise_cfg)
    reveal_reason(world, child, helper, surprise_cfg)

    world.para()
    finish_dinner(world, child, helper, tool_cfg, surprise_cfg)

    world.facts.update(
        outcome="soft" if pot.meters["soft"] >= THRESHOLD else "ontime",
        tool_found=tool.meters["found"] >= THRESHOLD,
        surprise_found=surprise.meters["revealed"] >= THRESHOLD,
        clues_read=int(notes.meters["found"]),
    )
    return world


KNOWLEDGE = {
    "spaghetti": [
        (
            "What is spaghetti?",
            "Spaghetti is a long kind of pasta that becomes soft when you cook it in boiling water. People often eat it with sauce."
        )
    ],
    "colander": [
        (
            "What does a colander do?",
            "A colander is a bowl with holes in it. It lets water run out while the pasta stays inside."
        )
    ],
    "server": [
        (
            "What is a pasta server?",
            "A pasta server is a spoon-like tool that helps lift and hold slippery noodles. It makes serving spaghetti easier."
        )
    ],
    "grater": [
        (
            "What does a cheese grater do?",
            "A cheese grater rubs cheese into tiny pieces. Those little pieces melt quickly on warm food."
        )
    ],
    "tongs": [
        (
            "What are kitchen tongs for?",
            "Kitchen tongs help you grab hot food without touching it with your fingers. They are useful for toast, bread, or noodles."
        )
    ],
    "rhyme": [
        (
            "What is a rhyme?",
            "A rhyme is when words sound alike at the end, like 'rack' and 'back.' Rhymes can make clues feel playful and easier to remember."
        )
    ],
    "mystery": [
        (
            "What is a mystery?",
            "A mystery is a problem or question you have to figure out. You solve it by noticing clues."
        )
    ],
    "surprise_slice": [
        (
            "What makes a surprise feel special?",
            "A surprise feels special when it is kind, thoughtful, and given at the right moment. Even something small can feel big when someone planned it with care."
        )
    ],
}
KNOWLEDGE_ORDER = [
    "spaghetti",
    "colander",
    "server",
    "grater",
    "tongs",
    "rhyme",
    "mystery",
    "surprise_slice",
]


def generation_prompts(world: World) -> list[str]:
    child = world.facts["child"]
    helper = world.facts["helper"]
    tool_cfg = world.facts["tool_cfg"]
    return [
        'Write a slice-of-life story for a 3-to-5-year-old that includes the word "spaghetti" and uses a rhyming kitchen mystery.',
        f"Tell a gentle family story where {child.id} cannot find the {tool_cfg.label} during spaghetti night, and {helper.label_word} turns the search into a rhyme game.",
        "Write a cozy story with a mystery to solve, two small clues, and a surprise slice waiting at the end of dinner."
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    child = world.facts["child"]
    helper = world.facts["helper"]
    tool_cfg = world.facts["tool_cfg"]
    hideout_cfg = world.facts["hideout_cfg"]
    surprise_cfg = world.facts["surprise_cfg"]
    outcome = world.facts["outcome"]
    clues = world.facts["clues_read"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id} and {child.pronoun('possessive')} {helper.label_word} during spaghetti night at home. They are in the kitchen together, trying to finish dinner."
        ),
        (
            f"Why did {child.id} feel worried at first?",
            f"{child.id} could not find the {tool_cfg.label}, even though they needed it to {tool_cfg.job}. The pot had to wait, so the missing tool made dinner feel stuck."
        ),
        (
            "How did the mystery begin?",
            f"It began when the missing tool turned out not to be lost after all. {helper.label_word.capitalize()} had hidden it on purpose and left rhyme notes to guide the search."
        ),
        (
            "How did the rhyme clues change the feeling in the kitchen?",
            f"At first the missing tool made the kitchen feel tense. Once {child.id} started reading the rhymes, worry turned into curiosity because each clue made the search feel like a game."
        ),
    ]
    qa.append(
        (
            "Where was the missing tool hiding?",
            f"It was hiding in {hideout_cfg.phrase}. {child.id} found it there after following {clues} little rhyme clue{'s' if clues != 1 else ''}."
        )
    )
    qa.append(
        (
            "What was the surprise?",
            f"The surprise was {surprise_cfg.phrase}. It was waiting right beside the missing tool, so solving the mystery led to a treat as well as the answer."
        )
    )
    if outcome == "soft":
        qa.append(
            (
                "Did dinner come out exactly as planned?",
                "Not quite. The noodles turned a little softer while everyone searched, but the family still finished dinner together and the evening stayed warm and happy."
            )
        )
    else:
        qa.append(
            (
                "Did they solve the problem in time?",
                f"Yes. They found the {tool_cfg.label} in time, so the spaghetti reached the table while it was still steaming nicely."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"spaghetti", "rhyme", "mystery", "surprise_slice"}
    tool_id = world.facts["tool_cfg"].id
    if tool_id in KNOWLEDGE:
        tags.add(tool_id)
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
        lines.append(f"  {ent.id:9} ({ent.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(T, H) :- tool(T), hideout(H), fits(T, H).

soft :- chosen_tool(T), chosen_hideout(H),
        urgency(T, U), distance(H, D), U + D >= 4.

outcome(soft) :- soft.
outcome(ontime) :- not soft.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for tool_id, tool in TOOLS.items():
        lines.append(asp.fact("tool", tool_id))
        lines.append(asp.fact("urgency", tool_id, tool.urgency))
        for hideout_id in sorted(tool.compatible_hideouts):
            lines.append(asp.fact("fits", tool_id, hideout_id))
    for hideout_id, hideout in HIDEOUTS.items():
        lines.append(asp.fact("hideout", hideout_id))
        lines.append(asp.fact("distance", hideout_id, hideout.distance))
    for surprise_id in SURPRISES:
        lines.append(asp.fact("surprise", surprise_id))
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
            asp.fact("chosen_tool", params.tool),
            asp.fact("chosen_hideout", params.hideout),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0
    py_gate = set(valid_combos())
    asp_gate = set(asp_valid_combos())
    if py_gate == asp_gate:
        print(f"OK: gate matches valid_combos() ({len(py_gate)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if asp_gate - py_gate:
            print("  only in clingo:", sorted(asp_gate - py_gate))
        if py_gate - asp_gate:
            print("  only in python:", sorted(py_gate - asp_gate))

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(40):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
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
            raise StoryError("generated story was empty")
        emit(sample, trace=False, qa=False, header="")
        print("OK: smoke test generated and emitted a normal story.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a spaghetti-night rhyme mystery with a surprise slice."
    )
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--hideout", choices=HIDEOUTS)
    ap.add_argument("--surprise", choices=SURPRISES)
    ap.add_argument("--child-name")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--helper-type", choices=HELPERS)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible tool/hideout combos derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner against the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.tool and args.hideout and not valid_combo(args.tool, args.hideout):
        raise StoryError(explain_rejection(args.tool, args.hideout))

    combos = [
        combo
        for combo in valid_combos()
        if (args.tool is None or combo[0] == args.tool)
        and (args.hideout is None or combo[1] == args.hideout)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    tool_id, hideout_id = rng.choice(sorted(combos))
    surprise_id = args.surprise or rng.choice(sorted(SURPRISES))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    child_name = args.child_name or rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES)
    helper_type = args.helper_type or rng.choice(HELPERS)
    child_trait = rng.choice(TRAITS)

    return StoryParams(
        tool=tool_id,
        hideout=hideout_id,
        surprise=surprise_id,
        child_name=child_name,
        child_gender=child_gender,
        helper_type=helper_type,
        child_trait=child_trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.tool not in TOOLS:
        raise StoryError(f"(Unknown tool: {params.tool})")
    if params.hideout not in HIDEOUTS:
        raise StoryError(f"(Unknown hideout: {params.hideout})")
    if params.surprise not in SURPRISES:
        raise StoryError(f"(Unknown surprise: {params.surprise})")
    if not valid_combo(params.tool, params.hideout):
        raise StoryError(explain_rejection(params.tool, params.hideout))

    world = tell(
        TOOLS[params.tool],
        HIDEOUTS[params.hideout],
        SURPRISES[params.surprise],
        child_name=params.child_name,
        child_gender=params.child_gender,
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
        print(asp_program("", "#show valid/2.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (tool, hideout) combos:\n")
        for tool_id, hideout_id in combos:
            params = StoryParams(
                tool=tool_id,
                hideout=hideout_id,
                surprise=next(iter(SURPRISES)),
                child_name="Lily",
                child_gender="girl",
                helper_type="mother",
                child_trait="curious",
            )
            print(f"  {tool_id:8} {hideout_id:15} -> {outcome_of(params)}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples: list[StorySample] = []
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
            header = f"### {p.child_name}: {p.tool} hidden in {p.hideout} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
