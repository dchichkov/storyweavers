#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/correction_monthly_stripe_dim_problem_solving_mystery.py
====================================================================================

A standalone story world for a small, rhyming mystery: a child notices that one
stripe on the family's monthly kindness chart looks dim, then works with a
grown-up to solve the mystery and make a careful correction.

The domain is intentionally tiny and state-driven:
- a child keeps a monthly wall chart with glowing paper stripes,
- one stripe seems stripe-dim or partly hidden for a concrete reason,
- the child investigates with clues,
- the child and helper choose a fitting fix,
- the ending image proves the chart can be read clearly again.

Run it
------
    python storyworlds/worlds/gpt-5.4/correction_monthly_stripe_dim_problem_solving_mystery.py
    python storyworlds/worlds/gpt-5.4/correction_monthly_stripe_dim_problem_solving_mystery.py --cause shadow --fix lamp
    python storyworlds/worlds/gpt-5.4/correction_monthly_stripe_dim_problem_solving_mystery.py --cause missing_sticker
    python storyworlds/worlds/gpt-5.4/correction_monthly_stripe_dim_problem_solving_mystery.py --all
    python storyworlds/worlds/gpt-5.4/correction_monthly_stripe_dim_problem_solving_mystery.py --qa
    python storyworlds/worlds/gpt-5.4/correction_monthly_stripe_dim_problem_solving_mystery.py --verify
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
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "sister"}
        male = {"boy", "father", "dad", "man", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Place:
    id: str
    room: str
    wall: str
    nook: str
    tags: set[str] = field(default_factory=set)


@dataclass
class ChartKind:
    id: str
    title: str
    stripe_word: str
    colors: tuple[str, str, str]
    promise: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Cause:
    id: str
    kind: str
    clue: str
    reveal: str
    effect: str
    fix_ids: tuple[str, ...]
    tags: set[str] = field(default_factory=set)


@dataclass
class Fix:
    id: str
    kind: str
    action: str
    result: str
    qa_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    chart: str
    cause: str
    fix: str
    child_name: str
    child_gender: str
    helper_name: str
    helper_type: str
    trait: str
    pet: str = ""
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


def _r_confusion(world: World) -> list[str]:
    chart = world.get("chart")
    child = world.get("child")
    out: list[str] = []
    if chart.meters["hard_to_read"] < THRESHOLD:
        return out
    sig = ("confusion", "chart")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["curiosity"] += 1
    child.memes["worry"] += 1
    out.append("__mystery__")
    return out


def _r_fix_clears(world: World) -> list[str]:
    chart = world.get("chart")
    child = world.get("child")
    helper = world.get("helper")
    out: list[str] = []
    if chart.meters["repaired"] < THRESHOLD:
        return out
    sig = ("clear", "chart")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    chart.meters["hard_to_read"] = 0.0
    chart.meters["stripe_dim"] = 0.0
    child.memes["worry"] = 0.0
    child.memes["pride"] += 1
    helper.memes["pride"] += 1
    out.append("__solved__")
    return out


CAUSAL_RULES = [
    Rule(name="confusion", tag="mystery", apply=_r_confusion),
    Rule(name="fix_clears", tag="resolution", apply=_r_fix_clears),
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


PLACES = {
    "hallway": Place(
        id="hallway",
        room="the hallway",
        wall="the pale hall wall",
        nook="by the shoe basket",
        tags={"hallway"},
    ),
    "kitchen": Place(
        id="kitchen",
        room="the kitchen",
        wall="the warm kitchen wall",
        nook="beside the cookie tin",
        tags={"kitchen"},
    ),
    "playroom": Place(
        id="playroom",
        room="the playroom",
        wall="the sunny playroom wall",
        nook="near the low book shelf",
        tags={"playroom"},
    ),
}

CHARTS = {
    "kindness": ChartKind(
        id="kindness",
        title="monthly kindness chart",
        stripe_word="stripe",
        colors=("gold", "teal", "rose"),
        promise="small kind deeds",
        tags={"monthly", "chart"},
    ),
    "chores": ChartKind(
        id="chores",
        title="monthly helper chart",
        stripe_word="stripe",
        colors=("blue", "green", "orange"),
        promise="little jobs done well",
        tags={"monthly", "chart"},
    ),
    "reading": ChartKind(
        id="reading",
        title="monthly reading chart",
        stripe_word="stripe",
        colors=("purple", "silver", "mint"),
        promise="quiet books read each night",
        tags={"monthly", "chart"},
    ),
}

CAUSES = {
    "shadow": Cause(
        id="shadow",
        kind="light",
        clue="A plant leaf made a long, soft bar across the paper.",
        reveal="the stripe looked stripe-dim because a leaf shadow fell across it",
        effect="shadow",
        fix_ids=("lamp", "move_plant"),
        tags={"shadow", "light"},
    ),
    "missing_sticker": Cause(
        id="missing_sticker",
        kind="record",
        clue="One tiny star sticker had slipped and was hiding on the floor.",
        reveal="the stripe looked stripe-dim because its shiny star sticker had fallen off",
        effect="missing_piece",
        fix_ids=("replace_sticker", "glue_sticker"),
        tags={"sticker", "correction"},
    ),
    "dust": Cause(
        id="dust",
        kind="surface",
        clue="A gray puff sat on the paper and dulled the color.",
        reveal="the stripe looked stripe-dim because dust had settled over the crayon shine",
        effect="dust",
        fix_ids=("wipe_chart",),
        tags={"dust", "clean"},
    ),
    "crayon_smudge": Cause(
        id="crayon_smudge",
        kind="record",
        clue="A sleepy elbow had rubbed the color into a cloudy blur.",
        reveal="the stripe looked stripe-dim because the crayon stripe had been smudged",
        effect="smudge",
        fix_ids=("redraw_stripe",),
        tags={"crayon", "correction"},
    ),
}

FIXES = {
    "lamp": Fix(
        id="lamp",
        kind="light",
        action="clicked on a small lamp and tipped its warm beam toward the chart",
        result="The hidden color woke up and glowed again.",
        qa_text="They used a lamp so the stripe could be seen clearly.",
        tags={"lamp", "light"},
    ),
    "move_plant": Fix(
        id="move_plant",
        kind="light",
        action="slid the plant pot to a brighter spot where its leaves could not cast a bar",
        result="The shadow slipped away, and the stripe shone plain and bright.",
        qa_text="They moved the plant so its shadow stopped covering the stripe.",
        tags={"plant", "light"},
    ),
    "replace_sticker": Fix(
        id="replace_sticker",
        kind="record",
        action="pressed on a fresh silver star in the empty little place",
        result="The stripe looked full and sparkly once more.",
        qa_text="They made a correction by adding a new star sticker.",
        tags={"sticker", "correction"},
    ),
    "glue_sticker": Fix(
        id="glue_sticker",
        kind="record",
        action="found the runaway star on the floor and dabbed a tiny dot of glue behind it",
        result="Back on the paper, the star sat still and bright.",
        qa_text="They made a correction by gluing the fallen sticker back on.",
        tags={"sticker", "correction", "glue"},
    ),
    "wipe_chart": Fix(
        id="wipe_chart",
        kind="surface",
        action="wiped the paper gently with a soft dry cloth",
        result="The dull gray dust lifted, and the color peeped through.",
        qa_text="They cleaned the chart gently so the dusty stripe showed again.",
        tags={"clean", "cloth"},
    ),
    "redraw_stripe": Fix(
        id="redraw_stripe",
        kind="record",
        action="used the matching crayon to redraw the blurred stripe with slow careful strokes",
        result="The color stood neat and steady again.",
        qa_text="They made a correction by redrawing the smudged stripe.",
        tags={"crayon", "correction"},
    ),
}

GIRL_NAMES = ["Mina", "Lily", "Nora", "Ava", "Ella", "Lucy", "Zoe", "Ruby"]
BOY_NAMES = ["Ben", "Leo", "Max", "Theo", "Finn", "Eli", "Sam", "Noah"]
TRAITS = ["careful", "curious", "bright", "patient", "gentle", "thoughtful"]
PETS = ["the cat", "the puppy", "the goldfish", "the little dog", ""]


def valid_fix_for(cause_id: str, fix_id: str) -> bool:
    cause = CAUSES[cause_id]
    fix = FIXES[fix_id]
    return fix_id in cause.fix_ids and fix.kind == cause.kind


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for place_id in PLACES:
        for chart_id in CHARTS:
            for cause_id, cause in CAUSES.items():
                for fix_id in cause.fix_ids:
                    if valid_fix_for(cause_id, fix_id):
                        combos.append((place_id, chart_id, cause_id, fix_id))
    return combos


def cause_prediction(world: World, cause: Cause) -> dict:
    sim = world.copy()
    chart = sim.get("chart")
    if cause.id == "shadow":
        chart.meters["stripe_dim"] += 1
        chart.meters["shadowed"] += 1
    elif cause.id == "missing_sticker":
        chart.meters["stripe_dim"] += 1
        chart.meters["missing_piece"] += 1
    elif cause.id == "dust":
        chart.meters["stripe_dim"] += 1
        chart.meters["dusty"] += 1
    elif cause.id == "crayon_smudge":
        chart.meters["stripe_dim"] += 1
        chart.meters["smudged"] += 1
    chart.meters["hard_to_read"] += 1
    propagate(sim, narrate=False)
    return {
        "stripe_dim": chart.meters["stripe_dim"],
        "hard_to_read": chart.meters["hard_to_read"],
    }


def apply_cause(world: World, cause: Cause) -> None:
    chart = world.get("chart")
    if cause.id == "shadow":
        chart.meters["stripe_dim"] += 1
        chart.meters["shadowed"] += 1
    elif cause.id == "missing_sticker":
        chart.meters["stripe_dim"] += 1
        chart.meters["missing_piece"] += 1
    elif cause.id == "dust":
        chart.meters["stripe_dim"] += 1
        chart.meters["dusty"] += 1
    elif cause.id == "crayon_smudge":
        chart.meters["stripe_dim"] += 1
        chart.meters["smudged"] += 1
    chart.meters["hard_to_read"] += 1
    propagate(world, narrate=False)


def apply_fix(world: World, fix: Fix) -> None:
    chart = world.get("chart")
    if fix.kind == "light":
        chart.meters["shadowed"] = 0.0
    elif fix.kind == "record":
        chart.meters["missing_piece"] = 0.0
        chart.meters["smudged"] = 0.0
    elif fix.kind == "surface":
        chart.meters["dusty"] = 0.0
    chart.meters["repaired"] += 1
    propagate(world, narrate=False)


def introduce(world: World, place: Place, chart_kind: ChartKind, child: Entity, helper: Entity) -> None:
    c1, c2, c3 = chart_kind.colors
    world.say(
        f"In {place.room}, on {place.wall}, hung a {chart_kind.title} so bright, "
        f"with {c1}, {c2}, and {c3} stripes in a row of light."
    )
    world.say(
        f"{child.id} liked to stop there every day and peek, "
        f"while {helper.id} smiled to see the family promise it would keep."
    )
    world.say(
        f"Each stripe marked {chart_kind.promise}, neat and small, "
        f"and once each monthly turn they counted them all."
    )


def discover(world: World, child: Entity, chart_kind: ChartKind, cause: Cause, place: Place) -> None:
    pred = cause_prediction(world, cause)
    world.facts["predicted_dim"] = pred["stripe_dim"]
    child.memes["notice"] += 1
    world.say(
        f"One afternoon, by {place.nook}, {child.id} looked again with a little hymn, "
        f"then blinked and whispered, \"Oh! One {chart_kind.stripe_word} looks stripe-dim.\""
    )
    apply_cause(world, cause)
    world.say(
        f"{child.pronoun().capitalize()} tilted {child.pronoun('possessive')} head with a puzzled chin. "
        f"\"Did a count go wrong? Do we need a correction within?\""
    )


def gather_clue(world: World, child: Entity, helper: Entity, cause: Cause) -> None:
    child.memes["curiosity"] += 1
    helper.memes["care"] += 1
    world.say(
        f"{helper.id} came near and said, \"Let's look, not guess. "
        f"We can solve this small mystery with calmness, not a mess.\""
    )
    world.say(cause.clue)
    world.say(
        f"So side by side they searched for the why, "
        f"with open eyes and a patient try."
    )


def reveal(world: World, child: Entity, helper: Entity, cause: Cause) -> None:
    child.memes["understanding"] += 1
    helper.memes["understanding"] += 1
    world.say(
        f"Then {child.id} clapped softly. \"Now I can see!\" "
        f"The answer was simple as simple could be:"
    )
    world.say(
        f"{cause.reveal[0].upper()}{cause.reveal[1:]}. "
        f"The mystery was not magic at all, only a small thing making a bright mark small."
    )


def solve(world: World, child: Entity, helper: Entity, fix: Fix) -> None:
    world.say(
        f"\"Let's make one careful correction,\" said {helper.id} with a grin. "
        f"\"We can set the little rightness back in.\""
    )
    world.say(
        f"So {child.id} and {helper.id} {fix.action}. {fix.result}"
    )
    apply_fix(world, fix)


def ending(world: World, child: Entity, helper: Entity, chart_kind: ChartKind, pet: str) -> None:
    chart = world.get("chart")
    child.memes["joy"] += 1
    helper.memes["joy"] += 1
    line = (
        f"Now the {chart_kind.title} was easy to read from top down to brim, "
        f"and not one stripe stayed stripe-dim."
    )
    world.say(line)
    if pet:
        world.say(f"Even {pet} sat near with a blink and a purr, as if the bright wall sang to {child.pronoun('object')} and {helper.pronoun('object')} for sure.")
    world.say(
        f"{child.id} traced the clear row with a proud little thumb. "
        f"\"When we look close and think, good answers can come.\""
    )


def tell(
    place: Place,
    chart_kind: ChartKind,
    cause: Cause,
    fix: Fix,
    child_name: str = "Mina",
    child_gender: str = "girl",
    helper_name: str = "Mom",
    helper_type: str = "mother",
    trait: str = "careful",
    pet: str = "",
) -> World:
    world = World()
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
        traits=["calm"],
    ))
    chart = world.add(Entity(
        id="chart",
        kind="thing",
        type="chart",
        label=chart_kind.title,
        phrase=f"the {chart_kind.title}",
        role="chart",
        tags=set(chart_kind.tags),
    ))

    world.facts["display_child_name"] = child_name
    world.facts["display_helper_name"] = helper_name
    world.facts["pet"] = pet

    introduce(world, place, chart_kind, child, helper)
    world.para()
    discover(world, child, chart_kind, cause, place)
    world.para()
    gather_clue(world, child, helper, cause)
    reveal(world, child, helper, cause)
    world.para()
    solve(world, child, helper, fix)
    ending(world, child, helper, chart_kind, pet)

    world.facts.update(
        place=place,
        chart_kind=chart_kind,
        cause=cause,
        fix=fix,
        child=child,
        helper=helper,
        chart=chart,
        solved=chart.meters["hard_to_read"] < THRESHOLD,
        stripe_dim_seen=True,
    )
    return world


