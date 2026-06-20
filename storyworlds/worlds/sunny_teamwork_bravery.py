#!/usr/bin/env python3
"""
storyworlds/worlds/sunny_teamwork_bravery.py
============================================

A standalone storyworld sketch for a sunny neighborhood task that becomes too
much for one child until brave honesty and teamwork make a happy ending.

The reasonableness gate is small and concrete:

    task load > solo capacity
    team plan covers every need of the task
    team plan has enough helping power to finish it

That keeps the story inside the requested domain. A task that one child could
easily finish alone is refused, and a plan that does not actually solve the
task is refused. The ASP rules near the bottom mirror the Python gate.
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SOLO_CAPACITY = 3


# ---------------------------------------------------------------------------
# Entities and world state
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "grandmother", "aunt"}
        male = {"boy", "father", "dad", "man", "grandfather", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def reflexive(self) -> str:
        if self.type in {"girl", "mother", "mom", "woman", "grandmother", "aunt"}:
            return "herself"
        if self.type in {"boy", "father", "dad", "man", "grandfather", "uncle"}:
            return "himself"
        return "themselves"

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Setting:
    id: str
    place: str
    morning: str
    detail: str
    payoff_place: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Task:
    id: str
    label: str
    goal: str
    object_phrase: str
    start_image: str
    solo_action: str
    strain_image: str
    ask_line: str
    finish_image: str
    load: int
    solo_progress: int
    needs: set[str]
    tags: set[str] = field(default_factory=set)


@dataclass
class Plan:
    id: str
    label: str
    offer: str
    method: str
    role_line: str
    finished_action: str
    covers: set[str]
    power: int
    helpers: int
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
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def by_role(self, role: str) -> Entity:
        for ent in self.entities.values():
            if ent.role == role:
                return ent
        raise KeyError(role)

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


# ---------------------------------------------------------------------------
# Causal rules
# ---------------------------------------------------------------------------
@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_task_too_heavy(world: World) -> list[str]:
    if "task" not in world.entities:
        return []
    task_ent = world.get("task")
    try:
        hero = world.by_role("hero")
    except KeyError:
        return []
    if task_ent.meters["remaining"] <= SOLO_CAPACITY:
        return []
    if hero.memes["trying_alone"] < THRESHOLD:
        return []
    sig = ("strain", task_ent.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["strain"] += 1
    hero.memes["worry"] += 1
    task_ent.meters["stalled"] += 1
    return ["__strain__"]


def _r_honesty_becomes_bravery(world: World) -> list[str]:
    try:
        hero = world.by_role("hero")
    except KeyError:
        return []
    if hero.memes["strain"] < THRESHOLD or hero.memes["truth_told"] < THRESHOLD:
        return []
    sig = ("honesty", hero.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["bravery"] += 1
    hero.memes["worry"] = 0.0
    return ["__honesty__"]


def _r_teamwork_finishes_task(world: World) -> list[str]:
    if "task" not in world.entities:
        return []
    task_ent = world.get("task")
    try:
        hero = world.by_role("hero")
    except KeyError:
        return []
    if hero.memes["teamwork"] < THRESHOLD:
        return []
    if task_ent.meters["remaining"] <= 0:
        return []
    sig = ("finish", task_ent.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    task_ent.meters["remaining"] = 0.0
    task_ent.meters["done"] += 1
    hero.memes["joy"] += 1
    return ["__finished__"]


CAUSAL_RULES: list[Rule] = [
    Rule("task_too_heavy", "physical", _r_task_too_heavy),
    Rule("honesty_becomes_bravery", "social", _r_honesty_becomes_bravery),
    Rule("teamwork_finishes_task", "social", _r_teamwork_finishes_task),
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


# ---------------------------------------------------------------------------
# Reasonableness gate and prediction
# ---------------------------------------------------------------------------
def too_much_for_one(task: Task) -> bool:
    return task.load > SOLO_CAPACITY


def plan_covers_task(plan: Plan, task: Task) -> bool:
    return task.needs <= plan.covers


def plan_has_power(plan: Plan, task: Task) -> bool:
    return plan.power >= task.load


def compatible_plan(plan: Plan, task: Task) -> bool:
    return plan_covers_task(plan, task) and plan_has_power(plan, task)


def select_plan(task: Task) -> Optional[Plan]:
    for plan in PLANS.values():
        if compatible_plan(plan, task):
            return plan
    return None


def predict_solo(world: World, task: Task) -> dict:
    sim = world.copy()
    hero = sim.by_role("hero")
    task_ent = sim.get("task")
    hero.memes["trying_alone"] += 1
    task_ent.meters["remaining"] = max(0.0, task_ent.meters["remaining"] - task.solo_progress)
    propagate(sim, narrate=False)
    return {
        "stalled": task_ent.meters["stalled"] >= THRESHOLD,
        "remaining": int(task_ent.meters["remaining"]),
        "strain": hero.memes["strain"],
    }


# ---------------------------------------------------------------------------
# Story verbs
# ---------------------------------------------------------------------------
def article(word: str) -> str:
    return "an" if word[:1].lower() in {"a", "e", "i", "o", "u"} else "a"


def entrance(setting: Setting) -> str:
    if setting.id == "maple_street":
        return f"onto {setting.place}"
    return f"into {setting.place}"


def in_place(setting: Setting) -> str:
    if setting.id == "maple_street":
        return f"on {setting.place}"
    return f"in {setting.place}"


def story_text(text: str, hero: Entity, helper: Optional[Entity] = None,
               parent: Optional[Entity] = None) -> str:
    text = text.replace("the child", hero.id).replace("The child", hero.id)
    text = text.replace("their head", f"{hero.pronoun('possessive')} head")
    if helper is not None:
        text = text.replace("the helper", helper.id).replace("The helper", helper.id)
    if parent is not None:
        word = parent.label_word.capitalize()
        text = text.replace("the grown-up", word).replace("The grown-up", word)
    return text


def need_phrase(need: str) -> str:
    return need.replace("_", " ")


def need_list(needs: set[str]) -> str:
    shown = [need_phrase(n) for n in sorted(needs)]
    if len(shown) <= 1:
        return "".join(shown)
    if len(shown) == 2:
        return f"{shown[0]} and {shown[1]}"
    return ", ".join(shown[:-1]) + f", and {shown[-1]}"


def introduce(world: World, hero: Entity, helper: Entity, parent: Entity,
              setting: Setting, task: Task) -> None:
    trait = hero.traits[0] if hero.traits else "helpful"
    world.say(
        f"One sunny morning, {hero.id} stepped {entrance(setting)} with "
        f"{hero.pronoun('possessive')} sleeves rolled up."
    )
    world.say(
        f"{setting.morning} {task.start_image} {helper.id} waved from nearby, "
        f"and {hero.id}'s {parent.label_word} was setting out a little snack table."
    )
    world.say(
        f"{hero.id} was {article(trait)} {trait} {hero.type} who liked being "
        f"useful before anyone had to ask."
    )


def choose_task(world: World, hero: Entity, task: Task) -> None:
    task_ent = world.add(Entity(
        id="task", type="task", label=task.label,
        attrs={"needs": sorted(task.needs)},
    ))
    task_ent.meters["remaining"] = float(task.load)
    hero.memes["hope"] += 1
    world.say(
        f"When {hero.id} saw {task.object_phrase}, {hero.pronoun()} made a "
        f"small promise inside: {hero.pronoun()} would {task.goal} all by "
        f"{hero.reflexive()}."
    )


def try_alone(world: World, hero: Entity, task: Task) -> None:
    task_ent = world.get("task")
    hero.memes["trying_alone"] += 1
    task_ent.meters["remaining"] = max(0.0, task_ent.meters["remaining"] - task.solo_progress)
    world.say(f"First {hero.pronoun()} {task.solo_action}.")
    propagate(world, narrate=False)
    if hero.memes["strain"] >= THRESHOLD:
        remaining = int(task_ent.meters["remaining"])
        world.facts["solo_remaining"] = remaining
        world.say(
            f"But {story_text(task.strain_image, hero)} There was still more "
            f"to do, and the sunny sidewalk seemed to stretch longer than before."
        )


def almost_hide(world: World, hero: Entity, parent: Entity, task: Task) -> None:
    if hero.memes["strain"] < THRESHOLD:
        return
    hero.memes["pride"] += 1
    world.say(
        f"For a moment, {hero.id} wanted to smile and say, \"I'm fine.\" "
        f"{story_text(task.ask_line, hero)}"
    )
    world.say(
        f"Then {hero.pronoun()} looked at {hero.pronoun('possessive')} "
        f"{parent.label_word} and took a brave breath."
    )


def tell_truth(world: World, hero: Entity, parent: Entity, task: Task) -> None:
    hero.memes["truth_told"] += 1
    propagate(world, narrate=False)
    world.say(
        f"\"I wanted to do it by myself,\" {hero.id} said, "
        f"\"but this job is bigger than my two hands.\""
    )
    world.say(
        f"{parent.label_word.capitalize()} nodded. \"That is brave honesty. "
        f"Brave does not have to mean alone.\""
    )
    world.facts["honest"] = hero.memes["bravery"] >= THRESHOLD


def invite_team(world: World, hero: Entity, helper: Entity, parent: Entity,
                task: Task, plan: Plan) -> None:
    team = world.add(Entity(id="team", kind="group", type="team", label=plan.label))
    team.meters["power"] = float(plan.power)
    team.attrs["covers"] = sorted(plan.covers)
    hero.memes["teamwork"] += 1
    helper.memes["teamwork"] += 1
    parent.memes["teamwork"] += 1
    world.say(
        f"{helper.id} came over at once. \"Let's make a team,\" "
        f"{helper.pronoun()} said."
    )
    world.say(f"{story_text(plan.offer, hero, helper, parent)} "
              f"{story_text(plan.role_line, hero, helper, parent)}")
    world.say(f"Together, they {story_text(plan.method, hero, helper, parent)}.")
    propagate(world, narrate=False)


def finish(world: World, hero: Entity, helper: Entity, parent: Entity,
           setting: Setting, task: Task, plan: Plan) -> None:
    task_ent = world.get("task")
    if task_ent.meters["done"] < THRESHOLD:
        return
    hero.memes["love"] += 1
    helper.memes["joy"] += 1
    parent.memes["joy"] += 1
    world.say(
        f"By lunchtime, {plan.finished_action}. {task.finish_image}"
    )
    world.say(
        f"{hero.id} looked over {setting.payoff_place} and grinned. "
        f"The job was finished, the day was still sunny, and the happy part was "
        f"not that {hero.pronoun()} had done it alone. The happy part was that "
        f"{hero.pronoun()} had told the truth, and everyone had helped."
    )


def tell(setting: Setting, task: Task, plan: Plan, hero_name: str = "Mia",
         hero_gender: str = "girl", helper_name: str = "Leo",
         helper_gender: str = "boy", parent_type: str = "mother",
         trait: str = "helpful") -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender,
                            label=hero_name, role="hero", traits=[trait]))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender,
                              label=helper_name, role="helper", traits=["kind"]))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type,
                              label="the parent", role="parent"))

    introduce(world, hero, helper, parent, setting, task)
    choose_task(world, hero, task)

    world.para()
    prediction = predict_solo(world, task)
    world.facts["prediction"] = prediction
    try_alone(world, hero, task)
    almost_hide(world, hero, parent, task)
    tell_truth(world, hero, parent, task)

    world.para()
    invite_team(world, hero, helper, parent, task, plan)
    finish(world, hero, helper, parent, setting, task, plan)

    world.facts.update(
        hero=hero, helper=helper, parent=parent, setting=setting,
        task=task, plan=plan, task_ent=world.get("task"),
        completed=world.get("task").meters["done"] >= THRESHOLD,
        too_much=too_much_for_one(task),
    )
    return world


# ---------------------------------------------------------------------------
# Content registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "maple_street": Setting(
        "maple_street", "Maple Street",
        "The maples made little coins of shade on the pavement.",
        "Mrs. Rivera's flower boxes blinked red and yellow in the sun.",
        "Maple Street",
        {"flower_watering", "book_drive", "picnic_tables"},
    ),
    "community_garden": Setting(
        "community_garden", "the community garden",
        "Bees hummed over the mint, and warm dirt smelled like summer.",
        "A row of thirsty marigolds leaned over the brick path.",
        "the garden path",
        {"flower_watering", "mulch_bags", "picnic_tables"},
    ),
    "courtyard": Setting(
        "courtyard", "the apartment courtyard",
        "Open windows shone like little mirrors in the bright morning.",
        "The bench, the steps, and the planters all waited for helping hands.",
        "the courtyard",
        {"book_drive", "chalk_booth", "picnic_tables"},
    ),
    "corner_park": Setting(
        "corner_park", "the corner park",
        "The slide was warm, and the grass glittered with sprinkler drops.",
        "Neighbors were getting ready for a small picnic under the trees.",
        "the park lawn",
        {"picnic_tables", "mulch_bags", "flower_watering"},
    ),
}

TASKS = {
    "flower_watering": Task(
        "flower_watering", "watering the flower boxes",
        "water every thirsty flower box on the block",
        "the long row of flower boxes and one silver watering can",
        "A row of flowers bent their heads as if asking for a drink.",
        "filled the watering can, carried it two careful steps, and poured a "
        "shiny rain over the first box",
        "the can grew heavy, the flowers kept waiting, and little drops ran "
        "down both of the child's wrists.",
        "The truth sat in the child's chest like a pebble: one can and one child "
        "would take all morning.",
        "Each flower box stood dark and damp, with petals lifted like tiny flags.",
        load=6,
        solo_progress=2,
        needs={"water", "many_trips"},
        tags={"sunny", "flowers", "water", "teamwork"},
    ),
    "book_drive": Task(
        "book_drive", "moving the book-drive boxes",
        "carry the donated books to the sidewalk table",
        "three cardboard boxes full of picture books",
        "The book boxes waited on the porch, fat with stories for other children.",
        "hugged one box around the middle and shuffled it toward the table",
        "the box bumped the child's knees, and the pile of books inside slid "
        "from side to side with a heavy thump.",
        "The honest words felt hard because the books were for a good cause, "
        "and the child wanted to be big enough.",
        "The books sat in neat stacks, ready for neighbors to choose and read.",
        load=7,
        solo_progress=2,
        needs={"lifting", "many_trips", "sorting"},
        tags={"sunny", "books", "sharing", "teamwork"},
    ),
    "picnic_tables": Task(
        "picnic_tables", "setting up the picnic tables",
        "set the little picnic area before the neighbors arrived",
        "folding tables, cups, and a basket of napkins",
        "The picnic things made a bright heap beside the grass.",
        "opened one folding table halfway and tried to tug it straight",
        "one table leg stuck out crooked, the cups rolled away, and the napkins "
        "fluttered like white birds.",
        "The child could see the picnic in their head, but the real table had "
        "more corners than two hands could hold.",
        "The cups stood in sunny rows, and the napkins stayed tucked beneath a "
        "smooth pebble.",
        load=6,
        solo_progress=2,
        needs={"holding", "sorting", "many_trips"},
        tags={"sunny", "picnic", "neighbors", "teamwork"},
    ),
    "mulch_bags": Task(
        "mulch_bags", "spreading the mulch",
        "cover the dry garden bed with soft brown mulch",
        "two scratchy bags of mulch beside the garden bed",
        "The dry bed looked crumbly, and the plants needed a cool blanket.",
        "dragged one bag by its corner and made a brave little furrow in the dirt",
        "the bag was scratchy and stubborn, and it left a brown trail far short "
        "of the garden bed.",
        "The child wanted to help the plants, but wanting did not make the bag "
        "lighter.",
        "The garden bed wore a neat brown blanket, and the leaves looked less "
        "tired in the heat.",
        load=8,
        solo_progress=2,
        needs={"lifting", "spreading", "many_trips"},
        tags={"sunny", "garden", "plants", "teamwork"},
    ),
    "chalk_booth": Task(
        "chalk_booth", "drawing the chalk welcome sign",
        "draw a welcome sign near the snack table",
        "a bucket of sidewalk chalk and a small empty square of pavement",
        "The clean square of pavement waited for color.",
        "drew a yellow sun and two purple flowers",
        "the little sign already looked cheerful, and there was plenty of time.",
        "There was no need for brave honesty yet; this job fit inside one pair "
        "of hands.",
        "The chalk sign glowed on the pavement.",
        load=2,
        solo_progress=2,
        needs={"drawing"},
        tags={"sunny", "chalk"},
    ),
}

PLANS = {
    "bucket_line": Plan(
        "bucket_line", "a bucket line",
        "\"We can make a bucket line,\" said the grown-up.",
        "passed small cups of water from hand to hand, slow and splashy and sure",
        "The grown-up filled, the helper carried, and the child poured at the roots.",
        "the last cup of water slipped into the soil",
        covers={"water", "many_trips"},
        power=7,
        helpers=3,
        tags={"water", "teamwork"},
    ),
    "wagon_team": Plan(
        "wagon_team", "a wagon team",
        "\"The wagon can carry what arms should not,\" said the grown-up.",
        "loaded a little red wagon, pulled together, and sorted each thing where "
        "it belonged",
        "The helper steadied the stack, the grown-up lifted the heavy parts, and "
        "the child chose the neat piles.",
        "the wagon rolled back empty and the table looked ready",
        covers={"lifting", "many_trips", "sorting"},
        power=8,
        helpers=3,
        tags={"wagon", "teamwork"},
    ),
    "table_crew": Plan(
        "table_crew", "a table crew",
        "\"Let's give every hand one job,\" said the grown-up.",
        "held the table steady, snapped the legs into place, and set the cups in "
        "careful rows",
        "The child counted cups, the helper held the corners, and the grown-up "
        "checked the wobbly legs.",
        "the picnic table stood straight under the tree",
        covers={"holding", "sorting", "many_trips"},
        power=7,
        helpers=3,
        tags={"picnic", "teamwork"},
    ),
    "mulch_chain": Plan(
        "mulch_chain", "a mulch chain",
        "\"We can move it in small scoops,\" said the grown-up.",
        "scooped the mulch into small pails, carried the pails, and spread each "
        "soft heap with a rake",
        "The grown-up opened the bags, the helper carried pails, and the child "
        "raked the brown blanket smooth.",
        "the last rake mark curved around the flowers",
        covers={"lifting", "spreading", "many_trips"},
        power=9,
        helpers=3,
        tags={"garden", "teamwork"},
    ),
    "cheering": Plan(
        "cheering", "cheering from the curb",
        "\"I can cheer for you,\" said the helper.",
        "clapped and called out kind words",
        "The helper cheered, but nobody moved the heavy parts.",
        "the child still had too much to do",
        covers={"encouragement"},
        power=1,
        helpers=1,
        tags={"kindness"},
    ),
}

GIRL_NAMES = ["Mia", "Lily", "Zoe", "Ava", "Ella", "Lucy", "Nora", "Rose"]
BOY_NAMES = ["Leo", "Ben", "Max", "Sam", "Finn", "Noah", "Eli", "Theo"]
TRAITS = ["helpful", "thoughtful", "busy", "cheerful", "careful", "eager"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for tid in setting.affords:
            task = TASKS[tid]
            if not too_much_for_one(task):
                continue
            for pid, plan in PLANS.items():
                if compatible_plan(plan, task):
                    combos.append((sid, tid, pid))
    return sorted(combos)


# ---------------------------------------------------------------------------
# Per-world parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    setting: str
    task: str
    plan: str
    name: str
    gender: str
    helper: str
    helper_gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
KNOWLEDGE = {
    "sunny": [("Why can sunny days make outdoor jobs feel bigger?",
               "Sunny days can be bright and warm, so a child may get tired more quickly. "
               "That is why taking breaks and sharing the work can help.")],
    "flowers": [("Why do flowers need water?",
                 "Flowers need water to keep their stems firm and their leaves alive. "
                 "Without water, they can droop in the sun.")],
    "water": [("Why is a bucket line helpful?",
               "A bucket line breaks one big carrying job into many little passes. "
               "Each person does a small part, so the water gets there safely.")],
    "books": [("Why can a box of books be hard to carry?",
               "Books are made of many pages, and many pages together get heavy. "
               "A wagon or extra hands can move them without hurting anyone.")],
    "sharing": [("What is a book drive?",
                 "A book drive is when people collect books to share with others. "
                 "It helps more children find stories to read.")],
    "picnic": [("Why do tables need more than one helper?",
                "A folding table can wobble while it opens. One person can hold it steady "
                "while another checks the legs and sets things on top.")],
    "garden": [("Why does mulch help a garden?",
                "Mulch covers the soil like a blanket. It helps keep the ground damp and "
                "protects plant roots from too much heat.")],
    "teamwork": [("Why does teamwork help with a big job?",
                  "Teamwork lets people share the heavy, careful, and busy parts of a job. "
                  "The work becomes safer and happier because nobody has to carry it alone.")],
    "wagon": [("What is a wagon good for?",
               "A wagon is good for moving things that are too heavy or awkward to carry. "
               "It rolls the weight along the ground.")],
}
KNOWLEDGE_ORDER = [
    "sunny", "flowers", "water", "books", "sharing", "picnic",
    "garden", "wagon", "teamwork",
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, helper = f["hero"], f["helper"]
    task, setting = f["task"], f["setting"]
    return [
        f'Write a TinyStories-style slice-of-life story using the word "sunny" '
        f"where {hero.id} tries to {task.goal} {in_place(setting)}.",
        f"Tell a child-facing story where one {hero.type} finds a neighborhood "
        f"task too big, tells the truth bravely, and finishes it with {helper.id}.",
        f"Write a happy-ending story about teamwork, brave honesty, and "
        f"{task.label} in a sunny neighborhood.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero, helper, parent = f["hero"], f["helper"], f["parent"]
    task, plan, setting = f["task"], f["plan"], f["setting"]
    parent_word = parent.label_word
    qa = [
        ("Who is the story about?",
         f"It is about {hero.id}, a {hero.type} {in_place(setting)}, and "
         f"{helper.id}, who helps when the job becomes too big. "
         f"{hero.id}'s {parent_word} also helps turn the work into a team plan."),
        (f"What task did {hero.id} want to do?",
         f"{hero.id} wanted to {task.goal} all by {hero.reflexive()}. "
         f"The task mattered because it would help the neighbors enjoy the sunny day."),
        (f"Why was the task too much for {hero.id} alone?",
         f"The job had more parts than one child could safely finish alone: "
         f"{need_list(task.needs)}. After {hero.id} tried, there was "
         f"still work left and {hero.pronoun()} felt strained."),
        (f"What brave thing did {hero.id} do?",
         f"{hero.id} told the truth and said the job was bigger than "
         f"{hero.pronoun('possessive')} two hands. That was brave because "
         f"{hero.pronoun()} wanted to seem big enough, but chose honesty instead."),
        ("How did teamwork solve the problem?",
         f"They used {plan.label}, which matched the job's real needs. "
         f"{helper.id}, {hero.id}, and {parent_word} each had a role, so the "
         f"work could be finished safely."),
        ("How did the story end?",
         f"The task was finished and the neighborhood looked ready for the day. "
         f"{hero.id} learned that a happy ending can come from telling the truth "
         f"and letting people help."),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["task"].tags) | set(world.facts["plan"].tags) | {"sunny", "teamwork"}
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


# ---------------------------------------------------------------------------
# CLI / trace
# ---------------------------------------------------------------------------
def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for ent in world.entities.values():
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.attrs:
            bits.append(f"attrs={ent.attrs}")
        lines.append(f"  {ent.id:8} ({ent.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("maple_street", "flower_watering", "bucket_line",
                "Mia", "girl", "Leo", "boy", "mother", "helpful"),
    StoryParams("courtyard", "book_drive", "wagon_team",
                "Ben", "boy", "Ava", "girl", "father", "eager"),
    StoryParams("corner_park", "picnic_tables", "table_crew",
                "Zoe", "girl", "Max", "boy", "mother", "careful"),
    StoryParams("community_garden", "mulch_bags", "mulch_chain",
                "Finn", "boy", "Nora", "girl", "father", "thoughtful"),
]


def explain_rejection(task: Task, plan: Optional[Plan] = None) -> str:
    if not too_much_for_one(task):
        return (f"(No story: {task.label} fits inside one child's effort here. "
                f"This world is about a sunny task that becomes too much for "
                f"one child before teamwork solves it.)")
    if plan is None:
        return (f"(No story: no selected team plan can finish {task.label}. "
                f"The plan must cover {sorted(task.needs)} and have enough helping power.)")
    if not plan_covers_task(plan, task):
        missing = sorted(task.needs - plan.covers)
        return (f"(No story: {plan.label} does not cover {missing}, so it would "
                f"not honestly solve {task.label}.)")
    return (f"(No story: {plan.label} is not strong enough for {task.label}; "
            f"power={plan.power}, load={task.load}.)")


# ---------------------------------------------------------------------------
# Inline ASP twin of the reasonableness gate
# ---------------------------------------------------------------------------
ASP_RULES = r"""
too_much(T) :- load(T, L), solo_capacity(S), L > S.
missing_need(P, T) :- task(T), plan(P), need(T, N), not covers(P, N).
plan_covers(P, T) :- task(T), plan(P), not missing_need(P, T).
enough_power(P, T) :- power(P, W), load(T, L), W >= L.
compatible(P, T) :- plan_covers(P, T), enough_power(P, T).
valid(S, T, P) :- setting(S), affords(S, T), too_much(T), compatible(P, T).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = [asp.fact("solo_capacity", SOLO_CAPACITY)]
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for tid in sorted(setting.affords):
            lines.append(asp.fact("affords", sid, tid))
    for tid, task in TASKS.items():
        lines.append(asp.fact("task", tid))
        lines.append(asp.fact("load", tid, task.load))
        for need in sorted(task.needs):
            lines.append(asp.fact("need", tid, need))
    for pid, plan in PLANS.items():
        lines.append(asp.fact("plan", pid))
        lines.append(asp.fact("power", pid, plan.power))
        for need in sorted(plan.covers):
            lines.append(asp.fact("covers", pid, need))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: ASP gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between ASP gate and valid_combos():")
    if clingo_set - python_set:
        print("  only in ASP:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in Python:", sorted(python_set - clingo_set))
    return 1


