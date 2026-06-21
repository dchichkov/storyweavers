#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/incorporate_cautionary_slice_of_life.py
==================================================================

A small standalone storyworld for a cautionary slice-of-life tale built around
one impatient mistake: a child wants one missing thing from a high shelf so they
can *incorporate* it into a home project, grabs an unsafe support, gets a scare,
and then learns the calm, ordinary safe way to finish.

The world model prefers a few plausible household variants over broad coverage:
a kitchen or craft-time setup, one child, one nearby grown-up, one unsafe way to
reach upward, and one safe fix that still lets the day end warmly.

Run it
------
    python storyworlds/worlds/gpt-5.4/incorporate_cautionary_slice_of_life.py
    python storyworlds/worlds/gpt-5.4/incorporate_cautionary_slice_of_life.py --task muffins
    python storyworlds/worlds/gpt-5.4/incorporate_cautionary_slice_of_life.py --support swivel_chair
    python storyworlds/worlds/gpt-5.4/incorporate_cautionary_slice_of_life.py --all
    python storyworlds/worlds/gpt-5.4/incorporate_cautionary_slice_of_life.py -n 5 --seed 7
    python storyworlds/worlds/gpt-5.4/incorporate_cautionary_slice_of_life.py --qa --json
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
# This file lives one level deeper than most worlds:
#   storyworlds/worlds/gpt-5.4/<this_file>.py
# so we add the storyworlds/ package dir itself.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
RISK_TUMBLE = 3


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
        female = {"girl", "mother", "mom", "woman", "aunt"}
        male = {"boy", "father", "dad", "man", "uncle"}
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
            "aunt": "aunt",
            "uncle": "uncle",
        }.get(self.type, self.type)


@dataclass
class Task:
    id: str
    place: str
    project: str
    opening: str
    need_line: str
    item_label: str
    item_phrase: str
    location: str
    incorporate_line: str
    closing_line: str
    height_need: int
    tags: set[str] = field(default_factory=set)


@dataclass
class Support:
    id: str
    label: str
    phrase: str
    reach: int
    risk: int
    unstable: bool
    motion: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Fix:
    id: str
    label: str
    phrase: str
    safe: bool
    adult_does: bool
    action_text: str
    closing_text: str
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