KNOWLEDGE = {
    "monthly": [
        (
            "What does monthly mean?",
            "Monthly means something happens once each month or belongs to a month. A monthly chart helps people look back over many days together."
        )
    ],
    "chart": [
        (
            "What is a chart?",
            "A chart is a paper or board that helps you keep track of things. It can use lines, boxes, stickers, or colors to show what happened."
        )
    ],
    "shadow": [
        (
            "Why can a shadow make something look dim?",
            "A shadow blocks some light from reaching what you are looking at. When less light reaches it, the color can seem darker or dimmer."
        )
    ],
    "sticker": [
        (
            "Why would a missing sticker change how a chart looks?",
            "A sticker can mark an important part of the chart. If it falls off, that spot may look empty or less bright than the others."
        )
    ],
    "dust": [
        (
            "Why does dust make things look dull?",
            "Dust sits on top of a surface and hides some of its shine. Wiping it away can make the color look clearer again."
        )
    ],
    "crayon": [
        (
            "What happens when crayon gets smudged?",
            "A smudged crayon mark gets rubbed and blurry instead of neat. That can make a line harder to see or read."
        )
    ],
    "correction": [
        (
            "What is a correction?",
            "A correction is a careful change that fixes a mistake or a wrong-looking part. It helps make something accurate or clear again."
        )
    ],
    "lamp": [
        (
            "What does a lamp do?",
            "A lamp gives light to a darker place. Better light helps your eyes see colors, edges, and details more clearly."
        )
    ],
    "mystery": [
        (
            "What is a mystery?",
            "A mystery is a question with an answer you do not know yet. You solve it by noticing clues and thinking carefully."
        )
    ],
}

