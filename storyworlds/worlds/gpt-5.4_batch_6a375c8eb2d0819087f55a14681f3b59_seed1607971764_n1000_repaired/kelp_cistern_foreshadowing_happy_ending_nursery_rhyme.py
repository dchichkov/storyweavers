#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/kelp_cistern_foreshadowing_happy_ending_nursery_rhyme.py
====================================================================================

A standalone story world for a seaside nursery-rhyme tale about a child, a
cistern, and a strip of kelp that turns out to be useful. The stories are small
and classical: a gentle clue appears first, trouble nearly follows, a helper
uses the clue wisely, and the ending image proves the home is safe and watered.

Seeded premise
--------------
Little children in a salt-bright cottage hear a tiny warning sound from the
cistern before a windy or dry day. The first clue is easy to ignore: a lid that
rattles, a spout that drips, a thirsty patch waiting for water. Then the risk
becomes clearer. With help, the child uses kelp as a sensible tying or padding
material, and the cistern keeps its water. The garden drinks, the house rests,
and the ending lands happily in a sing-song cadence.

Run it
------
    python storyworlds/worlds/gpt-5.4/kelp_cistern_foreshadowing_happy_ending_nursery_rhyme.py
    python storyworlds/worlds/gpt-5.4/kelp_cistern_foreshadowing_happy_ending_nursery_rhyme.py --problem loose_lid --weather windy
    python storyworlds/worlds/gpt-5.4/kelp_cistern_foreshadowing_happy_ending_nursery_rhyme.py --problem seam_leak --fix kelp_tie
    python storyworlds/worlds/gpt-5.4/kelp_cistern_foreshadowing_happy_ending_nursery_rhyme.py --all
    python storyworlds/worlds/gpt-5.4/kelp_cistern_foreshadowing_happy_ending_nursery_rhyme.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/kelp_cistern_foreshadowing_happy_ending_nursery_rhyme.py --verify
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
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
            "grandmother": "grandma",
            "grandfather": "grandpa",
            "mother": "mom",
            "father": "dad",
        }.get(self.type, self.type)
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Weather:
    id: str
    sky: str
    warning_line: str
    risk: str
    danger: str
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
    clue_sound: str
    clue_text: str
    risk_text: str
    damaged_part: str
    need: str
    loss_name: str
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
    works_for: set[str]
    text: str
    qa_text: str
    kelp_role: str
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
class Patch:
    id: str
    label: str
    needs_water: bool
    bloom: str
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


