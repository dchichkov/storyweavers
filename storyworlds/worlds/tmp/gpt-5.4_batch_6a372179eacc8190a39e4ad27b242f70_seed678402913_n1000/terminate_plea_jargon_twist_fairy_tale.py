#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/terminate_plea_jargon_twist_fairy_tale.py
====================================================================

A standalone storyworld for a small fairy-tale domain built from the seed words
"terminate", "plea", and "jargon", with a required twist.

Premise
-------
A child in a little kingdom loves one magical village wonder. A royal official
arrives with a termination order and explains it in stuffy jargon. The child
makes a plea, but the official does not listen. So the child goes to the one
feared creature nearby -- and the twist is that the "monster" is really the old
keeper who understands the ancient wording and can reveal what the order truly
meant. The kingdom saves the wonder, repairs the real problem, and the ending
image proves the change.

Run it
------
    python storyworlds/worlds/gpt-5.4/terminate_plea_jargon_twist_fairy_tale.py
    python storyworlds/worlds/gpt-5.4/terminate_plea_jargon_twist_fairy_tale.py --problem moonwell
    python storyworlds/worlds/gpt-5.4/terminate_plea_jargon_twist_fairy_tale.py --helper hill_ogre
    python storyworlds/worlds/gpt-5.4/terminate_plea_jargon_twist_fairy_tale.py --all
    python storyworlds/worlds/gpt-5.4/terminate_plea_jargon_twist_fairy_tale.py --verify
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
        female = {"girl", "woman", "queen", "fairy", "witch"}
        male = {"boy", "man", "king", "ogre", "dragon", "steward", "bailiff", "chamberlain"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Setting:
    id: str
    place: str
    crown_place: str
    path_text: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Problem:
    id: str
    label: str
    phrase: str
    domain: str
    setting_ids: set[str]
    joy_text: str
    order_text: str
    jargon_text: str
    real_fault: str
    repair_text: str
    ending_image: str
    helper_request: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Official:
    id: str
    type: str
    label: str
    entrance: str
    manner: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Helper:
    id: str
    type: str
    label: str
    epithet: str
    home: str
    skill: str
    fear_text: str
    reveal_text: str
    proof_text: str
    kind_act: str
    tags: set[str] = field(default_factory=set)


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


def _r_order_risk(world: World) -> list[str]:
    site = world.entities.get("site")
    hero = world.entities.get("hero")
    if site is None or hero is None:
        return []
    if site.meters["ordered_closed"] < THRESHOLD:
        return []
    sig = ("order_risk", site.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    site.meters["risk"] += 1
    hero.memes["worry"] += 1
    return []


def _r_jargon_confusion(world: World) -> list[str]:
    hero = world.entities.get("hero")
    official = world.entities.get("official")
    if hero is None or official is None:
        return []
    if official.memes["spoke_jargon"] < THRESHOLD:
        return []
    sig = ("jargon_confusion", hero.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["confusion"] += 1
    return []


def _r_plea_courage(world: World) -> list[str]:
    hero = world.entities.get("hero")
    if hero is None:
        return []
    if hero.memes["pleaded"] < THRESHOLD:
        return []
    sig = ("plea_courage", hero.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["courage"] += 1
    return []


def _r_truth_relief(world: World) -> list[str]:
    site = world.entities.get("site")
    hero = world.entities.get("hero")
    helper = world.entities.get("helper")
    if site is None or hero is None or helper is None:
        return []
    if helper.memes["understood_charter"] < THRESHOLD:
        return []
    sig = ("truth_relief", site.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    site.meters["risk"] = 0.0
    site.meters["safe"] += 1
    hero.memes["relief"] += 1
    helper.memes["trust"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="order_risk", tag="physical", apply=_r_order_risk),
    Rule(name="jargon_confusion", tag="social", apply=_r_jargon_confusion),
    Rule(name="plea_courage", tag="emotional", apply=_r_plea_courage),
    Rule(name="truth_relief", tag="social", apply=_r_truth_relief),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            out = rule.apply(world)
            if out:
                changed = True
                produced.extend(out)
    if narrate:
        for line in produced:
            world.say(line)
    return produced


def helper_fits(problem: Problem, helper: Helper) -> bool:
    return problem.domain == helper.skill


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for setting_id, setting in SETTINGS.items():
        for problem_id, problem in PROBLEMS.items():
            if setting_id not in problem.setting_ids:
                continue
            for helper_id, helper in HELPERS.items():
                if helper_fits(problem, helper):
                    combos.append((setting_id, problem_id, helper_id))
    return combos


def explain_rejection(setting: Optional[Setting], problem: Optional[Problem], helper: Optional[Helper]) -> str:
    if setting and problem and setting.id not in problem.setting_ids:
        return (
            f"(No story: {problem.label} does not belong in {setting.place}. "
            f"Pick a setting that suits that village wonder.)"
        )
    if problem and helper and not helper_fits(problem, helper):
        return (
            f"(No story: {helper.label} does not know the old {problem.domain} craft "
            f"needed to save {problem.label}. Pick a helper whose skill matches the problem.)"
        )
    return "(No valid combination matches the given options.)"


def predict_resolution(problem: Problem, helper: Helper) -> dict:
    return {
        "can_decode": helper_fits(problem, helper),
        "repair": problem.repair_text if helper_fits(problem, helper) else "",
    }


def once_upon(world: World, hero: Entity, problem: Problem) -> None:
    site = world.get("site")
    hero.memes["love"] += 1
    world.say(
        f"Once upon a time, in {world.setting.place}, there lived a child named {hero.id}. "
        f"{hero.id} loved {site.phrase}, for {problem.joy_text}."
    )


def official_arrives(world: World, official: Entity, problem: Problem) -> None:
    site = world.get("site")
    site.meters["ordered_closed"] += 1
    official.memes["duty"] += 1
    propagate(world, narrate=False)
    world.say(
        f"One morning, {official.phrase} came {OFFICIALS[official.attrs['official_id']].entrance} "
        f"and nailed a paper to a post beside {site.label}. "
        f'"By order of the crown, we must terminate {problem.order_text}," {official.pronoun()} announced.'
    )


def official_jargon(world: World, official: Entity, hero: Entity, problem: Problem) -> None:
    official.memes["spoke_jargon"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{hero.id} stared at the curled letters. "
        f'"Please do not use so much jargon," {hero.pronoun()} said, but '
        f"{official.pronoun()} only cleared {official.pronoun('possessive')} throat and replied, "
        f'"{problem.jargon_text}"'
    )


def child_plea(world: World, hero: Entity, official: Entity, problem: Problem) -> None:
    hero.memes["pleaded"] += 1
    propagate(world, narrate=False)
    world.say(
        f'Then {hero.id} made a plea. "{problem.helper_request}," {hero.pronoun()} begged. '
        f'But {official.label_word} shook {official.pronoun("possessive")} head and said the order must stand until someone proved the old words meant something else.'
    )


def seek_helper(world: World, hero: Entity, helper: Entity, problem: Problem) -> None:
    hero.memes["fear"] += 1
    world.say(
        f"So {hero.id} followed {world.setting.path_text} to {helper.attrs['home']}, "
        f"where everyone said {helper.label} lived. {HELPERS[helper.attrs['helper_id']].fear_text}"
    )
    world.say(
        f'At the doorway, {hero.id} swallowed hard and called, "{helper.label}, please listen to my plea. '
        f'They want to terminate {problem.order_text}, and I do not understand the jargon at all."'
    )


def helper_kindness(world: World, helper: Entity, hero: Entity) -> None:
    helper.memes["kindness"] += 1
    hero.memes["trust"] += 1
    world.say(
        f"{helper.label} did not roar or stomp. Instead, {helper.pronoun()} {helper.attrs['kind_act']}, "
        f"and the sound was gentler than rain on a roof."
    )


def helper_reveal(world: World, helper: Entity, problem: Problem) -> None:
    helper.memes["understood_charter"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{helper.pronoun().capitalize()} read the order once, then twice, and smiled a secret smile. "
        f'"Here is the twist," {helper.pronoun()} said. "{helper.attrs["reveal_text"]} '
        f'This order does not command them to end {problem.label}. It says to terminate {problem.real_fault}."'
    )


def return_to_court(world: World, hero: Entity, official: Entity, helper: Entity, problem: Problem) -> None:
    site = world.get("site")
    site.meters["repaired"] += 1
    official.memes["surprise"] += 1
    official.memes["shame"] += 1
    world.say(
        f"Back in {world.setting.crown_place}, {helper.label} laid an old seal beside the paper and showed the hidden line. "
        f"{helper.attrs['proof_text']} Even {official.label_word} could not deny it."
    )
    world.say(
        f'"Then let us mend what is truly wrong," {official.pronoun()} said at last. '
        f"Soon the townsfolk {problem.repair_text}, and no one spoke of closing {site.label} again."
    )


def ending(world: World, hero: Entity, helper: Entity, official: Entity, problem: Problem) -> None:
    hero.memes["joy"] += 1
    official.memes["wisdom"] += 1
    helper.memes["belonging"] += 1
    world.say(
        f"That evening, {official.label_word} thanked {hero.id} for the brave plea and thanked {helper.label} for the truth behind the twist."
    )
    world.say(problem.ending_image)


def tell(
    setting: Setting,
    problem: Problem,
    official_cfg: Official,
    helper_cfg: Helper,
    hero_name: str = "Mira",
    hero_gender: str = "girl",
) -> World:
    world = World(setting)
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_gender,
        label=hero_name,
        phrase=hero_name,
        role="hero",
        traits=["kind", "brave"],
    ))
    official = world.add(Entity(
        id="Official",
        kind="character",
        type=official_cfg.type,
        label=official_cfg.label,
        phrase=f"the {official_cfg.label}",
        role="official",
        attrs={"official_id": official_cfg.id},
        tags=set(official_cfg.tags),
    ))
    helper = world.add(Entity(
        id="Helper",
        kind="character",
        type=helper_cfg.type,
        label=helper_cfg.label,
        phrase=helper_cfg.epithet,
        role="helper",
        attrs={
            "helper_id": helper_cfg.id,
            "home": helper_cfg.home,
            "reveal_text": helper_cfg.reveal_text,
            "proof_text": helper_cfg.proof_text,
            "kind_act": helper_cfg.kind_act,
        },
        tags=set(helper_cfg.tags),
    ))
    site = world.add(Entity(
        id="site",
        kind="thing",
        type="wonder",
        label=problem.label,
        phrase=problem.phrase,
        role="site",
        tags=set(problem.tags),
    ))

    once_upon(world, hero, problem)

    world.para()
    official_arrives(world, official, problem)
    official_jargon(world, official, hero, problem)
    child_plea(world, hero, official, problem)

    world.para()
    seek_helper(world, hero, helper, problem)
    helper_kindness(world, helper, hero)
    helper_reveal(world, helper, problem)

    world.para()
    return_to_court(world, hero, official, helper, problem)
    ending(world, hero, helper, official, problem)

    world.facts.update(
        hero=hero,
        official=official,
        helper=helper,
        site=site,
        setting=setting,
        problem=problem,
        official_cfg=official_cfg,
        helper_cfg=helper_cfg,
        twist_revealed=helper.memes["understood_charter"] >= THRESHOLD,
        saved=site.meters["safe"] >= THRESHOLD,
        repaired=site.meters["repaired"] >= THRESHOLD,
        jargon_confused=hero.memes["confusion"] >= THRESHOLD,
        plea_made=hero.memes["pleaded"] >= THRESHOLD,
    )
    return world


KNOWLEDGE = {
    "jargon": [
        (
            "What is jargon?",
            "Jargon means special words that only some people know well. If someone uses too much jargon, it can make a simple idea hard to understand.",
        )
    ],
    "plea": [
        (
            "What is a plea?",
            "A plea is a very earnest request for help or kindness. It is stronger than a casual question because the speaker cares a great deal.",
        )
    ],
    "terminate": [
        (
            "What does terminate mean?",
            "Terminate means to end something. In a story, it can sound cold or official, which is why a child might find the word scary.",
        )
    ],
    "charter": [
        (
            "What is a charter in a fairy tale kingdom?",
            "A charter is an old written rule or promise. Kings and queens may keep charters to say what should be protected or repaired.",
        )
    ],
    "twist": [
        (
            "What is a twist in a story?",
            "A twist is a surprise that changes how you understand what was happening before. A good twist still fits the story and makes the ending feel earned.",
        )
    ],
    "water": [
        (
            "Why is a well important in a village?",
            "A well gives people water to drink and carry home. In fairy tales, a well can also feel magical because everyone gathers there.",
        )
    ],
    "sound": [
        (
            "Why do bells matter in a village?",
            "Bells call people together and mark happy times. Their sound can make a whole place feel lively and safe.",
        )
    ],
    "light": [
        (
            "Why do lanterns matter at night?",
            "Lanterns help people see in the dark. They also make a place feel warm and welcoming.",
        )
    ],
}

KNOWLEDGE_ORDER = ["terminate", "plea", "jargon", "twist", "charter", "water", "sound", "light"]


SETTINGS = {
    "green_hollow": Setting(
        id="green_hollow",
        place="Green Hollow",
        crown_place="the little court of Green Hollow",
        path_text="the fern path under willow leaves",
        affords={"moonwell", "lantern_garden"},
    ),
    "hill_market": Setting(
        id="hill_market",
        place="Hill Market",
        crown_place="the stone square of Hill Market",
        path_text="the steep lane between old bell towers",
        affords={"bell_tree", "lantern_garden"},
    ),
    "misty_ford": Setting(
        id="misty_ford",
        place="Misty Ford",
        crown_place="the bridge court by the ford",
        path_text="the reed road beside the silver water",
        affords={"moonwell", "bell_tree"},
    ),
}

PROBLEMS = {
    "moonwell": Problem(
        id="moonwell",
        label="the moonwell",
        phrase="the moonwell in the middle of the village",
        domain="water",
        setting_ids={"green_hollow", "misty_ford"},
        joy_text="its water shone like a coin of moonlight, and children loved to see stars tremble in its round face",
        order_text="the moonwell",
        jargon_text="Per the hereditary cistern codicil, immediate termination of the moonwell asset is procedurally indicated.",
        real_fault="the frayed bucket rope above the well",
        repair_text="braided a new silver rope and hung a smooth bucket on it",
        ending_image="So the moonwell stayed open, bright as a little moon, and the first bucket that rose that night carried stars in its water.",
        helper_request="Please do not take away our moonwell",
        tags={"water", "charter"},
    ),
    "bell_tree": Problem(
        id="bell_tree",
        label="the bell tree",
        phrase="the bell tree by the gate",
        domain="sound",
        setting_ids={"hill_market", "misty_ford"},
        joy_text="every breeze rang its tiny bells, and the town could hear laughter in the music",
        order_text="the bell tree",
        jargon_text="Per the resonant arbor appendix, termination of the bell tree structure is hereby initiated for acoustic compliance.",
        real_fault="the worm-eaten beam that held one heavy branch",
        repair_text="set a strong new beam under the branch and tied fresh silver ribbons among the bells",
        ending_image="When the wind came back, the bell tree sang so sweetly that even the pigeons puffed up their chests to listen.",
        helper_request="Please do not cut down our bell tree",
        tags={"sound", "charter"},
    ),
    "lantern_garden": Problem(
        id="lantern_garden",
        label="the lantern garden",
        phrase="the lantern garden behind the square",
        domain="light",
        setting_ids={"green_hollow", "hill_market"},
        joy_text="its glass flowers held warm little lights, and the paths glowed like a necklace dropped by dawn",
        order_text="the lantern garden",
        jargon_text="Under the noctilucent horticultural memorandum, termination of the lantern garden installation is recommended pending smoke abatement.",
        real_fault="the smoky brazier that dirtied the lantern glass",
        repair_text="carried away the smoky brazier and lit the garden with clean moon-oil lamps instead",
        ending_image="At dusk the lantern garden bloomed again, each light clear and golden, and the paths looked like streams made of stars.",
        helper_request="Please do not darken our lantern garden",
        tags={"light", "charter"},
    ),
}

OFFICIALS = {
    "steward": Official(
        id="steward",
        type="man",
        label="royal steward",
        entrance="in a plum-colored coat with a wax seal swinging from a ribbon",
        manner="stiff but not cruel",
        tags={"jargon", "terminate"},
    ),
    "bailiff": Official(
        id="bailiff",
        type="woman",
        label="castle bailiff",
        entrance="with a brass key-ring and boots polished like chestnuts",
        manner="brisk and proud of the rules",
        tags={"jargon", "terminate"},
    ),
    "chamberlain": Official(
        id="chamberlain",
        type="man",
        label="silver chamberlain",
        entrance="under a tall hat with a feather as straight as a ruler",
        manner="fussy and very sure of parchment",
        tags={"jargon", "terminate"},
    ),
}

HELPERS = {
    "marsh_wyrm": Helper(
        id="marsh_wyrm",
        type="dragon",
        label="the Marsh Wyrm",
        epithet="the Marsh Wyrm under the reeds",
        home="a mossy house by the water",
        skill="water",
        fear_text="Many people called the Marsh Wyrm a monster, though no one who had actually met him could remember being harmed.",
        reveal_text="I was the first keeper of wells in this kingdom, hidden for years under scales and mist.",
        proof_text="From inside one green scale-case, he drew the original water charter, dry as toast and stamped with the moon-queen's seal.",
        kind_act="set a kettle over a blue little flame and poured the visitor a cup of mint tea",
        tags={"water", "twist"},
    ),
    "hill_ogre": Helper(
        id="hill_ogre",
        type="ogre",
        label="the Hill Ogre",
        epithet="the Hill Ogre in the bell cave",
        home="a round cave tucked behind the old tower",
        skill="sound",
        fear_text="Children whispered that the Hill Ogre ate bells, but the truth had never been tested by a brave knock on the door.",
        reveal_text="I forged the first bells for this kingdom, and I know every true bell-mark and every false one.",
        proof_text="He unwrapped a tiny hammer of silver and the founding charter of the bell-makers' guild.",
        kind_act="opened the door with flour on his fingers and moved a tray of honey cakes to make room",
        tags={"sound", "twist"},
    ),
    "night_fairy": Helper(
        id="night_fairy",
        type="fairy",
        label="the Night Fairy",
        epithet="the Night Fairy among the moths",
        home="a lantern nest high in an elder tree",
        skill="light",
        fear_text="Some said the Night Fairy stole children's shadows, but really she only gathered burnt-out wicks and lonely moth wings.",
        reveal_text="I kept the first lantern garden for the queens of old, though most folk now remember only the flutter of my wings.",
        proof_text="From a silver sleeve, she produced a ribbon-bound lantern ledger and a seal bright as a firefly.",
        kind_act="lifted a lantern globe, blew away the dust, and made a warm glow blossom between her hands",
        tags={"light", "twist"},
    ),
}

GIRL_NAMES = ["Mira", "Elsie", "Nella", "Poppy", "Iris", "Tilda", "Wren", "Lina"]
BOY_NAMES = ["Tobin", "Milo", "Rowan", "Perrin", "Hugo", "Ned", "Ellis", "Bram"]


@dataclass
class StoryParams:
    setting: str
    problem: str
    official: str
    helper: str
    hero_name: str
    hero_gender: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        setting="green_hollow",
        problem="moonwell",
        official="steward",
        helper="marsh_wyrm",
        hero_name="Mira",
        hero_gender="girl",
    ),
    StoryParams(
        setting="hill_market",
        problem="bell_tree",
        official="bailiff",
        helper="hill_ogre",
        hero_name="Tobin",
        hero_gender="boy",
    ),
    StoryParams(
        setting="green_hollow",
        problem="lantern_garden",
        official="chamberlain",
        helper="night_fairy",
        hero_name="Iris",
        hero_gender="girl",
    ),
    StoryParams(
        setting="misty_ford",
        problem="bell_tree",
        official="steward",
        helper="hill_ogre",
        hero_name="Rowan",
        hero_gender="boy",
    ),
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    problem = f["problem"]
    setting = f["setting"]
    helper = f["helper_cfg"]
    return [
        f'Write a short fairy tale for a 3-to-5-year-old that includes the words "terminate", "plea", and "jargon". Set it in {setting.place} and build it around {problem.label}.',
        f"Tell a fairy tale where a child named {hero.id} tries to save {problem.label} after an official speaks confusing jargon, and the feared helper turns out to be the true keeper.",
        f"Write a twist story in a gentle fairy-tale style where {helper.label} seems scary at first but helps reveal what the old order really meant.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    official = f["official"]
    helper = f["helper"]
    problem = f["problem"]
    site = f["site"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, a brave child in {f['setting'].place}, who loved {site.label}. It is also about {official.label_word}, who brought the order, and {helper.label}, who knew the hidden truth.",
        ),
        (
            f"Why was {hero.id} upset?",
            f"{hero.id} was upset because the official said the kingdom might terminate {problem.order_text}. That put {site.label} in danger, so the child worried a beloved part of the village would be lost.",
        ),
        (
            "What was the child's plea?",
            f'{hero.id} begged the official not to take away {site.label} and later begged {helper.label} to listen and help. The plea mattered because the child refused to give up when the grown-up language made no sense.',
        ),
    ]
    if f.get("jargon_confused"):
        qa.append(
            (
                "Why did the jargon matter in the story?",
                f"The jargon hid the real meaning of the order, so people almost made the wrong choice. It sounded grand and official, but it kept the child from understanding that only {problem.real_fault} was supposed to be ended.",
            )
        )
    if f.get("twist_revealed"):
        qa.append(
            (
                "What was the twist?",
                f"The twist was that {helper.label}, whom people feared, was really the old keeper who understood the ancient charter. The helper showed that the order did not mean to destroy {site.label} at all.",
            )
        )
    if f.get("saved"):
        qa.append(
            (
                f"How was {site.label} saved?",
                f"{helper.label} read the old order correctly and proved what needed fixing. After that, the townsfolk {problem.repair_text}, so {site.label} stayed part of the village.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"terminate", "plea", "jargon", "twist"}
    tags |= set(world.facts["problem"].tags)
    tags |= set(world.facts["helper_cfg"].tags)
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags and tag in KNOWLEDGE:
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
    for ent in world.entities.values():
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.attrs:
            bits.append(f"attrs={ent.attrs}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
fits(P, H) :- problem(P), helper(H), domain(P, D), skill(H, D).
valid(S, P, H) :- setting(S), problem(P), helper(H), in_setting(P, S), fits(P, H).
saved(P, H) :- fits(P, H).
#show valid/3.
#show saved/2.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for setting_id in SETTINGS:
        lines.append(asp.fact("setting", setting_id))
    for problem_id, problem in PROBLEMS.items():
        lines.append(asp.fact("problem", problem_id))
        lines.append(asp.fact("domain", problem_id, problem.domain))
        for setting_id in sorted(problem.setting_ids):
            lines.append(asp.fact("in_setting", problem_id, setting_id))
    for helper_id, helper in HELPERS.items():
        lines.append(asp.fact("helper", helper_id))
        lines.append(asp.fact("skill", helper_id, helper.skill))
    return "\n".join(lines)


def asp_program(extra: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_saved_pairs() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "saved")))


def _smoke_story() -> None:
    sample = generate(CURATED[0])
    if not sample.story or "terminate" not in sample.story or "plea" not in sample.story or "jargon" not in sample.story:
        raise StoryError("(Smoke test failed: generated story is missing required seed words.)")
    _ = sample.to_dict()


def asp_verify() -> int:
    rc = 0
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: valid_combos() matches ASP ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    clingo_saved = set(asp_saved_pairs())
    python_saved = {
        (problem_id, helper_id)
        for problem_id, problem in PROBLEMS.items()
        for helper_id, helper in HELPERS.items()
        if helper_fits(problem, helper)
    }
    if clingo_saved == python_saved:
        print(f"OK: saved-pair logic matches ASP ({len(clingo_saved)} pairs).")
    else:
        rc = 1
        print("MISMATCH in saved-pair logic:")
        if clingo_saved - python_saved:
            print("  only in clingo:", sorted(clingo_saved - python_saved))
        if python_saved - clingo_saved:
            print("  only in python:", sorted(python_saved - clingo_saved))

    try:
        _smoke_story()
        print("OK: smoke story generation passed.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Fairy-tale storyworld: a child makes a plea, an official speaks jargon, and a twist reveals the true meaning of a termination order."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--official", choices=OFFICIALS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--hero-name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combos from the ASP twin")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting = SETTINGS.get(args.setting) if args.setting else None
    problem = PROBLEMS.get(args.problem) if args.problem else None
    helper = HELPERS.get(args.helper) if args.helper else None

    if setting and problem and setting.id not in problem.setting_ids:
        raise StoryError(explain_rejection(setting, problem, helper))
    if problem and helper and not helper_fits(problem, helper):
        raise StoryError(explain_rejection(setting, problem, helper))

    combos = [
        combo
        for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.problem is None or combo[1] == args.problem)
        and (args.helper is None or combo[2] == args.helper)
    ]
    if not combos:
        raise StoryError(explain_rejection(setting, problem, helper))

    chosen_setting, chosen_problem, chosen_helper = rng.choice(sorted(combos))
    official_id = args.official or rng.choice(sorted(OFFICIALS))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    hero_name = args.hero_name or rng.choice(GIRL_NAMES if hero_gender == "girl" else BOY_NAMES)

    return StoryParams(
        setting=chosen_setting,
        problem=chosen_problem,
        official=official_id,
        helper=chosen_helper,
        hero_name=hero_name,
        hero_gender=hero_gender,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting: {params.setting})")
    if params.problem not in PROBLEMS:
        raise StoryError(f"(Unknown problem: {params.problem})")
    if params.official not in OFFICIALS:
        raise StoryError(f"(Unknown official: {params.official})")
    if params.helper not in HELPERS:
        raise StoryError(f"(Unknown helper: {params.helper})")

    setting = SETTINGS[params.setting]
    problem = PROBLEMS[params.problem]
    official = OFFICIALS[params.official]
    helper = HELPERS[params.helper]

    if setting.id not in problem.setting_ids or not helper_fits(problem, helper):
        raise StoryError(explain_rejection(setting, problem, helper))

    world = tell(
        setting=setting,
        problem=problem,
        official_cfg=official,
        helper_cfg=helper,
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
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
        print(asp_program())
        return

    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, problem, helper) combos:\n")
        for setting_id, problem_id, helper_id in combos:
            print(f"  {setting_id:12} {problem_id:15} {helper_id}")
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
            header = f"### {p.hero_name}: {p.problem} in {p.setting} with {p.helper}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
