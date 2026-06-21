#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/tipsy_happy_ending_slice_of_life.py
==============================================================

A small storyworld about a child noticing a tipsy houseplant and helping save it
before it falls. The stories stay close to slice-of-life: a quiet room, a small
household problem, a sensible fix, and a warm happy ending.

The world model tracks physical state (tilt, spill, support) and emotional state
(worry, care, relief). Different plants, places, bumps, and repairs create
slightly different but still plausible stories.

Run it
------
    python storyworlds/worlds/gpt-5.4/tipsy_happy_ending_slice_of_life.py
    python storyworlds/worlds/gpt-5.4/tipsy_happy_ending_slice_of_life.py --plant sunflower --fix stake
    python storyworlds/worlds/gpt-5.4/tipsy_happy_ending_slice_of_life.py --place stool --fix pebbles
    python storyworlds/worlds/gpt-5.4/tipsy_happy_ending_slice_of_life.py --all
    python storyworlds/worlds/gpt-5.4/tipsy_happy_ending_slice_of_life.py --qa --json
    python storyworlds/worlds/gpt-5.4/tipsy_happy_ending_slice_of_life.py --verify
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
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
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
            "mother": "mom",
            "father": "dad",
            "grandmother": "grandma",
            "grandfather": "grandpa",
        }.get(self.type, self.type)


@dataclass
class Place:
    id: str
    label: str
    phrase: str
    room_text: str
    base_stability: int
    can_repot: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Plant:
    id: str
    label: str
    phrase: str
    height: int
    stem_soft: bool
    leaf_text: str
    ending_image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Bump:
    id: str
    label: str
    phrase: str
    source_text: str
    force: int
    tags: set[str] = field(default_factory=set)


@dataclass
class Fix:
    id: str
    label: str
    phrase: str
    action_text: str
    power: int
    needs_soft_stem: bool = False
    requires_repot: bool = False
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
        new = World()
        new.entities = copy.deepcopy(self.entities)
        new.fired = set(self.fired)
        new.paragraphs = [[]]
        new.facts = copy.deepcopy(self.facts)
        return new


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_worry(world: World) -> list[str]:
    plant = world.get("plant")
    child = world.get("child")
    out: list[str] = []
    if plant.meters["tilt"] >= THRESHOLD:
        sig = ("worry",)
        if sig not in world.fired:
            world.fired.add(sig)
            child.memes["worry"] += 1
            out.append("__worry__")
    if plant.meters["tilt"] >= 2.0:
        sig = ("spill",)
        if sig not in world.fired:
            world.fired.add(sig)
            plant.meters["soil_spill"] += 1
            out.append("__spill__")
    return out


def _r_fall(world: World) -> list[str]:
    plant = world.get("plant")
    if plant.meters["tilt"] > plant.meters["support"]:
        sig = ("at_risk",)
        if sig not in world.fired:
            world.fired.add(sig)
            plant.meters["at_risk"] += 1
    if plant.meters["at_risk"] >= THRESHOLD and plant.meters["tilt"] >= 3.0:
        sig = ("would_fall",)
        if sig not in world.fired:
            world.fired.add(sig)
            plant.meters["would_fall"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="worry", tag="emotional", apply=_r_worry),
    Rule(name="fall", tag="physical", apply=_r_fall),
]


def propagate(world: World) -> None:
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            before = len(world.fired)
            rule.apply(world)
            if len(world.fired) != before:
                changed = True


def predicted_tilt(place: Place, plant: Plant, bump: Bump) -> int:
    return max(1, plant.height + bump.force - place.base_stability)


def fix_fits(place: Place, plant: Plant, fix: Fix) -> bool:
    if fix.needs_soft_stem and not plant.stem_soft:
        return False
    if fix.requires_repot and not place.can_repot:
        return False
    return True


