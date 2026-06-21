#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/reckless_food_volcano_foreshadowing_sharing_suspense_whodunit.py
================================================================================================

A standalone story world for a tiny whodunit about a snack-time volcano.

Premise
-------
A child builds a shared "food volcano" for snack time. The volcano is stacked a
little too high in a reckless way, so quiet clues appear before anything big
happens: a bead of lava drips, the top leans, and the table feels tense. Then
the topper vanishes. Did a puppy steal it? Did a little sibling take it? The
children investigate, solve the mystery, and learn that a steadier, fairer snack
is better for sharing than a showy tower.

This world is deliberately small and constrained. Not every base / lava / topper
combination is allowed. A story is only valid when the combination sits right on
the edge: stable enough to look fine at first, but unstable once the builder adds
one extra reckless layer. That gives the story a real foreshadowing beat,
suspense, and a solvable mystery instead of an arbitrary accident.

Run it
------
    python storyworlds/worlds/gpt-5.4/reckless_food_volcano_foreshadowing_sharing_suspense_whodunit.py
    python storyworlds/worlds/gpt-5.4/reckless_food_volcano_foreshadowing_sharing_suspense_whodunit.py --base cracker_ring --lava berry_yogurt --topper cheese_cube
    python storyworlds/worlds/gpt-5.4/reckless_food_volcano_foreshadowing_sharing_suspense_whodunit.py --base cucumber_hill --lava berry_yogurt --topper grape_cluster
    python storyworlds/worlds/gpt-5.4/reckless_food_volcano_foreshadowing_sharing_suspense_whodunit.py --all
    python storyworlds/worlds/gpt-5.4/reckless_food_volcano_foreshadowing_sharing_suspense_whodunit.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/reckless_food_volcano_foreshadowing_sharing_suspense_whodunit.py --verify
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
RECKLESS_BONUS = 1


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
        female = {"girl", "mother", "mom", "woman", "sister"}
        male = {"boy", "father", "dad", "man", "brother"}
        animal = {"dog", "puppy", "cat", "kitten"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in animal:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
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
class Base:
    id: str
    label: str
    phrase: str
    support: int
    texture: str
    plate_fix: str
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
class Lava:
    id: str
    label: str
    phrase: str
    wetness: int
    color: str
    drip_text: str
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
class Topper:
    id: str
    label: str
    phrase: str
    weight: int
    smell: str
    clue_if_fallen: str
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
class Suspect:
    id: str
    label: str
    type: str
    role: str
    clue: str
    reveal: str
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
        return [e for e in self.entities.values() if e.kind == "character" and e.role in {"builder", "sleuth"}]

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


def stack_load(base: Base, lava: Lava, topper: Topper, reckless: bool = True) -> int:
    return lava.wetness + topper.weight + (RECKLESS_BONUS if reckless else 0)


def careful_load(lava: Lava, topper: Topper) -> int:
    return lava.wetness + topper.weight


def teeter_window(base: Base, lava: Lava, topper: Topper) -> bool:
    safe = careful_load(lava, topper)
    reckless = stack_load(base, lava, topper, reckless=True)
    return safe <= base.support < reckless


def _r_teeter(world: World) -> list[str]:
    volcano = world.get("volcano")
    if volcano.meters["load"] <= volcano.meters["support"]:
        return []
    sig = ("teeter", "volcano")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    volcano.meters["wobble"] += 1
    volcano.memes["risk"] += 1
    for kid in world.kids():
        kid.memes["suspense"] += 1
    return ["__wobble__"]


def _r_drip(world: World) -> list[str]:
    volcano = world.get("volcano")
    if volcano.meters["wobble"] < THRESHOLD:
        return []
    sig = ("drip", "volcano")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    volcano.meters["drip"] += 1
    return ["__drip__"]


def _r_helper_moves_topper(world: World) -> list[str]:
    volcano = world.get("volcano")
    suspect = world.get("suspect")
    topper = world.get("topper")
    if suspect.role != "helper":
        return []
    if volcano.meters["wobble"] < THRESHOLD or topper.attrs.get("location") != "top":
        return []
    sig = ("helper_move", suspect.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    topper.attrs["location"] = "plate"
    topper.meters["moved"] += 1
    volcano.meters["missing"] += 1
    suspect.memes["care"] += 1
    return ["__moved__"]


def _r_topper_falls(world: World) -> list[str]:
    volcano = world.get("volcano")
    suspect = world.get("suspect")
    topper = world.get("topper")
    if suspect.role != "pet":
        return []
    if volcano.meters["wobble"] < THRESHOLD or topper.attrs.get("location") != "top":
        return []
    sig = ("fall", "topper")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    topper.attrs["location"] = "floor"
    topper.meters["fallen"] += 1
    volcano.meters["missing"] += 1
    return ["__fallen__"]


def _r_pet_takes(world: World) -> list[str]:
    suspect = world.get("suspect")
    topper = world.get("topper")
    if suspect.role != "pet":
        return []
    if topper.attrs.get("location") != "floor":
        return []
    sig = ("pet_take", suspect.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    topper.attrs["location"] = "suspect"
    suspect.meters["snack_taken"] += 1
    return ["__taken__"]


CAUSAL_RULES: list[Rule] = [
    Rule(name="teeter", tag="physical", apply=_r_teeter),
    Rule(name="drip", tag="physical", apply=_r_drip),
    Rule(name="helper_move", tag="social", apply=_r_helper_moves_topper),
    Rule(name="topper_falls", tag="physical", apply=_r_topper_falls),
    Rule(name="pet_takes", tag="physical", apply=_r_pet_takes),
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
            if not sent.startswith("__"):
                world.say(sent)
    return produced


def culprit_of(params: "StoryParams") -> str:
    return SUSPECTS[params.suspect].role


def valid_combos() -> list[tuple[str, str, str]]:
    out: list[tuple[str, str, str]] = []
    for base_id, base in BASES.items():
        for lava_id, lava in LAVAS.items():
            for topper_id, topper in TOPPERS.items():
                if teeter_window(base, lava, topper):
                    out.append((base_id, lava_id, topper_id))
    return sorted(out)


def explain_rejection(base: Base, lava: Lava, topper: Topper) -> str:
    safe = careful_load(lava, topper)
    reckless = stack_load(base, lava, topper, reckless=True)
    if base.support < safe:
        return (
            f"(No story: {base.phrase} is too weak for {topper.phrase} and {lava.phrase}. "
            f"It would slump right away instead of giving foreshadowing and suspense.)"
        )
    if base.support >= reckless:
        return (
            f"(No story: {base.phrase} is sturdy enough even after the extra reckless layer. "
            f"Nothing would wobble, so there is no honest mystery to solve.)"
        )
    return "(No story: this combination does not fit the teetering-volcano constraint.)"


def predict_wobble(world: World) -> dict:
    sim = world.copy()
    propagate(sim, narrate=False)
    volcano = sim.get("volcano")
    topper = sim.get("topper")
    suspect = sim.get("suspect")
    return {
        "wobble": volcano.meters["wobble"],
        "drip": volcano.meters["drip"],
        "missing": volcano.meters["missing"],
        "topper_location": topper.attrs.get("location", ""),
        "culprit_role": suspect.role,
    }


def open_case(world: World, builder: Entity, sleuth: Entity, parent: Entity, base: Base, lava: Lava, topper: Topper) -> None:
    builder.memes["joy"] += 1
    sleuth.memes["joy"] += 1
    world.say(
        f"On snack day, {builder.id} and {sleuth.id} wanted to make a food volcano for everyone to share. "
        f"They built it on {base.phrase}, tucked in {lava.phrase} for the lava, and balanced {topper.phrase} on top."
    )
    world.say(
        f'"If we make it one layer taller, it will look like a real volcano," {builder.id} said.'
    )
    world.say(
        f'{sleuth.id} looked at the stack and whispered, "Maybe not too tall. We still want enough for everyone."'
    )
    world.say(
        f"{parent.label.capitalize()} set out the napkins and smiled. \"A sharing snack should stay easy to pass,\" {parent.pronoun()} said."
    )


def reckless_extra(world: World, builder: Entity, base: Base, lava: Lava, topper: Topper) -> None:
    volcano = world.get("volcano")
    builder.memes["pride"] += 1
    builder.memes["reckless"] += 1
    volcano.meters["support"] = float(base.support)
    volcano.meters["load"] = float(stack_load(base, lava, topper, reckless=True))
    world.say(
        f"But {builder.id} was feeling reckless. {builder.pronoun().capitalize()} added one more ring to the mountain and patted the top proudly."
    )


def foreshadow(world: World, sleuth: Entity, lava: Lava, topper: Topper) -> None:
    pred = predict_wobble(world)
    world.facts["predicted_wobble"] = pred["wobble"]
    world.facts["predicted_drip"] = pred["drip"]
    world.facts["predicted_missing"] = pred["missing"]
    world.say(
        f"Then came the first clue. {lava.drip_text}, and {topper.label} tipped just enough to make {sleuth.id} stop smiling."
    )
    world.say(
        f'"Did you see that?" {sleuth.id} asked. Nobody answered right away.'
    )


def pause_for_suspense(world: World, builder: Entity, sleuth: Entity, suspect: Entity) -> None:
    builder.memes["suspense"] += 1
    sleuth.memes["suspense"] += 1
    world.say(
        f"For one quiet moment, all they could hear was the little tick of sauce sliding down the side. "
        f"Even {suspect.label} seemed to be watching the table."
    )


def discover_loss(world: World, builder: Entity, sleuth: Entity, topper: Topper) -> None:
    world.say(
        f"When {builder.id} reached for the serving spoon, the top of the volcano looked wrong. {topper.phrase.capitalize()} was gone."
    )
    world.say(
        f'"Who took it?" {builder.id} gasped.'
    )
    world.say(
        f'{sleuth.id} put on {sleuth.pronoun("possessive")} best detective face. "This is the Case of the Missing Topper," {sleuth.pronoun()} said.'
    )


def investigate(world: World, builder: Entity, sleuth: Entity, suspect: Entity, topper: Topper) -> None:
    if suspect.role == "pet":
        world.say(
            f"They looked under the table first. There, by one chair leg, was {topper.clue_if_fallen}."
        )
        world.say(
            f"Next to it were {suspect.clue}. The room went still for a breath."
        )
    else:
        world.say(
            f"They looked beside the plates first. There, half-hidden by the napkins, was {suspect.clue}."
        )
        world.say(
            f"Nothing had been chewed. Nothing had been hidden far away. That made the mystery stranger, not smaller."
        )


def reveal_case(world: World, builder: Entity, sleuth: Entity, suspect: Entity, parent: Entity, topper: Topper) -> None:
    volcano = world.get("volcano")
    if suspect.role == "pet":
        world.say(
            f"Then {suspect.label} padded out with a happy face and a tiny smear near {suspect.pronoun('possessive')} mouth. "
            f"{suspect.reveal}"
        )
        world.say(
            f'"So {suspect.label} took it," {builder.id} said.'
        )
        world.say(
            f'"Yes," said {parent.label}, "but the real trouble started before that. The stack was wobbling because it had been built too high."'
        )
    else:
        world.say(
            f'"I moved it," {suspect.label} admitted. {suspect.reveal}'
        )
        world.say(
            f'{builder.id} blinked. "{topper.label.capitalize()} was not stolen?"'
        )
        world.say(
            f'"No," said {parent.label}. "It was rescued. The real trouble was the wobble. The mountain had been built too high."'
        )
    builder.memes["embarrassment"] += 1
    builder.memes["learning"] += 1
    sleuth.memes["relief"] += 1
    suspect.memes["relief"] += 1
    volcano.meters["case_solved"] += 1


def rebuild_for_sharing(world: World, builder: Entity, sleuth: Entity, suspect: Entity, parent: Entity, base: Base, lava: Lava, topper: Topper) -> None:
    volcano = world.get("volcano")
    volcano.meters["load"] = float(careful_load(lava, topper))
    volcano.meters["wobble"] = 0.0
    volcano.meters["drip"] = 0.0
    builder.memes["joy"] += 1
    builder.memes["reckless"] = 0.0
    builder.memes["care"] += 1
    sleuth.memes["joy"] += 1
    world.say(
        f"So they started over. This time {parent.label} helped them set the snack on {base.plate_fix}, lower and wider, with the lava in the middle instead of sliding down the side."
    )
    if suspect.role == "pet":
        world.say(
            f"{builder.id} broke a safe little piece for {suspect.label} in {suspect.pronoun('possessive')} bowl, far from the table, and everyone laughed."
        )
    else:
        world.say(
            f"{builder.id} thanked {suspect.label} for stopping the topple, and {suspect.pronoun()} placed {topper.phrase} neatly in the center."
        )
    world.say(
        f"Then the whole mystery turned back into a meal. {builder.id} passed the plates, {sleuth.id} spooned out the lava, and everybody got a fair share of the volcano."
    )
    world.say(
        f"The new mountain was not the tallest one ever made, but it stood steady, and that made it the best one to share."
    )


def tell(
    base: Base,
    lava: Lava,
    topper: Topper,
    suspect_cfg: Suspect,
    builder_name: str = "Nora",
    builder_gender: str = "girl",
    sleuth_name: str = "Ben",
    sleuth_gender: str = "boy",
    parent_type: str = "mother",
) -> World:
    world = World()
    builder = world.add(Entity(id=builder_name, kind="character", type=builder_gender, role="builder", label=builder_name, traits=["bold"]))
    sleuth = world.add(Entity(id=sleuth_name, kind="character", type=sleuth_gender, role="sleuth", label=sleuth_name, traits=["careful"]))
    parent_label = "Mom" if parent_type == "mother" else "Dad"
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, role="parent", label=parent_label))
    suspect = world.add(Entity(id="suspect", kind="character", type=suspect_cfg.type, role=suspect_cfg.role, label=suspect_cfg.label))
    volcano = world.add(Entity(id="volcano", type="food", label="volcano"))
    topper_ent = world.add(Entity(id="topper", type="food", label=topper.label, attrs={"location": "top"}))

    volcano.meters["support"] = float(base.support)
    volcano.meters["load"] = 0.0
    volcano.meters["wobble"] = 0.0
    volcano.meters["drip"] = 0.0
    volcano.meters["missing"] = 0.0
    volcano.meters["case_solved"] = 0.0
    topper_ent.meters["fallen"] = 0.0
    topper_ent.meters["moved"] = 0.0
    suspect.meters["snack_taken"] = 0.0
    world.facts["base"] = base
    world.facts["lava"] = lava
    world.facts["topper_cfg"] = topper
    world.facts["suspect_cfg"] = suspect_cfg

    open_case(world, builder, sleuth, parent, base, lava, topper)
    world.para()
    reckless_extra(world, builder, base, lava, topper)
    propagate(world, narrate=False)
    foreshadow(world, sleuth, lava, topper)
    pause_for_suspense(world, builder, sleuth, suspect)
    world.para()
    discover_loss(world, builder, sleuth, topper)
    investigate(world, builder, sleuth, suspect, topper)
    world.para()
    reveal_case(world, builder, sleuth, suspect, parent, topper)
    rebuild_for_sharing(world, builder, sleuth, suspect, parent, base, lava, topper)

    world.facts.update(
        builder=builder,
        sleuth=sleuth,
        parent=parent,
        suspect=suspect,
        volcano=volcano,
        topper=topper_ent,
        culprit=suspect.role,
        stolen=suspect.meters["snack_taken"] >= THRESHOLD,
        rescued=topper_ent.meters["moved"] >= THRESHOLD,
        fair_share=True,
    )
    return world


BASES = {
    "cracker_ring": Base(
        id="cracker_ring",
        label="cracker ring",
        phrase="a ring of round crackers",
        support=3,
        texture="dry and crisp",
        plate_fix="a wide blue plate",
        tags={"crackers", "plate"},
    ),
    "bread_bowl": Base(
        id="bread_bowl",
        label="bread bowl hill",
        phrase="a scooped bread-bowl hill",
        support=4,
        texture="soft but broad",
        plate_fix="a sturdy wooden board",
        tags={"bread", "plate"},
    ),
    "cucumber_hill": Base(
        id="cucumber_hill",
        label="cucumber hill",
        phrase="a hill of thick cucumber rounds",
        support=2,
        texture="cool and slippery",
        plate_fix="a shallow green tray",
        tags={"vegetable", "tray"},
    ),
}

LAVAS = {
    "cheese_dip": Lava(
        id="cheese_dip",
        label="cheese dip",
        phrase="warm cheese dip",
        wetness=1,
        color="golden",
        drip_text="A golden bead of cheese dip slipped from the crater and paused on one cracker edge",
        tags={"cheese", "dip"},
    ),
    "berry_yogurt": Lava(
        id="berry_yogurt",
        label="berry yogurt",
        phrase="bright berry yogurt",
        wetness=2,
        color="pink-red",
        drip_text="A bright pink-red line of yogurt crept down the side like lava looking for a path",
        tags={"berry", "yogurt"},
    ),
    "bean_salsa": Lava(
        id="bean_salsa",
        label="bean salsa",
        phrase="chunky bean salsa",
        wetness=1,
        color="red",
        drip_text="A shiny red drop of salsa slid lower and lower until it hung at the edge",
        tags={"beans", "salsa"},
    ),
}

TOPPERS = {
    "cheese_cube": Topper(
        id="cheese_cube",
        label="cheese cube",
        phrase="a cheese cube",
        weight=1,
        smell="savory",
        clue_if_fallen="a tiny yellow crumb",
        tags={"cheese"},
    ),
    "strawberry_cap": Topper(
        id="strawberry_cap",
        label="strawberry cap",
        phrase="a strawberry cap",
        weight=1,
        smell="sweet",
        clue_if_fallen="a red seed and a damp little smudge",
        tags={"strawberry", "fruit"},
    ),
    "grape_cluster": Topper(
        id="grape_cluster",
        label="grape cluster",
        phrase="a small grape cluster",
        weight=2,
        smell="sweet",
        clue_if_fallen="one lonely grape roll mark",
        tags={"grape", "fruit"},
    ),
}

SUSPECTS = {
    "puppy": Suspect(
        id="puppy",
        label="Pip the puppy",
        type="puppy",
        role="pet",
        clue="tiny pawprints in a berry-colored dot",
        reveal="The missing topper had landed low enough for a quick puppy snatch.",
        qa_text="Pip the puppy took the fallen topper after it slid from the wobbling volcano.",
        tags={"pet", "dog"},
    ),
    "little_sister": Suspect(
        id="little_sister",
        label="Mina",
        type="sister",
        role="helper",
        clue="a napkin folded around the missing topper on a side plate",
        reveal="\"It was leaning,\" she said. \"I did not want the whole thing to fall before anyone could share it.\"",
        qa_text="Mina moved the topper to a plate because she saw the volcano leaning and wanted to keep the snack safe for sharing.",
        tags={"family", "helper"},
    ),
    "little_brother": Suspect(
        id="little_brother",
        label="Ollie",
        type="brother",
        role="helper",
        clue="a careful side plate with the missing topper resting in the middle",
        reveal="\"I thought it would tumble,\" he said. \"I only moved the top so the rest could stay up.\"",
        qa_text="Ollie moved the topper to a side plate because he noticed the wobble and tried to stop a spill.",
        tags={"family", "helper"},
    ),
}

GIRL_NAMES = ["Nora", "Lily", "Mia", "Ava", "Ella", "June", "Zoe", "Anna", "Rose", "Lucy"]
BOY_NAMES = ["Ben", "Max", "Theo", "Sam", "Leo", "Finn", "Noah", "Eli", "Jack", "Owen"]


@dataclass
class StoryParams:
    base: str
    lava: str
    topper: str
    suspect: str
    builder: str
    builder_gender: str
    sleuth: str
    sleuth_gender: str
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


CURATED = [
    StoryParams(
        base="cracker_ring",
        lava="berry_yogurt",
        topper="cheese_cube",
        suspect="puppy",
        builder="Nora",
        builder_gender="girl",
        sleuth="Ben",
        sleuth_gender="boy",
        parent="mother",
    ),
    StoryParams(
        base="cucumber_hill",
        lava="cheese_dip",
        topper="strawberry_cap",
        suspect="little_sister",
        builder="Max",
        builder_gender="boy",
        sleuth="June",
        sleuth_gender="girl",
        parent="father",
    ),
    StoryParams(
        base="bread_bowl",
        lava="berry_yogurt",
        topper="grape_cluster",
        suspect="little_brother",
        builder="Ava",
        builder_gender="girl",
        sleuth="Theo",
        sleuth_gender="boy",
        parent="mother",
    ),
    StoryParams(
        base="cracker_ring",
        lava="bean_salsa",
        topper="grape_cluster",
        suspect="puppy",
        builder="Leo",
        builder_gender="boy",
        sleuth="Mia",
        sleuth_gender="girl",
        parent="father",
    ),
]


KNOWLEDGE = {
    "volcano": [
        (
            "What is a volcano?",
            "A volcano is a mountain-shaped place where hot melted rock can come out. In a pretend snack volcano, children copy that shape with food instead of real lava."
        )
    ],
    "sharing": [
        (
            "What does sharing food mean?",
            "Sharing food means making sure everyone gets some and nobody grabs all the best bits. It helps snack time feel fair and friendly."
        )
    ],
    "reckless": [
        (
            "What does reckless mean?",
            "Reckless means doing something without stopping to think about what could go wrong. A reckless choice can turn a fun idea into a messy problem."
        )
    ],
    "pet": [
        (
            "Why do pets sometimes take food?",
            "Pets follow good smells and quick chances. If food falls low enough, a puppy may grab it before people notice."
        )
    ],
    "detective": [
        (
            "What does a detective do?",
            "A detective looks for clues, asks careful questions, and tries to find the true reason something happened. Good detectives notice small details."
        )
    ],
    "tray": [
        (
            "Why does a wide tray help wobbly food?",
            "A wide tray gives food more room and a steadier base. Lower, wider snacks are less likely to tip over than tall narrow ones."
        )
    ],
    "yogurt": [
        (
            "Why can yogurt slide down food towers?",
            "Yogurt is soft and slippery, so it can creep down a tall stack if the surface tilts. That is why drips can be an early clue."
        )
    ],
    "crackers": [
        (
            "Why can crackers crack under a heavy topping?",
            "Crackers are crisp, not strong like a plate. Too much weight on a small cracker stack can make it shift or break."
        )
    ],
}
KNOWLEDGE_ORDER = ["volcano", "sharing", "reckless", "detective", "pet", "tray", "yogurt", "crackers"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    builder = f["builder"]
    sleuth = f["sleuth"]
    suspect_cfg = f["suspect_cfg"]
    base = f["base"]
    lava = f["lava"]
    topper = f["topper_cfg"]
    return [
        f'Write a short whodunit story for a 3-to-5-year-old that includes the words "reckless", "food", and "volcano".',
        f"Tell a gentle mystery where {builder.id} builds a shared snack volcano on {base.phrase}, {sleuth.id} notices the first clues, and the missing {topper.label} is traced to {suspect_cfg.label}.",
        f"Write a child-facing story with foreshadowing, sharing, and suspense, where a reckless extra layer makes {lava.label} drip before the mystery is solved and the snack is rebuilt fairly.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    builder = f["builder"]
    sleuth = f["sleuth"]
    parent = f["parent"]
    suspect = f["suspect"]
    base = f["base"]
    lava = f["lava"]
    topper = f["topper_cfg"]
    culprit = f["culprit"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {builder.id} and {sleuth.id}, who make a snack-time food volcano, and {suspect.label}, who becomes part of the mystery."
        ),
        (
            "What was the first clue that something was wrong?",
            f"The first clue was the drip of {lava.label} and the little tip in the top of the volcano. Those signs showed the stack was not as steady as it looked."
        ),
        (
            f"Why did the volcano become a problem?",
            f"It became a problem because {builder.id} added one more layer in a reckless way, making the load too heavy for {base.phrase}. That extra height turned a sharing snack into a wobbly mystery."
        ),
    ]
    if culprit == "pet":
        qa.append(
            (
                f"Who took the missing {topper.label}?",
                f"{suspect.label} took it after the topper slid down from the wobbling volcano. The puppy was the one who grabbed it, but the deeper cause was the shaky stack."
            )
        )
    else:
        qa.append(
            (
                f"Who moved the missing {topper.label}, and why?",
                f"{suspect.label} moved it to a side plate after noticing the volcano leaning. {suspect.pronoun().capitalize()} was trying to stop a bigger spill so the food could still be shared."
            )
        )
    qa.append(
        (
            "How did they solve the mystery and the snack problem?",
            f"They looked at the clues, found the true reason the topper was gone, and then rebuilt the volcano lower on {base.plate_fix}. That steadier shape made it easy to pass around and share fairly."
        )
    )
    qa.append(
        (
            f"How did the story end?",
            f"It ended with the children serving the snack instead of guarding it. The final image shows the change: plates moving from hand to hand, lava being spooned out neatly, and everyone getting a fair share."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"volcano", "sharing", "reckless", "detective", "tray"}
    suspect_cfg = f["suspect_cfg"]
    if suspect_cfg.role == "pet":
        tags.add("pet")
    if f["lava"].id == "berry_yogurt":
        tags.add("yogurt")
    if f["base"].id == "cracker_ring":
        tags.add("crackers")
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
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
careful_load(L,T,W+G) :- wetness(L,W), weight(T,G).
reckless_load(L,T,W+G+R) :- wetness(L,W), weight(T,G), reckless_bonus(R).

teeter_window(B,L,T) :- support(B,S), careful_load(L,T,C), reckless_load(L,T,R),
                        C <= S, S < R.
valid(B,L,T) :- base(B), lava(L), topper(T), teeter_window(B,L,T).

culprit(pet)    :- chosen_suspect(S), pet(S).
culprit(helper) :- chosen_suspect(S), helper(S).

#show valid/3.
#show culprit/1.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for base_id, base in BASES.items():
        lines.append(asp.fact("base", base_id))
        lines.append(asp.fact("support", base_id, base.support))
    for lava_id, lava in LAVAS.items():
        lines.append(asp.fact("lava", lava_id))
        lines.append(asp.fact("wetness", lava_id, lava.wetness))
    for topper_id, topper in TOPPERS.items():
        lines.append(asp.fact("topper", topper_id))
        lines.append(asp.fact("weight", topper_id, topper.weight))
    for suspect_id, suspect in SUSPECTS.items():
        lines.append(asp.fact("suspect", suspect_id))
        if suspect.role == "pet":
            lines.append(asp.fact("pet", suspect_id))
        if suspect.role == "helper":
            lines.append(asp.fact("helper", suspect_id))
    lines.append(asp.fact("reckless_bonus", RECKLESS_BONUS))
    return "\n".join(lines)


def asp_program(extra: str = "") -> str:
    return f"{asp_facts()}\n{extra}\n{ASP_RULES}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program(""))
    return sorted(set(asp.atoms(model, "valid")))


def asp_culprit(suspect_id: str) -> str:
    import asp

    model = asp.one_model(asp_program(asp.fact("chosen_suspect", suspect_id)))
    atoms = asp.atoms(model, "culprit")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0

    clingo_valid = set(asp_valid_combos())
    python_valid = set(valid_combos())
    if clingo_valid == python_valid:
        print(f"OK: gate matches valid_combos() ({len(clingo_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_valid - python_valid:
            print("  only in clingo:", sorted(clingo_valid - python_valid))
        if python_valid - clingo_valid:
            print("  only in python:", sorted(python_valid - clingo_valid))

    bad_roles = []
    for suspect_id in SUSPECTS:
        if asp_culprit(suspect_id) != SUSPECTS[suspect_id].role:
            bad_roles.append((suspect_id, asp_culprit(suspect_id), SUSPECTS[suspect_id].role))
    if not bad_roles:
        print(f"OK: culprit model matches suspect roles ({len(SUSPECTS)} suspects).")
    else:
        rc = 1
        print("MISMATCH in culprit model:", bad_roles)

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("smoke test produced an empty story")
        emit(sample, trace=False, qa=False, header="### smoke test")
        print("OK: generate/emit smoke test passed.")
    except Exception as err:  # pragma: no cover - verify path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a food volcano whodunit with foreshadowing, sharing, and suspense."
    )
    ap.add_argument("--base", choices=BASES)
    ap.add_argument("--lava", choices=LAVAS)
    ap.add_argument("--topper", choices=TOPPERS)
    ap.add_argument("--suspect", choices=SUSPECTS)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP twin and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_kid(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.base and args.lava and args.topper:
        base = BASES[args.base]
        lava = LAVAS[args.lava]
        topper = TOPPERS[args.topper]
        if not teeter_window(base, lava, topper):
            raise StoryError(explain_rejection(base, lava, topper))

    combos = [
        combo
        for combo in valid_combos()
        if (args.base is None or combo[0] == args.base)
        and (args.lava is None or combo[1] == args.lava)
        and (args.topper is None or combo[2] == args.topper)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    base_id, lava_id, topper_id = rng.choice(sorted(combos))
    builder, builder_gender = _pick_kid(rng)
    sleuth, sleuth_gender = _pick_kid(rng, avoid=builder)
    suspect = args.suspect or rng.choice(sorted(SUSPECTS))
    parent = args.parent or rng.choice(["mother", "father"])

    return StoryParams(
        base=base_id,
        lava=lava_id,
        topper=topper_id,
        suspect=suspect,
        builder=builder,
        builder_gender=builder_gender,
        sleuth=sleuth,
        sleuth_gender=sleuth_gender,
        parent=parent,
    )


def generate(params: StoryParams) -> StorySample:
    if params.base not in BASES:
        raise StoryError(f"(Unknown base: {params.base})")
    if params.lava not in LAVAS:
        raise StoryError(f"(Unknown lava: {params.lava})")
    if params.topper not in TOPPERS:
        raise StoryError(f"(Unknown topper: {params.topper})")
    if params.suspect not in SUSPECTS:
        raise StoryError(f"(Unknown suspect: {params.suspect})")
    if params.parent not in {"mother", "father"}:
        raise StoryError(f"(Unknown parent type: {params.parent})")

    base = BASES[params.base]
    lava = LAVAS[params.lava]
    topper = TOPPERS[params.topper]
    suspect_cfg = SUSPECTS[params.suspect]
    if not teeter_window(base, lava, topper):
        raise StoryError(explain_rejection(base, lava, topper))

    world = tell(
        base=base,
        lava=lava,
        topper=topper,
        suspect_cfg=suspect_cfg,
        builder_name=params.builder,
        builder_gender=params.builder_gender,
        sleuth_name=params.sleuth,
        sleuth_gender=params.sleuth_gender,
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
        print(asp_program(""))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (base, lava, topper) combos:\n")
        for base_id, lava_id, topper_id in combos:
            print(f"  {base_id:14} {lava_id:12} {topper_id}")
        print("\nculprit roles:")
        for suspect_id in sorted(SUSPECTS):
            print(f"  {suspect_id:14} -> {asp_culprit(suspect_id)}")
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
            header = f"### {p.builder} & {p.sleuth}: {p.base}/{p.lava}/{p.topper} ({p.suspect})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
