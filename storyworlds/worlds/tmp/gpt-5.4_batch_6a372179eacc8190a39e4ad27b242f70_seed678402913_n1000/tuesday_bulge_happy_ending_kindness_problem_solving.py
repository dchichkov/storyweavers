#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/tuesday_bulge_happy_ending_kindness_problem_solving.py
==================================================================================

A standalone storyworld for a small, child-facing comedy about a mysterious
bulge on a Tuesday morning. The tension is gentle: one child notices a funny
bulge in another child's bag or pocket, chooses kindness instead of teasing,
and the odd-looking item turns out to be exactly what is needed to solve a
small school-day problem.

The world model prefers combinations where:
- the hidden object can plausibly make a visible bulge in the chosen container
- the object actually solves the later problem
- the story ends with a concrete act of kindness and a happy image

Run it
------
    python storyworlds/worlds/gpt-5.4/tuesday_bulge_happy_ending_kindness_problem_solving.py
    python storyworlds/worlds/gpt-5.4/tuesday_bulge_happy_ending_kindness_problem_solving.py --container backpack --item tape_roll --problem torn_poster
    python storyworlds/worlds/gpt-5.4/tuesday_bulge_happy_ending_kindness_problem_solving.py --container sweater_pocket --item tape_roll
    python storyworlds/worlds/gpt-5.4/tuesday_bulge_happy_ending_kindness_problem_solving.py --all
    python storyworlds/worlds/gpt-5.4/tuesday_bulge_happy_ending_kindness_problem_solving.py --qa --json
    python storyworlds/worlds/gpt-5.4/tuesday_bulge_happy_ending_kindness_problem_solving.py --verify
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
    traits: list[str] = field(default_factory=list)
    role: str = ""
    owner: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "teacher_f"}
        male = {"boy", "father", "dad", "man", "teacher_m"}
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
            "teacher_f": "teacher",
            "teacher_m": "teacher",
        }.get(self.type, self.type)


@dataclass
class ContainerCfg:
    id: str
    label: str
    phrase: str
    capacity: int = 2
    bulge_threshold: int = 1
    location_text: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class ItemCfg:
    id: str
    label: str
    phrase: str
    size: int = 1
    need: str = ""
    joke: str = ""
    reveal_text: str = ""
    solve_text: str = ""
    flat_after: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class ProblemCfg:
    id: str
    label: str
    phrase: str
    need: str = ""
    trouble_text: str = ""
    helper_text: str = ""
    ending_text: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    container: str
    item: str
    problem: str
    observer_name: str
    observer_gender: str
    carrier_name: str
    carrier_gender: str
    teacher_type: str
    observer_trait: str
    carrier_trait: str
    seed: Optional[int] = None


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


