#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/short_problem_solving_foreshadowing_transformation_nursery_rhyme.py
================================================================================================

A small storyworld about a short caterpillar who solves a problem before the
rain, then changes into a butterfly. The prose stays child-facing and lightly
rhythmic, with a nursery-rhyme feel: concrete images, gentle repetition, and an
ending image that proves what changed.

Core shape
----------
A very short caterpillar wants to reach a high blossom. The sky gives a warning
that weather is coming. Because the caterpillar is short, it cannot simply climb
straight to the top. Instead it uses a sensible helper to reach a sheltered,
grippy place and spin a chrysalis. After the weather passes, the creature
transforms and can finally rise to the blossom.

Reasonableness gate
-------------------
Not every helper can solve every climb, and not every perch is a sensible place
for a chrysalis.

A generated story is valid only when:
- the helper reaches high enough for the chosen perch
- the perch is rough enough for silk to hold
- the perch is sheltered enough that a chrysalis makes sense

Outcome model
-------------
Even among valid stories, the foreshadowed weather can make the change quick or
slow:
- shelter >= weather severity  -> quick transformation by next morning
- shelter < weather severity   -> the chrysalis rocks through the storm and the
                                 transformation takes one extra day

Run it
------
python storyworlds/worlds/gpt-5.4/short_problem_solving_foreshadowing_transformation_nursery_rhyme.py
python storyworlds/worlds/gpt-5.4/short_problem_solving_foreshadowing_transformation_nursery_rhyme.py --all
python storyworlds/worlds/gpt-5.4/short_problem_solving_foreshadowing_transformation_nursery_rhyme.py -n 5 --seed 7 --qa
python storyworlds/worlds/gpt-5.4/short_problem_solving_foreshadowing_transformation_nursery_rhyme.py --verify
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
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Place:
    id: str
    label: str
    path: str
    blossom: str
    blossom_phrase: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Perch:
    id: str
    label: str
    phrase: str
    under_phrase: str
    height: int = 1
    rough: bool = True
    shelter: int = 1
    tags: set[str] = field(default_factory=set)


@dataclass
class Helper:
    id: str
    label: str
    phrase: str
    action: str
    reach: int = 1
    tags: set[str] = field(default_factory=set)


