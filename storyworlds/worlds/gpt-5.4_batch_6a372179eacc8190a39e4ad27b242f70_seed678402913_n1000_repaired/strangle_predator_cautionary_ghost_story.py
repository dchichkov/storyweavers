#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/strangle_predator_cautionary_ghost_story.py
======================================================================

A standalone storyworld for a gentle cautionary ghost story: a child slips away
at dusk to follow a pale, ghost-like lure near a dangerous place, gets tangled,
calls for help, and learns the safer way to face a spooky feeling.

Seed requirements carried into the domain
-----------------------------------------
Words: "strangle", "predator"
Feature: cautionary
Style: ghost story

World premise
-------------
This world rebuilds a small child-facing ghost-story shape:

* Beginning: someone hears an old warning about a spooky place at dusk.
* Tension: a pale light or whispery sound makes the place feel haunted.
* Turn: the child goes too near and gets caught in a real physical hazard.
* Resolution: a grown-up rescues them, explains the danger clearly, and shows a
  safer way to enjoy the night.

The ghostly part is atmospheric, but the simulation stays classical and
commonsense: the "ghost" impression comes from fog, moonlight, moths, reeds, or
wind, while the real risk is vines, wire, or roots near water or dark ground.

Run it
------
    python storyworlds/worlds/gpt-5.4/strangle_predator_cautionary_ghost_story.py
    python storyworlds/worlds/gpt-5.4/strangle_predator_cautionary_ghost_story.py --place marsh --hazard wire
    python storyworlds/worlds/gpt-5.4/strangle_predator_cautionary_ghost_story.py --hazard open_path
    python storyworlds/worlds/gpt-5.4/strangle_predator_cautionary_ghost_story.py --all
    python storyworlds/worlds/gpt-5.4/strangle_predator_cautionary_ghost_story.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/strangle_predator_cautionary_ghost_story.py --verify
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
        female = {"girl", "woman", "mother", "grandmother", "aunt"}
        male = {"boy", "man", "father", "grandfather", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        mapping = {
            "mother": "mom",
            "father": "dad",
            "grandmother": "grandma",
            "grandfather": "grandpa",
            "aunt": "aunt",
            "uncle": "uncle",
        }
        return mapping.get(self.type, self.type)


@dataclass
class Place:
    id: str
    scene: str
    haunted_name: str
    safe_spot: str
    danger_line: str
    night_image: str
    has_water: bool = False
    has_drop: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Lure:
    id: str
    glow: str
    cause: str
    whisper: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Hazard:
    id: str
    label: str
    phrase: str
    warning: str
    snag_text: str
    risk_noun: str
    danger: int
    strangle_risk: bool = False
    near_water_only: bool = False
    near_drop_only: bool = False
    harmless: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Rescue:
    id: str
    sense: int
    power: int
    text: str
    fail: str
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


def _r_tangle_fear(world: World) -> list[str]:
    hero = world.get("hero")
    if hero.meters["tangled"] < THRESHOLD:
        return []
    sig = ("tangle_fear",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["fear"] += 1
    if "caretaker" in world.entities:
        world.get("caretaker").memes["alarm"] += 1
    return ["__tangle__"]


def _r_tighten(world: World) -> list[str]:
    hero = world.get("hero")
    hazard = world.get("hazard")
    if hero.meters["tangled"] < THRESHOLD:
        return []
    sig = ("tighten",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.meters["trapped"] += 1
    if hazard.attrs.get("strangle_risk"):
        hero.meters["neck_risk"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="tangle_fear", tag="emotional", apply=_r_tangle_fear),
    Rule(name="tighten", tag="physical", apply=_r_tighten),
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


def hazard_fits(place: Place, hazard: Hazard) -> bool:
    if hazard.harmless:
        return False
    if hazard.near_water_only and not place.has_water:
        return False
    if hazard.near_drop_only and not place.has_drop:
        return False
    return True


def sensible_rescues() -> list[Rescue]:
    return [r for r in RESCUES.values() if r.sense >= SENSE_MIN]


def severity_of(hazard: Hazard, delay: int) -> int:
    return hazard.danger + delay


def is_contained(rescue: Rescue, hazard: Hazard, delay: int) -> bool:
    return rescue.power >= severity_of(hazard, delay)


def predict_tangle(world: World) -> dict:
    sim = world.copy()
    hero = sim.get("hero")
    hazard = sim.get("hazard")
    hero.meters["tangled"] += 1
    propagate(sim, narrate=False)
    return {
        "tangled": hero.meters["tangled"] >= THRESHOLD,
        "neck_risk": hero.meters["neck_risk"] >= THRESHOLD,
        "fear": hero.memes["fear"],
        "risk_noun": hazard.label,
    }


def opening(world: World, hero: Entity, caretaker: Entity, place: Place) -> None:
    world.say(
        f"At the edge of dusk, {hero.id} walked with {hero.pronoun('possessive')} "
        f"{caretaker.label_word} near {place.scene}. The grown-up path ended at "
        f"{place.safe_spot}, and beyond that lay {place.haunted_name}."
    )
    world.say(place.night_image)


def warning(world: World, hero: Entity, caretaker: Entity, place: Place, hazard: Hazard) -> None:
    pred = predict_tangle(world)
    world.facts["predicted_neck_risk"] = pred["neck_risk"]
    world.facts["predicted_fear"] = pred["fear"]
    hero.memes["unease"] += 1
    neck_line = ""
    if pred["neck_risk"]:
        neck_line = " If someone pushed through in the dark, the loops could even strangle a small animal."
    world.say(
        f'"Stay on this side of {place.danger_line}," {caretaker.label_word} said softly. '
        f'"{hazard.warning}{neck_line}"'
    )


def lure_appears(world: World, hero: Entity, lure: Lure, place: Place) -> None:
    hero.memes["curiosity"] += 1
    world.say(
        f"Then {lure.glow} drifted beyond the fence, and {lure.whisper}. In the half-light, "
        f"{place.haunted_name} looked exactly like the sort of place where a ghost might wait."
    )


def old_tale(world: World, caretaker: Entity, lure: Lure) -> None:
    world.say(
        f'{caretaker.label_word.capitalize()} did not laugh at the spooky feeling. '
        f'"Long ago, people told ghost stories about lights like that," {caretaker.pronoun()} said. '
        f'"But the old tale was only the night playing tricks. {lure.cause}."'
    )


def edge_closer(world: World, hero: Entity) -> None:
    hero.memes["defiance"] += 1
    world.say(
        f"{hero.id} promised to stay close, but one more pale flicker tugged at "
        f"{hero.pronoun('object')}. {hero.pronoun().capitalize()} took a quiet step past the safe stones."
    )


def snag(world: World, hero: Entity, hazard: Hazard) -> None:
    hero.meters["tangled"] += 1
    propagate(world, narrate=False)
    world.say(hazard.snag_text.format(name=hero.id))
    if hero.meters["neck_risk"] >= THRESHOLD:
        world.say(
            f"For one terrible second, {hero.id} felt the pull creeping upward and remembered "
            f"the warning that such loops could strangle a nesting bird or a frightened fox."
        )
    else:
        world.say(
            f"The fright was sharp and sudden. The place had not held a ghost at all, only a real danger hidden by dark."
        )


def cry_for_help(world: World, hero: Entity, caretaker: Entity) -> None:
    hero.memes["trust"] += 1
    world.say(f'"{caretaker.label_word.capitalize()}!" {hero.id} cried. "{hero.pronoun().capitalize()} can\'t get loose!"')


def rescue_success(world: World, caretaker: Entity, rescue: Rescue, hero: Entity) -> None:
    hero.meters["tangled"] = 0.0
    hero.meters["trapped"] = 0.0
    hero.meters["neck_risk"] = 0.0
    hero.memes["fear"] = 0.0
    hero.memes["relief"] += 1
    hero.memes["lesson"] += 1
    world.say(
        f"{caretaker.label_word.capitalize()} came at once and {rescue.text}. "
        f"Soon the tight feeling was gone, and {hero.id} could breathe in a long, shaky gulp."
    )


def rescue_fail(world: World, caretaker: Entity, rescue: Rescue, hero: Entity, place: Place) -> None:
    hero.memes["fear"] += 1
    hero.meters["trapped"] += 1
    world.say(
        f"{caretaker.label_word.capitalize()} {rescue.fail}, but the tangle only tightened. "
        f"The dark beside {place.scene} suddenly felt huge and cold."
    )


def call_second_help(world: World, caretaker: Entity, rescue: Rescue) -> None:
    world.say(
        f"{caretaker.pronoun().capitalize()} scooped the child away from the worst of it and called for more help. "
        f"A ranger from the lane arrived with stronger cutters and a bright headlamp."
    )


def lesson(world: World, caretaker: Entity, hero: Entity, hazard: Hazard, place: Place) -> None:
    predator_line = ""
    if place.has_water or "night" in hazard.tags:
        predator_line = (
            f" {caretaker.pronoun().capitalize()} added that after sunset, every small creature listens for a predator, "
            f"and children should not wander where they cannot see their feet."
        )
    world.say(
        f'{caretaker.label_word.capitalize()} knelt beside {hero.id} and wrapped a warm arm around '
        f'{hero.pronoun("object")}. "The night can look haunted," {caretaker.pronoun()} said, '
        f'"but the real danger is what you cannot see until it catches you."{predator_line}'
    )
    if hazard.strangle_risk:
        world.say(
            f'"That is why I warned you about {hazard.label}," {caretaker.pronoun()} went on. '
            f'"They do not mean to be cruel, but they can snag, tighten, and even strangle something small that thrashes."'
        )


def safer_end(world: World, hero: Entity, caretaker: Entity, lure: Lure, place: Place) -> None:
    hero.memes["wonder"] += 1
    world.say(
        f"They went back to {place.safe_spot}, where the stones were clear and flat. "
        f"From there, {caretaker.label_word} pointed toward the pale shimmer again."
    )
    world.say(
        f"It was no ghost after all, only {lure.cause.lower()}. Standing safely together, "
        f"{hero.id} could admire the strange night-light without stepping into it."
    )
    world.say(
        f"When they finally turned for home, {place.haunted_name} still looked whispery and silver, "
        f"but now it looked like a place to respect, not a place to chase."
    )


def grim_end(world: World, hero: Entity, caretaker: Entity, place: Place) -> None:
    hero.memes["lesson"] += 1
    hero.memes["relief"] += 1
    world.say(
        f"By the time the stronger help had cut everything away, {hero.id} was safe but trembling. "
        f"{caretaker.label_word.capitalize()} carried {hero.pronoun('object')} all the way home."
    )
    world.say(
        f"After that night, {hero.id} never crossed {place.danger_line} at dusk again. "
        f"The ghost story stayed in the village, but the real lesson stayed in {hero.pronoun('possessive')} bones."
    )


def tell(
    place: Place,
    lure: Lure,
    hazard: Hazard,
    rescue: Rescue,
    hero_name: str = "Nora",
    hero_type: str = "girl",
    caretaker_type: str = "grandmother",
    delay: int = 0,
) -> World:
    world = World()
    hero = world.add(Entity(id="hero", kind="character", type=hero_type, label=hero_name, role="hero"))
    caretaker = world.add(
        Entity(id="caretaker", kind="character", type=caretaker_type, label="the caretaker", role="caretaker")
    )
    hazard_ent = world.add(
        Entity(
            id="hazard",
            kind="thing",
            type="hazard",
            label=hazard.label,
            phrase=hazard.phrase,
            attrs={"strangle_risk": hazard.strangle_risk},
            tags=set(hazard.tags),
        )
    )
    world.add(Entity(id="place", kind="thing", type="place", label=place.haunted_name, tags=set(place.tags)))

    hero.attrs["name"] = hero_name
    caretaker.attrs["name"] = caretaker.label_word

    opening(world, hero, caretaker, place)
    warning(world, hero, caretaker, place, hazard)

    world.para()
    lure_appears(world, hero, lure, place)
    old_tale(world, caretaker, lure)
    edge_closer(world, hero)
    snag(world, hero, hazard)
    cry_for_help(world, hero, caretaker)

    world.para()
    contained = is_contained(rescue, hazard, delay)
    if contained:
        rescue_success(world, caretaker, rescue, hero)
        lesson(world, caretaker, hero, hazard, place)
        world.para()
        safer_end(world, hero, caretaker, lure, place)
        outcome = "rescued"
    else:
        rescue_fail(world, caretaker, rescue, hero, place)
        call_second_help(world, caretaker, rescue)
        lesson(world, caretaker, hero, hazard, place)
        world.para()
        grim_end(world, hero, caretaker, place)
        outcome = "hard_lesson"

    world.facts.update(
        hero=hero,
        caretaker=caretaker,
        place_cfg=place,
        lure=lure,
        hazard_cfg=hazard,
        rescue=rescue,
        outcome=outcome,
        delay=delay,
        severity=severity_of(hazard, delay),
        contained=contained,
        neck_risk=hazard.strangle_risk,
        ghostly=True,
    )
    return world


PLACES = {
    "marsh": Place(
        id="marsh",
        scene="the marsh behind the old mill",
        haunted_name="the Whisper Reeds",
        safe_spot="the stone landing",
        danger_line="the last fence post",
        night_image="Mist lay low over the water, and the reeds rubbed together with a papery hiss.",
        has_water=True,
        tags={"marsh", "night"},
    ),
    "orchard": Place(
        id="orchard",
        scene="the orchard behind the cider shed",
        haunted_name="the Moon Row",
        safe_spot="the lantern gate",
        danger_line="the gate latch",
        night_image="Wind moved through the apple branches, and loose strips of bark flashed pale as little hands.",
        has_water=False,
        tags={"orchard", "night"},
    ),
    "cliffpath": Place(
        id="cliffpath",
        scene="the cliff path above the sea",
        haunted_name="the White Turn",
        safe_spot="the watch bench",
        danger_line="the painted rope",
        night_image="Sea fog dragged over the grass, and the far surf boomed like someone knocking under the earth.",
        has_drop=True,
        tags={"cliff", "night"},
    ),
}

LURES = {
    "moths": Lure(
        id="moths",
        glow="a swarm of white moths",
        cause="Moonlight caught a flutter of white moth wings",
        whisper="their wings made a dry whisper in the reeds",
        tags={"moths", "night"},
    ),
    "fog": Lure(
        id="fog",
        glow="a patch of milk-pale fog",
        cause="cold fog had found a pocket of moonlight",
        whisper="the fog slid along the ground with a hush that sounded almost like someone calling",
        tags={"fog", "night"},
    ),
    "lantern_shard": Lure(
        id="lantern_shard",
        glow="a broken flash from an old bit of glass",
        cause="a shard of bottle-glass on the ground had caught the moon",
        whisper="the wind threaded through the grass in a thin whisper",
        tags={"moonlight", "night"},
    ),
}

HAZARDS = {
    "vines": Hazard(
        id="vines",
        label="hanging vine loops",
        phrase="the hanging vine loops by the edge",
        warning="The vine loops catch at sleeves and ankles in the dark.",
        snag_text="{name}'s foot slipped into a low green loop, and another wet vine curled around a wrist.",
        risk_noun="loops",
        danger=2,
        strangle_risk=True,
        tags={"vines", "night"},
    ),
    "wire": Hazard(
        id="wire",
        label="old fence wire",
        phrase="the old fence wire in the grass",
        warning="Old fence wire lies hidden there, and it can bite into boots before you feel it.",
        snag_text="{name} brushed the grass and stumbled as hidden wire caught at a boot and twisted around a knee.",
        risk_noun="wire",
        danger=3,
        near_drop_only=False,
        tags={"wire", "night"},
    ),
    "roots": Hazard(
        id="roots",
        label="twisted root hooks",
        phrase="the twisted root hooks by the bank",
        warning="The roots near the bank grab shoes and hold on when the mud is slick.",
        snag_text="{name} stepped where the ground looked solid, but a root hook clamped over a shoe and pitched the other foot sideways.",
        risk_noun="roots",
        danger=2,
        near_water_only=True,
        tags={"roots", "night"},
    ),
    "open_path": Hazard(
        id="open_path",
        label="open path",
        phrase="the open path",
        warning="It is only dark there.",
        snag_text="{name} took a step and found nothing to catch at all.",
        risk_noun="path",
        danger=0,
        harmless=True,
        tags={"path"},
    ),
}

RESCUES = {
    "shears": Rescue(
        id="shears",
        sense=3,
        power=4,
        text="used the hedge shears from the gate post to snip the tangle apart",
        fail="worked at the tangle with garden shears",
        qa_text="cut the tangle apart with hedge shears",
        tags={"shears", "safety"},
    ),
    "staff": Rescue(
        id="staff",
        sense=2,
        power=2,
        text="slid a long walking staff under the loops and lifted them away one by one",
        fail="tried to lever the loops away with a walking staff",
        qa_text="lifted the loops away with a walking staff",
        tags={"staff", "safety"},
    ),
    "bare_hands": Rescue(
        id="bare_hands",
        sense=1,
        power=1,
        text="pulled at the tangle with bare hands until it loosened",
        fail="pulled at the tangle with bare hands",
        qa_text="pulled at the tangle with bare hands",
        tags={"hands"},
    ),
}

GIRL_NAMES = ["Nora", "Mia", "Elsie", "Wren", "Ada", "Lucy", "Ivy", "Mabel"]
BOY_NAMES = ["Theo", "Finn", "Eli", "Owen", "Max", "Leo", "Ben", "Silas"]


@dataclass
class StoryParams:
    place: str
    lure: str
    hazard: str
    rescue: str
    name: str
    gender: str
    caretaker: str
    delay: int = 0
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        place="marsh",
        lure="moths",
        hazard="vines",
        rescue="shears",
        name="Nora",
        gender="girl",
        caretaker="grandmother",
        delay=0,
    ),
    StoryParams(
        place="orchard",
        lure="fog",
        hazard="wire",
        rescue="staff",
        name="Theo",
        gender="boy",
        caretaker="grandfather",
        delay=0,
    ),
    StoryParams(
        place="marsh",
        lure="lantern_shard",
        hazard="roots",
        rescue="staff",
        name="Ivy",
        gender="girl",
        caretaker="aunt",
        delay=1,
    ),
    StoryParams(
        place="cliffpath",
        lure="fog",
        hazard="wire",
        rescue="shears",
        name="Finn",
        gender="boy",
        caretaker="uncle",
        delay=1,
    ),
    StoryParams(
        place="marsh",
        lure="moths",
        hazard="wire",
        rescue="staff",
        name="Ada",
        gender="girl",
        caretaker="grandmother",
        delay=2,
    ),
]


KNOWLEDGE = {
    "ghost_story": [
        (
            "What is a ghost story?",
            "A ghost story is a spooky tale that makes ordinary night things feel mysterious. The best ones still leave room for real explanations."
        )
    ],
    "predator": [
        (
            "What is a predator?",
            "A predator is an animal that hunts other animals for food. Many predators come out when the light is low and small animals are harder to see."
        )
    ],
    "moths": [
        (
            "Why do moths look ghostly at night?",
            "White moths can flash in moonlight and seem to appear and disappear. That makes them look mysterious from far away."
        )
    ],
    "fog": [
        (
            "Why can fog look spooky?",
            "Fog blurs edges and softens shapes, so trees and fences do not look the way they do in daytime. Your eyes try to guess what is there."
        )
    ],
    "moonlight": [
        (
            "Why does moonlight make things look strange?",
            "Moonlight is dimmer than sunlight, so it leaves more shadows and silver edges. Familiar things can look unfamiliar in it."
        )
    ],
    "vines": [
        (
            "Why are hanging vines dangerous in the dark?",
            "Vines can catch at your feet, wrists, or clothes when you cannot see them clearly. If you struggle wildly, they can tighten instead of letting go."
        )
    ],
    "wire": [
        (
            "Why is old wire dangerous?",
            "Old wire can hide in grass and catch your shoe before you notice it. Sharp or twisted wire can trip you and make it hard to move safely."
        )
    ],
    "roots": [
        (
            "Why are roots slippery near water?",
            "Roots near a wet bank can be slick with mud and water. They can grab a shoe or make a foot slide."
        )
    ],
    "shears": [
        (
            "What are hedge shears for?",
            "Hedge shears are strong cutting tools grown-ups use for thick plants and stems. They can cut through tangles that are too tough to pull apart safely."
        )
    ],
    "staff": [
        (
            "Why might a long staff help in a tangle?",
            "A long staff lets a grown-up lift or move something from a safer distance. That can stop hands from getting caught too."
        )
    ],
    "night_safety": [
        (
            "Why should children stay on clear paths at dusk?",
            "At dusk it gets harder to see holes, roots, loops, and wire. A clear path lets you enjoy the evening without stepping into hidden danger."
        )
    ],
}
KNOWLEDGE_ORDER = [
    "ghost_story",
    "predator",
    "moths",
    "fog",
    "moonlight",
    "vines",
    "wire",
    "roots",
    "shears",
    "staff",
    "night_safety",
]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    if not sensible_rescues():
        return combos
    for place_id, place in PLACES.items():
        for lure_id in LURES:
            for hazard_id, hazard in HAZARDS.items():
                if hazard_fits(place, hazard):
                    combos.append((place_id, lure_id, hazard_id))
    return combos


def explain_rejection(place: Place, hazard: Hazard) -> str:
    if hazard.harmless:
        return (
            f"(No story: {hazard.phrase} would not trap anyone, so there is no honest cautionary turn. "
            f"Pick a real hazard like vines, wire, or roots.)"
        )
    if hazard.near_water_only and not place.has_water:
        return (
            f"(No story: {hazard.label} only make sense near water or a muddy bank, but {place.scene} has no water edge.)"
        )
    if hazard.near_drop_only and not place.has_drop:
        return (
            f"(No story: {hazard.label} belong near a drop or cliff edge, but {place.scene} does not have one.)"
        )
    return "(No story: that place and hazard do not make a reasonable cautionary ghost story.)"


def explain_rescue(rid: str) -> str:
    rescue = RESCUES[rid]
    better = ", ".join(sorted(r.id for r in sensible_rescues()))
    return (
        f"(Refusing rescue '{rid}': it scores too low on common sense "
        f"(sense={rescue.sense} < {SENSE_MIN}). Try one of: {better}.)"
    )


def outcome_of(params: StoryParams) -> str:
    rescue = RESCUES[params.rescue]
    hazard = HAZARDS[params.hazard]
    return "rescued" if is_contained(rescue, hazard, params.delay) else "hard_lesson"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    caretaker = f["caretaker"]
    place = f["place_cfg"]
    lure = f["lure"]
    hazard = f["hazard_cfg"]
    outcome = f["outcome"]
    base = (
        f'Write a short cautionary ghost story for a 3-to-5-year-old that includes the words '
        f'"strangle" and "predator". Set it near {place.scene} and make a pale night-light seem spooky at first.'
    )
    if outcome == "rescued":
        return [
            base,
            f"Tell a gentle ghost story where a child named {hero.attrs['name']} steps too close to {place.haunted_name}, "
            f"gets caught by {hazard.label}, and is rescued by {hero.pronoun('possessive')} {caretaker.label_word}.",
            f"Write a spooky-but-safe story where {lure.glow} looks like a ghost, but the real danger is hidden {hazard.risk_noun} in the dark.",
        ]
    return [
        base,
        f"Tell a stronger cautionary ghost story where {hero.attrs['name']} follows a ghostly light, gets badly tangled, and needs extra help after the first rescue fails.",
        f"Write a night-time story that teaches children to respect fences and warning lines because real danger can hide behind a ghostly feeling.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    caretaker = f["caretaker"]
    place = f["place_cfg"]
    lure = f["lure"]
    hazard = f["hazard_cfg"]
    rescue = f["rescue"]
    outcome = f["outcome"]
    hero_name = hero.attrs["name"]
    cw = caretaker.label_word
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero_name} and {hero.pronoun('possessive')} {cw} at {place.scene}. They are together as evening turns the place spooky."
        ),
        (
            f"Why did {cw} warn {hero_name} to stay back?",
            f"{cw.capitalize()} knew that {hazard.label} were hidden beyond {place.danger_line}. In the dark, they could catch a child before the child saw them."
        ),
        (
            f"What made the place seem haunted?",
            f"{lure.glow.capitalize()} appeared in the dusk, and {lure.whisper}. The strange light and sound made the ordinary night feel ghostly."
        ),
        (
            f"What was the real danger behind the ghostly feeling?",
            f"The real danger was {hazard.phrase}, not a ghost. The story turns from a spooky feeling to a physical risk when {hero_name} gets tangled."
        ),
    ]
    if f.get("neck_risk"):
        qa.append(
            (
                "Why does the story use the word 'strangle'?",
                f"It is part of the warning about how dangerous tight loops can be. {cw.capitalize()} explains that hidden vines or loops can strangle something small if it thrashes in panic."
            )
        )
    qa.append(
        (
            "How is the word 'predator' used in the story?",
            f"It helps explain that nighttime is serious for small creatures. {cw.capitalize()} says that when a predator is hunting, small animals stay alert, and children should be careful too."
        )
    )
    if outcome == "rescued":
        qa.append(
            (
                f"How did {cw} help {hero_name}?",
                f"{cw.capitalize()} {rescue.qa_text}. That worked quickly enough to free {hero_name} before the hidden danger grew worse."
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ends safely on {place.safe_spot}, where they can watch the pale light from a distance. {hero_name} still feels wonder, but now also respects the warning line."
            )
        )
    else:
        qa.append(
            (
                f"Did the first rescue work right away?",
                f"No. {cw.capitalize()} tried, but the tangle was too strong and extra help had to come. That makes the lesson feel more serious and cautionary."
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"{hero_name} got home safe, but badly shaken. After that, {hero.pronoun()} never crossed {place.danger_line} at dusk again."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"ghost_story", "predator", "night_safety"}
    tags |= set(f["lure"].tags)
    tags |= set(f["hazard_cfg"].tags)
    if f["rescue"].sense >= SENSE_MIN:
        tags |= set(f["rescue"].tags)
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
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if e.role:
            bits.append(f"role={e.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        lines.append(f"  {e.id:10} ({e.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
% reasonableness gate
hazard_fits(P, H) :- place(P), hazard(H), not harmless(H), not needs_water(H).
hazard_fits(P, H) :- place(P), hazard(H), not harmless(H), needs_water(H), has_water(P).

sensible(R) :- rescue(R), sense(R, S), sense_min(M), S >= M.
valid(P, L, H) :- place(P), lure(L), hazard_fits(P, H).

% outcome model
severity(V) :- chosen_hazard(H), danger(H, D), delay(T), V = D + T.
contained :- chosen_rescue(R), chosen_hazard(H), power(R, P), danger(H, D), delay(T), P >= D + T.
outcome(rescued) :- contained.
outcome(hard_lesson) :- not contained.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        if place.has_water:
            lines.append(asp.fact("has_water", pid))
        if place.has_drop:
            lines.append(asp.fact("has_drop", pid))
    for lid in LURES:
        lines.append(asp.fact("lure", lid))
    for hid, hazard in HAZARDS.items():
        lines.append(asp.fact("hazard", hid))
        lines.append(asp.fact("danger", hid, hazard.danger))
        if hazard.near_water_only:
            lines.append(asp.fact("needs_water", hid))
        if hazard.near_drop_only:
            lines.append(asp.fact("needs_drop", hid))
        if hazard.harmless:
            lines.append(asp.fact("harmless", hid))
    for rid, rescue in RESCUES.items():
        lines.append(asp.fact("rescue", rid))
        lines.append(asp.fact("sense", rid, rescue.sense))
        lines.append(asp.fact("power", rid, rescue.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
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

    scenario = "\n".join(
        [
            asp.fact("chosen_hazard", params.hazard),
            asp.fact("chosen_rescue", params.rescue),
            asp.fact("delay", params.delay),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0
    c_valid, p_valid = set(asp_valid_combos()), set(valid_combos())
    if c_valid == p_valid:
        print(f"OK: gate matches valid_combos() ({len(c_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if c_valid - p_valid:
            print("  only in clingo:", sorted(c_valid - p_valid))
        if p_valid - c_valid:
            print("  only in python:", sorted(p_valid - c_valid))

    c_sens, p_sens = set(asp_sensible()), {r.id for r in sensible_rescues()}
    if c_sens == p_sens:
        print(f"OK: sensible rescues match ({sorted(c_sens)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible rescues: clingo={sorted(c_sens)} python={sorted(p_sens)}")

    cases = list(CURATED)
    parser = build_parser()
    for s in range(30):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(s))
        except StoryError:
            continue
        cases.append(params)

    bad = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcome checks differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("smoke test produced an empty story")
        print("OK: smoke-test generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Storyworld: a cautionary ghost story where a child follows a spooky night lure into a real hidden danger."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--lure", choices=LURES)
    ap.add_argument("--hazard", choices=HAZARDS)
    ap.add_argument("--rescue", choices=RESCUES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--caretaker", choices=["grandmother", "grandfather", "aunt", "uncle"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], help="how long the tangle tightens before rescue takes hold")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.hazard:
        place = PLACES[args.place]
        hazard = HAZARDS[args.hazard]
        if not hazard_fits(place, hazard):
            raise StoryError(explain_rejection(place, hazard))
    if args.hazard and HAZARDS[args.hazard].harmless:
        place = PLACES[args.place] if args.place else next(iter(PLACES.values()))
        raise StoryError(explain_rejection(place, HAZARDS[args.hazard]))
    if args.rescue and RESCUES[args.rescue].sense < SENSE_MIN:
        raise StoryError(explain_rescue(args.rescue))

    combos = [
        combo
        for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.lure is None or combo[1] == args.lure)
        and (args.hazard is None or combo[2] == args.hazard)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, lure_id, hazard_id = rng.choice(sorted(combos))
    rescue_id = args.rescue or rng.choice(sorted(r.id for r in sensible_rescues()))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    caretaker = args.caretaker or rng.choice(["grandmother", "grandfather", "aunt", "uncle"])
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    return StoryParams(
        place=place_id,
        lure=lure_id,
        hazard=hazard_id,
        rescue=rescue_id,
        name=name,
        gender=gender,
        caretaker=caretaker,
        delay=delay,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.lure not in LURES:
        raise StoryError(f"(Unknown lure: {params.lure})")
    if params.hazard not in HAZARDS:
        raise StoryError(f"(Unknown hazard: {params.hazard})")
    if params.rescue not in RESCUES:
        raise StoryError(f"(Unknown rescue: {params.rescue})")
    if not hazard_fits(PLACES[params.place], HAZARDS[params.hazard]):
        raise StoryError(explain_rejection(PLACES[params.place], HAZARDS[params.hazard]))
    if RESCUES[params.rescue].sense < SENSE_MIN:
        raise StoryError(explain_rescue(params.rescue))

    world = tell(
        place=PLACES[params.place],
        lure=LURES[params.lure],
        hazard=HAZARDS[params.hazard],
        rescue=RESCUES[params.rescue],
        hero_name=params.name,
        hero_type=params.gender,
        caretaker_type=params.caretaker,
        delay=params.delay,
    )

    hero_name = params.name
    story_text = world.render().replace("hero", hero_name)
    world.paragraphs = [p[:] for p in world.paragraphs]
    return StorySample(
        params=params,
        story=story_text,
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
        print(asp_program("", "#show valid/3.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        sens = asp_sensible()
        print(f"sensible rescues: {', '.join(sens)}\n")
        print(f"{len(combos)} compatible (place, lure, hazard) combos:\n")
        for place, lure, hazard in combos:
            print(f"  {place:10} {lure:14} {hazard}")
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
            header = f"### {p.name}: {p.place}, {p.lure}, {p.hazard} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
