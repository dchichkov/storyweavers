#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/rice_pick_gerund_mystery_to_solve_teamwork.py
=========================================================================

A standalone storyworld about two children helping with rice, noticing that some
has gone missing, and solving the mystery together in a careful, heartwarming
way. The world prefers sensible investigation plans and rejects rash ones.

Run it
------
python storyworlds/worlds/gpt-5.4/rice_pick_gerund_mystery_to_solve_teamwork.py
python storyworlds/worlds/gpt-5.4/rice_pick_gerund_mystery_to_solve_teamwork.py --setting porch --culprit sparrow
python storyworlds/worlds/gpt-5.4/rice_pick_gerund_mystery_to_solve_teamwork.py --plan climb_boxes
python storyworlds/worlds/gpt-5.4/rice_pick_gerund_mystery_to_solve_teamwork.py --all
python storyworlds/worlds/gpt-5.4/rice_pick_gerund_mystery_to_solve_teamwork.py --qa --json
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
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
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
            "grandmother": "grandma",
            "grandfather": "grandpa",
            "mother": "mom",
            "father": "dad",
        }.get(self.type, self.type)


@dataclass
class Setting:
    id: str
    place: str
    opening: str
    sources: set[str] = field(default_factory=set)
    culprits: set[str] = field(default_factory=set)
    clues: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class RiceSource:
    id: str
    label: str
    phrase: str
    place_text: str
    exposed: int
    movable_to: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Culprit:
    id: str
    label: str
    singular: bool
    entry: str
    trail: str
    move_text: str
    tags: set[str] = field(default_factory=set)

    def pronoun(self) -> str:
        return "it" if self.singular else "they"


