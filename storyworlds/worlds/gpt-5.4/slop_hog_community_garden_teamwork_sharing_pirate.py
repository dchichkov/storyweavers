#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/slop_hog_community_garden_teamwork_sharing_pirate.py
===============================================================================

A standalone storyworld for a tiny pirate-flavored tale in a community garden:
two children pretend to be pirates, carry a bucket of slop to the compost, and
must keep a hungry hog away from the garden beds by sharing tools and working
together.

The core shape mirrors other Storyweavers worlds:
- typed entities with physical meters and emotional memes
- a short state-driven screenplay with a clear beginning, turn, and ending
- a Python reasonableness gate plus an inline ASP twin
- three Q&A sets generated from world state, not by parsing English

Run it
------
    python storyworlds/worlds/gpt-5.4/slop_hog_community_garden_teamwork_sharing_pirate.py
    python storyworlds/worlds/gpt-5.4/slop_hog_community_garden_teamwork_sharing_pirate.py --crop marigolds
    python storyworlds/worlds/gpt-5.4/slop_hog_community_garden_teamwork_sharing_pirate.py --plan paper_tray
    python storyworlds/worlds/gpt-5.4/slop_hog_community_garden_teamwork_sharing_pirate.py --all
    python storyworlds/worlds/gpt-5.4/slop_hog_community_garden_teamwork_sharing_pirate.py --verify
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
BRAVERY_INIT = 6.0
SHARING_TRAITS = {"careful", "kind", "patient", "sensible"}


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
    tasty_to_hog: bool = False
    leakproof: bool = False
    shareable: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Theme:
    id: str
    scene: str
    rig: str
    title_a: str
    title_b: str
    quest: str
    sendoff: str


@dataclass
class SlopKind:
    id: str
    label: str
    phrase: str
    smell: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Crop:
    id: str
    label: str
    bed: str
    tasty: bool
    fragility: int
    tags: set[str] = field(default_factory=set)

    @property
    def the_bed(self) -> str:
        return f"the {self.bed}"

    @property
    def The_bed(self) -> str:
        return f"The {self.bed}"


