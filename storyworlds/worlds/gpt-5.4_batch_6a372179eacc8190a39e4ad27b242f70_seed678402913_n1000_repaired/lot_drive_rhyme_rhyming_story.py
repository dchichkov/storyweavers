#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/lot_drive_rhyme_rhyming_story.py
===========================================================

A small storyworld about a child in a busy lot, a favorite toy that slips into
the drive lane, and the safe rule that keeps everyone calm. The prose is told
in a gentle rhyming-story style, but the story is driven by simulated state:
objects move, danger rises, a child lunges, a grown-up stops the dash, and the
ending depends on whether the chosen response is sensible and quick enough.

Run it
------
python storyworlds/worlds/gpt-5.4/lot_drive_rhyme_rhyming_story.py
python storyworlds/worlds/gpt-5.4/lot_drive_rhyme_rhyming_story.py --lot pumpkin_lot --thing ball
python storyworlds/worlds/gpt-5.4/lot_drive_rhyme_rhyming_story.py --thing boot
python storyworlds/worlds/gpt-5.4/lot_drive_rhyme_rhyming_story.py --response dash_and_grab
python storyworlds/worlds/gpt-5.4/lot_drive_rhyme_rhyming_story.py --all
python storyworlds/worlds/gpt-5.4/lot_drive_rhyme_rhyming_story.py -n 5 --seed 7 --qa
python storyworlds/worlds/gpt-5.4/lot_drive_rhyme_rhyming_story.py --verify
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
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class LotPlace:
    id: str
    label: str
    scene: str
    drive_phrase: str
    safe_spot: str
    lot_word: str = "lot"
    busy: int = 1
    breezy: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class LostThing:
    id: str
    label: str
    phrase: str
    motion: str
    start_play: str
    escape_line: str
    safe_use: str
    plural: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class SafePlay:
    id: str
    label: str
    phrase: str
    setup_line: str
    closing_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Response:
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
        other = World()
        other.entities = copy.deepcopy(self.entities)
        other.fired = set(self.fired)
        other.paragraphs = [[]]
        other.facts = copy.deepcopy(self.facts)
        return other


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_lane_danger(world: World) -> list[str]:
    obj = world.entities.get("thing")
    lane = world.entities.get("lane")
    hero = world.entities.get("hero")
    parent = world.entities.get("parent")
    if obj is None or lane is None or hero is None or parent is None:
        return []
    if obj.meters["in_lane"] < THRESHOLD:
        return []
    sig = ("lane_danger",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    lane.meters["danger"] += 1
    hero.memes["worry"] += 1
    parent.memes["worry"] += 1
    return ["__lane__"]


def _r_lunge_risk(world: World) -> list[str]:
    hero = world.entities.get("hero")
    lane = world.entities.get("lane")
    parent = world.entities.get("parent")
    if hero is None or lane is None or parent is None:
        return []
    if hero.meters["lunging"] < THRESHOLD or lane.meters["danger"] < THRESHOLD:
        return []
    sig = ("lunge_risk",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.meters["near_lane"] += 1
    hero.memes["fear"] += 1
    parent.memes["alarm"] += 1
    return ["__lunge__"]


def _r_hand_stop(world: World) -> list[str]:
    hero = world.entities.get("hero")
    if hero is None:
        return []
    if hero.meters["held_hand"] < THRESHOLD or hero.meters["lunging"] < THRESHOLD:
        return []
    sig = ("hand_stop",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.meters["stopped"] += 1
    hero.meters["lunging"] = 0.0
    hero.meters["near_lane"] = 0.0
    hero.memes["fear"] += 1
    return ["__stop__"]


CAUSAL_RULES: list[Rule] = [
    Rule(name="lane_danger", tag="physical", apply=_r_lane_danger),
    Rule(name="lunge_risk", tag="physical", apply=_r_lunge_risk),
    Rule(name="hand_stop", tag="social", apply=_r_hand_stop),
]


def propagate(world: World, narrate: bool = False) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            lines = rule.apply(world)
            if lines:
                changed = True
                produced.extend(lines)
    if narrate:
        for line in produced:
            if not line.startswith("__"):
                world.say(line)
    return produced


def hazard_at_risk(place: LotPlace, thing: LostThing) -> bool:
    return thing.motion in {"roll", "blow"}


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def escape_severity(place: LotPlace, thing: LostThing, delay: int) -> int:
    motion_bonus = 1 if thing.motion == "blow" and place.breezy else 0
    return place.busy + delay + motion_bonus


def is_saved(place: LotPlace, thing: LostThing, response: Response, delay: int) -> bool:
    return response.power >= escape_severity(place, thing, delay)


def predict_dash(world: World) -> dict:
    sim = world.copy()
    sim.get("thing").meters["in_lane"] += 1
    propagate(sim, narrate=False)
    sim.get("hero").meters["lunging"] += 1
    propagate(sim, narrate=False)
    return {
        "danger": sim.get("lane").meters["danger"],
        "near_lane": sim.get("hero").meters["near_lane"],
    }


def introduce(world: World, hero: Entity, parent: Entity, place: LotPlace, thing: LostThing) -> None:
    world.say(
        f"At the {place.label} one bright day in the lot, {hero.id} found {thing.phrase} and loved it a lot."
    )
    world.say(
        f"Beside {hero.pronoun('possessive')} {parent.label_word}, {hero.pronoun()} sang in a happy little jive, "
        f'pretending with a grin that tiny wheels could drive.'
    )
    hero.memes["joy"] += 1


def play_setup(world: World, hero: Entity, place: LotPlace, thing: LostThing) -> None:
    world.say(
        f"{thing.start_play} near {place.safe_spot}, a cozy little spot."
    )
    world.say(
        f"The lanes were meant for cars to pass; the play stayed by the curb and grass."
    )
    world.facts["started_safe"] = True


def escape_into_lane(world: World, hero: Entity, thing_ent: Entity, place: LotPlace, thing: LostThing) -> None:
    thing_ent.meters["in_lane"] += 1
    propagate(world, narrate=False)
    hero.memes["surprise"] += 1
    world.say(
        f"But then {thing.escape_line} and skipped into the drive, "
        f"where grown-up cars rolled slowly by, awake and wide alive."
    )


def lunge(world: World, hero: Entity, thing: LostThing) -> None:
    hero.meters["lunging"] += 1
    hero.memes["impulse"] += 1
    propagate(world, narrate=False)
    world.say(
        f'"My {thing.label}!" cried {hero.id}, and darted for the prize. '
        f"The wish to grab it quickly flashed like sparks behind {hero.pronoun('possessive')} eyes."
    )


def warn_and_hold(world: World, hero: Entity, parent: Entity, place: LotPlace) -> None:
    pred = predict_dash(world)
    world.facts["predicted_danger"] = pred["danger"]
    world.facts["predicted_near_lane"] = pred["near_lane"]
    hero.meters["held_hand"] += 1
    parent.memes["care"] += 1
    propagate(world, narrate=False)
    world.say(
        f'{parent.label_word.capitalize()} caught {hero.pronoun("possessive")} hand and held on tight. '
        f'"In a busy lot, we stop at the edge and let the grown-ups check the drive first, right?"'
    )


def rescue_success(world: World, parent: Entity, thing_ent: Entity, place: LotPlace, response: Response) -> None:
    thing_ent.meters["in_lane"] = 0.0
    thing_ent.meters["recovered"] += 1
    world.get("lane").meters["danger"] = 0.0
    hero = world.get("hero")
    hero.memes["relief"] += 1
    hero.memes["fear"] = 0.0
    world.say(
        f"{parent.label_word.capitalize()} {response.text}."
    )
    world.say(
        f"In just a moment, the drive was clear, the little thing was near, and {hero.id} could breathe out soft instead of sharp with fear."
    )


def rescue_fail(world: World, parent: Entity, thing_ent: Entity, response: Response, thing: LostThing) -> None:
    thing_ent.meters["in_lane"] = 0.0
    thing_ent.meters["lost"] += 1
    world.get("lane").meters["danger"] = 0.0
    hero = world.get("hero")
    hero.memes["sad"] += 1
    hero.memes["fear"] = 0.0
    world.say(
        f"{parent.label_word.capitalize()} {response.fail}."
    )
    world.say(
        f"The lane was safe again, but not the same; poor {thing.label} was bent and tame."
    )


def lesson(world: World, hero: Entity, parent: Entity, place: LotPlace, thing: LostThing) -> None:
    hero.memes["lesson"] += 1
    hero.memes["love"] += 1
    parent.memes["relief"] += 1
    if hero.meters["stopped"] >= THRESHOLD:
        stop_bit = "stopped at the edge"
    else:
        stop_bit = "stayed by the curb"
    world.say(
        f'{parent.label_word.capitalize()} knelt beside {hero.id}. '
        f'"You did not go into the drive. You {stop_bit}, and that helped keep you safe."'
    )
    world.say(
        f'"In a lot, toys can wait, but little feet should pause. We use calm eyes, still toes, and grown-up hands for parking-lot laws."'
    )


def safe_redirection(world: World, hero: Entity, parent: Entity, play: SafePlay, thing: LostThing) -> None:
    hero.memes["joy"] += 1
    hero.meters["playing_safe"] += 1
    world.say(
        f"Then {parent.label_word} made {play.setup_line}."
    )
    world.say(
        f"{hero.id} used {thing.safe_use} there instead, and soon the game felt bright, not dread."
    )
    world.say(
        f"{play.closing_line} In the safe small ring, {thing.label} could drive and dive, "
        f"and {hero.id}'s smile came bouncing back alive."
    )


def tell(
    place: LotPlace,
    thing: LostThing,
    play: SafePlay,
    response: Response,
    *,
    hero_name: str = "Mia",
    hero_gender: str = "girl",
    parent_type: str = "mother",
    trait: str = "careful",
    delay: int = 0,
) -> World:
    world = World()
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_gender,
        label=hero_name,
        role="hero",
        traits=[trait],
        tags={"child"},
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=parent_type,
        label="the parent",
        role="parent",
        tags={"grownup"},
    ))
    lane = world.add(Entity(
        id="lane",
        type="drive_lane",
        label="drive lane",
        phrase=place.drive_phrase,
        tags={"drive_lane"},
    ))
    thing_ent = world.add(Entity(
        id="thing",
        type="toy",
        label=thing.label,
        phrase=thing.phrase,
        tags=set(thing.tags),
    ))
    lot_ent = world.add(Entity(
        id="lot",
        type="lot",
        label=place.label,
        phrase=place.label,
        tags=set(place.tags),
    ))

    introduce(world, hero, parent, place, thing)
    play_setup(world, hero, place, thing)

    world.para()
    escape_into_lane(world, hero, thing_ent, place, thing)
    lunge(world, hero, thing)
    warn_and_hold(world, hero, parent, place)

    world.para()
    severity = escape_severity(place, thing, delay)
    world.facts["severity"] = severity
    world.facts["delay"] = delay
    saved = is_saved(place, thing, response, delay)
    if saved:
        rescue_success(world, parent, thing_ent, place, response)
    else:
        rescue_fail(world, parent, thing_ent, response, thing)
    lesson(world, hero, parent, place, thing)

    world.para()
    safe_redirection(world, hero, parent, play, thing)

    world.facts.update(
        place=place,
        thing_cfg=thing,
        play=play,
        response=response,
        hero=hero,
        parent=parent,
        thing=thing_ent,
        lot=lot_ent,
        outcome="saved" if saved else "squashed",
        saved=saved,
    )
    return world


LOTS = {
    "pumpkin_lot": LotPlace(
        id="pumpkin_lot",
        label="pumpkin lot",
        scene="orange pumpkins in neat rows",
        drive_phrase="the narrow drive between the pumpkin rows",
        safe_spot="the hay-bale corner",
        busy=1,
        breezy=True,
        tags={"lot", "pumpkin_lot", "parking"},
    ),
    "garden_lot": LotPlace(
        id="garden_lot",
        label="garden shop lot",
        scene="pots and petals by the carts",
        drive_phrase="the drive beside the flower carts",
        safe_spot="the wide brick walk",
        busy=2,
        breezy=True,
        tags={"lot", "garden_lot", "parking"},
    ),
    "book_lot": LotPlace(
        id="book_lot",
        label="book fair lot",
        scene="tables of bright books and folding signs",
        drive_phrase="the drive between the signposts",
        safe_spot="the chalk-marked curb",
        busy=2,
        breezy=False,
        tags={"lot", "book_lot", "parking"},
    ),
}

THINGS = {
    "ball": LostThing(
        id="ball",
        label="ball",
        phrase="a striped red ball",
        motion="roll",
        start_play="It went bump-bump-bump from shoe to shoe",
        escape_line="the ball gave one bold bobble",
        safe_use="the ball",
        tags={"ball", "roll"},
    ),
    "toy_truck": LostThing(
        id="toy_truck",
        label="toy truck",
        phrase="a little blue toy truck",
        motion="roll",
        start_play="It rumbled in circles with a putter and clack",
        escape_line="the toy truck tipped from the curb and rattled away",
        safe_use="the toy truck",
        tags={"truck", "roll"},
    ),
    "pinwheel": LostThing(
        id="pinwheel",
        label="pinwheel",
        phrase="a rainbow pinwheel on a stick",
        motion="blow",
        start_play="It whirled in the breeze with a shimmer and spin",
        escape_line="a puff of wind tugged the pinwheel free",
        safe_use="the pinwheel",
        tags={"pinwheel", "wind"},
    ),
    "boot": LostThing(
        id="boot",
        label="boot",
        phrase="one small rain boot",
        motion="stay",
        start_play="It sat by the curb with a thump and a flop",
        escape_line="the boot sat still",
        safe_use="the boot",
        tags={"boot"},
    ),
}

SAFE_PLAYS = {
    "chalk_loop": SafePlay(
        id="chalk_loop",
        label="chalk loop",
        phrase="a chalk loop on the walk",
        setup_line="a round chalk road on the sidewalk",
        closing_line="Soon the game had its own tiny track and its own happy sing.",
        tags={"chalk", "sidewalk"},
    ),
    "crate_track": SafePlay(
        id="crate_track",
        label="crate track",
        phrase="a box-and-crate track",
        setup_line="a little track with empty crates by the wall",
        closing_line="Soon the safe lane felt grand in a child-sized way.",
        tags={"track", "sidewalk"},
    ),
    "hay_ring": SafePlay(
        id="hay_ring",
        label="hay ring",
        phrase="a hay-bale ring",
        setup_line="a round play ring beside the hay bales",
        closing_line="Soon the game had a border and a calmer sort of spring.",
        tags={"hay", "sidewalk"},
    ),
}

RESPONSES = {
    "wait_and_fetch": Response(
        id="wait_and_fetch",
        sense=3,
        power=3,
        text="waited for a clear gap, then walked out calmly and fetched the toy back from the lane",
        fail="waited for a clear gap and stepped out safely, but a passing tire had already crunched the toy flat",
        qa_text="waited for a clear gap and fetched it back",
        tags={"wait", "grownup_help"},
    ),
    "signal_and_fetch": Response(
        id="signal_and_fetch",
        sense=3,
        power=4,
        text="raised a hand to the nearest driver, checked both ways, and brought the toy back with calm slow steps",
        fail="checked both ways and moved carefully, but the toy was already too damaged to save",
        qa_text="checked both ways, signaled, and brought it back",
        tags={"wait", "grownup_help", "look_both_ways"},
    ),
    "dash_and_grab": Response(
        id="dash_and_grab",
        sense=1,
        power=1,
        text="ran into the lane in a hurry and snatched the toy up fast",
        fail="rushed into the lane, but the quick grab was not quick enough",
        qa_text="ran into the lane and grabbed it",
        tags={"unsafe"},
    ),
}


@dataclass
class StoryParams:
    lot: str
    thing: str
    safe_play: str
    response: str
    name: str
    gender: str
    parent: str
    trait: str
    delay: int = 0
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        lot="pumpkin_lot",
        thing="ball",
        safe_play="hay_ring",
        response="wait_and_fetch",
        name="Mia",
        gender="girl",
        parent="mother",
        trait="careful",
        delay=0,
    ),
    StoryParams(
        lot="garden_lot",
        thing="pinwheel",
        safe_play="chalk_loop",
        response="signal_and_fetch",
        name="Leo",
        gender="boy",
        parent="father",
        trait="quick",
        delay=1,
    ),
    StoryParams(
        lot="book_lot",
        thing="toy_truck",
        safe_play="crate_track",
        response="wait_and_fetch",
        name="Nora",
        gender="girl",
        parent="mother",
        trait="curious",
        delay=2,
    ),
]

