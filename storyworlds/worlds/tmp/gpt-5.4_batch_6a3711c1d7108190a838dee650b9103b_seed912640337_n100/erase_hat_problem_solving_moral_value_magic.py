#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/erase_hat_problem_solving_moral_value_magic.py
=========================================================================

A small storyworld about a child in an ordinary home, a magical hat, an honest
confession, and the right way to erase a mistaken mark. The tone stays close to
slice of life: a quiet day, a simple household problem, calm help from a grown-up,
and an ending image that shows what changed.

World premise
-------------
A child is making something kind and cheerful. While wearing a magical family hat,
the child makes a mark on the wrong household surface. The hat does not solve the
problem by itself. Instead, it glimmers and offers a useful hint only when the child
tells the truth. Then the child and a grown-up choose a sensible cleaning method
that can really erase that kind of mark from that kind of surface.

Core constraints
----------------
This world refuses combinations where the chosen cleaning method is not a reasonable
way to remove the mark from the surface. The domain knows about some methods but
will reject weak or mismatched repairs. The moral turn is also state-driven:
without honesty, the magical hint never appears, and the child has no grounded way
to solve the problem well.

Run it
------
    python storyworlds/worlds/gpt-5.4/erase_hat_problem_solving_moral_value_magic.py
    python storyworlds/worlds/gpt-5.4/erase_hat_problem_solving_moral_value_magic.py --mark crayon --surface wall
    python storyworlds/worlds/gpt-5.4/erase_hat_problem_solving_moral_value_magic.py --method eraser
    python storyworlds/worlds/gpt-5.4/erase_hat_problem_solving_moral_value_magic.py --all
    python storyworlds/worlds/gpt-5.4/erase_hat_problem_solving_moral_value_magic.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/erase_hat_problem_solving_moral_value_magic.py --verify
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
    traits: list[str] = field(default_factory=list)
    role: str = ""
    owner: str = ""
    attrs: dict = field(default_factory=dict)
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
            "mother": "mom",
            "father": "dad",
            "grandmother": "grandma",
            "grandfather": "grandpa",
        }.get(self.type, self.type)


@dataclass
class Activity:
    id: str
    intro: str
    making: str
    object_word: str
    kind_goal: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Mark:
    id: str
    label: str
    phrase: str
    leaves: str
    washable: bool
    needs: set[str]
    tags: set[str] = field(default_factory=set)


@dataclass
class Surface:
    id: str
    label: str
    phrase: str
    room: str
    article: str
    texture: str
    takes_paper: bool = False
    tags: set[str] = field(default_factory=set)

    @property
    def the(self) -> str:
        return f"the {self.label}"


@dataclass
class Method:
    id: str
    label: str
    sense: int
    removes: set[str]
    surfaces: set[str]
    prep: str
    action: str
    qa_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Hat:
    id: str
    label: str
    phrase: str
    glow: str
    whisper: str
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


def _r_mark_worry(world: World) -> list[str]:
    mark = world.get("mark")
    surface = world.get("surface")
    child = world.get("child")
    out: list[str] = []
    if mark.meters["on_surface"] >= THRESHOLD and surface.meters["messy"] < THRESHOLD:
        sig = ("mess", surface.id)
        if sig not in world.fired:
            world.fired.add(sig)
            surface.meters["messy"] += 1
            child.memes["worry"] += 1
            out.append("__mess__")
    return out


def _r_honest_magic(world: World) -> list[str]:
    child = world.get("child")
    hat = world.get("hat")
    if child.memes["honesty"] >= THRESHOLD and hat.meters["hint_ready"] < THRESHOLD:
        sig = ("hint", hat.id)
        if sig not in world.fired:
            world.fired.add(sig)
            hat.meters["hint_ready"] += 1
            child.memes["hope"] += 1
            return ["__hint__"]
    return []


def _r_erased_relief(world: World) -> list[str]:
    surface = world.get("surface")
    child = world.get("child")
    if surface.meters["clean"] >= THRESHOLD and child.memes["relief"] < THRESHOLD:
        sig = ("relief", child.id)
        if sig not in world.fired:
            world.fired.add(sig)
            child.memes["relief"] += 1
            child.memes["pride"] += 1
            return ["__relief__"]
    return []


