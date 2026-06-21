#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/wednesday_reconciliation_nursery_rhyme.py
====================================================================

A standalone story world for a tiny nursery-rhyme-style domain:

    On Wednesday, two children want the same parade prop.
    They tug at it, spoil it, feel sorry, and find their way
    back to each other through mending and sharing.

The world is intentionally small and constraint-checked.  Not every repair fits
every prop, and not every sharing plan makes sense for every toy.  The story is
built from simulated state: desire becomes grabbing, damage stalls the play,
sadness rises, apology softens anger, mending restores hope, and a fitting
sharing plan lets the rhyme begin again.

Run it
------
    python storyworlds/worlds/gpt-5.4/wednesday_reconciliation_nursery_rhyme.py
    python storyworlds/worlds/gpt-5.4/wednesday_reconciliation_nursery_rhyme.py --prop paper_crown
    python storyworlds/worlds/gpt-5.4/wednesday_reconciliation_nursery_rhyme.py --fix string_loop
    python storyworlds/worlds/gpt-5.4/wednesday_reconciliation_nursery_rhyme.py --all
    python storyworlds/worlds/gpt-5.4/wednesday_reconciliation_nursery_rhyme.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/wednesday_reconciliation_nursery_rhyme.py --verify
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
SOFT_TRAITS = {"gentle", "patient", "kind"}
REPAIR_MIN = 1


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    age: int = 0
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    material: str = ""
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "teacher", "woman", "aunt"}
        male = {"boy", "father", "man", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {
            "mother": "mother",
            "father": "father",
            "teacher": "teacher",
            "aunt": "aunt",
        }.get(self.type, self.type)
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class Setting:
    id: str
    place: str
    opening: str
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


@dataclass
class Prop:
    id: str
    label: str
    phrase: str
    material: str
    damage_word: str
    damaged_phrase: str
    repair_note: str
    share_modes: set[str] = field(default_factory=set)
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
    phrase: str
    repairs: set[str] = field(default_factory=set)
    repair_power: int = 1
    story_text: str = ""
    qa_text: str = ""
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
class SharePlan:
    id: str
    label: str
    phrase: str
    fits: set[str] = field(default_factory=set)
    ending_line: str = ""
    qa_text: str = ""
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
        self.facts: dict = {
            "quarrel_happened": False,
            "damage_happened": False,
            "apology_given": False,
            "mended": False,
            "shared": False,
            "reconcile_mode": "",
        }

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"first", "second"}]

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


