#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/reward_sleep_misunderstanding_bravery_rhyme_detective_story.py

A small detective-story world about a bedtime reward that seems to have vanished.

The domain rebuilds a child-facing tale shape from the seed words "reward" and
"sleep", with three requested instruments:

- Misunderstanding: the child first thinks somebody took the reward.
- Bravery: the child must face a dark, slightly spooky place to solve the case.
- Rhyme: the clues are given as simple rhymes.

The simulation tracks physical state (where the reward really is, whether it is
hidden, whether the room feels dark) and emotional state (pride, suspicion,
fear, relief, bravery). The prose is rendered from world state, not from a
single frozen paragraph.

Run it
------
python storyworlds/worlds/gpt-5.4/reward_sleep_misunderstanding_bravery_rhyme_detective_story.py
python storyworlds/worlds/gpt-5.4/reward_sleep_misunderstanding_bravery_rhyme_detective_story.py --reward star_chart --hiding pillow
python storyworlds/worlds/gpt-5.4/reward_sleep_misunderstanding_bravery_rhyme_detective_story.py --reward drum  # rejected
python storyworlds/worlds/gpt-5.4/reward_sleep_misunderstanding_bravery_rhyme_detective_story.py --all --qa
python storyworlds/worlds/gpt-5.4/reward_sleep_misunderstanding_bravery_rhyme_detective_story.py --verify
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
# This file lives one level deeper than the usual worlds/*.py layout, so we add
# the storyworlds/ package directory by walking up three parents.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"              # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    owner: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    movable: bool = True
    # Shared numeric axes
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


# ---------------------------------------------------------------------------
# Domain configs
# ---------------------------------------------------------------------------
@dataclass
class Reward:
    id: str
    label: str
    phrase: str
    flat: bool = True
    sleep_kind: str = "good"
    tags: set[str] = field(default_factory=set)


@dataclass
class HidingPlace:
    id: str
    label: str
    phrase: str
    accepts_flat: bool = True
    dark: bool = False
    rhyme_a: str = ""
    rhyme_b: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Giver:
    id: str
    type: str
    label: str
    style: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Pet:
    id: str
    label: str
    phrase: str
    tags: set[str] = field(default_factory=set)


# ---------------------------------------------------------------------------
# World and rules
# ---------------------------------------------------------------------------
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