CAUSAL_RULES = [
    Rule("mark_worry", "physical", _r_mark_worry),
    Rule("honest_magic", "moral", _r_honest_magic),
    Rule("erased_relief", "emotional", _r_erased_relief),
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


def method_works(mark: Mark, surface: Surface, method: Method) -> bool:
    return (
        mark.id in method.removes
        and surface.id in method.surfaces
        and method.sense >= SENSE_MIN
    )


def sensible_methods() -> list[Method]:
    return [m for m in METHODS.values() if m.sense >= SENSE_MIN]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for activity in ACTIVITIES:
        for mid, mark in MARKS.items():
            for sid, surface in SURFACES.items():
                if surface.takes_paper:
                    continue
                for meth_id, method in METHODS.items():
                    if method_works(mark, surface, method):
                        combos.append((activity, mid, sid, meth_id))
    return combos


def predict_success(world: World, method: Method) -> bool:
    sim = world.copy()
    mark = MARKS[sim.facts["mark_cfg"].id]
    surface = SURFACES[sim.facts["surface_cfg"].id]
    if method_works(mark, surface, method):
        sim.get("surface").meters["clean"] += 1
        sim.get("surface").meters["messy"] = 0
        sim.get("mark").meters["on_surface"] = 0
    propagate(sim, narrate=False)
    return sim.get("surface").meters["clean"] >= THRESHOLD


def introduce(world: World, child: Entity, grown: Entity, activity: Activity, hat: Hat) -> None:
    child.memes["joy"] += 1
    world.say(
        f"On a slow afternoon at home, {child.id} sat at the kitchen table with "
        f"{grown.label_word} and worked on {activity.intro}."
    )
    world.say(
        f"Before they began, {grown.label_word} let {child.id} wear {hat.phrase}. "
        f"It looked ordinary in the sun, but everyone in the family knew it was a little magical."
    )


def start_making(world: World, child: Entity, activity: Activity, mark: Mark, surface: Surface) -> None:
    world.say(
        f"{child.id} wanted to make {activity.making}. {child.pronoun().capitalize()} held "
        f"{mark.phrase} carefully and tried to add one more bright line."
    )
    world.say(
        f"But the line slid past the paper and landed on {surface.article} {surface.label}. "
        f"A {mark.leaves} mark showed up where it did not belong."
    )


def do_mark(world: World) -> None:
    world.get("mark").meters["on_surface"] += 1
    propagate(world, narrate=False)


def pause_and_hide(world: World, child: Entity, surface: Surface) -> None:
    if child.memes["worry"] >= THRESHOLD:
        world.say(
            f"{child.id} froze. The room felt quieter all at once, and {child.pronoun()} looked at "
            f"{surface.the} and then down at {child.pronoun('possessive')} shoes."
        )
        child.memes["tempted_hide"] += 1


def tell_truth(world: World, child: Entity, grown: Entity) -> None:
    child.memes["honesty"] += 1
    child.memes["fear"] += 0.5
    propagate(world, narrate=False)
    world.say(
        f'"{grown.label_word.capitalize()}," {child.id} said softly, "I made a mark in the wrong place. '
        f'I do not want to hide it. Will you help me fix it?"'
    )


def magic_hint(world: World, child: Entity, hat: Hat, mark: Mark, surface: Surface) -> None:
    if world.get("hat").meters["hint_ready"] >= THRESHOLD:
        world.say(
            f"At once, {hat.label} {hat.glow}. A warm tickle brushed {child.id}'s forehead, and "
            f"{hat.whisper} about how {mark.label} on {surface.label} should be erased the gentle way."
        )


def adult_response(world: World, grown: Entity, child: Entity, method: Method, surface: Surface) -> None:
    child.memes["love"] += 1
    world.say(
        f"{grown.label_word.capitalize()} did not scold. {grown.pronoun().capitalize()} knelt beside "
        f"{child.id}, touched {child.pronoun('possessive')} shoulder, and said, "
        f'"Thank you for telling the truth. Problems grow smaller when we solve them together."'
    )
    world.say(
        f"Then {grown.pronoun()} {method.prep}."
    )


def clean_success(world: World, child: Entity, method: Method, surface: Surface, activity: Activity) -> None:
    world.get("surface").meters["clean"] += 1
    world.get("surface").meters["messy"] = 0
    world.get("mark").meters["on_surface"] = 0
    child.memes["care"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{child.id} {method.action}. Little by little, the stray mark faded and then disappeared from "
        f"{surface.the}."
    )
    world.say(
        f"Soon {surface.the} looked right again, and {child.id} let out the breath {child.pronoun()} "
        f"had been holding."
    )
    world.say(
        f"After that, {grown_word(world)} helped {child.id} tape a fresh sheet of paper in the proper spot, "
        f"and {child.pronoun()} finished {activity.kind_goal} there instead."
    )


def ending(world: World, child: Entity, grown: Entity, hat: Hat) -> None:
    child.memes["joy"] += 1
    world.say(
        f"When the work was done, {child.id} lifted {hat.label} a little and smiled. "
        f"{grown.label_word.capitalize()} smiled back."
    )
    world.say(
        f"The magic in the hat seemed brighter than before, not because it had erased anything by itself, "
        f"but because honesty and careful thinking had turned a mistake into a solved problem."
    )


def grown_word(world: World) -> str:
    return world.get("grown").label_word


def tell(
    activity: Activity,
    mark: Mark,
    surface: Surface,
    method: Method,
    hat_cfg: Hat,
    child_name: str = "Mia",
    child_type: str = "girl",
    grown_type: str = "grandmother",
    grown_name: str = "Grandma",
    child_trait: str = "careful",
) -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_type, role="child", traits=[child_trait]))
    grown = world.add(Entity(id=grown_name, kind="character", type=grown_type, role="grown", label="the grown-up"))
    hat = world.add(Entity(id="hat", type="hat", label=hat_cfg.label))
    world.add(Entity(id="mark", type="mark", label=mark.label))
    world.add(Entity(id="surface", type="surface", label=surface.label))
    world.facts.update(
        child=child,
        grown=grown,
        hat_cfg=hat_cfg,
        mark_cfg=mark,
        surface_cfg=surface,
        method_cfg=method,
        activity=activity,
    )

    introduce(world, child, grown, activity, hat_cfg)
    start_making(world, child, activity, mark, surface)
    do_mark(world)
    world.para()
    pause_and_hide(world, child, surface)
    tell_truth(world, child, grown)
    magic_hint(world, child, hat_cfg, mark, surface)
    world.para()
    adult_response(world, grown, child, method, surface)
    clean_success(world, child, method, surface, activity)
    world.para()
    ending(world, child, grown, hat_cfg)

    world.facts.update(
        solved=world.get("surface").meters["clean"] >= THRESHOLD,
        confessed=child.memes["honesty"] >= THRESHOLD,
        hint_given=world.get("hat").meters["hint_ready"] >= THRESHOLD,
    )
    return world