def can_stabilize(place: Place, plant: Plant, bump: Bump, fix: Fix) -> bool:
    if not fix_fits(place, plant, fix):
        return False
    return fix.power >= predicted_tilt(place, plant, bump)


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for place_id, place in PLACES.items():
        for plant_id, plant in PLANTS.items():
            for bump_id, bump in BUMPS.items():
                for fix_id, fix in FIXES.items():
                    if can_stabilize(place, plant, bump, fix):
                        combos.append((place_id, plant_id, bump_id, fix_id))
    return combos


def explain_rejection(place: Place, plant: Plant, bump: Bump, fix: Fix) -> str:
    if not fix_fits(place, plant, fix):
        if fix.needs_soft_stem and not plant.stem_soft:
            return (
                f"(No story: {fix.label} helps soft, bendy stems, but {plant.phrase} is too sturdy for that fix. "
                f"Try pebbles or a new pot instead.)"
            )
        if fix.requires_repot and not place.can_repot:
            return (
                f"(No story: {fix.label} needs enough space to repot the plant, and {place.label} is too cramped for that step. "
                f"Try a fix that can happen right there.)"
            )
    need = predicted_tilt(place, plant, bump)
    return (
        f"(No story: after {bump.phrase} at {place.label}, {plant.phrase} would lean too far. "
        f"{fix.label.capitalize()} is too weak for that much wobble; it handles {fix.power}, but this plant needs {need}.)"
    )


def predict_fall(place: Place, plant: Plant, bump: Bump) -> dict:
    world = World()
    world.add(Entity(id="child", kind="character", type="girl", role="child"))
    world.add(Entity(id="plant", type="plant", label=plant.label))
    pot = world.add(Entity(id="pot", type="pot", label="pot"))
    world.facts["predicted_tilt"] = predicted_tilt(place, plant, bump)
    pot.meters["tilt"] = float(world.facts["predicted_tilt"])
    world.get("plant").meters["tilt"] = float(world.facts["predicted_tilt"])
    propagate(world)
    return {
        "tilt": world.get("plant").meters["tilt"],
        "spill": world.get("plant").meters["soil_spill"] >= THRESHOLD,
        "would_fall": world.get("plant").meters["would_fall"] >= THRESHOLD,
    }


def introduce(world: World, child: Entity, helper: Entity, place: Place, plant: Plant) -> None:
    child.memes["care"] += 1
    world.say(
        f"After breakfast, {child.id} stopped by {place.phrase} to check {plant.phrase}. "
        f"{plant.leaf_text}, and the room felt ordinary and soft in the morning light."
    )
    world.say(
        f"{helper.label_word.capitalize()} was nearby, folding a towel and humming, while {child.id} gave the pot a careful little touch."
    )


def bump_plant(world: World, child: Entity, place: Place, plant: Plant, bump: Bump) -> None:
    tilt = predicted_tilt(place, plant, bump)
    world.get("plant").meters["tilt"] = float(tilt)
    world.get("pot").meters["tilt"] = float(tilt)
    propagate(world)
    world.say(
        f"Then {bump.source_text}. The pot gave a small slide, and suddenly the plant looked tipsy on {place.phrase}."
    )
    if world.get("plant").meters["soil_spill"] >= THRESHOLD:
        world.say("A little crescent of dark soil slipped onto the surface below.")
    else:
        world.say("It did not fall, but it leaned enough to make the whole corner look wrong.")


def notice_and_warn(world: World, child: Entity, helper: Entity, place: Place, plant: Plant, bump: Bump) -> None:
    pred = predict_fall(place, plant, bump)
    world.facts["predicted_fall"] = pred["would_fall"]
    child.memes["care"] += 1
    child.memes["worry"] += 1
    if pred["would_fall"]:
        world.say(
            f'"{helper.label_word.capitalize()}, look," {child.id} said. "{plant.label.capitalize()} might tumble if we leave it like that."'
        )
    else:
        world.say(
            f'"{helper.label_word.capitalize()}, look," {child.id} said. "{plant.label.capitalize()} is leaning, and I do not want it to get hurt."'
        )
    world.say(
        f"{helper.label_word.capitalize()} came over at once and bent close to the pot instead of rushing past it."
    )


