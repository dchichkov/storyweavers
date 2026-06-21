#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/serum_compromise_conflict_heartwarming.py
====================================================================

A standalone story world about two children caring for a droopy magical plant.
One child wants to pour in a whole bottle of serum at once. The other worries
that too much will hurt the plant. A gentle grown-up helps them face the
conflict and find a compromise: one careful drop of the right serum, plus the
right kind of ordinary care.

The world model enforces reasonableness:

- a plant only gets one of the ailments it can plausibly have
- only the matching serum can help that ailment
- the helping step must suit the ailment too
- explicit invalid choices raise StoryError with a readable explanation

Run it
------
    python storyworlds/worlds/gpt-5.4/serum_compromise_conflict_heartwarming.py
    python storyworlds/worlds/gpt-5.4/serum_compromise_conflict_heartwarming.py --all
    python storyworlds/worlds/gpt-5.4/serum_compromise_conflict_heartwarming.py --qa
    python storyworlds/worlds/gpt-5.4/serum_compromise_conflict_heartwarming.py --trace --seed 7
    python storyworlds/worlds/gpt-5.4/serum_compromise_conflict_heartwarming.py --verify
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
    phrase: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
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
            "grandmother": "grandma",
            "grandfather": "grandpa",
            "mother": "mom",
            "father": "dad",
            "aunt": "aunt",
            "uncle": "uncle",
        }.get(self.type, self.type)


@dataclass
class Setting:
    id: str
    place: str
    detail: str
    warm_end: str
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
class Plant:
    id: str
    label: str
    phrase: str
    nickname: str
    ailments: set[str] = field(default_factory=set)
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
class Problem:
    id: str
    sign: str
    worry: str
    need: str
    helper_family: str
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
class Serum:
    id: str
    label: str
    phrase: str
    fixes: set[str] = field(default_factory=set)
    color: str = ""
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
class Helper:
    id: str
    label: str
    phrase: str
    helps: set[str] = field(default_factory=set)
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

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"impulsive", "careful"}]

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


