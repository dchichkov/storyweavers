#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/squeeze_dim_bungalow_problem_solving_mystery.py
==========================================================================

A standalone storyworld for a gentle mystery: in a bungalow, a child notices a
beloved kitten is missing, gathers a real clue, reasons about the hiding place,
and solves the problem with the right tool.

Run it
------
python storyworlds/worlds/gpt-5.4/squeeze_dim_bungalow_problem_solving_mystery.py
python storyworlds/worlds/gpt-5.4/squeeze_dim_bungalow_problem_solving_mystery.py --spot heater_grate --clue warm_mew --tool wooden_spoon
python storyworlds/worlds/gpt-5.4/squeeze_dim_bungalow_problem_solving_mystery.py --tool ribbon
python storyworlds/worlds/gpt-5.4/squeeze_dim_bungalow_problem_solving_mystery.py --all
python storyworlds/worlds/gpt-5.4/squeeze_dim_bungalow_problem_solving_mystery.py -n 5 --seed 7 --qa
python storyworlds/worlds/gpt-5.4/squeeze_dim_bungalow_problem_solving_mystery.py --verify
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
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
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
class Spot:
    id: str
    label: str
    place: str
    eerie: str
    need: str
    tags: set[str] = field(default_factory=set)
    reveal: str = ""
    ending_image: str = ""
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
class Clue:
    id: str
    label: str
    text: str
    points_to: set[str] = field(default_factory=set)
    certainty: int = 1
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
    use_text: str
    qa_text: str
    works_on: set[str] = field(default_factory=set)
    sense: int = 2
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
    kitten = world.get("kitten")
    child = world.get("child")
    helper = world.get("helper")
    if kitten.attrs.get("missing", False) and ("missing_worry",) not in world.fired:
        world.fired.add(("missing_worry",))
        child.memes["worry"] += 1
        helper.memes["concern"] += 1
    return []


def _r_clue_focus(world: World) -> list[str]:
    if not world.facts.get("clue_seen", False):
        return []
    child = world.get("child")
    helper = world.get("helper")
    sig = ("clue_focus", world.facts.get("clue_id", ""))
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["curiosity"] += 1
    helper.memes["focus"] += 1
    return []


def _r_trapped_fear(world: World) -> list[str]:
    kitten = world.get("kitten")
    sig = ("trapped_fear",)
    if kitten.meters["stuck"] >= THRESHOLD and sig not in world.fired:
        world.fired.add(sig)
        kitten.memes["fear"] += 1
        world.get("child").memes["urgency"] += 1
    return []


def _r_rescue_relief(world: World) -> list[str]:
    kitten = world.get("kitten")
    sig = ("rescue_relief",)
    if kitten.attrs.get("found", False) and sig not in world.fired:
        world.fired.add(sig)
        for eid in ("child", "helper"):
            world.get(eid).memes["relief"] += 1
            world.get(eid).memes["love"] += 1
        kitten.memes["fear"] = 0.0
        kitten.memes["trust"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="missing_worry", tag="emotional", apply=_r_missing_worry),
    Rule(name="clue_focus", tag="emotional", apply=_r_clue_focus),
    Rule(name="trapped_fear", tag="emotional", apply=_r_trapped_fear),
    Rule(name="rescue_relief", tag="emotional", apply=_r_rescue_relief),
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
            elif any(sig[0] == rule.name for sig in world.fired):
                pass
    if narrate:
        for s in produced:
            world.say(s)
    return produced