@dataclass
class ClueSpot:
    id: str
    label: str
    phrase: str
    culprit: str
    difficulty: int
    reveal: str
    caution: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Plan:
    id: str
    sense: int
    power: int
    teamwork: bool
    text: str
    fail: str
    qa_text: str
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
    out: list[str] = []
    rice = world.get("rice")
    if rice.meters["missing"] < THRESHOLD:
        return out
    for eid in ("hero1", "hero2"):
        kid = world.get(eid)
        sig = ("worry", kid.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        kid.memes["concern"] += 1
        out.append("__mystery__")
    return out


def _r_team(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("worked_together") and ("team",) not in world.fired:
        world.fired.add(("team",))
        for eid in ("hero1", "hero2"):
            world.get(eid).memes["trust"] += 1
            world.get(eid).memes["brave"] += 1
        out.append("__team__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="worry", tag="emotional", apply=_r_worry),
    Rule(name="team", tag="social", apply=_r_team),
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
        for s in produced:
            world.say(s)
    return produced


SETTINGS = {
    "kitchen": Setting(
        id="kitchen",
        place="the warm kitchen",
        opening="The window was open a crack, and the table shone in the afternoon light.",
        sources={"bowl", "sack"},
        culprits={"mouse", "sparrow"},
        clues={"mouse_hole", "windowsill"},
        tags={"kitchen"},
    ),
    "porch": Setting(
        id="porch",
        place="the shady porch",
        opening="A soft breeze moved the curtain, and sounds from the yard drifted in.",
        sources={"tray", "bowl"},
        culprits={"sparrow", "chicken"},
        clues={"rafter", "coop_path", "windowsill"},
        tags={"porch"},
    ),
    "storeroom": Setting(
        id="storeroom",
        place="the little storeroom",
        opening="It smelled of baskets and straw, and the corners were dim and quiet.",
        sources={"sack", "bowl"},
        culprits={"mouse", "sparrow"},
        clues={"mouse_hole", "rafter"},
        tags={"storeroom"},
    ),
}

RICE_SOURCES = {
    "bowl": RiceSource(
        id="bowl",
        label="bowl of rice",
        phrase="a wide bowl of rice",
        place_text="on the low table",
        exposed=2,
        movable_to="a lid-topped jar",
        tags={"rice"},
    ),
    "sack": RiceSource(
        id="sack",
        label="rice sack",
        phrase="a cloth sack of rice",
        place_text="by the wall",
        exposed=3,
        movable_to="a tall tin with a tight lid",
        tags={"rice"},
    ),
    "tray": RiceSource(
        id="tray",
        label="drying tray of rice",
        phrase="a flat tray of rice set out to dry",
        place_text="near the sunny step",
        exposed=3,
        movable_to="a high shelf inside",
        tags={"rice"},
    ),
}

CULPRITS = {
    "mouse": Culprit(
        id="mouse",
        label="mouse",
        singular=True,
        entry="a tiny gray mouse",
        trail="a neat line of grains leading to a dark crack by the floor",
        move_text="nibbling one grain at a time and hurrying away with it",
        tags={"mouse"},
    ),
    "sparrow": Culprit(
        id="sparrow",
        label="sparrow",
        singular=True,
        entry="a brown sparrow",
        trail="a flutter of feathers and three grains resting by the sill",
        move_text="hopping in, snatching a grain, and darting back up",
        tags={"sparrow", "bird"},
    ),
    "chicken": Culprit(
        id="chicken",
        label="chicken",
        singular=True,
        entry="a cheeky chicken",
        trail="little scratch marks and a crooked trail of grains toward the yard",
        move_text="stretching its neck in from the porch and pecking quickly",
        tags={"chicken", "bird"},
    ),
}

CLUES = {
    "mouse_hole": ClueSpot(
        id="mouse_hole",
        label="mouse hole",
        phrase="the dark mouse hole near the floorboards",
        culprit="mouse",
        difficulty=2,
        reveal="two bright whiskers and a tiny nose peeping out beside the grains",
        caution="Putting fingers into a dark hole was not safe because something inside might bite or startle them.",
        tags={"mouse"},
    ),
    "windowsill": ClueSpot(
        id="windowsill",
        label="windowsill",
        phrase="the sunny windowsill",
        culprit="sparrow",
        difficulty=1,
        reveal="a sparrow balancing there, with one grain shining in its beak",
        caution="Leaning too far toward the open window could lead to a tumble.",
        tags={"bird"},
    ),
    "rafter": ClueSpot(
        id="rafter",
        label="rafter",
        phrase="the high porch rafter",
        culprit="sparrow",
        difficulty=3,
        reveal="a sparrow tucked high in the rafter, dropping little bits as it worked",
        caution="Climbing boxes to reach a high place could make the whole stack wobble.",
        tags={"bird"},
    ),
    "coop_path": ClueSpot(
        id="coop_path",
        label="coop path",
        phrase="the path by the chicken coop",
        culprit="chicken",
        difficulty=1,
        reveal="a chicken standing at the end of the grain trail, blinking as if nothing had happened",
        caution="Running after flapping chickens could make someone slip on loose straw.",
        tags={"chicken"},
    ),
}

PLANS = {
    "lantern_together": Plan(
        id="lantern_together",
        sense=3,
        power=3,
        teamwork=True,
        text="took a small lantern, stayed shoulder to shoulder, and checked the clue slowly",
        fail="started with the lantern and teamwork, but the clue was still too awkward to manage neatly",
        qa_text="They used a lantern and stayed together while they checked the clue.",
        tags={"lantern", "teamwork"},
    ),
    "ask_grandma": Plan(
        id="ask_grandma",
        sense=3,
        power=4,
        teamwork=True,
        text="called for a grown-up, then followed the trail together with calm, careful steps",
        fail="called for help, but in the hurry some extra rice still spilled before the mystery was solved",
        qa_text="They called a grown-up and followed the trail together.",
        tags={"adult_help", "teamwork"},
    ),
    "broom_peek": Plan(
        id="broom_peek",
        sense=2,
        power=2,
        teamwork=True,
        text="used a broom from the floor while one child pointed and the other held the bowl steady",
        fail="used a broom from the floor, but the clue was too high and a few more grains pattered down before they understood it",
        qa_text="They worked together with a broom from the floor instead of climbing.",
        tags={"teamwork"},
    ),
    "climb_boxes": Plan(
        id="climb_boxes",
        sense=1,
        power=1,
        teamwork=False,
        text="started to climb a stack of boxes alone",
        fail="climbed the boxes and made the stack wobble",
        qa_text="They tried climbing boxes.",
        tags={"unsafe"},
    ),
}

GIRL_NAMES = ["Mina", "Lila", "Ava", "Nora", "Zoe", "Ella", "Lucy", "Maya"]
BOY_NAMES = ["Ben", "Tao", "Finn", "Noah", "Eli", "Sam", "Leo", "Milo"]
TRAITS = ["careful", "gentle", "patient", "bright", "thoughtful", "steady"]


def culprit_can_reach(source: RiceSource, culprit: Culprit) -> bool:
    if culprit.id == "mouse":
        return source.id in {"bowl", "sack"}
    if culprit.id == "sparrow":
        return source.id in {"bowl", "tray", "sack"}
    if culprit.id == "chicken":
        return source.id in {"tray", "bowl"}
    return False


def valid_combo(setting_id: str, source_id: str, culprit_id: str, clue_id: str) -> bool:
    setting = SETTINGS[setting_id]
    source = RICE_SOURCES[source_id]
    culprit = CULPRITS[culprit_id]
    clue = CLUES[clue_id]
    if source_id not in setting.sources:
        return False
    if culprit_id not in setting.culprits:
        return False
    if clue_id not in setting.clues:
        return False
    if clue.culprit != culprit_id:
        return False
    if not culprit_can_reach(source, culprit):
        return False
    return True


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for setting_id in SETTINGS:
        for source_id in RICE_SOURCES:
            for culprit_id in CULPRITS:
                for clue_id in CLUES:
                    if valid_combo(setting_id, source_id, culprit_id, clue_id):
                        combos.append((setting_id, source_id, culprit_id, clue_id))
    return combos


def sensible_plans() -> list[Plan]:
    return [p for p in PLANS.values() if p.sense >= SENSE_MIN]


def outcome_of(params: "StoryParams") -> str:
    plan = PLANS[params.plan]
    clue = CLUES[params.clue]
    return "solved" if plan.power >= clue.difficulty else "spill"


def explain_combo_rejection(setting_id: str, source_id: str, culprit_id: str, clue_id: str) -> str:
    setting = SETTINGS[setting_id]
    source = RICE_SOURCES[source_id]
    culprit = CULPRITS[culprit_id]
    clue = CLUES[clue_id]
    if source_id not in setting.sources:
        return f"(No story: {source.label} does not belong in {setting.place} here.)"
    if culprit_id not in setting.culprits:
        return f"(No story: a {culprit.label} is not a plausible grain thief in {setting.place} here.)"
    if clue_id not in setting.clues:
        return f"(No story: {clue.phrase} is not part of {setting.place} here.)"
    if clue.culprit != culprit_id:
        return f"(No story: {clue.phrase} points to a {CLUES[clue_id].culprit}, not a {culprit.label}.)"
    return f"(No story: a {culprit.label} would not reasonably steal from that rice setup.)"


def explain_plan(plan_id: str) -> str:
    plan = PLANS[plan_id]
    better = ", ".join(sorted(p.id for p in sensible_plans()))
    return (
        f"(Refusing plan '{plan_id}': it scores too low on common sense "
        f"(sense={plan.sense} < {SENSE_MIN}). A mystery story may include caution, "
        f"but it should still prefer careful investigation. Try: {better}.)"
    )


def predict_clue(world: World, plan: Plan, clue: ClueSpot) -> dict:
    sim = world.copy()
    sim.facts["worked_together"] = plan.teamwork
    propagate(sim, narrate=False)
    return {
        "solved": plan.power >= clue.difficulty,
        "team": sim.get("hero1").memes["trust"] + sim.get("hero2").memes["trust"],
    }


def setup_scene(world: World, a: Entity, b: Entity, elder: Entity, source: RiceSource) -> None:
    a.memes["joy"] += 1
    b.memes["joy"] += 1
    world.say(
        f"{a.id} and {b.id} sat with {elder.label_word} in {world.setting.place}, "
        f"picking tiny husks from {source.phrase} {source.place_text}."
    )
    world.say(world.setting.opening)
    world.say(
        f"Each time they found a dark speck, they dropped it into a little cup, "
        f"and the clean rice made a soft white hill."
    )


def notice(world: World, a: Entity, b: Entity, source: RiceSource, culprit: Culprit) -> None:
    rice = world.get("rice")
    rice.meters["missing"] += 1
    propagate(world, narrate=False)
    world.say(
        f"After a while, {a.id} blinked. The white hill looked smaller, not bigger."
    )
    world.say(
        f'"That is strange," {b.id} said. "We have been picking rice, but some rice '
        f'is disappearing."'
    )
    world.say(
        f"On the floor lay {culprit.trail}. Suddenly the work felt like a little mystery to solve."
    )


def rush(world: World, a: Entity, clue: ClueSpot) -> None:
    a.memes["hurry"] += 1
    world.say(
        f'{a.id} took one quick step toward {clue.phrase}. "I want to see right now," '
        f"{a.pronoun()} said."
    )


def warn(world: World, b: Entity, a: Entity, clue: ClueSpot, plan: Plan, elder: Entity) -> None:
    pred = predict_clue(world, plan, clue)
    b.memes["caution"] += 1
    world.facts["predicted_solved"] = pred["solved"]
    world.say(
        f'{b.id} reached for {a.id}\'s sleeve. "Slow down," {b.pronoun()} said. '
        f'"{clue.caution}"'
    )
    if pred["solved"]:
        world.say(
            f'{b.id} added, "If we stay together and think first, we can solve it without making a mess."'
        )
    else:
        world.say(
            f'{b.id} added, "If we hurry with the wrong plan, we may lose the clue before {elder.label_word} even sees it."'
        )


def investigate_success(world: World, a: Entity, b: Entity, elder: Entity, culprit: Culprit,
                        clue: ClueSpot, plan: Plan, source: RiceSource) -> None:
    world.facts["worked_together"] = plan.teamwork
    propagate(world, narrate=False)
    world.say(
        f"So the two children {plan.text}. There, at {clue.phrase}, they found {clue.reveal}."
    )
    world.say(
        f'"It was {culprit.entry}!" {a.id} whispered. It had been {culprit.move_text}.'
    )
    world.say(
        f"{elder.label_word.capitalize()} smiled and helped them move the {source.label} into {source.movable_to}, "
        f"where small thieves could not reach it."
    )
    for kid in (a, b):
        kid.memes["relief"] += 1
        kid.memes["lesson"] += 1


def investigate_spill(world: World, a: Entity, b: Entity, elder: Entity, culprit: Culprit,
                      clue: ClueSpot, plan: Plan, source: RiceSource) -> None:
    rice = world.get("rice")
    rice.meters["spilled"] += 1
    world.facts["worked_together"] = plan.teamwork
    propagate(world, narrate=False)
    world.say(
        f"The children {plan.fail}. A soft scatter of grains slipped across the floor."
    )
    world.say(
        f"That was when {elder.label_word} came close and looked up to {clue.phrase}. "
        f"There was {clue.reveal}."
    )
    world.say(
        f"Together they laughed a tiny, shaky laugh. The thief was {culprit.entry}, "
        f"and the children had learned that careful steps mattered as much as sharp eyes."
    )
    world.say(
        f"{elder.label_word.capitalize()} fetched a dustpan, and all three of them cleaned the spilled rice before "
        f"moving the rest into {source.movable_to}."
    )
    for kid in (a, b):
        kid.memes["relief"] += 1
        kid.memes["lesson"] += 1
        kid.memes["concern"] = 0.0


def ending(world: World, a: Entity, b: Entity, elder: Entity) -> None:
    a.memes["joy"] += 1
    b.memes["joy"] += 1
    world.say(
        f"When the work was done, {a.id} and {b.id} sat down again beside {elder.label_word}."
    )
    world.say(
        f"They went back to picking rice together, slower now, listening to the tiny tap of each husk in the cup."
    )
    world.say(
        f"The room felt peaceful again, and the solved mystery made the clean white grains seem brighter than before."
    )


def tell(setting: Setting, source: RiceSource, culprit: Culprit, clue: ClueSpot, plan: Plan,
         hero1_name: str = "Mina", hero1_gender: str = "girl",
         hero2_name: str = "Ben", hero2_gender: str = "boy",
         elder_type: str = "grandmother", trait: str = "careful") -> World:
    world = World(setting)
    a = world.add(Entity(id="hero1", kind="character", type=hero1_gender, label=hero1_name, role="lead"))
    b = world.add(Entity(id="hero2", kind="character", type=hero2_gender, label=hero2_name, role="partner"))
    elder = world.add(Entity(id="elder", kind="character", type=elder_type, label="the elder", role="elder"))
    rice = world.add(Entity(id="rice", type="rice", label=source.label, tags={"rice"}))

    a.attrs["name"] = hero1_name
    b.attrs["name"] = hero2_name
    a.attrs["trait"] = "eager"
    b.attrs["trait"] = trait

    setup_scene(world, a, b, elder, source)
    world.para()
    notice(world, a, b, source, culprit)
    rush(world, a, clue)
    warn(world, b, a, clue, plan, elder)
    world.para()

    if plan.power >= clue.difficulty:
        investigate_success(world, a, b, elder, culprit, clue, plan, source)
        result = "solved"
    else:
        investigate_spill(world, a, b, elder, culprit, clue, plan, source)
        result = "spill"

    world.para()
    ending(world, a, b, elder)

    world.facts.update(
        setting=setting,
        source=source,
        culprit=culprit,
        clue=clue,
        plan=plan,
        hero1=a,
        hero2=b,
        elder=elder,
        result=result,
        teamwork=plan.teamwork,
        rice_missing=rice.meters["missing"] >= THRESHOLD,
        rice_spilled=rice.meters["spilled"] >= THRESHOLD,
    )
    return world


@dataclass
class StoryParams:
    setting: str
    source: str
    culprit: str
    clue: str
    plan: str
    hero1_name: str
    hero1_gender: str
    hero2_name: str
    hero2_gender: str
    elder_type: str
    trait: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "rice": [
        ("What is rice?",
         "Rice is a small grain that people cook and eat in many parts of the world. Before cooking, it may need to be cleaned or sorted.")
    ],
    "mouse": [
        ("Why might a mouse take grains of rice?",
         "A mouse looks for small bits of food it can carry away. Loose grains are easy for it to nibble or grab.")
    ],
    "bird": [
        ("Why do birds like grains?",
         "Many birds eat seeds and grains because they are small and easy to peck. A bird may hop in quickly, take one, and fly away.")
    ],
    "chicken": [
        ("Why would a chicken peck at rice?",
         "Chickens peck at little bits of food they see on the ground or nearby. Grains of rice are just the sort of thing that catches their eye.")
    ],
    "lantern": [
        ("Why is a lantern helpful when looking in a dim place?",
         "A lantern gives steady light so you can see clearly. When you can see better, it is easier to move carefully.")
    ],
    "adult_help": [
        ("Why is it smart to ask a grown-up for help with a tricky clue?",
         "A grown-up can help you reach, move, or check things safely. Asking for help is part of being careful, not part of giving up.")
    ],
    "teamwork": [
        ("What does teamwork mean?",
         "Teamwork means people help one another toward the same goal. One person may notice one clue while another remembers the safe way to act.")
    ],
}
KNOWLEDGE_ORDER = ["rice", "mouse", "bird", "chicken", "lantern", "adult_help", "teamwork"]


def child_name(ent: Entity) -> str:
    return ent.attrs.get("name", ent.label or ent.id)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    a = child_name(f["hero1"])
    b = child_name(f["hero2"])
    source = f["source"]
    culprit = f["culprit"]
    clue = f["clue"]
    result = f["result"]
    if result == "spill":
        return [
            'Write a heartwarming mystery-to-solve story for a 3-to-5-year-old that includes the words "rice" and "picking".',
            f"Tell a gentle cautionary story where {a} and {b} notice rice going missing while picking husks from {source.phrase}, then solve the mystery together after a small mistake.",
            f"Write a teamwork story about children who follow a clue to {clue.phrase}, discover a {culprit.label}, and learn to slow down and be careful.",
        ]
    return [
        'Write a heartwarming mystery-to-solve story for a 3-to-5-year-old that includes the words "rice" and "picking".',
        f"Tell a story where {a} and {b} are picking rice with a grandparent, notice grains going missing, and solve the mystery through teamwork.",
        f"Write a gentle cautionary story with a happy ending: a clue leads to {clue.phrase}, the thief turns out to be a {culprit.label}, and careful teamwork keeps everyone safe.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a = child_name(f["hero1"])
    b = child_name(f["hero2"])
    elder = f["elder"]
    source = f["source"]
    culprit = f["culprit"]
    clue = f["clue"]
    plan = f["plan"]
    result = f["result"]

    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about two children, {a} and {b}, and their {elder.label_word}. They are working together over a bowl of rice when a small mystery begins."
        ),
        (
            "What were the children doing at the start?",
            f"They were picking tiny husks from {source.phrase}. The quiet work is what let them notice that the rice looked smaller instead of bigger."
        ),
        (
            "Why did the rice feel like a mystery?",
            f"Some of the rice kept disappearing even while the children were carefully sorting it. Then they found a trail of grains, which showed that someone or something had been taking it away."
        ),
        (
            f"Why did {b} tell {a} to slow down?",
            f"{b} wanted them to be careful near {clue.phrase}. {clue.caution}"
        ),
    ]
    if result == "solved":
        qa.append(
            (
                "How did they solve the mystery?",
                f"{plan.qa_text} That careful plan led them to {clue.phrase}, where they discovered the {culprit.label} that had been taking the rice."
            )
        )
        qa.append(
            (
                "What changed at the end?",
                f"They moved the rice to a safer place and went back to picking it together. The ending feels peaceful because the mystery is solved and the children learned to use teamwork and caution."
            )
        )
    else:
        qa.append(
            (
                "Did they make a mistake while solving the mystery?",
                f"Yes. Their plan was careful in spirit, but it was not strong enough for that clue, so some extra rice spilled before the mystery was fully solved. Then {elder.label_word} helped them clean up and finish safely."
            )
        )
        qa.append(
            (
                "What did the children learn?",
                f"They learned that sharp eyes are not enough by themselves. Solving a mystery goes better when you slow down, work together, and choose the safest way to check a clue."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"rice", "teamwork"}
    tags |= set(world.facts["culprit"].tags)
    tags |= set(world.facts["plan"].tags)
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
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:8} ({e.type:11}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="kitchen",
        source="bowl",
        culprit="mouse",
        clue="mouse_hole",
        plan="ask_grandma",
        hero1_name="Mina",
        hero1_gender="girl",
        hero2_name="Ben",
        hero2_gender="boy",
        elder_type="grandmother",
        trait="careful",
    ),
    StoryParams(
        setting="porch",
        source="tray",
        culprit="sparrow",
        clue="rafter",
        plan="lantern_together",
        hero1_name="Lila",
        hero1_gender="girl",
        hero2_name="Tao",
        hero2_gender="boy",
        elder_type="grandfather",
        trait="steady",
    ),
    StoryParams(
        setting="porch",
        source="bowl",
        culprit="chicken",
        clue="coop_path",
        plan="broom_peek",
        hero1_name="Ava",
        hero1_gender="girl",
        hero2_name="Leo",
        hero2_gender="boy",
        elder_type="grandmother",
        trait="thoughtful",
    ),
    StoryParams(
        setting="storeroom",
        source="sack",
        culprit="sparrow",
        clue="rafter",
        plan="broom_peek",
        hero1_name="Nora",
        hero1_gender="girl",
        hero2_name="Finn",
        hero2_gender="boy",
        elder_type="grandfather",
        trait="patient",
    ),
]


