#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/caffeine_trellis_prior_transformation_heartwarming.py
================================================================================

A standalone storyworld about a child caring for a climbing plant on a trellis.

This tiny domain rebuilds a heartwarming "worry, mistaken shortcut, patient fix,
gentle transformation" tale. A child sees a treasured vine droop before a small
garden moment and remembers a prior half-understood idea about "waking things
up." The tempting shortcut is to use a grown-up drink with caffeine, but the
world refuses to tell stories where that is treated as sensible plant care.
Instead, the child and a calm grown-up choose the care that matches the real
problem: water for thirst, soft ties for a slipping vine, or richer soil for a
hungry plant. The ending image proves the change: the child has become more
patient, and the vine transforms from worried-looking to lively and blooming.

Run it
------
    python storyworlds/worlds/gpt-5.4/caffeine_trellis_prior_transformation_heartwarming.py
    python storyworlds/worlds/gpt-5.4/caffeine_trellis_prior_transformation_heartwarming.py --plant beans --problem dry_soil
    python storyworlds/worlds/gpt-5.4/caffeine_trellis_prior_transformation_heartwarming.py --remedy water
    python storyworlds/worlds/gpt-5.4/caffeine_trellis_prior_transformation_heartwarming.py --all
    python storyworlds/worlds/gpt-5.4/caffeine_trellis_prior_transformation_heartwarming.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/caffeine_trellis_prior_transformation_heartwarming.py --trace
    python storyworlds/worlds/gpt-5.4/caffeine_trellis_prior_transformation_heartwarming.py --asp
    python storyworlds/worlds/gpt-5.4/caffeine_trellis_prior_transformation_heartwarming.py --verify
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
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "aunt", "grandmother"}
        male = {"boy", "father", "dad", "man", "uncle", "grandfather"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad", "grandmother": "grandma", "grandfather": "grandpa"}.get(
            self.type, self.type
        )


@dataclass
class Plant:
    id: str
    label: str
    phrase: str
    bloom: str
    child_view: str
    climb_word: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Problem:
    id: str
    cue: str
    cause: str
    prior_misread: str
    needs: str
    turn: str
    result: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Remedy:
    id: str
    label: str
    sense: int
    fixes: set[str]
    act: str
    future: str
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


