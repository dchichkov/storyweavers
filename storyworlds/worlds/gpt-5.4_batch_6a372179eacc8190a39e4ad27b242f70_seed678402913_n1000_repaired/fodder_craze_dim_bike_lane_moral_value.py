#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/fodder_craze_dim_bike_lane_moral_value.py
====================================================================

A standalone story world for a rhyming bike-lane tale about bird fodder,
crowding, and learning to share safely.

Seed requirements rebuilt as world state
----------------------------------------
Words: fodder, craze-dim
Setting: bike lane
Features: Moral Value, Lesson Learned, Sharing
Style: Rhyming Story

Premise
-------
Two children roll along a bike lane and find a little cup of bird fodder.
One child wants to keep the fun all to themself and sprinkles the feed on the
painted lane. Birds crowd in, the lane turns risky, and a ringing bell makes
the problem feel real. The turn comes when the child chooses to share the
fodder and move it off the lane to a safer feeding spot. The ending image proves
the change: the birds peck at the side, the lane clears, and the children ride
on together.

Reasonableness gate
-------------------
Not every bird/feed/spot combination makes sense. This world only allows stories
where:
- the chosen feed is suitable for the chosen birds, and
- the feeding spot is *off the bike lane*, and
- the chosen birds plausibly gather at that kind of side spot.

An explicit invalid choice raises StoryError with a plain explanation.

Run it
------
python storyworlds/worlds/gpt-5.4/fodder_craze_dim_bike_lane_moral_value.py
python storyworlds/worlds/gpt-5.4/fodder_craze_dim_bike_lane_moral_value.py --bird sparrows --feed oat_fodder
python storyworlds/worlds/gpt-5.4/fodder_craze_dim_bike_lane_moral_value.py --spot center_line
python storyworlds/worlds/gpt-5.4/fodder_craze_dim_bike_lane_moral_value.py --all
python storyworlds/worlds/gpt-5.4/fodder_craze_dim_bike_lane_moral_value.py -n 5 --seed 7 --qa
python storyworlds/worlds/gpt-5.4/fodder_craze_dim_bike_lane_moral_value.py --verify
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
# This file lives under storyworlds/worlds/gpt-5.4/, so we add storyworlds/ to
# the path by going up three directories from this file.
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
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Ride:
    id: str
    noun: str
    verb: str
    sound: str
    line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Bird:
    id: str
    label: str
    flock_word: str
    move_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Feed:
    id: str
    label: str
    phrase: str
    birds: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Spot:
    id: str
    label: str
    phrase: str
    off_lane: bool = True
    birds: set[str] = field(default_factory=set)
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


