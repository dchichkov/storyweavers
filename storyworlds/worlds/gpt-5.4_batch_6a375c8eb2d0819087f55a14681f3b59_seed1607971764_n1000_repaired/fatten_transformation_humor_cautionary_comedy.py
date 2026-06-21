#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/fatten_transformation_humor_cautionary_comedy.py
============================================================================

A standalone story world about a child who wants to **fatten** a contest crop
too fast. The world models a comic transformation: a pumpkin or melon swells in
a silly way after an impatient shortcut, then either gets saved in time, is
talked out of the shortcut entirely, or splits into a gooey mess. The cautionary
lesson is simple and child-facing: living things do not grow well when you rush
them.

Run it
------
    python storyworlds/worlds/gpt-5.4/fatten_transformation_humor_cautionary_comedy.py
    python storyworlds/worlds/gpt-5.4/fatten_transformation_humor_cautionary_comedy.py --crop pumpkin --shortcut extra_fertilizer
    python storyworlds/worlds/gpt-5.4/fatten_transformation_humor_cautionary_comedy.py --crop sunflower
    python storyworlds/worlds/gpt-5.4/fatten_transformation_humor_cautionary_comedy.py --shortcut fizzy_soda
    python storyworlds/worlds/gpt-5.4/fatten_transformation_humor_cautionary_comedy.py --all
    python storyworlds/worlds/gpt-5.4/fatten_transformation_humor_cautionary_comedy.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/fatten_transformation_humor_cautionary_comedy.py --verify
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
SENSE_MIN = 2
BOLDNESS_INIT = 6.0
CAUTIOUS_TRAITS = {"careful", "patient", "sensible"}


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
    bulky_crop: bool = False
    living: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)
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
    detail: str
    afford_crops: set[str] = field(default_factory=set)
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
class Contest:
    id: str
    title: str
    hope: str
    end_award: str
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
class Crop:
    id: str
    label: str
    phrase: str
    patch: str
    bulky: bool
    tenderness: int
    swell_line: str
    crack_line: str
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
class Shortcut:
    id: str
    label: str
    sense: int
    stress: int
    line: str
    effect: str
    warning: str
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
class Response:
    id: str
    label: str
    sense: int
    power: int
    save_text: str
    fail_text: str
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
        return [e for e in self.entities.values() if e.role in {"instigator", "helper"}]

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


