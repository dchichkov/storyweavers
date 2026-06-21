#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/goldfish_toe_pl_wound_dining_room_quest.py
=====================================================================

A standalone storyworld about a small dining-room quest that turns into a tiny
injury, a caring repair, and a warm funny ending. The child wants to help a pet
goldfish with something important-looking, bumps a toe, gets a small wound, and
then finishes the quest in a calmer safer way.

The seed words "goldfish", "toe-pl", and "wound" appear naturally in the
stories. The tone stays child-facing, heartwarming, and lightly humorous.

Run it
------
    python storyworlds/worlds/gpt-5.4/goldfish_toe_pl_wound_dining_room_quest.py
    python storyworlds/worlds/gpt-5.4/goldfish_toe_pl_wound_dining_room_quest.py --mission feed
    python storyworlds/worlds/gpt-5.4/goldfish_toe_pl_wound_dining_room_quest.py --footwear socks
    python storyworlds/worlds/gpt-5.4/goldfish_toe_pl_wound_dining_room_quest.py --hazard wagon
    python storyworlds/worlds/gpt-5.4/goldfish_toe_pl_wound_dining_room_quest.py --verify
    python storyworlds/worlds/gpt-5.4/goldfish_toe_pl_wound_dining_room_quest.py --all --qa
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
# sys.path.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0
SAFETY_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"       # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    fragile: bool = False
    edible_for_fish: bool = False
    wearable: bool = False
    protective: bool = False
    on_floor: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "grandmother"}
        male = {"boy", "father", "dad", "man", "grandfather"}
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
class Mission:
    id: str
    title: str
    opening: str
    goal_text: str
    ending_text: str
    needs_safe_food: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Hazard:
    id: str
    label: str
    phrase: str
    verb: str
    severity: int
    funny_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Footwear:
    id: str
    label: str
    phrase: str
    protection: int
    quiet: bool
    plural: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Remedy:
    id: str
    label: str
    safety: int
    soothes: int
    text: str
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


