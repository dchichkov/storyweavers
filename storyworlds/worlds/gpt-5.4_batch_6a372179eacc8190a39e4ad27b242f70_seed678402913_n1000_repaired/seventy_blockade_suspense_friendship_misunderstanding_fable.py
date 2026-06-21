#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/seventy_blockade_suspense_friendship_misunderstanding_fable.py
=========================================================================================

A standalone story world for a small fable-shaped domain:

Two animal friends mean well, but one suddenly finds a blockade across a path and
misunderstands it. Suspense rises while the blocked friend tries to guess what
happened. Then the truth appears: the blockade was built to protect, not reject.
The misunderstanding clears, the friendship deepens, and the ending image proves
what changed.

Required seed words included in every story:
- "seventy"
- "blockade"

Run it
------
    python storyworlds/worlds/gpt-5.4/seventy_blockade_suspense_friendship_misunderstanding_fable.py
    python storyworlds/worlds/gpt-5.4/seventy_blockade_suspense_friendship_misunderstanding_fable.py --all
    python storyworlds/worlds/gpt-5.4/seventy_blockade_suspense_friendship_misunderstanding_fable.py -n 5 --seed 7
    python storyworlds/worlds/gpt-5.4/seventy_blockade_suspense_friendship_misunderstanding_fable.py --qa
    python storyworlds/worlds/gpt-5.4/seventy_blockade_suspense_friendship_misunderstanding_fable.py --verify
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
CLEAR_SIGNAL_MIN = 2
PATIENT_TRAITS = {"patient", "thoughtful", "steady"}


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
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Setting:
    id: str
    place: str
    path_name: str
    backdrop: str
    affords: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Hazard:
    id: str
    name: str
    sign: str
    threat: str
    sound: str
    aftermath: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Material:
    id: str
    label: str
    phrase: str
    count_noun: str
    verb: str
    guards: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Signal:
    id: str
    label: str
    clue: str
    explanation: str
    clarity: int = 1
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
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

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


def _r_blockade_holds(world: World) -> list[str]:
    out: list[str] = []
    path = world.entities.get("path")
    wall = world.entities.get("blockade")
    if path is None or wall is None:
        return out
    if path.meters["hazard_active"] < THRESHOLD or wall.meters["built"] < THRESHOLD:
        return out
    sig = ("holds", world.facts.get("hazard_id", ""), world.facts.get("material_id", ""))
    if sig in world.fired:
        return out
    world.fired.add(sig)
    path.meters["danger"] = 0.0
    path.meters["safe"] += 1
    builder = world.entities.get("friend")
    if builder is not None:
        builder.memes["care"] += 1
    out.append("__held__")
    return out


def _r_open_path_is_risky(world: World) -> list[str]:
    out: list[str] = []
    path = world.entities.get("path")
    wall = world.entities.get("blockade")
    if path is None or wall is None:
        return out
    if path.meters["hazard_active"] < THRESHOLD:
        return out
    if wall.meters["built"] >= THRESHOLD:
        return out
    sig = ("risky_open", world.facts.get("hazard_id", ""))
    if sig in world.fired:
        return out
    world.fired.add(sig)
    path.meters["danger"] += 1
    for actor in world.characters():
        actor.memes["fear"] += 1
    out.append("__risk__")
    return out


