#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/booze_slurp_teamwork_fairy_tale.py
=============================================================

A standalone story world for a fairy-tale rescue built from the seed words
"booze" and "slurp", with **teamwork** at the center.

Premise
-------
In a little kingdom, two children must bring silver-spring water to a drooping
magic flower before sunrise. But a bridge troll sits in the way, slurping nasty
bog booze from a mug. The booze is making the troll's problem worse: hiccups,
a cough, or a hungry belly. A fairy tells the children what gentle remedy the
troll really needs, and the children must work together with a small animal
helper to make it.

Coverage rule
-------------
Not every remedy/helper pairing is reasonable. A remedy only works for the
matching ailment, and its key ingredient must be reachable by a helper with the
right skill:

* mint tea   -> hiccups     -> needs a helper who can reach high mint
* honey milk -> cough       -> needs a helper who can calm the hive
* berry broth-> hunger      -> needs a helper who can find hidden berries

The world refuses mismatched choices with a clear StoryError.

Run it
------
    python storyworlds/worlds/gpt-5.4/booze_slurp_teamwork_fairy_tale.py
    python storyworlds/worlds/gpt-5.4/booze_slurp_teamwork_fairy_tale.py --ailment hiccups --remedy mint_tea --helper sparrow
    python storyworlds/worlds/gpt-5.4/booze_slurp_teamwork_fairy_tale.py --remedy honey_milk --helper sparrow
    python storyworlds/worlds/gpt-5.4/booze_slurp_teamwork_fairy_tale.py --all
    python storyworlds/worlds/gpt-5.4/booze_slurp_teamwork_fairy_tale.py --qa --json
    python storyworlds/worlds/gpt-5.4/booze_slurp_teamwork_fairy_tale.py --verify
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