@dataclass
class Weather:
    id: str
    sign: str
    rumble: str
    severity: int = 1
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
        other = World()
        other.entities = copy.deepcopy(self.entities)
        other.fired = set(self.fired)
        other.paragraphs = [[]]
        other.facts = copy.deepcopy(self.facts)
        return other


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_ready_to_spin(world: World) -> list[str]:
    hero = world.get("hero")
    perch = world.get("perch")
    helper = world.get("helper")
    if hero.meters["climbed"] < THRESHOLD:
        return []
    sig = ("ready_to_spin",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    if perch.meters["reachable"] >= THRESHOLD and perch.meters["grippy"] >= THRESHOLD:
        hero.meters["ready_to_spin"] += 1
        hero.memes["hope"] += 1
    return []


def _r_spin_to_chrysalis(world: World) -> list[str]:
    hero = world.get("hero")
    if hero.meters["ready_to_spin"] < THRESHOLD:
        return []
    sig = ("spin",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.meters["in_chrysalis"] += 1
    hero.meters["legs"] = 0.0
    hero.memes["calm"] += 1
    return []


def _r_transform(world: World) -> list[str]:
    hero = world.get("hero")
    weather = world.get("weather")
    perch = world.get("perch")
    if hero.meters["in_chrysalis"] < THRESHOLD:
        return []
    sig = ("transform",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    if perch.meters["shelter"] >= weather.meters["severity"]:
        hero.meters["wings"] += 1
        hero.meters["transformed"] += 1
        hero.memes["joy"] += 1
        world.facts["change_speed"] = "quick"
    else:
        hero.meters["waiting"] += 1
        hero.memes["patience"] += 1
        world.facts["change_speed"] = "slow"
    return []


CAUSAL_RULES: list[Rule] = [
    Rule(name="ready_to_spin", tag="physical", apply=_r_ready_to_spin),
    Rule(name="spin_to_chrysalis", tag="physical", apply=_r_spin_to_chrysalis),
    Rule(name="transform", tag="physical", apply=_r_transform),
]


def propagate(world: World) -> None:
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            before = len(world.fired)
            rule.apply(world)
            if len(world.fired) != before:
                changed = True


PLACES = {
    "garden": Place(
        id="garden",
        label="the garden",
        path="past the thyme and tiny stones",
        blossom="bluebell",
        blossom_phrase="a tall bluebell with a nodding blue cap",
        tags={"garden", "flower"},
    ),
    "orchard": Place(
        id="orchard",
        label="the orchard edge",
        path="past fallen petals and mossy roots",
        blossom="apple blossom",
        blossom_phrase="a high apple blossom with a pink-white face",
        tags={"orchard", "flower"},
    ),
    "pumpkin_patch": Place(
        id="pumpkin_patch",
        label="the pumpkin patch",
        path="between curly vines and striped leaves",
        blossom="gold pumpkin flower",
        blossom_phrase="a gold pumpkin flower bright as a button",
        tags={"patch", "flower"},
    ),
}

PERCHES = {
    "leaf_nook": Perch(
        id="leaf_nook",
        label="leaf nook",
        phrase="a little leaf nook",
        under_phrase="under a broad leaf",
        height=1,
        rough=True,
        shelter=2,
        tags={"leaf", "shelter"},
    ),
    "twig_fork": Perch(
        id="twig_fork",
        label="twig fork",
        phrase="a fork of two brown twigs",
        under_phrase="in a snug twig fork",
        height=2,
        rough=True,
        shelter=1,
        tags={"twig", "branch"},
    ),
    "bean_trellis": Perch(
        id="bean_trellis",
        label="bean trellis",
        phrase="a quiet knot on the bean trellis",
        under_phrase="by the bean strings",
        height=3,
        rough=True,
        shelter=2,
        tags={"trellis", "garden"},
    ),
    "smooth_stem": Perch(
        id="smooth_stem",
        label="smooth stem",
        phrase="a shiny smooth stem",
        under_phrase="on a slick stem",
        height=2,
        rough=False,
        shelter=1,
        tags={"stem"},
    ),
    "swinging_reed": Perch(
        id="swinging_reed",
        label="swinging reed",
        phrase="a swinging reed tip",
        under_phrase="on a reed that swayed and swayed",
        height=3,
        rough=True,
        shelter=0,
        tags={"reed", "wind"},
    ),
}

HELPERS = {
    "pebble_step": Helper(
        id="pebble_step",
        label="pebble step",
        phrase="a round pebble step",
        action="rolled a pebble close and climbed from it",
        reach=1,
        tags={"pebble"},
    ),
    "curled_leaf_ramp": Helper(
        id="curled_leaf_ramp",
        label="curled leaf ramp",
        phrase="a curled leaf ramp",
        action="propped a curled leaf like a tiny ramp",
        reach=2,
        tags={"leaf_ramp"},
    ),
    "moss_mound": Helper(
        id="moss_mound",
        label="moss mound",
        phrase="a springy moss mound",
        action="pat-patted a moss mound into a soft green stair",
        reach=2,
        tags={"moss"},
    ),
    "twig_ladder": Helper(
        id="twig_ladder",
        label="twig ladder",
        phrase="a twig ladder",
        action="leaned a twig like a ladder with many little bumps",
        reach=3,
        tags={"twig_ladder"},
    ),
}

WEATHERS = {
    "breeze": Weather(
        id="breeze",
        sign="The breeze went hush-hush through the leaves.",
        rumble="Only a soft evening wind came by.",
        severity=1,
        tags={"wind"},
    ),
    "drizzle": Weather(
        id="drizzle",
        sign="Small gray clouds stitched the sky with silver.",
        rumble="Soon a thin drizzle tapped the leaves.",
        severity=2,
        tags={"rain"},
    ),
    "storm": Weather(
        id="storm",
        sign="The clouds stacked up dark, and far thunder muttered low.",
        rumble="By dusk the rain drummed and the wind gave the garden a shake.",
        severity=3,
        tags={"storm", "rain"},
    ),
}

NAMES = ["Pip", "Mim", "Dot", "Nib", "Tiz", "Poppy"]


def helper_reaches(helper: Helper, perch: Perch) -> bool:
    return helper.reach >= perch.height


def perch_sensible(perch: Perch) -> bool:
    return perch.rough and perch.shelter >= 1


def valid_combo(helper: Helper, perch: Perch) -> bool:
    return helper_reaches(helper, perch) and perch_sensible(perch)


def valid_combos() -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    for helper_id, helper in HELPERS.items():
        for perch_id, perch in PERCHES.items():
            if valid_combo(helper, perch):
                out.append((helper_id, perch_id))
    return out


@dataclass
class StoryParams:
    place: str
    weather: str
    helper: str
    perch: str
    name: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        place="garden",
        weather="breeze",
        helper="pebble_step",
        perch="leaf_nook",
        name="Pip",
    ),
    StoryParams(
        place="orchard",
        weather="drizzle",
        helper="curled_leaf_ramp",
        perch="twig_fork",
        name="Mim",
    ),
    StoryParams(
        place="pumpkin_patch",
        weather="storm",
        helper="twig_ladder",
        perch="bean_trellis",
        name="Dot",
    ),
    StoryParams(
        place="garden",
        weather="storm",
        helper="twig_ladder",
        perch="twig_fork",
        name="Nib",
    ),
]


def explain_rejection(helper: Helper, perch: Perch) -> str:
    if helper.reach < perch.height:
        return (
            f"(No story: {helper.phrase} is too short to reach {perch.phrase}. "
            f"The helper must honestly solve the climb.)"
        )
    if not perch.rough:
        return (
            f"(No story: {perch.phrase} is too smooth for silk to hold. "
            f"A chrysalis needs a grippy place.)"
        )
    if perch.shelter < 1:
        return (
            f"(No story: {perch.phrase} is too exposed to make a sensible resting place. "
            f"Pick a perch with a bit of cover.)"
        )
    return "(No story: this helper and perch do not make a reasonable transformation tale.)"


def outcome_of(params: StoryParams) -> str:
    weather = WEATHERS[params.weather]
    perch = PERCHES[params.perch]
    return "quick" if perch.shelter >= weather.severity else "slow"


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.attrs:
            bits.append(f"attrs={ent.attrs}")
        lines.append(f"  {ent.id:8} ({ent.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


def predict_rest(world: World, helper_id: str, perch_id: str) -> dict:
    sim = world.copy()
    helper = sim.get(helper_id)
    perch = sim.get(perch_id)
    hero = sim.get("hero")
    if helper.reach >= perch.attrs["height"]:
        perch.meters["reachable"] += 1
        hero.meters["climbed"] += 1
    if perch.attrs["rough"]:
        perch.meters["grippy"] += 1
    perch.meters["shelter"] = float(perch.attrs["shelter"])
    propagate(sim)
    return {
        "ready": hero.meters["ready_to_spin"] >= THRESHOLD,
        "change_speed": sim.facts.get("change_speed", ""),
    }


def introduce(world: World, hero: Entity, place: Place) -> None:
    hero.memes["wish"] += 1
    world.say(
        f"{hero.id} was a short caterpillar in {place.label}, "
        f"{place.path}. {hero.pronoun().capitalize()} loved to look up at {place.blossom_phrase}."
    )
    world.say(
        f'"So high, so bright," sang {hero.id}, "one day I shall say good morning to that {place.blossom}."'
    )


def foreshadow(world: World, weather: Weather) -> None:
    world.say(weather.sign)
    world.say(
        "That little sign said softly that the day would not stay still."
    )


def problem(world: World, hero: Entity, helper: Helper, perch: Perch) -> None:
    hero.memes["frustration"] += 1
    world.say(
        f"But {hero.id} was short, and {perch.phrase} sat too high to reach with only tiny feet."
    )
    world.say(
        f'{hero.id} looked at {helper.phrase} and whispered, "A small thing may still be a smart thing."'
    )


def solve_climb(world: World, hero: Entity, helper: Helper, perch: Perch) -> None:
    world.say(
        f"So {hero.id} {helper.action}. Step by step, up went the small one, right to {perch.phrase}."
    )
    hero.meters["climbed"] += 1
    perch.meters["reachable"] += 1
    if perch.rough:
        perch.meters["grippy"] += 1
    perch.meters["shelter"] = float(perch.shelter)
    hero.memes["bravery"] += 1
    propagate(world)


def spin(world: World, hero: Entity, perch: Perch) -> None:
    world.say(
        f"There {hero.id} tucked close {perch.under_phrase} and spun a silk bed, neat and tight, for the coming night."
    )


def weather_passes(world: World, weather: Weather) -> None:
    world.say(weather.rumble)


def quick_change(world: World, hero: Entity, place: Place) -> None:
    hero.meters["wings"] += 1
    hero.meters["transformed"] += 1
    hero.meters["in_chrysalis"] = 0.0
    hero.memes["joy"] += 1
    world.say(
        f"By next morning the little case gave a crack. Out came {hero.id}, not crawling now but shining with new wings."
    )
    world.say(
        f"Up, up, up {hero.pronoun()} fluttered to the {place.blossom}, light as a rhyme and bright as a bell."
    )


def slow_change(world: World, hero: Entity, place: Place) -> None:
    hero.meters["waiting"] += 1
    hero.meters["in_chrysalis"] = 1.0
    hero.memes["patience"] += 1
    world.say(
        f"All night the silk bed rocked and tapped, yet it held fast. {hero.id} had to wait one more day, quiet and snug."
    )
    hero.meters["wings"] += 1
    hero.meters["transformed"] += 1
    hero.meters["in_chrysalis"] = 0.0
    world.say(
        f"Then the second sunrise warmed the garden gold. Out came {hero.id} with soft new wings, and soon {hero.pronoun()} rose to the {place.blossom} at last."
    )


def ending(world: World, hero: Entity, place: Place) -> None:
    hero.memes["content"] += 1
    world.say(
        f'And {hero.id} sang, "I was short, I was slow, but I thought, and I grew." The {place.blossom} nodded back in the sun.'
    )


def tell(place: Place, weather: Weather, helper: Helper, perch: Perch, name: str) -> World:
    world = World()
    hero = world.add(Entity(
        id="hero",
        kind="character",
        type="caterpillar",
        label=name,
        phrase=f"{name} the short caterpillar",
        role="hero",
        tags={"caterpillar", "butterfly"},
    ))
    hero.attrs["name"] = name
    hero.meters["legs"] = 1.0
    weather_ent = world.add(Entity(
        id="weather",
        type="weather",
        label=weather.id,
        attrs={"severity": weather.severity},
    ))
    weather_ent.meters["severity"] = float(weather.severity)
    helper_ent = world.add(Entity(
        id="helper",
        type="helper",
        label=helper.label,
        phrase=helper.phrase,
        attrs={"reach": helper.reach},
        tags=set(helper.tags),
    ))
    perch_ent = world.add(Entity(
        id="perch",
        type="perch",
        label=perch.label,
        phrase=perch.phrase,
        attrs={"height": perch.height, "rough": perch.rough, "shelter": perch.shelter},
        tags=set(perch.tags),
    ))

    introduce(world, hero, place)
    foreshadow(world, weather)

    world.para()
    problem(world, hero, helper, perch)
    pred = predict_rest(world, "helper", "perch")
    world.facts["predicted_ready"] = pred["ready"]
    solve_climb(world, hero, helper, perch)
    spin(world, hero, perch)

    world.para()
    weather_passes(world, weather)
    if perch.shelter >= weather.severity:
        world.facts["change_speed"] = "quick"
        quick_change(world, hero, place)
    else:
        world.facts["change_speed"] = "slow"
        slow_change(world, hero, place)

    world.para()
    ending(world, hero, place)

    world.facts.update(
        hero=hero,
        place=place,
        weather=weather,
        helper=helper,
        perch=perch,
        outcome=world.facts["change_speed"],
        reached=True,
        transformed=hero.meters["transformed"] >= THRESHOLD,
        blossom=place.blossom,
        hero_name=name,
    )
    return world


KNOWLEDGE = {
    "caterpillar": [
        (
            "What is a caterpillar?",
            "A caterpillar is a small crawling insect that is the young form of a butterfly or moth. Many caterpillars later change shape in a chrysalis."
        )
    ],
    "butterfly": [
        (
            "What is transformation in a butterfly's life?",
            "Transformation means the animal changes from one form to another. A caterpillar can rest in a chrysalis and later come out as a butterfly with wings."
        )
    ],
    "rain": [
        (
            "How can clouds warn that rain is coming?",
            "Dark or gray clouds can be a sign that rain is on the way. Wind and soft thunder can warn you before the drops begin."
        )
    ],
    "storm": [
        (
            "Why do small animals look for shelter before a storm?",
            "Storms can shake branches and soak tiny creatures. Shelter helps them stay safer and steadier."
        )
    ],
    "leaf": [
        (
            "Why is a broad leaf a good shelter?",
            "A broad leaf can block some rain and wind. It makes a small, covered place underneath."
        )
    ],
    "twig_ladder": [
        (
            "Why can a ladder help with a problem?",
            "A ladder helps you reach something high in careful steps. It turns a hard climb into a possible one."
        )
    ],
    "pebble": [
        (
            "How can a pebble help a tiny creature reach higher?",
            "A pebble can work like a little step. Even one small lift can help when someone is very short."
        )
    ],
    "moss": [
        (
            "What is moss like?",
            "Moss is a soft green plant that grows in little cushions. It can feel springy and damp."
        )
    ],
}
KNOWLEDGE_ORDER = ["caterpillar", "butterfly", "rain", "storm", "leaf", "twig_ladder", "pebble", "moss"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    place = f["place"]
    weather = f["weather"]
    helper = f["helper"]
    perch = f["perch"]
    name = f["hero_name"]
    return [
        'Write a short nursery-rhyme-style story for a 3-to-5-year-old that includes the word "short", uses foreshadowing, and ends with a transformation.',
        f"Tell a gentle story about a short caterpillar named {name} in {place.label} who notices that weather is coming and solves a climbing problem with {helper.phrase}.",
        f"Write a small rhythmic story where a tiny creature cannot reach {perch.phrase}, thinks carefully, makes a sensible plan, and later changes into a butterfly.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    name = f["hero_name"]
    place = f["place"]
    weather = f["weather"]
    helper = f["helper"]
    perch = f["perch"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {name}, a short caterpillar in {place.label}. {name} wanted to reach the high {place.blossom}."
        ),
        (
            f"What problem did {name} have?",
            f"{name} was too short to reach {perch.phrase} by climbing alone. That mattered because {name} needed a good resting place before the weather changed."
        ),
        (
            f"What was the foreshadowing in the story?",
            f"The sky and air gave a warning before the hard part came. {weather.sign} That clue told {name} there was not much time to choose a safe place."
        ),
        (
            f"How did {name} solve the problem?",
            f"{name} used {helper.phrase} to reach {perch.phrase}. The helper worked because it was tall enough to make the climb possible."
        ),
        (
            f"Why was {perch.phrase} a good place to rest?",
            f"It was rough enough for silk to hold and sheltered enough to make sense as a chrysalis place. That is why the plan was more than just brave; it was sensible."
        ),
    ]
    if outcome == "quick":
        qa.append(
            (
                f"How did {name} change?",
                f"{name} spun a chrysalis and changed by the next morning. The sheltered perch kept the change calm, so {name} soon came out with wings and flew to the {place.blossom}."
            )
        )
    else:
        qa.append(
            (
                f"Did the change happen right away?",
                f"No. The weather shook the silk bed through the night, so the change took one more day. Even so, the perch held, and {name} finally came out with wings and reached the {place.blossom}."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"caterpillar", "butterfly"}
    if "rain" in f["weather"].tags:
        tags.add("rain")
    if "storm" in f["weather"].tags:
        tags.add("storm")
    if "leaf" in f["perch"].tags:
        tags.add("leaf")
    if f["helper"].id == "twig_ladder":
        tags.add("twig_ladder")
    if f["helper"].id == "pebble_step":
        tags.add("pebble")
    if f["helper"].id == "moss_mound":
        tags.add("moss")
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


ASP_RULES = r"""
reaches(H, P) :- helper(H), perch(P), helper_reach(H, R), perch_height(P, Ht), R >= Ht.
sensible_perch(P) :- perch(P), rough(P), shelter(P, S), S >= 1.
valid(H, P) :- reaches(H, P), sensible_perch(P).

quick(P, W) :- perch(P), weather(W), shelter(P, S), severity(W, V), S >= V.
slow(P, W)  :- valid(_, P), weather(W), shelter(P, S), severity(W, V), S < V.

outcome(quick) :- chosen_perch(P), chosen_weather(W), quick(P, W).
outcome(slow)  :- chosen_perch(P), chosen_weather(W), not quick(P, W).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for hid, helper in HELPERS.items():
        lines.append(asp.fact("helper", hid))
        lines.append(asp.fact("helper_reach", hid, helper.reach))
    for pid, perch in PERCHES.items():
        lines.append(asp.fact("perch", pid))
        lines.append(asp.fact("perch_height", pid, perch.height))
        lines.append(asp.fact("shelter", pid, perch.shelter))
        if perch.rough:
            lines.append(asp.fact("rough", pid))
    for wid, weather in WEATHERS.items():
        lines.append(asp.fact("weather", wid))
        lines.append(asp.fact("severity", wid, weather.severity))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_perch", params.perch),
            asp.fact("chosen_weather", params.weather),
        ]
    )
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

    cases: list[StoryParams] = list(CURATED)
    for seed in range(50):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
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
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("smoke test produced an empty story")
        print("OK: smoke test story generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Storyworld: a short caterpillar solves a problem before the weather and transforms."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--weather", choices=WEATHERS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--perch", choices=PERCHES)
    ap.add_argument("--name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible helper/perch pairs from clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner against Python")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.helper and args.perch:
        helper = HELPERS[args.helper]
        perch = PERCHES[args.perch]
        if not valid_combo(helper, perch):
            raise StoryError(explain_rejection(helper, perch))

    combos = [
        combo for combo in valid_combos()
        if (args.helper is None or combo[0] == args.helper)
        and (args.perch is None or combo[1] == args.perch)
    ]
    if not combos:
        raise StoryError("(No valid helper/perch combination matches the given options.)")

    helper_id, perch_id = rng.choice(sorted(combos))
    place_id = args.place or rng.choice(sorted(PLACES))
    weather_id = args.weather or rng.choice(sorted(WEATHERS))
    name = args.name or rng.choice(NAMES)

    return StoryParams(
        place=place_id,
        weather=weather_id,
        helper=helper_id,
        perch=perch_id,
        name=name,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.weather not in WEATHERS:
        raise StoryError(f"(Unknown weather: {params.weather})")
    if params.helper not in HELPERS:
        raise StoryError(f"(Unknown helper: {params.helper})")
    if params.perch not in PERCHES:
        raise StoryError(f"(Unknown perch: {params.perch})")

    helper = HELPERS[params.helper]
    perch = PERCHES[params.perch]
    if not valid_combo(helper, perch):
        raise StoryError(explain_rejection(helper, perch))

    world = tell(
        place=PLACES[params.place],
        weather=WEATHERS[params.weather],
        helper=helper,
        perch=perch,
        name=params.name,
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
        print(asp_program("", "#show valid/2.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (helper, perch) combos:\n")
        for helper_id, perch_id in combos:
            print(f"  {helper_id:16} {perch_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 40, 40):
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
            header = f"### {p.name}: {p.helper} to {p.perch} in {p.place} ({p.weather}, {outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