def _r_bulge(world: World) -> list[str]:
    container = world.entities.get("container")
    item = world.entities.get("item")
    carrier = world.entities.get("carrier")
    if container is None or item is None or carrier is None:
        return []
    if item.attrs.get("inside") != "container":
        return []
    size = int(item.attrs.get("size", 0))
    threshold = int(container.attrs.get("bulge_threshold", 99))
    capacity = int(container.attrs.get("capacity", 0))
    if size > capacity or size < threshold:
        return []
    sig = ("bulge", container.id, item.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    container.meters["bulge"] += 1
    carrier.memes["secret"] += 1
    return []


def _r_relief(world: World) -> list[str]:
    problem = world.entities.get("problem")
    if problem is None or problem.meters["solved"] < THRESHOLD:
        return []
    sig = ("relief", problem.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    for ent in world.entities.values():
        if ent.kind == "character":
            ent.memes["relief"] += 1
    return []


CAUSAL_RULES: list[Rule] = [
    Rule(name="bulge", tag="physical", apply=_r_bulge),
    Rule(name="relief", tag="emotional", apply=_r_relief),
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


CONTAINERS = {
    "backpack": ContainerCfg(
        id="backpack",
        label="backpack",
        phrase="a small red backpack",
        capacity=3,
        bulge_threshold=2,
        location_text="on the floor beside the hooks",
        tags={"bag"},
    ),
    "lunch_bag": ContainerCfg(
        id="lunch_bag",
        label="lunch bag",
        phrase="a checkered lunch bag",
        capacity=2,
        bulge_threshold=2,
        location_text="on the lunch shelf",
        tags={"bag", "lunch"},
    ),
    "sweater_pocket": ContainerCfg(
        id="sweater_pocket",
        label="sweater pocket",
        phrase="a deep sweater pocket",
        capacity=1,
        bulge_threshold=1,
        location_text="right on the front of the sweater",
        tags={"pocket", "clothes"},
    ),
}

ITEMS = {
    "tape_roll": ItemCfg(
        id="tape_roll",
        label="tape roll",
        phrase="a fat roll of tape",
        size=2,
        need="repair",
        joke="as if a doughnut had tried to go to school in secret",
        reveal_text="a fat roll of tape",
        solve_text="held out the tape so the torn corners could be fixed",
        flat_after="The bag looked wonderfully ordinary once the round lump was gone.",
        tags={"tape", "repair"},
    ),
    "muffin": ItemCfg(
        id="muffin",
        label="blueberry muffin",
        phrase="an extra blueberry muffin wrapped in a napkin",
        size=2,
        need="snack",
        joke="like a soft hill with crumbs for dreams",
        reveal_text="an extra blueberry muffin wrapped in a napkin",
        solve_text="shared the muffin, breaking it into two soft halves",
        flat_after="After the muffin came out, the bag sagged back down with a little flop.",
        tags={"muffin", "food"},
    ),
    "spare_socks": ItemCfg(
        id="spare_socks",
        label="spare socks",
        phrase="a rolled-up pair of spare socks",
        size=1,
        need="dry",
        joke="like a tiny sleeping hamster made of stripes",
        reveal_text="a rolled-up pair of spare socks",
        solve_text="offered the dry socks right away",
        flat_after="Once the socks were needed, the pocket lay flat again against the sweater.",
        tags={"socks", "dry"},
    ),
}

PROBLEMS = {
    "torn_poster": ProblemCfg(
        id="torn_poster",
        label="torn poster",
        phrase="the class poster",
        need="repair",
        trouble_text="the class poster slipped off the wall and tore right across one corner",
        helper_text="The room went still for one surprised blink.",
        ending_text="Soon the poster hung straight again, and everyone admired the neat shiny patch.",
        tags={"poster", "repair"},
    ),
    "forgotten_snack": ProblemCfg(
        id="forgotten_snack",
        label="forgotten snack",
        phrase="snack time",
        need="snack",
        trouble_text="when snack time came, one little classmate opened an empty lunch box and blinked hard",
        helper_text="Even the crinkly snack shelf seemed to pause.",
        ending_text="Soon there were crumbs, smiles, and a much less worried face at the table.",
        tags={"snack", "food"},
    ),
    "puddle_shoe": ProblemCfg(
        id="puddle_shoe",
        label="wet shoe",
        phrase="after recess",
        need="dry",
        trouble_text="after recess, a child came in with one shoe full of puddle water and a sock that squished",
        helper_text="The squish made such a silly sound that a few children almost laughed, then didn't.",
        ending_text="Soon the wet sock was off, the dry socks were on, and the squishy shoe sat by the heater like a tired boat.",
        tags={"puddle", "socks", "dry"},
    ),
}

GIRL_NAMES = ["Lila", "Mia", "Nora", "Zoe", "Ruby", "Tess", "Ava", "June"]
BOY_NAMES = ["Ben", "Milo", "Theo", "Sam", "Finn", "Leo", "Owen", "Max"]
OBSERVER_TRAITS = ["gentle", "curious", "careful", "kind"]
CARRIER_TRAITS = ["helpful", "quiet", "thoughtful", "eager"]


def solves_problem(item: ItemCfg, problem: ProblemCfg) -> bool:
    return item.need == problem.need


def makes_visible_bulge(container: ContainerCfg, item: ItemCfg) -> bool:
    return item.size <= container.capacity and item.size >= container.bulge_threshold


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for container_id, container in CONTAINERS.items():
        for item_id, item in ITEMS.items():
            for problem_id, problem in PROBLEMS.items():
                if solves_problem(item, problem) and makes_visible_bulge(container, item):
                    combos.append((container_id, item_id, problem_id))
    return combos


def explain_combo(container: ContainerCfg, item: ItemCfg, problem: ProblemCfg) -> str:
    if not solves_problem(item, problem):
        return (
            f"(No story: {item.label} does not solve the {problem.label} problem. "
            f"This world only tells stories where the funny bulge turns out to be a real help.)"
        )
    if item.size > container.capacity:
        return (
            f"(No story: {item.label} is too big for the {container.label}. "
            f"It would not fit naturally there.)"
        )
    if item.size < container.bulge_threshold:
        return (
            f"(No story: {item.label} fits in the {container.label} too neatly, so there would be no visible bulge. "
            f"Pick a softer or smaller container, or a bulkier item.)"
        )
    return "(No story: this combination does not make a reasonable Tuesday bulge story.)"


def introduce(world: World, observer: Entity, carrier: Entity, teacher: Entity, container: ContainerCfg) -> None:
    world.say(
        f"On Tuesday morning, {observer.id} hung up {observer.pronoun('possessive')} coat and noticed "
        f"{carrier.id}'s {container.label} {container.location_text}."
    )
    world.say(
        f"{teacher.id} was writing the date on the board, and the room smelled faintly of crayons and wet mittens."
    )


def notice_bulge(world: World, observer: Entity, carrier: Entity, container_ent: Entity, item: ItemCfg) -> None:
    observer.memes["curiosity"] += 1
    container_ent.meters["noticed"] += 1
    world.say(
        f"There was a bulge in it, a round little bump, {item.joke}."
    )
    world.say(
        f"{observer.id} blinked at it once, then twice, because the bulge looked too funny to ignore."
    )


def ask_kindly(world: World, observer: Entity, carrier: Entity, container: ContainerCfg) -> None:
    observer.memes["kindness"] += 1
    carrier.memes["trust"] += 1
    world.say(
        f'Instead of pointing and laughing, {observer.id} stepped closer and whispered, '
        f'"Are you okay? Your {container.label} has a very surprising bulge."'
    )
    world.say(
        f"{carrier.id} pressed {carrier.pronoun('possessive')} lips together, then smiled a tiny smile."
    )


def hush_secret(world: World, carrier: Entity) -> None:
    carrier.memes["anticipation"] += 1
    world.say(
        f'"It is not a bad bulge," {carrier.id} whispered back. "It is a helping bulge. I was waiting for the right moment."'
    )


def comic_guess(world: World, observer: Entity, carrier: Entity) -> None:
    world.say(
        f'"Please tell me it is not a bowling ball," said {observer.id}.'
    )
    world.say(
        f'{carrier.id} snorted. "If I had a bowling ball, I would already be rolling down the hallway."'
    )


def trouble_appears(world: World, teacher: Entity, problem_ent: Entity, problem: ProblemCfg) -> None:
    problem_ent.meters["active"] += 1
    world.say(
        f"Then, just as {teacher.id} turned around, {problem.trouble_text}."
    )
    world.say(problem.helper_text)


def reveal_solution(world: World, carrier: Entity, container_ent: Entity, item_ent: Entity, item: ItemCfg) -> None:
    item_ent.attrs["inside"] = ""
    container_ent.meters["bulge"] = 0.0
    carrier.memes["shyness"] = 0.0
    carrier.memes["helpfulness"] += 1
    world.say(
        f"{carrier.id}'s eyes widened. \"Now,\" {carrier.pronoun()} said."
    )
    world.say(
        f"{carrier.pronoun().capitalize()} reached into the {container_ent.label} and pulled out {item.reveal_text}."
    )


def solve_problem(world: World, carrier: Entity, observer: Entity, teacher: Entity, problem_ent: Entity,
                  item_ent: Entity, item: ItemCfg, problem: ProblemCfg) -> None:
    item_ent.meters["used"] += 1
    problem_ent.meters["solved"] += 1
    observer.memes["admiration"] += 1
    teacher.memes["gratitude"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{carrier.id} {item.solve_text}."
    )
    world.say(
        f"{observer.id} helped too, and {teacher.id} said, "
        f'"That was thoughtful problem solving. Thank you for being so kind."'
    )
    world.say(problem.ending_text)


def happy_end(world: World, observer: Entity, carrier: Entity, container_ent: Entity, item: ItemCfg) -> None:
    observer.memes["joy"] += 1
    carrier.memes["joy"] += 1
    observer.memes["relief"] += 1
    carrier.memes["relief"] += 1
    world.say(item.flat_after)
    world.say(
        f"{observer.id} grinned. \"So it really was a helping bulge.\""
    )
    world.say(
        f'"The best kind," said {carrier.id}. By lunchtime, the story of the Tuesday bulge had become a class joke, '
        f'and every time someone said the word "bulge," they smiled instead of staring.'
    )


def tell(container: ContainerCfg, item: ItemCfg, problem: ProblemCfg,
         observer_name: str = "Milo", observer_gender: str = "boy",
         carrier_name: str = "June", carrier_gender: str = "girl",
         teacher_type: str = "teacher_f", observer_trait: str = "gentle",
         carrier_trait: str = "helpful") -> World:
    world = World()
    observer = world.add(Entity(
        id=observer_name,
        kind="character",
        type=observer_gender,
        role="observer",
        traits=[observer_trait],
    ))
    carrier = world.add(Entity(
        id=carrier_name,
        kind="character",
        type=carrier_gender,
        role="carrier",
        traits=[carrier_trait],
    ))
    teacher_name = "Ms. Bell" if teacher_type == "teacher_f" else "Mr. Bell"
    teacher = world.add(Entity(
        id=teacher_name,
        kind="character",
        type=teacher_type,
        role="teacher",
        label="the teacher",
    ))
    container_ent = world.add(Entity(
        id="container",
        kind="thing",
        type="container",
        label=container.label,
        phrase=container.phrase,
        owner=carrier.id,
        tags=set(container.tags),
        attrs={
            "capacity": container.capacity,
            "bulge_threshold": container.bulge_threshold,
            "location_text": container.location_text,
        },
    ))
    item_ent = world.add(Entity(
        id="item",
        kind="thing",
        type="item",
        label=item.label,
        phrase=item.phrase,
        owner=carrier.id,
        tags=set(item.tags),
        attrs={
            "inside": "container",
            "size": item.size,
            "need": item.need,
        },
    ))
    problem_ent = world.add(Entity(
        id="problem",
        kind="thing",
        type="problem",
        label=problem.label,
        phrase=problem.phrase,
        tags=set(problem.tags),
        attrs={"need": problem.need},
    ))

    propagate(world, narrate=False)

    introduce(world, observer, carrier, teacher, container)
    notice_bulge(world, observer, carrier, container_ent, item)

    world.para()
    ask_kindly(world, observer, carrier, container)
    hush_secret(world, carrier)
    comic_guess(world, observer, carrier)

    world.para()
    trouble_appears(world, teacher, problem_ent, problem)
    reveal_solution(world, carrier, container_ent, item_ent, item)
    solve_problem(world, carrier, observer, teacher, problem_ent, item_ent, item, problem)

    world.para()
    happy_end(world, observer, carrier, container_ent, item)

    world.facts.update(
        observer=observer,
        carrier=carrier,
        teacher=teacher,
        container_cfg=container,
        item_cfg=item,
        problem_cfg=problem,
        container=container_ent,
        item=item_ent,
        problem=problem_ent,
        solved=problem_ent.meters["solved"] >= THRESHOLD,
        visible_bulge=container_ent.meters["noticed"] >= THRESHOLD,
    )
    return world


KNOWLEDGE = {
    "tape": [
        (
            "What does tape do?",
            "Tape sticks things together or holds them in place. People use it to fix small tears and keep paper from flopping around."
        )
    ],
    "repair": [
        (
            "What does it mean to repair something?",
            "To repair something means to fix it so it works again or looks right again. A small repair can stop a bigger problem."
        )
    ],
    "muffin": [
        (
            "What is a muffin?",
            "A muffin is a small baked snack, a little like a soft cake. It can be shared if someone is hungry."
        )
    ],
    "food": [
        (
            "Why is sharing food kind?",
            "Sharing food can help when someone is hungry or forgot their snack. It shows you are paying attention to another person's needs."
        )
    ],
    "socks": [
        (
            "Why do dry socks feel better than wet socks?",
            "Dry socks feel warm and soft, while wet socks can feel cold and squishy. Changing into dry socks can make someone much more comfortable."
        )
    ],
    "dry": [
        (
            "What can you do when something is wet?",
            "You can dry it gently, change into something dry, or put it somewhere warm and safe. Solving the problem early keeps the rest of the day easier."
        )
    ],
    "puddle": [
        (
            "What is a puddle?",
            "A puddle is a small patch of water on the ground, often left after rain. If you step in it, your shoe or sock can get wet."
        )
    ],
    "poster": [
        (
            "What is a poster?",
            "A poster is a big piece of paper or card with words or pictures on it. Teachers and children hang posters up so everyone can see them."
        )
    ],
    "snack": [
        (
            "What is snack time?",
            "Snack time is a short break when children eat a little food and rest. It helps them have energy for the rest of the day."
        )
    ],
    "bag": [
        (
            "What is a bulge in a bag?",
            "A bulge is a bump that pushes outward because something inside is taking up space. Soft bags show bulges more easily than hard boxes."
        )
    ],
    "pocket": [
        (
            "Why do pockets puff out sometimes?",
            "Pockets puff out when something inside them is bigger or rounder than the cloth around it. The cloth has to stretch around the object."
        )
    ],
}
KNOWLEDGE_ORDER = ["bag", "pocket", "tape", "repair", "muffin", "food", "socks", "dry", "puddle", "poster", "snack"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    observer = f["observer"]
    carrier = f["carrier"]
    item = f["item_cfg"]
    problem = f["problem_cfg"]
    container = f["container_cfg"]
    return [
        'Write a funny, gentle story for a 3-to-5-year-old that includes the words "Tuesday" and "bulge".',
        f"Tell a comedy where {observer.id} notices a strange bulge in {carrier.id}'s {container.label}, asks kindly instead of teasing, and discovers it hides {item.label}.",
        f"Write a happy story about kindness and problem solving where a silly-looking bulge turns out to be just what is needed for {problem.label}.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    observer = f["observer"]
    carrier = f["carrier"]
    teacher = f["teacher"]
    container = f["container_cfg"]
    item = f["item_cfg"]
    problem = f["problem_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "When did the story happen?",
            "It happened on Tuesday morning in the classroom. The day mattered because the children later joked about the 'Tuesday bulge.'"
        ),
        (
            f"What did {observer.id} notice?",
            f"{observer.id} noticed a funny bulge in {carrier.id}'s {container.label}. It looked so odd that {observer.pronoun()} stopped to stare, but {observer.pronoun()} chose to ask kindly instead of making fun."
        ),
        (
            f"Why was {carrier.id} carrying {item.label}?",
            f"{carrier.id} was carrying it to help with a problem if one came up. The bulge looked silly from the outside, but the object inside had a useful job."
        ),
        (
            f"What problem happened later?",
            f"Later, {problem.trouble_text}. That was the exact moment when the strange bulge finally made sense."
        ),
        (
            f"How did the children solve the problem?",
            f"{carrier.id} pulled out {item.reveal_text} and used it to help. Then {observer.id} joined in, so the solution became both problem solving and kindness."
        ),
        (
            f"What did {teacher.id} think?",
            f"{teacher.id} was pleased and thankful. {teacher.pronoun().capitalize()} praised the children for being thoughtful instead of mean and for helping quickly."
        ),
        (
            "How did the story end?",
            f"It ended happily, with the problem solved and the famous bulge gone. The silly bump became a class joke because it had led to something kind."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["container_cfg"].tags) | set(world.facts["item_cfg"].tags) | set(world.facts["problem_cfg"].tags)
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
    for ent in world.entities.values():
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v or isinstance(v, int)}
            if shown:
                bits.append(f"attrs={shown}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:10} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
solves_problem(I, P) :- item(I), problem(P), fixes_need(I, N), problem_need(P, N).
bulge_ok(C, I) :- container(C), item(I), item_size(I, S), capacity(C, Cap), S <= Cap,
                  bulge_threshold(C, Th), S >= Th.
valid(C, I, P) :- container(C), item(I), problem(P), solves_problem(I, P), bulge_ok(C, I).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for cid, c in CONTAINERS.items():
        lines.append(asp.fact("container", cid))
        lines.append(asp.fact("capacity", cid, c.capacity))
        lines.append(asp.fact("bulge_threshold", cid, c.bulge_threshold))
    for iid, item in ITEMS.items():
        lines.append(asp.fact("item", iid))
        lines.append(asp.fact("item_size", iid, item.size))
        lines.append(asp.fact("fixes_need", iid, item.need))
    for pid, problem in PROBLEMS.items():
        lines.append(asp.fact("problem", pid))
        lines.append(asp.fact("problem_need", pid, problem.need))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: ASP gate matches valid_combos() ({len(python_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))

    smoke_cases = list(CURATED)
    parser = build_parser()
    for seed in range(20):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
        except StoryError:
            continue
        smoke_cases.append(params)

    bad = 0
    for params in smoke_cases:
        try:
            sample = generate(params)
            if not sample.story.strip():
                raise StoryError("empty story")
            if "{" in sample.story or "}" in sample.story:
                raise StoryError("unresolved brace in story")
            if params.container not in sample.story and "bulge" not in sample.story.lower():
                raise StoryError("story missed the core premise")
        except Exception as err:
            bad += 1
            print(f"SMOKE FAIL for {params}: {err}")
    if bad == 0:
        print(f"OK: smoke-tested generation on {len(smoke_cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(smoke_cases)} smoke tests failed.")
    return rc


CURATED = [
    StoryParams(
        container="backpack",
        item="tape_roll",
        problem="torn_poster",
        observer_name="Milo",
        observer_gender="boy",
        carrier_name="June",
        carrier_gender="girl",
        teacher_type="teacher_f",
        observer_trait="gentle",
        carrier_trait="helpful",
    ),
    StoryParams(
        container="lunch_bag",
        item="muffin",
        problem="forgotten_snack",
        observer_name="Ruby",
        observer_gender="girl",
        carrier_name="Ben",
        carrier_gender="boy",
        teacher_type="teacher_m",
        observer_trait="kind",
        carrier_trait="thoughtful",
    ),
    StoryParams(
        container="sweater_pocket",
        item="spare_socks",
        problem="puddle_shoe",
        observer_name="Theo",
        observer_gender="boy",
        carrier_name="Ava",
        carrier_gender="girl",
        teacher_type="teacher_f",
        observer_trait="careful",
        carrier_trait="eager",
    ),
    StoryParams(
        container="backpack",
        item="muffin",
        problem="forgotten_snack",
        observer_name="Zoe",
        observer_gender="girl",
        carrier_name="Finn",
        carrier_gender="boy",
        teacher_type="teacher_m",
        observer_trait="curious",
        carrier_trait="helpful",
    ),
    StoryParams(
        container="backpack",
        item="tape_roll",
        problem="torn_poster",
        observer_name="Nora",
        observer_gender="girl",
        carrier_name="Sam",
        carrier_gender="boy",
        teacher_type="teacher_f",
        observer_trait="gentle",
        carrier_trait="quiet",
    ),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Storyworld: a funny Tuesday bulge becomes a kind solution."
    )
    ap.add_argument("--container", choices=CONTAINERS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--observer-name")
    ap.add_argument("--carrier-name")
    ap.add_argument("--observer-gender", choices=["girl", "boy"])
    ap.add_argument("--carrier-gender", choices=["girl", "boy"])
    ap.add_argument("--teacher-type", choices=["teacher_f", "teacher_m"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid (container, item, problem) combos from ASP")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    names = [n for n in pool if n != avoid]
    return rng.choice(names)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.container and args.item and args.problem:
        container = CONTAINERS[args.container]
        item = ITEMS[args.item]
        problem = PROBLEMS[args.problem]
        if not (solves_problem(item, problem) and makes_visible_bulge(container, item)):
            raise StoryError(explain_combo(container, item, problem))

    combos = [
        combo for combo in valid_combos()
        if (args.container is None or combo[0] == args.container)
        and (args.item is None or combo[1] == args.item)
        and (args.problem is None or combo[2] == args.problem)
    ]
    if not combos:
        if args.container and args.item and args.problem:
            raise StoryError(explain_combo(CONTAINERS[args.container], ITEMS[args.item], PROBLEMS[args.problem]))
        raise StoryError("(No valid combination matches the given options.)")

    container_id, item_id, problem_id = rng.choice(sorted(combos))
    observer_gender = args.observer_gender or rng.choice(["girl", "boy"])
    carrier_gender = args.carrier_gender or rng.choice(["girl", "boy"])
    observer_name = args.observer_name or _pick_name(rng, observer_gender)
    carrier_name = args.carrier_name or _pick_name(rng, carrier_gender, avoid=observer_name)
    teacher_type = args.teacher_type or rng.choice(["teacher_f", "teacher_m"])
    observer_trait = rng.choice(OBSERVER_TRAITS)
    carrier_trait = rng.choice(CARRIER_TRAITS)
    return StoryParams(
        container=container_id,
        item=item_id,
        problem=problem_id,
        observer_name=observer_name,
        observer_gender=observer_gender,
        carrier_name=carrier_name,
        carrier_gender=carrier_gender,
        teacher_type=teacher_type,
        observer_trait=observer_trait,
        carrier_trait=carrier_trait,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        container = CONTAINERS[params.container]
        item = ITEMS[params.item]
        problem = PROBLEMS[params.problem]
    except KeyError as err:
        raise StoryError(f"(Invalid parameter value: {err})") from err

    if not solves_problem(item, problem) or not makes_visible_bulge(container, item):
        raise StoryError(explain_combo(container, item, problem))

    world = tell(
        container=container,
        item=item,
        problem=problem,
        observer_name=params.observer_name,
        observer_gender=params.observer_gender,
        carrier_name=params.carrier_name,
        carrier_gender=params.carrier_gender,
        teacher_type=params.teacher_type,
        observer_trait=params.observer_trait,
        carrier_trait=params.carrier_trait,
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
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (container, item, problem) combos:\n")
        for container, item, problem in combos:
            print(f"  {container:14} {item:12} {problem}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        for params in CURATED:
            samples.append(generate(params))
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
            header = f"### {p.observer_name} and {p.carrier_name}: {p.item} in {p.container} for {p.problem}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
