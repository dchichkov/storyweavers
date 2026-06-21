#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/gulp_paw_mystery_to_solve_dialogue_bad.py
====================================================================

A standalone storyworld for a small nursery-rhyme mystery: a cooling treat goes
missing, a child finds a paw print, and the trail leads toward a dark hiding
place. The world can tell a safer "solved with help" version or a cautionary bad
ending where the child follows the trail alone and loses both the treat and a
beloved toy.

Run it
------
    python storyworlds/worlds/gpt-5.4/gulp_paw_mystery_to_solve_dialogue_bad.py
    python storyworlds/worlds/gpt-5.4/gulp_paw_mystery_to_solve_dialogue_bad.py --plan alone
    python storyworlds/worlds/gpt-5.4/gulp_paw_mystery_to_solve_dialogue_bad.py --all
    python storyworlds/worlds/gpt-5.4/gulp_paw_mystery_to_solve_dialogue_bad.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/gulp_paw_mystery_to_solve_dialogue_bad.py --trace
    python storyworlds/worlds/gpt-5.4/gulp_paw_mystery_to_solve_dialogue_bad.py --asp
    python storyworlds/worlds/gpt-5.4/gulp_paw_mystery_to_solve_dialogue_bad.py --verify
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
BRAVERY_INIT = 2
SAFE_PLAN = "with_helper"


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
            "grandmother": "granny",
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
    label: str
    opening: str
    window: str
    yard: str
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
class Treat:
    id: str
    label: str
    phrase: str
    cooling: str
    crumbs: str
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
class Pet:
    id: str
    label: str
    sound: str
    paw_size: int
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
class Culprit:
    id: str
    label: str
    sound: str
    paw_size: int
    swift: int
    hides: set[str] = field(default_factory=set)
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
class Hideout:
    id: str
    label: str
    phrase: str
    dark: int
    warning: str
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
class Plan:
    id: str
    label: str
    with_helper: bool
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


