#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/suggest_trapezoid_misunderstanding_sound_effects_nursery_rhyme.py
================================================================================================

A small nursery-rhyme-flavored storyworld about a child in a shape-and-sound
circle who mishears a request about a trapezoid. A gentle helper suggests
checking what was really said, and the rhyme comes right again.

Run it
------
    python storyworlds/worlds/gpt-5.4/suggest_trapezoid_misunderstanding_sound_effects_nursery_rhyme.py
    python storyworlds/worlds/gpt-5.4/suggest_trapezoid_misunderstanding_sound_effects_nursery_rhyme.py --shape trapezoid --misunderstanding trap_toys
    python storyworlds/worlds/gpt-5.4/suggest_trapezoid_misunderstanding_sound_effects_nursery_rhyme.py --repair guess_louder
    python storyworlds/worlds/gpt-5.4/suggest_trapezoid_misunderstanding_sound_effects_nursery_rhyme.py --all
    python storyworlds/worlds/gpt-5.4/suggest_trapezoid_misunderstanding_sound_effects_nursery_rhyme.py --verify
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
        female = {"girl", "mother", "hen", "goose", "ewe"}
        male = {"boy", "father", "ram", "drake"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mother", "father": "father"}.get(self.type, self.type)


@dataclass
class Place:
    id: str
    name: str
    opening: str
    offered_shapes: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class ShapePiece:
    id: str
    label: str
    phrase: str
    family: str
    unusual: bool
    sturdy: bool
    tap_sound: str
    picture_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Misunderstanding:
    id: str
    heard_as: str
    needs_family: str = ""
    needs_unusual: bool = False
    severity: int = 1
    wrong_object: str = ""
    wrong_action: str = ""
    noise: str = ""
    consequence: str = ""
    qa_because: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class HelperStyle:
    id: str
    label: str
    type: str
    trait: str
    bonus: int
    opening: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Repair:
    id: str
    label: str
    sense: int
    power: int
    action_text: str
    result_text: str
    fail_text: str
    qa_text: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
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
        clone = World(self.place)
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


def _r_waits(world: World) -> list[str]:
    out: list[str] = []
    room = world.get("room")
    hero = world.get("hero")
    if room.meters["offbeat"] < THRESHOLD:
        return out
    sig = ("waits",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["embarrassment"] += 1
    out.append("__wait__")
    return out


def _r_noise(world: World) -> list[str]:
    out: list[str] = []
    room = world.get("room")
    if room.meters["noise"] < 2 * THRESHOLD:
        return out
    sig = ("confusion",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("hero").memes["confusion"] += 1
    world.get("leader").memes["concern"] += 1
    out.append("__noise__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="waits", tag="social", apply=_r_waits),
    Rule(name="noise", tag="sound", apply=_r_noise),
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


def plausible_misunderstanding(shape: ShapePiece, misunderstanding: Misunderstanding) -> bool:
    if misunderstanding.needs_family and shape.family != misunderstanding.needs_family:
        return False
    if misunderstanding.needs_unusual and not shape.unusual:
        return False
    return True


def sensible_repairs() -> list[Repair]:
    return [r for r in REPAIRS.values() if r.sense >= SENSE_MIN]


def best_repair() -> Repair:
    return max(REPAIRS.values(), key=lambda r: (r.sense, r.power))


def resolution_score(repair: Repair, helper: HelperStyle) -> int:
    return repair.power + helper.bonus


def outcome_of(params: "StoryParams") -> str:
    repair = REPAIRS[params.repair]
    helper = HELPERS[params.helper]
    misunderstanding = MISUNDERSTANDINGS[params.misunderstanding]
    return "resolved" if resolution_score(repair, helper) >= misunderstanding.severity else "wobbly"


def explain_misunderstanding(shape: ShapePiece, misunderstanding: Misunderstanding) -> str:
    if misunderstanding.needs_family and shape.family != misunderstanding.needs_family:
        return (
            f"(No story: {misunderstanding.heard_as!r} only sounds like words from the "
            f"{misunderstanding.needs_family!r} family, not {shape.label}. Pick a different "
            f"shape or a different misunderstanding.)"
        )
    if misunderstanding.needs_unusual and not shape.unusual:
        return (
            f"(No story: {shape.label} is too familiar here, so that misunderstanding is weak. "
            f"Use a stranger shape like trapezoid.)"
        )
    return "(No story: that misunderstanding does not fit this shape.)"


def explain_repair(rid: str) -> str:
    repair = REPAIRS[rid]
    better = ", ".join(sorted(r.id for r in sensible_repairs()))
    return (
        f"(Refusing repair '{rid}': it scores too low on common sense "
        f"(sense={repair.sense} < {SENSE_MIN}). Try a calmer fix such as {better}.)"
    )


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place_id, place in PLACES.items():
        for shape_id in sorted(place.offered_shapes):
            shape = SHAPES[shape_id]
            if not shape.sturdy:
                continue
            for mid, misunderstanding in MISUNDERSTANDINGS.items():
                if plausible_misunderstanding(shape, misunderstanding):
                    combos.append((place_id, shape_id, mid))
    return combos


def predict_muddle(world: World, misunderstanding: Misunderstanding) -> dict:
    sim = world.copy()
    hero = sim.get("hero")
    room = sim.get("room")
    hero.memes["confusion"] += 1
    room.meters["noise"] += 1
    room.meters["offbeat"] += 1
    if misunderstanding.noise:
        room.meters["noise"] += 1
    propagate(sim, narrate=False)
    return {
        "offbeat": room.meters["offbeat"],
        "noise": room.meters["noise"],
        "embarrassment": hero.memes["embarrassment"],
    }


def circle_setup(world: World, hero: Entity, leader: Entity, helper: Entity, shape: ShapePiece) -> None:
    hero.memes["joy"] += 1
    helper.memes["joy"] += 1
    world.say(
        f"{world.place.opening} {leader.id} set out bells, blocks, and bright picture cards. "
        f"{hero.id} and {helper.id} sat cross-legged on the rug, ready for a singing game."
    )
    world.say(
        f'The morning rhyme went, "Tap and clap, sing and slide; today we tap a {shape.label} side by side."'
    )


def request_shape(world: World, leader: Entity, hero: Entity, shape: ShapePiece) -> None:
    hero.memes["attention"] += 1
    world.say(
        f'{leader.id} smiled and said, "I suggest you tap the {shape.label}, {hero.id}, '
        f'and keep the tiny beat."'
    )


def misunderstand(world: World, hero: Entity, misunderstanding: Misunderstanding) -> None:
    pred = predict_muddle(world, misunderstanding)
    world.facts["predicted_noise"] = pred["noise"]
    world.facts["predicted_offbeat"] = pred["offbeat"]
    world.facts["predicted_embarrassment"] = pred["embarrassment"]
    hero.memes["confusion"] += 1
    world.get("room").meters["offbeat"] += 1
    if misunderstanding.noise:
        world.get("room").meters["noise"] += 2
    else:
        world.get("room").meters["noise"] += 1
    propagate(world, narrate=False)
    world.say(
        f"But {hero.id} heard {misunderstanding.heard_as!r} instead. "
        f"{hero.pronoun().capitalize()} {misunderstanding.wrong_action}."
    )
    if misunderstanding.noise:
        world.say(f"{misunderstanding.noise}! {misunderstanding.consequence}")
    else:
        world.say(misunderstanding.consequence)


def helper_suggests(world: World, helper: Entity, repair: Repair, leader: Entity) -> None:
    helper.memes["care"] += 1
    world.say(
        f"{helper.opening} {helper.id} leaned close. "
        f'"Let us not guess," {helper.pronoun()} said. "{repair.action_text}, and then the song can skip back into place."'
    )
    leader.memes["patience"] += 1


def clarify(world: World, leader: Entity, shape: ShapePiece) -> None:
    leader.memes["patience"] += 1
    world.say(
        f'{leader.id} gave a little nod and held up the picture card. '
        f'"Not {world.facts["misunderstanding"].heard_as}," {leader.pronoun()} said gently. '
        f'"The {shape.label} is this one here: {shape.picture_line}."'
    )


def repair_scene(world: World, hero: Entity, helper: Entity, repair: Repair, shape: ShapePiece) -> None:
    room = world.get("room")
    hero.memes["hope"] += 1
    if resolution_score(repair, HELPERS[world.facts["helper_style"].id]) >= MISUNDERSTANDINGS[world.facts["misunderstanding"].id].severity:
        hero.memes["confusion"] = 0.0
        hero.memes["relief"] += 1
        room.meters["offbeat"] = 0.0
        room.meters["noise"] = 0.0
        room.meters["rhythm"] += 1
        world.say(
            f"{hero.id} blinked, then laughed a little at the muddle. "
            f"{hero.pronoun().capitalize()} took {shape.phrase} in both hands and {repair.result_text}."
        )
        world.say(
            f'{shape.tap_sound}! {shape.tap_sound}! Soon every knee bobbed with the beat, '
            f'and the rhyme rolled smooth as a wagon wheel.'
        )
    else:
        room.meters["noise"] += 1
        room.meters["offbeat"] += 1
        hero.memes["confusion"] += 1
        hero.memes["embarrassment"] += 1
        propagate(world, narrate=False)
        world.say(
            f"{hero.id} tried to mend the muddle, but {repair.fail_text}. "
            f"The beat still bumped about instead of marching neatly."
        )


def closing(world: World, hero: Entity, helper: Entity, leader: Entity, shape: ShapePiece, outcome: str) -> None:
    if outcome == "resolved":
        hero.memes["joy"] += 1
        helper.memes["joy"] += 1
        world.say(
            f'So the circle sang, "Tock on the trapezoid, tap-tap-tap; when words feel foggy, stop and map." '
            f'{hero.id} knew the new shape now, and {helper.id} grinned to hear the room ring true.'
        )
    else:
        leader.memes["care"] += 1
        world.say(
            f'{leader.id} slowed the game to a hum and put {shape.phrase} beside {hero.id}. '
            f'"We can try again after one calm breath," {leader.pronoun()} said.'
        )
        world.say(
            f'The room grew softer, and though the rhyme was still a little crooked, '
            f'{hero.id} was no longer alone with the puzzly word.'
        )


def tell(
    place: Place,
    shape: ShapePiece,
    misunderstanding: Misunderstanding,
    helper_style: HelperStyle,
    repair: Repair,
    hero_name: str = "Merry",
    hero_type: str = "girl",
    leader_name: str = "Nurse Wren",
    leader_type: str = "mother",
) -> World:
    world = World(place)
    hero = world.add(Entity(id="hero", kind="character", type=hero_type, label=hero_name, phrase=hero_name, role="hero"))
    leader = world.add(Entity(id="leader", kind="character", type=leader_type, label=leader_name, phrase=leader_name, role="leader"))
    helper = world.add(Entity(
        id="helper",
        kind="character",
        type=helper_style.type,
        label=helper_style.label,
        phrase=helper_style.label,
        role="helper",
        traits=[helper_style.trait],
    ))
    piece = world.add(Entity(id="shape", kind="thing", type="shape", label=shape.label, phrase=shape.phrase, role="shape", tags=set(shape.tags)))
    room = world.add(Entity(id="room", kind="thing", type="room", label=place.name, phrase=place.name, role="room"))

    world.facts.update(
        place=place,
        shape_cfg=shape,
        misunderstanding=misunderstanding,
        helper_style=helper_style,
        repair=repair,
        hero=hero,
        helper=helper,
        leader=leader,
        piece=piece,
    )

    circle_setup(world, hero, leader, helper, shape)
    world.para()
    request_shape(world, leader, hero, shape)
    misunderstand(world, hero, misunderstanding)
    world.para()
    helper_suggests(world, helper, repair, leader)
    clarify(world, leader, shape)
    repair_scene(world, hero, helper, repair, shape)
    world.para()
    outcome = "resolved" if resolution_score(repair, helper_style) >= misunderstanding.severity else "wobbly"
    closing(world, hero, helper, leader, shape, outcome)

    world.facts.update(
        outcome=outcome,
        heard_as=misunderstanding.heard_as,
        learned_shape=outcome == "resolved",
        final_noise=room.meters["noise"],
        final_offbeat=room.meters["offbeat"],
    )
    return world


PLACES = {
    "nursery": Place(
        id="nursery",
        name="the nursery room",
        opening="In the nursery room, where the sun made squares on the floor,",
        offered_shapes={"trapezoid", "crescent", "triangle"},
        tags={"nursery"},
    ),
    "garden_ring": Place(
        id="garden_ring",
        name="the garden ring",
        opening="In the garden ring, where daisies nodded by the gate,",
        offered_shapes={"trapezoid", "crescent"},
        tags={"garden"},
    ),
}

SHAPES = {
    "trapezoid": ShapePiece(
        id="trapezoid",
        label="trapezoid",
        phrase="the wooden trapezoid block",
        family="trap",
        unusual=True,
        sturdy=True,
        tap_sound="tock",
        picture_line="a squat little shape with one short top and one broad bottom",
        tags={"shape", "trapezoid"},
    ),
    "crescent": ShapePiece(
        id="crescent",
        label="crescent",
        phrase="the moon-curved crescent block",
        family="press",
        unusual=True,
        sturdy=True,
        tap_sound="tik",
        picture_line="a moon-curved piece like a bright slice of night",
        tags={"shape", "crescent"},
    ),
    "triangle": ShapePiece(
        id="triangle",
        label="triangle",
        phrase="the three-cornered triangle tile",
        family="tri",
        unusual=False,
        sturdy=True,
        tap_sound="ting",
        picture_line="a neat little shape with three straight sides",
        tags={"shape", "triangle"},
    ),
}

MISUNDERSTANDINGS = {
    "trap_toys": Misunderstanding(
        id="trap_toys",
        heard_as="trap the toys",
        needs_family="trap",
        needs_unusual=False,
        severity=2,
        wrong_object="toy basket",
        wrong_action="hurried to the toy shelf and tucked blocks and balls into a basket as fast as she could",
        noise="clatter-clunk",
        consequence="The bells had to wait, and the circle lost its tidy beat.",
        qa_because="The word trapezoid sounded to the hero like trap the toys, so the child started cleaning instead of tapping the shape.",
        tags={"misunderstanding", "toys"},
    ),
    "bring_trumpet": Misunderstanding(
        id="bring_trumpet",
        heard_as="bring the trumpet",
        needs_family="trap",
        needs_unusual=True,
        severity=1,
        wrong_object="tin trumpet",
        wrong_action="grabbed the tin trumpet from the costume box and puffed her cheeks",
        noise="toot-toot",
        consequence="The silly horn noise bumped right across the singing game.",
        qa_because="The strange word sounded like trumpet, so the hero fetched the wrong noisemaker.",
        tags={"misunderstanding", "trumpet"},
    ),
    "fetch_present": Misunderstanding(
        id="fetch_present",
        heard_as="fetch the present",
        needs_family="press",
        needs_unusual=True,
        severity=1,
        wrong_object="ribbon parcel",
        wrong_action="lifted the ribbon parcel from the shelf and held it up proudly",
        noise="rustle-swish",
        consequence="Everyone looked at the parcel instead of the beat card.",
        qa_because="The odd shape word sounded like present, so the hero reached for a parcel instead of the shape.",
        tags={"misunderstanding", "present"},
    ),
}

HELPERS = {
    "lamb": HelperStyle(
        id="lamb",
        label="Lambkin",
        type="ewe",
        trait="patient",
        bonus=1,
        opening="Soft as a mitten",
        tags={"helper", "patient"},
    ),
    "duck": HelperStyle(
        id="duck",
        label="Dapple Duck",
        type="hen",
        trait="cheerful",
        bonus=0,
        opening="With a bright little bob",
        tags={"helper", "cheerful"},
    ),
    "crow": HelperStyle(
        id="crow",
        label="Crooked Crow",
        type="thing",
        trait="hasty",
        bonus=-1,
        opening="From the window ledge",
        tags={"helper", "hasty"},
    ),
}

REPAIRS = {
    "ask_again": Repair(
        id="ask_again",
        label="ask again",
        sense=3,
        power=2,
        action_text="ask Nurse Wren to say the shape word once more",
        result_text="copied the beat just as it was shown",
        fail_text="the word was still wobbling in her ears",
        qa_text="They asked to hear the shape word again and watched the picture card at the same time.",
        tags={"repair", "listen"},
    ),
    "picture_card": Repair(
        id="picture_card",
        label="check the picture card",
        sense=3,
        power=1,
        action_text="look at the picture card together",
        result_text="matched the picture to the right block and tapped carefully",
        fail_text="the picture helped a little, but the muddle did not quite melt",
        qa_text="They looked at the picture card so the shape could be seen as well as heard.",
        tags={"repair", "picture"},
    ),
    "guess_louder": Repair(
        id="guess_louder",
        label="guess louder",
        sense=1,
        power=0,
        action_text="just guess and make more noise",
        result_text="banged away as if noise alone could fix the mix-up",
        fail_text="guessing louder only made the muddle bigger",
        qa_text="They guessed instead of checking, which is why the mix-up stayed messy.",
        tags={"repair", "noise"},
    ),
}


@dataclass
class StoryParams:
    place: str
    shape: str
    misunderstanding: str
    helper: str
    repair: str
    hero_name: str
    hero_type: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        place="nursery",
        shape="trapezoid",
        misunderstanding="trap_toys",
        helper="lamb",
        repair="ask_again",
        hero_name="Merry",
        hero_type="girl",
    ),
    StoryParams(
        place="garden_ring",
        shape="trapezoid",
        misunderstanding="bring_trumpet",
        helper="duck",
        repair="ask_again",
        hero_name="Pip",
        hero_type="boy",
    ),
    StoryParams(
        place="nursery",
        shape="crescent",
        misunderstanding="fetch_present",
        helper="duck",
        repair="picture_card",
        hero_name="Nell",
        hero_type="girl",
    ),
    StoryParams(
        place="nursery",
        shape="trapezoid",
        misunderstanding="trap_toys",
        helper="crow",
        repair="picture_card",
        hero_name="Kit",
        hero_type="boy",
    ),
]


KNOWLEDGE = {
    "trapezoid": [
        (
            "What is a trapezoid?",
            "A trapezoid is a flat shape with one short side and one longer side that run the same way. It does not look exactly like a square or a triangle.",
        )
    ],
    "shape": [
        (
            "Why do picture cards help with shape names?",
            "Picture cards help because a child can see the shape while hearing the word. Seeing and hearing together makes confusing words easier to understand.",
        )
    ],
    "misunderstanding": [
        (
            "What is a misunderstanding?",
            "A misunderstanding happens when someone hears or understands something the wrong way. It can make people act on the wrong idea until they check again.",
        )
    ],
    "listen": [
        (
            "What can you do if you do not understand a word?",
            "You can ask someone to say it again and listen slowly. Asking again is a smart and brave way to learn.",
        )
    ],
    "picture": [
        (
            "How can a picture help with a new word?",
            "A picture shows what the word means. That helps your ears and your eyes work together.",
        )
    ],
    "noise": [
        (
            "Why can extra noise make a mix-up worse?",
            "Extra noise can cover up the words you need to hear. Then it becomes harder to understand what someone really said.",
        )
    ],
    "trumpet": [
        (
            "What sound does a trumpet make?",
            "A trumpet can make a bright toot-toot sound. It is a loud sound that is easy to notice in a room.",
        )
    ],
}
KNOWLEDGE_ORDER = ["trapezoid", "shape", "misunderstanding", "listen", "picture", "noise", "trumpet"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    misunderstanding = f["misunderstanding"]
    shape = f["shape_cfg"]
    repair = f["repair"]
    return [
        'Write a short nursery-rhyme-style story for a 3-to-5-year-old that includes the words "suggest" and "trapezoid".',
        f"Tell a gentle misunderstanding story where {hero.label} hears {misunderstanding.heard_as!r} instead of {shape.label}, and {helper.label} helps fix the mix-up.",
        f"Write a musical little story with sound effects, a shape lesson, and a calm repair where the children {repair.label} instead of guessing.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    leader = f["leader"]
    shape = f["shape_cfg"]
    misunderstanding = f["misunderstanding"]
    repair = f["repair"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.label}, {helper.label}, and {leader.label} in a singing circle. They are trying to keep a small shape rhyme in time.",
        ),
        (
            f"What did {leader.label} suggest?",
            f'{leader.label} suggested that {hero.label} tap the {shape.label}. The request was part of the morning rhyme and was meant to keep the beat small and steady.',
        ),
        (
            f"Why did {hero.label} make a mistake?",
            f"{misunderstanding.qa_because} Because of that mix-up, the room went offbeat before the right shape was shown.",
        ),
        (
            f"What did {helper.label} do to help?",
            f"{helper.label} did not tease {hero.label}. Instead, {repair.qa_text}",
        ),
    ]
    if outcome == "resolved":
        qa.append(
            (
                "How was the problem solved?",
                f"The picture and the repeated words helped {hero.label} understand the request. Then {hero.pronoun().capitalize()} tapped the {shape.label} the right way, and the rhyme sounded neat again.",
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended with the circle singing smoothly and the {shape.label} beat going {shape.tap_sound}-{shape.tap_sound}. The ending shows that checking kindly can turn a muddle into music.",
            )
        )
    else:
        qa.append(
            (
                "Did the mix-up get fixed right away?",
                f"No, not all the way. The room became calmer, but the word was still puzzly, so they slowed down and planned to try again gently.",
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended softly instead of perfectly. {hero.label} was no longer alone with the problem, even though the rhyme was still a little crooked.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = set(world.facts["shape_cfg"].tags) | set(world.facts["misunderstanding"].tags) | set(world.facts["repair"].tags)
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
    for ent in world.entities.values():
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
        lines.append(f"  {ent.id:8} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
% --- reasonableness gate ---------------------------------------------------
valid(Place, Shape, Mis) :- place(Place), offers(Place, Shape), sturdy(Shape),
                            misunderstanding(Mis), plausible(Shape, Mis).

plausible(Shape, Mis) :- misunderstanding(Mis), not needs_family(Mis, _), not needs_unusual(Mis), shape(Shape).
plausible(Shape, Mis) :- needs_family(Mis, Fam), family(Shape, Fam), not needs_unusual(Mis).
plausible(Shape, Mis) :- needs_family(Mis, Fam), family(Shape, Fam), needs_unusual(Mis), unusual(Shape).
plausible(Shape, Mis) :- not needs_family(Mis, _), needs_unusual(Mis), unusual(Shape).

sensible(Repair) :- repair(Repair), sense(Repair, S), sense_min(M), S >= M.

% --- outcome model ---------------------------------------------------------
helper_bonus(B) :- chosen_helper(H), bonus(H, B).
repair_power(P) :- chosen_repair(R), power(R, P).
mis_severity(S) :- chosen_mis(M), severity(M, S).
score(P + B) :- repair_power(P), helper_bonus(B).
resolved :- score(X), mis_severity(S), X >= S.
outcome(resolved) :- resolved.
outcome(wobbly) :- not resolved.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        for sid in sorted(place.offered_shapes):
            lines.append(asp.fact("offers", pid, sid))
    for sid, shape in SHAPES.items():
        lines.append(asp.fact("shape", sid))
        if shape.sturdy:
            lines.append(asp.fact("sturdy", sid))
        lines.append(asp.fact("family", sid, shape.family))
        if shape.unusual:
            lines.append(asp.fact("unusual", sid))
    for mid, misunderstanding in MISUNDERSTANDINGS.items():
        lines.append(asp.fact("misunderstanding", mid))
        lines.append(asp.fact("severity", mid, misunderstanding.severity))
        if misunderstanding.needs_family:
            lines.append(asp.fact("needs_family", mid, misunderstanding.needs_family))
        if misunderstanding.needs_unusual:
            lines.append(asp.fact("needs_unusual", mid))
    for hid, helper in HELPERS.items():
        lines.append(asp.fact("helper", hid))
        lines.append(asp.fact("bonus", hid, helper.bonus))
    for rid, repair in REPAIRS.items():
        lines.append(asp.fact("repair", rid))
        lines.append(asp.fact("sense", rid, repair.sense))
        lines.append(asp.fact("power", rid, repair.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible_repairs() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_helper", params.helper),
            asp.fact("chosen_repair", params.repair),
            asp.fact("chosen_mis", params.misunderstanding),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def smoke_test() -> None:
    sample = generate(CURATED[0])
    if not sample.story.strip():
        raise StoryError("Smoke test failed: generated story was empty.")
    if "trapezoid" not in sample.story:
        raise StoryError("Smoke test failed: expected story text to mention trapezoid.")


def asp_verify() -> int:
    rc = 0
    py_valid = set(valid_combos())
    asp_valid = set(asp_valid_combos())
    if py_valid == asp_valid:
        print(f"OK: gate matches valid_combos() ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if py_valid - asp_valid:
            print("  only in python:", sorted(py_valid - asp_valid))
        if asp_valid - py_valid:
            print("  only in clingo:", sorted(asp_valid - py_valid))

    py_sensible = {r.id for r in sensible_repairs()}
    asp_sensible = set(asp_sensible_repairs())
    if py_sensible == asp_sensible:
        print(f"OK: sensible repairs match ({sorted(py_sensible)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible repairs: python={sorted(py_sensible)} clingo={sorted(asp_sensible)}")

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(50):
        try:
            args = parser.parse_args([])
            params = resolve_params(args, random.Random(seed))
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
        smoke_test()
        print("OK: smoke test generated a normal story.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Nursery-rhyme storyworld: a shape-song misunderstanding, a kind suggestion, and a repaired beat."
    )
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--shape", choices=sorted(SHAPES))
    ap.add_argument("--misunderstanding", choices=sorted(MISUNDERSTANDINGS))
    ap.add_argument("--helper", choices=sorted(HELPERS))
    ap.add_argument("--repair", choices=sorted(REPAIRS))
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


GIRL_NAMES = ["Merry", "Nell", "Daisy", "Poppy", "Lark", "Tess"]
BOY_NAMES = ["Pip", "Robin", "Toby", "Milo", "Jem", "Finn"]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.shape and args.place and args.shape not in PLACES[args.place].offered_shapes:
        raise StoryError(f"(No story: {args.shape} is not one of the shape pieces in {PLACES[args.place].name}.)")

    if args.shape and args.misunderstanding:
        shape = SHAPES[args.shape]
        misunderstanding = MISUNDERSTANDINGS[args.misunderstanding]
        if not plausible_misunderstanding(shape, misunderstanding):
            raise StoryError(explain_misunderstanding(shape, misunderstanding))

    if args.repair and REPAIRS[args.repair].sense < SENSE_MIN:
        raise StoryError(explain_repair(args.repair))

    combos = [
        combo
        for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.shape is None or combo[1] == args.shape)
        and (args.misunderstanding is None or combo[2] == args.misunderstanding)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, shape_id, misunderstanding_id = rng.choice(sorted(combos))
    helper_id = args.helper or rng.choice(sorted(HELPERS))
    repair_id = args.repair or rng.choice(sorted(r.id for r in sensible_repairs()))
    hero_type = args.hero_type or rng.choice(["girl", "boy"])
    hero_name = args.hero_name or rng.choice(GIRL_NAMES if hero_type == "girl" else BOY_NAMES)

    return StoryParams(
        place=place_id,
        shape=shape_id,
        misunderstanding=misunderstanding_id,
        helper=helper_id,
        repair=repair_id,
        hero_name=hero_name,
        hero_type=hero_type,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        place = PLACES[params.place]
        shape = SHAPES[params.shape]
        misunderstanding = MISUNDERSTANDINGS[params.misunderstanding]
        helper = HELPERS[params.helper]
        repair = REPAIRS[params.repair]
    except KeyError as err:
        raise StoryError(f"(Invalid parameter key: {err.args[0]!r}.)") from None

    if params.shape not in place.offered_shapes:
        raise StoryError(f"(No story: {params.shape} is not available in {place.name}.)")
    if not plausible_misunderstanding(shape, misunderstanding):
        raise StoryError(explain_misunderstanding(shape, misunderstanding))
    if repair.sense < SENSE_MIN:
        raise StoryError(explain_repair(params.repair))

    world = tell(
        place=place,
        shape=shape,
        misunderstanding=misunderstanding,
        helper_style=helper,
        repair=repair,
        hero_name=params.hero_name,
        hero_type=params.hero_type,
    )
    story = world.render()
    if "{" in story or "}" in story:
        raise StoryError("Generated story leaked an unresolved template field.")
    return StorySample(
        params=params,
        story=story,
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
        print(asp_program("", "#show valid/3.\n#show sensible/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible repairs: {', '.join(asp_sensible_repairs())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, shape, misunderstanding) combos:\n")
        for place, shape, misunderstanding in combos:
            print(f"  {place:12} {shape:10} {misunderstanding}")
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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero_name}: {p.shape} / {p.misunderstanding} / {p.repair} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