GIRL_NAMES = ["Mia", "Lily", "Nora", "Zoe", "Ava", "Ella", "Lucy", "Ruby"]
BOY_NAMES = ["Leo", "Ben", "Sam", "Max", "Finn", "Noah", "Eli", "Jack"]
TRAITS = ["careful", "curious", "quick", "bouncy", "thoughtful", "eager"]


KNOWLEDGE = {
    "lot": [
        (
            "What is a parking lot?",
            "A parking lot is a place where cars stop and park. Because cars move in and out, children need to stay close to a grown-up there."
        )
    ],
    "drive_lane": [
        (
            "What is a drive lane?",
            "A drive lane is the part of a lot where cars travel through. It is for moving cars, not for games or chasing toys."
        )
    ],
    "ball": [
        (
            "Why can a ball be hard to catch near cars?",
            "A ball can roll farther than you expect. If it rolls into a drive lane, it can move faster than little feet."
        )
    ],
    "truck": [
        (
            "Why should a toy truck stay on the sidewalk instead of the drive?",
            "A toy truck is fun to drive in pretend play, but a real drive lane belongs to cars. Sidewalks and play spots are safer for toy games."
        )
    ],
    "pinwheel": [
        (
            "Why can wind be tricky in a parking lot?",
            "Wind can tug light things out of your hand and push them away quickly. That is why it helps to stop and let a grown-up help."
        )
    ],
    "wait": [
        (
            "Why is waiting important near a drive lane?",
            "Waiting gives you time to look, listen, and think. A calm pause can keep little feet out of the way of cars."
        )
    ],
    "grownup_help": [
        (
            "Why should a grown-up get the toy in a busy lot?",
            "A grown-up is taller, can see better, and can judge when it is safe to move. Asking for help is the smart choice."
        )
    ],
    "look_both_ways": [
        (
            "Why do people look both ways before crossing where cars go?",
            "Cars can come from either direction. Looking both ways helps you notice movement before you step."
        )
    ],
    "chalk": [
        (
            "What is a chalk road?",
            "A chalk road is a pretend path drawn on the ground for play. It lets a game feel real without using the place where cars drive."
        )
    ],
    "track": [
        (
            "What is a toy track for?",
            "A toy track gives wheels a clear place to go. That helps children keep their games in a safe spot."
        )
    ],
    "hay": [
        (
            "Why does a play ring help children stay safe?",
            "A play ring makes the game area easy to see. A clear border reminds everyone where play should stay."
        )
    ],
}
KNOWLEDGE_ORDER = [
    "lot",
    "drive_lane",
    "ball",
    "truck",
    "pinwheel",
    "wait",
    "grownup_help",
    "look_both_ways",
    "chalk",
    "track",
    "hay",
]