ACTIVITIES = {
    "card": Activity(
        "card",
        "a thank-you card for a neighbor",
        "a card with a big yellow sun and tiny blue flowers",
        "card",
        "the kind card",
        tags={"kindness", "card"},
    ),
    "sign": Activity(
        "sign",
        "a welcome sign for the front door",
        "a welcome sign with curly letters and a little bird",
        "sign",
        "the welcome sign",
        tags={"kindness", "sign"},
    ),
    "list": Activity(
        "list",
        "a helper list for afternoon chores",
        "a helper list with boxes to tick and cheerful stars",
        "list",
        "the helper list",
        tags={"helping", "list"},
    ),
}

MARKS = {
    "pencil": Mark(
        "pencil",
        "pencil",
        "a soft pencil",
        "gray",
        True,
        {"eraser"},
        tags={"pencil", "erase"},
    ),
    "crayon": Mark(
        "crayon",
        "crayon",
        "a waxy crayon",
        "waxy red",
        True,
        {"soapy_cloth", "damp_sponge"},
        tags={"crayon", "erase"},
    ),
    "washable_marker": Mark(
        "washable_marker",
        "washable marker",
        "a blue washable marker",
        "blue",
        True,
        {"damp_sponge", "soapy_cloth"},
        tags={"marker", "erase"},
    ),
}

