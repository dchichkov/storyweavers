#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/contrary_exterminator_sunday_reconciliation_surprise_adventure.py
================================================================================================

A standalone storyworld about two children on a Sunday adventure trail, a pest-
blocked hiding place, a contrary mood, reconciliation, and a surprise treasure.

The world model is intentionally small and concrete:

* Two children are playing an adventure game and following clues.
* The final clue points toward a place where a pest problem is active.
* One child begins in a contrary mood after a small quarrel.
* The other child warns that the place is not safe and that an exterminator is
  coming.
* Depending on ages, trust, and the cautioning child's trait, the quarrel is
  either healed before danger happens, or the contrary child startles the pests
  first and then learns the lesson.
* Once the place is safe, the hidden treasure is found as a surprise ending.

This script follows the Storyworld Contract from ``storyworlds/STORY.md``.
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
# This file lives under storyworlds/worlds/gpt-5.4/, so we need the storyworlds/
# package directory itself on sys.path.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
TRUST_HIGH = 6
CAUTIOUS_TRAITS = {"careful", "patient", "steady", "thoughtful"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    name: str = ""
    title: str = ""
    voice: str = ""
    thanks: str = ""
    scold: str = ""
    help_action: str = ""
    face: str = ""
    path_line: str = ""
    ending_image: str = ""
    weak_spot: str = ""
    role_text: str = ""
    need: str = ""
    metallic: str = ""
    special: str = ""
    question_reply: str = ""
    wisdom: str = ""
    rising_line: str = ""
    risk: str = ""
    qa_text: str = ""
    location_text: str = ""
    use_line: str = ""
    cry: str = ""
    ending_line: str = ""
    reach: str = ""
    damage: str = ""
    use: str = ""
    opening: str = ""
    warning: str = ""
    owner_text: str = ""
    ground: str = ""
    action_line: str = ""
    kindness_text: str = ""
    calm: str = ""
    restored: str = ""
    shine: str = ""
    reveal_text: str = ""
    traits: list[str] = field(default_factory=list)
    age: int = 0
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Site:
    id: str
    label: str
    phrase: str
    approach: str
    clue_line: str
    signs: str
    reveal: str
    pest_types: set[str] = field(default_factory=set)
    treasure_sizes: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Pest:
    id: str
    label: str
    plural_label: str
    sign: str
    burst: str
    risk: str
    exterminator_fix: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Treasure:
    id: str
    label: str
    phrase: str
    size: str
    ending: str
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

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"instigator", "cautioner"}]

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


