#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/broad_chard_land_mystery_to_solve_heartwarming.py
=============================================================================

A standalone story world for a heartwarming "mystery to solve" in a little
garden. A child and a caring helper look after a small patch of land where broad
beans and chard are growing. One morning something has troubled the plants.
Instead of blaming in a hurry, they follow clues, solve the mystery gently, and
end with a kinder, safer garden.

The world model prefers only *reasonable* mysteries: a place must plausibly host
the culprit, and the chosen fix must be the kind of fix that really suits that
culprit. The simulation then turns those choices into a complete story with a
beginning, a clue-finding middle, and an ending image that proves what changed.

Run it
------
    python storyworlds/worlds/gpt-5.4/broad_chard_land_mystery_to_solve_heartwarming.py
    python storyworlds/worlds/gpt-5.4/broad_chard_land_mystery_to_solve_heartwarming.py --culprit rabbit
    python storyworlds/worlds/gpt-5.4/broad_chard_land_mystery_to_solve_heartwarming.py --solution pinwheel
    python storyworlds/worlds/gpt-5.4/broad_chard_land_mystery_to_solve_heartwarming.py --all
    python storyworlds/worlds/gpt-5.4/broad_chard_land_mystery_to_solve_heartwarming.py -n 5 --seed 7
    python storyworlds/worlds/gpt-5.4/broad_chard_land_mystery_to_solve_heartwarming.py --qa --json
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

# Make the shared result containers importable when this script is run directly
# from a nested world directory.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"            # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
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
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "grandmother"}
        male = {"boy", "man", "father", "grandfather"}
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
        }.get(self.type, self.label or self.type)


@dataclass
class Setting:
    id: str
    place: str
    patch_phrase: str
    morning_detail: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Culprit:
    id: str
    label: str
    signs: list[str] = field(default_factory=list)
    clue_summary: str = ""
    trace_text: str = ""
    motive_text: str = ""
    gentle_truth: str = ""
    ending_image: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Solution:
    id: str
    label: str
    suits: set[str] = field(default_factory=set)
    action_text: str = ""
    kindness_text: str = ""
    result_text: str = ""
    qa_text: str = ""
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
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
        clone = World(self.setting)
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


