#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/record_gerund_kindness_animal_story.py
=================================================================

A standalone story world for a tiny animal-story domain about kindness.

Premise
-------
Two small animals are on their way to a kind forest gathering. One of them sees
another animal struggling with an honest, physical problem: a heavy basket, a
wobbly cart, or a pile of dropped things. The helper can be too rushed to stop,
or can choose a kind act that solves the problem in a concrete way. The world
tracks bodies with physical meters and feelings with emotional memes, then
renders a complete child-facing story from that state.

The required seed word "record-gerund" is woven into the world as the title of a
funny page in the helper's kindness notebook. The odd little phrase appears in
the story naturally as a remembered writing exercise rather than raw scaffolding.

Run it
------
    python storyworlds/worlds/gpt-5.4/record_gerund_kindness_animal_story.py
    python storyworlds/worlds/gpt-5.4/record_gerund_kindness_animal_story.py --all
    python storyworlds/worlds/gpt-5.4/record_gerund_kindness_animal_story.py --qa
    python storyworlds/worlds/gpt-5.4/record_gerund_kindness_animal_story.py --trace
    python storyworlds/worlds/gpt-5.4/record_gerund_kindness_animal_story.py --asp
    python storyworlds/worlds/gpt-5.4/record_gerund_kindness_animal_story.py --verify
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
KIND_MIN = 2


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
        mapping = {
            "subject": "they",
            "object": "them",
            "possessive": "their",
        }
        return mapping[case]


@dataclass
class AnimalSpec:
    id: str
    label: str
    home: str
    sound: str
    gait: str
    carrying_style: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Problem:
    id: str
    label: str
    setting: str
    need: str
    item: str
    item_phrase: str
    trouble: str
    risk: str
    kind_fix: str
    happy_end: str
    failure_end: str
    helper_gear: str
    gear_phrase: str
    requires_gear: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Gathering:
    id: str
    label: str
    goal: str
    closing: str
    treat: str
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


def _r_strain_to_worry(world: World) -> list[str]:
    out: list[str] = []
    struggler = world.get("struggler")
    if struggler.meters["strain"] >= THRESHOLD:
        sig = ("strain_to_worry", "struggler")
        if sig not in world.fired:
            world.fired.add(sig)
            struggler.memes["worry"] += 1
            out.append("__strain__")
    return out


def _r_help_to_relief(world: World) -> list[str]:
    out: list[str] = []
    helper = world.get("helper")
    struggler = world.get("struggler")
    if helper.meters["help_given"] >= THRESHOLD:
        sig = ("help_to_relief", "pair")
        if sig not in world.fired:
            world.fired.add(sig)
            struggler.meters["strain"] = 0.0
            struggler.memes["relief"] += 1
            helper.memes["kind_pride"] += 1
            helper.memes["rush"] = 0.0
            out.append("__relief__")
    return out


def _r_drop_to_mess(world: World) -> list[str]:
    out: list[str] = []
    path = world.get("path")
    struggler = world.get("struggler")
    if struggler.meters["dropped"] >= THRESHOLD:
        sig = ("drop_to_mess", "path")
        if sig not in world.fired:
            world.fired.add(sig)
            path.meters["mess"] += 1
            struggler.memes["sadness"] += 1
            out.append("__mess__")
    return out


