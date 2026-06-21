#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/vole_problem_solving_lesson_learned_superhero_story.py
=================================================================================

A standalone story world for a tiny superhero tale about a vole who learns that
the best heroes do not just dash forward -- they stop, look closely, and solve
the real problem.

Domain:
- protagonist: a little vole in superhero play
- feature focus: problem solving, lesson learned
- style: superhero story

Run it
------
    python storyworlds/worlds/gpt-5.4/vole_problem_solving_lesson_learned_superhero_story.py
    python storyworlds/worlds/gpt-5.4/vole_problem_solving_lesson_learned_superhero_story.py --place garden --problem puddle_path --plan twig_bridge
    python storyworlds/worlds/gpt-5.4/vole_problem_solving_lesson_learned_superhero_story.py --plan cape_yank
    python storyworlds/worlds/gpt-5.4/vole_problem_solving_lesson_learned_superhero_story.py --all --qa
    python storyworlds/worlds/gpt-5.4/vole_problem_solving_lesson_learned_superhero_story.py --verify
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
SENSE_MIN = 2


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
        female = {"girl", "mother", "sister", "hen"}
        male = {"boy", "father", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]
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
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Setting:
    id: str
    label: str
    scene: str
    affords: set[str] = field(default_factory=set)
    materials: set[str] = field(default_factory=set)
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
    severity: int
    intro: str
    victim_kind: str
    victim_label: str
    goal: str
    obstacle: str
    object_label: str
    cry: str
    problem_meter: str
    solved_meter: str
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
class Plan:
    id: str
    need: str
    material: str
    sense: int
    power: int
    noun: str
    build_text: str
    solve_text: str
    qa_text: str
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


def _r_distress(world: World) -> list[str]:
    out: list[str] = []
    problem = world.get("problem")
    victim = world.get("victim")
    if problem.meters["active"] < THRESHOLD or problem.meters["solved"] >= THRESHOLD:
        return out
    sig = ("distress", world.facts.get("problem_id", "problem"))
    if sig in world.fired:
        return out
    world.fired.add(sig)
    victim.memes["worry"] += 1
    world.get("hero").memes["mission"] += 1
    return out


