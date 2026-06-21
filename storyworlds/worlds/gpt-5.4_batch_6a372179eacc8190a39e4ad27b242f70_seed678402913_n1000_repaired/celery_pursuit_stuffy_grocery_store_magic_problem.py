#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/celery_pursuit_stuffy_grocery_store_magic_problem.py
===============================================================================

A standalone story world for a tiny grocery-store adventure with a missing
stuffy, a rustling bunch of celery, practical problem solving, and a small
magical twist.

The core premise is narrow on purpose:

* A child brings a beloved stuffed toy to the grocery store.
* The air near the produce misters feels stuffy, and a strange shimmer flickers
  in a bunch of celery.
* During the child's eager pursuit of the shimmer, the stuffy goes missing.
* The celery's magic points toward the hiding place.
* A sensible store problem-solving method retrieves the toy.
* Twist: the celery was quietly helping all along.

The world model enforces one main constraint:
a retrieval method must actually work for the chosen hiding place. Weak or
mismatched fixes are refused with a StoryError.

Run it
------
    python storyworlds/worlds/gpt-5.4/celery_pursuit_stuffy_grocery_store_magic_problem.py
    python storyworlds/worlds/gpt-5.4/celery_pursuit_stuffy_grocery_store_magic_problem.py --hide under_shelf --solution grabber
    python storyworlds/worlds/gpt-5.4/celery_pursuit_stuffy_grocery_store_magic_problem.py --hide high_display --solution flashlight
    python storyworlds/worlds/gpt-5.4/celery_pursuit_stuffy_grocery_store_magic_problem.py --all
    python storyworlds/worlds/gpt-5.4/celery_pursuit_stuffy_grocery_store_magic_problem.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/celery_pursuit_stuffy_grocery_store_magic_problem.py --verify
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
        female = {"girl", "mother", "mom", "woman", "clerk_woman"}
        male = {"boy", "father", "dad", "man", "clerk_man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class MagicCue:
    id: str
    label: str
    start_text: str
    lead_text: str
    twist_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class HidingPlace:
    id: str
    label: str
    place_text: str
    found_text: str
    need: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Solution:
    id: str
    label: str
    action_text: str
    qa_text: str
    supports: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class ToyCfg:
    id: str
    label: str
    phrase: str
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


def _r_missing_toy(world: World) -> list[str]:
    toy = world.entities.get("toy")
    child = world.entities.get("child")
    parent = world.entities.get("parent")
    if toy is None or child is None or parent is None:
        return []
    if toy.meters["missing"] < THRESHOLD:
        return []
    sig = ("missing_toy", toy.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["worry"] += 1
    parent.memes["concern"] += 1
    return ["__missing__"]


def _r_magic_clue(world: World) -> list[str]:
    toy = world.entities.get("toy")
    clue = world.entities.get("clue")
    hide = world.entities.get("hide")
    if toy is None or clue is None or hide is None:
        return []
    if toy.meters["missing"] < THRESHOLD or clue.meters["glowing"] < THRESHOLD:
        return []
    sig = ("magic_clue", hide.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hide.meters["revealed"] += 1
    child = world.entities.get("child")
    if child is not None:
        child.memes["hope"] += 1
    return ["__clue__"]


def _r_retrieved(world: World) -> list[str]:
    toy = world.entities.get("toy")
    child = world.entities.get("child")
    parent = world.entities.get("parent")
    if toy is None or child is None or parent is None:
        return []
    if toy.meters["retrieved"] < THRESHOLD:
        return []
    sig = ("retrieved", toy.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    toy.meters["missing"] = 0.0
    child.memes["relief"] += 1
    child.memes["joy"] += 1
    child.memes["worry"] = 0.0
    parent.memes["relief"] += 1
    return ["__retrieved__"]


CAUSAL_RULES: list[Rule] = [
    Rule(name="missing_toy", tag="emotional", apply=_r_missing_toy),
    Rule(name="magic_clue", tag="magic", apply=_r_magic_clue),
    Rule(name="retrieved", tag="resolution", apply=_r_retrieved),
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
                produced.extend(s for s in lines if not s.startswith("__"))
    if narrate:
        for line in produced:
            world.say(line)
    return produced


MAGIC = {
    "star_tie": MagicCue(
        id="star_tie",
        label="star twist tie",
        start_text="a silver star twist tie on the celery blinked once, as if it had opened a tiny eye",
        lead_text="The silver star skipped ahead, making the celery leaves rustle like a soft green map.",
        twist_text="When the trouble was over, the star twist tie winked once more and sat still, as if the celery had only been a bunch of celery all along.",
        tags={"magic", "celery"},
    ),
    "green_glow": MagicCue(
        id="green_glow",
        label="green glow",
        start_text="a small green glow ran up the celery stalks and hung there like a lantern made of leaf-light",
        lead_text="The green glow bobbed onward between crates, turning the celery into a row of pointing fingers.",
        twist_text="After the rescue, the glow melted back into the pale ribs of the celery, leaving only a fresh green smell behind.",
        tags={"magic", "celery"},
    ),
    "leaf_whisper": MagicCue(
        id="leaf_whisper",
        label="leaf whisper",
        start_text='the celery leaves gave a dry little whisper that sounded almost like, "This way"',
        lead_text="The whisper seemed to hop from bunch to bunch, gently pulling them onward.",
        twist_text="At the end, the whisper faded into an ordinary produce rustle, and nobody but the child seemed to notice.",
        tags={"magic", "celery"},
    ),
}

HIDING_PLACES = {
    "under_shelf": HidingPlace(
        id="under_shelf",
        label="under the bottom shelf",
        place_text="it had skidded under the bottom shelf where apples sat in neat red rows",
        found_text="far under the bottom shelf, just beyond small reaching fingers",
        need="low_reach",
        tags={"shelf"},
    ),
    "high_display": HidingPlace(
        id="high_display",
        label="on top of the cereal display",
        place_text="it had landed on top of a tall cereal display after bouncing off a box corner",
        found_text="perched on top of the cereal display, looking very small and very far away",
        need="high_reach",
        tags={"high", "cereal"},
    ),
    "cart_rack": HidingPlace(
        id="cart_rack",
        label="between the nested carts",
        place_text="it had been tucked between two nested shopping carts near the entrance",
        found_text="wedged between the shiny wire bars of the nested carts",
        need="cart_release",
        tags={"cart"},
    ),
}

SOLUTIONS = {
    "grabber": Solution(
        id="grabber",
        label="store grabber",
        action_text="borrowed the long store grabber from the clerk and carefully pinched the toy by one floppy ear",
        qa_text="used the long store grabber to reach the toy safely",
        supports={"low_reach"},
        tags={"grabber", "problem_solving"},
    ),
    "step_stool": Solution(
        id="step_stool",
        label="rolling step stool",
        action_text="asked the clerk to lock a rolling step stool in place, then the grown-up climbed carefully and lifted the toy down",
        qa_text="used a locked rolling step stool with the clerk's help to bring the toy down",
        supports={"high_reach"},
        tags={"step_stool", "problem_solving", "clerk"},
    ),
    "cart_release": Solution(
        id="cart_release",
        label="cart release trick",
        action_text="worked with the clerk to pull one cart back, making a safe little gap where the toy could be lifted out",
        qa_text="pulled one nested cart back with the clerk so the toy could be lifted out",
        supports={"cart_release"},
        tags={"cart", "problem_solving", "clerk"},
    ),
    "flashlight": Solution(
        id="flashlight",
        label="phone flashlight",
        action_text="shone a light into the gap and looked carefully",
        qa_text="used a light to look more carefully",
        supports=set(),
        tags={"flashlight"},
    ),
}

TOYS = {
    "bunny": ToyCfg(
        id="bunny",
        label="bunny",
        phrase="a soft gray bunny with one bent ear",
        tags={"stuffy"},
    ),
    "dragon": ToyCfg(
        id="dragon",
        label="dragon",
        phrase="a small green dragon with stitched gold wings",
        tags={"stuffy"},
    ),
    "bear": ToyCfg(
        id="bear",
        label="bear",
        phrase="a round brown bear with a blue scarf",
        tags={"stuffy"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Anna", "Maya", "Nora", "Rose"]
BOY_NAMES = ["Tom", "Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Noah", "Eli", "Theo"]
TRAITS = ["curious", "brisk", "careful", "eager", "observant", "hopeful"]


def retrieval_works(hide: HidingPlace, solution: Solution) -> bool:
    return hide.need in solution.supports


def valid_combos() -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    for hide_id, hide in HIDING_PLACES.items():
        for solution_id, solution in SOLUTIONS.items():
            if retrieval_works(hide, solution):
                out.append((hide_id, solution_id))
    return out


def explain_rejection(hide: HidingPlace, solution: Solution) -> str:
    return (
        f"(No story: {solution.label} does not actually solve a toy stuck {hide.label}. "
        f"This world only allows fixes that can really reach the hiding place.)"
    )


def predict_retrieval(hide: HidingPlace, solution: Solution) -> dict:
    return {
        "works": retrieval_works(hide, solution),
        "need": hide.need,
    }


def introduce_store(world: World, child: Entity, parent: Entity, toy: Entity, trait: str) -> None:
    child.memes["wonder"] += 1
    world.say(
        f"{child.id} came to the grocery store with {child.pronoun('possessive')} "
        f"{toy.label}, tucked safely under {child.pronoun('possessive')} arm."
    )
    world.say(
        f"The store felt bright and busy, but the produce corner was warm and a little stuffy, "
        f"with mist curling over the greens. {child.id}, a {trait} {child.type}, liked to imagine "
        f"that every aisle was the start of an adventure."
    )
    world.say(
        f"{parent.label_word.capitalize()} pushed the cart toward the vegetables while "
        f"{child.id} marched beside it like a tiny explorer."
    )


def magic_begins(world: World, child: Entity, magic: MagicCue) -> None:
    clue = world.get("clue")
    clue.meters["glowing"] += 1
    child.memes["curiosity"] += 1
    world.say(
        f"Then, right beside the celery, {magic.start_text}."
    )
    world.say(
        f"{child.id} gasped. In a blink, curiosity turned into pursuit."
    )


def pursuit_and_loss(world: World, child: Entity, toy: Entity, hide: HidingPlace, magic: MagicCue) -> None:
    toy.meters["missing"] += 1
    child.memes["haste"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{magic.lead_text} {child.id} hurried after it past oranges, potatoes, and stacks of soup."
    )
    world.say(
        f"But in the quick turn around the cart, {child.pronoun('possessive')} {toy.label} slipped loose. "
        f"A soft thump came, and then the toy was gone."
    )
    world.say(
        f"When {child.id} stopped and looked around, {child.pronoun('possessive')} heart dropped. "
        f"The {toy.label} was missing."
    )
    world.say(
        f"Together they searched until they finally saw where it had gone: {hide.place_text}."
    )


def clue_reveals(world: World, child: Entity, parent: Entity, magic: MagicCue, hide: HidingPlace) -> None:
    propagate(world, narrate=False)
    child.memes["focus"] += 1
    world.say(
        f'"Don\'t worry," said {parent.label_word}, keeping {parent.pronoun("possessive")} voice calm. '
        f'"We can solve this if we look carefully."'
    )
    if world.get("hide").meters["revealed"] >= THRESHOLD:
        world.say(
            f"Just then the celery shimmer pointed again, and they spotted the toy {hide.found_text}."
        )


def solve_problem(world: World, child: Entity, parent: Entity, solution: Solution) -> None:
    toy = world.get("toy")
    prediction = predict_retrieval(HIDING_PLACES[world.facts["hide_cfg"].id], solution)
    world.facts["predicted_need"] = prediction["need"]
    world.facts["predicted_works"] = prediction["works"]
    if not prediction["works"]:
        raise StoryError("Internal invalid story: retrieval method does not fit the hiding place.")
    toy.meters["retrieved"] += 1
    propagate(world, narrate=False)
    world.say(
        f"So {parent.label_word} {solution.action_text}."
    )
    world.say(
        f"A moment later, the {toy.label} was back in {child.id}'s arms."
    )


def ending_twist(world: World, child: Entity, toy: Entity, magic: MagicCue) -> None:
    child.memes["gratitude"] += 1
    world.say(
        f"{child.id} hugged the {toy.label} so tightly that its soft body squished up under {child.pronoun('possessive')} chin."
    )
    world.say(
        "For one quiet second, the whole grocery store seemed to pause: carts, lights, and even the humming coolers."
    )
    world.say(
        f"Then {magic.twist_text}"
    )
    world.say(
        f"{child.id} looked back at the celery and smiled. Maybe it had been magic. Maybe it had only been leaves. "
        f"Either way, the adventure ended with the lost friend found, and the produce aisle no longer felt stuffy at all."
    )


def tell(
    *,
    magic_id: str,
    hide_id: str,
    solution_id: str,
    toy_id: str,
    child_name: str,
    child_gender: str,
    parent_type: str,
    trait: str,
) -> World:
    magic = MAGIC[magic_id]
    hide = HIDING_PLACES[hide_id]
    solution = SOLUTIONS[solution_id]
    toy_cfg = TOYS[toy_id]

    if not retrieval_works(hide, solution):
        raise StoryError(explain_rejection(hide, solution))

    world = World()
    child = world.add(Entity(
        id=child_name,
        kind="character",
        type=child_gender,
        label=child_name,
        role="child",
        traits=[trait],
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=parent_type,
        label="the parent",
        role="parent",
    ))
    toy = world.add(Entity(
        id="toy",
        kind="thing",
        type="toy",
        label=toy_cfg.label,
        phrase=toy_cfg.phrase,
        role="toy",
        tags=set(toy_cfg.tags),
    ))
    clue = world.add(Entity(
        id="clue",
        kind="thing",
        type="magic",
        label=magic.label,
        role="magic",
        tags=set(magic.tags),
    ))
    world.add(Entity(
        id="hide",
        kind="thing",
        type="place",
        label=hide.label,
        role="hide",
        tags=set(hide.tags),
    ))

    introduce_store(world, child, parent, toy, trait)
    world.para()
    magic_begins(world, child, magic)
    pursuit_and_loss(world, child, toy, hide, magic)
    world.para()
    clue_reveals(world, child, parent, magic, hide)
    solve_problem(world, child, parent, solution)
    world.para()
    ending_twist(world, child, toy, magic)

    world.facts.update(
        child=child,
        parent=parent,
        toy=toy,
        magic=magic,
        hide_cfg=hide,
        solution=solution,
        resolved=toy.meters["retrieved"] >= THRESHOLD,
        magical_help=world.get("hide").meters["revealed"] >= THRESHOLD,
        setting="grocery store",
    )
    return world


@dataclass
class StoryParams:
    magic: str
    hide: str
    solution: str
    toy: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "celery": [
        (
            "What is celery?",
            "Celery is a green vegetable with long crunchy stalks. People often find it in the produce section of a grocery store."
        )
    ],
    "stuffy": [
        (
            "What is a stuffy?",
            "A stuffy is a soft stuffed toy that a child may carry for comfort. Some children call it a stuffed animal or a plush toy."
        )
    ],
    "grabber": [
        (
            "What is a store grabber?",
            "A store grabber is a long tool that can pinch and pick things up from far away. It helps people reach something without crawling into a tight space."
        )
    ],
    "step_stool": [
        (
            "Why do grown-ups use a step stool for high places?",
            "A sturdy step stool lets a grown-up reach something above eye level more safely. It is better than stretching or climbing on shelves."
        )
    ],
    "cart": [
        (
            "Why can toys get stuck between shopping carts?",
            "Nested carts have narrow wire gaps and moving parts. A small toy can slip into those spaces and be hard to pull out with fingers alone."
        )
    ],
    "problem_solving": [
        (
            "What does problem solving mean?",
            "Problem solving means looking at what is wrong, thinking carefully, and trying a fix that fits the problem. It is not just hurrying; it is choosing a useful next step."
        )
    ],
    "magic": [
        (
            "What is a magical clue in a story?",
            "A magical clue is a surprising sign that helps a character notice something important. In stories it can guide people, but they still have to act wisely."
        )
    ],
    "clerk": [
        (
            "What does a store clerk do?",
            "A store clerk helps shoppers and takes care of the store. A clerk may know where tools are and how to solve small problems safely."
        )
    ],
}
KNOWLEDGE_ORDER = ["celery", "stuffy", "magic", "problem_solving", "grabber", "step_stool", "cart", "clerk"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    toy = f["toy"]
    hide = f["hide_cfg"]
    solution = f["solution"]
    return [
        'Write an adventure story for a 3-to-5-year-old set in a grocery store that includes the words "celery", "pursuit", and "stuffy".',
        f"Tell a gentle magical adventure where {child.id} loses a beloved {toy.label} in a grocery store during a pursuit sparked by celery, then solves the problem by using {solution.label}.",
        f"Write a small story with a twist: a child thinks a strange sign in the produce aisle is only part of the store, but it quietly helps lead them to a toy lost {hide.label}.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    toy = f["toy"]
    magic = f["magic"]
    hide = f["hide_cfg"]
    solution = f["solution"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, {child.pronoun('possessive')} beloved {toy.label}, and {child.pronoun('possessive')} {parent.label_word} in a grocery store."
        ),
        (
            "What made the adventure begin?",
            f"It began when something strange happened near the celery and caught {child.id}'s eye. That magical sign turned curiosity into pursuit."
        ),
        (
            f"Why did {child.id} become upset?",
            f"{child.id} became upset because the {toy.label} slipped away during the chase and went missing. The toy mattered because it was a comforting stuffy, not just another thing from the store."
        ),
        (
            f"Where was the {toy.label}?",
            f"They found it {hide.found_text}. It was close enough to see but not easy for small hands to reach."
        ),
        (
            "How did they solve the problem?",
            f"They solved it when {parent.label_word} {solution.action_text}. That worked because the fix matched the place where the toy was stuck."
        ),
    ]
    if f.get("magical_help"):
        qa.append(
            (
                "What was the twist at the end?",
                f"The twist was that the celery seemed to have been helping all along. It gave a magical clue, but {child.id} and {parent.label_word} still had to solve the problem sensibly."
            )
        )
    qa.append(
        (
            f"How did {child.id} feel at the end?",
            f"{child.id} felt relieved and happy once the {toy.label} was back. The ending proves the change because the aisle that had felt stuffy and tense now felt calm and full of wonder."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = {"celery", "stuffy", "magic", "problem_solving"}
    solution = world.facts["solution"]
    tags |= set(solution.tags)
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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        magic="star_tie",
        hide="under_shelf",
        solution="grabber",
        toy="bunny",
        name="Lily",
        gender="girl",
        parent="mother",
        trait="observant",
    ),
    StoryParams(
        magic="green_glow",
        hide="high_display",
        solution="step_stool",
        toy="dragon",
        name="Max",
        gender="boy",
        parent="father",
        trait="eager",
    ),
    StoryParams(
        magic="leaf_whisper",
        hide="cart_rack",
        solution="cart_release",
        toy="bear",
        name="Mia",
        gender="girl",
        parent="mother",
        trait="careful",
    ),
]


ASP_RULES = r"""
needs(H, N) :- hiding(H), need(H, N).
works(H, S) :- needs(H, N), solution(S), supports(S, N).
valid(H, S) :- hiding(H), solution(S), works(H, S).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for hide_id, hide in HIDING_PLACES.items():
        lines.append(asp.fact("hiding", hide_id))
        lines.append(asp.fact("need", hide_id, hide.need))
    for solution_id, solution in SOLUTIONS.items():
        lines.append(asp.fact("solution", solution_id))
        for need in sorted(solution.supports):
            lines.append(asp.fact("supports", solution_id, need))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/2."))
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

    smoke_cases = list(CURATED)
    try:
        default_params = resolve_params(build_parser().parse_args([]), random.Random(123))
        smoke_cases.append(default_params)
    except StoryError as err:
        rc = 1
        print("SMOKE FAILURE while resolving defaults:", err)

    for i, params in enumerate(smoke_cases, 1):
        try:
            sample = generate(params)
            if not sample.story or "celery" not in sample.story.lower():
                raise StoryError("generated story was empty or missing required word 'celery'")
            if "pursuit" not in sample.story.lower():
                raise StoryError("generated story was missing required word 'pursuit'")
            if "stuffy" not in sample.story.lower():
                raise StoryError("generated story was missing required word 'stuffy'")
            _ = sample.to_dict()
            print(f"OK: smoke story {i} generated.")
        except Exception as err:
            rc = 1
            print(f"SMOKE FAILURE on case {i}: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A grocery-store adventure with celery magic, a missing stuffy, and practical problem solving."
    )
    ap.add_argument("--magic", choices=sorted(MAGIC))
    ap.add_argument("--hide", choices=sorted(HIDING_PLACES))
    ap.add_argument("--solution", choices=sorted(SOLUTIONS))
    ap.add_argument("--toy", choices=sorted(TOYS))
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible (hide, solution) combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP parity and run smoke generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.hide and args.solution:
        hide = HIDING_PLACES[args.hide]
        solution = SOLUTIONS[args.solution]
        if not retrieval_works(hide, solution):
            raise StoryError(explain_rejection(hide, solution))

    combos = [
        combo for combo in valid_combos()
        if (args.hide is None or combo[0] == args.hide)
        and (args.solution is None or combo[1] == args.solution)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    hide_id, solution_id = rng.choice(sorted(combos))
    magic_id = args.magic or rng.choice(sorted(MAGIC))
    toy_id = args.toy or rng.choice(sorted(TOYS))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(
        magic=magic_id,
        hide=hide_id,
        solution=solution_id,
        toy=toy_id,
        name=name,
        gender=gender,
        parent=parent,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.magic not in MAGIC:
        raise StoryError(f"(Invalid magic choice: {params.magic})")
    if params.hide not in HIDING_PLACES:
        raise StoryError(f"(Invalid hide choice: {params.hide})")
    if params.solution not in SOLUTIONS:
        raise StoryError(f"(Invalid solution choice: {params.solution})")
    if params.toy not in TOYS:
        raise StoryError(f"(Invalid toy choice: {params.toy})")

    world = tell(
        magic_id=params.magic,
        hide_id=params.hide,
        solution_id=params.solution,
        toy_id=params.toy,
        child_name=params.name,
        child_gender=params.gender,
        parent_type=params.parent,
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
        print(asp_program("", "#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (hide, solution) combos:\n")
        for hide_id, solution_id in combos:
            print(f"  {hide_id:12} {solution_id}")
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
            header = f"### {p.name}: {p.hide} with {p.solution}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
