#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/grow_cocaine_garage_mystery_to_solve_problem.py
============================================================================

A standalone storyworld about a small garage mystery told in a fairy-tale style:
a child wants a little plant to grow, finds a frighteningly confusing clue, and
solves the real problem by looking carefully instead of guessing wildly.

The seed required the words "grow" and "cocaine", the setting "garage", and the
features "Mystery to Solve", "Problem Solving", and "Misunderstanding". In this
world, the misunderstanding comes from a torn scrap of old paper in the garage
with the word "cocaine" printed on it. The child briefly imagines it might be
the secret to making the plant grow, but a calm grown-up explains that it is a
bad grown-up word on old trash and has nothing to do with caring for plants.
The real answer comes from the simulated state of the plant: light, water,
roots, and drainage.

Run it
------
    python storyworlds/worlds/gpt-5.4/grow_cocaine_garage_mystery_to_solve_problem.py
    python storyworlds/worlds/gpt-5.4/grow_cocaine_garage_mystery_to_solve_problem.py --problem too_dark
    python storyworlds/worlds/gpt-5.4/grow_cocaine_garage_mystery_to_solve_problem.py --fix water_can
    python storyworlds/worlds/gpt-5.4/grow_cocaine_garage_mystery_to_solve_problem.py --all
    python storyworlds/worlds/gpt-5.4/grow_cocaine_garage_mystery_to_solve_problem.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/grow_cocaine_garage_mystery_to_solve_problem.py --verify
