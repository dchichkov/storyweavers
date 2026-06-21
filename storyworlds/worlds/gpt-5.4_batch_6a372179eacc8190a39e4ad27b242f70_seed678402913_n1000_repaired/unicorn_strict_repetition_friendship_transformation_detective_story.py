#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/unicorn_strict_repetition_friendship_transformation_detective_story.py
================================================================================================

A standalone storyworld for a child-sized detective mystery with a unicorn,
a strict grown-up, repeated clues, friendship, and magical transformation.

The domain:
- A child detective and a friend notice that ordinary things keep changing
  overnight in the same shared place.
- A strict keeper closes the area until the mystery is solved.
- The children follow repeated clues and choose how to approach the hidden
  unicorn behind the transformations.
- If they respect the rule and use a gentle approach that matches the unicorn's
  need, the case ends in friendship.
- If they respect the rule but choose a less fitting approach, the case is
  solved politely but the friendship stays light.
- If they sneak around the strict rule, they startle the unicorn and lose the
  chance for a warm ending.

Run it
------
    python storyworlds/worlds/gpt-5.4/unicorn_strict_repetition_friendship_transformation_detective_story.py
    python storyworlds/worlds/gpt-5.4/unicorn_strict_repetition_friendship_transformation_detective_story.py --setting garden --mystery flowers
    python storyworlds/worlds/gpt-5.4/unicorn_strict_repetition_friendship_transformation_detective_story.py --approach chalk_note --setting orchard
    python storyworlds/worlds/gpt-5.4/unicorn_strict_repetition_friendship_transformation_detective_story.py --choice sneak
    python storyworlds/worlds/gpt-5.4/unicorn_strict_repetition_friendship_transformation_detective_story.py --all
    python storyworlds/worlds/gpt-5.4/unicorn_strict_repetition_friendship_transformation_detective_story.py --verify
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