def _r_think(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    if hero.memes["thinking"] < THRESHOLD:
        return out
    sig = ("think", hero.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["focus"] += 1
    hero.memes["impatience"] = 0.0
    return out


def _r_relief(world: World) -> list[str]:
    out: list[str] = []
    problem = world.get("problem")
    if problem.meters["solved"] < THRESHOLD:
        return out
    sig = ("relief", world.facts.get("problem_id", "problem"))
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("victim").memes["relief"] += 1
    world.get("hero").memes["joy"] += 1
    world.get("sidekick").memes["joy"] += 1
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="distress", tag="emotional", apply=_r_distress),
    Rule(name="think", tag="emotional", apply=_r_think),
    Rule(name="relief", tag="emotional", apply=_r_relief),
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
                produced.extend(sents)
    if narrate:
        for sent in produced:
            world.say(sent)
    return produced


SETTINGS = {
    "garden": Setting(
        id="garden",
        label="the garden",
        scene="Sunflower stalks leaned over the paths like giant towers, and the pebble walk shone in the sun.",
        affords={"puddle_path", "blocked_burrow"},
        materials={"twig", "leaf", "reed", "pole"},
        tags={"garden"},
    ),
    "meadow": Setting(
        id="meadow",
        label="the meadow",
        scene="Buttercups nodded in the breeze, and a ribbon of dirt path curled through the grass.",
        affords={"puddle_path", "kite_tree"},
        materials={"twig", "leaf", "pole"},
        tags={"meadow"},
    ),
    "orchard": Setting(
        id="orchard",
        label="the orchard",
        scene="Apple trees made cool green shade, and old crates stood in neat stacks beside the path.",
        affords={"blocked_burrow", "kite_tree"},
        materials={"crate", "pole", "twig"},
        tags={"orchard"},
    ),
}

PROBLEMS = {
    "puddle_path": Problem(
        id="puddle_path",
        need="cross",
        severity=1,
        intro="A rain puddle had spread across the path like a shiny blue moat.",
        victim_kind="ants",
        victim_label="the ant twins",
        goal="carry a crumb home",
        obstacle="the puddle",
        object_label="their bread crumb",
        cry='"Oh no!" cried the ant twins. "Our bread crumb is bigger than our legs, and the puddle is too wide for us."',
        problem_meter="blocked",
        solved_meter="crossed",
        tags={"puddle", "problem_solving"},
    ),
    "blocked_burrow": Problem(
        id="blocked_burrow",
        need="move",
        severity=2,
        intro="A fallen flowerpot had tipped against a burrow door and sealed it shut.",
        victim_kind="mole",
        victim_label="Mina the mole pup",
        goal="get back into her burrow",
        obstacle="the flowerpot",
        object_label="the burrow door",
        cry='"Help!" squeaked Mina the mole pup. "I can see my warm blanket inside, but the flowerpot is too heavy for me."',
        problem_meter="jammed",
        solved_meter="opened",
        tags={"burrow", "problem_solving"},
    ),
    "kite_tree": Problem(
        id="kite_tree",
        need="reach",
        severity=1,
        intro="A little red kite had snagged on a low branch and fluttered there like a trapped flag.",
        victim_kind="rabbit",
        victim_label="Rori the rabbit",
        goal="get a kite back",
        obstacle="the branch",
        object_label="the red kite",
        cry='"My kite!" said Rori the rabbit. "I cannot jump high enough to reach it."',
        problem_meter="stuck",
        solved_meter="retrieved",
        tags={"kite", "problem_solving"},
    ),
}

PLANS = {
    "twig_bridge": Plan(
        id="twig_bridge",
        need="cross",
        material="twig",
        sense=3,
        power=1,
        noun="a tiny twig bridge",
        build_text="lined up dry twigs from the path until they made a narrow little bridge over the water",
        solve_text="The ant twins marched across the twig bridge together and tugged their bread crumb safely home",
        qa_text="built a tiny twig bridge so the ant twins could cross the puddle",
        tags={"bridge", "twigs"},
    ),
    "leaf_boat": Plan(
        id="leaf_boat",
        need="cross",
        material="leaf",
        sense=3,
        power=1,
        noun="a leaf boat",
        build_text="chose the widest leaf nearby and bent the stem into a tiny handle",
        solve_text="The ant twins climbed into the leaf boat, and the vole nudged it gently across the puddle",
        qa_text="made a leaf boat and ferried the ant twins across the puddle",
        tags={"leaf", "boat"},
    ),
    "reed_lever": Plan(
        id="reed_lever",
        need="move",
        material="reed",
        sense=3,
        power=2,
        noun="a strong reed lever",
        build_text="slid a strong reed under the edge of the flowerpot and pressed down slowly",
        solve_text="The flowerpot rocked, lifted, and rolled aside just enough for Mina to slip back into her burrow",
        qa_text="used a strong reed as a lever to move the flowerpot",
        tags={"lever", "reed"},
    ),
    "crate_steps": Plan(
        id="crate_steps",
        need="reach",
        material="crate",
        sense=3,
        power=1,
        noun="crate steps",
        build_text="dragged two light orchard crates into a safe little stair",
        solve_text="Climbing the crate steps, the vole reached the low branch and gently pulled the red kite free",
        qa_text="stacked crate steps and climbed up to reach the kite",
        tags={"crate", "steps"},
    ),
    "long_pole": Plan(
        id="long_pole",
        need="reach",
        material="pole",
        sense=3,
        power=1,
        noun="a long rescue pole",
        build_text="found a smooth fallen stem and tested its reach from the ground",
        solve_text="With one careful lift of the long pole, the red kite slipped off the branch and floated down",
        qa_text="used a long pole to lift the kite off the branch",
        tags={"pole", "reach"},
    ),
    "cape_yank": Plan(
        id="cape_yank",
        need="move",
        material="cape",
        sense=1,
        power=0,
        noun="a cape yank",
        build_text="grabbed the cape and planned to tug wildly",
        solve_text="Nothing sensible happened",
        qa_text="tried to solve it with a wild cape yank",
        tags={"cape"},
    ),
}


def problem_supported(setting: Setting, problem: Problem) -> bool:
    return problem.id in setting.affords


def plan_supported(setting: Setting, problem: Problem, plan: Plan) -> bool:
    return (
        plan.need == problem.need
        and plan.material in setting.materials
        and plan.sense >= SENSE_MIN
        and plan.power >= problem.severity
    )


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place, setting in SETTINGS.items():
        for problem_id, problem in PROBLEMS.items():
            if not problem_supported(setting, problem):
                continue
            for plan_id, plan in PLANS.items():
                if plan_supported(setting, problem, plan):
                    combos.append((place, problem_id, plan_id))
    return combos


def explain_problem_rejection(setting: Setting, problem: Problem) -> str:
    return (
        f"(No story: {problem.obstacle} does not fit {setting.label}. "
        f"Pick a place that actually affords this kind of rescue.)"
    )


def explain_plan_rejection(setting: Setting, problem: Problem, plan: Plan) -> str:
    if plan.sense < SENSE_MIN:
        return (
            f"(Refusing plan '{plan.id}': it is too wild to count as good problem solving "
            f"(sense={plan.sense} < {SENSE_MIN}). A superhero story here should reward careful thinking.)"
        )
    if plan.need != problem.need:
        return (
            f"(No story: {plan.noun} solves a '{plan.need}' problem, but this mission needs "
            f"'{problem.need}'. The rescue tool has to match the real problem.)"
        )
    if plan.material not in setting.materials:
        return (
            f"(No story: {setting.label} does not have the material needed for {plan.noun}. "
            f"Choose a plan the vole could actually build there.)"
        )
    if plan.power < problem.severity:
        return (
            f"(No story: {plan.noun} is too weak for {problem.obstacle}. "
            f"This world only tells rescues the chosen plan can truly finish.)"
        )
    return "(No story: that plan does not fit this rescue.)"


def predict_success(world: World, plan: Plan) -> dict:
    sim = world.copy()
    hero = sim.get("hero")
    problem = sim.get("problem")
    tool = sim.get("tool")
    hero.memes["thinking"] += 1
    propagate(sim, narrate=False)
    tool.meters["built"] += 1
    if (
        plan.need == sim.facts.get("need")
        and plan.sense >= SENSE_MIN
        and plan.power >= sim.facts.get("severity", 0)
    ):
        problem.meters["solved"] += 1
        problem.meters["active"] = 0.0
        propagate(sim, narrate=False)
    return {
        "solved": problem.meters["solved"] >= THRESHOLD,
        "focus": hero.memes["focus"],
    }


def introduce(world: World, hero: Entity, sidekick: Entity) -> None:
    title = hero.attrs["hero_title"]
    world.say(
        f"{hero.id} was a little vole with a red cape made from a scrap of ribbon and a paper star pinned at the neck."
    )
    world.say(
        f"Whenever the wind puffed the cape behind {hero.pronoun('object')}, {hero.pronoun()} called {hero.pronoun('object')}self {title}."
    )
    world.say(
        f"That afternoon {hero.id} and {sidekick.id}, {hero.pronoun('possessive')} trusty sidekick, hurried into {world.setting.label}. {world.setting.scene}"
    )


def mission_arrives(world: World, hero: Entity, victim: Entity, problem_cfg: Problem) -> None:
    problem = world.get("problem")
    problem.meters["active"] += 1
    problem.meters[problem_cfg.problem_meter] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then a cry for help zipped through the air. {problem_cfg.intro}"
    )
    world.say(problem_cfg.cry)
    world.say(
        f"{hero.id} planted {hero.pronoun('possessive')} paws wide. "
        f'"This is a job for {hero.attrs["hero_title"]}!" {hero.pronoun()} declared.'
    )