SPOTS = {
    "sofa_gap": Spot(
        id="sofa_gap",
        label="the gap behind the parlor sofa",
        place="the front room",
        eerie="A squeeze-dim stripe of afternoon light lay behind the sofa, and something tiny gave a shy jingle there.",
        need="lure",
        tags={"jingle", "fabric", "low"},
        reveal="A pair of bright eyes blinked out from the dust-fringe behind the sofa.",
        ending_image="Soon the sofa was only a sofa again, and Pip was purring in a warm lap.",
    ),
    "high_cupboard": Spot(
        id="high_cupboard",
        label="the top of the kitchen cupboard",
        place="the kitchen",
        eerie="Up near the ceiling, the bungalow kitchen held its breath, and one soft feather trembled above the cupboard.",
        need="stool",
        tags={"feather", "high", "kitchen"},
        reveal="Curled behind the bread tin sat Pip, looking very surprised to have become a mystery.",
        ending_image="After that, every cupboard top looked less spooky and more silly, especially with Pip washing one paw in plain sight.",
    ),
    "heater_grate": Spot(
        id="heater_grate",
        label="the heater grate in the hall",
        place="the hallway",
        eerie="From the hall came a warm little mew, squeezed thin through the metal slats of the heater grate.",
        need="tap",
        tags={"warm", "mew", "hall"},
        reveal="Just under the grate, whiskers twitched in the dusty dark.",
        ending_image="When the grate clicked shut again, the hallway lost its mystery and kept only Pip's happy bell-note.",
    ),
}

CLUES = {
    "bell_jingle": Clue(
        id="bell_jingle",
        label="a faint bell jingle",
        text="They stood very still and heard a faint bell jingle from low by the front room sofa.",
        points_to={"jingle", "fabric", "low"},
        certainty=2,
        tags={"bell", "sofa"},
    ),
    "feather_drift": Clue(
        id="feather_drift",
        label="a drifting feather",
        text="A gray feather drifted down in the kitchen, and the top of the cupboard looked oddly rumpled.",
        points_to={"feather", "high", "kitchen"},
        certainty=2,
        tags={"feather", "kitchen"},
    ),
    "warm_mew": Clue(
        id="warm_mew",
        label="a warm little mew",
        text="In the hallway they heard a warm little mew behind the heater grate, thin but clear.",
        points_to={"warm", "mew", "hall"},
        certainty=2,
        tags={"sound", "hall"},
    ),
    "dust_smudge": Clue(
        id="dust_smudge",
        label="a dusty smudge",
        text="Near the baseboard they found a dusty paw-smudge, but it only said Pip had gone low and hidden.",
        points_to={"low"},
        certainty=1,
        tags={"dust", "paw"},
    ),
}

TOOLS = {
    "ribbon": Tool(
        id="ribbon",
        label="ribbon wand",
        phrase="a ribbon tied to a wooden spoon",
        use_text="slid the ribbon out and let it dance and whisper where small eyes could see it",
        qa_text="used a ribbon lure so Pip would creep toward the open room",
        works_on={"lure"},
        sense=3,
        tags={"ribbon", "gentle"},
    ),
    "step_stool": Tool(
        id="step_stool",
        label="step stool",
        phrase="a steady step stool",
        use_text="set the stool in place, climbed carefully, and peered over the cupboard top",
        qa_text="used a step stool to look safely on top of the cupboard",
        works_on={"stool"},
        sense=3,
        tags={"stool", "careful"},
    ),
    "wooden_spoon": Tool(
        id="wooden_spoon",
        label="wooden spoon",
        phrase="a long wooden spoon",
        use_text="tapped the grate softly and nudged the toy mouse out where frightened paws could follow it",
        qa_text="tapped the grate and guided Pip out with a long wooden spoon",
        works_on={"tap"},
        sense=3,
        tags={"spoon", "gentle"},
    ),
    "broom": Tool(
        id="broom",
        label="broom",
        phrase="a long broom",
        use_text="poked too clumsily to help a scared kitten",
        qa_text="tried a broom",
        works_on=set(),
        sense=1,
        tags={"broom"},
    ),
}

CHILD_NAMES = ["Nora", "Milo", "Ava", "Ben", "Lila", "Theo", "Ivy", "Sam"]
HELPERS = [
    ("mother", "Mom"),
    ("father", "Dad"),
    ("grandmother", "Grandma"),
    ("grandfather", "Grandpa"),
]
TRAITS = ["careful", "patient", "curious", "thoughtful", "steady"]
KITTEN_NAMES = ["Pip", "Muffin", "Button", "Pebble"]


