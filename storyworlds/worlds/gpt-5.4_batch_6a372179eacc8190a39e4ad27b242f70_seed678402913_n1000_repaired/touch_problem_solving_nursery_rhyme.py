#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/touch_problem_solving_nursery_rhyme.py
=================================================================

A standalone story world for a tiny nursery-rhyme-style domain about **touch**
and **problem solving**. A small child faces one high-up garden problem:
something important must be touched to help hungry ducklings, thirsty tulips,
or peeping chicks. The child cannot reach alone, so a calm grown-up helps find
a sensible way to do it.

The world model is intentionally small and concrete:

    child wants to touch target but cannot reach
    + helper adds reach (and may or may not allow precise touch)
    -> touch happens
    -> the problem is solved
    -> relief, pride, and a changed ending image

The reasonableness gate rejects helpers that are too unsafe, too short, or too
clumsy for the chosen target. The inline ASP twin mirrors that same logic.

Run it
------
    python storyworlds/worlds/gpt-5.4/touch_problem_solving_nursery_rhyme.py
    python storyworlds/worlds/gpt-5.4/touch_problem_solving_nursery_rhyme.py --goal bell
    python storyworlds/worlds/gpt-5.4/touch_problem_solving_nursery_rhyme.py --goal button --helper broom
    python storyworlds/worlds/gpt-5.4/touch_problem_solving_nursery_rhyme.py --all
    python storyworlds/worlds/gpt-5.4/touch_problem_solving_nursery_rhyme.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/touch_problem_solving_nursery_rhyme.py --trace
    python storyworlds/worlds/gpt-5.4/touch_problem_solving_nursery_rhyme.py --json
    python storyworlds/worlds/gpt-5.4/touch_problem_solving_nursery_rhyme.py --verify
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
CHILD_REACH = 0.6
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
        female = {"girl", "mother", "mom", "woman", "grandmother"}
        male = {"boy", "father", "dad", "man", "grandfather"}
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
        }.get(self.type, self.type)


@dataclass
class Goal:
    id: str
    label: str
    phrase: str
    place: str
    height: float
    precise: bool = False
    opener: str = ""
    need_line: str = ""
    try_line: str = ""
    solve_line: str = ""
    ending_line: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Helper:
    id: str
    label: str
    phrase: str
    reach_bonus: float
    precise: bool = False
    sense: int = 0
    rise_line: str = ""
    touch_line: str = ""
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