def repair(world: World, child: Entity, helper: Entity, plant: Plant, fix: Fix) -> None:
    world.get("plant").meters["support"] = float(fix.power)
    world.get("pot").meters["support"] = float(fix.power)
    if world.get("plant").meters["support"] >= world.get("plant").meters["tilt"]:
        world.get("plant").meters["tilt"] = 0.0
        world.get("pot").meters["tilt"] = 0.0
        world.get("plant").meters["steady"] += 1
    child.memes["relief"] += 1
    helper.memes["pride"] += 1
    world.say(
        f"Together they {fix.action_text}."
    )
    if world.get("plant").meters["soil_spill"] >= THRESHOLD:
        world.say("Then they brushed the spilled soil back in with quiet fingers.")
    world.say(
        f"Little by little, the wobble left the pot until it stood straight again."
    )


def ending(world: World, child: Entity, helper: Entity, plant: Plant, place: Place, fix: Fix) -> None:
    child.memes["joy"] += 1
    child.memes["relief"] += 1
    world.say(
        f"{child.id} stepped back and smiled. {helper.label_word.capitalize()} said the plant looked much happier now, and {child.id} thought so too."
    )
    world.say(
        f"Soon {plant.ending_image} at {place.phrase}, steady and safe. The morning went on in its gentle way, only brighter because they had cared in time."
    )


