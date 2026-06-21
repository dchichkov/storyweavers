#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/nervous_bar_repetition_superhero_story.py
====================================================================

A standalone story world for a tiny superhero tale built around one child, one
bar, one nervous moment, and a repeated brave rhythm that helps the child move.

The seed asked for:
- the word "nervous"
- the word "bar"
- repetition
- a superhero-story style

So this world models a child pretending to be a superhero on a training mission.
The child faces a bar obstacle, feels nervous, gets grounded help, repeats a
short brave phrase, and either crosses the bar or sensibly steps down to a lower
practice bar first. The state of the world -- not a frozen template -- decides
which ending is told.

Run it
------
    python storyworlds/worlds/gpt-5.4/nervous_bar_repetition_superhero_story.py
    python storyworlds/worlds/gpt-5.4/nervous_bar_repetition_superhero_story.py --bar rescue_bar --method mantra
    python storyworlds/worlds/gpt-5.4/nervous_bar_repetition_superhero_story.py --all
    python storyworlds/worlds/gpt-5.4/nervous_bar_repetition_superhero_story.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/nervous_bar_repetition_superhero_story.py --verify
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
# from a nested world directory.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------
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
        female = {"girl", "mother", "mom", "woman", "grandmother", "grandma"}
        male = {"boy", "father", "dad", "man", "coach"}
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
        }.get(self.type, self.type)


# ---------------------------------------------------------------------------
# Domain configs
# ---------------------------------------------------------------------------
@dataclass
class Scene:
    id: str
    place: str
    opening: str
    mission_name: str
    rescue_item: str
    skyline: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Bar:
    id: str
    label: str
    phrase: str
    difficulty: int
    height_word: str
    shimmer: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Nerve:
    id: str
    label: str
    level: int
    body_sign: str
    thought: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Method:
    id: str
    label: str
    support: int
    text: str
    repeated_words: str
    allows_practice: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class HelperCfg:
    id: str
    helper_type: str
    helper_name: str
    bonus: int
    style: str
    tags: set[str] = field(default_factory=set)


# ---------------------------------------------------------------------------
# World and rules
# ---------------------------------------------------------------------------
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


