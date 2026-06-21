#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/perspective_sample_prowl_happy_ending_twist_lesson.py
=================================================================================

A standalone story world about a child at a twilight stand who notices a missing
sample, goes on a little prowl, then learns to look from another perspective.
The twist is that the "thief" is only a small hungry animal, not a scary sneaky
monster. The ending stays happy: the child protects the stall kindly, shares one
safe treat away from the table, and learns to ask why before blaming.

The prose aims for a gentle rhyming-story feel, while the world model still
drives the turn:

    exposed sample + hungry nearby prowler -> one sample goes missing
    new perspective                         -> suspicion softens into empathy
    covered tray + gentle offering away     -> prowler eats, leaves, peace returns

Run it
------
    python storyworlds/worlds/gpt-5.4/perspective_sample_prowl_happy_ending_twist_lesson.py
    python storyworlds/worlds/gpt-5.4/perspective_sample_prowl_happy_ending_twist_lesson.py --setting moon_market --sample nut_cookie --prowler squirrel
    python storyworlds/worlds/gpt-5.4/perspective_sample_prowl_happy_ending_twist_lesson.py --sample cheese_cracker --prowler rabbit
    python storyworlds/worlds/gpt-5.4/perspective_sample_prowl_happy_ending_twist_lesson.py --response chase
    python storyworlds/worlds/gpt-5.4/perspective_sample_prowl_happy_ending_twist_lesson.py --all
    python storyworlds/worlds/gpt-5.4/perspective_sample_prowl_happy_ending_twist_lesson.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/perspective_sample_prowl_happy_ending_twist_lesson.py --verify
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
INSIGHTFUL_TRAITS = {"patient", "curious", "gentle"}


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
        female = {"girl", "mother", "mom", "woman", "grandmother"}
        male = {"boy", "father", "dad", "man", "grandfather"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

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
class Setting:
    id: str
    place: str
    glow: str
    shelter: str
    perch: str
    affords: set[str] = field(default_factory=set)
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
class SampleFood:
    id: str
    label: str
    phrase: str
    crumbs: str
    plural: bool = False
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
class Prowler:
    id: str
    label: str
    phrase: str
    tracks: str
    reveal: str
    likes: set[str] = field(default_factory=set)
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
class Response:
    id: str
    sense: int
    text: str
    qa_text: str
    fail_reason: str
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
        clone.facts = dict(self.facts)
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


def _r_nibble(world: World) -> list[str]:
    tray = world.get("tray")
    prowler = world.get("prowler")
    hero = world.get("hero")
    if tray.meters["exposed"] < THRESHOLD:
        return []
    if prowler.meters["nearby"] < THRESHOLD or prowler.meters["hungry"] < THRESHOLD:
        return []
    sig = ("nibble", world.facts["sample"].id, world.facts["prowler_cfg"].id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    tray.meters["missing"] += 1
    tray.meters["samples"] = max(0.0, tray.meters["samples"] - 1.0)
    hero.memes["worry"] += 1
    hero.memes["suspicion"] += 1
    hero.meters["steps"] += 1
    return ["__nibble__"]


def _r_reframe(world: World) -> list[str]:
    hero = world.get("hero")
    if hero.memes["perspective"] < THRESHOLD or hero.memes["suspicion"] < THRESHOLD:
        return []
    sig = ("reframe", hero.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["suspicion"] = 0.0
    hero.memes["empathy"] += 1
    hero.memes["fear"] = 0.0
    return ["__reframe__"]


def _r_resolve(world: World) -> list[str]:
    tray = world.get("tray")
    prowler = world.get("prowler")
    hero = world.get("hero")
    if tray.meters["covered"] < THRESHOLD or tray.meters["offering_away"] < THRESHOLD:
        return []
    if prowler.meters["nearby"] < THRESHOLD or prowler.meters["hungry"] < THRESHOLD:
        return []
    sig = ("resolve", prowler.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    prowler.meters["hungry"] = 0.0
    prowler.meters["nearby"] = 0.0
    prowler.meters["fed"] += 1
    hero.memes["relief"] += 1
    hero.memes["pride"] += 1
    return ["__resolve__"]


CAUSAL_RULES = [
    Rule(name="nibble", tag="physical", apply=_r_nibble),
    Rule(name="reframe", tag="social", apply=_r_reframe),
    Rule(name="resolve", tag="physical", apply=_r_resolve),
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
                produced.extend(x for x in out if not x.startswith("__"))
    if narrate:
        for line in produced:
            world.say(line)
    return produced


def compatible(setting: Setting, sample: SampleFood, prowler: Prowler) -> bool:
    return prowler.id in setting.affords and sample.id in prowler.likes


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def notices_alone(trait: str) -> bool:
    return trait in INSIGHTFUL_TRAITS


def outcome_of(params: "StoryParams") -> str:
    return "self_shift" if notices_alone(params.trait) else "helper_shift"


def explain_rejection(setting: Setting, sample: SampleFood, prowler: Prowler) -> str:
    if prowler.id not in setting.affords:
        return (
            f"(No story: {prowler.label} does not fit {setting.place} here, so there is no "
            f"reasonable prowler for the child to find.)"
        )
    if sample.id not in prowler.likes:
        return (
            f"(No story: {prowler.label} would not be drawn to {sample.phrase}, so the missing "
            f"sample clue would not make sense.)"
        )
    return "(No story: this combination does not form a reasonable little mystery.)"


def explain_response(rid: str) -> str:
    r = RESPONSES[rid]
    better = ", ".join(sorted(x.id for x in sensible_responses()))
    return (
        f"(Refusing response '{rid}': it scores too low on common sense "
        f"(sense={r.sense} < {SENSE_MIN}). Try a gentler solution such as {better}.)"
    )


def predict_missing(world: World) -> dict:
    sim = world.copy()
    propagate(sim, narrate=False)
    tray = sim.get("tray")
    return {
        "missing": tray.meters["missing"] >= THRESHOLD,
        "samples_left": tray.meters["samples"],
    }


def rhyme_intro(world: World, hero: Entity, helper: Entity, sample: SampleFood) -> None:
    world.say(
        f"At {world.setting.place}, in {world.setting.glow}, {hero.id} helped {helper.label_word} set things just so."
    )
    world.say(
        f"They laid out {sample.phrase} in a neat little row, sweet for a sample, soft in the glow."
    )


def first_loss(world: World, hero: Entity, sample: SampleFood) -> None:
    pred = predict_missing(world)
    world.facts["predicted_missing"] = pred["missing"]
    world.say(
        f"But when {hero.id} looked back, one piece was gone. {sample.crumbs} marked the cloth where the treat had shone."
    )
    world.say(
        f'"Who would take a sample and slip off on the prowl?" {hero.id} whispered, with a puzzled little scowl.'
    )


def decide_to_prowl(world: World, hero: Entity) -> None:
    hero.memes["fear"] += 1
    hero.meters["steps"] += 1
    world.say(
        f"So {hero.id} made a hush-hush prowl by {world.setting.shelter}, where leaves gave tiny shivers and shadows looked welter."
    )


def notice_clue(world: World, hero: Entity, prowler: Prowler) -> None:
    world.say(
        f"By {world.setting.perch}, {hero.id} found {prowler.tracks}; the clue was so small it changed all the tracks."
    )


def helper_prompt(world: World, hero: Entity, helper: Entity) -> None:
    world.say(
        f'{helper.label_word.capitalize()} came softly and said, "Try another perspective before you fill up with dread."'
    )
    world.say(
        f'"Kneel low by the lantern, and look near the ground. Big shadows can puff up what is little and round."'
    )
    hero.memes["perspective"] += 1
    propagate(world, narrate=False)


def self_prompt(world: World, hero: Entity) -> None:
    world.say(
        f"{hero.id} paused by the lantern and took a slow breath. \"From another perspective, this may not be theft.\""
    )
    hero.memes["perspective"] += 1
    propagate(world, narrate=False)


def reveal_twist(world: World, prowler: Prowler) -> None:
    world.say(
        f"And there was the twist in the hush of the night: {prowler.reveal}, not a robber in flight."
    )


def kind_fix(world: World, hero: Entity, helper: Entity, response: Response, sample: SampleFood) -> None:
    tray = world.get("tray")
    tray.meters["covered"] += 1
    tray.meters["offering_away"] += 1
    tray.meters["exposed"] = 0.0
    world.say(
        f"{hero.id} and {helper.label_word} {response.text.format(sample=sample.label, perch=world.setting.perch)}."
    )
    propagate(world, narrate=False)


def lesson(world: World, hero: Entity, helper: Entity) -> None:
    world.say(
        f'{helper.label_word.capitalize()} smiled. "When something seems strange, try perspective before blame or anger arrange."'
    )
    world.say(
        f'{hero.id} nodded. "A clue can look scary till kindness looks through. Then the right thing to do can come clearly in view."'
    )


def happy_end(world: World, hero: Entity, helper: Entity, sample: SampleFood, prowler: Prowler) -> None:
    world.say(
        f"Soon the stand stayed tidy, the night stayed bright, and the little {prowler.label} nibbled away out of sight."
    )
    world.say(
        f"{hero.id} served the next sample with a grin warm and wide, while moonlight and good sense stood side by side."
    )


def tell(
    setting: Setting,
    sample: SampleFood,
    prowler_cfg: Prowler,
    response: Response,
    hero_name: str = "Lina",
    hero_type: str = "girl",
    helper_type: str = "mother",
    trait: str = "patient",
) -> World:
    world = World(setting)
    hero = world.add(
        Entity(
            id=hero_name,
            kind="character",
            type=hero_type,
            role="hero",
            traits=[trait],
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
    tray = world.add(
        Entity(
            id="tray",
            type="tray",
            label="sample tray",
        )
    )
    prowler = world.add(
        Entity(
            id="prowler",
            type="animal",
            label=prowler_cfg.label,
            role="prowler",
        )
    )

    world.facts.update(
        setting=setting,
        sample=sample,
        prowler_cfg=prowler_cfg,
        response=response,
        hero=hero,
        helper=helper,
        tray=tray,
        predicted_missing=False,
    )

    tray.meters["samples"] = 4.0
    tray.meters["exposed"] = 1.0
    tray.meters["covered"] = 0.0
    tray.meters["offering_away"] = 0.0
    tray.meters["missing"] = 0.0
    prowler.meters["nearby"] = 1.0
    prowler.meters["hungry"] = 1.0
    prowler.meters["fed"] = 0.0
    hero.memes["worry"] = 0.0
    hero.memes["suspicion"] = 0.0
    hero.memes["fear"] = 0.0
    hero.memes["perspective"] = 0.0
    hero.memes["empathy"] = 0.0
    hero.memes["relief"] = 0.0
    hero.memes["pride"] = 0.0
    hero.meters["steps"] = 0.0

    rhyme_intro(world, hero, helper, sample)

    world.para()
    propagate(world, narrate=False)
    first_loss(world, hero, sample)
    decide_to_prowl(world, hero)
    notice_clue(world, hero, prowler_cfg)

    world.para()
    if notices_alone(trait):
        self_prompt(world, hero)
        shift = "self_shift"
    else:
        helper_prompt(world, hero, helper)
        shift = "helper_shift"
    reveal_twist(world, prowler_cfg)
    kind_fix(world, hero, helper, response, sample)
    lesson(world, hero, helper)

    world.para()
    happy_end(world, hero, helper, sample, prowler_cfg)

    world.facts.update(
        shift=shift,
        missing=tray.meters["missing"] >= THRESHOLD,
        fed=prowler.meters["fed"] >= THRESHOLD,
        lesson_learned=hero.memes["perspective"] >= THRESHOLD and hero.memes["empathy"] >= THRESHOLD,
    )
    return world


SETTINGS = {
    "moon_market": Setting(
        id="moon_market",
        place="the moon market",
        glow="lantern glow",
        shelter="the herb hedge",
        perch="the apple crate",
        affords={"mouse", "squirrel"},
        tags={"market", "night"},
    ),
    "garden_gate": Setting(
        id="garden_gate",
        place="the garden gate",
        glow="evening glow",
        shelter="the bean vines",
        perch="the watering stool",
        affords={"rabbit", "mouse"},
        tags={"garden", "night"},
    ),
    "orchard_path": Setting(
        id="orchard_path",
        place="the orchard path",
        glow="dusky gold",
        shelter="the berry bushes",
        perch="the little stump",
        affords={"rabbit", "squirrel"},
        tags={"orchard", "night"},
    ),
}

SAMPLES = {
    "apple_slice": SampleFood(
        id="apple_slice",
        label="apple slices",
        phrase="a plate of crisp apple slices",
        crumbs="A few pale crumbs and a wet little shine",
        plural=True,
        tags={"sample", "apple"},
    ),
    "nut_cookie": SampleFood(
        id="nut_cookie",
        label="nut cookies",
        phrase="a tray of nut cookies",
        crumbs="A dusting of crumbs and one tiny bite line",
        plural=True,
        tags={"sample", "cookie"},
    ),
    "cheese_cracker": SampleFood(
        id="cheese_cracker",
        label="cheese crackers",
        phrase="a basket of cheese crackers",
        crumbs="A golden flake trail and a nibble so fine",
        plural=True,
        tags={"sample", "cracker"},
    ),
    "carrot_round": SampleFood(
        id="carrot_round",
        label="carrot rounds",
        phrase="a bowl of sweet carrot rounds",
        crumbs="A bright orange crumb and a half-moon sign",
        plural=True,
        tags={"sample", "carrot"},
    ),
}

PROWLERS = {
    "rabbit": Prowler(
        id="rabbit",
        label="rabbit",
        phrase="a small gray rabbit",
        tracks="two neat hopping prints",
        reveal="a rabbit with twitching ears and a crumb on its lip",
        likes={"apple_slice", "carrot_round"},
        tags={"rabbit", "animal"},
    ),
    "squirrel": Prowler(
        id="squirrel",
        label="squirrel",
        phrase="a quick brown squirrel",
        tracks="fine scratchy prints with a tail sweep",
        reveal="a squirrel with bright bead eyes and cookie dust on its chin",
        likes={"nut_cookie", "apple_slice"},
        tags={"squirrel", "animal"},
    ),
    "mouse": Prowler(
        id="mouse",
        label="mouse",
        phrase="a tiny field mouse",
        tracks="pinprick prints beside a narrow crumb trail",
        reveal="a field mouse with round ears and a cracker flake in its paws",
        likes={"cheese_cracker", "nut_cookie"},
        tags={"mouse", "animal"},
    ),
}

RESPONSES = {
    "leaf_plate": Response(
        id="leaf_plate",
        sense=3,
        text="covered the tray and set one extra {sample} on a leaf by {perch}",
        qa_text="covered the tray and put one extra sample a little way from the stand",
        fail_reason="too rough for a gentle story",
        tags={"kindness", "share"},
    ),
    "little_bowl": Response(
        id="little_bowl",
        sense=3,
        text="covered the tray and left one small piece in a little bowl beside {perch}",
        qa_text="covered the tray and left one small piece in a little bowl away from the tray",
        fail_reason="too rough for a gentle story",
        tags={"kindness", "share"},
    ),
    "chase": Response(
        id="chase",
        sense=1,
        text="ran after the prowler waving their arms",
        qa_text="chased the animal away",
        fail_reason="it scares the animal and teaches blame instead of understanding",
        tags={"rough"},
    ),
}

GIRL_NAMES = ["Lina", "Maya", "Nora", "Zoe", "Ella", "Ivy", "Tessa", "Ruby"]
BOY_NAMES = ["Milo", "Theo", "Finn", "Owen", "Eli", "Noah", "Ben", "Jude"]
TRAITS = ["patient", "curious", "gentle", "hasty", "bold", "bouncy"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    if not sensible_responses():
        return combos
    for sid, setting in SETTINGS.items():
        for food_id, sample in SAMPLES.items():
            for pid, prowler in PROWLERS.items():
                if compatible(setting, sample, prowler):
                    combos.append((sid, food_id, pid))
    return combos


@dataclass
class StoryParams:
    setting: str
    sample: str
    prowler: str
    response: str
    name: str
    gender: str
    helper: str
    trait: str
    seed: Optional[int] = None
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


KNOWLEDGE = {
    "perspective": [
        (
            "What does perspective mean?",
            "Perspective means the way something looks from where you are standing or thinking. If you change your place or your thinking, the same clue can make more sense."
        )
    ],
    "sample": [
        (
            "What is a sample?",
            "A sample is a small taste of food so someone can try it. It is only a little piece, not the whole plate."
        )
    ],
    "prowl": [
        (
            "What does prowl mean?",
            "To prowl means to move around quietly while looking for something. Animals often prowl softly when they are hungry or curious."
        )
    ],
    "rabbit": [
        (
            "Why does a rabbit nibble plants and vegetables?",
            "Rabbits eat plant food, so sweet vegetables and fruit can smell tempting to them. They use quick little bites because their teeth are made for nibbling."
        )
    ],
    "squirrel": [
        (
            "Why might a squirrel come near a snack stand?",
            "Squirrels notice nutty smells very quickly. If food is left out, a squirrel may scamper close to investigate."
        )
    ],
    "mouse": [
        (
            "Why does a mouse follow crumbs?",
            "A mouse has a tiny body and a sharp nose, so crumbs can be enough to attract it. Little trails help it find safe bits of food."
        )
    ],
    "kindness": [
        (
            "Why is it good to solve a problem kindly?",
            "A kind solution protects people and also avoids needless fear. It helps you fix the trouble without making a small problem bigger."
        )
    ],
}
KNOWLEDGE_ORDER = ["perspective", "sample", "prowl", "rabbit", "squirrel", "mouse", "kindness"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    sample = f["sample"]
    prowler = f["prowler_cfg"]
    shift = f["shift"]
    if shift == "self_shift":
        second = (
            f"Tell a rhyming story where {hero.id} notices a missing sample, goes on a quiet prowl, "
            f"and changes {hero.pronoun('possessive')} own perspective before discovering a hungry {prowler.label}."
        )
    else:
        second = (
            f"Tell a rhyming story where {hero.id} notices a missing sample, goes on a quiet prowl, "
            f"and a calm {helper.label_word} teaches {hero.pronoun('object')} to try another perspective."
        )
    return [
        'Write a short rhyming story for a 3-to-5-year-old that uses the words "perspective", "sample", and "prowl", with a twist, a lesson, and a happy ending.',
        second,
        f'Write a gentle story in verse where a child guarding {sample.phrase} thinks something sneaky is near, but the twist reveals a hungry {prowler.label} and the lesson is to look kindly before blaming.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    sample = f["sample"]
    prowler = f["prowler_cfg"]
    response = f["response"]
    shift = f["shift"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, who was helping {hero.pronoun('possessive')} {helper.label_word} with {sample.phrase}. It is also about a little {prowler.label} that came near because it was hungry."
        ),
        (
            "Why did the child go on a prowl?",
            f"{hero.id} saw that one sample was missing and wanted to know who had taken it. The crumbs and tiny signs by the stand made the mystery feel real."
        ),
        (
            "What was the twist?",
            f"The twist was that the 'thief' was not a scary robber at all. It was really {prowler.phrase}, drawn close by the smell of the food."
        ),
    ]
    if shift == "self_shift":
        qa.append(
            (
                f"How did {hero.id} change the story by using perspective?",
                f"{hero.id} stopped and looked again from a calmer perspective before deciding anything. That helped {hero.pronoun('object')} notice the tiny tracks and understand that a small hungry animal had taken the sample, not a mean sneaky stranger."
            )
        )
    else:
        qa.append(
            (
                f"How did {helper.label_word} help {hero.id} use perspective?",
                f"{helper.label_word.capitalize()} told {hero.id} to try another perspective and look low near the lantern. That changed a big spooky shadow into the clear sight of a small hungry {prowler.label}."
            )
        )
    qa.append(
        (
            "How did they solve the problem?",
            f"They {response.qa_text}. That way the stand stayed neat, and the little {prowler.label} got something safe without snatching from the table."
        )
    )
    qa.append(
        (
            "What lesson did the child learn?",
            f"{hero.id} learned not to blame too quickly when something looks strange. A kinder perspective can turn fear into understanding and lead to a better fix."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"perspective", "sample", "prowl", "kindness"}
    tags |= set(f["prowler_cfg"].tags)
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
        if e.role:
            bits.append(f"role={e.role}")
        if e.traits:
            bits.append(f"traits={e.traits}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="moon_market",
        sample="nut_cookie",
        prowler="squirrel",
        response="leaf_plate",
        name="Lina",
        gender="girl",
        helper="mother",
        trait="patient",
    ),
    StoryParams(
        setting="garden_gate",
        sample="carrot_round",
        prowler="rabbit",
        response="little_bowl",
        name="Milo",
        gender="boy",
        helper="father",
        trait="hasty",
    ),
    StoryParams(
        setting="orchard_path",
        sample="apple_slice",
        prowler="rabbit",
        response="leaf_plate",
        name="Nora",
        gender="girl",
        helper="grandmother",
        trait="curious",
    ),
    StoryParams(
        setting="moon_market",
        sample="cheese_cracker",
        prowler="mouse",
        response="little_bowl",
        name="Theo",
        gender="boy",
        helper="grandfather",
        trait="bouncy",
    ),
]


ASP_RULES = r"""
% --- reasonableness gate ---------------------------------------------------
likes_sample(P, S) :- likes(P, S).
fits_setting(Place, P) :- affords(Place, P).
valid(Place, S, P) :- setting(Place), sample(S), prowler(P), fits_setting(Place, P), likes_sample(P, S).

sensible(R) :- response(R), sense(R, N), sense_min(M), N >= M.

% --- branch of the perspective twist --------------------------------------
insightful(patient).
insightful(curious).
insightful(gentle).

self_shift :- trait(T), insightful(T).
helper_shift :- trait(T), not insightful(T).

outcome(self_shift) :- self_shift.
outcome(helper_shift) :- helper_shift.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for pid in sorted(s.affords):
            lines.append(asp.fact("affords", sid, pid))
    for food_id in SAMPLES:
        lines.append(asp.fact("sample", food_id))
    for pid, prowler in PROWLERS.items():
        lines.append(asp.fact("prowler", pid))
        for liked in sorted(prowler.likes):
            lines.append(asp.fact("likes", pid, liked))
    for rid, response in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, response.sense))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    for trait in sorted(TRAITS):
        lines.append(asp.fact("trait_name", trait))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = asp.fact("trait", params.trait)
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0

    c_valid = set(asp_valid_combos())
    p_valid = set(valid_combos())
    if c_valid == p_valid:
        print(f"OK: gate matches valid_combos() ({len(c_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if c_valid - p_valid:
            print("  only in clingo:", sorted(c_valid - p_valid))
        if p_valid - c_valid:
            print("  only in python:", sorted(p_valid - c_valid))

    c_sens = set(asp_sensible())
    p_sens = {r.id for r in sensible_responses()}
    if c_sens == p_sens:
        print(f"OK: sensible responses match ({sorted(c_sens)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible responses: clingo={sorted(c_sens)} python={sorted(p_sens)}")

    cases = list(CURATED)
    for s in range(100):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(s))
            params.seed = s
            cases.append(params)
        except StoryError:
            rc = 1
            print(f"Unexpected StoryError while resolving seed {s}.")
            break
    mismatches = [p for p in cases if asp_outcome(p) != outcome_of(p)]
    if not mismatches:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {len(mismatches)}/{len(cases)} outcome branches differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("empty story")
        print("OK: smoke test generated a normal story.")
    except Exception as exc:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a missing sample, a quiet prowl, a kinder perspective."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--sample", choices=SAMPLES)
    ap.add_argument("--prowler", choices=PROWLERS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=["mother", "father", "grandmother", "grandfather"])
    ap.add_argument("--name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program (facts + inline rules)")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.sample and args.prowler:
        setting = SETTINGS[args.setting]
        sample = SAMPLES[args.sample]
        prowler = PROWLERS[args.prowler]
        if not compatible(setting, sample, prowler):
            raise StoryError(explain_rejection(setting, sample, prowler))
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))

    combos = [
        combo
        for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.sample is None or combo[1] == args.sample)
        and (args.prowler is None or combo[2] == args.prowler)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, sample_id, prowler_id = rng.choice(sorted(combos))
    response_id = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = args.helper or rng.choice(["mother", "father", "grandmother", "grandfather"])
    trait = rng.choice(TRAITS)
    return StoryParams(
        setting=setting_id,
        sample=sample_id,
        prowler=prowler_id,
        response=response_id,
        name=name,
        gender=gender,
        helper=helper,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting: {params.setting})")
    if params.sample not in SAMPLES:
        raise StoryError(f"(Unknown sample: {params.sample})")
    if params.prowler not in PROWLERS:
        raise StoryError(f"(Unknown prowler: {params.prowler})")
    if params.response not in RESPONSES:
        raise StoryError(f"(Unknown response: {params.response})")

    setting = SETTINGS[params.setting]
    sample = SAMPLES[params.sample]
    prowler = PROWLERS[params.prowler]
    response = RESPONSES[params.response]

    if not compatible(setting, sample, prowler):
        raise StoryError(explain_rejection(setting, sample, prowler))
    if response.sense < SENSE_MIN:
        raise StoryError(explain_response(params.response))

    world = tell(
        setting=setting,
        sample=sample,
        prowler_cfg=prowler,
        response=response,
        hero_name=params.name,
        hero_type=params.gender,
        helper_type=params.helper,
        trait=params.trait,
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
        print(asp_program("", "#show valid/3.\n#show sensible/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, sample, prowler) combos:\n")
        for setting, sample, prowler in combos:
            print(f"  {setting:12} {sample:14} {prowler}")
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
            header = f"### {p.name}: {p.sample} at {p.setting} ({p.prowler}, {outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
