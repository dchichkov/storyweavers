#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/cerely_belong_gerund_flashback_tall_tale.py
======================================================================

A standalone story world for a tiny Tall-Tale-style county-fair domain built
around a giant garden exhibit, a threatening mishap, and a flashback that helps
a child remember the right fix.

Seed requirements carried into the world:
- includes the exact words "cerely" and "belong-gerund"
- includes a true flashback beat
- keeps the style close to a child-facing tall tale

Run it
------
python storyworlds/worlds/gpt-5.4/cerely_belong_gerund_flashback_tall_tale.py
python storyworlds/worlds/gpt-5.4/cerely_belong_gerund_flashback_tall_tale.py --crop sunflower --trouble wind
python storyworlds/worlds/gpt-5.4/cerely_belong_gerund_flashback_tall_tale.py --fix singing
python storyworlds/worlds/gpt-5.4/cerely_belong_gerund_flashback_tall_tale.py --all
python storyworlds/worlds/gpt-5.4/cerely_belong_gerund_flashback_tall_tale.py -n 5 --seed 7 --qa
python storyworlds/worlds/gpt-5.4/cerely_belong_gerund_flashback_tall_tale.py --verify
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
FLASHBACK_TRAITS = {"mindful", "careful", "steady"}


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
        female = {"girl", "mother", "grandmother", "woman", "aunt"}
        male = {"boy", "father", "grandfather", "man", "uncle"}
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
        }.get(self.type, self.type)
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
    boast: str
    fair_name: str
    trouble_ids: set[str] = field(default_factory=set)
    base_severity: int = 2
    ending_good: str = ""
    ending_bad: str = ""
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
class Trouble:
    id: str
    label: str
    sign: str
    meter: str
    threat_text: str
    qa_phrase: str
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
class Fix:
    id: str
    label: str
    covers: set[str] = field(default_factory=set)
    sense: int = 0
    power: int = 0
    prep: str = ""
    success: str = ""
    fail: str = ""
    qa_text: str = ""
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


def _r_risk(world: World) -> list[str]:
    crop = world.entities.get("crop")
    hero = world.entities.get("hero")
    if crop is None or hero is None:
        return []
    for meter in ("lean", "droop", "roll"):
        if crop.meters[meter] < THRESHOLD:
            continue
        sig = ("risk", meter)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        crop.meters["risk"] += 1
        hero.memes["worry"] += 1
        return ["__risk__"]
    return []


def _r_damage(world: World) -> list[str]:
    crop = world.entities.get("crop")
    if crop is None:
        return []
    delay = int(world.facts.get("delay", 0))
    if crop.meters["risk"] < THRESHOLD or delay <= 0:
        return []
    sig = ("damage", delay)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    crop.meters["damage"] += float(delay)
    return []


