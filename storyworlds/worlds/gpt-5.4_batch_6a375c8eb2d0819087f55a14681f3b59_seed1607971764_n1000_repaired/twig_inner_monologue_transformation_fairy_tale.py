#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/twig_inner_monologue_transformation_fairy_tale.py
============================================================================

A standalone story world for a small fairy-tale domain built around a humble
twig, a child's inner monologue, and a magical transformation.

Premise
-------
A child in a storybook place finds a plain twig and meets a gentle problem in
the world: a dark path, a fallen nest, or a thorn gate. The child wonders,
silently, whether something so small can help. If the child's heart is already
steady, the twig wakes at once. If not, a nearby guide gives one true sentence
of advice, and the child tries again. In either case, the turn is a visible
transformation: the twig becomes the exact magical thing needed.

Reasonableness rule
-------------------
Not every transformation fits every problem, and not every guide belongs in
every setting. The world only generates combinations where:

* the setting honestly contains the problem
* the twig's transformed shape really solves that problem
* the chosen guide plausibly lives in or watches over that setting

The result is a tiny but coherent fairy-tale simulation rather than a paragraph
with swapped nouns.

Run it
------
    python storyworlds/worlds/gpt-5.4/twig_inner_monologue_transformation_fairy_tale.py
    python storyworlds/worlds/gpt-5.4/twig_inner_monologue_transformation_fairy_tale.py --problem dark_path
    python storyworlds/worlds/gpt-5.4/twig_inner_monologue_transformation_fairy_tale.py --transform nest_cradle
    python storyworlds/worlds/gpt-5.4/twig_inner_monologue_transformation_fairy_tale.py --all
    python storyworlds/worlds/gpt-5.4/twig_inner_monologue_transformation_fairy_tale.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/twig_inner_monologue_transformation_fairy_tale.py --trace
    python storyworlds/worlds/gpt-5.4/twig_inner_monologue_transformation_fairy_tale.py --asp
    python storyworlds/worlds/gpt-5.4/twig_inner_monologue_transformation_fairy_tale.py --verify
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
STRONG_TRAITS = {"brave", "hopeful", "steady"}


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
        female = {"girl", "woman", "mother", "fairy_godmother"}
        male = {"boy", "man", "father"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type.replace("_", " ")


@dataclass
class Setting:
    id: str
    place: str
    opening: str
    shimmer: str
    affords: set[str] = field(default_factory=set)
    guides: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class Problem:
    id: str
    need: str
    title: str
    trouble: str
    wish: str
    ending: str
    target_label: str
    target_phrase: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class Transformation:
    id: str
    power: str
    form: str
    awaken: str
    solve_text: str
    keepsake: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class Guide:
    id: str
    label: str
    phrase: str
    advice: str
    sign: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


def _r_awaken(world: World) -> list[str]:
    hero = world.get("hero")
    twig = world.get("twig")
    if hero.memes["resolve"] < THRESHOLD:
        return []
    if twig.meters["awakened"] >= THRESHOLD:
        return []
    sig = ("awaken",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    twig.meters["awakened"] += 1
    twig.meters["magic"] += 1
    hero.memes["wonder"] += 1
    return ["__awakened__"]


def _r_solve(world: World) -> list[str]:
    twig = world.get("twig")
    target = world.get("target")
    hero = world.get("hero")
    need = world.facts["problem_cfg"].need
    power = world.facts["transform_cfg"].power
    if twig.meters["awakened"] < THRESHOLD:
        return []
    if need != power:
        return []
    sig = ("solve", need)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    target.meters["fixed"] += 1
    hero.memes["relief"] += 1
    hero.memes["joy"] += 1
    return ["__solved__"]


CAUSAL_RULES = [
    Rule(name="awaken", tag="magic", apply=_r_awaken),
    Rule(name="solve", tag="magic", apply=_r_solve),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
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


def problem_in_setting(setting: Setting, problem: Problem) -> bool:
    return problem.id in setting.affords


def guide_in_setting(setting: Setting, guide: Guide) -> bool:
    return guide.id in setting.guides


def transformation_fits(problem: Problem, transform: Transformation) -> bool:
    return problem.need == transform.power


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for setting_id, setting in SETTINGS.items():
        for problem_id, problem in PROBLEMS.items():
            if not problem_in_setting(setting, problem):
                continue
            for transform_id, transform in TRANSFORMATIONS.items():
                if not transformation_fits(problem, transform):
                    continue
                for guide_id, guide in GUIDES.items():
                    if guide_in_setting(setting, guide):
                        combos.append((setting_id, problem_id, transform_id, guide_id))
    return sorted(combos)


def needs_help(trait: str) -> bool:
    return trait not in STRONG_TRAITS


def predict_solution(world: World) -> dict:
    sim = world.copy()
    sim.get("hero").memes["resolve"] += 1
    propagate(sim, narrate=False)
    return {
        "awakened": sim.get("twig").meters["awakened"] >= THRESHOLD,
        "fixed": sim.get("target").meters["fixed"] >= THRESHOLD,
    }


def introduce(world: World, hero: Entity, setting: Setting) -> None:
    world.say(
        f"Once, in {setting.place}, there lived {hero.id}, a little {hero.type} "
        f"with {hero.attrs['trait_phrase']} and a listening heart."
    )
    world.say(setting.opening)
    world.say(setting.shimmer)


def find_twig(world: World, hero: Entity) -> None:
    hero.memes["curiosity"] += 1
    world.say(
        f"By the path, {hero.id} found a twig no longer than {hero.pronoun('possessive')} hand. "
        f"It was plain brown, with one silver bead of dew resting on it."
    )


def meet_problem(world: World, hero: Entity, problem: Problem) -> None:
    hero.memes["care"] += 1
    world.say(problem.trouble)
    world.say(
        f"{hero.id} stopped at once. {problem.wish}"
    )


def inner_monologue(world: World, hero: Entity, problem: Problem) -> None:
    hero.memes["doubt"] += 1
    world.say(
        f'Inside, {hero.id} thought, "I am small, and this twig is small too. '
        f'Can a little thing mend {problem.title}?"'
    )
    world.say(
        f'Then another thought came softly: "If I walk away, {problem.title} will stay sad. '
        f'I must at least try."'
    )


def first_try(world: World, hero: Entity, transform: Transformation) -> None:
    pred = predict_solution(world)
    world.facts["predicted_awakened"] = pred["awakened"]
    world.facts["predicted_fixed"] = pred["fixed"]
    world.say(
        f"{hero.id} held the twig in both hands and whispered to it. "
        f"{transform.awaken}"
    )


def guide_arrives(world: World, guide_ent: Entity, guide_cfg: Guide) -> None:
    world.say(guide_cfg.sign)
    world.say(
        f'"{guide_cfg.advice}" said {guide_ent.phrase}.'
    )


def take_advice(world: World, hero: Entity) -> None:
    hero.memes["courage"] += 1
    hero.memes["resolve"] += 1
    world.say(
        f"{hero.id} took a slower breath. The frightened thought inside "
        f"{hero.pronoun('object')} grew smaller, and the brave one grew bright."
    )


def self_belief(world: World, hero: Entity) -> None:
    hero.memes["courage"] += 1
    hero.memes["resolve"] += 1
    world.say(
        f"{hero.id} straightened {hero.pronoun('possessive')} shoulders and answered the shy thought inside: "
        f'"Small is not the same as useless."'
    )


def transform_and_solve(
    world: World,
    hero: Entity,
    problem: Problem,
    transform: Transformation,
) -> None:
    propagate(world, narrate=False)
    twig = world.get("twig")
    target = world.get("target")
    if twig.meters["awakened"] < THRESHOLD or target.meters["fixed"] < THRESHOLD:
        raise StoryError("(Story crashed: the twig should have awakened and solved the problem here.)")
    world.say(transform.awaken)
    world.say(transform.solve_text.format(target=problem.target_label))
    world.say(problem.ending)


def ending_image(world: World, hero: Entity, transform: Transformation, guide_ent: Entity, outcome: str) -> None:
    if outcome == "helped":
        world.say(
            f"When the work was done, {guide_ent.label_word} bowed once and slipped back into the shining leaves."
        )
    else:
        world.say(
            f"No one clapped and no trumpet sounded, but {hero.id} knew something true had changed inside "
            f"{hero.pronoun('object')}."
        )
    world.say(
        f"{hero.id} tucked the {transform.keepsake} behind {hero.pronoun('possessive')} ear for the walk home, "
        f"and even the wind seemed to whisper that a humble twig may hold a brave kind of magic."
    )


def tell(
    setting: Setting,
    problem: Problem,
    transform: Transformation,
    guide_cfg: Guide,
    hero_name: str = "Elin",
    hero_type: str = "girl",
    trait: str = "hopeful",
    parent_title: str = "grandmother",
) -> World:
    world = World(setting)
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_type,
        role="hero",
        traits=[trait],
        attrs={"trait_phrase": TRAIT_PHRASES[trait], "parent_title": parent_title},
    ))
    guide_ent = world.add(Entity(
        id="guide",
        kind="character",
        type="guide",
        label=guide_cfg.label,
        phrase=guide_cfg.phrase,
        role="guide",
        tags=set(guide_cfg.tags),
    ))
    twig = world.add(Entity(
        id="twig",
        type="twig",
        label="twig",
        phrase="a little twig",
        role="tool",
        tags={"twig"},
    ))
    target = world.add(Entity(
        id="target",
        type="target",
        label=problem.target_label,
        phrase=problem.target_phrase,
        role="target",
        tags=set(problem.tags),
    ))

    hero.memes["curiosity"] = 0.0
    hero.memes["care"] = 0.0
    hero.memes["doubt"] = 0.0
    hero.memes["courage"] = 1.0 if not needs_help(trait) else 0.0
    hero.memes["resolve"] = 0.0
    hero.memes["wonder"] = 0.0
    hero.memes["relief"] = 0.0
    hero.memes["joy"] = 0.0
    twig.meters["awakened"] = 0.0
    twig.meters["magic"] = 0.0
    target.meters["fixed"] = 0.0

    world.facts.update(
        hero=hero,
        guide=guide_ent,
        setting=setting,
        problem_cfg=problem,
        transform_cfg=transform,
        target=target,
        twig=twig,
        branch="helped" if needs_help(trait) else "self",
        parent_title=parent_title,
        resolved=False,
    )

    introduce(world, hero, setting)
    find_twig(world, hero)
    world.para()
    meet_problem(world, hero, problem)
    inner_monologue(world, hero, problem)
    first_try(world, hero, transform)

    world.para()
    if needs_help(trait):
        guide_arrives(world, guide_ent, guide_cfg)
        take_advice(world, hero)
        outcome = "helped"
    else:
        self_belief(world, hero)
        outcome = "self"

    transform_and_solve(world, hero, problem, transform)
    world.para()
    ending_image(world, hero, transform, guide_ent, outcome)

    world.facts["resolved"] = target.meters["fixed"] >= THRESHOLD
    world.facts["outcome"] = outcome
    return world


SETTINGS = {
    "moon_meadow": Setting(
        id="moon_meadow",
        place="the Moon Meadow",
        opening="Every blade of grass wore a pearl of dew, and the moon hung low like a patient lamp.",
        shimmer="Nothing in that meadow hurried; even the crickets seemed to sing in careful silver stitches.",
        affords={"dark_path"},
        guides={"firefly"},
        tags={"night", "meadow"},
    ),
    "rose_lane": Setting(
        id="rose_lane",
        place="Rose Lane beside the old spring",
        opening="The hedges curved like green walls, and pale roses leaned out as if they were listening for secrets.",
        shimmer="At the lane's end stood a gate of sleeping thorns that opened only for gentle hands.",
        affords={"thorn_gate"},
        guides={"robin", "owl"},
        tags={"garden", "roses"},
    ),
    "willow_brook": Setting(
        id="willow_brook",
        place="Willow Brook under the drooping trees",
        opening="The water moved so softly that it seemed to be telling itself a bedtime tale.",
        shimmer="Long willow leaves brushed the air, and the banks smelled of wet earth and mint.",
        affords={"fallen_nest"},
        guides={"owl", "frog"},
        tags={"brook", "willow"},
    ),
}

PROBLEMS = {
    "dark_path": Problem(
        id="dark_path",
        need="light",
        title="the dark path",
        trouble="Soon the path to the cottage bent under the hazel trees, and the light there thinned to almost nothing.",
        wish="Ahead, one tiny lantern by the footbridge had gone dark, and the stones beyond it looked deep and unsure.",
        ending="The path no longer looked like a place for stumbling. It looked like a promise kept.",
        target_label="lantern",
        target_phrase="the dark lantern by the footbridge",
        tags={"lantern", "light"},
    ),
    "thorn_gate": Problem(
        id="thorn_gate",
        need="open",
        title="the thorn gate",
        trouble="At the end of Rose Lane, the thorn gate had woven itself shut so tightly that even sunlight could hardly pass.",
        wish="Behind it, the old spring sang in a thirsty little voice, and the rose roots waited for water.",
        ending="The roses lifted their heads as the first thread of spring water ran through their roots.",
        target_label="gate",
        target_phrase="the sleeping thorn gate",
        tags={"thorns", "gate", "spring"},
    ),
    "fallen_nest": Problem(
        id="fallen_nest",
        need="lift",
        title="the fallen nest",
        trouble="Beside the brook, a small finch's nest had slipped from a low branch and come to rest in the reeds.",
        wish="The mother finch fluttered above it, too worried to sing and too small to lift it back alone.",
        ending="From the safe branch above, the mother finch gave one clear note, and it sounded like thanks.",
        target_label="nest",
        target_phrase="the fallen finch nest",
        tags={"bird", "nest"},
    ),
}

TRANSFORMATIONS = {
    "star_wand": Transformation(
        id="star_wand",
        power="light",
        form="star wand",
        awaken="At once the twig shivered, put out three bright leaves of light, and lengthened into a little star wand.",
        solve_text="It floated to the {target}, touched it gently, and filled it with a warm gold glow.",
        keepsake="silvered twig-wand",
        tags={"light", "magic"},
    ),
    "green_key": Transformation(
        id="green_key",
        power="open",
        form="green key",
        awaken="At once the twig warmed in the child's palms, curled into a green key, and grew a tiny rosebud at its tip.",
        solve_text="It slipped between the thorns of the {target}, and the whole woven lock softened, sighed, and opened outward.",
        keepsake="green key-twig",
        tags={"gate", "magic"},
    ),
    "nest_cradle": Transformation(
        id="nest_cradle",
        power="lift",
        form="nest cradle",
        awaken="At once the twig bent without breaking, spread tender willow fingers, and became a living cradle of green.",
        solve_text="It slid beneath the {target}, rose lightly as a bird's breath, and settled it back on the waiting branch.",
        keepsake="willow cradle-twig",
        tags={"nest", "magic"},
    ),
}

GUIDES = {
    "firefly": Guide(
        id="firefly",
        label="the firefly",
        phrase="the firefly with the lantern-tail",
        advice="Kind hands wake sleeping magic. Ask the twig to help, and believe your own voice when you ask.",
        sign="Then a firefly drifted up, bright as a moving seed of gold.",
        tags={"insect", "light"},
    ),
    "owl": Guide(
        id="owl",
        label="the old owl",
        phrase="the old owl in the branch-crook",
        advice="A true spell is only a brave thought spoken aloud twice: once in fear, and once in faith.",
        sign="From a bent branch above came the round, calm blink of an old owl.",
        tags={"owl", "wisdom"},
    ),
    "frog": Guide(
        id="frog",
        label="the mossy frog",
        phrase="the mossy frog by the stones",
        advice="Small things know how to carry small lives. Hold steady, and let the twig remember the tree it came from.",
        sign="A mossy frog lifted its head from the brook edge and blinked as if it had been waiting.",
        tags={"frog", "brook"},
    ),
}

GIRL_NAMES = ["Elin", "Mara", "Nell", "Iris", "Tessa", "Wren", "Lina", "Orla"]
BOY_NAMES = ["Aren", "Tobin", "Nico", "Bram", "Ewan", "Silas", "Rian", "Milo"]
TRAITS = ["brave", "hopeful", "steady", "timid", "gentle", "dreamy"]
TRAIT_PHRASES = {
    "brave": "quick feet and a brave brow",
    "hopeful": "hopeful eyes and muddy shoes",
    "steady": "steady hands and a patient step",
    "timid": "soft steps and a cautious brow",
    "gentle": "gentle hands and a quiet smile",
    "dreamy": "dreamy eyes and pockets full of wonders",
}
PARENT_TITLES = ["grandmother", "aunt", "mother", "father"]


@dataclass
class StoryParams:
    setting: str
    problem: str
    transform: str
    guide: str
    name: str
    gender: str
    trait: str
    parent_title: str
    seed: Optional[int] = None
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


KNOWLEDGE = {
    "twig": [(
        "What is a twig?",
        "A twig is a very small branch from a tree or bush. It is light in your hand, but in stories it can become something important."
    )],
    "light": [(
        "Why is a light helpful on a dark path?",
        "A light helps you see where the path goes and where your feet should step. It makes hidden stones and turns easier to notice."
    )],
    "lantern": [(
        "What does a lantern do?",
        "A lantern holds a light so people can see in dim places. In fairy tales, a glowing lantern often means guidance and safety."
    )],
    "thorns": [(
        "What are thorns?",
        "Thorns are sharp points that grow on some plants, like roses. They help protect the plant, but they can scratch if you grab them carelessly."
    )],
    "spring": [(
        "What is a spring?",
        "A spring is water that comes up from the ground. It can feed streams, flowers, and thirsty roots."
    )],
    "nest": [(
        "What is a bird's nest for?",
        "A nest is a little home where birds keep eggs or baby birds safe. It needs to stay in a secure place so the family will not tumble out."
    )],
    "owl": [(
        "Why are owls often wise in fairy tales?",
        "Owls are quiet and watchful, so stories often imagine them as wise old helpers. They seem like creatures that notice what others miss."
    )],
    "firefly": [(
        "Why do fireflies glow?",
        "Fireflies make their own little light inside their bodies. Their glow helps them signal to one another in the dark."
    )],
    "frog": [(
        "Where do frogs like to live?",
        "Frogs like wet places such as ponds, brooks, and marshy banks. Their strong legs help them hop and swim there."
    )],
    "magic": [(
        "What kind of magic appears in fairy tales?",
        "Fairy-tale magic often wakes when someone is brave, kind, or truthful. The magic usually changes the world in a way that matches the character's heart."
    )],
}
KNOWLEDGE_ORDER = ["twig", "light", "lantern", "thorns", "spring", "nest", "owl", "firefly", "frog", "magic"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    problem = f["problem_cfg"]
    setting = f["setting"]
    transform = f["transform_cfg"]
    if f["outcome"] == "helped":
        return [
            f'Write a fairy tale for a 3-to-5-year-old that includes the word "twig", a child\'s inner monologue, and a magical transformation in {setting.place}.',
            f"Tell a gentle fairy tale where {hero.id} worries that a twig is too small to help with {problem.title}, but a kindly guide gives one true sentence of advice.",
            f"Write a story where a plain twig becomes a {transform.form} and solves a problem after the child chooses courage over doubt.",
        ]
    return [
        f'Write a fairy tale for a 3-to-5-year-old that includes the word "twig", a child\'s inner monologue, and a magical transformation in {setting.place}.',
        f"Tell a fairy tale where {hero.id} quietly argues with {hero.pronoun('possessive')} own frightened thoughts and discovers that a humble twig can hold real magic.",
        f"Write a story where a plain twig becomes a {transform.form} and solves a problem because the child believes before anyone else does.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    guide = f["guide"]
    problem = f["problem_cfg"]
    transform = f["transform_cfg"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, a little {hero.type} who finds a twig and wants to help. "
            f"The story follows what happens inside {hero.pronoun('possessive')} thoughts as well as what happens in the enchanted place around {hero.pronoun('object')}."
        ),
        (
            "What problem did the child find?",
            f"{hero.id} found {problem.title}. {problem.wish}"
        ),
        (
            "What did the child think inside?",
            f"{hero.id} wondered whether someone small, holding only a twig, could really help. "
            f"That inner question matters because it is the frightened thought {hero.pronoun()} must answer before the magic can wake."
        ),
        (
            "How did the twig change?",
            f"The twig transformed into a {transform.form}. It changed in exactly the way the problem needed, so the magic felt purposeful instead of random."
        ),
    ]
    if outcome == "helped":
        qa.append((
            f"How did {guide.label_word} help {hero.id}?",
            f"{guide.label_word.capitalize()} gave {hero.id} one piece of calm advice and helped {hero.pronoun('object')} try again with courage. "
            f"The guide did not solve the problem alone; the advice made room for {hero.id}'s own brave choice."
        ))
    else:
        qa.append((
            f"Why did the magic wake without help from anyone else?",
            f"The magic woke because {hero.id} answered {hero.pronoun('possessive')} own doubtful thought with a brave one. "
            f"In this story, the transformation follows inner courage, so the change begins inside {hero.pronoun('object')} before it appears in the twig."
        ))
    qa.append((
        "How did the story end?",
        f"It ended with {problem.ending.lower()} "
        f"The final image shows that both the world and the child's heart have changed."
    ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"twig", "magic"}
    problem = world.facts["problem_cfg"]
    guide = world.facts["guide"]
    tags |= set(problem.tags)
    tags |= set(guide.tags)
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
        if e.role:
            bits.append(f"role={e.role}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:8} ({e.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="moon_meadow",
        problem="dark_path",
        transform="star_wand",
        guide="firefly",
        name="Elin",
        gender="girl",
        trait="timid",
        parent_title="grandmother",
        seed=101,
    ),
    StoryParams(
        setting="rose_lane",
        problem="thorn_gate",
        transform="green_key",
        guide="owl",
        name="Bram",
        gender="boy",
        trait="brave",
        parent_title="aunt",
        seed=102,
    ),
    StoryParams(
        setting="willow_brook",
        problem="fallen_nest",
        transform="nest_cradle",
        guide="frog",
        name="Iris",
        gender="girl",
        trait="gentle",
        parent_title="mother",
        seed=103,
    ),
    StoryParams(
        setting="rose_lane",
        problem="thorn_gate",
        transform="green_key",
        guide="robin",
        name="Nico",
        gender="boy",
        trait="steady",
        parent_title="father",
        seed=104,
    ),
    StoryParams(
        setting="willow_brook",
        problem="fallen_nest",
        transform="nest_cradle",
        guide="owl",
        name="Mara",
        gender="girl",
        trait="hopeful",
        parent_title="grandmother",
        seed=105,
    ),
]


def explain_rejection(setting: Setting, problem: Problem, transform: Transformation, guide: Guide) -> str:
    if not problem_in_setting(setting, problem):
        return (
            f"(No story: {problem.title} does not belong in {setting.place}. "
            f"Pick a problem that the setting can honestly hold.)"
        )
    if not transformation_fits(problem, transform):
        return (
            f"(No story: a twig transformed into {transform.form} solves '{transform.power}', "
            f"but this problem needs '{problem.need}'. The transformation must fit the need.)"
        )
    if not guide_in_setting(setting, guide):
        return (
            f"(No story: {guide.label} is not a natural guide for {setting.place}. "
            f"Choose a guide that belongs in that place.)"
        )
    return "(No story: this combination is not reasonable in this world.)"


def outcome_of(params: StoryParams) -> str:
    return "helped" if needs_help(params.trait) else "self"


ASP_RULES = r"""
fits(P, T) :- problem(P), transform(T), needs(P, N), power(T, N).
valid(S, P, T, G) :- setting(S), problem(P), transform(T), guide(G),
                     affords(S, P), fits(P, T), guide_at(S, G).

strong_trait(Tr) :- trait(Tr), trait_kind(Tr, strong).
soft_trait(Tr)   :- trait(Tr), not strong_trait(Tr).

outcome(helped) :- chosen_trait(Tr), soft_trait(Tr).
outcome(self)   :- chosen_trait(Tr), strong_trait(Tr).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for problem in sorted(setting.affords):
            lines.append(asp.fact("affords", sid, problem))
        for guide in sorted(setting.guides):
            lines.append(asp.fact("guide_at", sid, guide))
    for pid, problem in PROBLEMS.items():
        lines.append(asp.fact("problem", pid))
        lines.append(asp.fact("needs", pid, problem.need))
    for tid, transform in TRANSFORMATIONS.items():
        lines.append(asp.fact("transform", tid))
        lines.append(asp.fact("power", tid, transform.power))
    for gid in GUIDES:
        lines.append(asp.fact("guide", gid))
    for trait in TRAITS:
        lines.append(asp.fact("trait", trait))
        kind = "strong" if trait in STRONG_TRAITS else "soft"
        lines.append(asp.fact("trait_kind", trait, kind))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    scenario = asp.fact("chosen_trait", params.trait)
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def asp_verify() -> int:
    rc = 0
    py_set = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py_set == asp_set:
        print(f"OK: gate matches valid_combos() ({len(py_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if py_set - asp_set:
            print("  only in python:", sorted(py_set - asp_set))
        if asp_set - py_set:
            print("  only in clingo:", sorted(asp_set - py_set))

    cases = list(CURATED)
    for s in range(80):
        try:
            p = resolve_params(build_parser().parse_args([]), random.Random(s))
        except StoryError:
            continue
        p.seed = s
        cases.append(p)
    bad = []
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            bad.append(params)
    if not bad:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {len(bad)}/{len(cases)} outcome differences.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("(Smoke test failed: generated empty story.)")
        print("OK: smoke generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Fairy-tale story world: a child, a twig, an inner voice, and a transformation."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--transform", choices=TRANSFORMATIONS)
    ap.add_argument("--guide", choices=GUIDES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("--parent-title", choices=PARENT_TITLES)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combinations from the ASP twin")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.problem and args.transform and args.guide:
        setting = SETTINGS[args.setting]
        problem = PROBLEMS[args.problem]
        transform = TRANSFORMATIONS[args.transform]
        guide = GUIDES[args.guide]
        if not (
            problem_in_setting(setting, problem)
            and transformation_fits(problem, transform)
            and guide_in_setting(setting, guide)
        ):
            raise StoryError(explain_rejection(setting, problem, transform, guide))

    combos = [
        combo for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.problem is None or combo[1] == args.problem)
        and (args.transform is None or combo[2] == args.transform)
        and (args.guide is None or combo[3] == args.guide)
    ]
    if not combos:
        if args.setting and args.problem and args.transform and args.guide:
            raise StoryError(
                explain_rejection(
                    SETTINGS[args.setting],
                    PROBLEMS[args.problem],
                    TRANSFORMATIONS[args.transform],
                    GUIDES[args.guide],
                )
            )
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, problem_id, transform_id, guide_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    parent_title = args.parent_title or rng.choice(PARENT_TITLES)
    return StoryParams(
        setting=setting_id,
        problem=problem_id,
        transform=transform_id,
        guide=guide_id,
        name=name,
        gender=gender,
        trait=trait,
        parent_title=parent_title,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting: {params.setting})")
    if params.problem not in PROBLEMS:
        raise StoryError(f"(Unknown problem: {params.problem})")
    if params.transform not in TRANSFORMATIONS:
        raise StoryError(f"(Unknown transform: {params.transform})")
    if params.guide not in GUIDES:
        raise StoryError(f"(Unknown guide: {params.guide})")
    if params.trait not in TRAITS:
        raise StoryError(f"(Unknown trait: {params.trait})")
    if params.gender not in {"girl", "boy"}:
        raise StoryError(f"(Unknown gender: {params.gender})")
    if params.parent_title not in PARENT_TITLES:
        raise StoryError(f"(Unknown parent title: {params.parent_title})")

    setting = SETTINGS[params.setting]
    problem = PROBLEMS[params.problem]
    transform = TRANSFORMATIONS[params.transform]
    guide = GUIDES[params.guide]
    if not (
        problem_in_setting(setting, problem)
        and transformation_fits(problem, transform)
        and guide_in_setting(setting, guide)
    ):
        raise StoryError(explain_rejection(setting, problem, transform, guide))

    world = tell(
        setting=setting,
        problem=problem,
        transform=transform,
        guide_cfg=guide,
        hero_name=params.name,
        hero_type=params.gender,
        trait=params.trait,
        parent_title=params.parent_title,
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
        print(asp_program("", "#show valid/4.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid (setting, problem, transform, guide) combos:\n")
        for setting, problem, transform, guide in combos:
            print(f"  {setting:12} {problem:12} {transform:12} {guide}")
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
            header = (
                f"### {p.name}: {p.problem} in {p.setting} "
                f"({p.transform}, {outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
