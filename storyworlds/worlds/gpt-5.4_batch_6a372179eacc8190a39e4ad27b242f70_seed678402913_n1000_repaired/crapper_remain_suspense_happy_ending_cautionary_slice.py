#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/crapper_remain_suspense_happy_ending_cautionary_slice.py

A standalone storyworld about a child, a bathroom mistake, a rising toilet, and
a calm grown-up who handles it sensibly. The prose stays close to slice-of-life:
an ordinary home, a small mistake, a tense middle, and an ending image that
shows the lesson will remain.

Seed words required by the batch:
- crapper
- remain

Run it
------
    python storyworlds/worlds/gpt-5.4/crapper_remain_suspense_happy_ending_cautionary_slice.py
    python storyworlds/worlds/gpt-5.4/crapper_remain_suspense_happy_ending_cautionary_slice.py --item toy_block --response plunger
    python storyworlds/worlds/gpt-5.4/crapper_remain_suspense_happy_ending_cautionary_slice.py --all
    python storyworlds/worlds/gpt-5.4/crapper_remain_suspense_happy_ending_cautionary_slice.py --qa --json
    python storyworlds/worlds/gpt-5.4/crapper_remain_suspense_happy_ending_cautionary_slice.py --verify
"""

from __future__ import annotations

import argparse
import contextlib
import copy
import io
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
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {
            "mother": "mom",
            "father": "dad",
            "grandmother": "grandma",
            "grandfather": "grandpa",
        }.get(self.type, self.type)


@dataclass
class Bathroom:
    id: str
    place: str
    detail: str
    toilet_style: str
    tags: set[str] = field(default_factory=set)


@dataclass
class ItemCfg:
    id: str
    label: str
    phrase: str
    kind: str
    visible: bool
    severity: int
    flush_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class ResponseCfg:
    id: str
    sense: int
    power: int
    handles: set[str] = field(default_factory=set)
    needs_visible: bool = False
    text: str = ""
    fail: str = ""
    qa_text: str = ""
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, bathroom: Bathroom) -> None:
        self.bathroom = bathroom
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
        clone = World(self.bathroom)
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


def _r_rising_water(world: World) -> list[str]:
    toilet = world.get("toilet")
    if toilet.meters["blocked"] < THRESHOLD or toilet.meters["flushed"] < THRESHOLD:
        return []
    sig = ("rising",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    toilet.meters["water_high"] += 1
    for ent in list(world.entities.values()):
        if ent.role in {"child", "adult"}:
            ent.memes["fear"] += 1
    return ["__rising__"]


def _r_spill(world: World) -> list[str]:
    toilet = world.get("toilet")
    floor = world.get("floor")
    severity = toilet.meters["severity"]
    if toilet.meters["water_high"] < THRESHOLD or severity < 3:
        return []
    sig = ("spill",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    floor.meters["wet"] += 1
    floor.meters["mess"] += 1
    toilet.meters["overflowed"] += 1
    for ent in list(world.entities.values()):
        if ent.role == "adult":
            ent.meters["cleanup"] += 1
    return ["__spill__"]


CAUSAL_RULES = [
    Rule(name="rising_water", tag="physical", apply=_r_rising_water),
    Rule(name="spill", tag="physical", apply=_r_spill),
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
        for sent in produced:
            if not sent.startswith("__"):
                world.say(sent)
    return produced


def response_compatible(item: ItemCfg, response: ResponseCfg) -> bool:
    if item.kind not in response.handles:
        return False
    if response.needs_visible and not item.visible:
        return False
    return True


def sensible_responses() -> list[ResponseCfg]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def fireless_severity(item: ItemCfg, delay: int) -> int:
    return item.severity + delay


def is_contained(item: ItemCfg, response: ResponseCfg, delay: int) -> bool:
    if not response_compatible(item, response):
        return False
    return response.power >= fireless_severity(item, delay)


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for bath_id in BATHROOMS:
        for item_id, item in ITEMS.items():
            for resp_id, resp in RESPONSES.items():
                if resp.sense >= SENSE_MIN and response_compatible(item, resp):
                    combos.append((bath_id, item_id, resp_id))
    return combos


def predict_trouble(world: World, item: ItemCfg) -> dict:
    sim = world.copy()
    toilet = sim.get("toilet")
    toilet.meters["blocked"] += 1
    toilet.meters["severity"] = float(item.severity)
    toilet.meters["flushed"] += 1
    propagate(sim, narrate=False)
    return {
        "water_high": toilet.meters["water_high"] >= THRESHOLD,
        "overflowed": sim.get("floor").meters["wet"] >= THRESHOLD,
    }


def introduce(world: World, child: Entity, adult: Entity, item: ItemCfg) -> None:
    world.say(
        f"Late in the afternoon, {child.id} trailed after {adult.label_word} through "
        f"{world.bathroom.place}. {world.bathroom.detail}"
    )
    world.say(
        f"{child.id} had {item.phrase} in {child.pronoun('possessive')} hand and was supposed "
        f"to carry it back to the shelf."
    )


def bathroom_beat(world: World, child: Entity, adult: Entity) -> None:
    world.say(
        f"When they passed the bathroom, {adult.label_word} gave the old {world.bathroom.toilet_style} "
        f"a quick look and said, \"This old crapper still works fine when we treat it kindly.\""
    )
    world.say(
        f"{child.id} smiled at the funny word, but the warning tucked itself into "
        f"{child.pronoun('possessive')} mind."
    )


def drop_and_hide(world: World, child: Entity, item: ItemCfg) -> None:
    child.memes["worry"] += 1
    toilet = world.get("toilet")
    item_ent = world.get("item")
    world.say(
        f"A second later, {item.phrase} slipped from {child.pronoun('possessive')} fingers and plopped "
        f"into the toilet bowl."
    )
    if item.visible:
        world.say(
            f"It bobbed there in the water, close enough to see, and {child.id}'s stomach turned cold."
        )
    else:
        world.say(
            f"It vanished under the water at once, and {child.id} could only stare at the quiet bowl."
        )
    world.say(
        f"{child.id} did not want to admit what had happened. For one shaky moment, {child.pronoun()} "
        f"hoped a flush would make the problem disappear and let everything remain secret."
    )
    toilet.meters["blocked"] += 1
    toilet.meters["severity"] = float(item.severity)
    item_ent.attrs["in_toilet"] = True


def flush(world: World, child: Entity, item: ItemCfg) -> None:
    toilet = world.get("toilet")
    toilet.meters["flushed"] += 1
    child.memes["defiance"] += 1
    propagate(world, narrate=False)
    world.say(item.flush_line)
    if toilet.meters["water_high"] >= THRESHOLD:
        world.say(
            "Instead of sliding away, the water swirled, climbed, and kept climbing."
        )
        world.say(
            f"{child.id} froze. The bowl looked full and bright and much too close to the rim."
        )


def call_for_help(world: World, child: Entity, adult: Entity) -> None:
    child.memes["honesty"] += 1
    adult.memes["care"] += 1
    world.say(f"\"{adult.label_word.capitalize()}!\" {child.id} called at last.")
    world.say(
        f"\"I dropped something in, and now the water won't stop rising!\""
    )


def rescue_success(world: World, adult: Entity, item: ItemCfg, response: ResponseCfg) -> None:
    toilet = world.get("toilet")
    floor = world.get("floor")
    toilet.meters["blocked"] = 0.0
    toilet.meters["water_high"] = 0.0
    toilet.meters["overflowed"] = 0.0
    floor.meters["wet"] = 0.0
    world.say(
        f"{adult.label_word.capitalize()} came in fast, but not wild. {adult.pronoun().capitalize()} {response.text}"
    )
    world.say(
        "For one long second the water trembled near the top. Then it slipped back down with a soft gulp."
    )
    child = world.get("child")
    child.memes["relief"] += 1
    adult.memes["relief"] += 1


def rescue_fail(world: World, adult: Entity, response: ResponseCfg) -> None:
    toilet = world.get("toilet")
    floor = world.get("floor")
    world.say(
        f"{adult.label_word.capitalize()} hurried in and {response.fail}"
    )
    toilet.meters["water_high"] += 1
    toilet.meters["severity"] += 1
    propagate(world, narrate=False)
    if floor.meters["wet"] >= THRESHOLD:
        world.say(
            "But the water lifted over the rim and spread across the bathroom tiles in a cold, shiny sheet."
        )
    child = world.get("child")
    child.memes["fear"] += 1
    adult.meters["cleanup"] += 1


def lesson(world: World, child: Entity, adult: Entity, item: ItemCfg, happy: bool) -> None:
    child.memes["lesson"] += 1
    adult.memes["love"] += 1
    if happy:
        world.say(
            f"{adult.label_word.capitalize()} wrapped a towel around the base of the toilet anyway, "
            f"just to be safe, then knelt beside {child.id}."
        )
        world.say(
            f"\"I am glad you called me,\" {adult.pronoun()} said. \"The bathroom is for people and toilet paper. "
            f"{item.label.capitalize()} should remain out of the bowl, even when you feel scared.\""
        )
        world.say(
            f"{child.id} nodded hard. \"I thought I could hide it,\" {child.pronoun()} whispered. "
            f"\"Next time I'll tell right away.\""
        )
    else:
        world.say(
            f"When the floor was mopped and the last drip was gone, {adult.label_word} sat with {child.id} "
            f"on the edge of the tub."
        )
        world.say(
            f"\"You are more important than the mess,\" {adult.pronoun()} said softly. "
            f"\"But {item.label} should remain out of the toilet, and hiding a mistake can make a little problem grow.\""
        )
        world.say(
            f"{child.id} leaned close and nodded. The bathroom smelled like soap, and the lesson felt big and plain."
        )


def ending(world: World, child: Entity, adult: Entity, item: ItemCfg, happy: bool) -> None:
    if happy:
        world.say(
            f"That evening, {item.phrase} sat back on the shelf where it belonged."
        )
        world.say(
            f"{child.id} brushed {child.pronoun('possessive')} teeth, glanced once at the quiet toilet, "
            f"and felt the worry loosen at last."
        )
        world.say(
            f"The old bathroom remained ordinary again, and that was exactly what made the ending feel good."
        )
    else:
        world.say(
            f"Later, the clean towels had to remain on the rack until the floor dried all the way."
        )
        world.say(
            f"{child.id} helped fold fresh ones beside {adult.label_word}, and the house felt calm again, "
            f"even after the scare."
        )


def tell(
    bathroom: Bathroom,
    item: ItemCfg,
    response: ResponseCfg,
    *,
    child_name: str = "Nora",
    child_gender: str = "girl",
    adult_type: str = "mother",
    trait: str = "careful",
    delay: int = 0,
) -> World:
    world = World(bathroom=bathroom)
    child = world.add(Entity(
        id="child",
        kind="character",
        type=child_gender,
        label=child_name,
        phrase=child_name,
        role="child",
        attrs={"name": child_name, "trait": trait},
    ))
    adult = world.add(Entity(
        id="adult",
        kind="character",
        type=adult_type,
        label=adult_type,
        phrase=adult_type,
        role="adult",
    ))
    toilet = world.add(Entity(
        id="toilet",
        type="toilet",
        label="toilet",
        phrase="the toilet",
        tags={"toilet"},
    ))
    world.add(Entity(
        id="floor",
        type="floor",
        label="tile floor",
        phrase="the tile floor",
        tags={"cleanup"},
    ))
    world.add(Entity(
        id="item",
        type="item",
        label=item.label,
        phrase=item.phrase,
        tags=set(item.tags),
    ))

    child.memes["trust"] += 1
    adult.memes["care"] += 1

    introduce(world, child, adult, item)
    bathroom_beat(world, child, adult)

    world.para()
    drop_and_hide(world, child, item)
    flush(world, child, item)
    call_for_help(world, child, adult)

    severity = fireless_severity(item, delay)
    world.get("toilet").meters["severity"] = float(severity)
    contained = is_contained(item, response, delay)

    if contained:
        world.para()
        rescue_success(world, adult, item, response)
        lesson(world, child, adult, item, happy=True)
        world.para()
        ending(world, child, adult, item, happy=True)
        outcome = "contained"
    else:
        world.para()
        rescue_fail(world, adult, response)
        lesson(world, child, adult, item, happy=False)
        world.para()
        ending(world, child, adult, item, happy=False)
        outcome = "overflowed"

    world.facts.update(
        bathroom=bathroom,
        item_cfg=item,
        response=response,
        child=child,
        adult=adult,
        severity=severity,
        delay=delay,
        outcome=outcome,
        predicted=predict_trouble(world, item),
    )
    return world


def pair_name(ent: Entity) -> str:
    return ent.attrs.get("name", ent.label or ent.id)


BATHROOMS = {
    "apartment": Bathroom(
        id="apartment",
        place="their small apartment",
        detail="A pan of soup was cooling in the kitchen, and socks from the laundry basket still waited to be matched.",
        toilet_style="bathroom toilet",
        tags={"home"},
    ),
    "grandpa_house": Bathroom(
        id="grandpa_house",
        place="Grandpa's house",
        detail="A radio murmured in the next room, and the hallway smelled faintly of clean towels and old wood.",
        toilet_style="hall bathroom toilet",
        tags={"home"},
    ),
    "duplex": Bathroom(
        id="duplex",
        place="their upstairs duplex",
        detail="The windows were open for evening air, and someone downstairs was clinking dishes after dinner.",
        toilet_style="old upstairs toilet",
        tags={"home"},
    ),
}

ITEMS = {
    "paper_boat": ItemCfg(
        id="paper_boat",
        label="paper boat",
        phrase="a folded paper boat",
        kind="soft",
        visible=True,
        severity=2,
        flush_line="With a tiny, guilty push, the handle went down.",
        tags={"paper", "toilet"},
    ),
    "toy_block": ItemCfg(
        id="toy_block",
        label="toy block",
        phrase="a small wooden toy block",
        kind="hard",
        visible=True,
        severity=2,
        flush_line="The handle clacked, the water spun, and the block knocked once against the porcelain.",
        tags={"toy", "toilet"},
    ),
    "paper_wad": ItemCfg(
        id="paper_wad",
        label="paper wad",
        phrase="a thick wad of toilet paper",
        kind="soft",
        visible=False,
        severity=1,
        flush_line="The flush sounded ordinary at first, which somehow made the next moment even worse.",
        tags={"paper", "toilet"},
    ),
    "washcloth": ItemCfg(
        id="washcloth",
        label="washcloth",
        phrase="a little blue washcloth",
        kind="cloth",
        visible=False,
        severity=3,
        flush_line="The handle dropped, the bowl sighed, and then the sound turned strangely heavy.",
        tags={"cloth", "toilet"},
    ),
}

RESPONSES = {
    "shutoff_glove": ResponseCfg(
        id="shutoff_glove",
        sense=4,
        power=3,
        handles={"soft", "hard"},
        needs_visible=True,
        text="reached behind the toilet to stop the water, pulled on a rubber glove, and lifted the stuck thing out before the bowl could spill",
        fail="reached behind the toilet and tried to pull the stuck thing free, but it was already wedged too deep",
        qa_text="stopped the water and lifted the stuck item out with a rubber glove",
        tags={"toilet", "glove"},
    ),
    "plunger": ResponseCfg(
        id="plunger",
        sense=3,
        power=2,
        handles={"soft"},
        needs_visible=False,
        text="grabbed the plunger from beside the sink and worked it in steady pushes until the clog broke loose",
        fail="worked the plunger again and again, but the clog held tight",
        qa_text="used the plunger in calm, steady pushes until the clog came loose",
        tags={"toilet", "plunger"},
    ),
    "plumber": ResponseCfg(
        id="plumber",
        sense=4,
        power=4,
        handles={"soft", "hard", "cloth"},
        needs_visible=False,
        text="shut the bathroom door, turned off the water, and called the building plumber, who came with a long tool and cleared the pipe",
        fail="called the plumber, but before help could arrive the bowl had already spilled over",
        qa_text="turned off the water and called a plumber with the right tool",
        tags={"toilet", "plumber"},
    ),
    "flush_again": ResponseCfg(
        id="flush_again",
        sense=1,
        power=0,
        handles={"soft", "hard", "cloth"},
        needs_visible=False,
        text="flushed again and hoped the water would sort itself out",
        fail="flushed again, which only made the water rise faster",
        qa_text="flushed again",
        tags={"toilet"},
    ),
}

GIRL_NAMES = ["Nora", "Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Maya"]
BOY_NAMES = ["Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Theo", "Eli"]
TRAITS = ["careful", "curious", "busy", "gentle", "thoughtful", "restless"]


@dataclass
class StoryParams:
    bathroom: str
    item: str
    response: str
    child_name: str
    child_gender: str
    adult_type: str
    trait: str
    delay: int = 0
    seed: Optional[int] = None


KNOWLEDGE = {
    "toilet": [
        (
            "What should go into a toilet?",
            "Only pee, poop, and toilet paper should go into a toilet. Other things can get stuck and block the pipe.",
        )
    ],
    "plunger": [
        (
            "What does a plunger do?",
            "A plunger pushes water and air back and forth to loosen a clog. Grown-ups use it carefully to help a blocked toilet or sink.",
        )
    ],
    "plumber": [
        (
            "Who fixes pipes and toilets when they clog badly?",
            "A plumber does. Plumbers have special tools to reach clogs inside pipes and fix bathroom problems safely.",
        )
    ],
    "glove": [
        (
            "Why might a grown-up wear a rubber glove in the bathroom?",
            "A rubber glove helps keep hands clean when a grown-up has to touch something wet or dirty. It is part of doing a messy job safely.",
        )
    ],
    "paper": [
        (
            "Why can wet paper clog a toilet?",
            "Wet paper can bunch up into a thick lump. If too much gathers in one place, water cannot move past it easily.",
        )
    ],
    "toy": [
        (
            "Why is a toy block bad for a toilet?",
            "A toy block is hard and does not break apart in water. It can get wedged in the pipe and stop the water from flowing.",
        )
    ],
    "cloth": [
        (
            "Why should cloth stay out of a toilet?",
            "Cloth soaks up water and can twist into a heavy knot. That can make a toilet clog much worse.",
        )
    ],
    "cleanup": [
        (
            "What should you do if water spills on a bathroom floor?",
            "Tell a grown-up right away and keep your feet careful so no one slips. Then the water can be cleaned up with towels or a mop.",
        )
    ],
}
KNOWLEDGE_ORDER = ["toilet", "paper", "toy", "cloth", "plunger", "glove", "plumber", "cleanup"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    item = f["item_cfg"]
    adult = f["adult"]
    outcome = f["outcome"]
    name = pair_name(child)
    if outcome == "contained":
        return [
            f'Write a slice-of-life story for a 3-to-5-year-old that includes the words "crapper" and "remain".',
            f"Tell a suspenseful but gentle story where {name} drops {item.phrase} into a toilet, hides the mistake with a flush, and then asks {child.pronoun('possessive')} {adult.label_word} for help before the bathroom overflows.",
            f"Write a cautionary story with a happy ending about a child learning that small bathroom mistakes do not stay small when secrets remain hidden.",
        ]
    return [
        f'Write a slice-of-life story for a 3-to-5-year-old that includes the words "crapper" and "remain".',
        f"Tell a suspenseful home story where {name} hides a toilet mistake for one moment too long and the bathroom floor gets wet before {child.pronoun('possessive')} {adult.label_word} can fix it.",
        f"Write a cautionary story that stays gentle: a child learns to tell the truth quickly after a bathroom mess grows bigger.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    adult = f["adult"]
    item = f["item_cfg"]
    response = f["response"]
    name = pair_name(child)
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {name}, a child at home, and {child.pronoun('possessive')} {adult.label_word}. The story follows one small mistake in the bathroom and what they do next.",
        ),
        (
            f"What fell into the toilet?",
            f"{item.phrase.capitalize()} fell into the toilet. That is what started the problem and made {name} feel worried.",
        ),
        (
            f"Why was the middle of the story suspenseful?",
            f"The water kept rising instead of going down, so {name} did not know if the toilet would spill. The bowl stayed close to the rim, which made every second feel tense.",
        ),
        (
            f"Why did {name} call for help?",
            f"{name} first hoped a flush would hide the mistake, but the toilet water rose instead. That made {child.pronoun('object')} understand the problem was getting bigger and could not be handled alone.",
        ),
    ]
    if f["outcome"] == "contained":
        qa.append(
            (
                f"How did {adult.label_word} fix the problem?",
                f"{adult.label_word.capitalize()} {response.qa_text}. That sensible method matched the kind of clog and stopped the bathroom from spilling over.",
            )
        )
        qa.append(
            (
                "What lesson did the child learn?",
                f"{name} learned that {item.label} should remain out of the toilet and that it is better to tell the truth quickly. Asking for help early kept a scary moment from turning into a bigger mess.",
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended calmly and happily. The bathroom returned to normal, and {item.phrase} was back where it belonged.",
            )
        )
    else:
        qa.append(
            (
                f"Did the bathroom stay dry?",
                f"No. Water spilled onto the bathroom floor before the problem was fixed. The delay gave the clog time to grow into a mess that needed extra cleanup.",
            )
        )
        qa.append(
            (
                "What lesson did the child learn?",
                f"{name} learned that hiding a mistake can make a small problem bigger. {item.label.capitalize()} should remain out of the toilet, and grown-ups can help sooner if they know what happened.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = {"toilet"}
    item = world.facts["item_cfg"]
    response = world.facts["response"]
    tags |= set(item.tags)
    tags |= set(response.tags)
    if world.facts["outcome"] == "overflowed":
        tags.add("cleanup")
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
        lines.append(f"  {ent.id:8} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        bathroom="apartment",
        item="paper_boat",
        response="shutoff_glove",
        child_name="Nora",
        child_gender="girl",
        adult_type="mother",
        trait="curious",
        delay=0,
    ),
    StoryParams(
        bathroom="grandpa_house",
        item="toy_block",
        response="shutoff_glove",
        child_name="Ben",
        child_gender="boy",
        adult_type="grandfather",
        trait="restless",
        delay=0,
    ),
    StoryParams(
        bathroom="duplex",
        item="paper_wad",
        response="plunger",
        child_name="Lucy",
        child_gender="girl",
        adult_type="father",
        trait="busy",
        delay=1,
    ),
    StoryParams(
        bathroom="apartment",
        item="washcloth",
        response="plumber",
        child_name="Max",
        child_gender="boy",
        adult_type="mother",
        trait="thoughtful",
        delay=0,
    ),
    StoryParams(
        bathroom="grandpa_house",
        item="washcloth",
        response="plunger",
        child_name="Ella",
        child_gender="girl",
        adult_type="grandmother",
        trait="gentle",
        delay=1,
    ),
]


def explain_rejection(item: ItemCfg, response: ResponseCfg) -> str:
    if response.sense < SENSE_MIN:
        return (
            f"(No story: '{response.id}' is known to the world, but it is not a sensible fix for a rising toilet. "
            f"Choose a calmer, smarter response.)"
        )
    if response.needs_visible and not item.visible:
        return (
            f"(No story: {response.id} only works when the stuck thing can still be seen, but {item.phrase} is no longer visible in the bowl.)"
        )
    if item.kind not in response.handles:
        return (
            f"(No story: {response.id} is not a good match for {item.phrase}. The fix should fit the kind of clog.)"
        )
    return "(No story: that item and response do not make a reasonable bathroom story.)"


def outcome_of(params: StoryParams) -> str:
    item = ITEMS[params.item]
    response = RESPONSES[params.response]
    return "contained" if is_contained(item, response, params.delay) else "overflowed"


ASP_RULES = r"""
sensible(R) :- response(R), sense(R, S), sense_min(M), S >= M.
compatible(I, R) :- item(I), response(R), kind(I, K), handles(R, K),
                    not need_visible(R), sensible(R).
