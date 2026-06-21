#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/alias_milk_tricycle_flashback_humor_mystery_to.py
============================================================================

A standalone story world about a child using a detective alias to solve a small
home mystery: who kept leaving a little trail of missing milk? The answer comes
from ordinary slice-of-life world state, with a gentle flashback, a funny turn,
and a solved mystery.

The domain is intentionally small and concrete:
- a child invents an alias and plays detective
- someone small keeps sipping or spilling milk
- clues around the home point toward a culprit
- a flashback shows the earlier cause of the mystery
- the ending proves what changed: milk is kept safely, and the tricycle gets a new use

Run it
------
    python storyworlds/worlds/gpt-5.4/alias_milk_tricycle_flashback_humor_mystery_to.py
    python storyworlds/worlds/gpt-5.4/alias_milk_tricycle_flashback_humor_mystery_to.py --culprit sibling --vehicle tricycle
    python storyworlds/worlds/gpt-5.4/alias_milk_tricycle_flashback_humor_mystery_to.py --container carton --clue pawprints
    python storyworlds/worlds/gpt-5.4/alias_milk_tricycle_flashback_humor_mystery_to.py --all
    python storyworlds/worlds/gpt-5.4/alias_milk_tricycle_flashback_humor_mystery_to.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/alias_milk_tricycle_flashback_humor_mystery_to.py --verify
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
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "sister"}
        male = {"boy", "father", "man", "brother"}
        animal = {"cat", "kitten", "dog", "puppy"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in animal:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class Alias:
    id: str
    title: str
    style: str
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
class Container:
    id: str
    label: str
    phrase: str
    portable: bool
    stable: bool
    easy_to_tilt: bool
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
class Vehicle:
    id: str
    label: str
    phrase: str
    wobbly: bool
    speedy: bool
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
    type: str
    label: str
    relation: str
    can_confess: bool
    leaves_pawprints: bool = False
    leaves_milk_mustache: bool = False
    tips_when_bumping: bool = False
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
class Clue:
    id: str
    label: str
    phrase: str
    points_to: set[str]
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
class Fix:
    id: str
    label: str
    works_for: set[str]
    text: str
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
        other = World()
        other.entities = copy.deepcopy(self.entities)
        other.fired = set(self.fired)
        other.paragraphs = [[]]
        other.facts = copy.deepcopy(self.facts)
        return other


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


def _r_spill_marks(world: World) -> list[str]:
    culprit = world.get("culprit")
    kitchen = world.get("kitchen")
    hall = world.get("hall")
    if culprit.meters["milk_taken"] < THRESHOLD:
        return []
    sig = ("spill_marks", culprit.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    kitchen.meters["drip"] += 1
    hall.meters["trail"] += 1
    if culprit.attrs.get("leaves_pawprints"):
        hall.meters["pawprints"] += 1
    if culprit.attrs.get("leaves_milk_mustache"):
        culprit.meters["mustache"] += 1
    return []


def _r_bump_tip(world: World) -> list[str]:
    culprit = world.get("culprit")
    container = world.get("container")
    vehicle = world.get("vehicle")
    if not culprit.attrs.get("tips_when_bumping"):
        return []
    if not vehicle.attrs.get("wobbly"):
        return []
    if not container.attrs.get("easy_to_tilt"):
        return []
    if culprit.meters["ride_attempt"] < THRESHOLD:
        return []
    sig = ("bump_tip", culprit.id, container.id, vehicle.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    container.meters["tilted"] += 1
    container.meters["spilled"] += 1
    world.get("kitchen").meters["drip"] += 1
    world.get("hall").meters["trail"] += 1
    return []


def _r_detective_excited(world: World) -> list[str]:
    child = world.get("child")
    if child.memes["mystery"] < THRESHOLD:
        return []
    sig = ("detective_excited", child.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["curiosity"] += 1
    child.memes["joy"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="spill_marks", tag="physical", apply=_r_spill_marks),
    Rule(name="bump_tip", tag="physical", apply=_r_bump_tip),
    Rule(name="detective_excited", tag="emotional", apply=_r_detective_excited),
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
        for s in produced:
            world.say(s)
    return produced


def valid_combo(culprit: Culprit, clue: Clue, fix: Fix) -> bool:
    return culprit.id in clue.points_to and culprit.id in fix.works_for


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for culprit_id, culprit in CULPRITS.items():
        for clue_id, clue in CLUES.items():
            for fix_id, fix in FIXES.items():
                if valid_combo(culprit, clue, fix):
                    out.append((culprit_id, clue_id, fix_id))
    return out


def explain_rejection(culprit: Culprit, clue: Clue, fix: Fix) -> str:
    if culprit.id not in clue.points_to:
        return (
            f"(No story: the clue '{clue.label}' would not honestly point to {culprit.label}. "
            f"The mystery needs fair clues, not random guessing.)"
        )
    if culprit.id not in fix.works_for:
        return (
            f"(No story: the fix '{fix.label}' would not solve trouble caused by {culprit.label}. "
            f"The ending must really change the world.)"
        )
    return "(No story: this combination is not valid.)"


def predict_case(culprit: Culprit, clue: Clue, vehicle: Vehicle, container: Container) -> dict:
    world = World()
    world.add(Entity(id="child", kind="character", type="girl", role="detective"))
    world.add(Entity(id="parent", kind="character", type="mother", role="parent"))
    world.add(Entity(
        id="culprit",
        kind="character" if culprit.type not in {"cat", "kitten", "dog", "puppy"} else "thing",
        type=culprit.type,
        label=culprit.label,
        role="culprit",
        attrs={
            "leaves_pawprints": culprit.leaves_pawprints,
            "leaves_milk_mustache": culprit.leaves_milk_mustache,
            "tips_when_bumping": culprit.tips_when_bumping,
        },
    ))
    world.add(Entity(
        id="container",
        type="container",
        label=container.label,
        attrs={"easy_to_tilt": container.easy_to_tilt},
    ))
    world.add(Entity(
        id="vehicle",
        type="vehicle",
        label=vehicle.label,
        attrs={"wobbly": vehicle.wobbly},
    ))
    world.add(Entity(id="kitchen", type="room", label="kitchen"))
    world.add(Entity(id="hall", type="room", label="hall"))
    world.get("culprit").meters["milk_taken"] = 1
    if culprit.tips_when_bumping:
        world.get("culprit").meters["ride_attempt"] = 1
    propagate(world, narrate=False)
    return {
        "drip": world.get("kitchen").meters["drip"] >= THRESHOLD,
        "pawprints": world.get("hall").meters["pawprints"] >= THRESHOLD,
        "mustache": world.get("culprit").meters["mustache"] >= THRESHOLD,
        "fair": culprit.id in clue.points_to,
    }


@dataclass
class StoryParams:
    alias: str
    container: str
    vehicle: str
    culprit: str
    clue: str
    fix: str
    child_name: str
    child_gender: str
    parent: str
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


def setup_scene(world: World, child: Entity, parent: Entity, alias_cfg: Alias, container: Container, vehicle: Vehicle) -> None:
    child.memes["joy"] += 1
    world.say(
        f"After breakfast, {child.id} tied a dish towel around {child.pronoun('possessive')} shoulders and announced a brand-new alias: "
        f'"{alias_cfg.title}!"'
    )
    world.say(
        f"{parent.label_word.capitalize()} laughed and saluted the tiny detective. "
        f"In the kitchen, {container.phrase} sat on the table, and {vehicle.phrase} waited by the hall rug."
    )
    world.say(
        f"{child.id} liked mysteries almost as much as riding the {vehicle.label}, so the morning already felt important."
    )


def mystery_appears(world: World, child: Entity, parent: Entity, container: Container) -> None:
    child.memes["mystery"] += 1
    propagate(world, narrate=False)
    world.para()
    world.say(
        f"But when {parent.label_word} came back to pour another cup, a little white drip shone on the floor."
    )
    world.say(
        f'"That is strange," {parent.label_word} said. "A moment ago, {container.phrase} was much fuller."'
    )
    world.say(
        f"{child.id} stood very straight. A case involving milk had appeared."
    )


def declare_alias(world: World, child: Entity, alias_cfg: Alias) -> None:
    world.say(
        f'"Do not worry," {child.id} said. "{alias_cfg.title}, {alias_cfg.style}, will solve this mystery."'
    )


def inspect_clue(world: World, child: Entity, clue: Clue, culprit: Entity) -> None:
    child.memes["focus"] += 1
    world.para()
    if clue.id == "pawprints":
        world.say(
            f"{child.id} crouched low and found tiny pale pawprints leading away from the kitchen."
        )
        world.say(
            f'"Aha," whispered {child.pronoun()}, trying to sound very serious even while {child.pronoun("possessive")} knees squeaked on the floor.'
        )
    elif clue.id == "mustache":
        world.say(
            f"Near the sofa sat {culprit.label}, wearing a silly little milk mustache."
        )
        world.say(
            f"{child.id} pressed {child.pronoun('possessive')} lips together so hard that a laugh almost leaked out."
        )
    else:
        world.say(
            f"By the hall rug, {child.id} found a crooked wet line and one little bump mark on the table leg."
        )
        world.say(
            f'"This was not an ordinary breakfast," {child.pronoun()} said in {child.pronoun("possessive")} deepest detective voice.'
        )


def flashback(world: World, child: Entity, culprit_cfg: Culprit, container: Container, vehicle: Vehicle) -> None:
    world.para()
    world.say(
        f"Then {child.id} remembered what had happened a few minutes earlier."
    )
    if culprit_cfg.id == "kitten":
        world.say(
            f"In a quick flashback, the kitten had stretched up for a sniff, tapped the {container.label} with one curious paw, and lapped the tiny puddle that slipped over the edge."
        )
    elif culprit_cfg.id == "sibling":
        world.say(
            f"In the flashback, {world.get('culprit').label} had taken one secret sip, then another, and had not noticed the bright milk stripe resting over {world.get('culprit').pronoun('possessive')} upper lip."
        )
    else:
        wobble = "wobbly " if vehicle.wobbly else ""
        world.say(
            f"In the flashback, the puppy had tried to nose past the {wobble}{vehicle.label}, bumped the table leg, and made the {container.label} wobble just enough to slosh."
        )


def solve_mystery(world: World, child: Entity, culprit_cfg: Culprit, clue: Clue) -> None:
    world.para()
    if culprit_cfg.id == "kitten":
        world.say(
            f'{child.id} pointed to the floor. "The answer is the kitten. The pawprints match, and the milk trail starts right beside the table."'
        )
    elif culprit_cfg.id == "sibling":
        world.say(
            f'"The answer is {world.get("culprit").label}," {child.id} announced. "The clue is the milk mustache, and that is a very honest clue."'
        )
    else:
        world.say(
            f'"The answer is the puppy," {child.id} declared. "The bump mark and the milk trail show that the table was jiggled when the puppy hurried past."'
        )
    world.say(
        f"{parent.label_word.capitalize()} blinked once, then smiled. The mystery was solved fairly, not just guessed."
    )
    child.memes["pride"] += 1


def funny_confession(world: World, culprit: Entity, culprit_cfg: Culprit) -> None:
    if culprit_cfg.can_confess:
        world.say(
            f'{culprit.label} looked embarrassed and mumbled, "I only meant to take one tiny sip."'
        )
    elif culprit_cfg.id == "kitten":
        world.say(
            f"The kitten answered with a tiny mew and licked its whiskers, which felt almost the same as a confession."
        )
    else:
        world.say(
            f"The puppy wagged so hard that its whole back half wiggled, which was not exactly a confession but was not exactly a denial either."
        )


def repair(world: World, parent: Entity, fix: Fix, container: Container, vehicle: Vehicle) -> None:
    world.para()
    world.say(
        f"{parent.label_word.capitalize()} {fix.text.format(container=container.label, vehicle=vehicle.label)}"
    )
    world.say(
        fix.ending.format(container=container.label, vehicle=vehicle.label)
    )


def close_story(world: World, child: Entity, alias_cfg: Alias, vehicle: Vehicle) -> None:
    child.memes["joy"] += 1
    world.say(
        f'{child.id} climbed onto the {vehicle.label} and rang an invisible detective bell. "{alias_cfg.title} accepts payment in hugs and pancakes," {child.pronoun()} said.'
    )
    world.say(
        f"Everyone laughed, and the house felt ordinary again in the nicest way."
    )


def tell(
    alias_cfg: Alias,
    container_cfg: Container,
    vehicle_cfg: Vehicle,
    culprit_cfg: Culprit,
    clue_cfg: Clue,
    fix_cfg: Fix,
    child_name: str = "Mia",
    child_gender: str = "girl",
    parent_type: str = "mother",
) -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="detective"))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, role="parent", label="the parent"))
    culprit = world.add(Entity(
        id="culprit",
        kind="character" if culprit_cfg.type in {"girl", "boy", "sister", "brother"} else "thing",
        type=culprit_cfg.type,
        role="culprit",
        label=culprit_cfg.label,
        attrs={
            "relation": culprit_cfg.relation,
            "leaves_pawprints": culprit_cfg.leaves_pawprints,
            "leaves_milk_mustache": culprit_cfg.leaves_milk_mustache,
            "tips_when_bumping": culprit_cfg.tips_when_bumping,
        },
        tags=set(culprit_cfg.tags),
    ))
    container = world.add(Entity(
        id="container",
        type="container",
        label=container_cfg.label,
        attrs={
            "portable": container_cfg.portable,
            "stable": container_cfg.stable,
            "easy_to_tilt": container_cfg.easy_to_tilt,
        },
        tags=set(container_cfg.tags),
    ))
    vehicle = world.add(Entity(
        id="vehicle",
        type="vehicle",
        label=vehicle_cfg.label,
        attrs={
            "wobbly": vehicle_cfg.wobbly,
            "speedy": vehicle_cfg.speedy,
        },
        tags=set(vehicle_cfg.tags),
    ))
    world.add(Entity(id="kitchen", type="room", label="kitchen"))
    world.add(Entity(id="hall", type="room", label="hall"))

    child.memes["mystery"] = 0.0
    child.memes["curiosity"] = 0.0
    culprit.meters["milk_taken"] = 1.0
    culprit.meters["ride_attempt"] = 1.0 if culprit_cfg.tips_when_bumping else 0.0
    container.meters["spilled"] = 0.0
    container.meters["tilted"] = 0.0

    propagate(world, narrate=False)

    setup_scene(world, child, parent, alias_cfg, container_cfg, vehicle_cfg)
    mystery_appears(world, child, parent, container_cfg)
    declare_alias(world, child, alias_cfg)
    inspect_clue(world, child, clue_cfg, culprit)
    flashback(world, child, culprit_cfg, container_cfg, vehicle_cfg)
    solve_mystery(world, child, culprit_cfg, clue_cfg)
    funny_confession(world, culprit, culprit_cfg)
    repair(world, parent, fix_cfg, container_cfg, vehicle_cfg)
    close_story(world, child, alias_cfg, vehicle_cfg)

    world.facts.update(
        child=child,
        parent=parent,
        culprit=culprit,
        alias_cfg=alias_cfg,
        container_cfg=container_cfg,
        vehicle_cfg=vehicle_cfg,
        culprit_cfg=culprit_cfg,
        clue_cfg=clue_cfg,
        fix_cfg=fix_cfg,
        solved=True,
        milk_spilled=container.meters["spilled"] >= THRESHOLD or world.get("kitchen").meters["drip"] >= THRESHOLD,
        pawprints=world.get("hall").meters["pawprints"] >= THRESHOLD,
        mustache=culprit.meters["mustache"] >= THRESHOLD,
        trail=world.get("hall").meters["trail"] >= THRESHOLD,
    )
    return world


