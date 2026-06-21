#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/grocery_maid_basil_dialogue_fairy_tale.py
====================================================================

A small fairy-tale storyworld about a maid sent to the village grocery for basil.

The world model tracks whether the basil stays fresh on the road home. A sensible
wrapping or container can protect it from rain, wind, or heat; a weak choice is
refused, and even a good choice can fail if the journey is delayed too long.

Run it
------
    python storyworlds/worlds/gpt-5.4/grocery_maid_basil_dialogue_fairy_tale.py
    python storyworlds/worlds/gpt-5.4/grocery_maid_basil_dialogue_fairy_tale.py --dish moon_soup --obstacle wind
    python storyworlds/worlds/gpt-5.4/grocery_maid_basil_dialogue_fairy_tale.py --solution apron_pocket
    python storyworlds/worlds/gpt-5.4/grocery_maid_basil_dialogue_fairy_tale.py --all
    python storyworlds/worlds/gpt-5.4/grocery_maid_basil_dialogue_fairy_tale.py --verify
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
    traits: list[str] = field(default_factory=list)
    attrs: dict[str, object] = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "maid", "cook_woman", "queen", "grandmother"}
        male = {"boy", "man", "cook_man", "king", "grandfather"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        mapping = {
            "cook_woman": "cook",
            "cook_man": "cook",
            "grandmother": "grandmother",
            "grandfather": "grandfather",
        }
        return mapping.get(self.type, self.type)


@dataclass
class Setting:
    id: str
    home: str
    ruler: str
    kitchen: str
    road: str
    ending_image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Dish:
    id: str
    label: str
    pot: str
    basil_use: str
    ending_line: str
    uses_basil: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Obstacle:
    id: str
    label: str
    threat: str
    sign: str
    danger: str
    severity: int
    tags: set[str] = field(default_factory=set)


@dataclass
class Solution:
    id: str
    label: str
    phrase: str
    guards: set[str]
    sense: int
    power: int
    success_text: str
    fail_text: str
    qa_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    setting: str
    dish: str
    obstacle: str
    solution: str
    maid_name: str
    maid_gender: str
    cook_type: str
    trait: str
    delay: int = 0
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

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


def _r_basil_ruined(world: World) -> list[str]:
    out: list[str] = []
    basil = world.get("basil")
    for threat in ("wet", "scatter", "wilt"):
        if basil.meters[threat] < THRESHOLD:
            continue
        sig = ("ruined", threat)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        basil.meters["ruined"] += 1
        world.get("maid").memes["fear"] += 1
        world.get("kitchen").meters["delay"] += 1
        out.append("__ruined__")
    return out


def _r_safe_arrival(world: World) -> list[str]:
    basil = world.get("basil")
    if basil.meters["delivered"] < THRESHOLD:
        return []
    sig = ("delivered",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    if basil.meters["ruined"] < THRESHOLD:
        world.get("kitchen").memes["hope"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="basil_ruined", tag="physical", apply=_r_basil_ruined),
    Rule(name="safe_arrival", tag="social", apply=_r_safe_arrival),
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


SETTINGS = {
    "castle": Setting(
        id="castle",
        home="the hilltop castle",
        ruler="the queen",
        kitchen="a copper-roofed kitchen where pots sang on their hooks",
        road="the cobbled road beneath the castle gate",
        ending_image="lamplight shining on the castle windows",
        tags={"castle", "kitchen"},
    ),
    "cottage": Setting(
        id="cottage",
        home="the baker's old cottage",
        ruler="Grandmother Rowan",
        kitchen="a snug kitchen where a blue kettle hummed beside the fire",
        road="the lane that curved past the mill and the willow tree",
        ending_image="a warm cottage window glowing like honey",
        tags={"cottage", "kitchen"},
    ),
    "tower": Setting(
        id="tower",
        home="the watchful tower above the orchard",
        ruler="the old steward",
        kitchen="a round kitchen with herbs hanging like green tassels from the beams",
        road="the winding path that curled around the orchard wall",
        ending_image="the tower lantern blinking over the orchard",
        tags={"tower", "kitchen"},
    ),
}

DISHES = {
    "moon_soup": Dish(
        id="moon_soup",
        label="moon soup",
        pot="the silver soup pot",
        basil_use="The cook said the basil would make the whole pot smell green and kind.",
        ending_line="When the steam rose, the room smelled as if summer had learned to sing.",
        uses_basil=True,
        tags={"soup", "basil_food"},
    ),
    "garden_pie": Dish(
        id="garden_pie",
        label="garden pie",
        pot="the pie dish with little painted pears around the rim",
        basil_use="The cook said chopped basil would wake the pie the way a bell wakes a sleepy town.",
        ending_line="When the pie was cut, green flecks winked through the filling like tiny leaves of luck.",
        uses_basil=True,
        tags={"pie", "basil_food"},
    ),
    "sun_bread": Dish(
        id="sun_bread",
        label="sun bread",
        pot="the wide bread bowl",
        basil_use="The cook said torn basil would tuck a bright garden smell into every warm slice.",
        ending_line="When the loaf broke open, the table filled with warm crumbs and a sweet green scent.",
        uses_basil=True,
        tags={"bread", "basil_food"},
    ),
    "honey_cake": Dish(
        id="honey_cake",
        label="honey cake",
        pot="the small gold cake tin",
        basil_use="No one in this kitchen would put basil in a honey cake.",
        ending_line="The cake might be lovely, but it is not a basil errand.",
        uses_basil=False,
        tags={"cake"},
    ),
}

OBSTACLES = {
    "rain": Obstacle(
        id="rain",
        label="rain",
        threat="wet",
        sign="By the time she reached the market square, rain pearls were already tapping on the stones.",
        danger="If the leaves were soaked on the road home, they would slump and bruise.",
        severity=2,
        tags={"rain", "wet"},
    ),
    "wind": Obstacle(
        id="wind",
        label="wind",
        threat="scatter",
        sign="A teasing wind skipped through the market and tugged at ribbons, hats, and loose paper.",
        danger="If the bunch came loose, the little basil leaves would whirl away like green birds.",
        severity=2,
        tags={"wind"},
    ),
    "hot_sun": Obstacle(
        id="hot_sun",
        label="hot sun",
        threat="wilt",
        sign="The noon sun poured down so warmly that even the shutters seemed sleepy.",
        danger="If the herbs grew too hot, the basil would droop before it ever reached the pot.",
        severity=2,
        tags={"sun", "heat"},
    ),
    "storm": Obstacle(
        id="storm",
        label="storm",
        threat="wet",
        sign="Dark clouds gathered fast, and the market folk began tying down awnings and closing shutters.",
        danger="A hard storm could drench and bruise delicate basil in only a few breaths.",
        severity=3,
        tags={"storm", "rain", "wet"},
    ),
}

SOLUTIONS = {
    "lidded_basket": Solution(
        id="lidded_basket",
        label="lidded basket",
        phrase="a little lidded basket lined with clean cloth",
        guards={"wet", "scatter"},
        sense=3,
        power=3,
        success_text="tucked the basil into the lidded basket and snapped the lid shut, so not even the road's mischief could trouble it",
        fail_text="hid the basil in the basket, but the journey stretched on until damp crept in and the leaves sagged",
        qa_text="She carried the basil in a lidded basket that kept the leaves together and sheltered.",
        tags={"basket"},
    ),
    "damp_cloth": Solution(
        id="damp_cloth",
        label="damp cloth",
        phrase="a cool damp cloth tied around the stems",
        guards={"wilt"},
        sense=3,
        power=3,
        success_text="wrapped the stems in a cool damp cloth, and the basil rode home as fresh as a streamside plant",
        fail_text="wrapped the basil in the damp cloth, but the long hot road stole the coolness away and the leaves drooped",
        qa_text="She wrapped the stems in a damp cloth so the basil would stay cool and fresh.",
        tags={"cloth"},
    ),
    "clay_pot": Solution(
        id="clay_pot",
        label="clay pot",
        phrase="a small clay pot with a fitted lid",
        guards={"wet", "scatter", "wilt"},
        sense=3,
        power=4,
        success_text="nestled the basil in the clay pot and carried it close, where it stayed shaded, snug, and sweet",
        fail_text="set the basil in the clay pot, but the road took so very long that even there the leaves lost their lively spring",
        qa_text="She set the basil in a clay pot with a lid, which kept it shaded and safe on the road.",
        tags={"pot"},
    ),
    "apron_pocket": Solution(
        id="apron_pocket",
        label="apron pocket",
        phrase="her apron pocket",
        guards={"scatter"},
        sense=1,
        power=1,
        success_text="stuffed the basil into her apron pocket and hurried along",
        fail_text="stuffed the basil into her apron pocket, where it bent and bruised at once",
        qa_text="She used her apron pocket, which was a poor way to carry delicate basil.",
        tags={"apron"},
    ),
}

MAID_NAMES_GIRL = ["Mira", "Elin", "Tessa", "Nella", "Iris", "Lina", "Bela", "Wren"]
MAID_NAMES_BOY = ["Rowan", "Tobin", "Milo", "Finn", "Arlen", "Nico", "Jory", "Pip"]
TRAITS = ["careful", "brisk", "gentle", "thoughtful", "hopeful", "steady"]


def uses_basil(dish: Dish) -> bool:
    return dish.uses_basil


def sensible_solutions() -> list[Solution]:
    return [s for s in SOLUTIONS.values() if s.sense >= SENSE_MIN]


def obstacle_severity(obstacle: Obstacle, delay: int) -> int:
    return obstacle.severity + delay


def can_guard(solution: Solution, obstacle: Obstacle) -> bool:
    return obstacle.threat in solution.guards


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for setting_id in SETTINGS:
        for dish_id, dish in DISHES.items():
            if not uses_basil(dish):
                continue
            for obstacle_id in OBSTACLES:
                combos.append((setting_id, dish_id, obstacle_id))
    return combos


def outcome_of(params: StoryParams) -> str:
    obstacle = OBSTACLES[params.obstacle]
    solution = SOLUTIONS[params.solution]
    if not can_guard(solution, obstacle):
        return "ruined"
    return "delivered" if solution.power >= obstacle_severity(obstacle, params.delay) else "ruined"


def explain_dish(dish: Dish) -> str:
    return (
        f"(No story: {dish.label} does not truly need basil, so the maid has no honest basil errand. "
        f"Choose a dish such as moon_soup, garden_pie, or sun_bread.)"
    )


def explain_solution(solution_id: str, obstacle_id: str = "") -> str:
    solution = SOLUTIONS[solution_id]
    if solution.sense < SENSE_MIN:
        better = ", ".join(sorted(s.id for s in sensible_solutions()))
        return (
            f"(Refusing solution '{solution_id}': it is too flimsy for this world "
            f"(sense={solution.sense} < {SENSE_MIN}). Try one of: {better}.)"
        )
    if obstacle_id:
        obstacle = OBSTACLES[obstacle_id]
        return (
            f"(No story: {solution.label} does not protect basil from {obstacle.label}. "
            f"The maid needs a method that guards against {obstacle.threat}.)"
        )
    return "(No story: that solution does not fit the road's danger.)"


def predict_risk(world: World, obstacle: Obstacle, solution: Solution, delay: int) -> dict[str, object]:
    sim = world.copy()
    _journey(sim, obstacle=obstacle, solution=solution, delay=delay, narrate=False)
    basil = sim.get("basil")
    return {
        "ruined": basil.meters["ruined"] >= THRESHOLD,
        "threat": obstacle.threat,
        "delay": delay,
    }


def _journey(world: World, obstacle: Obstacle, solution: Solution, delay: int, narrate: bool = True) -> None:
    basil = world.get("basil")
    maid = world.get("maid")
    maid.memes["resolve"] += 1
    if can_guard(solution, obstacle) and solution.power >= obstacle_severity(obstacle, delay):
        basil.meters["protected"] += 1
        if narrate:
            world.say(
                f"On {world.setting.road}, {obstacle.sign} Yet {maid.id} {solution.success_text}."
            )
    else:
        basil.meters[obstacle.threat] += 1
        if narrate:
            world.say(
                f"On {world.setting.road}, {obstacle.sign} {maid.id} {solution.fail_text}."
            )
    propagate(world, narrate=narrate)


def introduce(world: World, maid: Entity, cook: Entity, setting: Setting) -> None:
    trait = maid.traits[0] if maid.traits else "faithful"
    world.say(
        f"In {setting.home} there lived a young {trait} maid named {maid.id}. "
        f"She worked in {setting.kitchen}, and everyone knew that her feet were quick and her heart was kind."
    )
    world.say(
        f"The cook, who ruled the spoons as sternly as any king ruled a crown, trusted {maid.id} with the day's small important errands."
    )


def call_for_basil(world: World, maid: Entity, cook: Entity, dish: Dish, setting: Setting) -> None:
    maid.memes["duty"] += 1
    world.say(
        f"That morning the cook lifted the lid of {dish.pot} and sighed. "
        f'"{maid.id}," said the cook, "our {dish.label} lacks its green finishing touch. '
        f'Run to the village grocery and bring me fresh basil before {setting.ruler} sits down to table."'
    )
    world.say(dish.basil_use)
    world.facts["grocery_word_used"] = True


def grocery_scene(world: World, maid: Entity, obstacle: Obstacle, solution: Solution) -> None:
    grocer = world.get("grocer")
    basil = world.get("basil")
    maid.memes["hope"] += 1
    world.say(
        f"So {maid.id} went to the grocery at the market square, where strings of onions swung from the beams and the grocer kept herbs in shining pans of water."
    )
    world.say(
        f'The grocer lifted a bright bunch of basil and said, "Here is basil fit for a feast. But mind the {obstacle.label} on the road home."'
    )
    world.say(obstacle.danger)
    pred = predict_risk(world, obstacle=obstacle, solution=solution, delay=world.facts["delay"])
    if pred["ruined"]:
        world.say(
            f'{maid.id} answered, "Then I must carry it wisely, or all my running will be for nothing."'
        )
    else:
        world.say(
            f'{maid.id} answered, "Then I will guard it carefully, and not a leaf shall be lost."'
        )
    basil.attrs["source"] = "grocery"


def choose_solution(world: World, maid: Entity, solution: Solution) -> None:
    world.say(
        f'The grocer handed {maid.pronoun("object")} {solution.phrase}. "{solution.label.capitalize()} will serve better than haste," the grocer said.'
    )
    world.say(f'"Thank you," said {maid.id}. "I will carry the basil as if it were a little green crown."')
    world.facts["chosen_solution_phrase"] = solution.phrase


def return_scene_success(world: World, maid: Entity, cook: Entity, dish: Dish, setting: Setting, solution: Solution) -> None:
    basil = world.get("basil")
    basil.meters["delivered"] += 1
    propagate(world, narrate=False)
    maid.memes["relief"] += 1
    cook.memes["pride"] += 1
    world.say(
        f'Back in the kitchen, {maid.id} opened the {solution.label} and set the basil on the table. '
        f'"Fresh as dawn!" cried the cook.'
    )
    world.say(
        f'The cook tore the leaves into {dish.pot}, and {dish.ending_line}'
    )
    world.say(
        f'{setting.ending_image.capitalize()} seemed brighter than before, and {maid.id} felt that even a small errand could end like a blessing.'
    )


def return_scene_failure(world: World, maid: Entity, cook: Entity, dish: Dish, setting: Setting) -> None:
    basil = world.get("basil")
    maid.memes["sorrow"] += 1
    cook.memes["care"] += 1
    world.say(
        f"When {maid.id} came back to the kitchen and opened her bundle, the basil lay tired and spoiled."
    )
    world.say(
        f'"Oh dear," whispered {maid.id}. "I hurried, but I did not guard it well enough."'
    )
    world.say(
        f'The cook did not scold. Instead the cook said, "Truth told quickly is better than a hidden mistake. Come, little maid. We still have one small chance."'
    )
    basil.attrs["used_in_dish"] = False
    world.para()
    world.say(
        f'Together they tucked the limp basil aside for compost and planted a few spare basil seeds in a window box. '
        f'The meal was plain that day, but a week later new leaves rose bright and sweet.'
    )
    world.say(
        f'{maid.id} touched the tiny plants and said, "Next time I will be as careful with the road as with the cooking."'
    )
    world.say(
        f'The cook smiled and answered, "That is how wisdom grows." Soon {setting.ending_image} watched over a windowsill lined with brave new green.'
    )


def tell(
    setting: Setting,
    dish: Dish,
    obstacle: Obstacle,
    solution: Solution,
    maid_name: str = "Mira",
    maid_gender: str = "girl",
    cook_type: str = "cook_woman",
    trait: str = "careful",
    delay: int = 0,
) -> World:
    world = World(setting)
    maid_type = "maid" if maid_gender == "girl" else "boy"
    maid = world.add(
        Entity(
            id=maid_name,
            kind="character",
            type=maid_type,
            role="maid",
            traits=[trait],
            label="the maid",
            tags={"maid"},
        )
    )
    cook = world.add(
        Entity(
            id="Cook",
            kind="character",
            type=cook_type,
            role="cook",
            label="the cook",
            tags={"cook"},
        )
    )
    grocer = world.add(
        Entity(
            id="Grocer",
            kind="character",
            type="woman",
            role="grocer",
            label="the grocer",
            tags={"grocery"},
        )
    )
    basil = world.add(
        Entity(
            id="basil",
            type="herb",
            label="basil",
            phrase="a bright bunch of basil",
            tags={"basil"},
        )
    )
    world.add(Entity(id="kitchen", type="room", label="the kitchen", tags={"kitchen"}))
    world.facts["delay"] = delay

    introduce(world, maid, cook, setting)
    call_for_basil(world, maid, cook, dish, setting)

    world.para()
    grocery_scene(world, maid, obstacle, solution)
    choose_solution(world, maid, solution)

    world.para()
    _journey(world, obstacle=obstacle, solution=solution, delay=delay, narrate=True)

    world.para()
    outcome = outcome_of(
        StoryParams(
            setting=setting.id,
            dish=dish.id,
            obstacle=obstacle.id,
            solution=solution.id,
            maid_name=maid_name,
            maid_gender=maid_gender,
            cook_type=cook_type,
            trait=trait,
            delay=delay,
            seed=None,
        )
    )
    if outcome == "delivered":
        return_scene_success(world, maid, cook, dish, setting, solution)
    else:
        return_scene_failure(world, maid, cook, dish, setting)

    world.facts.update(
        maid=maid,
        cook=cook,
        grocer=grocer,
        basil=basil,
        setting_cfg=setting,
        dish_cfg=dish,
        obstacle_cfg=obstacle,
        solution_cfg=solution,
        outcome=outcome,
        ruined=basil.meters["ruined"] >= THRESHOLD,
        delivered=outcome == "delivered",
    )
    return world


KNOWLEDGE = {
    "grocery": [
        (
            "What is a grocery?",
            "A grocery is a shop where people buy food like fruit, bread, herbs, and other things for meals."
        )
    ],
    "basil": [
        (
            "What is basil?",
            "Basil is a green herb with soft leaves and a sweet smell. People use it to make food taste fresh and lively."
        )
    ],
    "rain": [
        (
            "Why can rain spoil fresh herbs?",
            "Fresh herbs are delicate. If heavy rain soaks them, the leaves can bruise and turn limp."
        )
    ],
    "wind": [
        (
            "Why is wind a problem for loose leaves?",
            "Wind can pick up light leaves and scatter them. That is why small things often need a closed container."
        )
    ],
    "heat": [
        (
            "Why do plants wilt in strong heat?",
            "Strong heat makes leaves lose water, so they droop and feel tired. Keeping them cool helps them stay fresh."
        )
    ],
    "basket": [
        (
            "Why is a lidded basket useful?",
            "A lid helps keep things together and gives them some shelter. That makes a basket better for delicate food than an open hand or pocket."
        )
    ],
    "pot": [
        (
            "Why does a clay pot help carry herbs?",
            "A clay pot can shade and protect tender leaves. With a lid, it keeps wind and splashes away too."
        )
    ],
    "cloth": [
        (
            "Why would a damp cloth help basil?",
            "A damp cloth can keep the stems cool for a while. That helps basil stay fresh on a hot walk."
        )
    ],
    "maid": [
        (
            "What work might a maid do in a fairy tale?",
            "A maid might sweep, carry messages, fetch ingredients, or help in the kitchen. In many fairy tales, careful small tasks matter a great deal."
        )
    ],
}
KNOWLEDGE_ORDER = ["maid", "grocery", "basil", "rain", "wind", "heat", "basket", "pot", "cloth"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    maid = f["maid"]
    dish = f["dish_cfg"]
    obstacle = f["obstacle_cfg"]
    outcome = f["outcome"]
    if outcome == "delivered":
        return [
            f'Write a fairy tale for a 3-to-5-year-old that includes the words "grocery", "maid", and "basil", with clear dialogue and a happy ending.',
            f"Tell a gentle fairy tale where a maid named {maid.id} must fetch basil from the grocery for {dish.label}, faces {obstacle.label} on the road, and succeeds by carrying the herb wisely.",
            f'Write a story in fairy-tale style where careful dialogue helps a maid treat a simple kitchen errand like an important quest.'
        ]
    return [
        f'Write a fairy tale for a 3-to-5-year-old that includes the words "grocery", "maid", and "basil", with dialogue and a gentle lesson.',
        f"Tell a fairy tale where a maid named {maid.id} fetches basil from the grocery for {dish.label}, but {obstacle.label} spoils the errand and the grown-up helps turn the mistake into wisdom.",
        f'Write a child-friendly tale in which a maid tells the truth after a basil errand goes wrong, and the ending shows hope growing back.'
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    maid = f["maid"]
    cook = f["cook"]
    dish = f["dish_cfg"]
    obstacle = f["obstacle_cfg"]
    solution = f["solution_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about a maid named {maid.id} and the cook who sent {maid.pronoun('object')} on an errand. The story follows {maid.id} as {maid.pronoun()} tries to bring basil home safely."
        ),
        (
            f"Why did {maid.id} go to the grocery?",
            f"{maid.id} went to the grocery to fetch fresh basil for {dish.label}. The cook needed the herb so the meal would smell and taste bright."
        ),
        (
            f"What danger was waiting on the road?",
            f"The danger was {obstacle.label}. It threatened the basil because {obstacle.danger.lower()}"
        ),
        (
            f"How did {maid.id} try to protect the basil?",
            f"{maid.id} used {solution.phrase}. {solution.qa_text}"
        ),
    ]
    if f["outcome"] == "delivered":
        qa.append(
            (
                "How did the story end?",
                f"The basil reached the kitchen fresh, and the cook added it to {dish.label}. The bright smell in the kitchen shows that the errand truly succeeded."
            )
        )
        qa.append(
            (
                f"Why was the cook pleased with {maid.id}?",
                f"The cook was pleased because {maid.id} did not merely run fast; {maid.pronoun()} carried the basil with care. That careful choice kept the herb fresh all the way home."
            )
        )
    else:
        qa.append(
            (
                "How did the story end?",
                f"The basil was spoiled, so the meal stayed plain that day. But the cook helped {maid.id} plant new basil seeds, and the ending image of fresh sprouts shows that the mistake became a lesson."
            )
        )
        qa.append(
            (
                f"Was the cook cruel when the errand failed?",
                f"No. The cook cared more about truth and learning than blame, so {cook.pronoun()} helped {maid.id} start again. That kindness turned a sad moment into hope."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = {"maid", "grocery", "basil"}
    obstacle = world.facts["obstacle_cfg"]
    solution = world.facts["solution_cfg"]
    if obstacle.id in {"rain", "storm"}:
        tags.add("rain")
    if obstacle.id == "wind":
        tags.add("wind")
    if obstacle.id == "hot_sun":
        tags.add("heat")
    if solution.id == "lidded_basket":
        tags.add("basket")
    if solution.id == "clay_pot":
        tags.add("pot")
    if solution.id == "damp_cloth":
        tags.add("cloth")
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
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        lines.append(f"  {ent.id:8} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="castle",
        dish="moon_soup",
        obstacle="wind",
        solution="lidded_basket",
        maid_name="Mira",
        maid_gender="girl",
        cook_type="cook_woman",
        trait="careful",
        delay=0,
        seed=None,
    ),
    StoryParams(
        setting="cottage",
        dish="garden_pie",
        obstacle="hot_sun",
        solution="damp_cloth",
        maid_name="Rowan",
        maid_gender="boy",
        cook_type="cook_man",
        trait="steady",
        delay=0,
        seed=None,
    ),
    StoryParams(
        setting="tower",
        dish="sun_bread",
        obstacle="storm",
        solution="clay_pot",
        maid_name="Elin",
        maid_gender="girl",
        cook_type="cook_woman",
        trait="hopeful",
        delay=0,
        seed=None,
    ),
    StoryParams(
        setting="castle",
        dish="moon_soup",
        obstacle="hot_sun",
        solution="damp_cloth",
        maid_name="Tobin",
        maid_gender="boy",
        cook_type="cook_man",
        trait="brisk",
        delay=2,
        seed=None,
    ),
]


ASP_RULES = r"""
uses_basil_dish(D) :- dish(D), basil_ok(D).
sensible(S) :- solution(S), sense(S, N), sense_min(M), N >= M.
valid(St, D, O) :- setting(St), dish(D), obstacle(O), uses_basil_dish(D).

severity(V) :- chosen_obstacle(O), base_severity(O, B), delay(D), V = B + D.
guarded :- chosen_solution(S), chosen_obstacle(O), guards(S, T), threat(O, T).
contains :- chosen_solution(S), power(S, P), severity(V), P >= V.

outcome(delivered) :- guarded, contains.
outcome(ruined) :- not outcome(delivered).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for setting_id in SETTINGS:
        lines.append(asp.fact("setting", setting_id))
    for dish_id, dish in DISHES.items():
        lines.append(asp.fact("dish", dish_id))
        if dish.uses_basil:
            lines.append(asp.fact("basil_ok", dish_id))
    for obstacle_id, obstacle in OBSTACLES.items():
        lines.append(asp.fact("obstacle", obstacle_id))
        lines.append(asp.fact("threat", obstacle_id, obstacle.threat))
        lines.append(asp.fact("base_severity", obstacle_id, obstacle.severity))
    for solution_id, solution in SOLUTIONS.items():
        lines.append(asp.fact("solution", solution_id))
        lines.append(asp.fact("sense", solution_id, solution.sense))
        lines.append(asp.fact("power", solution_id, solution.power))
        for guard in sorted(solution.guards):
            lines.append(asp.fact("guards", solution_id, guard))
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
    return sorted(x for (x,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_obstacle", params.obstacle),
            asp.fact("chosen_solution", params.solution),
            asp.fact("delay", params.delay),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH: valid combos differ between Python and ASP.")

    py_sensible = {s.id for s in sensible_solutions()}
    asp_sens = set(asp_sensible())
    if py_sensible == asp_sens:
        print(f"OK: sensible solutions match ({sorted(py_sensible)}).")
    else:
        rc = 1
        print(f"MISMATCH: sensible solutions differ: python={sorted(py_sensible)} asp={sorted(asp_sens)}")

    cases = list(CURATED)
    for seed in range(40):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        params.seed = seed
        cases.append(params)
    bad = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("Generated empty story.")
        with contextlib.redirect_stdout(io.StringIO()):
            emit(sample, trace=False, qa=True, header="smoke")
        print("OK: smoke test generated and emitted a sample story.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Fairy-tale storyworld: a maid fetches basil from the grocery and must bring it home fresh."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--dish", choices=DISHES)
    ap.add_argument("--obstacle", choices=OBSTACLES)
    ap.add_argument("--solution", choices=SOLUTIONS)
    ap.add_argument("--maid-gender", choices=["girl", "boy"])
    ap.add_argument("--maid-name")
    ap.add_argument("--cook", choices=["cook_woman", "cook_man"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], help="how long the road home drags on")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combos derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.dish and not DISHES[args.dish].uses_basil:
        raise StoryError(explain_dish(DISHES[args.dish]))
    if args.solution and SOLUTIONS[args.solution].sense < SENSE_MIN:
        raise StoryError(explain_solution(args.solution))
    if args.solution and args.obstacle and not can_guard(SOLUTIONS[args.solution], OBSTACLES[args.obstacle]):
        raise StoryError(explain_solution(args.solution, args.obstacle))

    combos = [
        combo for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.dish is None or combo[1] == args.dish)
        and (args.obstacle is None or combo[2] == args.obstacle)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, dish_id, obstacle_id = rng.choice(sorted(combos))
    solution_candidates = [
        s.id for s in sensible_solutions()
        if can_guard(s, OBSTACLES[obstacle_id])
    ]
    if args.solution:
        solution_id = args.solution
    else:
        solution_id = rng.choice(sorted(solution_candidates))
    maid_gender = args.maid_gender or rng.choice(["girl", "boy"])
    if maid_gender == "girl":
        maid_name = args.maid_name or rng.choice(MAID_NAMES_GIRL)
    else:
        maid_name = args.maid_name or rng.choice(MAID_NAMES_BOY)
    cook_type = args.cook or rng.choice(["cook_woman", "cook_man"])
    trait = rng.choice(TRAITS)
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    return StoryParams(
        setting=setting_id,
        dish=dish_id,
        obstacle=obstacle_id,
        solution=solution_id,
        maid_name=maid_name,
        maid_gender=maid_gender,
        cook_type=cook_type,
        trait=trait,
        delay=delay,
        seed=None,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting: {params.setting})")
    if params.dish not in DISHES:
        raise StoryError(f"(Unknown dish: {params.dish})")
    if params.obstacle not in OBSTACLES:
        raise StoryError(f"(Unknown obstacle: {params.obstacle})")
    if params.solution not in SOLUTIONS:
        raise StoryError(f"(Unknown solution: {params.solution})")
    dish = DISHES[params.dish]
    obstacle = OBSTACLES[params.obstacle]
    solution = SOLUTIONS[params.solution]
    if not dish.uses_basil:
        raise StoryError(explain_dish(dish))
    if solution.sense < SENSE_MIN:
        raise StoryError(explain_solution(params.solution))
    if not can_guard(solution, obstacle):
        raise StoryError(explain_solution(params.solution, params.obstacle))

    world = tell(
        setting=SETTINGS[params.setting],
        dish=dish,
        obstacle=obstacle,
        solution=solution,
        maid_name=params.maid_name,
        maid_gender=params.maid_gender,
        cook_type=params.cook_type,
        trait=params.trait,
        delay=params.delay,
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
        print(asp_program("", "#show valid/3.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible solutions: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, dish, obstacle) combos:\n")
        for setting_id, dish_id, obstacle_id in combos:
            print(f"  {setting_id:8} {dish_id:11} {obstacle_id}")
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.maid_name}: {p.dish} with {p.obstacle} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
