#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/shamrock_bless_flashback_bravery_happy_ending_fable.py
==================================================================================

A standalone storyworld for a gentle fable: a small creature must carry a
shamrock through a worrisome place in order to bless someone in need. The tale
uses a flashback as part of the decision to be brave, and it ends happily when
kindness is returned with courage.

The world model is classical and state-driven:
- typed entities with physical meters and emotional memes
- a small forward-chaining rule engine
- a reasonableness gate over route / weather / help choices
- an inline ASP twin for parity checks
- story text, prompts, and QA derived from simulated state

Run it
------
    python storyworlds/worlds/gpt-5.4/shamrock_bless_flashback_bravery_happy_ending_fable.py
    python storyworlds/worlds/gpt-5.4/shamrock_bless_flashback_bravery_happy_ending_fable.py --hero rabbit --route brook
    python storyworlds/worlds/gpt-5.4/shamrock_bless_flashback_bravery_happy_ending_fable.py --route cliff
    python storyworlds/worlds/gpt-5.4/shamrock_bless_flashback_bravery_happy_ending_fable.py --all
    python storyworlds/worlds/gpt-5.4/shamrock_bless_flashback_bravery_happy_ending_fable.py --qa
    python storyworlds/worlds/gpt-5.4/shamrock_bless_flashback_bravery_happy_ending_fable.py --verify
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