"""

from __future__ import annotations

import argparse
import copy
import io
import json
import os
import random
import sys
from collections import defaultdict
from contextlib import redirect_stdout
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
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
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)
    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Plant:
    id: str
    label: str
    phrase: str
    sprout: str
    promise: str
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


@dataclass
class Problem:
    id: str
    sign: str
    hidden_cause: str
    symptom: str
    remedy_hint: str
    needs: str
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
class Fix:
    id: str
    label: str
    action: str
    result: str
    solves: set[str] = field(default_factory=set)
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
class Misread:
    id: str
    scrap: str
    worry: str
    correction: str
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


def _r_problem_symptom(world: World) -> list[str]:
    plant = world.get("plant")
    problem = world.facts["problem_cfg"]
    sig = ("symptom", problem.id)
    if sig in world.fired:
        return []
    if plant.meters["problem"] < THRESHOLD:
        return []
    world.fired.add(sig)
    if problem.id == "too_dark":
        plant.meters["droop"] += 1
        plant.meters["pale"] += 1
    elif problem.id == "too_dry":
        plant.meters["droop"] += 1
        plant.meters["dry"] += 1
    elif problem.id == "cramped_root":
        plant.meters["crowded"] += 1
        plant.meters["stuck"] += 1
    elif problem.id == "blocked_drain":
        plant.meters["soggy"] += 1
        plant.meters["yellow"] += 1
    plant.memes["need_help"] += 1
    return []


def _r_fixed_recovery(world: World) -> list[str]:
    plant = world.get("plant")
    sig = ("recovery",)
    if sig in world.fired:
        return []
    if plant.meters["fixed"] < THRESHOLD:
        return []
    world.fired.add(sig)
    plant.meters["droop"] = 0.0
    plant.meters["dry"] = 0.0
    plant.meters["soggy"] = 0.0
    plant.meters["crowded"] = 0.0
    plant.meters["yellow"] = 0.0
    plant.meters["pale"] = 0.0
    plant.meters["stuck"] = 0.0
    plant.meters["growth"] += 1
    plant.meters["perk"] += 1
    plant.memes["hope"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="problem_symptom", tag="physical", apply=_r_problem_symptom),
    Rule(name="fixed_recovery", tag="physical", apply=_r_fixed_recovery),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            res = rule.apply(world)
            if res:
                changed = True
                produced.extend(res)
            elif world.fired:
                pass
            if res:
                changed = True
    if narrate:
        for sent in produced:
            world.say(sent)
    return produced


def compatible(problem: Problem, fix: Fix) -> bool:
    return problem.id in fix.solves


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for plant_id in PLANTS:
        for problem_id, problem in PROBLEMS.items():
            for fix_id, fix in FIXES.items():
                if compatible(problem, fix):
                    combos.append((plant_id, problem_id, fix_id))
    return combos


def explain_rejection(problem: Problem, fix: Fix) -> str:
    return (
        f"(No story: {fix.label} does not solve the real problem here. "
        f"The plant shows that {problem.hidden_cause}, so the fix must address "
        f"{problem.needs} rather than something else.)"
    )


def predict_recovery(world: World, fix_id: str) -> dict:
    sim = world.copy()
    fix = FIXES[fix_id]
    plant = sim.get("plant")
    if compatible(sim.facts["problem_cfg"], fix):
        plant.meters["fixed"] += 1
        propagate(sim, narrate=False)
    return {
        "grows": plant.meters["growth"] >= THRESHOLD,
        "perk": plant.meters["perk"],
    }


def introduce(world: World, hero: Entity, plant_cfg: Plant) -> None:
    hero.memes["care"] += 1
    world.say(
        f"In the hush of the garage, where old shelves stood like sleepy towers, "
        f"{hero.id} kept {plant_cfg.phrase} on a wooden crate. "
        f"{hero.pronoun().capitalize()} wanted it to grow into {plant_cfg.promise}."
    )


def set_problem(world: World, problem: Problem) -> None:
    plant = world.get("plant")
    plant.meters["problem"] += 1
    propagate(world, narrate=False)
    world.say(
        f"But one morning the little plant looked wrong. {problem.sign} "
        f"It was a tiny mystery hiding among the rakes and boxes."
    )


def discover_scrap(world: World, hero: Entity, helper: Entity, misread: Misread) -> None:
    hero.memes["worry"] += 1
    helper.memes["wonder"] += 1
    world.say(
        f"On the floor beside the pot lay {misread.scrap}. "
        f'"Look," whispered {helper.id}, "there is a strange word here: '
        f'cocaine."'
    )
    world.say(
        f"{hero.id} blinked at the scrap and wondered if the odd word had "
        f"something to do with making things grow."
    )


def misinterpret(world: World, hero: Entity, parent: Entity, misread: Misread) -> None:
    world.say(
        f'"Maybe that is the secret?" {hero.id} asked. {misread.worry}'
    )
    world.say(
        f"{parent.label_word.capitalize()} came near at once and gently shook "
        f"{parent.pronoun('possessive')} head. "
        f'"No, that word is not a plant helper," {parent.pronoun()} said. '
        f'"It is a bad grown-up word on an old bit of trash, and children should '
        f'never use mystery powders or mystery papers as clues for caring for plants."'
    )


def inspect(world: World, hero: Entity, helper: Entity, problem: Problem) -> None:
    hero.memes["focus"] += 1
    helper.memes["focus"] += 1
    world.say(
        f"So instead of trusting the scrap, {hero.id}, {helper.id}, and the grown-up "
        f"looked at the plant itself. They noticed that {problem.symptom}."
    )
    world.say(
        f"That made the answer feel less spooky and more sensible: {problem.remedy_hint}."
    )


def solve(world: World, hero: Entity, helper: Entity, fix: Fix) -> None:
    plant = world.get("plant")
    hero.memes["pride"] += 1
    helper.memes["pride"] += 1
    plant.meters["fixed"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Together they {fix.action}. "
        f"The work was small and careful, like helping a sleepy fairy tie her shoe."
    )
    world.say(fix.result)


def ending(world: World, hero: Entity, helper: Entity, plant_cfg: Plant) -> None:
    hero.memes["relief"] += 1
    helper.memes["relief"] += 1
    world.say(
        f"By evening, the garage no longer felt full of riddles. "
        f"The little {plant_cfg.label} stood straighter, and a brave new green tip "
        f"seemed ready to grow."
    )
    world.say(
        f'{hero.id} smiled at {helper.id}. "The true answer was not in a scary word," '
        f"{hero.pronoun()} said. \"It was in looking closely and helping kindly.\""
    )


def tell(
    plant_cfg: Plant,
    problem_cfg: Problem,
    fix_cfg: Fix,
    misread_cfg: Misread,
    hero_name: str = "Nora",
    hero_gender: str = "girl",
    helper_name: str = "Finn",
    helper_gender: str = "boy",
    parent_type: str = "mother",
) -> World:
    world = World()
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender, role="hero"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender, role="helper"))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, role="parent", label="the parent"))
    plant = world.add(Entity(id="plant", kind="thing", type="plant", label=plant_cfg.label, phrase=plant_cfg.phrase))
    garage = world.add(Entity(id="garage", kind="thing", type="place", label="garage"))

    world.facts.update(
        plant_cfg=plant_cfg,
        problem_cfg=problem_cfg,
        fix_cfg=fix_cfg,
        misread_cfg=misread_cfg,
        hero=hero,
        helper=helper,
        parent=parent,
        plant=plant,
        place=garage,
        solved=False,
    )

    introduce(world, hero, plant_cfg)
    set_problem(world, problem_cfg)

    world.para()
    discover_scrap(world, hero, helper, misread_cfg)
    misinterpret(world, hero, parent, misread_cfg)

    world.para()
    inspect(world, hero, helper, problem_cfg)
    solve(world, hero, helper, fix_cfg)
    ending(world, hero, helper, plant_cfg)

    world.facts["solved"] = plant.meters["growth"] >= THRESHOLD
    return world


PLANTS = {
    "bean": Plant(
        id="bean",
        label="bean plant",
        phrase="a bean plant in a blue pot",
        sprout="green hook",
        promise="a ladder of leaves",
        tags={"plant", "bean"},
    ),
    "sunflower": Plant(
        id="sunflower",
        label="sunflower seedling",
        phrase="a sunflower seedling in a red pot",
        sprout="tiny golden-faced stalk",
        promise="a tall bright wheel of petals",
        tags={"plant", "sunflower"},
    ),
    "pea": Plant(
        id="pea",
        label="pea vine",
        phrase="a pea vine in a striped pot",
        sprout="curling green thread",
        promise="soft curling vines and sweet pods",
        tags={"plant", "pea"},
    ),
}

PROBLEMS = {
    "too_dark": Problem(
        id="too_dark",
        sign="Its leaves looked pale, and the stem leaned toward the crack of light under the garage door.",
        hidden_cause="it has been kept too dark",
        symptom="the stem was stretching toward light and the leaves were pale",
        remedy_hint="the plant needed light, not magic",
        needs="more light",
        tags={"light", "garage"},
    ),
    "too_dry": Problem(
        id="too_dry",
        sign="The soil had pulled away from the edge of the pot, and the leaves drooped like sleepy ribbons.",
        hidden_cause="the soil has grown too dry",
        symptom="the soil was dry and the leaves drooped from thirst",
        remedy_hint="the plant needed a drink, not a mystery charm",
        needs="water",
        tags={"water", "garage"},
    ),
    "cramped_root": Problem(
        id="cramped_root",
        sign="A white root curled from the drain hole, and the plant looked stuck though it tried its best.",
        hidden_cause="its roots are cramped in a pot that is too small",
        symptom="roots were pushing out of the bottom and had no room left",
        remedy_hint="the plant needed a bigger home for its roots",
        needs="a bigger pot",
        tags={"roots", "pot"},
    ),
    "blocked_drain": Problem(
        id="blocked_drain",
        sign="The soil shone wet and heavy, and a little stale puddle sat in the saucer below.",
        hidden_cause="water cannot drain through the pot",
        symptom="the soil stayed soggy and water sat trapped underneath",
        remedy_hint="the plant needed the pot's drain hole cleared",
        needs="better drainage",
        tags={"water", "drain"},
    ),
}

FIXES = {
    "sunny_step": Fix(
        id="sunny_step",
        label="moving the pot to the sunny step",
        action="carried the pot from the dim garage shelf to the sunny step by the open side door",
        result="Soon the leaves seemed to face the brighter world, as if they had remembered where morning lived.",
        solves={"too_dark"},
        tags={"light", "sun"},
    ),
    "water_can": Fix(
        id="water_can",
        label="watering the plant gently",
        action="used a little tin watering can and gave the dry soil a slow, gentle drink",
        result="The soil darkened softly, and after a while the drooping leaves looked less tired.",
        solves={"too_dry"},
        tags={"water"},
    ),
    "bigger_pot": Fix(
        id="bigger_pot",
        label="repotting into a bigger pot",
        action="tipped the plant out with great care and settled it into a bigger clay pot with fresh soil",
        result="Its stem stopped looking trapped, and the roots finally had room to stretch like waking toes.",
        solves={"cramped_root"},
        tags={"roots", "pot"},
    ),
    "clear_hole": Fix(
        id="clear_hole",
        label="clearing the drain hole",
        action="lifted the pot, cleared the little drain hole with a twig, and poured away the stale water from the saucer",
        result="The heavy wetness eased, and the plant no longer had to sit with soggy roots.",
        solves={"blocked_drain"},
        tags={"drain", "water"},
    ),
}

MISREADS = {
    "paper": Misread(
        id="paper",
        scrap="a torn old paper scrap with dusty black letters",
        worry="The garage felt colder for a moment, as if a wicked riddle had spoken.",
        correction="It was only an old scrap with a harmful grown-up word.",
        tags={"mystery", "trash", "safety"},
    ),
}

GIRL_NAMES = ["Nora", "Lily", "Mira", "Ava", "Elsie", "June", "Wren", "Maya"]
BOY_NAMES = ["Finn", "Theo", "Ben", "Owen", "Milo", "Leo", "Jack", "Eli"]
TRAITS = ["careful", "curious", "patient", "bright", "gentle"]


@dataclass
class StoryParams:
    plant: str
    problem: str
    fix: str
    misread: str = "paper"
    hero_name: str = "Nora"
    hero_gender: str = "girl"
    helper_name: str = "Finn"
    helper_gender: str = "boy"
    parent: str = "mother"
    trait: str = "curious"
    seed: Optional[int] = None
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


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    plant_cfg = f["plant_cfg"]
    problem_cfg = f["problem_cfg"]
    fix_cfg = f["fix_cfg"]
    return [
        (
            f'Write a fairy-tale style story for a 3-to-5-year-old set in a garage, '
            f'where a child wants a {plant_cfg.label} to grow, finds the strange word '
            f'"cocaine" on old trash, and solves the real mystery by careful observation.'
        ),
        (
            f"Tell a gentle mystery story where {hero.id} first misunderstands a scary clue, "
            f"then notices that {problem_cfg.symptom}, and fixes the problem by {fix_cfg.label}."
        ),
        (
            "Write a child-facing story about misunderstanding and problem solving in which "
            'the word "cocaine" appears only as a confusing old warning word, never as a tool, '
            "and the ending proves that looking closely works better than guessing."
        ),
    ]


KNOWLEDGE = {
    "plant": [
        (
            "What helps a plant grow?",
            "Plants need the right things, like light, water, air, and room for roots. When one of those is missing, the plant can look weak or droopy."
        )
    ],
    "light": [
        (
            "Why do plants need light?",
            "Plants use light to make food for themselves. Without enough light, they can turn pale and stretch toward brighter places."
        )
    ],
    "water": [
        (
            "Why do plants need water?",
            "Water helps a plant move food through its stem and leaves. If the soil gets too dry, the plant can droop and look tired."
        )
    ],
    "roots": [
        (
            "Why do roots need room?",
            "Roots spread through soil to drink water and hold the plant steady. If they are packed too tightly, the plant can stop growing well."
        )
    ],
    "drain": [
        (
            "Why does a flowerpot need a drain hole?",
            "A drain hole lets extra water escape. If water stays trapped, roots can sit in soggy soil and the plant may get sick."
        )
    ],
    "safety": [
        (
            "What should children do with mystery powders or mystery labels?",
            "They should leave them alone and tell a grown-up. Unknown things are not for touching, tasting, or trying."
        )
    ],
    "mystery": [
        (
            "How do you solve a mystery carefully?",
            "You look for real clues and ask calm questions. Good problem solving comes from noticing what is truly there, not from guessing at scary ideas."
        )
    ],
}


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    parent = f["parent"]
    plant_cfg = f["plant_cfg"]
    problem_cfg = f["problem_cfg"]
    fix_cfg = f["fix_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, {helper.id}, and {hero.id}'s {parent.label_word}, who were caring for {plant_cfg.phrase} in the garage. They all helped solve the mystery together."
        ),
        (
            f"What was the mystery in the garage?",
            f"The mystery was why the little {plant_cfg.label} did not look healthy and would not seem to grow. The clue that mattered was the plant's own condition, because {problem_cfg.symptom}."
        ),
        (
            'Why did the word "cocaine" appear in the story?',
            'It appeared on an old scrap of trash in the garage, and the children briefly misunderstood it as an important clue. The grown-up explained that it was only a harmful grown-up word on old paper and had nothing to do with helping a plant grow.'
        ),
        (
            "How did they solve the problem?",
            f"They looked closely at the real signs on the plant instead of trusting the scary scrap, and then they solved the problem by {fix_cfg.label}. That worked because {problem_cfg.hidden_cause}, so the fix matched what the plant truly needed."
        ),
        (
            "How did the story end?",
            f"The plant looked better, and the garage stopped feeling spooky and confusing. The ending shows change because the plant stood straighter and seemed ready to grow after they helped it the right way."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"plant", "mystery", "safety"} | set(f["problem_cfg"].tags) | set(f["fix_cfg"].tags)
    out: list[tuple[str, str]] = []
    for key in ["plant", "light", "water", "roots", "drain", "safety", "mystery"]:
        if key in tags:
            out.extend(KNOWLEDGE[key])
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
        parts = []
        if e.role:
            parts.append(f"role={e.role}")
        if meters:
            parts.append(f"meters={dict(meters)}")
        if memes:
            parts.append(f"memes={dict(memes)}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                parts.append(f"attrs={shown}")
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(parts)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        plant="bean",
        problem="too_dark",
        fix="sunny_step",
        misread="paper",
        hero_name="Nora",
        hero_gender="girl",
        helper_name="Finn",
        helper_gender="boy",
        parent="mother",
        trait="curious",
    ),
    StoryParams(
        plant="sunflower",
        problem="too_dry",
        fix="water_can",
        misread="paper",
        hero_name="Milo",
        hero_gender="boy",
        helper_name="June",
        helper_gender="girl",
        parent="father",
        trait="patient",
    ),
    StoryParams(
        plant="pea",
        problem="cramped_root",
        fix="bigger_pot",
        misread="paper",
        hero_name="Wren",
        hero_gender="girl",
        helper_name="Theo",
        helper_gender="boy",
        parent="mother",
        trait="careful",
    ),
    StoryParams(
        plant="bean",
        problem="blocked_drain",
        fix="clear_hole",
        misread="paper",
        hero_name="Eli",
        hero_gender="boy",
        helper_name="Maya",
        helper_gender="girl",
        parent="father",
        trait="bright",
    ),
]


def outcome_of(params: StoryParams) -> str:
    problem = PROBLEMS[params.problem]
    fix = FIXES[params.fix]
    return "solved" if compatible(problem, fix) else "stuck"


ASP_RULES = r"""
compatible(P, F) :- problem(P), fix(F), solves(F, P).
valid(Pl, P, F) :- plant(Pl), compatible(P, F).
outcome(solved) :- chosen_problem(P), chosen_fix(F), compatible(P, F).
outcome(stuck)  :- chosen_problem(P), chosen_fix(F), not compatible(P, F).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for plant_id in PLANTS:
        lines.append(asp.fact("plant", plant_id))
    for problem_id in PROBLEMS:
        lines.append(asp.fact("problem", problem_id))
    for fix_id, fix in FIXES.items():
        lines.append(asp.fact("fix", fix_id))
        for problem_id in sorted(fix.solves):
            lines.append(asp.fact("solves", fix_id, problem_id))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_problem", params.problem),
            asp.fact("chosen_fix", params.fix),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def asp_verify() -> int:
    rc = 0
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: valid_combos matches ASP ({len(python_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))

    cases = list(CURATED)
    for seed in range(50):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        params.seed = seed
        cases.append(params)
    mismatches = [p for p in cases if asp_outcome(p) != outcome_of(p)]
    if not mismatches:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {len(mismatches)} outcome differences.")

    try:
        smoke = generate(CURATED[0])
        with redirect_stdout(io.StringIO()):
            emit(smoke, trace=False, qa=True, header="### smoke")
        if not smoke.story.strip():
            raise StoryError("smoke test generated an empty story")
        print("OK: smoke generation and emit succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Fairy-tale garage mystery storyworld about helping a plant grow."
    )
    ap.add_argument("--plant", choices=PLANTS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the ASP facts and rules")
    return ap


def _pick_name(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.problem and args.fix:
        problem = PROBLEMS[args.problem]
        fix = FIXES[args.fix]
        if not compatible(problem, fix):
            raise StoryError(explain_rejection(problem, fix))

    combos = [
        combo
        for combo in valid_combos()
        if (args.plant is None or combo[0] == args.plant)
        and (args.problem is None or combo[1] == args.problem)
        and (args.fix is None or combo[2] == args.fix)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    plant_id, problem_id, fix_id = rng.choice(sorted(combos))
    hero_name, hero_gender = _pick_name(rng)
    helper_name, helper_gender = _pick_name(rng, avoid=hero_name)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(
        plant=plant_id,
        problem=problem_id,
        fix=fix_id,
        misread="paper",
        hero_name=hero_name,
        hero_gender=hero_gender,
        helper_name=helper_name,
        helper_gender=helper_gender,
        parent=parent,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.plant not in PLANTS:
        raise StoryError(f"(Unknown plant '{params.plant}'.)")
    if params.problem not in PROBLEMS:
        raise StoryError(f"(Unknown problem '{params.problem}'.)")
    if params.fix not in FIXES:
        raise StoryError(f"(Unknown fix '{params.fix}'.)")
    if params.misread not in MISREADS:
        raise StoryError(f"(Unknown misunderstanding '{params.misread}'.)")
    if params.parent not in {"mother", "father"}:
        raise StoryError(f"(Unknown parent type '{params.parent}'.)")

    problem = PROBLEMS[params.problem]
    fix = FIXES[params.fix]
    if not compatible(problem, fix):
        raise StoryError(explain_rejection(problem, fix))

    world = tell(
        plant_cfg=PLANTS[params.plant],
        problem_cfg=problem,
        fix_cfg=fix,
        misread_cfg=MISREADS[params.misread],
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        helper_name=params.helper_name,
        helper_gender=params.helper_gender,
        parent_type=params.parent,
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
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (plant, problem, fix) combos:\n")
        for plant_id, problem_id, fix_id in combos:
            print(f"  {plant_id:10} {problem_id:14} {fix_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero_name}: {p.problem} -> {p.fix} ({p.plant})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