def _r_paw_clue(world: World) -> list[str]:
    treat = world.get("treat")
    child = world.get("child")
    pet = world.get("pet")
    culprit = world.get("culprit")
    if treat.meters["missing"] < THRESHOLD:
        return []
    sig = ("paw_clue",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["curiosity"] += 1
    child.memes["suspicion"] += 1
    world.facts["paw_size_seen"] = culprit.attrs["paw_size"]
    world.facts["first_suspect"] = pet.label
    world.facts["clue_text"] = "a floury paw print by the sill"
    return [
        f"By the sill lay a floury paw print, not little, not neat, with {treat.crumbs} in a crooked row."
    ]


def _r_compare_paws(world: World) -> list[str]:
    child = world.get("child")
    pet = world.get("pet")
    culprit = world.get("culprit")
    if child.meters["compared_paws"] < THRESHOLD:
        return []
    sig = ("compare_paws",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    if pet.attrs["paw_size"] != culprit.attrs["paw_size"]:
        child.memes["doubt"] += 1
        pet.memes["relief"] += 1
        world.facts["pet_cleared"] = True
        return [
            f'"This paw is broader than {pet.label}\'s paw," said {child.id}. "So {pet.label} did not do it."'
        ]
    world.facts["pet_cleared"] = False
    return [
        f'"This paw is just the size of {pet.label}\'s paw," said {child.id}, though the crumbs still pointed out the door.'
    ]


def _r_dark_risk(world: World) -> list[str]:
    child = world.get("child")
    hide = world.get("hideout")
    if child.meters["searching_alone"] < THRESHOLD:
        return []
    sig = ("dark_risk",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    if hide.attrs["dark"] > 0:
        child.memes["fear"] += hide.attrs["dark"]
        hide.meters["danger"] += hide.attrs["dark"]
    return []


def _r_helper_recovery(world: World) -> list[str]:
    child = world.get("child")
    helper = world.get("helper")
    treat = world.get("treat")
    culprit = world.get("culprit")
    if child.meters["searching_with_helper"] < THRESHOLD:
        return []
    sig = ("helper_recovery",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    helper.memes["care"] += 1
    if culprit.meters["cornered"] >= THRESHOLD:
        treat.meters["found"] += 1
        treat.meters["missing"] = 0.0
    return []


CAUSAL_RULES = [
    Rule(name="paw_clue", tag="mystery", apply=_r_paw_clue),
    Rule(name="compare_paws", tag="mystery", apply=_r_compare_paws),
    Rule(name="dark_risk", tag="danger", apply=_r_dark_risk),
    Rule(name="helper_recovery", tag="resolution", apply=_r_helper_recovery),
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


def valid_hide(culprit: Culprit, hideout: Hideout, setting: Setting) -> bool:
    return hideout.id in setting.affords and hideout.id in culprit.hides


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for sid, setting in SETTINGS.items():
        for cid, culprit in CULPRITS.items():
            for hid, hideout in HIDEOUTS.items():
                if valid_hide(culprit, hideout, setting):
                    out.append((sid, cid, hid))
    return out


def danger_score(culprit: Culprit, hideout: Hideout, plan: Plan) -> int:
    if plan.with_helper:
        return 0
    return culprit.swift + hideout.dark


def outcome_of(params: "StoryParams") -> str:
    if params.plan == SAFE_PLAN:
        return "solved"
    culprit = CULPRITS[params.culprit]
    hideout = HIDEOUTS[params.hideout]
    if danger_score(culprit, hideout, PLANS[params.plan]) > BRAVERY_INIT:
        return "bad"
    return "solved_alone"


def explain_rejection(setting: Optional[Setting], culprit: Optional[Culprit], hideout: Optional[Hideout]) -> str:
    if setting and hideout and hideout.id not in setting.affords:
        return (
            f"(No story: {hideout.label} does not belong in {setting.label}. "
            f"Pick a hiding place that fits the setting.)"
        )
    if culprit and hideout and hideout.id not in culprit.hides:
        return (
            f"(No story: {culprit.label} would not sensibly hide in {hideout.label}. "
            f"Choose a hideout that matches the culprit.)"
        )
    return "(No valid combination matches the given options.)"


def predict_search(world: World, plan: Plan) -> dict:
    sim = world.copy()
    child = sim.get("child")
    culprit = sim.get("culprit")
    hideout = sim.get("hideout")
    if plan.with_helper:
        culprit.meters["cornered"] += 1
        child.meters["searching_with_helper"] += 1
    else:
        child.meters["searching_alone"] += 1
    propagate(sim, narrate=False)
    return {
        "danger": int(hideout.meters["danger"]),
        "fear": int(child.memes["fear"]),
        "found": sim.get("treat").meters["found"] >= THRESHOLD,
    }


def opening_beat(world: World, child: Entity, helper: Entity, treat_cfg: Treat) -> None:
    child.memes["joy"] += 1
    world.say(
        f"In {world.setting.label}, neat and slight, {world.setting.opening}."
    )
    world.say(
        f"{helper.label_word.capitalize()} set out {treat_cfg.phrase}, saying, "
        f'"Cool there, little {treat_cfg.label}, till supper calls tonight."'
    )
    world.say(
        f"{child.id} nodded, humming low, while dusk made {world.setting.window} glow."
    )


def vanish(world: World, child: Entity, treat_cfg: Treat) -> None:
    treat = world.get("treat")
    culprit = world.get("culprit")
    treat.meters["missing"] += 1
    culprit.meters["stole_treat"] += 1
    world.say(
        f"But when the kettle gave a hiss, the {treat_cfg.label} was gone from its cooling place."
    )
    world.say(
        f'"Oh dear," said {child.id}, "it cannot hop. Who took my little supper-top?"'
    )
    propagate(world, narrate=True)


def question_pet(world: World, child: Entity, pet: Entity) -> None:
    pet.memes["blamed"] += 1
    world.say(
        f'"{pet.label.capitalize()}, was it you?" asked {child.id}. "{pet.sound}," went {pet.label}, and {pet.pronoun()} tucked {pet.pronoun("possessive")} nose.'
    )
    world.say(
        f'{child.id} bent low beside the floor. "One paw print only—nothing more."'
    )


def compare_clue(world: World, child: Entity, pet: Entity) -> None:
    child.meters["compared_paws"] += 1
    propagate(world, narrate=True)
    if world.facts.get("pet_cleared"):
        child.memes["fairness"] += 1
        world.say(
            f'"Then someone else came padding through," said {child.id}. "{pet.label.capitalize()}, I was wrong of you."'
        )
    else:
        world.say(
            f'"It still might be you," said {child.id}, but the crumb trail tugged at the thought.'
        )


def choose_plan(world: World, child: Entity, helper: Entity, plan: Plan, hideout: Hideout) -> None:
    pred = predict_search(world, plan)
    world.facts["predicted_danger"] = pred["danger"]
    if plan.with_helper:
        world.say(
            f'"Granny, granny, come with me. The trail runs toward {hideout.phrase}," said {child.id}.'
        )
        world.say(
            f'"A mystery is best with two calm eyes," said {helper.label_word}.'
        )
    else:
        world.say(
            f'{child.id} gave a little gulp. "{helper.label_word.capitalize()} is busy. I can solve it by myself," {child.pronoun()} whispered.'
        )
        if pred["danger"] > 0:
            world.say(
                f'Yet {hideout.warning}, and the dark there felt thicker than a song.'
            )


def search_with_helper(world: World, child: Entity, helper: Entity, culprit: Entity,
                       treat_cfg: Treat, hideout: Hideout) -> None:
    culprit.meters["cornered"] += 1
    child.meters["searching_with_helper"] += 1
    propagate(world, narrate=False)
    world.say(
        f'Together they followed the crumbs to {hideout.phrase}, where two bright eyes blinked back.'
    )
    world.say(
        f'"Aha!" said {helper.label_word}. "There is our thief." {culprit.label.capitalize()} gave a startled "{culprit.sound}!"'
    )
    world.say(
        f'The {culprit.label} dropped the {treat_cfg.label}. It was nibbled at one side, but still there all the same.'
    )
    world.say(
        f'{child.id} clapped softly. "The paw print told the truth," {child.pronoun()} said.'
    )


def search_alone(world: World, child: Entity, culprit: Entity, pet: Entity,
                 treat_cfg: Treat, hideout: Hideout) -> None:
    child.meters["searching_alone"] += 1
    propagate(world, narrate=False)
    world.say(
        f'Alone went {child.id}, past the gate, following crumbs to {hideout.phrase}.'
    )
    world.say(
        f'Then {culprit.label} sprang from the dark with the last of the {treat_cfg.label} in {culprit.pronoun("possessive")} mouth.'
    )
    world.say(
        f'{child.id} gave a great gulp and stumbled back. In the fright, {child.pronoun("possessive")} rag doll fell into the weeds.'
    )
    world.say(
        f'"Wait!" cried {child.id}, but swift {culprit.label} vanished, supper lost and mystery only half-solved.'
    )
    child.meters["lost_toy"] += 1
    world.facts["lost_item"] = child.attrs["toy"]
    pet.memes["worry"] += 1


def safe_close(world: World, child: Entity, helper: Entity, treat_cfg: Treat) -> None:
    child.memes["relief"] += 1
    child.memes["lesson"] += 1
    helper.memes["care"] += 1
    world.say(
        f'Back by the warm lamplight, {helper.label_word} cut away the bitten bit and shared the rest.'
    )
    world.say(
        f'"Next time," said {helper.label_word}, "we solve dark riddles side by side."'
    )
    world.say(
        f'So the small house hummed, and the once-missing {treat_cfg.label} ended the night in little thankful bites.'
    )


def bad_close(world: World, child: Entity, helper: Entity, hideout: Hideout) -> None:
    child.memes["regret"] += 1
    child.memes["lesson"] += 1
    child.memes["fear"] += 1
    world.say(
        f'{helper.label_word.capitalize()} found {child.id} crying by the path, with empty hands and muddy shoes.'
    )
    world.say(
        f'"I saw whose paw it was," sobbed {child.id}, "but I went alone, and now the supper is gone and so is my {child.attrs["toy"]}."'
    )
    world.say(
        f'{helper.label_word.capitalize()} hugged {child.pronoun("object")} close. But the night stayed sad: the treat was eaten, the toy was lost, and nobody sang on the way back from {hideout.label}.'
    )


def tell(setting: Setting, treat_cfg: Treat, pet_cfg: Pet, culprit_cfg: Culprit,
         hideout_cfg: Hideout, plan_cfg: Plan, child_name: str = "Mabel",
         child_gender: str = "girl", helper_type: str = "grandmother",
         toy: str = "rag doll") -> World:
    world = World(setting)
    child = world.add(Entity(
        id=child_name,
        kind="character",
        type=child_gender,
        role="child",
        traits=["curious"],
        attrs={"toy": toy},
    ))
    helper = world.add(Entity(
        id="Helper",
        kind="character",
        type=helper_type,
        role="helper",
        label="the helper",
        attrs={},
    ))
    pet = world.add(Entity(
        id="pet",
        kind="character",
        type="animal",
        role="pet",
        label=pet_cfg.label,
        attrs={"paw_size": pet_cfg.paw_size},
    ))
    culprit = world.add(Entity(
        id="culprit",
        kind="character",
        type="animal",
        role="culprit",
        label=culprit_cfg.label,
        attrs={"paw_size": culprit_cfg.paw_size, "swift": culprit_cfg.swift},
    ))
    treat = world.add(Entity(
        id="treat",
        kind="thing",
        type="food",
        label=treat_cfg.label,
        attrs={},
    ))
    hideout = world.add(Entity(
        id="hideout",
        kind="thing",
        type="place",
        label=hideout_cfg.label,
        attrs={"dark": hideout_cfg.dark},
    ))

    child.memes["bravery"] = float(BRAVERY_INIT)
    child.memes["fear"] = 0.0
    child.memes["curiosity"] = 0.0
    child.memes["doubt"] = 0.0
    helper.memes["care"] = 0.0
    pet.memes["relief"] = 0.0
    treat.meters["missing"] = 0.0
    treat.meters["found"] = 0.0
    culprit.meters["cornered"] = 0.0
    hideout.meters["danger"] = 0.0
    child.meters["compared_paws"] = 0.0
    child.meters["searching_alone"] = 0.0
    child.meters["searching_with_helper"] = 0.0
    child.meters["lost_toy"] = 0.0

    world.facts.update(
        setting=setting,
        treat_cfg=treat_cfg,
        pet_cfg=pet_cfg,
        culprit_cfg=culprit_cfg,
        hideout_cfg=hideout_cfg,
        plan_cfg=plan_cfg,
        child=child,
        helper=helper,
        pet=pet,
        culprit=culprit,
        treat=treat,
        hideout=hideout,
        predicted_danger=0,
        pet_cleared=False,
        clue_text="",
        lost_item="",
    )

    opening_beat(world, child, helper, treat_cfg)
    world.para()
    vanish(world, child, treat_cfg)
    question_pet(world, child, pet)
    compare_clue(world, child, pet)
    world.para()
    choose_plan(world, child, helper, plan_cfg, hideout_cfg)
    if plan_cfg.with_helper:
        search_with_helper(world, child, helper, culprit, treat_cfg, hideout_cfg)
        world.para()
        safe_close(world, child, helper, treat_cfg)
        outcome = "solved"
    else:
        search_alone(world, child, culprit, pet, treat_cfg, hideout_cfg)
        world.para()
        bad_close(world, child, helper, hideout_cfg)
        outcome = "bad"

    world.facts.update(
        outcome=outcome,
        solved=treat.meters["found"] >= THRESHOLD or outcome == "solved",
        bad_ending=outcome == "bad",
    )
    return world


KNOWLEDGE = {
    "paw": [(
        "What is a paw print?",
        "A paw print is the mark an animal's foot leaves on the ground. It can help you tell that an animal walked there."
    )],
    "crumbs": [(
        "What are crumbs?",
        "Crumbs are tiny bits that fall from bread, cake, or a bun. A crumb trail can show where food was carried."
    )],
    "fox": [(
        "Why is a fox hard to catch?",
        "A fox moves quickly and quietly, so it can dart away before people get close. That is why grown-up help matters when something runs into the dark."
    )],
    "raccoon": [(
        "What does a raccoon use its paws for?",
        "A raccoon uses its front paws to grab and carry food. Those little paws can leave clear prints if they step in flour or mud."
    )],
    "badger": [(
        "Why might a badger leave a broad paw print?",
        "A badger has strong, broad feet for digging. That can make a larger paw mark than a house pet leaves."
    )],
    "dark": [(
        "Why is it harder to solve a mystery in the dark?",
        "In the dark, it is harder to see clues and harder to notice danger. A grown-up can help you look carefully and stay safe."
    )],
    "ask_help": [(
        "Why should a child ask a grown-up for help with a scary problem?",
        "A grown-up can see more, carry a light, and keep you safe. Asking for help is wise, not babyish."
    )],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    treat_cfg = f["treat_cfg"]
    pet_cfg = f["pet_cfg"]
    hideout_cfg = f["hideout_cfg"]
    if f["outcome"] == "bad":
        return [
            f'Write a nursery-rhyme-style mystery where a child finds a paw print after a missing {treat_cfg.label}, says "gulp," and follows the clue into the dark alone.',
            f"Tell a rhyming story with dialogue where {child.id} wrongly suspects {pet_cfg.label}, solves part of a food mystery, and then reaches a bad ending near {hideout_cfg.label}.",
            f'Write a child-facing cautionary tale with the words "gulp" and "paw," a mystery to solve, spoken lines, and a sad ending that teaches asking for help.'
        ]
    return [
        f'Write a nursery-rhyme-style mystery where a child finds a paw print after a missing {treat_cfg.label} and solves it with a grown-up.',
        f"Tell a rhyming story with dialogue where {child.id} first suspects {pet_cfg.label}, then follows clues to {hideout_cfg.label}, and ends safely.",
        f'Write a simple mystery story for small children using the words "gulp" and "paw," with clues, dialogue, and a calm lesson about asking for help.'
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    pet = f["pet"]
    culprit = f["culprit"]
    treat_cfg = f["treat_cfg"]
    hideout_cfg = f["hideout_cfg"]
    plan_cfg = f["plan_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "What was the mystery in the story?",
            f"The mystery was who took the missing {treat_cfg.label} from the sill. {child.id} had to use the paw print and the crumbs to work out what happened."
        ),
        (
            f"Why did {child.id} first suspect {pet.label}?",
            f"{child.id} saw a paw print, and {pet.label} has paws, so {child.pronoun()} guessed the pet might be guilty. But then {child.pronoun()} compared the print and saw it did not match {pet.label}'s paw."
        ),
        (
            "What clue helped solve the mystery?",
            f"The best clue was {f.get('clue_text', 'the paw print')}. It showed that some animal had taken the treat and walked away with crumbs."
        ),
    ]
    if plan_cfg.with_helper:
        qa.append((
            f"How did {child.id} solve the mystery safely?",
            f"{child.id} asked {helper.label_word} to come along, and together they followed the crumbs to {hideout_cfg.phrase}. Because {helper.label_word} came too, the culprit dropped the {treat_cfg.label} and the mystery was solved without anyone getting badly scared."
        ))
        qa.append((
            "How did the story end?",
            f"It ended safely. The {treat_cfg.label} was found, and {child.id} learned that dark mysteries are better solved with help."
        ))
    else:
        qa.append((
            f"Why was the ending bad?",
            f"The ending was bad because {child.id} followed the trail into the dark alone. {culprit.label.capitalize()} ran off with the last of the {treat_cfg.label}, and {child.id} also lost {child.pronoun('possessive')} {child.attrs['toy']} in the fright."
        ))
        qa.append((
            f"What did {child.id} learn?",
            f"{child.id} learned that solving a scary mystery alone is not brave in a useful way. Asking {helper.label_word} for help would have been safer and would probably have saved both supper and the toy."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"paw", "crumbs", "dark"}
    tags |= set(f["culprit_cfg"].tags)
    if f["outcome"] == "bad":
        tags.add("ask_help")
    else:
        tags.add("ask_help")
    order = ["paw", "crumbs", "fox", "raccoon", "badger", "dark", "ask_help"]
    out: list[tuple[str, str]] = []
    for tag in order:
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


SETTINGS = {
    "cottage": Setting(
        id="cottage",
        label="a little cottage",
        opening="where the kettle sang in the fading light",
        window="the kitchen window",
        yard="the herb yard",
        affords={"hedge", "woodpile"},
    ),
    "farmhouse": Setting(
        id="farmhouse",
        label="a red farmhouse",
        opening="where the spoons all shone in the fading light",
        window="the pantry window",
        yard="the strawy yard",
        affords={"shed", "woodpile"},
    ),
    "mill_house": Setting(
        id="mill_house",
        label="the mill house",
        opening="where the wheel hummed in the fading light",
        window="the low mullioned window",
        yard="the stony yard",
        affords={"hedge", "shed"},
    ),
}

TREATS = {
    "bun": Treat(
        id="bun",
        label="bun",
        phrase="a honey bun",
        cooling="cool on the sill",
        crumbs="sweet crumbs",
        tags={"crumbs"},
    ),
    "tart": Treat(
        id="tart",
        label="tart",
        phrase="a plum tart",
        cooling="cool on the sill",
        crumbs="sticky crumbs",
        tags={"crumbs"},
    ),
    "pie": Treat(
        id="pie",
        label="pie",
        phrase="a moon pie",
        cooling="cool on the sill",
        crumbs="flaky crumbs",
        tags={"crumbs"},
    ),
}

PETS = {
    "cat": Pet(
        id="cat",
        label="cat",
        sound="mew",
        paw_size=1,
        tags={"paw"},
    ),
    "puppy": Pet(
        id="puppy",
        label="puppy",
        sound="ruff",
        paw_size=2,
        tags={"paw"},
    ),
}

CULPRITS = {
    "fox": Culprit(
        id="fox",
        label="fox",
        sound="yip",
        paw_size=3,
        swift=2,
        hides={"hedge", "woodpile"},
        tags={"fox", "paw"},
    ),
    "raccoon": Culprit(
        id="raccoon",
        label="raccoon",
        sound="chrr",
        paw_size=2,
        swift=1,
        hides={"shed", "woodpile"},
        tags={"raccoon", "paw"},
    ),
    "badger": Culprit(
        id="badger",
        label="badger",
        sound="snuff",
        paw_size=4,
        swift=2,
        hides={"hedge", "shed"},
        tags={"badger", "paw"},
    ),
}

HIDEOUTS = {
    "hedge": Hideout(
        id="hedge",
        label="the hedge",
        phrase="the hedge by the gate",
        dark=1,
        warning="the hedge rattled in the evening wind",
        tags={"dark"},
    ),
    "woodpile": Hideout(
        id="woodpile",
        label="the woodpile",
        phrase="the woodpile behind the house",
        dark=1,
        warning="the woodpile made long toothy shadows",
        tags={"dark"},
    ),
    "shed": Hideout(
        id="shed",
        label="the shed",
        phrase="the old shed at the yard-end",
        dark=2,
        warning="the shed door hung open like a black mouth",
        tags={"dark"},
    ),
}

PLANS = {
    "with_helper": Plan(
        id="with_helper",
        label="ask granny to come",
        with_helper=True,
        tags={"ask_help"},
    ),
    "alone": Plan(
        id="alone",
        label="go alone",
        with_helper=False,
        tags={"dark", "ask_help"},
    ),
}

GIRL_NAMES = ["Mabel", "Dolly", "Nell", "Rose", "Lila", "Tess"]
BOY_NAMES = ["Toby", "Ned", "Ollie", "Ben", "Kit", "Pip"]
TOYS = ["rag doll", "tin whistle", "striped ball", "patchwork rabbit"]


@dataclass
class StoryParams:
    setting: str
    treat: str
    pet: str
    culprit: str
    hideout: str
    plan: str
    child_name: str
    child_gender: str
    helper: str = "grandmother"
    toy: str = "rag doll"
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
        setting="cottage",
        treat="bun",
        pet="cat",
        culprit="fox",
        hideout="hedge",
        plan="alone",
        child_name="Mabel",
        child_gender="girl",
        helper="grandmother",
        toy="rag doll",
    ),
    StoryParams(
        setting="farmhouse",
        treat="tart",
        pet="puppy",
        culprit="raccoon",
        hideout="shed",
        plan="with_helper",
        child_name="Toby",
        child_gender="boy",
        helper="grandmother",
        toy="striped ball",
    ),
    StoryParams(
        setting="mill_house",
        treat="pie",
        pet="cat",
        culprit="badger",
        hideout="shed",
        plan="alone",
        child_name="Nell",
        child_gender="girl",
        helper="grandmother",
        toy="patchwork rabbit",
    ),
    StoryParams(
        setting="cottage",
        treat="tart",
        pet="puppy",
        culprit="fox",
        hideout="woodpile",
        plan="with_helper",
        child_name="Ben",
        child_gender="boy",
        helper="grandmother",
        toy="tin whistle",
    ),
]


ASP_RULES = r"""
valid(S, C, H) :- setting(S), culprit(C), hideout(H), affords(S, H), can_hide(C, H).

danger(Cw + Hd) :- chosen_culprit(C), swift(C, Cw), chosen_hideout(H), dark(H, Hd), chosen_plan(alone).
danger(0) :- chosen_plan(with_helper).

solved :- chosen_plan(with_helper).
solved_alone :- chosen_plan(alone), danger(D), bravery_init(B), D <= B.
bad :- chosen_plan(alone), danger(D), bravery_init(B), D > B.

outcome(solved) :- solved.
outcome(solved_alone) :- solved_alone.
outcome(bad) :- bad.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
        for hid in sorted(SETTINGS[sid].affords):
            lines.append(asp.fact("affords", sid, hid))
    for cid, culprit in CULPRITS.items():
        lines.append(asp.fact("culprit", cid))
        lines.append(asp.fact("swift", cid, culprit.swift))
        for hid in sorted(culprit.hides):
            lines.append(asp.fact("can_hide", cid, hid))
    for hid, hideout in HIDEOUTS.items():
        lines.append(asp.fact("hideout", hid))
        lines.append(asp.fact("dark", hid, hideout.dark))
    for pid in PLANS:
        lines.append(asp.fact("plan", pid))
    lines.append(asp.fact("bravery_init", BRAVERY_INIT))
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
        asp.fact("chosen_culprit", params.culprit),
        asp.fact("chosen_hideout", params.hideout),
        asp.fact("chosen_plan", params.plan),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Nursery-rhyme mystery storyworld: a missing treat, a paw print, and a choice between help and going alone."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--treat", choices=TREATS)
    ap.add_argument("--pet", choices=PETS)
    ap.add_argument("--culprit", choices=CULPRITS)
    ap.add_argument("--hideout", choices=HIDEOUTS)
    ap.add_argument("--plan", choices=PLANS)
    ap.add_argument("--helper", choices=["grandmother", "grandfather", "mother", "father"])
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid setting/culprit/hideout combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run smoke tests")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting = SETTINGS.get(args.setting) if args.setting else None
    culprit = CULPRITS.get(args.culprit) if args.culprit else None
    hideout = HIDEOUTS.get(args.hideout) if args.hideout else None

    if args.culprit and args.hideout and not valid_hide(culprit, hideout, setting or SETTINGS[next(iter(SETTINGS))]):
        if setting and not valid_hide(culprit, hideout, setting):
            raise StoryError(explain_rejection(setting, culprit, hideout))
        if not setting and hideout.id not in culprit.hides:
            raise StoryError(explain_rejection(None, culprit, hideout))

    combos = [
        c for c in valid_combos()
        if (args.setting is None or c[0] == args.setting)
        and (args.culprit is None or c[1] == args.culprit)
        and (args.hideout is None or c[2] == args.hideout)
    ]
    if not combos:
        raise StoryError(explain_rejection(setting, culprit, hideout))

    chosen_setting, chosen_culprit, chosen_hideout = rng.choice(sorted(combos))
    treat = args.treat or rng.choice(sorted(TREATS))
    pet = args.pet or rng.choice(sorted(PETS))
    plan = args.plan or rng.choice(sorted(PLANS))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = args.helper or rng.choice(["grandmother", "grandfather", "mother", "father"])
    toy = rng.choice(TOYS)
    return StoryParams(
        setting=chosen_setting,
        treat=treat,
        pet=pet,
        culprit=chosen_culprit,
        hideout=chosen_hideout,
        plan=plan,
        child_name=name,
        child_gender=gender,
        helper=helper,
        toy=toy,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting: {params.setting})")
    if params.treat not in TREATS:
        raise StoryError(f"(Unknown treat: {params.treat})")
    if params.pet not in PETS:
        raise StoryError(f"(Unknown pet: {params.pet})")
    if params.culprit not in CULPRITS:
        raise StoryError(f"(Unknown culprit: {params.culprit})")
    if params.hideout not in HIDEOUTS:
        raise StoryError(f"(Unknown hideout: {params.hideout})")
    if params.plan not in PLANS:
        raise StoryError(f"(Unknown plan: {params.plan})")
    if not valid_hide(CULPRITS[params.culprit], HIDEOUTS[params.hideout], SETTINGS[params.setting]):
        raise StoryError(explain_rejection(SETTINGS[params.setting], CULPRITS[params.culprit], HIDEOUTS[params.hideout]))

    world = tell(
        setting=SETTINGS[params.setting],
        treat_cfg=TREATS[params.treat],
        pet_cfg=PETS[params.pet],
        culprit_cfg=CULPRITS[params.culprit],
        hideout_cfg=HIDEOUTS[params.hideout],
        plan_cfg=PLANS[params.plan],
        child_name=params.child_name,
        child_gender=params.child_gender,
        helper_type=params.helper,
        toy=params.toy,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        attrs = {k: v for k, v in e.attrs.items() if v or v == 0}
        bits = []
        if e.role:
            bits.append(f"role={e.role}")
        if attrs:
            bits.append(f"attrs={attrs}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:8} ({e.type:11}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(x[0] for x in world.fired))}")
    return "\n".join(lines)


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
    py_valid = set(valid_combos())
    asp_valid = set(asp_valid_combos())
    if py_valid == asp_valid:
        print(f"OK: gate matches valid_combos() ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if py_valid - asp_valid:
            print("  only in python:", sorted(py_valid - asp_valid))
        if asp_valid - py_valid:
            print("  only in clingo:", sorted(asp_valid - py_valid))

    cases = list(CURATED)
    parser = build_parser()
    for s in range(40):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(s))
        except StoryError:
            continue
        params.seed = s
        cases.append(params)
    bad = 0
    for params in cases:
        py = outcome_of(params)
        asp = asp_outcome(params)
        if py != asp:
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(cases[0])
        if not smoke.story.strip():
            raise StoryError("smoke test generated an empty story")
        emit(smoke, trace=False, qa=False, header="")
        print("OK: smoke test generate/emit succeeded.")
    except Exception as err:  # pragma: no cover - verification path
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
        print(f"{len(combos)} compatible (setting, culprit, hideout) combos:\n")
        for setting, culprit, hideout in combos:
            print(f"  {setting:10} {culprit:8} {hideout}")
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
            header = (
                f"### {p.child_name}: {p.treat} mystery at {p.setting} "
                f"({p.culprit} in {p.hideout}, {outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