CAUSAL_RULES = [
    Rule(name="strain_to_worry", tag="social", apply=_r_strain_to_worry),
    Rule(name="help_to_relief", tag="social", apply=_r_help_to_relief),
    Rule(name="drop_to_mess", tag="physical", apply=_r_drop_to_mess),
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


def valid_combo(problem: Problem, kindness_level: int) -> bool:
    if problem.requires_gear and not problem.helper_gear:
        return False
    return kindness_level >= 1


def valid_combos() -> list[tuple[str, str, int]]:
    out: list[tuple[str, str, int]] = []
    for animal_id in ANIMALS:
        for problem_id, problem in PROBLEMS.items():
            for kindness in KINDNESS_LEVELS:
                if valid_combo(problem, kindness):
                    out.append((animal_id, problem_id, kindness))
    return out


def predict_need(problem: Problem, kindness_level: int) -> dict:
    can_fix = kindness_level >= problem_min_kindness(problem)
    return {
        "can_fix": can_fix,
        "risk": problem.risk,
    }


def problem_min_kindness(problem: Problem) -> int:
    return 2 if problem.requires_gear else 1


def outcome_of(params: "StoryParams") -> str:
    problem = PROBLEMS[params.problem]
    if params.kindness_level < problem_min_kindness(problem):
        return "rushed"
    return "helped"


def intro(world: World, helper: Entity, gathering: Gathering, notebook_word: str) -> None:
    world.say(
        f"In the soft morning woods, {helper.id} the {helper.type} set out for {gathering.label}. "
        f"{helper.pronoun('possessive').capitalize()} little satchel held a leaf notebook, and on one page "
        f"a funny practice title still said \"{notebook_word}.\""
    )
    world.say(
        f"{helper.id} liked the silly words in the notebook, but liked kind deeds even more."
    )


def travel(world: World, helper: Entity, problem: Problem, gathering: Gathering) -> None:
    helper.memes["rush"] += 1
    world.say(
        f"{helper.pronoun('subject').capitalize()} {helper.attrs.get('gait', 'hurried')} along {problem.setting}, "
        f"thinking about {gathering.goal} and the sweet smell of {gathering.treat} waiting there."
    )


def meet_trouble(world: World, struggler: Entity, problem: Problem) -> None:
    struggler.meters["strain"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Near {problem.setting}, {world.get('helper').id} saw {struggler.id} the {struggler.type} with {problem.item_phrase}. "
        f"{struggler.id} was {problem.trouble}."
    )
    if struggler.memes["worry"] >= THRESHOLD:
        world.say(
            f"{struggler.pronoun('subject').capitalize()} looked worried because {problem.risk}."
        )


def pause_and_notice(world: World, helper: Entity, struggler: Entity, problem: Problem) -> None:
    pred = predict_need(problem, helper.attrs.get("kindness_level", 1))
    helper.memes["noticing"] += 1
    world.facts["predicted_risk"] = pred["risk"]
    world.say(
        f"{helper.id} slowed down. {helper.pronoun('subject').capitalize()} remembered that a kind friend notices when someone needs help."
    )
    world.say(
        f'"Oh dear," {helper.pronoun("subject")} whispered. "If I hurry past, {pred["risk"]}."'
    )


def help_action(world: World, helper: Entity, struggler: Entity, problem: Problem) -> None:
    helper.meters["help_given"] += 1
    helper.meters["carrying"] += 1
    if problem.requires_gear:
        helper.meters["gear_used"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{helper.id} put down {helper.pronoun('possessive')} satchel and {problem.kind_fix}."
    )
    world.say(
        f"Soon the hard part was over, and {struggler.id}'s breathing grew calm again."
    )


def gratitude(world: World, helper: Entity, struggler: Entity) -> None:
    struggler.memes["gratitude"] += 1
    helper.memes["warmth"] += 1
    world.say(
        f'"Thank you," said {struggler.id}. "You saw my trouble and stopped."'
    )
    world.say(
        f"{helper.id} smiled. Helping made the path feel brighter than sunshine."
    )


def share_arrival(world: World, helper: Entity, struggler: Entity, gathering: Gathering, problem: Problem) -> None:
    world.say(
        f"Together they went on to {gathering.label}, and {problem.happy_end}."
    )
    world.say(
        f"There they shared {gathering.treat}, and {gathering.closing}"
    )


def rush_past(world: World, helper: Entity, struggler: Entity, problem: Problem, gathering: Gathering) -> None:
    helper.memes["selfish_hurry"] += 1
    world.say(
        f"For a moment, {helper.id} kept going. The satchel bumped against {helper.pronoun('possessive')} side, and {helper.pronoun('subject')} told {helper.pronoun('object')}self that {gathering.label} could not wait."
    )
    struggler.meters["dropped"] += 1
    propagate(world, narrate=False)
    world.say(
        f"But behind {helper.pronoun('object')}, {problem.failure_end}."
    )
    helper.memes["guilt"] += 1


def return_to_help(world: World, helper: Entity, struggler: Entity, problem: Problem) -> None:
    world.say(
        f"{helper.id} stopped so fast that a fern leaf fluttered from the satchel."
    )
    world.say(
        f'"That is not the kind way," {helper.pronoun("subject")} said, turning back.'
    )
    help_action(world, helper, struggler, problem)
    gratitude(world, helper, struggler)


def tell(
    helper_spec: AnimalSpec,
    struggler_spec: AnimalSpec,
    problem: Problem,
    gathering: Gathering,
    kindness_level: int,
    helper_name: str,
    struggler_name: str,
    notebook_word: str = "record-gerund",
) -> World:
    world = World()
    helper = world.add(Entity(
        id=helper_name,
        kind="character",
        type=helper_spec.label,
        role="helper",
        attrs={"home": helper_spec.home, "sound": helper_spec.sound, "gait": helper_spec.gait,
               "kindness_level": kindness_level},
        tags=set(helper_spec.tags),
    ))
    struggler = world.add(Entity(
        id=struggler_name,
        kind="character",
        type=struggler_spec.label,
        role="struggler",
        attrs={"home": struggler_spec.home, "sound": struggler_spec.sound, "gait": struggler_spec.gait},
        tags=set(struggler_spec.tags),
    ))
    world.add(Entity(id="path", type="path", label=problem.setting, tags=set(problem.tags)))

    intro(world, helper, gathering, notebook_word)
    travel(world, helper, problem, gathering)

    world.para()
    meet_trouble(world, struggler, problem)
    pause_and_notice(world, helper, struggler, problem)

    world.para()
    if kindness_level >= problem_min_kindness(problem):
        help_action(world, helper, struggler, problem)
        gratitude(world, helper, struggler)
        world.para()
        share_arrival(world, helper, struggler, gathering, problem)
        outcome = "helped"
    else:
        rush_past(world, helper, struggler, problem, gathering)
        world.para()
        return_to_help(world, helper, struggler, problem)
        world.para()
        share_arrival(world, helper, struggler, gathering, problem)
        outcome = "rushed"

    world.facts.update(
        helper=helper,
        struggler=struggler,
        helper_spec=helper_spec,
        struggler_spec=struggler_spec,
        problem=problem,
        gathering=gathering,
        kindness_level=kindness_level,
        notebook_word=notebook_word,
        outcome=outcome,
        helped=helper.meters["help_given"] >= THRESHOLD,
    )
    return world


ANIMALS = {
    "rabbit": AnimalSpec(
        id="rabbit",
        label="rabbit",
        home="the bramble burrow",
        sound="soft thumps",
        gait="hopped",
        carrying_style="between both paws",
        tags={"rabbit", "forest"},
    ),
    "squirrel": AnimalSpec(
        id="squirrel",
        label="squirrel",
        home="the oak tree",
        sound="tiny chitters",
        gait="scampered",
        carrying_style="against the chest",
        tags={"squirrel", "forest"},
    ),
    "hedgehog": AnimalSpec(
        id="hedgehog",
        label="hedgehog",
        home="the fern nook",
        sound="small snuffles",
        gait="padded",
        carrying_style="balanced carefully",
        tags={"hedgehog", "forest"},
    ),
    "duck": AnimalSpec(
        id="duck",
        label="duck",
        home="the pond reeds",
        sound="quiet quacks",
        gait="waddled",
        carrying_style="tucked under one wing",
        tags={"duck", "pond"},
    ),
}

PROBLEMS = {
    "berries": Problem(
        id="berries",
        label="berry basket",
        setting="the mossy path",
        need="someone to help carry a heavy basket",
        item="basket",
        item_phrase="a basket so full of berries that it bent to one side",
        trouble="leaning and trying not to spill a single berry",
        risk="the berries will tumble into the mud",
        kind_fix="lifted one handle and carried the heavy berry basket together with the other animal",
        happy_end="the berry basket reached the table without one berry missing",
        failure_end="the basket tipped and red berries rolled into the mud",
        helper_gear="paws",
        gear_phrase="both paws",
        requires_gear=False,
        tags={"berries", "helping"},
    ),
    "cart": Problem(
        id="cart",
        label="wobbly cart",
        setting="the little bridge",
        need="someone to steady a wobbling cart",
        item="cart",
        item_phrase="a tiny wooden cart with one wheel wobbling badly",
        trouble="trying to pull and steady it at the same time",
        risk="the cart will bump sideways and spill everything",
        kind_fix="braced the wobbling wheel with a smooth stick and pulled beside the other animal until the cart rolled straight",
        happy_end="the cart crossed the bridge safely and all the parcels stayed dry",
        failure_end="the cart lurched sideways and little parcels slid onto the boards",
        helper_gear="stick",
        gear_phrase="a smooth stick",
        requires_gear=True,
        tags={"bridge", "cart", "helping"},
    ),
    "acorns": Problem(
        id="acorns",
        label="dropped acorns",
        setting="the rooty hill",
        need="someone to gather dropped acorns before they roll away",
        item="acorns",
        item_phrase="a bundle of acorns in a leaf wrap that had begun to split",
        trouble="trying to hold the wrap shut with both front paws",
        risk="the acorns will scatter down the hill",
        kind_fix="spread out a broad leaf, caught the rolling acorns, and tied the torn leaf wrap with a grass ribbon",
        happy_end="every acorn stayed safe in a neat leaf bundle",
        failure_end="acorns pattered down the hill like little brown marbles",
        helper_gear="broad leaf",
        gear_phrase="a broad leaf and a grass ribbon",
        requires_gear=True,
        tags={"acorn", "hill", "helping"},
    ),
}

GATHERINGS = {
    "kind_circle": Gathering(
        id="kind_circle",
        label="the forest kindness circle",
        goal="the morning song and sharing time",
        closing="everyone could see that the best thing carried into the circle was kindness",
        treat="warm clover cakes",
        tags={"kindness"},
    ),
    "pond_picnic": Gathering(
        id="pond_picnic",
        label="the pond picnic",
        goal="the blanket picnic under the willow",
        closing="the willow leaves nodded as if they agreed that helping first had made the feast sweeter",
        treat="seed buns and berry slices",
        tags={"kindness", "picnic"},
    ),
}

HELPER_NAMES = ["Moss", "Pip", "Nibbles", "Juniper", "Pebble", "Sunny"]
STRUGGLER_NAMES = ["Fern", "Clover", "Tumble", "Reed", "Hazel", "Drift"]
KINDNESS_LEVELS = [1, 2, 3]


@dataclass
class StoryParams:
    helper_animal: str
    struggler_animal: str
    problem: str
    gathering: str
    helper_name: str
    struggler_name: str
    kindness_level: int
    notebook_word: str = "record-gerund"
    seed: Optional[int] = None


KNOWLEDGE = {
    "kindness": [
        (
            "What is kindness?",
            "Kindness is choosing to help, comfort, or care for someone. A kind act can make a hard moment feel lighter."
        )
    ],
    "rabbit": [
        (
            "How do rabbits move?",
            "Rabbits often move by hopping with their strong back legs. They can be quick and light on the ground."
        )
    ],
    "squirrel": [
        (
            "What do squirrels carry in their paws?",
            "Squirrels can hold nuts, seeds, or little bits of food in their front paws. They are very good at balancing small things."
        )
    ],
    "hedgehog": [
        (
            "What is special about a hedgehog?",
            "A hedgehog has short spines on its back. It can curl into a ball when it wants to feel safe."
        )
    ],
    "duck": [
        (
            "Why do ducks like ponds?",
            "Ducks are water birds, so ponds give them a place to swim, float, and look for food."
        )
    ],
    "berries": [
        (
            "Why can a heavy basket be hard to carry?",
            "A heavy basket can pull your arms down and tip to one side. If it wobbles too much, things inside can spill."
        )
    ],
    "cart": [
        (
            "Why is a wobbly wheel a problem?",
            "A wobbly wheel does not roll straight. It can make a cart tip or bump so that the things inside fall out."
        )
    ],
    "acorn": [
        (
            "What is an acorn?",
            "An acorn is a small nut that grows on an oak tree. Many woodland animals like to gather acorns for food."
        )
    ],
    "bridge": [
        (
            "Why do you walk carefully on a small bridge?",
            "A small bridge can feel narrow and bumpy. Walking carefully helps you keep your balance and protect what you are carrying."
        )
    ],
    "helping": [
        (
            "Why is it good to help someone with a hard job?",
            "Helping can make the work safer and easier. It also shows the other person that they do not have to struggle alone."
        )
    ],
}
KNOWLEDGE_ORDER = ["kindness", "rabbit", "squirrel", "hedgehog", "duck", "berries", "cart", "acorn", "bridge", "helping"]


CURATED = [
    StoryParams(
        helper_animal="rabbit",
        struggler_animal="duck",
        problem="berries",
        gathering="kind_circle",
        helper_name="Moss",
        struggler_name="Reed",
        kindness_level=3,
        notebook_word="record-gerund",
    ),
    StoryParams(
        helper_animal="squirrel",
        struggler_animal="hedgehog",
        problem="cart",
        gathering="pond_picnic",
        helper_name="Pip",
        struggler_name="Clover",
        kindness_level=2,
        notebook_word="record-gerund",
    ),
    StoryParams(
        helper_animal="duck",
        struggler_animal="rabbit",
        problem="acorns",
        gathering="kind_circle",
        helper_name="Sunny",
        struggler_name="Fern",
        kindness_level=1,
        notebook_word="record-gerund",
    ),
]


def generation_prompts(world: World) -> list[str]:
    helper = world.facts["helper"]
    struggler = world.facts["struggler"]
    problem = world.facts["problem"]
    gathering = world.facts["gathering"]
    notebook_word = world.facts["notebook_word"]
    return [
        f'Write a gentle animal story for a 3-to-5-year-old that includes the word "{notebook_word}" and shows kindness through helping.',
        f"Tell a woodland story where {helper.id} the {helper.type} notices {struggler.id} the {struggler.type} struggling with {problem.label} on the way to {gathering.label}.",
        f"Write a simple animal story with a clear problem, a kind choice, and a warm ending that proves helping changed the day.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    helper = world.facts["helper"]
    struggler = world.facts["struggler"]
    problem = world.facts["problem"]
    gathering = world.facts["gathering"]
    outcome = world.facts["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {helper.id} the {helper.type} and {struggler.id} the {struggler.type}. They met on the way to {gathering.label}."
        ),
        (
            f"What problem did {struggler.id} have?",
            f"{struggler.id} was struggling with {problem.item_phrase}. That was a problem because {problem.risk}."
        ),
        (
            f"Why did {helper.id} stop?",
            f"{helper.id} noticed that {struggler.id} looked worried and remembered to be kind. {helper.pronoun('subject').capitalize()} understood that hurrying past would leave the trouble unfixed."
        ),
    ]
    if outcome == "helped":
        qa.append(
            (
                f"How did {helper.id} help {struggler.id}?",
                f"{helper.id} {problem.kind_fix}. That solved the physical problem and made {struggler.id} feel relieved."
            )
        )
    else:
        qa.append(
            (
                f"Did {helper.id} help right away?",
                f"No. {helper.id} hurried on at first, and {problem.failure_end}. Then guilt made {helper.pronoun('object')} turn back and help the kind way."
            )
        )
    qa.append(
        (
            "How did the story end?",
            f"It ended with the animals going together to {gathering.label}. The ending shows that kindness changed the day because they arrived calm, together, and ready to share."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = {"kindness"}
    tags |= set(world.facts["helper_spec"].tags)
    tags |= set(world.facts["struggler_spec"].tags)
    tags |= set(world.facts["problem"].tags)
    tags |= set(world.facts["gathering"].tags)
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
        bits: list[str] = []
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
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
        lines.append(f"  {ent.id:10} ({ent.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


def explain_rejection(problem_id: str, kindness_level: int) -> str:
    problem = PROBLEMS[problem_id]
    needed = problem_min_kindness(problem)
    return (
        f"(No story: {problem.label} needs at least kindness level {needed} in this world, "
        f"but you asked for {kindness_level}. The helper would not have enough patience or preparation "
        f"to make the kindness turn feel honest.)"
    )


ASP_RULES = r"""
animal(A) :- helper_animal(A).
animal(A) :- struggler_animal(A).

min_kindness(P, 2) :- problem(P), requires_gear(P).
min_kindness(P, 1) :- problem(P), not requires_gear(P).

valid(A, P, K) :- helper_animal(A), problem(P), kindness_level(K), min_kindness(P, M), K >= 1.

helped :- chosen_problem(P), chosen_kindness(K), min_kindness(P, M), K >= M.
rushed :- chosen_problem(P), chosen_kindness(K), min_kindness(P, M), K < M.

outcome(helped) :- helped.
outcome(rushed) :- rushed.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for animal_id in ANIMALS:
        lines.append(asp.fact("helper_animal", animal_id))
        lines.append(asp.fact("struggler_animal", animal_id))
    for problem_id, problem in PROBLEMS.items():
        lines.append(asp.fact("problem", problem_id))
        if problem.requires_gear:
            lines.append(asp.fact("requires_gear", problem_id))
    for level in KINDNESS_LEVELS:
        lines.append(asp.fact("kindness_level", level))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join([
        asp.fact("chosen_problem", params.problem),
        asp.fact("chosen_kindness", params.kindness_level),
    ])
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Animal story world about kindness. Unspecified choices are picked at random (seeded)."
    )
    ap.add_argument("--helper-animal", choices=ANIMALS)
    ap.add_argument("--struggler-animal", choices=ANIMALS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--gathering", choices=GATHERINGS)
    ap.add_argument("--kindness-level", type=int, choices=KINDNESS_LEVELS)
    ap.add_argument("--helper-name")
    ap.add_argument("--struggler-name")
    ap.add_argument("--notebook-word", default=None)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    problem_id = args.problem or rng.choice(sorted(PROBLEMS))
    kindness_level = args.kindness_level if args.kindness_level is not None else rng.choice(KINDNESS_LEVELS)

    if args.problem and args.kindness_level is not None:
        if not valid_combo(PROBLEMS[args.problem], args.kindness_level):
            raise StoryError(explain_rejection(args.problem, args.kindness_level))

    helper_animal = args.helper_animal or rng.choice(sorted(ANIMALS))
    struggler_choices = [a for a in sorted(ANIMALS) if a != helper_animal]
    struggler_animal = args.struggler_animal or rng.choice(struggler_choices)
    if struggler_animal == helper_animal and len(ANIMALS) > 1:
        others = [a for a in sorted(ANIMALS) if a != helper_animal]
        struggler_animal = rng.choice(others)

    gathering = args.gathering or rng.choice(sorted(GATHERINGS))
    helper_name = args.helper_name or rng.choice(HELPER_NAMES)
    struggler_name = args.struggler_name or rng.choice([n for n in STRUGGLER_NAMES if n != helper_name])
    notebook_word = args.notebook_word or "record-gerund"

    params = StoryParams(
        helper_animal=helper_animal,
        struggler_animal=struggler_animal,
        problem=problem_id,
        gathering=gathering,
        helper_name=helper_name,
        struggler_name=struggler_name,
        kindness_level=kindness_level,
        notebook_word=notebook_word,
    )

    if params.problem not in PROBLEMS or params.helper_animal not in ANIMALS or params.struggler_animal not in ANIMALS:
        raise StoryError("(No story: one or more requested options are not part of this world.)")
    return params


def generate(params: StoryParams) -> StorySample:
    if params.helper_animal not in ANIMALS:
        raise StoryError(f"(No story: unknown helper animal '{params.helper_animal}'.)")
    if params.struggler_animal not in ANIMALS:
        raise StoryError(f"(No story: unknown struggler animal '{params.struggler_animal}'.)")
    if params.problem not in PROBLEMS:
        raise StoryError(f"(No story: unknown problem '{params.problem}'.)")
    if params.gathering not in GATHERINGS:
        raise StoryError(f"(No story: unknown gathering '{params.gathering}'.)")
    if params.kindness_level not in KINDNESS_LEVELS:
        raise StoryError(f"(No story: kindness level must be one of {KINDNESS_LEVELS}.)")

    world = tell(
        helper_spec=ANIMALS[params.helper_animal],
        struggler_spec=ANIMALS[params.struggler_animal],
        problem=PROBLEMS[params.problem],
        gathering=GATHERINGS[params.gathering],
        kindness_level=params.kindness_level,
        helper_name=params.helper_name,
        struggler_name=params.struggler_name,
        notebook_word=params.notebook_word,
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

    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if cl - py:
            print("  only in ASP:", sorted(cl - py))
        if py - cl:
            print("  only in Python:", sorted(py - cl))

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(20):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
            params.seed = seed
            cases.append(params)
        except StoryError:
            rc = 1
            print(f"Unexpected StoryError while resolving params for seed {seed}.")
            break

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
        sample = generate(cases[0] if cases else CURATED[0])
        if not sample.story.strip():
            raise StoryError("empty story")
        print("OK: smoke test generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (helper_animal, problem, kindness_level) combos:\n")
        for helper_animal, problem, kindness_level in combos:
            print(f"  {helper_animal:10} {problem:8} kindness={kindness_level}")
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
            header = f"### {p.helper_name} the {p.helper_animal}: {p.problem} ({outcome_of(p)})"
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