def rush_first(world: World, hero: Entity, sidekick: Entity, problem_cfg: Problem) -> None:
    hero.memes["bravery"] += 1
    hero.memes["impatience"] += 1
    world.say(
        f"{hero.id} almost sprang forward at once, ready to make one huge superhero move at {problem_cfg.obstacle}."
    )
    world.say(
        f'But {sidekick.id} touched the edge of the red cape and whispered, "Wait. What is the real problem first?"'
    )


def inspect(world: World, hero: Entity, sidekick: Entity, problem_cfg: Problem, plan: Plan) -> None:
    hero.memes["thinking"] += 1
    hero.memes["wisdom"] += 1
    propagate(world, narrate=False)
    prediction = predict_success(world, plan)
    world.facts["predicted_focus"] = prediction["focus"]
    world.say(
        f"{hero.id} stopped, blinked, and looked closely. It was not enough to be brave; {hero.pronoun()} had to understand what was wrong."
    )
    if problem_cfg.need == "cross":
        line = "The problem was not fighting the puddle. The problem was making a safe way across."
    elif problem_cfg.need == "move":
        line = "The problem was not shouting at the flowerpot. The problem was finding a smart way to move it."
    else:
        line = "The problem was not jumping higher and higher. The problem was reaching the branch safely."
    world.say(line)
    world.say(
        f'"I need {plan.noun}," {hero.id} said at last. "{sidekick.id}, help me look."'
    )