def _r_swell(world: World) -> list[str]:
    out: list[str] = []
    crop = world.get("crop")
    if crop.meters["overfed"] < THRESHOLD:
        return out
    sig = ("swell", crop.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    crop.meters["swollen"] += 1
    crop.meters["stress"] += crop.meters["overfed"]
    for kid in world.kids():
        kid.memes["surprise"] += 1
    out.append("__swell__")
    return out


def _r_crack(world: World) -> list[str]:
    out: list[str] = []
    crop = world.get("crop")
    if crop.meters["stress"] < crop.meters["split_limit"]:
        return out
    sig = ("crack", crop.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    crop.meters["cracked"] += 1
    crop.meters["messy"] += 1
    world.get("patch").meters["messy"] += 1
    for kid in world.kids():
        kid.memes["alarm"] += 1
    out.append("__crack__")
    return out


CAUSAL_RULES = [
    Rule(name="swell", tag="physical", apply=_r_swell),
    Rule(name="crack", tag="physical", apply=_r_crack),
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


def crop_at_risk(setting: Setting, crop: Crop) -> bool:
    return crop.id in setting.afford_crops and crop.bulky


def sensible_shortcuts() -> list[Shortcut]:
    return [s for s in SHORTCUTS.values() if s.sense >= SENSE_MIN]


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def risk_severity(crop: Crop, shortcut: Shortcut, delay: int) -> int:
    return crop.tenderness + shortcut.stress + delay


def is_saved(crop: Crop, shortcut: Shortcut, response: Response, delay: int) -> bool:
    return response.power >= risk_severity(crop, shortcut, delay)


def initial_caution(trait: str) -> float:
    return 5.0 if trait in CAUTIOUS_TRAITS else 3.0


def would_avert(relation: str, instigator_age: int, helper_age: int, trait: str) -> bool:
    helper_older = relation == "siblings" and helper_age > instigator_age
    authority = (initial_caution(trait) + 1.0) + (4.0 if helper_older else 0.0)
    return helper_older and authority > BOLDNESS_INIT


def predict_split(world: World, shortcut: Shortcut, delay: int) -> dict:
    sim = world.copy()
    crop = sim.get("crop")
    crop.meters["overfed"] += shortcut.stress
    crop.meters["split_limit"] = float(sim.facts["crop_cfg"].tenderness + delay + 1)
    propagate(sim, narrate=False)
    return {
        "swollen": crop.meters["swollen"] >= THRESHOLD,
        "cracked": crop.meters["cracked"] >= THRESHOLD,
        "stress": crop.meters["stress"],
    }


def introduce(world: World, a: Entity, b: Entity, setting: Setting, contest: Contest, crop: Crop) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
    world.say(
        f"On the edge of {setting.place}, {a.id} and {b.id} had a little garden patch. "
        f"{setting.detail}"
    )
    world.say(
        f"They were growing {crop.phrase} for the {contest.title}, and {a.id} kept dreaming "
        f"about {contest.hope}."
    )


def admire_crop(world: World, a: Entity, crop: Crop) -> None:
    world.say(
        f"Every morning {a.id} crouched beside {crop.patch} and grinned. "
        f'"Grow, grow, grow," {a.pronoun()} whispered. "I want to fatten this {crop.label} into a champion."'
    )


def tempt(world: World, a: Entity, shortcut: Shortcut) -> None:
    a.memes["boldness"] += 1
    world.say(
        f"That afternoon {a.id} had a bright, wiggly idea. "
        f'"Maybe I can {shortcut.label}," {a.pronoun()} said. "{shortcut.line}"'
    )


def warn(world: World, b: Entity, a: Entity, shortcut: Shortcut, crop: Crop, adult: Entity, delay: int) -> None:
    pred = predict_split(world, shortcut, delay)
    b.memes["caution"] += 1
    world.facts["predicted_crack"] = pred["cracked"]
    world.facts["predicted_stress"] = pred["stress"]
    extra = ""
    if pred["cracked"]:
        extra = f" {b.pronoun().capitalize()} could almost picture {crop.the if hasattr(crop, 'the') else 'it'} popping like a pudding."
    world.say(
        f'{b.id} shook {b.pronoun("possessive")} head. "{shortcut.warning} {crop.label.capitalize()}s are living things, not balloons. '
        f'If you rush {adult.label_word}\'s garden lesson, the {crop.label} could split."{extra}'
    )


def defy(world: World, a: Entity, b: Entity, shortcut: Shortcut) -> None:
    a.memes["defiance"] += 1
    older = a.attrs.get("relation") == "siblings" and a.age > b.age
    if older:
        rel = "big brother" if a.type == "boy" else "big sister"
        world.say(
            f'"It will be funny, not harmful," {a.id} said. Because {a.id} was {b.pronoun("possessive")} {rel}, '
            f"{b.id} could not stop {a.pronoun('object')} in time."
        )
    else:
        world.say(f'"It will be funny, not harmful," {a.id} said, and hurried to try it anyway.')


def back_down(world: World, a: Entity, b: Entity, shortcut: Shortcut, adult: Entity, crop: Crop) -> None:
    a.memes["boldness"] = 0.0
    a.memes["relief"] += 1
    b.memes["relief"] += 1
    rel = "brother" if b.type == "boy" else "sister"
    world.say(
        f'{a.id} looked at {crop.patch}, then at {b.id}. Because {b.id} was {a.pronoun("possessive")} older {rel}, '
        f'{a.pronoun()} trusted {b.pronoun("object")} enough to stop.'
    )
    world.say(
        f'They put the {shortcut.label} away and went to ask {adult.label_word} how real gardeners help a plant grow.'
    )


def overfeed(world: World, crop_ent: Entity, shortcut: Shortcut, crop: Crop, delay: int) -> None:
    crop_ent.meters["overfed"] += shortcut.stress
    crop_ent.meters["split_limit"] = float(crop.tenderness + delay + 1)
    if shortcut.id == "all_day_hose":
        world.get("patch").meters["soggy"] += 1
    propagate(world, narrate=False)
    world.say(shortcut.effect)
    if crop_ent.meters["swollen"] >= THRESHOLD:
        world.say(crop.swell_line)
    if crop_ent.meters["cracked"] >= THRESHOLD:
        world.say(crop.crack_line)


def alarm(world: World, a: Entity, b: Entity, crop: Crop, adult: Entity) -> None:
    if world.get("crop").meters["cracked"] >= THRESHOLD:
        world.say(
            f'"{adult.label_word.upper()}!" {b.id} yelped. "{crop.label.capitalize()} goo! It split!"'
        )
    else:
        world.say(
            f'{b.id} stared and then snorted a little laugh. "It got so round it looks like it swallowed a drum," '
            f'{b.pronoun()} said.'
        )


def rescue(world: World, adult: Entity, response: Response, crop: Crop, contest: Contest) -> None:
    crop_ent = world.get("crop")
    crop_ent.meters["cracked"] = 0.0
    crop_ent.meters["stress"] = 0.0
    world.get("patch").meters["soggy"] = 0.0
    world.say(
        f"{adult.label_word.capitalize()} came over fast and {response.save_text}."
    )
    crop_ent.meters["saved"] += 1
    crop_ent.meters["scarred"] += 1
    world.say(
        f"The {crop.label} kept a funny scar, but it settled down instead of bursting. "
        f"By fair day it was not the biggest, but it was so oddly lumpy that it won {contest.end_award}."
    )


def lesson(world: World, adult: Entity, a: Entity, b: Entity) -> None:
    for kid in (a, b):
        kid.memes["lesson"] += 1
        kid.memes["relief"] += 1
        kid.memes["fear"] = 0.0
    world.say(
        f'{adult.label_word.capitalize()} knelt between them and the vines. "You cannot fatten a living thing by bullying it," '
        f'{adult.pronoun()} said. "Plants need water, food, and time in the right amounts."'
    )
    world.say(
        f'{a.id} rubbed the back of {a.pronoun("possessive")} neck. {b.id} nodded so hard that a leaf stuck to '
        f'{b.pronoun("possessive")} sleeve.'
    )


def safe_method(world: World, adult: Entity, a: Entity, b: Entity, crop: Crop) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
        kid.memes["patience"] += 1
    world.say(
        f"The next week, {adult.label_word} showed them a measuring cup, a mulch ring, and a little notebook for watering days."
    )
    world.say(
        f"Together they cared for the vines slowly. A new {crop.label} grew round and healthy, and nobody tried to hurry it."
    )


def rescue_fail(world: World, adult: Entity, response: Response, crop: Crop) -> None:
    crop_ent = world.get("crop")
    crop_ent.meters["cracked"] += 1
    crop_ent.meters["ruined"] += 1
    world.get("patch").meters["messy"] += 1
    world.say(
        f"{adult.label_word.capitalize()} hurried over and {response.fail_text}."
    )
    world.say(
        f"The {crop.label} sagged open with a wet plop, and shiny seeds slid everywhere like marbles wearing jelly shoes."
    )


def salvage(world: World, adult: Entity, a: Entity, b: Entity, crop: Crop) -> None:
    for kid in (a, b):
        kid.memes["lesson"] += 1
        kid.memes["relief"] += 1
    world.say(
        f"No ribbon was coming from that {crop.label}, but {adult.label_word} spread out a tray and saved the seeds."
    )
    world.say(
        f'"We cannot undo a silly shortcut," {adult.pronoun()} said gently, "but we can begin again the patient way."'
    )
    world.say(
        f'By evening {a.id} and {b.id} were roasting seeds and laughing at how the great giant {crop.label} had lost a fight with its own skin.'
    )


def tell(
    setting: Setting,
    contest: Contest,
    crop_cfg: Crop,
    shortcut: Shortcut,
    response: Response,
    instigator: str = "Milo",
    instigator_gender: str = "boy",
    helper: str = "Nora",
    helper_gender: str = "girl",
    trait: str = "patient",
    adult_type: str = "mother",
    delay: int = 0,
    instigator_age: int = 6,
    helper_age: int = 4,
    relation: str = "siblings",
) -> World:
    world = World(setting)
    a = world.add(Entity(
        id=instigator,
        kind="character",
        type=instigator_gender,
        role="instigator",
        age=instigator_age,
        attrs={"relation": relation},
    ))
    b = world.add(Entity(
        id=helper,
        kind="character",
        type=helper_gender,
        role="helper",
        age=helper_age,
        traits=[trait],
        attrs={"relation": relation},
    ))
    adult = world.add(Entity(
        id="Adult",
        kind="character",
        type=adult_type,
        role="adult",
        label="the grown-up",
    ))
    patch = world.add(Entity(
        id="patch",
        kind="thing",
        type="garden_patch",
        label="patch",
    ))
    crop_ent = world.add(Entity(
        id="crop",
        kind="thing",
        type="crop",
        label=crop_cfg.label,
        bulky_crop=crop_cfg.bulky,
        living=True,
    ))

    a.memes["boldness"] = BOLDNESS_INIT
    b.memes["caution"] = initial_caution(trait)
    crop_ent.meters["split_limit"] = float(crop_cfg.tenderness + delay + 1)

    world.facts.update(
        contest=contest,
        crop_cfg=crop_cfg,
        shortcut=shortcut,
        response=response,
        relation=relation,
        delay=delay,
    )

    introduce(world, a, b, setting, contest, crop_cfg)
    admire_crop(world, a, crop_cfg)

    world.para()
    tempt(world, a, shortcut)
    warn(world, b, a, shortcut, crop_cfg, adult, delay)

    averted = would_avert(relation, instigator_age, helper_age, trait)
    if averted:
        back_down(world, a, b, shortcut, adult, crop_cfg)
        world.para()
        safe_method(world, adult, a, b, crop_cfg)
        outcome = "averted"
    else:
        defy(world, a, b, shortcut)
        world.para()
        overfeed(world, crop_ent, shortcut, crop_cfg, delay)
        alarm(world, a, b, crop_cfg, adult)

        contained = is_saved(crop_cfg, shortcut, response, delay)
        world.para()
        if contained:
            rescue(world, adult, response, crop_cfg, contest)
            lesson(world, adult, a, b)
            world.para()
            safe_method(world, adult, a, b, crop_cfg)
            outcome = "saved"
        else:
            rescue_fail(world, adult, response, crop_cfg)
            salvage(world, adult, a, b, crop_cfg)
            outcome = "split"

    world.facts.update(
        instigator=a,
        helper=b,
        adult=adult,
        crop=crop_ent,
        patch=patch,
        setting=setting,
        averted=outcome == "averted",
        outcome=outcome,
        cracked=crop_ent.meters["cracked"] >= THRESHOLD or crop_ent.meters["ruined"] >= THRESHOLD,
        saved=crop_ent.meters["saved"] >= THRESHOLD,
    )
    return world


SETTINGS = {
    "backyard": Setting(
        id="backyard",
        place="the backyard fence",
        detail="A crooked sunflower stake leaned nearby, and the hose slept in a loose green loop.",
        afford_crops={"pumpkin", "melon", "squash"},
    ),
    "community_garden": Setting(
        id="community_garden",
        place="the community garden",
        detail="Bee boxes hummed at one end, and hand-painted signs stuck up between the rows.",
        afford_crops={"pumpkin", "melon", "squash"},
    ),
    "school_patch": Setting(
        id="school_patch",
        place="the school garden patch",
        detail="A paper scarecrow smiled from the beans, and the dirt still smelled warm from the morning sun.",
        afford_crops={"pumpkin", "squash"},
    ),
}

CONTESTS = {
    "fair": Contest(
        id="fair",
        title="Harvest Fair",
        hope="the biggest ribbon on the table",
        end_award='the ribbon for "Silliest Shape"',
    ),
    "parade": Contest(
        id="parade",
        title="Autumn Parade",
        hope="cheers for the grandest garden wagon",
        end_award='the laugh-and-clap prize for "Funniest Vegetable"',
    ),
    "supper": Contest(
        id="supper",
        title="Soup Supper Display",
        hope="a place in the middle of the table",
        end_award='the little card that said "Most Unusual Gourd"',
    ),
}

CROPS = {
    "pumpkin": Crop(
        id="pumpkin",
        label="pumpkin",
        phrase="a round orange pumpkin",
        patch="the pumpkin vine",
        bulky=True,
        tenderness=2,
        swell_line="By sunset the pumpkin looked so puffed up that even the crows seemed to stare at it. Its skin shone tight and smooth, as if someone had polished a moon.",
        crack_line="Then a thin line split across the side. Seeds and stringy orange goo slithered out, and the proud giant made the sad little sound of a pudding giving up.",
        tags={"pumpkin", "garden"},
    ),
    "melon": Crop(
        id="melon",
        label="melon",
        phrase="a striped green melon",
        patch="the melon bed",
        bulky=True,
        tenderness=1,
        swell_line="The melon plumped up so fast it looked as if it had stuffed both cheeks at once. The vine tugged at it like a belt that had lost an argument.",
        crack_line="A crack zipped down one side, and sweet juice dribbled into the dirt. Suddenly the magnificent melon looked less like a champion and more like a dropped picnic.",
        tags={"melon", "garden"},
    ),
    "squash": Crop(
        id="squash",
        label="squash",
        phrase="a fat yellow squash",
        patch="the squash leaves",
        bulky=True,
        tenderness=2,
        swell_line="The squash swelled into a bumpy yellow blimp. One side bulged higher than the other, which made it look as if it were trying to smuggle a pillow.",
        crack_line="With a wet pop, the side gave way. Seeds flopped out and a leaf stuck to the mess like a tiny green hat.",
        tags={"squash", "garden"},
    ),
    "sunflower": Crop(
        id="sunflower",
        label="sunflower",
        phrase="a tall sunflower",
        patch="the sunflower row",
        bulky=False,
        tenderness=1,
        swell_line="",
        crack_line="",
        tags={"sunflower", "garden"},
    ),
}

SHORTCUTS = {
    "extra_fertilizer": Shortcut(
        id="extra_fertilizer",
        label="give it extra fertilizer",
        sense=2,
        stress=2,
        line="One scoop helped, so maybe three scoops will make it huge by tomorrow.",
        effect="Before dinner, the soil got a heap of extra plant food. The smell was strong enough to make both children wrinkle their noses.",
        warning="Too much plant food is still too much.",
        tags={"fertilizer", "garden"},
    ),
    "all_day_hose": Shortcut(
        id="all_day_hose",
        label="leave the hose running on it all day",
        sense=2,
        stress=1,
        line="Maybe nonstop water will fatten it like soup in a pot.",
        effect="The hose whispered and splashed for far too long, until the dirt around the roots turned dark and squishy.",
        warning="Roots need air too, not a swamp.",
        tags={"water", "garden"},
    ),
    "fizzy_soda": Shortcut(
        id="fizzy_soda",
        label="pour fizzy soda on it",
        sense=1,
        stress=2,
        line="Bubbles make everything lively, so maybe bubbles will make it grow.",
        effect="The soda fizzed and stuck to the leaves in a shiny, sugary skin.",
        warning="Sticky sugar is not a garden trick.",
        tags={"soda", "garden"},
    ),
}

RESPONSES = {
    "rinse_and_drain": Response(
        id="rinse_and_drain",
        label="rinse and drain",
        sense=3,
        power=4,
        save_text="rinsed the soil, loosened a dry ring around the roots, and let the patch drain before the skin tore any farther",
        fail_text="rinsed and drained as fast as possible, but the poor thing had already pushed itself too far",
        qa_text="rinsed the soil and let the patch drain so the crop could settle down",
        tags={"watering", "garden"},
    ),
    "shade_and_wait": Response(
        id="shade_and_wait",
        label="shade and wait",
        sense=2,
        power=3,
        save_text="set up a cloth shade, stopped the extra feeding, and propped the fruit so the strain eased",
        fail_text="set up shade and support, but the skin was already giving way",
        qa_text="gave the crop shade and support and stopped the extra feeding",
        tags={"support", "garden"},
    ),
    "poke_it": Response(
        id="poke_it",
        label="poke it with a stick",
        sense=1,
        power=1,
        save_text="poked at it until, by luck, it somehow calmed down",
        fail_text="poked at it with a stick, which only made the cracked side sag faster",
        qa_text="poked it with a stick",
        tags={"garden"},
    ),
}

GIRL_NAMES = ["Nora", "Lila", "Mia", "Ava", "June", "Zoe", "Ruby", "Ella"]
BOY_NAMES = ["Milo", "Ben", "Theo", "Sam", "Leo", "Finn", "Owen", "Max"]
TRAITS = ["careful", "patient", "sensible", "curious", "cheerful", "thoughtful"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for setting_id, setting in SETTINGS.items():
        for crop_id, crop in CROPS.items():
            if not crop_at_risk(setting, crop):
                continue
            for shortcut_id, shortcut in SHORTCUTS.items():
                if shortcut.sense >= SENSE_MIN:
                    combos.append((setting_id, crop_id, shortcut_id))
    return combos


@dataclass
class StoryParams:
    setting: str
    contest: str
    crop: str
    shortcut: str
    response: str
    instigator: str
    instigator_gender: str
    helper: str
    helper_gender: str
    adult: str
    trait: str
    delay: int = 0
    instigator_age: int = 6
    helper_age: int = 4
    relation: str = "siblings"
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
    "pumpkin": [
        (
            "How do pumpkins grow?",
            "Pumpkins grow from flowers on long vines. They need sunlight, water, and time to get bigger."
        )
    ],
    "melon": [
        (
            "Why can a melon split?",
            "A melon can split if it grows too fast or takes in too much water at once. Its skin cannot always stretch gently enough."
        )
    ],
    "squash": [
        (
            "What is squash?",
            "Squash is a kind of garden fruit that grows on a vine. Some squash are long and some are round."
        )
    ],
    "garden": [
        (
            "What do plants need to grow well?",
            "Plants need the right amounts of sunlight, water, food, and space. Too much can be as unhelpful as too little."
        )
    ],
    "fertilizer": [
        (
            "What does fertilizer do?",
            "Fertilizer gives plants extra nutrients from the soil. Gardeners use only a little, because too much can stress a plant."
        )
    ],
    "water": [
        (
            "Why is too much water bad for roots?",
            "Roots need both water and air in the soil. If the soil stays soggy, the roots cannot breathe well."
        )
    ],
    "soda": [
        (
            "Why is soda not good for garden plants?",
            "Soda is sugary and sticky, and plants are not meant to drink it. Water is what a thirsty plant really needs."
        )
    ],
    "watering": [
        (
            "Why do gardeners measure water?",
            "Gardeners measure water so plants get enough without drowning. Gentle, steady care helps living things grow best."
        )
    ],
    "support": [
        (
            "Why would a gardener support a heavy fruit?",
            "A heavy fruit can pull on its stem or press awkwardly against the ground. Support helps it rest safely while it grows."
        )
    ],
}
KNOWLEDGE_ORDER = ["pumpkin", "melon", "squash", "garden", "fertilizer", "water", "soda", "watering", "support"]


def pair_noun(a: Entity, b: Entity, relation: str) -> str:
    if relation == "siblings":
        if a.type == "boy" and b.type == "boy":
            return "two brothers"
        if a.type == "girl" and b.type == "girl":
            return "two sisters"
        return "a brother and a sister"
    return "two friends"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    a = f["instigator"]
    b = f["helper"]
    crop_cfg = f["crop_cfg"]
    shortcut = f["shortcut"]
    contest = f["contest"]
    outcome = f["outcome"]
    if outcome == "averted":
        return [
            f'Write a funny cautionary story for a 3-to-5-year-old where a child wants to fatten a {crop_cfg.label} too fast for the {contest.title}, but an older helper talks them out of it.',
            f"Tell a gentle comedy where {a.id} has a silly garden shortcut, {b.id} warns that living things are not balloons, and the children choose patience instead.",
            f'Write a transformation story where the big change does not happen because a wiser child stops the mistake before it starts. Include the word "fatten".',
        ]
    if outcome == "saved":
        return [
            f'Write a comic cautionary story for a 3-to-5-year-old where a child tries to fatten a {crop_cfg.label} too fast for the {contest.title}, and a grown-up saves the garden in time.',
            f"Tell a funny story where {a.id} uses {shortcut.label}, the crop swells in a ridiculous way, and the ending teaches patient care.",
            f'Write a simple story with Transformation, Humor, and a gentle warning, using the word "fatten" and ending with a silly but safe garden prize.',
        ]
    return [
        f'Write a funny cautionary story for a 3-to-5-year-old where a child tries to fatten a {crop_cfg.label} too fast for the {contest.title}, and the crop splits into a messy disaster.',
        f"Tell a comedy where {a.id} ignores {b.id}'s warning, rushes a garden trick, and everyone learns that living things cannot be hurried.",
        f'Write a transformation story with a gooey, silly ending that still feels gentle for children. Include the word "fatten".',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a = f["instigator"]
    b = f["helper"]
    adult = f["adult"]
    crop_cfg = f["crop_cfg"]
    shortcut = f["shortcut"]
    response = f["response"]
    contest = f["contest"]
    relation = f["relation"]
    pair = pair_noun(a, b, relation)
    pw = adult.label_word
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair}, {a.id} and {b.id}, who were growing a {crop_cfg.label} for the {contest.title}. It also includes their {pw}, who knew how to care for the garden."
        ),
        (
            f"Why did {a.id} want to fatten the {crop_cfg.label}?",
            f"{a.id} wanted the crop to look huge for the {contest.title}. {a.pronoun().capitalize()} thought a bigger {crop_cfg.label} might win more cheers or a ribbon."
        ),
        (
            f"What warning did {b.id} give?",
            f"{b.id} warned that living things are not balloons and should not be rushed. {b.pronoun().capitalize()} explained that too much too fast could make the {crop_cfg.label} split."
        ),
    ]
    outcome = f["outcome"]
    if outcome == "averted":
        qa.append((
            f"What did {a.id} do after listening to {b.id}?",
            f"{a.id} stopped before trying the shortcut and went to ask {pw} for the right way to help the plant. That choice kept the garden calm and safe."
        ))
        qa.append((
            "How did the story end?",
            f"It ended with slow, careful gardening. A new {crop_cfg.label} grew healthy because the children used patience instead of trying to force a funny transformation."
        ))
    elif outcome == "saved":
        qa.append((
            f"What happened when {a.id} used {shortcut.label}?",
            f"The {crop_cfg.label} swelled in a silly way and looked ready to burst. The funny change happened because {a.id} tried to make it grow too fast."
        ))
        qa.append((
            f"How did the {pw} save the {crop_cfg.label}?",
            f"{pw.capitalize()} {response.qa_text}. That quick help stopped the trouble before the crop split apart completely."
        ))
        qa.append((
            "What lesson did the children learn?",
            f"They learned that you cannot fatten a living thing by forcing it. Gentle care and time work better than impatient shortcuts."
        ))
    else:
        qa.append((
            f"What happened to the {crop_cfg.label}?",
            f"It cracked open and made a gooey mess in the patch. The split happened because the crop was pushed past what it could handle."
        ))
        qa.append((
            f"Could the {pw} fix it completely?",
            f"No. {pw.capitalize()} helped save the seeds, but the big {crop_cfg.label} was ruined. The problem had gone too far before help arrived."
        ))
        qa.append((
            "How did the story end?",
            f"It ended with the children laughing a little while roasting saved seeds and promising to garden more patiently next time. The messy ending turned into a lesson instead of another bad shortcut."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["crop_cfg"].tags) | set(f["shortcut"].tags)
    outcome = f["outcome"]
    if outcome == "saved":
        tags |= set(f["response"].tags)
    elif outcome == "split":
        tags |= {"garden"}
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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.age:
            bits.append(f"age={ent.age}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:8} ({ent.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="backyard",
        contest="fair",
        crop="pumpkin",
        shortcut="extra_fertilizer",
        response="rinse_and_drain",
        instigator="Milo",
        instigator_gender="boy",
        helper="Nora",
        helper_gender="girl",
        adult="mother",
        trait="patient",
        delay=0,
        instigator_age=6,
        helper_age=4,
        relation="siblings",
    ),
    StoryParams(
        setting="community_garden",
        contest="parade",
        crop="melon",
        shortcut="all_day_hose",
        response="shade_and_wait",
        instigator="Ava",
        instigator_gender="girl",
        helper="Ben",
        helper_gender="boy",
        adult="father",
        trait="careful",
        delay=1,
        instigator_age=7,
        helper_age=5,
        relation="friends",
    ),
    StoryParams(
        setting="school_patch",
        contest="supper",
        crop="squash",
        shortcut="extra_fertilizer",
        response="shade_and_wait",
        instigator="Theo",
        instigator_gender="boy",
        helper="Ruby",
        helper_gender="girl",
        adult="mother",
        trait="sensible",
        delay=2,
        instigator_age=6,
        helper_age=4,
        relation="siblings",
    ),
    StoryParams(
        setting="backyard",
        contest="fair",
        crop="pumpkin",
        shortcut="all_day_hose",
        response="rinse_and_drain",
        instigator="Leo",
        instigator_gender="boy",
        helper="Max",
        helper_gender="boy",
        adult="father",
        trait="patient",
        delay=0,
        instigator_age=5,
        helper_age=7,
        relation="siblings",
    ),
]


def explain_crop_rejection(setting: Setting, crop: Crop) -> str:
    if crop.id not in setting.afford_crops:
        return f"(No story: {crop.label} is not a crop this patch is set up to grow.)"
    if not crop.bulky:
        return (
            f"(No story: a {crop.label} is not the kind of big, swelling harvest crop this world can honestly make comic and cautionary. "
            f"Pick a bulky crop like pumpkin, melon, or squash.)"
        )
    return "(No story: that crop does not fit this garden premise.)"


def explain_shortcut(shortcut_id: str) -> str:
    shortcut = SHORTCUTS[shortcut_id]
    better = " / ".join(sorted(s.id for s in sensible_shortcuts()))
    return (
        f"(Refusing shortcut '{shortcut_id}': it scores too low on common sense "
        f"(sense={shortcut.sense} < {SENSE_MIN}). Try one of these instead: {better}.)"
    )


def explain_response(response_id: str) -> str:
    response = RESPONSES[response_id]
    better = " / ".join(sorted(r.id for r in sensible_responses()))
    return (
        f"(Refusing response '{response_id}': it scores too low on common sense "
        f"(sense={response.sense} < {SENSE_MIN}). Try one of these instead: {better}.)"
    )


def outcome_of(params: StoryParams) -> str:
    if would_avert(params.relation, params.instigator_age, params.helper_age, params.trait):
        return "averted"
    crop = CROPS[params.crop]
    shortcut = SHORTCUTS[params.shortcut]
    response = RESPONSES[params.response]
    return "saved" if is_saved(crop, shortcut, response, params.delay) else "split"


ASP_RULES = r"""
% --- reasonableness gate ---------------------------------------------------
good_crop(C)      :- crop(C), bulky(C).
good_shortcut(S)  :- shortcut(S), shortcut_sense(S, V), sense_min(M), V >= M.
good_response(R)  :- response(R), response_sense(R, V), sense_min(M), V >= M.
valid(Place, Crop, Shortcut) :- setting(Place), grows(Place, Crop), good_crop(Crop), good_shortcut(Shortcut).

% --- outcome model ---------------------------------------------------------
cautious_now(T)  :- trait(T), is_cautious(T).
init_caution(5)  :- trait(T), cautious_now(T).
init_caution(3)  :- trait(T), not cautious_now(T).
helper_older     :- relation(siblings), instigator_age(IA), helper_age(HA), HA > IA.
bonus(4)         :- helper_older.
bonus(0)         :- not helper_older.
authority(C + 1 + B) :- init_caution(C), bonus(B).
averted          :- helper_older, authority(A), boldness_init(BI), A > BI.

severity(Tn + Ss + D) :- chosen_crop(C), crop_tenderness(C, Tn),
                         chosen_shortcut(S), shortcut_stress(S, Ss),
                         delay(D).
saved            :- chosen_response(R), response_power(R, P), severity(V), P >= V.

outcome(averted) :- averted.
outcome(saved)   :- not averted, saved.
outcome(split)   :- not averted, not saved.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for setting_id in SETTINGS:
        lines.append(asp.fact("setting", setting_id))
    for setting_id, setting in SETTINGS.items():
        for crop_id in sorted(setting.afford_crops):
            lines.append(asp.fact("grows", setting_id, crop_id))
    for crop_id, crop in CROPS.items():
        lines.append(asp.fact("crop", crop_id))
        if crop.bulky:
            lines.append(asp.fact("bulky", crop_id))
        lines.append(asp.fact("crop_tenderness", crop_id, crop.tenderness))
    for shortcut_id, shortcut in SHORTCUTS.items():
        lines.append(asp.fact("shortcut", shortcut_id))
        lines.append(asp.fact("shortcut_sense", shortcut_id, shortcut.sense))
        lines.append(asp.fact("shortcut_stress", shortcut_id, shortcut.stress))
    for response_id, response in RESPONSES.items():
        lines.append(asp.fact("response", response_id))
        lines.append(asp.fact("response_sense", response_id, response.sense))
        lines.append(asp.fact("response_power", response_id, response.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    lines.append(asp.fact("boldness_init", int(BOLDNESS_INIT)))
    for trait in sorted(CAUTIOUS_TRAITS):
        lines.append(asp.fact("is_cautious", trait))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible_shortcuts() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show good_shortcut/1."))
    return sorted(v for (v,) in asp.atoms(model, "good_shortcut"))


def asp_sensible_responses() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show good_response/1."))
    return sorted(v for (v,) in asp.atoms(model, "good_response"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join([
        asp.fact("chosen_crop", params.crop),
        asp.fact("chosen_shortcut", params.shortcut),
        asp.fact("chosen_response", params.response),
        asp.fact("delay", params.delay),
        asp.fact("relation", params.relation),
        asp.fact("instigator_age", params.instigator_age),
        asp.fact("helper_age", params.helper_age),
        asp.fact("trait", params.trait),
    ])
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    c_short = set(asp_sensible_shortcuts())
    p_short = {s.id for s in sensible_shortcuts()}
    if c_short == p_short:
        print(f"OK: sensible shortcuts match ({sorted(c_short)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible shortcuts: clingo={sorted(c_short)} python={sorted(p_short)}")

    c_resp = set(asp_sensible_responses())
    p_resp = {r.id for r in sensible_responses()}
    if c_resp == p_resp:
        print(f"OK: sensible responses match ({sorted(c_resp)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible responses: clingo={sorted(c_resp)} python={sorted(p_resp)}")

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(60):
        try:
            cases.append(resolve_params(parser.parse_args([]), random.Random(seed)))
        except StoryError:
            continue
    bad = sum(1 for params in cases if asp_outcome(params) != outcome_of(params))
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("smoke test produced an empty story")
        print("OK: smoke test story generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a child tries to fatten a garden crop too fast. "
                    "Unspecified choices are picked at random (seeded)."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--contest", choices=CONTESTS)
    ap.add_argument("--crop", choices=CROPS)
    ap.add_argument("--shortcut", choices=SHORTCUTS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--adult", choices=["mother", "father"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], help="how long the garden trouble sits before help")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_kid(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.crop:
        setting = SETTINGS[args.setting]
        crop = CROPS[args.crop]
        if not crop_at_risk(setting, crop):
            raise StoryError(explain_crop_rejection(setting, crop))
    if args.shortcut and SHORTCUTS[args.shortcut].sense < SENSE_MIN:
        raise StoryError(explain_shortcut(args.shortcut))
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))

    combos = [
        combo for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.crop is None or combo[1] == args.crop)
        and (args.shortcut is None or combo[2] == args.shortcut)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, crop_id, shortcut_id = rng.choice(sorted(combos))
    contest_id = args.contest or rng.choice(sorted(CONTESTS))
    response_id = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    instigator, instigator_gender = _pick_kid(rng)
    helper, helper_gender = _pick_kid(rng, avoid=instigator)
    adult_type = args.adult or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    relation = rng.choice(["siblings", "friends"])
    instigator_age, helper_age = rng.sample([3, 4, 5, 6, 7], 2)
    return StoryParams(
        setting=setting_id,
        contest=contest_id,
        crop=crop_id,
        shortcut=shortcut_id,
        response=response_id,
        instigator=instigator,
        instigator_gender=instigator_gender,
        helper=helper,
        helper_gender=helper_gender,
        adult=adult_type,
        trait=trait,
        delay=delay,
        instigator_age=instigator_age,
        helper_age=helper_age,
        relation=relation,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting: {params.setting})")
    if params.contest not in CONTESTS:
        raise StoryError(f"(Unknown contest: {params.contest})")
    if params.crop not in CROPS:
        raise StoryError(f"(Unknown crop: {params.crop})")
    if params.shortcut not in SHORTCUTS:
        raise StoryError(f"(Unknown shortcut: {params.shortcut})")
    if params.response not in RESPONSES:
        raise StoryError(f"(Unknown response: {params.response})")

    setting = SETTINGS[params.setting]
    crop = CROPS[params.crop]
    shortcut = SHORTCUTS[params.shortcut]
    response = RESPONSES[params.response]

    if not crop_at_risk(setting, crop):
        raise StoryError(explain_crop_rejection(setting, crop))
    if shortcut.sense < SENSE_MIN:
        raise StoryError(explain_shortcut(params.shortcut))
    if response.sense < SENSE_MIN:
        raise StoryError(explain_response(params.response))

    world = tell(
        setting=setting,
        contest=CONTESTS[params.contest],
        crop_cfg=crop,
        shortcut=shortcut,
        response=response,
        instigator=params.instigator,
        instigator_gender=params.instigator_gender,
        helper=params.helper,
        helper_gender=params.helper_gender,
        trait=params.trait,
        adult_type=params.adult,
        delay=params.delay,
        instigator_age=params.instigator_age,
        helper_age=params.helper_age,
        relation=params.relation,
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
        print(asp_program("", "#show valid/3.\n#show good_shortcut/1.\n#show good_response/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"sensible shortcuts: {', '.join(asp_sensible_shortcuts())}")
        print(f"sensible responses: {', '.join(asp_sensible_responses())}\n")
        print(f"{len(combos)} compatible (setting, crop, shortcut) combos:\n")
        for setting_id, crop_id, shortcut_id in combos:
            print(f"  {setting_id:18} {crop_id:10} {shortcut_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = (
                f"### {p.instigator} & {p.helper}: {p.crop} with {p.shortcut} "
                f"at {p.setting} ({outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
