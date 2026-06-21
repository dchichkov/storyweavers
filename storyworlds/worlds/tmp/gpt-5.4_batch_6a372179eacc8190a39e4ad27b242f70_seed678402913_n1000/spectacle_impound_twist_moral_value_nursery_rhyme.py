#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/spectacle_impound_twist_moral_value_nursery_rhyme.py
===============================================================================

A tiny nursery-rhyme-style story world about a child who wants to make a grand
street spectacle for the morning parade. Some parade rigs are steady and some
are not; some are gentle enough for a lane full of ducklings and some are too
loud. When the child chooses flash over care, the parade marshal may impound
the little cart until it is made safe. The twist is that the town does not
reward the biggest show. It rewards the kindest heart.

Run it
------
    python storyworlds/worlds/gpt-5.4/spectacle_impound_twist_moral_value_nursery_rhyme.py
    python storyworlds/worlds/gpt-5.4/spectacle_impound_twist_moral_value_nursery_rhyme.py --vehicle wagon --spectacle mirror_castle --pace racing
    python storyworlds/worlds/gpt-5.4/spectacle_impound_twist_moral_value_nursery_rhyme.py --vehicle pram --spectacle drum_comet
    python storyworlds/worlds/gpt-5.4/spectacle_impound_twist_moral_value_nursery_rhyme.py --all --qa
    python storyworlds/worlds/gpt-5.4/spectacle_impound_twist_moral_value_nursery_rhyme.py --verify
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


# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------
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


# ---------------------------------------------------------------------------
# Domain configs
# ---------------------------------------------------------------------------
@dataclass
class Vehicle:
    id: str
    label: str
    phrase: str
    capacity: int
    height_limit: int
    quiet_limit: int
    glide: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Spectacle:
    id: str
    label: str
    phrase: str
    load: int
    height: int
    noise: int
    shimmer: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Pace:
    id: str
    label: str
    hurry: int
    line: str
    tags: set[str] = field(default_factory=set)


# ---------------------------------------------------------------------------
# World
# ---------------------------------------------------------------------------
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


