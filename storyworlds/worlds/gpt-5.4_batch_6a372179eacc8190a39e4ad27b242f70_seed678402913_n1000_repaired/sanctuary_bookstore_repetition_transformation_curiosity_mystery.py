#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/sanctuary_bookstore_repetition_transformation_curiosity_mystery.py
================================================================================================

A standalone storyworld for a gentle bookstore mystery shaped by repetition,
curiosity, and transformation.

Premise
-------
A child visits a bookstore and keeps hearing the same strange sound from a small
back corner. The repeated clue turns curiosity into a careful investigation with
a bookseller. They discover a hidden creature or object, solve the small problem
sensibly, and the once-dusty corner becomes a true sanctuary.

Run it
------
    python storyworlds/worlds/gpt-5.4/sanctuary_bookstore_repetition_transformation_curiosity_mystery.py
    python storyworlds/worlds/gpt-5.4/sanctuary_bookstore_repetition_transformation_curiosity_mystery.py --section poetry --mystery kitten --helper flashlight
    python storyworlds/worlds/gpt-5.4/sanctuary_bookstore_repetition_transformation_curiosity_mystery.py --mystery pigeon --helper flashlight
    python storyworlds/worlds/gpt-5.4/sanctuary_bookstore_repetition_transformation_curiosity_mystery.py --all --qa
    python storyworlds/worlds/gpt-5.4/sanctuary_bookstore_repetition_transformation_curiosity_mystery.py --verify
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
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "bookseller_woman"}
        male = {"boy", "man", "father", "bookseller_man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def title_word(self) -> str:
        if self.role == "bookseller":
            return "bookseller"
        return self.type


@dataclass
class Section:
    id: str
    label: str
    detail: str
    affords: set[str] = field(default_factory=set)


@dataclass
class MysteryCase:
    id: str
    source_label: str
    source_phrase: str
    source_type: str
    sound_word: str
    repeated_line: str
    hiding_place: str
    reveal_line: str
    problem_line: str
    comfort_line: str
    ending_image: str
    allowed_helpers: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Helper:
    id: str
    label: str
    phrase: str
    action_line: str
    why_good: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, section: Section) -> None:
        self.section = section
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
        clone = World(self.section)
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


def _r_repetition_curiosity(world: World) -> list[str]:
    child = world.entities.get("child")
    if child is None:
        return []
    heard = child.meters["heard_clue"]
    if heard < 2:
        return []
    sig = ("curiosity", int(heard))
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["curiosity"] += 1
    child.memes["unease"] += 1
    return []