def tell(
    place: Place,
    plant_cfg: Plant,
    bump: Bump,
    fix: Fix,
    child_name: str,
    child_type: str,
    helper_type: str,
    trait: str,
) -> World:
    world = World()
    child = world.add(
        Entity(
            id=child_name,
            kind="character",
            type=child_type,
            label=child_name,
            role="child",
            attrs={"trait": trait},
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
    plant = world.add(
        Entity(
            id="plant",
            type="plant",
            label=plant_cfg.label,
            phrase=plant_cfg.phrase,
            tags=set(plant_cfg.tags),
        )
    )
    world.add(Entity(id="pot", type="pot", label="pot"))

    introduce(world, child, helper, place, plant_cfg)
    world.para()
    bump_plant(world, child, place, plant_cfg, bump)
    notice_and_warn(world, child, helper, place, plant_cfg, bump)
    world.para()
    repair(world, child, helper, plant_cfg, fix)
    ending(world, child, helper, plant_cfg, place, fix)

    world.facts.update(
        child=child,
        helper=helper,
        place=place,
        plant_cfg=plant_cfg,
        bump=bump,
        fix=fix,
        tilt=predicted_tilt(place, plant_cfg, bump),
        spilled=world.get("plant").meters["soil_spill"] >= THRESHOLD,
        saved=world.get("plant").meters["steady"] >= THRESHOLD,
    )
    return world


PLACES = {
    "windowsill": Place(
        id="windowsill",
        label="the windowsill",
        phrase="the sunny windowsill",
        room_text="the kitchen window",
        base_stability=1,
        can_repot=True,
        tags={"home", "window"},
    ),
    "desk": Place(
        id="desk",
        label="the desk",
        phrase="the little desk by the lamp",
        room_text="the bedroom desk",
        base_stability=2,
        can_repot=True,
        tags={"home", "desk"},
    ),
    "stool": Place(
        id="stool",
        label="the stool",
        phrase="the narrow stool by the back door",
        room_text="the back door corner",
        base_stability=0,
        can_repot=False,
        tags={"home", "stool"},
    ),
}

PLANTS = {
    "basil": Plant(
        id="basil",
        label="the basil",
        phrase="a pot of basil",
        height=1,
        stem_soft=True,
        leaf_text="Its leaves smelled fresh and green",
        ending_image="the basil sat straight with its leaves lifted toward the window",
        tags={"plant", "herb"},
    ),
    "bean": Plant(
        id="bean",
        label="the bean plant",
        phrase="a bean plant in a striped pot",
        height=2,
        stem_soft=True,
        leaf_text="Its thin stem curled toward the light",
        ending_image="the bean plant rested upright, its thin stem no longer wavering",
        tags={"plant", "sprout"},
    ),
    "sunflower": Plant(
        id="sunflower",
        label="the sunflower",
        phrase="a young sunflower in a yellow pot",
        height=3,
        stem_soft=False,
        leaf_text="Its round leaves made a bright green circle under the bud",
        ending_image="the sunflower stood proudly, its small head turned to the day",
        tags={"plant", "flower"},
    ),
}

BUMPS = {
    "cat_tail": Bump(
        id="cat_tail",
        label="the cat's tail",
        phrase="the cat's tail whisking by",
        source_text="the family cat jumped onto the chair and flicked its tail against the pot",
        force=2,
        tags={"cat"},
    ),
    "curtain": Bump(
        id="curtain",
        label="the curtain",
        phrase="the curtain brushing past",
        source_text="a breeze pushed the curtain across the pot with a soft swish",
        force=1,
        tags={"breeze"},
    ),
    "backpack": Bump(
        id="backpack",
        label="the backpack",
        phrase="a backpack brushing the shelf",
        source_text=f"{'{child}'}",
        force=2,
        tags={"school"},
    ),
}

FIXES = {
    "pebbles": Fix(
        id="pebbles",
        label="pebbles around the base",
        phrase="small pebbles",
        action_text="tucked a few pebbles around the base of the stem and turned the pot to its strongest side",
        power=2,
        needs_soft_stem=False,
        requires_repot=False,
        tags={"plant_care", "pebbles"},
    ),
    "stake": Fix(
        id="stake",
        label="a little plant stake",
        phrase="a little plant stake",
        action_text="slid in a little plant stake and tied the stem with a soft loop of string",
        power=3,
        needs_soft_stem=True,
        requires_repot=False,
        tags={"plant_care", "stake"},
    ),
    "new_pot": Fix(
        id="new_pot",
        label="a wider pot",
        phrase="a wider pot",
        action_text="moved the plant into a wider pot with fresh soil pressed snugly around it",
        power=4,
        needs_soft_stem=False,
        requires_repot=True,
        tags={"plant_care", "repot"},
    ),
}


GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Nora", "Rose"]
BOY_NAMES = ["Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Eli", "Theo"]
TRAITS = ["careful", "patient", "gentle", "observant", "helpful"]


@dataclass
class StoryParams:
    place: str
    plant: str
    bump: str
    fix: str
    child_name: str
    child_gender: str
    helper: str
    trait: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        place="windowsill",
        plant="basil",
        bump="curtain",
        fix="pebbles",
        child_name="Lily",
        child_gender="girl",
        helper="mother",
        trait="careful",
    ),
    StoryParams(
        place="desk",
        plant="bean",
        bump="cat_tail",
        fix="stake",
        child_name="Ben",
        child_gender="boy",
        helper="father",
        trait="patient",
    ),
    StoryParams(
        place="windowsill",
        plant="sunflower",
        bump="backpack",
        fix="new_pot",
        child_name="Mia",
        child_gender="girl",
        helper="grandmother",
        trait="gentle",
    ),
    StoryParams(
        place="stool",
        plant="basil",
        bump="curtain",
        fix="pebbles",
        child_name="Leo",
        child_gender="boy",
        helper="mother",
        trait="observant",
    ),
]