ASP_RULES = r"""
valid(S, Src, C, Cl) :- setting(S), source(Src), culprit(C), clue(Cl),
                        setting_source(S, Src),
                        setting_culprit(S, C),
                        setting_clue(S, Cl),
                        clue_for(Cl, C),
                        reaches(C, Src).

sensible(P) :- plan(P), sense(P, X), sense_min(M), X >= M.

outcome(solved) :- chosen_plan(P), power(P, Pow), chosen_clue(Cl), difficulty(Cl, D), Pow >= D.
outcome(spill)  :- chosen_plan(P), power(P, Pow), chosen_clue(Cl), difficulty(Cl, D), Pow < D.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for src in sorted(setting.sources):
            lines.append(asp.fact("setting_source", sid, src))
        for c in sorted(setting.culprits):
            lines.append(asp.fact("setting_culprit", sid, c))
        for cl in sorted(setting.clues):
            lines.append(asp.fact("setting_clue", sid, cl))
    for src_id in RICE_SOURCES:
        lines.append(asp.fact("source", src_id))
    for culprit_id, culprit in CULPRITS.items():
        lines.append(asp.fact("culprit", culprit_id))
        for src_id, source in RICE_SOURCES.items():
            if culprit_can_reach(source, culprit):
                lines.append(asp.fact("reaches", culprit_id, src_id))
    for clue_id, clue in CLUES.items():
        lines.append(asp.fact("clue", clue_id))
        lines.append(asp.fact("clue_for", clue_id, clue.culprit))
        lines.append(asp.fact("difficulty", clue_id, clue.difficulty))
    for plan_id, plan in PLANS.items():
        lines.append(asp.fact("plan", plan_id))
        lines.append(asp.fact("sense", plan_id, plan.sense))
        lines.append(asp.fact("power", plan_id, plan.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible_plans() -> list[str]:
    import asp
    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(p for (p,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp
    scenario = "\n".join([
        asp.fact("chosen_plan", params.plan),
        asp.fact("chosen_clue", params.clue),
    ])
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def asp_verify() -> int:
    rc = 0

    py_valid = set(valid_combos())
    asp_valid = set(asp_valid_combos())
    if py_valid == asp_valid:
        print(f"OK: gate matches valid_combos() ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if asp_valid - py_valid:
            print("  only in clingo:", sorted(asp_valid - py_valid))
        if py_valid - asp_valid:
            print("  only in python:", sorted(py_valid - asp_valid))

    py_sensible = {p.id for p in sensible_plans()}
    asp_sensible = set(asp_sensible_plans())
    if py_sensible == asp_sensible:
        print(f"OK: sensible plans match ({sorted(py_sensible)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible plans: clingo={sorted(asp_sensible)} python={sorted(py_sensible)}")

    cases = list(CURATED)
    for s in range(50):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(s))
            cases.append(params)
        except StoryError:
            continue
    bad = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("Smoke test produced an empty story.")
        print("OK: smoke test generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: missing rice, a clue, and careful teamwork."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--source", choices=RICE_SOURCES)
    ap.add_argument("--culprit", choices=CULPRITS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--plan", choices=PLANS)
    ap.add_argument("--elder", choices=["grandmother", "grandfather"])
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


def _pick_child(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.plan and PLANS[args.plan].sense < SENSE_MIN:
        raise StoryError(explain_plan(args.plan))

    if args.setting and args.source and args.culprit and args.clue:
        if not valid_combo(args.setting, args.source, args.culprit, args.clue):
            raise StoryError(explain_combo_rejection(args.setting, args.source, args.culprit, args.clue))

    combos = [
        c for c in valid_combos()
        if (args.setting is None or c[0] == args.setting)
        and (args.source is None or c[1] == args.source)
        and (args.culprit is None or c[2] == args.culprit)
        and (args.clue is None or c[3] == args.clue)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, source_id, culprit_id, clue_id = rng.choice(sorted(combos))
    plan_id = args.plan or rng.choice(sorted(p.id for p in sensible_plans()))
    hero1_name, hero1_gender = _pick_child(rng)
    hero2_name, hero2_gender = _pick_child(rng, avoid=hero1_name)
    elder_type = args.elder or rng.choice(["grandmother", "grandfather"])
    trait = rng.choice(TRAITS)

    return StoryParams(
        setting=setting_id,
        source=source_id,
        culprit=culprit_id,
        clue=clue_id,
        plan=plan_id,
        hero1_name=hero1_name,
        hero1_gender=hero1_gender,
        hero2_name=hero2_name,
        hero2_gender=hero2_gender,
        elder_type=elder_type,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        setting = SETTINGS[params.setting]
        source = RICE_SOURCES[params.source]
        culprit = CULPRITS[params.culprit]
        clue = CLUES[params.clue]
        plan = PLANS[params.plan]
    except KeyError as err:
        raise StoryError(f"(Invalid parameter choice: {err})") from err

    if not valid_combo(params.setting, params.source, params.culprit, params.clue):
        raise StoryError(explain_combo_rejection(params.setting, params.source, params.culprit, params.clue))
    if plan.sense < SENSE_MIN:
        raise StoryError(explain_plan(params.plan))

    world = tell(
        setting=setting,
        source=source,
        culprit=culprit,
        clue=clue,
        plan=plan,
        hero1_name=params.hero1_name,
        hero1_gender=params.hero1_gender,
        hero2_name=params.hero2_name,
        hero2_gender=params.hero2_gender,
        elder_type=params.elder_type,
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
        print(asp_program("", "#show valid/4.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible plans: {', '.join(asp_sensible_plans())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, source, culprit, clue) combos:\n")
        for setting_id, source_id, culprit_id, clue_id in combos:
            print(f"  {setting_id:10} {source_id:6} {culprit_id:8} {clue_id}")
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
            header = (
                f"### {p.hero1_name} & {p.hero2_name}: {p.culprit} at {p.clue} "
                f"({p.setting}, {p.source}, {p.plan}, {outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