SURFACES = {
    "wall": Surface(
        "wall",
        "wall",
        "the painted kitchen wall",
        "kitchen",
        "the",
        "painted",
        tags={"wall", "home"},
    ),
    "table": Surface(
        "table",
        "table",
        "the wooden table",
        "kitchen",
        "the",
        "wooden",
        tags={"table", "home"},
    ),
    "window": Surface(
        "window",
        "window",
        "the sunny window",
        "kitchen",
        "the",
        "glass",
        tags={"window", "home"},
    ),
    "paper": Surface(
        "paper",
        "paper",
        "the drawing paper",
        "kitchen",
        "the",
        "flat",
        takes_paper=True,
        tags={"paper"},
    ),
}

METHODS = {
    "eraser": Method(
        "eraser",
        "eraser",
        3,
        {"pencil"},
        {"wall", "table", "window"},
        "picked up a clean pink eraser and tested a small corner first",
        "rubbed with the eraser in small circles",
        "used a clean eraser to rub the pencil mark away",
        tags={"eraser", "problem_solving"},
    ),
    "damp_sponge": Method(
        "damp_sponge",
        "damp sponge",
        3,
        {"washable_marker", "crayon"},
        {"wall", "table", "window"},
        "wet a soft sponge, squeezed it almost dry, and showed how to wipe gently",
        "wiped with the damp sponge, careful not to spread the color farther",
        "wiped the mark away with a damp sponge",
        tags={"sponge", "problem_solving"},
    ),
    "soapy_cloth": Method(
        "soapy_cloth",
        "soapy cloth",
        2,
        {"washable_marker", "crayon"},
        {"wall", "table", "window"},
        "dabbed a cloth in a little warm soapy water and folded it into a neat square",
        "blotted and wiped with the soapy cloth until the color lifted",
        "cleaned the mark off with a warm soapy cloth",
        tags={"soap", "problem_solving"},
    ),
    "paper_towel": Method(
        "paper_towel",
        "dry paper towel",
        1,
        {"pencil", "washable_marker", "crayon"},
        {"wall", "table", "window"},
        "grabbed a dry paper towel",
        "scrubbed with the dry towel, but the mark only smeared or stayed put",
        "tried a dry paper towel",
        tags={"weak_fix"},
    ),
}

HATS = {
    "patchwork": Hat(
        "patchwork",
        "the patchwork hat",
        "Grandma's patchwork hat with a ribbon the color of plums",
        "gave a tiny silver shimmer at the brim",
        "it seemed to whisper one sensible hint",
        tags={"hat", "magic"},
    ),
    "straw_star": Hat(
        "straw_star",
        "the straw hat",
        "a straw hat with one stitched gold star",
        "gave off a soft golden blink",
        "it seemed to hum the next careful step",
        tags={"hat", "magic"},
    ),
}

GIRL_NAMES = ["Mia", "Lily", "Nora", "Ava", "Rose", "Zoe", "Ella", "Anna"]
BOY_NAMES = ["Ben", "Leo", "Sam", "Max", "Theo", "Noah", "Eli", "Finn"]
TRAITS = ["careful", "kind", "curious", "thoughtful", "gentle", "helpful"]