def _r_discovery_relief(world: World) -> list[str]:
    child = world.entities.get("child")
    bookseller = world.entities.get("bookseller")
    mystery = world.entities.get("mystery")
    if child is None or bookseller is None or mystery is None:
        return []
    if mystery.meters["found"] < THRESHOLD:
        return []
    sig = ("relief", mystery.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["relief"] += 1
    bookseller.memes["relief"] += 1
    mystery.memes["fear"] = 0.0
    return []


def _r_transformation(world: World) -> list[str]:
    nook = world.entities.get("nook")
    if nook is None:
        return []
    if nook.meters["helped"] < THRESHOLD:
        return []
    sig = ("transformation", "nook")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    nook.meters["cozy"] += 1
    nook.meters["dust"] = 0.0
    return []


CAUSAL_RULES = [
    Rule(name="repetition_curiosity", tag="emotional", apply=_r_repetition_curiosity),
    Rule(name="discovery_relief", tag="emotional", apply=_r_discovery_relief),
    Rule(name="transformation", tag="physical", apply=_r_transformation),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
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
            world.say(line)
    return produced


SECTIONS = {
    "poetry": Section(
        id="poetry",
        label="the poetry shelves",
        detail="Tall thin books stood in neat rows, and the lamps there always made the dust look golden.",
        affords={"kitten", "letter", "music_box"},
    ),
    "history": Section(
        id="history",
        label="the history shelves",
        detail="The shelves were heavy and dark, with little brass labels and long shadows near the floor.",
        affords={"letter", "pigeon"},
    ),
    "children": Section(
        id="children",
        label="the children's corner",
        detail="Bright covers faced out like little doors, and a painted moon hung over a low rug.",
        affords={"kitten", "music_box"},
    ),
}

MYSTERIES = {
    "kitten": MysteryCase(
        id="kitten",
        source_label="kitten",
        source_phrase="a dusty gray kitten",
        source_type="animal",
        sound_word="mew",
        repeated_line='"Mew... mew... mew..." came the sound again.',
        hiding_place="behind the bottom row of a leaning picture-book shelf",
        reveal_line="A pair of round eyes blinked from the dark gap.",
        problem_line="The tiny kitten had wriggled in after warmth and could not find the way back out.",
        comfort_line="The bookseller wrapped the shaking kitten in a soft scarf and set down a saucer of water.",
        ending_image="Soon the kitten was asleep in a basket beside the chair, with one paw tucked over its nose.",
        allowed_helpers={"flashlight", "book_cart"},
        tags={"kitten", "animal", "rescue"},
    ),
    "pigeon": MysteryCase(
        id="pigeon",
        source_label="pigeon",
        source_phrase="a young pigeon with speckled wings",
        source_type="animal",
        sound_word="flutter",
        repeated_line='"Flutter-flutter, tap... flutter-flutter, tap..." came the sound again.',
        hiding_place="on the narrow ledge above a high back window",
        reveal_line="Soft wings flashed in the half-light near the glass.",
        problem_line="The young pigeon had flown in through an open upper window and was too frightened to glide back out.",
        comfort_line="The bookseller lifted the pigeon down with slow hands and opened the window wide to the quiet alley garden.",
        ending_image="A minute later the pigeon settled on the ivy outside, safe and calm in the evening light.",
        allowed_helpers={"step_stool"},
        tags={"pigeon", "animal", "rescue"},
    ),
    "letter": MysteryCase(
        id="letter",
        source_label="letter",
        source_phrase="an old cream envelope tied with blue thread",
        source_type="object",
        sound_word="tap",
        repeated_line='"Tap... tap... tap..." came the sound again.',
        hiding_place="inside a loose wooden panel under a biography shelf",
        reveal_line="Behind the panel rested an old envelope, nudged by the heater whenever warm air sighed through the crack.",
        problem_line="The sound was not a ghost at all. It was the hidden letter tapping the wood every time the heater woke up.",
        comfort_line="Inside was a note from the first owner asking that the quiet corner always stay open for shy readers who needed a peaceful place.",
        ending_image="The letter was framed on the wall, where its blue thread looked like a tiny ribbon of sky.",
        allowed_helpers={"flashlight"},
        tags={"letter", "note", "history"},
    ),
    "music_box": MysteryCase(
        id="music_box",
        source_label="music box",
        source_phrase="a little silver music box shaped like a moon",
        source_type="object",
        sound_word="ting",
        repeated_line='"Ting... ting... ting..." came the sound again.',
        hiding_place="inside a donation basket under a table of bargain books",
        reveal_line="Under a pile of old bookmarks sat a silver music box, trembling each time the table shook.",
        problem_line="Someone had left the wound music box in the basket, and every nudge made it sing three tiny notes.",
        comfort_line="The bookseller wound it down, then found a card tucked underneath with the donor's name and a note to share it in the reading nook.",
        ending_image="Later the music box rested on a small shelf, chiming only when someone gently turned the key.",
        allowed_helpers={"book_cart", "flashlight"},
        tags={"music_box", "sound", "history"},
    ),
}

HELPERS = {
    "flashlight": Helper(
        id="flashlight",
        label="flashlight",
        phrase="a small brass flashlight",
        action_line="The bookseller clicked on a small brass flashlight, and the beam slipped under the shelf like a thin bright finger.",
        why_good="It let them see safely into a dark hidden place.",
        tags={"flashlight", "light"},
    ),
    "step_stool": Helper(
        id="step_stool",
        label="step stool",
        phrase="a sturdy wooden step stool",
        action_line="The bookseller fetched a sturdy wooden step stool and climbed carefully until eye level met the high ledge.",
        why_good="It made a high place reachable without climbing the shelves.",
        tags={"stool", "reach"},
    ),
    "book_cart": Helper(
        id="book_cart",
        label="book cart",
        phrase="a quiet rolling book cart",
        action_line="Together they rolled a quiet book cart aside, making room to reach the hidden spot without tipping any books.",
        why_good="It cleared space and kept the shelves steady while they helped.",
        tags={"cart", "safe"},
    ),
}

GIRL_NAMES = ["Lena", "Mira", "Nora", "Ivy", "June", "Clara", "Tessa"]
BOY_NAMES = ["Eli", "Owen", "Milo", "Jasper", "Theo", "Ben", "Noah"]
BOOKSELLER_NAMES = ["Ms. Vale", "Mr. Rowan", "Auntie Bea", "Mrs. Finch"]
TRAITS = ["careful", "quiet", "curious", "thoughtful", "gentle"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for sid, section in SECTIONS.items():
        for mid in sorted(section.affords):
            mystery = MYSTERIES[mid]
            for hid in sorted(mystery.allowed_helpers):
                combos.append((sid, mid, hid))
    return combos


def explain_rejection(section: Section, mystery: MysteryCase, helper: Helper) -> str:
    if mystery.id not in section.affords:
        return (
            f"(No story: {mystery.source_label} does not fit {section.label} in this world. "
            f"Pick a section that could plausibly hide it.)"
        )
    if helper.id not in mystery.allowed_helpers:
        allowed = ", ".join(sorted(mystery.allowed_helpers))
        return (
            f"(No story: {helper.label} is not a sensible way to solve the {mystery.source_label} mystery. "
            f"Try one of: {allowed}.)"
        )
    return "(No story: this combination is not reasonable.)"


def section_for(mystery_id: str) -> list[str]:
    return [sid for sid, sec in SECTIONS.items() if mystery_id in sec.affords]


@dataclass
class StoryParams:
    section: str
    mystery: str
    helper: str
    child_name: str
    child_gender: str
    bookseller_name: str
    bookseller_type: str
    trait: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        section="children",
        mystery="kitten",
        helper="flashlight",
        child_name="Mira",
        child_gender="girl",
        bookseller_name="Ms. Vale",
        bookseller_type="bookseller_woman",
        trait="curious",
        seed=1,
    ),
    StoryParams(
        section="history",
        mystery="pigeon",
        helper="step_stool",
        child_name="Theo",
        child_gender="boy",
        bookseller_name="Mr. Rowan",
        bookseller_type="bookseller_man",
        trait="careful",
        seed=2,
    ),
    StoryParams(
        section="poetry",
        mystery="letter",
        helper="flashlight",
        child_name="Nora",
        child_gender="girl",
        bookseller_name="Mrs. Finch",
        bookseller_type="bookseller_woman",
        trait="thoughtful",
        seed=3,
    ),
    StoryParams(
        section="children",
        mystery="music_box",
        helper="book_cart",
        child_name="Eli",
        child_gender="boy",
        bookseller_name="Auntie Bea",
        bookseller_type="bookseller_woman",
        trait="gentle",
        seed=4,
    ),
]


def introduce(world: World, child: Entity, bookseller: Entity) -> None:
    world.say(
        f"{child.id} loved the bookstore because it felt like a secret little city made of paper and lamp-glow. "
        f"On rainy afternoons, {bookseller.id}, the kindly bookseller, always said the place was a sanctuary for quiet hearts."
    )
    world.say(world.section.detail)


def wander(world: World, child: Entity) -> None:
    child.memes["calm"] += 1
    world.say(
        f"That day {child.id} drifted toward {world.section.label}, tracing titles with slow fingers and wondering which story might open first."
    )


def hear_clue(world: World, child: Entity, mystery: MysteryCase) -> None:
    child.meters["heard_clue"] += 1
    propagate(world, narrate=False)
    first = {
        1: f"Then {child.id} heard a sound from the back corner: {mystery.repeated_line}",
        2: f"{child.id} stood still. From the same corner came the very same sound: {mystery.repeated_line}",
        3: f"A third time the hidden corner answered with it: {mystery.repeated_line}",
    }[int(child.meters["heard_clue"])]
    world.say(first)


def curiosity_question(world: World, child: Entity, bookseller: Entity, mystery: MysteryCase) -> None:
    child.memes["curiosity"] += 1
    world.say(
        f'"Did you hear that?" {child.id} whispered. "{mystery.sound_word.capitalize()}... and then {mystery.sound_word} again?"'
    )
    world.say(
        f'{bookseller.id} tilted {bookseller.pronoun("possessive")} head. "I did," {bookseller.pronoun()} said. '
        f'"Let\'s be curious and careful at the same time."'
    )


def approach_nook(world: World, child: Entity) -> None:
    nook = world.get("nook")
    nook.meters["dust"] += 1
    child.memes["unease"] += 1
    world.say(
        "At the back stood a narrow reading nook with a chair, a crooked lamp, and shadows tucked behind stacked books. "
        "It looked more forgotten than frightening, but mysteries can make even dust feel watchful."
    )


def use_helper(world: World, bookseller: Entity, helper: Helper) -> None:
    world.say(helper.action_line)
    world.facts["helper_reason"] = helper.why_good


def discover(world: World, child: Entity, mystery: MysteryCase) -> None:
    thing = world.get("mystery")
    thing.meters["found"] += 1
    propagate(world, narrate=False)
    world.say(mystery.reveal_line)
    world.say(mystery.problem_line)
    child.memes["wonder"] += 1


def solve(world: World, bookseller: Entity, mystery: MysteryCase) -> None:
    thing = world.get("mystery")
    nook = world.get("nook")
    thing.meters["safe"] += 1
    nook.meters["helped"] += 1
    propagate(world, narrate=False)
    world.say(mystery.comfort_line)
    bookseller.memes["care"] += 1


def transform(world: World, child: Entity, bookseller: Entity, mystery: MysteryCase) -> None:
    nook = world.get("nook")
    child.memes["belonging"] += 1
    bookseller.memes["belonging"] += 1
    world.say(
        f"After that, they straightened the chair, brushed away the dust, and set the little corner in order. "
        f"What had felt like the hiding place of a puzzle slowly changed into a real sanctuary."
    )
    if mystery.id in {"kitten", "pigeon"}:
        world.say(
            "A folded blanket, a bowl of water, and a handwritten sign asking for gentle voices turned the nook soft and welcoming."
        )
    else:
        world.say(
            "A framed note, a polished lamp, and a neat stack of favorite stories made the nook glow with a calm new purpose."
        )
    world.say(
        f"{bookseller.id} smiled and said, \"Some mysteries do not end by staying mysterious. They end by showing us what needs kindness.\""
    )
    world.say(
        f"{mystery.ending_image} {child.id} chose a book and sat nearby, listening to the corner now that it no longer sounded lonely."
    )
    world.facts["sanctuary_ready"] = nook.meters["cozy"] >= THRESHOLD


def tell(
    section: Section,
    mystery: MysteryCase,
    helper: Helper,
    child_name: str,
    child_gender: str,
    bookseller_name: str,
    bookseller_type: str,
    trait: str,
) -> World:
    world = World(section)
    child = world.add(
        Entity(
            id=child_name,
            kind="character",
            type=child_gender,
            role="child",
            label=child_name,
            attrs={"trait": trait},
        )
    )
    bookseller = world.add(
        Entity(
            id=bookseller_name,
            kind="character",
            type=bookseller_type,
            role="bookseller",
            label="the bookseller",
        )
    )
    mystery_ent = world.add(
        Entity(
            id="mystery",
            kind="thing",
            type=mystery.source_type,
            label=mystery.source_label,
            phrase=mystery.source_phrase,
            tags=set(mystery.tags),
        )
    )
    mystery_ent.memes["fear"] = 1.0 if mystery.source_type == "animal" else 0.0
    world.add(
        Entity(
            id="nook",
            kind="thing",
            type="place",
            label="nook",
            phrase="the back reading nook",
            tags={"sanctuary"},
        )
    )

    introduce(world, child, bookseller)
    wander(world, child)

    world.para()
    hear_clue(world, child, mystery)
    hear_clue(world, child, mystery)
    hear_clue(world, child, mystery)
    curiosity_question(world, child, bookseller, mystery)
    approach_nook(world, child)

    world.para()
    use_helper(world, bookseller, helper)
    world.say(f"They followed the sound to {mystery.hiding_place}.")
    discover(world, child, mystery)
    solve(world, bookseller, mystery)

    world.para()
    transform(world, child, bookseller, mystery)

    world.facts.update(
        child=child,
        bookseller=bookseller,
        mystery_cfg=mystery,
        helper_cfg=helper,
        section=section,
        heard_count=int(child.meters["heard_clue"]),
        found=mystery_ent.meters["found"] >= THRESHOLD,
        solved=mystery_ent.meters["safe"] >= THRESHOLD,
        transformed=world.get("nook").meters["cozy"] >= THRESHOLD,
    )
    return world


KNOWLEDGE = {
    "kitten": [
        (
            "Why might a kitten hide in a small place?",
            "A kitten may hide when it feels scared, cold, or lost. Small spaces can feel safer to a tiny animal."
        )
    ],
    "pigeon": [
        (
            "Why can a bird get stuck indoors?",
            "A bird may fly in through an open window and then feel confused about how to get back out. Bright glass and high walls can make the way hard to find."
        )
    ],
    "letter": [
        (
            "What is an envelope for?",
            "An envelope holds a letter or note to keep it together and protected. People often use one when they want words to be saved carefully."
        )
    ],
    "music_box": [
        (
            "What is a music box?",
            "A music box is a small object that plays a tune when its inside parts move. Some play because they are wound with a key."
        )
    ],
    "flashlight": [
        (
            "Why is a flashlight helpful in dark places?",
            "A flashlight helps people see into dark spaces without putting their hands where they cannot see. That makes looking for a problem safer."
        )
    ],
    "stool": [
        (
            "Why is a step stool safer than climbing shelves?",
            "A step stool is made to help someone reach a high place while keeping their feet steady. Climbing shelves can make books fall or the shelves tip."
        )
    ],
    "cart": [
        (
            "Why move heavy things carefully in a bookstore?",
            "Book carts and shelves can be heavy, so moving them slowly keeps people, books, and small animals safe. Careful hands stop accidents before they start."
        )
    ],
    "sanctuary": [
        (
            "What is a sanctuary?",
            "A sanctuary is a place where someone can feel safe, quiet, and protected. It can be for people, animals, or both."
        )
    ],
    "mystery": [
        (
            "What is a mystery?",
            "A mystery is a puzzle about something hidden or not understood yet. People solve mysteries by noticing clues and asking careful questions."
        )
    ],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    mystery = f["mystery_cfg"]
    section = f["section"]
    return [
        f'Write a gentle mystery story for a 3-to-5-year-old set in a bookstore that includes the word "sanctuary".',
        f"Tell a story where {child.id} hears the same strange sound three times near {section.label}, grows curious, and solves a small mystery with a bookseller.",
        f"Write a child-facing story with repetition, curiosity, and transformation, where a hidden {mystery.source_label} or clue turns a dusty corner into a sanctuary.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    bookseller = f["bookseller"]
    mystery = f["mystery_cfg"]
    helper = f["helper_cfg"]
    section = f["section"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, a child exploring a bookstore, and {bookseller.id}, the bookseller who helps solve the mystery."
        ),
        (
            "What kept happening in the bookstore?",
            f"The same strange sound came three times from the back corner near {section.label}. Hearing it again and again made the mystery feel real and pulled {child.id} closer."
        ),
        (
            f"Why did {child.id} feel curious?",
            f"{child.id} kept hearing the same {mystery.sound_word} sound from a hidden place, so it seemed like a clue instead of an accident. Repetition made {child.pronoun('object')} want to know who or what was there."
        ),
        (
            f"How did the bookseller help investigate?",
            f"{bookseller.id} used {helper.phrase} while staying calm and careful. {helper.why_good}"
        ),
        (
            "What was hidden in the nook?",
            f"It was {mystery.source_phrase} hidden {mystery.hiding_place}. The mystery stopped feeling spooky once they could see the real cause."
        ),
        (
            "How was the problem solved?",
            f"They found what was hidden and helped it safely. {mystery.comfort_line} That kind response changed the whole feeling of the corner."
        ),
        (
            "How did the bookstore change by the end?",
            f"The dusty nook was cleaned and arranged into a sanctuary instead of a worrying shadowy corner. The ending proves the transformation because the same place that held a mystery now feels safe and welcoming."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    mystery = f["mystery_cfg"]
    helper = f["helper_cfg"]
    tags = {"sanctuary", "mystery"} | set(mystery.tags) | set(helper.tags)
    order = ["sanctuary", "mystery", "kitten", "pigeon", "letter", "music_box", "flashlight", "stool", "cart"]
    out: list[tuple[str, str]] = []
    for tag in order:
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
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        lines.append(f"  {e.id:12} ({e.type:14}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
allowed_helper(M, H) :- mystery(M), helper(H), helper_for(M, H).
valid(S, M, H) :- section(S), affords(S, M), allowed_helper(M, H).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, section in SECTIONS.items():
        lines.append(asp.fact("section", sid))
        for mid in sorted(section.affords):
            lines.append(asp.fact("affords", sid, mid))
    for mid, mystery in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        for hid in sorted(mystery.allowed_helpers):
            lines.append(asp.fact("helper_for", mid, hid))
    for hid in HELPERS:
        lines.append(asp.fact("helper", hid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A bookstore mystery storyworld about repetition, curiosity, and a sanctuary transformed from a hidden nook."
    )
    ap.add_argument("--section", choices=SECTIONS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--child-name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--bookseller-name")
    ap.add_argument("--bookseller-type", choices=["bookseller_woman", "bookseller_man"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible (section, mystery, helper) combos via clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.section and args.mystery and args.helper:
        section = SECTIONS[args.section]
        mystery = MYSTERIES[args.mystery]
        helper = HELPERS[args.helper]
        if (args.section, args.mystery, args.helper) not in valid_combos():
            raise StoryError(explain_rejection(section, mystery, helper))
    elif args.section and args.mystery:
        section = SECTIONS[args.section]
        mystery = MYSTERIES[args.mystery]
        if args.mystery not in section.affords:
            raise StoryError(explain_rejection(section, mystery, HELPERS[next(iter(HELPERS))]))
    elif args.mystery and args.helper:
        mystery = MYSTERIES[args.mystery]
        helper = HELPERS[args.helper]
        if args.helper not in mystery.allowed_helpers:
            home_section = SECTIONS[section_for(args.mystery)[0]]
            raise StoryError(explain_rejection(home_section, mystery, helper))

    combos = [
        combo
        for combo in valid_combos()
        if (args.section is None or combo[0] == args.section)
        and (args.mystery is None or combo[1] == args.mystery)
        and (args.helper is None or combo[2] == args.helper)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    section_id, mystery_id, helper_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    child_name = args.child_name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    bookseller_type = args.bookseller_type or rng.choice(["bookseller_woman", "bookseller_man"])
    bookseller_name = args.bookseller_name or rng.choice(BOOKSELLER_NAMES)
    trait = rng.choice(TRAITS)
    return StoryParams(
        section=section_id,
        mystery=mystery_id,
        helper=helper_id,
        child_name=child_name,
        child_gender=gender,
        bookseller_name=bookseller_name,
        bookseller_type=bookseller_type,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.section not in SECTIONS:
        raise StoryError(f"(Invalid section: {params.section})")
    if params.mystery not in MYSTERIES:
        raise StoryError(f"(Invalid mystery: {params.mystery})")
    if params.helper not in HELPERS:
        raise StoryError(f"(Invalid helper: {params.helper})")
    if (params.section, params.mystery, params.helper) not in valid_combos():
        raise StoryError(explain_rejection(SECTIONS[params.section], MYSTERIES[params.mystery], HELPERS[params.helper]))

    world = tell(
        section=SECTIONS[params.section],
        mystery=MYSTERIES[params.mystery],
        helper=HELPERS[params.helper],
        child_name=params.child_name,
        child_gender=params.child_gender,
        bookseller_name=params.bookseller_name,
        bookseller_type=params.bookseller_type,
        trait=params.trait,
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


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py == asp_set:
        print(f"OK: ASP gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if asp_set - py:
            print("  only in ASP:", sorted(asp_set - py))
        if py - asp_set:
            print("  only in Python:", sorted(py - asp_set))

    smoke_cases = list(CURATED)
    try:
        default_params = resolve_params(build_parser().parse_args([]), random.Random(777))
        default_params.seed = 777
        smoke_cases.append(default_params)
    except StoryError as err:
        rc = 1
        print(f"FAILED: resolve_params smoke test raised StoryError: {err}")

    for i, params in enumerate(smoke_cases, 1):
        try:
            sample = generate(params)
            if not sample.story.strip():
                raise StoryError("empty story")
            if "sanctuary" not in sample.story.lower():
                raise StoryError('story does not include "sanctuary"')
            if sample.world is None:
                raise StoryError("missing world model")
            print(f"OK: smoke test {i} generated story for {params.mystery} in {params.section}.")
        except Exception as err:  # noqa: BLE001
            rc = 1
            print(f"FAILED: smoke test {i} crashed: {err}")
    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (section, mystery, helper) combos:\n")
        for section, mystery, helper in combos:
            print(f"  {section:10} {mystery:10} {helper}")
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
            header = f"### {p.child_name}: {p.mystery} in {p.section} with {p.helper}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