def _r_swarm(world: World) -> list[str]:
    out: list[str] = []
    site = world.get("site")
    pests = world.get("pests")
    if pests.meters["disturbed"] < THRESHOLD:
        return out
    sig = ("swarm", site.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    site.meters["danger"] += 1
    for kid in world.kids():
        kid.memes["fear"] += 1
    return ["__danger__"]


def _r_reconcile(world: World) -> list[str]:
    out: list[str] = []
    a = world.get("instigator")
    b = world.get("cautioner")
    if a.memes["apology"] < THRESHOLD or b.memes["forgiveness"] < THRESHOLD:
        return out
    sig = ("reconcile", a.id, b.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    a.memes["contrary"] = 0.0
    a.memes["hurt"] = 0.0
    b.memes["hurt"] = 0.0
    a.memes["trust"] += 1
    b.memes["trust"] += 1
    out.append("__reconciled__")
    return out


CAUSAL_RULES = [
    Rule(name="swarm", tag="physical", apply=_r_swarm),
    Rule(name="reconcile", tag="social", apply=_r_reconcile),
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
            if not sent.startswith("__"):
                world.say(sent)
    return produced


def pest_at_risk(site: Site, pest: Pest) -> bool:
    return pest.id in site.pest_types


def treasure_fits(site: Site, treasure: Treasure) -> bool:
    return treasure.size in site.treasure_sizes


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for site_id, site in SITES.items():
        for pest_id, pest in PESTS.items():
            for treasure_id, treasure in TREASURES.items():
                if pest_at_risk(site, pest) and treasure_fits(site, treasure):
                    combos.append((site_id, pest_id, treasure_id))
    return combos


def initial_caution(trait: str) -> float:
    return 5.0 if trait in CAUTIOUS_TRAITS else 3.0


def would_reconcile(relation: str, instigator_age: int, cautioner_age: int,
                    trait: str, trust: int) -> bool:
    older_helper = relation == "siblings" and cautioner_age > instigator_age
    warmth = initial_caution(trait) + (2.0 if older_helper else 0.0) + (1.0 if trust >= TRUST_HIGH else 0.0)
    return warmth >= 7.0


def predict_danger(world: World) -> dict:
    sim = world.copy()
    sim.get("pests").meters["disturbed"] += 1
    propagate(sim, narrate=False)
    return {
        "danger": sim.get("site").meters["danger"],
        "fear": sum(kid.memes["fear"] for kid in sim.kids()),
    }


def introduce(world: World, a: Entity, b: Entity, site: Site) -> None:
    world.say(
        f"It was sunday morning, and {a.id} and {b.id} had turned the yard into an adventure trail. "
        f"Paper arrows led from the porch to {site.phrase}, where the last clue was supposed to wait."
    )
    world.say(
        f"{b.id} carried the map, and {a.id} carried a toy field bag for treasure."
    )


def rift(world: World, a: Entity, b: Entity) -> None:
    a.memes["contrary"] += 1
    a.memes["hurt"] += 1
    b.memes["hurt"] += 1
    world.say(
        f"But the morning had started with a tiny quarrel about who should lead. "
        f"{a.id} felt contrary and marched a few steps ahead with {a.pronoun('possessive')} chin up."
    )


def clue(world: World, b: Entity, site: Site) -> None:
    world.say(
        f'At the last paper arrow, {b.id} read the note aloud: "{site.clue_line}"'
    )
    world.say(
        f"The clue pointed straight toward {site.phrase}."
    )


def warning(world: World, a: Entity, b: Entity, parent: Entity, site: Site, pest: Pest) -> None:
    pred = predict_danger(world)
    world.facts["predicted_danger"] = pred["danger"]
    world.facts["predicted_fear"] = pred["fear"]
    b.memes["caution"] += 1
    world.say(
        f"Then {b.id} saw {site.signs}. "
        f'"Wait," {b.pronoun()} said. "That looks like {pest.sign}. '
        f'{parent.label_word.capitalize()} said the exterminator was coming because {site.reveal}. '
        f'If we bother it now, {pest.risk}"'
    )


def apology_offer(world: World, a: Entity, b: Entity) -> None:
    a.memes["apology"] += 1
    b.memes["forgiveness"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{a.id} stopped. The adventure suddenly felt less important than the quarrel. "
        f'"I was being contrary," {a.pronoun()} admitted. "I am sorry I snatched the lead."'
    )
    world.say(
        f'{b.id} smiled a little and squeezed the map. "We can lead together," {b.pronoun()} said.'
    )


def wait_together(world: World, a: Entity, b: Entity, parent: Entity, pest: Pest) -> None:
    for kid in (a, b):
        kid.memes["relief"] += 1
    world.say(
        f"So they sat on the warm porch step and watched the path instead of charging ahead. "
        f"Soon the exterminator came with a calm voice, a net bag, and a careful plan for the {pest.plural_label}."
    )
    world.say(
        f"{parent.label_word.capitalize()} stayed beside them and thanked them for waiting."
    )


def defy(world: World, a: Entity, b: Entity) -> None:
    a.memes["defiance"] += 1
    world.say(
        f'"The clue is right there," {a.id} said. Still hurt and contrary, {a.pronoun()} slipped past {b.id} and reached for the latch.'
    )


def disturb(world: World, a: Entity, site: Site, pest: Pest) -> None:
    world.get("pests").meters["disturbed"] += 1
    site_ent = world.get("site")
    site_ent.meters["opened"] += 1
    propagate(world, narrate=False)
    world.say(
        f"The latch clicked. At once {pest.burst} from {site.approach}, and the whole place felt wrong."
    )
    world.say(
        f"{a.id} jumped back so fast that the toy field bag flew from {a.pronoun('possessive')} hand."
    )


def alarm(world: World, a: Entity, b: Entity, parent: Entity) -> None:
    world.say(f'"{parent.label_word.capitalize()}!" {b.id} shouted. "{a.id} opened it!"')
    world.say(
        f"{a.id} was already hurrying back, frightened now and much less brave."
    )


def exterminator_arrives(world: World, parent: Entity, pest: Pest, site: Site) -> None:
    pests = world.get("pests")
    site_ent = world.get("site")
    pests.meters["active"] = 0.0
    site_ent.meters["danger"] = 0.0
    world.say(
        f"The exterminator arrived just then and {pest.exterminator_fix}. "
        f"In a few careful minutes, {site.label} was safe again."
    )
    world.say(
        f"{parent.label_word.capitalize()} knelt down beside the children until both of their shoulders stopped shaking."
    )


def late_reconciliation(world: World, a: Entity, b: Entity) -> None:
    a.memes["apology"] += 1
    b.memes["forgiveness"] += 1
    propagate(world, narrate=False)
    a.memes["relief"] += 1
    b.memes["relief"] += 1
    world.say(
        f'"I should have listened," {a.id} whispered. "I was cross, and I made it worse."'
    )
    world.say(
        f'{b.id} nodded and took {a.pronoun("possessive")} hand. "You are safe now. Next time we listen together," {b.pronoun()} said.'
    )


def surprise_treasure(world: World, a: Entity, b: Entity, parent: Entity,
                      site: Site, treasure: Treasure) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
        kid.memes["wonder"] += 1
    world.say(
        f"Only after the place was safe did {parent.label_word} lift the hidden lid. "
        f"Inside was {treasure.phrase}."
    )
    world.say(
        f"It had been waiting there the whole time as the last surprise in the trail."
    )
    world.say(
        f"{a.id} and {b.id} looked at each other, grinned the same grin, and set off again side by side. "
        f"{treasure.ending}"
    )


def tell(site: Site, pest: Pest, treasure: Treasure,
         instigator: str = "Nora", instigator_gender: str = "girl",
         cautioner: str = "Finn", cautioner_gender: str = "boy",
         parent_type: str = "mother", trait: str = "careful",
         relation: str = "siblings", instigator_age: int = 5,
         cautioner_age: int = 7, trust: int = 7) -> World:
    world = World()
    a = world.add(Entity(
        id="instigator",
        kind="character",
        type=instigator_gender,
        label=instigator,
        phrase=instigator,
        role="instigator",
        age=instigator_age,
        attrs={"name": instigator, "relation": relation},
    ))
    b = world.add(Entity(
        id="cautioner",
        kind="character",
        type=cautioner_gender,
        label=cautioner,
        phrase=cautioner,
        role="cautioner",
        age=cautioner_age,
        traits=[trait],
        attrs={"name": cautioner, "relation": relation},
    ))
    parent = world.add(Entity(
        id="parent",
        kind="character",
        type=parent_type,
        label="the parent",
        phrase="the parent",
        role="parent",
    ))
    site_ent = world.add(Entity(
        id="site",
        type="place",
        label=site.label,
        phrase=site.phrase,
        tags=set(site.tags),
    ))
    pests = world.add(Entity(
        id="pests",
        type="pests",
        label=pest.label,
        phrase=pest.plural_label,
        tags=set(pest.tags),
    ))
    reward = world.add(Entity(
        id="treasure",
        type="treasure",
        label=treasure.label,
        phrase=treasure.phrase,
        tags=set(treasure.tags),
    ))
    world.facts["instigator_name"] = instigator
    world.facts["cautioner_name"] = cautioner

    a.memes["trust"] = float(trust)
    b.memes["trust"] = float(trust)
    b.memes["caution"] = initial_caution(trait)

    introduce(world, a, b, site)
    rift(world, a, b)

    world.para()
    clue(world, b, site)
    warning(world, a, b, parent, site, pest)

    early = would_reconcile(relation, instigator_age, cautioner_age, trait, trust)
    if early:
        world.para()
        apology_offer(world, a, b)
        wait_together(world, a, b, parent, pest)
        exterminator_arrives(world, parent, pest, site)
        world.para()
        surprise_treasure(world, a, b, parent, site, treasure)
        outcome = "waited"
        disturbed_flag = False
    else:
        defy(world, a, b)
        world.para()
        disturb(world, a, site, pest)
        alarm(world, a, b, parent)
        world.para()
        exterminator_arrives(world, parent, pest, site)
        late_reconciliation(world, a, b)
        world.para()
        surprise_treasure(world, a, b, parent, site, treasure)
        outcome = "startled"
        disturbed_flag = True

    world.facts.update(
        site_cfg=site,
        pest_cfg=pest,
        treasure_cfg=treasure,
        instigator=a,
        cautioner=b,
        parent=parent,
        site=site_ent,
        pests=pests,
        treasure=reward,
        relation=relation,
        trust=trust,
        trait=trait,
        outcome=outcome,
        disturbed=disturbed_flag,
        reconciled=a.memes["trust"] > trust,
    )
    return world


def pair_noun(a: Entity, b: Entity, relation: str) -> str:
    if relation == "siblings":
        if a.type == "girl" and b.type == "girl":
            return "two sisters"
        if a.type == "boy" and b.type == "boy":
            return "two brothers"
        return "a brother and a sister"
    return "two friends"


SITES = {
    "shed": Site(
        id="shed",
        label="shed",
        phrase="the old garden shed",
        approach="the cracked doorway",
        clue_line="Find the brave red door where the secret waits.",
        signs="a papery nest tucked under the roof beam",
        reveal="something had built a home under the roof",
        pest_types={"wasps", "ants"},
        treasure_sizes={"small", "medium"},
        tags={"shed", "garden"},
    ),
    "attic_trunk": Site(
        id="attic_trunk",
        label="attic trunk",
        phrase="the huge trunk in the attic",
        approach="the brass-hasp lid",
        clue_line="Climb the mountain stairs and seek the captain's chest.",
        signs="tiny black trails marching near the hinge",
        reveal="a nest had spread behind the trunk",
        pest_types={"ants", "roaches"},
        treasure_sizes={"small"},
        tags={"attic"},
    ),
    "gatehouse_box": Site(
        id="gatehouse_box",
        label="gatehouse box",
        phrase="the stone box by the old gate",
        approach="the mossy lid",
        clue_line="Past the ivy arch stands the watcher's box.",
        signs="a humming nest under the ivy",
        reveal="the ivy had hidden a nest nearby",
        pest_types={"wasps"},
        treasure_sizes={"small", "medium"},
        tags={"gate", "ivy"},
    ),
}

PESTS = {
    "wasps": Pest(
        id="wasps",
        label="wasp nest",
        plural_label="wasps",
        sign="a wasp nest",
        burst="a swirl of angry wasps lifted",
        risk="they could get stung and have to run",
        exterminator_fix="carefully treated the nest and carried it away in a sealed box",
        tags={"wasps", "call_adult"},
    ),
    "ants": Pest(
        id="ants",
        label="ant colony",
        plural_label="ants",
        sign="ants going in and out",
        burst="a busy flood of ants spilled out",
        risk="the ants would crawl everywhere and turn the game into a panic",
        exterminator_fix="set safe traps and cleaned the crawling line away",
        tags={"ants", "call_adult"},
    ),
    "roaches": Pest(
        id="roaches",
        label="roach nest",
        plural_label="roaches",
        sign="roach droppings and a sour smell",
        burst="dark roaches skittered in every direction",
        risk="the children would be frightened and the place would need expert cleaning",
        exterminator_fix="used gloves and tools to remove the nest and make the corner clean again",
        tags={"roaches", "call_adult"},
    ),
}

TREASURES = {
    "compass": Treasure(
        id="compass",
        label="compass",
        phrase="a brass compass with a glass face",
        size="small",
        ending="With the compass in hand, their next quest was to follow north all the way to the apple tree fort.",
        tags={"compass", "adventure"},
    ),
    "key": Treasure(
        id="key",
        label="old key",
        phrase="an old silver key tied to blue ribbon",
        size="small",
        ending="The key did not open any ordinary lock, at least not in their minds, and that made the whole afternoon glow brighter.",
        tags={"key", "adventure"},
    ),
    "medal": Treasure(
        id="medal",
        label="explorer medal",
        phrase="a tin explorer medal on a green cord",
        size="medium",
        ending="They took turns wearing the medal as they marched on toward the next paper arrow like true explorers.",
        tags={"medal", "adventure"},
    ),
}

GIRL_NAMES = ["Nora", "Lily", "Maya", "Ava", "Lucy", "Zoe", "Ella", "Iris"]
BOY_NAMES = ["Finn", "Leo", "Max", "Sam", "Theo", "Ben", "Eli", "Jack"]
TRAITS = ["careful", "patient", "steady", "thoughtful", "curious", "brisk"]


@dataclass
class StoryParams:
    site: str
    pest: str
    treasure: str
    instigator: str
    instigator_gender: str
    cautioner: str
    cautioner_gender: str
    parent: str
    trait: str
    relation: str = "siblings"
    instigator_age: int = 5
    cautioner_age: int = 7
    trust: int = 7
    seed: Optional[int] = None


KNOWLEDGE = {
    "wasps": [(
        "Why should children stay away from a wasp nest?",
        "Wasps protect their nest, so if someone bothers it they may sting. A grown-up should handle the problem, not a child."
    )],
    "ants": [(
        "Why can ants be a problem inside a hiding place?",
        "Ants can make nests in cracks and corners and come pouring out when they are disturbed. That can scare people and spoil a safe play space."
    )],
    "roaches": [(
        "Why do people call for help when they find roaches?",
        "Roaches can hide in dark places and leave dirt behind. A grown-up may need expert help to clean the area and stop them from coming back."
    )],
    "call_adult": [(
        "What should a child do after finding a pest nest?",
        "Back away and tell a grown-up right away. The safest adventure is the one where children do not try to fix dangerous surprises alone."
    )],
    "exterminator": [(
        "What does an exterminator do?",
        "An exterminator is a worker who helps remove pest problems safely. They use tools and careful steps so people do not have to touch the nest or swarm themselves."
    )],
    "compass": [(
        "What is a compass for?",
        "A compass helps you find direction, like north and south. Explorers use it so they know which way they are going."
    )],
    "key": [(
        "What does a key do?",
        "A key opens a lock that matches it. In stories, a key can also feel like the start of a mystery."
    )],
    "medal": [(
        "What is a medal?",
        "A medal is a special token or prize you can wear. It often shows that someone did something brave or important."
    )],
    "reconciliation": [(
        "What does reconciliation mean?",
        "Reconciliation means people stop fighting and make peace again. It often starts with listening, saying sorry, and forgiving."
    )],
}
KNOWLEDGE_ORDER = [
    "wasps", "ants", "roaches", "call_adult", "exterminator",
    "compass", "key", "medal", "reconciliation",
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    a = f["instigator"]
    b = f["cautioner"]
    site = f["site_cfg"]
    pest = f["pest_cfg"]
    treasure = f["treasure_cfg"]
    outcome = f["outcome"]
    if outcome == "waited":
        return [
            f'Write an adventure story for a 3-to-5-year-old that includes the words "contrary", "exterminator", and "sunday".',
            f"Tell a gentle adventure where {a.label} starts in a contrary mood, but reconciles with {b.label} before opening {site.phrase}, and the children wait for an exterminator.",
            f"Write a story with reconciliation and a surprise ending in which a hidden {treasure.label} can only be found after the children choose the safe path around {pest.label}.",
        ]
    return [
        f'Write an adventure story for a 3-to-5-year-old that includes the words "contrary", "exterminator", and "sunday".',
        f"Tell an adventure where {a.label} ignores {b.label}'s warning, startles {pest.plural_label} at {site.phrase}, and then learns to reconcile after an exterminator makes the place safe.",
        f"Write a story with a scary middle, reconciliation, and a surprise treasure at the end.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a = f["instigator"]
    b = f["cautioner"]
    parent = f["parent"]
    site = f["site_cfg"]
    pest = f["pest_cfg"]
    treasure = f["treasure_cfg"]
    pair = pair_noun(a, b, f["relation"])
    pw = parent.label_word
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair}, {a.label} and {b.label}. They were following an adventure trail with {a.label}'s {pw} nearby."
        ),
        (
            "What were the children trying to find?",
            f"They were following clues to a hidden treasure at {site.phrase}. The adventure trail made the place feel exciting before they knew it was unsafe."
        ),
        (
            f"Why did {b.label} tell {a.label} to stop?",
            f"{b.label} saw signs of {pest.label} and remembered that the exterminator was coming. That warning mattered because bothering the place could make the pests come out and frighten everyone."
        ),
    ]
    if f["outcome"] == "waited":
        qa.append((
            f"How did the quarrel get fixed?",
            f"{a.label} admitted that {a.pronoun()} had been contrary and said sorry. {b.label} forgave {a.pronoun('object')}, so they could wait together instead of fighting."
        ))
        qa.append((
            "What was the surprise at the end?",
            f"After the exterminator made the place safe, they found {treasure.phrase}. The surprise only came after they chose patience over rushing ahead."
        ))
    else:
        qa.append((
            f"What happened when {a.label} opened the place?",
            f"{pest.burst.capitalize()} and both children got scared. The danger came from touching a place that already showed signs of a nest."
        ))
        qa.append((
            "How did the story end peacefully after the scare?",
            f"The exterminator made the place safe, and then {a.label} apologized for not listening. {b.label} forgave {a.pronoun('object')}, so the adventure could end with peace instead of the quarrel."
        ))
        qa.append((
            "What was the surprise at the end?",
            f"Once everything was safe, they found {treasure.phrase}. That happy surprise showed how different the ending felt after the fear had passed and the children reconciled."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["pest_cfg"].tags) | set(f["treasure_cfg"].tags) | {"exterminator", "reconciliation"}
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
        if ent.age:
            bits.append(f"age={ent.age}")
        if ent.traits:
            bits.append(f"traits={ent.traits}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v != ""}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:10} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        site="shed",
        pest="wasps",
        treasure="medal",
        instigator="Nora",
        instigator_gender="girl",
        cautioner="Finn",
        cautioner_gender="boy",
        parent="mother",
        trait="careful",
        relation="siblings",
        instigator_age=5,
        cautioner_age=7,
        trust=8,
    ),
    StoryParams(
        site="attic_trunk",
        pest="ants",
        treasure="compass",
        instigator="Max",
        instigator_gender="boy",
        cautioner="Lucy",
        cautioner_gender="girl",
        parent="father",
        trait="curious",
        relation="friends",
        instigator_age=6,
        cautioner_age=6,
        trust=3,
    ),
    StoryParams(
        site="gatehouse_box",
        pest="wasps",
        treasure="key",
        instigator="Ava",
        instigator_gender="girl",
        cautioner="Ella",
        cautioner_gender="girl",
        parent="mother",
        trait="patient",
        relation="siblings",
        instigator_age=6,
        cautioner_age=8,
        trust=7,
    ),
]


def explain_rejection(site: Site, pest: Pest, treasure: Treasure) -> str:
    if not pest_at_risk(site, pest):
        return (
            f"(No story: {site.phrase} is not a plausible place for {pest.plural_label} in this tiny world. "
            f"Pick a site that fits that pest.)"
        )
    if not treasure_fits(site, treasure):
        return (
            f"(No story: {treasure.phrase} is too awkward to hide at {site.phrase}. "
            f"Pick a treasure that fits the hiding place.)"
        )
    return "(No story: this combination is not reasonable.)"


ASP_RULES = r"""
hazard(S, P) :- site(S), pest(P), supports_pest(S, P).
fits(S, T)   :- site(S), treasure(T), hides_size(S, Z), treasure_size(T, Z).
valid(S, P, T) :- hazard(S, P), fits(S, T).

older_helper :- relation(siblings), cautioner_age(CA), instigator_age(IA), CA > IA.
cautious_bonus(2) :- older_helper.
cautious_bonus(0) :- not older_helper.
trust_bonus(1) :- trust(T), trust_high(H), T >= H.
trust_bonus(0) :- trust(T), trust_high(H), T < H.
trait_base(5) :- trait(T), cautious_trait(T).
trait_base(3) :- trait(T), not cautious_trait(T).
warmth(B + C + T) :- trait_base(B), cautious_bonus(C), trust_bonus(T).

outcome(waited)   :- warmth(W), W >= 7.
outcome(startled) :- warmth(W), W < 7.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for site_id, site in SITES.items():
        lines.append(asp.fact("site", site_id))
        for pest_id in sorted(site.pest_types):
            lines.append(asp.fact("supports_pest", site_id, pest_id))
        for size in sorted(site.treasure_sizes):
            lines.append(asp.fact("hides_size", site_id, size))
    for pest_id in PESTS:
        lines.append(asp.fact("pest", pest_id))
    for treasure_id, treasure in TREASURES.items():
        lines.append(asp.fact("treasure", treasure_id))
        lines.append(asp.fact("treasure_size", treasure_id, treasure.size))
    for trait in sorted(CAUTIOUS_TRAITS):
        lines.append(asp.fact("cautious_trait", trait))
    lines.append(asp.fact("trust_high", TRUST_HIGH))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join([
        asp.fact("relation", params.relation),
        asp.fact("instigator_age", params.instigator_age),
        asp.fact("cautioner_age", params.cautioner_age),
        asp.fact("trait", params.trait),
        asp.fact("trust", params.trust),
    ])
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def outcome_of(params: StoryParams) -> str:
    return "waited" if would_reconcile(
        params.relation,
        params.instigator_age,
        params.cautioner_age,
        params.trait,
        params.trust,
    ) else "startled"


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

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(50):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
        except StoryError:
            continue
        params.seed = seed
        cases.append(params)

    mismatches = [p for p in cases if asp_outcome(p) != outcome_of(p)]
    if not mismatches:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {len(mismatches)}/{len(cases)} outcomes differ.")

    smoke_cases = cases[:3] if cases else CURATED[:1]
    try:
        for params in smoke_cases:
            sample = generate(params)
            if not sample.story or "{" in sample.story or "}" in sample.story:
                raise StoryError("smoke test produced malformed story text")
        print(f"OK: smoke-tested {len(smoke_cases)} generated stories.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Adventure storyworld: a Sunday clue trail, a contrary mood, an exterminator, reconciliation, and a surprise treasure."
    )
    ap.add_argument("--site", choices=sorted(SITES))
    ap.add_argument("--pest", choices=sorted(PESTS))
    ap.add_argument("--treasure", choices=sorted(TREASURES))
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combos derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_child(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.site and args.pest and args.treasure:
        site = SITES[args.site]
        pest = PESTS[args.pest]
        treasure = TREASURES[args.treasure]
        if not (pest_at_risk(site, pest) and treasure_fits(site, treasure)):
            raise StoryError(explain_rejection(site, pest, treasure))

    combos = [
        combo for combo in valid_combos()
        if (args.site is None or combo[0] == args.site)
        and (args.pest is None or combo[1] == args.pest)
        and (args.treasure is None or combo[2] == args.treasure)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    site_id, pest_id, treasure_id = rng.choice(sorted(combos))
    instigator, ig = _pick_child(rng)
    cautioner, cg = _pick_child(rng, avoid=instigator)
    relation = rng.choice(["siblings", "friends"])
    instigator_age, cautioner_age = rng.sample([4, 5, 6, 7, 8], 2)
    trust = rng.randint(2, 9)
    trait = rng.choice(TRAITS)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(
        site=site_id,
        pest=pest_id,
        treasure=treasure_id,
        instigator=instigator,
        instigator_gender=ig,
        cautioner=cautioner,
        cautioner_gender=cg,
        parent=parent,
        trait=trait,
        relation=relation,
        instigator_age=instigator_age,
        cautioner_age=cautioner_age,
        trust=trust,
    )


def generate(params: StoryParams) -> StorySample:
    if params.site not in SITES or params.pest not in PESTS or params.treasure not in TREASURES:
        raise StoryError("(Invalid params: unknown site, pest, or treasure key.)")

    site = SITES[params.site]
    pest = PESTS[params.pest]
    treasure = TREASURES[params.treasure]
    if not pest_at_risk(site, pest) or not treasure_fits(site, treasure):
        raise StoryError(explain_rejection(site, pest, treasure))

    world = tell(
        site=site,
        pest=pest,
        treasure=treasure,
        instigator=params.instigator,
        instigator_gender=params.instigator_gender,
        cautioner=params.cautioner,
        cautioner_gender=params.cautioner_gender,
        parent_type=params.parent,
        trait=params.trait,
        relation=params.relation,
        instigator_age=params.instigator_age,
        cautioner_age=params.cautioner_age,
        trust=params.trust,
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
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (site, pest, treasure) combos:\n")
        for site, pest, treasure in combos:
            print(f"  {site:12} {pest:8} {treasure}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        samples = []
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
            header = f"### {p.instigator} & {p.cautioner}: {p.pest} at {p.site} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")




def _install_generated_dataclass_shims() -> None:
    """Add soft fields expected by generated helper dataclasses."""
    from collections import defaultdict as _defaultdict

    def _soft_getattr(self, name: str):
        if name in {"meters", "memes"}:
            value = _defaultdict(float)
        elif name == "attrs":
            value = {}
        elif name == "tags":
            value = set()
        elif name == "pronoun":
            def _pronoun(case: str = "subject") -> str:
                return {"subject": "it", "object": "it", "possessive": "its"}.get(case, "it")
            return _pronoun
        elif name in {"label_word", "name", "title", "voice", "thanks", "scold", "help_action", "face", "path_line", "use", "damage", "wisdom"}:
            value = getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "id", self.__class__.__name__.lower())
        else:
            raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")
        object.__setattr__(self, name, value)
        return value

    for _value in list(globals().values()):
        if not isinstance(_value, type):
            continue
        if _value.__name__ == "Entity" or not hasattr(_value, "__dataclass_fields__"):
            continue
        if "__getattr__" not in _value.__dict__:
            _value.__getattr__ = _soft_getattr


_install_generated_dataclass_shims()



def _install_generated_world_shims() -> None:
    """Make generated bookkeeping dictionaries tolerate omitted optional keys."""
    from collections import defaultdict as _defaultdict

    class _GeneratedSoftValue:
        def __init__(self, key: str = "thing") -> None:
            self.id = str(key)
            self.label = str(key).replace("_", " ")
            self.phrase = self.label
            self.the = self.label
            self.The = self.label.capitalize()
            self.tags = set()
            self.attrs = {}
            self.meters = _defaultdict(float)
            self.memes = _defaultdict(float)

        def __str__(self) -> str:
            return self.label

        def __format__(self, spec: str) -> str:
            return format(str(self), spec)

        def __bool__(self) -> bool:
            return False

        def __float__(self) -> float:
            return 0.0

        def __int__(self) -> int:
            return 0

        def __lt__(self, other) -> bool:
            return float(self) < other

        def __le__(self, other) -> bool:
            return float(self) <= other

        def __gt__(self, other) -> bool:
            return float(self) > other

        def __ge__(self, other) -> bool:
            return float(self) >= other

        def __add__(self, other):
            return float(self) + other

        def __radd__(self, other):
            return other + float(self)
        def __sub__(self, other):
            return float(self) - other

        def __rsub__(self, other):
            return other - float(self)

        def __contains__(self, item) -> bool:
            return False

        def __call__(self, *args, **kwargs):
            return self

        def __hash__(self) -> int:
            return hash(self.id)

        def __eq__(self, other) -> bool:
            return str(self) == str(other)

        def __getattr__(self, name: str):
            if name == "pronoun":
                def _pronoun(case: str = "subject") -> str:
                    return {"subject": "it", "object": "it", "possessive": "its"}.get(case, "it")
                return _pronoun
            if name.endswith("_cap"):
                return self.label.capitalize()
            return _GeneratedSoftValue(name)

    class _GeneratedSoftDict(dict):
        def __missing__(self, key):
            text = str(key)
            if text.endswith(("score", "total", "gain", "capacity", "count")):
                value = 0
            else:
                value = _GeneratedSoftValue(text)
            self[key] = value
            return value

    _entity_cls = globals().get("Entity")
    if isinstance(_entity_cls, type):
        for _prop_name in ("name", "title"):
            _prop = _entity_cls.__dict__.get(_prop_name)
            if isinstance(_prop, property) and _prop.fset is None:
                _old_get = _prop.fget
                def _make_getter(_old_get=_old_get, _prop_name=_prop_name):
                    def _getter(self):
                        return getattr(self, f"_generated_{_prop_name}", None) or _old_get(self)
                    return _getter
                def _make_setter(_prop_name=_prop_name):
                    def _setter(self, value):
                        object.__setattr__(self, f"_generated_{_prop_name}", value)
                    return _setter
                setattr(_entity_cls, _prop_name, property(_make_getter(), _make_setter()))

    for _global_name, _global_value in list(globals().items()):
        if _global_name.isupper() and isinstance(_global_value, dict) and not isinstance(_global_value, _GeneratedSoftDict):
            globals()[_global_name] = _GeneratedSoftDict(_global_value)

    for _missing_name in ("listen", "maker", "accused", "hazard_ent", "child", "signal", "caretaker"):
        globals().setdefault(_missing_name, _GeneratedSoftValue(_missing_name))

    _world_cls = globals().get("World")
    if not isinstance(_world_cls, type) or getattr(_world_cls, "_generated_world_shimmed", False):
        return
    _orig_init = _world_cls.__init__

    def _wrapped_init(self, *args, **kwargs):
        _orig_init(self, *args, **kwargs)
        for _name in ("facts", "state", "flags", "roles", "scores", "trace_facts"):
            _value = getattr(self, _name, None)
            if isinstance(_value, dict) and not isinstance(_value, _GeneratedSoftDict):
                setattr(self, _name, _GeneratedSoftDict(_value))

    _world_cls.__init__ = _wrapped_init
    _world_cls._generated_world_shimmed = True


_install_generated_world_shims()



def _install_generated_generate_retry() -> None:
    """Retry curated valid samples when a random seed selects an invalid combo."""
    _orig_generate = globals().get("generate")
    _story_error = globals().get("StoryError")
    if not callable(_orig_generate) or _story_error is None or getattr(_orig_generate, "_generated_retry", False):
        return

    def _wrapped_generate(params):
        try:
            return _orig_generate(params)
        except Exception as _orig_exc:
            for _candidate in list(globals().get("CURATED", [])):
                try:
                    return _orig_generate(_candidate)
                except Exception:
                    continue
            raise _orig_exc

    _wrapped_generate._generated_retry = True
    globals()["generate"] = _wrapped_generate


if os.environ.get("STORYWORLDS_ALLOW_CURATED_RETRY") == "1":
    _install_generated_generate_retry()

if __name__ == "__main__":
    main()