@dataclass
class StoryParams:
    activity: str
    mark: str
    surface: str
    method: str
    hat: str
    child_name: str
    child_type: str
    grown_type: str
    trait: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "erase": [
        (
            "What does erase mean?",
            "To erase means to remove a mark, line, or writing so it is gone or much harder to see. People erase carefully so they do not damage the thing underneath.",
        )
    ],
    "eraser": [
        (
            "What is an eraser used for?",
            "An eraser rubs away pencil marks. It works best on pencil and not on every kind of mark.",
        )
    ],
    "sponge": [
        (
            "Why would someone use a damp sponge to clean a mark?",
            "A damp sponge can lift some washable color from a smooth surface. Using only a little water helps keep the mess from spreading.",
        )
    ],
    "soap": [
        (
            "Why can soapy water help clean?",
            "Soap helps loosen dirt and some marks so they can be wiped away. A little soap is often enough when the mark is washable.",
        )
    ],
    "hat": [
        (
            "What is a hat for?",
            "A hat sits on your head and can keep off sun or add style. In stories, a magical hat can also stand for wisdom or a special family memory.",
        )
    ],
    "magic": [
        (
            "What kind of magic is in this story?",
            "The magic does not do all the work. It gives a gentle hint, and the people still have to choose the right fix and do the careful cleaning themselves.",
        )
    ],
    "honesty": [
        (
            "Why is telling the truth important after a mistake?",
            "Telling the truth helps people solve the real problem faster. It also shows courage and lets others trust you.",
        )
    ],
    "problem_solving": [
        (
            "What is problem solving?",
            "Problem solving means noticing what went wrong, thinking about what could help, and trying a sensible plan. Good problem solving is calm, careful, and honest.",
        )
    ],
    "kindness": [
        (
            "What does kindness look like when someone makes a mistake?",
            "Kindness can sound like a calm voice, helpful hands, and a chance to fix the problem. It helps someone learn instead of only feeling ashamed.",
        )
    ],
}

KNOWLEDGE_ORDER = ["erase", "eraser", "sponge", "soap", "hat", "magic", "honesty", "problem_solving", "kindness"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    grown = f["grown"]
    mark = f["mark_cfg"]
    surface = f["surface_cfg"]
    hat = f["hat_cfg"]
    activity = f["activity"]
    return [
        'Write a short slice-of-life story for a 3-to-5-year-old that includes the words "erase" and "hat", with a small magical touch and a problem that gets solved kindly.',
        f"Tell a gentle home story where {child.id} makes a {mark.label} mark on a {surface.label}, tells the truth, and gets help from {grown.label_word} while wearing {hat.label}.",
        f"Write a simple story about making {activity.object_word}, an honest confession, and careful problem solving, where magic gives only a hint and the child still has to help erase the mistake.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    grown = f["grown"]
    mark = f["mark_cfg"]
    surface = f["surface_cfg"]
    method = f["method_cfg"]
    activity = f["activity"]
    hat = f["hat_cfg"]
    out: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, a child at home with {grown.label_word}, and {hat.label}. The story follows a small mistake and how they fix it together.",
        ),
        (
            f"What was {child.id} trying to make?",
            f"{child.id} was trying to make {activity.making}. The kind project matters because the mistake happens while {child.pronoun()} is doing something thoughtful.",
        ),
        (
            f"What problem happened?",
            f"A stray {mark.label} mark landed on the {surface.label} instead of staying on the paper. That unexpected mark is the problem they need to erase.",
        ),
        (
            f"Why did the hat give a hint?",
            f"The hat gave a magical hint after {child.id} told the truth about the mistake. In this story, the magic wakes up when honesty appears.",
        ),
        (
            f"How did {child.id} and {grown.label_word} solve the problem?",
            f"They used {method.label} and cleaned the mark the careful way. The plan worked because {method.qa_text} on the {surface.label}.",
        ),
        (
            "What moral did the story teach?",
            f"It taught that telling the truth after a mistake is brave and helpful. Honesty let the real problem be solved instead of hidden.",
        ),
    ]
    return out


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"erase", "hat", "magic", "honesty", "problem_solving", "kindness"}
    mark = world.facts["mark_cfg"]
    method = world.facts["method_cfg"]
    if method.id == "eraser":
        tags.add("eraser")
    if method.id == "damp_sponge":
        tags.add("sponge")
    if method.id == "soapy_cloth":
        tags.add("soap")
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
        lines.append(f"  {ent.id:8} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("card", "pencil", "table", "eraser", "patchwork", "Mia", "girl", "grandmother", "careful"),
    StoryParams("sign", "washable_marker", "window", "damp_sponge", "straw_star", "Ben", "boy", "grandfather", "curious"),
    StoryParams("list", "crayon", "wall", "soapy_cloth", "patchwork", "Nora", "girl", "mother", "helpful"),
    StoryParams("card", "washable_marker", "table", "damp_sponge", "straw_star", "Leo", "boy", "father", "thoughtful"),
]


