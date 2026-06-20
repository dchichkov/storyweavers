#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/guzzle_active_misunderstanding_sound_effects_detective_story.py
===========================================================================================

A tiny story world for a child-sized detective mystery: an active child hears
odd drinking sounds in a shadowy place, misunderstands them as a sneaky intruder,
and solves the case by investigating. The real culprit is a thirsty animal
guzzling water after energetic play.

This script follows the Storyworld contract:
- standalone stdlib file
- shared result containers imported eagerly from storyworlds/results.py
- typed entities with physical meters and emotional memes
- a Python reasonableness gate plus an inline ASP twin
- story, prompts, story-grounded QA, and world-knowledge QA
"""

from __future__ import annotations

import argparse
import copy
import io
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

# Make the shared result containers importable when this script is run directly
# from the repo root or from this nested model directory.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"            # "character" | "animal" | "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


# ---------------------------------------------------------------------------
# Parametrization knobs
# ---------------------------------------------------------------------------
@dataclass
class Setting:
    id: str
    place: str
    nook: str
    dark: bool
    sounds_big: bool
    allowed_pets: set[str] = field(default_factory=set)
    intro: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class PetSpec:
    id: str
    label: str
    type: str
    thirsty_after: str
    zoomed: str
    drink_verb: str
    gulp: str
    sound_word: str
    allows: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class WaterSpec:
    id: str
    label: str
    phrase: str
    splash: str
    sizes: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    gives_light: bool
    detective_line: str
    tags: set[str] = field(default_factory=set)


# ---------------------------------------------------------------------------
# World
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
        return clone


# ---------------------------------------------------------------------------
# Causal rules
# ---------------------------------------------------------------------------
@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_active_to_thirst(world: World) -> list[str]:
    pet = world.get("pet")
    if pet.meters["active"] < THRESHOLD:
        return []
    sig = ("active_to_thirst", pet.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    pet.meters["thirst"] += 1
    return []


def _r_thirst_to_guzzle(world: World) -> list[str]:
    pet = world.get("pet")
    water = world.get("water")
    if pet.meters["thirst"] < THRESHOLD:
        return []
    sig = ("thirst_to_guzzle", pet.id, water.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    pet.meters["guzzling"] += 1
    water.meters["level"] -= 1
    water.meters["splashed"] += 1
    return ["__guzzle__"]


def _r_guzzle_to_suspicion(world: World) -> list[str]:
    child = world.get("child")
    pet = world.get("pet")
    setting = world.facts["setting_cfg"]
    if pet.meters["guzzling"] < THRESHOLD or not setting.dark:
        return []
    sig = ("guzzle_to_suspicion", child.id, pet.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["suspicion"] += 1
    child.memes["fear"] += 1
    return []


CAUSAL_RULES = [
    Rule("active_to_thirst", "physical", _r_active_to_thirst),
    Rule("thirst_to_guzzle", "physical", _r_thirst_to_guzzle),
    Rule("guzzle_to_suspicion", "emotional", _r_guzzle_to_suspicion),
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
            if not line.startswith("__"):
                world.say(line)
    return produced


# ---------------------------------------------------------------------------
# Constraint helpers
# ---------------------------------------------------------------------------
def compatible(setting: Setting, pet: PetSpec, water: WaterSpec, tool: Tool) -> bool:
    if pet.id not in setting.allowed_pets:
        return False
    if water.id not in pet.allows:
        return False
    if pet.id not in water.sizes:
        return False
    if setting.dark and not tool.gives_light:
        return False
    return True


def valid_combos() -> list[tuple[str, str, str, str]]:
    out: list[tuple[str, str, str, str]] = []
    for s_id, setting in SETTINGS.items():
        for p_id, pet in PETS.items():
            for w_id, water in WATERS.items():
                for t_id, tool in TOOLS.items():
                    if compatible(setting, pet, water, tool):
                        out.append((s_id, p_id, w_id, t_id))
    return out


def explain_rejection(setting: Setting, pet: PetSpec, water: WaterSpec, tool: Tool) -> str:
    if pet.id not in setting.allowed_pets:
        return (
            f"(No story: {pet.label} does not belong in {setting.place}, so the mystery "
            f"would feel made up. Pick a pet that plausibly lives or wanders there.)"
        )
    if water.id not in pet.allows or pet.id not in water.sizes:
        return (
            f"(No story: {pet.label} would not sensibly guzzle from {water.phrase}. "
            f"Choose a water source that fits the animal.)"
        )
    if setting.dark and not tool.gives_light:
        return (
            f"(No story: {setting.place} is too dark for a fair child-detective search "
            f"with {tool.label}. Pick a tool that gives light, like a flashlight or lantern.)"
        )
    return "(No story: this combination is not reasonable.)"


# ---------------------------------------------------------------------------
# Prediction
# ---------------------------------------------------------------------------
def predict_sound(world: World) -> dict:
    sim = world.copy()
    propagate(sim, narrate=False)
    pet = sim.get("pet")
    child = sim.get("child")
    return {
        "guzzling": pet.meters["guzzling"] >= THRESHOLD,
        "suspicion": child.memes["suspicion"],
    }


# ---------------------------------------------------------------------------
# Verbs
# ---------------------------------------------------------------------------
def introduce(world: World, child: Entity, helper: Entity, setting: Setting) -> None:
    child.memes["curiosity"] += 1
    world.say(
        f"{child.id} liked to solve tiny mysteries, and on this evening {child.pronoun()} was extra "
        f"active, pattering through {setting.place} with {helper.id} close behind."
    )
    world.say(setting.intro)


def establish_pet(world: World, pet: Entity, pet_cfg: PetSpec) -> None:
    pet.meters["active"] += 1
    world.say(
        f"Earlier, {pet.label} had {pet_cfg.zoomed}, and now {pet.pronoun()} was breathing fast from all that play."
    )
    propagate(world, narrate=False)


def hear_sound(world: World, child: Entity, setting: Setting, pet_cfg: PetSpec, water: WaterSpec) -> None:
    pred = predict_sound(world)
    world.facts["predicted_guzzling"] = pred["guzzling"]
    world.facts["predicted_suspicion"] = pred["suspicion"]
    if pred["guzzling"]:
        child.memes["alert"] += 1
        world.say(
            f"Then a sound drifted from {setting.nook}: "
            f'"{pet_cfg.gulp} {pet_cfg.gulp}! {water.splash}! {pet_cfg.sound_word}!"'
        )
    else:
        world.say(f"The place had gone still for a moment, as if it were holding a secret.")


def misunderstand(world: World, child: Entity, helper: Entity, setting: Setting) -> None:
    if setting.dark:
        child.memes["suspicion"] += 1
        child.memes["fear"] += 1
        world.say(
            f'{child.id} froze. "A midnight juice thief!" {child.pronoun().capitalize()} whispered. '
            f'"Or maybe a tunnel monster hiding in the dark!"'
        )
        world.say(
            f"{helper.id} stared at {setting.nook}, wide-eyed too, because the gulping sounded much bigger than it really was."
        )
    else:
        child.memes["suspicion"] += 1
        world.say(
            f'"A clue-eating crook!" {child.id} gasped. The odd sloshing noise made an ordinary corner feel suspicious.'
        )


def prepare_search(world: World, child: Entity, helper: Entity, tool: Tool) -> None:
    child.memes["bravery"] += 1
    helper.memes["trust"] += 1
    world.say(
        f'{child.id} lifted {tool.phrase}. "{tool.detective_line}," {child.pronoun()} said.'
    )
    world.say(f"{helper.id} nodded and tiptoed beside {child.pronoun('object')} like a faithful detective partner.")


def investigate(world: World, child: Entity, helper: Entity, setting: Setting) -> None:
    world.say(
        f"They padded toward {setting.nook}, listening for every tiny clue. The house seemed to answer with creaks and little shadows."
    )


def reveal(world: World, child: Entity, helper: Entity, pet: Entity, pet_cfg: PetSpec, water: Entity, water_cfg: WaterSpec) -> None:
    child.memes["fear"] = 0.0
    child.memes["relief"] += 1
    child.memes["wonder"] += 1
    helper.memes["relief"] += 1
    world.say(
        f"But when the light reached the corner, there was no thief at all. {pet.label.capitalize()} was bent over {water_cfg.phrase}, "
        f"{pet_cfg.drink_verb} as fast as {pet.pronoun()} could."
    )
    world.say(
        f'"{pet_cfg.gulp} {pet_cfg.gulp}," went the thirsty mouth, and "{water_cfg.splash}" went the water. '
        f"The scary mystery turned into a very ordinary, very thirsty pet."
    )


def explain_case(world: World, child: Entity, helper: Entity, pet: Entity, pet_cfg: PetSpec, water_cfg: WaterSpec) -> None:
    child.memes["understanding"] += 1
    world.say(
        f'"Case solved," {child.id} said, kneeling down. "{pet.label.capitalize()} was not sneaking at all. '
        f'{pet.pronoun().capitalize()} got thirsty after being so active, so {pet.pronoun()} came to {pet_cfg.drink_verb} from {water_cfg.phrase}."'
    )
    world.say(
        f"{helper.id} laughed so softly that the whole mystery shrank to the size of a happy mistake."
    )


def resolve(world: World, child: Entity, helper: Entity, pet: Entity, water: Entity) -> None:
    child.memes["care"] += 1
    helper.memes["joy"] += 1
    pet.memes["comfort"] += 1
    world.say(
        f"They set the {water.label} straight and watched {pet.label} finish drinking. Soon the detective team was rubbing a warm head and giggling instead of guessing."
    )
    world.say(
        f"On the way back, {child.id} wrote the case in {child.pronoun('possessive')} mind: not every spooky sound means trouble; sometimes it only means someone needs a drink."
    )


# ---------------------------------------------------------------------------
# Story screenplay
# ---------------------------------------------------------------------------
def tell(
    setting: Setting,
    pet_cfg: PetSpec,
    water_cfg: WaterSpec,
    tool: Tool,
    child_name: str = "Nora",
    child_gender: str = "girl",
    helper_name: str = "Ben",
    helper_gender: str = "boy",
    parent_type: str = "mother",
) -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="detective"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender, role="helper"))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, role="parent", label="the parent"))
    pet = world.add(Entity(id="pet", kind="animal", type=pet_cfg.type, label=pet_cfg.label, role="pet"))
    water = world.add(Entity(id="water", kind="thing", type="water_source", label=water_cfg.label, role="water"))
    tool_ent = world.add(Entity(id="tool", kind="thing", type="tool", label=tool.label, role="tool"))

    world.facts.update(
        setting_cfg=setting,
        pet_cfg=pet_cfg,
        water_cfg=water_cfg,
        tool_cfg=tool,
        child=child,
        helper=helper,
        parent=parent,
        pet=pet,
        water=water,
        tool=tool_ent,
    )

    introduce(world, child, helper, setting)
    establish_pet(world, pet, pet_cfg)

    world.para()
    hear_sound(world, child, setting, pet_cfg, water_cfg)
    misunderstand(world, child, helper, setting)
    prepare_search(world, child, helper, tool)

    world.para()
    investigate(world, child, helper, setting)
    reveal(world, child, helper, pet, pet_cfg, water, water_cfg)
    explain_case(world, child, helper, pet, pet_cfg, water_cfg)

    world.para()
    resolve(world, child, helper, pet, water)

    world.facts.update(
        misunderstanding=child.memes["understanding"] >= THRESHOLD,
        solved=True,
        sound_heard=pet.meters["guzzling"] >= THRESHOLD,
    )
    return world


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "hallway": Setting(
        "hallway",
        "the hallway",
        "the dim space under the coat rack",
        dark=True,
        sounds_big=True,
        allowed_pets={"puppy", "cat"},
        intro="The hallway was full of soft shadows, and every shoe looked like a secret in waiting.",
        tags={"dark", "house"},
    ),
    "backyard": Setting(
        "backyard",
        "the backyard",
        "the corner by the flower pots",
        dark=False,
        sounds_big=False,
        allowed_pets={"puppy", "duck", "goat"},
        intro="Outside, the evening air smelled cool, and the stepping-stones looked like a trail of clues.",
        tags={"yard"},
    ),
    "barn": Setting(
        "barn",
        "the barn",
        "the shadowy stall near the hay bales",
        dark=True,
        sounds_big=True,
        allowed_pets={"goat", "pony"},
        intro="The barn held warm hay smells, dark beams, and enough rustles to make any small detective stand taller.",
        tags={"dark", "farm"},
    ),
}

PETS = {
    "puppy": PetSpec(
        "puppy",
        "the puppy",
        "puppy",
        "a hard run",
        "raced in silly circles after a bouncing ball",
        "guzzling",
        "glug",
        "slurp",
        allows={"bowl", "bucket"},
        tags={"dog", "water"},
    ),
    "cat": PetSpec(
        "cat",
        "the cat",
        "cat",
        "a burst of chasing",
        "darted after a toy mouse and skidded across the floor",
        "lapping",
        "lap",
        "sip-sip",
        allows={"bowl"},
        tags={"cat", "water"},
    ),
    "duck": PetSpec(
        "duck",
        "the duck",
        "duck",
        "a busy waddle",
        "flapped and hustled around the yard in a very important hurry",
        "guzzling",
        "glup",
        "splish",
        allows={"bowl", "bucket"},
        tags={"duck", "water"},
    ),
    "goat": PetSpec(
        "goat",
        "the goat",
        "goat",
        "a wild romp",
        "skipped, kicked, and bounced around as if the whole world were a hill",
        "guzzling",
        "glug",
        "slossh",
        allows={"bucket", "trough"},
        tags={"goat", "water"},
    ),
    "pony": PetSpec(
        "pony",
        "the pony",
        "pony",
        "a fast trot",
        "trotted in a bright, stompy loop around the pen",
        "guzzling",
        "GLOOP",
        "slosh",
        allows={"trough"},
        tags={"pony", "water"},
    ),
}

WATERS = {
    "bowl": WaterSpec(
        "bowl",
        "water bowl",
        "the water bowl",
        "plink-plink",
        sizes={"puppy", "cat", "duck"},
        tags={"bowl", "water"},
    ),
    "bucket": WaterSpec(
        "bucket",
        "bucket",
        "the bucket of water",
        "slossh",
        sizes={"puppy", "duck", "goat"},
        tags={"bucket", "water"},
    ),
    "trough": WaterSpec(
        "trough",
        "trough",
        "the trough",
        "swish-slosh",
        sizes={"goat", "pony"},
        tags={"trough", "water"},
    ),
}

TOOLS = {
    "flashlight": Tool(
        "flashlight",
        "flashlight",
        "the flashlight",
        True,
        "Detective Beam, on",
        tags={"flashlight", "light"},
    ),
    "lantern": Tool(
        "lantern",
        "camping lantern",
        "the camping lantern",
        True,
        "Lantern light, help us inspect the clues",
        tags={"lantern", "light"},
    ),
    "magnifier": Tool(
        "magnifier",
        "magnifying glass",
        "the magnifying glass",
        False,
        "Time to inspect every puddly clue",
        tags={"magnifier"},
    ),
    "notebook": Tool(
        "notebook",
        "notebook",
        "the little detective notebook",
        False,
        "Every mystery needs notes",
        tags={"notebook"},
    ),
}

GIRL_NAMES = ["Nora", "Mia", "Lucy", "Ava", "Zoe", "Lila", "Ruby", "Ella"]
BOY_NAMES = ["Ben", "Max", "Theo", "Sam", "Eli", "Leo", "Finn", "Jack"]


# ---------------------------------------------------------------------------
# Per-world params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    setting: str
    pet: str
    water: str
    tool: str
    child_name: str
    child_gender: str
    helper_name: str
    helper_gender: str
    parent: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
KNOWLEDGE = {
    "dog": [("Why might a puppy drink a lot of water after running?",
             "Running makes a puppy thirsty, so it may drink quickly to cool down and feel better. That is a normal body need after active play.")],
    "cat": [("Why does a cat sometimes make little drinking sounds?",
             "A cat laps water with its tongue, so you may hear tiny quick sounds. In a quiet room, those sounds can seem bigger than they really are.")],
    "duck": [("Do ducks need drinking water too?",
              "Yes. Ducks need clean water to drink, just like other animals do. They may also splash while they drink.")],
    "goat": [("Why can a goat sound loud in a barn?",
              "A barn echoes, so a goat's steps or drinking noises can bounce around and seem louder. Big spaces make small sounds feel mysterious.")],
    "pony": [("Why might a pony drink from a trough after trotting?",
              "Trotting is active work, so a pony can get thirsty and drink deeply afterward. A trough holds enough water for a larger animal.")],
    "light": [("Why is a light useful when you investigate a dark place?",
               "A light helps you see what is really there. Seeing clearly can turn a scary guess into the true answer.")],
    "water": [("What does guzzle mean?",
               "Guzzle means to drink a lot very quickly. You might hear gulps and splashes when someone guzzles water.")],
    "misunderstanding": [("What is a misunderstanding?",
                          "A misunderstanding happens when someone thinks something means one thing, but it really means another. It can be fixed by looking carefully and learning the truth.")],
    "detective": [("What does a detective do?",
                   "A detective looks for clues and tries to figure out what really happened. Good detectives do not stop at the first scary guess.")],
}

KNOWLEDGE_ORDER = ["water", "misunderstanding", "detective", "light", "dog", "cat", "duck", "goat", "pony"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    setting = f["setting_cfg"]
    pet = f["pet_cfg"]
    tool = f["tool_cfg"]
    return [
        'Write a gentle detective story for a 3-to-5-year-old that includes the words "guzzle" and "active".',
        f"Tell a mystery where {child.id} hears spooky drinking sounds in {setting.place}, misunderstands them, and solves the case with {tool.phrase}.",
        f"Write a child-facing detective tale with sound effects like \"{pet.gulp}! {pet.sound_word}!\" where the big suspect turns out to be {pet.label} needing water.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    pet = f["pet_cfg"]
    water = f["water_cfg"]
    setting = f["setting_cfg"]
    tool = f["tool_cfg"]
    qa: list[tuple[str, str]] = [
        ("Who is the story about?",
         f"It is about {child.id}, a little detective, and {helper.id}, the detective partner. They were trying to understand a strange sound."),
        ("What strange sound did they hear?",
         f"They heard gulping and splashing from {setting.nook}. The sound effects made the corner feel more mysterious than it really was."),
        (f"Why did {child.id} think something spooky was there?",
         f"{child.id} heard the loud guzzling in a shadowy place and did not know what was making it. Because the noise sounded bigger in the dark, {child.pronoun()} misunderstood it as a thief or monster."),
        ("What was really making the sound?",
         f"It was {pet.label} drinking from {water.phrase}. {pet.label.capitalize()} had been very active earlier, so {pet.pronoun()} was thirsty and started to guzzle."),
        (f"How did {child.id} solve the case?",
         f"{child.id} walked closer with {tool.phrase} and looked carefully instead of only guessing. Once the light or close look reached the nook, the mystery stopped being scary and became easy to explain."),
        ("How did the story end?",
         f"The case ended happily. The children understood the misunderstanding, helped with the water, and laughed because the 'intruder' was only a thirsty pet."),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"misunderstanding", "detective", "water"}
    if f["tool_cfg"].gives_light:
        tags.add("light")
    tags |= set(f["pet_cfg"].tags)
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
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if e.role:
            bits.append(f"role={e.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:8} ({e.type:11}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Curated set
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams("hallway", "puppy", "bowl", "flashlight", "Nora", "girl", "Ben", "boy", "mother"),
    StoryParams("backyard", "duck", "bucket", "magnifier", "Lucy", "girl", "Max", "boy", "father"),
    StoryParams("barn", "goat", "trough", "lantern", "Theo", "boy", "Mia", "girl", "mother"),
    StoryParams("hallway", "cat", "bowl", "flashlight", "Ava", "girl", "Leo", "boy", "father"),
]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
valid(S, P, W, T) :- setting(S), pet(P), water(W), tool(T),
                     allowed(S, P), drinks_from(P, W), fits(W, P),
                     not dark_without_light(S, T).

dark_without_light(S, T) :- dark(S), tool(T), not gives_light(T).

active(P) :- pet(P).
thirsty(P) :- active(P).
guzzling(P) :- thirsty(P), chosen_pet(P), chosen_water(W), drinks_from(P, W), fits(W, P).
suspicious :- chosen_setting(S), dark(S), chosen_pet(P), guzzling(P).
outcome(solved) :- chosen_tool(T), chosen_setting(S), valid(S, P, W, T),
                   chosen_pet(P), chosen_water(W).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for s_id, setting in SETTINGS.items():
        lines.append(asp.fact("setting", s_id))
        if setting.dark:
            lines.append(asp.fact("dark", s_id))
        for p in sorted(setting.allowed_pets):
            lines.append(asp.fact("allowed", s_id, p))
    for p_id, pet in PETS.items():
        lines.append(asp.fact("pet", p_id))
        for w in sorted(pet.allows):
            lines.append(asp.fact("drinks_from", p_id, w))
    for w_id, water in WATERS.items():
        lines.append(asp.fact("water", w_id))
        for p in sorted(water.sizes):
            lines.append(asp.fact("fits", w_id, p))
    for t_id, tool in TOOLS.items():
        lines.append(asp.fact("tool", t_id))
        if tool.gives_light:
            lines.append(asp.fact("gives_light", t_id))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join([
        asp.fact("chosen_setting", params.setting),
        asp.fact("chosen_pet", params.pet),
        asp.fact("chosen_water", params.water),
        asp.fact("chosen_tool", params.tool),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if cl - py:
            print("  only in clingo:", sorted(cl - py))
        if py - cl:
            print("  only in python:", sorted(py - cl))

    for params in CURATED[:2]:
        if asp_outcome(params) != "solved":
            rc = 1
            print("MISMATCH: ASP did not derive solved outcome for curated params.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("Generated empty story during verify smoke test.")
        buf = io.StringIO()
        old = sys.stdout
        sys.stdout = buf
        try:
            emit(sample, trace=False, qa=False)
        finally:
            sys.stdout = old
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    else:
        print("OK: smoke test generate/emit succeeded.")
    return rc


# ---------------------------------------------------------------------------
# Standard interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a child detective misunderstands a guzzling sound and solves the case."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--pet", choices=PETS)
    ap.add_argument("--water", choices=WATERS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible scenarios from clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.pet and args.water and args.tool:
        setting = SETTINGS[args.setting]
        pet = PETS[args.pet]
        water = WATERS[args.water]
        tool = TOOLS[args.tool]
        if not compatible(setting, pet, water, tool):
            raise StoryError(explain_rejection(setting, pet, water, tool))

    combos = [
        c for c in valid_combos()
        if (args.setting is None or c[0] == args.setting)
        and (args.pet is None or c[1] == args.pet)
        and (args.water is None or c[2] == args.water)
        and (args.tool is None or c[3] == args.tool)
    ]
    if not combos:
        sample_setting = SETTINGS[args.setting] if args.setting else next(iter(SETTINGS.values()))
        sample_pet = PETS[args.pet] if args.pet else next(iter(PETS.values()))
        sample_water = WATERS[args.water] if args.water else next(iter(WATERS.values()))
        sample_tool = TOOLS[args.tool] if args.tool else next(iter(TOOLS.values()))
        raise StoryError(explain_rejection(sample_setting, sample_pet, sample_water, sample_tool))

    setting, pet, water, tool = rng.choice(sorted(combos))
    child_name, child_gender = _pick_name(rng)
    helper_name, helper_gender = _pick_name(rng, avoid=child_name)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(setting, pet, water, tool, child_name, child_gender, helper_name, helper_gender, parent)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.setting],
        PETS[params.pet],
        WATERS[params.water],
        TOOLS[params.tool],
        params.child_name,
        params.child_gender,
        params.helper_name,
        params.helper_gender,
        params.parent,
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
        print(asp_program("", "#show valid/4.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, pet, water, tool) combos:\n")
        for setting, pet, water, tool in combos:
            print(f"  {setting:8} {pet:6} {water:6} {tool}")
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
            header = f"### {p.child_name}: {p.pet} in {p.setting} with {p.tool}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")
if __name__ == "__main__":
    main()