ALIASES = {
    "whisker": Alias(
        id="whisker",
        title="Detective Whisker",
        style="keeper of kitchen clues",
        tags={"alias", "detective"},
    ),
    "puddle": Alias(
        id="puddle",
        title="Inspector Puddle",
        style="finder of slippery secrets",
        tags={"alias", "detective"},
    ),
    "toast": Alias(
        id="toast",
        title="Captain Toast",
        style="solver of breakfast mysteries",
        tags={"alias", "detective"},
    ),
}

CONTAINERS = {
    "glass": Container(
        id="glass",
        label="glass",
        phrase="a glass of milk",
        portable=True,
        stable=False,
        easy_to_tilt=True,
        tags={"milk", "kitchen"},
    ),
    "mug": Container(
        id="mug",
        label="mug",
        phrase="a blue mug of milk",
        portable=True,
        stable=True,
        easy_to_tilt=False,
        tags={"milk", "kitchen"},
    ),
    "carton": Container(
        id="carton",
        label="carton",
        phrase="a small milk carton",
        portable=True,
        stable=False,
        easy_to_tilt=True,
        tags={"milk", "kitchen"},
    ),
}

VEHICLES = {
    "tricycle": Vehicle(
        id="tricycle",
        label="tricycle",
        phrase="a red tricycle",
        wobbly=True,
        speedy=False,
        tags={"tricycle", "ride"},
    ),
    "wagon": Vehicle(
        id="wagon",
        label="wagon",
        phrase="a little wagon",
        wobbly=False,
        speedy=False,
        tags={"wagon", "ride"},
    ),
    "scooter": Vehicle(
        id="scooter",
        label="scooter",
        phrase="a three-wheel scooter",
        wobbly=False,
        speedy=True,
        tags={"scooter", "ride"},
    ),
}