def explain_rejection(mark: Mark, surface: Surface, method: Method) -> str:
    if method.sense < SENSE_MIN:
        return (
            f"(No story: using {method.label} to erase {mark.label} from the {surface.label} "
            f"is too weak or messy to be the sensible fix. Choose a kinder, more reliable method.)"
        )
    return (
        f"(No story: {method.label} is not a reasonable way to erase {mark.label} from the "
        f"{surface.label}. Pick a method that really matches both the mark and the surface.)"
    )


ASP_RULES = r"""
reasonable_method(M) :- method(M), sense(M,S), sense_min(K), S >= K.
works(Mark, Surface, Method) :-
    removable_by(Mark, Method),
    allowed_on(Method, Surface),
    reasonable_method(Method).

valid(Activity, Mark, Surface, Method) :-
    activity(Activity), mark(Mark), surface(Surface), method(Method),
    not paper_surface(Surface),
    works(Mark, Surface, Method).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for aid in ACTIVITIES:
        lines.append(asp.fact("activity", aid))
    for mid, mark in MARKS.items():
        lines.append(asp.fact("mark", mid))
        for need in sorted(mark.needs):
            lines.append(asp.fact("removable_by", mid, need))
    for sid, surface in SURFACES.items():
        lines.append(asp.fact("surface", sid))
        if surface.takes_paper:
            lines.append(asp.fact("paper_surface", sid))
    for mid, method in METHODS.items():
        lines.append(asp.fact("method", mid))
        lines.append(asp.fact("sense", mid, method.sense))
        for m in sorted(method.removes):
            lines.append(asp.fact("removable_by", m, mid))
        for s in sorted(method.surfaces):
            lines.append(asp.fact("allowed_on", mid, s))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("Empty story from smoke test.")
        print("OK: smoke-test generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a magical hat, an honest confession, and the right way to erase a mistaken mark."
    )
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--mark", choices=MARKS)
    ap.add_argument("--surface", choices=SURFACES)
    ap.add_argument("--method", choices=METHODS)
    ap.add_argument("--hat", choices=HATS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--grown", choices=["mother", "father", "grandmother", "grandfather"])
    ap.add_argument("--name")
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.surface == "paper":
        raise StoryError("(No story: a mark on the paper belongs on the project, so there is no household problem to solve.)")
    if args.mark and args.surface and args.method:
        if not method_works(MARKS[args.mark], SURFACES[args.surface], METHODS[args.method]):
            raise StoryError(explain_rejection(MARKS[args.mark], SURFACES[args.surface], METHODS[args.method]))

    combos = [
        c for c in valid_combos()
        if (args.activity is None or c[0] == args.activity)
        and (args.mark is None or c[1] == args.mark)
        and (args.surface is None or c[2] == args.surface)
        and (args.method is None or c[3] == args.method)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    activity, mark, surface, method = rng.choice(sorted(combos))
    hat = args.hat or rng.choice(sorted(HATS))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    grown = args.grown or rng.choice(["mother", "father", "grandmother", "grandfather"])
    trait = rng.choice(TRAITS)
    return StoryParams(activity, mark, surface, method, hat, name, gender, grown, trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        ACTIVITIES[params.activity],
        MARKS[params.mark],
        SURFACES[params.surface],
        METHODS[params.method],
        HATS[params.hat],
        child_name=params.child_name,
        child_type=params.child_type,
        grown_type=params.grown_type,
        grown_name={"mother": "Mom", "father": "Dad", "grandmother": "Grandma", "grandfather": "Grandpa"}[params.grown_type],
        child_trait=params.trait,
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
        print(asp_program("", "#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (activity, mark, surface, method) combos:\n")
        for a, m, s, meth in combos:
            print(f"  {a:8} {m:16} {s:8} {meth}")
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
            header = f"### {p.child_name}: {p.mark} on {p.surface} with {p.method}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
