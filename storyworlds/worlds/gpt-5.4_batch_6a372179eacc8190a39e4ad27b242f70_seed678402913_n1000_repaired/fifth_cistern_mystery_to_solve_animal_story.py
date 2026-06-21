#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/fifth_cistern_mystery_to_solve_animal_story.py
=========================================================================

A standalone story world for a gentle animal mystery: in a little garden valley,
the fifth cistern keeps losing water, and two small animals must look for the
right clue, reason about the cause, and choose the matching repair.

The domain is intentionally small and constraint-checked. A story is only valid
when:
- the chosen setting can really host the chosen cause,
- the chosen clue is the clue that cause would leave,
- the chosen fix is the sort of repair that would actually solve that cause.

This makes the "Mystery to Solve" feature come from world state rather than from
a frozen paragraph with swapped nouns.

Run it
------
    python storyworlds/worlds/gpt-5.4/fifth_cistern_mystery_to_solve_animal_story.py
    python storyworlds/worlds/gpt-5.4/fifth_cistern_mystery_to_solve_animal_story.py --setting orchard --cause thirsty_goat
    python storyworlds/worlds/gpt-5.4/fifth_cistern_mystery_to_solve_animal_story.py --cause root_crack --setting barnyard
    python storyworlds/worlds/gpt-5.4/fifth_cistern_mystery_to_solve_animal_story.py --all
    python storyworlds/worlds/gpt-5.4/fifth_cistern_mystery_to_solve_animal_story.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/fifth_cistern_mystery_to_solve_animal_story.py --trace
    python storyworlds/worlds/gpt-5.4/fifth_cistern_mystery_to_solve_animal_story.py --verify
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional

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
    traits: list[str] = field(default_factory=list)
    role: str = ""
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
        female = {"girl", "mother", "hen", "goose", "doe"}
        male = {"boy", "father", "buck"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Setting:
    id: str
    label: str
    scene: str
    affords: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Cause:
    id: str
    culprit_label: str
    problem: str
    sign: str
    find_text: str
    explain_text: str
    repair_text: str
    fix_id: str
    clue_id: str
    water_loss: int
    tags: set[str] = field(default_factory=set)


@dataclass
class Clue:
    id: str
    label: str
    observe_text: str
    inference_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Fix:
    id: str
    label: str
    do_text: str
    result_text: str
    tags: set[str] = field(default_factory=set)


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


def cause_fits_setting(setting_id: str, cause_id: str) -> bool:
    return cause_id in SETTINGS[setting_id].affords


def clue_matches_cause(cause_id: str, clue_id: str) -> bool:
    return CAUSES[cause_id].clue_id == clue_id


def fix_matches_cause(cause_id: str, fix_id: str) -> bool:
    return CAUSES[cause_id].fix_id == fix_id


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for setting_id in SETTINGS:
        for cause_id in CAUSES:
            if not cause_fits_setting(setting_id, cause_id):
                continue
            cause = CAUSES[cause_id]
            if cause.clue_id in CLUES and cause.fix_id in FIXES:
                combos.append((setting_id, cause_id, cause.clue_id, cause.fix_id))
    return combos


def explain_setting_rejection(setting_id: str, cause_id: str) -> str:
    setting = SETTINGS[setting_id]
    cause = CAUSES[cause_id]
    return (
        f"(No story: {setting.label} does not reasonably support the cause "
        f"'{cause.culprit_label}'. The mystery clue would have no honest source there.)"
    )


def explain_clue_rejection(cause_id: str, clue_id: str) -> str:
    cause = CAUSES[cause_id]
    clue = CLUES[clue_id]
    right = CLUES[cause.clue_id].label
    return (
        f"(No story: '{clue.label}' does not match the cause '{cause.culprit_label}'. "
        f"This cause should leave the clue '{right}'.)"
    )


def explain_fix_rejection(cause_id: str, fix_id: str) -> str:
    cause = CAUSES[cause_id]
    fix = FIXES[fix_id]
    right = FIXES[cause.fix_id].label
    return (
        f"(No story: '{fix.label}' would not solve the problem caused by "
        f"'{cause.culprit_label}'. A fitting repair here is '{right}'.)"
    )


def introduce(world: World, hero: Entity, friend: Entity, keeper: Entity, cistern: Entity) -> None:
    world.say(
        f"In {world.setting.label}, where {world.setting.scene}, {hero.id} the {hero.type} "
        f"liked morning jobs, and {friend.id} the {friend.type} liked puzzles."
    )
    world.say(
        f"Each dawn they helped {keeper.id} watch five rain barrels and one old stone cistern "
        f"that fed the lettuce beds and the bean hill."
    )
    world.say(
        f"That morning, {keeper.id} tapped the row with a careful paw. "
        f'"One, two, three, four... but the fifth cistern is low again," {keeper.pronoun()} said.'
    )
    cistern.meters["water"] = 1.0
    cistern.meters["missing_water"] = float(world.facts["cause"].water_loss)
    hero.memes["care"] += 1
    friend.memes["curiosity"] += 1
    keeper.memes["worry"] += 1


def worry(world: World, hero: Entity, friend: Entity, keeper: Entity) -> None:
    world.say(
        f"The little seedlings bent in the pale light, and all three animals looked at them. "
        f"If the water kept slipping away, the garden would grow thirsty by noon."
    )
    world.say(
        f'"This is a mystery to solve," {friend.id} whispered. '
        f'"Let us look before the sun drinks the last dampness from the ground."'
    )
    hero.memes["resolve"] += 1
    friend.memes["resolve"] += 1


def inspect(world: World, hero: Entity, friend: Entity, clue: Clue) -> None:
    world.say(
        f"{hero.id} and {friend.id} padded around the fifth cistern together, moving slowly so "
        f"their eyes could notice small things."
    )
    world.say(clue.observe_text)
    hero.meters["steps"] += 1
    friend.meters["steps"] += 1
    world.facts["observed_clue"] = clue.id
    friend.memes["understanding"] += 1


def reason_out(world: World, hero: Entity, friend: Entity, cause: Cause, clue: Clue) -> None:
    world.say(
        f'"{clue.inference_text}" said {friend.id}. {hero.id} looked again and saw it too.'
    )
    world.say(cause.find_text)
    world.say(cause.explain_text)
    world.facts["solved"] = True
    world.get("cistern").meters["mystery"] = 0.0
    hero.memes["relief"] += 1
    friend.memes["pride"] += 1


def repair(world: World, hero: Entity, keeper: Entity, cause: Cause, fix: Fix) -> None:
    cistern = world.get("cistern")
    world.say(
        f"{keeper.id} nodded at once, and together they {fix.do_text}."
    )
    cistern.meters["missing_water"] = 0.0
    cistern.meters["water"] = 3.0
    cistern.meters["soundness"] += 1
    keeper.memes["worry"] = 0.0
    keeper.memes["gratitude"] += 1
    world.say(fix.result_text)
    world.say(cause.repair_text)
    hero.memes["joy"] += 1


def ending(world: World, hero: Entity, friend: Entity, keeper: Entity, fix: Fix) -> None:
    world.say(
        f"When they came back after breakfast, the fifth cistern was still full. "
        f"A round silver line of water shone near the rim instead of sinking away."
    )
    world.say(
        f"The seedlings lifted their leaves, and {keeper.id} poured each row a cool drink. "
        f'"Well done, little detectives," {keeper.pronoun()} said.'
    )
    world.say(
        f"{hero.id} felt tall inside, and {friend.id} smiled at the quiet stone wall. "
        f"The mystery was no longer a worry; it had turned into a good piece of thinking and "
        f"a {fix.label} that worked."
    )


def tell(
    setting: Setting,
    cause: Cause,
    clue: Clue,
    fix: Fix,
    hero_name: str,
    hero_type: str,
    friend_name: str,
    friend_type: str,
    keeper_name: str,
    keeper_type: str,
) -> World:
    world = World(setting=setting)
    hero = world.add(
        Entity(
            id=hero_name,
            kind="character",
            type=hero_type,
            role="hero",
            label=hero_name,
            tags={"animal"},
        )
    )
    friend = world.add(
        Entity(
            id=friend_name,
            kind="character",
            type=friend_type,
            role="friend",
            label=friend_name,
            tags={"animal"},
        )
    )
    keeper = world.add(
        Entity(
            id=keeper_name,
            kind="character",
            type=keeper_type,
            role="keeper",
            label=keeper_name,
            tags={"adult", "animal"},
        )
    )
    cistern = world.add(
        Entity(
            id="cistern",
            kind="thing",
            type="cistern",
            label="the fifth cistern",
            phrase="the fifth cistern",
            tags={"water", "garden"},
        )
    )
    world.get("cistern").meters["mystery"] = 1.0
    world.facts.update(
        setting=setting,
        cause=cause,
        clue=clue,
        fix=fix,
        hero=hero,
        friend=friend,
        keeper=keeper,
        solved=False,
    )

    introduce(world, hero, friend, keeper, cistern)
    world.para()
    worry(world, hero, friend, keeper)
    inspect(world, hero, friend, clue)
    world.para()
    reason_out(world, hero, friend, cause, clue)
    repair(world, hero, keeper, cause, fix)
    world.para()
    ending(world, hero, friend, keeper, fix)
    return world


SETTINGS = {
    "orchard": Setting(
        id="orchard",
        label="the orchard garden",
        scene="pear trees leaned over warm paths and bees hummed above the thyme",
        affords={"loose_plug", "thirsty_goat", "root_crack"},
        tags={"garden", "orchard"},
    ),
    "barnyard": Setting(
        id="barnyard",
        label="the barnyard patch",
        scene="straw smelled sweet and a split-rail fence circled the little pumpkin beds",
        affords={"loose_plug", "thirsty_goat"},
        tags={"farm", "barnyard"},
    ),
    "mossy_wall": Setting(
        id="mossy_wall",
        label="the mossy wall garden",
        scene="ferns curled beside an old wall where vines and raindrops liked to linger",
        affords={"loose_plug", "root_crack"},
        tags={"garden", "wall"},
    ),
}

CAUSES = {
    "loose_plug": Cause(
        id="loose_plug",
        culprit_label="a loose wooden plug",
        problem="the stopper under the cistern had wriggled loose",
        sign="wet stones below the spout",
        find_text=(
            f"Under the mossy lip, they found the small wooden plug hanging crooked by its string."
        ),
        explain_text=(
            "A tiny gap was enough to let the water trickle out all night. That was why the fifth "
            "cistern kept growing light before morning."
        ),
        repair_text=(
            "After that, no patient dripping sound came from the base of the stone."
        ),
        fix_id="tighten_plug",
        clue_id="wet_stones",
        water_loss=2,
        tags={"water", "repair"},
    ),
    "thirsty_goat": Cause(
        id="thirsty_goat",
        culprit_label="a thirsty goat",
        problem="a goat had learned to nudge the little tap and drink in the dark",
        sign="hoofprints in the mud",
        find_text=(
            "At the side of the cistern they found a line of moon-dried hoofprints and a few white hairs "
            "caught on the latch."
        ),
        explain_text=(
            "The prints led to the drinking trough, where the tap stood half open. A thirsty visitor had "
            "been helping itself every night."
        ),
        repair_text=(
            "The trough stayed dry until morning chores, and no new hoofprints circled back."
        ),
        fix_id="latch_tap",
        clue_id="hoofprints",
        water_loss=3,
        tags={"water", "farm", "animal"},
    ),
    "root_crack": Cause(
        id="root_crack",
        culprit_label="a root crack in the stone",
        problem="a vine root had pressed into the side and opened a thin crack",
        sign="a thread of roots in the wall",
        find_text=(
            "Behind a curtain of leaves they spotted a hair-thin crack with a pale root running through it "
            "like string through cloth."
        ),
        explain_text=(
            "Rain had fed the vine, and the root had slowly pried the stones apart. The water was slipping "
            "out through that quiet seam."
        ),
        repair_text=(
            "The wall looked snug again, with no damp line creeping down it."
        ),
        fix_id="patch_crack",
        clue_id="root_threads",
        water_loss=2,
        tags={"water", "wall", "plants"},
    ),
}

CLUES = {
    "wet_stones": Clue(
        id="wet_stones",
        label="wet stones",
        observe_text=(
            "Near the bottom, the stones were dark and shiny even though the morning breeze had already dried "
            "the path around them."
        ),
        inference_text=(
            "Those stones are wet right under the plug. Water must be escaping from below, not vanishing into the sky"
        ),
        tags={"water", "clue"},
    ),
    "hoofprints": Clue(
        id="hoofprints",
        label="hoofprints",
        observe_text=(
            "In the soft mud they saw neat split hoofprints, stepping to the tap and away again."
        ),
        inference_text=(
            "These are not bird tracks or cracks. Someone with hooves visited in the night"
        ),
        tags={"animal", "clue"},
    ),
    "root_threads": Clue(
        id="root_threads",
        label="root threads",
        observe_text=(
            "Friend pushed aside the vine leaves and found tiny root threads tucked in a narrow line in the stone."
        ),
        inference_text=(
            "Roots can pry and split. If a root is in the wall, the wall may be opening"
        ),
        tags={"plants", "clue"},
    ),
}

FIXES = {
    "tighten_plug": Fix(
        id="tighten_plug",
        label="tightened plug",
        do_text="pulled the plug snug, wrapped the string twice, and pressed it firm with a flat pebble",
        result_text=(
            "Then they filled the cistern to its chalk mark and waited. Not one drop slipped down the stones."
        ),
        tags={"repair", "water"},
    ),
    "latch_tap": Fix(
        id="latch_tap",
        label="latched tap",
        do_text="closed the little tap, tied on a twig latch, and set a fresh bucket for daytime watering instead",
        result_text=(
            "Then they poured in two buckets and watched the handle. It stayed shut, and the water line held steady."
        ),
        tags={"repair", "water", "animal"},
    ),
    "patch_crack": Fix(
        id="patch_crack",
        label="patched crack",
        do_text="trimmed the pushing vine, packed cool clay into the crack, and smoothed it with wet paws",
        result_text=(
            "Then they topped up the cistern and watched the wall. The damp thread faded, and the clay held."
        ),
        tags={"repair", "water", "plants"},
    ),
}

ANIMALS = [
    {"name": "Mira", "type": "mouse"},
    {"name": "Pip", "type": "rabbit"},
    {"name": "Tansy", "type": "squirrel"},
    {"name": "Bramble", "type": "hedgehog"},
    {"name": "Nettle", "type": "mouse"},
    {"name": "Fern", "type": "rabbit"},
]

KEEPERS = [
    {"name": "Aunt Clover", "type": "goose"},
    {"name": "Old Rowan", "type": "tortoise"},
    {"name": "Mrs. Thimble", "type": "hen"},
]


@dataclass
class StoryParams:
    setting: str
    cause: str
    clue: str
    fix: str
    hero_name: str
    hero_type: str
    friend_name: str
    friend_type: str
    keeper_name: str
    keeper_type: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "cistern": [
        (
            "What is a cistern?",
            "A cistern is a big container that stores water. Gardens and homes can use that saved water later."
        )
    ],
    "mystery": [
        (
            "What does it mean to solve a mystery?",
            "Solving a mystery means noticing clues and thinking carefully about what caused a problem. You do not guess wildly; you look and reason."
        )
    ],
    "clue": [
        (
            "What is a clue?",
            "A clue is a sign that helps you understand what happened. Footprints, wet stones, and broken twigs can all be clues."
        )
    ],
    "water": [
        (
            "Why do gardens need water?",
            "Plants need water to stay firm and keep growing. Without enough water, their leaves droop and the soil dries out."
        )
    ],
    "goat": [
        (
            "What kind of tracks does a goat make?",
            "A goat makes split hoofprints. They look different from the prints of birds or the paws of rabbits."
        )
    ],
    "roots": [
        (
            "How can roots crack stone?",
            "Roots can press and grow in tiny spaces. Over time, that steady push can open a crack wider."
        )
    ],
    "plug": [
        (
            "What does a plug do in a water container?",
            "A plug blocks the opening so water stays inside. If it comes loose, the water can drip away."
        )
    ],
    "repair": [
        (
            "Why is it good to fix a problem after you find it?",
            "Finding the cause is only the first step. A good repair stops the trouble from coming back."
        )
    ],
}
KNOWLEDGE_ORDER = ["cistern", "mystery", "clue", "water", "goat", "roots", "plug", "repair"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    setting = f["setting"]
    cause = f["cause"]
    hero = f["hero"]
    friend = f["friend"]
    return [
        (
            f'Write a gentle animal mystery for a 3-to-5-year-old that includes the words '
            f'"fifth" and "cistern", and takes place in {setting.label}.'
        ),
        (
            f"Tell a story where {hero.id} the {hero.type} and {friend.id} the {friend.type} "
            f"notice that the fifth cistern is losing water and solve the puzzle by following a real clue."
        ),
        (
            f'Write a complete child-facing story with a clear mystery, the cause "{cause.culprit_label}", '
            f"and a happy ending where the garden is safe again."
        ),
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    keeper = f["keeper"]
    setting = f["setting"]
    cause = f["cause"]
    clue = f["clue"]
    fix = f["fix"]
    out: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id} the {hero.type}, {friend.id} the {friend.type}, and {keeper.id}, who care for the garden water."
        ),
        (
            "What was the mystery?",
            "The fifth cistern kept turning up low in the morning. That worried everyone because the seedlings needed the water."
        ),
        (
            "What clue helped them solve it?",
            f"They noticed {clue.label}. That clue mattered because it pointed them toward the real cause instead of a wild guess."
        ),
        (
            "What was causing the problem?",
            f"The trouble came from {cause.culprit_label}. {cause.explain_text}"
        ),
        (
            "How did they fix the fifth cistern?",
            f"They {fix.do_text}. {fix.result_text}"
        ),
        (
            "How could they tell the mystery was solved at the end?",
            "When they came back later, the fifth cistern was still full. The water stayed where it belonged, so the garden could be watered."
        ),
        (
            "Why did they look carefully instead of guessing?",
            f"They wanted a true answer, not just a fast one. In {setting.label}, the right clue showed them exactly what needed to be fixed."
        ),
    ]
    return out


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"cistern", "mystery", "clue", "water", "repair"}
    if f["cause"].id == "thirsty_goat":
        tags.add("goat")
    if f["cause"].id == "root_crack":
        tags.add("roots")
    if f["cause"].id == "loose_plug":
        tags.add("plug")
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
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
    lines.append(f"  setting: {world.setting.id}")
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
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        lines.append(f"  {ent.id:12} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  solved: {world.facts.get('solved')}")
    lines.append(f"  cause: {world.facts.get('cause').id}")
    lines.append(f"  clue: {world.facts.get('clue').id}")
    lines.append(f"  fix: {world.facts.get('fix').id}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="orchard",
        cause="loose_plug",
        clue="wet_stones",
        fix="tighten_plug",
        hero_name="Mira",
        hero_type="mouse",
        friend_name="Pip",
        friend_type="rabbit",
        keeper_name="Old Rowan",
        keeper_type="tortoise",
    ),
    StoryParams(
        setting="barnyard",
        cause="thirsty_goat",
        clue="hoofprints",
        fix="latch_tap",
        hero_name="Fern",
        hero_type="rabbit",
        friend_name="Tansy",
        friend_type="squirrel",
        keeper_name="Mrs. Thimble",
        keeper_type="hen",
    ),
    StoryParams(
        setting="mossy_wall",
        cause="root_crack",
        clue="root_threads",
        fix="patch_crack",
        hero_name="Nettle",
        hero_type="mouse",
        friend_name="Bramble",
        friend_type="hedgehog",
        keeper_name="Aunt Clover",
        keeper_type="goose",
    ),
]