KNOWLEDGE = {
    "plant": [
        (
            "Why do houseplants need steady pots?",
            "A steady pot keeps a plant's roots safe and helps the stem stay upright. If the pot leans too far, the plant can fall and get damaged."
        )
    ],
    "herb": [
        (
            "What is basil?",
            "Basil is a soft green herb. People often grow it in small pots because its leaves smell nice and can be used in food."
        )
    ],
    "flower": [
        (
            "Why might a young sunflower need extra support?",
            "A young sunflower can grow tall before its stem gets strong. Extra support helps it stay upright while it is still growing."
        )
    ],
    "sprout": [
        (
            "Why are bean plants easy to bend?",
            "Bean plants often have thin, tender stems. That makes them lively growers, but it also means they can lean or bend easily."
        )
    ],
    "cat": [
        (
            "Why can a cat knock things over by accident?",
            "Cats move quickly and their tails sweep behind them. A light bump from a tail can shift something small or wobbly."
        )
    ],
    "breeze": [
        (
            "How can a breeze move things inside a house?",
            "When a window or door is open, moving air can push light cloth or paper. That is why curtains sometimes sway across a room."
        )
    ],
    "plant_care": [
        (
            "What does it mean to take care of a plant?",
            "Taking care of a plant means noticing what it needs, like light, water, and a safe place to grow. Small careful actions can keep it healthy."
        )
    ],
    "stake": [
        (
            "What does a plant stake do?",
            "A plant stake is a small support put beside a stem. It helps a bendy plant stand up while it grows stronger."
        )
    ],
    "repot": [
        (
            "Why put a plant in a wider pot?",
            "A wider pot gives the roots more room and makes the bottom steadier. That can help a tall or top-heavy plant stop wobbling."
        )
    ],
    "pebbles": [
        (
            "Why might pebbles help a leaning plant?",
            "Pebbles can help hold the soil in place and give a small stem a firmer base. They are a gentle fix for a light wobble, not for a very big lean."
        )
    ],
}
KNOWLEDGE_ORDER = ["plant", "herb", "flower", "sprout", "cat", "breeze", "plant_care", "stake", "repot", "pebbles"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    plant = f["plant_cfg"]
    place = f["place"]
    fix = f["fix"]
    return [
        f'Write a gentle slice-of-life story for a 3-to-5-year-old that includes the word "tipsy" and ends happily.',
        f"Tell a home story where {child.id} notices that {plant.phrase} has gone tipsy on {place.label}, asks a grown-up for help, and together they make it safe again.",
        f"Write a small everyday story with a warm ending, where a child saves a leaning plant using {fix.label} before anything worse happens.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    plant = f["plant_cfg"]
    place = f["place"]
    bump = f["bump"]
    fix = f["fix"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, a child caring for {plant.phrase}, and {child.pronoun('possessive')} {helper.label_word}, who helps fix the problem."
        ),
        (
            f"Why did the plant look tipsy?",
            f"It looked tipsy after {bump.phrase}. That bump made the pot lean on {place.label}, so {child.id} worried it might fall."
        ),
        (
            f"What did {child.id} do when the plant started leaning?",
            f"{child.id} noticed the danger and called {helper.label_word} over right away. That mattered because they fixed the wobble before the plant could tumble."
        ),
    ]
    if f["spilled"]:
        qa.append(
            (
                "Did anything spill?",
                "Yes. A little soil slipped out when the pot leaned. They cleaned it up gently while they made the plant steady again."
            )
        )
    qa.append(
        (
            f"How did they make the plant safe again?",
            f"They used {fix.label} and worked together carefully. The fix matched the kind of wobble the plant had, so the pot could stand straight again."
        )
    )
    qa.append(
        (
            "How did the story end?",
            f"It ended happily, with the plant standing safe and upright again. The ending feels warm because a small household problem was solved with care instead of panic."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["plant_cfg"].tags) | set(f["bump"].tags) | set(f["fix"].tags)
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
        if ent.attrs:
            bits.append(f"attrs={ent.attrs}")
        lines.append(f"  {ent.id:8} ({ent.type:11}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
need(Place, Plant, Bump, N) :-
    place(Place), plant(Plant), bump(Bump),
    height(Plant, H), force(Bump, F), base_stability(Place, S),
    N = H + F - S, N > 0.

fits(Place, Plant, Fix) :-
    fix(Fix),
    not needs_soft(Fix);
    needs_soft(Fix), soft_stem(Plant).

fits(Place, Plant, Fix) :-
    fix(Fix),
    not requires_repot(Fix);
    requires_repot(Fix), can_repot(Place).

valid(Place, Plant, Bump, Fix) :-
    need(Place, Plant, Bump, N),
    fits(Place, Plant, Fix),
    power(Fix, P), P >= N.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        lines.append(asp.fact("base_stability", pid, place.base_stability))
        if place.can_repot:
            lines.append(asp.fact("can_repot", pid))
    for pid, plant in PLANTS.items():
        lines.append(asp.fact("plant", pid))
        lines.append(asp.fact("height", pid, plant.height))
        if plant.stem_soft:
            lines.append(asp.fact("soft_stem", pid))
    for bid, bump in BUMPS.items():
        lines.append(asp.fact("bump", bid))
        lines.append(asp.fact("force", bid, bump.force))
    for fid, fix in FIXES.items():
        lines.append(asp.fact("fix", fid))
        lines.append(asp.fact("power", fid, fix.power))
        if fix.needs_soft_stem:
            lines.append(asp.fact("needs_soft", fid))
        if fix.requires_repot:
            lines.append(asp.fact("requires_repot", fid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH between ASP and Python valid combos:")
        if clingo_set - python_set:
            print("  only in ASP:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in Python:", sorted(python_set - clingo_set))

    try:
        sample = generate(CURATED[0])
        if not sample.story or "tipsy" not in sample.story.lower():
            raise StoryError("smoke test story missing text or required seed word")
        emit(sample, trace=False, qa=False)
        print("OK: smoke generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Storyworld: a child notices a tipsy plant and helps make it safe again."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--plant", choices=PLANTS)
    ap.add_argument("--bump", choices=BUMPS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--helper", choices=["mother", "father", "grandmother", "grandfather"])
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set")
    ap.add_argument("--trace", action="store_true", help="dump world state")
    ap.add_argument("--qa", action="store_true", help="include QA")
    ap.add_argument("--json", action="store_true", help="emit JSON")
    ap.add_argument("--asp", action="store_true", help="list compatible combos from ASP")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.plant and args.bump and args.fix:
        place = PLACES[args.place]
        plant = PLANTS[args.plant]
        bump = BUMPS[args.bump]
        fix = FIXES[args.fix]
        if not can_stabilize(place, plant, bump, fix):
            raise StoryError(explain_rejection(place, plant, bump, fix))

    combos = [
        combo
        for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.plant is None or combo[1] == args.plant)
        and (args.bump is None or combo[2] == args.bump)
        and (args.fix is None or combo[3] == args.fix)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, plant_id, bump_id, fix_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = args.helper or rng.choice(["mother", "father", "grandmother", "grandfather"])
    trait = rng.choice(TRAITS)
    return StoryParams(
        place=place_id,
        plant=plant_id,
        bump=bump_id,
        fix=fix_id,
        child_name=name,
        child_gender=gender,
        helper=helper,
        trait=trait,
    )


def _render_bump_source(child_name: str, bump: Bump) -> str:
    if bump.id == "backpack":
        return f"{child_name}'s backpack brushed the side of the pot as {child_name} turned around"
    return bump.source_text


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.plant not in PLANTS:
        raise StoryError(f"(Unknown plant: {params.plant})")
    if params.bump not in BUMPS:
        raise StoryError(f"(Unknown bump: {params.bump})")
    if params.fix not in FIXES:
        raise StoryError(f"(Unknown fix: {params.fix})")

    place = PLACES[params.place]
    plant = PLANTS[params.plant]
    bump = copy.deepcopy(BUMPS[params.bump])
    bump.source_text = _render_bump_source(params.child_name, bump)
    fix = FIXES[params.fix]
    if not can_stabilize(place, plant, bump, fix):
        raise StoryError(explain_rejection(place, plant, bump, fix))

    world = tell(
        place=place,
        plant_cfg=plant,
        bump=bump,
        fix=fix,
        child_name=params.child_name,
        child_type=params.child_gender,
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
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, plant, bump, fix) combos:\n")
        for place, plant, bump, fix in combos:
            print(f"  {place:10} {plant:10} {bump:10} {fix}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples: list[StorySample] = []
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
            header = f"### {p.child_name}: {p.plant} on {p.place} ({p.bump} -> {p.fix})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