# Make storyworlds/results.py importable when this file is run directly.
_THIS = os.path.abspath(__file__)
_WORLD_DIR = os.path.dirname(_THIS)
_STORYWORLDS_DIR = os.path.dirname(os.path.dirname(_WORLD_DIR))
sys.path.insert(0, _STORYWORLDS_DIR)
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2
BRAVERY_NEED = 5.0
HELPFUL_WEATHERS = {"dew", "sunny"}


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
        female = {"hen", "doe", "mother", "woman"}
        male = {"stag", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class HeroKind:
    id: str
    species: str
    title: str
    home: str
    move: str
    fear_sound: str
    brave_image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class RecipientKind:
    id: str
    label: str
    need: str
    blessing_result: str
    thanks: str
    tags: set[str] = field(default_factory=set)


@dataclass
class RouteKind:
    id: str
    label: str
    danger: str
    obstacle: str
    crossing: str
    challenge: int
    needs_help: bool = False
    allowed: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class HelperKind:
    id: str
    label: str
    action: str
    courage: str
    sense: int
    tags: set[str] = field(default_factory=set)


@dataclass
class WeatherKind:
    id: str
    label: str
    effect: str
    easy: bool
    tags: set[str] = field(default_factory=set)


@dataclass
class MemoryKind:
    id: str
    giver: str
    gift: str
    lesson: str
    warmth: str
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


def _r_carry_blessing(world: World) -> list[str]:
    hero = world.get("hero")
    shamrock = world.get("shamrock")
    recipient = world.get("recipient")
    if shamrock.meters["delivered"] < THRESHOLD:
        return []
    sig = ("blessed", recipient.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    recipient.meters["blessed"] += 1
    recipient.meters["comfort"] += 1
    hero.memes["joy"] += 1
    hero.memes["peace"] += 1
    return []


def _r_flashback_strength(world: World) -> list[str]:
    hero = world.get("hero")
    if hero.memes["remembering"] < THRESHOLD:
        return []
    sig = ("memory_strength", hero.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["gratitude"] += 1
    hero.memes["bravery"] += 2
    return []


CAUSAL_RULES = [
    Rule(name="carry_blessing", tag="physical", apply=_r_carry_blessing),
    Rule(name="flashback_strength", tag="emotional", apply=_r_flashback_strength),
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
        for s in produced:
            world.say(s)
    return produced


HEROES = {
    "rabbit": HeroKind(
        id="rabbit",
        species="rabbit",
        title="a small gray rabbit",
        home="a clover hill",
        move="hopped",
        fear_sound="the chuckle of the rushing water",
        brave_image="ears up and heart steady",
        tags={"rabbit", "bravery"},
    ),
    "mouse": HeroKind(
        id="mouse",
        species="mouse",
        title="a tiny field mouse",
        home="a warm root-burrow",
        move="scurried",
        fear_sound="the hollow wind in the reeds",
        brave_image="whiskers still and paws sure",
        tags={"mouse", "bravery"},
    ),
    "wren": HeroKind(
        id="wren",
        species="wren",
        title="a little brown wren",
        home="a nest in the hawthorn hedge",
        move="fluttered",
        fear_sound="the dark mutter under the branches",
        brave_image="wings tucked close and eyes bright",
        tags={"bird", "bravery"},
    ),
}

RECIPIENTS = {
    "lamb": RecipientKind(
        id="lamb",
        label="the young lamb",
        need="had lost heart after a night storm",
        blessing_result="stood up straighter and gave a soft, glad bleat",
        thanks="The lamb pressed the shamrock close and smiled.",
        tags={"lamb", "kindness"},
    ),
    "fox_cub": RecipientKind(
        id="fox_cub",
        label="the fox cub",
        need="was shivering after getting caught in the rain",
        blessing_result="stopped trembling and curled into a warm, hopeful ball",
        thanks="The fox cub's amber eyes shone with relief.",
        tags={"fox", "kindness"},
    ),
    "hedgehog": RecipientKind(
        id="hedgehog",
        label="the old hedgehog",
        need="had spent the morning lonely beneath a fern",
        blessing_result="lifted his nose and chuckled as if the day had turned golden",
        thanks="The hedgehog bowed his prickly little head in thanks.",
        tags={"hedgehog", "kindness"},
    ),
}

ROUTES = {
    "brook": RouteKind(
        id="brook",
        label="the singing brook",
        danger="the water ran quick over smooth stones",
        obstacle="a narrow place where the stepping-stones trembled under spray",
        crossing="crossed from stone to stone",
        challenge=2,
        needs_help=False,
        allowed=True,
        tags={"water", "crossing"},
    ),
    "thicket": RouteKind(
        id="thicket",
        label="the shadowy thicket",
        danger="the brambles scratched and the path looked like a knot",
        obstacle="a tunnel of thorny stems and flickering leaves",
        crossing="slipped through the thorny opening",
        challenge=2,
        needs_help=False,
        allowed=True,
        tags={"thicket", "crossing"},
    ),
    "marsh": RouteKind(
        id="marsh",
        label="the silver marsh",
        danger="the ground quivered and the reeds hid the firm path",
        obstacle="a wet patch where one wrong step would sink a small foot",
        crossing="picked a careful way over the hummocks",
        challenge=3,
        needs_help=True,
        allowed=True,
        tags={"marsh", "crossing"},
    ),
    "cliff": RouteKind(
        id="cliff",
        label="the windy cliff edge",
        danger="the drop was steep and the stones were loose",
        obstacle="a sharp ledge above a deep fall",
        crossing="crept along the cliff edge",
        challenge=5,
        needs_help=True,
        allowed=False,
        tags={"cliff"},
    ),
}

HELPERS = {
    "turtle": HelperKind(
        id="turtle",
        label="the old turtle",
        action="offered a broad shell for a steady step",
        courage="went slowly and did not hurry the frightened heart",
        sense=3,
        tags={"turtle", "help"},
    ),
    "deer": HelperKind(
        id="deer",
        label="the gentle deer",
        action="bent low so the small traveler could pass in the shelter of warm legs",
        courage="stood calm as a tree in the wind",
        sense=3,
        tags={"deer", "help"},
    ),
    "reed_raft": HelperKind(
        id="reed_raft",
        label="a little reed raft",
        action="floated light and true over the wet places",
        courage="showed that even small things can bear a kind errand",
        sense=2,
        tags={"raft", "help"},
    ),
    "butterfly": HelperKind(
        id="butterfly",
        label="the butterfly",
        action="fluttered nearby, but could not carry anyone or make the path safe",
        courage="was pretty, though not strong enough for this job",
        sense=1,
        tags={"butterfly"},
    ),
}

WEATHERS = {
    "dew": WeatherKind(
        id="dew",
        label="a silver dewy morning",
        effect="the clover shone and the air smelled cool and clean",
        easy=True,
        tags={"dew", "morning"},
    ),
    "windy": WeatherKind(
        id="windy",
        label="a windy noon",
        effect="the reeds hissed and leaves kept turning their pale backs",
        easy=False,
        tags={"wind", "weather"},
    ),
    "sunny": WeatherKind(
        id="sunny",
        label="a bright sunny afternoon",
        effect="sunlight lay over the meadow like warm cloth",
        easy=True,
        tags={"sun", "weather"},
    ),
}

MEMORIES = {
    "saved_nest": MemoryKind(
        id="saved_nest",
        giver="the recipient",
        gift="once tucked a fallen nestling back into safety",
        lesson="Kindness given on a quiet day deserves courage on a hard one.",
        warmth="The remembered kindness warmed the hero's chest like sunlight.",
        tags={"memory", "kindness"},
    ),
    "shared_seed": MemoryKind(
        id="shared_seed",
        giver="the recipient",
        gift="once shared the last sweet seed of winter",
        lesson="A small gift can become a large reason to be brave.",
        warmth="The old generosity glowed in the hero like a banked ember.",
        tags={"memory", "kindness"},
    ),
    "shelter_rain": MemoryKind(
        id="shelter_rain",
        giver="the recipient",
        gift="once made room under a leaf when the rain came hard",
        lesson="A heart remembered is a heart worth helping.",
        warmth="The memory made the dark path seem less lonely.",
        tags={"memory", "rain"},
    ),
}


def route_possible(route: RouteKind) -> bool:
    return route.allowed


def helper_needed(route: RouteKind) -> bool:
    return route.needs_help


def sensible_helpers(route: RouteKind) -> list[HelperKind]:
    if route.needs_help:
        return [h for h in HELPERS.values() if h.sense >= SENSE_MIN]
    return list(HELPERS.values())


def valid_combo(hero_id: str, recipient_id: str, route_id: str, helper_id: str, weather_id: str, memory_id: str) -> bool:
    del hero_id, recipient_id, memory_id
    route = ROUTES[route_id]
    helper = HELPERS[helper_id]
    weather = WEATHERS[weather_id]
    if not route_possible(route):
        return False
    if helper_needed(route) and helper.sense < SENSE_MIN:
        return False
    if route.id == "marsh" and weather.id == "windy" and helper.sense < 3:
        return False
    return True


def valid_combos() -> list[tuple[str, str, str, str, str, str]]:
    combos: list[tuple[str, str, str, str, str, str]] = []
    for hero_id in HEROES:
        for recipient_id in RECIPIENTS:
            for route_id in ROUTES:
                for helper_id in HELPERS:
                    for weather_id in WEATHERS:
                        for memory_id in MEMORIES:
                            if valid_combo(hero_id, recipient_id, route_id, helper_id, weather_id, memory_id):
                                combos.append((hero_id, recipient_id, route_id, helper_id, weather_id, memory_id))
    return combos


def courage_total(route: RouteKind, helper: HelperKind, weather: WeatherKind, memory: MemoryKind) -> float:
    score = 2.0
    if helper.sense >= SENSE_MIN:
        score += 1.0
    if weather.easy:
        score += 1.0
    if route.challenge <= 2:
        score += 1.0
    if memory.id:
        score += 1.0
    return score


def predict_success(hero: Entity, route: RouteKind, helper: HelperKind, weather: WeatherKind, memory: MemoryKind) -> dict:
    brave = hero.memes["bravery"] + 2.0
    if helper.sense >= SENSE_MIN:
        brave += 1.0
    if weather.easy:
        brave += 1.0
    return {
        "enough_bravery": brave >= route.challenge + 2.0,
        "risk": route.challenge,
        "support": helper.sense,
        "memory": memory.id,
    }


def explain_rejection(route: RouteKind, helper: Optional[HelperKind] = None, weather: Optional[WeatherKind] = None) -> str:
    if not route.allowed:
        return (
            f"(No story: {route.label} is beyond the gentle reasonableness of this fable. "
            f"The danger is too great for a child-facing happy ending. Try brook, thicket, or marsh.)"
        )
    if helper is not None and route.needs_help and helper.sense < SENSE_MIN:
        return (
            f"(No story: {helper.label} is too weak a helper for {route.label}. "
            f"A brave errand may be difficult, but it still needs a sensible way through.)"
        )
    if route.id == "marsh" and weather is not None and weather.id == "windy":
        return (
            f"(No story: the marsh in strong wind needs the steadiest help. "
            f"Choose the turtle or deer, or choose gentler weather.)"
        )
    return "(No story: this combination does not form a reasonable fable.)"


def introduce(world: World, hero: Entity, hero_cfg: HeroKind, recipient_cfg: RecipientKind, weather: WeatherKind) -> None:
    world.say(
        f"In {weather.label}, there lived {hero_cfg.title} in {hero_cfg.home}. "
        f"{weather.effect}."
    )
    world.say(
        f"One day, {hero.id} heard that {recipient_cfg.label} {recipient_cfg.need}."
    )


def gift_shamrock(world: World, hero: Entity, recipient_cfg: RecipientKind) -> None:
    shamrock = world.get("shamrock")
    hero.memes["care"] += 1
    shamrock.meters["fresh"] += 1
    world.say(
        f"So {hero.id} chose the greenest shamrock from the clover patch and said, "
        f'"May this little leaf bless {recipient_cfg.label} with comfort."'
    )


def fear_route(world: World, hero: Entity, route: RouteKind) -> None:
    hero.memes["fear"] += 1
    world.say(
        f"But the way led by {route.label}, where {route.danger}. "
        f"{route.obstacle} made even a kind errand feel large."
    )


def flashback(world: World, hero: Entity, memory: MemoryKind, recipient_cfg: RecipientKind) -> None:
    hero.memes["remembering"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then a memory came back to {hero.id}. Long ago, {recipient_cfg.label} "
        f"{memory.gift}."
    )
    world.say(
        f"{memory.warmth} {memory.lesson}"
    )


def choose_bravery(world: World, hero: Entity, helper_cfg: HelperKind, route: RouteKind, weather: WeatherKind) -> None:
    pred = predict_success(hero, route, helper_cfg, weather, world.facts["memory_cfg"])
    world.facts["predicted_support"] = pred["support"]
    world.facts["predicted_risk"] = pred["risk"]
    if helper_cfg.sense >= SENSE_MIN:
        world.say(
            f"Just then, {helper_cfg.label} came near and {helper_cfg.action}. "
            f"{helper_cfg.label.capitalize()} {helper_cfg.courage}."
        )
        hero.memes["trust"] += 1
        hero.memes["bravery"] += 1
    else:
        world.say(
            f"{helper_cfg.label.capitalize()} drifted nearby, yet even {hero.id} could see that "
            f"this would not make the hard place safe."
        )
    if weather.easy:
        world.say(
            f"The gentle weather helped too, and the small traveler felt {world.facts['hero_cfg'].brave_image}."
        )
        hero.memes["bravery"] += 1
    else:
        world.say(
            "The wind still muttered, but it no longer sounded like a command to turn back."
        )
    world.say(
        f'So {hero.id} whispered, "Bravery is not a loud thing. It is a kind thing that keeps going."'
    )


def cross_route(world: World, hero: Entity, route: RouteKind) -> None:
    shamrock = world.get("shamrock")
    hero.meters["travel"] += 1
    shamrock.meters["carried"] += 1
    world.say(
        f"{hero.id.capitalize()} {route.crossing}, holding the shamrock carefully so not one leaf would tear."
    )


def deliver(world: World, hero: Entity, recipient_cfg: RecipientKind) -> None:
    shamrock = world.get("shamrock")
    shamrock.meters["delivered"] += 1
    propagate(world, narrate=False)
    recipient = world.get("recipient")
    world.say(
        f"At last {hero.id} reached {recipient_cfg.label} and laid the shamrock down. "
        f'"I brought this to bless you," {hero.pronoun()} said.'
    )
    world.say(
        f"At once, {recipient_cfg.label} {recipient_cfg.blessing_result} {recipient_cfg.thanks}"
    )
    if recipient.meters["blessed"] >= THRESHOLD:
        world.say(
            "The meadow seemed brighter, as if kindness itself had lifted a lantern there."
        )


def home_ending(world: World, hero: Entity, route: RouteKind) -> None:
    hero.memes["relief"] += 1
    hero.memes["joy"] += 1
    world.say(
        f"When {hero.id} turned toward home again, {route.label} no longer seemed like a place of fear. "
        f"It was only a path that had been crossed for love."
    )
    world.say(
        "And from that day on, the small folk of the meadow would say that even a shamrock may bless a sorrowful heart, "
        "when a brave one carries it."
    )


def tell(
    hero_cfg: HeroKind,
    recipient_cfg: RecipientKind,
    route_cfg: RouteKind,
    helper_cfg: HelperKind,
    weather_cfg: WeatherKind,
    memory_cfg: MemoryKind,
    hero_name: str = "Pip",
) -> World:
    world = World()
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_cfg.species,
        label=hero_cfg.species,
        role="hero",
        tags=set(hero_cfg.tags),
    ))
    recipient = world.add(Entity(
        id="recipient",
        kind="character",
        type=recipient_cfg.id,
        label=recipient_cfg.label,
        role="recipient",
        tags=set(recipient_cfg.tags),
    ))
    shamrock = world.add(Entity(
        id="shamrock",
        kind="thing",
        type="shamrock",
        label="shamrock",
        phrase="a green shamrock",
        role="gift",
        tags={"shamrock", "bless"},
    ))
    helper = world.add(Entity(
        id="helper",
        kind="character" if helper_cfg.id in {"turtle", "deer", "butterfly"} else "thing",
        type=helper_cfg.id,
        label=helper_cfg.label,
        role="helper",
        tags=set(helper_cfg.tags),
    ))
    hero.memes["bravery"] = 1.0
    world.facts.update(
        hero=hero,
        hero_cfg=hero_cfg,
        recipient=recipient,
        recipient_cfg=recipient_cfg,
        shamrock=shamrock,
        helper=helper,
        helper_cfg=helper_cfg,
        route_cfg=route_cfg,
        weather_cfg=weather_cfg,
        memory_cfg=memory_cfg,
    )

    introduce(world, hero, hero_cfg, recipient_cfg, weather_cfg)
    gift_shamrock(world, hero, recipient_cfg)

    world.para()
    fear_route(world, hero, route_cfg)
    flashback(world, hero, memory_cfg, recipient_cfg)
    choose_bravery(world, hero, helper_cfg, route_cfg, weather_cfg)

    world.para()
    cross_route(world, hero, route_cfg)
    deliver(world, hero, recipient_cfg)

    world.para()
    home_ending(world, hero, route_cfg)

    world.facts["success"] = shamrock.meters["delivered"] >= THRESHOLD and recipient.meters["blessed"] >= THRESHOLD
    world.facts["flashback_used"] = hero.memes["remembering"] >= THRESHOLD
    world.facts["brave"] = hero.memes["bravery"] >= THRESHOLD
    return world


# Per-world parameters.
@dataclass
class StoryParams:
    hero: str
    recipient: str
    route: str
    helper: str
    weather: str
    memory: str
    name: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "shamrock": [
        (
            "What is a shamrock?",
            "A shamrock is a small green clover leaf. In stories, people sometimes treat it as a sign of luck, hope, or blessing."
        )
    ],
    "bless": [
        (
            "What does bless mean?",
            "To bless someone means to wish good, comfort, or peace for them. In a fable, a blessing often shows kindness made visible."
        )
    ],
    "bravery": [
        (
            "What is bravery?",
            "Bravery means doing the right thing even when you feel afraid. It does not mean having no fear at all."
        )
    ],
    "flashback": [
        (
            "What is a flashback in a story?",
            "A flashback is a memory of something that happened earlier. Writers use it to show why a character makes a choice now."
        )
    ],
    "brook": [
        (
            "Why can a brook feel scary to a small animal?",
            "Even a small stream can seem big when the stones are slippery and the water is quick. What feels easy for a large creature can feel daring for a tiny one."
        )
    ],
    "thicket": [
        (
            "What is a thicket?",
            "A thicket is a place where bushes and stems grow close together. It can feel dark and tangled inside."
        )
    ],
    "marsh": [
        (
            "Why is a marsh hard to cross?",
            "A marsh has wet ground that can wobble under your feet. You have to find the firm places carefully."
        )
    ],
    "help": [
        (
            "Why is asking for help sometimes part of bravery?",
            "Because bravery is not only pushing forward alone. Sometimes the brave choice is accepting steady help and using good sense."
        )
    ],
}
KNOWLEDGE_ORDER = ["shamrock", "bless", "flashback", "bravery", "brook", "thicket", "marsh", "help"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    recipient_cfg = f["recipient_cfg"]
    route_cfg = f["route_cfg"]
    return [
        'Write a short fable for a 3-to-5-year-old that includes the words "shamrock" and "bless".',
        f"Tell a gentle animal fable where {hero.id} carries a shamrock to {recipient_cfg.label}, uses a flashback to remember an old kindness, and chooses bravery on the way through {route_cfg.label}.",
        "Write a happy-ending meadow fable where a small creature feels afraid, remembers something good from the past, and then does a brave kind deed.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    hero_cfg = f["hero_cfg"]
    recipient_cfg = f["recipient_cfg"]
    route_cfg = f["route_cfg"]
    helper_cfg = f["helper_cfg"]
    memory_cfg = f["memory_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, {hero_cfg.title}, who carried a shamrock on a kind errand. The story also follows {recipient_cfg.label}, who needed comfort."
        ),
        (
            "Why did the hero take a shamrock?",
            f"{hero.id} wanted the shamrock to bless {recipient_cfg.label} with comfort. The shamrock was a small gift, but it carried a large wish of kindness."
        ),
        (
            f"What made {route_cfg.label} feel frightening?",
            f"It felt frightening because {route_cfg.danger}. That hard place made the kind errand seem bigger than the hero at first."
        ),
    ]
    if f.get("flashback_used"):
        qa.append(
            (
                "What was the flashback, and why did it matter?",
                f"The flashback was the memory that {recipient_cfg.label} {memory_cfg.gift}. It mattered because remembering old kindness gave {hero.id} a reason to be brave now."
            )
        )
    qa.append(
        (
            f"How did {hero.id} become brave enough to go on?",
            f"{hero.id} remembered the past kindness and decided that courage should serve love. {helper_cfg.label.capitalize()} also helped, which turned fear into a steadier kind of bravery."
        )
    )
    if f.get("success"):
        qa.append(
            (
                "How did the story end?",
                f"It ended happily: {hero.id} reached {recipient_cfg.label}, and the shamrock seemed to bless them with comfort. The return path no longer looked so frightening, because courage had changed what the hero saw."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"shamrock", "bless", "flashback", "bravery", "help"}
    route_id = f["route_cfg"].id
    if route_id in {"brook", "thicket", "marsh"}:
        tags.add(route_id)
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
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        lines.append(f"  {ent.id:10} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        hero="rabbit",
        recipient="lamb",
        route="brook",
        helper="turtle",
        weather="dew",
        memory="saved_nest",
        name="Pip",
    ),
    StoryParams(
        hero="mouse",
        recipient="hedgehog",
        route="thicket",
        helper="deer",
        weather="sunny",
        memory="shared_seed",
        name="Moss",
    ),
    StoryParams(
        hero="wren",
        recipient="fox_cub",
        route="marsh",
        helper="turtle",
        weather="sunny",
        memory="shelter_rain",
        name="Tansy",
    ),
]


ASP_RULES = r"""
route_possible(R) :- route(R), allowed(R).
helper_ok(R, H)   :- helper(H), route(R), not needs_help(R), sense(H, _).
helper_ok(R, H)   :- helper(H), route(R), needs_help(R), sense(H, S), sense_min(M), S >= M.
windy_marsh_ok(H) :- sense(H, S), S >= 3.

valid(Hero, Rec, Route, Helper, Weather, Memory) :-
    hero(Hero), recipient(Rec), route(Route), helper(Helper), weather(Weather), memory(Memory),
    route_possible(Route), helper_ok(Route, Helper).

:- valid(_, _, marsh, Helper, windy, _), not windy_marsh_ok(Helper).

support(1) :- chosen_helper(H), sense(H, S), sense_min(M), S >= M.
support(0) :- chosen_helper(H), sense(H, S), sense_min(M), S < M.
weather_bonus(1) :- chosen_weather(W), easy(W).
weather_bonus(0) :- chosen_weather(W), not easy(W).
route_bonus(1) :- chosen_route(R), challenge(R, C), C <= 2.
route_bonus(0) :- chosen_route(R), challenge(R, C), C > 2.
memory_bonus(1) :- chosen_memory(_).
courage(2 + S + W + R + M) :- support(S), weather_bonus(W), route_bonus(R), memory_bonus(M).
enough_bravery :- chosen_route(R), challenge(R, C), courage(V), V >= C + 2.
outcome(happy) :- enough_bravery.
"""

def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for hid in HEROES:
        lines.append(asp.fact("hero", hid))
    for rid in RECIPIENTS:
        lines.append(asp.fact("recipient", rid))
    for rid, route in ROUTES.items():
        lines.append(asp.fact("route", rid))
        lines.append(asp.fact("challenge", rid, route.challenge))
        if route.needs_help:
            lines.append(asp.fact("needs_help", rid))
        if route.allowed:
            lines.append(asp.fact("allowed", rid))
    for hid, helper in HELPERS.items():
        lines.append(asp.fact("helper", hid))
        lines.append(asp.fact("sense", hid, helper.sense))
    for wid, weather in WEATHERS.items():
        lines.append(asp.fact("weather", wid))
        if weather.easy:
            lines.append(asp.fact("easy", wid))
    for mid in MEMORIES:
        lines.append(asp.fact("memory", mid))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/6."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join([
        asp.fact("chosen_route", params.route),
        asp.fact("chosen_helper", params.helper),
        asp.fact("chosen_weather", params.weather),
        asp.fact("chosen_memory", params.memory),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def outcome_of(params: StoryParams) -> str:
    route = ROUTES[params.route]
    helper = HELPERS[params.helper]
    weather = WEATHERS[params.weather]
    memory = MEMORIES[params.memory]
    brave = courage_total(route, helper, weather, memory)
    return "happy" if brave >= route.challenge + 2.0 else "?"


def _assert_params_exist(params: StoryParams) -> None:
    if params.hero not in HEROES:
        raise StoryError(f"(Unknown hero '{params.hero}'.)")
    if params.recipient not in RECIPIENTS:
        raise StoryError(f"(Unknown recipient '{params.recipient}'.)")
    if params.route not in ROUTES:
        raise StoryError(f"(Unknown route '{params.route}'.)")
    if params.helper not in HELPERS:
        raise StoryError(f"(Unknown helper '{params.helper}'.)")
    if params.weather not in WEATHERS:
        raise StoryError(f"(Unknown weather '{params.weather}'.)")
    if params.memory not in MEMORIES:
        raise StoryError(f"(Unknown memory '{params.memory}'.)")


def asp_verify() -> int:
    rc = 0
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: ASP gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    cases = list(CURATED)
    for s in range(30):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(s))
            params.seed = s
            cases.append(params)
        except StoryError:
            continue
    bad = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story or "shamrock" not in sample.story or "bless" not in sample.story:
            raise StoryError("smoke test story missing required seed words")
        print("OK: smoke test story generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Storyworld: a shamrock, a blessing, a flashback, and a brave happy fable."
    )
    ap.add_argument("--hero", choices=HEROES)
    ap.add_argument("--recipient", choices=RECIPIENTS)
    ap.add_argument("--route", choices=ROUTES)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--weather", choices=WEATHERS)
    ap.add_argument("--memory", choices=MEMORIES)
    ap.add_argument("--name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combinations from ASP")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.route is not None:
        route = ROUTES[args.route]
        if not route.allowed:
            raise StoryError(explain_rejection(route))
    if args.route is not None and args.helper is not None:
        route = ROUTES[args.route]
        helper = HELPERS[args.helper]
        weather = WEATHERS[args.weather] if args.weather else None
        if route.needs_help and helper.sense < SENSE_MIN:
            raise StoryError(explain_rejection(route, helper, weather))
        if route.id == "marsh" and weather is not None and weather.id == "windy" and helper.sense < 3:
            raise StoryError(explain_rejection(route, helper, weather))

    combos = [
        combo for combo in valid_combos()
        if (args.hero is None or combo[0] == args.hero)
        and (args.recipient is None or combo[1] == args.recipient)
        and (args.route is None or combo[2] == args.route)
        and (args.helper is None or combo[3] == args.helper)
        and (args.weather is None or combo[4] == args.weather)
        and (args.memory is None or combo[5] == args.memory)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    hero_id, recipient_id, route_id, helper_id, weather_id, memory_id = rng.choice(sorted(combos))
    hero_cfg = HEROES[hero_id]
    default_names = {
        "rabbit": ["Pip", "Clover", "Merry"],
        "mouse": ["Moss", "Nib", "Poppy"],
        "wren": ["Tansy", "Wisp", "Bramble"],
    }
    name = args.name or rng.choice(default_names[hero_cfg.id])
    return StoryParams(
        hero=hero_id,
        recipient=recipient_id,
        route=route_id,
        helper=helper_id,
        weather=weather_id,
        memory=memory_id,
        name=name,
    )


def generate(params: StoryParams) -> StorySample:
    _assert_params_exist(params)
    if not valid_combo(params.hero, params.recipient, params.route, params.helper, params.weather, params.memory):
        route = ROUTES[params.route]
        helper = HELPERS[params.helper]
        weather = WEATHERS[params.weather]
        raise StoryError(explain_rejection(route, helper, weather))
    world = tell(
        hero_cfg=HEROES[params.hero],
        recipient_cfg=RECIPIENTS[params.recipient],
        route_cfg=ROUTES[params.route],
        helper_cfg=HELPERS[params.helper],
        weather_cfg=WEATHERS[params.weather],
        memory_cfg=MEMORIES[params.memory],
        hero_name=params.name,
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
        print(asp_program("", "#show valid/6.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (hero, recipient, route, helper, weather, memory) combos:\n")
        for combo in combos:
            print("  " + " ".join(f"{part:10}" for part in combo))
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
            header = f"### {p.name}: {p.hero} carries shamrock by {p.route} to {p.recipient}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