KNOWLEDGE_ORDER = ["monthly", "chart", "mystery", "shadow", "sticker", "dust", "crayon", "correction", "lamp"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child_name = f["display_child_name"]
    helper_name = f["display_helper_name"]
    chart_kind = f["chart_kind"]
    cause = f["cause"]
    return [
        'Write a rhyming story for a 3-to-5-year-old that includes the words "correction", "monthly", and "stripe-dim".',
        f"Tell a gentle mystery-to-solve story where {child_name} notices a stripe-dim place on a {chart_kind.title} and works with {helper_name} to figure out why.",
        f"Write a child-facing problem-solving poem-story where the clue is that {cause.clue.lower()} and the ending shows the chart bright again.",
    ]


def story_qa_pairs(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    chart_kind = f["chart_kind"]
    cause = f["cause"]
    fix = f["fix"]
    child_name = f["display_child_name"]
    helper_name = f["display_helper_name"]
    qa = [
        (
            "Who is the story about?",
            f"It is about {child_name}, a child who notices something odd on a {chart_kind.title}, and {helper_name}, who helps solve the mystery. Together they look for clues instead of guessing."
        ),
        (
            "What was the mystery in the story?",
            f"The mystery was why one stripe on the {chart_kind.title} looked stripe-dim. {child_name} worried the chart might need a correction because one part did not match the others."
        ),
        (
            f"Why did {child_name} think a correction might be needed?",
            f"{child_name} saw that one stripe looked dim and uneven compared with the rest. That made {child.pronoun('object')} wonder whether something had gone wrong on the chart."
        ),
        (
            "What clue helped them solve the mystery?",
            f"The clue was this: {cause.clue} That clue pointed them toward the real cause instead of a wild guess."
        ),
        (
            "What was really making the stripe look dim?",
            f"It was {cause.reveal}. Once they noticed the real reason, the mystery stopped feeling confusing."
        ),
        (
            "How did they solve the problem?",
            f"{fix.qa_text} That careful step fixed the real cause, so the chart became easy to read again."
        ),
        (
            "How did the story end?",
            f"It ended with the monthly chart bright and clear again, with no stripe left stripe-dim. The ending shows that patient problem solving can turn worry into pride."
        ),
    ]
    return qa


def world_knowledge_pairs(world: World) -> list[tuple[str, str]]:
    tags = {"monthly", "chart", "mystery"}
    cause = world.facts["cause"]
    fix = world.facts["fix"]
    if "shadow" in cause.tags or "light" in cause.tags or "lamp" in fix.tags:
        tags.add("shadow")
        tags.add("lamp")
    if "sticker" in cause.tags or "sticker" in fix.tags:
        tags.add("sticker")
        tags.add("correction")
    if "dust" in cause.tags:
        tags.add("dust")
    if "crayon" in cause.tags or "crayon" in fix.tags:
        tags.add("crayon")
        tags.add("correction")
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
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = [f"type={ent.type}"]
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.traits:
            bits.append(f"traits={ent.traits}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:8} {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="hallway",
        chart="kindness",
        cause="shadow",
        fix="lamp",
        child_name="Mina",
        child_gender="girl",
        helper_name="Mom",
        helper_type="mother",
        trait="careful",
        pet="the cat",
    ),
    StoryParams(
        place="kitchen",
        chart="chores",
        cause="missing_sticker",
        fix="glue_sticker",
        child_name="Ben",
        child_gender="boy",
        helper_name="Dad",
        helper_type="father",
        trait="curious",
        pet="",
    ),
    StoryParams(
        place="playroom",
        chart="reading",
        cause="dust",
        fix="wipe_chart",
        child_name="Lucy",
        child_gender="girl",
        helper_name="Mom",
        helper_type="mother",
        trait="patient",
        pet="the puppy",
    ),
    StoryParams(
        place="hallway",
        chart="kindness",
        cause="crayon_smudge",
        fix="redraw_stripe",
        child_name="Theo",
        child_gender="boy",
        helper_name="Dad",
        helper_type="father",
        trait="thoughtful",
        pet="the little dog",
    ),
    StoryParams(
        place="kitchen",
        chart="reading",
        cause="missing_sticker",
        fix="replace_sticker",
        child_name="Ava",
        child_gender="girl",
        helper_name="Mom",
        helper_type="mother",
        trait="bright",
        pet="the goldfish",
    ),
]


def explain_rejection(cause_id: str, fix_id: str) -> str:
    cause = CAUSES[cause_id]
    fix = FIXES[fix_id]
    return (
        f"(No story: the fix '{fix_id}' does not match the cause '{cause_id}'. "
        f"This mystery needs a fix for {cause.kind}, but '{fix_id}' is a {fix.kind} fix.)"
    )


ASP_RULES = r"""
valid_fix(C, F) :- cause(C), fix(F), allows(C, F), cause_kind(C, K), fix_kind(F, K).
valid(P, Ch, C, F) :- place(P), chart(Ch), cause(C), fix(F), valid_fix(C, F).

% A simple state twin of the mystery:
stripe_dim(C) :- cause(C).
solved(C, F)  :- valid_fix(C, F).
outcome(C, F, solved) :- stripe_dim(C), solved(C, F).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place_id in PLACES:
        lines.append(asp.fact("place", place_id))
    for chart_id in CHARTS:
        lines.append(asp.fact("chart", chart_id))
    for cause_id, cause in CAUSES.items():
        lines.append(asp.fact("cause", cause_id))
        lines.append(asp.fact("cause_kind", cause_id, cause.kind))
        for fix_id in cause.fix_ids:
            lines.append(asp.fact("allows", cause_id, fix_id))
    for fix_id, fix in FIXES.items():
        lines.append(asp.fact("fix", fix_id))
        lines.append(asp.fact("fix_kind", fix_id, fix.kind))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_valid_fixes() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid_fix/2."))
    return sorted(set(asp.atoms(model, "valid_fix")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join([
        asp.fact("chosen_cause", params.cause),
        asp.fact("chosen_fix", params.fix),
        "outcome_choice(O) :- chosen_cause(C), chosen_fix(F), outcome(C,F,O).",
    ])
    model = asp.one_model(asp_program(extra, "#show outcome_choice/1."))
    atoms = asp.atoms(model, "outcome_choice")
    return atoms[0][0] if atoms else "?"


def verify_smoke() -> None:
    sample = generate(CURATED[0])
    if not sample.story or "stripe-dim" not in sample.story or "monthly" not in sample.story:
        raise StoryError("Smoke test failed: generated story missing required words or text.")
    emit(sample, trace=False, qa=False, header="")


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
            print("  only in ASP:", sorted(asp_valid - py_valid))
        if py_valid - asp_valid:
            print("  only in Python:", sorted(py_valid - asp_valid))

    py_fixes = {(cause_id, fix_id) for cause_id, cause in CAUSES.items() for fix_id in cause.fix_ids if valid_fix_for(cause_id, fix_id)}
    asp_fixes = set(asp_valid_fixes())
    if py_fixes == asp_fixes:
        print(f"OK: valid fixes match ({len(py_fixes)} pairs).")
    else:
        rc = 1
        print("MISMATCH in valid fixes:")
        if asp_fixes - py_fixes:
            print("  only in ASP:", sorted(asp_fixes - py_fixes))
        if py_fixes - asp_fixes:
            print("  only in Python:", sorted(py_fixes - asp_fixes))

    cases = list(CURATED)
    for seed in range(50):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
            cases.append(params)
        except StoryError:
            rc = 1
            print(f"Unexpected StoryError during resolve_params smoke seed {seed}.")
            break
    bad = 0
    for params in cases:
        py_out = "solved" if valid_fix_for(params.cause, params.fix) else "?"
        asp_out = asp_outcome(params)
        if py_out != asp_out:
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        verify_smoke()
        print("OK: smoke generation/emit passed.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE FAILURE: {exc}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Rhyming mystery storyworld: a child notices one stripe-dim line on a monthly chart and solves the problem."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--chart", choices=CHARTS)
    ap.add_argument("--cause", choices=CAUSES)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--child-name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combinations from the ASP twin")
    ap.add_argument("--verify", action="store_true", help="check Python/ASP parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.cause and args.fix and not valid_fix_for(args.cause, args.fix):
        raise StoryError(explain_rejection(args.cause, args.fix))

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.chart is None or combo[1] == args.chart)
        and (args.cause is None or combo[2] == args.cause)
        and (args.fix is None or combo[3] == args.fix)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, chart, cause, fix = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    child_name = args.child_name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper_type = args.helper or rng.choice(["mother", "father"])
    helper_name = "Mom" if helper_type == "mother" else "Dad"
    trait = rng.choice(TRAITS)
    pet = rng.choice(PETS)
    return StoryParams(
        place=place,
        chart=chart,
        cause=cause,
        fix=fix,
        child_name=child_name,
        child_gender=gender,
        helper_name=helper_name,
        helper_type=helper_type,
        trait=trait,
        pet=pet,
    )


def _validate_params(params: StoryParams) -> None:
    if params.place not in PLACES:
        raise StoryError(f"(No story: unknown place '{params.place}').")
    if params.chart not in CHARTS:
        raise StoryError(f"(No story: unknown chart '{params.chart}').")
    if params.cause not in CAUSES:
        raise StoryError(f"(No story: unknown cause '{params.cause}').")
    if params.fix not in FIXES:
        raise StoryError(f"(No story: unknown fix '{params.fix}').")
    if not valid_fix_for(params.cause, params.fix):
        raise StoryError(explain_rejection(params.cause, params.fix))
    if params.child_gender not in {"girl", "boy"}:
        raise StoryError(f"(No story: unknown gender '{params.child_gender}').")
    if params.helper_type not in {"mother", "father"}:
        raise StoryError(f"(No story: unknown helper type '{params.helper_type}').")


def generate(params: StoryParams) -> StorySample:
    _validate_params(params)
    world = tell(
        place=PLACES[params.place],
        chart_kind=CHARTS[params.chart],
        cause=CAUSES[params.cause],
        fix=FIXES[params.fix],
        child_name=params.child_name,
        child_gender=params.child_gender,
        helper_name=params.helper_name,
        helper_type=params.helper_type,
        trait=params.trait,
        pet=params.pet,
    )

    story = world.render().replace("child", world.facts["display_child_name"]).replace("helper", world.facts["display_helper_name"])
    return StorySample(
        params=params,
        story=story,
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa_pairs(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_pairs(world)],
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
        print(asp_program("", "#show valid/4.\n#show valid_fix/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, chart, cause, fix) combos:\n")
        for place, chart, cause, fix in combos:
            print(f"  {place:8} {chart:8} {cause:15} {fix}")
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.child_name}: {p.cause} -> {p.fix} ({p.chart} at {p.place})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