CAUSAL_RULES = [
    Rule(name="risk", tag="physical", apply=_r_risk),
    Rule(name="damage", tag="physical", apply=_r_damage),
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
        for sent in produced:
            world.say(sent)
    return produced


def hazard_at_risk(crop: Crop, trouble: Trouble) -> bool:
    return trouble.id in crop.trouble_ids


def sensible_fixes() -> list[Fix]:
    return [f for f in FIXES.values() if f.sense >= SENSE_MIN]


def fix_handles(fix: Fix, trouble: Trouble) -> bool:
    return trouble.id in fix.covers


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for crop_id, crop in CROPS.items():
        for trouble_id, trouble in TROUBLES.items():
            if not hazard_at_risk(crop, trouble):
                continue
            for fix_id, fix in FIXES.items():
                if fix.sense >= SENSE_MIN and fix_handles(fix, trouble):
                    combos.append((crop_id, trouble_id, fix_id))
    return combos


def preemptive_flashback(trait: str, keepsake: bool, delay: int) -> bool:
    return keepsake and trait in FLASHBACK_TRAITS and delay == 0


def severity_of(crop: Crop, delay: int) -> int:
    return crop.base_severity + delay


def contained(fix: Fix, crop: Crop, delay: int) -> bool:
    return fix.power >= severity_of(crop, delay)


def outcome_of(params: "StoryParams") -> str:
    if preemptive_flashback(params.trait, params.keepsake, params.delay):
        return "steady"
    crop = CROPS[params.crop]
    fix = FIXES[params.fix]
    return "saved" if contained(fix, crop, params.delay) else "spoiled"


def apply_trouble(world: World, trouble: Trouble, narrate: bool = True) -> None:
    crop = world.get("crop")
    crop.meters[trouble.meter] += 1
    propagate(world, narrate=narrate)


def predict_trouble(world: World, trouble: Trouble) -> dict:
    sim = world.copy()
    apply_trouble(sim, trouble, narrate=False)
    crop = sim.get("crop")
    hero = sim.get("hero")
    return {
        "risk": crop.meters["risk"],
        "damage": crop.meters["damage"],
        "worry": hero.memes["worry"],
    }


def tall_opening(world: World, hero: Entity, crop_cfg: Crop) -> None:
    hero.memes["pride"] += 1
    world.say(
        f"{hero.id} had grown {crop_cfg.phrase} behind the family shed, and {crop_cfg.boast}."
    )
    world.say(
        f"By the week of the county fair, folks had begun calling it "
        f'"{crop_cfg.fair_name}," which was the sort of name a thing gets only after it has become bigger than common sense.'
    )


def fair_plan(world: World, hero: Entity, helper: Entity, crop_cfg: Crop) -> None:
    world.say(
        f"{hero.id} and {helper.id} rolled out before sunrise to carry the great "
        f"{crop_cfg.label} to the fairgrounds."
    )
    world.say(
        f"They felt so proud that even the wagon wheels seemed to hum a victory tune."
    )


def trouble_arrives(world: World, hero: Entity, trouble: Trouble) -> None:
    hero.memes["alarm"] += 1
    world.say(
        f"But halfway there, {trouble.sign}."
    )
    world.say(
        f"{hero.id} saw at once that {trouble.threat_text}"
    )


def flashback(world: World, hero: Entity, mentor: Entity, trouble: Trouble) -> None:
    hero.memes["memory"] += 1
    keepsake_text = ""
    if hero.attrs.get("keepsake"):
        keepsake_text = f" As {hero.pronoun()} touched the smooth lucky button in {hero.pronoun('possessive')} pocket,"
    world.say(
        f"{keepsake_text} a springtime picture opened in {hero.pronoun('possessive')} mind like a little door."
    )
    world.say(
        f"In the flashback, {mentor.label_word.capitalize()} stood by the seed rows and said, "
        f'"Grow it cerely, child. The minute a prize starts belong-gerund to trouble, '
        f'you answer with the right fix, not the fastest fuss."'
    )
    world.say(
        f"That memory steadied {hero.id} enough to stop staring and start thinking."
    )


def preempt_fix(world: World, hero: Entity, helper: Entity, fix: Fix, crop_cfg: Crop) -> None:
    crop = world.get("crop")
    crop.meters["stable"] += 1
    hero.memes["relief"] += 1
    hero.memes["confidence"] += 1
    world.say(
        f"Before the trouble could take a proper bite, {hero.id} remembered what to do."
    )
    world.say(
        f"{hero.pronoun().capitalize()} and {helper.id} {fix.prep}, and soon {fix.success}"
    )
    world.say(
        f"The mighty {crop_cfg.label} never lost so much as a proud shiver."
    )


def damage_scene(world: World, hero: Entity, crop_cfg: Crop, trouble: Trouble) -> None:
    apply_trouble(world, trouble, narrate=False)
    world.say(
        f"In one hard minute, {trouble.threat_text}"
    )
    if world.get("crop").meters["damage"] >= THRESHOLD:
        world.say(
            f"{hero.id}'s heart sank, because the big {crop_cfg.label} had already begun to look less like a legend and more like a worry."
        )


def rescue(world: World, hero: Entity, helper: Entity, fix: Fix, crop_cfg: Crop) -> None:
    crop = world.get("crop")
    crop.meters["stable"] += 1
    crop.meters["risk"] = 0.0
    crop.meters["lean"] = 0.0
    crop.meters["droop"] = 0.0
    crop.meters["roll"] = 0.0
    hero.memes["relief"] += 1
    hero.memes["gratitude"] += 1
    world.say(
        f"{hero.id} called to {helper.id}, and together they {fix.prep}."
    )
    world.say(
        f"Soon {fix.success}"
    )
    world.say(
        f"The fair road stopped feeling like a place of trouble and started feeling like a road to glory again."
    )


def spoil(world: World, hero: Entity, helper: Entity, fix: Fix, crop_cfg: Crop) -> None:
    crop = world.get("crop")
    crop.meters["spoiled"] += 1
    hero.memes["sadness"] += 1
    hero.memes["gratitude"] += 1
    world.say(
        f"{hero.id} and {helper.id} tried to help by {fix.prep}, but {fix.fail}"
    )
    world.say(
        f"By the time they reached the fair, the giant {crop_cfg.label} was still huge, but it no longer looked like a ribbon winner."
    )


def good_ending(world: World, hero: Entity, helper: Entity, crop_cfg: Crop, outcome: str) -> None:
    hero.memes["joy"] += 1
    if outcome == "steady":
        world.say(
            f"At the fair, children stretched on tiptoe to see it, and the judges laughed the happy laugh people use when a story has somehow become true."
        )
    else:
        world.say(
            f"At the fair, the judges walked all the way around it twice before pinning on a blue ribbon big enough to flap in the breeze."
        )
    world.say(
        crop_cfg.ending_good
    )
    world.say(
        f"That evening, {hero.id} went home taller on the inside, knowing a grand thing stays grand only when somebody keeps a calm head beside it."
    )


def bad_ending(world: World, hero: Entity, helper: Entity, crop_cfg: Crop) -> None:
    hero.memes["resolve"] += 1
    world.say(
        f"No ribbon came home with them, but {helper.id} cut out the best seeds and wrapped them in a handkerchief."
    )
    world.say(
        crop_cfg.ending_bad
    )
    world.say(
        f"{hero.id} carried the seed bundle home as carefully as treasure, already planning next year's tall tale."
    )


def tell(
    crop_cfg: Crop,
    trouble: Trouble,
    fix: Fix,
    hero_name: str = "Mira",
    hero_gender: str = "girl",
    helper_type: str = "father",
    mentor_type: str = "grandfather",
    trait: str = "mindful",
    delay: int = 0,
    keepsake: bool = True,
) -> World:
    world = World()
    world.facts["delay"] = delay

    hero = world.add(
        Entity(
            id=hero_name,
            kind="character",
            type=hero_gender,
            label=hero_name,
            role="hero",
            traits=[trait],
            attrs={"keepsake": keepsake},
        )
    )
    helper = world.add(
        Entity(
            id="Helper",
            kind="character",
            type=helper_type,
            label="the helper",
            role="helper",
        )
    )
    mentor = world.add(
        Entity(
            id="Mentor",
            kind="character",
            type=mentor_type,
            label="the mentor",
            role="mentor",
        )
    )
    crop = world.add(
        Entity(
            id="crop",
            kind="thing",
            type="crop",
            label=crop_cfg.label,
            phrase=crop_cfg.phrase,
            role="crop",
        )
    )

    tall_opening(world, hero, crop_cfg)
    fair_plan(world, hero, helper, crop_cfg)

    world.para()
    trouble_arrives(world, hero, trouble)
    pred = predict_trouble(world, trouble)
    world.facts["predicted_risk"] = pred["risk"]
    world.facts["predicted_damage"] = pred["damage"]
    flashback(world, hero, mentor, trouble)

    outcome = "steady" if preemptive_flashback(trait, keepsake, delay) else (
        "saved" if contained(fix, crop_cfg, delay) else "spoiled"
    )

    world.para()
    if outcome == "steady":
        preempt_fix(world, hero, helper, fix, crop_cfg)
    else:
        damage_scene(world, hero, crop_cfg, trouble)
        if outcome == "saved":
            rescue(world, hero, helper, fix, crop_cfg)
        else:
            spoil(world, hero, helper, fix, crop_cfg)

    world.para()
    if outcome in {"steady", "saved"}:
        good_ending(world, hero, helper, crop_cfg, outcome)
    else:
        bad_ending(world, hero, helper, crop_cfg)

    world.facts.update(
        hero=hero,
        helper=helper,
        mentor=mentor,
        crop_cfg=crop_cfg,
        trouble=trouble,
        fix=fix,
        outcome=outcome,
        keepsake=keepsake,
        delay=delay,
        preemptive=(outcome == "steady"),
        saved=(outcome == "saved"),
        spoiled=(outcome == "spoiled"),
    )
    return world


CROPS = {
    "sunflower": Crop(
        id="sunflower",
        label="sunflower",
        phrase="a sunflower so tall it had to nod to passing clouds",
        boast="its shadow reached the chicken coop before breakfast",
        fair_name="Sky-Howdy Sunflower",
        trouble_ids={"wind", "thirst"},
        base_severity=2,
        ending_good="Before supper, its seeds were being counted like little striped coins, and every child in line wanted one for next spring.",
        ending_bad="Still, everybody agreed they had never seen a sunflower with such brave manners, even in defeat.",
        tags={"sunflower", "garden"},
    ),
    "pumpkin": Crop(
        id="pumpkin",
        label="pumpkin",
        phrase="a pumpkin so round it looked like a sunset that had sat down in the dirt",
        boast="three hens once tried to roost behind it, thinking it was a hill",
        fair_name="Moon-Pie Pumpkin",
        trouble_ids={"wobble", "thirst"},
        base_severity=2,
        ending_good="By afternoon, people were swearing its pie could have fed a brass band and still left room for second helpings.",
        ending_bad="Even without a prize, it made enough soup to fill half the fair with warm orange smiles.",
        tags={"pumpkin", "garden", "soup"},
    ),
    "beanvine": Crop(
        id="beanvine",
        label="bean vine",
        phrase="a pole-bean vine so high the top leaves gossiped with chimney smoke",
        boast="its longest runner had to be wound twice around the cart so it would not wave at passing geese",
        fair_name="Cloud-Tickler Beanvine",
        trouble_ids={"wind", "thirst"},
        base_severity=3,
        ending_good="Later, the blue ribbon hung from the wagon rail while neighbors measured beans against their forearms and gave up halfway.",
        ending_bad="Folks still told the story of that vine all winter, which is another sort of winning in a tall-tale town.",
        tags={"beans", "garden"},
    ),
}

TROUBLES = {
    "wind": Trouble(
        id="wind",
        label="wind",
        sign="a prairie gust came bowling across the road hard enough to flip a hat and startle the dust",
        meter="lean",
        threat_text="the giant exhibit leaned and shuddered as if the sky had reached down to give it a shove.",
        qa_phrase="a strong gust made it lean",
        tags={"wind", "weather"},
    ),
    "thirst": Trouble(
        id="thirst",
        label="thirst",
        sign="the sun climbed high and hot, and the morning dew vanished faster than butter on a biscuit",
        meter="droop",
        threat_text="the big leaves began to droop and the whole thing looked thirsty clear to its roots.",
        qa_phrase="heat made it droop with thirst",
        tags={"sun", "water", "weather"},
    ),
    "wobble": Trouble(
        id="wobble",
        label="wobble",
        sign="the wagon hit a rut so deep it could have hidden a terrier",
        meter="roll",
        threat_text="the giant exhibit lurched sideways and started wobbling toward the edge of the wagon bed.",
        qa_phrase="a deep rut made it wobble toward the wagon edge",
        tags={"wagon", "road"},
    ),
}

FIXES = {
    "rope_brace": Fix(
        id="rope_brace",
        label="rope brace",
        covers={"wind"},
        sense=3,
        power=4,
        prep="looped stout rope around the stalk, tied it to the wagon rail, and braced it with a fence post",
        success="the great stem stood firm again, straight as a church steeple",
        fail="the gusts kept batting at it until the bend would not come out",
        qa_text="They tied it fast with rope and a brace so the wind could not push it over.",
        tags={"rope", "wind"},
    ),
    "water_wagon": Fix(
        id="water_wagon",
        label="water wagon",
        covers={"thirst"},
        sense=3,
        power=3,
        prep="hauled up the barrel dipper and gave the roots a long, cool drink",
        success="the leaves lifted again, green and proud",
        fail="the roots had gone too dry for one barrel to cheer them in time",
        qa_text="They gave it a deep drink from the wagon barrel, which helped the thirsty plant lift itself again.",
        tags={"water", "barrel"},
    ),
    "straw_nest": Fix(
        id="straw_nest",
        label="straw nest",
        covers={"wobble"},
        sense=3,
        power=3,
        prep="packed straw thick around the base and wedged the giant thing snug as an egg in a nest",
        success="the wobble stopped and the wagon rolled on without another sideways shimmy",
        fail="the bruise had already spread, and the shell never sat handsome again",
        qa_text="They packed straw around it and wedged it snug so it would stop wobbling on the wagon.",
        tags={"straw", "wagon"},
    ),
    "singing": Fix(
        id="singing",
        label="singing at it",
        covers={"wind", "thirst", "wobble"},
        sense=1,
        power=1,
        prep="sang to it at the top of their lungs",
        success="it somehow behaved itself",
        fail="a song was not enough to mend the trouble",
        qa_text="They sang at it, but singing is not a practical fix for a real garden mishap.",
        tags={"silly"},
    ),
}

GIRL_NAMES = ["Mira", "June", "Tessa", "Nell", "Willa", "Daisy", "Ruth", "Mae"]
BOY_NAMES = ["Eli", "Beau", "Cal", "Jesse", "Ned", "Owen", "Reed", "Silas"]
TRAITS = ["mindful", "careful", "steady", "bold", "eager", "stubborn"]


@dataclass
class StoryParams:
    crop: str
    trouble: str
    fix: str
    hero_name: str
    hero_gender: str
    helper_type: str
    mentor_type: str
    trait: str
    delay: int = 0
    keepsake: bool = True
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
    "sunflower": [
        (
            "Why do sunflowers turn toward light?",
            "Sunflowers grow toward sunlight because light helps plants make food. Following the light helps them stay strong."
        )
    ],
    "pumpkin": [
        (
            "Why can a pumpkin bruise?",
            "A pumpkin has a hard shell, but a hard bump can still damage it. A bruise makes it look less healthy and less pretty."
        )
    ],
    "beans": [
        (
            "Why do climbing beans need support?",
            "Climbing bean plants grow long and tall, so they need poles or strings to hold them up. Without support, wind can tug them down."
        )
    ],
    "wind": [
        (
            "What can strong wind do to tall plants?",
            "Strong wind can bend or topple tall plants. That is why gardeners sometimes tie them to supports."
        )
    ],
    "water": [
        (
            "Why do plants droop when they are thirsty?",
            "Plants need water to keep their stems and leaves firm. When they get too dry, the leaves can sag and droop."
        )
    ],
    "wagon": [
        (
            "Why do people pad fragile things on a wagon?",
            "Padding helps keep a heavy or delicate thing from sliding and bumping. Less bumping means less damage."
        )
    ],
    "rope": [
        (
            "What does a rope brace do?",
            "A rope brace helps hold something steady so it does not lean or fall. It spreads the pull and keeps the thing in place."
        )
    ],
    "straw": [
        (
            "Why is straw useful for cushioning?",
            "Straw is light and springy, so it can soften bumps. That makes it useful when something needs a gentle nest."
        )
    ],
    "garden": [
        (
            "What do gardeners do at a fair?",
            "Gardeners bring flowers, fruits, or vegetables they have raised. People look at them, learn from them, and sometimes give prizes."
        )
    ],
}
KNOWLEDGE_ORDER = ["garden", "sunflower", "pumpkin", "beans", "wind", "water", "wagon", "rope", "straw"]