def _r_wound_hurts(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    if child.meters["wound"] < THRESHOLD:
        return out
    sig = ("wound_hurts", "child")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["pain"] += 1
    child.memes["need_help"] += 1
    out.append("__ouch__")
    return out


def _r_guardian_cares(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    guardian = world.get("guardian")
    if child.memes["need_help"] < THRESHOLD:
        return out
    sig = ("guardian_cares", "child")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    guardian.memes["care"] += 1
    child.memes["trust"] += 1
    out.append("__care__")
    return out


def _r_remedy_calms(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    if child.meters["bandaged"] < THRESHOLD:
        return out
    sig = ("remedy_calms", "child")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["pain"] = 0.0
    child.memes["relief"] += 1
    child.memes["bravery"] += 1
    out.append("__relief__")
    return out


CAUSAL_RULES = [
    Rule(name="wound_hurts", tag="physical", apply=_r_wound_hurts),
    Rule(name="guardian_cares", tag="social", apply=_r_guardian_cares),
    Rule(name="remedy_calms", tag="social", apply=_r_remedy_calms),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            res = rule.apply(world)
            if res:
                changed = True
                produced.extend(s for s in res if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


MISSIONS = {
    "feed": Mission(
        id="feed",
        title="the Breakfast Pearl",
        opening="announced that the goldfish looked like a tiny king waiting for breakfast",
        goal_text="carry one safe pinch of fish flakes to the bowl",
        ending_text="the goldfish made a pleased little gulp and fanned its tail like a flag",
        needs_safe_food=True,
        tags={"goldfish", "fish_food"},
    ),
    "pebble": Mission(
        id="pebble",
        title="the Shiny Pebble",
        opening="decided the goldfish deserved its shiniest blue pebble moved to the front of the bowl",
        goal_text="bring the shiny pebble from the dish to the bowl",
        ending_text="the goldfish nosed the pebble and flashed orange around it like a bit of living sunset",
        needs_safe_food=False,
        tags={"goldfish", "pebble"},
    ),
    "song": Mission(
        id="song",
        title="the Bubble Song",
        opening="said the goldfish needed a proper dining-room song before breakfast",
        goal_text="stand by the bowl and sing the bubble song with a spoon as a baton",
        ending_text="the goldfish bobbed up twice, as if it were clapping with bubbles",
        needs_safe_food=False,
        tags={"goldfish", "song"},
    ),
}

HAZARDS = {
    "chair": Hazard(
        id="chair",
        label="chair leg",
        phrase="the crooked dining chair leg",
        verb="banged a toe on the chair leg",
        severity=2,
        funny_line="The brave knight made a face like a squashed lemon.",
        tags={"chair", "toe"},
    ),
    "table": Hazard(
        id="table",
        label="table foot",
        phrase="the heavy table foot",
        verb="stubbed a toe on the table foot",
        severity=2,
        funny_line="The grand quest paused for one very serious hop-hop-hop.",
        tags={"table", "toe"},
    ),
    "wagon": Hazard(
        id="wagon",
        label="toy wagon",
        phrase="the little toy wagon by the sideboard",
        verb="caught a toe on the toy wagon",
        severity=1,
        funny_line="Even heroes, it turned out, could be defeated by one sneaky wheel.",
        tags={"wagon", "toe"},
    ),
}

FOOTWEAR = {
    "barefoot": Footwear(
        id="barefoot",
        label="bare feet",
        phrase="bare feet",
        protection=0,
        quiet=True,
        plural=True,
        tags={"feet"},
    ),
    "socks": Footwear(
        id="socks",
        label="socks",
        phrase="soft socks",
        protection=0,
        quiet=True,
        plural=True,
        tags={"socks", "feet"},
    ),
    "slippers": Footwear(
        id="slippers",
        label="slippers",
        phrase="puffy slippers",
        protection=1,
        quiet=False,
        plural=True,
        tags={"slippers", "feet"},
    ),
}

REMEDIES = {
    "wash_bandage": Remedy(
        id="wash_bandage",
        label="wash and bandage",
        safety=3,
        soothes=3,
        text="washed the little wound, dabbed on cream, and wrapped the toe in a tiny bandage that the child proudly called a toe-pl",
        qa_text="washed the little wound and wrapped the toe in a tiny bandage called a toe-pl",
        tags={"bandage", "wound"},
    ),
    "ice_bandage": Remedy(
        id="ice_bandage",
        label="cool cloth and bandage",
        safety=3,
        soothes=2,
        text="pressed on a cool cloth, cleaned the little wound, and added a bright bandage that the child named a toe-pl",
        qa_text="used a cool cloth, cleaned the little wound, and added a bright toe-pl bandage",
        tags={"bandage", "wound"},
    ),
    "kiss_only": Remedy(
        id="kiss_only",
        label="kiss only",
        safety=1,
        soothes=1,
        text="kissed the toe and called it fixed",
        qa_text="kissed the toe and called it fixed",
        tags={"comfort"},
    ),
}

CHILD_NAMES = ["Lily", "Mia", "Nora", "Ava", "Ben", "Leo", "Max", "Theo"]
TRAITS = ["careful", "bright", "bouncy", "gentle", "curious", "cheerful"]


def wound_severity(hazard: Hazard, footwear: Footwear) -> int:
    return max(0, hazard.severity - footwear.protection)


def hazard_real(hazard: Hazard, footwear: Footwear) -> bool:
    return wound_severity(hazard, footwear) > 0


def sensible_remedies() -> list[Remedy]:
    return [r for r in REMEDIES.values() if r.safety >= SAFETY_MIN]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for mission_id in MISSIONS:
        for hazard_id, hazard in HAZARDS.items():
            for footwear_id, footwear in FOOTWEAR.items():
                if hazard_real(hazard, footwear):
                    combos.append((mission_id, hazard_id, footwear_id))
    return combos


@dataclass
class StoryParams:
    mission: str
    hazard: str
    footwear: str
    remedy: str
    child_name: str
    child_gender: str
    guardian: str
    trait: str
    fish_name: str
    seed: Optional[int] = None


def introduce(world: World, child: Entity, guardian: Entity, mission: Mission, fish: Entity, footwear: Footwear) -> None:
    world.say(
        f"In the dining room, {child.id} stood beside the table in {footwear.phrase} and "
        f"{mission.opening}. On the sideboard, {fish.id} the goldfish blinked from a round bowl "
        f"as if the whole room were a kingdom made for watching."
    )
    world.say(
        f'"This is Quest {mission.title}!" {child.id} said. '
        f'{guardian.label_word.capitalize()} smiled and gave a small bow from the napkin drawer.'
    )


def announce_goal(world: World, child: Entity, mission: Mission) -> None:
    child.memes["eager"] += 1
    world.say(
        f"The job was simple and grand at the same time: {mission.goal_text}. "
        f"That made {child.id} walk with the careful face of someone carrying treasure."
    )


def start_mission(world: World, child: Entity, mission: Mission) -> None:
    if mission.id == "song":
        world.say(
            f"{child.id} lifted a spoon like a silver baton and marched between the chairs."
        )
    elif mission.id == "pebble":
        world.say(
            f"{child.id} pinched the blue pebble in one hand and stretched the other arm out for balance."
        )
    else:
        world.say(
            f"{child.id} held the fish flakes in a tiny pinched hand and tiptoed toward the bowl."
        )


def trip(world: World, child: Entity, hazard: Hazard, footwear: Footwear) -> None:
    child.meters["wound"] += wound_severity(hazard, footwear)
    child.meters["toe_wound"] += 1
    child.meters["stopped"] += 1
    propagate(world, narrate=False)
    world.say(
        f"But halfway through the dining room, {child.id} {hazard.verb}. "
        f'"Ow!" {child.pronoun()} yelped, and the quest stopped in the middle of one step. '
        f"{hazard.funny_line}"
    )
    world.say(
        f"There was only a little wound on {child.pronoun('possessive')} toe, but little wounds can feel very big when they surprise you."
    )


def comfort(world: World, guardian: Entity, child: Entity, fish: Entity) -> None:
    guardian.memes["care"] += 1
    child.memes["sad"] += 1
    world.say(
        f"{guardian.label_word.capitalize()} came quickly, knelt on the dining-room rug, and looked at the toe. "
        f'"Oh, my brave helper," {guardian.pronoun()} said. "That is a small wound, but it still deserves gentle hands."'
    )
    world.say(
        f"From the bowl, {fish.id} the goldfish turned in a slow orange circle, as if checking whether the hero was all right."
    )


def remedy_scene(world: World, guardian: Entity, child: Entity, remedy: Remedy) -> None:
    child.meters["bandaged"] += 1
    child.meters["cleaned"] += 1
    propagate(world, narrate=False)
    world.say(
        f"At the dining-room sideboard, {guardian.label_word} {remedy.text}. "
        f'{child.id} looked down and gave a watery little laugh. "My toe-pl makes me look important," '
        f'{child.pronoun()} said.'
    )


def slower_plan(world: World, guardian: Entity, child: Entity, mission: Mission, fish: Entity) -> None:
    child.memes["careful"] += 1
    guardian.memes["pride"] += 1
    world.say(
        f'"A quest can be slow and still be brave," {guardian.label_word} said. '
        f'Together they tried again, this time with smaller steps and one steady hand near the bowl.'
    )
    if mission.id == "feed":
        world.say(
            f"The flakes reached the water at last, and {fish.id} nibbled them with tiny happy pecks."
        )
    elif mission.id == "pebble":
        world.say(
            f"The blue pebble touched the glass with one soft tick, and {fish.id} drifted over to inspect the new treasure."
        )
    else:
        world.say(
            f"{child.id} sang the bubble song in a brave but careful voice, and the spoon-baton waved only a little."
        )
    world.say(mission.ending_text + ".")


def ending(world: World, child: Entity, guardian: Entity, fish: Entity) -> None:
    child.memes["joy"] += 1
    child.memes["love"] += 1
    world.say(
        f"Then {child.id} sat in a chair with the bandaged foot sticking out very grandly. "
        f'{guardian.label_word.capitalize()} called the hero "Sir Toe-pl of the Dining Room," and {child.pronoun()} giggled so hard '
        f"that even {fish.id} seemed to wobble with the joke."
    )
    world.say(
        f"The wound was small, the care was big, and the dining room felt warm again."
    )


def tell(
    mission: Mission,
    hazard: Hazard,
    footwear: Footwear,
    remedy: Remedy,
    child_name: str,
    child_gender: str,
    guardian_type: str,
    trait: str,
    fish_name: str,
) -> World:
    world = World()
    child = world.add(Entity(
        id="child",
        kind="character",
        type=child_gender,
        label=child_name,
        phrase=child_name,
        role="child",
        traits=[trait],
    ))
    guardian = world.add(Entity(
        id="guardian",
        kind="character",
        type=guardian_type,
        label="the grown-up",
        phrase="the grown-up",
        role="guardian",
    ))
    fish = world.add(Entity(
        id="fish",
        kind="thing",
        type="goldfish",
        label=fish_name,
        phrase=f"{fish_name} the goldfish",
        role="fish",
    ))
    hazard_ent = world.add(Entity(
        id="hazard",
        kind="thing",
        type="hazard",
        label=hazard.label,
        phrase=hazard.phrase,
        on_floor=True,
    ))
    shoes = world.add(Entity(
        id="footwear",
        kind="thing",
        type="footwear",
        label=footwear.label,
        phrase=footwear.phrase,
        wearable=True,
        protective=footwear.protection > 0,
    ))

    world.facts["display_child_name"] = child_name
    world.facts["display_guardian"] = guardian.label_word
    world.facts["display_fish_name"] = fish_name

    introduce(world, child, guardian, mission, fish, footwear)
    announce_goal(world, child, mission)
    world.para()
    start_mission(world, child, mission)
    trip(world, child, hazard, footwear)
    comfort(world, guardian, child, fish)
    world.para()
    remedy_scene(world, guardian, child, remedy)
    slower_plan(world, guardian, child, mission, fish)
    ending(world, child, guardian, fish)

    world.facts.update(
        mission=mission,
        hazard=hazard,
        footwear=footwear,
        remedy=remedy,
        child=child,
        guardian=guardian,
        fish=fish,
        wound=child.meters["wound"] >= THRESHOLD,
        toe_wound=child.meters["toe_wound"] >= THRESHOLD,
        bandaged=child.meters["bandaged"] >= THRESHOLD,
        safe_again=child.memes["relief"] >= THRESHOLD or child.meters["bandaged"] >= THRESHOLD,
    )
    return world


KNOWLEDGE = {
    "goldfish": [
        (
            "What is a goldfish?",
            "A goldfish is a small fish that people sometimes keep as a pet in a bowl or tank. It needs clean water and the right food."
        )
    ],
    "fish_food": [
        (
            "What should pet fish eat?",
            "Pet fish should eat fish food that is made for them. Grown-ups help choose the right amount so the water stays clean."
        )
    ],
    "pebble": [
        (
            "Why do bowls sometimes have pebbles in them?",
            "Pebbles can make a fish bowl look bright and interesting. They are decorations, not snacks."
        )
    ],
    "song": [
        (
            "Can pets hear people talking or singing nearby?",
            "Many pets notice sounds and movement around them. A gentle voice can become part of a calm routine."
        )
    ],
    "toe": [
        (
            "Why does a stubbed toe hurt so much?",
            "Toes have lots of nerves and they hit hard edges first when you bump them. That makes a tiny bump feel big for a moment."
        )
    ],
    "wound": [
        (
            "What is a wound?",
            "A wound is a place where skin gets hurt, like a scrape or small cut. It should be cleaned so it can heal."
        )
    ],
    "bandage": [
        (
            "What does a bandage do?",
            "A bandage covers a hurt spot and helps keep it clean. It can also make a child feel cared for and protected."
        )
    ],
    "slippers": [
        (
            "What are slippers for?",
            "Slippers are soft shoes people wear inside the house. Some slippers can help protect feet from cold floors and little bumps."
        )
    ],
    "socks": [
        (
            "Do socks stop hard bumps?",
            "Socks make feet warm, but they do not do much to stop a toe from hitting a hard chair. They are soft, not strong."
        )
    ],
}

KNOWLEDGE_ORDER = ["goldfish", "fish_food", "pebble", "song", "toe", "wound", "bandage", "slippers", "socks"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child_name = f["display_child_name"]
    fish_name = f["display_fish_name"]
    mission = f["mission"]
    return [
        f'Write a heartwarming story for a 3-to-5-year-old set in a dining room that includes the words "goldfish", "toe-pl", and "wound".',
        f"Tell a gentle quest story where {child_name} tries to help {fish_name} the goldfish, bumps a toe, and is cared for by a grown-up before finishing the quest.",
        f'Write a humorous but tender story in which a tiny injury leads to a silly title like "Sir Toe-pl," and the ending proves the child feels safe again.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child_name = f["display_child_name"]
    guardian_word = f["display_guardian"]
    fish_name = f["display_fish_name"]
    mission = f["mission"]
    hazard = f["hazard"]
    remedy = f["remedy"]
    footwear = f["footwear"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child_name}, a grown-up {guardian_word}, and {fish_name} the goldfish in the dining room. The little quest begins because {child_name} wants to do something important for the goldfish."
        ),
        (
            f"What was Quest {mission.title}?",
            f"It was the plan to {mission.goal_text}. The quest made an ordinary dining-room job feel brave and funny."
        ),
        (
            f"How did {child_name} get hurt?",
            f"{child_name} {hazard.verb}. That made a small wound on the toe and stopped the quest for a moment."
        ),
        (
            f"Why did the story mention {footwear.label}?",
            f"{child_name} was wearing {footwear.phrase} during the quest across the dining room. That detail matters because house things can still hurt little toes when someone is hurrying."
        ),
    ]
    if f["bandaged"]:
        qa.append(
            (
                f"How did the grown-up help after the wound?",
                f"The {guardian_word} {remedy.qa_text}. Cleaning and covering the toe helped the pain settle and let the child feel brave again."
            )
        )
    qa.append(
        (
            "Why was the toe-pl funny?",
            f'The child gave the tiny bandage a grand silly name: "toe-pl." The joke made the hurt feel smaller and turned the repair into part of the adventure.'
        )
    )
    qa.append(
        (
            "How did the story end?",
            f"{child_name} finished the quest more carefully, and {fish_name} the goldfish seemed pleased. The ending shows that the wound was small but the care around it was big."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["mission"].tags) | set(f["hazard"].tags) | set(f["remedy"].tags) | set(f["footwear"].tags)
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
        flags = [name for name, on in (
            ("fragile", ent.fragile),
            ("edible_for_fish", ent.edible_for_fish),
            ("wearable", ent.wearable),
            ("protective", ent.protective),
            ("on_floor", ent.on_floor),
        ) if on]
        if flags:
            bits.append(f"flags={flags}")
        lines.append(f"  {ent.id:9} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        mission="feed",
        hazard="chair",
        footwear="barefoot",
        remedy="wash_bandage",
        child_name="Lily",
        child_gender="girl",
        guardian="mother",
        trait="careful",
        fish_name="Sunny",
    ),
    StoryParams(
        mission="pebble",
        hazard="table",
        footwear="socks",
        remedy="ice_bandage",
        child_name="Ben",
        child_gender="boy",
        guardian="grandfather",
        trait="curious",
        fish_name="Goldie",
    ),
    StoryParams(
        mission="song",
        hazard="wagon",
        footwear="barefoot",
        remedy="wash_bandage",
        child_name="Nora",
        child_gender="girl",
        guardian="father",
        trait="cheerful",
        fish_name="Pip",
    ),
    StoryParams(
        mission="feed",
        hazard="table",
        footwear="slippers",
        remedy="ice_bandage",
        child_name="Theo",
        child_gender="boy",
        guardian="mother",
        trait="bright",
        fish_name="Comet",
    ),
]


def explain_hazard(hazard: Hazard, footwear: Footwear) -> str:
    return (
        f"(No story: with {footwear.phrase}, {hazard.phrase} would not make a real toe wound in this small world. "
        f"The story needs an actual little wound so the care and repair are honest.)"
    )


def explain_remedy(remedy: Remedy) -> str:
    return (
        f"(Refusing remedy '{remedy.id}': it is too weak for a wound story "
        f"(safety={remedy.safety} < {SAFETY_MIN}). A caring grown-up should clean and bandage the toe.)"
    )


def outcome_of(params: StoryParams) -> str:
    if not hazard_real(HAZARDS[params.hazard], FOOTWEAR[params.footwear]):
        return "no_wound"
    if REMEDIES[params.remedy].safety >= SAFETY_MIN:
        return "healed"
    return "poor_care"


ASP_RULES = r"""
real_hazard(H, F) :- hazard(H), footwear(F), severity(H, S), protection(F, P), S > P.
sensible_remedy(R) :- remedy(R), safety(R, S), safety_min(M), S >= M.
valid(Ms, H, F) :- mission(Ms), real_hazard(H, F).

outcome(no_wound) :- chosen_hazard(H), chosen_footwear(F), not real_hazard(H, F).
outcome(healed) :- chosen_hazard(H), chosen_footwear(F), real_hazard(H, F),
                   chosen_remedy(R), sensible_remedy(R).
outcome(poor_care) :- chosen_hazard(H), chosen_footwear(F), real_hazard(H, F),
                      chosen_remedy(R), not sensible_remedy(R).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for mission_id in MISSIONS:
        lines.append(asp.fact("mission", mission_id))
    for hazard_id, hazard in HAZARDS.items():
        lines.append(asp.fact("hazard", hazard_id))
        lines.append(asp.fact("severity", hazard_id, hazard.severity))
    for footwear_id, footwear in FOOTWEAR.items():
        lines.append(asp.fact("footwear", footwear_id))
        lines.append(asp.fact("protection", footwear_id, footwear.protection))
    for remedy_id, remedy in REMEDIES.items():
        lines.append(asp.fact("remedy", remedy_id))
        lines.append(asp.fact("safety", remedy_id, remedy.safety))
    lines.append(asp.fact("safety_min", SAFETY_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible_remedies() -> list[str]:
    import asp
    model = asp.one_model(asp_program("", "#show sensible_remedy/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible_remedy"))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join([
        asp.fact("chosen_hazard", params.hazard),
        asp.fact("chosen_footwear", params.footwear),
        asp.fact("chosen_remedy", params.remedy),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def _smoke_emit(sample: StorySample) -> None:
    emit(sample, trace=False, qa=False, header="")


def asp_verify() -> int:
    rc = 0
    clingo_valid = set(asp_valid_combos())
    python_valid = set(valid_combos())
    if clingo_valid == python_valid:
        print(f"OK: gate matches valid_combos() ({len(clingo_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_valid - python_valid:
            print("  only in clingo:", sorted(clingo_valid - python_valid))
        if python_valid - clingo_valid:
            print("  only in python:", sorted(python_valid - clingo_valid))

    clingo_sensible = set(asp_sensible_remedies())
    python_sensible = {r.id for r in sensible_remedies()}
    if clingo_sensible == python_sensible:
        print(f"OK: sensible remedies match ({sorted(clingo_sensible)}).")
    else:
        rc = 1
        print(
            f"MISMATCH in sensible remedies: clingo={sorted(clingo_sensible)} "
            f"python={sorted(python_sensible)}"
        )

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(40):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(params)

    mismatches = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            mismatches += 1
    if mismatches == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {mismatches}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        _smoke_emit(sample)
        print("OK: smoke generation/emit passed.")
    except Exception as exc:  # pragma: no cover - verify path only
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Storyworld: a dining-room quest, a stubbed toe, and a warm repair."
    )
    ap.add_argument("--mission", choices=MISSIONS)
    ap.add_argument("--hazard", choices=HAZARDS)
    ap.add_argument("--footwear", choices=FOOTWEAR)
    ap.add_argument("--remedy", choices=REMEDIES)
    ap.add_argument("--guardian", choices=["mother", "father", "grandmother", "grandfather"])
    ap.add_argument("--child-name")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--fish-name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible (mission, hazard, footwear) combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_child(rng: random.Random, explicit_gender: Optional[str]) -> tuple[str, str]:
    gender = explicit_gender or rng.choice(["girl", "boy"])
    if gender == "girl":
        return rng.choice([n for n in CHILD_NAMES if n in {"Lily", "Mia", "Nora", "Ava"}]), gender
    return rng.choice([n for n in CHILD_NAMES if n in {"Ben", "Leo", "Max", "Theo"}]), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.hazard and args.footwear:
        hazard = HAZARDS[args.hazard]
        footwear = FOOTWEAR[args.footwear]
        if not hazard_real(hazard, footwear):
            raise StoryError(explain_hazard(hazard, footwear))
    if args.remedy and REMEDIES[args.remedy].safety < SAFETY_MIN:
        raise StoryError(explain_remedy(REMEDIES[args.remedy]))

    combos = [
        combo for combo in valid_combos()
        if (args.mission is None or combo[0] == args.mission)
        and (args.hazard is None or combo[1] == args.hazard)
        and (args.footwear is None or combo[2] == args.footwear)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    mission_id, hazard_id, footwear_id = rng.choice(sorted(combos))
    remedy_id = args.remedy or rng.choice(sorted(r.id for r in sensible_remedies()))
    child_name, child_gender = _pick_child(rng, args.child_gender)
    return StoryParams(
        mission=mission_id,
        hazard=hazard_id,
        footwear=footwear_id,
        remedy=remedy_id,
        child_name=args.child_name or child_name,
        child_gender=child_gender,
        guardian=args.guardian or rng.choice(["mother", "father", "grandmother", "grandfather"]),
        trait=rng.choice(TRAITS),
        fish_name=args.fish_name or rng.choice(["Sunny", "Goldie", "Pip", "Comet", "Marigold"]),
    )


def generate(params: StoryParams) -> StorySample:
    if params.mission not in MISSIONS:
        raise StoryError(f"(Unknown mission: {params.mission})")
    if params.hazard not in HAZARDS:
        raise StoryError(f"(Unknown hazard: {params.hazard})")
    if params.footwear not in FOOTWEAR:
        raise StoryError(f"(Unknown footwear: {params.footwear})")
    if params.remedy not in REMEDIES:
        raise StoryError(f"(Unknown remedy: {params.remedy})")
    if params.guardian not in {"mother", "father", "grandmother", "grandfather"}:
        raise StoryError(f"(Unknown guardian: {params.guardian})")
    if not hazard_real(HAZARDS[params.hazard], FOOTWEAR[params.footwear]):
        raise StoryError(explain_hazard(HAZARDS[params.hazard], FOOTWEAR[params.footwear]))
    if REMEDIES[params.remedy].safety < SAFETY_MIN:
        raise StoryError(explain_remedy(REMEDIES[params.remedy]))

    world = tell(
        mission=MISSIONS[params.mission],
        hazard=HAZARDS[params.hazard],
        footwear=FOOTWEAR[params.footwear],
        remedy=REMEDIES[params.remedy],
        child_name=params.child_name,
        child_gender=params.child_gender,
        guardian_type=params.guardian,
        trait=params.trait,
        fish_name=params.fish_name,
    )

    # Replace internal ids with display names in prose-facing outputs.
    story = world.render()
    story = story.replace("child", params.child_name)
    story = story.replace("guardian", world.facts["display_guardian"])
    story = story.replace("fish", params.fish_name)

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
        print(asp_program("", "#show valid/3.\n#show sensible_remedy/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible remedies: {', '.join(asp_sensible_remedies())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (mission, hazard, footwear) combos:\n")
        for mission_id, hazard_id, footwear_id in combos:
            print(f"  {mission_id:8} {hazard_id:6} {footwear_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        for params in CURATED:
            sample = generate(params)
            samples.append(sample)
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

    for idx, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.child_name}: {p.mission} in the dining room ({p.hazard}, {p.footwear})"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