def valid_combos() -> list[tuple[str, str]]:
    combos: list[tuple[str, str]] = []
    for lot_id, place in LOTS.items():
        for thing_id, thing in THINGS.items():
            if hazard_at_risk(place, thing):
                combos.append((lot_id, thing_id))
    return combos


def explain_rejection(place: LotPlace, thing: LostThing) -> str:
    if thing.motion == "stay":
        return (
            f"(No story: {thing.phrase} would not roll or blow into the drive lane at the {place.label}. "
            f"Without a real lot hazard, there is no honest problem for the grown-up to solve.)"
        )
    return "(No story: this lot and toy do not make a plausible drive-lane hazard.)"


def explain_response(rid: str) -> str:
    resp = RESPONSES[rid]
    better = ", ".join(sorted(r.id for r in sensible_responses()))
    return (
        f"(Refusing response '{rid}': it scores too low on common sense "
        f"(sense={resp.sense} < {SENSE_MIN}). Try a calmer parking-lot response such as {better}.)"
    )


def outcome_of(params: StoryParams) -> str:
    if params.lot not in LOTS or params.thing not in THINGS or params.response not in RESPONSES:
        raise StoryError("(Cannot compute outcome: unknown parameter value.)")
    return "saved" if is_saved(LOTS[params.lot], THINGS[params.thing], RESPONSES[params.response], params.delay) else "squashed"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    place = f["place"]
    thing = f["thing_cfg"]
    play = f["play"]
    outcome = f["outcome"]
    if outcome == "saved":
        return [
            f'Write a gentle rhyming story for a 3-to-5-year-old that includes the words "lot" and "drive". A child\'s {thing.label} slips into a busy lot, a grown-up stops the child, and the ending turns safe and bright.',
            f"Tell a rhyming story where {hero.id} nearly runs after a {thing.label} in the {place.label}, but a parent keeps {hero.pronoun('object')} safe and makes {play.phrase} for the ending.",
            f'Write a short rhyme about stopping at the edge of a drive lane and letting a grown-up help, with a warm ending and a toy that can still "drive" in pretend play.',
        ]
    return [
        f'Write a rhyming cautionary story for a 3-to-5-year-old that includes the words "lot" and "drive". A toy slips into a busy lot, a child is stopped safely, but the toy is too late to save.',
        f"Tell a gentle parking-lot rhyme where {hero.id} learns that toys can wait, even when {thing.label} is lost in the drive lane.",
        f'Write a child-facing rhyme with a sad toy but a safe child, and end by showing a new safe place to play.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    parent = f["parent"]
    thing = f["thing_cfg"]
    place = f["place"]
    play = f["play"]
    response = f["response"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, {hero.pronoun('possessive')} favorite {thing.label}, and {hero.pronoun('possessive')} {parent.label_word} at the {place.label}."
        ),
        (
            f"Why was the {place.lot_word} dangerous?",
            f"The toy slipped into the drive lane, where cars move through the lot. That made the space unsafe for a child to chase anything."
        ),
        (
            f"Why did {hero.id} start to run?",
            f"{hero.id} saw {hero.pronoun('possessive')} {thing.label} get away and wanted to grab it fast. The quick wish to save the toy came before a safer plan."
        ),
        (
            f"What did {hero.id}'s {parent.label_word} do?",
            f"{parent.label_word.capitalize()} held {hero.pronoun('possessive')} hand and stopped {hero.pronoun('object')} at the edge. That pause mattered because a busy drive lane is a place for cars, not little feet."
        ),
    ]
    if outcome == "saved":
        qa.append(
            (
                f"How did the grown-up get the {thing.label} back?",
                f"{parent.label_word.capitalize()} {response.qa_text}. The calm method worked because the grown-up waited for a safe moment instead of rushing."
            )
        )
    else:
        qa.append(
            (
                f"Was the {thing.label} saved?",
                f"No. {parent.label_word.capitalize()} tried carefully, but the toy was already too damaged to keep. The important part is that {hero.id} stayed safe by not running into the drive."
            )
        )
    qa.append(
        (
            "How did the story end?",
            f"It ended with a safer game in {play.phrase}. The new play spot let the toy pretend to drive without using the real drive lane."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = set(f["place"].tags) | {"drive_lane"} | set(f["thing_cfg"].tags) | set(f["response"].tags) | set(f["play"].tags)
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
        bits: list[str] = []
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.traits:
            bits.append(f"traits={ent.traits}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        lines.append(f"  {ent.id:8} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
hazard(P, T) :- lot(P), thing(T), motion(T, roll).
hazard(P, T) :- lot(P), thing(T), motion(T, blow).

sensible(R) :- response(R), sense(R, S), sense_min(M), S >= M.
valid(P, T) :- lot(P), thing(T), hazard(P, T).

motion_bonus(P, T, 1) :- breezy(P), motion(T, blow).
motion_bonus(P, T, 0) :- not breezy(P).
motion_bonus(P, T, 0) :- breezy(P), not motion(T, blow).

severity(V) :- chosen_lot(P), chosen_thing(T), busy(P, B), delay(D), motion_bonus(P, T, M), V = B + D + M.
resp_power(Pw) :- chosen_response(R), power(R, Pw).

outcome(saved) :- resp_power(Pw), severity(V), Pw >= V.
outcome(squashed) :- resp_power(Pw), severity(V), Pw < V.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for lot_id, place in LOTS.items():
        lines.append(asp.fact("lot", lot_id))
        lines.append(asp.fact("busy", lot_id, place.busy))
        if place.breezy:
            lines.append(asp.fact("breezy", lot_id))
    for thing_id, thing in THINGS.items():
        lines.append(asp.fact("thing", thing_id))
        lines.append(asp.fact("motion", thing_id, thing.motion))
    for rid, response in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, response.sense))
        lines.append(asp.fact("power", rid, response.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_lot", params.lot),
            asp.fact("chosen_thing", params.thing),
            asp.fact("chosen_response", params.response),
            asp.fact("delay", params.delay),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def asp_verify() -> int:
    rc = 0
    py_valid = set(valid_combos())
    asp_valid = set(asp_valid_combos())
    if py_valid == asp_valid:
        print(f"OK: gate matches valid_combos() ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if asp_valid - py_valid:
            print("  only in clingo:", sorted(asp_valid - py_valid))
        if py_valid - asp_valid:
            print("  only in python:", sorted(py_valid - asp_valid))

    py_sens = {r.id for r in sensible_responses()}
    asp_sens = set(asp_sensible())
    if py_sens == asp_sens:
        print(f"OK: sensible responses match ({sorted(py_sens)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible responses: clingo={sorted(asp_sens)} python={sorted(py_sens)}")

    cases: list[StoryParams] = list(CURATED)
    parser = build_parser()
    for seed in range(30):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
        except StoryError:
            continue
        params.seed = seed
        cases.append(params)
    bad = 0
    for params in cases:
        py_out = outcome_of(params)
        asp_out = asp_outcome(params)
        if py_out != asp_out:
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("(Smoke test failed: empty story.)")
        print("OK: smoke test generated a normal story.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Rhyming lot-and-drive storyworld: a child, a rolling toy, a safe stop, and a safer place to play."
    )
    ap.add_argument("--lot", choices=LOTS)
    ap.add_argument("--thing", choices=THINGS)
    ap.add_argument("--safe-play", dest="safe_play", choices=SAFE_PLAYS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], help="How long the toy stays in danger before help reaches it.")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid lot-and-thing combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.lot and args.thing:
        place = LOTS[args.lot]
        thing = THINGS[args.thing]
        if not hazard_at_risk(place, thing):
            raise StoryError(explain_rejection(place, thing))
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))

    combos = [
        combo
        for combo in valid_combos()
        if (args.lot is None or combo[0] == args.lot)
        and (args.thing is None or combo[1] == args.thing)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    lot_id, thing_id = rng.choice(sorted(combos))
    safe_play = args.safe_play or rng.choice(sorted(SAFE_PLAYS))
    response = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    return StoryParams(
        lot=lot_id,
        thing=thing_id,
        safe_play=safe_play,
        response=response,
        name=name,
        gender=gender,
        parent=parent,
        trait=trait,
        delay=delay,
    )


def generate(params: StoryParams) -> StorySample:
    if params.lot not in LOTS:
        raise StoryError(f"(Unknown lot '{params.lot}'.)")
    if params.thing not in THINGS:
        raise StoryError(f"(Unknown thing '{params.thing}'.)")
    if params.safe_play not in SAFE_PLAYS:
        raise StoryError(f"(Unknown safe-play '{params.safe_play}'.)")
    if params.response not in RESPONSES:
        raise StoryError(f"(Unknown response '{params.response}'.)")
    place = LOTS[params.lot]
    thing = THINGS[params.thing]
    play = SAFE_PLAYS[params.safe_play]
    response = RESPONSES[params.response]
    if not hazard_at_risk(place, thing):
        raise StoryError(explain_rejection(place, thing))
    if response.sense < SENSE_MIN:
        raise StoryError(explain_response(params.response))

    world = tell(
        place=place,
        thing=thing,
        play=play,
        response=response,
        hero_name=params.name,
        hero_gender=params.gender,
        parent_type=params.parent,
        trait=params.trait,
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/2.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (lot, thing) combos:\n")
        for lot_id, thing_id in combos:
            print(f"  {lot_id:12} {thing_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.thing} in {p.lot} ({p.response}, {outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