def build_plan(world: World, hero: Entity, sidekick: Entity, plan: Plan) -> None:
    tool = world.get("tool")
    tool.meters["built"] += 1
    sidekick.memes["helpfulness"] += 1
    world.say(
        f"Together they searched the ground, and soon {hero.id} {plan.build_text}."
    )
    world.say(
        f"The little invention did not look flashy, but it looked right."
    )


def solve(world: World, hero: Entity, victim: Entity, problem_cfg: Problem, plan: Plan) -> None:
    problem = world.get("problem")
    problem.meters["solved"] += 1
    problem.meters["active"] = 0.0
    problem.meters[problem_cfg.solved_meter] += 1
    propagate(world, narrate=False)
    world.say(plan.solve_text + ".")
    world.say(
        f"{victim.id}'s face changed at once. The worried look melted away like a cloud moving off the sun."
    )


def celebration(world: World, hero: Entity, sidekick: Entity, victim: Entity, plan: Plan) -> None:
    hero.memes["learned"] += 1
    hero.memes["pride"] += 1
    world.say(
        f'"Hooray for {hero.attrs["hero_title"]}!" {victim.id} cheered.'
    )
    world.say(
        f'{sidekick.id} grinned. "You were brave," {sidekick.pronoun()} said, "but the best part was when you stopped to think."'
    )
    world.say(
        f"{hero.id} looked at {plan.noun} and nodded. "
        f'"A real superhero solves the right problem," {hero.pronoun()} said.'
    )
    world.say(
        f"Then the little vole swished the red cape once more, not to look grand, but because another good idea might be needed someday."
    )