CULPRITS = {
    "kitten": Culprit(
        id="kitten",
        type="kitten",
        label="the kitten",
        relation="pet",
        can_confess=False,
        leaves_pawprints=True,
        leaves_milk_mustache=False,
        tips_when_bumping=False,
        tags={"pet", "cat"},
    ),
    "sibling": Culprit(
        id="sibling",
        type="sister",
        label="Nora",
        relation="sibling",
        can_confess=True,
        leaves_pawprints=False,
        leaves_milk_mustache=True,
        tips_when_bumping=False,
        tags={"family", "sibling"},
    ),
    "puppy": Culprit(
        id="puppy",
        type="puppy",
        label="the puppy",
        relation="pet",
        can_confess=False,
        leaves_pawprints=False,
        leaves_milk_mustache=False,
        tips_when_bumping=True,
        tags={"pet", "dog"},
    ),
}

CLUES = {
    "pawprints": Clue(
        id="pawprints",
        label="pawprints",
        phrase="tiny pawprints in the milk",
        points_to={"kitten"},
        tags={"clue", "pawprints"},
    ),
    "mustache": Clue(
        id="mustache",
        label="milk mustache",
        phrase="a milk mustache",
        points_to={"sibling"},
        tags={"clue", "milk"},
    ),
    "bump": Clue(
        id="bump",
        label="bump mark",
        phrase="a bump mark and a crooked milk trail",
        points_to={"puppy"},
        tags={"clue", "trail"},
    ),
}