CURATED = [
    StoryParams(
        crop="sunflower",
        trouble="wind",
        fix="rope_brace",
        hero_name="June",
        hero_gender="girl",
        helper_type="father",
        mentor_type="grandfather",
        trait="mindful",
        delay=0,
        keepsake=True,
    ),
    StoryParams(
        crop="pumpkin",
        trouble="wobble",
        fix="straw_nest",
        hero_name="Eli",
        hero_gender="boy",
        helper_type="mother",
        mentor_type="grandmother",
        trait="eager",
        delay=0,
        keepsake=False,
    ),
    StoryParams(
        crop="beanvine",
        trouble="wind",
        fix="rope_brace",
        hero_name="Willa",
        hero_gender="girl",
        helper_type="father",
        mentor_type="grandmother",
        trait="bold",
        delay=1,
        keepsake=True,
    ),
    StoryParams(
        crop="pumpkin",
        trouble="thirst",
        fix="water_wagon",
        hero_name="Silas",
        hero_gender="boy",
        helper_type="father",
        mentor_type="grandfather",
        trait="steady",
        delay=0,
        keepsake=True,
    ),
    StoryParams(
        crop="beanvine",
        trouble="wind",
        fix="rope_brace",
        hero_name="Mae",
        hero_gender="girl",
        helper_type="mother",
        mentor_type="grandfather",
        trait="stubborn",
        delay=2,
        keepsake=False,
    ),
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    crop_cfg = f["crop_cfg"]
    trouble = f["trouble"]
    outcome = f["outcome"]
    if outcome == "steady":
        return [
            'Write a child-facing tall tale about a giant county-fair crop, using the words "cerely" and "belong-gerund," and include a flashback that helps the child act in time.',
            f"Tell a tall tale where {hero.id} remembers {hero.pronoun('possessive')} mentor's odd advice in a flashback and saves a giant {crop_cfg.label} before {trouble.label} can really hurt it.",
            f"Write a gentle exaggerated story in which a child keeps calm, uses the right farm fix, and reaches the fair with a prize-winning {crop_cfg.label}.",
        ]
    if outcome == "saved":
        return [
            'Write a child-facing tall tale about a giant county-fair crop, using the words "cerely" and "belong-gerund," and include a flashback after trouble starts.',
            f"Tell a tall tale where {trouble.label} threatens {hero.id}'s giant {crop_cfg.label}, but a remembered lesson leads to the right rescue.",
            f"Write an exaggerated fair-day story with a flashback, a practical fix, and a happy ending that proves calm thinking can save a big problem.",
        ]
    return [
        'Write a child-facing tall tale about a giant county-fair crop, using the words "cerely" and "belong-gerund," and include a flashback even though the rescue comes too late.',
        f"Tell a tall tale where {hero.id} remembers the right lesson, but {trouble.label} has already done too much damage to the giant {crop_cfg.label}.",
        f"Write a warm cautionary story in tall-tale style where a child loses the ribbon but keeps the lesson and plans to try again next year.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    mentor = f["mentor"]
    crop_cfg = f["crop_cfg"]
    trouble = f["trouble"]
    fix = f["fix"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, who raised a giant {crop_cfg.label} for the county fair. {helper.id} helped on the road, and {mentor.label_word} appeared in a flashback with useful advice."
        ),
        (
            f"What problem threatened the giant {crop_cfg.label}?",
            f"{trouble.qa_phrase.capitalize()}. That mattered because the crop was meant for the fair, so even a little damage could spoil its big day."
        ),
        (
            "What happened in the flashback?",
            f"{hero.id} remembered {mentor.label_word}'s springtime advice: 'Grow it cerely' and act when a prize starts 'belong-gerund to trouble.' The flashback calmed {hero.pronoun('object')} enough to choose a real fix instead of panicking."
        ),
    ]
    if outcome == "steady":
        qa.append(
            (
                f"How did {hero.id} save the crop before it was hurt?",
                f"{hero.id} remembered the lesson early and used {fix.label} at once. {fix.qa_text} Because the fix came before any real damage, the crop reached the fair looking proud."
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended happily at the fair, with the giant {crop_cfg.label} still looking grand. The ending proves that a calm memory at the right moment can stop trouble before it grows."
            )
        )
    elif outcome == "saved":
        qa.append(
            (
                "How did they fix the problem?",
                f"{hero.id} and {helper.id} used {fix.label}. {fix.qa_text} The trouble had already started, but the right method was strong enough to save the exhibit."
            )
        )
        qa.append(
            (
                "Why did the crop still win?",
                f"It still won because the rescue worked before the damage became too great. The story shows that acting quickly with the right tool can turn a scare into a success."
            )
        )
    else:
        qa.append(
            (
                "Why did they lose the ribbon?",
                f"They remembered the right idea, but the trouble had already gone too far. The giant {crop_cfg.label} was still impressive, yet it no longer looked neat enough to win."
            )
        )
        qa.append(
            (
                "Was the ending all sad?",
                f"No. They did not get a ribbon, but they saved seeds and kept the lesson. That leaves the story hopeful, because next year's try has already begun."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["crop_cfg"].tags) | set(f["trouble"].tags) | set(f["fix"].tags)
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
        if ent.traits:
            bits.append(f"traits={ent.traits}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v or isinstance(v, bool)}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:8} ({ent.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


def explain_rejection(crop: Crop, trouble: Trouble) -> str:
    return (
        f"(No story: {crop.label} is not the kind of fair exhibit this world treats as being at risk from "
        f"{trouble.label}. Pick a trouble that fits the crop's physical problem.)"
    )


def explain_fix(fix_id: str) -> str:
    fix = FIXES[fix_id]
    better = ", ".join(sorted(f.id for f in sensible_fixes()))
    return (
        f"(Refusing fix '{fix_id}': it scores too low on common sense "
        f"(sense={fix.sense} < {SENSE_MIN}). Try one of the practical fixes: {better}.)"
    )


ASP_RULES = r"""
hazard(C, T) :- crop(C), trouble(T), threatens(C, T).
sensible(F) :- fix(F), sense(F, S), sense_min(M), S >= M.
handles(F, T) :- covers(F, T).
valid(C, T, F) :- hazard(C, T), sensible(F), handles(F, T).

steady :- keepsake, trait(T), flashback_trait(T), delay(0).
severity(B + D) :- chosen_crop(C), base_severity(C, B), delay(D).
saved :- not steady, chosen_fix(F), power(F, P), severity(S), P >= S.

outcome(steady) :- steady.
outcome(saved) :- not steady, saved.
outcome(spoiled) :- not steady, not saved.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for crop_id, crop in CROPS.items():
        lines.append(asp.fact("crop", crop_id))
        lines.append(asp.fact("base_severity", crop_id, crop.base_severity))
        for trouble_id in sorted(crop.trouble_ids):
            lines.append(asp.fact("threatens", crop_id, trouble_id))
    for trouble_id in TROUBLES:
        lines.append(asp.fact("trouble", trouble_id))
    for fix_id, fix in FIXES.items():
        lines.append(asp.fact("fix", fix_id))
        lines.append(asp.fact("sense", fix_id, fix.sense))
        lines.append(asp.fact("power", fix_id, fix.power))
        for trouble_id in sorted(fix.covers):
            lines.append(asp.fact("covers", fix_id, trouble_id))
    for trait in sorted(FLASHBACK_TRAITS):
        lines.append(asp.fact("flashback_trait", trait))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible_fixes() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(fix for (fix,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra_lines = [
        asp.fact("chosen_crop", params.crop),
        asp.fact("chosen_fix", params.fix),
        asp.fact("delay", params.delay),
        asp.fact("trait", params.trait),
    ]
    if params.keepsake:
        extra_lines.append(asp.fact("keepsake"))
    model = asp.one_model(asp_program("\n".join(extra_lines), "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a giant fair crop, a flashback, and the right fix."
    )
    ap.add_argument("--crop", choices=sorted(CROPS))
    ap.add_argument("--trouble", choices=sorted(TROUBLES))
    ap.add_argument("--fix", choices=sorted(FIXES))
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--helper-type", choices=["mother", "father"])
    ap.add_argument("--mentor-type", choices=["grandmother", "grandfather"])
    ap.add_argument("--trait", choices=sorted(TRAITS))
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], help="how long the trouble gets a head start")
    ap.add_argument("--keepsake", choices=["yes", "no"], help="whether the hero carries the lucky button that sharpens the flashback")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible triples derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str) -> str:
    return rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.fix and FIXES[args.fix].sense < SENSE_MIN:
        raise StoryError(explain_fix(args.fix))
    if args.crop and args.trouble:
        crop = CROPS[args.crop]
        trouble = TROUBLES[args.trouble]
        if not hazard_at_risk(crop, trouble):
            raise StoryError(explain_rejection(crop, trouble))

    combos = [
        combo for combo in valid_combos()
        if (args.crop is None or combo[0] == args.crop)
        and (args.trouble is None or combo[1] == args.trouble)
        and (args.fix is None or combo[2] == args.fix)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    crop_id, trouble_id, fix_id = rng.choice(sorted(combos))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    hero_name = args.hero_name or _pick_name(rng, hero_gender)
    helper_type = args.helper_type or rng.choice(["mother", "father"])
    mentor_type = args.mentor_type or rng.choice(["grandmother", "grandfather"])
    trait = args.trait or rng.choice(TRAITS)
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    keepsake = {"yes": True, "no": False}.get(args.keepsake, rng.choice([True, False, True]))
    return StoryParams(
        crop=crop_id,
        trouble=trouble_id,
        fix=fix_id,
        hero_name=hero_name,
        hero_gender=hero_gender,
        helper_type=helper_type,
        mentor_type=mentor_type,
        trait=trait,
        delay=delay,
        keepsake=keepsake,
    )


def _require_lookup(name: str, table: dict, key: str):
    if key not in table:
        raise StoryError(f"(Invalid {name}: {key})")
    return table[key]


def generate(params: StoryParams) -> StorySample:
    crop_cfg = _require_lookup("crop", CROPS, params.crop)
    trouble = _require_lookup("trouble", TROUBLES, params.trouble)
    fix = _require_lookup("fix", FIXES, params.fix)

    if not hazard_at_risk(crop_cfg, trouble):
        raise StoryError(explain_rejection(crop_cfg, trouble))
    if fix.sense < SENSE_MIN:
        raise StoryError(explain_fix(params.fix))
    if not fix_handles(fix, trouble):
        raise StoryError(
            f"(No story: {fix.label} does not honestly solve {trouble.label}. Pick a fix that handles this trouble.)"
        )

    world = tell(
        crop_cfg=crop_cfg,
        trouble=trouble,
        fix=fix,
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        helper_type=params.helper_type,
        mentor_type=params.mentor_type,
        trait=params.trait,
        delay=params.delay,
        keepsake=params.keepsake,
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

    python_valid = set(valid_combos())
    clingo_valid = set(asp_valid_combos())
    if python_valid == clingo_valid:
        print(f"OK: gate matches valid_combos() ({len(python_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if python_valid - clingo_valid:
            print("  only in python:", sorted(python_valid - clingo_valid))
        if clingo_valid - python_valid:
            print("  only in clingo:", sorted(clingo_valid - python_valid))

    python_sensible = {fix.id for fix in sensible_fixes()}
    clingo_sensible = set(asp_sensible_fixes())
    if python_sensible == clingo_sensible:
        print(f"OK: sensible fixes match ({sorted(python_sensible)}).")
    else:
        rc = 1
        print(
            f"MISMATCH in sensible fixes: python={sorted(python_sensible)} clingo={sorted(clingo_sensible)}"
        )

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(50):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
            params.seed = seed
            cases.append(params)
        except StoryError:
            rc = 1
            print(f"Unexpected resolve failure at seed {seed}.")
            break

    mismatches = [p for p in cases if asp_outcome(p) != outcome_of(p)]
    if not mismatches:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {len(mismatches)}/{len(cases)} outcomes differ.")
        for p in mismatches[:5]:
            print(f"  {p} -> python={outcome_of(p)} clingo={asp_outcome(p)}")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("generated empty story")
        print("OK: smoke-test generation succeeded.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show sensible/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (crop, trouble, fix) triples:\n")
        for crop_id, trouble_id, fix_id in combos:
            print(f"  {crop_id:10} {trouble_id:8} {fix_id}")
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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero_name}: {p.crop} / {p.trouble} / {p.fix} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