def tell(
    setting: Setting,
    problem_cfg: Problem,
    plan: Plan,
    *,
    hero_name: str = "Pip",
    sidekick_name: str = "Tansy",
    mentor_type: str = "mother",
) -> World:
    world = World(setting)
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type="vole",
        label="the vole hero",
        role="hero",
        attrs={"hero_title": "Captain Clover"},
    ))
    sidekick = world.add(Entity(
        id=sidekick_name,
        kind="character",
        type="mouse",
        label="the sidekick",
        role="sidekick",
        attrs={},
    ))
    mentor = world.add(Entity(
        id="Mentor",
        kind="character",
        type=mentor_type,
        label="the grown-up",
        role="mentor",
        attrs={},
    ))
    victim = world.add(Entity(
        id=problem_cfg.victim_label.split()[0].capitalize() if problem_cfg.victim_label.startswith("the ") else problem_cfg.victim_label.split()[0],
        kind="character",
        type=problem_cfg.victim_kind,
        label=problem_cfg.victim_label,
        role="victim",
        attrs={},
    ))
    problem = world.add(Entity(
        id="problem",
        kind="thing",
        type="problem",
        label=problem_cfg.obstacle,
        role="problem",
        attrs={},
    ))
    tool = world.add(Entity(
        id="tool",
        kind="thing",
        type="tool",
        label=plan.noun,
        role="tool",
        attrs={"material": plan.material},
    ))

    world.facts.update(
        place=setting,
        problem_cfg=problem_cfg,
        problem_id=problem_cfg.id,
        plan=plan,
        need=problem_cfg.need,
        severity=problem_cfg.severity,
        hero=hero,
        sidekick=sidekick,
        mentor=mentor,
        victim=victim,
        object_label=problem_cfg.object_label,
    )

    hero.memes["bravery"] = 1.0
    hero.memes["impatience"] = 0.0
    hero.memes["thinking"] = 0.0
    hero.memes["wisdom"] = 0.0
    hero.memes["learned"] = 0.0
    sidekick.memes["helpfulness"] = 0.0
    victim.memes["worry"] = 0.0
    victim.memes["relief"] = 0.0
    problem.meters["active"] = 0.0
    problem.meters["solved"] = 0.0
    problem.meters[problem_cfg.problem_meter] = 0.0
    problem.meters[problem_cfg.solved_meter] = 0.0
    tool.meters["built"] = 0.0

    introduce(world, hero, sidekick)
    world.para()
    mission_arrives(world, hero, victim, problem_cfg)
    rush_first(world, hero, sidekick, problem_cfg)
    world.para()
    inspect(world, hero, sidekick, problem_cfg, plan)
    build_plan(world, hero, sidekick, plan)
    solve(world, hero, victim, problem_cfg, plan)
    world.para()
    celebration(world, hero, sidekick, victim, plan)

    world.facts.update(
        solved=problem.meters["solved"] >= THRESHOLD,
        lesson_learned=hero.memes["learned"] >= THRESHOLD,
        used_plan=plan.id,
    )
    return world


@dataclass
class StoryParams:
    place: str
    problem: str
    plan: str
    hero_name: str
    sidekick_name: str
    mentor: str
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


GIRL_NAMES = ["Mina", "Tansy", "Luma", "Poppy", "Nell", "Ivy"]
BOY_NAMES = ["Pip", "Moss", "Ollie", "Bram", "Tobin", "Ash"]
SIDEKICK_NAMES = ["Tansy", "Moss", "Poppy", "Ash", "Juniper", "Bean"]

CURATED = [
    StoryParams(
        place="garden",
        problem="puddle_path",
        plan="twig_bridge",
        hero_name="Pip",
        sidekick_name="Tansy",
        mentor="mother",
        seed=1,
    ),
    StoryParams(
        place="garden",
        problem="blocked_burrow",
        plan="reed_lever",
        hero_name="Moss",
        sidekick_name="Bean",
        mentor="father",
        seed=2,
    ),
    StoryParams(
        place="orchard",
        problem="kite_tree",
        plan="crate_steps",
        hero_name="Luma",
        sidekick_name="Ash",
        mentor="mother",
        seed=3,
    ),
    StoryParams(
        place="meadow",
        problem="kite_tree",
        plan="long_pole",
        hero_name="Ollie",
        sidekick_name="Juniper",
        mentor="father",
        seed=4,
    ),
    StoryParams(
        place="meadow",
        problem="puddle_path",
        plan="leaf_boat",
        hero_name="Poppy",
        sidekick_name="Moss",
        mentor="mother",
        seed=5,
    ),
]


KNOWLEDGE = {
    "vole": [
        (
            "What is a vole?",
            "A vole is a very small furry animal with a round body, tiny ears, and quick little paws. It often lives near grass, gardens, or burrows."
        )
    ],
    "puddle": [
        (
            "What is a puddle?",
            "A puddle is a small patch of water on the ground, often left after rain. Tiny animals may find even a small puddle hard to cross."
        )
    ],
    "bridge": [
        (
            "What does a bridge do?",
            "A bridge makes a safe way to cross over something like water or a gap. Even a small bridge can solve a big problem when it fits the need."
        )
    ],
    "lever": [
        (
            "What is a lever?",
            "A lever is a strong bar or stick you push on to help lift or move something heavy. It lets a small force help with a bigger job."
        )
    ],
    "kite": [
        (
            "Why can a kite get stuck in a tree?",
            "A kite is light and catches the wind, so a gust can blow it into a branch. Once it snags there, reaching it safely matters more than jumping wildly."
        )
    ],
    "problem_solving": [
        (
            "What does problem solving mean?",
            "Problem solving means stopping to notice what is wrong, thinking of a good plan, and trying the plan carefully. It is not just doing something fast."
        )
    ],
    "superhero": [
        (
            "What makes someone a real superhero?",
            "A real superhero helps others with courage and kindness. The best superheroes also think carefully so their brave ideas really work."
        )
    ],
}
KNOWLEDGE_ORDER = ["vole", "superhero", "problem_solving", "puddle", "bridge", "lever", "kite"]


