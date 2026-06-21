#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/upright_flashback_mystery.py
======================================================

A standalone storyworld for a small child-facing mystery with a flashback:
something wobbly is found standing upright when everyone expected it to fall.
Two children follow a physical clue, remember an earlier moment, and solve the
mystery in a calm, sensible way.

This world models:
- typed entities with physical meters and emotional memes
- a simple forward-chaining causal engine
- a Python reasonableness gate plus an inline ASP twin
- state-driven prose, three QA sets, JSON output, trace output, and verification

Run it
------
    python storyworlds/worlds/gpt-5.4/upright_flashback_mystery.py
    python storyworlds/worlds/gpt-5.4/upright_flashback_mystery.py --place classroom --object robot --support clay_ring
    python storyworlds/worlds/gpt-5.4/upright_flashback_mystery.py --object kite   # rejected: no indoor stand-up mystery here
    python storyworlds/worlds/gpt-5.4/upright_flashback_mystery.py --all
    python storyworlds/worlds/gpt-5.4/upright_flashback_mystery.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/upright_flashback_mystery.py --verify
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


# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------
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
        female = {"girl", "mother", "teacher", "grandma", "woman"}
        male = {"boy", "father", "grandpa", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {
            "teacher": "teacher",
            "mother": "mom",
            "father": "dad",
            "grandma": "grandma",
            "grandpa": "grandpa",
        }.get(self.type, self.type)


# ---------------------------------------------------------------------------
# Domain registries
# ---------------------------------------------------------------------------
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
    scene: str
    floor: str
    affordances: set[str] = field(default_factory=set)
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
class WobblyObject:
    id: str
    label: str
    phrase: str
    material: str
    need: int
    bump_text: str
    image: str
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
class Support:
    id: str
    label: str
    phrase: str
    strength: int
    method: str
    clue_mark: str
    clue_line: str
    flashback_line: str
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
class Clue:
    id: str
    label: str
    notice: str
    question: str
    recall: str
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
    type: str
    label: str
    style: str
    advice: str
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


PLACES = {
    "classroom": Place(
        id="classroom",
        label="the classroom",
        scene="sunlight lay across the art shelf and the reading rug",
        floor="the smooth classroom floor",
        affordances={"robot", "boat"},
        tags={"classroom"},
    ),
    "windowseat": Place(
        id="windowseat",
        label="the window seat",
        scene="the long bench under the window was full of small treasures",
        floor="the painted wooden boards",
        affordances={"boat", "pinwheel"},
        tags={"home"},
    ),
    "garden_shed": Place(
        id="garden_shed",
        label="the garden shed",
        scene="light came through the slats and striped the pots and tools",
        floor="the dusty shed floor",
        affordances={"pinwheel", "robot"},
        tags={"garden"},
    ),
}

OBJECTS = {
    "robot": WobblyObject(
        id="robot",
        label="paper robot",
        phrase="a silver paper robot with square shoulders",
        material="paper",
        need=2,
        bump_text="When the door thumped shut, the paper robot had given a tiny shake.",
        image="its bright foil chest still catching the light",
        tags={"paper", "robot"},
    ),
    "boat": WobblyObject(
        id="boat",
        label="cardboard boat",
        phrase="a cardboard boat with a blue crayon sail",
        material="cardboard",
        need=1,
        bump_text="When someone hurried past, the cardboard boat had trembled on the shelf.",
        image="its blue sail still pointing straight ahead",
        tags={"cardboard", "boat"},
    ),
    "pinwheel": WobblyObject(
        id="pinwheel",
        label="rainbow pinwheel",
        phrase="a rainbow pinwheel on a thin stick",
        material="paper",
        need=2,
        bump_text="When the wind slipped in, the pinwheel had shivered on its stick.",
        image="its rainbow blades held neat and still",
        tags={"pinwheel", "paper"},
    ),
    "kite": WobblyObject(
        id="kite",
        label="big kite",
        phrase="a big kite with a long tail",
        material="paper",
        need=3,
        bump_text="The kite had flapped and tugged too hard to stand on its own.",
        image="its tail puddled on the floor",
        tags={"kite", "paper"},
    ),
}

SUPPORTS = {
    "clay_ring": Support(
        id="clay_ring",
        label="clay ring",
        phrase="a soft ring of modeling clay",
        strength=2,
        method="pressed a soft ring of modeling clay around the base",
        clue_mark="a gray smudge at the bottom",
        clue_line="At the base there was a gray smudge, round as a thumbprint moon.",
        flashback_line="In the flashback, the helper's thumb pressed the clay into a neat little ring.",
        tags={"clay", "support"},
    ),
    "bookend": Support(
        id="bookend",
        label="bookend",
        phrase="a heavy wooden bookend",
        strength=1,
        method="set a heavy wooden bookend behind it",
        clue_mark="a clean square line in the dust",
        clue_line="Behind it, a clean square line showed where something heavy had rested.",
        flashback_line="In the flashback, the helper slid a bookend behind it so it would not tip backward.",
        tags={"bookend", "support"},
    ),
    "string_loop": Support(
        id="string_loop",
        label="string loop",
        phrase="a little loop of garden string",
        strength=2,
        method="tied a little loop of string to steady it",
        clue_mark="a pale string loop tucked near the stem",
        clue_line="Near the base lay a pale loop of string, almost hiding in the dust.",
        flashback_line="In the flashback, the helper looped the string gently so the object could stay straight.",
        tags={"string", "support"},
    ),
}

CLUES = {
    "smudge": Clue(
        id="smudge",
        label="smudge",
        notice="a strange gray smudge",
        question="Why was there a gray smudge if no one had painted there?",
        recall="The gray mark tugged at a memory from earlier.",
        tags={"clue", "smudge"},
    ),
    "line": Clue(
        id="line",
        label="line",
        notice="a neat square line",
        question="Why was the dust missing in one tidy square?",
        recall="The tidy line made an old picture in the child's mind come back.",
        tags={"clue", "line"},
    ),
    "loop": Clue(
        id="loop",
        label="loop",
        notice="a little loop of string",
        question="Who would leave a loop of string beside a display?",
        recall="The loop pulled a half-forgotten moment out of hiding.",
        tags={"clue", "loop"},
    ),
}

HELPERS = {
    "teacher": Helper(
        id="teacher",
        type="teacher",
        label="the teacher",
        style="calm",
        advice="A display stands best when its base is steady.",
        tags={"teacher"},
    ),
    "grandpa": Helper(
        id="grandpa",
        type="grandpa",
        label="grandpa",
        style="patient",
        advice="If something is precious and wobbly, make the bottom safe first.",
        tags={"grandpa"},
    ),
    "mom": Helper(
        id="mom",
        type="mother",
        label="the mom",
        style="gentle",
        advice="Tiny fixes can keep careful work from tumbling over.",
        tags={"mom"},
    ),
}

CLUE_FOR_SUPPORT = {
    "clay_ring": "smudge",
    "bookend": "line",
    "string_loop": "loop",
}

GIRL_NAMES = ["Lina", "Maya", "Zoe", "Nora", "Ivy", "Ella", "June", "Ruby"]
BOY_NAMES = ["Ben", "Leo", "Max", "Sam", "Theo", "Finn", "Eli", "Noah"]
TRAITS = ["careful", "curious", "quiet", "observant", "thoughtful", "brisk"]


# ---------------------------------------------------------------------------
# World and rules
# ---------------------------------------------------------------------------
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


def _r_bump_topple(world: World) -> list[str]:
    obj = world.get("object")
    if obj.meters["bumped"] < THRESHOLD:
        return []
    sig = ("bump_topple",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    if obj.meters["support_power"] < obj.meters["need"]:
        obj.meters["upright"] = 0.0
        obj.meters["fallen"] += 1
        obj.meters["wobble"] += 1
        return ["__fallen__"]
    obj.meters["upright"] += 1
    obj.meters["steady"] += 1
    return ["__upright__"]


def _r_fall_worry(world: World) -> list[str]:
    obj = world.get("object")
    if obj.meters["fallen"] < THRESHOLD:
        return []
    sig = ("fall_worry",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    for role in ("sleuth", "partner"):
        world.get(role).memes["worry"] += 1
    return ["__worry__"]


def _r_upright_curiosity(world: World) -> list[str]:
    obj = world.get("object")
    if obj.meters["upright"] < THRESHOLD or obj.meters["bumped"] < THRESHOLD:
        return []
    sig = ("upright_curiosity",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    for role in ("sleuth", "partner"):
        world.get(role).memes["curiosity"] += 1
    return ["__mystery__"]


def _r_clue_recalls(world: World) -> list[str]:
    if world.get("clue").meters["noticed"] < THRESHOLD:
        return []
    sig = ("clue_recalls",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    world.get("sleuth").memes["memory"] += 1
    return ["__flashback__"]


RULES = [
    Rule(name="bump_topple", tag="physical", apply=_r_bump_topple),
    Rule(name="fall_worry", tag="emotional", apply=_r_fall_worry),
    Rule(name="upright_curiosity", tag="emotional", apply=_r_upright_curiosity),
    Rule(name="clue_recalls", tag="memory", apply=_r_clue_recalls),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in RULES:
            out = rule.apply(world)
            if out:
                changed = True
                produced.extend(x for x in out if not x.startswith("__"))
    if narrate:
        for sent in produced:
            world.say(sent)
    return produced


# ---------------------------------------------------------------------------
# Constraints and prediction
# ---------------------------------------------------------------------------
def support_fits(obj: WobblyObject, support: Support) -> bool:
    return support.strength >= obj.need


def clue_matches_support(clue_id: str, support_id: str) -> bool:
    return CLUE_FOR_SUPPORT.get(support_id) == clue_id


def helper_allowed(place: Place, helper: Helper) -> bool:
    if place.id == "classroom":
        return helper.id == "teacher"
    return helper.id in {"grandpa", "mom"}


def valid_combo(place_id: str, object_id: str, support_id: str, helper_id: str) -> bool:
    if place_id not in PLACES or object_id not in OBJECTS or support_id not in SUPPORTS or helper_id not in HELPERS:
        return False
    place = PLACES[place_id]
    obj = OBJECTS[object_id]
    support = SUPPORTS[support_id]
    helper = HELPERS[helper_id]
    return (
        object_id in place.affordances
        and support_fits(obj, support)
        and helper_allowed(place, helper)
    )


def valid_combos() -> list[tuple[str, str, str, str]]:
    out = []
    for place_id, place in PLACES.items():
        for object_id in sorted(place.affordances):
            obj = OBJECTS[object_id]
            for support_id, support in SUPPORTS.items():
                for helper_id, helper in HELPERS.items():
                    if support_fits(obj, support) and helper_allowed(place, helper):
                        out.append((place_id, obj.id, support.id, helper.id))
    return sorted(out)


def explain_rejection(place: Place, obj: WobblyObject, support: Support, helper: Helper) -> str:
    if obj.id not in place.affordances:
        return (
            f"(No story: {obj.label} does not belong naturally in {place.label}, "
            f"so the mystery would feel forced there.)"
        )
    if not support_fits(obj, support):
        return (
            f"(No story: {support.label} is too weak to keep the {obj.label} upright "
            f"after a bump. The mystery only works if the support could really hold it.)"
        )
    if not helper_allowed(place, helper):
        return (
            f"(No story: {helper.label} is not the natural grown-up helper for {place.label}. "
            f"Pick a helper who would reasonably have been there earlier.)"
        )
    return "(No story: this combination is not reasonable.)"


def predict_after_bump(obj: WobblyObject, support: Support) -> dict:
    world = World()
    world.add(Entity(id="object", type="display", label=obj.label))
    world.add(Entity(id="sleuth", kind="character", type="girl", label="the child"))
    world.add(Entity(id="partner", kind="character", type="boy", label="the other child"))
    world.add(Entity(id="clue", type="clue", label="the clue"))
    world.get("object").meters["need"] = float(obj.need)
    world.get("object").meters["support_power"] = float(support.strength)
    world.get("object").meters["bumped"] += 1
    propagate(world, narrate=False)
    return {
        "upright": world.get("object").meters["upright"] >= THRESHOLD,
        "fallen": world.get("object").meters["fallen"] >= THRESHOLD,
    }


# ---------------------------------------------------------------------------
# Story actions
# ---------------------------------------------------------------------------
def introduce(world: World, place: Place, sleuth: Entity, partner: Entity, obj: WobblyObject) -> None:
    sleuth.memes["warmth"] += 1
    partner.memes["warmth"] += 1
    world.say(
        f"After tidy-up time in {place.label}, {sleuth.id} and {partner.id} came back for one last look. "
        f"{place.scene}. On the shelf stood {obj.phrase}."
    )
    world.say(
        f"They both knew it was the wobblest thing there, and yet it was standing perfectly upright, "
        f"{obj.image}."
    )


def bump_memory(world: World, obj: WobblyObject) -> None:
    world.say(obj.bump_text)
    world.say(
        "Both children stopped close to the shelf. If it had shaken that much, why had it not fallen?"
    )


def seed_bump(world: World, obj: WobblyObject, support: Support) -> None:
    display = world.get("object")
    display.meters["need"] = float(obj.need)
    display.meters["support_power"] = float(support.strength)
    display.meters["bumped"] += 1
    propagate(world, narrate=False)


def wonder(world: World, sleuth: Entity, partner: Entity, obj: WobblyObject) -> None:
    sleuth.memes["curiosity"] += 1
    partner.memes["curiosity"] += 1
    world.say(f'"That is the mystery," {sleuth.id} whispered. "{obj.label.capitalize()} should have tipped over."')
    world.say(
        f'{partner.id} crouched to look more closely. "Then something must have helped it stay upright."'
    )


def inspect_clue(world: World, sleuth: Entity, partner: Entity, support: Support, clue: Clue) -> None:
    clue_ent = world.get("clue")
    clue_ent.meters["noticed"] += 1
    propagate(world, narrate=False)
    world.say(support.clue_line)
    world.say(
        f'"Look," said {partner.id}. "{clue.notice.capitalize()}."'
    )
    world.say(f"{clue.question}")


def flashback(world: World, sleuth: Entity, helper: Entity, support: Support, clue: Clue, obj: WobblyObject) -> None:
    sleuth.memes["understanding"] += 1
    world.say(clue.recall)
    world.say(
        f"Then a flashback opened in {sleuth.id}'s mind: earlier that afternoon, {helper.label_word} had paused by the shelf, "
        f"seen the {obj.label} lean, and {support.method}."
    )
    world.say(
        f'{support.flashback_line} "{helper.attrs["advice"]}" {helper.pronoun()} had said.'
    )


def solve(world: World, sleuth: Entity, partner: Entity, helper: Entity, support: Support, obj: WobblyObject) -> None:
    world.get("object").meters["solved"] += 1
    sleuth.memes["relief"] += 1
    partner.memes["relief"] += 1
    world.say(
        f'"It was not magic," said {sleuth.id}. "It was {helper.label_word}\'s careful fix."'
    )
    world.say(
        f'{partner.id} smiled. "The {support.label} held the {obj.label} steady when the bump came."'
    )


def ask_and_confirm(world: World, helper: Entity, support: Support, obj: WobblyObject) -> None:
    helper.memes["care"] += 1
    world.say(
        f"When they asked, {helper.label_word} nodded and laughed softly. "
        f'"I saw it wobbling, so I {support.method}," {helper.pronoun()} said. '
        f'"Mysteries like this usually leave a clue."'
    )


def changed_ending(world: World, place: Place, sleuth: Entity, partner: Entity, helper: Entity, obj: WobblyObject) -> None:
    sleuth.memes["confidence"] += 1
    partner.memes["confidence"] += 1
    world.say(
        f"After that, {sleuth.id} and {partner.id} checked the bottoms of their own little displays before they stepped away."
    )
    world.say(
        f"Soon the shelf in {place.label} looked neat and brave, with every wobbly treasure standing upright on purpose."
    )


# ---------------------------------------------------------------------------
# Screenplay
# ---------------------------------------------------------------------------
def tell(
    place: Place,
    obj: WobblyObject,
    support: Support,
    clue: Clue,
    helper_cfg: Helper,
    *,
    sleuth_name: str = "Maya",
    sleuth_gender: str = "girl",
    partner_name: str = "Ben",
    partner_gender: str = "boy",
    sleuth_trait: str = "observant",
    partner_trait: str = "curious",
) -> World:
    world = World()
    sleuth = world.add(
        Entity(
            id=sleuth_name,
            kind="character",
            type=sleuth_gender,
            role="sleuth",
            traits=[sleuth_trait],
        )
    )
    partner = world.add(
        Entity(
            id=partner_name,
            kind="character",
            type=partner_gender,
            role="partner",
            traits=[partner_trait],
        )
    )
    helper = world.add(
        Entity(
            id="helper",
            kind="character",
            type=helper_cfg.type,
            role="helper",
            label=helper_cfg.label,
            attrs={"advice": helper_cfg.advice},
        )
    )
    world.add(Entity(id="object", type="display", label=obj.label))
    world.add(Entity(id="clue", type="clue", label=clue.label))

    world.facts.update(
        place=place,
        object_cfg=obj,
        support=support,
        clue_cfg=clue,
        helper_cfg=helper_cfg,
        sleuth=sleuth,
        partner=partner,
        helper=helper,
    )

    introduce(world, place, sleuth, partner, obj)
    bump_memory(world, obj)

    world.para()
    seed_bump(world, obj, support)
    wonder(world, sleuth, partner, obj)
    inspect_clue(world, sleuth, partner, support, clue)

    world.para()
    flashback(world, sleuth, helper, support, clue, obj)
    solve(world, sleuth, partner, helper, support, obj)
    ask_and_confirm(world, helper, support, obj)

    world.para()
    changed_ending(world, place, sleuth, partner, helper, obj)

    world.facts.update(
        outcome="solved" if world.get("object").meters["solved"] >= THRESHOLD else "unsolved",
        stayed_upright=world.get("object").meters["upright"] >= THRESHOLD,
        clue_noticed=world.get("clue").meters["noticed"] >= THRESHOLD,
    )
    return world


# ---------------------------------------------------------------------------
# Story params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    object: str
    support: str
    clue: str
    helper: str
    sleuth_name: str
    sleuth_gender: str
    partner_name: str
    partner_gender: str
    sleuth_trait: str
    partner_trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
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
    "clay": [
        (
            "What can modeling clay do for a wobbly thing?",
            "Modeling clay can press around the bottom and help hold a light object steady. That makes it less likely to tip over."
        )
    ],
    "bookend": [
        (
            "What is a bookend for?",
            "A bookend is a heavy support that keeps books or other things from falling over. It helps hold them straight."
        )
    ],
    "string": [
        (
            "What can a loop of string do?",
            "A loop of string can gently steady something thin or tall. It helps stop a wobble from turning into a fall."
        )
    ],
    "clue": [
        (
            "What is a clue?",
            "A clue is a small sign that helps you figure something out. In a mystery, clues lead your thinking toward the answer."
        )
    ],
    "flashback": [
        (
            "What is a flashback in a story?",
            "A flashback is when the story remembers something that happened earlier. It helps explain what is happening now."
        )
    ],
    "upright": [
        (
            "What does upright mean?",
            "Upright means standing straight up instead of lying down or falling over. A cup on a table can be upright."
        )
    ],
    "steady": [
        (
            "Why do wobbly things need a steady base?",
            "A steady base keeps the bottom from sliding or tipping. That helps the whole thing stay up."
        )
    ],
}
KNOWLEDGE_ORDER = ["upright", "clue", "flashback", "steady", "clay", "bookend", "string"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    place = f["place"]
    obj = f["object_cfg"]
    return [
        f'Write a gentle mystery for a 3-to-5-year-old about a {obj.label} that is still upright after a bump. Include a flashback that explains the clue.',
        f"Tell a small mystery set in {place.label} where two children investigate why a wobbly {obj.label} did not fall over.",
        'Write a child-facing story using the word "upright" with a calm mystery, one physical clue, and an ending that shows the children learned to steady things on purpose.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    sleuth = f["sleuth"]
    partner = f["partner"]
    helper = f["helper"]
    obj = f["object_cfg"]
    support = f["support"]
    clue = f["clue_cfg"]
    place = f["place"]

    return [
        (
            "What was the mystery in the story?",
            f"The mystery was why the {obj.label} was still upright after a bump that should have knocked it down. That made {sleuth.id} and {partner.id} stop and look for a real reason."
        ),
        (
            f"What clue did {partner.id} notice?",
            f"{partner.id} noticed {clue.notice} near the {obj.label}. The clue mattered because it showed that someone had touched or steadied the display earlier."
        ),
        (
            f"How did the flashback help {sleuth.id} solve the mystery?",
            f"The clue pulled an earlier moment back into {sleuth.id}'s mind. In the flashback, {helper.label_word} had {support.method}, which explained how the {obj.label} stayed upright."
        ),
        (
            f"Why did the {obj.label} not fall over?",
            f"It did not fall because the {support.label} made the base steadier when the bump came. The careful fix changed what would have happened."
        ),
        (
            "How did the story end?",
            f"It ended with the children checking the bottoms of their own displays so they could stand upright on purpose. The ending image shows they learned from the mystery instead of just wondering about it."
        ),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"upright", "clue", "flashback", "steady"}
    support = world.facts["support"]
    if "clay" in support.tags:
        tags.add("clay")
    if "bookend" in support.tags:
        tags.add("bookend")
    if "string" in support.tags:
        tags.add("string")
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


# ---------------------------------------------------------------------------
# Trace / CLI helpers
# ---------------------------------------------------------------------------
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
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="classroom",
        object="robot",
        support="clay_ring",
        clue="smudge",
        helper="teacher",
        sleuth_name="Maya",
        sleuth_gender="girl",
        partner_name="Ben",
        partner_gender="boy",
        sleuth_trait="observant",
        partner_trait="curious",
    ),
    StoryParams(
        place="windowseat",
        object="boat",
        support="bookend",
        clue="line",
        helper="mom",
        sleuth_name="Ruby",
        sleuth_gender="girl",
        partner_name="Leo",
        partner_gender="boy",
        sleuth_trait="quiet",
        partner_trait="thoughtful",
    ),
    StoryParams(
        place="garden_shed",
        object="pinwheel",
        support="string_loop",
        clue="loop",
        helper="grandpa",
        sleuth_name="Ivy",
        sleuth_gender="girl",
        partner_name="Finn",
        partner_gender="boy",
        sleuth_trait="careful",
        partner_trait="brisk",
    ),
    StoryParams(
        place="classroom",
        object="boat",
        support="bookend",
        clue="line",
        helper="teacher",
        sleuth_name="June",
        sleuth_gender="girl",
        partner_name="Max",
        partner_gender="boy",
        sleuth_trait="thoughtful",
        partner_trait="curious",
    ),
    StoryParams(
        place="windowseat",
        object="pinwheel",
        support="clay_ring",
        clue="smudge",
        helper="mom",
        sleuth_name="Ella",
        sleuth_gender="girl",
        partner_name="Theo",
        partner_gender="boy",
        sleuth_trait="observant",
        partner_trait="quiet",
    ),
]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% registry-level gate
fit_support(O,S) :- object(O), support(S), need(O,N), strength(S,P), P >= N.
allowed_helper(P,H) :- place(P), helper(H), in_classroom(P), helper_kind(H,teacher).
allowed_helper(P,H) :- place(P), helper(H), not in_classroom(P), helper_kind(H,grandpa).
allowed_helper(P,H) :- place(P), helper(H), not in_classroom(P), helper_kind(H,mother).

valid(P,O,S,H) :- affords(P,O), fit_support(O,S), allowed_helper(P,H).

% clue/support pairing
clue_matches(C,S) :- clue_for_support(S,C).

% outcome model
stays_upright :- chosen_object(O), chosen_support(S), fit_support(O,S).
solved :- stays_upright, chosen_support(S), chosen_clue(C), clue_matches(C,S).
outcome(solved) :- solved.
outcome(bad_clue) :- stays_upright, not solved.
outcome(fallen) :- not stays_upright.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        if place_id == "classroom":
            lines.append(asp.fact("in_classroom", place_id))
        for obj_id in sorted(place.affordances):
            lines.append(asp.fact("affords", place_id, obj_id))
    for obj_id, obj in OBJECTS.items():
        lines.append(asp.fact("object", obj_id))
        lines.append(asp.fact("need", obj_id, obj.need))
    for support_id, support in SUPPORTS.items():
        lines.append(asp.fact("support", support_id))
        lines.append(asp.fact("strength", support_id, support.strength))
    for helper_id, helper in HELPERS.items():
        lines.append(asp.fact("helper", helper_id))
        lines.append(asp.fact("helper_kind", helper_id, helper.type))
    for clue_id in CLUES:
        lines.append(asp.fact("clue", clue_id))
    for support_id, clue_id in CLUE_FOR_SUPPORT.items():
        lines.append(asp.fact("clue_for_support", support_id, clue_id))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    scenario = "\n".join(
        [
            asp.fact("chosen_object", params.object),
            asp.fact("chosen_support", params.support),
            asp.fact("chosen_clue", params.clue),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def outcome_of(params: StoryParams) -> str:
    if not support_fits(OBJECTS[params.object], SUPPORTS[params.support]):
        return "fallen"
    if not clue_matches_support(params.clue, params.support):
        return "bad_clue"
    return "solved"


def asp_verify() -> int:
    rc = 0

    py_set = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py_set == asp_set:
        print(f"OK: gate matches valid_combos() ({len(py_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if py_set - asp_set:
            print("  only in python:", sorted(py_set - asp_set))
        if asp_set - py_set:
            print("  only in clingo:", sorted(asp_set - py_set))

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
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("smoke test generated an empty story")
        print("OK: smoke test generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


# ---------------------------------------------------------------------------
# Standard storyworld interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: an upright mystery solved by a clue and a flashback."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--object", choices=OBJECTS)
    ap.add_argument("--support", choices=SUPPORTS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--sleuth-name")
    ap.add_argument("--partner-name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the ASP twin matches the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.object and args.support and args.helper:
        if not valid_combo(args.place, args.object, args.support, args.helper):
            raise StoryError(
                explain_rejection(
                    PLACES[args.place],
                    OBJECTS[args.object],
                    SUPPORTS[args.support],
                    HELPERS[args.helper],
                )
            )

    filtered = [
        combo
        for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.object is None or combo[1] == args.object)
        and (args.support is None or combo[2] == args.support)
        and (args.helper is None or combo[3] == args.helper)
    ]
    if not filtered:
        if args.place and args.object and args.support and args.helper:
            raise StoryError(
                explain_rejection(
                    PLACES[args.place],
                    OBJECTS[args.object],
                    SUPPORTS[args.support],
                    HELPERS[args.helper],
                )
            )
        raise StoryError("(No valid combination matches the given options.)")

    place_id, object_id, support_id, helper_id = rng.choice(filtered)
    clue_id = args.clue or CLUE_FOR_SUPPORT[support_id]

    if not clue_matches_support(clue_id, support_id):
        raise StoryError(
            f"(No story: clue '{clue_id}' does not match support '{support_id}'. "
            f"The flashback clue has to point to the real fix.)"
        )

    sleuth_name, sleuth_gender = _pick_name(rng)
    partner_name, partner_gender = _pick_name(rng, avoid=sleuth_name)
    sleuth_name = args.sleuth_name or sleuth_name
    partner_name = args.partner_name or partner_name
    sleuth_trait = rng.choice(TRAITS)
    partner_trait = rng.choice([t for t in TRAITS if t != sleuth_trait] or TRAITS)

    return StoryParams(
        place=place_id,
        object=object_id,
        support=support_id,
        clue=clue_id,
        helper=helper_id,
        sleuth_name=sleuth_name,
        sleuth_gender=sleuth_gender,
        partner_name=partner_name,
        partner_gender=partner_gender,
        sleuth_trait=sleuth_trait,
        partner_trait=partner_trait,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        place = PLACES[params.place]
        obj = OBJECTS[params.object]
        support = SUPPORTS[params.support]
        clue = CLUES[params.clue]
        helper = HELPERS[params.helper]
    except KeyError as err:
        raise StoryError(f"(Invalid story parameter: {err.args[0]})") from None

    if not valid_combo(params.place, params.object, params.support, params.helper):
        raise StoryError(explain_rejection(place, obj, support, helper))
    if not clue_matches_support(params.clue, params.support):
        raise StoryError(
            f"(No story: clue '{params.clue}' does not fit support '{params.support}', "
            f"so the flashback would not honestly solve the mystery.)"
        )

    world = tell(
        place,
        obj,
        support,
        clue,
        helper,
        sleuth_name=params.sleuth_name,
        sleuth_gender=params.sleuth_gender,
        partner_name=params.partner_name,
        partner_gender=params.partner_gender,
        sleuth_trait=params.sleuth_trait,
        partner_trait=params.partner_trait,
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
        print(asp_program("", "#show valid/4.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, object, support, helper) combos:\n")
        for place_id, object_id, support_id, helper_id in combos:
            clue_id = CLUE_FOR_SUPPORT[support_id]
            print(f"  {place_id:12} {object_id:9} {support_id:11} {helper_id:8} clue={clue_id}")
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.sleuth_name} & {p.partner_name}: {p.object} in {p.place} ({p.support}, {p.helper})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