def _r_missing_feels_scary(world: World) -> list[str]:
    reward = world.get("reward")
    hero = world.get("hero")
    if reward.attrs.get("place") == "found":
        return []
    sig = ("missing_scary",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["worry"] += 1
    hero.memes["suspicion"] += 1
    return []


def _r_dark_spot_raises_fear(world: World) -> list[str]:
    hero = world.get("hero")
    place = world.get("place")
    if place.meters["dark"] < THRESHOLD:
        return []
    sig = ("dark_fear",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["fear"] += 1
    return []


CAUSAL_RULES: list[Rule] = [
    Rule(name="missing_feels_scary", tag="emotion", apply=_r_missing_feels_scary),
    Rule(name="dark_spot_raises_fear", tag="emotion", apply=_r_dark_spot_raises_fear),
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
        for line in produced:
            world.say(line)
    return produced


# ---------------------------------------------------------------------------
# Constraints and prediction
# ---------------------------------------------------------------------------
def hiding_fits(reward: Reward, hiding: HidingPlace) -> bool:
    return reward.flat and hiding.accepts_flat


def valid_combos() -> list[tuple[str, str, str]]:
    out: list[tuple[str, str, str]] = []
    for rid, reward in REWARDS.items():
        for hid, hiding in HIDING_PLACES.items():
            if not hiding_fits(reward, hiding):
                continue
            for gid in GIVERS:
                out.append((rid, hid, gid))
    return out


def brave_enough(trait: str, dark: bool) -> bool:
    base = {"timid": 2, "careful": 3, "curious": 4, "brave": 5, "steady": 4}.get(trait, 3)
    need = 4 if dark else 2
    return base >= need


def outcome_of(params: "StoryParams") -> str:
    hiding = HIDING_PLACES[params.hiding]
    return "self_solved" if brave_enough(params.trait, hiding.dark) else "helped_solved"


def predict_search(params: "StoryParams") -> dict:
    hiding = HIDING_PLACES[params.hiding]
    return {
        "dark": hiding.dark,
        "self_solved": brave_enough(params.trait, hiding.dark),
    }


# ---------------------------------------------------------------------------
# Screenplay verbs
# ---------------------------------------------------------------------------
def introduce(world: World, hero: Entity, giver: Entity, reward: Reward) -> None:
    hero.memes["pride"] += 1
    world.say(
        f"{hero.id} loved bedtime mysteries almost as much as bedtime stories. "
        f"That morning, {hero.pronoun()} had earned {reward.phrase} as a reward for a night of good sleep."
    )
    world.say(
        f"{giver.label_word.capitalize()} had called {hero.pronoun('object')} "
        f'"Detective {hero.id}," because {hero.pronoun()} always noticed tiny things.'
    )


def bedtime_setup(world: World, hero: Entity, reward_ent: Entity, pet_ent: Entity, giver: Entity) -> None:
    hero.memes["calm"] += 1
    world.say(
        f"After brushing teeth and putting on soft pajamas, {hero.id} set the reward on the bedside table."
    )
    world.say(
        f"{pet_ent.phrase.capitalize()} curled nearby while {giver.label_word} tucked the blanket under {hero.pronoun('possessive')} chin."
    )
    reward_ent.attrs["place"] = "table"
    world.facts["initial_place"] = "bedside table"


def vanish(world: World, hero: Entity, reward_ent: Entity) -> None:
    reward_ent.attrs["place"] = "missing"
    reward_ent.meters["hidden"] += 1
    propagate(world, narrate=False)
    world.say(
        f"But when {hero.id} woke up from {hero.pronoun('possessive')} sleep and reached for the reward, the bedside table was empty."
    )
    world.say(
        f'"A clue! Or a crime!" whispered {hero.id}.'
    )


def misunderstanding(world: World, hero: Entity, pet_ent: Entity) -> None:
    hero.memes["misunderstanding"] += 1
    world.say(
        f"{hero.id} looked at {pet_ent.label} and gasped. "
        f'"Did you take it, {pet_ent.label}?"'
    )
    world.say(
        f"{pet_ent.phrase.capitalize()} only blinked and washed one paw, which made the mystery seem even deeper."
    )


def first_clue(world: World, giver: Entity, hiding: HidingPlace) -> None:
    note = (
        f'"Look where moonbeams softly creep, "
        f"and where your dreams still like to sleep."'
    )
    world.say(
        f"On the rug lay a folded paper. {giver.label_word.capitalize()} smiled and said, "
        f"{note}"
    )
    world.facts["rhyme1"] = note


def detective_reasoning(world: World, hero: Entity, hiding: HidingPlace) -> None:
    hero.memes["focus"] += 1
    world.say(
        f'{hero.id} put a finger on {hero.pronoun("possessive")} lip. '
        f'"If it likes to sleep, then it must be near {hiding.label}," {hero.pronoun()} said.'
    )


def approach_dark_place(world: World, hero: Entity, hiding: HidingPlace) -> None:
    place = world.get("place")
    if hiding.dark:
        place.meters["dark"] += 1
        propagate(world, narrate=False)
        world.say(
            f"The trail led to {hiding.phrase}, where the shadows looked thick and blue."
        )
        world.say(
            f"{hero.id}'s knees felt wiggly for one moment. Even detectives do not always feel brave at first."
        )
    else:
        world.say(
            f"The trail led to {hiding.phrase}, which looked quiet instead of scary."
        )


def self_search(world: World, hero: Entity, reward_ent: Entity, hiding: HidingPlace) -> None:
    hero.memes["bravery"] += 1
    reward_ent.attrs["place"] = "found"
    reward_ent.meters["hidden"] = 0.0
    world.say(
        f"{hero.id} took one slow breath, then another, and crept forward all by {hero.pronoun('object')}self."
    )
    world.say(
        f'Under {hiding.label}, {hero.pronoun()} found the reward and laughed. '
        f'"Case closed!"'
    )


def ask_for_help(world: World, hero: Entity, giver: Entity, reward_ent: Entity, hiding: HidingPlace) -> None:
    hero.memes["bravery"] += 1
    hero.memes["trust"] += 1
    reward_ent.attrs["place"] = "found"
    reward_ent.meters["hidden"] = 0.0
    world.say(
        f"{hero.id} wanted to be brave, but the dark still felt too big alone."
    )
    world.say(
        f'So {hero.pronoun()} held {giver.label_word}\'s hand and said, "A detective can ask for backup."'
    )
    world.say(
        f"Together they peeped under {hiding.label} and found the reward shining there."
    )


def clear_misunderstanding(world: World, hero: Entity, pet_ent: Entity, giver: Entity, hiding: HidingPlace) -> None:
    hero.memes["relief"] += 1
    hero.memes["kindness"] += 1
    hero.memes["suspicion"] = 0.0
    world.say(
        f"{hero.id} looked back at {pet_ent.label} and felt a warm, sorry little squeeze inside."
    )
    world.say(
        f'"You did not take it after all," {hero.pronoun()} said. '
        f"{giver.label_word.capitalize()} nodded and explained that the reward had been hidden as part of a detective game."
    )
    if hiding.dark:
        world.say(
            f"The mystery had never been about blame. It had been about finding courage in a dark place."
        )
    else:
        world.say(
            f"The mystery had never been about blame. It had been about looking carefully before guessing."
        )


def ending(world: World, hero: Entity, reward: Reward, giver: Entity, pet_ent: Entity, hiding: HidingPlace) -> None:
    rhyme2 = f'"Small feet, sweet sleep, the promise you keep."'
    world.say(
        f'{giver.label_word.capitalize()} pinned {reward.phrase} onto the pajama top and said, {rhyme2}'
    )
    world.say(
        f"{hero.id} grinned at {pet_ent.label}, who gave a pleased little swish."
    )
    world.say(
        f"That night, the room felt softer. {hero.id} slipped into sleep already planning the next tiny case."
    )
    world.facts["rhyme2"] = rhyme2


def tell(
    reward: Reward,
    hiding: HidingPlace,
    giver_cfg: Giver,
    pet_cfg: Pet,
    hero_name: str,
    hero_gender: str,
    trait: str,
) -> World:
    world = World()
    hero = world.add(Entity(id="hero", kind="character", type=hero_gender, label=hero_name, role="hero"))
    hero.id = hero_name
    hero.attrs["trait"] = trait
    giver = world.add(Entity(id="giver", kind="character", type=giver_cfg.type, label="the parent", role="giver"))
    pet_ent = world.add(Entity(id="pet", type="pet", label=pet_cfg.label, phrase=pet_cfg.phrase, role="pet"))
    reward_ent = world.add(Entity(id="reward", type="reward", label=reward.label, phrase=reward.phrase, owner=hero_name))
    place_ent = world.add(Entity(id="place", type="place", label=hiding.label, phrase=hiding.phrase))

    introduce(world, hero, giver, reward)
    bedtime_setup(world, hero, reward_ent, pet_ent, giver)

    world.para()
    vanish(world, hero, reward_ent)
    misunderstanding(world, hero, pet_ent)
    first_clue(world, giver, hiding)
    detective_reasoning(world, hero, hiding)

    world.para()
    approach_dark_place(world, hero, hiding)
    if brave_enough(trait, hiding.dark):
        self_search(world, hero, reward_ent, hiding)
        outcome = "self_solved"
    else:
        ask_for_help(world, hero, giver, reward_ent, hiding)
        outcome = "helped_solved"

    world.para()
    clear_misunderstanding(world, hero, pet_ent, giver, hiding)
    ending(world, hero, reward, giver, pet_ent, hiding)

    world.facts.update(
        hero=hero,
        giver=giver,
        pet=pet_ent,
        reward_cfg=reward,
        hiding_cfg=hiding,
        reward=reward_ent,
        outcome=outcome,
        trait=trait,
        dark=hiding.dark,
        misunderstood_pet=True,
        found=True,
    )
    return world


# ---------------------------------------------------------------------------
# Content registries
# ---------------------------------------------------------------------------
REWARDS = {
    "star_chart": Reward(
        id="star_chart",
        label="star sticker",
        phrase="a shiny gold star sticker",
        flat=True,
        sleep_kind="good",
        tags={"reward", "sticker", "sleep"},
    ),
    "moon_badge": Reward(
        id="moon_badge",
        label="moon badge",
        phrase="a silver moon badge",
        flat=True,
        sleep_kind="calm",
        tags={"reward", "badge", "sleep"},
    ),
    "sun_card": Reward(
        id="sun_card",
        label="sun card",
        phrase="a bright sun reward card",
        flat=True,
        sleep_kind="quiet",
        tags={"reward", "card", "sleep"},
    ),
    # Deliberate decoy for the reasonableness gate.
    "drum": Reward(
        id="drum",
        label="toy drum",
        phrase="a little toy drum",
        flat=False,
        sleep_kind="none",
        tags={"toy"},
    ),
}

HIDING_PLACES = {
    "pillow": HidingPlace(
        id="pillow",
        label="the pillow",
        phrase="the pillow by the bed",
        accepts_flat=True,
        dark=False,
        rhyme_a="creep",
        rhyme_b="sleep",
        tags={"bedroom", "pillow"},
    ),
    "blanket_fold": HidingPlace(
        id="blanket_fold",
        label="the blanket fold",
        phrase="the folded blanket at the foot of the bed",
        accepts_flat=True,
        dark=False,
        rhyme_a="deep",
        rhyme_b="sleep",
        tags={"bedroom", "blanket"},
    ),
    "under_bed": HidingPlace(
        id="under_bed",
        label="the bed",
        phrase="the space under the bed",
        accepts_flat=True,
        dark=True,
        rhyme_a="keep",
        rhyme_b="sleep",
        tags={"bedroom", "dark"},
    ),
    "closet_slipper": HidingPlace(
        id="closet_slipper",
        label="the closet slipper",
        phrase="the closet corner behind one slipper",
        accepts_flat=True,
        dark=True,
        rhyme_a="peep",
        rhyme_b="sleep",
        tags={"closet", "dark"},
    ),
}

GIVERS = {
    "mother": Giver(
        id="mother",
        type="mother",
        label="the parent",
        style="gentle",
        tags={"parent"},
    ),
    "father": Giver(
        id="father",
        type="father",
        label="the parent",
        style="warm",
        tags={"parent"},
    ),
}

PETS = {
    "cat": Pet(
        id="cat",
        label="the cat",
        phrase="the cat",
        tags={"cat"},
    ),
    "dog": Pet(
        id="dog",
        label="the puppy",
        phrase="the puppy",
        tags={"dog"},
    ),
    "rabbit": Pet(
        id="rabbit",
        label="the rabbit",
        phrase="the rabbit",
        tags={"rabbit"},
    ),
}

GIRL_NAMES = ["Lila", "Mia", "Nora", "Ava", "Ella", "Lucy", "Ivy", "Ruby"]
BOY_NAMES = ["Ben", "Max", "Theo", "Sam", "Leo", "Noah", "Eli", "Finn"]
TRAITS = ["timid", "careful", "curious", "steady", "brave"]


# ---------------------------------------------------------------------------
# Per-world parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    reward: str
    hiding: str
    giver: str
    pet: str
    name: str
    gender: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
KNOWLEDGE = {
    "reward": [
        (
            "What is a reward?",
            "A reward is a small prize or nice thing someone gets after doing something well. In this story world, the reward celebrates a calm night of sleep.",
        )
    ],
    "sleep": [
        (
            "Why is sleep important?",
            "Sleep helps your body and brain rest and grow. After good sleep, children often feel calmer, stronger, and more ready for the day.",
        )
    ],
    "detective": [
        (
            "What does a detective do?",
            "A detective looks for clues and tries to solve a mystery. Good detectives pay attention before they decide what happened.",
        )
    ],
    "rhyme": [
        (
            "What is a rhyme?",
            "A rhyme uses words that sound alike, like sleep and keep. Rhymes can make clues easier to remember.",
        )
    ],
    "bravery": [
        (
            "What is bravery?",
            "Bravery does not mean never feeling scared. It means doing the next careful thing even when you feel a little afraid.",
        )
    ],
    "misunderstanding": [
        (
            "What is a misunderstanding?",
            "A misunderstanding happens when someone guesses wrong about what is going on. Asking questions and checking clues can clear it up.",
        )
    ],
    "bedroom": [
        (
            "Why do things sometimes get lost in a bedroom?",
            "Bedrooms have blankets, pillows, beds, and corners where small things can slip or hide. A careful search often finds them.",
        )
    ],
}
KNOWLEDGE_ORDER = ["reward", "sleep", "detective", "rhyme", "bravery", "misunderstanding", "bedroom"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    reward = f["reward_cfg"]
    hiding = f["hiding_cfg"]
    outcome = f["outcome"]
    help_line = "finds it alone" if outcome == "self_solved" else "asks for backup and solves it with a parent"
    return [
        f'Write a detective story for a 3-to-5-year-old that includes the words "reward" and "sleep".',
        f"Tell a gentle mystery about a child named {hero.id} who loses {reward.phrase}, misunderstands the pet, follows rhyming clues, and {help_line}.",
        f"Write a bedtime detective story with a dark clue near {hiding.label}, a misunderstanding, a brave moment, and a warm ending.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    giver = f["giver"]
    pet = f["pet"]
    reward = f["reward_cfg"]
    hiding = f["hiding_cfg"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, a child who treats a missing bedtime reward like a detective case. {giver.label_word.capitalize()} and {pet.label} are part of the mystery too.",
        ),
        (
            f"What reward had {hero.id} earned?",
            f"{hero.id} had earned {reward.phrase} for a night of good sleep. The reward mattered because it reminded {hero.pronoun('object')} of doing something hard and proud.",
        ),
        (
            f"Why did {hero.id} think {pet.label} had taken the reward?",
            f"{hero.id} woke up and found the bedside table empty, so the reward seemed to be gone. Because {pet.label} was nearby, {hero.pronoun()} guessed too quickly and had a misunderstanding.",
        ),
        (
            "What clue helped solve the mystery?",
            f"A folded paper gave a rhyming clue about looking where dreams still sleep. The rhyme pointed {hero.id} toward {hiding.label}.",
        ),
    ]
    if hiding.dark:
        qa.append(
            (
                f"How was {hero.id} brave?",
                f"{hero.id} had to face {hiding.phrase}, which felt dark and a little spooky. "
                + (
                    f"{hero.pronoun().capitalize()} took slow breaths and searched there anyway."
                    if outcome == "self_solved"
                    else f"{hero.pronoun().capitalize()} was brave enough to admit the dark felt big and to ask {giver.label_word} for backup."
                ),
            )
        )
    else:
        qa.append(
            (
                f"How did {hero.id} solve the case?",
                f"{hero.id} listened carefully to the rhyme and thought about where the clue pointed. That careful thinking led {hero.pronoun('object')} to {hiding.label}, where the reward was waiting.",
            )
        )
    qa.append(
        (
            f"Was {pet.label} really the one who took the reward?",
            f"No. The reward had been hidden as part of a detective game, so {hero.id}'s first guess was wrong. The story shows that checking clues is kinder than blaming someone too fast.",
        )
    )
    qa.append(
        (
            "How did the story end?",
            f"The reward was found, the misunderstanding was cleared up, and {hero.id} felt proud and calm. At the end, the room feels safe again and {hero.pronoun()} drifts toward sleep with a solved case behind {hero.pronoun('object')}.",
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"reward", "sleep", "detective", "rhyme", "misunderstanding", "bedroom"}
    if world.facts.get("dark"):
        tags.add("bravery")
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


# ---------------------------------------------------------------------------
# Trace
# ---------------------------------------------------------------------------
def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        if e.role:
            bits.append(f"role={e.role}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Curated set
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(
        reward="star_chart",
        hiding="under_bed",
        giver="mother",
        pet="cat",
        name="Lila",
        gender="girl",
        trait="brave",
    ),
    StoryParams(
        reward="moon_badge",
        hiding="closet_slipper",
        giver="father",
        pet="dog",
        name="Ben",
        gender="boy",
        trait="careful",
    ),
    StoryParams(
        reward="sun_card",
        hiding="pillow",
        giver="mother",
        pet="rabbit",
        name="Nora",
        gender="girl",
        trait="curious",
    ),
    StoryParams(
        reward="star_chart",
        hiding="blanket_fold",
        giver="father",
        pet="cat",
        name="Theo",
        gender="boy",
        trait="steady",
    ),
]


# ---------------------------------------------------------------------------
# Rejection helpers
# ---------------------------------------------------------------------------
def explain_rejection(reward: Reward, hiding: HidingPlace) -> str:
    if not reward.flat:
        return (
            f"(No story: {reward.phrase} is too bulky for a gentle bedtime hiding game. "
            f"This world expects a small flat reward that could plausibly slip under or beside {hiding.label}.)"
        )
    if not hiding.accepts_flat:
        return (
            f"(No story: {hiding.label} is not a plausible place for this reward in this world.)"
        )
    return "(No story: this reward and hiding place do not make a reasonable detective mystery.)"


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% Reasonableness gate
valid(R, H, G) :- reward(R), hiding(H), giver(G), flat(R), accepts_flat(H).

% Outcome model
need(4) :- chosen_hiding(H), dark(H).
need(2) :- chosen_hiding(H), not dark(H).

trait_score(2) :- chosen_trait(timid).
trait_score(3) :- chosen_trait(careful).
trait_score(4) :- chosen_trait(curious).
trait_score(4) :- chosen_trait(steady).
trait_score(5) :- chosen_trait(brave).

brave_enough :- trait_score(S), need(N), S >= N.

outcome(self_solved) :- brave_enough.
outcome(helped_solved) :- not brave_enough.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for rid, reward in REWARDS.items():
        lines.append(asp.fact("reward", rid))
        if reward.flat:
            lines.append(asp.fact("flat", rid))
    for hid, hiding in HIDING_PLACES.items():
        lines.append(asp.fact("hiding", hid))
        if hiding.accepts_flat:
            lines.append(asp.fact("accepts_flat", hid))
        if hiding.dark:
            lines.append(asp.fact("dark", hid))
    for gid in GIVERS:
        lines.append(asp.fact("giver", gid))
    for trait in TRAITS:
        lines.append(asp.fact("trait_name", trait))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_hiding", params.hiding),
            asp.fact("chosen_trait", params.trait),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    cases = list(CURATED)
    for s in range(30):
        rng = random.Random(s)
        try:
            params = resolve_params(build_parser().parse_args([]), rng)
        except StoryError:
            continue
        cases.append(params)
    mismatches = []
    for params in cases:
        a = asp_outcome(params)
        p = outcome_of(params)
        if a != p:
            mismatches.append((params, a, p))
    if mismatches:
        rc = 1
        print(f"MISMATCH in outcomes: {len(mismatches)} cases.")
        for params, a, p in mismatches[:5]:
            print(" ", params, "asp=", a, "python=", p)
    else:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")

    # Smoke test ordinary generation.
    try:
        sample = generate(cases[0])
        if not sample.story.strip():
            raise StoryError("Generated empty story during verify.")
        print("OK: generate() smoke test passed.")
    except Exception as exc:  # pragma: no cover - defensive verify path
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


# ---------------------------------------------------------------------------
# Interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A bedtime detective story world about a missing reward, sleep, rhymes, and bravery."
    )
    ap.add_argument("--reward", choices=REWARDS)
    ap.add_argument("--hiding", choices=HIDING_PLACES)
    ap.add_argument("--giver", choices=GIVERS)
    ap.add_argument("--pet", choices=PETS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--trait", choices=TRAITS)
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.reward and args.hiding:
        reward = REWARDS[args.reward]
        hiding = HIDING_PLACES[args.hiding]
        if not hiding_fits(reward, hiding):
            raise StoryError(explain_rejection(reward, hiding))

    combos = [
        combo
        for combo in valid_combos()
        if (args.reward is None or combo[0] == args.reward)
        and (args.hiding is None or combo[1] == args.hiding)
        and (args.giver is None or combo[2] == args.giver)
    ]
    if not combos:
        if args.reward and args.hiding:
            raise StoryError(explain_rejection(REWARDS[args.reward], HIDING_PLACES[args.hiding]))
        raise StoryError("(No valid combination matches the given options.)")

    reward_id, hiding_id, giver_id = rng.choice(sorted(combos))
    pet_id = args.pet or rng.choice(sorted(PETS))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(
        reward=reward_id,
        hiding=hiding_id,
        giver=giver_id,
        pet=pet_id,
        name=name,
        gender=gender,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.reward not in REWARDS:
        raise StoryError(f"(Unknown reward: {params.reward})")
    if params.hiding not in HIDING_PLACES:
        raise StoryError(f"(Unknown hiding place: {params.hiding})")
    if params.giver not in GIVERS:
        raise StoryError(f"(Unknown giver: {params.giver})")
    if params.pet not in PETS:
        raise StoryError(f"(Unknown pet: {params.pet})")
    if params.trait not in TRAITS:
        raise StoryError(f"(Unknown trait: {params.trait})")
    if not hiding_fits(REWARDS[params.reward], HIDING_PLACES[params.hiding]):
        raise StoryError(explain_rejection(REWARDS[params.reward], HIDING_PLACES[params.hiding]))

    world = tell(
        reward=REWARDS[params.reward],
        hiding=HIDING_PLACES[params.hiding],
        giver_cfg=GIVERS[params.giver],
        pet_cfg=PETS[params.pet],
        hero_name=params.name,
        hero_gender=params.gender,
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (reward, hiding, giver) combos:\n")
        for reward, hiding, giver in combos:
            print(f"  {reward:10} {hiding:14} {giver}")
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
            header = f"### {p.name}: {p.reward} hidden at {p.hiding} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