def _r_parched_droop(world: World) -> list[str]:
    plant = world.get("plant")
    if plant.meters["dryness"] < THRESHOLD:
        return []
    sig = ("parched_droop",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    plant.meters["droop"] += 1
    return []


def _r_loose_droop(world: World) -> list[str]:
    plant = world.get("plant")
    if plant.meters["support_loss"] < THRESHOLD:
        return []
    sig = ("loose_droop",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    plant.meters["droop"] += 1
    return []


def _r_hungry_pale(world: World) -> list[str]:
    plant = world.get("plant")
    if plant.meters["hunger"] < THRESHOLD:
        return []
    sig = ("hungry_pale",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    plant.meters["pale"] += 1
    plant.meters["droop"] += 1
    return []


def _r_caffeine_harm(world: World) -> list[str]:
    plant = world.get("plant")
    if plant.meters["caffeine_hit"] < THRESHOLD:
        return []
    sig = ("caffeine_harm",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    plant.meters["dryness"] += 1
    plant.meters["droop"] += 1
    if "child" in world.entities:
        world.get("child").memes["worry"] += 1
    return []


def _r_thriving_bloom(world: World) -> list[str]:
    plant = world.get("plant")
    if plant.meters["hydrated"] < THRESHOLD and plant.meters["fed"] < THRESHOLD and plant.meters["supported"] < THRESHOLD:
        return []
    if plant.meters["dryness"] >= THRESHOLD or plant.meters["support_loss"] >= THRESHOLD or plant.meters["hunger"] >= THRESHOLD:
        return []
    sig = ("thriving_bloom",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    plant.meters["upright"] += 1
    plant.meters["blooming"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="parched_droop", tag="physical", apply=_r_parched_droop),
    Rule(name="loose_droop", tag="physical", apply=_r_loose_droop),
    Rule(name="hungry_pale", tag="physical", apply=_r_hungry_pale),
    Rule(name="caffeine_harm", tag="physical", apply=_r_caffeine_harm),
    Rule(name="thriving_bloom", tag="physical", apply=_r_thriving_bloom),
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
        for s in produced:
            world.say(s)
    return produced


PLANTS = {
    "beans": Plant(
        id="beans",
        label="bean vine",
        phrase="a small bean vine",
        bloom="white bean blossoms",
        child_view="tiny green hands reaching up",
        climb_word="coil",
        tags={"beans", "plant", "trellis"},
    ),
    "morning_glory": Plant(
        id="morning_glory",
        label="morning glory vine",
        phrase="a morning glory vine",
        bloom="blue star-shaped flowers",
        child_view="a little green ribbon that wanted the sky",
        climb_word="twist",
        tags={"flowers", "plant", "trellis"},
    ),
    "sweet_pea": Plant(
        id="sweet_pea",
        label="sweet pea vine",
        phrase="a sweet pea vine",
        bloom="soft pink blossoms",
        child_view="a shy climber with curly fingers",
        climb_word="curl",
        tags={"flowers", "plant", "trellis"},
    ),
}

PROBLEMS = {
    "dry_soil": Problem(
        id="dry_soil",
        cue="The soil in the pot looked crumbly, and the leaves hung like tired ribbons.",
        cause="The roots were thirsty after a hot day.",
        prior_misread='Earlier that week, the child had heard a grown-up joke that caffeine wakes people up, and the child mixed that up with what a thirsty plant might need.',
        needs="water",
        turn="The problem was thirst, not sleepiness.",
        result="the leaves lifted by evening and the vine looked fresh again",
        tags={"water", "dry"},
    ),
    "slipping_vine": Problem(
        id="slipping_vine",
        cue="One long stem had sagged away from the trellis and was dragging its leaves against the pot.",
        cause="The climber had grown faster than its loose loop could hold.",
        prior_misread='The child remembered a prior moment when a tired person was helped by a warm drink, and for a second wondered if a splash of something with caffeine might perk the vine up too.',
        needs="ties",
        turn="The problem was support, not sleepiness.",
        result="the stem rested against the trellis again and began reaching upward",
        tags={"support", "trellis"},
    ),
    "hungry_soil": Problem(
        id="hungry_soil",
        cue="The vine was standing up, but its leaves looked pale and its buds seemed slow and small.",
        cause="The potting soil had little left to feed a growing plant.",
        prior_misread='The child had a prior thought that if caffeine can make grown-ups feel buzzy, maybe it could make a plant bloom faster too.',
        needs="compost",
        turn="The problem was hunger in the soil, not sleepiness.",
        result="the leaves deepened to a richer green and the buds swelled overnight",
        tags={"compost", "soil"},
    ),
}

REMEDIES = {
    "water": Remedy(
        id="water",
        label="watering can",
        sense=3,
        fixes={"dry_soil"},
        act="filled the little watering can and poured slowly until the soil turned dark and cool",
        future="By evening, a new stretch of green had appeared at the top of the trellis.",
        qa_text="They watered the thirsty roots slowly with a watering can.",
        tags={"water"},
    ),
    "ties": Remedy(
        id="ties",
        label="soft garden ties",
        sense=3,
        fixes={"slipping_vine"},
        act="used soft garden ties to fasten the wandering stem to the trellis without pinching it",
        future="By evening, the stem had begun to lean into the trellis instead of away from it.",
        qa_text="They fastened the slipping stem gently to the trellis with soft ties.",
        tags={"ties", "trellis"},
    ),
    "compost": Remedy(
        id="compost",
        label="compost scoop",
        sense=3,
        fixes={"hungry_soil"},
        act="mixed a scoop of crumbly compost into the top of the soil and watered it in",
        future="By morning, the buds looked fuller, as if they had remembered what they were growing toward.",
        qa_text="They fed the soil with compost and a little water.",
        tags={"compost"},
    ),
    "coffee": Remedy(
        id="coffee",
        label="cold coffee mug",
        sense=1,
        fixes=set(),
        act="tilted a mug of leftover coffee with caffeine toward the pot",
        future="The vine would only have felt worse.",
        qa_text="They tried coffee, which was not a sensible plant remedy.",
        tags={"caffeine", "coffee"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Anna", "Maya", "Nora", "Rose"]
BOY_NAMES = ["Leo", "Ben", "Max", "Sam", "Eli", "Jack", "Finn", "Noah", "Theo", "Owen"]
TRAITS = ["careful", "hopeful", "gentle", "curious", "patient", "kind"]


@dataclass
class StoryParams:
    plant: str
    problem: str
    remedy: str
    child_name: str
    child_gender: str
    helper_type: str
    trait: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        plant="morning_glory",
        problem="dry_soil",
        remedy="water",
        child_name="Lily",
        child_gender="girl",
        helper_type="grandmother",
        trait="hopeful",
        seed=1,
    ),
    StoryParams(
        plant="beans",
        problem="slipping_vine",
        remedy="ties",
        child_name="Leo",
        child_gender="boy",
        helper_type="father",
        trait="careful",
        seed=2,
    ),
    StoryParams(
        plant="sweet_pea",
        problem="hungry_soil",
        remedy="compost",
        child_name="Maya",
        child_gender="girl",
        helper_type="mother",
        trait="gentle",
        seed=3,
    ),
]


def remedy_matches(problem_id: str, remedy_id: str) -> bool:
    remedy = REMEDIES[remedy_id]
    return problem_id in remedy.fixes


def sensible_remedies() -> list[Remedy]:
    return [r for r in REMEDIES.values() if r.sense >= 2]


def valid_combos() -> list[tuple[str, str, str]]:
    out: list[tuple[str, str, str]] = []
    for plant_id in PLANTS:
        for problem_id in PROBLEMS:
            for remedy_id in REMEDIES:
                if remedy_matches(problem_id, remedy_id) and REMEDIES[remedy_id].sense >= 2:
                    out.append((plant_id, problem_id, remedy_id))
    return out


def explain_rejection(problem_id: str, remedy_id: str) -> str:
    problem = PROBLEMS[problem_id]
    remedy = REMEDIES[remedy_id]
    if remedy.sense < 2:
        return (
            f"(No story: {remedy.label} is not a sensible plant remedy here. "
            f"The child may be tempted by caffeine, but the world treats that as a mistaken shortcut, not a fix.)"
        )
    return (
        f"(No story: {remedy.label} does not match {problem.id}. "
        f"{problem.turn} This world only allows remedies that solve the real cause.)"
    )


def apply_problem(world: World, problem: Problem) -> None:
    plant = world.get("plant")
    if problem.id == "dry_soil":
        plant.meters["dryness"] += 1
    elif problem.id == "slipping_vine":
        plant.meters["support_loss"] += 1
    elif problem.id == "hungry_soil":
        plant.meters["hunger"] += 1
    propagate(world, narrate=False)


def predict_with_remedy(world: World, remedy_id: str) -> dict:
    sim = world.copy()
    plant = sim.get("plant")
    if remedy_id == "water":
        plant.meters["dryness"] = 0.0
        plant.meters["hydrated"] += 1
    elif remedy_id == "ties":
        plant.meters["support_loss"] = 0.0
        plant.meters["supported"] += 1
    elif remedy_id == "compost":
        plant.meters["hunger"] = 0.0
        plant.meters["fed"] += 1
        plant.meters["hydrated"] += 1
    elif remedy_id == "coffee":
        plant.meters["caffeine_hit"] += 1
    propagate(sim, narrate=False)
    return {
        "droop": plant.meters["droop"],
        "blooming": plant.meters["blooming"],
        "dryness": plant.meters["dryness"],
        "support_loss": plant.meters["support_loss"],
        "hunger": plant.meters["hunger"],
    }


def introduce(world: World, child: Entity, helper: Entity, plant_cfg: Plant) -> None:
    world.say(
        f"{child.id} kept {plant_cfg.phrase} beside the back steps, where a small wooden trellis leaned against a sunny wall."
    )
    world.say(
        f"To {child.pronoun('object')}, the vine looked like {plant_cfg.child_view}, and {child.pronoun()} checked it every morning before breakfast."
    )
    world.say(
        f"{helper.label_word.capitalize()} had helped {child.pronoun('object')} plant it, so caring for it felt like a secret little team."
    )


def worry(world: World, child: Entity, plant_cfg: Plant, problem: Problem) -> None:
    child.memes["love"] += 1
    child.memes["worry"] += 1
    world.say(
        f"One warm afternoon, {problem.cue}"
    )
    world.say(
        f"{child.id} touched the pot and looked up the trellis. Tomorrow was the little porch show for neighbors, and {child.pronoun()} had hoped to see {plant_cfg.bloom}."
    )


def temptation(world: World, child: Entity, helper: Entity, problem: Problem) -> None:
    child.memes["haste"] += 1
    world.say(problem.prior_misread)
    world.say(
        f"On the table nearby sat {helper.label_word}'s mug with a little cold coffee in the bottom. {child.id} stared at it and whispered, \"Maybe caffeine would wake the vine up.\""
    )


def helper_intervenes(world: World, child: Entity, helper: Entity, problem: Problem) -> None:
    helper.memes["care"] += 1
    child.memes["trust"] += 1
    world.say(
        f'{helper.label_word.capitalize()} heard that soft whisper and came to stand beside {child.pronoun("object")}. "{problem.turn}" {helper.pronoun()} said gently.'
    )
    world.say(
        f'"Coffee is for grown-up mugs, not for little roots. Let\'s look closely and help the plant in the way it really needs."'
    )


def choose_remedy(world: World, child: Entity, helper: Entity, plant_cfg: Plant, problem: Problem, remedy: Remedy) -> None:
    plant = world.get("plant")
    if remedy.id == "water":
        plant.meters["dryness"] = 0.0
        plant.meters["hydrated"] += 1
    elif remedy.id == "ties":
        plant.meters["support_loss"] = 0.0
        plant.meters["supported"] += 1
    elif remedy.id == "compost":
        plant.meters["hunger"] = 0.0
        plant.meters["fed"] += 1
        plant.meters["hydrated"] += 1
    child.memes["patience"] += 1
    child.memes["worry"] = 0.0
    child.memes["hope"] += 1
    world.say(
        f"Together they studied the vine again and saw the true trouble: {problem.cause}"
    )
    world.say(
        f"Then {helper.label_word} and {child.id} {remedy.act}."
    )
    propagate(world, narrate=False)
    world.say(remedy.future)


def transformation(world: World, child: Entity, helper: Entity, plant_cfg: Plant, problem: Problem) -> None:
    plant = world.get("plant")
    if plant.meters["blooming"] >= THRESHOLD:
        bloom_line = f"By the next morning, {plant_cfg.bloom} had opened along the trellis like small smiles."
    else:
        bloom_line = f"By the next morning, the vine looked steadier on the trellis, ready for its next bit of growing."
    child.memes["joy"] += 1
    child.memes["lesson"] += 1
    world.say(bloom_line)
    world.say(
        f"{child.id} felt changed too. The day before, {child.pronoun()} had wanted a fast magic answer; now {child.pronoun()} understood that growing things answered best to patient care."
    )
    world.say(
        f"When the neighbors came by, {child.id} did not boast about making the plant hurry. {child.pronoun().capitalize()} simply smiled at {helper.label_word} and at the vine climbing its trellis, alive in its own gentle time."
    )
    world.facts["ending_image"] = bloom_line
    world.facts["problem_result"] = problem.result


def tell(plant_cfg: Plant, problem: Problem, remedy: Remedy, child_name: str, child_gender: str, helper_type: str, trait: str) -> World:
    world = World()
    child = world.add(
        Entity(
            id=child_name,
            kind="character",
            type=child_gender,
            role="child",
            traits=[trait],
            label=child_name,
        )
    )
    helper = world.add(
        Entity(
            id="Helper",
            kind="character",
            type=helper_type,
            role="helper",
            label="the helper",
        )
    )
    plant = world.add(
        Entity(
            id="plant",
            kind="thing",
            type="plant",
            label=plant_cfg.label,
            phrase=plant_cfg.phrase,
            tags=set(plant_cfg.tags),
        )
    )
    trellis = world.add(
        Entity(
            id="trellis",
            kind="thing",
            type="trellis",
            label="trellis",
            phrase="a little wooden trellis",
            tags={"trellis"},
        )
    )

    apply_problem(world, problem)

    introduce(world, child, helper, plant_cfg)
    world.para()
    worry(world, child, plant_cfg, problem)
    temptation(world, child, helper, problem)
    world.para()
    helper_intervenes(world, child, helper, problem)
    choose_remedy(world, child, helper, plant_cfg, problem, remedy)
    world.para()
    transformation(world, child, helper, plant_cfg, problem)

    world.facts.update(
        child=child,
        helper=helper,
        plant_cfg=plant_cfg,
        problem=problem,
        remedy=remedy,
        plant=plant,
        trellis=trellis,
        predicted_bad=predict_with_remedy(world, "coffee"),
        predicted_good=predict_with_remedy(world, remedy.id),
        transformed=child.memes["lesson"] >= THRESHOLD,
    )
    return world


KNOWLEDGE = {
    "caffeine": [
        (
            "What is caffeine?",
            "Caffeine is something in drinks like coffee and some tea that can make people feel more awake. It is not plant food, and children should not experiment with it."
        )
    ],
    "trellis": [
        (
            "What is a trellis?",
            "A trellis is a frame made of wood or wire that helps climbing plants grow upward. Vines hold onto it as they reach for light."
        )
    ],
    "water": [
        (
            "Why do plants need water?",
            "Plants need water because their roots drink it from the soil. Water helps the leaves stay firm and helps the whole plant move what it needs."
        )
    ],
    "compost": [
        (
            "What does compost do for a plant?",
            "Compost feeds the soil with rich, broken-down plant matter. That gives roots more good things to use while the plant grows."
        )
    ],
    "ties": [
        (
            "Why would a gardener tie a vine to a trellis?",
            "A soft tie can guide a stem back to its support so it does not bend or drag. It helps the plant climb without hurting it."
        )
    ],
    "patience": [
        (
            "Why is patience important when you grow a plant?",
            "Plants change slowly, so good care often takes time to show. Patience helps you notice what a plant really needs instead of forcing a quick answer."
        )
    ],
}
KNOWLEDGE_ORDER = ["caffeine", "trellis", "water", "compost", "ties", "patience"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    plant_cfg = f["plant_cfg"]
    problem = f["problem"]
    return [
        'Write a heartwarming story for a 3-to-5-year-old that includes the words "caffeine", "trellis", and "prior".',
        f"Tell a gentle Transformation story where {child.id} worries about {plant_cfg.phrase} on a trellis, remembers a prior mistaken idea, and learns to help it properly.",
        f"Write a cozy garden story where a child nearly chooses a quick fix with caffeine, but a caring grown-up helps {child.pronoun('object')} notice that {problem.needs} is what the plant really needs.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    plant_cfg = f["plant_cfg"]
    problem = f["problem"]
    remedy = f["remedy"]
    bad = f["predicted_bad"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, a child caring for {plant_cfg.phrase}, and {helper.label_word} who helps {child.pronoun('object')} understand it. The vine on the trellis matters because it is something they have tended together."
        ),
        (
            "Why was the child worried?",
            f"{child.id} was worried because {problem.cue.lower()} {child.pronoun().capitalize()} had hoped the vine would look lively for the neighbors the next day. Seeing the plant struggle made the garden feel suddenly fragile."
        ),
        (
            "What prior idea did the child misunderstand?",
            f"{problem.prior_misread} That is why {child.id} briefly thought caffeine might help, even though the plant was not a sleepy person at all."
        ),
        (
            "Why did the grown-up say not to use coffee with caffeine?",
            f"{helper.label_word.capitalize()} said not to use it because coffee was not the real answer to the vine's problem. In the world model, the caffeine idea would leave the plant drooping and could even make its trouble worse."
        ),
        (
            "How did they solve the problem?",
            f"{remedy.qa_text} They first looked closely at the plant's real condition, and then they chose care that matched the cause instead of a hurried guess."
        ),
        (
            "What transformed by the end of the story?",
            f"The vine changed from looking troubled to looking stronger on the trellis, and {child.id} changed too. {child.pronoun().capitalize()} moved from wanting a quick trick to trusting patient care."
        ),
    ]
    if bad["droop"] >= THRESHOLD:
        qa.append(
            (
                "What might have happened if the child had poured in the coffee?",
                f"The plant would still have drooped, because caffeine was not the help it needed. The wrong shortcut would have added worry instead of solving the real problem."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"caffeine", "trellis", "patience"}
    tags |= set(f["problem"].tags)
    tags |= set(f["remedy"].tags)
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
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
sensible(R) :- remedy(R), sense(R, S), sense_min(M), S >= M.
fixes_problem(Pb, R) :- fixes(R, Pb).
valid(Pl, Pb, R) :- plant(Pl), problem(Pb), remedy(R), sensible(R), fixes_problem(Pb, R).

good_outcome(Pb, R) :- valid(_, Pb, R).
bad_shortcut(coffee) :- remedy(coffee).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for plant_id in PLANTS:
        lines.append(asp.fact("plant", plant_id))
    for problem_id in PROBLEMS:
        lines.append(asp.fact("problem", problem_id))
    for remedy_id, remedy in REMEDIES.items():
        lines.append(asp.fact("remedy", remedy_id))
        lines.append(asp.fact("sense", remedy_id, remedy.sense))
        for problem_id in sorted(remedy.fixes):
            lines.append(asp.fact("fixes", remedy_id, problem_id))
    lines.append(asp.fact("sense_min", 2))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def _check_story(sample: StorySample) -> Optional[str]:
    if not sample.story.strip():
        return "empty story"
    lowered = sample.story.lower()
    for needle in ["caffeine", "trellis", "prior"]:
        if needle not in lowered:
            return f'missing required word "{needle}"'
    if "{" in sample.story or "}" in sample.story:
        return "unresolved template braces"
    return None


def asp_verify() -> int:
    rc = 0

    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: ASP gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    c_sens = set(asp_sensible())
    p_sens = {r.id for r in sensible_remedies()}
    if c_sens == p_sens:
        print(f"OK: sensible remedies match ({sorted(c_sens)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible remedies: clingo={sorted(c_sens)} python={sorted(p_sens)}")

    try:
        sample = generate(CURATED[0])
        err = _check_story(sample)
        if err:
            raise StoryError(err)
        print("OK: smoke test story generation passed.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")

    try:
        parser = build_parser()
        for seed in range(5):
            args = parser.parse_args([])
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            sample = generate(params)
            err = _check_story(sample)
            if err:
                raise StoryError(err)
        print("OK: random generation smoke tests passed.")
    except Exception as exc:
        rc = 1
        print(f"RANDOM SMOKE TEST FAILED: {exc}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Story world sketch: a child, a vine on a trellis, a mistaken caffeine shortcut, and a heartwarming transformation."
    )
    ap.add_argument("--plant", choices=PLANTS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--remedy", choices=REMEDIES)
    ap.add_argument("--child-name")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=["mother", "father", "grandmother", "grandfather"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combos from ASP")
    ap.add_argument("--verify", action="store_true", help="check ASP parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.problem and args.remedy:
        if not remedy_matches(args.problem, args.remedy) or REMEDIES[args.remedy].sense < 2:
            raise StoryError(explain_rejection(args.problem, args.remedy))
    if args.remedy and REMEDIES[args.remedy].sense < 2:
        problem_id = args.problem or "dry_soil"
        raise StoryError(explain_rejection(problem_id, args.remedy))

    combos = [
        c
        for c in valid_combos()
        if (args.plant is None or c[0] == args.plant)
        and (args.problem is None or c[1] == args.problem)
        and (args.remedy is None or c[2] == args.remedy)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    plant_id, problem_id, remedy_id = rng.choice(sorted(combos))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    child_name = args.child_name or rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES)
    helper_type = args.helper or rng.choice(["mother", "father", "grandmother", "grandfather"])
    trait = rng.choice(TRAITS)
    return StoryParams(
        plant=plant_id,
        problem=problem_id,
        remedy=remedy_id,
        child_name=child_name,
        child_gender=child_gender,
        helper_type=helper_type,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        plant_cfg = PLANTS[params.plant]
        problem = PROBLEMS[params.problem]
        remedy = REMEDIES[params.remedy]
    except KeyError as exc:
        raise StoryError(f"(Invalid parameter: {exc})") from exc

    if not remedy_matches(params.problem, params.remedy) or remedy.sense < 2:
        raise StoryError(explain_rejection(params.problem, params.remedy))

    world = tell(
        plant_cfg=plant_cfg,
        problem=problem,
        remedy=remedy,
        child_name=params.child_name,
        child_gender=params.child_gender,
        helper_type=params.helper_type,
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
        print(asp_program("", "#show valid/3.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"sensible remedies: {', '.join(asp_sensible())}\n")
        print(f"{len(combos)} compatible (plant, problem, remedy) combos:\n")
        for plant_id, problem_id, remedy_id in combos:
            print(f"  {plant_id:15} {problem_id:15} {remedy_id}")
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
            header = f"### {p.child_name}: {p.plant} / {p.problem} / {p.remedy}"
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