def _r_damage_saddens(world: World) -> list[str]:
    prop = world.get("prop")
    if prop.meters["damaged"] < THRESHOLD:
        return []
    sig = ("damage_saddens", prop.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    for kid in world.kids():
        kid.memes["sadness"] += 1
        kid.memes["anger"] += 1
    world.facts["game_stopped"] = True
    return ["__damage__"]


def _r_apology_softens(world: World) -> list[str]:
    if world.facts.get("apology_from") not in {"first", "second", "both"}:
        return []
    sig = ("apology_softens", world.facts["apology_from"])
    if sig in world.fired:
        return []
    world.fired.add(sig)
    for kid in world.kids():
        if kid.memes["anger"] > 0:
            kid.memes["anger"] -= 1
        kid.memes["trust"] += 1
        kid.memes["hope"] += 1
    world.facts["apology_given"] = True
    return ["__apology__"]


def _r_mending_restores(world: World) -> list[str]:
    prop = world.get("prop")
    if prop.meters["mended"] < THRESHOLD:
        return []
    sig = ("mending_restores", prop.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    prop.meters["damaged"] = 0.0
    for kid in world.kids():
        kid.memes["sadness"] = max(0.0, kid.memes["sadness"] - 1)
        kid.memes["hope"] += 1
    world.facts["mended"] = True
    return ["__mended__"]


def _r_shared_play(world: World) -> list[str]:
    if not world.facts.get("shared_ready"):
        return []
    prop = world.get("prop")
    if prop.meters["mended"] < THRESHOLD:
        return []
    sig = ("shared_play", prop.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    for kid in world.kids():
        kid.memes["joy"] += 1
        kid.memes["friendship"] += 1
        kid.memes["anger"] = 0.0
    world.facts["shared"] = True
    return ["__shared__"]


CAUSAL_RULES: list[Rule] = [
    Rule(name="damage_saddens", tag="emotion", apply=_r_damage_saddens),
    Rule(name="apology_softens", tag="emotion", apply=_r_apology_softens),
    Rule(name="mending_restores", tag="physical", apply=_r_mending_restores),
    Rule(name="shared_play", tag="social", apply=_r_shared_play),
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
                produced.extend(s for s in out if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def fix_fits(prop: Prop, fix: Fix) -> bool:
    return prop.material in fix.repairs and fix.repair_power >= REPAIR_MIN


def share_fits(prop: Prop, plan: SharePlan) -> bool:
    return plan.id in prop.share_modes and prop.id in plan.fits


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for setting_id in SETTINGS:
        for prop_id, prop in PROPS.items():
            for fix_id, fix in FIXES.items():
                if not fix_fits(prop, fix):
                    continue
                for plan_id, plan in SHARE_PLANS.items():
                    if share_fits(prop, plan):
                        combos.append((setting_id, prop_id, fix_id, plan_id))
    return combos


def self_reconcile(relation: str, first_age: int, second_age: int,
                   first_trait: str, second_trait: str) -> bool:
    older_soft = (
        relation == "siblings"
        and second_age > first_age
        and second_trait in SOFT_TRAITS
    )
    both_soft = first_trait in SOFT_TRAITS and second_trait in SOFT_TRAITS
    return older_soft or both_soft


def introduce(world: World, first: Entity, second: Entity, helper: Entity, prop: Prop) -> None:
    world.say(
        f"On wednesday morning, mild and bright, {first.id} and {second.id} came with skipping feet to "
        f"{world.setting.place}. {world.setting.opening}"
    )
    world.say(
        f"{helper.label_word.capitalize()} had brought {prop.phrase}, and both children thought it "
        f"the prettiest thing in sight."
    )


def covet(world: World, first: Entity, second: Entity, prop: Prop) -> None:
    first.memes["want"] += 1
    second.memes["want"] += 1
    world.say(
        f'"I shall have the {prop.label} for the first small song," said {first.id}. '
        f'"No, I shall have it," sang {second.id}, and each one reached along.'
    )


def tug(world: World, first: Entity, second: Entity, prop_ent: Entity, prop: Prop) -> None:
    first.memes["anger"] += 1
    second.memes["anger"] += 1
    prop_ent.meters["pulled"] += 1
    prop_ent.meters["damaged"] += 1
    prop_ent.meters["frayedness"] += 1
    world.facts["quarrel_happened"] = True
    world.facts["damage_happened"] = True
    propagate(world, narrate=False)
    world.say(
        f"They gave a tug and then a pull, not hard, but hard enough. "
        f"The {prop.label} went {prop.damage_word}, and all the merry music stopped."
    )
    world.say(
        f"{first.id} looked cross. {second.id} looked near to tears. "
        f"The bright little game fell quiet."
    )


def guided_pause(world: World, helper: Entity, prop: Prop) -> None:
    world.say(
        f'{helper.label_word.capitalize()} did not scold. "{prop.damaged_phrase.capitalize()} is sad work," '
        f'{helper.pronoun()} said, "but sad things may still be mended, and cross hearts may too."'
    )


def self_pause(world: World, first: Entity, second: Entity, prop: Prop) -> None:
    world.say(
        f"For one still blink, {second.id} saw {first.id}'s wet eyes and the {prop.label} gone wrong. "
        f"The quarrel suddenly sounded silly in the quiet air."
    )


def apologize_self(world: World, first: Entity, second: Entity) -> None:
    world.facts["apology_from"] = "both"
    propagate(world, narrate=False)
    first.memes["remorse"] += 1
    second.memes["remorse"] += 1
    world.say(
        f'"I was too grabby," whispered {second.id}. "{so_was_i(first)}," said {first.id}. '
        f'Then both children said, "I am sorry."'
    )


def so_was_i(first: Entity) -> str:
    return "So was I"


def apologize_guided(world: World, helper: Entity, first: Entity, second: Entity) -> None:
    world.facts["apology_from"] = "both"
    propagate(world, narrate=False)
    first.memes["remorse"] += 1
    second.memes["remorse"] += 1
    world.say(
        f'{helper.label_word.capitalize()} touched one small shoulder and then the other. '
        f'"Try gentle words before gentle hands," {helper.pronoun()} said. '
        f'{first.id} murmured sorry first, and {second.id} answered with sorry too.'
    )


def mend(world: World, helper: Entity, prop_ent: Entity, prop: Prop, fix: Fix) -> None:
    prop_ent.meters["mended"] += 1
    world.facts["used_fix"] = fix.id
    propagate(world, narrate=False)
    world.say(
        f"Together they used {fix.phrase}. {helper.label_word.capitalize()} {fix.story_text}, "
        f"and the children watched the poor {prop.label} come right again."
    )


def share(world: World, first: Entity, second: Entity, prop: Prop, plan: SharePlan) -> None:
    world.facts["shared_ready"] = True
    world.facts["used_share"] = plan.id
    propagate(world, narrate=False)
    world.say(
        f'"Now for the fair way," said {first.id}. {plan.phrase.capitalize()}. '
        f"{second.id} nodded, glad of it."
    )
    world.say(
        f"{plan.ending_line} The rhyme began again, and no one tugged at all."
    )


def ending(world: World, first: Entity, second: Entity, prop: Prop) -> None:
    world.say(
        f"So wednesday wore a softer smile. {first.id} and {second.id} kept close together, "
        f"and the {prop.label} that had once gone wrong now shone between them like a little peace."
    )


def tell(setting: Setting, prop: Prop, fix: Fix, plan: SharePlan,
         first_name: str = "Molly", first_gender: str = "girl",
         second_name: str = "Teddy", second_gender: str = "boy",
         helper_type: str = "teacher", relation: str = "friends",
         first_trait: str = "quick", second_trait: str = "gentle",
         first_age: int = 4, second_age: int = 5) -> World:
    world = World(setting)
    first = world.add(Entity(
        id=first_name,
        kind="character",
        type=first_gender,
        role="first",
        age=first_age,
        traits=[first_trait],
        attrs={"relation": relation},
        label=first_name,
    ))
    second = world.add(Entity(
        id=second_name,
        kind="character",
        type=second_gender,
        role="second",
        age=second_age,
        traits=[second_trait],
        attrs={"relation": relation},
        label=second_name,
    ))
    helper = world.add(Entity(
        id="Helper",
        kind="character",
        type=helper_type,
        role="helper",
        label=helper_type,
    ))
    prop_ent = world.add(Entity(
        id="prop",
        kind="thing",
        type="prop",
        role="prop",
        label=prop.label,
        material=prop.material,
        tags=set(prop.tags),
    ))

    world.facts.update(
        setting=setting,
        prop_cfg=prop,
        fix=fix,
        share=plan,
        first=first,
        second=second,
        helper=helper,
        relation=relation,
        self_possible=self_reconcile(relation, first_age, second_age, first_trait, second_trait),
        apology_from="",
        used_fix="",
        used_share="",
        game_stopped=False,
        shared_ready=False,
    )

    introduce(world, first, second, helper, prop)
    world.para()
    covet(world, first, second, prop)
    tug(world, first, second, prop_ent, prop)
    world.para()

    if world.facts["self_possible"]:
        world.facts["reconcile_mode"] = "self"
        self_pause(world, first, second, prop)
        apologize_self(world, first, second)
    else:
        world.facts["reconcile_mode"] = "guided"
        guided_pause(world, helper, prop)
        apologize_guided(world, helper, first, second)

    mend(world, helper, prop_ent, prop, fix)
    world.para()
    share(world, first, second, prop, plan)
    ending(world, first, second, prop)
    return world


SETTINGS = {
    "garden": Setting(
        id="garden",
        place="the garden gate",
        opening="There the daisies bobbed like little heads, and the hedge kept time in green.",
        ending="The hedge kept time in green.",
        tags={"garden"},
    ),
    "green": Setting(
        id="green",
        place="the village green",
        opening="There the geese were waddling slowly, and a windy cloud went by.",
        ending="A windy cloud went by.",
        tags={"green"},
    ),
    "stair": Setting(
        id="stair",
        place="the sunny stair",
        opening="There the rail was warm with noon, and the house hummed soft behind them.",
        ending="The house hummed soft behind them.",
        tags={"stair"},
    ),
}

PROPS = {
    "ribbon": Prop(
        id="ribbon",
        label="ribbon",
        phrase="a blue parade ribbon",
        material="cloth",
        damage_word="frayed",
        damaged_phrase="the frayed ribbon",
        repair_note="cloth can be made neat with a careful knot",
        share_modes={"turns", "together"},
        tags={"ribbon", "cloth"},
    ),
    "paper_crown": Prop(
        id="paper_crown",
        label="paper crown",
        phrase="a gold paper crown",
        material="paper",
        damage_word="crumpled",
        damaged_phrase="the crumpled crown",
        repair_note="paper needs patching if it is bent or torn",
        share_modes={"turns"},
        tags={"crown", "paper"},
    ),
    "little_drum": Prop(
        id="little_drum",
        label="little drum",
        phrase="a little red drum with a narrow strap",
        material="strap",
        damage_word="loose-strapped",
        damaged_phrase="the loose-strapped drum",
        repair_note="a strap must be looped or tied before the drum can march again",
        share_modes={"turns", "together"},
        tags={"drum", "music"},
    ),
}

FIXES = {
    "knot_bow": Fix(
        id="knot_bow",
        label="knot bow",
        phrase="a neat little knot",
        repairs={"cloth", "strap"},
        repair_power=1,
        story_text="tied the torn bit snug and straight",
        qa_text="They tied a neat knot to mend it",
        tags={"knot", "repair"},
    ),
    "paste_patch": Fix(
        id="paste_patch",
        label="paste patch",
        phrase="a dab of paste and a square patch",
        repairs={"paper"},
        repair_power=1,
        story_text="smoothed the bent place and set on a careful patch",
        qa_text="They used paste and a patch to mend it",
        tags={"paste", "repair"},
    ),
    "string_loop": Fix(
        id="string_loop",
        label="string loop",
        phrase="a fresh little loop of string",
        repairs={"strap", "cloth"},
        repair_power=1,
        story_text="threaded a new loop where the old bit had slipped away",
        qa_text="They made a fresh loop of string so it would hold again",
        tags={"string", "repair"},
    ),
}

SHARE_PLANS = {
    "turns": SharePlan(
        id="turns",
        label="take turns",
        phrase="One would lead the first verse, and one would lead the next",
        fits={"ribbon", "paper_crown", "little_drum"},
        ending_line="First one child shone, then the other, and each one clapped for the next turn",
        qa_text="They decided to take turns with it",
        tags={"turns", "sharing"},
    ),
    "together": SharePlan(
        id="together",
        label="together",
        phrase="They would hold and use it together for the rhyme",
        fits={"ribbon", "little_drum"},
        ending_line="They stepped side by side, each with a hand or beat to give, and the game felt bigger for having room for two",
        qa_text="They used it together instead of fighting over one turn",
        tags={"together", "sharing"},
    ),
}

GIRL_NAMES = ["Molly", "Daisy", "Nell", "Lucy", "May", "Rosie", "Tilly", "Ada"]
BOY_NAMES = ["Teddy", "Ben", "Jack", "Tom", "Ned", "Finn", "Sam", "Ollie"]
TRAITS = ["quick", "gentle", "patient", "kind", "proud"]
RELATIONS = ["friends", "siblings"]


@dataclass
class StoryParams:
    setting: str
    prop: str
    fix: str
    share: str
    first_name: str
    first_gender: str
    second_name: str
    second_gender: str
    helper: str
    relation: str
    first_trait: str
    second_trait: str
    first_age: int = 4
    second_age: int = 5
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
    "sharing": [
        (
            "What does taking turns mean?",
            "Taking turns means one person has a turn first and another person has a turn next. It helps everyone feel included and keeps a game fair."
        ),
    ],
    "sorry": [
        (
            "Why do people say sorry after a quarrel?",
            "People say sorry to show they know they hurt someone or acted wrongly. A real apology can help soft feelings grow where hard feelings were."
        ),
    ],
    "repair": [
        (
            "What does it mean to mend something?",
            "To mend something means to fix it after it is torn, bent, or broken. Careful hands can often make a little thing useful again."
        ),
    ],
    "paper": [
        (
            "Why does paper crumple easily?",
            "Paper is light and thin, so pushing or pulling it can bend it quickly. That is why paper things need gentle hands."
        ),
    ],
    "cloth": [
        (
            "Why can a ribbon be tied again?",
            "A ribbon is cloth, so if it frays or slips, a careful knot can often hold it together. Soft things can still be strong when they are tied neatly."
        ),
    ],
    "music": [
        (
            "What does a little drum do in a rhyme game?",
            "A little drum keeps a beat for marching or singing. A steady beat helps everyone move together."
        ),
    ],
}
KNOWLEDGE_ORDER = ["sharing", "sorry", "repair", "paper", "cloth", "music"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    first = f["first"]
    second = f["second"]
    prop = f["prop_cfg"]
    plan = f["share"]
    mode = f["reconcile_mode"]
    if mode == "self":
        return [
            f'Write a nursery-rhyme-style story that includes the word "wednesday" and ends in reconciliation.',
            f"Tell a gentle verse-tale where {first.id} and {second.id} quarrel over a {prop.label}, feel sorry, mend it, and {plan.label}.",
            f"Write a small rhyming story where two children fix both a spoiled toy and their spoiled tempers without harsh scolding.",
        ]
    return [
        f'Write a nursery-rhyme-style story that includes the word "wednesday" and a calm reconciliation.',
        f"Tell a gentle rhyme where {first.id} and {second.id} quarrel over a {prop.label}, and a grown-up helps them say sorry, mend it, and {plan.label}.",
        f"Write a child-facing story in a sing-song voice where a fight pauses a game, but apology and fairness bring the song back.",
    ]


def pair_noun(first: Entity, second: Entity, relation: str) -> str:
    if relation == "siblings":
        if first.type == "boy" and second.type == "boy":
            return "two brothers"
        if first.type == "girl" and second.type == "girl":
            return "two sisters"
        return "a brother and a sister"
    return "two friends"


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    first = f["first"]
    second = f["second"]
    helper = f["helper"]
    prop = f["prop_cfg"]
    fix = f["fix"]
    plan = f["share"]
    relation = f["relation"]
    pair = pair_noun(first, second, relation)
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair}, {first.id} and {second.id}, on wednesday. They both wanted the same {prop.label}, and that is what started the trouble."
        ),
        (
            f"Why did {first.id} and {second.id} quarrel?",
            f"They both wanted to use the {prop.label} first, so they reached for it at the same time. The wanting turned into tugging because neither child stopped to make room for the other."
        ),
        (
            f"What happened to the {prop.label}?",
            f"It went {prop.damage_word} when the children tugged at it. The damage stopped the game and made both children feel sad instead of merry."
        ),
    ]
    if f["reconcile_mode"] == "self":
        qa.append(
            (
                "How did the children begin to make peace?",
                f"They noticed each other's hurt faces and both said sorry. That apology mattered because it softened the quarrel before the mending began."
            )
        )
    else:
        qa.append(
            (
                f"How did the {helper.label_word} help them make peace?",
                f"The {helper.label_word} stayed calm and asked for gentle words before gentle hands. That helped the children say sorry to each other instead of staying cross."
            )
        )
    qa.append(
        (
            f"How was the {prop.label} fixed?",
            f"{fix.qa_text}. Once the children helped with the repair, the spoiled plaything no longer felt like the center of the quarrel."
        )
    )
    qa.append(
        (
            "How did the story end?",
            f"They were reconciled and used a fair plan: {plan.qa_text}. The ending proves the change because the rhyme begins again and the children stay close instead of pulling apart."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"sharing", "sorry", "repair"}
    tags |= set(f["prop_cfg"].tags)
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
        parts = []
        if ent.role:
            parts.append(f"role={ent.role}")
        if ent.age:
            parts.append(f"age={ent.age}")
        if ent.material:
            parts.append(f"material={ent.material}")
        if ent.traits:
            parts.append(f"traits={ent.traits}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                parts.append(f"attrs={shown}")
        if meters:
            parts.append(f"meters={dict(meters)}")
        if memes:
            parts.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(parts)}")
    lines.append(f"  facts={{{', '.join(f'{k}={v!r}' for k, v in world.facts.items() if k not in {'first', 'second', 'helper', 'setting', 'prop_cfg', 'fix', 'share'})}}}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="garden",
        prop="ribbon",
        fix="knot_bow",
        share="together",
        first_name="Molly",
        first_gender="girl",
        second_name="Teddy",
        second_gender="boy",
        helper="teacher",
        relation="friends",
        first_trait="quick",
        second_trait="gentle",
        first_age=4,
        second_age=5,
    ),
    StoryParams(
        setting="green",
        prop="paper_crown",
        fix="paste_patch",
        share="turns",
        first_name="Daisy",
        first_gender="girl",
        second_name="Lucy",
        second_gender="girl",
        helper="aunt",
        relation="siblings",
        first_trait="proud",
        second_trait="patient",
        first_age=4,
        second_age=6,
    ),
    StoryParams(
        setting="stair",
        prop="little_drum",
        fix="string_loop",
        share="together",
        first_name="Ben",
        first_gender="boy",
        second_name="May",
        second_gender="girl",
        helper="mother",
        relation="friends",
        first_trait="kind",
        second_trait="gentle",
        first_age=5,
        second_age=5,
    ),
    StoryParams(
        setting="garden",
        prop="little_drum",
        fix="knot_bow",
        share="turns",
        first_name="Tom",
        first_gender="boy",
        second_name="Nell",
        second_gender="girl",
        helper="father",
        relation="siblings",
        first_trait="quick",
        second_trait="gentle",
        first_age=5,
        second_age=7,
    ),
]


def explain_fix(prop: Prop, fix: Fix) -> str:
    return (
        f"(No story: {fix.label} does not suit a {prop.label}. "
        f"The {prop.label} is made of {prop.material}, so it needs a fitting mend: {prop.repair_note}.)"
    )


def explain_share(prop: Prop, plan: SharePlan) -> str:
    good = ", ".join(sorted(prop.share_modes))
    return (
        f"(No story: the sharing plan '{plan.id}' does not fit a {prop.label}. "
        f"Try one of: {good}.)"
    )


ASP_RULES = r"""
valid_fix(P, F) :- prop(P), fix(F), material(P, M), repairs(F, M), repair_power(F, Pw), repair_min(Min), Pw >= Min.
valid_share(P, S) :- prop(P), share_plan(S), share_mode(P, S), share_fit(S, P).
valid(Place, P, F, S) :- setting(Place), valid_fix(P, F), valid_share(P, S).

older_soft_sibling :- relation(siblings), second_age(SA), first_age(FA), SA > FA, soft_trait(second_trait_name).
both_soft :- soft_trait(first_trait_name), soft_trait(second_trait_name).

mode(self) :- older_soft_sibling.
mode(self) :- both_soft.
mode(guided) :- not mode(self).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for pid, prop in PROPS.items():
        lines.append(asp.fact("prop", pid))
        lines.append(asp.fact("material", pid, prop.material))
        for mode in sorted(prop.share_modes):
            lines.append(asp.fact("share_mode", pid, mode))
    for fid, fix in FIXES.items():
        lines.append(asp.fact("fix", fid))
        lines.append(asp.fact("repair_power", fid, fix.repair_power))
        for mat in sorted(fix.repairs):
            lines.append(asp.fact("repairs", fid, mat))
    for sid, plan in SHARE_PLANS.items():
        lines.append(asp.fact("share_plan", sid))
        for prop_id in sorted(plan.fits):
            lines.append(asp.fact("share_fit", sid, prop_id))
    lines.append(asp.fact("repair_min", REPAIR_MIN))
    for trait in sorted(SOFT_TRAITS):
        lines.append(asp.fact("soft_trait_name", trait))
        lines.append(asp.fact("soft_trait", trait))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{extra}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_mode(params: StoryParams) -> str:
    import asp

    extra = "\n".join([
        asp.fact("relation", params.relation),
        asp.fact("first_age", params.first_age),
        asp.fact("second_age", params.second_age),
        asp.fact("first_trait_name", params.first_trait),
        asp.fact("second_trait_name", params.second_trait),
    ])
    model = asp.one_model(asp_program(extra, "#show mode/1."))
    out = asp.atoms(model, "mode")
    return out[0][0] if out else "?"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Nursery-rhyme story world: a wednesday quarrel, a mending, and a reconciliation."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--prop", choices=PROPS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--share", choices=SHARE_PLANS)
    ap.add_argument("--helper", choices=["mother", "father", "teacher", "aunt"])
    ap.add_argument("--relation", choices=RELATIONS)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.prop and args.fix:
        if not fix_fits(PROPS[args.prop], FIXES[args.fix]):
            raise StoryError(explain_fix(PROPS[args.prop], FIXES[args.fix]))
    if args.prop and args.share:
        if not share_fits(PROPS[args.prop], SHARE_PLANS[args.share]):
            raise StoryError(explain_share(PROPS[args.prop], SHARE_PLANS[args.share]))

    combos = [
        c for c in valid_combos()
        if (args.setting is None or c[0] == args.setting)
        and (args.prop is None or c[1] == args.prop)
        and (args.fix is None or c[2] == args.fix)
        and (args.share is None or c[3] == args.share)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, prop_id, fix_id, share_id = rng.choice(sorted(combos))
    first_gender = rng.choice(["girl", "boy"])
    second_gender = rng.choice(["girl", "boy"])
    first_name = _pick_name(rng, first_gender)
    second_name = _pick_name(rng, second_gender, avoid=first_name)
    helper = args.helper or rng.choice(["mother", "father", "teacher", "aunt"])
    relation = args.relation or rng.choice(RELATIONS)
    first_trait = rng.choice(TRAITS)
    second_trait = rng.choice(TRAITS)
    first_age, second_age = rng.sample([4, 5, 6, 7], 2)
    return StoryParams(
        setting=setting_id,
        prop=prop_id,
        fix=fix_id,
        share=share_id,
        first_name=first_name,
        first_gender=first_gender,
        second_name=second_name,
        second_gender=second_gender,
        helper=helper,
        relation=relation,
        first_trait=first_trait,
        second_trait=second_trait,
        first_age=first_age,
        second_age=second_age,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting: {params.setting})")
    if params.prop not in PROPS:
        raise StoryError(f"(Unknown prop: {params.prop})")
    if params.fix not in FIXES:
        raise StoryError(f"(Unknown fix: {params.fix})")
    if params.share not in SHARE_PLANS:
        raise StoryError(f"(Unknown sharing plan: {params.share})")

    setting = SETTINGS[params.setting]
    prop = PROPS[params.prop]
    fix = FIXES[params.fix]
    share_plan = SHARE_PLANS[params.share]

    if not fix_fits(prop, fix):
        raise StoryError(explain_fix(prop, fix))
    if not share_fits(prop, share_plan):
        raise StoryError(explain_share(prop, share_plan))

    world = tell(
        setting=setting,
        prop=prop,
        fix=fix,
        plan=share_plan,
        first_name=params.first_name,
        first_gender=params.first_gender,
        second_name=params.second_name,
        second_gender=params.second_gender,
        helper_type=params.helper,
        relation=params.relation,
        first_trait=params.first_trait,
        second_trait=params.second_trait,
        first_age=params.first_age,
        second_age=params.second_age,
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
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: valid combos match ({len(python_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos.")
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))

    cases = list(CURATED)
    for seed in range(50):
        try:
            args = build_parser().parse_args([])
            cases.append(resolve_params(args, random.Random(seed)))
        except StoryError:
            continue
    bad = 0
    for params in cases:
        py_mode = "self" if self_reconcile(
            params.relation,
            params.first_age,
            params.second_age,
            params.first_trait,
            params.second_trait,
        ) else "guided"
        if asp_mode(params) != py_mode:
            bad += 1
    if bad == 0:
        print(f"OK: reconciliation mode matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} reconciliation modes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("(Smoke test failed: generated empty story.)")
        print("OK: smoke test generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/4.\n#show mode/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid (setting, prop, fix, share) combos:\n")
        for setting_id, prop_id, fix_id, share_id in combos:
            print(f"  {setting_id:8} {prop_id:12} {fix_id:11} {share_id}")
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
            mode = "self" if self_reconcile(
                p.relation, p.first_age, p.second_age, p.first_trait, p.second_trait
            ) else "guided"
            header = (
                f"### {p.first_name} & {p.second_name}: {p.prop} at {p.setting} "
                f"({p.fix}, {p.share}, {mode})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