FIXES = {
    "high_shelf": Fix(
        id="high_shelf",
        label="high shelf",
        works_for={"kitten", "puppy"},
        text="wiped the floor, set the {container} higher up, and promised that milk would wait on the counter instead of near fast little feet.",
        ending="After that, the {container} stayed out of bumping and sniffing range.",
        tags={"safety", "kitchen"},
    ),
    "ask_first": Fix(
        id="ask_first",
        label="ask first",
        works_for={"sibling"},
        text="poured everyone a fresh little drink and said that secret sips were not needed when asking nicely worked better.",
        ending="Nora nodded, scrubbed off the milk mustache, and asked for a cup the proper way next time.",
        tags={"sharing", "family"},
    ),
    "parking_spot": Fix(
        id="parking_spot",
        label="parking spot",
        works_for={"puppy"},
        text="mopped the drip and made a special parking spot for the {vehicle} far from the table.",
        ending="The {vehicle} stayed by the wall after that, and breakfast had room to be calm again.",
        tags={"safety", "tricycle"},
    ),
}

GIRL_NAMES = ["Mia", "Lily", "Ava", "Zoe", "Nora", "Ella", "Lucy", "Anna"]
BOY_NAMES = ["Ben", "Max", "Leo", "Sam", "Eli", "Finn", "Theo", "Jack"]