def _r_lane_crowd(world: World) -> list[str]:
    lane = world.get("lane")
    flock = world.get("flock")
    if lane.meters["feed"] < THRESHOLD:
        return []
    sig = ("lane_crowd",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    flock.meters["on_lane"] += 1
    lane.meters["clutter"] += 1
    lane.meters["danger"] += 1
    world.get("hero").memes["alarm"] += 1
    world.get("friend").memes["worry"] += 1
    return ["__crowd__"]


def _r_safe_spot(world: World) -> list[str]:
    spot = world.get("spot")
    lane = world.get("lane")
    flock = world.get("flock")
    if spot.meters["feed"] < THRESHOLD or not spot.attrs.get("off_lane", False):
        return []
    sig = ("safe_spot",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    flock.meters["off_lane"] += 1
    lane.meters["danger"] = 0.0
    lane.meters["clutter"] = 0.0
    world.get("hero").memes["kindness"] += 1
    world.get("hero").memes["relief"] += 1
    world.get("friend").memes["joy"] += 1
    return ["__safe__"]


CAUSAL_RULES: list[Rule] = [
    Rule(name="lane_crowd", tag="physical", apply=_r_lane_crowd),
    Rule(name="safe_spot", tag="physical", apply=_r_safe_spot),
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


def feed_fits(feed: Feed, bird: Bird) -> bool:
    return bird.id in feed.birds


def safe_spot_for(spot: Spot, bird: Bird) -> bool:
    return spot.off_lane and bird.id in spot.birds


def valid_combo(ride_id: str, bird_id: str, feed_id: str, spot_id: str) -> bool:
    if ride_id not in RIDES or bird_id not in BIRDS or feed_id not in FEEDS or spot_id not in SPOTS:
        return False
    return feed_fits(FEEDS[feed_id], BIRDS[bird_id]) and safe_spot_for(SPOTS[spot_id], BIRDS[bird_id])


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for ride_id in RIDES:
        for bird_id, bird in BIRDS.items():
            for feed_id, feed in FEEDS.items():
                for spot_id, spot in SPOTS.items():
                    if feed_fits(feed, bird) and safe_spot_for(spot, bird):
                        combos.append((ride_id, bird_id, feed_id, spot_id))
    return combos


def explain_rejection(bird: Bird, feed: Feed, spot: Spot) -> str:
    if not feed_fits(feed, bird):
        return (
            f"(No story: {feed.label} is not a sensible treat for {bird.label}. "
            f"Pick feed that these birds would actually peck.)"
        )
    if not spot.off_lane:
        return (
            f"(No story: {spot.label} sits in the bike lane itself. The lesson here "
            f"requires moving the fodder off the lane, not feeding birds where wheels roll.)"
        )
    if bird.id not in spot.birds:
        return (
            f"(No story: {bird.label} would not sensibly gather at {spot.label}. "
            f"Pick a side spot that fits those birds.)"
        )
    return "(No story: this bike-lane feeding plan is not reasonable.)"


def predict_lane_crowd(world: World) -> dict:
    sim = world.copy()
    toss_on_lane(sim, narrate=False)
    lane = sim.get("lane")
    flock = sim.get("flock")
    return {
        "danger": lane.meters["danger"],
        "clutter": lane.meters["clutter"],
        "birds_on_lane": flock.meters["on_lane"],
    }


def introduce(world: World, hero: Entity, friend: Entity, ride: Ride) -> None:
    hero.memes["joy"] += 1
    friend.memes["joy"] += 1
    world.say(
        f"In the craze-dim dawn by the bike lane bright, {hero.id} rolled {ride.line} with {friend.id} in light. "
        f"{ride.sound.capitalize()} went the wheels in a whispery way, and the lane hummed soft at the start of the day."
    )


def find_fodder(world: World, hero: Entity, friend: Entity, feed: Feed, bird: Bird) -> None:
    world.say(
        f"By the curb they spotted {feed.phrase}, a tiny cup of fodder for {bird.label} that peeped nearby. "
        f'"Let us feed them!" laughed {hero.id}. "{bird.flock_word.capitalize()} in a fluttering sky!"'
    )


def hoard_idea(world: World, hero: Entity, friend: Entity) -> None:
    hero.memes["greed"] += 1
    friend.memes["care"] += 1
    world.say(
        f"But {hero.id} hugged the little cup tight. "
        f'"I want the whole happy cloud for me, the biggest bird dance in sight!"'
    )


def friend_warning(world: World, hero: Entity, friend: Entity, bird: Bird) -> None:
    pred = predict_lane_crowd(world)
    world.facts["predicted_danger"] = pred["danger"]
    friend.memes["worry"] += 1
    world.say(
        f'{friend.id} pointed down at the painted track. '
        f'"Not in the lane," {friend.pronoun()} said. '
        f'"If the {bird.label} crowd where the wheels come back, someone may wobble instead."'
    )


def toss_on_lane(world: World, narrate: bool = True) -> None:
    lane = world.get("lane")
    lane.meters["feed"] += 1
    propagate(world, narrate=narrate)


def temptation(world: World, hero: Entity, bird: Bird, feed: Feed) -> None:
    toss_on_lane(world)
    world.say(
        f"Still {hero.id} shook out {feed.label} in a stripe on the lane-side seam, "
        f"and down came the {bird.flock_word} in a hopping, pecking stream."
    )


def bell_turn(world: World, hero: Entity, friend: Entity, ride: Ride) -> None:
    lane = world.get("lane")
    hero.memes["alarm"] += 1
    friend.memes["alarm"] += 1
    lane.meters["near_miss"] += 1
    world.say(
        f"Then ring-ring-rang came a rider behind, and {hero.id} pulled {ride.verb} with a startled mind. "
        f"{friend.id} gripped the bar, and the birds bounced wide; the crowded lane was no place to ride."
    )


def choose_share(world: World, hero: Entity, friend: Entity) -> None:
    hero.memes["greed"] = 0.0
    hero.memes["sharing"] += 1
    friend.memes["trust"] += 1
    world.say(
        f"{hero.id} looked at {friend.id}, then down at the line. "
        f'"This fun is not fair if it tangles the ride. Let us share and move aside."'
    )


def move_and_share(world: World, hero: Entity, friend: Entity, bird: Bird, spot: Spot, feed: Feed) -> None:
    lane = world.get("lane")
    lane.meters["feed"] = 0.0
    spot_ent = world.get("spot")
    spot_ent.meters["feed"] += 1
    propagate(world, narrate=False)
    world.say(
        f"So they carried the fodder to {spot.phrase}, where the lane stayed clear and calm. "
        f"They tipped it out together, palm by palm, and the {bird.label} came to peck without harm."
    )


def lesson(world: World, hero: Entity, friend: Entity) -> None:
    hero.memes["lesson"] += 1
    friend.memes["lesson"] += 1
    world.say(
        f'"A shared small cup can still be grand," said {friend.id} with a grin so warm. '
        f'"When kindness leads the game along, the joy stays bright and nobody meets harm."'
    )


def ending(world: World, hero: Entity, friend: Entity, ride: Ride, bird: Bird, spot: Spot) -> None:
    hero.memes["joy"] += 1
    friend.memes["joy"] += 1
    world.say(
        f"Soon the bike lane shone in an easy line, the {bird.label} pecked softly by {spot.label}, fine. "
        f"Side by side rode {hero.id} and {friend.id} with hearts set right to share, and share again, in morning light."
    )


def tell(
    ride: Ride,
    bird: Bird,
    feed: Feed,
    spot: Spot,
    hero_name: str = "Tess",
    hero_gender: str = "girl",
    friend_name: str = "Milo",
    friend_gender: str = "boy",
) -> World:
    world = World()
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender, role="hero", traits=["eager"]))
    friend = world.add(Entity(id=friend_name, kind="character", type=friend_gender, role="friend", traits=["steady"]))
    lane = world.add(Entity(id="lane", type="place", label="bike lane", attrs={"setting": "bike lane"}))
    flock = world.add(Entity(id="flock", type="birds", label=bird.label, attrs={"bird": bird.id}))
    spot_ent = world.add(
        Entity(
            id="spot",
            type="place",
            label=spot.label,
            phrase=spot.phrase,
            attrs={"off_lane": spot.off_lane},
        )
    )

    introduce(world, hero, friend, ride)
    find_fodder(world, hero, friend, feed, bird)

    world.para()
    hoard_idea(world, hero, friend)
    friend_warning(world, hero, friend, bird)

    world.para()
    temptation(world, hero, bird, feed)
    bell_turn(world, hero, friend, ride)

    world.para()
    choose_share(world, hero, friend)
    move_and_share(world, hero, friend, bird, spot, feed)
    lesson(world, hero, friend)
    ending(world, hero, friend, ride, bird, spot)

    world.facts.update(
        hero=hero,
        friend=friend,
        lane=lane,
        flock=flock,
        ride=ride,
        bird=bird,
        feed=feed,
        spot_cfg=spot,
        spot=spot_ent,
        shared=hero.memes["sharing"] >= THRESHOLD,
        learned=hero.memes["lesson"] >= THRESHOLD,
        near_miss=lane.meters["near_miss"] >= THRESHOLD,
        lane_safe=lane.meters["danger"] < THRESHOLD,
    )
    return world


@dataclass
class StoryParams:
    ride: str
    bird: str
    feed: str
    spot: str
    hero_name: str
    hero_gender: str
    friend_name: str
    friend_gender: str
    seed: Optional[int] = None


RIDES = {
    "bike": Ride(
        id="bike",
        noun="bike",
        verb="the bike aside",
        sound="whirr",
        line="a blue bike",
        tags={"bike", "bike_lane"},
    ),
    "scooter": Ride(
        id="scooter",
        noun="scooter",
        verb="the scooter aside",
        sound="zip",
        line="a red scooter",
        tags={"scooter", "bike_lane"},
    ),
}

BIRDS = {
    "pigeons": Bird(
        id="pigeons",
        label="pigeons",
        flock_word="pigeons",
        move_line="They bob and peck in busy little bands.",
        tags={"birds", "pigeons"},
    ),
    "sparrows": Bird(
        id="sparrows",
        label="sparrows",
        flock_word="sparrows",
        move_line="They skip in quick little hops.",
        tags={"birds", "sparrows"},
    ),
    "doves": Bird(
        id="doves",
        label="doves",
        flock_word="doves",
        move_line="They flutter down in pale, soft sweeps.",
        tags={"birds", "doves"},
    ),
}

FEEDS = {
    "seed_fodder": Feed(
        id="seed_fodder",
        label="seed fodder",
        phrase="a paper cup of seed fodder",
        birds={"pigeons", "sparrows", "doves"},
        tags={"fodder", "sharing", "bird_feed"},
    ),
    "oat_fodder": Feed(
        id="oat_fodder",
        label="oat fodder",
        phrase="a folded pouch of oat fodder",
        birds={"pigeons", "doves"},
        tags={"fodder", "sharing", "bird_feed"},
    ),
    "crumb_fodder": Feed(
        id="crumb_fodder",
        label="crumb fodder",
        phrase="a tiny tin of crumb fodder",
        birds={"sparrows", "pigeons"},
        tags={"fodder", "sharing", "bird_feed"},
    ),
}

SPOTS = {
    "bench_side": Spot(
        id="bench_side",
        label="the bench side",
        phrase="the bench side by the hedge",
        off_lane=True,
        birds={"pigeons", "sparrows", "doves"},
        tags={"safe_spot", "sharing"},
    ),
    "tree_square": Spot(
        id="tree_square",
        label="the tree square",
        phrase="the little tree square beside the curb",
        off_lane=True,
        birds={"sparrows", "doves"},
        tags={"safe_spot", "sharing"},
    ),
    "grassy_edge": Spot(
        id="grassy_edge",
        label="the grassy edge",
        phrase="the grassy edge beyond the painted line",
        off_lane=True,
        birds={"pigeons", "sparrows", "doves"},
        tags={"safe_spot", "sharing"},
    ),
    "center_line": Spot(
        id="center_line",
        label="the center line",
        phrase="the center line of the bike lane",
        off_lane=False,
        birds={"pigeons", "sparrows", "doves"},
        tags={"unsafe_spot"},
    ),
}

GIRL_NAMES = ["Tess", "Mina", "Lila", "Nora", "Ava", "Ruby", "Cora", "June"]
BOY_NAMES = ["Milo", "Ben", "Theo", "Eli", "Noah", "Finn", "Jude", "Owen"]

KNOWLEDGE = {
    "bike_lane": [
        (
            "What is a bike lane?",
            "A bike lane is a part of the street marked for bicycles and similar small wheels. People should try to keep it clear so riders can move safely.",
        )
    ],
    "birds": [
        (
            "Why should people avoid feeding birds in the middle of a bike lane?",
            "Birds may crowd where the food is, and riders might have to swerve around them. Feeding birds off to the side keeps both birds and people safer.",
        )
    ],
    "sharing": [
        (
            "What does sharing mean?",
            "Sharing means letting someone else enjoy part of what you have. It can turn a grabby moment into a kinder one for everyone.",
        )
    ],
    "fodder": [
        (
            "What does fodder mean?",
            "Fodder means food given to animals. In this story, the fodder is a little treat for birds to peck.",
        )
    ],
    "pigeons": [
        (
            "What do pigeons do when they find food?",
            "Pigeons often walk and bob toward it together. They peck quickly, so they can crowd a small place fast.",
        )
    ],
    "sparrows": [
        (
            "How do sparrows move when they look for crumbs?",
            "Sparrows often hop in quick little bursts. They dart in and out, which can make a busy path feel even busier.",
        )
    ],
    "doves": [
        (
            "Why do doves like quiet places to peck?",
            "Doves are calmer birds and do better where people are not rushing past them. A quiet side spot helps them feed without panic.",
        )
    ],
    "safe_spot": [
        (
            "Why is a side spot better than the lane itself?",
            "A side spot lets the birds eat without blocking moving wheels. It keeps the path clear and shows thoughtful care.",
        )
    ],
}
KNOWLEDGE_ORDER = ["bike_lane", "birds", "sharing", "fodder", "pigeons", "sparrows", "doves", "safe_spot"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    bird = f["bird"]
    ride = f["ride"]
    return [
        'Write a short rhyming story for a 3-to-5-year-old set in a bike lane that includes the words "fodder" and "craze-dim".',
        f"Tell a gentle moral story where {hero.id} and {friend.id} find bird fodder while riding a {ride.noun}, make an unsafe choice, and then learn to share in a safer way.",
        f"Write a child-facing poem-story about {bird.label} crowding a bike lane until two friends move the food aside and learn that sharing should never block someone else's ride.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    bird = f["bird"]
    ride = f["ride"]
    feed = f["feed"]
    spot = f["spot_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id} and {friend.id}, two children rolling in the bike lane. They found {feed.phrase} and had to decide what kind of fun was also kind.",
        ),
        (
            f"What problem started when {hero.id} shook the fodder onto the lane?",
            f"The {bird.label} hurried right onto the bike lane to peck at it, so the lane became crowded and risky. That mattered because moving wheels and hopping birds do not mix well in the same narrow place.",
        ),
        (
            f"Why did {friend.id} warn {hero.id}?",
            f"{friend.id} could see that birds in the lane might make someone wobble or swerve. The warning came before the bell, because {friend.id} noticed the risk early.",
        ),
    ]
    if f.get("near_miss"):
        qa.append(
            (
                "What changed the story from a greedy game into a lesson?",
                f"A rider rang a bell from behind, and the crowded lane suddenly felt real and unsafe. That near miss helped {hero.id} understand that keeping all the fun was not worth making the path dangerous.",
            )
        )
    if f.get("shared"):
        qa.append(
            (
                f"How did {hero.id} solve the problem?",
                f"{hero.id} chose to share the fodder with {friend.id} and carry it to {spot.phrase}. That moved the birds off the lane and let the fun continue without blocking the ride.",
            )
        )
    if f.get("learned"):
        qa.append(
            (
                "What lesson did the children learn?",
                f"They learned that sharing is not only about splitting a treat; it is also about making room for other people. A kind choice kept the birds fed and the bike lane safe at the same time.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"bike_lane", "birds", "sharing", "fodder", "safe_spot"}
    tags |= set(world.facts["bird"].tags)
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
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if ent.role:
            bits.append(f"role={ent.role}")
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        ride="bike",
        bird="pigeons",
        feed="seed_fodder",
        spot="bench_side",
        hero_name="Tess",
        hero_gender="girl",
        friend_name="Milo",
        friend_gender="boy",
    ),
    StoryParams(
        ride="scooter",
        bird="sparrows",
        feed="crumb_fodder",
        spot="grassy_edge",
        hero_name="Ben",
        hero_gender="boy",
        friend_name="Lila",
        friend_gender="girl",
    ),
    StoryParams(
        ride="bike",
        bird="doves",
        feed="oat_fodder",
        spot="tree_square",
        hero_name="Nora",
        hero_gender="girl",
        friend_name="Jude",
        friend_gender="boy",
    ),
]


ASP_RULES = r"""
fits_feed(Bird, Feed) :- bird(Bird), feed(Feed), likes(Feed, Bird).
safe_spot(Bird, Spot) :- bird(Bird), spot(Spot), off_lane(Spot), welcomes(Spot, Bird).
valid(Ride, Bird, Feed, Spot) :- ride(Ride), fits_feed(Bird, Feed), safe_spot(Bird, Spot).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for ride_id in RIDES:
        lines.append(asp.fact("ride", ride_id))
    for bird_id in BIRDS:
        lines.append(asp.fact("bird", bird_id))
    for feed_id, feed in FEEDS.items():
        lines.append(asp.fact("feed", feed_id))
        for bird_id in sorted(feed.birds):
            lines.append(asp.fact("likes", feed_id, bird_id))
    for spot_id, spot in SPOTS.items():
        lines.append(asp.fact("spot", spot_id))
        if spot.off_lane:
            lines.append(asp.fact("off_lane", spot_id))
        for bird_id in sorted(spot.birds):
            lines.append(asp.fact("welcomes", spot_id, bird_id))
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
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH between clingo and valid_combos():")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    smoke_cases = list(CURATED)
    try:
        smoke_cases.append(resolve_params(build_parser().parse_args([]), random.Random(7)))
    except StoryError as err:
        rc = 1
        print(f"SMOKE setup failed: {err}")

    for params in smoke_cases:
        try:
            sample = generate(params)
            if not sample.story.strip():
                raise StoryError("generated empty story")
            emit(sample, trace=False, qa=False, header="")
        except Exception as err:  # pragma: no cover - verify path
            rc = 1
            print(f"SMOKE generation failed for {params}: {err}")
            break

    if rc == 0:
        print(f"OK: smoke-tested {len(smoke_cases)} generated stories.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Rhyming bike-lane story world about fodder, sharing, and choosing a safer place."
    )
    ap.add_argument("--ride", choices=RIDES)
    ap.add_argument("--bird", choices=BIRDS)
    ap.add_argument("--feed", choices=FEEDS)
    ap.add_argument("--spot", choices=SPOTS)
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--friend-name")
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combinations from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.bird and args.feed:
        bird = BIRDS[args.bird]
        feed = FEEDS[args.feed]
        spot = SPOTS[args.spot] if args.spot else next(iter(SPOTS.values()))
        if not feed_fits(feed, bird):
            raise StoryError(explain_rejection(bird, feed, spot))
    if args.bird and args.spot:
        bird = BIRDS[args.bird]
        spot = SPOTS[args.spot]
        feed = FEEDS[args.feed] if args.feed else next(iter(FEEDS.values()))
        if not safe_spot_for(spot, bird):
            raise StoryError(explain_rejection(bird, feed, spot))

    combos = [
        combo
        for combo in valid_combos()
        if (args.ride is None or combo[0] == args.ride)
        and (args.bird is None or combo[1] == args.bird)
        and (args.feed is None or combo[2] == args.feed)
        and (args.spot is None or combo[3] == args.spot)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    ride_id, bird_id, feed_id, spot_id = rng.choice(sorted(combos))

    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    hero_name = args.hero_name or _pick_name(rng, hero_gender)
    friend_gender = args.friend_gender or rng.choice(["girl", "boy"])
    friend_name = args.friend_name or _pick_name(rng, friend_gender, avoid=hero_name)

    return StoryParams(
        ride=ride_id,
        bird=bird_id,
        feed=feed_id,
        spot=spot_id,
        hero_name=hero_name,
        hero_gender=hero_gender,
        friend_name=friend_name,
        friend_gender=friend_gender,
    )


def generate(params: StoryParams) -> StorySample:
    missing = [
        name
        for name, registry in (
            ("ride", RIDES),
            ("bird", BIRDS),
            ("feed", FEEDS),
            ("spot", SPOTS),
        )
        if getattr(params, name) not in registry
    ]
    if missing:
        raise StoryError(f"(Invalid params: unknown {', '.join(missing)} choice.)")
    if not valid_combo(params.ride, params.bird, params.feed, params.spot):
        raise StoryError(
            explain_rejection(BIRDS[params.bird], FEEDS[params.feed], SPOTS[params.spot])
        )

    world = tell(
        ride=RIDES[params.ride],
        bird=BIRDS[params.bird],
        feed=FEEDS[params.feed],
        spot=SPOTS[params.spot],
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        friend_name=params.friend_name,
        friend_gender=params.friend_gender,
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
        print(f"{len(combos)} compatible (ride, bird, feed, spot) combos:\n")
        for ride_id, bird_id, feed_id, spot_id in combos:
            print(f"  {ride_id:8} {bird_id:9} {feed_id:12} {spot_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero_name} & {p.friend_name}: {p.bird} with {p.feed} at {p.spot}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