def clue_matches(clue: Clue, spot: Spot) -> bool:
    return bool(clue.points_to & spot.tags)


def tool_works(tool: Tool, spot: Spot) -> bool:
    return spot.need in tool.works_on


def sensible_tools() -> list[Tool]:
    return [tool for tool in TOOLS.values() if tool.sense >= SENSE_MIN]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for spot_id, spot in SPOTS.items():
        for clue_id, clue in CLUES.items():
            for tool_id, tool in TOOLS.items():
                if clue_matches(clue, spot) and tool_works(tool, spot) and tool.sense >= SENSE_MIN:
                    combos.append((spot_id, clue_id, tool_id))
    return sorted(combos)


def explain_rejection(spot: Spot, clue: Clue) -> str:
    return (
        f"(No story: {clue.label} does not honestly point to {spot.label}. "
        f"The mystery needs a real clue that fits the hiding place.)"
    )


def explain_tool(tool: Tool, spot: Spot) -> str:
    if tool.sense < SENSE_MIN:
        return (
            f"(Refusing tool '{tool.id}': it is too clumsy for a gentle rescue. "
            f"Choose a calmer, more sensible tool.)"
        )
    return (
        f"(No story: {tool.label} does not solve the problem at {spot.label}. "
        f"The tool must fit how the kitten can be reached.)"
    )


def outcome_of(params: "StoryParams") -> str:
    return "swift" if params.delay == 0 and CLUES[params.clue].certainty >= 2 else "patient"


def predict_found(world: World, spot_id: str, clue_id: str, tool_id: str) -> dict:
    sim = world.copy()
    sim.facts["clue_seen"] = True
    sim.facts["clue_id"] = clue_id
    if clue_matches(CLUES[clue_id], SPOTS[spot_id]) and tool_works(TOOLS[tool_id], SPOTS[spot_id]):
        kitten = sim.get("kitten")
        kitten.attrs["found"] = True
        kitten.attrs["missing"] = False
        kitten.meters["stuck"] = 0.0
    propagate(sim, narrate=False)
    return {
        "found": sim.get("kitten").attrs.get("found", False),
        "relief": sim.get("child").memes["relief"],
    }


def intro(world: World, child: Entity, helper: Entity, kitten: Entity) -> None:
    world.say(
        f"In a quiet bungalow at the end of the lane, {child.id} liked the hour when the rooms grew squeeze-dim and every lamp seemed to be thinking."
    )
    world.say(
        f"{helper.label_word.capitalize()} was folding a tea towel, and {kitten.id}, the small gray kitten with the bell collar, should have been pattering after the sound."
    )
    world.say(
        f"But the bungalow felt too still. {child.id} looked under the table, then behind the curtains, and felt {child.pronoun('possessive')} chest go tight."
    )


def missing(world: World, child: Entity, helper: Entity, kitten: Entity) -> None:
    kitten.attrs["missing"] = True
    kitten.meters["stuck"] = 1.0
    world.facts["problem"] = "missing_kitten"
    propagate(world, narrate=False)
    world.say(f'"{kitten.id}?" {child.id} called. No bell answered.')
    world.say(
        f'{helper.label_word.capitalize()} set down the towel. "A mystery then," {helper.pronoun()} said, "but mysteries get smaller when we look for real clues."'
    )


def observe_clue(world: World, child: Entity, helper: Entity, clue: Clue, spot: Spot) -> None:
    world.facts["clue_seen"] = True
    world.facts["clue_id"] = clue.id
    propagate(world, narrate=False)
    world.say(spot.eerie)
    world.say(clue.text)
    world.say(
        f"{child.id} frowned in a thinking way. {child.pronoun().capitalize()} was not guessing anymore; {child.pronoun()} was noticing."
    )


def wrong_turn(world: World, child: Entity, helper: Entity, clue: Clue, spot: Spot) -> None:
    world.say(
        f"For one minute the mystery seemed to point everywhere at once. {child.id} checked the coat basket first, but found only one mitten and a marble."
    )
    world.say(
        f'"Listen to the clue again," {helper.label_word} whispered. "{clue.label.capitalize()} is telling us about {spot.place}, not the basket."'
    )