KNOWLEDGE = {
    "alias": [
        (
            "What is an alias?",
            "An alias is another name someone uses, often for fun or for a special job. In a pretend detective game, an alias can make the game feel exciting."
        )
    ],
    "milk": [
        (
            "What is milk?",
            "Milk is a drink people often have with breakfast or snacks. If it spills, it can make the floor slippery and messy."
        )
    ],
    "tricycle": [
        (
            "What is a tricycle?",
            "A tricycle is a small ride with three wheels. It is steady for young children, but it still needs a safe parking spot indoors."
        )
    ],
    "pawprints": [
        (
            "What are pawprints?",
            "Pawprints are the little marks an animal's feet leave behind. They can work like clues when you are trying to see where a pet has been."
        )
    ],
    "mystery": [
        (
            "What is a mystery?",
            "A mystery is something you do not understand yet and want to figure out. Good clues help you solve it fairly."
        )
    ],
    "flashback": [
        (
            "What is a flashback in a story?",
            "A flashback is a short look back at something that happened earlier. It helps explain the present by showing the cause from before."
        )
    ],
    "sharing": [
        (
            "Why is it better to ask before taking someone else's drink?",
            "Asking first is kinder and clearer than sneaking a sip. It helps everyone solve small problems before feelings get hurt."
        )
    ],
    "safety": [
        (
            "Why should spills be cleaned up quickly?",
            "Spills can make floors sticky or slippery. Cleaning them quickly keeps people and pets safer."
        )
    ],
}