@dataclass
class Plan:
    id: str
    label: str
    phrase: str
    sense: int
    power: int
    leakproof: bool
    shareable: bool
    team_text: str
    rescue_text: str
    fail_text: str
    qa_text: str
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
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_hog_risk(world: World) -> list[str]:
    out: list[str] = []
    hog = world.entities.get("hog")
    crop = world.entities.get("crop")
    garden = world.entities.get("garden")
    if not hog or not crop or not garden:
        return out
    if hog.meters["at_crop"] < THRESHOLD:
        return out
    sig = ("hog_risk", crop.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    garden.meters["risk"] += 1
    crop.meters["trampled"] += 1
    for kid in world.kids():
        kid.memes["fear"] += 1
        kid.memes["sadness"] += 1
    out.append("__hog__")
    return out


CAUSAL_RULES = [
    Rule("hog_risk", "physical", _r_hog_risk),
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
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def crop_at_risk(slop: SlopKind, crop: Crop) -> bool:
    return "food" in slop.tags and crop.tasty


def sensible_plans() -> list[Plan]:
    return [p for p in PLANS.values() if p.sense >= SENSE_MIN]


def risk_severity(crop: Crop, delay: int) -> int:
    return crop.fragility + delay


def is_saved(plan: Plan, crop: Crop, delay: int) -> bool:
    return plan.power >= risk_severity(crop, delay)


def initial_sharing(trait: str) -> float:
    return 5.0 if trait in SHARING_TRAITS else 3.0


def would_share_first(relation: str, instigator_age: int, cautioner_age: int, trait: str) -> bool:
    cautioner_older = relation == "siblings" and cautioner_age > instigator_age
    authority = (initial_sharing(trait) + 1.0) + (4.0 if cautioner_older else 0.0)
    return cautioner_older and authority > BRAVERY_INIT


def predict_trouble(world: World, crop_id: str) -> dict:
    sim = world.copy()
    hog = sim.get("hog")
    crop = sim.get(crop_id)
    hog.meters["at_crop"] += 1
    propagate(sim, narrate=False)
    return {
        "trampled": crop.meters["trampled"] >= THRESHOLD,
        "risk": sim.get("garden").meters["risk"],
    }


def play_setup(world: World, a: Entity, b: Entity, theme: Theme) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
    world.say(
        f"On a bright morning, {a.id} and {b.id} turned the community garden into {theme.scene}. "
        f"{theme.rig}"
    )
    world.say(
        f'"{theme.title_a} {a.id} and {theme.title_b} {b.id}!" {a.id} shouted. '
        f'"Today we sail for {theme.quest}!"'
    )


def introduce_job(world: World, b: Entity, slop: SlopKind, crop: Crop) -> None:
    world.say(
        f"Near the compost corner waited {slop.phrase}. It smelled {slop.smell}, and the gardeners "
        f"wanted it tipped into the bin instead of left beside {crop.the_bed}."
    )
    world.say(
        f'{b.id} peered toward {crop.the_bed}. "{crop.label.capitalize()} are growing there," '
        f'{b.pronoun()} said. "We have to keep the path clean."'
    )


def tempt(world: World, a: Entity, plan: Plan) -> None:
    a.memes["bravado"] += 1
    world.say(
        f'{a.id} spotted {plan.phrase}. "{plan.label.capitalize()}! I can do the whole job myself," '
        f'{a.pronoun()} said.'
    )
    world.say("For one excited second, doing it alone felt fast and grand.")


def warn(world: World, b: Entity, a: Entity, slop: SlopKind, crop: Crop, adult: Entity, plan: Plan) -> None:
    pred = predict_trouble(world, "crop")
    b.memes["sharing"] += 1
    world.facts["predicted_risk"] = pred["risk"]
    extra = ""
    if b.memes["sharing"] >= 6:
        extra = f" {b.pronoun().capitalize()} already knew pirate crews did better when everyone shared."
    world.say(
        f'{b.id} shook {b.pronoun("possessive")} head. "{a.id}, don\'t hog {plan.label}. '
        f'If the slop splashes on the path, a hog could smell it and rush right to {crop.the_bed}. '
        f'{adult.label_word.capitalize()} said we should work together and share the load."{extra}'
    )


def back_down(world: World, a: Entity, b: Entity, plan: Plan, theme: Theme) -> None:
    a.memes["bravery"] = 0.0
    a.memes["relief"] += 1
    b.memes["relief"] += 1
    world.say(
        f'"I wanted to be the fastest pirate," {a.id} admitted. But {b.id} was '
        f"{a.pronoun('possessive')} older sibling, so {a.id} listened, put one hand beside "
        f"{b.pronoun('possessive')} on the {plan.label}, and stopped trying to hog the job."
    )
    world.say(plan.team_text)
    for kid in (a, b):
        kid.memes["teamwork"] += 1
        kid.memes["sharing"] += 1


def defy(world: World, a: Entity, b: Entity, plan: Plan) -> None:
    a.memes["defiance"] += 1
    world.say(
        f'"I\'m the captain," {a.id} said, hugging the {plan.label} close. '
        f"{b.id} hurried after {a.pronoun('object')}, still asking to help."
    )


def spill_slop(world: World, hog: Entity, crop_ent: Entity, slop: SlopKind, crop: Crop, plan: Plan) -> None:
    if not plan.leakproof:
        world.get("path").meters["messy"] += 1
        world.get("slop").meters["spilled"] += 1
        world.say(
            f"But the {plan.label} was a poor ship for drippy slop. A wet stripe of peels and mash "
            f"slopped onto the path."
        )
    else:
        world.get("slop").meters["spilled"] += 1
        world.say(
            f"The load jolted anyway, and one slippery splash of slop plopped over the rim onto the path."
        )
    hog.meters["smelled_food"] += 1
    hog.meters["at_crop"] += 1
    propagate(world, narrate=False)
    crop_ent.meters["shaken"] += 1
    world.say(
        f"From the next plot came a snort. A round brown hog pushed through the half-open side gate, "
        f"sniffed the slop, and trotted straight toward {crop.the_bed}."
    )


def alarm(world: World, b: Entity, crop: Crop, adult: Entity) -> None:
    world.say(f'"The hog! {crop.The_bed}!" {b.id} cried.')
    world.say(f'"{adult.label_word.upper()}!"')


def rescue(world: World, adult: Entity, a: Entity, b: Entity, hog: Entity, crop_ent: Entity,
           plan: Plan, crop: Crop, theme: Theme) -> None:
    hog.meters["at_crop"] = 0.0
    crop_ent.meters["trampled"] = 0.0
    world.get("garden").meters["risk"] = 0.0
    for kid in (a, b):
        kid.memes["teamwork"] += 1
        kid.memes["sharing"] += 1
        kid.memes["relief"] += 1
    world.say(
        f"{adult.label_word.capitalize()} came running. Together the three of them {plan.rescue_text}, "
        f"making a neat trail to the compost bin and away from {crop.the_bed}."
    )
    world.say(
        f"The hog followed the smell, snuffling happily into the emptying compost bay while "
        f"{adult.pronoun()} swung the gate shut behind it."
    )
    world.say(
        f"Only a few leaves were bent, and soon the little garden looked safe again. "
        f"The pirate crew had saved the bed by sharing the work."
    )


def lesson(world: World, adult: Entity, a: Entity, b: Entity, plan: Plan) -> None:
    for kid in (a, b):
        kid.memes["love"] += 1
        kid.memes["lesson"] += 1
    world.say("For a moment, everyone listened to the hog grunt on the other side of the gate.")
    world.say(
        f'Then {adult.label_word.capitalize()} knelt beside them. "I am glad you called me," '
        f'{adult.pronoun()} said. "Big jobs in a garden go better when nobody hogs the tools. '
        f'You shared {plan.label}, worked as a team, and that kept the plants safe."'
    )
    world.say(f'"Next time we share first," whispered {a.id} and {b.id} together.')


def happy_ending(world: World, a: Entity, b: Entity, crop: Crop, theme: Theme) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
    world.say(
        f"After that, they watered {crop.the_bed} side by side, passing the can back and forth "
        f"like true shipmates."
    )
    world.say(
        f"Then the two pirates {theme.sendoff} -- muddy-kneed, busy-handed, and proud that a shared "
        f"job had made the garden bloom."
    )


def rescue_fail(world: World, adult: Entity, plan: Plan, crop: Crop) -> None:
    world.get("garden").meters["risk"] += 1
    world.get("crop").meters["trampled"] += 1
    world.say(
        f"{adult.label_word.capitalize()} ran in, but {plan.fail_text}. The hog ducked past the compost "
        f"path and burrowed into {crop.the_bed}."
    )
    world.say(
        f"Leaves flapped, soil flew, and the neat little row turned to garden slop under the hog's hooves."
    )


def sad_lesson(world: World, adult: Entity, a: Entity, b: Entity, crop: Crop) -> None:
    for kid in (a, b):
        kid.memes["sadness"] += 1
        kid.memes["lesson"] += 1
        kid.memes["love"] += 1
    world.say(
        f"{adult.label_word.capitalize()} gathered them close beside the broken bed. "
        f'"Plants can grow again," {adult.pronoun()} said softly, "but only if we slow down, share, '
        f'and do the job the careful way."'
    )
    world.say(
        f"{a.id} and {b.id} looked at the torn leaves and understood. After that day, neither of them "
        f"tried to hog the work in the garden again."
    )


def tell(theme: Theme, slop: SlopKind, crop: Crop, plan: Plan,
         instigator: str = "Tom", instigator_gender: str = "boy",
         cautioner: str = "Lily", cautioner_gender: str = "girl",
         trait: str = "kind", adult_type: str = "mother", delay: int = 0,
         instigator_age: int = 6, cautioner_age: int = 4,
         relation: str = "siblings", trust: int = 6) -> World:
    world = World()
    a = world.add(Entity(id=instigator, kind="character", type=instigator_gender,
                         role="instigator", age=instigator_age,
                         attrs={"relation": relation}))
    b = world.add(Entity(id=cautioner, kind="character", type=cautioner_gender,
                         role="cautioner", age=cautioner_age,
                         traits=[trait], attrs={"relation": relation}))
    adult = world.add(Entity(id="Gardener", kind="character", type=adult_type,
                             role="adult", label="the gardener"))
    world.add(Entity(id="garden", type="garden", label="the community garden"))
    world.add(Entity(id="path", type="path", label="the path"))
    world.add(Entity(id="slop", type="slop", label=slop.label))
    crop_ent = world.add(Entity(id="crop", type="crop", label=crop.label, tasty_to_hog=crop.tasty))
    hog = world.add(Entity(id="hog", type="hog", label="the hog"))
    tool = world.add(Entity(id="tool", type="tool", label=plan.label,
                            leakproof=plan.leakproof, shareable=plan.shareable))

    a.memes["bravery"] = BRAVERY_INIT
    b.memes["trust"] = float(trust)
    b.memes["sharing"] = initial_sharing(trait)

    play_setup(world, a, b, theme)
    introduce_job(world, b, slop, crop)

    world.para()
    tempt(world, a, plan)
    warn(world, b, a, slop, crop, adult, plan)

    averted = would_share_first(relation, instigator_age, cautioner_age, trait)
    if averted:
        back_down(world, a, b, plan, theme)
        world.para()
        lesson(world, adult, a, b, plan)
        world.para()
        happy_ending(world, a, b, crop, theme)
        severity, contained = 0, True
        hog_enters = False
    else:
        defy(world, a, b, plan)
        world.para()
        spill_slop(world, hog, crop_ent, slop, crop, plan)
        hog_enters = True
        alarm(world, b, crop, adult)
        severity = risk_severity(crop, delay)
        contained = is_saved(plan, crop, delay)
        world.para()
        if contained:
            rescue(world, adult, a, b, hog, crop_ent, plan, crop, theme)
            lesson(world, adult, a, b, plan)
            world.para()
            happy_ending(world, a, b, crop, theme)
        else:
            rescue_fail(world, adult, plan, crop)
            sad_lesson(world, adult, a, b, crop)

    outcome = "averted" if averted else ("saved" if contained else "trampled")
    world.facts.update(
        instigator=a,
        cautioner=b,
        adult=adult,
        theme=theme,
        slop=slop,
        crop_cfg=crop,
        crop=crop_ent,
        hog=hog,
        plan=plan,
        tool=tool,
        outcome=outcome,
        hog_enters=hog_enters,
        severity=severity,
        delay=delay,
    )
    return world


THEMES = {
    "pirates": Theme(
        "pirates",
        "a little green harbor",
        "A wheelbarrow became a treasure cart, bamboo poles were masts, and the stepping stones "
        "were tiny islands between the beds.",
        "Captain",
        "Matey",
        "Compost Cove",
        "set off down the bean paths like a brave little pirate crew",
    ),
    "buccaneers": Theme(
        "buccaneers",
        "a secret pirate island",
        "The raised beds were island walls, the hose was a coiled sea-snake, and an old crate "
        "became their dock for garden treasure.",
        "Captain",
        "Scout",
        "the compost fort",
        "marched between the beds like laughing buccaneers",
    ),
    "sailors": Theme(
        "sailors",
        "a windy harbor",
        "The watering can was a silver bell, the pea trellis was a ship mast, and a red wagon "
        "waited like a little boat by the gate.",
        "Skipper",
        "Lookout",
        "the green dock",
        "sailed their make-believe ship past the herbs and sunflowers",
    ),
}

SLOPS = {
    "veggie_slop": SlopKind(
        "veggie_slop",
        "vegetable slop",
        "a bucket of vegetable slop made from peels and bean ends",
        "like onion skins and damp earth",
        tags={"food", "compost", "slop"},
    ),
    "melon_slop": SlopKind(
        "melon_slop",
        "melon slop",
        "a pail of melon slop with rinds and soft pink bits",
        "sweet and drippy",
        tags={"food", "compost", "slop"},
    ),
    "soup_slop": SlopKind(
        "soup_slop",
        "soupy slop",
        "a tub of soupy slop from old carrot tops and potato peels",
        "warm and messy",
        tags={"food", "compost", "slop"},
    ),
}

CROPS = {
    "lettuce": Crop("lettuce", "lettuce", "lettuce bed", True, 3, tags={"lettuce", "garden_food"}),
    "carrots": Crop("carrots", "carrots", "carrot row", True, 2, tags={"carrots", "garden_food"}),
    "pumpkins": Crop("pumpkins", "pumpkins", "pumpkin patch", True, 2, tags={"pumpkins", "garden_food"}),
    "marigolds": Crop("marigolds", "marigolds", "marigold border", False, 1, tags={"flowers"}),
}

PLANS = {
    "wheelbarrow": Plan(
        "wheelbarrow",
        "wheelbarrow",
        "the big blue wheelbarrow",
        3,
        4,
        True,
        True,
        "So they gripped the wheelbarrow together, one on each side, and rolled the slop toward the compost bay without a splash.",
        "rolled the wheelbarrow together while shaking a tidy trail of slop into the compost trench",
        "the wheelbarrow bumped too hard, and the hog was already too deep in the bed to turn",
        "used the wheelbarrow together to lead the hog away to the compost bay",
        tags={"wheelbarrow", "sharing", "teamwork"},
    ),
    "lidded_bucket": Plan(
        "lidded_bucket",
        "lidded bucket",
        "the lidded bucket with two side handles",
        3,
        3,
        True,
        True,
        "So they took one handle each, counted to three, and carried the lidded bucket together like careful deckhands.",
        "carried the lidded bucket together and tapped little spoonfuls of slop toward the compost pen",
        "the bucket trail was too slow, and the hog had already rooted through too many plants",
        "carried the lidded bucket together and lured the hog to the compost pen",
        tags={"bucket", "sharing", "teamwork"},
    ),
    "paper_tray": Plan(
        "paper_tray",
        "paper tray",
        "a floppy paper tray",
        1,
        1,
        False,
        False,
        "They tried to steady the paper tray, but it sagged in the middle.",
        "waved the paper tray and called to the hog",
        "the paper tray tore, spilling slop everywhere before anyone could guide the hog",
        "tried to use a paper tray, but it was too flimsy to help",
        tags={"tray"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Anna", "Maya", "Nora", "Rose"]
BOY_NAMES = ["Tom", "Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Noah", "Eli", "Theo"]
TRAITS = ["kind", "careful", "patient", "sensible", "brave", "curious"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for theme in THEMES:
        for sid, slop in SLOPS.items():
            for cid, crop in CROPS.items():
                if crop_at_risk(slop, crop):
                    combos.append((theme, sid, cid))
    return combos


@dataclass
class StoryParams:
    theme: str
    slop: str
    crop: str
    plan: str
    instigator: str
    instigator_gender: str
    cautioner: str
    cautioner_gender: str
    adult: str
    trait: str
    delay: int = 0
    instigator_age: int = 6
    cautioner_age: int = 4
    relation: str = "siblings"
    trust: int = 6
    seed: Optional[int] = None


KNOWLEDGE = {
    "slop": [("What is slop for compost?",
              "Compost slop is a wet mix of old fruit and vegetable scraps. It can turn into good soil food when it goes in the right bin.")],
    "hog": [("What is a hog?",
             "A hog is a big pig. It has a strong nose and loves to sniff out food.")],
    "compost": [("What is compost?",
                 "Compost is made from old plant scraps that rot down into rich soil. Gardeners use it to help new plants grow.")],
    "wheelbarrow": [("What is a wheelbarrow?",
                     "A wheelbarrow is a little cart with one wheel in front. It helps people move heavy or messy things in a garden.")],
    "bucket": [("Why can a lidded bucket be useful?",
                "A lidded bucket keeps drippy things from splashing out so easily. That makes messy jobs safer and cleaner.")],
    "sharing": [("Why is sharing helpful in a big job?",
                 "Sharing lets two people use the same tools and help each other. A hard job can feel lighter and go more safely when everyone helps.")],
    "teamwork": [("What is teamwork?",
                  "Teamwork means people help each other to do one job together. Each person does a part, and the whole job goes better.")],
    "garden_food": [("Why should you protect vegetables in a garden?",
                     "Vegetables take time to grow. If an animal stomps or eats them, the gardeners lose the food they worked hard to raise.")],
    "flowers": [("What do flowers do in a garden?",
                 "Flowers make a garden bright, and many flowers help bees and other pollinators. They are important even when they are not food.")],
}
KNOWLEDGE_ORDER = ["slop", "hog", "compost", "wheelbarrow", "bucket", "sharing",
                   "teamwork", "garden_food", "flowers"]


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
    a, b, slop, crop, plan, theme = f["instigator"], f["cautioner"], f["slop"], f["crop_cfg"], f["plan"], f["theme"]
    outcome = f["outcome"]
    base = (
        f'Write a pirate-flavored story for a 3-to-5-year-old set in a community garden. '
        f'Include the words "slop" and "hog", and make teamwork and sharing matter.'
    )
    if outcome == "averted":
        return [
            base,
            f"Tell a gentle story where {a.id} wants to hog the {plan.label}, but {b.id} talks {a.pronoun('object')} into sharing and the children save {crop.the_bed} before the hog can get there.",
            f"Write a simple community-garden pirate tale where two children carry {slop.label} together, share the tool, and learn that crews do better when nobody hogs the job.",
        ]
    if outcome == "trampled":
        return [
            base,
            f"Tell a cautionary story where {a.id} tries to do the garden job alone, slop spills, and a hog tramples {crop.the_bed} before the grown-up can fix it.",
            f"Write a story with a sad but child-safe lesson: sharing would have helped, but the pirate crew learned too late after the hog made a mess in the garden.",
        ]
    return [
        base,
        f"Tell a story where {a.id} first tries to hog the {plan.label}, but then the children and a gardener work together to guide a hog away from {crop.the_bed}.",
        f"Write a child-facing pirate tale in a community garden where sharing a {plan.label} turns a messy slop problem into a teamwork success.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a, b, adult = f["instigator"], f["cautioner"], f["adult"]
    slop, crop, plan = f["slop"], f["crop_cfg"], f["plan"]
    pair = pair_noun(a, b, a.attrs.get("relation", "friends"))
    pw = adult.label_word
    qa: list[tuple[str, str]] = [
        ("Who is the story about?",
         f"It is about {pair}, {a.id} and {b.id}, pretending to be pirates in a community garden. The gardener helps them when the garden job turns tricky."),
        ("What job did the children have?",
         f"They needed to carry {slop.phrase} to the compost area. The job mattered because leaving food-smelling slop near the beds could attract trouble."),
        (f"Why did {b.id} tell {a.id} not to hog the {plan.label}?",
         f"{b.id} warned that if the slop spilled, a hog might smell it and rush toward {crop.the_bed}. Sharing the tool would make the messy job steadier and safer."),
    ]
    if f["hog_enters"]:
        qa.append((
            "What brought the hog into the garden trouble?",
            f"The hog smelled spilled slop on the path and followed the food smell toward {crop.the_bed}. The slop, not the pirate game, is what pulled the animal into the problem."
        ))
    if f["outcome"] == "averted":
        qa.append((
            f"How was the problem stopped before it got worse?",
            f"{a.id} listened to {b.id} and stopped trying to hog the tool. Because they shared and worked together right away, the slop reached the compost neatly and the hog never got a chance to charge the bed."
        ))
        qa.append((
            "How did the story end?",
            f"It ended with the children watering the bed side by side and passing the can back and forth. That ending shows they had changed from grabbing at the job to sharing it."
        ))
    elif f["outcome"] == "saved":
        qa.append((
            f"How did the gardener and children save {crop.the_bed}?",
            f"They {plan.qa_text}. Working together changed the hog's path and gave the gardener time to shut the gate."
        ))
        qa.append((
            "What lesson did the children learn?",
            f"They learned that big garden jobs go better when nobody hogs the tools. Sharing helped them steady the mess and fix the danger together."
        ))
    else:
        qa.append((
            f"Could they save {crop.the_bed} in time?",
            f"No. The plan was too weak or too late, and the hog rooted into the bed before it could be turned away. The children stayed safe, but the plants were badly trampled."
        ))
        qa.append((
            "What did the ending teach?",
            f"The ending taught that rushing alone can make a bigger mess. If they had slowed down and shared the work from the start, the garden would have had a much better chance."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["slop"].tags) | {"hog", "sharing", "teamwork", "compost"}
    tags |= set(f["crop_cfg"].tags)
    if f["plan"].id == "wheelbarrow":
        tags.add("wheelbarrow")
    if f["plan"].id == "lidded_bucket":
        tags.add("bucket")
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
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        flags = [n for n, on in (("tasty_to_hog", e.tasty_to_hog),
                                 ("leakproof", e.leakproof),
                                 ("shareable", e.shareable)) if on]
        if flags:
            bits.append(f"flags={flags}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.age:
            bits.append(f"age={e.age}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("pirates", "veggie_slop", "lettuce", "wheelbarrow",
                "Tom", "boy", "Lily", "girl", "mother", "careful", 0,
                instigator_age=5, cautioner_age=7, relation="siblings", trust=5),
    StoryParams("buccaneers", "melon_slop", "carrots", "lidded_bucket",
                "Max", "boy", "Mia", "girl", "father", "kind", 0,
                instigator_age=6, cautioner_age=5, relation="friends", trust=6),
    StoryParams("pirates", "soup_slop", "lettuce", "lidded_bucket",
                "Sam", "boy", "Zoe", "girl", "mother", "brave", 1,
                instigator_age=7, cautioner_age=5, relation="siblings", trust=4),
    StoryParams("sailors", "veggie_slop", "pumpkins", "wheelbarrow",
                "Eli", "boy", "Nora", "girl", "father", "curious", 2,
                instigator_age=7, cautioner_age=4, relation="siblings", trust=3),
]


def explain_rejection(slop: SlopKind, crop: Crop) -> str:
    if not crop.tasty:
        return (
            f"(No story: {crop.the_bed} would not tempt a hungry hog in this world, so "
            f"there is no strong garden danger to solve. Pick a food crop like lettuce, carrots, or pumpkins.)"
        )
    if "food" not in slop.tags:
        return (
            f"(No story: {slop.label} would not smell like food to the hog, so it would not drive the central trouble.)"
        )
    return "(No story: this combination does not create a believable hog problem.)"


def explain_plan(plan_id: str) -> str:
    p = PLANS[plan_id]
    better = " / ".join(sorted(x.id for x in sensible_plans()))
    return (
        f"(Refusing plan '{plan_id}': it scores too low on common sense "
        f"(sense={p.sense} < {SENSE_MIN}). A drippy garden job needs a steadier shared tool. Try: {better}.)"
    )


def outcome_of(params: StoryParams) -> str:
    if would_share_first(params.relation, params.instigator_age, params.cautioner_age, params.trait):
        return "averted"
    return "saved" if is_saved(PLANS[params.plan], CROPS[params.crop], params.delay) else "trampled"


ASP_RULES = r"""
hazard(S, C) :- slop(S), crop(C), food_smell(S), tasty(C).
sensible(P)  :- plan(P), sense(P, S), sense_min(M), S >= M.
valid(T, S, C) :- theme(T), hazard(S, C).

sharing_now(T) :- trait(T), sharing_trait(T).
init_share(5)  :- trait(T), sharing_now(T).
init_share(3)  :- trait(T), not sharing_now(T).
cautioner_older :- relation(siblings), instigator_age(IA), cautioner_age(CA), CA > IA.
bonus(4) :- cautioner_older.
bonus(0) :- not cautioner_older.
authority(C + 1 + B) :- init_share(C), bonus(B).
averted :- cautioner_older, authority(A), bravery_init(BR), A > BR.

severity(F + D) :- chosen_crop(C), fragility(C, F), delay(D).
resp_power(Pw) :- chosen_plan(P), power(P, Pw).
saved :- resp_power(Pw), severity(V), Pw >= V.

outcome(averted) :- averted.
outcome(saved) :- not averted, saved.
outcome(trampled) :- not averted, not saved.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for tid in THEMES:
        lines.append(asp.fact("theme", tid))
    for sid, slop in SLOPS.items():
        lines.append(asp.fact("slop", sid))
        if "food" in slop.tags:
            lines.append(asp.fact("food_smell", sid))
    for cid, crop in CROPS.items():
        lines.append(asp.fact("crop", cid))
        if crop.tasty:
            lines.append(asp.fact("tasty", cid))
        lines.append(asp.fact("fragility", cid, crop.fragility))
    for pid, plan in PLANS.items():
        lines.append(asp.fact("plan", pid))
        lines.append(asp.fact("sense", pid, plan.sense))
        lines.append(asp.fact("power", pid, plan.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    lines.append(asp.fact("bravery_init", int(BRAVERY_INIT)))
    for tr in sorted(SHARING_TRAITS):
        lines.append(asp.fact("sharing_trait", tr))
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
    return sorted(p for (p,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp
    scenario = "\n".join([
        asp.fact("chosen_crop", params.crop),
        asp.fact("chosen_plan", params.plan),
        asp.fact("delay", params.delay),
        asp.fact("relation", params.relation),
        asp.fact("instigator_age", params.instigator_age),
        asp.fact("cautioner_age", params.cautioner_age),
        asp.fact("trait", params.trait),
    ])
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def asp_verify() -> int:
    rc = 0
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    clingo_sense, python_sense = set(asp_sensible()), {p.id for p in sensible_plans()}
    if clingo_sense == python_sense:
        print(f"OK: sensible plans match ({sorted(clingo_sense)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible plans: clingo={sorted(clingo_sense)} python={sorted(python_sense)}")

    cases = list(CURATED)
    parser = build_parser()
    for s in range(100):
        try:
            cases.append(resolve_params(parser.parse_args([]), random.Random(s)))
        except StoryError:
            continue
    bad = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        emit(sample, trace=False, qa=False, header="### smoke test")
        print("OK: smoke generation succeeded.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Pirate-flavored community-garden storyworld about slop, a hog, teamwork, and sharing."
    )
    ap.add_argument("--theme", choices=THEMES)
    ap.add_argument("--slop", choices=SLOPS)
    ap.add_argument("--crop", choices=CROPS)
    ap.add_argument("--plan", choices=PLANS)
    ap.add_argument("--adult", choices=["mother", "father"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2],
                    help="how long the hog gets to nose toward the crop before the rescue settles it")
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
    if args.crop and args.slop:
        slop, crop = SLOPS[args.slop], CROPS[args.crop]
        if not crop_at_risk(slop, crop):
            raise StoryError(explain_rejection(slop, crop))
    if args.crop and not CROPS[args.crop].tasty:
        slop = SLOPS[args.slop] if args.slop else next(iter(SLOPS.values()))
        raise StoryError(explain_rejection(slop, CROPS[args.crop]))
    if args.plan and PLANS[args.plan].sense < SENSE_MIN:
        raise StoryError(explain_plan(args.plan))

    combos = [c for c in valid_combos()
              if (args.theme is None or c[0] == args.theme)
              and (args.slop is None or c[1] == args.slop)
              and (args.crop is None or c[2] == args.crop)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    theme, slop, crop = rng.choice(sorted(combos))
    plan = args.plan or rng.choice(sorted(p.id for p in sensible_plans()))
    instigator, ig = _pick_kid(rng)
    cautioner, cg = _pick_kid(rng, avoid=instigator)
    adult = args.adult or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    relation = rng.choice(["siblings", "friends"])
    instigator_age, cautioner_age = rng.sample([3, 4, 5, 6, 7], 2)
    trust = rng.randint(0, 10)
    return StoryParams(theme, slop, crop, plan, instigator, ig, cautioner, cg, adult, trait,
                       delay, instigator_age=instigator_age, cautioner_age=cautioner_age,
                       relation=relation, trust=trust)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        THEMES[params.theme],
        SLOPS[params.slop],
        CROPS[params.crop],
        PLANS[params.plan],
        params.instigator,
        params.instigator_gender,
        params.cautioner,
        params.cautioner_gender,
        params.trait,
        params.adult,
        params.delay,
        params.instigator_age,
        params.cautioner_age,
        params.relation,
        params.trust,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
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
        print(asp_program("", "#show valid/3.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible plans: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (theme, slop, crop) combos:\n")
        for theme, slop, crop in combos:
            print(f"  {theme:11} {slop:12} {crop}")
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
            header = f"### {p.instigator} & {p.cautioner}: {p.slop} near {p.crop} ({p.theme}, {p.plan}, {outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