def reason(world: World, child: Entity, helper: Entity, clue: Clue, spot: Spot, tool: Tool) -> None:
    pred = predict_found(world, spot.id, clue.id, tool.id)
    world.facts["predicted_found"] = pred["found"]
    world.say(
        f'{child.id} looked toward {spot.place}. "If the clue says {clue.label}, then Pip must be near {spot.label}," {child.pronoun()} said.'
    )
    world.say(
        f'{helper.label_word.capitalize()} smiled. "And what solves that kind of problem?"'
    )
    world.say(
        f'"{tool.label.capitalize()}," said {child.id}. "Not because it is long, but because it can help gently."'
    )


def rescue(world: World, child: Entity, helper: Entity, kitten: Entity, spot: Spot, tool: Tool) -> None:
    world.say(
        f"{helper.label_word.capitalize()} fetched {tool.phrase} and {tool.use_text}."
    )
    world.say(spot.reveal)
    kitten.attrs["found"] = True
    kitten.attrs["missing"] = False
    kitten.meters["stuck"] = 0.0
    kitten.meters["dusty"] += 1
    propagate(world, narrate=False)
    world.say(
        f"In one quick rustle, {kitten.id} came out, dusty, embarrassed, and very ready to be held."
    )


def ending(world: World, child: Entity, helper: Entity, kitten: Entity, spot: Spot, outcome: str) -> None:
    world.say(
        f'{child.id} hugged {kitten.id} and laughed a shaky little laugh. "It was not a ghost after all," {child.pronoun()} said.'
    )
    if outcome == "swift":
        world.say(
            f'"No," said {helper.label_word}, rubbing the kitten between the ears. "Just a puzzle with paws."'
        )
    else:
        world.say(
            f'"No," said {helper.label_word}, "just a puzzle that needed patient eyes before brave hands."'
        )
    world.say(spot.ending_image)
def tell(
    child_gender: str,
    helper_type: HelperType,
    helper_name: str,
    kitten_name: str,
    trait: Trait,
    spot: Spot,
    clue: Clue,
    tool: Tool,
    delay: Delay,
    child_name=None,
) -> World:
    world = World()
    child = world.add(Entity(
        id=child_name,
        kind="character",
        type=child_gender,
        label=child_name,
        role="child",
        traits=[trait],
    ))
    helper = world.add(Entity(
        id=helper_name,
        kind="character",
        type=helper_type,
        label=helper_name,
        role="helper",
    ))
    kitten = world.add(Entity(
        id="kitten",
        kind="thing",
        type="kitten",
        label=kitten_name,
        role="kitten",
        attrs={"name": kitten_name, "missing": False, "found": False},
    ))
    bungalow = world.add(Entity(
        id="bungalow",
        kind="thing",
        type="home",
        label="bungalow",
        role="setting",
    ))
    hiding = world.add(Entity(
        id="spot",
        kind="thing",
        type="spot",
        label=spot.label,
        role="spot",
        attrs={"need": spot.need, "place": spot.place},
    ))
    tool_ent = world.add(Entity(
        id="tool",
        kind="thing",
        type="tool",
        label=tool.label,
        role="tool",
    ))

    world.facts.update(
        child=child,
        helper=helper,
        kitten=kitten,
        bungalow=bungalow,
        spot_cfg=spot,
        clue_cfg=clue,
        tool_cfg=tool,
        clue_seen=False,
        clue_id=clue.id,
        delay=delay,
    )

    intro(world, child, helper, kitten)
    world.para()
    missing(world, child, helper, kitten)
    observe_clue(world, child, helper, clue, spot)

    world.para()
    if delay > 0:
        wrong_turn(world, child, helper, clue, spot)
    reason(world, child, helper, clue, spot, tool)

    world.para()
    rescue(world, child, helper, kitten, spot, tool)

    world.para()
    out = outcome_of(StoryParams(
        spot=spot.id,
        clue=clue.id,
        tool=tool.id,
        child_name=child_name,
        child_gender=child_gender,
        helper_type=helper_type,
        helper_name=helper_name,
        kitten_name=kitten_name,
        trait=trait,
        delay=delay,
        seed=None,
    ))
    ending(world, child, helper, kitten, spot, out)

    world.facts.update(
        outcome=out,
        solved=True,
        found=kitten.attrs["found"],
        dusty=kitten.meters["dusty"] >= THRESHOLD,
        predicted_found=world.facts.get("predicted_found", False),
    )
    return world
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
    "bungalow": [
        (
            "What is a bungalow?",
            "A bungalow is a house with its main rooms on one level. That means you can walk from room to room without climbing stairs."
        )
    ],
    "bell": [
        (
            "Why can a bell help you find a kitten?",
            "A bell makes a small ringing sound when the kitten moves. That sound can help people notice where the kitten has gone."
        )
    ],
    "feather": [
        (
            "Why would a feather be a clue?",
            "A feather can show where a kitten has been playing. It is useful because it points to a place the kitten touched."
        )
    ],
    "ribbon": [
        (
            "Why might a ribbon help with a scared kitten?",
            "A ribbon moves softly and can tempt a kitten to come closer. It helps without pulling or hurting."
        )
    ],
    "stool": [
        (
            "Why should a grown-up use a step stool carefully?",
            "A step stool helps someone look up high without stretching too far. Using it carefully makes the search safer."
        )
    ],
    "heater": [
        (
            "Why do sounds change behind a heater grate?",
            "Metal slats can make a sound seem thin or muffled. That can make a tiny mew sound mysterious."
        )
    ],
    "clue": [
        (
            "What is a clue?",
            "A clue is a small sign that helps you figure something out. Good clues help you think instead of just guess."
        )
    ],
}
KNOWLEDGE_ORDER = ["bungalow", "clue", "bell", "feather", "heater", "ribbon", "stool"]