def _r_wobble(world: World) -> list[str]:
    hero = world.entities.get("hero")
    bar = world.entities.get("bar")
    if hero is None or bar is None:
        return []
    if hero.memes["nervous"] < THRESHOLD:
        return []
    if bar.meters["faced"] < THRESHOLD:
        return []
    sig = ("wobble", hero.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.meters["wobble"] += 1
    return ["__wobble__"]


def _r_brave_chant(world: World) -> list[str]:
    hero = world.entities.get("hero")
    helper = world.entities.get("helper")
    if hero is None or helper is None:
        return []
    if world.facts.get("repeated") is not True:
        return []
    sig = ("brave", hero.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["courage"] += 1
    hero.memes["trust"] += 1
    helper.memes["care"] += 1
    return ["__brave__"]


def _r_pride(world: World) -> list[str]:
    hero = world.entities.get("hero")
    if hero is None:
        return []
    if hero.meters["crossed"] < THRESHOLD and hero.meters["practiced"] < THRESHOLD:
        return []
    sig = ("pride", hero.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["pride"] += 1
    return []


CAUSAL_RULES: list[Rule] = [
    Rule(name="wobble", tag="physical", apply=_r_wobble),
    Rule(name="brave_chant", tag="emotional", apply=_r_brave_chant),
    Rule(name="pride", tag="emotional", apply=_r_pride),
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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SCENES: dict[str, Scene] = {
    "playground_roof": Scene(
        id="playground_roof",
        place="the playground",
        opening="The red slide became a rocket tower, the sandbox became a cloud dock, and the black safety mats became the roofs of the city.",
        mission_name="Sky Bar Rescue",
        rescue_item="a small stuffed fox",
        skyline="Above the swings, the whole playground looked like a city waiting for help.",
        tags={"playground", "superhero"},
    ),
    "schoolyard_base": Scene(
        id="schoolyard_base",
        place="the schoolyard",
        opening="The painted circles on the ground became secret launch pads, and the climbing frame became Hero Base.",
        mission_name="Morning Bar Patrol",
        rescue_item="a silver lunch box",
        skyline="From the far end of the yard, the bars looked like a shining bridge between tall towers.",
        tags={"schoolyard", "superhero"},
    ),
    "park_training": Scene(
        id="park_training",
        place="the park",
        opening="The bench became a command station, the bushes became dark villain caves, and the climbing frame became the brave tower.",
        mission_name="Star Bar Mission",
        rescue_item="a tiny cape pin",
        skyline="In the bright afternoon, the bars flashed like a hero road in the sky.",
        tags={"park", "superhero"},
    ),
}

BARS: dict[str, Bar] = {
    "practice_bar": Bar(
        id="practice_bar",
        label="practice bar",
        phrase="the low practice bar",
        difficulty=1,
        height_word="low",
        shimmer="It was close to the ground and warm from the sun.",
        tags={"bar", "practice"},
    ),
    "balance_bar": Bar(
        id="balance_bar",
        label="balance bar",
        phrase="the middle balance bar",
        difficulty=2,
        height_word="middle-high",
        shimmer="It stretched straight ahead like a silver path.",
        tags={"bar", "balance"},
    ),
    "rescue_bar": Bar(
        id="rescue_bar",
        label="rescue bar",
        phrase="the high rescue bar",
        difficulty=3,
        height_word="high",
        shimmer="It gleamed above the mats, long and narrow, like the edge of a rooftop.",
        tags={"bar", "high"},
    ),
}

NERVES: dict[str, Nerve] = {
    "fluttery": Nerve(
        id="fluttery",
        label="fluttery",
        level=1,
        body_sign="a tiny jump in the belly",
        thought="Maybe this is harder than it looked.",
        tags={"nervous"},
    ),
    "nervous": Nerve(
        id="nervous",
        label="nervous",
        level=2,
        body_sign="a slow, shaky feeling in the knees",
        thought="What if my feet miss the bar?",
        tags={"nervous"},
    ),
    "very_nervous": Nerve(
        id="very_nervous",
        label="very nervous",
        level=3,
        body_sign="hands that wanted to squeeze into little fists",
        thought="What if I freeze right in the middle?",
        tags={"nervous"},
    ),
}

METHODS: dict[str, Method] = {
    "mantra": Method(
        id="mantra",
        label="a brave whisper",
        support=1,
        text="leaned close and taught a tiny hero rhythm",
        repeated_words="Breathe, grip, step.",
        allows_practice=False,
        tags={"repetition", "breathing"},
    ),
    "counting": Method(
        id="counting",
        label="counting out loud",
        support=2,
        text="raised a hand and counted each move like a mission clock",
        repeated_words="One brave step. One brave step. One brave step.",
        allows_practice=False,
        tags={"repetition", "counting"},
    ),
    "hand_hold": Method(
        id="hand_hold",
        label="a steady hand",
        support=2,
        text="offered a steady hand at the start and a calm voice all the way across",
        repeated_words="Hold, breathe, go.",
        allows_practice=False,
        tags={"repetition", "support"},
    ),
    "practice_first": Method(
        id="practice_first",
        label="a smaller start",
        support=2,
        text="pointed to the low bar first and turned the big mission into two small missions",
        repeated_words="Small step, strong step.",
        allows_practice=True,
        tags={"repetition", "practice"},
    ),
}

HELPERS: dict[str, HelperCfg] = {
    "mom": HelperCfg(
        id="mom",
        helper_type="mother",
        helper_name="Mom",
        bonus=1,
        style="with a smile that stayed calm even when the mission felt big",
        tags={"family"},
    ),
    "dad": HelperCfg(
        id="dad",
        helper_type="father",
        helper_name="Dad",
        bonus=1,
        style="with a quiet superhero nod",
        tags={"family"},
    ),
    "coach": HelperCfg(
        id="coach",
        helper_type="coach",
        helper_name="Coach Ray",
        bonus=1,
        style="like someone who had seen many nervous heroes become steady ones",
        tags={"coach"},
    ),
    "grandma": HelperCfg(
        id="grandma",
        helper_type="grandmother",
        helper_name="Grandma June",
        bonus=1,
        style="with soft eyes and a cape-patterned scarf",
        tags={"family"},
    ),
}

GIRL_NAMES = ["Luna", "Mia", "Zoe", "Ava", "Nina", "Ruby", "Ivy", "Tess"]
BOY_NAMES = ["Kai", "Leo", "Max", "Finn", "Eli", "Theo", "Jude", "Noah"]
TRAITS = ["quick", "careful", "bright", "hopeful", "bouncy", "thoughtful"]


# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    scene: str
    bar: str
    nerve: str
    method: str
    helper: str
    hero_name: str
    hero_gender: str
    hero_trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Constraint logic
# ---------------------------------------------------------------------------
def support_total(method_id: str, helper_id: str) -> int:
    return METHODS[method_id].support + HELPERS[helper_id].bonus


def required_support(bar_id: str, nerve_id: str) -> int:
    return BARS[bar_id].difficulty + NERVES[nerve_id].level


def combo_is_reasonable(bar_id: str, nerve_id: str, method_id: str, helper_id: str) -> bool:
    total = support_total(method_id, helper_id)
    need = required_support(bar_id, nerve_id)
    if total >= need:
        return True
    if METHODS[method_id].allows_practice and total + 1 >= need:
        return True
    return False


def outcome_of(params: StoryParams) -> str:
    need = required_support(params.bar, params.nerve)
    total = support_total(params.method, params.helper)
    if total >= need:
        return "crossed"
    if METHODS[params.method].allows_practice and total + 1 >= need:
        return "practiced_then_crossed"
    return "?"


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for scene_id in SCENES:
        for bar_id in BARS:
            for nerve_id in NERVES:
                for method_id in METHODS:
                    for helper_id in HELPERS:
                        if combo_is_reasonable(bar_id, nerve_id, method_id, helper_id):
                            combos.append((scene_id, bar_id, nerve_id, method_id, helper_id))
    return combos


def explain_rejection(bar_id: str, nerve_id: str, method_id: str, helper_id: str) -> str:
    bar = BARS[bar_id]
    nerve = NERVES[nerve_id]
    method = METHODS[method_id]
    helper = HELPERS[helper_id]
    total = support_total(method_id, helper_id)
    need = required_support(bar_id, nerve_id)
    if not method.allows_practice:
        return (
            f"(No story: {method.label} from {helper.helper_name} is too thin a fix for "
            f"a {nerve.label} child on {bar.phrase}. The support score is {total}, but "
            f"this mission needs {need}. Try counting, a steadier helper, or practice first.)"
        )
    return (
        f"(No story: even starting smaller, {method.label} from {helper.helper_name} is not "
        f"enough for {bar.phrase} when the hero feels {nerve.label}. The support score is "
        f"{total}, and this mission needs at least {need - 1} plus practice.)"
    )


# ---------------------------------------------------------------------------
# Simulation helpers
# ---------------------------------------------------------------------------
def predict(world: World, params: StoryParams) -> dict[str, int | str]:
    sim = world.copy()
    hero = sim.get("hero")
    bar_ent = sim.get("bar")
    hero.memes["nervous"] = float(NERVES[params.nerve].level)
    bar_ent.meters["faced"] = 1.0
    sim.facts["repeated"] = True
    propagate(sim, narrate=False)
    return {
        "need": required_support(params.bar, params.nerve),
        "support": support_total(params.method, params.helper),
        "outcome": outcome_of(params),
        "wobble": int(hero.meters["wobble"]),
        "courage": int(hero.memes["courage"]),
    }


def introduce(world: World, scene: Scene, hero: Entity) -> None:
    world.say(
        f"{hero.id} was a little {hero.attrs['trait']} {hero.type} who never walked into "
        f"{scene.place} in an ordinary way."
    )
    world.say(scene.opening)
    world.say(
        f"Today {hero.pronoun()} tugged {hero.pronoun('possessive')} cape straight and announced "
        f'that it was time for {scene.mission_name}.'
    )


def mission_setup(world: World, scene: Scene, bar: Bar, hero: Entity) -> None:
    world.say(
        f"On the far side of {bar.phrase} waited {scene.rescue_item}. "
        f"{scene.skyline}"
    )
    world.say(bar.shimmer)
    bar_ent = world.get("bar")
    bar_ent.meters["faced"] = 1.0
    propagate(world, narrate=False)


def nervous_turn(world: World, hero: Entity, nerve: Nerve, bar: Bar) -> None:
    hero.memes["nervous"] = float(nerve.level)
    hero.meters["pause"] += 1
    world.say(
        f"But when {hero.id} stood in front of {bar.phrase}, {hero.pronoun('possessive')} "
        f"superhero boots felt suddenly small. A {nerve.body_sign} moved through "
        f"{hero.pronoun('object')}, and {hero.pronoun()} felt {nerve.label}."
    )
    world.say(f"{hero.id} looked at the bar and thought, {nerve.thought}")
    propagate(world, narrate=False)


def helper_arrives(world: World, helper: Entity, method: Method, hero: Entity) -> None:
    world.say(
        f"{helper.id} came beside {hero.id} {helper.attrs['style']}. "
        f"{helper.pronoun().capitalize()} {method.text}."
    )


def repeat_brave_words(world: World, hero: Entity, helper: Entity, method: Method) -> None:
    world.facts["repeated"] = True
    world.say(
        f'"{method.repeated_words}" {helper.id} said. '
        f'"{method.repeated_words}" {hero.id} whispered back.'
    )
    world.say(
        f'Again they said it: "{method.repeated_words}" Again {hero.id} said it: '
        f'"{method.repeated_words}"'
    )
    propagate(world, narrate=False)


def cross_big_bar(world: World, scene: Scene, bar: Bar, hero: Entity, method: Method) -> None:
    hero.meters["crossed"] += 1
    hero.meters["steps"] += float(bar.difficulty)
    hero.memes["nervous"] = max(0.0, hero.memes["nervous"] - 1.0)
    world.say(
        f"{hero.id} lifted one foot, then the other. {method.repeated_words} "
        f"Step by step, step by step, {hero.pronoun()} moved along the bar."
    )
    world.say(
        f"The wobble in {hero.pronoun('possessive')} knees did not boss {hero.pronoun('object')} "
        f"around anymore. It was still there, but courage was there too."
    )
    world.say(
        f"At the end of the bar, {hero.id} scooped up {scene.rescue_item} and held it high. "
        f'The mission was saved.'
    )
    propagate(world, narrate=False)


def practice_then_cross(world: World, scene: Scene, hero: Entity, big_bar: Bar, method: Method) -> None:
    hero.meters["practiced"] += 1
    world.say(
        f"{hero.id} did not leap at the big bar. Instead, {hero.pronoun()} started on the low practice bar."
    )
    world.say(
        f'{method.repeated_words} Once across the small bar. {method.repeated_words} '
        f'Twice across the small bar. {method.repeated_words} Three times across the small bar.'
    )
    hero.memes["courage"] += 1
    hero.memes["nervous"] = max(0.0, hero.memes["nervous"] - 1.0)
    world.say(
        f"By the third try, {hero.id}'s shoulders had dropped and {hero.pronoun('possessive')} "
        f"steps had become strong."
    )
    hero.meters["crossed"] += 1
    world.say(
        f"Then {hero.pronoun()} turned back to {big_bar.phrase}. This time the bar still looked high, "
        f"but it no longer looked impossible."
    )
    world.say(
        f"{hero.id} crossed it with careful feet and a brave grin, reached {scene.rescue_item}, "
        f"and tapped {hero.pronoun('possessive')} chest like a true hero."
    )
    propagate(world, narrate=False)


def closing_image(world: World, hero: Entity, scene: Scene, bar: Bar) -> None:
    world.say(
        f"When the game was over, {bar.phrase} was still just a bar in {scene.place}. "
        f"But to {hero.id}, it had become proof."
    )
    world.say(
        f"A hero could feel nervous, whisper brave words, and still keep going."
    )


def tell(
    scene: Scene,
    bar: Bar,
    nerve: Nerve,
    method: Method,
    helper_cfg: HelperCfg,
    hero_name: str,
    hero_gender: str,
    hero_trait: str,
) -> World:
    world = World()
    hero = world.add(
        Entity(
            id=hero_name,
            kind="character",
            type=hero_gender,
            label=hero_name,
            role="hero",
            attrs={"trait": hero_trait},
            tags={"hero"},
        )
    )
    helper = world.add(
        Entity(
            id=helper_cfg.helper_name,
            kind="character",
            type=helper_cfg.helper_type,
            label=helper_cfg.helper_name,
            role="helper",
            attrs={"style": helper_cfg.style},
            tags=set(helper_cfg.tags),
        )
    )
    world.add(
        Entity(
            id="bar",
            kind="thing",
            type="bar",
            label=bar.label,
            phrase=bar.phrase,
            tags=set(bar.tags),
        )
    )
    world.add(
        Entity(
            id="token",
            kind="thing",
            type="rescue_item",
            label=scene.rescue_item,
            phrase=scene.rescue_item,
        )
    )

    introduce(world, scene, hero)
    mission_setup(world, scene, bar, hero)

    world.para()
    nervous_turn(world, hero, nerve, bar)
    helper_arrives(world, helper, method, hero)
    repeat_brave_words(world, hero, helper, method)

    world.para()
    out = outcome_of(
        StoryParams(
            scene=scene.id,
            bar=bar.id,
            nerve=nerve.id,
            method=method.id,
            helper=helper_cfg.id,
            hero_name=hero_name,
            hero_gender=hero_gender,
            hero_trait=hero_trait,
        )
    )
    if out == "crossed":
        cross_big_bar(world, scene, bar, hero, method)
    elif out == "practiced_then_crossed":
        practice_then_cross(world, scene, hero, bar, method)
    else:
        raise StoryError("Internal outcome mismatch: unreasonable story escaped the gate.")

    world.para()
    closing_image(world, hero, scene, bar)

    world.facts.update(
        scene=scene,
        bar_cfg=bar,
        nerve_cfg=nerve,
        method_cfg=method,
        helper_cfg=helper_cfg,
        hero=hero,
        helper=helper,
        outcome=out,
        repeated_words=method.repeated_words,
        support=support_total(method.id, helper_cfg.id),
        need=required_support(bar.id, nerve.id),
        predicted=predict(
            world,
            StoryParams(
                scene=scene.id,
                bar=bar.id,
                nerve=nerve.id,
                method=method.id,
                helper=helper_cfg.id,
                hero_name=hero_name,
                hero_gender=hero_gender,
                hero_trait=hero_trait,
            ),
        ),
    )
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
KNOWLEDGE: dict[str, list[tuple[str, str]]] = {
    "bar": [
        (
            "What is a bar on a playground?",
            "A playground bar is a strong metal bar children can hold, swing from, or balance along. It helps them practice climbing and balance.",
        )
    ],
    "nervous": [
        (
            "What does nervous mean?",
            "Nervous means you feel worried or shaky because something seems hard, new, or a little scary. Your body might feel fluttery, tight, or wobbly.",
        )
    ],
    "repetition": [
        (
            "Why can saying the same brave words again and again help?",
            "Repetition can help because it gives your mind one simple thing to hold onto. The repeated words make your body slow down and feel steadier.",
        )
    ],
    "breathing": [
        (
            "Why do people take deep breaths when they feel nervous?",
            "Slow breaths tell your body to calm down. That can make your hands, legs, and thoughts feel steadier.",
        )
    ],
    "counting": [
        (
            "How can counting help when something feels hard?",
            "Counting breaks one big job into small parts. Then you only have to do the next step instead of worrying about the whole thing at once.",
        )
    ],
    "practice": [
        (
            "Why is it smart to practice on an easier thing first?",
            "Practicing on an easier version helps your body learn the moves safely. Then the bigger challenge feels more familiar.",
        )
    ],
    "superhero": [
        (
            "Does being brave mean never feeling scared?",
            "No. Being brave means doing the right or steady thing even when you feel scared or nervous.",
        )
    ],
}
KNOWLEDGE_ORDER = ["bar", "nervous", "repetition", "breathing", "counting", "practice", "superhero"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    scene = f["scene"]
    bar = f["bar_cfg"]
    nerve = f["nerve_cfg"]
    method = f["method_cfg"]
    out = f["outcome"]
    prompts = [
        (
            f'Write a short superhero story for a 3-to-5-year-old that includes the words '
            f'"nervous" and "bar".'
        ),
        (
            f"Tell a gentle superhero story where {hero.id} feels {nerve.label} in front of "
            f"{bar.phrase} and uses repetition to become brave."
        ),
    ]
    if out == "practiced_then_crossed":
        prompts.append(
            f"Write a superhero training story set in {scene.place} where a child starts smaller, "
            f"repeats '{method.repeated_words}', and then succeeds on the bigger bar."
        )
    else:
        prompts.append(
            f"Write a superhero mission in {scene.place} where a child repeats '{method.repeated_words}' "
            f"and crosses a bar to save something important."
        )
    return prompts


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    scene = f["scene"]
    bar = f["bar_cfg"]
    nerve = f["nerve_cfg"]
    method = f["method_cfg"]
    out = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, a child pretending to be a superhero, and {helper.id}, who helps during the mission.",
        ),
        (
            "Why did the hero feel nervous?",
            f"{hero.id} felt {nerve.label} because {bar.phrase} looked hard and high. The big mission made {hero.pronoun('possessive')} body feel shaky before {hero.pronoun()} even stepped onto the bar.",
        ),
        (
            f"What words did {hero.id} repeat?",
            f'{hero.id} repeated, "{method.repeated_words}" {method.repeated_words} was the brave rhythm that helped {hero.pronoun('object')} focus on one step at a time.',
        ),
    ]
    if out == "crossed":
        qa.append(
            (
                f"How did {hero.id} get across the bar?",
                f"{helper.id} helped with {method.label}, and {hero.id} kept repeating the brave words while moving step by step. The repetition turned one big scary job into small steady actions.",
            )
        )
    else:
        qa.append(
            (
                f"Why did {hero.id} start on the practice bar first?",
                f"{hero.id} was too nervous to jump straight onto the bigger bar, so {helper.id} made the mission smaller first. Practice gave {hero.pronoun('object')} time to feel steadier before trying the high bar again.",
            )
        )
    qa.append(
        (
            "How did the story end?",
            f"It ended with {hero.id} finishing the mission and seeing the bar in a new way. The bar was still a bar in {scene.place}, but now it proved that a hero can feel nervous and still be brave.",
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = {"bar", "nervous", "repetition", "superhero"}
    method = world.facts["method_cfg"]
    tags |= set(method.tags)
    if world.facts["outcome"] == "practiced_then_crossed":
        tags.add("practice")
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


# ---------------------------------------------------------------------------
# Trace
# ---------------------------------------------------------------------------
def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for ent in world.entities.values():
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits: list[str] = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:10} ({ent.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
reasonable(Scene, Bar, Nerve, Method, Helper) :-
    scene(Scene), bar(Bar), nerve(Nerve), method(Method), helper(Helper),
    support(Method, MS), bonus(Helper, HB), need(Bar, Nerve, Need),
    MS + HB >= Need.

reasonable(Scene, Bar, Nerve, Method, Helper) :-
    scene(Scene), bar(Bar), nerve(Nerve), method(Method), helper(Helper),
    allows_practice(Method),
    support(Method, MS), bonus(Helper, HB), need(Bar, Nerve, Need),
    MS + HB + 1 >= Need.

outcome(crossed) :-
    chosen_bar(Bar), chosen_nerve(Nerve), chosen_method(Method), chosen_helper(Helper),
    support(Method, MS), bonus(Helper, HB), need(Bar, Nerve, Need),
    MS + HB >= Need.

outcome(practiced_then_crossed) :-
    chosen_bar(Bar), chosen_nerve(Nerve), chosen_method(Method), chosen_helper(Helper),
    allows_practice(Method),
    support(Method, MS), bonus(Helper, HB), need(Bar, Nerve, Need),
    MS + HB < Need, MS + HB + 1 >= Need.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for scene_id in SCENES:
        lines.append(asp.fact("scene", scene_id))
    for bar_id, bar in BARS.items():
        lines.append(asp.fact("bar", bar_id))
        lines.append(asp.fact("bar_difficulty", bar_id, bar.difficulty))
    for nerve_id, nerve in NERVES.items():
        lines.append(asp.fact("nerve", nerve_id))
        lines.append(asp.fact("nerve_level", nerve_id, nerve.level))
    for method_id, method in METHODS.items():
        lines.append(asp.fact("method", method_id))
        lines.append(asp.fact("support", method_id, method.support))
        if method.allows_practice:
            lines.append(asp.fact("allows_practice", method_id))
    for helper_id, helper in HELPERS.items():
        lines.append(asp.fact("helper", helper_id))
        lines.append(asp.fact("bonus", helper_id, helper.bonus))
    for bar_id, bar in BARS.items():
        for nerve_id, nerve in NERVES.items():
            lines.append(asp.fact("need", bar_id, nerve_id, bar.difficulty + nerve.level))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show reasonable/5."))
    return sorted(set(asp.atoms(model, "reasonable")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_bar", params.bar),
            asp.fact("chosen_nerve", params.nerve),
            asp.fact("chosen_method", params.method),
            asp.fact("chosen_helper", params.helper),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


# ---------------------------------------------------------------------------
# Curated set
# ---------------------------------------------------------------------------
CURATED: list[StoryParams] = [
    StoryParams(
        scene="playground_roof",
        bar="balance_bar",
        nerve="nervous",
        method="counting",
        helper="mom",
        hero_name="Luna",
        hero_gender="girl",
        hero_trait="bright",
    ),
    StoryParams(
        scene="schoolyard_base",
        bar="rescue_bar",
        nerve="very_nervous",
        method="practice_first",
        helper="coach",
        hero_name="Max",
        hero_gender="boy",
        hero_trait="careful",
    ),
    StoryParams(
        scene="park_training",
        bar="practice_bar",
        nerve="fluttery",
        method="mantra",
        helper="grandma",
        hero_name="Ivy",
        hero_gender="girl",
        hero_trait="hopeful",
    ),
    StoryParams(
        scene="playground_roof",
        bar="rescue_bar",
        nerve="nervous",
        method="hand_hold",
        helper="dad",
        hero_name="Leo",
        hero_gender="boy",
        hero_trait="quick",
    ),
]


# ---------------------------------------------------------------------------
# Standard interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a nervous child faces a bar like a superhero and uses repetition to get brave."
    )
    ap.add_argument("--scene", choices=SCENES)
    ap.add_argument("--bar", choices=BARS)
    ap.add_argument("--nerve", choices=NERVES)
    ap.add_argument("--method", choices=METHODS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.bar and args.nerve and args.method and args.helper:
        if not combo_is_reasonable(args.bar, args.nerve, args.method, args.helper):
            raise StoryError(explain_rejection(args.bar, args.nerve, args.method, args.helper))

    combos = [
        combo
        for combo in valid_combos()
        if (args.scene is None or combo[0] == args.scene)
        and (args.bar is None or combo[1] == args.bar)
        and (args.nerve is None or combo[2] == args.nerve)
        and (args.method is None or combo[3] == args.method)
        and (args.helper is None or combo[4] == args.helper)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    scene_id, bar_id, nerve_id, method_id, helper_id = rng.choice(sorted(combos))
    hero_gender = args.gender or rng.choice(["girl", "boy"])
    pool = GIRL_NAMES if hero_gender == "girl" else BOY_NAMES
    hero_name = args.name or rng.choice(pool)
    hero_trait = rng.choice(TRAITS)
    return StoryParams(
        scene=scene_id,
        bar=bar_id,
        nerve=nerve_id,
        method=method_id,
        helper=helper_id,
        hero_name=hero_name,
        hero_gender=hero_gender,
        hero_trait=hero_trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.scene not in SCENES:
        raise StoryError(f"(Invalid scene: {params.scene})")
    if params.bar not in BARS:
        raise StoryError(f"(Invalid bar: {params.bar})")
    if params.nerve not in NERVES:
        raise StoryError(f"(Invalid nerve: {params.nerve})")
    if params.method not in METHODS:
        raise StoryError(f"(Invalid method: {params.method})")
    if params.helper not in HELPERS:
        raise StoryError(f"(Invalid helper: {params.helper})")
    if not combo_is_reasonable(params.bar, params.nerve, params.method, params.helper):
        raise StoryError(explain_rejection(params.bar, params.nerve, params.method, params.helper))

    world = tell(
        scene=SCENES[params.scene],
        bar=BARS[params.bar],
        nerve=NERVES[params.nerve],
        method=METHODS[params.method],
        helper_cfg=HELPERS[params.helper],
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        hero_trait=params.hero_trait,
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

    py_set = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py_set == asp_set:
        print(f"OK: ASP gate matches valid_combos() ({len(py_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in compatible combos:")
        if asp_set - py_set:
            print("  only in ASP:", sorted(asp_set - py_set))
        if py_set - asp_set:
            print("  only in Python:", sorted(py_set - asp_set))

    cases: list[StoryParams] = list(CURATED)
    for seed in range(30):
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
        print(f"OK: ASP outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("Smoke test produced an empty story.")
        print("OK: smoke-test story generation succeeded.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show reasonable/5.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (scene, bar, nerve, method, helper) combos:\n")
        for scene_id, bar_id, nerve_id, method_id, helper_id in combos:
            print(f"  {scene_id:16} {bar_id:13} {nerve_id:12} {method_id:14} {helper_id}")
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero_name}: {p.nerve} on {p.bar} with {p.method}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