# ---------------------------------------------------------------------------
# Rules
# ---------------------------------------------------------------------------
@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_wobble(world: World) -> list[str]:
    vehicle = world.get("vehicle")
    show = world.get("show")
    hero = world.get("hero")
    if vehicle.meters["moving"] < THRESHOLD:
        return []
    risky = False
    if show.attrs["height"] >= 2 and hero.memes["hurry"] >= THRESHOLD:
        risky = True
    if show.attrs["noise"] > vehicle.attrs["quiet_limit"]:
        risky = True
    if not risky:
        return []
    sig = ("wobble",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    vehicle.meters["wobble"] += 1
    hero.memes["worry"] += 1
    return ["__wobble__"]


def _r_scare_ducks(world: World) -> list[str]:
    show = world.get("show")
    hero = world.get("hero")
    ducks = world.get("ducks")
    if show.attrs["noise"] < 2 or hero.memes["hurry"] < THRESHOLD:
        return []
    sig = ("ducks",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    ducks.memes["fear"] += 1
    hero.memes["worry"] += 1
    return ["__ducks__"]


def _r_impound(world: World) -> list[str]:
    vehicle = world.get("vehicle")
    marshal = world.get("marshal")
    if vehicle.meters["wobble"] < THRESHOLD and world.get("ducks").memes["fear"] < THRESHOLD:
        return []
    sig = ("impound",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    vehicle.meters["impounded"] += 1
    vehicle.meters["moving"] = 0.0
    marshal.memes["duty"] += 1
    return ["__impound__"]


def _r_cheer(world: World) -> list[str]:
    hero = world.get("hero")
    crowd = world.get("crowd")
    if hero.memes["kindness"] < THRESHOLD:
        return []
    sig = ("cheer",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    crowd.memes["cheer"] += 1
    hero.memes["hope"] += 1
    return ["__cheer__"]


CAUSAL_RULES = [
    Rule(name="wobble", tag="physical", apply=_r_wobble),
    Rule(name="scare_ducks", tag="social", apply=_r_scare_ducks),
    Rule(name="impound", tag="physical", apply=_r_impound),
    Rule(name="cheer", tag="social", apply=_r_cheer),
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
            if not line.startswith("__"):
                world.say(line)
    return produced


# ---------------------------------------------------------------------------
# Constraints and outcome logic
# ---------------------------------------------------------------------------
def rig_fits(vehicle: Vehicle, spectacle: Spectacle) -> bool:
    return spectacle.load <= vehicle.capacity and spectacle.height <= vehicle.height_limit


def would_impound(vehicle: Vehicle, spectacle: Spectacle, pace: Pace) -> bool:
    if spectacle.noise > vehicle.quiet_limit:
        return True
    return pace.hurry >= 1 and (spectacle.height >= 2 or spectacle.noise >= 2)


def outcome_of(params: "StoryParams") -> str:
    vehicle = VEHICLES[params.vehicle]
    spectacle = SPECTACLES[params.spectacle]
    pace = PACES[params.pace]
    return "impounded" if would_impound(vehicle, spectacle, pace) else "steady"


def explain_rejection(vehicle: Vehicle, spectacle: Spectacle) -> str:
    if spectacle.load > vehicle.capacity:
        return (
            f"(No story: {spectacle.phrase} is too heavy for {vehicle.phrase}. "
            f"A parade cart that cannot carry its own spectacle is not a plausible start.)"
        )
    return (
        f"(No story: {spectacle.phrase} stands too tall for {vehicle.phrase}. "
        f"The show would be impossible before the story even begins.)"
    )


# ---------------------------------------------------------------------------
# Prediction
# ---------------------------------------------------------------------------
def predict_trouble(world: World) -> dict:
    sim = world.copy()
    sim.get("vehicle").meters["moving"] += 1
    propagate(sim, narrate=False)
    return {
        "wobble": sim.get("vehicle").meters["wobble"] >= THRESHOLD,
        "duck_fear": sim.get("ducks").memes["fear"] >= THRESHOLD,
        "impounded": sim.get("vehicle").meters["impounded"] >= THRESHOLD,
    }


# ---------------------------------------------------------------------------
# Verbs / screenplay beats
# ---------------------------------------------------------------------------
def introduce(world: World, hero: Entity, helper: Entity, vehicle: Vehicle, spectacle: Spectacle) -> None:
    hero.memes["joy"] += 1
    hero.memes["pride"] += 1
    world.say(
        f"In the lane where cobbles clicked, little {hero.id} woke up quick. "
        f"By the gate stood {vehicle.phrase}, ready for the morning spectacle."
    )
    world.say(
        f"{helper.id} came skipping, light on toes, while {hero.id} tied bows upon bows. "
        f"Soon {spectacle.phrase} rose above the cart, {spectacle.shimmer}."
    )


def boast(world: World, hero: Entity, pace: Pace, spectacle: Spectacle) -> None:
    hero.memes["hurry"] = float(pace.hurry)
    world.say(
        f'"What a spectacle!" sang {hero.id}. "{spectacle.label} will make the whole town stare." '
        f'{pace.line}'
    )


def warning(world: World, hero: Entity, helper: Entity, marshal: Entity) -> None:
    pred = predict_trouble(world)
    world.facts["predicted_wobble"] = pred["wobble"]
    world.facts["predicted_ducks"] = pred["duck_fear"]
    helper.memes["care"] += 1
    if pred["impounded"]:
        extra = "The lane ahead held ducklings and a turning stone, and a rattly rush would not end well."
    else:
        extra = "The lane ahead held ducklings and a turning stone, so care would carry the day."
    world.say(
        f'{helper.id} touched the handle and said, "Slow feet, bright eyes, and kindly cheer. '
        f'Even {marshal.label_word} smiles when little carts are careful here." {extra}'
    )


def start_parade(world: World, vehicle: Entity, hero: Entity) -> None:
    vehicle.meters["moving"] += 1
    hero.memes["hope"] += 1
    propagate(world, narrate=False)


def impound_scene(world: World, hero: Entity, helper: Entity, marshal: Entity, vehicle: Vehicle, spectacle: Spectacle) -> None:
    world.say(
        f"Clink-clank, clatter-snap! {vehicle.label.capitalize()} gave a wobbling flap. "
        f"The ducklings peeped and huddled near as {spectacle.label} shivered in the air."
    )
    world.say(
        f'{marshal.label_word.capitalize()} raised a hand. "I must impound this cart for now," '
        f'{marshal.pronoun()} said. "A parade may sparkle, but it must not scare small feet or tip its crown."'
    )
    hero.memes["shame"] += 1
    helper.memes["care"] += 1


def steady_scene(world: World, hero: Entity, helper: Entity, vehicle: Vehicle, spectacle: Spectacle) -> None:
    world.say(
        f"{vehicle.label.capitalize()} rolled with {vehicle.glide}, and the lane rang soft and sweet. "
        f"{spectacle.label.capitalize()} bobbed above the bows, but it did not bump a single beak or beat."
    )
    world.say(
        f"{hero.id} grinned at {helper.id}. It looked grand enough to win a prize, or so {hero.pronoun()} thought."
    )


def kindness_turn(world: World, hero: Entity, helper: Entity, marshal: Entity) -> None:
    ducks = world.get("ducks")
    hero.memes["kindness"] += 1
    hero.memes["pride"] = 0.0
    ducks.memes["fear"] = 0.0
    propagate(world, narrate=False)
    if world.get("vehicle").meters["impounded"] >= THRESHOLD:
        world.say(
            f"But when the ducklings peeped at the curb, {hero.id} forgot the ribbon dream. "
            f"{hero.pronoun().capitalize()} knelt beside them with {helper.id}, brushing stray streamers from the lane and guiding the fluffy line across the gleam."
        )
        world.say(
            f"Seeing those gentle hands, {marshal.label_word} softened. "
            f'"A sorry heart that turns to help is worth more than a noisy show," {marshal.pronoun()} said.'
        )
        world.get("vehicle").meters["impounded"] = 0.0
        world.facts["returned_after_help"] = True
    else:
        world.say(
            f"Then a ribbon string blew loose and tangled near the ducklings by the curb. "
            f"{hero.id} stopped the cart at once, and with {helper.id} tucked every string away before walking the little birds across."
        )
        world.say(
            f'{marshal.label_word.capitalize()} nodded. "That is parade music to my ears," {marshal.pronoun()} said.'
        )


def twist_award(world: World, hero: Entity, marshal: Entity, spectacle: Spectacle) -> None:
    hero.memes["joy"] += 1
    hero.memes["lesson"] += 1
    world.say(
        f"At last came judging time. Children lined up with tassels, tin stars, and towers high as bread. "
        f"{hero.id} waited for praise of {spectacle.label}, for surely the biggest spectacle would be chosen, or so everyone said."
    )
    world.say(
        f"But the town bell chimed a smaller tune. {marshal.label_word.capitalize()} held up a blue heart ribbon and smiled. "
        f'"This goes not to the grandest cart," {marshal.pronoun()} said, "but to the child who kept the lane safe and kind."'
    )
    world.say(
        f"So {hero.id} wore the ribbon on a quiet coat, and learned a better song to sing: "
        f"bright things may dazzle for a minute, but gentle deeds are what make a village ring."
    )


def closing_image(world: World, hero: Entity, helper: Entity, vehicle: Vehicle) -> None:
    world.say(
        f"Home they went by evening light, with {helper.id} skipping at {hero.id}'s side. "
        f"{vehicle.label.capitalize()} rolled softly then, and the ducklings slept while the little blue ribbon rode."
    )


def tell(
    vehicle_cfg: Vehicle,
    spectacle_cfg: Spectacle,
    pace_cfg: Pace,
    hero_name: str = "Mina",
    hero_gender: str = "girl",
    helper_name: str = "Pip",
    helper_gender: str = "boy",
    marshal_type: str = "father",
) -> World:
    world = World()
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender, role="hero"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender, role="helper"))
    marshal = world.add(Entity(id="Marshal", kind="character", type=marshal_type, role="marshal", label="the marshal"))
    vehicle = world.add(
        Entity(
            id="vehicle",
            type="vehicle",
            label=vehicle_cfg.label,
            phrase=vehicle_cfg.phrase,
            attrs={
                "capacity": vehicle_cfg.capacity,
                "height_limit": vehicle_cfg.height_limit,
                "quiet_limit": vehicle_cfg.quiet_limit,
                "glide": vehicle_cfg.glide,
            },
            tags=set(vehicle_cfg.tags),
        )
    )
    show = world.add(
        Entity(
            id="show",
            type="spectacle",
            label=spectacle_cfg.label,
            phrase=spectacle_cfg.phrase,
            attrs={
                "load": spectacle_cfg.load,
                "height": spectacle_cfg.height,
                "noise": spectacle_cfg.noise,
                "shimmer": spectacle_cfg.shimmer,
            },
            tags=set(spectacle_cfg.tags),
        )
    )
    ducks = world.add(Entity(id="ducks", type="ducklings", label="ducklings", tags={"ducklings"}))
    crowd = world.add(Entity(id="crowd", type="crowd", label="the crowd"))

    introduce(world, hero, helper, vehicle_cfg, spectacle_cfg)
    world.para()
    boast(world, hero, pace_cfg, spectacle_cfg)
    warning(world, hero, helper, marshal)
    start_parade(world, vehicle, hero)

    world.para()
    impounded = vehicle.meters["impounded"] >= THRESHOLD
    if impounded:
        impound_scene(world, hero, helper, marshal, vehicle_cfg, spectacle_cfg)
    else:
        steady_scene(world, hero, helper, vehicle_cfg, spectacle_cfg)

    world.para()
    kindness_turn(world, hero, helper, marshal)

    world.para()
    twist_award(world, hero, marshal, spectacle_cfg)
    closing_image(world, hero, helper, vehicle_cfg)

    world.facts.update(
        hero=hero,
        helper=helper,
        marshal=marshal,
        vehicle_cfg=vehicle_cfg,
        spectacle_cfg=spectacle_cfg,
        pace_cfg=pace_cfg,
        impounded=impounded,
        returned_after_help=world.facts.get("returned_after_help", False),
        outcome="impounded" if impounded else "steady",
    )
    return world


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
VEHICLES = {
    "wagon": Vehicle(
        id="wagon",
        label="wagon",
        phrase="a red wagon with stout little wheels",
        capacity=2,
        height_limit=2,
        quiet_limit=2,
        glide="a patient, wooden glide",
        tags={"wagon"},
    ),
    "handcart": Vehicle(
        id="handcart",
        label="handcart",
        phrase="a trim handcart with tidy rails",
        capacity=3,
        height_limit=3,
        quiet_limit=1,
        glide="a neat, narrow whisper",
        tags={"cart"},
    ),
    "pram": Vehicle(
        id="pram",
        label="pram",
        phrase="a toy pram with silver handles",
        capacity=1,
        height_limit=1,
        quiet_limit=3,
        glide="a sleepy little hum",
        tags={"pram"},
    ),
}

SPECTACLES = {
    "ribbon_moon": Spectacle(
        id="ribbon_moon",
        label="ribbon moon",
        phrase="a ribbon moon with paper stars",
        load=1,
        height=1,
        noise=0,
        shimmer="it fluttered without a fuss",
        tags={"ribbon", "moon"},
    ),
    "bell_sun": Spectacle(
        id="bell_sun",
        label="bell sun",
        phrase="a bell sun with golden rays",
        load=1,
        height=1,
        noise=2,
        shimmer="it jingled with every tiny turn",
        tags={"bells", "sun"},
    ),
    "mirror_castle": Spectacle(
        id="mirror_castle",
        label="mirror castle",
        phrase="a mirror castle of cardboard towers",
        load=2,
        height=2,
        noise=1,
        shimmer="it flashed silver squares over the lane",
        tags={"mirror", "castle"},
    ),
    "drum_comet": Spectacle(
        id="drum_comet",
        label="drum comet",
        phrase="a drum comet with tailing tins",
        load=2,
        height=2,
        noise=3,
        shimmer="it rattled and boomed like a pan parade",
        tags={"drum", "noise"},
    ),
}

PACES = {
    "careful": Pace(
        id="careful",
        label="careful",
        hurry=0,
        line='Then {name} took a steady breath and promised not to dash.',
        tags={"careful"},
    ),
    "brisk": Pace(
        id="brisk",
        label="brisk",
        hurry=1,
        line='Then {name} gave the handle a smart little push, half skipping, half swaying.',
        tags={"brisk"},
    ),
    "racing": Pace(
        id="racing",
        label="racing",
        hurry=1,
        line='Then {name} cried, "Make way, make way!" and rushed as if the prize were already won.',
        tags={"racing"},
    ),
}

GIRL_NAMES = ["Mina", "Tess", "Lulu", "Dora", "Nell", "Mabel", "Poppy", "June"]
BOY_NAMES = ["Pip", "Toby", "Ned", "Ollie", "Benji", "Milo", "Finn", "Jory"]


# ---------------------------------------------------------------------------
# StoryParams
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    vehicle: str
    spectacle: str
    pace: str
    hero_name: str
    hero_gender: str
    helper_name: str
    helper_gender: str
    marshal: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        vehicle="wagon",
        spectacle="mirror_castle",
        pace="careful",
        hero_name="Mina",
        hero_gender="girl",
        helper_name="Pip",
        helper_gender="boy",
        marshal="father",
    ),
    StoryParams(
        vehicle="wagon",
        spectacle="bell_sun",
        pace="racing",
        hero_name="Toby",
        hero_gender="boy",
        helper_name="Nell",
        helper_gender="girl",
        marshal="mother",
    ),
    StoryParams(
        vehicle="handcart",
        spectacle="drum_comet",
        pace="brisk",
        hero_name="Poppy",
        hero_gender="girl",
        helper_name="Milo",
        helper_gender="boy",
        marshal="father",
    ),
    StoryParams(
        vehicle="pram",
        spectacle="ribbon_moon",
        pace="careful",
        hero_name="Ned",
        hero_gender="boy",
        helper_name="June",
        helper_gender="girl",
        marshal="mother",
    ),
]


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
KNOWLEDGE = {
    "spectacle": [
        (
            "What is a spectacle?",
            "A spectacle is something big and eye-catching that people stop to look at. It may be bright, noisy, or surprising."
        )
    ],
    "impound": [
        (
            "What does impound mean?",
            "To impound something means a grown-up in charge takes it away for a while because it is not safe or not allowed. You only get it back after the problem is fixed."
        )
    ],
    "ducklings": [
        (
            "Why should people be gentle around ducklings?",
            "Ducklings are small and easy to frighten. Gentle, quiet steps help keep them safe."
        )
    ],
    "kindness": [
        (
            "Why can kindness matter more than showing off?",
            "Showing off makes people look at you for a moment, but kindness helps others for real. That is why many stories treat kindness as the better prize."
        )
    ],
    "parade": [
        (
            "What is a parade?",
            "A parade is a line of people or carts moving together so others can watch. Good parades are cheerful, but they also have to be safe."
        )
    ],
    "bells": [
        (
            "Why can bells be a problem near small animals?",
            "Bells can ring suddenly and loudly. That can startle small animals that do not know where the sound is coming from."
        )
    ],
    "mirror": [
        (
            "Why can tall decorations wobble?",
            "Tall decorations put more weight high up. When a cart turns or bumps, the top can sway and make the whole thing less steady."
        )
    ],
}
KNOWLEDGE_ORDER = ["spectacle", "impound", "parade", "ducklings", "bells", "mirror", "kindness"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    vehicle = f["vehicle_cfg"]
    spectacle = f["spectacle_cfg"]
    outcome = f["outcome"]
    if outcome == "impounded":
        return [
            'Write a nursery-rhyme-style story for a young child that includes the words "spectacle" and "impound".',
            f"Tell a rhyming parade story where {hero.id} makes {spectacle.phrase} on {vehicle.phrase}, rushes too fast, and the marshal must impound the cart until a kinder choice is made.",
            "Write a twist ending where everyone expects the biggest show to win, but the prize goes to the child who helps others instead.",
        ]
    return [
        'Write a nursery-rhyme-style story for a young child that includes the words "spectacle" and "impound".',
        f"Tell a gentle parade story where {hero.id} rolls {spectacle.phrase} on {vehicle.phrase}, chooses care over showing off, and proves kindness matters most.",
        "Write a twist ending where the crowd expects the brightest decoration to win, but the prize goes to safe and kind behavior instead.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    marshal = f["marshal"]
    vehicle = f["vehicle_cfg"]
    spectacle = f["spectacle_cfg"]
    pace = f["pace_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, who built a parade spectacle, and {helper.id}, who tried to help. The marshal also mattered because {marshal.pronoun()} watched whether the lane stayed safe."
        ),
        (
            f"What kind of spectacle did {hero.id} make?",
            f"{hero.id} made {spectacle.phrase} on {vehicle.phrase}. It was meant to make the parade look bright and grand."
        ),
        (
            f"Why did {helper.id} tell {hero.id} to be careful?",
            f"{helper.id} could see that the lane had a turning stone and little ducklings nearby. Care mattered because a rushed cart might wobble or frighten someone small."
        ),
    ]
    if f["impounded"]:
        qa.append(
            (
                f"Why did the marshal impound the cart?",
                f'The marshal impounded it because {hero.id} hurried with a spectacle that was too risky for the lane. The cart wobbled and the ducklings were frightened, so safety had to come before showing off.'
            )
        )
        qa.append(
            (
                f"What changed after the cart was impounded?",
                f"After the impound, {hero.id} stopped thinking only about winning and helped the ducklings instead. That kind action showed the marshal that {hero.pronoun()} had learned something important."
            )
        )
    else:
        qa.append(
            (
                f"Was the cart impounded in this story?",
                f"No. {hero.id} moved carefully, so the spectacle stayed steady and the lane stayed calm. The story still used the idea of impound as something careful children avoid."
            )
        )
        qa.append(
            (
                f"What kind thing did {hero.id} do during the parade?",
                f"{hero.id} stopped the parade to help the ducklings cross safely and tuck loose ribbons away. That mattered more than keeping the parade moving fast."
            )
        )
    qa.append(
        (
            "What was the twist at the end?",
            f"The twist was that the town did not choose the biggest or noisiest spectacle as the winner. Instead, the ribbon went to {hero.id} for being safe and kind."
        )
    )
    qa.append(
        (
            "What is the moral of the story?",
            "The moral is that kindness and care are worth more than showing off. Bright things can catch the eye, but gentle choices help a whole town."
        )
    )
    qa.append(
        (
            f"How did {hero.id} feel at the end?",
            f"{hero.id} felt happy, but in a quieter way than at the start. {hero.pronoun().capitalize()} learned that a warm heart can shine brighter than a parade prize."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"spectacle", "impound", "parade", "ducklings", "kindness"}
    show = world.get("show")
    if "bells" in show.tags or "noise" in show.tags:
        tags.add("bells")
    if "mirror" in show.tags or show.attrs["height"] >= 2:
        tags.add("mirror")
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
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


# ---------------------------------------------------------------------------
# Trace
# ---------------------------------------------------------------------------
def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        attrs = {k: v for k, v in e.attrs.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if attrs:
            bits.append(f"attrs={attrs}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
fits(V, S) :- capacity(V, C), load(S, L), L <= C,
              height_limit(V, Hm), height(S, H), H <= Hm.
valid(V, S) :- vehicle(V), spectacle(S), fits(V, S).

risky(V, S, P) :- quiet_limit(V, Q), noise(S, N), N > Q, pace(P).
risky(V, S, P) :- hurry(P, H), H >= 1, height(S, T), T >= 2, vehicle(V), spectacle(S).
risky(V, S, P) :- hurry(P, H), H >= 1, noise(S, N), N >= 2, vehicle(V), spectacle(S).

outcome(impounded) :- chosen_vehicle(V), chosen_spectacle(S), chosen_pace(P), risky(V, S, P).
outcome(steady) :- chosen_vehicle(V), chosen_spectacle(S), chosen_pace(P), not risky(V, S, P).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for vid, vehicle in VEHICLES.items():
        lines.append(asp.fact("vehicle", vid))
        lines.append(asp.fact("capacity", vid, vehicle.capacity))
        lines.append(asp.fact("height_limit", vid, vehicle.height_limit))
        lines.append(asp.fact("quiet_limit", vid, vehicle.quiet_limit))
    for sid, spectacle in SPECTACLES.items():
        lines.append(asp.fact("spectacle", sid))
        lines.append(asp.fact("load", sid, spectacle.load))
        lines.append(asp.fact("height", sid, spectacle.height))
        lines.append(asp.fact("noise", sid, spectacle.noise))
    for pid, pace in PACES.items():
        lines.append(asp.fact("pace", pid))
        lines.append(asp.fact("hurry", pid, pace.hurry))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_vehicle", params.vehicle),
            asp.fact("chosen_spectacle", params.spectacle),
            asp.fact("chosen_pace", params.pace),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if cl - py:
            print("  only in clingo:", sorted(cl - py))
        if py - cl:
            print("  only in python:", sorted(py - cl))

    cases = list(CURATED)
    for seed in range(30):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(params)
    bad = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if bad == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("Empty story generated during smoke test.")
        print("OK: smoke test story generation succeeded.")
    except Exception as err:  # pragma: no cover - verify path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


# ---------------------------------------------------------------------------
# Interface helpers
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str]]:
    combos: list[tuple[str, str]] = []
    for vid, vehicle in VEHICLES.items():
        for sid, spectacle in SPECTACLES.items():
            if rig_fits(vehicle, spectacle):
                combos.append((vid, sid))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Nursery-rhyme parade storyworld: a child builds a spectacle, "
        "may face an impound, and learns that kindness beats showing off."
    )
    ap.add_argument("--vehicle", choices=VEHICLES)
    ap.add_argument("--spectacle", choices=SPECTACLES)
    ap.add_argument("--pace", choices=PACES)
    ap.add_argument("--hero-name")
    ap.add_argument("--helper-name")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
    ap.add_argument("--marshal", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible vehicle/spectacle set from clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP twin and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.vehicle and args.spectacle:
        vehicle = VEHICLES[args.vehicle]
        spectacle = SPECTACLES[args.spectacle]
        if not rig_fits(vehicle, spectacle):
            raise StoryError(explain_rejection(vehicle, spectacle))

    combos = [
        combo
        for combo in valid_combos()
        if (args.vehicle is None or combo[0] == args.vehicle)
        and (args.spectacle is None or combo[1] == args.spectacle)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    vehicle_id, spectacle_id = rng.choice(sorted(combos))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or rng.choice(["girl", "boy"])
    hero_name = args.hero_name or _pick_name(rng, hero_gender)
    helper_name = args.helper_name or _pick_name(rng, helper_gender, avoid=hero_name)
    pace = args.pace or rng.choice(sorted(PACES))
    marshal = args.marshal or rng.choice(["mother", "father"])
    return StoryParams(
        vehicle=vehicle_id,
        spectacle=spectacle_id,
        pace=pace,
        hero_name=hero_name,
        hero_gender=hero_gender,
        helper_name=helper_name,
        helper_gender=helper_gender,
        marshal=marshal,
    )


def _paced_line(params: StoryParams) -> str:
    return PACES[params.pace].line.format(name=params.hero_name)


def generate(params: StoryParams) -> StorySample:
    if params.vehicle not in VEHICLES:
        raise StoryError(f"(Unknown vehicle '{params.vehicle}'.)")
    if params.spectacle not in SPECTACLES:
        raise StoryError(f"(Unknown spectacle '{params.spectacle}'.)")
    if params.pace not in PACES:
        raise StoryError(f"(Unknown pace '{params.pace}'.)")
    if params.marshal not in {"mother", "father"}:
        raise StoryError(f"(Unknown marshal type '{params.marshal}'.)")
    if not rig_fits(VEHICLES[params.vehicle], SPECTACLES[params.spectacle]):
        raise StoryError(explain_rejection(VEHICLES[params.vehicle], SPECTACLES[params.spectacle]))

    pace_cfg = Pace(
        id=PACES[params.pace].id,
        label=PACES[params.pace].label,
        hurry=PACES[params.pace].hurry,
        line=_paced_line(params),
        tags=set(PACES[params.pace].tags),
    )
    world = tell(
        vehicle_cfg=VEHICLES[params.vehicle],
        spectacle_cfg=SPECTACLES[params.spectacle],
        pace_cfg=pace_cfg,
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        helper_name=params.helper_name,
        helper_gender=params.helper_gender,
        marshal_type=params.marshal,
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
        print(asp_program("", "#show valid/2.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (vehicle, spectacle) combos:\n")
        for vehicle, spectacle in combos:
            print(f"  {vehicle:8} {spectacle}")
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
            header = f"### {p.hero_name}: {p.spectacle} on {p.vehicle} ({p.pace}, {outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