def _r_worry(world: World) -> list[str]:
    mystery = world.entities.get("mystery")
    child = world.entities.get("child")
    if mystery is None or child is None:
        return []
    if mystery.meters["damage"] < THRESHOLD:
        return []
    sig = ("worry",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["worry"] += 1
    return ["__worry__"]


def _r_solve(world: World) -> list[str]:
    mystery = world.entities.get("mystery")
    child = world.entities.get("child")
    helper = world.entities.get("helper")
    if mystery is None or child is None or helper is None:
        return []
    needed = float(world.facts.get("needed_clues", 0))
    found = mystery.meters["clues_found"]
    if found < needed or mystery.meters["solved"] >= THRESHOLD:
        return []
    sig = ("solved",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    mystery.meters["solved"] += 1
    child.memes["certainty"] += 1
    helper.memes["certainty"] += 1
    return ["__solved__"]


def _r_relief(world: World) -> list[str]:
    mystery = world.entities.get("mystery")
    garden = world.entities.get("garden")
    child = world.entities.get("child")
    helper = world.entities.get("helper")
    if not all([mystery, garden, child, helper]):
        return []
    if mystery.meters["solved"] < THRESHOLD or garden.meters["protected"] < THRESHOLD:
        return []
    sig = ("relief",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["relief"] += 1
    helper.memes["relief"] += 1
    child.memes["joy"] += 1
    helper.memes["joy"] += 1
    return ["__relief__"]


CAUSAL_RULES = [
    Rule(name="worry", tag="emotion", apply=_r_worry),
    Rule(name="solve", tag="mystery", apply=_r_solve),
    Rule(name="relief", tag="emotion", apply=_r_relief),
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
            if not line.startswith("__"):
                world.say(line)
    return produced


SETTINGS = {
    "library_garden": Setting(
        id="library_garden",
        place="behind the library",
        patch_phrase="a broad patch of land behind the library fence",
        morning_detail="The bricks still held a little night coolness, and the path smelled like damp soil.",
        affords={"rabbit", "crow", "snail"},
    ),
    "school_garden": Setting(
        id="school_garden",
        place="beside the school",
        patch_phrase="a small learning garden on a broad patch of land beside the school",
        morning_detail="A bell had not rung yet, and dew shone on every leaf.",
        affords={"crow", "snail", "puppy"},
    ),
    "backyard_plot": Setting(
        id="backyard_plot",
        place="at the back of the house",
        patch_phrase="a broad little strip of land at the back of the house",
        morning_detail="The fence cast long sleepy shadows over the beds.",
        affords={"rabbit", "snail", "puppy"},
    ),
}

CULPRITS = {
    "rabbit": Culprit(
        id="rabbit",
        label="rabbit",
        signs=[
            "neat moon-shaped bites on the chard",
            "two soft hopping prints in the soil",
            "a loose place under the fence",
        ],
        clue_summary="neat bites, hopping prints, and a gap under the fence",
        trace_text="The prints led straight to a loosened place under the fence, where a few white hairs clung to the wire.",
        motive_text="A hungry rabbit had found the greens first.",
        gentle_truth="It was not being naughty. It was just small and hungry, and the garden smelled wonderful.",
        ending_image="outside the fence a rabbit sat in the clover, leaving the chard alone",
        tags={"rabbit", "fence", "garden"},
    ),
    "crow": Culprit(
        id="crow",
        label="crow",
        signs=[
            "broad bean seeds scratched out of one row",
            "a shiny plant label dragged sideways",
            "a black feather near the bed",
        ],
        clue_summary="scratched soil, a moved shiny label, and a black feather",
        trace_text="A black feather lay by the broad beans, and the shiny label had been tugged as if bright things had caught an eye from above.",
        motive_text="A curious crow had hopped down to investigate the gleam and peck at the fresh seeds.",
        gentle_truth="It was not trying to ruin anything. Crows love shiny things and are always searching for breakfast.",
        ending_image="a crow watched from the apple tree while the pinwheel flickered softly below",
        tags={"crow", "pinwheel", "garden"},
    ),
    "snail": Culprit(
        id="snail",
        label="snail",
        signs=[
            "tiny round holes in the chard",
            "silver trails on the dark soil",
            "a snail tucked under the watering can",
        ],
        clue_summary="little holes, silver trails, and a hidden snail",
        trace_text="When they lifted the watering can, a snail sat underneath as still as a button, with a silver trail curling behind it.",
        motive_text="A snail had spent the cool night nibbling the tender chard.",
        gentle_truth="It was not mean. It was only following the wet, delicious leaves the way snails do.",
        ending_image="the chard stood in the sun while the snail rested in the shady compost corner",
        tags={"snail", "garden", "compost"},
    ),
    "puppy": Culprit(
        id="puppy",
        label="puppy",
        signs=[
            "broad seedlings tipped sideways",
            "muddy paw prints across the path",
            "an open gate swinging a little",
        ],
        clue_summary="paw prints, bent broad seedlings, and an open gate",
        trace_text="The muddy paw prints went in happy loops, and the gate latch hung open as if a bouncing body had nudged through.",
        motive_text="A playful puppy had bounded in and treated the bed like a tiny race track.",
        gentle_truth="It was not trying to hurt the garden. It only needed a clear place to run.",
        ending_image="the broad beans lifted again while a puppy trotted happily along its own little path",
        tags={"puppy", "gate", "garden"},
    ),
}

SOLUTIONS = {
    "fence_clover": Solution(
        id="fence_clover",
        label="a low fence and a clover corner",
        suits={"rabbit"},
        action_text="Together they tucked the loose wire back in place, added a low bit of mesh, and planted a clover corner outside the bed.",
        kindness_text="That way the rabbit could still find a breakfast of its own without chewing the chard.",
        result_text="The garden bed was protected, and the visitor had somewhere kinder to nibble.",
        qa_text="They fixed the fence and planted clover outside the bed so the rabbit had food somewhere else.",
        tags={"fence", "rabbit", "garden"},
    ),
    "pinwheel_ribbon": Solution(
        id="pinwheel_ribbon",
        label="a pinwheel and soft ribbon lines",
        suits={"crow"},
        action_text="They pressed the broad seeds back into the soil, tied soft ribbons above the row, and set a bright pinwheel where the shiny label had been.",
        kindness_text="The moving color gave the crow a reason to keep its clever feet farther away.",
        result_text="The broad row was planted again, and the bird learned to watch from the tree instead of hopping in the bed.",
        qa_text="They replanted the broad beans and used ribbons and a pinwheel to keep the crow out of the bed.",
        tags={"pinwheel", "crow", "garden"},
    ),
    "compost_board": Solution(
        id="compost_board",
        label="a shady board by the compost",
        suits={"snail"},
        action_text="They gently moved the snail to the compost corner and laid a damp board there to make a cooler hiding place.",
        kindness_text="Then they watered in the morning instead of late at night, so the chard would not invite so many midnight visitors.",
        result_text="The snail had a shady home, and the chard had a better chance to grow whole leaves.",
        qa_text="They moved the snail to the compost corner and made a shady place there so it would stay away from the chard.",
        tags={"snail", "compost", "garden"},
    ),
    "latch_path": Solution(
        id="latch_path",
        label="a stronger latch and a puppy path",
        suits={"puppy"},
        action_text="They clicked the gate latch tight and laid flat stepping stones along the edge of the plot.",
        kindness_text="The new path gave the puppy a place to trot without racing through the broad beans.",
        result_text="The bed stayed safe, and the puppy had a clear route that felt like an invitation instead of a scolding.",
        qa_text="They fixed the gate latch and made a little path so the puppy would not run through the plants.",
        tags={"puppy", "gate", "garden"},
    ),
}

GIRL_NAMES = ["Lily", "Maya", "Nora", "Ava", "Zoe", "Ella", "Mina", "Ruby"]
BOY_NAMES = ["Ben", "Leo", "Sam", "Owen", "Eli", "Theo", "Max", "Noah"]
TRAITS = ["patient", "curious", "gentle", "careful", "hopeful"]
HELPER_TYPES = ["grandmother", "grandfather", "mother", "father", "neighbor"]

KNOWLEDGE = {
    "broad": [(
        "What are broad beans?",
        "Broad beans are beans that grow in green pods on sturdy plants. People plant them in gardens because the beans can be cooked and eaten."
    )],
    "chard": [(
        "What is chard?",
        "Chard is a leafy vegetable with colorful stems and broad leaves. People grow it in gardens and can cook the leaves for meals."
    )],
    "land": [(
        "What does a patch of land mean?",
        "A patch of land is a small piece of ground. It can be used for grass, flowers, or a little garden."
    )],
    "garden": [(
        "Why do gardens need care?",
        "Gardens need water, sunlight, and gentle care so plants can grow well. Small problems can be fixed when people notice them early."
    )],
    "rabbit": [(
        "Why might a rabbit nibble garden plants?",
        "Rabbits eat tender leaves because they are soft and tasty. A hungry rabbit may visit a garden if it can get in easily."
    )],
    "crow": [(
        "Why do crows pick up shiny things?",
        "Crows are curious birds and often notice objects that glitter or move. They investigate with their eyes and beaks."
    )],
    "snail": [(
        "Why do snails come out in cool, damp places?",
        "Snails like damp air because it helps keep their bodies from drying out. That is why they often move around at night or after watering."
    )],
    "puppy": [(
        "Why can a puppy be hard on a garden without meaning to?",
        "Puppies run, bounce, and explore with their paws. They can squash small plants just by playing too close."
    )],
    "fence": [(
        "What does a garden fence do?",
        "A garden fence makes a clear boundary around plants. It helps protect growing leaves and stems from being stepped on or eaten."
    )],
    "pinwheel": [(
        "Why can a pinwheel help in a garden?",
        "A pinwheel spins and flashes color in the breeze. That movement can make birds choose to stay a little farther away."
    )],
    "compost": [(
        "What is compost?",
        "Compost is a pile of old leaves and food scraps that break down into rich soil. Many little garden creatures like the cool, shady places around it."
    )],
    "gate": [(
        "Why does a latch matter on a gate?",
        "A latch keeps a gate closed when it should stay shut. That helps people and animals use the right path."
    )],
}
KNOWLEDGE_ORDER = [
    "broad",
    "chard",
    "land",
    "garden",
    "rabbit",
    "crow",
    "snail",
    "puppy",
    "fence",
    "pinwheel",
    "compost",
    "gate",
]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place_id, setting in SETTINGS.items():
        for culprit_id in sorted(setting.affords):
            for solution_id, solution in SOLUTIONS.items():
                if culprit_id in solution.suits:
                    combos.append((place_id, culprit_id, solution_id))
    return combos


def solution_for(culprit_id: str) -> list[str]:
    return sorted(sid for sid, sol in SOLUTIONS.items() if culprit_id in sol.suits)


def place_allows(place_id: str, culprit_id: str) -> bool:
    return culprit_id in SETTINGS[place_id].affords


def explain_place(place: Setting, culprit: Culprit) -> str:
    return (
        f"(No story: {culprit.label} is not a good fit for the garden {place.place}. "
        f"Pick a culprit that plausibly belongs there.)"
    )


def explain_solution(culprit: Culprit, solution: Solution) -> str:
    good = ", ".join(solution_for(culprit.id))
    return (
        f"(No story: {solution.label} does not suit a {culprit.label}. "
        f"Try one of: {good}.)"
    )


@dataclass
class StoryParams:
    place: str
    culprit: str
    solution: str
    child_name: str
    child_gender: str
    helper_name: str
    helper_type: str
    trait: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        place="library_garden",
        culprit="rabbit",
        solution="fence_clover",
        child_name="Nora",
        child_gender="girl",
        helper_name="Jun",
        helper_type="grandfather",
        trait="curious",
        seed=11,
    ),
    StoryParams(
        place="school_garden",
        culprit="crow",
        solution="pinwheel_ribbon",
        child_name="Ben",
        child_gender="boy",
        helper_name="Mara",
        helper_type="neighbor",
        trait="careful",
        seed=12,
    ),
    StoryParams(
        place="backyard_plot",
        culprit="snail",
        solution="compost_board",
        child_name="Lily",
        child_gender="girl",
        helper_name="Ana",
        helper_type="grandmother",
        trait="gentle",
        seed=13,
    ),
    StoryParams(
        place="school_garden",
        culprit="puppy",
        solution="latch_path",
        child_name="Leo",
        child_gender="boy",
        helper_name="Dad",
        helper_type="father",
        trait="patient",
        seed=14,
    ),
]


def introduce(world: World, child: Entity, helper: Entity) -> None:
    child.memes["love"] += 1
    helper.memes["love"] += 1
    broad = world.get("broad")
    chard = world.get("chard")
    world.say(
        f"{child.id} and {helper.id}, {child.id}'s {helper.label_word}, cared for "
        f"{world.setting.patch_phrase}. In one bed the {broad.label} stood sturdy and green, "
        f"and in the next the {chard.label} spread its broad leaves like little flags."
    )
    world.say(world.setting.morning_detail)


def discover_problem(world: World, child: Entity) -> None:
    mystery = world.get("mystery")
    broad = world.get("broad")
    chard = world.get("chard")
    broad.meters["disturbed"] += 1
    chard.meters["disturbed"] += 1
    mystery.meters["damage"] += 1
    propagate(world, narrate=False)
    world.say(
        f"But that morning something was wrong. The row of {broad.label} looked bothered, "
        f"and the {chard.label} did not look as neat as it had the day before."
    )
    if child.memes["worry"] >= THRESHOLD:
        world.say(
            f'{child.id} stopped short. "Oh no," {child.pronoun()} whispered. '
            f'"Who visited our garden in the night?"'
        )


def invite_mystery(world: World, child: Entity, helper: Entity) -> None:
    child.memes["curiosity"] += 1
    helper.memes["calm"] += 1
    world.say(
        f'{helper.id} knelt beside the bed instead of hurrying to blame anyone. '
        f'"Then this is a mystery to solve," {helper.pronoun()} said. '
        f'"Let us look at the clues one by one."'
    )


def inspect_clues(world: World, child: Entity, helper: Entity, culprit: Culprit) -> None:
    mystery = world.get("mystery")
    child.memes["focus"] += 1
    helper.memes["focus"] += 1
    for clue in culprit.signs:
        mystery.meters["clues_found"] += 1
        world.say(f"They found {clue}.")
    propagate(world, narrate=False)
    world.say(culprit.trace_text)
    if world.get("mystery").meters["solved"] >= THRESHOLD:
        world.say(
            f'{child.id} looked up with wide eyes. "{culprit.label.capitalize()}!" '
            f'{child.pronoun().capitalize()} had the answer at last.'
        )


def reveal(world: World, child: Entity, helper: Entity, culprit: Culprit) -> None:
    child.memes["wonder"] += 1
    helper.memes["kindness"] += 1
    world.say(
        f"It had been {culprit.motive_text} {culprit.gentle_truth}"
    )
    world.say(
        f'{helper.id} smiled and brushed a crumb of soil from {child.id}\'s sleeve. '
        f'"We can protect the garden and still be kind," {helper.pronoun()} said.'
    )


def fix_problem(world: World, child: Entity, helper: Entity, solution: Solution) -> None:
    garden = world.get("garden")
    broad = world.get("broad")
    chard = world.get("chard")
    broad.meters["safe"] += 1
    chard.meters["safe"] += 1
    garden.meters["protected"] += 1
    propagate(world, narrate=False)
    world.say(solution.action_text)
    world.say(solution.kindness_text)
    if child.memes["relief"] >= THRESHOLD:
        world.say(
            f"{solution.result_text} {child.id}'s worried shoulders softened, and "
            f"{helper.id} squeezed {child.pronoun('possessive')} hand."
        )


def ending(world: World, child: Entity, helper: Entity, culprit: Culprit) -> None:
    child.memes["joy"] += 1
    helper.memes["joy"] += 1
    world.say(
        "The next morning they came back early. Dew sat on the leaves, and the whole garden seemed to be holding a small, bright breath."
    )
    world.say(
        f"The broad beans stood straighter, the chard looked calmer, and {culprit.ending_image}. "
        f"{child.id} laughed, and {helper.id} laughed with {child.pronoun('object')}."
    )
    world.say(
        f'From then on, whenever something puzzling happened on their patch of land, '
        f'{child.id} remembered that good clues and a kind heart could grow side by side.'
    )


def tell(
    setting: Setting,
    culprit_cfg: Culprit,
    solution_cfg: Solution,
    *,
    child_name: str,
    child_gender: str,
    helper_name: str,
    helper_type: str,
    trait: str,
) -> World:
    world = World(setting)
    child = world.add(Entity(
        id="child",
        kind="character",
        type=child_gender,
        label=child_name,
        phrase=child_name,
        role="child",
        traits=[trait],
    ))
    helper = world.add(Entity(
        id="helper",
        kind="character",
        type=helper_type,
        label=helper_name,
        phrase=helper_name,
        role="helper",
        traits=["steady"],
    ))
    garden = world.add(Entity(
        id="garden",
        type="garden",
        label="garden",
        phrase="the garden",
        tags={"garden", "land"},
    ))
    broad = world.add(Entity(
        id="broad",
        type="plant",
        label="broad beans",
        phrase="the broad beans",
        tags={"broad", "garden"},
    ))
    chard = world.add(Entity(
        id="chard",
        type="plant",
        label="chard",
        phrase="the chard",
        tags={"chard", "garden"},
    ))
    mystery = world.add(Entity(
        id="mystery",
        type="mystery",
        label="mystery",
        phrase="a mystery",
    ))

    world.facts["needed_clues"] = len(culprit_cfg.signs)

    introduce(world, child, helper)
    world.para()
    discover_problem(world, child)
    invite_mystery(world, child, helper)
    world.para()
    inspect_clues(world, child, helper, culprit_cfg)
    reveal(world, child, helper, culprit_cfg)
    world.para()
    fix_problem(world, child, helper, solution_cfg)
    ending(world, child, helper, culprit_cfg)

    world.facts.update(
        child=child,
        helper=helper,
        garden=garden,
        broad=broad,
        chard=chard,
        mystery=mystery,
        setting=setting,
        culprit=culprit_cfg,
        solution=solution_cfg,
        solved=mystery.meters["solved"] >= THRESHOLD,
        protected=garden.meters["protected"] >= THRESHOLD,
        clues_found=int(mystery.meters["clues_found"]),
    )
    return world


def generation_prompts(world: World) -> list[str]:
    child = world.facts["child"]
    helper = world.facts["helper"]
    culprit = world.facts["culprit"]
    solution = world.facts["solution"]
    return [
        'Write a heartwarming mystery-to-solve story for a 3-to-5-year-old that includes the words "broad", "chard", and "land".',
        f"Tell a gentle garden mystery where {child.label} and {helper.label}, {child.label}'s {helper.label_word}, find clues in a patch of land and discover that a {culprit.label} visited the broad beans and chard.",
        f"Write a cozy story where a child follows clues instead of blaming in a hurry, solves the mystery kindly, and ends by using {solution.label} to protect the garden.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    child = world.facts["child"]
    helper = world.facts["helper"]
    culprit = world.facts["culprit"]
    solution = world.facts["solution"]
    setting = world.facts["setting"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.label} and {helper.label}, {child.label}'s {helper.label_word}, caring for a little garden. They look after broad beans and chard on a patch of land together."
        ),
        (
            "What was the mystery?",
            "Something had troubled the garden during the night. The broad beans and chard looked disturbed, so the child and helper had to find out what happened."
        ),
        (
            "How did they solve the mystery?",
            f"They looked carefully for clues instead of guessing. They found {culprit.clue_summary}, and those clues pointed to a {culprit.label}."
        ),
        (
            f"Why was the {culprit.label} in the garden?",
            f"{culprit.motive_text} {culprit.gentle_truth} The mystery feels kinder once they understand the reason."
        ),
        (
            "How did they fix the problem?",
            f"{solution.qa_text} The fix protected the plants and still made room for the animal's needs."
        ),
        (
            "How did the story end?",
            f"The next morning the garden looked calmer and safer in {setting.place}. The broad beans and chard were better protected, and everyone ended the mystery with relief instead of anger."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"broad", "chard", "land", "garden"}
    tags |= set(world.facts["culprit"].tags)
    tags |= set(world.facts["solution"].tags)
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
        if ent.traits:
            bits.append(f"traits={ent.traits}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        lines.append(f"  {ent.id:8} ({ent.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
allowed_place(P, C) :- place(P), culprit(C), affords(P, C).
fits(S, C) :- solution(S), culprit(C), suits(S, C).
valid(P, C, S) :- allowed_place(P, C), fits(S, C).
"""

def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id, setting in SETTINGS.items():
        lines.append(asp.fact("place", place_id))
        for culprit_id in sorted(setting.affords):
            lines.append(asp.fact("affords", place_id, culprit_id))
    for culprit_id in CULPRITS:
        lines.append(asp.fact("culprit", culprit_id))
    for solution_id, solution in SOLUTIONS.items():
        lines.append(asp.fact("solution", solution_id))
        for culprit_id in sorted(solution.suits):
            lines.append(asp.fact("suits", solution_id, culprit_id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


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

    smoke_cases = list(CURATED[:2])
    try:
        generated = generate(smoke_cases[0])
        if not generated.story.strip():
            raise StoryError("empty story in smoke test")
        with contextlib.redirect_stdout(io.StringIO()):
            emit(generated, trace=True, qa=True, header="### smoke")
        random_case = resolve_params(build_parser().parse_args([]), random.Random(123))
        random_case.seed = 123
        generated2 = generate(random_case)
        if not generated2.story.strip():
            raise StoryError("empty story in random smoke test")
        with contextlib.redirect_stdout(io.StringIO()):
            emit(generated2, trace=False, qa=False)
        print("OK: smoke generation and emit succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Heartwarming garden mystery storyworld. Unspecified choices are randomized."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--culprit", choices=CULPRITS)
    ap.add_argument("--solution", choices=SOLUTIONS)
    ap.add_argument("--child")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-type", choices=HELPER_TYPES)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.culprit and not place_allows(args.place, args.culprit):
        raise StoryError(explain_place(SETTINGS[args.place], CULPRITS[args.culprit]))
    if args.culprit and args.solution and args.culprit not in SOLUTIONS[args.solution].suits:
        raise StoryError(explain_solution(CULPRITS[args.culprit], SOLUTIONS[args.solution]))

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.culprit is None or combo[1] == args.culprit)
        and (args.solution is None or combo[2] == args.solution)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, culprit_id, solution_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    child_name = args.child or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper_type = args.helper_type or rng.choice(HELPER_TYPES)

    if args.helper:
        helper_name = args.helper
    else:
        if helper_type in {"grandmother", "mother"}:
            helper_name = rng.choice(["Mara", "Ana", "Ruth", "June", "Ivy"])
        elif helper_type in {"grandfather", "father"}:
            helper_name = rng.choice(["Jun", "Omar", "Luis", "Dan", "Arlo"])
        else:
            helper_name = rng.choice(["Mara", "Jun", "Pat", "Rae", "Sky"])

    trait = rng.choice(TRAITS)
    return StoryParams(
        place=place_id,
        culprit=culprit_id,
        solution=solution_id,
        child_name=child_name,
        child_gender=gender,
        helper_name=helper_name,
        helper_type=helper_type,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in SETTINGS:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.culprit not in CULPRITS:
        raise StoryError(f"(Unknown culprit: {params.culprit})")
    if params.solution not in SOLUTIONS:
        raise StoryError(f"(Unknown solution: {params.solution})")
    if not place_allows(params.place, params.culprit):
        raise StoryError(explain_place(SETTINGS[params.place], CULPRITS[params.culprit]))
    if params.culprit not in SOLUTIONS[params.solution].suits:
        raise StoryError(explain_solution(CULPRITS[params.culprit], SOLUTIONS[params.solution]))

    world = tell(
        SETTINGS[params.place],
        CULPRITS[params.culprit],
        SOLUTIONS[params.solution],
        child_name=params.child_name,
        child_gender=params.child_gender,
        helper_name=params.helper_name,
        helper_type=params.helper_type,
        trait=params.trait,
    )

    child = world.get("child")
    helper = world.get("helper")
    display_world = copy.deepcopy(world)
    display_world.get("child").id = child.label
    display_world.get("helper").id = helper.label
    story_text = display_world.render()

    return StorySample(
        params=params,
        story=story_text,
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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, culprit, solution) combos:\n")
        for place_id, culprit_id, solution_id in combos:
            print(f"  {place_id:15} {culprit_id:8} {solution_id}")
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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.child_name}: {p.culprit} at {p.place} ({p.solution})"
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