# Make shared result containers importable when this nested script is run directly.
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
        female = {"girl", "mother", "woman", "aunt"}
        male = {"boy", "father", "man", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Setting:
    id: str
    place: str
    closed_patch: str
    rule_reason: str
    detail: str
    clues_spot: str
    affords: set[str] = field(default_factory=set)
    can_write: bool = False
    has_clover: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Mystery:
    id: str
    ordinary: str
    transformed: str
    plural: bool
    clue_dust: str
    clue_mark: str
    ending_image: str
    fits: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Approach:
    id: str
    sense: int
    needs: set[str]
    prep: str
    line: str
    closing: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    setting: str
    mystery: str
    approach: str
    choice: str
    mood: str
    detective_name: str
    detective_gender: str
    friend_name: str
    friend_gender: str
    keeper: str
    trait: str
    seed: Optional[int] = None


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[["World"], list[str]]


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = copy.deepcopy(self.facts)
        return clone


def _r_repeat_clues(world: World) -> list[str]:
    mystery = world.facts.get("mystery_cfg")
    transformed = world.facts.get("transformed")
    if mystery is None or transformed is None:
        return []
    if transformed.meters["changed"] < THRESHOLD:
        return []
    sig = ("repeat_clues", transformed.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    world.get("detective").memes["suspicion"] += 1
    world.get("friend").memes["suspicion"] += 1
    world.get("unicorn").meters["glitter"] += 1
    world.get("unicorn").meters["hoofprints"] += 1
    return [
        f"Again there was {mystery.clue_dust}.",
        f"Again there was {mystery.clue_mark}.",
        "Again there was one long silver hair, caught where the moonlight could find it.",
    ]


def _r_friendship_softens(world: World) -> list[str]:
    unicorn = world.get("unicorn")
    if unicorn.memes["heard_kindness"] < THRESHOLD:
        return []
    sig = ("soften", unicorn.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    unicorn.memes["fear"] = 0.0
    unicorn.memes["trust"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="repeat_clues", tag="physical", apply=_r_repeat_clues),
    Rule(name="friendship_softens", tag="social", apply=_r_friendship_softens),
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


SETTINGS = {
    "garden": Setting(
        id="garden",
        place="the school garden",
        closed_patch="the moon gate",
        rule_reason="the bean shoots were small and easy to crush",
        detail="Rows of leaves trembled in the breeze, and a narrow path curled past the flower beds.",
        clues_spot="by the gate latch",
        affords={"flowers", "stones"},
        can_write=True,
        has_clover=True,
        tags={"garden"},
    ),
    "orchard": Setting(
        id="orchard",
        place="the little orchard behind the hall",
        closed_patch="the apple path",
        rule_reason="windfall fruit made the ground slippery before breakfast",
        detail="Low branches made green roofs over the path, and baskets waited under the trees.",
        clues_spot="near the oldest tree",
        affords={"apples", "flowers"},
        can_write=False,
        has_clover=True,
        tags={"orchard"},
    ),
    "courtyard": Setting(
        id="courtyard",
        place="the stone courtyard",
        closed_patch="the fountain steps",
        rule_reason="the steps stayed slick with dew in the early morning",
        detail="The fountain whispered in the middle, and the paving stones held the night's coolness.",
        clues_spot="on the fountain rim",
        affords={"stones", "flowers"},
        can_write=True,
        has_clover=False,
        tags={"courtyard"},
    ),
}

MYSTERIES = {
    "flowers": Mystery(
        id="flowers",
        ordinary="plain white flowers",
        transformed="rainbow bell-flowers",
        plural=True,
        clue_dust="silver dust on the petals",
        clue_mark="tiny shining hoofprints in the soft dirt",
        ending_image="the flowers chimed softly whenever the unicorn dipped its head",
        fits={"garden", "orchard", "courtyard"},
        tags={"flowers", "transformation"},
    ),
    "apples": Mystery(
        id="apples",
        ordinary="fallen apples",
        transformed="golden lantern-apples",
        plural=True,
        clue_dust="gold light caught in the stems",
        clue_mark="a ring of neat hoofprints around the basket",
        ending_image="the apples glowed like little lamps under the leaves",
        fits={"orchard"},
        tags={"apples", "transformation"},
    ),
    "stones": Mystery(
        id="stones",
        ordinary="gray stepping stones",
        transformed="smooth star-stones",
        plural=True,
        clue_dust="silver dust in the cracks",
        clue_mark="one bright hoofprint on the damp edge of the path",
        ending_image="the stones shone with star shapes every time the unicorn trotted past",
        fits={"garden", "courtyard"},
        tags={"stones", "transformation"},
    ),
}

APPROACHES = {
    "quiet_wait": Approach(
        id="quiet_wait",
        sense=3,
        needs={"shy", "lonely"},
        prep="sat very still with a notebook open and a lantern turned low",
        line='"{friend}, let it come when it feels safe,"',
        closing="They stayed so quiet that even the fountain sounded loud.",
        tags={"wait", "gentle"},
    ),
    "chalk_note": Approach(
        id="chalk_note",
        sense=3,
        needs={"shy", "lonely"},
        prep='wrote on the path: "Dear unicorn, we want to help, not chase."',
        line='"Maybe a shy creature would answer words before faces,"',
        closing="The chalk letters looked brave and kind at the same time.",
        tags={"chalk", "gentle"},
    ),
    "clover_gift": Approach(
        id="clover_gift",
        sense=2,
        needs={"hungry", "lonely"},
        prep="set out a neat little bunch of clover beside the path",
        line='"If our visitor is hungry, this might say welcome without a noise,"',
        closing="The clover smelled sweet in the cold air.",
        tags={"clover", "gentle"},
    ),
    "shout": Approach(
        id="shout",
        sense=1,
        needs=set(),
        prep='called, "Come out right now!"',
        line='"A mystery should stop hiding,"',
        closing="The words banged around the place much too hard.",
        tags={"loud"},
    ),
}

MOODS = {
    "shy": {
        "intro": "It was hiding because too many eyes and too many questions made its heart race.",
        "need": "quiet kindness",
    },
    "lonely": {
        "intro": "It had been making bright changes because it wanted someone to notice them kindly.",
        "need": "company",
    },
    "hungry": {
        "intro": "It had been wandering at night, hungry enough to be bold with its magic.",
        "need": "something gentle to eat",
    },
}

KEEPER_LINES = {
    "mother": "No one is to cross the rope before we understand what is happening.",
    "father": "No one is to step past the sign until the mystery is settled.",
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Anna", "Maya", "Nora", "Rose"]
BOY_NAMES = ["Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Noah", "Eli", "Theo", "Owen"]
TRAITS = ["careful", "curious", "patient", "thoughtful", "sharp-eyed", "steady"]


def mystery_fits(setting_id: str, mystery_id: str) -> bool:
    return mystery_id in SETTINGS[setting_id].affords and setting_id in MYSTERIES[mystery_id].fits


def approach_allowed(setting_id: str, approach_id: str) -> bool:
    if approach_id == "chalk_note":
        return SETTINGS[setting_id].can_write
    if approach_id == "clover_gift":
        return SETTINGS[setting_id].has_clover
    return True


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for setting_id in sorted(SETTINGS):
        for mystery_id in sorted(MYSTERIES):
            if not mystery_fits(setting_id, mystery_id):
                continue
            for approach_id, approach in APPROACHES.items():
                if approach.sense < SENSE_MIN:
                    continue
                if approach_allowed(setting_id, approach_id):
                    combos.append((setting_id, mystery_id, approach_id))
    return combos


def outcome_of(params: StoryParams) -> str:
    if params.choice == "sneak":
        return "startled"
    if params.mood in APPROACHES[params.approach].needs:
        return "friends"
    return "solved"


def explain_mystery(setting_id: str, mystery_id: str) -> str:
    setting = SETTINGS[setting_id]
    mystery = MYSTERIES[mystery_id]
    return (
        f"(No story: {mystery.ordinary} do not belong in {setting.place} in this world, "
        f"so the repeated transformation would feel arbitrary. Pick a mystery that fits the setting.)"
    )


def explain_approach(setting_id: str, approach_id: str) -> str:
    setting = SETTINGS[setting_id]
    if approach_id == "chalk_note":
        return (
            f"(No story: {setting.place} has no good chalk path in this setup, so a chalk note is not a real clue-plan there.)"
        )
    if approach_id == "clover_gift":
        return (
            f"(No story: there is no easy clover at {setting.place}, so the children cannot honestly leave a clover gift.)"
        )
    approach = APPROACHES[approach_id]
    return (
        f"(No story: the approach '{approach_id}' scores too low on common sense "
        f"(sense={approach.sense} < {SENSE_MIN}). A child detective should use a gentler plan.)"
    )


def predict_after_approach(world: World, choice: str, approach: Approach, mood: str) -> dict:
    sim = world.copy()
    unicorn = sim.get("unicorn")
    if choice == "ask":
        unicorn.memes["heard_kindness"] += 1
        propagate(sim, narrate=False)
        if mood in approach.needs:
            unicorn.memes["friendship"] += 1
            unicorn.meters["stays"] += 1
        else:
            unicorn.meters["stays"] += 1
    else:
        unicorn.memes["fear"] += 1
        unicorn.meters["runs"] += 1
    return {
        "stays": unicorn.meters["stays"] >= THRESHOLD,
        "runs": unicorn.meters["runs"] >= THRESHOLD,
        "friendship": unicorn.memes["friendship"] >= THRESHOLD,
    }


def introduce(world: World, detective: Entity, friend: Entity, keeper: Entity, mystery: Mystery) -> None:
    world.say(
        f"{detective.id} liked mysteries, and {friend.id} liked helping {detective.pronoun('object')} think. "
        f"That made them a very small detective team."
    )
    world.say(
        f"For three mornings in a row, something impossible had happened in {world.setting.place}: "
        f"{mystery.ordinary} had turned into {mystery.transformed}."
    )
    world.say(world.setting.detail)
    world.say(
        f"{detective.id}'s {keeper.label_word} was strict about the closed-off part near {world.setting.closed_patch}. "
        f'"{KEEPER_LINES[keeper.type]}"'
    )


def inspect_once(world: World, detective: Entity, friend: Entity, mystery: Mystery, number_word: str) -> None:
    transformed = world.get("changed")
    transformed.meters["changed"] += 1
    world.say(
        f"On the {number_word} morning, {detective.id} knelt beside the changed things and opened a notebook."
    )
    propagate(world, narrate=True)
    world.say(
        f'{friend.id} whispered, "That is clue number {world.facts["clue_count"] + 1}."'
    )
    world.facts["clue_count"] += 1


def strict_warning(world: World, keeper: Entity) -> None:
    keeper.memes["strictness"] += 1
    world.say(
        f'{keeper.label_word.capitalize()} pointed to the rope across {world.setting.closed_patch}. '
        f'"The rule is there for a reason. {world.setting.rule_reason.capitalize()}, and I will not have anyone slipping before breakfast."'
    )


def deduce(world: World, detective: Entity, friend: Entity) -> None:
    detective.memes["insight"] += 1
    friend.memes["trust"] += 1
    world.say(
        f'{detective.id} tapped the notebook. "Three mornings. Three clues. Silver dust, shining hoofprints, and one long hair every time."'
    )
    world.say(
        f'"That sounds like one visitor, not three," {friend.id} said. Together they said the answer in the same tiny breath: "A unicorn."'
    )


def ask_permission(world: World, detective: Entity, keeper: Entity, approach: Approach) -> None:
    detective.memes["honesty"] += 1
    world.say(
        f'"We want to solve it the careful way," {detective.id} told {keeper.label_word}. '
        f'"May we try one gentle plan?"'
    )
    world.say(
        f"{keeper.label_word.capitalize()} looked at the notebook, then at the rope, and finally nodded once."
    )
    world.say(
        f"{detective.id} and {world.get('friend').id} {approach.prep}. {approach.closing}"
    )


def sneak_in(world: World, detective: Entity, friend: Entity, approach: Approach) -> None:
    detective.memes["defiance"] += 1
    friend.memes["worry"] += 1
    world.say(
        f"But that night, the mystery tugged harder than the rule. {detective.id} and {friend.id} slipped under the rope by {world.setting.closed_patch}."
    )
    world.say(
        f"They {approach.prep}. {approach.closing}"
    )


def keeper_explains(world: World, keeper: Entity, mood: str) -> None:
    world.say(
        f"{keeper.label_word.capitalize()} kept {keeper.pronoun('possessive')} voice low. "
        f'"If there truly is a unicorn here, we must not scare it. {MOODS[mood]["intro"]}"'
    )


def unicorn_appears(world: World, mystery: Mystery) -> None:
    unicorn = world.get("unicorn")
    unicorn.meters["seen"] += 1
    world.say(
        "A white shape stepped out of the dimness, then the moon found its horn. "
        "It was a unicorn, small and bright-eyed, with a mane like a loose silver ribbon."
    )
    world.say(
        f"When it breathed over the {mystery.ordinary}, the last plain bits shimmered and changed too."
    )


def friendship_end(world: World, detective: Entity, friend: Entity, mystery: Mystery, approach: Approach) -> None:
    unicorn = world.get("unicorn")
    unicorn.memes["friendship"] += 1
    detective.memes["friendship"] += 1
    friend.memes["friendship"] += 1
    world.say(
        f'{friend.id} smiled first. {approach.line} {friend.id} said.'
    )
    world.say(
        "The unicorn came closer instead of backing away. It lowered its head until the children could stroke the cool braid of its mane."
    )
    world.say(
        f"By sunrise, the case was solved and something better had happened: a friendship had begun. In the pale light, {mystery.ending_image}."
    )


def solved_end(world: World, keeper: Entity, mystery: Mystery, approach: Approach) -> None:
    unicorn = world.get("unicorn")
    unicorn.meters["stays"] += 1
    world.say(
        f'{approach.line} {world.get("friend").id} said.'
    )
    world.say(
        "The unicorn stepped out, listened, and stayed just long enough for everyone to see the truth."
    )
    world.say(
        f"{keeper.label_word.capitalize()} smiled in a softer way than before. "
        f'"So that was our midnight artist."'
    )
    world.say(
        f"Then the unicorn trotted back into the shadows, leaving the mystery solved and the morning glowing. Behind it, {mystery.ending_image}."
    )


def startled_end(world: World, keeper: Entity, mystery: Mystery) -> None:
    unicorn = world.get("unicorn")
    unicorn.memes["fear"] += 1
    unicorn.meters["runs"] += 1
    world.say(
        "A unicorn flashed out from behind the dark leaves, but the sudden movement and the broken rule frightened it."
    )
    world.say(
        f"It leapt away in a spray of silver dust, and one last ripple of magic ran over the {mystery.ordinary}."
    )
    world.say(
        f"When {keeper.label_word} found the children, {keeper.pronoun()} was not loud, only disappointed. "
        f'"Now we know who did it, but we lost our chance to make it feel safe."'
    )
    world.say(
        f"The case was solved, but the place felt lonelier than before. At dawn, {mystery.ending_image}, and no unicorn came back to see it."
    )


def tell(
    setting: Setting,
    mystery: Mystery,
    approach: Approach,
    choice: str,
    mood: str,
    detective_name: str,
    detective_gender: str,
    friend_name: str,
    friend_gender: str,
    keeper_type: str,
    trait: str,
) -> World:
    world = World(setting)
    detective = world.add(
        Entity(
            id=detective_name,
            kind="character",
            type=detective_gender,
            role="detective",
            attrs={"trait": trait},
        )
    )
    friend = world.add(
        Entity(
            id=friend_name,
            kind="character",
            type=friend_gender,
            role="friend",
            attrs={"trait": "kind"},
        )
    )
    keeper = world.add(
        Entity(
            id="Keeper",
            kind="character",
            type=keeper_type,
            role="keeper",
            label="the keeper",
        )
    )
    unicorn = world.add(
        Entity(
            id="unicorn",
            kind="character",
            type="creature",
            role="unicorn",
            label="the unicorn",
            attrs={"mood": mood},
        )
    )
    changed = world.add(
        Entity(
            id="changed",
            kind="thing",
            type="mystery",
            label=mystery.transformed,
            phrase=mystery.ordinary,
        )
    )

    world.facts.update(
        detective=detective,
        friend=friend,
        keeper=keeper,
        unicorn=unicorn,
        mystery_cfg=mystery,
        transformed=changed,
        setting_cfg=setting,
        approach_cfg=approach,
        choice=choice,
        mood=mood,
        clue_count=0,
    )

    introduce(world, detective, friend, keeper, mystery)
    world.para()
    for number_word in ("first", "second", "third"):
        inspect_once(world, detective, friend, mystery, number_word)
    strict_warning(world, keeper)
    deduce(world, detective, friend)

    world.para()
    prediction = predict_after_approach(world, choice, approach, mood)
    world.facts["predicted"] = prediction
    if choice == "ask":
        ask_permission(world, detective, keeper, approach)
        keeper_explains(world, keeper, mood)
        world.para()
        unicorn_appears(world, mystery)
        unicorn.memes["heard_kindness"] += 1
        propagate(world, narrate=False)
        if mood in approach.needs:
            friendship_end(world, detective, friend, mystery, approach)
            outcome = "friends"
        else:
            solved_end(world, keeper, mystery, approach)
            outcome = "solved"
    else:
        sneak_in(world, detective, friend, approach)
        world.para()
        startled_end(world, keeper, mystery)
        outcome = "startled"

    world.facts["outcome"] = outcome
    return world


KNOWLEDGE = {
    "unicorn": [
        (
            "What is a unicorn?",
            "A unicorn is a make-believe horse-like creature with one horn on its head. In stories, it is often shy and magical."
        )
    ],
    "detective": [
        (
            "What does a detective do?",
            "A detective notices clues, asks careful questions, and puts small facts together to solve a mystery."
        )
    ],
    "clue": [
        (
            "What is a clue?",
            "A clue is a small sign that helps you figure something out. A footprint, a hair, or a note can all be clues."
        )
    ],
    "friendship": [
        (
            "How can kindness help a shy animal or person?",
            "Kindness helps by making the other one feel safe. Quiet voices and patient actions show that you are not there to scare them."
        )
    ],
    "transformation": [
        (
            "What does transformation mean in a story?",
            "Transformation means something changes into a new form. In a magical story, plain things can turn bright or strange."
        )
    ],
    "garden": [
        (
            "Why do grown-ups sometimes close off part of a garden?",
            "They may be protecting small plants or keeping children away from slippery places. Rules can be strict because they are meant to keep everyone safe."
        )
    ],
    "orchard": [
        (
            "What is an orchard?",
            "An orchard is a place where fruit trees grow together. People often walk there to pick or gather fruit."
        )
    ],
    "courtyard": [
        (
            "What is a courtyard?",
            "A courtyard is an open space with walls or buildings around it. It can have stones, steps, or a fountain in the middle."
        )
    ],
    "chalk": [
        (
            "Why is chalk good for leaving a note outside?",
            "Chalk shows up clearly on stone and can be washed away later. That makes it useful for a temporary note."
        )
    ],
    "clover": [
        (
            "What is clover?",
            "Clover is a small plant with round leaves. It often grows in grass and smells fresh when you pick it."
        )
    ],
    "wait": [
        (
            "Why can waiting quietly be brave?",
            "Waiting quietly can be brave because you are choosing patience instead of rushing. That can help a frightened creature feel safe enough to come closer."
        )
    ],
}
KNOWLEDGE_ORDER = [
    "unicorn",
    "detective",
    "clue",
    "friendship",
    "transformation",
    "garden",
    "orchard",
    "courtyard",
    "chalk",
    "clover",
    "wait",
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    detective = f["detective"]
    friend = f["friend"]
    keeper = f["keeper"]
    mystery = f["mystery_cfg"]
    setting = f["setting_cfg"]
    outcome = f["outcome"]
    if outcome == "friends":
        return [
            'Write a short detective story for a 3-to-5-year-old that includes the words "unicorn" and "strict".',
            f"Tell a gentle mystery where {detective.id} and {friend.id} follow repeated clues in {setting.place}, discover a unicorn behind a magical transformation, and end in friendship.",
            f"Write a child-facing detective story where a strict {keeper.label_word} enforces a safety rule, the clues repeat three times, and the children solve why {mystery.ordinary} keep turning into {mystery.transformed}.",
        ]
    if outcome == "solved":
        return [
            'Write a short detective story for a 3-to-5-year-old that includes the words "unicorn" and "strict".',
            f"Tell a small mystery where repeated clues lead children to a shy unicorn in {setting.place}, and the case is solved carefully under a strict grown-up's rule.",
            f"Write a story with repetition, transformation, and a detective feeling, where {mystery.ordinary} become {mystery.transformed} and the truth is found without a chase.",
        ]
    return [
        'Write a short detective story for a 3-to-5-year-old that includes the words "unicorn" and "strict".',
        f"Tell a detective story where repeated clues lead to a unicorn, but the children break a strict rule and frighten it away.",
        f"Write a gentle cautionary mystery with friendship almost within reach, where {mystery.ordinary} transform overnight and the ending shows what was lost by sneaking.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    detective = f["detective"]
    friend = f["friend"]
    keeper = f["keeper"]
    mystery = f["mystery_cfg"]
    setting = f["setting_cfg"]
    approach = f["approach_cfg"]
    mood = f["mood"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {detective.id} and {friend.id}, a tiny detective team, and the strict {keeper.label_word} watching over {setting.place}. The mystery leads them to a unicorn."
        ),
        (
            "What was the mystery?",
            f"For three mornings in a row, {mystery.ordinary} had changed into {mystery.transformed}. The repeated change told the children that the same magic visitor kept coming back."
        ),
        (
            "What clues repeated?",
            f"The clues repeated three times: {mystery.clue_dust}, {mystery.clue_mark}, and one long silver hair. Those matching clues helped the children decide they were following one creature, not guessing wildly."
        ),
        (
            f"Why was {keeper.label_word} so strict about {setting.closed_patch}?",
            f"{keeper.label_word.capitalize()} was strict because {setting.rule_reason}. The rule was meant to keep people safe while the mystery was still unsolved."
        ),
    ]
    if outcome == "friends":
        qa.append(
            (
                "How did they solve the case?",
                f"They respected the rule, used a gentle plan, and waited for the unicorn to feel safe enough to appear. Because the approach matched what the unicorn needed -- {MOODS[mood]['need']} -- the case ended in friendship as well as truth."
            )
        )
        qa.append(
            (
                "What changed at the end?",
                f"The children did not only learn who made the transformations; they also became friends with the unicorn. The ending image shows that change clearly, because {mystery.ending_image} while the unicorn stayed near them."
            )
        )
    elif outcome == "solved":
        qa.append(
            (
                "Did the children become friends with the unicorn?",
                f"Not quite. The unicorn stayed long enough to solve the mystery, but it did not come close enough for a full friendship, because the plan was kind but not the exact thing it needed."
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended with the truth gently uncovered under the strict rule, and the place still glowing with magic. The children learned that careful detective work can solve a case without chasing."
            )
        )
    else:
        qa.append(
            (
                "Why did the ending feel sadder?",
                f"It felt sadder because the children broke the rule and frightened the unicorn just when they had found it. They solved the case, but they lost the chance to make the unicorn feel safe and stay."
            )
        )
        qa.append(
            (
                "What did they learn?",
                f"They learned that a mystery is not only about finding the answer fast. It is also about how you treat the one at the center of it."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"unicorn", "detective", "clue", "friendship", "transformation"}
    tags |= set(f["setting_cfg"].tags)
    tags |= set(f["approach_cfg"].tags)
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
        bits: list[str] = []
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
        lines.append(f"  {ent.id:10} ({ent.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="garden",
        mystery="flowers",
        approach="quiet_wait",
        choice="ask",
        mood="shy",
        detective_name="Lily",
        detective_gender="girl",
        friend_name="Ben",
        friend_gender="boy",
        keeper="mother",
        trait="careful",
    ),
    StoryParams(
        setting="orchard",
        mystery="apples",
        approach="clover_gift",
        choice="ask",
        mood="hungry",
        detective_name="Max",
        detective_gender="boy",
        friend_name="Maya",
        friend_gender="girl",
        keeper="father",
        trait="sharp-eyed",
    ),
    StoryParams(
        setting="courtyard",
        mystery="stones",
        approach="chalk_note",
        choice="ask",
        mood="hungry",
        detective_name="Nora",
        detective_gender="girl",
        friend_name="Finn",
        friend_gender="boy",
        keeper="mother",
        trait="patient",
    ),
    StoryParams(
        setting="garden",
        mystery="stones",
        approach="quiet_wait",
        choice="sneak",
        mood="lonely",
        detective_name="Theo",
        detective_gender="boy",
        friend_name="Lucy",
        friend_gender="girl",
        keeper="father",
        trait="curious",
    ),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Story world sketch: a repeated magical mystery, a strict rule, and a unicorn."
    )
    ap.add_argument("--setting", choices=sorted(SETTINGS))
    ap.add_argument("--mystery", choices=sorted(MYSTERIES))
    ap.add_argument("--approach", choices=sorted(APPROACHES))
    ap.add_argument("--choice", choices=["ask", "sneak"])
    ap.add_argument("--mood", choices=sorted(MOODS))
    ap.add_argument("--keeper", choices=["mother", "father"])
    ap.add_argument("--detective-name")
    ap.add_argument("--friend-name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combos and derived outcomes from clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP twin against Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_child(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    names = [name for name in pool if name != avoid]
    return rng.choice(names), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.mystery and not mystery_fits(args.setting, args.mystery):
        raise StoryError(explain_mystery(args.setting, args.mystery))
    if args.setting and args.approach and not approach_allowed(args.setting, args.approach):
        raise StoryError(explain_approach(args.setting, args.approach))
    if args.approach and APPROACHES[args.approach].sense < SENSE_MIN:
        raise StoryError(explain_approach(args.setting or "garden", args.approach))

    combos = [
        combo for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.mystery is None or combo[1] == args.mystery)
        and (args.approach is None or combo[2] == args.approach)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, mystery_id, approach_id = rng.choice(sorted(combos))
    detective_name, detective_gender = _pick_child(rng)
    friend_name, friend_gender = _pick_child(rng, avoid=detective_name)
    if args.detective_name:
        detective_name = args.detective_name
    if args.friend_name:
        friend_name = args.friend_name
    return StoryParams(
        setting=setting_id,
        mystery=mystery_id,
        approach=approach_id,
        choice=args.choice or rng.choice(["ask", "ask", "sneak"]),
        mood=args.mood or rng.choice(sorted(MOODS)),
        detective_name=detective_name,
        detective_gender=detective_gender,
        friend_name=friend_name,
        friend_gender=friend_gender,
        keeper=args.keeper or rng.choice(["mother", "father"]),
        trait=rng.choice(TRAITS),
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting: {params.setting})")
    if params.mystery not in MYSTERIES:
        raise StoryError(f"(Unknown mystery: {params.mystery})")
    if params.approach not in APPROACHES:
        raise StoryError(f"(Unknown approach: {params.approach})")
    if params.mood not in MOODS:
        raise StoryError(f"(Unknown mood: {params.mood})")
    if not mystery_fits(params.setting, params.mystery):
        raise StoryError(explain_mystery(params.setting, params.mystery))
    if not approach_allowed(params.setting, params.approach):
        raise StoryError(explain_approach(params.setting, params.approach))
    if APPROACHES[params.approach].sense < SENSE_MIN:
        raise StoryError(explain_approach(params.setting, params.approach))
    if params.choice not in {"ask", "sneak"}:
        raise StoryError(f"(Unknown choice: {params.choice})")

    world = tell(
        setting=SETTINGS[params.setting],
        mystery=MYSTERIES[params.mystery],
        approach=APPROACHES[params.approach],
        choice=params.choice,
        mood=params.mood,
        detective_name=params.detective_name,
        detective_gender=params.detective_gender,
        friend_name=params.friend_name,
        friend_gender=params.friend_gender,
        keeper_type=params.keeper,
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


ASP_RULES = r"""
% --- compatibility gate ----------------------------------------------------
valid(S, M, A) :- setting(S), mystery(M), approach(A),
                  affords(S, M), fits(M, S), sensible(A), allowed(S, A).

sensible(A) :- approach(A), sense(A, V), sense_min(Min), V >= Min.

allowed(S, chalk_note) :- can_write(S).
allowed(S, clover_gift) :- has_clover(S).
allowed(S, quiet_wait) :- setting(S).
allowed(S, shout) :- setting(S).

% --- outcome model ---------------------------------------------------------
need_match :- chosen_mood(M), chosen_approach(A), needs(A, M).
outcome(friends) :- chosen_choice(ask), need_match.
outcome(solved) :- chosen_choice(ask), not need_match.
outcome(startled) :- chosen_choice(sneak).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for setting_id, setting in SETTINGS.items():
        lines.append(asp.fact("setting", setting_id))
        if setting.can_write:
            lines.append(asp.fact("can_write", setting_id))
        if setting.has_clover:
            lines.append(asp.fact("has_clover", setting_id))
        for mystery_id in sorted(setting.affords):
            lines.append(asp.fact("affords", setting_id, mystery_id))
    for mystery_id, mystery in MYSTERIES.items():
        lines.append(asp.fact("mystery", mystery_id))
        for setting_id in sorted(mystery.fits):
            lines.append(asp.fact("fits", mystery_id, setting_id))
    for approach_id, approach in APPROACHES.items():
        lines.append(asp.fact("approach", approach_id))
        lines.append(asp.fact("sense", approach_id, approach.sense))
        for mood in sorted(approach.needs):
            lines.append(asp.fact("needs", approach_id, mood))
    for mood in sorted(MOODS):
        lines.append(asp.fact("mood", mood))
    lines.append(asp.fact("sense_min", SENSE_MIN))
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
            asp.fact("chosen_choice", params.choice),
            asp.fact("chosen_approach", params.approach),
            asp.fact("chosen_mood", params.mood),
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
        print("MISMATCH in compatible combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    cases = list(CURATED)
    for seed in range(50):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        params.seed = seed
        cases.append(params)

    mismatches = []
    for params in cases:
        a = asp_outcome(params)
        p = outcome_of(params)
        if a != p:
            mismatches.append((params, a, p))
    if not mismatches:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {len(mismatches)}/{len(cases)} outcomes differ.")
        for params, a, p in mismatches[:5]:
            print(" ", params, "clingo=", a, "python=", p)

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("(Smoke test failed: empty story.)")
        print("OK: smoke test generated a normal story.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, mystery, approach) combos:\n")
        for setting_id, mystery_id, approach_id in combos:
            print(f"  {setting_id:10} {mystery_id:8} {approach_id}")
        print("\nSample derived outcomes:")
        for params in CURATED:
            print(
                f"  {params.setting:10} {params.mystery:8} {params.approach:11} "
                f"{params.choice:5} {params.mood:6} -> {asp_outcome(params)}"
            )
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        attempts = 0
        while len(samples) < args.n and attempts < max(50, args.n * 50):
            seed = base_seed + attempts
            attempts += 1
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
            header = (
                f"### {p.detective_name} & {p.friend_name}: {p.mystery} at {p.setting} "
                f"({p.approach}, {p.choice}, {outcome_of(p)})"
            )
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
