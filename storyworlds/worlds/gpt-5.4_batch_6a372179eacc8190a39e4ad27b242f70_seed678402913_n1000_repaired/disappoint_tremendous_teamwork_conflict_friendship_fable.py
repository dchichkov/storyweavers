#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/disappoint_tremendous_teamwork_conflict_friendship_fable.py
======================================================================================

A small fable-like story world about two animal friends, a shared task, a quarrel,
and the way teamwork repairs both the work and the friendship.

The core constraint of this world is simple: the chosen task must truly require
both friends. A story is only valid when the first friend cannot finish the task
alone, the second friend cannot finish it alone, and their combined skills can.
That keeps the conflict honest and makes the repair matter.

Run it
------
    python storyworlds/worlds/gpt-5.4/disappoint_tremendous_teamwork_conflict_friendship_fable.py
    python storyworlds/worlds/gpt-5.4/disappoint_tremendous_teamwork_conflict_friendship_fable.py --friend1 squirrel --friend2 beaver --task figs
    python storyworlds/worlds/gpt-5.4/disappoint_tremendous_teamwork_conflict_friendship_fable.py --repair sulk
    python storyworlds/worlds/gpt-5.4/disappoint_tremendous_teamwork_conflict_friendship_fable.py --all
    python storyworlds/worlds/gpt-5.4/disappoint_tremendous_teamwork_conflict_friendship_fable.py --verify
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

# Make the shared result containers importable when this script is run directly
# from the repo root or from this nested directory.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0
SENSE_MIN = 1


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
        table = {"subject": "they", "object": "them", "possessive": "their"}
        return table[case]