def _r_misunderstanding_hurts(world: World) -> list[str]:
    hero = world.entities.get("hero")
    if hero is None or hero.memes["misunderstanding"] < THRESHOLD:
        return []
    sig = ("hurt", hero.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["hurt"] += 1
    return []


def _r_explanation_repairs(world: World) -> list[str]:
    hero = world.entities.get("hero")
    friend = world.entities.get("friend")
    if hero is None or friend is None:
        return []
    if hero.memes["understanding"] < THRESHOLD:
        return []
    sig = ("repair", hero.id, friend.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["misunderstanding"] = 0.0
    hero.memes["hurt"] = 0.0
    hero.memes["trust"] += 1
    friend.memes["trust"] += 1
    hero.memes["relief"] += 1
    friend.memes["relief"] += 1
    return []


CAUSAL_RULES: list[Rule] = [
    Rule(name="blockade_holds", tag="physical", apply=_r_blockade_holds),
    Rule(name="open_path_is_risky", tag="physical", apply=_r_open_path_is_risky),
    Rule(name="misunderstanding_hurts", tag="social", apply=_r_misunderstanding_hurts),
    Rule(name="explanation_repairs", tag="social", apply=_r_explanation_repairs),
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
        for sent in produced:
            world.say(sent)
    return produced


def valid_material(hazard: Hazard, material: Material) -> bool:
    return hazard.id in material.guards


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for setting_id, setting in SETTINGS.items():
        for hazard_id in sorted(setting.affords):
            hazard = HAZARDS[hazard_id]
            for material_id, material in MATERIALS.items():
                if valid_material(hazard, material):
                    combos.append((setting_id, hazard.id, material_id))
    return combos


def misunderstanding_depth(signal: Signal, trait: str) -> str:
    if signal.clarity >= CLEAR_SIGNAL_MIN or trait in PATIENT_TRAITS:
        return "brief"
    return "deep"


def predict_safety(world: World, hazard_id: str, material_id: str) -> dict:
    sim = world.copy()
    sim.facts["hazard_id"] = hazard_id
    sim.facts["material_id"] = material_id
    sim.get("path").meters["hazard_active"] += 1
    sim.get("blockade").meters["built"] += 1
    propagate(sim, narrate=False)
    return {
        "safe": sim.get("path").meters["safe"] >= THRESHOLD,
        "danger": sim.get("path").meters["danger"],
    }


def introduce(world: World, hero: Entity, friend: Entity) -> None:
    world.say(
        f"In {world.setting.place}, {hero.id} the {hero.type} and {friend.id} the {friend.type} "
        f"were such good friends that the smaller birds said they shared one brave heart between them."
    )
    world.say(world.setting.backdrop)


def promise(world: World, hero: Entity, friend: Entity) -> None:
    world.say(
        f"That morning they had promised to meet by {world.setting.path_name} and carry breakfast to each other: "
        f"{hero.id} would bring berries, and {friend.id} would bring honey cakes."
    )


def approach(world: World, hero: Entity, material: Material, signal: Signal) -> None:
    world.say(
        f"But when {hero.id} reached the bend, {hero.pronoun()} stopped short. "
        f"Across the path stood a blockade of seventy {material.count_noun}, "
        f"{material.verb} into {material.phrase}."
    )
    world.say(
        f"{signal.clue} Yet {friend_name(world)} was nowhere to be seen."
    )


def feel_misunderstanding(world: World, hero: Entity, depth: str) -> None:
    hero.memes["misunderstanding"] += 1
    propagate(world, narrate=False)
    if depth == "deep":
        world.say(
            f"{hero.id}'s chest gave a small, sore thump. "
            f'"Has my friend shut me out?" {hero.pronoun()} wondered.'
        )
    else:
        world.say(
            f"{hero.id} blinked and felt a quick pinch of worry. "
            f"Perhaps there was some reason, but from where {hero.pronoun()} stood, the blockade still looked unfriendly."
        )


def suspense(world: World, hero: Entity, hazard: Hazard) -> None:
    hero.memes["fear"] += 1
    world.say(
        f"Then {hero.pronoun()} heard {hazard.sound}. The sound came once, then again, "
        f"and the path felt too quiet in between."
    )
    world.say(
        f"{hero.id} did not know whether to step closer or run, and that was the sharpest part of the suspense."
    )


def friend_name(world: World) -> str:
    return world.get("friend").id


def reveal(world: World, friend: Entity, hazard: Hazard, material: Material, signal: Signal) -> None:
    path = world.get("path")
    wall = world.get("blockade")
    world.facts["hazard_id"] = hazard.id
    world.facts["material_id"] = material.id
    path.meters["hazard_active"] += 1
    wall.meters["built"] += 1
    propagate(world, narrate=False)
    friend.memes["care"] += 1
    world.say(
        f"At last {friend.id} sprang out from the far side, panting and dusty. "
        f'"Do not climb over!" {friend.pronoun()} cried. "I built that blockade because {hazard.threat}."'
    )
    world.say(
        f"{signal.explanation} {friend.id} pointed past the path, where {hazard.sign}."
    )


def explain_depth(world: World, hero: Entity, friend: Entity, depth: str) -> None:
    hero.memes["understanding"] += 1
    propagate(world, narrate=False)
    if depth == "deep":
        world.say(
            f"{hero.id} felt heat rise in {hero.pronoun('possessive')} face. "
            f"{hero.pronoun().capitalize()} had mistaken care for cruelty."
        )
    else:
        world.say(
            f"At once the worry in {hero.id}'s mind changed shape. "
            f"What had looked rude from far away looked loving now."
        )
    world.say(
        f'"I thought you meant to keep me away," {hero.id} said. '
        f'"Never," answered {friend.id}.'
    )


def join_hands(world: World, hero: Entity, friend: Entity, hazard: Hazard) -> None:
    hero.memes["love"] += 1
    friend.memes["love"] += 1
    world.say(
        f"So the two friends waited together until {hazard.aftermath}. "
        f"When the danger had passed, they opened a safe gap, crossed side by side, and shared breakfast on the other bank."
    )


def moral(world: World, hero: Entity, friend: Entity) -> None:
    world.say(
        f"After that, whenever either friend saw a sudden barrier, {hero.id} and {friend.id} asked for the reason before they blamed the heart behind it."
    )
    world.say("And the old owls, who admire plain truths, said: friendship grows safest where questions walk ahead of suspicion.")


def tell(
    setting: Setting,
    hazard: Hazard,
    material: Material,
    signal: Signal,
    hero_name: str = "Mira",
    hero_type: str = "mole",
    friend_name_value: str = "Pip",
    friend_type: str = "otter",
    trait: str = "patient",
) -> World:
    world = World(setting=setting)
    hero = world.add(
        Entity(
            id=hero_name,
            kind="character",
            type=hero_type,
            role="hero",
            traits=[trait],
            tags={"friendship"},
        )
    )
    friend = world.add(
        Entity(
            id=friend_name_value,
            kind="character",
            type=friend_type,
            role="friend",
            traits=["loyal"],
            tags={"friendship"},
        )
    )
    path = world.add(
        Entity(
            id="path",
            type="path",
            label=setting.path_name,
            phrase=setting.path_name,
            tags={"path"},
        )
    )
    blockade = world.add(
        Entity(
            id="blockade",
            type="blockade",
            label="blockade",
            phrase=material.phrase,
            tags={"blockade"},
        )
    )

    depth = misunderstanding_depth(signal, trait)

    introduce(world, hero, friend)
    promise(world, hero, friend)

    world.para()
    approach(world, hero, material, signal)
    feel_misunderstanding(world, hero, depth)
    suspense(world, hero, hazard)

    world.para()
    reveal(world, friend, hazard, material, signal)
    explain_depth(world, hero, friend, depth)

    world.para()
    join_hands(world, hero, friend, hazard)
    moral(world, hero, friend)

    pred = predict_safety(world, hazard.id, material.id)
    world.facts.update(
        hero=hero,
        friend=friend,
        setting=setting,
        hazard=hazard,
        material=material,
        signal=signal,
        depth=depth,
        predicted_safe=pred["safe"],
        predicted_danger=pred["danger"],
        resolved=hero.memes["trust"] >= THRESHOLD,
    )
    return world


SETTINGS = {
    "brook": Setting(
        id="brook",
        place="the Willow Brook",
        path_name="the little plank crossing",
        backdrop="The reeds bowed over the water, and the morning light moved in stripes across the mud.",
        affords={"flood"},
        tags={"water"},
    ),
    "hill": Setting(
        id="hill",
        place="the Hazel Hill path",
        path_name="the narrow downhill lane",
        backdrop="Dry grass whispered on the slope, and the lane curled between roots like a ribbon.",
        affords={"rolling_nuts"},
        tags={"hill"},
    ),
    "hedge": Setting(
        id="hedge",
        place="the Bramble Hedge gap",
        path_name="the opening in the hedge",
        backdrop="The hedge smelled green and sharp, and tiny leaves flickered whenever the wind tested them.",
        affords={"thorn_wind"},
        tags={"hedge"},
    ),
}

HAZARDS = {
    "flood": Hazard(
        id="flood",
        name="rising floodwater",
        sign="brown water slapped against the posts and rose higher than it had at dawn",
        threat="the brook had swollen, and one wrong step would send someone sliding into the cold rush",
        sound="the thudding gulp of water striking wood",
        aftermath="the water sank back into the brook and the crossing stopped trembling",
        tags={"water", "safety"},
    ),
    "rolling_nuts": Hazard(
        id="rolling_nuts",
        name="rolling hazelnuts",
        sign="a tumble of hard hazelnuts kept rattling down from the windy slope",
        threat="hard nuts were rolling down the lane like marbles, ready to trip small feet",
        sound="a dry clatter bouncing from root to root",
        aftermath="the last hazelnuts rolled still and the lane grew quiet again",
        tags={"hill", "safety"},
    ),
    "thorn_wind": Hazard(
        id="thorn_wind",
        name="thorny wind",
        sign="gusts kept ripping loose thorns from the bramble wall and sending them skittering through the gap",
        threat="the wind was flicking sharp thorns through the opening, and eyes and paws were safer away from it",
        sound="a hiss, then the tiny scratch of thorns on stone",
        aftermath="the gusts softened and the loose thorns settled harmlessly in the grass",
        tags={"wind", "safety"},
    ),
}

MATERIALS = {
    "stones": Material(
        id="stones",
        label="stones",
        phrase="a low wall",
        count_noun="smooth stones",
        verb="stacked",
        guards={"flood"},
        tags={"stones", "blockade"},
    ),
    "branches": Material(
        id="branches",
        label="branches",
        phrase="a springy fence",
        count_noun="crooked branches",
        verb="woven",
        guards={"rolling_nuts"},
        tags={"branches", "blockade"},
    ),
    "leaves": Material(
        id="leaves",
        label="leaves",
        phrase="a thick leafy screen",
        count_noun="broad leaves",
        verb="tied",
        guards={"thorn_wind"},
        tags={"leaves", "blockade"},
    ),
}

SIGNALS = {
    "ribbon": Signal(
        id="ribbon",
        label="ribbon",
        clue="A red ribbon fluttered from the top, but from a distance it looked more like a warning than an invitation.",
        explanation="The ribbon, meant as a sign to wait, had been too small to read kindly from afar.",
        clarity=1,
        tags={"misunderstanding"},
    ),
    "arrow": Signal(
        id="arrow",
        label="arrow",
        clue="A scratched arrow pointed toward a safe stump nearby, though the mark was faint in the dust.",
        explanation="The little arrow had been a guide to the safe waiting place.",
        clarity=2,
        tags={"misunderstanding"},
    ),
    "whistle": Signal(
        id="whistle",
        label="whistle",
        clue="A hollow reed whistle hung on a string there, but the wind had swallowed its meaning.",
        explanation="The whistle had been left so a waiting friend could call back without stepping into danger.",
        clarity=2,
        tags={"misunderstanding"},
    ),
}

ANIMALS = {
    "mole": {"label": "mole"},
    "otter": {"label": "otter"},
    "rabbit": {"label": "rabbit"},
    "beaver": {"label": "beaver"},
    "mouse": {"label": "mouse"},
    "badger": {"label": "badger"},
}

NAMES = {
    "mole": ["Mira", "Moss", "Nell"],
    "otter": ["Pip", "Reed", "Tala"],
    "rabbit": ["Fern", "Hop", "Poppy"],
    "beaver": ["Bram", "Dew", "Toll"],
    "mouse": ["Nip", "Clover", "Tansy"],
    "badger": ["Brindle", "Ash", "Marlow"],
}

TRAITS = ["patient", "thoughtful", "steady", "hasty", "touchy", "quick"]

KNOWLEDGE = {
    "blockade": [
        (
            "What is a blockade?",
            "A blockade is something placed across a way to stop movement. Sometimes it is unkind, but sometimes it is there to keep others safe from danger."
        )
    ],
    "misunderstanding": [
        (
            "What is a misunderstanding?",
            "A misunderstanding happens when someone guesses the wrong meaning of another person's words or actions. Asking a calm question can often clear it up."
        )
    ],
    "water": [
        (
            "Why can floodwater be dangerous?",
            "Floodwater moves fast and can knock feet out from under you. Even shallow rushing water can be stronger than it looks."
        )
    ],
    "hill": [
        (
            "Why can things rolling downhill be dangerous?",
            "Things rolling downhill can move quickly and bump into feet or legs. That can make someone slip or fall."
        )
    ],
    "wind": [
        (
            "Why should you protect your eyes from flying thorns?",
            "Flying thorns are sharp and can scratch skin or eyes. It is safest to stay back until the wind is calm."
        )
    ],
    "friendship": [
        (
            "How can friends fix a misunderstanding?",
            "Friends can stop, explain what they meant, and listen to each other. Trust grows again when both sides tell the truth kindly."
        )
    ],
}
KNOWLEDGE_ORDER = ["blockade", "misunderstanding", "water", "hill", "wind", "friendship"]


@dataclass
class StoryParams:
    setting: str
    hazard: str
    material: str
    signal: str
    hero_name: str
    hero_type: str
    friend_name: str
    friend_type: str
    trait: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        setting="brook",
        hazard="flood",
        material="stones",
        signal="ribbon",
        hero_name="Mira",
        hero_type="mole",
        friend_name="Pip",
        friend_type="otter",
        trait="hasty",
        seed=101,
    ),
    StoryParams(
        setting="hill",
        hazard="rolling_nuts",
        material="branches",
        signal="arrow",
        hero_name="Fern",
        hero_type="rabbit",
        friend_name="Bram",
        friend_type="beaver",
        trait="patient",
        seed=102,
    ),
    StoryParams(
        setting="hedge",
        hazard="thorn_wind",
        material="leaves",
        signal="whistle",
        hero_name="Nip",
        hero_type="mouse",
        friend_name="Brindle",
        friend_type="badger",
        trait="touchy",
        seed=103,
    ),
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    hazard = f["hazard"]
    return [
        'Write a short fable for a young child that includes the words "seventy" and "blockade".',
        f"Tell a suspenseful friendship story where {hero.id} sees a blockade and misunderstands {friend.id}'s intentions before learning the barrier was built for safety.",
        f"Write a fable in which a sudden obstacle, a hidden danger like {hazard.name}, and one honest explanation turn suspicion back into friendship.",
    ]


def story_qa_pairs(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    setting = f["setting"]
    hazard = f["hazard"]
    material = f["material"]
    signal = f["signal"]
    depth = f["depth"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id} the {hero.type} and {friend.id} the {friend.type}, two close friends. Their friendship is tested when one sees a sudden blockade and guesses the wrong reason for it."
        ),
        (
            "What did the hero find on the path?",
            f"{hero.id} found a blockade of seventy {material.count_noun} across {setting.path_name}. It looked sudden and stern, so it sparked the misunderstanding."
        ),
        (
            f"Why did {hero.id} feel upset at first?",
            f"{hero.id} saw the blockade before hearing any explanation and thought {friend.id} might be shutting {hero.pronoun('object')} out. {signal.clue.split('.')[0]}. That made the barrier look colder than it really was."
        ),
        (
            f"What was the real reason for the blockade?",
            f"The blockade was there because {hazard.threat}. {friend.id} built it to stop a friend from stepping into danger, not to hurt any feelings."
        ),
    ]
    if depth == "deep":
        qa.append(
            (
                "Was the misunderstanding small or strong?",
                f"It was strong at first. {hero.id} truly feared that friendship had been replaced by rejection, because the clue was unclear and the silence lasted too long."
            )
        )
    else:
        qa.append(
            (
                "Was the misunderstanding small or strong?",
                f"It was brief. {hero.id} felt worried, but part of {hero.pronoun('possessive')} mind still hoped there was a kind reason behind the blockade."
            )
        )
    qa.append(
        (
            "How was the problem solved?",
            f"{friend.id} explained the danger and showed what the signal had meant. Then both friends waited until the path was safe and crossed together, which proved that trust had returned."
        )
    )
    qa.append(
        (
            "What is the moral of the story?",
            "The moral is that a friend should ask before blaming. A barrier can hide care as easily as it hides a path."
        )
    )
    return qa


def world_knowledge_pairs(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"blockade", "misunderstanding", "friendship"}
    tags |= set(f["hazard"].tags)
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
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.traits:
            bits.append(f"traits={ent.traits}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:10} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


def explain_rejection(setting_id: str, hazard_id: str, material_id: str) -> str:
    setting = SETTINGS[setting_id]
    hazard = HAZARDS[hazard_id]
    material = MATERIALS[material_id]
    if hazard_id not in setting.affords:
        options = ", ".join(sorted(setting.affords))
        return (
            f"(No story: {setting.place} does not naturally host the hazard '{hazard_id}'. "
            f"Try one of: {options}.)"
        )
    return (
        f"(No story: {material.label} do not make a sensible protective blockade against {hazard.name}. "
        f"Pick material that actually suits the danger.)"
    )


def outcome_of(params: StoryParams) -> str:
    if params.signal not in SIGNALS:
        raise StoryError(f"(No story: unknown signal '{params.signal}'.)")
    return misunderstanding_depth(SIGNALS[params.signal], params.trait)


ASP_RULES = r"""
valid(S, H, M) :- setting(S), affords(S, H), material(M), guards(M, H).

patient_trait(T) :- patient_word(T).
patient_trait(T) :- thoughtful_word(T).
patient_trait(T) :- steady_word(T).

depth(brief) :- chosen_signal(Sg), clarity(Sg, C), clear_min(M), C >= M.
depth(brief) :- chosen_trait(T), patient_trait(T).
depth(deep)  :- not depth(brief).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for setting_id, setting in SETTINGS.items():
        lines.append(asp.fact("setting", setting_id))
        for hazard_id in sorted(setting.affords):
            lines.append(asp.fact("affords", setting_id, hazard_id))
    for hazard_id in HAZARDS:
        lines.append(asp.fact("hazard", hazard_id))
    for material_id, material in MATERIALS.items():
        lines.append(asp.fact("material", material_id))
        for guard in sorted(material.guards):
            lines.append(asp.fact("guards", material_id, guard))
    for signal_id, signal in SIGNALS.items():
        lines.append(asp.fact("signal", signal_id))
        lines.append(asp.fact("clarity", signal_id, signal.clarity))
    lines.append(asp.fact("clear_min", CLEAR_SIGNAL_MIN))
    for trait in TRAITS:
        lines.append(asp.fact("trait_word", trait))
    for trait in sorted(PATIENT_TRAITS):
        if trait == "patient":
            lines.append(asp.fact("patient_word", trait))
        elif trait == "thoughtful":
            lines.append(asp.fact("thoughtful_word", trait))
        elif trait == "steady":
            lines.append(asp.fact("steady_word", trait))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_depth(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_signal", params.signal),
            asp.fact("chosen_trait", params.trait),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show depth/1."))
    atoms = asp.atoms(model, "depth")
    return atoms[0][0] if atoms else "?"


def _validate_params(params: StoryParams) -> None:
    if params.setting not in SETTINGS:
        raise StoryError(f"(No story: unknown setting '{params.setting}'.)")
    if params.hazard not in HAZARDS:
        raise StoryError(f"(No story: unknown hazard '{params.hazard}'.)")
    if params.material not in MATERIALS:
        raise StoryError(f"(No story: unknown material '{params.material}'.)")
    if params.signal not in SIGNALS:
        raise StoryError(f"(No story: unknown signal '{params.signal}'.)")
    if params.hero_type not in ANIMALS:
        raise StoryError(f"(No story: unknown hero type '{params.hero_type}'.)")
    if params.friend_type not in ANIMALS:
        raise StoryError(f"(No story: unknown friend type '{params.friend_type}'.)")
    if params.trait not in TRAITS:
        raise StoryError(f"(No story: unknown trait '{params.trait}'.)")
    if (params.setting, params.hazard, params.material) not in valid_combos():
        raise StoryError(explain_rejection(params.setting, params.hazard, params.material))
    if params.hero_name == params.friend_name:
        raise StoryError("(No story: the two friends need different names.)")


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
    for seed in range(30):
        rng = random.Random(seed)
        try:
            params = resolve_params(build_parser().parse_args([]), rng)
        except StoryError:
            continue
        params.seed = seed
        cases.append(params)

    mismatches = 0
    for params in cases:
        if asp_depth(params) != outcome_of(params):
            mismatches += 1
    if mismatches == 0:
        print(f"OK: misunderstanding depth matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {mismatches}/{len(cases)} depth outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("empty story")
        emit(smoke, trace=False, qa=False, header="")
        print("OK: smoke generation succeeded.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a blockade, a misunderstanding, and a friendship repaired."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--hazard", choices=HAZARDS)
    ap.add_argument("--material", choices=MATERIALS)
    ap.add_argument("--signal", choices=SIGNALS)
    ap.add_argument("--hero-type", choices=ANIMALS)
    ap.add_argument("--friend-type", choices=ANIMALS)
    ap.add_argument("--hero-name")
    ap.add_argument("--friend-name")
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible (setting, hazard, material) triples")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP twin and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, animal_type: str, avoid: str = "") -> str:
    pool = [name for name in NAMES[animal_type] if name != avoid]
    return rng.choice(pool)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.hazard and args.material:
        if (args.setting, args.hazard, args.material) not in valid_combos():
            raise StoryError(explain_rejection(args.setting, args.hazard, args.material))

    combos = [
        combo
        for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.hazard is None or combo[1] == args.hazard)
        and (args.material is None or combo[2] == args.material)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, hazard_id, material_id = rng.choice(sorted(combos))
    signal_id = args.signal or rng.choice(sorted(SIGNALS))
    hero_type = args.hero_type or rng.choice(sorted(ANIMALS))
    friend_type = args.friend_type or rng.choice(sorted(ANIMALS))
    hero_name = args.hero_name or _pick_name(rng, hero_type)
    friend_name_value = args.friend_name or _pick_name(rng, friend_type, avoid=hero_name)
    if friend_name_value == hero_name:
        alternatives = [n for n in NAMES[friend_type] if n != hero_name]
        if not alternatives:
            raise StoryError("(No story: could not choose two different names.)")
        friend_name_value = rng.choice(alternatives)
    trait = args.trait or rng.choice(TRAITS)

    params = StoryParams(
        setting=setting_id,
        hazard=hazard_id,
        material=material_id,
        signal=signal_id,
        hero_name=hero_name,
        hero_type=hero_type,
        friend_name=friend_name_value,
        friend_type=friend_type,
        trait=trait,
    )
    _validate_params(params)
    return params


def generate(params: StoryParams) -> StorySample:
    _validate_params(params)
    world = tell(
        setting=SETTINGS[params.setting],
        hazard=HAZARDS[params.hazard],
        material=MATERIALS[params.material],
        signal=SIGNALS[params.signal],
        hero_name=params.hero_name,
        hero_type=params.hero_type,
        friend_name_value=params.friend_name,
        friend_type=params.friend_type,
        trait=params.trait,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa_pairs(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_pairs(world)],
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
        print(asp_program("", "#show valid/3.\n#show depth/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, hazard, material) combos:\n")
        for setting_id, hazard_id, material_id in combos:
            print(f"  {setting_id:8} {hazard_id:13} {material_id}")
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
                f"### {p.hero_name} and {p.friend_name}: {p.material} against {p.hazard} "
                f"at {p.setting} ({outcome_of(p)} misunderstanding)"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