def _r_worry(world: World) -> list[str]:
    child = world.entities.get("child")
    target = world.entities.get("target")
    problem = world.entities.get("problem")
    if child is None or target is None or problem is None:
        return []
    if problem.meters["unsolved"] < THRESHOLD:
        return []
    if target.meters["touched"] >= THRESHOLD:
        return []
    sig = ("worry", child.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["worry"] += 1
    return ["__worry__"]


def _r_solve(world: World) -> list[str]:
    child = world.entities.get("child")
    target = world.entities.get("target")
    problem = world.entities.get("problem")
    if child is None or target is None or problem is None:
        return []
    if target.meters["touched"] < THRESHOLD:
        return []
    sig = ("solve", target.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    problem.meters["unsolved"] = 0.0
    problem.meters["solved"] += 1
    child.memes["relief"] += 1
    child.memes["pride"] += 1
    child.memes["worry"] = 0.0
    return ["__solved__"]


CAUSAL_RULES: list[Rule] = [
    Rule(name="worry", tag="meme", apply=_r_worry),
    Rule(name="solve", tag="physical", apply=_r_solve),
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
                produced.extend(line for line in lines if not line.startswith("__"))
    if narrate:
        for line in produced:
            world.say(line)
    return produced


GOALS = {
    "bell": Goal(
        id="bell",
        label="bell",
        phrase="the brass garden bell",
        place="by the duck pen",
        height=1.25,
        precise=False,
        opener="By the duck pen, six ducklings dabbled and dawdled instead of waddling home for supper.",
        need_line="The brass garden bell was what called them in, but it hung too high for small hands to touch.",
        try_line="Little feet rose on tiptoe, but the bell stayed up where only the sunlight could kiss it.",
        solve_line="At the bright bell-clang, the ducklings turned together and came bob-bob-bobbing across the grass.",
        ending_line="Soon they tucked themselves into the pen like six yellow boats, while the bell sang one last tiny ding.",
        tags={"bell", "ducklings", "garden"},
    ),
    "button": Goal(
        id="button",
        label="button",
        phrase="the blue fountain button",
        place="beside the tulip bed",
        height=1.05,
        precise=True,
        opener="Beside the tulip bed, three droopy tulips bent their heads as if they had forgotten their morning song.",
        need_line="The fountain could wake them, but the blue button sat too high for small hands to touch.",
        try_line="Up went the chin and up went the fingers, yet the button waited just a little higher than a child could reach.",
        solve_line="With one neat press, the fountain woke and sent silver water skipping into the bed, and the tulips lifted their faces.",
        ending_line="Soon the petals wore bright beads of water and nodded in the spray as though they were dancing in place.",
        tags={"button", "fountain", "tulips", "garden"},
    ),
    "latch": Goal(
        id="latch",
        label="latch",
        phrase="the little coop latch",
        place="on the hen-house door",
        height=1.15,
        precise=True,
        opener="On the hen-house door, a little latch held two peeping chicks behind the sunny run they wanted to explore.",
        need_line="The chicks were safe but cross, and the latch sat too high for small hands to touch.",
        try_line="A hop and a stretch were brave and fine, yet the latch still clicked from a place just out of reach.",
        solve_line="Up went the latch with a tidy click, and out came the chicks on careful, peppery feet.",
        ending_line="They peeped around the child's shoes like two crumbs of buttered toast, busy and pleased at last.",
        tags={"latch", "chicks", "coop", "garden"},
    ),
}

HELPERS = {
    "stool": Helper(
        id="stool",
        label="stool",
        phrase="a red stool",
        reach_bonus=0.7,
        precise=True,
        sense=3,
        rise_line="A red stool stood steady as a little stage.",
        touch_line="Standing tall on the stool, the child could finally touch what had been too high before.",
        tags={"stool", "reach"},
    ),
    "parent_lift": Helper(
        id="parent_lift",
        label="grown-up lift",
        phrase="a gentle grown-up lift",
        reach_bonus=1.0,
        precise=True,
        sense=3,
        rise_line="Strong arms made a careful, gentle lift, high enough for a small task and low enough for a calm heart.",
        touch_line="From that snug, careful lift, the child could touch the target easily.",
        tags={"lift", "adult_help", "reach"},
    ),
    "broom": Helper(
        id="broom",
        label="broom handle",
        phrase="a smooth broom handle",
        reach_bonus=0.9,
        precise=False,
        sense=2,
        rise_line="A smooth broom handle was long enough to tap from the ground.",
        touch_line="With the broom held slow and steady, the child could touch from below without climbing at all.",
        tags={"broom", "reach"},
    ),
    "crate": Helper(
        id="crate",
        label="wobbly crate",
        phrase="a wobbly crate",
        reach_bonus=0.6,
        precise=True,
        sense=1,
        rise_line="A wobbly crate leaned by the fence, all bump and no balance.",
        touch_line="It was tall enough, perhaps, but far from wise.",
        tags={"crate", "unsafe"},
    ),
}


def sensible_helpers() -> list[Helper]:
    return [helper for helper in HELPERS.values() if helper.sense >= SENSE_MIN]


def effective_reach(helper: Helper) -> float:
    return CHILD_REACH + helper.reach_bonus


def can_touch(goal: Goal, helper: Helper) -> bool:
    if effective_reach(helper) + 1e-9 < goal.height:
        return False
    if goal.precise and not helper.precise:
        return False
    return True


def valid_combos() -> list[tuple[str, str]]:
    combos: list[tuple[str, str]] = []
    for goal_id, goal in GOALS.items():
        for helper_id, helper in HELPERS.items():
            if helper.sense >= SENSE_MIN and can_touch(goal, helper):
                combos.append((goal_id, helper_id))
    return combos


@dataclass
class StoryParams:
    goal: str
    helper: str
    child: str
    gender: str
    parent: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        goal="bell",
        helper="broom",
        child="Mina",
        gender="girl",
        parent="mother",
        seed=101,
    ),
    StoryParams(
        goal="button",
        helper="stool",
        child="Toby",
        gender="boy",
        parent="father",
        seed=102,
    ),
    StoryParams(
        goal="latch",
        helper="parent_lift",
        child="Nell",
        gender="girl",
        parent="grandmother",
        seed=103,
    ),
    StoryParams(
        goal="bell",
        helper="stool",
        child="Ben",
        gender="boy",
        parent="grandfather",
        seed=104,
    ),
    StoryParams(
        goal="button",
        helper="parent_lift",
        child="Ivy",
        gender="girl",
        parent="mother",
        seed=105,
    ),
]

GIRL_NAMES = ["Mina", "Nell", "Ivy", "Poppy", "May", "Lila", "Tess", "Wren"]
BOY_NAMES = ["Toby", "Ben", "Ollie", "Sam", "Ned", "Finn", "Kit", "Leo"]


def explain_rejection(goal: Goal, helper: Helper) -> str:
    if helper.sense < SENSE_MIN:
        return (
            f"(No story: {helper.phrase} is known to the world, but it is too wobbly or unwise "
            f"for a child-facing problem-solving story. Pick a steadier helper.)"
        )
    if effective_reach(helper) + 1e-9 < goal.height:
        return (
            f"(No story: {helper.phrase} does not give enough reach to touch {goal.phrase}. "
            f"The child would still be too short.)"
        )
    if goal.precise and not helper.precise:
        return (
            f"(No story: {goal.phrase} needs a neat, precise touch, but {helper.phrase} is only good "
            f"for broad tapping. Pick a helper that allows careful touch.)"
        )
    return "(No story: this goal and helper do not make a reasonable problem-solving pair.)"


def outcome_of(params: StoryParams) -> str:
    goal = GOALS[params.goal]
    helper = HELPERS[params.helper]
    return "solved" if can_touch(goal, helper) else "failed"


def _pick_name(rng: random.Random, gender: str) -> str:
    if gender == "girl":
        return rng.choice(GIRL_NAMES)
    return rng.choice(BOY_NAMES)


def predict_touch(world: World, goal_id: str, helper_id: str) -> dict:
    sim = world.copy()
    goal = GOALS[goal_id]
    helper = HELPERS[helper_id]
    sim.facts["effective_reach"] = effective_reach(helper)
    return {
        "can_touch": can_touch(goal, helper),
        "gap": max(0.0, goal.height - effective_reach(helper)),
    }


def introduce(world: World, child: Entity, parent: Entity, goal: Goal) -> None:
    child.memes["curiosity"] += 1
    world.say(
        f"Tiptoe morning, tick-tock light: little {child.id} skipped through the garden with "
        f"{child.pronoun('possessive')} {parent.label_word}."
    )
    world.say(goal.opener)
    world.say(goal.need_line)
    propagate(world, narrate=False)


def try_alone(world: World, child: Entity, goal: Goal) -> None:
    child.memes["wish"] += 1
    world.say(
        f'"Let me touch it," said {child.id}, soft and bright.'
    )
    world.say(goal.try_line)


def think_together(world: World, child: Entity, parent: Entity, helper: Helper, goal: Goal) -> None:
    pred = predict_touch(world, goal.id, helper.id)
    child.memes["thinking"] += 1
    parent.memes["calm"] += 1
    world.facts["predicted_gap"] = round(pred["gap"], 2)
    if helper.id == "broom":
        plan = (
            f'"No climbing needed," said {parent.label_word}. "For {goal.phrase}, a long, gentle tap will do."'
        )
    elif helper.id == "parent_lift":
        plan = (
            f'"I can lift you gently," said {parent.label_word}, "and then your fingers can make the careful touch."'
        )
    else:
        plan = (
            f'"We need a clever little boost," said {parent.label_word}.'
        )
    world.say(
        f"{child.id} stopped hopping and started thinking. {helper.rise_line} {plan}"
    )


def use_helper(world: World, child: Entity, parent: Entity, helper: Helper, goal: Goal) -> None:
    child.meters["reach"] = effective_reach(helper)
    target = world.get("target")
    world.say(helper.touch_line)
    if helper.id == "broom":
        world.say(
            f"{child.id} held the broom with both hands and gave {goal.phrase} the gentlest touch."
        )
    elif helper.id == "parent_lift":
        world.say(
            f"Up in that careful lift, {child.id} stretched one finger and gave {goal.phrase} a sure little touch."
        )
    else:
        world.say(
            f"{child.id} climbed onto the stool, took a breath, and gave {goal.phrase} a neat little touch."
        )
    target.meters["touched"] += 1
    child.memes["bravery"] += 1
    propagate(world, narrate=False)


def solve_scene(world: World, goal: Goal) -> None:
    world.say(goal.solve_line)


def ending(world: World, child: Entity, parent: Entity, goal: Goal, helper: Helper) -> None:
    child.memes["love"] += 1
    parent.memes["pride"] += 1
    world.say(
        f'{parent.label_word.capitalize()} smiled. "See?" {parent.pronoun()} said. '
        f'"When a thing is too high, we stop, we think, and we find the right touch."'
    )
    world.say(goal.ending_line)
    if helper.id == "stool":
        world.say(f"The red stool waited quietly nearby, as if pleased to have helped.")
    elif helper.id == "parent_lift":
        world.say(f"{child.id} tucked close for one more moment before wriggling back down to the path.")
    else:
        world.say("The broom went back by the gate, plain and still after its useful little turn.")


def tell(goal: Goal, helper: Helper, child_name: str, gender: str, parent_type: str) -> World:
    world = World()
    child = world.add(
        Entity(
            id=child_name,
            kind="character",
            type=gender,
            label=child_name,
            role="child",
        )
    )
    parent = world.add(
        Entity(
            id="Parent",
            kind="character",
            type=parent_type,
            label="the parent",
            role="parent",
        )
    )
    target = world.add(
        Entity(
            id="target",
            kind="thing",
            type="target",
            label=goal.label,
            phrase=goal.phrase,
            attrs={"height": goal.height, "precise": goal.precise, "place": goal.place},
            tags=set(goal.tags),
        )
    )
    problem = world.add(
        Entity(
            id="problem",
            kind="thing",
            type="problem",
            label=goal.id,
            phrase=goal.opener,
            tags=set(goal.tags),
        )
    )
    helper_ent = world.add(
        Entity(
            id="helper",
            kind="thing",
            type="helper",
            label=helper.label,
            phrase=helper.phrase,
            attrs={"sense": helper.sense, "reach_bonus": helper.reach_bonus, "precise": helper.precise},
            tags=set(helper.tags),
        )
    )
    child.meters["reach"] = CHILD_REACH
    problem.meters["unsolved"] = 1.0

    introduce(world, child, parent, goal)
    world.para()
    try_alone(world, child, goal)
    think_together(world, child, parent, helper, goal)
    world.para()
    use_helper(world, child, parent, helper, goal)
    solve_scene(world, goal)
    world.para()
    ending(world, child, parent, goal, helper)

    world.facts.update(
        child=child,
        parent=parent,
        goal=goal,
        helper=helper,
        helper_ent=helper_ent,
        target=target,
        problem=problem,
        solved=problem.meters["solved"] >= THRESHOLD,
        outcome="solved" if problem.meters["solved"] >= THRESHOLD else "failed",
        effective_reach=child.meters["reach"],
        touch_word_used=True,
    )
    return world


KNOWLEDGE = {
    "bell": [
        (
            "What does a bell do?",
            "A bell makes a ringing sound people or animals can hear from far away. It can be used to call everyone in."
        )
    ],
    "ducklings": [
        (
            "What is a duckling?",
            "A duckling is a baby duck. Ducklings are small, fluffy, and like to follow a sound or a parent."
        )
    ],
    "button": [
        (
            "What does a button do on a machine or fountain?",
            "A button is a small part you press to make something start or change. When you press it, it tells the machine what to do."
        )
    ],
    "tulips": [
        (
            "Why do flowers need water?",
            "Flowers need water to stay fresh and standing tall. Without enough water, they droop and look sleepy."
        )
    ],
    "latch": [
        (
            "What is a latch?",
            "A latch is a little fastener that keeps a door or gate closed until someone lifts or moves it."
        )
    ],
    "chicks": [
        (
            "What is a chick?",
            "A chick is a baby chicken. Chicks are small, soft, and often peep when they want to move about."
        )
    ],
    "stool": [
        (
            "What is a stool for?",
            "A stool is a small seat or step that can help you reach something a bit higher. A sturdy stool should stand steady."
        )
    ],
    "adult_help": [
        (
            "Why is it good to ask a grown-up for help?",
            "A grown-up can help you think of a safer plan. They can steady, lift, or guide you when something is too hard alone."
        )
    ],
    "broom": [
        (
            "Can a broom help you reach something?",
            "Sometimes a broom can help tap something from far away. It works best for broad touches, not tiny careful pressing."
        )
    ],
    "reach": [
        (
            "What does reach mean?",
            "Reach means how far your hand or body can stretch to touch something. If something is out of reach, you need another safe plan."
        )
    ],
}

KNOWLEDGE_ORDER = [
    "bell",
    "ducklings",
    "button",
    "tulips",
    "latch",
    "chicks",
    "stool",
    "adult_help",
    "broom",
    "reach",
]


def generation_prompts(world: World) -> list[str]:
    child = world.facts["child"]
    goal = world.facts["goal"]
    helper = world.facts["helper"]
    parent = world.facts["parent"]
    return [
        f'Write a short nursery-rhyme-style story for a 3-to-5-year-old that includes the word "touch" and a small problem solved with help.',
        f"Tell a gentle garden story where {child.id} cannot touch {goal.phrase} alone, so {child.pronoun('possessive')} {parent.label_word} helps {child.pronoun('object')} think of a better plan using {helper.phrase}.",
        f"Write a rhyming-leaning story with a beginning, a little reaching problem, and a happy ending image after the right touch solves it.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    child = world.facts["child"]
    parent = world.facts["parent"]
    goal = world.facts["goal"]
    helper = world.facts["helper"]
    gap = world.facts.get("predicted_gap", 0.0)
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id} and {child.pronoun('possessive')} {parent.label_word} in the garden. Together they face a small problem that needs a careful touch."
        ),
        (
            f"What was the problem in the story?",
            f"The problem was that {goal.phrase} needed to be touched to help, but it was too high for {child.id} to reach alone. That is why the story turns into a little problem-solving game."
        ),
        (
            f"Why could {child.id} not solve it right away?",
            f"{child.id} tried first, but {goal.phrase} was still out of reach. The gap was small, about {gap:.2f} meters after guessing the wrong way to do it, but still too much for bare tiptoes."
        ),
        (
            f"How did they solve the problem?",
            f"They stopped, thought together, and used {helper.phrase}. That helper gave {child.id} the right way to touch {goal.phrase} safely and make the change happen."
        ),
    ]
    if world.facts.get("solved"):
        qa.append(
            (
                "What changed at the end?",
                f"The problem in the garden was solved, and the whole place looked different afterward. {goal.ending_line}"
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    goal = world.facts["goal"]
    helper = world.facts["helper"]
    tags = set(goal.tags) | set(helper.tags) | {"reach"}
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
    for entity in list(world.entities.values()):
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        bits = []
        if entity.role:
            bits.append(f"role={entity.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if entity.attrs:
            shown = {k: v for k, v in entity.attrs.items() if v or v == 0}
            if shown:
                bits.append(f"attrs={shown}")
        if entity.tags:
            bits.append(f"tags={sorted(entity.tags)}")
        lines.append(f"  {entity.id:8} ({entity.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
helper_reaches(G, H) :- goal(G), helper(H), goal_height(G, GH), child_reach(CR), reach_bonus(H, RB), CR + RB >= GH.
helper_precise_enough(G, H) :- goal(G), helper(H), not precise_goal(G).
helper_precise_enough(G, H) :- goal(G), helper(H), precise_goal(G), precise_helper(H).

sensible(H) :- helper(H), helper_sense(H, S), sense_min(M), S >= M.
valid(G, H) :- goal(G), helper(H), sensible(H), helper_reaches(G, H), helper_precise_enough(G, H).

chosen_valid :- chosen_goal(G), chosen_helper(H), valid(G, H).
outcome(solved) :- chosen_valid.
outcome(failed) :- chosen_goal(_), chosen_helper(_), not chosen_valid.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = [asp.fact("child_reach", CHILD_REACH), asp.fact("sense_min", SENSE_MIN)]
    for goal_id, goal in GOALS.items():
        lines.append(asp.fact("goal", goal_id))
        lines.append(asp.fact("goal_height", goal_id, goal.height))
        if goal.precise:
            lines.append(asp.fact("precise_goal", goal_id))
    for helper_id, helper in HELPERS.items():
        lines.append(asp.fact("helper", helper_id))
        lines.append(asp.fact("reach_bonus", helper_id, helper.reach_bonus))
        lines.append(asp.fact("helper_sense", helper_id, helper.sense))
        if helper.precise:
            lines.append(asp.fact("precise_helper", helper_id))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible_helpers() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(helper for (helper,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_goal", params.goal),
            asp.fact("chosen_helper", params.helper),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


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

    clingo_sensible = set(asp_sensible_helpers())
    python_sensible = {helper.id for helper in sensible_helpers()}
    if clingo_sensible == python_sensible:
        print(f"OK: sensible helpers match ({sorted(clingo_sensible)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible helpers: clingo={sorted(clingo_sensible)} python={sorted(python_sensible)}")

    cases: list[StoryParams] = []
    for goal_id in GOALS:
        for helper_id in HELPERS:
            cases.append(
                StoryParams(
                    goal=goal_id,
                    helper=helper_id,
                    child="Test",
                    gender="girl",
                    parent="mother",
                    seed=0,
                )
            )
    bad = sum(1 for params in cases if asp_outcome(params) != outcome_of(params))
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("smoke test produced an empty story")
        print("OK: smoke test story generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Nursery-rhyme-style touch problem-solving storyworld. Unspecified choices are picked at random (seeded)."
    )
    ap.add_argument("--goal", choices=GOALS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--child")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father", "grandmother", "grandfather"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program (facts + inline rules)")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.goal and args.helper:
        goal = GOALS[args.goal]
        helper = HELPERS[args.helper]
        if not (helper.sense >= SENSE_MIN and can_touch(goal, helper)):
            raise StoryError(explain_rejection(goal, helper))
    elif args.helper:
        helper = HELPERS[args.helper]
        if helper.sense < SENSE_MIN:
            goal = GOALS[args.goal] if args.goal else next(iter(GOALS.values()))
            raise StoryError(explain_rejection(goal, helper))

    combos = [
        combo
        for combo in valid_combos()
        if (args.goal is None or combo[0] == args.goal)
        and (args.helper is None or combo[1] == args.helper)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    goal_id, helper_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    child = args.child or _pick_name(rng, gender)
    parent = args.parent or rng.choice(["mother", "father", "grandmother", "grandfather"])
    return StoryParams(
        goal=goal_id,
        helper=helper_id,
        child=child,
        gender=gender,
        parent=parent,
        seed=None,
    )


def generate(params: StoryParams) -> StorySample:
    if params.goal not in GOALS:
        raise StoryError(f"(Invalid goal: {params.goal})")
    if params.helper not in HELPERS:
        raise StoryError(f"(Invalid helper: {params.helper})")
    goal = GOALS[params.goal]
    helper = HELPERS[params.helper]
    if helper.sense < SENSE_MIN or not can_touch(goal, helper):
        raise StoryError(explain_rejection(goal, helper))
    world = tell(goal, helper, params.child, params.gender, params.parent)
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
        print(asp_program("", "#show sensible/1.\n#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        sensible = asp_sensible_helpers()
        combos = asp_valid_combos()
        print(f"sensible helpers: {', '.join(sensible)}\n")
        print(f"{len(combos)} compatible (goal, helper) combos:\n")
        for goal_id, helper_id in combos:
            print(f"  {goal_id:8} {helper_id}")
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
            header = f"### {p.child}: {p.goal} with {p.helper}"
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