def generation_prompts(world: World) -> list[str]:
    hero = world.facts["hero"]
    problem_cfg = world.facts["problem_cfg"]
    plan = world.facts["plan"]
    return [
        f'Write a short superhero story for a 3-to-5-year-old about a vole who solves a problem. Include the word "vole".',
        f"Tell a gentle superhero story where {hero.id}, a little vole in a red cape, first wants to rush in but learns to stop and think before helping.",
        f'Write a problem-solving story with a clear lesson learned, where the hero uses {plan.noun} to fix a problem involving {problem_cfg.obstacle}.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    hero = world.facts["hero"]
    sidekick = world.facts["sidekick"]
    victim = world.facts["victim"]
    problem_cfg = world.facts["problem_cfg"]
    plan = world.facts["plan"]
    place = world.facts["place"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, a little vole who pretends to be a superhero, and {sidekick.id}, the sidekick who helps {hero.pronoun('object')} think. The mission begins when {victim.label} needs help in {place.label}."
        ),
        (
            "What problem needed to be solved?",
            f"{victim.label.capitalize()} needed help because {problem_cfg.obstacle} was in the way. That kept {victim.pronoun('object')} from being able to {problem_cfg.goal}."
        ),
        (
            f"Why did {hero.id} stop rushing and start thinking?",
            f"{hero.id} almost tried one big superhero move right away, but {sidekick.id} asked what the real problem was first. That reminder helped the vole see that brave feelings alone would not fix {problem_cfg.obstacle}."
        ),
        (
            f"How did {hero.id} solve the problem?",
            f"{hero.id} {plan.qa_text}. The plan worked because it matched the real job that had to be done, not just the most dramatic thing the vole could imagine."
        ),
        (
            "What lesson did the vole learn?",
            f"The vole learned that a real superhero does not just hurry. {hero.pronoun().capitalize()} learned to look closely, understand the problem, and choose the right plan."
        ),
    ]
    if world.facts.get("solved"):
        qa.append(
            (
                f"How did the story end?",
                f"The rescue ended happily, and {victim.label} could finally {problem_cfg.goal}. The last image shows the little vole swishing a red cape after learning that smart thinking is part of being heroic."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"vole", "superhero"} | set(world.facts["problem_cfg"].tags)
    plan = world.facts["plan"]
    if "bridge" in plan.tags:
        tags.add("bridge")
    if "lever" in plan.tags:
        tags.add("lever")
    if "kite" in world.facts["problem_cfg"].tags:
        tags.add("kite")
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
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:10} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
problem_supported(Place, Problem) :- affords(Place, Problem).

plan_supported(Place, Problem, Plan) :-
    problem_supported(Place, Problem),
    need_of(Problem, Need),
    plan_need(Plan, Need),
    requires(Plan, Material),
    material(Place, Material),
    sense(Plan, S), sense_min(M), S >= M,
    power(Plan, P), severity(Problem, V), P >= V.