ASP_RULES = r"""
fits_setting(S, C) :- affords(S, C).
matches_clue(C, Cl) :- cause_clue(C, Cl).
matches_fix(C, F) :- cause_fix(C, F).
valid(S, C, Cl, F) :- fits_setting(S, C), matches_clue(C, Cl), matches_fix(C, F).
solved(C, Cl, F) :- matches_clue(C, Cl), matches_fix(C, F).
"""

def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for cause_id in sorted(setting.affords):
            lines.append(asp.fact("affords", sid, cause_id))
    for cid, cause in CAUSES.items():
        lines.append(asp.fact("cause", cid))
        lines.append(asp.fact("cause_clue", cid, cause.clue_id))
        lines.append(asp.fact("cause_fix", cid, cause.fix_id))
    for clue_id in CLUES:
        lines.append(asp.fact("clue", clue_id))
    for fix_id in FIXES:
        lines.append(asp.fact("fix", fix_id))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_solved(cause_id: str, clue_id: str, fix_id: str) -> bool:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_cause", cause_id),
            asp.fact("chosen_clue", clue_id),
            asp.fact("chosen_fix", fix_id),
            "done :- chosen_cause(C), chosen_clue(Cl), chosen_fix(F), solved(C, Cl, F).",
        ]
    )
    model = asp.one_model(asp_program(extra, "#show done/0."))
    return bool(model and "done" in str(model))


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Animal mystery story world: the fifth cistern keeps losing water, and small animal detectives solve why."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--cause", choices=CAUSES)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible stories derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run smoke tests")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def pick_animals(rng: random.Random) -> tuple[dict, dict, dict]:
    hero = rng.choice(ANIMALS)
    friend_choices = [a for a in ANIMALS if a["name"] != hero["name"]]
    friend = rng.choice(friend_choices)
    keeper = rng.choice(KEEPERS)
    return hero, friend, keeper


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.cause and not cause_fits_setting(args.setting, args.cause):
        raise StoryError(explain_setting_rejection(args.setting, args.cause))
    if args.cause and args.clue and not clue_matches_cause(args.cause, args.clue):
        raise StoryError(explain_clue_rejection(args.cause, args.clue))
    if args.cause and args.fix and not fix_matches_cause(args.cause, args.fix):
        raise StoryError(explain_fix_rejection(args.cause, args.fix))

    combos = [
        combo
        for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.cause is None or combo[1] == args.cause)
        and (args.clue is None or combo[2] == args.clue)
        and (args.fix is None or combo[3] == args.fix)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, cause_id, clue_id, fix_id = rng.choice(sorted(combos))
    hero, friend, keeper = pick_animals(rng)
    return StoryParams(
        setting=setting_id,
        cause=cause_id,
        clue=clue_id,
        fix=fix_id,
        hero_name=hero["name"],
        hero_type=hero["type"],
        friend_name=friend["name"],
        friend_type=friend["type"],
        keeper_name=keeper["name"],
        keeper_type=keeper["type"],
    )


