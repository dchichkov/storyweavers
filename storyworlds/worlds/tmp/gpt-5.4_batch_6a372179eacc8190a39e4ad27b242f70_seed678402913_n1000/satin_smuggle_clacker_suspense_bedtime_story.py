#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/satin_smuggle_clacker_suspense_bedtime_story.py
===========================================================================

A standalone storyworld for a gentle suspense bedtime tale: a child tries to
smuggle a noisy clacker toy into bed, someone notices, the house holds its
breath, and the night is saved by a quieter choice.

The domain is intentionally small and constraint-checked. The world model asks:
is the object truly noisy enough to threaten sleep, is the hiding place
plausible for smuggling it under the covers, and is the grown-up response a calm
and sensible bedtime fix? Those checks decide whether the story can exist and
how the ending turns out.

Run it
------
    python storyworlds/worlds/gpt-5.4/satin_smuggle_clacker_suspense_bedtime_story.py
    python storyworlds/worlds/gpt-5.4/satin_smuggle_clacker_suspense_bedtime_story.py --hiding satin_pillow
    python storyworlds/worlds/gpt-5.4/satin_smuggle_clacker_suspense_bedtime_story.py --response stomp
    python storyworlds/worlds/gpt-5.4/satin_smuggle_clacker_suspense_bedtime_story.py --all
    python storyworlds/worlds/gpt-5.4/satin_smuggle_clacker_suspense_bedtime_story.py --qa --json
    python storyworlds/worlds/gpt-5.4/satin_smuggle_clacker_suspense_bedtime_story.py --verify
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
COURAGE_INIT = 5.0
CAREFUL_TRAITS = {"careful", "gentle", "watchful", "patient"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    age: int = 0
    attrs: dict = field(default_factory=dict)
    noisy: bool = False
    soft: bool = False
    sleepy: bool = False
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
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class RoomTheme:
    id: str
    room: str
    opening: str
    hush_image: str
    underbed: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Contraband:
    id: str
    label: str
    phrase: str
    sound: str
    motion: str
    noise: int
    plural: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class HidingPlace:
    id: str
    label: str
    phrase: str
    preposition: str
    rustle: str
    muffles: int
    satin: bool = False
    bed_safe: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class QuietThing:
    id: str
    label: str
    phrase: str
    comfort: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Response:
    id: str
    sense: int
    speed: int
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


def _r_noise_rises(world: World) -> list[str]:
    out: list[str] = []
    toy = world.entities.get("toy")
    if toy is None or toy.meters["clack"] < THRESHOLD:
        return out
    sig = ("noise_rises",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    room = world.entities.get("room")
    if room is not None:
        room.meters["tension"] += 1
    for ent in world.entities.values():
        if ent.role in {"smuggler", "watcher"}:
            ent.memes["worry"] += 1
    sleeper = world.entities.get("sleeper")
    if sleeper is not None:
        sleeper.meters["stirring"] += 1
    out.append("__clack__")
    return out


def _r_wake(world: World) -> list[str]:
    out: list[str] = []
    sleeper = world.entities.get("sleeper")
    room = world.entities.get("room")
    if sleeper is None or room is None:
        return out
    if sleeper.meters["stirring"] < THRESHOLD or room.meters["tension"] < THRESHOLD:
        return out
    sig = ("wake",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    sleeper.meters["awake"] += 1
    for ent in world.entities.values():
        if ent.role in {"smuggler", "watcher", "parent"}:
            ent.memes["alarm"] += 1
    out.append("__awake__")
    return out


CAUSAL_RULES = [
    Rule(name="noise_rises", tag="physical", apply=_r_noise_rises),
    Rule(name="wake", tag="physical", apply=_r_wake),
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


def hiding_works(toy: Contraband, hiding: HidingPlace) -> bool:
    return toy.noise > 0 and hiding.bed_safe


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def noise_risk(toy: Contraband, hiding: HidingPlace, delay: int) -> int:
    return max(0, toy.noise - hiding.muffles) + delay


def will_wake(toy: Contraband, hiding: HidingPlace, delay: int, response: Response) -> bool:
    return response.speed < noise_risk(toy, hiding, delay)


def initial_care(trait: str) -> float:
    return 5.0 if trait in CAREFUL_TRAITS else 3.0


def would_confess(relation: str, smuggler_age: int, watcher_age: int, trait: str) -> bool:
    watcher_older = relation == "siblings" and watcher_age > smuggler_age
    calm_weight = initial_care(trait) + 1.0 + (3.0 if watcher_older else 0.0)
    return watcher_older and calm_weight > COURAGE_INIT


def predict_noise(world: World, toy_id: str) -> dict:
    sim = world.copy()
    toy = sim.get(toy_id)
    toy.meters["clack"] += 1
    propagate(sim, narrate=False)
    sleeper = sim.get("sleeper")
    room = sim.get("room")
    return {
        "stirs": sleeper.meters["stirring"] >= THRESHOLD,
        "awake": sleeper.meters["awake"] >= THRESHOLD,
        "tension": room.meters["tension"],
    }


def bedtime_setup(world: World, a: Entity, b: Entity, theme: RoomTheme, sleeper: Entity) -> None:
    world.say(
        f"It was bedtime, and {theme.opening} {theme.hush_image}"
    )
    world.say(
        f"{a.id} and {b.id} had brushed their teeth, listened to one last story, "
        f"and climbed into bed while {sleeper.label} slept nearby."
    )


def desire(world: World, a: Entity, toy: Contraband, hiding: HidingPlace) -> None:
    a.memes["desire"] += 1
    satin = " satin" if hiding.satin else ""
    world.say(
        f"But {a.id} was not ready for the dark to be still. Tucked in "
        f"{a.pronoun('possessive')} hand was {toy.phrase}, and {a.pronoun()} wanted "
        f"to smuggle it {hiding.preposition} the{ satin} {hiding.label} for one more secret game."
    )
    world.say(
        f"In {a.pronoun('possessive')} mind, the little toy could {toy.motion} without anyone hearing."
    )


def warning(world: World, b: Entity, a: Entity, toy: Contraband, hiding: HidingPlace, parent: Entity) -> None:
    pred = predict_noise(world, "toy")
    b.memes["care"] += 1
    world.facts["predicted_tension"] = pred["tension"]
    detail = "The satin looked smooth and safe, but it would still whisper when it moved." if hiding.satin else (
        f"The {hiding.label} would {hiding.rustle} if anything hard rubbed against it."
    )
    world.say(
        f"{b.id} saw the shape in {a.pronoun('possessive')} fist and whispered, "
        f'"Is that {toy.phrase}? If it clacks, it might wake {world.get("sleeper").label}. '
        f'{parent.label_word.capitalize()} said this room needs quiet feet and quiet hands."'
    )
    world.say(detail)


def defy(world: World, a: Entity, b: Entity, toy: Contraband) -> None:
    a.memes["defiance"] += 1
    world.say(
        f'"Only for one tiny minute," {a.id} whispered back. {a.pronoun().capitalize()} '
        f'curled closer under the blanket while {b.id} held still and listened.'
    )


def back_down(world: World, a: Entity, b: Entity, toy: Contraband, quiet: QuietThing, parent: Entity) -> None:
    a.memes["relief"] += 1
    b.memes["relief"] += 1
    world.say(
        f'{a.id} looked toward the little bed, then at {b.id}, who was older and very sure. '
        f'The brave feeling in {a.pronoun("possessive")} chest went soft instead of stubborn.'
    )
    world.say(
        f'"You are right," {a.pronoun()} breathed. {a.pronoun().capitalize()} slid {toy.phrase} back onto the shelf '
        f"and reached for {quiet.phrase} instead."
    )
    world.say(
        f"The room stayed hush-hush, and even {parent.label_word} in the hall did not have to come in."
    )


def sneak(world: World, a: Entity, toy_ent: Entity, toy: Contraband, hiding: HidingPlace) -> None:
    toy_ent.meters["hidden"] += 1
    world.say(
        f"Very slowly, {a.id} tucked the toy {hiding.preposition} {hiding.phrase}. "
        f"The whole room seemed to wait."
    )


def clack(world: World, a: Entity, toy_ent: Entity, toy: Contraband, hiding: HidingPlace) -> None:
    toy_ent.meters["clack"] += 1
    propagate(world, narrate=False)
    whisper = "The satin gave a tiny whisper" if hiding.satin else f"The {hiding.label} gave a tiny {hiding.rustle}"
    world.say(
        f"Then {whisper}, and {toy.phrase} made {toy.sound} in the dark."
    )
    world.say(
        f"{a.id}'s heart bumped once, hard. {world.get('sleeper').label.capitalize()} turned in sleep."
    )


def alarm(world: World, b: Entity, parent: Entity) -> None:
    sleeper = world.get("sleeper")
    if sleeper.meters["awake"] >= THRESHOLD:
        world.say(f'"Oh no," {b.id} whispered, but {sleeper.label} was already awake.')
    else:
        world.say(
            f'{b.id} pressed a finger to {b.pronoun("possessive")} lips and whispered, '
            f'"Quick. Call {parent.label_word} before another clack."'
        )


def rescue(world: World, parent: Entity, response: Response, quiet: QuietThing, toy: Contraband) -> None:
    toy_ent = world.get("toy")
    toy_ent.meters["clack"] = 0.0
    world.get("room").meters["tension"] = 0.0
    world.get("sleeper").meters["stirring"] = 0.0
    world.say(
        f"{parent.label_word.capitalize()} came in right away and {response.text}."
    )
    world.say(
        f"In place of {toy.phrase}, {parent.pronoun()} tucked in {quiet.phrase}. "
        f"It {quiet.comfort} instead of making noise."
    )


def lesson(world: World, parent: Entity, a: Entity, b: Entity, toy: Contraband) -> None:
    for kid in (a, b):
        kid.memes["relief"] += 1
        kid.memes["lesson"] += 1
    world.say(
        f'{parent.label_word.capitalize()} sat on the edge of the bed and spoke so softly that the shadows seemed to listen too. '
        f'"I am glad you called me," {parent.pronoun()} said. "A clacker belongs in playtime, not under a blanket at bedtime."'
    )
    world.say(
        f"{a.id} nodded and held the blanket with both hands. {b.id} leaned close, and the room slowly un-scrunched itself."
    )


def safe_end(world: World, a: Entity, b: Entity, quiet: QuietThing, theme: RoomTheme) -> None:
    for kid in (a, b):
        kid.memes["sleepy"] += 1
        kid.memes["joy"] += 1
    world.say(
        f"Soon {a.id} and {b.id} were breathing slowly again. {quiet.phrase.capitalize()} rested between them, "
        f"and {theme.room} looked peaceful enough to hold the whole night."
    )
    world.say("Nothing clacked after that. The dark stayed gentle, and everybody slept.")


def rescue_fail(world: World, parent: Entity, response: Response, toy: Contraband) -> None:
    world.say(f"{parent.label_word.capitalize()} hurried in and {response.fail}.")
    world.get("sleeper").meters["awake"] = 1.0
    world.get("room").meters["tension"] += 1.0


def wake_scene(world: World, sleeper: Entity, parent: Entity) -> None:
    world.say(
        f"{sleeper.label.capitalize()} let out a sharp little cry, and the quiet bedtime house was quiet no more."
    )
    world.say(
        f"{parent.label_word.capitalize()} lifted {sleeper.pronoun('object')} up and rocked {sleeper.pronoun('object')} in the moonlight."
    )


def sorry_end(world: World, a: Entity, b: Entity, toy: Contraband, quiet: QuietThing) -> None:
    for kid in (a, b):
        kid.memes["lesson"] += 1
        kid.memes["sad"] += 1
    world.say(
        f"{a.id} wished {a.pronoun()} had never tried to smuggle {toy.phrase} into bed at all. {b.id} rubbed {b.pronoun('possessive')} eyes and stayed beside {a.pronoun('object')} anyway."
    )
    world.say(
        f"At last the house settled again, but much later than before. {quiet.phrase.capitalize()} lay ready on the blanket, waiting for tomorrow night's wiser choice."
    )


def tell(
    theme: RoomTheme,
    contraband: Contraband,
    hiding: HidingPlace,
    quiet: QuietThing,
    response: Response,
    smuggler: str = "Lila",
    smuggler_gender: str = "girl",
    watcher: str = "Ned",
    watcher_gender: str = "boy",
    parent_type: str = "mother",
    trait: str = "careful",
    relation: str = "siblings",
    smuggler_age: int = 5,
    watcher_age: int = 7,
    delay: int = 0,
) -> World:
    world = World()
    a = world.add(Entity(
        id=smuggler,
        kind="character",
        type=smuggler_gender,
        role="smuggler",
        age=smuggler_age,
        attrs={"relation": relation},
    ))
    b = world.add(Entity(
        id=watcher,
        kind="character",
        type=watcher_gender,
        role="watcher",
        age=watcher_age,
        traits=[trait],
        attrs={"relation": relation},
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=parent_type,
        role="parent",
        label="the parent",
    ))
    sleeper = world.add(Entity(
        id="sleeper",
        kind="character",
        type="baby",
        role="sleeper",
        label="the baby",
        sleepy=True,
    ))
    room = world.add(Entity(
        id="room",
        type="room",
        label=theme.room,
    ))
    toy_ent = world.add(Entity(
        id="toy",
        type="toy",
        label=contraband.label,
        phrase=contraband.phrase,
        noisy=True,
        tags=set(contraband.tags),
    ))
    quiet_ent = world.add(Entity(
        id="quiet",
        type="comfort",
        label=quiet.label,
        phrase=quiet.phrase,
        soft=True,
        tags=set(quiet.tags),
    ))

    a.memes["courage"] = COURAGE_INIT
    b.memes["care"] = initial_care(trait)

    bedtime_setup(world, a, b, theme, sleeper)
    world.para()
    desire(world, a, contraband, hiding)
    warning(world, b, a, contraband, hiding, parent)

    confessed = would_confess(relation, smuggler_age, watcher_age, trait)
    if confessed:
        back_down(world, a, b, contraband, quiet, parent)
        world.para()
        safe_end(world, a, b, quiet, theme)
        outcome = "averted"
    else:
        defy(world, a, b, contraband)
        world.para()
        sneak(world, a, toy_ent, contraband, hiding)
        clack(world, a, toy_ent, contraband, hiding)
        for _ in range(delay):
            world.get("room").meters["tension"] += 1
            world.get("sleeper").meters["stirring"] += 1
        propagate(world, narrate=False)
        alarm(world, b, parent)

        woke = will_wake(contraband, hiding, delay, response)
        world.para()
        if not woke:
            rescue(world, parent, response, quiet, contraband)
            lesson(world, parent, a, b, contraband)
            world.para()
            safe_end(world, a, b, quiet, theme)
            outcome = "settled"
        else:
            rescue_fail(world, parent, response, contraband)
            wake_scene(world, sleeper, parent)
            sorry_end(world, a, b, contraband, quiet)
            outcome = "woke_house"

    world.facts.update(
        theme=theme,
        contraband=contraband,
        hiding=hiding,
        quiet=quiet,
        response=response,
        smuggler=a,
        watcher=b,
        parent=parent,
        sleeper=sleeper,
        room=room,
        toy=toy_ent,
        quiet_ent=quiet_ent,
        relation=relation,
        delay=delay,
        outcome=outcome,
        confessed=confessed,
        woke=sleeper.meters["awake"] >= THRESHOLD,
    )
    return world


ROOM_THEMES = {
    "nursery_hall": RoomTheme(
        id="nursery_hall",
        room="the small bedroom by the nursery",
        opening="the small bedroom by the nursery was blue with moonlight",
        hush_image="Even the hallway clock seemed to breathe more quietly there.",
        underbed="the low bed by the wall",
        tags={"bedtime", "night"},
    ),
    "attic_room": RoomTheme(
        id="attic_room",
        room="the snug attic room",
        opening="the snug attic room was full of silver roof-shadows",
        hush_image="Rain tapped the roof so softly it sounded like faraway fingers.",
        underbed="the slanted bed under the eaves",
        tags={"bedtime", "night"},
    ),
    "guest_room": RoomTheme(
        id="guest_room",
        room="the warm guest room",
        opening="the warm guest room glowed with one stripe of moon across the quilt",
        hush_image="The night-light by the dresser made a small puddle of gold.",
        underbed="the tidy bed near the window",
        tags={"bedtime", "night"},
    ),
}

CONTRABAND = {
    "wooden_clacker": Contraband(
        id="wooden_clacker",
        label="clacker",
        phrase="a small wooden clacker",
        sound='a dry "clack-clack"',
        motion="click and spin",
        noise=3,
        tags={"clacker", "noise", "toy"},
    ),
    "shell_clacker": Contraband(
        id="shell_clacker",
        label="clacker",
        phrase="a shell clacker on a string",
        sound='a sharp "tik-clack"',
        motion="swing and knock",
        noise=2,
        tags={"clacker", "noise", "toy"},
    ),
    "tin_clacker": Contraband(
        id="tin_clacker",
        label="clacker",
        phrase="a bright tin clacker",
        sound='a hard "clack!"',
        motion="snap and jump",
        noise=4,
        tags={"clacker", "noise", "toy"},
    ),
}

HIDING_PLACES = {
    "satin_pillow": HidingPlace(
        id="satin_pillow",
        label="satin pillow",
        phrase="the satin pillow",
        preposition="under",
        rustle="slip",
        muffles=1,
        satin=True,
        bed_safe=True,
        tags={"satin", "pillow"},
    ),
    "quilt_fold": HidingPlace(
        id="quilt_fold",
        label="quilt fold",
        phrase="a fold in the quilt",
        preposition="inside",
        rustle="rustle",
        muffles=1,
        satin=False,
        bed_safe=True,
        tags={"quilt"},
    ),
    "pajama_pocket": HidingPlace(
        id="pajama_pocket",
        label="pajama pocket",
        phrase="the pajama pocket",
        preposition="inside",
        rustle="scritch",
        muffles=0,
        satin=False,
        bed_safe=True,
        tags={"pajamas"},
    ),
    "sock_drawer": HidingPlace(
        id="sock_drawer",
        label="sock drawer",
        phrase="the sock drawer",
        preposition="inside",
        rustle="slide",
        muffles=2,
        satin=False,
        bed_safe=False,
        tags={"drawer"},
    ),
}

QUIET_THINGS = {
    "satin_ribbon": QuietThing(
        id="satin_ribbon",
        label="satin ribbon",
        phrase="a cool satin ribbon",
        comfort="slid through small fingers like water",
        tags={"satin", "quiet"},
    ),
    "cloth_star": QuietThing(
        id="cloth_star",
        label="cloth star",
        phrase="a soft cloth star",
        comfort="sat quietly and warm in the palm",
        tags={"quiet", "comfort"},
    ),
    "plush_moon": QuietThing(
        id="plush_moon",
        label="plush moon",
        phrase="a little plush moon",
        comfort="rested softly against the cheek",
        tags={"quiet", "comfort"},
    ),
}

RESPONSES = {
    "quiet_swap": Response(
        id="quiet_swap",
        sense=3,
        speed=3,
        text="lifted the blanket, took the clacker away, and traded it for a soft comfort toy before another sound could happen",
        fail="tried to hush the room, but the sound had already come twice and the baby woke fully",
        qa_text="quietly took the clacker away and swapped in a soft comfort toy",
        tags={"quiet", "bedtime"},
    ),
    "hall_shelf": Response(
        id="hall_shelf",
        sense=2,
        speed=2,
        text="gently carried the clacker out to the hall shelf and smoothed the blankets flat again",
        fail="carried the clacker to the hall shelf, but not before one more clack escaped into the room",
        qa_text="carried the clacker out to the hall shelf and settled the blankets again",
        tags={"quiet", "bedtime"},
    ),
    "lecture": Response(
        id="lecture",
        sense=2,
        speed=1,
        text="whispered a short reminder first, then reached for the toy",
        fail="stopped to explain the rule before moving the toy, and the pause was long enough for the baby to wake",
        qa_text="gave a quick reminder and then removed the toy",
        tags={"bedtime", "rules"},
    ),
    "stomp": Response(
        id="stomp",
        sense=1,
        speed=0,
        text="stamped across the floor and snatched up the toy",
        fail="made even more noise by stomping across the floor, so the whole room woke up",
        qa_text="stomped over and grabbed the toy",
        tags={"noise"},
    ),
}

GIRL_NAMES = ["Lila", "Mina", "Tess", "Nora", "Ava", "Ella", "Mara", "June"]
BOY_NAMES = ["Ned", "Owen", "Finn", "Leo", "Sam", "Theo", "Max", "Eli"]
TRAITS = ["careful", "gentle", "watchful", "patient", "curious", "thoughtful"]


@dataclass
class StoryParams:
    theme: str
    contraband: str
    hiding: str
    quiet: str
    response: str
    smuggler: str
    smuggler_gender: str
    watcher: str
    watcher_gender: str
    parent: str
    trait: str
    relation: str = "siblings"
    smuggler_age: int = 5
    watcher_age: int = 7
    delay: int = 0
    seed: Optional[int] = None


KNOWLEDGE = {
    "clacker": [(
        "What is a clacker?",
        "A clacker is a toy that makes a hard clicking or knocking sound when its parts hit together. It is fun in daytime, but too noisy for bedtime."
    )],
    "satin": [(
        "What is satin?",
        "Satin is a smooth, shiny kind of cloth that feels cool and slippery. It looks gentle, but it can still whisper and slide when it moves."
    )],
    "bedtime": [(
        "Why do homes get quiet at bedtime?",
        "People get quiet at bedtime so bodies and minds can settle down to sleep. Soft voices and soft hands help everyone rest."
    )],
    "noise": [(
        "Why can a little noise feel big at night?",
        "At night everything else is quiet, so even a small sound stands out more. That can startle sleepers and make it harder to rest."
    )],
    "quiet": [(
        "What are good quiet things to hold at bedtime?",
        "Soft comfort things like a ribbon, cloth toy, or plush animal are good quiet bedtime choices. They can be held and stroked without waking anyone."
    )],
    "comfort": [(
        "Why can a soft toy help at bedtime?",
        "A soft toy gives hands something calm to hold. That can make a child feel safe without adding any noisy excitement."
    )],
    "rules": [(
        "Why do grown-ups have bedtime rules?",
        "Grown-ups use bedtime rules to help everybody feel safe and rested. Good bedtime rules keep the room calm for all the sleepers in it."
    )],
}
KNOWLEDGE_ORDER = ["clacker", "satin", "bedtime", "noise", "quiet", "comfort", "rules"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    if not sensible_responses():
        return combos
    for theme_id in ROOM_THEMES:
        for c_id, contraband in CONTRABAND.items():
            for h_id, hiding in HIDING_PLACES.items():
                if hiding_works(contraband, hiding):
                    combos.append((theme_id, c_id, h_id))
    return combos


CURATED = [
    StoryParams(
        theme="nursery_hall",
        contraband="wooden_clacker",
        hiding="satin_pillow",
        quiet="satin_ribbon",
        response="quiet_swap",
        smuggler="Lila",
        smuggler_gender="girl",
        watcher="Ned",
        watcher_gender="boy",
        parent="mother",
        trait="careful",
        relation="siblings",
        smuggler_age=5,
        watcher_age=7,
        delay=0,
    ),
    StoryParams(
        theme="attic_room",
        contraband="shell_clacker",
        hiding="quilt_fold",
        quiet="cloth_star",
        response="hall_shelf",
        smuggler="Owen",
        smuggler_gender="boy",
        watcher="Mina",
        watcher_gender="girl",
        parent="father",
        trait="gentle",
        relation="friends",
        smuggler_age=6,
        watcher_age=6,
        delay=0,
    ),
    StoryParams(
        theme="guest_room",
        contraband="tin_clacker",
        hiding="pajama_pocket",
        quiet="plush_moon",
        response="lecture",
        smuggler="Tess",
        smuggler_gender="girl",
        watcher="Finn",
        watcher_gender="boy",
        parent="mother",
        trait="watchful",
        relation="siblings",
        smuggler_age=6,
        watcher_age=5,
        delay=1,
    ),
    StoryParams(
        theme="nursery_hall",
        contraband="shell_clacker",
        hiding="satin_pillow",
        quiet="cloth_star",
        response="quiet_swap",
        smuggler="Sam",
        smuggler_gender="boy",
        watcher="Theo",
        watcher_gender="boy",
        parent="father",
        trait="patient",
        relation="siblings",
        smuggler_age=4,
        watcher_age=7,
        delay=0,
    ),
]


def pair_noun(a: Entity, b: Entity, relation: str) -> str:
    if relation == "siblings":
        if a.type == "boy" and b.type == "boy":
            return "two brothers"
        if a.type == "girl" and b.type == "girl":
            return "two sisters"
        return "a brother and a sister"
    return "two children"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    a = f["smuggler"]
    b = f["watcher"]
    theme = f["theme"]
    contraband = f["contraband"]
    hiding = f["hiding"]
    quiet = f["quiet"]
    outcome = f["outcome"]
    base = (
        f'Write a suspenseful bedtime story for a 3-to-5-year-old that includes the words '
        f'"satin", "smuggle", and "clacker". Set it in {theme.room}.'
    )
    if outcome == "averted":
        return [
            base,
            f"Tell a gentle night story where {a.id} wants to smuggle {contraband.phrase} under {hiding.phrase}, "
            f"but {b.id} quietly talks {a.pronoun('object')} out of it before any sound happens.",
            f"Write a calm suspense story that stays soft: a child nearly brings a clacker to bed, then chooses {quiet.phrase} instead.",
        ]
    if outcome == "settled":
        return [
            base,
            f"Tell a bedtime story where a hidden clacker makes one tiny sound, a grown-up comes quickly, and the room becomes peaceful again.",
            f"Write a suspenseful but gentle story about a child who tries to smuggle a clacker under the covers and learns why soft bedtime things are better.",
        ]
    return [
        base,
        f"Tell a cautionary bedtime story where the suspense breaks: the clacker wakes the baby because help comes too slowly.",
        f"Write a soft, child-facing night story that shows how one noisy choice can wake a whole sleeping house.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a = f["smuggler"]
    b = f["watcher"]
    parent = f["parent"]
    sleeper = f["sleeper"]
    contraband = f["contraband"]
    hiding = f["hiding"]
    quiet = f["quiet"]
    response = f["response"]
    relation = f["relation"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair_noun(a, b, relation)}, {a.id} and {b.id}, at bedtime. It also includes {parent.label_word} and {sleeper.label}, whose sleep the children almost disturb.",
        ),
        (
            f"What did {a.id} want to do?",
            f"{a.id} wanted to smuggle {contraband.phrase} {hiding.preposition} {hiding.phrase} for one more secret game. That choice mattered because a clacker is noisy, even in a quiet room.",
        ),
        (
            f"Why was {b.id} worried?",
            f"{b.id} was worried the clacker would make noise and wake {sleeper.label}. The room was already in bedtime quiet, so even one small clack could feel big.",
        ),
    ]
    if outcome == "averted":
        qa.append((
            f"What happened after {b.id} warned {a.id}?",
            f"{a.id} listened and gave up the plan before the clacker made any sound. {a.pronoun().capitalize()} chose {quiet.phrase} instead, which let the room stay peaceful.",
        ))
        qa.append((
            "How did the story end?",
            f"It ended quietly and safely. The children settled down with {quiet.phrase}, and everybody slept.",
        ))
    elif outcome == "settled":
        qa.append((
            "Did the clacker make a sound?",
            f"Yes. It made a tiny sound in the dark, and that was enough to make everyone tense and make {sleeper.label} stir.",
        ))
        qa.append((
            f"How did {parent.label_word} fix the problem?",
            f"{parent.label_word.capitalize()} {response.qa_text}. That quick, quiet response stopped the suspense from turning into a fully wakeful night.",
        ))
        qa.append((
            f"What did {a.id} learn?",
            f"{a.id} learned that bedtime things need to be soft and quiet. The clacker belonged to daytime play, while {quiet.phrase} was the wiser night choice.",
        ))
    else:
        qa.append((
            f"What went wrong?",
            f"The clacker made noise, and help did not come quickly enough to keep the room settled. Because the house was so quiet, the sound woke {sleeper.label}.",
        ))
        qa.append((
            "How did the story end?",
            f"It ended with the house awake and the children feeling sorry. Later the room became quiet again, but much later than it would have if the clacker had stayed out of bed.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["contraband"].tags) | set(f["hiding"].tags) | set(f["response"].tags) | set(f["quiet"].tags) | set(f["theme"].tags)
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
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        flags = [name for name, on in (("noisy", e.noisy), ("soft", e.soft), ("sleepy", e.sleepy)) if on]
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
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


def explain_rejection(contraband: Contraband, hiding: HidingPlace) -> str:
    if not hiding.bed_safe:
        return (
            f"(No story: {hiding.phrase} is not a bed-hiding place. A child could hide {contraband.phrase} there, "
            f"but that would not be a bedtime smuggle-under-the-covers story.)"
        )
    return "(No story: this combination does not create a plausible bedtime-noise risk.)"


def explain_response(rid: str) -> str:
    r = RESPONSES[rid]
    better = " / ".join(sorted(x.id for x in sensible_responses()))
    return (
        f"(Refusing response '{rid}': it scores too low on common sense (sense={r.sense} < {SENSE_MIN}). "
        f"Try a calmer bedtime response: {better}.)"
    )


def outcome_of(params: StoryParams) -> str:
    if would_confess(params.relation, params.smuggler_age, params.watcher_age, params.trait):
        return "averted"
    woke = will_wake(CONTRABAND[params.contraband], HIDING_PLACES[params.hiding], params.delay, RESPONSES[params.response])
    return "woke_house" if woke else "settled"


ASP_RULES = r"""
% --- reasonableness gate ---------------------------------------------------
hazard(C, H) :- contraband(C), hiding(H), noisy_level(C, N), N > 0, bed_safe(H).
sensible(R)  :- response(R), sense(R, S), sense_min(M), S >= M.
valid(T, C, H) :- theme(T), hazard(C, H).

% --- outcome model ---------------------------------------------------------
care_now(T, 5) :- trait(T), careful_trait(T).
care_now(T, 3) :- trait(T), not careful_trait(T).
watcher_older :- relation(siblings), watcher_age(WA), smuggler_age(SA), WA > SA.
bonus(3) :- watcher_older.
bonus(0) :- not watcher_older.
authority(C + 1 + B) :- care_now(T, C), trait(T), bonus(B).
averted :- watcher_older, authority(A), courage_init(CI), A > CI.

risk(V) :- chosen_contraband(C), noisy_level(C, N), chosen_hiding(H), muffles(H, M), delay(D), V = N - M + D, V > 0.
risk(0) :- chosen_contraband(C), noisy_level(C, N), chosen_hiding(H), muffles(H, M), delay(D), N - M + D <= 0.

settled :- chosen_response(R), speed(R, S), risk(V), S >= V.
woke_house :- not averted, chosen_response(R), speed(R, S), risk(V), S < V.

outcome(averted) :- averted.
outcome(settled) :- not averted, settled.
outcome(woke_house) :- woke_house.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for tid in ROOM_THEMES:
        lines.append(asp.fact("theme", tid))
    for cid, c in CONTRABAND.items():
        lines.append(asp.fact("contraband", cid))
        lines.append(asp.fact("noisy_level", cid, c.noise))
    for hid, h in HIDING_PLACES.items():
        lines.append(asp.fact("hiding", hid))
        lines.append(asp.fact("muffles", hid, h.muffles))
        if h.bed_safe:
            lines.append(asp.fact("bed_safe", hid))
    for qid in QUIET_THINGS:
        lines.append(asp.fact("quiet", qid))
    for rid, r in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, r.sense))
        lines.append(asp.fact("speed", rid, r.speed))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    lines.append(asp.fact("courage_init", int(COURAGE_INIT)))
    for trait in sorted(CAREFUL_TRAITS):
        lines.append(asp.fact("careful_trait", trait))
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
    scenario = "\n".join([
        asp.fact("chosen_contraband", params.contraband),
        asp.fact("chosen_hiding", params.hiding),
        asp.fact("chosen_response", params.response),
        asp.fact("delay", params.delay),
        asp.fact("relation", params.relation),
        asp.fact("smuggler_age", params.smuggler_age),
        asp.fact("watcher_age", params.watcher_age),
        asp.fact("trait", params.trait),
    ])
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

    c_sense, p_sense = set(asp_sensible()), {r.id for r in sensible_responses()}
    if c_sense == p_sense:
        print(f"OK: sensible responses match ({sorted(c_sense)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible responses: clingo={sorted(c_sense)} python={sorted(p_sense)}")

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(40):
        try:
            cases.append(resolve_params(parser.parse_args([]), random.Random(seed)))
        except StoryError:
            continue
    bad = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("Generated empty story during smoke test.")
        print("OK: smoke-tested ordinary story generation.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a child tries to smuggle a noisy clacker into bed, and the night holds its breath."
    )
    ap.add_argument("--theme", choices=ROOM_THEMES)
    ap.add_argument("--contraband", choices=CONTRABAND)
    ap.add_argument("--hiding", choices=HIDING_PLACES)
    ap.add_argument("--quiet", choices=QUIET_THINGS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], help="extra beat before help arrives; higher makes waking the house more likely")
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
    if args.hiding and not HIDING_PLACES[args.hiding].bed_safe:
        contraband = CONTRABAND[args.contraband] if args.contraband else next(iter(CONTRABAND.values()))
        raise StoryError(explain_rejection(contraband, HIDING_PLACES[args.hiding]))
    if args.contraband and args.hiding:
        c = CONTRABAND[args.contraband]
        h = HIDING_PLACES[args.hiding]
        if not hiding_works(c, h):
            raise StoryError(explain_rejection(c, h))
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))

    combos = [
        combo for combo in valid_combos()
        if (args.theme is None or combo[0] == args.theme)
        and (args.contraband is None or combo[1] == args.contraband)
        and (args.hiding is None or combo[2] == args.hiding)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    theme, contraband, hiding = rng.choice(sorted(combos))
    quiet = args.quiet or rng.choice(sorted(QUIET_THINGS))
    response = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    smuggler, sg = _pick_kid(rng)
    watcher, wg = _pick_kid(rng, avoid=smuggler)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    relation = rng.choice(["siblings", "friends"])
    smuggler_age, watcher_age = rng.sample([4, 5, 6, 7], 2)
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    return StoryParams(
        theme=theme,
        contraband=contraband,
        hiding=hiding,
        quiet=quiet,
        response=response,
        smuggler=smuggler,
        smuggler_gender=sg,
        watcher=watcher,
        watcher_gender=wg,
        parent=parent,
        trait=trait,
        relation=relation,
        smuggler_age=smuggler_age,
        watcher_age=watcher_age,
        delay=delay,
    )


def generate(params: StoryParams) -> StorySample:
    if params.theme not in ROOM_THEMES:
        raise StoryError(f"(Unknown theme: {params.theme})")
    if params.contraband not in CONTRABAND:
        raise StoryError(f"(Unknown contraband: {params.contraband})")
    if params.hiding not in HIDING_PLACES:
        raise StoryError(f"(Unknown hiding place: {params.hiding})")
    if params.quiet not in QUIET_THINGS:
        raise StoryError(f"(Unknown quiet item: {params.quiet})")
    if params.response not in RESPONSES:
        raise StoryError(f"(Unknown response: {params.response})")
    if RESPONSES[params.response].sense < SENSE_MIN:
        raise StoryError(explain_response(params.response))
    if not hiding_works(CONTRABAND[params.contraband], HIDING_PLACES[params.hiding]):
        raise StoryError(explain_rejection(CONTRABAND[params.contraband], HIDING_PLACES[params.hiding]))

    world = tell(
        theme=ROOM_THEMES[params.theme],
        contraband=CONTRABAND[params.contraband],
        hiding=HIDING_PLACES[params.hiding],
        quiet=QUIET_THINGS[params.quiet],
        response=RESPONSES[params.response],
        smuggler=params.smuggler,
        smuggler_gender=params.smuggler_gender,
        watcher=params.watcher,
        watcher_gender=params.watcher_gender,
        parent_type=params.parent,
        trait=params.trait,
        relation=params.relation,
        smuggler_age=params.smuggler_age,
        watcher_age=params.watcher_age,
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
        print(asp_program("", "#show valid/3.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (theme, contraband, hiding) combos:\n")
        for theme, contraband, hiding in combos:
            print(f"  {theme:12} {contraband:14} {hiding}")
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
                f"### {p.smuggler} & {p.watcher}: {p.contraband} in {p.hiding} "
                f"({p.theme}, {p.response}, {outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