# Make the shared result containers importable when this script is run directly.
# This file lives under storyworlds/worlds/gpt-5.4/, so we add storyworlds/.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
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
        female = {"girl", "mother", "queen", "woman"}
        male = {"boy", "father", "king", "man", "troll"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mother", "father": "father"}.get(self.type, self.label or self.type)


@dataclass
class Place:
    id: str
    label: str
    path_word: str
    sky: str
    water_phrase: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Ailment:
    id: str
    label: str
    symptom_line: str
    complaint: str
    because_line: str
    need_skill: str
    severity: int
    tags: set[str] = field(default_factory=set)


@dataclass
class Remedy:
    id: str
    label: str
    phrase: str
    for_ailment: str
    ingredient: str
    gather_line: str
    brew_line: str
    cure_line: str
    power: int
    tags: set[str] = field(default_factory=set)


@dataclass
class Helper:
    id: str
    label: str
    phrase: str
    skill: str
    help_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Flower:
    id: str
    label: str
    phrase: str
    sleep_line: str
    bloom_line: str
    tags: set[str] = field(default_factory=set)


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


def _r_troll_blocks(world: World) -> list[str]:
    troll = world.get("troll")
    if troll.meters["ailment"] < THRESHOLD or troll.meters["booze"] < THRESHOLD:
        return []
    sig = ("block",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    troll.meters["blocking"] += 1
    for kid in (world.get("hero1"), world.get("hero2")):
        kid.memes["worry"] += 1
    return ["__blocked__"]


def _r_flower_sleeps(world: World) -> list[str]:
    flower = world.get("flower")
    if flower.meters["dry"] < THRESHOLD or world.get("clock").meters["delay"] < 2:
        return []
    sig = ("sleep",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    flower.meters["sleeping"] += 1
    return ["__sleep__"]


def _r_flower_blooms(world: World) -> list[str]:
    flower = world.get("flower")
    if flower.meters["watered"] < THRESHOLD or flower.meters["sleeping"] >= THRESHOLD:
        return []
    sig = ("bloom",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    flower.meters["blooming"] += 1
    flower.meters["dry"] = 0.0
    return ["__bloom__"]


CAUSAL_RULES: list[Rule] = [
    Rule(name="troll_blocks", tag="social", apply=_r_troll_blocks),
    Rule(name="flower_sleeps", tag="time", apply=_r_flower_sleeps),
    Rule(name="flower_blooms", tag="physical", apply=_r_flower_blooms),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for sent in produced:
            if sent.startswith("__"):
                continue
            world.say(sent)
    return produced


PLACES = {
    "moon_bridge": Place(
        id="moon_bridge",
        label="Moon Bridge",
        path_word="bridge",
        sky="A pale moon still shone above the reeds.",
        water_phrase="the silver spring beyond the bridge",
        tags={"bridge", "spring"},
    ),
    "fern_gate": Place(
        id="fern_gate",
        label="Fern Gate",
        path_word="gate",
        sky="Mist curled around the old stone gate.",
        water_phrase="the silver spring beyond the gate",
        tags={"gate", "spring"},
    ),
    "thorn_ford": Place(
        id="thorn_ford",
        label="Thorn Ford",
        path_word="ford",
        sky="Pink dawn waited behind the thorn bushes.",
        water_phrase="the silver spring beyond the ford",
        tags={"ford", "spring"},
    ),
}

AILMENTS = {
    "hiccups": Ailment(
        id="hiccups",
        label="hiccups",
        symptom_line="Every few breaths, the troll bounced with great booming hiccups.",
        complaint='"Hic! This bog booze was meant to warm my belly, not make it jump!"',
        because_line="The fairy whispered that bitter booze only made hiccups kick harder.",
        need_skill="reach_high",
        severity=1,
        tags={"hiccups"},
    ),
    "cough": Ailment(
        id="cough",
        label="cough",
        symptom_line="Between his slurps, the troll gave a rough, chesty cough.",
        complaint='"This smoky bog booze scratches all the way down," he grumbled.',
        because_line="The fairy whispered that harsh booze could leave a throat even sorer.",
        need_skill="calm_hive",
        severity=2,
        tags={"cough"},
    ),
    "hunger": Ailment(
        id="hunger",
        label="hungry belly",
        symptom_line="The troll's stomach rumbled so loudly that pebbles danced at his feet.",
        complaint='"Slurp, slurp... but this bog booze fills no belly at all," he sighed.',
        because_line="The fairy whispered that bog booze never made an empty stomach full.",
        need_skill="find_hidden",
        severity=2,
        tags={"hunger"},
    ),
}

REMEDIES = {
    "mint_tea": Remedy(
        id="mint_tea",
        label="mint tea",
        phrase="a steaming cup of mint tea",
        for_ailment="hiccups",
        ingredient="high mint leaves",
        gather_line="One child would hold the kettle while the other, with a helper, gathered mint from a high stone.",
        brew_line="Together they tore the cool leaves into hot spring water until the steam smelled fresh and green.",
        cure_line="The warm mint settled the bouncing hiccups one by one.",
        power=2,
        tags={"mint", "tea"},
    ),
    "honey_milk": Remedy(
        id="honey_milk",
        label="honey milk",
        phrase="a warm mug of honey milk",
        for_ailment="cough",
        ingredient="golden hive honey",
        gather_line="One child warmed the milk while the other, with a helper, waited gently by the hive for a spoon of honey.",
        brew_line="Together they stirred the honey into the milk until it shone like pale gold.",
        cure_line="The honey soothed the troll's throat, and the cough loosened at last.",
        power=3,
        tags={"honey", "milk"},
    ),
    "berry_broth": Remedy(
        id="berry_broth",
        label="berry broth",
        phrase="a little bowl of berry broth",
        for_ailment="hunger",
        ingredient="hidden red berries",
        gather_line="One child fetched the pot while the other, with a helper, found hidden berries under fern leaves.",
        brew_line="Together they mashed the berries and simmered them with water until the broth smelled sweet and brave.",
        cure_line="The berry broth gave the troll's empty belly something real at last.",
        power=2,
        tags={"berries", "broth"},
    ),
}

HELPERS = {
    "sparrow": Helper(
        id="sparrow",
        label="sparrow",
        phrase="a quick brown sparrow",
        skill="reach_high",
        help_line="The sparrow darted up to the high stone and tugged mint down in its beak.",
        tags={"bird", "mint"},
    ),
    "moonbee": Helper(
        id="moonbee",
        label="moonbee",
        phrase="a round little moonbee",
        skill="calm_hive",
        help_line="The moonbee hummed a soft hive-song until the bees turned gentle and shared a drop of honey.",
        tags={"bee", "honey"},
    ),
    "hedgehog": Helper(
        id="hedgehog",
        label="hedgehog",
        phrase="a busy hedgehog",
        skill="find_hidden",
        help_line="The hedgehog nosed under the fern roots and found a nest of hidden berries.",
        tags={"hedgehog", "berries"},
    ),
}

FLOWERS = {
    "moonflower": Flower(
        id="moonflower",
        label="moonflower",
        phrase="the village moonflower",
        sleep_line="By the time they reached the garden, the moonflower had folded its white petals for the day.",
        bloom_line="The moonflower opened all at once, wide and white, and the garden looked as if a little moon had settled there.",
        tags={"flower", "moonflower"},
    ),
    "sunbell": Flower(
        id="sunbell",
        label="sunbell",
        phrase="the golden sunbell",
        sleep_line="By the time they reached the garden, the sunbell had tucked its gold face under its own leaves.",
        bloom_line="The sunbell lifted its gold face and rang a tiny bright shimmer in the morning air.",
        tags={"flower", "sunbell"},
    ),
    "silver_lily": Flower(
        id="silver_lily",
        label="silver lily",
        phrase="the silver lily",
        sleep_line="By the time they reached the garden, the silver lily had closed like a folded lantern.",
        bloom_line="The silver lily unfolded like a silver lantern, and dew flashed on every petal.",
        tags={"flower", "lily"},
    ),
}

GIRL_NAMES = ["Lina", "Mira", "Tessa", "Nora", "Elsie", "Wren", "Clara", "Poppy"]
BOY_NAMES = ["Robin", "Milo", "Finn", "Tobin", "Jory", "Ari", "Ned", "Leo"]

TRAITS = ["kind", "brave", "careful", "quick", "steady", "hopeful"]


def remedy_matches(ailment: Ailment, remedy: Remedy) -> bool:
    return remedy.for_ailment == ailment.id


def helper_fits(remedy: Remedy, helper: Helper) -> bool:
    need = AILMENTS[remedy.for_ailment].need_skill
    return helper.skill == need


def valid_combos() -> list[tuple[str, str, str, str, str]]:
    combos: list[tuple[str, str, str, str, str]] = []
    for place_id in PLACES:
        for ailment_id, ailment in AILMENTS.items():
            for remedy_id, remedy in REMEDIES.items():
                if not remedy_matches(ailment, remedy):
                    continue
                for helper_id, helper in HELPERS.items():
                    if not helper_fits(remedy, helper):
                        continue
                    for flower_id in FLOWERS:
                        combos.append((place_id, ailment_id, remedy_id, helper_id, flower_id))
    return combos


@dataclass
class StoryParams:
    place: str
    ailment: str
    remedy: str
    helper: str
    flower: str
    hero1: str
    hero1_gender: str
    hero2: str
    hero2_gender: str
    parent: str
    trait1: str
    trait2: str
    delay: int = 0
    seed: Optional[int] = None


def outcome_of(params: StoryParams) -> str:
    ailment = AILMENTS[params.ailment]
    remedy = REMEDIES[params.remedy]
    if not remedy_matches(ailment, remedy):
        return "invalid"
    if not helper_fits(remedy, HELPERS[params.helper]):
        return "invalid"
    severity = ailment.severity + params.delay
    return "bloomed" if remedy.power >= severity else "slept"


def explain_rejection(ailment: Ailment, remedy: Remedy, helper: Helper) -> str:
    if not remedy_matches(ailment, remedy):
        return (
            f"(No story: {remedy.label} does not fit {ailment.label}. "
            f"In this world, the troll's problem needs the matching gentle remedy.)"
        )
    if not helper_fits(remedy, helper):
        need = AILMENTS[remedy.for_ailment].need_skill.replace("_", " ")
        return (
            f"(No story: {helper.label} cannot help make {remedy.label}. "
            f"That remedy needs a helper who can {need}.)"
        )
    return "(No story: this combination is not reasonable in the fairy-tale world.)"


def setup_world(
    place: Place,
    ailment: Ailment,
    remedy: Remedy,
    helper_cfg: Helper,
    flower_cfg: Flower,
    hero1_name: str,
    hero1_gender: str,
    hero2_name: str,
    hero2_gender: str,
    parent_type: str,
    trait1: str,
    trait2: str,
    delay: int,
) -> World:
    world = World()
    hero1 = world.add(Entity(id="hero1", kind="character", type=hero1_gender, label=hero1_name,
                             role="hero1", traits=[trait1]))
    hero2 = world.add(Entity(id="hero2", kind="character", type=hero2_gender, label=hero2_name,
                             role="hero2", traits=[trait2]))
    parent = world.add(Entity(id="parent", kind="character", type=parent_type, label=parent_type,
                              role="parent"))
    troll = world.add(Entity(id="troll", kind="character", type="troll", label="bridge troll",
                             role="troll"))
    helper = world.add(Entity(id="helper", type="animal", label=helper_cfg.label, phrase=helper_cfg.phrase))
    flower = world.add(Entity(id="flower", type="flower", label=flower_cfg.label, phrase=flower_cfg.phrase))
    world.add(Entity(id="clock", type="time", label="dawn"))
    world.add(Entity(id="path", type="path", label=place.path_word))
    hero1.memes["hope"] += 1
    hero2.memes["hope"] += 1
    flower.meters["dry"] += 1
    troll.meters["ailment"] += 1
    troll.meters["booze"] += 1
    world.get("clock").meters["delay"] = float(delay)
    world.facts.update(
        place=place,
        ailment=ailment,
        remedy=remedy,
        helper_cfg=helper_cfg,
        flower_cfg=flower_cfg,
        hero1=hero1,
        hero2=hero2,
        parent=parent,
        troll=troll,
        helper=helper,
        flower=flower,
        delay=delay,
    )
    propagate(world, narrate=False)
    return world


def introduce(world: World) -> None:
    place = world.facts["place"]
    flower_cfg = world.facts["flower_cfg"]
    h1 = world.get("hero1")
    h2 = world.get("hero2")
    parent = world.get("parent")
    world.say(
        f"In a little kingdom where wells wore silver rims and dawn moved softly through the reeds, "
        f"{h1.label} and {h2.label} lived in a cottage beside the royal garden."
    )
    world.say(
        f"Before the sun was up, {parent.label_word} sent them on a gentle hurry: "
        f"they must fetch water from {place.water_phrase} for {flower_cfg.phrase}, which had begun to droop in the night."
    )
    world.say(place.sky)


def show_problem(world: World) -> None:
    ailment = world.facts["ailment"]
    place = world.facts["place"]
    troll = world.get("troll")
    h1 = world.get("hero1")
    h2 = world.get("hero2")
    world.say(
        f"But on the {place.path_word} sat a troll with moss on his boots and a mug in his hand."
    )
    if ailment.id == "hiccups":
        world.say(
            'He tipped the mug back and went "slurp, slurp," and then "HIC!" so loudly that the railings shook.'
        )
    elif ailment.id == "cough":
        world.say(
            'He took a long "slurp" from the mug, then coughed into his elbow until the mist jumped.'
        )
    else:
        world.say(
            'He hunched over the mug and muttered, "slurp, slurp," as if the bitter drink could fill a growling stomach.'
        )
    world.say(
        f"The mug smelled of bog booze, sour and sharp, and the troll did not move aside."
    )
    world.say(ailment.symptom_line)
    world.say(ailment.complaint)
    if troll.meters["blocking"] >= THRESHOLD:
        world.say(
            f"With the troll planted there, neither child could reach the spring by the straight path."
        )


def fairy_warning(world: World) -> None:
    ailment = world.facts["ailment"]
    remedy = world.facts["remedy"]
    h1 = world.get("hero1")
    h2 = world.get("hero2")
    for kid in (h1, h2):
        kid.memes["worry"] += 1
    world.say(
        f"A reed-fairy rose from the ditch, no taller than a spoon, and whispered to {h1.label} and {h2.label}, "
        f'"Do not fear the bog booze. Fear what it is not fixing."'
    )
    world.say(ailment.because_line)
    world.say(
        f'"What he needs is {remedy.phrase}," said the fairy. "And you will make it only if you work together."'
    )


def teamwork_gather(world: World) -> None:
    remedy = world.facts["remedy"]
    helper_cfg = world.facts["helper_cfg"]
    h1 = world.get("hero1")
    h2 = world.get("hero2")
    helper = world.get("helper")
    for kid in (h1, h2):
        kid.memes["teamwork"] += 1
    world.say(
        f"{h1.label} and {h2.label} nodded at once. {remedy.gather_line}"
    )
    world.say(helper_cfg.help_line)
    world.say(
        f"{h1.label} did not wait for {h2.label}, and {h2.label} did not leave {h1.label} to do everything alone. "
        f"Each child took one part of the work, and the work began to feel possible."
    )


def brew_remedy(world: World) -> None:
    remedy = world.facts["remedy"]
    h1 = world.get("hero1")
    h2 = world.get("hero2")
    world.say(remedy.brew_line)
    if world.facts["delay"] > 0:
        world.say(
            f"But the morning kept creeping forward while they worked, and each careful minute felt precious."
        )
    world.say(
        f"When the cup was ready, {h1.label} carried it with both hands, and {h2.label} shielded the steam from the wind."
    )


def soothe_troll(world: World, success: bool) -> None:
    troll = world.get("troll")
    remedy = world.facts["remedy"]
    h1 = world.get("hero1")
    h2 = world.get("hero2")
    troll.meters["booze"] = 0.0
    troll.meters["remedy"] += 1
    troll.meters["ailment"] = max(0.0, troll.meters["ailment"] - 1.0)
    if success:
        troll.meters["blocking"] = 0.0
        troll.memes["gratitude"] += 1
        h1.memes["relief"] += 1
        h2.memes["relief"] += 1
        world.say(
            f'The troll blinked at the children. "For me?" he asked, and his voice had gone small.'
        )
        world.say(
            f'He took the cup instead of the booze mug, sipped once, and then once again, slower this time.'
        )
        world.say(remedy.cure_line)
        world.say(
            f'The troll set the ugly booze aside, rubbed his eyes, and said, "I was sitting in the way when I should have been asking for help."'
        )
        world.say(
            f"He stood up, bowed as well as a troll could bow, and cleared the {world.facts['place'].path_word}."
        )
    else:
        troll.meters["blocking"] = 0.0
        troll.memes["gratitude"] += 1
        world.say(
            f'The troll took the cup in both hands and drank it gratefully, leaving the booze mug untouched on the stones.'
        )
        world.say(
            f'The remedy helped him, but slowly, and the sky had already grown brighter at the edge.'
        )
        world.say(
            f'"You have been kind to me," the troll said, moving aside at last, "but dawn did not wait for any of us."'
        )


def fetch_water_and_end(world: World, success: bool) -> None:
    flower = world.get("flower")
    flower_cfg = world.facts["flower_cfg"]
    h1 = world.get("hero1")
    h2 = world.get("hero2")
    world.say(
        f"Together the children hurried to the spring. One held the silver pail steady while the other filled it, "
        f"and together they carried the shining water back without spilling a drop."
    )
    if success:
        flower.meters["watered"] += 1
        propagate(world, narrate=False)
        h1.memes["joy"] += 1
        h2.memes["joy"] += 1
        world.say(
            f"They poured the water around the roots of {flower_cfg.phrase}."
        )
        world.say(flower_cfg.bloom_line)
        world.say(
            f"The troll came after them carrying the clean pail, and from that morning on he offered thirsty travelers spring water instead of booze."
        )
        world.say(
            f"As for {h1.label} and {h2.label}, they always remembered that two small pairs of hands can do what one pair alone cannot."
        )
    else:
        world.get("clock").meters["delay"] += 1
        propagate(world, narrate=False)
        h1.memes["sadness"] += 1
        h2.memes["sadness"] += 1
        world.say(
            f"They poured the water carefully around the roots of {flower_cfg.phrase}, but they were a breath too late."
        )
        world.say(flower_cfg.sleep_line)
        world.say(
            f"Still, the water sank into the earth, and the fairy promised the flower would wake stronger the next night because kindness had reached its roots."
        )
        world.say(
            f"The children did not quarrel or blame each other. They set the empty pail between them and walked home side by side, already planning to start earlier tomorrow."
        )


def tell(
    place: Place,
    ailment: Ailment,
    remedy: Remedy,
    helper_cfg: Helper,
    flower_cfg: Flower,
    hero1_name: str,
    hero1_gender: str,
    hero2_name: str,
    hero2_gender: str,
    parent_type: str,
    trait1: str,
    trait2: str,
    delay: int,
) -> World:
    world = setup_world(
        place=place,
        ailment=ailment,
        remedy=remedy,
        helper_cfg=helper_cfg,
        flower_cfg=flower_cfg,
        hero1_name=hero1_name,
        hero1_gender=hero1_gender,
        hero2_name=hero2_name,
        hero2_gender=hero2_gender,
        parent_type=parent_type,
        trait1=trait1,
        trait2=trait2,
        delay=delay,
    )
    introduce(world)
    world.para()
    show_problem(world)
    fairy_warning(world)
    world.para()
    teamwork_gather(world)
    brew_remedy(world)
    success = outcome_of(
        StoryParams(
            place=place.id,
            ailment=ailment.id,
            remedy=remedy.id,
            helper=helper_cfg.id,
            flower=flower_cfg.id,
            hero1=hero1_name,
            hero1_gender=hero1_gender,
            hero2=hero2_name,
            hero2_gender=hero2_gender,
            parent=parent_type,
            trait1=trait1,
            trait2=trait2,
            delay=delay,
        )
    ) == "bloomed"
    world.para()
    soothe_troll(world, success=success)
    world.para()
    fetch_water_and_end(world, success=success)
    world.facts.update(
        success=success,
        outcome="bloomed" if success else "slept",
        teamwork=True,
        blocked=True,
        story_helper=world.get("helper"),
    )
    return world


KNOWLEDGE = {
    "booze": [
        (
            "What is booze?",
            "Booze is a grown-up word for drinks with alcohol in them. They can taste bitter and are not for children."
        )
    ],
    "slurp": [
        (
            "What does slurp mean?",
            "To slurp means to drink or eat noisily, making a sucking sound. People often slurp soup or a drink when it is hot."
        )
    ],
    "mint": [
        (
            "What is mint?",
            "Mint is a green plant with a cool, fresh smell. People sometimes put mint in tea."
        )
    ],
    "honey": [
        (
            "What is honey?",
            "Honey is a sweet golden food made by bees from flower nectar. It tastes sweet and smooth."
        )
    ],
    "berries": [
        (
            "What are berries?",
            "Berries are small juicy fruits that grow on bushes or low plants. Many berries are sweet, but some should only be eaten when a grown-up says they are safe."
        )
    ],
    "teamwork": [
        (
            "What is teamwork?",
            "Teamwork means people help each other do one job together. Often each person does one part, and together they can do more than either could alone."
        )
    ],
    "flower": [
        (
            "Why do flowers need water?",
            "Flowers need water to stay fresh and open. Without enough water, their stems and petals can droop."
        )
    ],
}

KNOWLEDGE_ORDER = ["booze", "slurp", "mint", "honey", "berries", "teamwork", "flower"]


def pair_noun(h1: Entity, h2: Entity) -> str:
    if h1.type == "boy" and h2.type == "boy":
        return "two children"
    if h1.type == "girl" and h2.type == "girl":
        return "two children"
    return "two children"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    h1 = f["hero1"]
    h2 = f["hero2"]
    ailment = f["ailment"]
    remedy = f["remedy"]
    flower = f["flower_cfg"]
    outcome = f["outcome"]
    if outcome == "bloomed":
        return [
            'Write a fairy tale for a 3-to-5-year-old that includes the words "booze" and "slurp" and centers on teamwork.',
            f"Tell a gentle fairy tale where {h1.label} and {h2.label} meet a troll whose {ailment.label} is made worse by bog booze, and they work together to make {remedy.label}.",
            f"Write a magical story where two children save {flower.phrase} before dawn by helping an obstacle instead of fighting it.",
        ]
    return [
        'Write a fairy tale for a 3-to-5-year-old that includes the words "booze" and "slurp" and centers on teamwork.',
        f"Tell a bittersweet fairy tale where {h1.label} and {h2.label} kindly help a troll with {ailment.label}, but dawn reaches the flower first.",
        f"Write a story where teamwork still matters even though the children arrive a little too late to save {flower.phrase} that morning.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    h1 = f["hero1"]
    h2 = f["hero2"]
    troll = f["troll"]
    ailment = f["ailment"]
    remedy = f["remedy"]
    helper_cfg = f["helper_cfg"]
    flower_cfg = f["flower_cfg"]
    place = f["place"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair_noun(h1, h2)}, {h1.label} and {h2.label}, and a troll on the {place.path_word}. It is also about the drooping magic flower they were trying to help."
        ),
        (
            f"Why were {h1.label} and {h2.label} hurrying out so early?",
            f"They needed to fetch water from the silver spring for {flower_cfg.phrase} before sunrise. The flower was already drooping, so waiting longer would make the task harder."
        ),
        (
            "What was the troll doing with the booze?",
            f"The troll was drinking bog booze and making loud slurp sounds from his mug. The bitter drink was not solving his problem, and it helped keep him grumpy and in the way."
        ),
        (
            f"What problem did the troll really have?",
            f"He had {ailment.label}. The fairy explained that the booze was making that trouble worse instead of helping it."
        ),
        (
            f"How did teamwork help {h1.label} and {h2.label}?",
            f"They split the job instead of trying to do everything one at a time. One child handled one part while the other child handled another, and their helper made the key ingredient possible."
        ),
        (
            f"What did the helper do?",
            f"The {helper_cfg.label} helped them get {remedy.ingredient}. That mattered because they could not make {remedy.label} without that ingredient."
        ),
    ]
    if f["outcome"] == "bloomed":
        qa.extend([
            (
                f"How did the children help the troll move from the {place.path_word}?",
                f"They gave him {remedy.phrase} instead of more booze. The gentle remedy soothed his real problem, so he set the booze aside and chose to move."
            ),
            (
                f"What happened to {flower_cfg.phrase} at the end?",
                f"The children reached it in time with spring water, and it bloomed. The ending shows that their teamwork changed the whole morning for the better."
            ),
        ])
    else:
        qa.extend([
            (
                "Did the children fail completely?",
                f"No. They still helped the troll kindly and brought water to the roots of {flower_cfg.phrase}. They were simply too late to see it open that morning."
            ),
            (
                f"What happened to {flower_cfg.phrase} at the end?",
                f"It had already closed for the day by the time they arrived. Even so, the water and the children's kindness still helped it for the next night."
            ),
        ])
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"booze", "slurp", "teamwork", "flower"}
    remedy = f["remedy"]
    if remedy.id == "mint_tea":
        tags.add("mint")
    elif remedy.id == "honey_milk":
        tags.add("honey")
    elif remedy.id == "berry_broth":
        tags.add("berries")
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
        if ent.label and ent.label != ent.id:
            bits.append(f"label={ent.label!r}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.traits:
            bits.append(f"traits={ent.traits}")
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="moon_bridge",
        ailment="hiccups",
        remedy="mint_tea",
        helper="sparrow",
        flower="moonflower",
        hero1="Lina",
        hero1_gender="girl",
        hero2="Robin",
        hero2_gender="boy",
        parent="mother",
        trait1="brave",
        trait2="careful",
        delay=0,
    ),
    StoryParams(
        place="fern_gate",
        ailment="cough",
        remedy="honey_milk",
        helper="moonbee",
        flower="sunbell",
        hero1="Mira",
        hero1_gender="girl",
        hero2="Finn",
        hero2_gender="boy",
        parent="father",
        trait1="steady",
        trait2="kind",
        delay=1,
    ),
    StoryParams(
        place="thorn_ford",
        ailment="hunger",
        remedy="berry_broth",
        helper="hedgehog",
        flower="silver_lily",
        hero1="Nora",
        hero1_gender="girl",
        hero2="Milo",
        hero2_gender="boy",
        parent="mother",
        trait1="quick",
        trait2="hopeful",
        delay=2,
    ),
]


ASP_RULES = r"""
% --- reasonableness gate ---------------------------------------------------
valid(Place, Ail, Rem, Help, Fl) :-
    place(Place), ailment(Ail), remedy(Rem), helper(Help), flower(Fl),
    remedy_for(Rem, Ail), need_skill(Ail, Skill), helper_skill(Help, Skill).

% --- outcome model ---------------------------------------------------------
severity(V) :- chosen_ailment(A), base_severity(A, B), delay(D), V = B + D.
success :- chosen_remedy(R), chosen_ailment(A), remedy_for(R, A),
           remedy_power(R, P), severity(V), P >= V.
outcome(bloomed) :- success.
outcome(slept) :- not success.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for aid, ail in AILMENTS.items():
        lines.append(asp.fact("ailment", aid))
        lines.append(asp.fact("need_skill", aid, ail.need_skill))
        lines.append(asp.fact("base_severity", aid, ail.severity))
    for rid, rem in REMEDIES.items():
        lines.append(asp.fact("remedy", rid))
        lines.append(asp.fact("remedy_for", rid, rem.for_ailment))
        lines.append(asp.fact("remedy_power", rid, rem.power))
    for hid, helper in HELPERS.items():
        lines.append(asp.fact("helper", hid))
        lines.append(asp.fact("helper_skill", hid, helper.skill))
    for fid in FLOWERS:
        lines.append(asp.fact("flower", fid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/5."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join([
        asp.fact("chosen_ailment", params.ailment),
        asp.fact("chosen_remedy", params.remedy),
        asp.fact("delay", params.delay),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def _random_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Fairy-tale story world: two children use teamwork to help a troll and save a flower."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--ailment", choices=AILMENTS)
    ap.add_argument("--remedy", choices=REMEDIES)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--flower", choices=FLOWERS)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], help="how far dawn has already crept forward")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible scenarios from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.ailment and args.remedy and args.helper:
        ail = AILMENTS[args.ailment]
        rem = REMEDIES[args.remedy]
        helper = HELPERS[args.helper]
        if not (remedy_matches(ail, rem) and helper_fits(rem, helper)):
            raise StoryError(explain_rejection(ail, rem, helper))
    elif args.ailment and args.remedy:
        ail = AILMENTS[args.ailment]
        rem = REMEDIES[args.remedy]
        if not remedy_matches(ail, rem):
            helper = HELPERS[args.helper] if args.helper else next(iter(HELPERS.values()))
            raise StoryError(explain_rejection(ail, rem, helper))
    elif args.remedy and args.helper:
        rem = REMEDIES[args.remedy]
        helper = HELPERS[args.helper]
        ail = AILMENTS[rem.for_ailment]
        if not helper_fits(rem, helper):
            raise StoryError(explain_rejection(ail, rem, helper))

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.ailment is None or combo[1] == args.ailment)
        and (args.remedy is None or combo[2] == args.remedy)
        and (args.helper is None or combo[3] == args.helper)
        and (args.flower is None or combo[4] == args.flower)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, ailment_id, remedy_id, helper_id, flower_id = rng.choice(sorted(combos))
    hero1_gender = rng.choice(["girl", "boy"])
    hero2_gender = rng.choice(["girl", "boy"])
    hero1 = _random_name(rng, hero1_gender)
    hero2 = _random_name(rng, hero2_gender, avoid=hero1)
    parent = args.parent or rng.choice(["mother", "father"])
    trait1 = rng.choice(TRAITS)
    trait2 = rng.choice(TRAITS)
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    return StoryParams(
        place=place_id,
        ailment=ailment_id,
        remedy=remedy_id,
        helper=helper_id,
        flower=flower_id,
        hero1=hero1,
        hero1_gender=hero1_gender,
        hero2=hero2,
        hero2_gender=hero2_gender,
        parent=parent,
        trait1=trait1,
        trait2=trait2,
        delay=delay,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        place = PLACES[params.place]
        ailment = AILMENTS[params.ailment]
        remedy = REMEDIES[params.remedy]
        helper = HELPERS[params.helper]
        flower = FLOWERS[params.flower]
    except KeyError as exc:
        raise StoryError(f"(Invalid parameter key: {exc.args[0]!r})") from None

    if not remedy_matches(ailment, remedy) or not helper_fits(remedy, helper):
        raise StoryError(explain_rejection(ailment, remedy, helper))

    world = tell(
        place=place,
        ailment=ailment,
        remedy=remedy,
        helper_cfg=helper,
        flower_cfg=flower,
        hero1_name=params.hero1,
        hero1_gender=params.hero1_gender,
        hero2_name=params.hero2,
        hero2_gender=params.hero2_gender,
        parent_type=params.parent,
        trait1=params.trait1,
        trait2=params.trait2,
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

    cases: list[StoryParams] = list(CURATED)
    for seed in range(50):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
            params.seed = seed
            cases.append(params)
        except StoryError:
            continue
    mismatches = [p for p in cases if asp_outcome(p) != outcome_of(p)]
    if not mismatches:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH in outcome model on {len(mismatches)} scenarios.")
        for p in mismatches[:5]:
            print(" ", p, asp_outcome(p), outcome_of(p))

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("smoke test generated an empty story")
        print("OK: smoke test generation succeeded.")
    except Exception as exc:  # pragma: no cover - verify path
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/5.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, ailment, remedy, helper, flower) combos:\n")
        for place, ailment, remedy, helper, flower in combos:
            print(f"  {place:12} {ailment:8} {remedy:11} {helper:9} {flower}")
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
                f"### {p.hero1} & {p.hero2}: {p.ailment} / {p.remedy} / "
                f"{p.helper} at {p.place} ({outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