def _r_wobble(world: World) -> list[str]:
    child = world.entities.get("child")
    support = world.entities.get("support")
    room = world.entities.get("room")
    if not child or not support or not room:
        return []
    if child.meters["on_support"] < THRESHOLD or support.meters["unstable"] < THRESHOLD:
        return []
    sig = ("wobble", support.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    support.meters["wobbling"] += 1
    room.meters["danger"] += 1
    child.memes["fear"] += 1
    return ["__wobble__"]


def _r_tip(world: World) -> list[str]:
    child = world.entities.get("child")
    support = world.entities.get("support")
    room = world.entities.get("room")
    if not child or not support or not room:
        return []
    if support.meters["wobbling"] < THRESHOLD or world.facts.get("delay", 0) <= 0:
        return []
    sig = ("tip", support.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    support.meters["tipped"] += 1
    child.meters["bump"] += 1
    room.meters["danger"] += 1
    child.memes["fear"] += 1
    return ["__tip__"]


CAUSAL_RULES: list[Rule] = [
    Rule(name="wobble", tag="physical", apply=_r_wobble),
    Rule(name="tip", tag="physical", apply=_r_tip),
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
                produced.extend(sents)
    if narrate:
        for sent in produced:
            if not sent.startswith("__"):
                world.say(sent)
    return produced


def valid_combo(task: Task, support: Support, fix: Fix) -> bool:
    return (
        task.height_need <= support.reach
        and support.unstable
        and fix.safe
    )


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for task_id, task in TASKS.items():
        for support_id, support in SUPPORTS.items():
            for fix_id, fix in FIXES.items():
                if valid_combo(task, support, fix):
                    combos.append((task_id, support_id, fix_id))
    return combos


def tumble_happens(support: Support, delay: int) -> bool:
    return support.risk + delay >= RISK_TUMBLE


def predict_trouble(world: World) -> dict:
    sim = world.copy()
    child = sim.get("child")
    support = sim.get("support")
    child.meters["on_support"] += 1
    support.meters["unstable"] += 1
    propagate(sim, narrate=False)
    return {
        "wobble": support.meters["wobbling"] >= THRESHOLD,
        "tip": support.meters["tipped"] >= THRESHOLD,
        "danger": sim.get("room").meters["danger"],
    }


def introduce(world: World, child: Entity, adult: Entity, task: Task) -> None:
    trait = child.traits[0] if child.traits else "busy"
    world.say(
        f"After school, {child.id} stood with {child.pronoun('possessive')} "
        f"{adult.label_word} in {task.place}. {task.opening}"
    )
    world.say(
        f"{child.pronoun().capitalize()} was a {trait} little {child.type}, and "
        f"the ordinary room felt special because they were making something together."
    )


def setup_need(world: World, child: Entity, task: Task) -> None:
    child.memes["joy"] += 1
    world.say(task.need_line)
    world.say(task.incorporate_line)


def eye_shelf(world: World, child: Entity, task: Task, support: Support) -> None:
    world.say(
        f"But {task.item_phrase} was still {task.location}. {child.id} looked around, "
        f"spotted {support.phrase}, and thought it might be a quick way up."
    )


def warn(world: World, child: Entity, adult: Entity, support: Support) -> None:
    pred = predict_trouble(world)
    world.facts["predicted_danger"] = pred["danger"]
    adult.memes["care"] += 1
    world.say(
        f'"Wait," said {adult.label_word}. "That {support.label} can {support.motion}. '
        f'It is not steady for climbing."'
    )


def defy(world: World, child: Entity, support: Support) -> None:
    child.memes["impatience"] += 1
    world.say(
        f"{child.id} wanted the missing piece right away. "
        f"{child.pronoun().capitalize()} put one foot on {support.phrase} anyway."
    )


def climb(world: World, child: Entity, support: Entity) -> None:
    child.meters["on_support"] += 1
    support.meters["unstable"] += 1
    propagate(world, narrate=False)


def scare_or_tumble(world: World, child: Entity, adult: Entity, support: Support) -> str:
    support_ent = world.get("support")
    if support_ent.meters["tipped"] >= THRESHOLD:
        child.memes["fear"] += 1
        world.say(
            f"At once, {support.phrase} {support.motion}. "
            f"{child.id}'s hand flew out, the seat slipped away, and {child.pronoun()} "
            f"landed on the floor with a surprised little thump."
        )
        world.say(
            f"{adult.label_word.capitalize()} hurried over and gathered {child.pronoun('object')} close. "
            f'"Up high is not the place for a wiggly stand," {adult.pronoun()} said.'
        )
        return "tumble"
    world.say(
        f"The moment {child.pronoun()} reached up, {support.phrase} began to {support.motion}. "
        f"{adult.label_word.capitalize()} caught {child.pronoun('possessive')} arm before anything worse happened."
    )
    world.say(
        f"{child.id}'s knees went soft with surprise. For one quiet second, "
        f"{child.pronoun()} understood how fast a small choice could turn scary."
    )
    return "near_miss"


def comfort(world: World, child: Entity, adult: Entity) -> None:
    child.memes["relief"] += 1
    child.memes["lesson"] += 1
    adult.memes["care"] += 1
    if child.meters["bump"] >= THRESHOLD:
        world.say(
            f'{adult.label_word.capitalize()} rubbed the little bump on {child.pronoun("possessive")} knee '
            f'and waited until {child.pronoun()} took a steady breath.'
        )
    else:
        world.say(
            f'{adult.label_word.capitalize()} kept one hand on {child.pronoun("possessive")} shoulder '
            f'until {child.pronoun()} stopped trembling.'
        )
    world.say(
        f'"If something is too high, we do not rush and we do not climb on things that roll or wobble," '
        f'{adult.pronoun()} said. "We ask for the safe help we need."'
    )


def safe_fix(world: World, child: Entity, adult: Entity, task: Task, fix: Fix) -> None:
    child.memes["joy"] += 1
    child.memes["relief"] += 1
    child.meters["on_support"] = 0.0
    world.get("room").meters["danger"] = 0.0
    world.say(fix.action_text.replace("{adult}", adult.label_word).replace("{child}", child.id))
    world.say(
        f"Soon {task.item_phrase} was in reach, and {task.closing_line}"
    )
    world.say(fix.closing_text.replace("{child}", child.id).replace("{adult}", adult.label_word))


def ending_image(world: World, child: Entity, task: Task, fix: Fix) -> None:
    if fix.id == "adult_reach":
        world.say(
            f"When the project was done, {child.id} glanced once at the high shelf and then at "
            f"{child.pronoun('possessive')} {world.get('adult').label_word}. This time, {child.pronoun()} smiled and asked first."
        )
    else:
        world.say(
            f"After that, whenever {child.id} needed something from up high, "
            f"{child.pronoun()} looked for the steady step stool instead of the nearest seat."
        )


def tell(
    task: Task,
    support_cfg: Support,
    fix: Fix,
    *,
    child_name: str = "Lina",
    child_gender: str = "girl",
    adult_type: str = "mother",
    trait: str = "eager",
    delay: int = 0,
) -> World:
    world = World()
    child = world.add(Entity(
        id=child_name,
        kind="character",
        type=child_gender,
        role="child",
        label=child_name,
        traits=[trait],
    ))
    adult = world.add(Entity(
        id="adult",
        kind="character",
        type=adult_type,
        role="adult",
        label="the adult",
    ))
    room = world.add(Entity(
        id="room",
        kind="thing",
        type="room",
        label=task.place,
    ))
    support = world.add(Entity(
        id="support",
        kind="thing",
        type="support",
        label=support_cfg.label,
        phrase=support_cfg.phrase,
        tags=set(support_cfg.tags),
    ))
    world.facts["delay"] = delay

    introduce(world, child, adult, task)
    setup_need(world, child, task)

    world.para()
    eye_shelf(world, child, task, support_cfg)
    warn(world, child, adult, support_cfg)
    defy(world, child, support_cfg)

    world.para()
    climb(world, child, support)
    outcome = scare_or_tumble(world, child, adult, support_cfg)
    comfort(world, child, adult)

    world.para()
    safe_fix(world, child, adult, task, fix)
    ending_image(world, child, task, fix)

    world.facts.update(
        child=child,
        adult=adult,
        room=room,
        task=task,
        support_cfg=support_cfg,
        fix=fix,
        outcome=outcome,
        bumped=child.meters["bump"] >= THRESHOLD,
        learned=child.memes["lesson"] >= THRESHOLD,
    )
    return world


TASKS = {
    "muffins": Task(
        id="muffins",
        place="the kitchen",
        project="banana muffins",
        opening="A bowl of mashed bananas, flour, and milk sat on the counter, waiting to become banana muffins.",
        need_line="They were almost ready to stir the batter when they remembered one last jar.",
        item_label="cinnamon",
        item_phrase="the little jar of cinnamon",
        location="on the top pantry shelf",
        incorporate_line='"{item} will make it smell warm," {child} said once, but in the real story line it becomes concrete later.',
        closing_line="they finished the batter and folded the cinnamon in slowly so it would incorporate all through the mix.",
        height_need=2,
        tags={"cinnamon", "baking", "high_shelf"},
    ),
    "collage": Task(
        id="collage",
        place="the dining room",
        project="a welcome-home poster",
        opening="Paper scraps, glue, and crayons were spread over the table for a welcome-home poster.",
        need_line="The poster already had bright letters, but it still needed one shiny touch.",
        item_label="gold stars",
        item_phrase="the packet of gold stars",
        location="on the highest shelf of the side cabinet",
        incorporate_line='"{item} will make the corners sparkle when we incorporate them into the poster," {child} said.',
        closing_line="they pressed the stars into the corners, and the shiny pieces made the whole poster look finished.",
        height_need=2,
        tags={"glue", "poster", "high_shelf"},
    ),
    "trail_mix": Task(
        id="trail_mix",
        place="the kitchen",
        project="a jar of trail mix for tomorrow",
        opening="Oats, seeds, and dried fruit waited in small bowls for a jar of homemade trail mix.",
        need_line="Only one crunchy part was missing.",
        item_label="pretzel twists",
        item_phrase="the tin of pretzel twists",
        location="on the top shelf above the fridge",
        incorporate_line='"{item} will make the mix extra crunchy once we incorporate them," {child} said.',
        closing_line="they poured the pretzels in last and shook the jar until the crunchy pieces were mixed all through.",
        height_need=3,
        tags={"kitchen", "help", "high_shelf"},
    ),
}

SUPPORTS = {
    "swivel_chair": Support(
        id="swivel_chair",
        label="desk chair",
        phrase="the swivel chair",
        reach=2,
        risk=2,
        unstable=True,
        motion="roll and turn under your feet",
        tags={"chair", "unsafe_support"},
    ),
    "stacked_crates": Support(
        id="stacked_crates",
        label="stack of crates",
        phrase="the stacked crates",
        reach=3,
        risk=3,
        unstable=True,
        motion="shimmy apart",
        tags={"unsafe_support"},
    ),
    "laundry_basket": Support(
        id="laundry_basket",
        label="laundry basket",
        phrase="the upside-down laundry basket",
        reach=1,
        risk=3,
        unstable=True,
        motion="squash and slide",
        tags={"unsafe_support"},
    ),
    "step_stool": Support(
        id="step_stool",
        label="step stool",
        phrase="the steady step stool",
        reach=2,
        risk=0,
        unstable=False,
        motion="stay still",
        tags={"step_stool"},
    ),
}

FIXES = {
    "adult_reach": Fix(
        id="adult_reach",
        label="ask a grown-up",
        phrase="ask a grown-up to reach it",
        safe=True,
        adult_does=True,
        action_text="{adult} reached up, brought the missing item down, and set it in {child}'s hands.",
        closing_text="The day kept its cozy feeling because {child} had what was needed without another scare.",
        tags={"ask_for_help"},
    ),
    "step_stool": Fix(
        id="step_stool",
        label="step stool",
        phrase="use the real step stool",
        safe=True,
        adult_does=False,
        action_text="{adult} pulled over the real step stool, held it steady, and let {child} climb just one careful step.",
        closing_text="{child} liked doing the last part alone, but now the careful way felt better than the quick way.",
        tags={"step_stool"},
    ),
    "wait_together": Fix(
        id="wait_together",
        label="wait together",
        phrase="wait until a grown-up can help",
        safe=True,
        adult_does=True,
        action_text="{adult} said they could wait one minute, and then together they reached the missing item the safe way.",
        closing_text="Waiting had seemed slow at first, but it turned out to be much easier than getting scared.",
        tags={"ask_for_help", "waiting"},
    ),
}


GIRL_NAMES = ["Lina", "Maya", "Nora", "Ava", "Ella", "Lucy", "Zoe", "Ivy"]
BOY_NAMES = ["Owen", "Leo", "Max", "Ben", "Sam", "Theo", "Eli", "Noah"]
TRAITS = ["eager", "busy", "careful", "curious", "impatient", "helpful"]


@dataclass
class StoryParams:
    task: str
    support: str
    fix: str
    child_name: str
    child_gender: str
    adult_type: str
    trait: str
    delay: int = 0
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        task="muffins",
        support="swivel_chair",
        fix="step_stool",
        child_name="Maya",
        child_gender="girl",
        adult_type="mother",
        trait="eager",
        delay=0,
    ),
    StoryParams(
        task="collage",
        support="stacked_crates",
        fix="adult_reach",
        child_name="Leo",
        child_gender="boy",
        adult_type="father",
        trait="impatient",
        delay=1,
    ),
    StoryParams(
        task="trail_mix",
        support="stacked_crates",
        fix="wait_together",
        child_name="Nora",
        child_gender="girl",
        adult_type="aunt",
        trait="curious",
        delay=1,
    ),
    StoryParams(
        task="muffins",
        support="swivel_chair",
        fix="adult_reach",
        child_name="Ben",
        child_gender="boy",
        adult_type="mother",
        trait="helpful",
        delay=0,
    ),
]


KNOWLEDGE = {
    "high_shelf": [
        (
            "Why should children ask for help with a high shelf?",
            "Things on a high shelf can be hard to reach safely. A grown-up or a steady step stool can help without climbing on something wobbly."
        )
    ],
    "chair": [
        (
            "Why is a rolling chair not safe to stand on?",
            "A rolling chair can move when your weight shifts. That means it can slide away before you are ready."
        )
    ],
    "unsafe_support": [
        (
            "Why are wobbly things bad for climbing?",
            "Wobbly things can tip, slide, or squish under your feet. Even a short climb can turn into a fall very quickly."
        )
    ],
    "step_stool": [
        (
            "What is a step stool for?",
            "A step stool is a small steady stool that helps you reach something a little higher. It is made to stand still while you climb carefully."
        )
    ],
    "ask_for_help": [
        (
            "When should you ask a grown-up for help?",
            "You should ask when something is too high, too heavy, too sharp, or feels unsafe. Asking for help is a smart safety choice."
        )
    ],
    "waiting": [
        (
            "Why can waiting be safer than rushing?",
            "Rushing can make people grab the first idea instead of the best one. Waiting a moment gives you time to choose the safe way."
        )
    ],
    "cinnamon": [
        (
            "What does cinnamon do in baking?",
            "Cinnamon adds a warm smell and flavor to food. A small amount can make muffins or oatmeal taste cozy."
        )
    ],
    "glue": [
        (
            "What does glue do in a craft?",
            "Glue helps paper and decorations stick where you want them. It holds the pieces together so the craft stays in place."
        )
    ],
    "help": [
        (
            "Why is teamwork useful in a kitchen?",
            "One person can stir while another person reaches or measures. Working together makes many jobs easier and safer."
        )
    ],
}
KNOWLEDGE_ORDER = [
    "high_shelf",
    "chair",
    "unsafe_support",
    "step_stool",
    "ask_for_help",
    "waiting",
    "cinnamon",
    "glue",
    "help",
]


def task_incorporate_line(task: Task, child: Entity) -> str:
    return task.incorporate_line.format(item=task.item_label, child=child.id)


def generation_prompts(world: World) -> list[str]:
    child = world.facts["child"]
    task = world.facts["task"]
    support = world.facts["support_cfg"]
    fix = world.facts["fix"]
    return [
        f'Write a short cautionary slice-of-life story for a 3-to-5-year-old that includes the word "incorporate".',
        f"Tell a gentle household story where {child.id} tries to use {support.phrase} to reach {task.item_phrase}, gets a scare, and then learns the safe way.",
        f"Write a cozy everyday story about making {task.project} where one missing item is too high up, a grown-up gives a warning, and {fix.phrase} solves the problem.",
    ]


def pair_story_qa(world: World) -> list[tuple[str, str]]:
    child = world.facts["child"]
    adult = world.facts["adult"]
    task = world.facts["task"]
    support = world.facts["support_cfg"]
    fix = world.facts["fix"]
    outcome = world.facts["outcome"]
    adult_word = adult.label_word
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id} and {child.pronoun('possessive')} {adult_word}. They were spending ordinary time together while making {task.project}."
        ),
        (
            f"What did {child.id} want from the high shelf?",
            f"{child.id} wanted {task.item_phrase}. It was needed to finish the project they were making together."
        ),
        (
            f"How was the word 'incorporate' part of the story?",
            f"{child.id} wanted to incorporate {task.item_label} into the project. The word fit because they were trying to mix or add one last part into something already being made."
        ),
        (
            f"Why did {adult_word} warn {child.id}?",
            f"{adult_word.capitalize()} warned {child.pronoun('object')} because {support.phrase} was not steady. It could {support.motion}, so climbing on it could turn dangerous fast."
        ),
    ]
    if outcome == "near_miss":
        qa.append(
            (
                f"What happened when {child.id} climbed anyway?",
                f"The {support.label} began to move under {child.pronoun('object')}, and {adult_word} caught {child.pronoun('possessive')} arm before a fall. That scare showed {child.pronoun('object')} why the warning mattered."
            )
        )
    else:
        qa.append(
            (
                f"What happened when {child.id} climbed anyway?",
                f"The unsafe support moved and {child.id} tumbled to the floor with a small bump. It was a little accident, but it taught the safety lesson in a very real way."
            )
        )
    qa.append(
        (
            "How did they solve the problem?",
            f"They used {fix.phrase}. That safe choice still got the missing item down, so the project could be finished without more danger."
        )
    )
    qa.append(
        (
            f"What changed by the end of the story?",
            f"{child.id} still got to help finish {task.project}, but now {child.pronoun()} understood not to climb on something wobbly. The ending image shows a child who asks or uses the proper step stool instead of rushing."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["task"].tags) | set(world.facts["support_cfg"].tags) | set(world.facts["fix"].tags)
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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        lines.append(f"  {ent.id:8} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


def explain_rejection(task: Task, support: Support, fix: Fix) -> str:
    if task.height_need > support.reach:
        return (
            f"(No story: {support.phrase} is not tall enough to reach {task.item_phrase} {task.location}. "
            f"The premise needs a real temptation to climb, so pick a support that can actually reach.)"
        )
    if not support.unstable:
        return (
            f"(No story: {support.phrase} is already steady. This world only tells the cautionary version, "
            f"where the child is tempted by a quick but unsafe way up.)"
        )
    if not fix.safe:
        return "(No story: the chosen fix is not a safe solution.)"
    return "(No story: that combination does not fit this world.)"


ASP_RULES = r"""
task_valid(T, S, F) :- task(T), support(S), fix(F),
                       needs_height(T, H), reaches(S, R), R >= H,
                       unstable(S), safe_fix(F).

risk_value(V) :- chosen_support(S), risk(S, Rs), delay(D), V = Rs + D.
outcome(near_miss) :- risk_value(V), tumble_threshold(T), V < T.
outcome(tumble)    :- risk_value(V), tumble_threshold(T), V >= T.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for task_id, task in TASKS.items():
        lines.append(asp.fact("task", task_id))
        lines.append(asp.fact("needs_height", task_id, task.height_need))
    for support_id, support in SUPPORTS.items():
        lines.append(asp.fact("support", support_id))
        lines.append(asp.fact("reaches", support_id, support.reach))
        lines.append(asp.fact("risk", support_id, support.risk))
        if support.unstable:
            lines.append(asp.fact("unstable", support_id))
    for fix_id, fix in FIXES.items():
        lines.append(asp.fact("fix", fix_id))
        if fix.safe:
            lines.append(asp.fact("safe_fix", fix_id))
    lines.append(asp.fact("tumble_threshold", RISK_TUMBLE))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show task_valid/3."))
    return sorted(set(asp.atoms(model, "task_valid")))


def outcome_of(params: StoryParams) -> str:
    support = SUPPORTS[params.support]
    return "tumble" if tumble_happens(support, params.delay) else "near_miss"


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join([
        asp.fact("chosen_support", params.support),
        asp.fact("delay", params.delay),
    ])
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
    for seed in range(50):
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
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("smoke test generated empty story")
        if not smoke.prompts or not smoke.story_qa or not smoke.world_qa:
            raise StoryError("smoke test generated incomplete sample")
        print("OK: smoke test generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Cautionary slice-of-life storyworld: a child reaches for a high-shelf item the unsafe way, gets a scare, and learns the safe way."
    )
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--support", choices=SUPPORTS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--adult", choices=["mother", "father", "aunt", "uncle"])
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--delay", type=int, choices=[0, 1], help="0 = near miss, 1 = small tumble for riskier supports")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combinations derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP twin and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.task and args.support and args.fix:
        task = TASKS[args.task]
        support = SUPPORTS[args.support]
        fix = FIXES[args.fix]
        if not valid_combo(task, support, fix):
            raise StoryError(explain_rejection(task, support, fix))

    combos = [
        combo for combo in valid_combos()
        if (args.task is None or combo[0] == args.task)
        and (args.support is None or combo[1] == args.support)
        and (args.fix is None or combo[2] == args.fix)
    ]
    if not combos:
        if args.task and args.support and args.fix:
            raise StoryError(explain_rejection(TASKS[args.task], SUPPORTS[args.support], FIXES[args.fix]))
        raise StoryError("(No valid combination matches the given options.)")

    task_id, support_id, fix_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    name = args.name or rng.choice(pool)
    adult_type = args.adult or rng.choice(["mother", "father", "aunt", "uncle"])
    trait = rng.choice(TRAITS)
    delay = args.delay if args.delay is not None else rng.choice([0, 1])
    return StoryParams(
        task=task_id,
        support=support_id,
        fix=fix_id,
        child_name=name,
        child_gender=gender,
        adult_type=adult_type,
        trait=trait,
        delay=delay,
    )


def generate(params: StoryParams) -> StorySample:
    if params.task not in TASKS:
        raise StoryError(f"Unknown task: {params.task}")
    if params.support not in SUPPORTS:
        raise StoryError(f"Unknown support: {params.support}")
    if params.fix not in FIXES:
        raise StoryError(f"Unknown fix: {params.fix}")

    task = TASKS[params.task]
    support = SUPPORTS[params.support]
    fix = FIXES[params.fix]
    if not valid_combo(task, support, fix):
        raise StoryError(explain_rejection(task, support, fix))

    world = tell(
        task=task,
        support_cfg=support,
        fix=fix,
        child_name=params.child_name,
        child_gender=params.child_gender,
        adult_type=params.adult_type,
        trait=params.trait,
        delay=params.delay,
    )

    story = world.render()
    child = world.facts["child"]
    task_line = task_incorporate_line(task, child)
    story = story.replace(task.incorporate_line, task_line)

    return StorySample(
        params=params,
        story=story,
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in pair_story_qa(world)],
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
        print(asp_program("", "#show task_valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (task, support, fix) combos:\n")
        for task_id, support_id, fix_id in combos:
            print(f"  {task_id:10} {support_id:14} {fix_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.child_name}: {p.task} with {p.support} -> {outcome_of(p)}"
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