# ---------------------------------------------------------------------------
# Standard interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: sunny neighborhood bravery and teamwork. "
                    "Unspecified choices are picked at random.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--plan", choices=PLANS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
    ap.add_argument("--helper")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None,
                    help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true",
                    help="list compatible stories derived by ASP")
    ap.add_argument("--verify", action="store_true",
                    help="check the inline ASP gate matches Python")
    ap.add_argument("--show-asp", action="store_true",
                    help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid] or list(pool)
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.task:
        task = TASKS[args.task]
        if not too_much_for_one(task):
            raise StoryError(explain_rejection(task))
    if args.task and args.plan:
        task, plan = TASKS[args.task], PLANS[args.plan]
        if not compatible_plan(plan, task):
            raise StoryError(explain_rejection(task, plan))

    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.task is None or c[1] == args.task)
              and (args.plan is None or c[2] == args.plan)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting, task, plan = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or rng.choice(["girl", "boy"])
    name = args.name or _pick_name(rng, gender)
    helper = args.helper or _pick_name(rng, helper_gender, avoid=name)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(setting, task, plan, name, gender, helper, helper_gender,
                       parent, trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.setting], TASKS[params.task], PLANS[params.plan],
        params.name, params.gender, params.helper, params.helper_gender,
        params.parent, params.trait,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False,
         header: str = "") -> None:
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
        print(f"{len(combos)} compatible (setting, task, plan) combos:\n")
        for setting, task, plan in combos:
            print(f"  {setting:18} {task:16} {plan}")
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
            header = f"### {p.name}: {p.task} at {p.setting} ({p.plan})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