valid(Place, Problem, Plan) :- place(Place), problem(Problem), plan(Plan),
                               plan_supported(Place, Problem, Plan).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id, setting in SETTINGS.items():
        lines.append(asp.fact("place", place_id))
        for problem_id in sorted(setting.affords):
            lines.append(asp.fact("affords", place_id, problem_id))
        for material in sorted(setting.materials):
            lines.append(asp.fact("material", place_id, material))
    for problem_id, problem in PROBLEMS.items():
        lines.append(asp.fact("problem", problem_id))
        lines.append(asp.fact("need_of", problem_id, problem.need))
        lines.append(asp.fact("severity", problem_id, problem.severity))
    for plan_id, plan in PLANS.items():
        lines.append(asp.fact("plan", plan_id))
        lines.append(asp.fact("plan_need", plan_id, plan.need))
        lines.append(asp.fact("requires", plan_id, plan.material))
        lines.append(asp.fact("sense", plan_id, plan.sense))
        lines.append(asp.fact("power", plan_id, plan.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: ASP gate matches valid_combos() ({len(clingo_set)} combos).")
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
            raise StoryError("empty story")
        with redirect_stdout(io.StringIO()):
            emit(sample, trace=True, qa=True, header="### smoke")
        rng = random.Random(123)
        params = resolve_params(build_parser().parse_args([]), rng)
        sample2 = generate(params)
        if not sample2.story.strip():
            raise StoryError("empty random story")
        print("OK: smoke-tested normal story generation and emit().")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A superhero story world about a little vole who learns to solve the real problem."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--plan", choices=PLANS)
    ap.add_argument("--hero-name")
    ap.add_argument("--sidekick-name")
    ap.add_argument("--mentor", choices=["mother", "father"], help="grown-up mentioned in the background")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible (place, problem, plan) combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the ASP program")
    return ap


def _pick_name(rng: random.Random) -> str:
    return rng.choice(sorted(set(GIRL_NAMES + BOY_NAMES)))


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.problem:
        setting = SETTINGS[args.place]
        problem = PROBLEMS[args.problem]
        if not problem_supported(setting, problem):
            raise StoryError(explain_problem_rejection(setting, problem))
    if args.place and args.problem and args.plan:
        setting = SETTINGS[args.place]
        problem = PROBLEMS[args.problem]
        plan = PLANS[args.plan]
        if not plan_supported(setting, problem, plan):
            raise StoryError(explain_plan_rejection(setting, problem, plan))
    elif args.plan and PLANS[args.plan].sense < SENSE_MIN:
        problem = PROBLEMS[args.problem] if args.problem else next(iter(PROBLEMS.values()))
        setting = SETTINGS[args.place] if args.place else next(iter(SETTINGS.values()))
        raise StoryError(explain_plan_rejection(setting, problem, PLANS[args.plan]))

    combos = [
        combo
        for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.problem is None or combo[1] == args.problem)
        and (args.plan is None or combo[2] == args.plan)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, problem_id, plan_id = rng.choice(sorted(combos))
    hero_name = args.hero_name or _pick_name(rng)
    sidekick_pool = [n for n in SIDEKICK_NAMES if n != hero_name]
    sidekick_name = args.sidekick_name or rng.choice(sidekick_pool)
    mentor = args.mentor or rng.choice(["mother", "father"])
    return StoryParams(
        place=place,
        problem=problem_id,
        plan=plan_id,
        hero_name=hero_name,
        sidekick_name=sidekick_name,
        mentor=mentor,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in SETTINGS:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.problem not in PROBLEMS:
        raise StoryError(f"(Unknown problem: {params.problem})")
    if params.plan not in PLANS:
        raise StoryError(f"(Unknown plan: {params.plan})")

    setting = SETTINGS[params.place]
    problem_cfg = PROBLEMS[params.problem]
    plan = PLANS[params.plan]

    if not problem_supported(setting, problem_cfg):
        raise StoryError(explain_problem_rejection(setting, problem_cfg))
    if not plan_supported(setting, problem_cfg, plan):
        raise StoryError(explain_plan_rejection(setting, problem_cfg, plan))

    world = tell(
        setting,
        problem_cfg,
        plan,
        hero_name=params.hero_name,
        sidekick_name=params.sidekick_name,
        mentor_type=params.mentor,
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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, problem, plan) combos:\n")
        for place, problem, plan in combos:
            print(f"  {place:8} {problem:15} {plan}")
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
            header = f"### {p.hero_name}: {p.problem} at {p.place} with {p.plan}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