def _r_risk_grows(world: World) -> list[str]:
    cistern = world.get("cistern")
    weather = world.facts["weather_cfg"]
    problem = world.facts["problem_cfg"]
    if cistern.meters["weakness"] < THRESHOLD:
        return []
    sig = ("risk_grows", weather.id, problem.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    cistern.meters["risk"] += 1
    child = world.get("child")
    helper = world.get("helper")
    child.memes["worry"] += 1
    helper.memes["attention"] += 1
    return ["__risk__"]


def _r_water_loss(world: World) -> list[str]:
    cistern = world.get("cistern")
    patch = world.get("patch")
    if cistern.meters["open_or_leaking"] < THRESHOLD:
        return []
    sig = ("water_loss",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    cistern.meters["water"] -= 1
    cistern.meters["loss"] += 1
    patch.meters["thirst"] += 1
    world.get("child").memes["worry"] += 1
    return ["__loss__"]


def _r_patch_drinks(world: World) -> list[str]:
    cistern = world.get("cistern")
    patch = world.get("patch")
    if cistern.meters["safe"] < THRESHOLD or cistern.meters["water"] < THRESHOLD:
        return []
    sig = ("patch_drinks",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    if patch.attrs.get("needs_water", False):
        patch.meters["watered"] += 1
        patch.meters["thirst"] = 0.0
        patch.meters["bloomed"] += 1
    child = world.get("child")
    helper = world.get("helper")
    child.memes["joy"] += 1
    helper.memes["joy"] += 1
    return ["__bloom__"]


CAUSAL_RULES = [
    Rule(name="risk_grows", tag="physical", apply=_r_risk_grows),
    Rule(name="water_loss", tag="physical", apply=_r_water_loss),
    Rule(name="patch_drinks", tag="physical", apply=_r_patch_drinks),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            out = rule.apply(world)
            if out:
                changed = True
                produced.extend(s for s in out if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def fix_works(problem: Problem, fix: Fix) -> bool:
    return problem.id in fix.works_for


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for weather_id in WEATHERS:
        for problem_id, problem in PROBLEMS.items():
            for fix_id, fix in FIXES.items():
                if fix_works(problem, fix):
                    combos.append((weather_id, problem_id, fix_id))
    return combos


def predict_trouble(world: World) -> dict:
    sim = world.copy()
    cistern = sim.get("cistern")
    cistern.meters["open_or_leaking"] += 1
    propagate(sim, narrate=False)
    return {
        "water_left": cistern.meters["water"],
        "loss": cistern.meters["loss"],
        "thirst": sim.get("patch").meters["thirst"],
    }


def opening(world: World, child: Entity, helper: Entity, weather: Weather, patch: Patch) -> None:
    child.memes["joy"] += 1
    world.say(
        f"In a salt-bright cottage by the shore lived {child.id} and {child.pronoun('possessive')} "
        f"{helper.label_word}, with {patch.label} by the step and a round cistern by the wall."
    )
    world.say(
        f"{weather.sky} {weather.warning_line} {child.id} skipped by with a little pail and sang, "
        f'"Plink, plank, plunk by the wall, tell me if the raindrops fall."'
    )


def clue(world: World, child: Entity, problem: Problem) -> None:
    cistern = world.get("cistern")
    cistern.meters["weakness"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then came {problem.clue_sound}: {problem.clue_text}. "
        f"{child.id} stopped and whispered, \"That sounds small now, but small things can grow.\""
    )


def foreshadow(world: World, helper: Entity, weather: Weather, problem: Problem, patch: Patch) -> None:
    pred = predict_trouble(world)
    world.facts["predicted_loss"] = pred["loss"]
    world.facts["predicted_thirst"] = pred["thirst"]
    world.say(
        f'{helper.label_word.capitalize()} listened too and said, "{weather.risk} '
        f'If we leave it so, {problem.risk_text}, and {patch.label} may stand with thirsty roots."'
    )


def fetch_kelp(world: World, child: Entity) -> None:
    child.memes["purpose"] += 1
    kelp = world.get("kelp")
    kelp.meters["ready"] += 1
    world.say(
        f"So {child.id} ran to the beach path, where a clean ribbon of kelp lay drying on a stone. "
        f"{child.pronoun().capitalize()} lifted the kelp with two careful hands and brought it home."
    )


def attempt_fix(world: World, child: Entity, helper: Entity, problem: Problem, fix: Fix) -> None:
    cistern = world.get("cistern")
    kelp = world.get("kelp")
    child.memes["hope"] += 1
    helper.memes["care"] += 1
    kelp.meters["used"] += 1
    cistern.meters["open_or_leaking"] = 0.0
    cistern.meters["safe"] += 1
    world.say(
        f"{helper.label_word.capitalize()} and {child.id} worked side by side. "
        f"{helper.pronoun().capitalize()} {fix.text}."
    )
    world.say(
        f"The kelp was {fix.kelp_role}, and the cistern gave one last soft sound, then settled into stillness."
    )


def reward(world: World, child: Entity, helper: Entity, patch: Patch) -> None:
    cistern = world.get("cistern")
    cistern.meters["water"] += 1
    propagate(world, narrate=False)
    child.memes["relief"] += 1
    helper.memes["relief"] += 1
    world.say(
        f"Soon the stored rain stayed where it belonged. They tipped a little water to {patch.label}, "
        f"and {patch.bloom}."
    )
    world.say(
        f'Then {child.id} clapped and sang, "Kelp for a ribbon, cistern for rain, '
        f'now our small garden laughs again."'
    )
    world.say(
        f"That evening the shore wind hummed, the cistern rested snug and sound, and the cottage slept content."
    )


def tell(
    weather: Weather,
    problem: Problem,
    fix: Fix,
    patch_cfg: Patch,
    child_name: str = "Mina",
    child_gender: str = "girl",
    helper_type: str = "grandmother",
) -> World:
    world = World()
    child = world.add(Entity(id="child", kind="character", type=child_gender, label=child_name, role="child"))
    helper = world.add(
        Entity(id="helper", kind="character", type=helper_type, label=helper_type, role="helper")
    )
    cistern = world.add(Entity(id="cistern", kind="thing", type="cistern", label="cistern"))
    kelp = world.add(Entity(id="kelp", kind="thing", type="kelp", label="kelp"))
    patch = world.add(
        Entity(
            id="patch",
            kind="thing",
            type="patch",
            label=patch_cfg.label,
            attrs={"needs_water": patch_cfg.needs_water},
        )
    )

    cistern.meters["water"] = 2.0
    cistern.meters["weakness"] = 0.0
    cistern.meters["open_or_leaking"] = 0.0
    cistern.meters["safe"] = 0.0
    cistern.meters["loss"] = 0.0
    cistern.meters["risk"] = 0.0
    patch.meters["thirst"] = 0.0
    patch.meters["watered"] = 0.0
    patch.meters["bloomed"] = 0.0
    kelp.meters["ready"] = 0.0
    kelp.meters["used"] = 0.0
    child.memes["joy"] = 0.0
    child.memes["worry"] = 0.0
    child.memes["purpose"] = 0.0
    child.memes["hope"] = 0.0
    child.memes["relief"] = 0.0
    helper.memes["attention"] = 0.0
    helper.memes["care"] = 0.0
    helper.memes["joy"] = 0.0
    helper.memes["relief"] = 0.0

    world.facts.update(
        weather_cfg=weather,
        problem_cfg=problem,
        fix_cfg=fix,
        patch_cfg=patch_cfg,
        child_name=child_name,
    )

    opening(world, child, helper, weather, patch_cfg)
    clue(world, child, problem)

    world.para()
    foreshadow(world, helper, weather, problem, patch_cfg)
    fetch_kelp(world, child)

    world.para()
    attempt_fix(world, child, helper, problem, fix)
    reward(world, child, helper, patch_cfg)

    world.facts.update(
        child=child,
        helper=helper,
        cistern=cistern,
        kelp=kelp,
        patch=patch,
        weather=weather,
        problem=problem,
        fix=fix,
        outcome="happy" if cistern.meters["safe"] >= THRESHOLD and patch.meters["bloomed"] >= THRESHOLD else "oops",
    )
    return world


WEATHERS = {
    "windy": Weather(
        id="windy",
        sky="The clouds went scudding and the gulls flew low.",
        warning_line="A brisk wind whistled from the sea.",
        risk="The wind will worry a loose thing all day.",
        danger="wind may lift or shake the weak part",
        tags={"wind", "weather"},
    ),
    "dry": Weather(
        id="dry",
        sky="The sun shone pale and the air held no promise of quick rain.",
        warning_line="A dry breeze brushed the rosemary hedge.",
        risk="A dry day asks a cistern to hold every drop.",
        danger="every saved drop will matter",
        tags={"dry", "weather"},
    ),
    "misty": Weather(
        id="misty",
        sky="A pearl-gray mist curled over the shore.",
        warning_line="The air was soft, but the day felt watchful.",
        risk="Even a gentle day can turn a tiny trouble into a larger one.",
        danger="small trouble may spread if left alone",
        tags={"mist", "weather"},
    ),
}

PROBLEMS = {
    "loose_lid": Problem(
        id="loose_lid",
        clue_sound="a tip-tap rattle",
        clue_text="the cistern lid hopped a little whenever the wind touched it",
        risk_text="the lid may flap open and let precious water slosh or spoil",
        damaged_part="lid",
        need="to be tied snug",
        loss_name="slosh",
        tags={"lid", "water"},
    ),
    "seam_leak": Problem(
        id="seam_leak",
        clue_sound="a plink-plink drip",
        clue_text="a silver bead of water slipped from the cistern seam and ran down the side",
        risk_text="the little leak may keep dripping until the stored rain is wasted",
        damaged_part="seam",
        need="to be padded and bound",
        loss_name="drip",
        tags={"seam", "water"},
    ),
}

FIXES = {
    "kelp_tie": Fix(
        id="kelp_tie",
        works_for={"loose_lid"},
        text="braided the kelp into a green cord and tied the lid down snug over the latch",
        qa_text="They braided the kelp into a cord and tied the cistern lid down snug.",
        kelp_role="strong and springy, better than a loose string",
        tags={"kelp", "tie"},
    ),
    "kelp_wrap": Fix(
        id="kelp_wrap",
        works_for={"seam_leak"},
        text="folded the kelp soft and flat, pressed it over the seam, and bound it with twine until the drip stopped",
        qa_text="They folded the kelp over the leaking seam and bound it in place until the drip stopped.",
        kelp_role="soft enough to pad the crack and tough enough to stay put",
        tags={"kelp", "patch"},
    ),
}

PATCHES = {
    "beans": Patch(
        id="beans",
        label="the bean patch",
        needs_water=True,
        bloom="the bean leaves lifted their green faces",
        tags={"beans", "garden"},
    ),
    "mint": Patch(
        id="mint",
        label="the mint bed",
        needs_water=True,
        bloom="the mint stood bright and sweet again",
        tags={"mint", "garden"},
    ),
    "nasturtiums": Patch(
        id="nasturtiums",
        label="the nasturtium bed",
        needs_water=True,
        bloom="the nasturtiums opened like little cups of fire",
        tags={"flowers", "garden"},
    ),
}

GIRL_NAMES = ["Mina", "Tilly", "Nora", "May", "Elsie", "Wren"]
BOY_NAMES = ["Finn", "Toby", "Ned", "Kit", "Rowan", "Pip"]


@dataclass
class StoryParams:
    weather: str
    problem: str
    fix: str
    patch: str
    child_name: str
    child_gender: str
    helper_type: str
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


KNOWLEDGE = {
    "kelp": [
        (
            "What is kelp?",
            "Kelp is a kind of big brown seaweed that grows in the ocean. When it washes ashore, it can feel long, strong, and a little rubbery.",
        )
    ],
    "cistern": [
        (
            "What is a cistern?",
            "A cistern is a container that stores water for later. People can use that saved water for gardens and chores.",
        )
    ],
    "rainwater": [
        (
            "Why is saved rainwater useful?",
            "Saved rainwater helps when the day is dry and plants need a drink. Keeping it in a cistern means the water is ready when you need it.",
        )
    ],
    "foreshadow": [
        (
            "What does a little warning clue do in a story?",
            "A small clue hints that something important may happen later. It helps the middle of the story feel earned instead of sudden.",
        )
    ],
    "garden": [
        (
            "Why do garden plants need water?",
            "Plants need water to stay firm and growing. Without enough water, their leaves droop and their roots get thirsty.",
        )
    ],
}
KNOWLEDGE_ORDER = ["kelp", "cistern", "rainwater", "foreshadow", "garden"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    weather = f["weather"]
    problem = f["problem"]
    patch = f["patch_cfg"]
    return [
        'Write a short nursery-rhyme style story for a 3-to-5-year-old that includes the words "kelp" and "cistern".',
        f"Tell a sing-song seaside story where {f['child_name']} hears {problem.clue_sound} from a cistern before a {weather.id} day and helps save water for {patch.label}.",
        "Write a gentle foreshadowing story with a happy ending, where a tiny warning sound matters later and the fix feels clever and kind.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    problem = f["problem"]
    fix = f["fix"]
    patch = f["patch_cfg"]
    weather = f["weather"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {f['child_name']} and {helper.label_word}, who live by the shore with a cistern and {patch.label}. They notice a small problem before it can grow bigger.",
        ),
        (
            "What was the first clue that something might go wrong?",
            f"The first clue was {problem.clue_sound}, because {problem.clue_text}. That little sound foreshadowed that the cistern might lose water later.",
        ),
        (
            f"Why did {helper.label_word} take the clue seriously?",
            f"{helper.label_word.capitalize()} knew that {weather.risk.lower()} {problem.risk_text}. The warning mattered because the garden would need the stored water.",
        ),
        (
            "How did kelp help fix the cistern?",
            f"{fix.qa_text} The kelp was useful because it was {fix.kelp_role}.",
        ),
        (
            "How did the story end?",
            f"It ended happily: the cistern stayed safe, the water was saved, and {patch.bloom}. The final song shows that the family learned to listen when a small warning speaks.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"kelp", "cistern", "rainwater", "foreshadow", "garden"}
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
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:8} ({ent.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        weather="windy",
        problem="loose_lid",
        fix="kelp_tie",
        patch="beans",
        child_name="Mina",
        child_gender="girl",
        helper_type="grandmother",
    ),
    StoryParams(
        weather="dry",
        problem="seam_leak",
        fix="kelp_wrap",
        patch="mint",
        child_name="Finn",
        child_gender="boy",
        helper_type="grandfather",
    ),
    StoryParams(
        weather="misty",
        problem="loose_lid",
        fix="kelp_tie",
        patch="nasturtiums",
        child_name="Tilly",
        child_gender="girl",
        helper_type="mother",
    ),
]


def explain_rejection(problem: Problem, fix: Fix) -> str:
    return (
        f"(No story: {fix.id} is not a sensible repair for {problem.id}. "
        f"The fix must actually address the cistern's trouble, so choose a matching repair.)"
    )


ASP_RULES = r"""
works(P,F) :- problem(P), fix(F), supports(F,P).
valid(W,P,F) :- weather(W), works(P,F).

outcome(happy) :- chosen_problem(P), chosen_fix(F), works(P,F).
:- chosen_problem(P), chosen_fix(F), not works(P,F).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for wid in WEATHERS:
        lines.append(asp.fact("weather", wid))
    for pid in PROBLEMS:
        lines.append(asp.fact("problem", pid))
    for fid, fix in FIXES.items():
        lines.append(asp.fact("fix", fid))
        for problem_id in sorted(fix.works_for):
            lines.append(asp.fact("supports", fid, problem_id))
    for patch_id in PATCHES:
        lines.append(asp.fact("patch", patch_id))
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
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def outcome_of(params: StoryParams) -> str:
    if params.problem not in PROBLEMS or params.fix not in FIXES:
        return "?"
    return "happy" if fix_works(PROBLEMS[params.problem], FIXES[params.fix]) else "?"


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos.")

    cases = list(CURATED)
    for seed in range(50):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        params.seed = seed
        cases.append(params)

    bad = [p for p in cases if asp_outcome(p) != outcome_of(p)]
    if bad:
        rc = 1
        print(f"MISMATCH: {len(bad)}/{len(cases)} outcomes differ.")
    else:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("Smoke test failed: empty story.")
        print("OK: smoke test generate() produced a story.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Nursery-rhyme seaside storyworld about kelp, a cistern, and a small warning that leads to a happy fix."
    )
    ap.add_argument("--weather", choices=WEATHERS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--patch", choices=PATCHES)
    ap.add_argument("--child-name")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--helper-type", choices=["grandmother", "grandfather", "mother", "father"])
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
    if args.problem and args.fix:
        problem = PROBLEMS[args.problem]
        fix = FIXES[args.fix]
        if not fix_works(problem, fix):
            raise StoryError(explain_rejection(problem, fix))

    combos = [
        combo
        for combo in valid_combos()
        if (args.weather is None or combo[0] == args.weather)
        and (args.problem is None or combo[1] == args.problem)
        and (args.fix is None or combo[2] == args.fix)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    weather_id, problem_id, fix_id = rng.choice(sorted(combos))
    patch_id = args.patch or rng.choice(sorted(PATCHES))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    child_name = args.child_name or rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES)
    helper_type = args.helper_type or rng.choice(["grandmother", "grandfather", "mother", "father"])
    return StoryParams(
        weather=weather_id,
        problem=problem_id,
        fix=fix_id,
        patch=patch_id,
        child_name=child_name,
        child_gender=child_gender,
        helper_type=helper_type,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        weather = WEATHERS[params.weather]
        problem = PROBLEMS[params.problem]
        fix = FIXES[params.fix]
        patch = PATCHES[params.patch]
    except KeyError as err:
        raise StoryError(f"(Invalid story parameter: {err.args[0]})") from None
    if not fix_works(problem, fix):
        raise StoryError(explain_rejection(problem, fix))

    world = tell(
        weather=weather,
        problem=problem,
        fix=fix,
        patch_cfg=patch,
        child_name=params.child_name,
        child_gender=params.child_gender,
        helper_type=params.helper_type,
    )
    return StorySample(
        params=params,
        story=world.render().replace("child", params.child_name),
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
        print(f"{len(combos)} compatible (weather, problem, fix) combos:\n")
        for weather, problem, fix in combos:
            print(f"  {weather:8} {problem:10} {fix}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples = []
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
            header = f"### {p.child_name}: {p.problem} on a {p.weather} day ({p.fix})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