@dataclass
class Animal:
    id: str
    title: str
    phrase: str
    skills: set[str] = field(default_factory=set)
    nature: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Task:
    id: str
    item: str
    place: str
    gather_needs: set[str] = field(default_factory=set)
    carry_needs: set[str] = field(default_factory=set)
    urgency: int = 1
    start_image: str = ""
    ending_image: str = ""
    moral: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Conflict:
    id: str
    boast: str
    sting: str
    wrong: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Repair:
    id: str
    sense: int
    power: int
    opening: str
    promise: str
    qa_text: str
    tags: set[str] = field(default_factory=set)


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

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

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
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_hurt_conflict(world: World) -> list[str]:
    a = world.entities.get("friend1")
    b = world.entities.get("friend2")
    if not a or not b:
        return []
    if a.memes["boast"] < THRESHOLD or b.memes["hurt"] < THRESHOLD:
        return []
    sig = ("conflict", a.id, b.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    a.memes["conflict"] += 1
    b.memes["conflict"] += 1
    return ["__conflict__"]


def _r_apology_softens(world: World) -> list[str]:
    a = world.entities.get("friend1")
    b = world.entities.get("friend2")
    if not a or not b:
        return []
    if a.memes["apology"] < THRESHOLD:
        return []
    sig = ("soften", a.id, b.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    b.memes["trust"] += 1
    b.memes["hurt"] = 0.0
    a.memes["conflict"] = 0.0
    b.memes["conflict"] = 0.0
    return []


def _r_work_completed(world: World) -> list[str]:
    basket = world.entities.get("basket")
    if not basket:
        return []
    if basket.meters["gathered"] < THRESHOLD or basket.meters["carried"] < THRESHOLD:
        return []
    sig = ("stored", basket.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    basket.meters["stored"] += 1
    for ent in world.characters():
        ent.memes["joy"] += 1
        ent.memes["friendship"] += 1
    return ["__stored__"]


CAUSAL_RULES: list[Rule] = [
    Rule(name="hurt_conflict", tag="social", apply=_r_hurt_conflict),
    Rule(name="apology_softens", tag="social", apply=_r_apology_softens),
    Rule(name="work_completed", tag="physical", apply=_r_work_completed),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                out.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for sent in out:
            world.say(sent)
    return out


ANIMALS = {
    "squirrel": Animal(
        id="squirrel",
        title="Squirrel",
        phrase="a bright squirrel with quick paws",
        skills={"climb", "quick"},
        nature="restless and eager",
        tags={"squirrel", "climb"},
    ),
    "beaver": Animal(
        id="beaver",
        title="Beaver",
        phrase="a broad beaver with a patient back",
        skills={"strong", "steady", "swim"},
        nature="slow-spoken and reliable",
        tags={"beaver", "strong", "steady"},
    ),
    "rabbit": Animal(
        id="rabbit",
        title="Rabbit",
        phrase="a rabbit with swift feet and a neat little nose",
        skills={"dig", "quick"},
        nature="fast and excitable",
        tags={"rabbit", "dig"},
    ),
    "turtle": Animal(
        id="turtle",
        title="Turtle",
        phrase="a turtle with a careful shell",
        skills={"steady", "swim"},
        nature="calm and thoughtful",
        tags={"turtle", "steady", "swim"},
    ),
    "crow": Animal(
        id="crow",
        title="Crow",
        phrase="a glossy crow with sharp eyes",
        skills={"fly", "steady"},
        nature="clever and watchful",
        tags={"crow", "fly"},
    ),
    "hedgehog": Animal(
        id="hedgehog",
        title="Hedgehog",
        phrase="a hedgehog with a brave little snout",
        skills={"squeeze", "steady"},
        nature="quiet and stubborn",
        tags={"hedgehog", "squeeze"},
    ),
}

TASKS = {
    "figs": Task(
        id="figs",
        item="a basket of ripe figs",
        place="the high fig tree by the old wall",
        gather_needs={"climb", "fly"},
        carry_needs={"strong", "steady"},
        urgency=1,
        start_image="Purple figs shone high above the grass.",
        ending_image="At the end, the fig basket sat safe in the shade, and the friends ate one soft fig together.",
        moral="Even sweet fruit tastes better when it is earned together.",
        tags={"fruit", "tree"},
    ),
    "turnips": Task(
        id="turnips",
        item="three fat turnips",
        place="the soft patch beside the burrow hill",
        gather_needs={"dig", "squeeze"},
        carry_needs={"strong", "steady"},
        urgency=1,
        start_image="Green tops waved over the earth like little flags.",
        ending_image="At the end, the turnips rested in the meadow store, and the two friends leaned against them, laughing.",
        moral="A buried prize comes up fastest when paws and patience work side by side.",
        tags={"garden", "root"},
    ),
    "reeds": Task(
        id="reeds",
        item="a bundle of river reeds",
        place="the bend where the river pushed against the bank",
        gather_needs={"swim"},
        carry_needs={"strong"},
        urgency=2,
        start_image="The river reeds bowed and hissed in the wind.",
        ending_image="At the end, the reeds stood tied in a neat bundle, ready to mend the little roof before night.",
        moral="When the day is short, quarrels steal more than time.",
        tags={"river", "roof"},
    ),
    "berries": Task(
        id="berries",
        item="a bowl of thorn-hedge berries",
        place="the thorn hedge near the sunny path",
        gather_needs={"fly", "squeeze"},
        carry_needs={"steady"},
        urgency=2,
        start_image="Red berries glowed between the sharp thorns.",
        ending_image="At the end, the berry bowl gleamed like rubies, and the friends watched the sunset with stained smiles.",
        moral="A careful friend can carry what a bold friend can reach.",
        tags={"berries", "thorn"},
    ),
}

CONFLICTS = {
    "boast": Conflict(
        id="boast",
        boast='said, "I can do the whole thing myself."',
        sting="Those words landed harder than a dropped stone.",
        wrong="claimed all the work before the work had even begun",
        tags={"pride"},
    ),
    "snatch": Conflict(
        id="snatch",
        boast='grabbed the basket first and said, "Move aside. You will only slow me down."',
        sting="The snatch made the morning feel cold.",
        wrong="tried to take the task away from a friend",
        tags={"rude"},
    ),
    "blame": Conflict(
        id="blame",
        boast='frowned and said, "If this goes badly, it will be your fault."',
        sting="The blame stung like nettles.",
        wrong="blamed a friend before anything had gone wrong",
        tags={"blame"},
    ),
}

REPAIRS = {
    "apologize": Repair(
        id="apologize",
        sense=2,
        power=3,
        opening='said, "I was wrong. I do not want to disappoint you."',
        promise='said, "Let us do it together, and let the work belong to both of us."',
        qa_text="apologized plainly and asked to work together",
        tags={"apology", "friendship"},
    ),
    "share_credit": Repair(
        id="share_credit",
        sense=1,
        power=2,
        opening='said, "The task is too big for one pair of paws."',
        promise='said, "If we finish, I will speak your name with mine."',
        qa_text="admitted the task needed both of them and offered to share the credit",
        tags={"teamwork", "friendship"},
    ),
    "sulk": Repair(
        id="sulk",
        sense=0,
        power=0,
        opening='muttered without looking up',
        promise='said nothing kind at all',
        qa_text="sulked instead of repairing the friendship",
        tags={"sulk"},
    ),
}


def pair_title(friend1: Animal, friend2: Animal) -> str:
    return f"{friend1.title} and {friend2.title}"


def covers_need(animal_id: str, needed: set[str]) -> bool:
    return bool(ANIMALS[animal_id].skills & needed)


def solo_sufficient(animal_id: str, task_id: str) -> bool:
    task = TASKS[task_id]
    return covers_need(animal_id, task.gather_needs) and covers_need(animal_id, task.carry_needs)


def combined_sufficient(friend1_id: str, friend2_id: str, task_id: str) -> bool:
    task = TASKS[task_id]
    skills = set(ANIMALS[friend1_id].skills) | set(ANIMALS[friend2_id].skills)
    return bool(skills & task.gather_needs) and bool(skills & task.carry_needs)


def task_needs_teamwork(friend1_id: str, friend2_id: str, task_id: str) -> bool:
    if friend1_id == friend2_id:
        return False
    if not combined_sufficient(friend1_id, friend2_id, task_id):
        return False
    if solo_sufficient(friend1_id, task_id) or solo_sufficient(friend2_id, task_id):
        return False
    return True


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for friend1_id in ANIMALS:
        for friend2_id in ANIMALS:
            if friend1_id == friend2_id:
                continue
            for task_id in TASKS:
                if task_needs_teamwork(friend1_id, friend2_id, task_id):
                    combos.append((friend1_id, friend2_id, task_id))
    return combos


def sensible_repairs() -> list[Repair]:
    return [repair for repair in REPAIRS.values() if repair.sense >= SENSE_MIN]


def urgency_value(task_id: str, delay: int) -> int:
    return TASKS[task_id].urgency + delay


def timely_success(repair_id: str, task_id: str, delay: int) -> bool:
    return REPAIRS[repair_id].power >= urgency_value(task_id, delay)


def choose_skill(animal_id: str, needed: set[str]) -> str:
    match = sorted(ANIMALS[animal_id].skills & needed)
    return match[0] if match else ""


def predict_solo_attempt(world: World, task_id: str) -> dict:
    sim = world.copy()
    actor = sim.get("friend1")
    basket = sim.get("basket")
    task = TASKS[task_id]
    if covers_need(actor.attrs["animal_id"], task.gather_needs):
        basket.meters["gathered"] += 1
    if covers_need(actor.attrs["animal_id"], task.carry_needs):
        basket.meters["carried"] += 1
    propagate(sim, narrate=False)
    return {
        "stored": basket.meters["stored"] >= THRESHOLD,
        "missing_gather": not covers_need(actor.attrs["animal_id"], task.gather_needs),
        "missing_carry": not covers_need(actor.attrs["animal_id"], task.carry_needs),
    }


def missing_clause(task: Task, pred: dict) -> str:
    if pred["missing_gather"] and pred["missing_carry"]:
        return "The task needed one friend to reach the prize and another to bring it home safely."
    if pred["missing_gather"]:
        return "One part of the job still needed a friend who could reach the hard place."
    return "One part of the job still needed a friend who could bear the load home safely."


def introduce(world: World, a: Entity, b: Entity, task: Task) -> None:
    world.say(
        f"In a green meadow, {a.id} and {b.id} were friends. "
        f"{a.id} was {a.attrs['nature']}, and {b.id} was {b.attrs['nature']}."
    )
    world.say(
        f"One morning they saw {task.item} at {task.place}. {task.start_image} "
        f"They promised to bring it back before the little field feast."
    )


def spark_conflict(world: World, a: Entity, b: Entity, conflict: Conflict, task_id: str) -> None:
    pred = predict_solo_attempt(world, task_id)
    world.facts["predicted_solo"] = pred
    a.memes["boast"] += 1
    b.memes["hurt"] += 1
    propagate(world, narrate=False)
    world.say(
        f"But before they began, {a.id} {conflict.boast} {conflict.sting}"
    )
    world.say(
        f"{b.id} lowered {b.pronoun('possessive')} head. {missing_clause(TASKS[task_id], pred)}"
    )


def solo_attempt(world: World, a: Entity, task: Task) -> None:
    basket = world.get("basket")
    gather_skill = choose_skill(a.attrs["animal_id"], task.gather_needs)
    carry_skill = choose_skill(a.attrs["animal_id"], task.carry_needs)
    if gather_skill:
        basket.meters["gathered"] += 1
        world.say(f"{a.id} managed the first part with {gather_skill.replace('_', ' ')} skill.")
    else:
        world.say(f"{a.id} rushed to the work, but could not even begin the first part alone.")
    if carry_skill:
        basket.meters["carried"] += 1
        world.say(f"{a.id} also tried to carry the prize home alone.")
    else:
        world.say(f"When it was time to bring the prize home, {a.id} had no sure way to do it alone.")
    if basket.meters["stored"] < THRESHOLD:
        a.memes["disappointment"] += 1
        world.say(
            f"The work stopped halfway, and the lonely attempt began to disappoint even {a.id}."
        )
    propagate(world, narrate=False)


def repair_friendship(world: World, a: Entity, b: Entity, repair: Repair) -> None:
    a.memes["apology"] += 1
    a.memes["humility"] += 1
    propagate(world, narrate=False)
    world.say(
        f"At last {a.id} looked at {b.id} and {repair.opening} Then {a.id} {repair.promise}"
    )
    b.memes["trust"] += 1
    b.memes["friendship"] += 1
    a.memes["friendship"] += 1


def teamwork_success(world: World, a: Entity, b: Entity, task: Task) -> None:
    basket = world.get("basket")
    gatherer = a if covers_need(a.attrs["animal_id"], task.gather_needs) else b
    carrier = a if covers_need(a.attrs["animal_id"], task.carry_needs) else b
    gather_skill = choose_skill(gatherer.attrs["animal_id"], task.gather_needs)
    carry_skill = choose_skill(carrier.attrs["animal_id"], task.carry_needs)
    basket.meters["gathered"] = 1.0
    basket.meters["carried"] = 1.0
    propagate(world, narrate=False)
    world.facts["gatherer"] = gatherer
    world.facts["carrier"] = carrier
    world.facts["gather_skill"] = gather_skill
    world.facts["carry_skill"] = carry_skill
    world.say(
        f"Then the friends worked as friends should. {gatherer.id} used {gather_skill.replace('_', ' ')} skill to win the prize from its place, "
        f"and {carrier.id} used {carry_skill.replace('_', ' ')} strength to bear it home."
    )
    world.say(
        f"The field feast did not see two rivals anymore. It saw one tremendous piece of teamwork."
    )
    world.say(task.ending_image)


def late_end(world: World, a: Entity, b: Entity, task: Task) -> None:
    a.memes["friendship"] += 1
    b.memes["friendship"] += 1
    a.memes["disappointment"] += 1
    b.memes["disappointment"] += 1
    world.say(
        f"The friends made peace, but the sun had already slipped low. They could not finish {task.item} before the feast began."
    )
    world.say(
        f"They sat together instead, sorry for the quarrel and sorry for the lost chance. "
        f"They had not meant to disappoint each other, yet the delay had done exactly that."
    )
    world.say(
        f"Even so, they stayed side by side, and that small faithful choice kept the friendship from growing bitter."
    )


def moral_close(world: World, task: Task, happy: bool) -> None:
    if happy:
        world.say(
            f"And so the meadow learned this: {task.moral}"
        )
    else:
        world.say(
            "And so the meadow learned this: friendship can survive a quarrel, but wasted time does not return."
        )


def tell(friend1_id: str, friend2_id: str, task_id: str, conflict_id: str, repair_id: str, delay: int) -> World:
    world = World()
    a_cfg = ANIMALS[friend1_id]
    b_cfg = ANIMALS[friend2_id]
    task = TASKS[task_id]
    conflict = CONFLICTS[conflict_id]
    repair = REPAIRS[repair_id]

    a = world.add(Entity(
        id=a_cfg.title,
        kind="character",
        type=a_cfg.id,
        label=a_cfg.title,
        phrase=a_cfg.phrase,
        role="friend1",
        attrs={"animal_id": a_cfg.id, "nature": a_cfg.nature},
        tags=set(a_cfg.tags),
    ))
    b = world.add(Entity(
        id=b_cfg.title,
        kind="character",
        type=b_cfg.id,
        label=b_cfg.title,
        phrase=b_cfg.phrase,
        role="friend2",
        attrs={"animal_id": b_cfg.id, "nature": b_cfg.nature},
        tags=set(b_cfg.tags),
    ))
    basket = world.add(Entity(
        id="basket",
        kind="thing",
        type="task",
        label=task.item,
        phrase=task.item,
        tags=set(task.tags),
    ))

    introduce(world, a, b, task)

    world.para()
    spark_conflict(world, a, b, conflict, task_id)
    solo_attempt(world, a, task)

    world.para()
    repair_friendship(world, a, b, repair)
    happy = timely_success(repair_id, task_id, delay)
    if happy:
        teamwork_success(world, a, b, task)
    else:
        late_end(world, a, b, task)

    world.para()
    moral_close(world, task, happy)

    world.facts.update(
        friend1=a,
        friend2=b,
        task=task,
        conflict=conflict,
        repair=repair,
        delay=delay,
        happy=happy,
        outcome="tremendous" if happy else "disappointing",
        basket=basket,
        solo_pred=world.facts.get("predicted_solo", {}),
    )
    return world


@dataclass
class StoryParams:
    friend1: str
    friend2: str
    task: str
    conflict: str
    repair: str
    delay: int = 0
    seed: Optional[int] = None


KNOWLEDGE = {
    "teamwork": [
        (
            "What is teamwork?",
            "Teamwork is when two or more people help each other do one job. Each one does a part, and the parts fit together."
        )
    ],
    "friendship": [
        (
            "What helps a friendship after a quarrel?",
            "A real apology and kind actions help a friendship heal. Saying sorry matters most when you also act better next."
        )
    ],
    "apology": [
        (
            "What is an apology?",
            "An apology is when you admit you were wrong and try to make things better. A good apology is honest and gentle."
        )
    ],
    "squirrel": [
        (
            "What can a squirrel do well?",
            "A squirrel is good at climbing and moving quickly. That helps it reach things high in trees."
        )
    ],
    "beaver": [
        (
            "Why is a beaver useful in hard work?",
            "A beaver is strong and steady. That makes it good at carrying and building."
        )
    ],
    "rabbit": [
        (
            "What is a rabbit good at?",
            "A rabbit is quick, and its paws are good for scratching and digging. That helps with jobs close to the ground."
        )
    ],
    "turtle": [
        (
            "Why can a turtle help with careful work?",
            "A turtle moves carefully and stays steady. That helps when something must be carried without dropping it."
        )
    ],
    "crow": [
        (
            "Why is a crow good at reaching high places?",
            "A crow can fly. Flying lets it reach branches and hedges that ground animals cannot."
        )
    ],
    "hedgehog": [
        (
            "How can a hedgehog help in a tight place?",
            "A hedgehog can squeeze its small body into narrow spaces. That helps it reach things hidden in little gaps."
        )
    ],
    "tree": [
        (
            "Why is a high tree hard for some animals?",
            "A high tree is hard because not every animal can climb or fly to the top. A job there may need a special helper."
        )
    ],
    "river": [
        (
            "Why can a river job be urgent?",
            "A river can rise, bend, and pull at things. If you wait too long, the water or the wind may make the work harder."
        )
    ],
}
KNOWLEDGE_ORDER = [
    "teamwork",
    "friendship",
    "apology",
    "squirrel",
    "beaver",
    "rabbit",
    "turtle",
    "crow",
    "hedgehog",
    "tree",
    "river",
]


CURATED = [
    StoryParams(
        friend1="squirrel",
        friend2="beaver",
        task="figs",
        conflict="boast",
        repair="apologize",
        delay=0,
    ),
    StoryParams(
        friend1="rabbit",
        friend2="turtle",
        task="turnips",
        conflict="snatch",
        repair="share_credit",
        delay=0,
    ),
    StoryParams(
        friend1="crow",
        friend2="hedgehog",
        task="berries",
        conflict="blame",
        repair="share_credit",
        delay=1,
    ),
    StoryParams(
        friend1="turtle",
        friend2="beaver",
        task="reeds",
        conflict="boast",
        repair="apologize",
        delay=2,
    ),
]


def explain_rejection(friend1_id: str, friend2_id: str, task_id: str) -> str:
    if friend1_id == friend2_id:
        return "(No story: a teamwork fable needs two different friends.)"
    if not combined_sufficient(friend1_id, friend2_id, task_id):
        return (
            f"(No story: {ANIMALS[friend1_id].title} and {ANIMALS[friend2_id].title} still do not have the right combined skills for {TASKS[task_id].item}.)"
        )
    return (
        f"(No story: {ANIMALS[friend1_id].title} and {ANIMALS[friend2_id].title} do not truly need each other for {TASKS[task_id].item}. "
        "This world only tells stories where teamwork is necessary, not optional.)"
    )


def explain_repair(repair_id: str) -> str:
    repair = REPAIRS[repair_id]
    better = ", ".join(sorted(r.id for r in sensible_repairs()))
    return (
        f"(Refusing repair '{repair_id}': it scores too low on common sense for healing a friendship "
        f"(sense={repair.sense} < {SENSE_MIN}). Try: {better}.)"
    )


def outcome_of(params: StoryParams) -> str:
    return "tremendous" if timely_success(params.repair, params.task, params.delay) else "disappointing"


ASP_RULES = r"""
animal_has(A, S) :- animal(A), skill(A, S).
covers_gather(A, T) :- animal_has(A, S), gather_need(T, S).
covers_carry(A, T)  :- animal_has(A, S), carry_need(T, S).

solo_ok(A, T) :- covers_gather(A, T), covers_carry(A, T).
combined_ok(A, B, T) :- animal(A), animal(B), A != B,
                        covers_gather(A, T).
combined_ok(A, B, T) :- animal(A), animal(B), A != B,
                        covers_gather(B, T).
combined_carry(A, B, T) :- animal(A), animal(B), A != B,
                           covers_carry(A, T).
combined_carry(A, B, T) :- animal(A), animal(B), A != B,
                           covers_carry(B, T).

valid(A, B, T) :- animal(A), animal(B), task(T), A != B,
                  combined_ok(A, B, T), combined_carry(A, B, T),
                  not solo_ok(A, T), not solo_ok(B, T).

sensible(R) :- repair(R), sense(R, S), sense_min(M), S >= M.

late_value(V) :- chosen_task(T), task_urgency(T, U), delay(D), V = U + D.
success :- chosen_repair(R), repair_power(R, P), late_value(V), P >= V.
outcome(tremendous) :- success.
outcome(disappointing) :- not success.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for animal_id, animal in ANIMALS.items():
        lines.append(asp.fact("animal", animal_id))
        for skill in sorted(animal.skills):
            lines.append(asp.fact("skill", animal_id, skill))
    for task_id, task in TASKS.items():
        lines.append(asp.fact("task", task_id))
        for skill in sorted(task.gather_needs):
            lines.append(asp.fact("gather_need", task_id, skill))
        for skill in sorted(task.carry_needs):
            lines.append(asp.fact("carry_need", task_id, skill))
        lines.append(asp.fact("task_urgency", task_id, task.urgency))
    for repair_id, repair in REPAIRS.items():
        lines.append(asp.fact("repair", repair_id))
        lines.append(asp.fact("sense", repair_id, repair.sense))
        lines.append(asp.fact("repair_power", repair_id, repair.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible_repairs() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_task", params.task),
            asp.fact("chosen_repair", params.repair),
            asp.fact("delay", params.delay),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    a = f["friend1"]
    b = f["friend2"]
    task = f["task"]
    return [
        'Write a short fable for a 3-to-5-year-old that includes the words "disappoint" and "tremendous" and teaches teamwork.',
        f"Tell a fable where {a.id} and {b.id} quarrel over {task.item}, then learn that friendship is stronger than pride.",
        f"Write a gentle animal story with conflict, apology, and a shared task that only two friends together can finish.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a = f["friend1"]
    b = f["friend2"]
    task = f["task"]
    repair = f["repair"]
    conflict = f["conflict"]
    outcome = f["outcome"]
    solo_pred = f.get("solo_pred", {})
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {a.id} and {b.id}, two animal friends who promised to bring back {task.item}. Their friendship is the heart of the fable."
        ),
        (
            f"Why did {a.id} and {b.id} need each other?",
            f"They needed each other because the task had two parts, and one friend alone could not finish both. {missing_clause(task, solo_pred)}"
        ),
        (
            f"What caused the conflict?",
            f"The conflict began when {a.id} {conflict.wrong}. That hurt {b.id}'s feelings and broke the teamwork before the work had even started."
        ),
        (
            f"What happened when {a.id} tried to do the task alone?",
            f"{a.id} could not finish it alone, so the work stopped halfway. That failure showed that pride was weaker than partnership."
        ),
        (
            f"How did {a.id} try to repair the friendship?",
            f"{a.id} {repair.qa_text}. The repair mattered because kind words opened the door for teamwork again."
        ),
    ]
    if outcome == "tremendous":
        gatherer = f.get("gatherer")
        carrier = f.get("carrier")
        gather_skill = f.get("gather_skill", "").replace("_", " ")
        carry_skill = f.get("carry_skill", "").replace("_", " ")
        qa.append(
            (
                "How did the story end?",
                f"It ended happily: {gatherer.id} used {gather_skill} skill, and {carrier.id} used {carry_skill} strength, so the friends finished the task together. Their success was tremendous because it came only after the quarrel was repaired."
            )
        )
    else:
        qa.append(
            (
                "Did the friends fix everything in time?",
                "No. They made peace, but they had delayed too long to finish the work before the feast. The ending is sadder because friendship healed faster than time did."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"teamwork", "friendship"}
    tags |= set(ANIMALS[f["friend1"].attrs["animal_id"]].tags)
    tags |= set(ANIMALS[f["friend2"].attrs["animal_id"]].tags)
    tags |= set(f["repair"].tags)
    tags |= set(f["task"].tags)
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
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.attrs:
            bits.append(f"attrs={ent.attrs}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:10} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Fable story world: teamwork, conflict, friendship, and the cost of pride."
    )
    ap.add_argument("--friend1", choices=ANIMALS)
    ap.add_argument("--friend2", choices=ANIMALS)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--conflict", choices=CONFLICTS)
    ap.add_argument("--repair", choices=REPAIRS)
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], help="extra lateness before the friends make peace")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid teamwork triples from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run smoke tests")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.friend1 and args.friend2 and args.task:
        if not task_needs_teamwork(args.friend1, args.friend2, args.task):
            raise StoryError(explain_rejection(args.friend1, args.friend2, args.task))
    if args.friend1 and args.friend2 and args.friend1 == args.friend2:
        raise StoryError("(No story: a teamwork fable needs two different friends.)")
    if args.repair and REPAIRS[args.repair].sense < SENSE_MIN:
        raise StoryError(explain_repair(args.repair))

    combos = [
        combo
        for combo in valid_combos()
        if (args.friend1 is None or combo[0] == args.friend1)
        and (args.friend2 is None or combo[1] == args.friend2)
        and (args.task is None or combo[2] == args.task)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    friend1_id, friend2_id, task_id = rng.choice(sorted(combos))
    conflict_id = args.conflict or rng.choice(sorted(CONFLICTS))
    repair_id = args.repair or rng.choice(sorted(r.id for r in sensible_repairs()))
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    return StoryParams(
        friend1=friend1_id,
        friend2=friend2_id,
        task=task_id,
        conflict=conflict_id,
        repair=repair_id,
        delay=delay,
    )


def generate(params: StoryParams) -> StorySample:
    if params.friend1 not in ANIMALS or params.friend2 not in ANIMALS:
        raise StoryError("(Invalid animal choice in params.)")
    if params.task not in TASKS:
        raise StoryError("(Invalid task choice in params.)")
    if params.conflict not in CONFLICTS:
        raise StoryError("(Invalid conflict choice in params.)")
    if params.repair not in REPAIRS:
        raise StoryError("(Invalid repair choice in params.)")
    if not task_needs_teamwork(params.friend1, params.friend2, params.task):
        raise StoryError(explain_rejection(params.friend1, params.friend2, params.task))
    if REPAIRS[params.repair].sense < SENSE_MIN:
        raise StoryError(explain_repair(params.repair))

    world = tell(
        friend1_id=params.friend1,
        friend2_id=params.friend2,
        task_id=params.task,
        conflict_id=params.conflict,
        repair_id=params.repair,
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


def asp_verify() -> int:
    rc = 0

    clingo_valid = set(asp_valid_combos())
    python_valid = set(valid_combos())
    if clingo_valid == python_valid:
        print(f"OK: gate matches valid_combos() ({len(clingo_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_valid - python_valid:
            print("  only in clingo:", sorted(clingo_valid - python_valid))
        if python_valid - clingo_valid:
            print("  only in python:", sorted(python_valid - clingo_valid))

    clingo_repairs = set(asp_sensible_repairs())
    python_repairs = {repair.id for repair in sensible_repairs()}
    if clingo_repairs == python_repairs:
        print(f"OK: sensible repairs match ({sorted(clingo_repairs)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible repairs: clingo={sorted(clingo_repairs)} python={sorted(python_repairs)}")

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(40):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
            params.seed = seed
            cases.append(params)
        except StoryError:
            continue
    bad = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("(Smoke test generated an empty story.)")
        emit(sample, trace=False, qa=False, header="")
        print("OK: smoke generation/emit succeeded.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show sensible/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"sensible repairs: {', '.join(asp_sensible_repairs())}\n")
        print(f"{len(combos)} valid (friend1, friend2, task) combos:\n")
        for friend1_id, friend2_id, task_id in combos:
            print(f"  {friend1_id:10} {friend2_id:10} {task_id}")
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
            header = f"### {ANIMALS[p.friend1].title} + {ANIMALS[p.friend2].title}: {p.task} ({p.conflict}, {outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