def generation_prompts(world: World) -> list[str]:
    child = world.facts["child"]
    helper = world.facts["helper"]
    kitten = world.facts["kitten"]
    clue = world.facts["clue_cfg"]
    tool = world.facts["tool_cfg"]
    spot = world.facts["spot_cfg"]
    return [
        'Write a gentle mystery for a 3-to-5-year-old set in a bungalow. Include the exact word "squeeze-dim" and make the problem solved by noticing a clue.',
        f"Tell a child-friendly mystery where {child.id} and {helper.label_word} search for a missing kitten named {kitten.label}, follow {clue.label}, and solve the puzzle with a {tool.label}.",
        f"Write a short problem-solving story in which a strange sound in {spot.place} seems spooky at first, but turns out to be an ordinary kitten mystery solved with careful thinking.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    child = world.facts["child"]
    helper = world.facts["helper"]
    kitten = world.facts["kitten"]
    spot = world.facts["spot_cfg"]
    clue = world.facts["clue_cfg"]
    tool = world.facts["tool_cfg"]
    outcome = world.facts["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, {child.pronoun('possessive')} {helper.label_word}, and a missing kitten named {kitten.label}. The mystery begins when the bungalow grows quiet and Pip does not come when called."
        ),
        (
            "What was the mystery in the bungalow?",
            f"The mystery was that {kitten.label} had vanished and only a strange clue remained. The house felt spooky because the missing bell and the odd sound made ordinary rooms seem secret."
        ),
        (
            "What clue helped them solve it?",
            f"The clue was {clue.label}. It mattered because it pointed toward {spot.place} instead of somewhere random."
        ),
        (
            f"How did {child.id} help solve the problem?",
            f"{child.id} listened carefully and matched the clue to the right place. Then {child.pronoun()} chose the {tool.label} because it could help gently instead of making the kitten more scared."
        ),
        (
            "How did they find the kitten?",
            f"{helper.label_word.capitalize()} {tool.qa_text}. That worked because {spot.label} needed exactly that kind of careful reach."
        ),
    ]
    if outcome == "swift":
        qa.append(
            (
                "Did they solve the mystery quickly?",
                f"Yes. Once they trusted the clue, the answer came fast. The real change was from spooky guessing to calm noticing."
            )
        )
    else:
        qa.append(
            (
                "Did they solve the mystery right away?",
                f"Not quite. They checked one wrong place first, then listened to the clue again and corrected themselves. That extra pause showed how patient thinking can fix a mistake."
            )
        )
    qa.append(
        (
            "How did the story end?",
            f"It ended with {kitten.label} safe in loving arms and the bungalow feeling ordinary again. The last image proves the mystery was solved because the scary place lost its strangeness."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"bungalow", "clue"}
    clue = world.facts["clue_cfg"]
    tool = world.facts["tool_cfg"]
    spot = world.facts["spot_cfg"]
    if "bell" in clue.tags or "sofa" in clue.tags:
        tags.add("bell")
    if "feather" in clue.tags:
        tags.add("feather")
    if spot.id == "heater_grate":
        tags.add("heater")
    if tool.id == "ribbon":
        tags.add("ribbon")
    if tool.id == "step_stool":
        tags.add("stool")
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
        if ent.role:
            bits.append(f"role={ent.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v or v == 0}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:10} ({ent.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(sig[0] for sig in world.fired))}")
    return "\n".join(lines)
@dataclass
class StoryParams:
    spot: str
    clue: str
    tool: str
    child_name: str
    child_gender: str
    helper_type: str
    helper_name: str
    kitten_name: str
    trait: str
    delay: int = 0
    seed: Optional[int] = None




CURATED = [
    StoryParams(
        spot="sofa_gap",
        clue="bell_jingle",
        tool="ribbon",
        child_name="Nora",
        child_gender="girl",
        helper_type="grandfather",
        helper_name="Grandpa",
        kitten_name="Pip",
        trait="careful",
        delay=0,
        seed=None,
    ),
    StoryParams(
        spot="high_cupboard",
        clue="feather_drift",
        tool="step_stool",
        child_name="Milo",
        child_gender="boy",
        helper_type="mother",
        helper_name="Mom",
        kitten_name="Button",
        trait="thoughtful",
        delay=1,
        seed=None,
    ),
    StoryParams(
        spot="heater_grate",
        clue="warm_mew",
        tool="wooden_spoon",
        child_name="Ivy",
        child_gender="girl",
        helper_type="father",
        helper_name="Dad",
        kitten_name="Pebble",
        trait="patient",
        delay=0,
        seed=None,
    ),
]


ASP_RULES = r"""
spot_matches(S,C) :- spot(S), clue(C), spot_tag(S,T), clue_tag(C,T).
sensible_tool(T) :- tool(T), sense(T,S), sense_min(M), S >= M.
valid(S,C,T) :- spot(S), clue(C), tool(T), spot_matches(S,C), needs(S,N), works_on(T,N), sensible_tool(T).

outcome(swift) :- chosen_clue(C), certainty(C,2), delay(0).
outcome(patient) :- not outcome(swift).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for spot_id, spot in SPOTS.items():
        lines.append(asp.fact("spot", spot_id))
        lines.append(asp.fact("needs", spot_id, spot.need))
        for tag in sorted(spot.tags):
            lines.append(asp.fact("spot_tag", spot_id, tag))
    for clue_id, clue in CLUES.items():
        lines.append(asp.fact("clue", clue_id))
        lines.append(asp.fact("certainty", clue_id, clue.certainty))
        for tag in sorted(clue.points_to):
            lines.append(asp.fact("clue_tag", clue_id, tag))
    for tool_id, tool in TOOLS.items():
        lines.append(asp.fact("tool", tool_id))
        lines.append(asp.fact("sense", tool_id, tool.sense))
        for need in sorted(tool.works_on):
            lines.append(asp.fact("works_on", tool_id, need))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join([
        asp.fact("chosen_clue", params.clue),
        asp.fact("delay", params.delay),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    ap = set(asp_valid_combos())
    if py == ap:
        print(f"OK: gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if py - ap:
            print("  only in python:", sorted(py - ap))
        if ap - py:
            print("  only in clingo:", sorted(ap - py))

    cases = list(CURATED)
    for seed in range(50):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(params)
    bad = sum(1 for params in cases if asp_outcome(params) != outcome_of(params))
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(cases[0])
        if not sample.story.strip():
            raise StoryError("empty story from smoke test")
        print("OK: smoke test generated a normal story.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Gentle bungalow mystery: a missing kitten, a true clue, and a problem solved by careful thinking."
    )
    ap.add_argument("--spot", choices=sorted(SPOTS))
    ap.add_argument("--clue", choices=sorted(CLUES))
    ap.add_argument("--tool", choices=sorted(TOOLS))
    ap.add_argument("--child-name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=[h[0] for h in HELPERS])
    ap.add_argument("--delay", type=int, choices=[0, 1], help="0 = quick solve, 1 = one wrong check before the right answer")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible story combos derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.spot and args.clue:
        if not clue_matches(CLUES[args.clue], SPOTS[args.spot]):
            raise StoryError(explain_rejection(SPOTS[args.spot], CLUES[args.clue]))
    if args.spot and args.tool:
        if not tool_works(TOOLS[args.tool], SPOTS[args.spot]):
            raise StoryError(explain_tool(TOOLS[args.tool], SPOTS[args.spot]))
    if args.tool and TOOLS[args.tool].sense < SENSE_MIN:
        spot = SPOTS[args.spot] if args.spot else next(iter(SPOTS.values()))
        raise StoryError(explain_tool(TOOLS[args.tool], spot))

    combos = [
        combo for combo in valid_combos()
        if (args.spot is None or combo[0] == args.spot)
        and (args.clue is None or combo[1] == args.clue)
        and (args.tool is None or combo[2] == args.tool)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    spot_id, clue_id, tool_id = rng.choice(sorted(combos))
    child_gender = args.gender or rng.choice(["girl", "boy"])
    child_name = args.child_name or rng.choice([n for n in CHILD_NAMES if (child_gender == "girl" and n not in {"Milo", "Ben", "Theo", "Sam"}) or (child_gender == "boy" and n not in {"Nora", "Ava", "Lila", "Ivy"})])
    helper_type = args.helper or rng.choice([h[0] for h in HELPERS])
    helper_name = dict(HELPERS)[helper_type]
    kitten_name = rng.choice(KITTEN_NAMES)
    trait = rng.choice(TRAITS)
    delay = args.delay if args.delay is not None else rng.choice([0, 0, 1])
    return StoryParams(
        spot=spot_id,
        clue=clue_id,
        tool=tool_id,
        child_name=child_name,
        child_gender=child_gender,
        helper_type=helper_type,
        helper_name=helper_name,
        kitten_name=kitten_name,
        trait=trait,
        delay=delay,
        seed=None,
    )


def generate(params: StoryParams) -> StorySample:
    if params.spot not in SPOTS:
        raise StoryError(f"(Unknown spot: {params.spot})")
    if params.clue not in CLUES:
        raise StoryError(f"(Unknown clue: {params.clue})")
    if params.tool not in TOOLS:
        raise StoryError(f"(Unknown tool: {params.tool})")

    spot = SPOTS[params.spot]
    clue = CLUES[params.clue]
    tool = TOOLS[params.tool]

    if not clue_matches(clue, spot):
        raise StoryError(explain_rejection(spot, clue))
    if not tool_works(tool, spot) or tool.sense < SENSE_MIN:
        raise StoryError(explain_tool(tool, spot))

    world = tell(
        child_name=params.child_name,
        child_gender=params.child_gender,
        helper_type=params.helper_type,
        helper_name=params.helper_name,
        kitten_name=params.kitten_name,
        trait=params.trait,
        spot=spot,
        clue=clue,
        tool=tool,
        delay=params.delay,
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
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (spot, clue, tool) combos:\n")
        for spot, clue, tool in combos:
            print(f"  {spot:14} {clue:14} {tool}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.child_name}: {p.clue} -> {p.spot} with {p.tool} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