def _r_conflict(world: World) -> list[str]:
    a = world.get("kid_a")
    b = world.get("kid_b")
    if a.memes["push"] < THRESHOLD or b.memes["worry"] < THRESHOLD:
        return []
    sig = ("conflict",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    a.memes["conflict"] += 1
    b.memes["conflict"] += 1
    return ["__conflict__"]


def _r_burn(world: World) -> list[str]:
    plant = world.get("plant")
    if plant.meters["overdose"] < THRESHOLD:
        return []
    sig = ("burn",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    plant.meters["singed"] += 1
    plant.meters["droop"] += 1
    for kid in world.kids():
        kid.memes["guilt"] += 1
    return ["__burn__"]


def _r_heal(world: World) -> list[str]:
    plant = world.get("plant")
    if plant.meters["matched_serum"] < THRESHOLD or plant.meters["helper_done"] < THRESHOLD:
        return []
    if plant.meters["singed"] >= THRESHOLD:
        return []
    sig = ("heal",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    plant.meters["recovered"] += 1
    plant.meters["bloom"] += 1
    for kid in world.kids():
        kid.memes["relief"] += 1
    return ["__heal__"]


CAUSAL_RULES = [
    Rule(name="conflict", tag="social", apply=_r_conflict),
    Rule(name="burn", tag="physical", apply=_r_burn),
    Rule(name="heal", tag="physical", apply=_r_heal),
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
        for s in produced:
            world.say(s)
    return produced


def problem_fits(plant: Plant, problem: Problem) -> bool:
    return problem.id in plant.ailments


def serum_fits(problem: Problem, serum: Serum) -> bool:
    return problem.id in serum.fixes


def helper_fits(problem: Problem, helper: Helper) -> bool:
    return problem.id in helper.helps


def valid_combos() -> list[tuple[str, str, str, str, str]]:
    combos: list[tuple[str, str, str, str, str]] = []
    for setting_id in SETTINGS:
        for plant_id, plant in PLANTS.items():
            for problem_id, problem in PROBLEMS.items():
                if not problem_fits(plant, problem):
                    continue
                for serum_id, serum in SERUMS.items():
                    if not serum_fits(problem, serum):
                        continue
                    for helper_id, helper in HELPERS.items():
                        if helper_fits(problem, helper):
                            combos.append((setting_id, plant_id, problem_id, serum_id, helper_id))
    return combos


def explain_combo(plant: Plant, problem: Problem, serum: Serum, helper: Helper) -> str:
    if not problem_fits(plant, problem):
        return (
            f"(No story: {plant.phrase} does not usually have {problem.sign}. "
            f"Pick a problem that suits this plant.)"
        )
    if not serum_fits(problem, serum):
        return (
            f"(No story: {serum.label} is not the right serum for {problem.sign}. "
            f"It would not honestly help this problem.)"
        )
    if not helper_fits(problem, helper):
        return (
            f"(No story: {helper.label} does not give the kind of help this plant needs. "
            f"The compromise must pair the serum with the right care step.)"
        )
    return "(No story: this combination does not make sense in the world.)"


def predict_recovery(world: World, problem: Problem, serum: Serum, helper: Helper, mode: str) -> dict:
    sim = world.copy()
    plant = sim.get("plant")
    if mode == "compromise":
        plant.meters["matched_serum"] += 1
        plant.meters["helper_done"] += 1
    else:
        plant.meters["overdose"] += 1
        plant.meters["matched_serum"] += 1
    propagate(sim, narrate=False)
    return {
        "recovered": plant.meters["recovered"] >= THRESHOLD,
        "singed": plant.meters["singed"] >= THRESHOLD,
    }


def introduce(world: World, a: Entity, b: Entity, grown: Entity, plant: Entity, plant_cfg: Plant) -> None:
    for kid in (a, b):
        kid.memes["care"] += 1
    world.say(
        f"After breakfast, {a.id} and {b.id} went to {world.setting.place}, where "
        f"{world.setting.detail}"
    )
    world.say(
        f"On the middle shelf stood {plant_cfg.phrase}. The children called {plant.pronoun('object')} "
        f"{plant_cfg.nickname}, and they checked on {plant.pronoun('object')} every day with {grown.label_word}."
    )


def notice(world: World, a: Entity, b: Entity, plant_cfg: Plant, problem: Problem) -> None:
    plant = world.get("plant")
    plant.meters["trouble"] += 1
    a.memes["worry"] += 1
    b.memes["worry"] += 1
    world.say(
        f"That morning, though, {plant_cfg.nickname} did not look lively. {problem.sign.capitalize()}, "
        f"and {a.id} felt a little twist of worry."
    )
    world.say(
        f'"Oh no," {b.id} whispered. "It looks like {plant_cfg.nickname} needs help."'
    )


def propose_rush(world: World, a: Entity, serum: Serum) -> None:
    a.memes["push"] += 1
    world.say(
        f'{a.id} spotted {serum.phrase} on the potting table and reached for it at once. '
        f'"If one drop helps, a big splash will help faster," {a.pronoun()} said.'
    )


def caution(world: World, b: Entity, a: Entity, plant_cfg: Plant, serum: Serum, helper: Helper, problem: Problem) -> None:
    pred = predict_recovery(world, problem, serum, helper, mode="rush")
    world.facts["pred_rush_singed"] = pred["singed"]
    b.memes["worry"] += 1
    propagate(world, narrate=False)
    extra = " Too much serum can sting instead of soothe." if pred["singed"] else ""
    world.say(
        f'{b.id} put both hands around the bottle and gently pulled it down. '
        f'"Please do not pour all the serum on {plant_cfg.nickname}," {b.pronoun()} said.{extra}'
    )


def grownup_steps_in(world: World, grown: Entity, problem: Problem, serum: Serum, helper: Helper) -> None:
    pred = predict_recovery(world, problem, serum, helper, mode="compromise")
    world.facts["pred_compromise_recovered"] = pred["recovered"]
    world.say(
        f"{grown.label_word.capitalize()} came over, knelt beside the shelf, and looked from one child to the other."
    )
    world.say(
        f'"I can hear the conflict in both your voices," {grown.pronoun()} said softly. '
        f'"You both want to help. Let us make a compromise: one careful drop of the serum, '
        f"and then we {helper.action}."
    )


def accept_compromise(world: World, a: Entity, b: Entity, plant_cfg: Plant, serum: Serum, helper: Helper) -> None:
    plant = world.get("plant")
    for kid in (a, b):
        kid.memes["relief"] += 1
        kid.memes["love"] += 1
        kid.memes["conflict"] = 0.0
    plant.meters["matched_serum"] += 1
    plant.meters["helper_done"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{a.id} let out a breath and nodded. {b.id} nodded too."
    )
    world.say(
        f"Together they touched one shining {serum.color} drop to the soil, and then they {helper.action}. "
        f"No one hurried now. Their hands worked side by side."
    )
    if plant.meters["recovered"] >= THRESHOLD:
        world.say(
            f"By supper time, {plant_cfg.nickname} was already standing a little taller, as if the plant could feel the kindness in the room."
        )


def rush_anyway(world: World, a: Entity, b: Entity, plant_cfg: Plant, serum: Serum, helper: Helper, grown: Entity) -> None:
    plant = world.get("plant")
    a.memes["regret"] += 1
    plant.meters["overdose"] += 1
    plant.meters["matched_serum"] += 1
    propagate(world, narrate=False)
    world.say(
        f"But worry made {a.id} quick instead of careful. Before anyone could stop {a.pronoun('object')}, "
        f"{a.pronoun()} tipped the bottle, and too much serum splashed into the pot."
    )
    if plant.meters["singed"] >= THRESHOLD:
        world.say(
            f"A sharp little smell rose up. One leaf curled at the edge, and {plant_cfg.nickname} drooped even more."
        )
    world.say(
        f"{a.id}'s face crumpled. {b.id} was not angry now, only sad."
    )
    world.say(
        f'{grown.label_word.capitalize()} put an arm around both children. '
        f'"The plant still needs us," {grown.pronoun()} said. "Now we will help gently."'
    )
    plant.meters["helper_done"] += 1
    world.say(
        f"They cleaned the rim of the pot, and then they {helper.action}. {a.id} whispered sorry to {plant_cfg.nickname}."
    )


def apology_and_close(world: World, a: Entity, b: Entity, grown: Entity, plant_cfg: Plant, choice: str) -> None:
    plant = world.get("plant")
    world.para()
    if choice == "compromise":
        a.memes["trust"] += 1
        b.memes["trust"] += 1
        world.say(
            f"That evening, {a.id} leaned against {b.id}, and {b.id} leaned back."
        )
        world.say(
            f'"You were trying to help fast," {b.id} said. "And you were trying to help right," {a.id} answered. '
            f"After that, they smiled."
        )
        world.say(
            f"On the shelf, {plant_cfg.nickname} lifted a fresh green tip toward the window. {world.setting.warm_end}"
        )
    else:
        a.memes["love"] += 1
        b.memes["love"] += 1
        a.memes["relief"] += 1
        b.memes["relief"] += 1
        a.memes["conflict"] = 0.0
        b.memes["conflict"] = 0.0
        plant.meters["recovered_later"] += 1
        world.say(
            f'"I wanted to fix everything all at once," {a.id} said in a shaky voice.'
        )
        world.say(
            f'{b.id} squeezed {a.pronoun("possessive")} hand. "{grown.label_word.capitalize()} was right," '
            f'{b.pronoun()} said. "Small care can be strong care."'
        )
        world.say(
            f"The next morning, the singed leaf was still there, but beside it a tiny new bud had opened. "
            f"{plant_cfg.nickname} was not perfect, yet it was trying again, and so were they."
        )
@dataclass
class StoryParams:
    setting: str
    plant: str
    problem: str
    serum: str
    helper: str
    choice: str
    child_a: str
    child_a_gender: str
    child_b: str
    child_b_gender: str
    grownup: str
    relation: str = "siblings"
    trait_a: str = "eager"
    trait_b: str = "careful"
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
    "serum": [
        (
            "What is a serum for a plant?",
            "A serum is a special liquid made to help with one problem. It only works well when it is the right serum and only a little is used."
        )
    ],
    "roots": [
        (
            "What do roots do for a plant?",
            "Roots drink in water and hold the plant steady in the soil. If the roots are weak, the whole plant can droop."
        )
    ],
    "leaves": [
        (
            "Why are leaves important?",
            "Leaves help a plant catch light and make food. When leaves look pale, the plant may need gentle care."
        )
    ],
    "stem": [
        (
            "What does a stem do?",
            "A stem helps hold leaves and flowers up. If a stem bends too much, the plant may need support."
        )
    ],
    "watering": [
        (
            "Why should you water a plant slowly?",
            "A slow drink gives the soil time to soak up the water. Dumping too much at once can make a mess and does not always help."
        )
    ],
    "mist": [
        (
            "Why might someone mist plant leaves?",
            "A soft mist can freshen delicate leaves without pushing them around. Gentle care is often better than rough care."
        )
    ],
    "support": [
        (
            "Why would a plant need a stake or ribbon?",
            "A small stake and a soft tie help a bent stem stand up safely. The tie must be gentle so it does not hurt the plant."
        )
    ],
    "compromise": [
        (
            "What is a compromise?",
            "A compromise is a plan that listens to more than one person's worry or wish. It helps people solve a conflict together instead of fighting to win."
        )
    ],
}
KNOWLEDGE_ORDER = ["serum", "roots", "leaves", "stem", "watering", "mist", "support", "compromise"]


def character_name(ent: Entity) -> str:
    return ent.attrs.get("name", ent.label or ent.id)


def generation_prompts(world: World) -> list[str]:
    a = world.facts["child_a"]
    b = world.facts["child_b"]
    plant_cfg = world.facts["plant_cfg"]
    serum = world.facts["serum"]
    helper = world.facts["helper"]
    problem = world.facts["problem"]
    return [
        f'Write a heartwarming story for a 3-to-5-year-old that includes the words "serum" and "compromise".',
        f"Tell a gentle conflict story where {character_name(a)} wants to use {serum.label} too quickly to help {plant_cfg.nickname}, but {character_name(b)} asks for careful help instead.",
        f"Write a cozy plant-care story in which two children disagree about how to fix {problem.worry}, and a grown-up helps them work together with {helper.label}.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    a = world.facts["child_a"]
    b = world.facts["child_b"]
    grown = world.facts["grownup"]
    plant_cfg = world.facts["plant_cfg"]
    problem = world.facts["problem"]
    serum = world.facts["serum"]
    helper = world.facts["helper"]
    choice = world.facts["choice"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {character_name(a)} and {character_name(b)}, two children caring for {plant_cfg.nickname}, with help from their {grown.label_word}. They all wanted the little plant to feel better."
        ),
        (
            f"What was wrong with {plant_cfg.nickname}?",
            f"{plant_cfg.nickname} looked unwell because {problem.sign}. That is what made the children hurry to help."
        ),
        (
            f"Why did {character_name(a)} and {character_name(b)} argue?",
            f"They had a conflict because {character_name(a)} wanted to use the serum fast, while {character_name(b)} worried that too much could hurt the plant. Both children were trying to help, but they disagreed about how."
        ),
    ]
    if choice == "compromise":
        qa.extend([
            (
                "What was the compromise?",
                f"The compromise was to use one careful drop of {serum.label} and then {helper.action}. That plan mixed quick help with gentle help, so both children could take part."
            ),
            (
                f"Why did the compromise work?",
                f"It worked because the serum matched the plant's problem and the extra care matched it too. Instead of rushing, the children gave {plant_cfg.nickname} the kind of help it really needed."
            ),
            (
                "How did the story end?",
                f"The story ended warmly, with the children close together and {plant_cfg.nickname} lifting a fresh green tip. The ending shows that patient care changed both the plant and the mood in the room."
            ),
        ])
    else:
        qa.extend([
            (
                f"What happened when {character_name(a)} poured too much serum?",
                f"The plant was singed, and one leaf curled at the edge. That happened because too much serum was used all at once instead of carefully."
            ),
            (
                "Did the children stay upset with each other?",
                f"No. After the mistake, the anger melted into sadness and then into kindness, because they still wanted to help together. By the next morning, a new bud showed that careful love could still matter."
            ),
            (
                "What did they learn?",
                f"They learned that small care can be strong care. The lesson came from seeing that a hurried fix made the problem worse, but gentle help gave the plant another chance."
            ),
        ])
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = {"serum", "compromise"}
    problem = world.facts["problem"]
    serum = world.facts["serum"]
    helper = world.facts["helper"]
    tags |= set(problem.tags)
    tags |= set(serum.tags)
    tags |= set(helper.tags)
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
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:8} ({ent.type:11}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="sunroom",
        plant="moonflower",
        problem="sleepy_roots",
        serum="root_serum",
        helper="watering_can",
        choice="compromise",
        child_a="Lina",
        child_a_gender="girl",
        child_b="Owen",
        child_b_gender="boy",
        grownup="grandmother",
        relation="siblings",
        trait_a="eager",
        trait_b="careful",
    ),
    StoryParams(
        setting="greenhouse",
        plant="fern",
        problem="pale_leaves",
        serum="leaf_serum",
        helper="mister",
        choice="compromise",
        child_a="Maya",
        child_a_gender="girl",
        child_b="Theo",
        child_b_gender="boy",
        grownup="grandfather",
        relation="cousins",
        trait_a="hopeful",
        trait_b="gentle",
    ),
    StoryParams(
        setting="kitchen",
        plant="strawberry",
        problem="bent_stem",
        serum="stem_serum",
        helper="ribbon_tie",
        choice="rush",
        child_a="Ben",
        child_a_gender="boy",
        child_b="Ruby",
        child_b_gender="girl",
        grownup="mother",
        relation="siblings",
        trait_a="quick",
        trait_b="steady",
    ),
    StoryParams(
        setting="sunroom",
        plant="moonflower",
        problem="pale_leaves",
        serum="leaf_serum",
        helper="mister",
        choice="rush",
        child_a="Ella",
        child_a_gender="girl",
        child_b="Finn",
        child_b_gender="boy",
        grownup="aunt",
        relation="friends",
        trait_a="bright",
        trait_b="thoughtful",
    ),
]


ASP_RULES = r"""
valid(S, P, Pr, Se, H) :- setting(S), plant(P), problem(Pr), serum(Se), helper(H),
                          plant_has(P, Pr), serum_fixes(Se, Pr), helper_helps(H, Pr).

outcome(healed) :- chosen_choice(compromise).
outcome(singed) :- chosen_choice(rush).

#show valid/5.
#show outcome/1.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for pid, plant in PLANTS.items():
        lines.append(asp.fact("plant", pid))
        for pr in sorted(plant.ailments):
            lines.append(asp.fact("plant_has", pid, pr))
    for prid in PROBLEMS:
        lines.append(asp.fact("problem", prid))
    for sid, serum in SERUMS.items():
        lines.append(asp.fact("serum", sid))
        for pr in sorted(serum.fixes):
            lines.append(asp.fact("serum_fixes", sid, pr))
    for hid, helper in HELPERS.items():
        lines.append(asp.fact("helper", hid))
        for pr in sorted(helper.helps):
            lines.append(asp.fact("helper_helps", hid, pr))
    return "\n".join(lines)


def asp_program(extra: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(choice: str) -> str:
    import asp

    model = asp.one_model(asp_program(f"chosen_choice({choice})."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def outcome_of(params: StoryParams) -> str:
    return "healed" if params.choice == "compromise" else "singed"


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if py - cl:
            print("  only in python:", sorted(py - cl))
        if cl - py:
            print("  only in clingo:", sorted(cl - py))

    for choice in CHOICES:
        if asp_outcome(choice) != ("healed" if choice == "compromise" else "singed"):
            rc = 1
            print(f"MISMATCH in outcome for choice={choice}")
    if rc == 0:
        print("OK: outcome model matches Python outcome_of().")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("(Verify failed: smoke test generated an empty story.)")
        print("OK: smoke test story generation succeeded.")
    except Exception as exc:  # pragma: no cover - verification path
        print(f"VERIFY FAILED during smoke test: {exc}")
        return 1
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: a magical plant, a serum, a conflict, and a compromise."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--plant", choices=PLANTS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--serum", choices=SERUMS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--choice", choices=CHOICES)
    ap.add_argument("--grownup", choices=GROWNUPS)
    ap.add_argument("--relation", choices=["siblings", "cousins", "friends"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed")
    ap.add_argument("--all", action="store_true", help="render the curated set")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include prompts and Q&A")
    ap.add_argument("--json", action="store_true", help="emit JSON")
    ap.add_argument("--asp", action="store_true", help="list compatible combinations via clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def pick_child(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.plant and args.problem and args.serum and args.helper:
        plant = PLANTS[args.plant]
        problem = PROBLEMS[args.problem]
        serum = SERUMS[args.serum]
        helper = HELPERS[args.helper]
        if not (problem_fits(plant, problem) and serum_fits(problem, serum) and helper_fits(problem, helper)):
            raise StoryError(explain_combo(plant, problem, serum, helper))

    combos = [
        combo for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.plant is None or combo[1] == args.plant)
        and (args.problem is None or combo[2] == args.problem)
        and (args.serum is None or combo[3] == args.serum)
        and (args.helper is None or combo[4] == args.helper)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, plant_id, problem_id, serum_id, helper_id = rng.choice(sorted(combos))
    choice = args.choice or rng.choice(CHOICES)
    child_a, ga = pick_child(rng)
    child_b, gb = pick_child(rng, avoid=child_a)
    grownup = args.grownup or rng.choice(GROWNUPS)
    relation = args.relation or rng.choice(["siblings", "cousins", "friends"])
    trait_a = rng.choice(TRAITS_A)
    trait_b = rng.choice(TRAITS_B)
    return StoryParams(
        setting=setting_id,
        plant=plant_id,
        problem=problem_id,
        serum=serum_id,
        helper=helper_id,
        choice=choice,
        child_a=child_a,
        child_a_gender=ga,
        child_b=child_b,
        child_b_gender=gb,
        grownup=grownup,
        relation=relation,
        trait_a=trait_a,
        trait_b=trait_b,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Invalid setting: {params.setting})")
    if params.plant not in PLANTS:
        raise StoryError(f"(Invalid plant: {params.plant})")
    if params.problem not in PROBLEMS:
        raise StoryError(f"(Invalid problem: {params.problem})")
    if params.serum not in SERUMS:
        raise StoryError(f"(Invalid serum: {params.serum})")
    if params.helper not in HELPERS:
        raise StoryError(f"(Invalid helper: {params.helper})")
    if params.choice not in CHOICES:
        raise StoryError(f"(Invalid choice: {params.choice})")

    plant = PLANTS[params.plant]
    problem = PROBLEMS[params.problem]
    serum = SERUMS[params.serum]
    helper = HELPERS[params.helper]
    if not (problem_fits(plant, problem) and serum_fits(problem, serum) and helper_fits(problem, helper)):
        raise StoryError(explain_combo(plant, problem, serum, helper))

    world = tell(
        setting=SETTINGS[params.setting],
        plant_cfg=plant,
        problem=problem,
        serum=serum,
        helper=helper,
        choice=params.choice,
        child_a=params.child_a,
        child_a_gender=params.child_a_gender,
        child_b=params.child_b,
        child_b_gender=params.child_b_gender,
        grownup_type=params.grownup,
        relation=params.relation,
        trait_a=params.trait_a,
        trait_b=params.trait_b,
    )

    story = world.render().replace("kid_a", params.child_a).replace("kid_b", params.child_b)
    story = story.replace("kid_b", params.child_b)

    # Replace labels inserted through entity ids with display names.
    story = story.replace(world.get("kid_a").id, params.child_a)
    story = story.replace(world.get("kid_b").id, params.child_b)

    return StorySample(
        params=params,
        story=story,
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
        print(f"{len(combos)} compatible (setting, plant, problem, serum, helper) combos:\n")
        for setting_id, plant_id, problem_id, serum_id, helper_id in combos:
            print(f"  {setting_id:10} {plant_id:11} {problem_id:13} {serum_id:11} {helper_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
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
            header = (
                f"### {p.child_a} & {p.child_b}: {p.plant} / {p.problem} "
                f"({p.choice}, {p.setting})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")






def tell(
    setting: Setting,
    plant_cfg: Plant,
    problem: Problem,
    serum: Serum,
    helper: Helper,
    choice: str,
    child_a: str = "Lina",
    child_a_gender: str = "girl",
    child_b: str = "Owen",
    child_b_gender: str = "boy",
    grownup_type: str = "grandmother",
    relation: str = "siblings",
    trait_a: str = "eager",
    trait_b: str = "careful",
) -> World:
    world = World(setting)
    a = world.add(Entity(
        id="kid_a",
        kind="character",
        type=child_a_gender,
        label=child_a,
        role="impulsive",
        traits=[trait_a],
        attrs={"name": child_a, "relation": relation},
    ))
    b = world.add(Entity(
        id="kid_b",
        kind="character",
        type=child_b_gender,
        label=child_b,
        role="careful",
        traits=[trait_b],
        attrs={"name": child_b, "relation": relation},
    ))
    grown = world.add(Entity(
        id="grownup",
        kind="character",
        type=grownup_type,
        label="the grown-up",
        role="grownup",
    ))
    plant = world.add(Entity(
        id="plant",
        type="plant",
        label=plant_cfg.label,
        phrase=plant_cfg.phrase,
        tags=set(plant_cfg.tags),
    ))
    serum_ent = world.add(Entity(
        id="serum",
        type="tool",
        label=serum.label,
        phrase=serum.phrase,
        tags=set(serum.tags),
    ))
    helper_ent = world.add(Entity(
        id="helper",
        type="tool",
        label=helper.label,
        phrase=helper.phrase,
        tags=set(helper.tags),
    ))
    world.facts.update(
        child_a=a,
        child_b=b,
        grownup=grown,
        plant=plant,
        plant_cfg=plant_cfg,
        problem=problem,
        serum=serum,
        serum_ent=serum_ent,
        helper=helper,
        helper_ent=helper_ent,
        choice=choice,
        relation=relation,
        pred_rush_singed=False,
        pred_compromise_recovered=False,
    )

    introduce(world, a, b, grown, plant, plant_cfg)
    notice(world, a, b, plant_cfg, problem)

    world.para()
    propose_rush(world, a, serum)
    caution(world, b, a, plant_cfg, serum, helper, problem)
    grownup_steps_in(world, grown, problem, serum, helper)

    world.para()
    if choice == "compromise":
        accept_compromise(world, a, b, plant_cfg, serum, helper)
    else:
        rush_anyway(world, a, b, plant_cfg, serum, helper, grown)

    apology_and_close(world, a, b, grown, plant_cfg, choice)

    world.facts.update(
        conflict_happened=a.memes["push"] >= THRESHOLD and b.memes["worry"] >= THRESHOLD,
        singed=plant.meters["singed"] >= THRESHOLD,
        healed=plant.meters["recovered"] >= THRESHOLD,
        later_bud=plant.meters["recovered_later"] >= THRESHOLD,
        outcome="healed" if choice == "compromise" else "singed",
    )
    return world


SETTINGS = {
    "sunroom": Setting(
        id="sunroom",
        place="the little sunroom",
        detail="glass panes warmed the floor in pale gold squares and every shelf smelled softly of leaves",
        warm_end="The children watched in silence for a moment, then tucked themselves under the same blanket on the window seat.",
    ),
    "greenhouse": Setting(
        id="greenhouse",
        place="the backyard greenhouse",
        detail="dew still shone on the glass and the air felt warm enough for secrets",
        warm_end="Outside, evening birds called, and inside the greenhouse everything felt gentler than before.",
    ),
    "kitchen": Setting(
        id="kitchen window",
        place="the kitchen window",
        detail="the jars and teacups by the sill made the whole corner look like a tiny garden town",
        warm_end="Soon the window looked less like a place for worry and more like a place for patient love.",
    ),
}

PLANTS = {
    "moonflower": Plant(
        id="moonflower",
        label="moonflower",
        phrase="a moonflower in a blue clay pot",
        nickname="Moonie",
        ailments={"sleepy_roots", "pale_leaves"},
        tags={"plant", "moonflower"},
    ),
    "strawberry": Plant(
        id="strawberry",
        label="strawberry plant",
        phrase="a strawberry plant with three tiny white blossoms",
        nickname="Berry-Bell",
        ailments={"sleepy_roots", "bent_stem"},
        tags={"plant", "strawberry"},
    ),
    "fern": Plant(
        id="fern",
        label="fern",
        phrase="a feathery fern in a basket pot",
        nickname="Frill",
        ailments={"pale_leaves"},
        tags={"plant", "fern"},
    ),
}

PROBLEMS = {
    "sleepy_roots": Problem(
        id="sleepy_roots",
        sign="the stems hung low and the soil looked tired",
        worry="drooping low",
        need="a little root help and a careful drink",
        helper_family="water",
        tags={"roots", "watering"},
    ),
    "pale_leaves": Problem(
        id="pale_leaves",
        sign="the leaves had gone pale, almost the color of paper",
        worry="pale leaves",
        need="leaf help and soft mist",
        helper_family="mist",
        tags={"leaves", "mist"},
    ),
    "bent_stem": Problem(
        id="bent_stem",
        sign="one stem leaned sideways as if it had forgotten how to stand",
        worry="a bent stem",
        need="stem help and a gentle tie",
        helper_family="support",
        tags={"stem", "support"},
    ),
}

SERUMS = {
    "root_serum": Serum(
        id="root_serum",
        label="root serum",
        phrase="a bottle of root serum",
        fixes={"sleepy_roots"},
        color="amber",
        tags={"serum", "roots"},
    ),
    "leaf_serum": Serum(
        id="leaf_serum",
        label="leaf serum",
        phrase="a bottle of leaf serum",
        fixes={"pale_leaves"},
        color="green",
        tags={"serum", "leaves"},
    ),
    "stem_serum": Serum(
        id="stem_serum",
        label="stem serum",
        phrase="a bottle of stem serum",
        fixes={"bent_stem"},
        color="silver",
        tags={"serum", "stem"},
    ),
}

HELPERS = {
    "watering_can": Helper(
        id="watering_can",
        label="watering can",
        phrase="a little brass watering can",
        helps={"sleepy_roots"},
        action="gave the pot a slow drink from the watering can",
        tags={"watering_can", "watering"},
    ),
    "mister": Helper(
        id="mister",
        label="plant mister",
        phrase="a glass plant mister",
        helps={"pale_leaves"},
        action="mist the leaves until they gleamed softly",
        tags={"mister", "mist"},
    ),
    "ribbon_tie": Helper(
        id="ribbon_tie",
        label="soft ribbon tie",
        phrase="a soft ribbon tie and a slim stake",
        helps={"bent_stem"},
        action="tied the stem to a slim stake with the soft ribbon",
        tags={"ribbon", "support"},
    ),
}

GIRL_NAMES = ["Lina", "Maya", "Nora", "Ava", "Lucy", "Ella", "Ruby", "Ivy"]
BOY_NAMES = ["Owen", "Theo", "Ben", "Eli", "Milo", "Finn", "Noah", "Sam"]
TRAITS_A = ["eager", "quick", "hopeful", "bright"]
TRAITS_B = ["careful", "gentle", "thoughtful", "steady"]
CHOICES = ["compromise", "rush"]
GROWNUPS = ["grandmother", "grandfather", "mother", "father", "aunt", "uncle"]

if __name__ == "__main__":
    main()