KNOWLEDGE_ORDER = ["alias", "milk", "tricycle", "pawprints", "mystery", "flashback", "sharing", "safety"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    alias_cfg = f["alias_cfg"]
    culprit_cfg = f["culprit_cfg"]
    vehicle_cfg = f["vehicle_cfg"]
    return [
        f'Write a gentle slice-of-life mystery for a 3-to-5-year-old where a child invents an alias and solves a tiny breakfast problem involving milk.',
        f"Tell a funny home story where {child.id} becomes {alias_cfg.title}, studies clues, and works out what happened near the {vehicle_cfg.label}.",
        f"Write a short story with a flashback, a small mystery to solve, and a warm ending where the culprit turns out to be {culprit_cfg.label}.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    culprit = f["culprit"]
    alias_cfg = f["alias_cfg"]
    container_cfg = f["container_cfg"]
    vehicle_cfg = f["vehicle_cfg"]
    clue_cfg = f["clue_cfg"]
    fix_cfg = f["fix_cfg"]
    pw = parent.label_word

    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, who takes the alias {alias_cfg.title}, and {pw}, who notices the missing milk. The story also includes {culprit.label}, who turns out to be the cause of the mystery."
        ),
        (
            "What was the mystery?",
            f"The mystery was why the {container_cfg.label} was less full and why little drops of milk had appeared on the floor. {child.id} treated the small breakfast mess like a real case to solve."
        ),
        (
            f"Why did {child.id} use an alias?",
            f"{child.id} wanted to feel like a real detective, so the alias made the search more exciting and funny. It turned an ordinary home problem into playful pretend work."
        ),
        (
            "How did the flashback help solve the mystery?",
            f"The flashback showed what had happened a few minutes earlier, before anyone understood the mess. It connected the clue to the true cause, so the answer was fair instead of a wild guess."
        ),
    ]

    if clue_cfg.id == "pawprints":
        qa.append(
            (
                "What clue solved the case?",
                f"The clue was the tiny pawprints in the milk. They pointed to the kitten because those marks led away from the table where the milk had been."
            )
        )
    elif clue_cfg.id == "mustache":
        qa.append(
            (
                "What clue solved the case?",
                f"The clue was the milk mustache on Nora. It mattered because it showed she had taken a sip before anyone asked about the missing milk."
            )
        )
    else:
        qa.append(
            (
                "What clue solved the case?",
                f"The clue was the bump mark with the crooked milk trail. Together they showed that something hurried past the table and jiggled it."
            )
        )

    qa.append(
        (
            f"How did {pw} fix the problem?",
            f"{pw.capitalize()} {fix_cfg.text.format(container=container_cfg.label, vehicle=vehicle_cfg.label)} {fix_cfg.ending.format(container=container_cfg.label, vehicle=vehicle_cfg.label)}"
        )
    )
    qa.append(
        (
            "How did the story end?",
            f"It ended with everyone laughing and the mystery solved. The new plan changed the house a little, so breakfast could feel calm again while {child.id} still enjoyed pretending to be {alias_cfg.title}."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"alias", "milk", "mystery", "flashback"}
    if f["vehicle_cfg"].id == "tricycle":
        tags.add("tricycle")
    if f["clue_cfg"].id == "pawprints":
        tags.add("pawprints")
    if f["fix_cfg"].id == "ask_first":
        tags.add("sharing")
    else:
        tags.add("safety")
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
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:10} ({e.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        alias="whisker",
        container="glass",
        vehicle="tricycle",
        culprit="kitten",
        clue="pawprints",
        fix="high_shelf",
        child_name="Mia",
        child_gender="girl",
        parent="mother",
    ),
    StoryParams(
        alias="puddle",
        container="mug",
        vehicle="wagon",
        culprit="sibling",
        clue="mustache",
        fix="ask_first",
        child_name="Ben",
        child_gender="boy",
        parent="father",
    ),
    StoryParams(
        alias="toast",
        container="carton",
        vehicle="tricycle",
        culprit="puppy",
        clue="bump",
        fix="parking_spot",
        child_name="Lucy",
        child_gender="girl",
        parent="mother",
    ),
]


