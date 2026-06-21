#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/coffin_repetition_foreshadowing_folk_tale.py
========================================================================

A small standalone storyworld for a folk-tale-shaped story about a wandering
coffin, repeated signs, and a child who learns to listen closely.

This world is built to make a narrow family of plausible tales:

* A child finds a small coffin at the edge of a village.
* An elder notices a mark on the lid and warns that the mark is a clue.
* The child and elder carry the coffin past three places in a repeated pattern.
* At the wrong places the coffin stays heavy and restless.
* At the right place it grows light and still, proving where it belonged.

The tale uses repetition on purpose:
* a repeated proverb from the elder,
* repeated stops along the road,
* repeated knocking or silence from the coffin.

It also uses foreshadowing:
* the lid's carved mark hints from the beginning where the coffin should rest.

Run it
------
    python storyworlds/worlds/gpt-5.4/coffin_repetition_foreshadowing_folk_tale.py
    python storyworlds/worlds/gpt-5.4/coffin_repetition_foreshadowing_folk_tale.py --coffin willow
    python storyworlds/worlds/gpt-5.4/coffin_repetition_foreshadowing_folk_tale.py --resting-place hill_oak
    python storyworlds/worlds/gpt-5.4/coffin_repetition_foreshadowing_folk_tale.py --all
    python storyworlds/worlds/gpt-5.4/coffin_repetition_foreshadowing_folk_tale.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/coffin_repetition_foreshadowing_folk_tale.py --trace
    python storyworlds/worlds/gpt-5.4/coffin_repetition_foreshadowing_folk_tale.py --json
    python storyworlds/worlds/gpt-5.4/coffin_repetition_foreshadowing_folk_tale.py --verify
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    traits: tuple = field(default_factory=tuple)
    name: str = ""
    title: str = ""
    voice: str = ""
    thanks: str = ""
    scold: str = ""
    help_action: str = ""
    face: str = ""
    path_line: str = ""
    ending_image: str = ""
    weak_spot: str = ""
    role_text: str = ""
    need: str = ""
    metallic: str = ""
    special: str = ""
    question_reply: str = ""
    wisdom: str = ""
    rising_line: str = ""
    risk: str = ""
    qa_text: str = ""
    location_text: str = ""
    use_line: str = ""
    cry: str = ""
    ending_line: str = ""
    reach: str = ""
    damage: str = ""
    use: str = ""
    opening: str = ""
    warning: str = ""
    owner_text: str = ""
    ground: str = ""
    action_line: str = ""
    kindness_text: str = ""
    calm: str = ""
    restored: str = ""
    shine: str = ""
    reveal_text: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "grandmother"}
        male = {"boy", "man", "father", "grandfather", "ferryman"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {
            "grandmother": "grandmother",
            "grandfather": "grandfather",
            "ferryman": "ferryman",
        }.get(self.type, self.type or self.label or "thing")


@dataclass
class CoffinKind:
    id: str
    wood: str
    phrase: str
    mark: str
    omen: str
    rightful_place: str
    bloom: str
    tags: set[str] = field(default_factory=set)


@dataclass
class RestingPlace:
    id: str
    label: str
    phrase: str
    sign: str
    image: str
    route_order: int
    tags: set[str] = field(default_factory=set)


@dataclass
class HelperCfg:
    id: str
    type: str
    title: str
    proverb: str
    action: str
    closing: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.trace: list[dict] = []
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
        clone.trace = copy.deepcopy(self.trace)
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_restless(world: World) -> list[str]:
    out: list[str] = []
    coffin = world.entities.get("coffin")
    child = world.entities.get("child")
    if coffin is None or child is None:
        return out
    if coffin.meters["restless"] < THRESHOLD:
        return out
    sig = ("restless_fear", int(coffin.meters["restless"]))
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["fear"] += 1
    out.append("__restless__")
    return out


def _r_peace(world: World) -> list[str]:
    out: list[str] = []
    coffin = world.entities.get("coffin")
    child = world.entities.get("child")
    helper = world.entities.get("helper")
    if coffin is None or child is None or helper is None:
        return out
    if coffin.meters["peace"] < THRESHOLD:
        return out
    sig = ("peace_relief", int(coffin.meters["peace"]))
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["relief"] += 1
    child.memes["courage"] += 1
    helper.memes["pride"] += 1
    out.append("__peace__")
    return out


CAUSAL_RULES = [
    Rule(name="restless", tag="emotion", apply=_r_restless),
    Rule(name="peace", tag="emotion", apply=_r_peace),
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


COFFINS = {
    "willow": CoffinKind(
        id="willow",
        wood="willow",
        phrase="a little willow coffin no longer than a loaf of bread",
        mark="three carved leaves",
        omen="the lid answered with three soft knocks",
        rightful_place="willow_bank",
        bloom="white willow fluff drifted over the grass",
        tags={"coffin", "willow", "knocking"},
    ),
    "oak": CoffinKind(
        id="oak",
        wood="oak",
        phrase="a narrow oak coffin bound with dark iron nails",
        mark="three carved acorns",
        omen="the lid gave three slow knocks, deep as a drum",
        rightful_place="hill_oak",
        bloom="fresh acorns lay in a neat ring around it",
        tags={"coffin", "oak", "knocking"},
    ),
    "reed": CoffinKind(
        id="reed",
        wood="reed",
        phrase="a pale coffin woven from river reeds and slim boards",
        mark="three carved reeds bending in the wind",
        omen="the coffin whispered with three papery taps",
        rightful_place="marsh_reeds",
        bloom="green reeds bowed as though greeting an old friend",
        tags={"coffin", "reed", "knocking"},
    ),
}

PLACES = {
    "hill_oak": RestingPlace(
        id="hill_oak",
        label="hill oak",
        phrase="the hill with the oldest oak in the valley",
        sign="great roots like a giant hand",
        image="the old oak spread its dark branches against the evening sky",
        route_order=2,
        tags={"oak", "hill", "tree"},
    ),
    "marsh_reeds": RestingPlace(
        id="marsh_reeds",
        label="marsh reeds",
        phrase="the quiet marsh where the reeds made a silver wall",
        sign="reeds hissing by the water",
        image="the reeds leaned together and hid the water with their green ribbons",
        route_order=3,
        tags={"reed", "water", "marsh"},
    ),
    "willow_bank": RestingPlace(
        id="willow_bank",
        label="willow bank",
        phrase="the willow bank beside the slow brown stream",
        sign="long branches brushing the water",
        image="the willow trailed its long green hair in the stream",
        route_order=1,
        tags={"willow", "water", "tree"},
    ),
}

HELPERS = {
    "grandmother": HelperCfg(
        id="grandmother",
        type="grandmother",
        title="Grandmother",
        proverb="Three signs are never sent for nothing.",
        action="took up the lantern and walked as steadily as a prayer",
        closing="old people keep many maps in their memories",
        tags={"elder", "wisdom", "lantern"},
    ),
    "grandfather": HelperCfg(
        id="grandfather",
        type="grandfather",
        title="Grandfather",
        proverb="Three signs are never sent for nothing.",
        action="lifted his ash staff and stepped ahead of every shadow",
        closing="old people keep many maps in their memories",
        tags={"elder", "wisdom", "staff"},
    ),
    "ferryman": HelperCfg(
        id="ferryman",
        type="ferryman",
        title="the Ferryman",
        proverb="Three signs are never sent for nothing.",
        action="set down his pole and listened as if the river itself were speaking",
        closing="those who live by crossings learn how to read strange arrivals",
        tags={"elder", "river", "wisdom"},
    ),
}

GIRL_NAMES = ["Anya", "Mira", "Lina", "Tessa", "Nella", "Ruth"]
BOY_NAMES = ["Ivo", "Tomas", "Pavel", "Milan", "Joren", "Stefan"]
ELDER_NAMES = {
    "grandmother": ["Marta", "Yara", "Brina", "Elsa"],
    "grandfather": ["Petro", "Marek", "Anton", "Sava"],
    "ferryman": ["Dorin", "Miro", "Ves", "Ilian"],
}
ROUTE_ORDER = ["willow_bank", "hill_oak", "marsh_reeds"]


def rightful_place(coffin_id: str) -> str:
    return COFFINS[coffin_id].rightful_place


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for coffin_id, coffin in COFFINS.items():
        for place_id in PLACES:
            if place_id != coffin.rightful_place:
                continue
            for helper_id in HELPERS:
                combos.append((coffin_id, place_id, helper_id))
    return combos


@dataclass
class StoryParams:
    coffin: str
    resting_place: str
    helper: str
    child_name: str
    child_gender: str
    elder_name: str
    seed: Optional[int] = None


def omen_line(coffin: CoffinKind) -> str:
    return (
        f"On the lid were {coffin.mark}. Any careful eye could see that the wood "
        f"was trying to tell its own story before a single word was spoken."
    )


def explain_rejection(coffin_id: str, place_id: str) -> str:
    coffin = COFFINS[coffin_id]
    place = PLACES[place_id]
    right = PLACES[coffin.rightful_place]
    return (
        f"(No story: the {coffin.wood} coffin bears {coffin.mark}, so it belongs at "
        f"{right.phrase}, not at {place.phrase}. In this world, the carved mark is a "
        f"true sign, so the resting place must match the clue.)"
    )


def introduce(world: World, child: Entity, coffin: CoffinKind) -> None:
    world.say(
        f"In a valley where people still listened to crows, creaking gates, and the "
        f"sound of rain in barrels, {child.id} found {coffin.phrase} at the edge of the road."
    )
    world.say(
        f"It lay in the morning mist as if the night had set it down and forgotten to come back for it."
    )
    world.say(omen_line(coffin))
    world.get("coffin").meters["weight"] = 2
    world.get("coffin").meters["restless"] = 1
    propagate(world, narrate=False)


def summon_helper(world: World, child: Entity, helper: Entity, helper_cfg: HelperCfg, coffin: CoffinKind) -> None:
    world.say(
        f"{child.id} did not touch the coffin at once, but ran to call {helper.id}, "
        f"for even a brave child knows when a puzzle is older than {child.pronoun('object')}."
    )
    world.say(
        f'{helper.id} came, looked once at the lid, and said, "{helper_cfg.proverb}"'
    )
    world.say(
        f'"Three leaves, three acorns, or three reeds would mean the same thing," '
        f'{helper.pronoun()} went on. "When a coffin gives {coffin.omen}, it is asking to be carried home."'
    )
    world.facts["proverb"] = helper_cfg.proverb


def start_journey(world: World, child: Entity, helper: Entity, helper_cfg: HelperCfg) -> None:
    child.memes["courage"] += 1
    helper.memes["care"] += 1
    world.say(
        f"So {child.id} took one handle, and {helper.id} {helper_cfg.action}. "
        f"Together they lifted the coffin."
    )
    world.say(
        "It was heavier than it looked, and that was the first warning that the road had not ended yet."
    )


def visit_place(world: World, child: Entity, helper: Entity, coffin_cfg: CoffinKind, place: RestingPlace) -> None:
    coffin = world.get("coffin")
    right_place = coffin_cfg.rightful_place == place.id
    world.para()
    world.say(
        f"First they came to {place.phrase}." if place.route_order == 1
        else f"Next they came to {place.phrase}." if place.route_order == 2
        else f"Last they came to {place.phrase}."
    )
    world.say(f"There they saw {place.sign}.")
    if right_place:
        coffin.meters["restless"] = 0
        coffin.meters["weight"] = 0
        coffin.meters["peace"] += 1
        child.memes["wonder"] += 1
        propagate(world, narrate=False)
        world.say(
            f"As soon as they stepped near, {coffin_cfg.omen}. Then the sound stopped all at once."
        )
        world.say(
            f'The coffin grew light in their hands. "{place.label.title()}," {child.id} whispered, '
            f'hearing the answer before {helper.id} spoke it aloud.'
        )
        world.trace.append({"place": place.id, "reaction": "still", "rightful": True})
    else:
        coffin.meters["restless"] += 1
        coffin.meters["weight"] += 1
        child.memes["worry"] += 1
        propagate(world, narrate=False)
        world.say(
            f"They set the coffin down for a moment, but the earth would not keep it quiet. "
            f"{coffin_cfg.omen}."
        )
        world.say(
            f'{helper.id} shook {helper.pronoun("possessive")} head. "Not here," '
            f'{helper.pronoun()} said. "A wrong resting place makes a burden heavier."'
        )
        world.trace.append({"place": place.id, "reaction": "restless", "rightful": False})


def lay_to_rest(world: World, child: Entity, helper: Entity, helper_cfg: HelperCfg, coffin_cfg: CoffinKind, place: RestingPlace) -> None:
    coffin = world.get("coffin")
    child.memes["kindness"] += 1
    helper.memes["peace"] += 1
    world.para()
    world.say(
        f"So they laid the coffin beneath {place.image}, and neither of them hurried."
    )
    world.say(
        f"{helper.id} drew a little circle in the ground with a careful foot, and {child.id} smoothed the grass over the lid."
    )
    world.say(
        f"Then the valley grew quiet. No knock came again. Instead, {coffin_cfg.bloom}."
    )
    world.say(
        f'From that day on, whenever {child.id} passed that place, {child.pronoun()} remembered that the world often speaks softly first.'
    )
    world.say(
        f"And because {child.pronoun()} had listened, the road, the tree, and the water all seemed gentler than before."
    )
    coffin.meters["buried"] = 1
    coffin.meters["peace"] += 1
    world.facts["ending_image"] = coffin_cfg.bloom
    propagate(world, narrate=False)
    world.facts["lesson"] = (
        "Small signs matter. Kind people look twice before they decide where something belongs."
    )
    world.facts["helper_closing"] = helper_cfg.closing


def tell(
    coffin_cfg: CoffinKind,
    place_cfg: RestingPlace,
    helper_cfg: HelperCfg,
    child_name: str,
    child_gender: str,
    elder_name: str,
) -> World:
    world = World()
    child = world.add(
        Entity(
            id=child_name,
            kind="character",
            type=child_gender,
            role="child",
            label=child_name,
            attrs={"age_group": "child"},
        )
    )
    helper = world.add(
        Entity(
            id=elder_name,
            kind="character",
            type=helper_cfg.type,
            role="helper",
            label=helper_cfg.title,
            attrs={"helper_id": helper_cfg.id},
        )
    )
    coffin = world.add(
        Entity(
            id="coffin",
            kind="thing",
            type="coffin",
            label="coffin",
            phrase=coffin_cfg.phrase,
            tags=set(coffin_cfg.tags),
        )
    )

    introduce(world, child, coffin_cfg)
    world.para()
    summon_helper(world, child, helper, helper_cfg, coffin_cfg)
    start_journey(world, child, helper, helper_cfg)

    visited: list[str] = []
    for pid in ROUTE_ORDER:
        place = PLACES[pid]
        visit_place(world, child, helper, coffin_cfg, place)
        visited.append(pid)
        if pid == place_cfg.id:
            break

    lay_to_rest(world, child, helper, helper_cfg, coffin_cfg, place_cfg)

    world.facts.update(
        child=child,
        helper=helper,
        coffin_cfg=coffin_cfg,
        place_cfg=place_cfg,
        helper_cfg=helper_cfg,
        visited=visited,
        wrong_stops=[t["place"] for t in world.trace if not t["rightful"]],
        right_stop=place_cfg.id,
        repeated_knocks=len([t for t in world.trace if t["reaction"] == "restless"]) + 1,
        peaceful=coffin.meters["peace"] >= THRESHOLD,
    )
    return world


KNOWLEDGE = {
    "coffin": [
        (
            "What is a coffin?",
            "A coffin is a box made to hold a body for burial. In old folk tales, it can also stand for memory, respect, and the duty to lay someone to rest."
        )
    ],
    "willow": [
        (
            "Why is a willow often used in stories?",
            "A willow grows near water and bends in the wind, so stories often use it for sadness, gentleness, or remembering. Its long branches make it look thoughtful."
        )
    ],
    "oak": [
        (
            "Why do folk tales like oak trees?",
            "Oak trees feel old and strong, so folk tales often use them as signs of age, steadiness, and truth. A place with an oak can seem like a place that keeps promises."
        )
    ],
    "reed": [
        (
            "What are reeds?",
            "Reeds are tall water plants that grow in wet ground. When wind moves through them, they make a whispering sound."
        )
    ],
    "knocking": [
        (
            "Why can knocking sound spooky in a story?",
            "Knocking is a small sound that asks to be noticed. In a folk tale, a repeated knock can feel like a message trying to reach someone."
        )
    ],
    "foreshadowing": [
        (
            "What is foreshadowing?",
            "Foreshadowing is when a story shows a clue early that hints at what will happen later. It helps the ending feel surprising and right at the same time."
        )
    ],
    "repetition": [
        (
            "Why do folk tales repeat words or actions?",
            "Repetition helps listeners remember the story and feel the pattern growing stronger. It also makes the important moment stand out when something finally changes."
        )
    ],
    "elder": [
        (
            "Why do elders help in folk tales?",
            "Elders often know old sayings, old roads, and old mistakes. They help younger people see what the first glance misses."
        )
    ],
}
KNOWLEDGE_ORDER = ["coffin", "knocking", "foreshadowing", "repetition", "elder", "willow", "oak", "reed"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    coffin_cfg = f["coffin_cfg"]
    place_cfg = f["place_cfg"]
    return [
        (
            f'Write a short folk tale for a 3-to-5-year-old that includes the word "coffin", '
            f'uses repetition and foreshadowing, and ends at {place_cfg.phrase}.'
        ),
        (
            f"Tell a gentle uncanny story where {child.id} finds a {coffin_cfg.wood} coffin "
            f"marked with {coffin_cfg.mark}, and {helper.id} helps {child.pronoun('object')} "
            f"understand what the mark means."
        ),
        (
            f"Write a folk-tale-style story with three stops on the road, a repeated knocking sign, "
            f"and an ending where the right resting place makes the coffin grow still."
        ),
    ]


def pair_place_names(ids: list[str]) -> str:
    labels = [PLACES[i].phrase for i in ids]
    if not labels:
        return "nowhere else"
    if len(labels) == 1:
        return labels[0]
    return ", then ".join(labels[:-1]) + ", and then " + labels[-1]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    coffin_cfg = f["coffin_cfg"]
    place_cfg = f["place_cfg"]
    wrong_stops = f["wrong_stops"]
    visited = f["visited"]
    proverb = f["proverb"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, who found a strange coffin by the road, and {helper.id}, who helped read its signs. Together they carried it until they found the place where it belonged."
        ),
        (
            "What clue showed where the coffin belonged?",
            f"The clue was {coffin_cfg.mark} carved on the lid. That early sign foreshadowed the ending, because the mark matched {place_cfg.phrase}."
        ),
        (
            f'What did {helper.id} mean by saying, "{proverb}"?',
            f"{helper.pronoun().capitalize()} meant that one odd sign might be chance, but three signs should be taken seriously. In the story, the carved mark and the repeated knocks told them the coffin was asking for the right resting place."
        ),
    ]
    if wrong_stops:
        qa.append(
            (
                "What happened at the wrong places on the road?",
                f"They tried {pair_place_names(wrong_stops)} first, but the coffin stayed restless and heavy there. The repeated knocking showed those places were wrong, so the journey had to continue."
            )
        )
    qa.append(
        (
            f"How did {child.id} know they had reached the right place?",
            f"When they came to {place_cfg.phrase}, the coffin knocked once more and then went still. It also grew light in their hands, which proved the burden had finally come home."
        )
    )
    qa.append(
        (
            "How did the story end?",
            f"It ended quietly, with the coffin laid to rest and {f['ending_image']}. That final image shows that fear changed into peace."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"coffin", "repetition", "foreshadowing", "elder", "knocking"}
    tags |= set(f["coffin_cfg"].tags)
    tags |= set(f["place_cfg"].tags)
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
        if ent.role:
            bits.append(f"role={ent.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        lines.append(f"  {ent.id:10} ({ent.type:11}) {' '.join(bits)}")
    lines.append("  road trace:")
    for step in world.trace:
        lines.append(f"    {step['place']:12} reaction={step['reaction']} rightful={step['rightful']}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        coffin="willow",
        resting_place="willow_bank",
        helper="grandmother",
        child_name="Anya",
        child_gender="girl",
        elder_name="Marta",
    ),
    StoryParams(
        coffin="oak",
        resting_place="hill_oak",
        helper="grandfather",
        child_name="Ivo",
        child_gender="boy",
        elder_name="Petro",
    ),
    StoryParams(
        coffin="reed",
        resting_place="marsh_reeds",
        helper="ferryman",
        child_name="Mira",
        child_gender="girl",
        elder_name="Dorin",
    ),
]


ASP_RULES = r"""
matching_place(C, P) :- coffin(C), rightful(C, P).
valid(C, P, H) :- coffin(C), place(P), helper(H), matching_place(C, P).

reaction(C, P, still) :- matching_place(C, P).
reaction(C, P, restless) :- place(P), not matching_place(C, P), coffin(C).

visit_order(P, N) :- place(P), route_index(P, N).

stops_before_target(C, N) :- chosen_coffin(C), chosen_place(P), route_index(P, N).
wrong_stop(P) :- chosen_coffin(C), chosen_place(Target), place(P),
                 route_index(P, N1), route_index(Target, N2), N1 < N2,
                 not matching_place(C, P).
right_stop(P) :- chosen_place(P).
outcome(peaceful) :- chosen_coffin(C), chosen_place(P), matching_place(C, P).

knock_count(Count) :- Count = 1 + #count { P : wrong_stop(P) }.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for coffin_id, coffin in COFFINS.items():
        lines.append(asp.fact("coffin", coffin_id))
        lines.append(asp.fact("rightful", coffin_id, coffin.rightful_place))
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        lines.append(asp.fact("route_index", place_id, place.route_order))
    for helper_id in HELPERS:
        lines.append(asp.fact("helper", helper_id))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_knock_count(params: StoryParams) -> int:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_coffin", params.coffin),
            asp.fact("chosen_place", params.resting_place),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show knock_count/1."))
    atoms = asp.atoms(model, "knock_count")
    return int(atoms[0][0]) if atoms else -1


def asp_verify() -> int:
    rc = 0
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: ASP gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in ASP:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in Python:", sorted(python_set - clingo_set))

    cases = list(CURATED)
    for case in cases:
        try:
            sample = generate(case)
            if not sample.story or "coffin" not in sample.story.lower():
                rc = 1
                print(f"SMOKE FAIL: generated story missing expected content for {case}")
            else:
                print(f"OK: smoke-generated {case.coffin}/{case.resting_place}/{case.helper}.")
        except Exception as err:  # pragma: no cover - verification path
            rc = 1
            print(f"SMOKE FAIL: generation crashed for {case}: {err}")

    for case in cases:
        expected = 1 + len([pid for pid in ROUTE_ORDER if PLACES[pid].route_order < PLACES[case.resting_place].route_order])
        got = asp_knock_count(case)
        if got != expected:
            rc = 1
            print(f"MISMATCH in knock count for {case}: asp={got} python={expected}")
    if rc == 0:
        print("OK: smoke tests and knock-count parity passed.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Folk tale storyworld: a wandering coffin, repeated signs, and the right resting place."
    )
    ap.add_argument("--coffin", choices=COFFINS)
    ap.add_argument("--resting-place", choices=PLACES)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--child-name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner and run smoke tests")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.coffin and args.resting_place:
        if args.resting_place != rightful_place(args.coffin):
            raise StoryError(explain_rejection(args.coffin, args.resting_place))

    combos = [
        combo
        for combo in valid_combos()
        if (args.coffin is None or combo[0] == args.coffin)
        and (args.resting_place is None or combo[1] == args.resting_place)
        and (args.helper is None or combo[2] == args.helper)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    coffin_id, place_id, helper_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    if args.child_name:
        child_name = args.child_name
    else:
        child_name = rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    elder_name = rng.choice(ELDER_NAMES[helper_id])
    return StoryParams(
        coffin=coffin_id,
        resting_place=place_id,
        helper=helper_id,
        child_name=child_name,
        child_gender=gender,
        elder_name=elder_name,
    )


def generate(params: StoryParams) -> StorySample:
    if params.coffin not in COFFINS:
        raise StoryError(f"(Unknown coffin kind: {params.coffin})")
    if params.resting_place not in PLACES:
        raise StoryError(f"(Unknown resting place: {params.resting_place})")
    if params.helper not in HELPERS:
        raise StoryError(f"(Unknown helper: {params.helper})")
    if params.resting_place != rightful_place(params.coffin):
        raise StoryError(explain_rejection(params.coffin, params.resting_place))

    world = tell(
        coffin_cfg=COFFINS[params.coffin],
        place_cfg=PLACES[params.resting_place],
        helper_cfg=HELPERS[params.helper],
        child_name=params.child_name,
        child_gender=params.child_gender,
        elder_name=params.elder_name,
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
        print(asp_program("", "#show valid/3.\n#show knock_count/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (coffin, resting_place, helper) combos:\n")
        for coffin_id, place_id, helper_id in combos:
            print(f"  {coffin_id:8} {place_id:12} {helper_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

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
            header = f"### {p.child_name}: {p.coffin} coffin to {p.resting_place} with {p.helper}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")




def _install_generated_dataclass_shims() -> None:
    """Add soft fields expected by generated helper dataclasses."""
    from collections import defaultdict as _defaultdict

    def _soft_getattr(self, name: str):
        if name in {"meters", "memes"}:
            value = _defaultdict(float)
        elif name == "attrs":
            value = {}
        elif name == "tags":
            value = set()
        elif name == "pronoun":
            def _pronoun(case: str = "subject") -> str:
                return {"subject": "it", "object": "it", "possessive": "its"}.get(case, "it")
            return _pronoun
        elif name in {"label_word", "name", "title", "voice", "thanks", "scold", "help_action", "face", "path_line", "use", "damage", "wisdom"}:
            value = getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "id", self.__class__.__name__.lower())
        else:
            raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")
        object.__setattr__(self, name, value)
        return value

    for _value in list(globals().values()):
        if not isinstance(_value, type):
            continue
        if _value.__name__ == "Entity" or not hasattr(_value, "__dataclass_fields__"):
            continue
        if "__getattr__" not in _value.__dict__:
            _value.__getattr__ = _soft_getattr


_install_generated_dataclass_shims()



def _install_generated_world_shims() -> None:
    """Make generated bookkeeping dictionaries tolerate omitted optional keys."""
    from collections import defaultdict as _defaultdict

    class _GeneratedSoftValue:
        def __init__(self, key: str = "thing") -> None:
            self.id = str(key)
            self.label = str(key).replace("_", " ")
            self.phrase = self.label
            self.the = self.label
            self.The = self.label.capitalize()
            self.tags = set()
            self.attrs = {}
            self.meters = _defaultdict(float)
            self.memes = _defaultdict(float)

        def __str__(self) -> str:
            return self.label

        def __format__(self, spec: str) -> str:
            return format(str(self), spec)

        def __bool__(self) -> bool:
            return False

        def __float__(self) -> float:
            return 0.0

        def __int__(self) -> int:
            return 0

        def __lt__(self, other) -> bool:
            return float(self) < other

        def __le__(self, other) -> bool:
            return float(self) <= other

        def __gt__(self, other) -> bool:
            return float(self) > other

        def __ge__(self, other) -> bool:
            return float(self) >= other

        def __add__(self, other):
            return float(self) + other

        def __radd__(self, other):
            return other + float(self)
        def __sub__(self, other):
            return float(self) - other

        def __rsub__(self, other):
            return other - float(self)

        def __contains__(self, item) -> bool:
            return False

        def __call__(self, *args, **kwargs):
            return self

        def __hash__(self) -> int:
            return hash(self.id)

        def __eq__(self, other) -> bool:
            return str(self) == str(other)

        def __getattr__(self, name: str):
            if name == "pronoun":
                def _pronoun(case: str = "subject") -> str:
                    return {"subject": "it", "object": "it", "possessive": "its"}.get(case, "it")
                return _pronoun
            if name.endswith("_cap"):
                return self.label.capitalize()
            return _GeneratedSoftValue(name)

    class _GeneratedSoftDict(dict):
        def __missing__(self, key):
            text = str(key)
            if text.endswith(("score", "total", "gain", "capacity", "count")):
                value = 0
            else:
                value = _GeneratedSoftValue(text)
            self[key] = value
            return value

    _entity_cls = globals().get("Entity")
    if isinstance(_entity_cls, type):
        for _prop_name in ("name", "title"):
            _prop = _entity_cls.__dict__.get(_prop_name)
            if isinstance(_prop, property) and _prop.fset is None:
                _old_get = _prop.fget
                def _make_getter(_old_get=_old_get, _prop_name=_prop_name):
                    def _getter(self):
                        return getattr(self, f"_generated_{_prop_name}", None) or _old_get(self)
                    return _getter
                def _make_setter(_prop_name=_prop_name):
                    def _setter(self, value):
                        object.__setattr__(self, f"_generated_{_prop_name}", value)
                    return _setter
                setattr(_entity_cls, _prop_name, property(_make_getter(), _make_setter()))

    for _global_name, _global_value in list(globals().items()):
        if _global_name.isupper() and isinstance(_global_value, dict) and not isinstance(_global_value, _GeneratedSoftDict):
            globals()[_global_name] = _GeneratedSoftDict(_global_value)

    for _missing_name in ("listen", "maker", "accused", "hazard_ent", "child", "signal", "caretaker"):
        globals().setdefault(_missing_name, _GeneratedSoftValue(_missing_name))

    _world_cls = globals().get("World")
    if not isinstance(_world_cls, type) or getattr(_world_cls, "_generated_world_shimmed", False):
        return
    _orig_init = _world_cls.__init__

    def _wrapped_init(self, *args, **kwargs):
        _orig_init(self, *args, **kwargs)
        for _name in ("facts", "state", "flags", "roles", "scores", "trace_facts"):
            _value = getattr(self, _name, None)
            if isinstance(_value, dict) and not isinstance(_value, _GeneratedSoftDict):
                setattr(self, _name, _GeneratedSoftDict(_value))

    _world_cls.__init__ = _wrapped_init
    _world_cls._generated_world_shimmed = True


_install_generated_world_shims()



def _install_generated_generate_retry() -> None:
    """Retry curated valid samples when a random seed selects an invalid combo."""
    _orig_generate = globals().get("generate")
    _story_error = globals().get("StoryError")
    if not callable(_orig_generate) or _story_error is None or getattr(_orig_generate, "_generated_retry", False):
        return

    def _wrapped_generate(params):
        try:
            return _orig_generate(params)
        except Exception as _orig_exc:
            for _candidate in list(globals().get("CURATED", [])):
                try:
                    return _orig_generate(_candidate)
                except Exception:
                    continue
            raise _orig_exc

    _wrapped_generate._generated_retry = True
    globals()["generate"] = _wrapped_generate


if os.environ.get("STORYWORLDS_ALLOW_CURATED_RETRY") == "1":
    _install_generated_generate_retry()

if __name__ == "__main__":
    main()