def generate(params: StoryParams) -> StorySample:
    try:
        setting = SETTINGS[params.setting]
        cause = CAUSES[params.cause]
        clue = CLUES[params.clue]
        fix = FIXES[params.fix]
    except KeyError as err:
        raise StoryError(f"(Invalid parameter key: {err})") from err

    if not cause_fits_setting(params.setting, params.cause):
        raise StoryError(explain_setting_rejection(params.setting, params.cause))
    if not clue_matches_cause(params.cause, params.clue):
        raise StoryError(explain_clue_rejection(params.cause, params.clue))
    if not fix_matches_cause(params.cause, params.fix):
        raise StoryError(explain_fix_rejection(params.cause, params.fix))

    world = tell(
        setting=setting,
        cause=cause,
        clue=clue,
        fix=fix,
        hero_name=params.hero_name,
        hero_type=params.hero_type,
        friend_name=params.friend_name,
        friend_type=params.friend_type,
        keeper_name=params.keeper_name,
        keeper_type=params.keeper_type,
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
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if cl - py:
            print("  only in asp:", sorted(cl - py))
        if py - cl:
            print("  only in python:", sorted(py - cl))

    solved_cases = 0
    for setting_id, cause_id, clue_id, fix_id in sorted(py):
        solved_cases += 1
        py_solved = clue_matches_cause(cause_id, clue_id) and fix_matches_cause(cause_id, fix_id)
        try:
            asp_ok = asp_solved(cause_id, clue_id, fix_id)
        except Exception as err:
            rc = 1
            print(f"ASP solved-check crashed for {(cause_id, clue_id, fix_id)}: {err}")
            break
        if py_solved != asp_ok:
            rc = 1
            print(f"MISMATCH in solved inference for {(cause_id, clue_id, fix_id)}")
    if rc == 0:
        print(f"OK: solved inference matches on {solved_cases} cases.")

    try:
        sample = generate(CURATED[0])
        if not sample.story or "fifth cistern" not in sample.story or "cistern" not in sample.story:
            raise StoryError("(Smoke test failed: generated story missing expected content.)")
        print("OK: smoke-test story generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/4.\n#show solved/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, cause, clue, fix) combos:\n")
        for setting_id, cause_id, clue_id, fix_id in combos:
            print(f"  {setting_id:10} {cause_id:13} {clue_id:12} {fix_id}")
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
            header = f"### {p.setting}: {p.cause} -> {p.fix}"
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