ASP_RULES = r"""
valid(Culprit, Clue, Fix) :- culprit(Culprit), clue(Clue), fix(Fix),
                             clue_points(Clue, Culprit), fix_works(Fix, Culprit).

% What physical signs follow from each culprit.
has_sign(Culprit, pawprints) :- culprit_leaves_pawprints(Culprit).
has_sign(Culprit, mustache)  :- culprit_leaves_mustache(Culprit).
has_sign(Culprit, bump)      :- culprit_tips_when_bumping(Culprit).

fair_clue(Culprit, Clue) :- clue_points(Clue, Culprit).

scenario_ok :- chosen_culprit(C), chosen_clue(L), chosen_fix(F),
               valid(C, L, F).

outcome(solved) :- scenario_ok.
#show valid/3.
#show outcome/1.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for cid, culprit in CULPRITS.items():
        lines.append(asp.fact("culprit", cid))
        if culprit.leaves_pawprints:
            lines.append(asp.fact("culprit_leaves_pawprints", cid))
        if culprit.leaves_milk_mustache:
            lines.append(asp.fact("culprit_leaves_mustache", cid))
        if culprit.tips_when_bumping:
            lines.append(asp.fact("culprit_tips_when_bumping", cid))
    for clue_id, clue in CLUES.items():
        lines.append(asp.fact("clue", clue_id))
        for cid in sorted(clue.points_to):
            lines.append(asp.fact("clue_points", clue_id, cid))
    for fix_id, fix in FIXES.items():
        lines.append(asp.fact("fix", fix_id))
        for cid in sorted(fix.works_for):
            lines.append(asp.fact("fix_works", fix_id, cid))
    for alias_id in ALIASES:
        lines.append(asp.fact("alias", alias_id))
    for container_id in CONTAINERS:
        lines.append(asp.fact("container", container_id))
    for vehicle_id in VEHICLES:
        lines.append(asp.fact("vehicle", vehicle_id))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program(show="#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    scenario = "\n".join(
        [
            asp.fact("chosen_culprit", params.culprit),
            asp.fact("chosen_clue", params.clue),
            asp.fact("chosen_fix", params.fix),
        ]
    )
    model = asp.one_model(asp_program(extra=scenario, show="#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def outcome_of(params: StoryParams) -> str:
    if params.culprit not in CULPRITS or params.clue not in CLUES or params.fix not in FIXES:
        return "invalid"
    return "solved" if valid_combo(CULPRITS[params.culprit], CLUES[params.clue], FIXES[params.fix]) else "invalid"


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
    parser = build_parser()
    for s in range(40):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(s))
        except StoryError:
            continue
        cases.append(params)

    bad = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            bad += 1
    if bad == 0:
        print(f"OK: ASP outcome matches Python on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} scenario outcomes differ.")

    try:
        sample = generate(cases[0])
        emit(sample, trace=False, qa=False, header="")
        print("OK: smoke test generation/emit succeeded.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a child detective alias, a little milk mystery, and a cozy solved ending."
    )
    ap.add_argument("--alias", choices=ALIASES)
    ap.add_argument("--container", choices=CONTAINERS)
    ap.add_argument("--vehicle", choices=VEHICLES)
    ap.add_argument("--culprit", choices=CULPRITS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--child-name")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid culprit/clue/fix combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.culprit and args.clue and args.fix:
        culprit = CULPRITS[args.culprit]
        clue = CLUES[args.clue]
        fix = FIXES[args.fix]
        if not valid_combo(culprit, clue, fix):
            raise StoryError(explain_rejection(culprit, clue, fix))

    combos = [
        c for c in valid_combos()
        if (args.culprit is None or c[0] == args.culprit)
        and (args.clue is None or c[1] == args.clue)
        and (args.fix is None or c[2] == args.fix)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    culprit_id, clue_id, fix_id = rng.choice(sorted(combos))
    alias_id = args.alias or rng.choice(sorted(ALIASES))
    container_id = args.container or rng.choice(sorted(CONTAINERS))
    vehicle_id = args.vehicle or rng.choice(sorted(VEHICLES))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    child_name = args.child_name or rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(
        alias=alias_id,
        container=container_id,
        vehicle=vehicle_id,
        culprit=culprit_id,
        clue=clue_id,
        fix=fix_id,
        child_name=child_name,
        child_gender=child_gender,
        parent=parent,
    )


def generate(params: StoryParams) -> StorySample:
    if params.alias not in ALIASES:
        raise StoryError(f"(Unknown alias: {params.alias})")
    if params.container not in CONTAINERS:
        raise StoryError(f"(Unknown container: {params.container})")
    if params.vehicle not in VEHICLES:
        raise StoryError(f"(Unknown vehicle: {params.vehicle})")
    if params.culprit not in CULPRITS:
        raise StoryError(f"(Unknown culprit: {params.culprit})")
    if params.clue not in CLUES:
        raise StoryError(f"(Unknown clue: {params.clue})")
    if params.fix not in FIXES:
        raise StoryError(f"(Unknown fix: {params.fix})")

    culprit = CULPRITS[params.culprit]
    clue = CLUES[params.clue]
    fix = FIXES[params.fix]
    if not valid_combo(culprit, clue, fix):
        raise StoryError(explain_rejection(culprit, clue, fix))

    world = tell(
        alias_cfg=ALIASES[params.alias],
        container_cfg=CONTAINERS[params.container],
        vehicle_cfg=VEHICLES[params.vehicle],
        culprit_cfg=culprit,
        clue_cfg=clue,
        fix_cfg=fix,
        child_name=params.child_name,
        child_gender=params.child_gender,
        parent_type=params.parent,
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
        print(asp_program(show="#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid (culprit, clue, fix) combos:\n")
        for culprit, clue, fix in combos:
            print(f"  {culprit:8} {clue:10} {fix}")
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
            header = f"### {p.child_name}: {p.culprit} / {p.clue} / {p.fix} ({p.vehicle})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