compatible(I, R) :- item(I), response(R), kind(I, K), handles(R, K),
                    need_visible(R), visible(I), sensible(R).

valid(B, I, R) :- bathroom(B), compatible(I, R).

severity_total(V + D) :- chosen_item(I), severity(I, V), delay(D).
contained :- chosen_item(I), chosen_response(R), compatible(I, R),
             power(R, P), severity_total(S), P >= S.
outcome(contained) :- contained.
outcome(overflowed) :- not contained.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for bath_id in BATHROOMS:
        lines.append(asp.fact("bathroom", bath_id))
    for item_id, item in ITEMS.items():
        lines.append(asp.fact("item", item_id))
        lines.append(asp.fact("kind", item_id, item.kind))
        lines.append(asp.fact("severity", item_id, item.severity))
        if item.visible:
            lines.append(asp.fact("visible", item_id))
    for resp_id, resp in RESPONSES.items():
        lines.append(asp.fact("response", resp_id))
        lines.append(asp.fact("sense", resp_id, resp.sense))
        lines.append(asp.fact("power", resp_id, resp.power))
        if resp.needs_visible:
            lines.append(asp.fact("need_visible", resp_id))
        for kind in sorted(resp.handles):
            lines.append(asp.fact("handles", resp_id, kind))
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
            asp.fact("chosen_item", params.item),
            asp.fact("chosen_response", params.response),
            asp.fact("delay", params.delay),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


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

    py_sensible = {r.id for r in sensible_responses()}
    asp_sens = set(asp_sensible())
    if py_sensible == asp_sens:
        print(f"OK: sensible responses match ({sorted(py_sensible)}).")
    else:
        rc = 1
        print("MISMATCH in sensible responses:")
        print("  python:", sorted(py_sensible))
        print("  clingo:", sorted(asp_sens))

    cases = list(CURATED)
    for seed in range(50):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(params)

    mismatches = []
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            mismatches.append(params)
    if not mismatches:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {len(mismatches)}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("Smoke test generated an empty story.")
        with contextlib.redirect_stdout(io.StringIO()):
            emit(sample, trace=True, qa=True, header="### smoke")
        print("OK: smoke test generate()/emit() succeeded.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Storyworld: a child, a clogged toilet, suspense, and a lesson. Unspecified choices are randomized."
    )
    ap.add_argument("--bathroom", choices=sorted(BATHROOMS))
    ap.add_argument("--item", choices=sorted(ITEMS))
    ap.add_argument("--response", choices=sorted(RESPONSES))
    ap.add_argument("--child-name")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--adult-type", choices=["mother", "father", "grandmother", "grandfather"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], help="How long help takes after the water starts rising.")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner against Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.item and args.response:
        item = ITEMS[args.item]
        response = RESPONSES[args.response]
        if not (response.sense >= SENSE_MIN and response_compatible(item, response)):
            raise StoryError(explain_rejection(item, response))
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_rejection(ITEMS[args.item] if args.item else next(iter(ITEMS.values())), RESPONSES[args.response]))

    combos = [
        combo for combo in valid_combos()
        if (args.bathroom is None or combo[0] == args.bathroom)
        and (args.item is None or combo[1] == args.item)
        and (args.response is None or combo[2] == args.response)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    bathroom_id, item_id, response_id = rng.choice(sorted(combos))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    child_name = args.child_name or rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES)
    adult_type = args.adult_type or rng.choice(["mother", "father", "grandmother", "grandfather"])
    trait = rng.choice(TRAITS)
    delay = args.delay if args.delay is not None else rng.choice([0, 0, 1, 2])
    return StoryParams(
        bathroom=bathroom_id,
        item=item_id,
        response=response_id,
        child_name=child_name,
        child_gender=child_gender,
        adult_type=adult_type,
        trait=trait,
        delay=delay,
    )


def generate(params: StoryParams) -> StorySample:
    if params.bathroom not in BATHROOMS:
        raise StoryError(f"(Unknown bathroom: {params.bathroom})")
    if params.item not in ITEMS:
        raise StoryError(f"(Unknown item: {params.item})")
    if params.response not in RESPONSES:
        raise StoryError(f"(Unknown response: {params.response})")

    bathroom = BATHROOMS[params.bathroom]
    item = ITEMS[params.item]
    response = RESPONSES[params.response]
    if response.sense < SENSE_MIN or not response_compatible(item, response):
        raise StoryError(explain_rejection(item, response))

    world = tell(
        bathroom=bathroom,
        item=item,
        response=response,
        child_name=params.child_name,
        child_gender=params.child_gender,
        adult_type=params.adult_type,
        trait=params.trait,
        delay=params.delay,
    )
    return StorySample(
        params=params,
        story=world.render().replace("child", params.child_name).replace("adult", world.get("adult").label_word),
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
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (bathroom, item, response) combos:\n")
        for bathroom_id, item_id, response_id in combos:
            print(f"  {bathroom_id:13} {item_id:11} {response_id}")
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
            header = f"### {p.child_name}: {p.item} in {p.bathroom} ({p.response}, {outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
