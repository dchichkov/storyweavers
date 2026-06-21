#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/mole_increment_conflict_problem_solving_rhyme_tall.py
================================================================================

A standalone story world for a child-facing tall tale about a mighty little
mole who solves outsized problems one careful increment at a time.

This world models:
- a terrain with workable ground
- a local problem threatening something important
- a dirt-working plan that may or may not fit the problem
- a helper whose strength can make the plan reasonable
- a rival whose teasing creates the conflict and whose change of heart shapes
  the ending

The stories are tall tales: the mole's digging is grand, the stakes are bigger
than life, and the solution arrives through practical, step-by-step problem
solving. Each story includes rhyme in the mole's work chant and uses the words
"mole" and "increment" in the prose.

Run it
------
    python storyworlds/worlds/gpt-5.4/mole_increment_conflict_problem_solving_rhyme_tall.py
    python storyworlds/worlds/gpt-5.4/mole_increment_conflict_problem_solving_rhyme_tall.py --terrain prairie --problem flood --plan trench
    python storyworlds/worlds/gpt-5.4/mole_increment_conflict_problem_solving_rhyme_tall.py --problem wagon --plan trench
    python storyworlds/worlds/gpt-5.4/mole_increment_conflict_problem_solving_rhyme_tall.py --all
    python storyworlds/worlds/gpt-5.4/mole_increment_conflict_problem_solving_rhyme_tall.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/mole_increment_conflict_problem_solving_rhyme_tall.py --verify
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
MAX_INCREMENTS = 3


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
        female = {"girl", "woman", "hen"}
        male = {"boy", "man", "badger", "bison"}
        neutral = {"mole", "crow", "town", "thing"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in neutral:
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
class Terrain:
    id: str
    place: str
    detail: str
    bonus: int
    supports: set[str] = field(default_factory=set)
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
    opening: str
    threat: str
    target: str
    need: str
    severity: int
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
    noun: str
    verb: str
    built_label: str
    power: int
    solves: set[str] = field(default_factory=set)
    chant: str = ""
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
class Helper:
    id: str
    label: str
    type: str
    power: int
    entrance: str
    action: str
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
class Rival:
    id: str
    label: str
    type: str
    taunt: str
    soften: str
    openness: int
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


def _r_worry(world: World) -> list[str]:
    problem = world.get("problem")
    if problem.meters["active"] < THRESHOLD:
        return []
    sig = ("worry",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    world.get("town").memes["worry"] += 1
    world.get("mole").memes["resolve"] += 1
    return []


def _r_soften(world: World) -> list[str]:
    rival = world.get("rival")
    work = world.get("work")
    if rival.attrs.get("joined"):
        return []
    if work.meters["built"] < 2:
        return []
    if rival.attrs.get("openness", 0) + work.attrs.get("plan_power", 0) < 4:
        return []
    sig = ("soften", rival.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    rival.attrs["joined"] = True
    rival.memes["respect"] += 1
    world.get("mole").memes["hope"] += 1
    return ["__joined__"]


def _r_solve(world: World) -> list[str]:
    problem = world.get("problem")
    work = world.get("work")
    if problem.meters["active"] < THRESHOLD:
        return []
    strength = work.meters["built"] + work.attrs.get("plan_power", 0)
    need = problem.attrs.get("need_score", 99)
    if strength < need:
        return []
    sig = ("solve",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    problem.meters["active"] = 0.0
    world.get("town").memes["relief"] += 1
    world.get("mole").memes["pride"] += 1
    return ["__solved__"]


CAUSAL_RULES = [
    Rule(name="worry", tag="social", apply=_r_worry),
    Rule(name="soften", tag="social", apply=_r_soften),
    Rule(name="solve", tag="physical", apply=_r_solve),
]


def propagate(world: World) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            out = rule.apply(world)
            if out:
                produced.extend(out)
                changed = True
            elif rule.name == "worry":
                # worry may fire silently; still counts as state change if it was new
                pass
    return produced


TERRAINS = {
    "prairie": Terrain(
        id="prairie",
        place="the wide prairie",
        detail="The grass rolled so far that even the clouds seemed to stop for water.",
        bonus=1,
        supports={"trench", "wall", "mound"},
        tags={"prairie"},
    ),
    "canyon": Terrain(
        id="canyon",
        place="the red canyon",
        detail="The earth there stood in layers like a stack of rusty flapjacks.",
        bonus=1,
        supports={"trench", "ramp", "wall"},
        tags={"canyon"},
    ),
    "orchard": Terrain(
        id="orchard",
        place="the apple orchard",
        detail="Each row of trees looked as neat as combed hair after Sunday washing.",
        bonus=0,
        supports={"trench", "wall", "mound"},
        tags={"orchard"},
    ),
    "fairground": Terrain(
        id="fairground",
        place="the county fairground",
        detail="The empty midway stretched long enough to make a goose feel dizzy.",
        bonus=0,
        supports={"ramp", "mound", "wall"},
        tags={"fairground"},
    ),
}

PROBLEMS = {
    "flood": Problem(
        id="flood",
        opening="one noon the creek forgot its manners",
        threat="A silver ribbon of water hopped its bank and came skipping toward the bean rows.",
        target="the bean rows",
        need="divert",
        severity=5,
        tags={"water", "beans"},
    ),
    "wagon": Problem(
        id="wagon",
        opening="one windy afternoon the pie wagon groaned",
        threat="The town pie wagon sank axle-deep in the road, and every blueberry pie leaned like a sleepy moon.",
        target="the pie wagon",
        need="lift",
        severity=5,
        tags={"wagon", "pies"},
    ),
    "dust": Problem(
        id="dust",
        opening="one dry day the wind got too proud",
        threat="A dust cloud rolled toward the schoolhouse, puffing bigger every minute like a brown balloon.",
        target="the schoolhouse",
        need="block",
        severity=4,
        tags={"dust", "schoolhouse"},
    ),
}

PLANS = {
    "trench": Plan(
        id="trench",
        noun="trench",
        verb="scratch a winding trench",
        built_label="channel",
        power=2,
        solves={"divert"},
        chant="Dig a lane to save the grain!",
        tags={"trench"},
    ),
    "ramp": Plan(
        id="ramp",
        noun="ramp",
        verb="pile a broad dirt ramp",
        built_label="rise",
        power=2,
        solves={"lift"},
        chant="Raise a rise to lift the prize!",
        tags={"ramp"},
    ),
    "wall": Plan(
        id="wall",
        noun="wall",
        verb="pat a stout dirt wall",
        built_label="barrier",
        power=1,
        solves={"block"},
        chant="Pack it high to hush the sky!",
        tags={"wall"},
    ),
    "mound": Plan(
        id="mound",
        noun="mound",
        verb="heap a sky-high molehill",
        built_label="mound",
        power=2,
        solves={"lift", "block"},
        chant="Heap it steep and never sleep!",
        tags={"mound"},
    ),
}

HELPERS = {
    "none": Helper(
        id="none",
        label="no helper",
        type="thing",
        power=0,
        entrance="No one came at first, so the little mole worked alone.",
        action="worked with nothing but his own bright claws",
        tags=set(),
    ),
    "badger": Helper(
        id="badger",
        label="Badger",
        type="badger",
        power=1,
        entrance="Badger heard the scratching from halfway across the county and trotted over with a shovel broad as a biscuit pan.",
        action="scraped and shoved beside the mole",
        tags={"badger"},
    ),
    "bison": Helper(
        id="bison",
        label="Bison",
        type="bison",
        power=2,
        entrance="Bison thundered in from the edge of town, lowering shoulders as wide as barn doors.",
        action="leaned and pushed with a mighty shove",
        tags={"bison"},
    ),
}

RIVALS = {
    "crow": Rival(
        id="crow",
        label="Crow",
        type="crow",
        taunt='"A mole that small cannot mend trouble that tall!" Crow cawed from the fencepost.',
        soften='Crow blinked, shuffled his feet, and muttered, "Well, I do like a good rhyme more than a bad guess."',
        openness=2,
        tags={"crow"},
    ),
    "coyote": Rival(
        id="coyote",
        label="Coyote",
        type="coyote",
        taunt='"You could dig till the moon needs milking and still not finish!" Coyote yipped.',
        soften='Coyote stopped laughing and said, "That is the steadiest little plan I ever saw."',
        openness=1,
        tags={"coyote"},
    ),
    "goose": Rival(
        id="goose",
        label="Goose",
        type="thing",
        taunt='"Honk all day if you like, but dirt will not jump just because a mole sings at it!" cried Goose.',
        soften='Goose flapped once and admitted, "A fair chant and a fairer plan deserve fair help."',
        openness=3,
        tags={"goose"},
    ),
}


def plan_fits(problem: Problem, plan: Plan) -> bool:
    return problem.need in plan.solves


def terrain_supports(terrain: Terrain, plan: Plan) -> bool:
    return plan.id in terrain.supports


def work_score(terrain: Terrain, helper: Helper, plan: Plan) -> int:
    return terrain.bonus + helper.power + plan.power + MAX_INCREMENTS


def combo_succeeds(terrain: Terrain, problem: Problem, plan: Plan, helper: Helper) -> bool:
    return plan_fits(problem, plan) and terrain_supports(terrain, plan) and work_score(terrain, helper, plan) >= problem.severity


def valid_combos() -> list[tuple[str, str, str, str]]:
    out: list[tuple[str, str, str, str]] = []
    for terrain_id, terrain in TERRAINS.items():
        for problem_id, problem in PROBLEMS.items():
            for plan_id, plan in PLANS.items():
                for helper_id, helper in HELPERS.items():
                    if combo_succeeds(terrain, problem, plan, helper):
                        out.append((terrain_id, problem_id, plan_id, helper_id))
    return out


def rival_joins(rival: Rival, plan: Plan) -> bool:
    return rival.openness + plan.power >= 4


@dataclass
class StoryParams:
    terrain: str
    problem: str
    plan: str
    helper: str
    rival: str
    mole_name: str
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


CURATED = [
    StoryParams(
        terrain="prairie",
        problem="flood",
        plan="trench",
        helper="badger",
        rival="crow",
        mole_name="Marlow",
    ),
    StoryParams(
        terrain="fairground",
        problem="wagon",
        plan="ramp",
        helper="none",
        rival="goose",
        mole_name="Midge",
    ),
    StoryParams(
        terrain="orchard",
        problem="dust",
        plan="wall",
        helper="bison",
        rival="coyote",
        mole_name="Marlow",
    ),
    StoryParams(
        terrain="prairie",
        problem="dust",
        plan="mound",
        helper="none",
        rival="goose",
        mole_name="Midge",
    ),
    StoryParams(
        terrain="canyon",
        problem="wagon",
        plan="ramp",
        helper="badger",
        rival="crow",
        mole_name="Marlow",
    ),
]

MOLE_NAMES = ["Marlow", "Midge", "Moss", "Millie"]


def explain_rejection(terrain: Terrain, problem: Problem, plan: Plan, helper: Helper) -> str:
    if not plan_fits(problem, plan):
        return (
            f"(No story: a {plan.noun} does not solve this trouble. "
            f"The problem needs a way to {problem.need}, so pick a plan that really matches it.)"
        )
    if not terrain_supports(terrain, plan):
        return (
            f"(No story: {terrain.place} will not sensibly support a {plan.noun} in this tall tale. "
            f"Pick a plan the ground can honestly hold.)"
        )
    return (
        f"(No story: {helper.label.capitalize() if helper.id != 'none' else 'working alone'} does not give "
        f"enough strength for this problem. The mole needs a stronger helper or a better-matched plan.)"
    )


def outcome_of(params: StoryParams) -> str:
    rival = RIVALS[params.rival]
    plan = PLANS[params.plan]
    return "joined" if rival_joins(rival, plan) else "solo"


def chant_for(plan: Plan, problem: Problem) -> str:
    if plan.id == "trench" and problem.id == "flood":
        return "Dig a lane to save the grain!"
    if plan.id == "ramp" and problem.id == "wagon":
        return "Raise a rise to lift the prize!"
    if plan.id == "wall" and problem.id == "dust":
        return "Pack it high to hush the sky!"
    if plan.id == "mound" and problem.id == "dust":
        return "Heap it steep till the dust can't leap!"
    if plan.id == "mound" and problem.id == "wagon":
        return "Heap it steep and save the keep!"
    return plan.chant


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for ent in list(world.entities.values()):
        bits = []
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v or v == 0}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


def introduce(world: World, mole: Entity, terrain: Terrain, problem: Problem) -> None:
    mole.memes["confidence"] += 1
    world.say(
        f"In {terrain.place}, there lived a mole named {mole.id} whose paws could scratch "
        f"so briskly that fence posts swore they felt a breeze. {terrain.detail}"
    )
    world.say(
        f"Folks said {mole.id} never hurried foolishly; he solved things one careful increment at a time."
    )
    world.say(
        f"Then {problem.opening}. {problem.threat}"
    )


def alarm(world: World, town: Entity, mole: Entity, problem: Problem) -> None:
    world.say(
        f"The town gasped because {problem.target} mattered to everybody, and every eye turned toward the little mole."
    )
    town.memes["trust"] += 1
    world.say(
        f'{mole.id} brushed dirt from his nose and said, "Big trouble may shout, but small sense can still speak up."'
    )


def taunt(world: World, rival: Entity, problem: Problem) -> None:
    rival.memes["skeptic"] += 1
    world.say(RIVALS[rival.attrs["cfg"]].taunt)
    world.say(
        f"For a blink, the teasing stung sharper than a thistle."
    )


def plan_scene(world: World, mole: Entity, terrain: Terrain, problem: Problem, plan: Plan) -> None:
    mole.memes["resolve"] += 1
    chant = chant_for(plan, problem)
    world.facts["chant"] = chant
    world.say(
        f"But {mole.id} studied the ground, the danger, and the space between them. "
        f"He chose to {plan.verb} because that was the honest way to {problem.need} the trouble."
    )
    world.say(
        f'He tapped the earth three times and made a rhyme for the work: "{chant}"'
    )


def helper_arrives(world: World, helper_cfg: Helper) -> None:
    if helper_cfg.id == "none":
        world.say(helper_cfg.entrance)
    else:
        world.say(helper_cfg.entrance)


def work_increment(world: World, mole: Entity, helper: Entity, helper_cfg: Helper,
                   plan: Plan, problem: Problem, increment_no: int) -> list[str]:
    work = world.get("work")
    work.meters["built"] += 1
    mole.meters["increments"] += 1
    mole.memes["grit"] += 1
    world.say(
        f"With the {increment_no}{ordinal_tail(increment_no)} increment, {mole.id} clawed and packed dirt until the {plan.built_label} looked bigger than last time and straighter too."
    )
    world.say(
        f'"{world.facts["chant"]}" sang {mole.id}.'
    )
    if increment_no == 2 and helper_cfg.power > 0 and not helper.attrs.get("helped"):
        helper.attrs["helped"] = True
        work.meters["built"] += helper_cfg.power
        mole.memes["relief"] += 1
        world.say(
            f"Then {helper_cfg.label} {helper_cfg.action}, adding a great lurch of good work all at once."
        )
    events = propagate(world)
    return events


def rival_turn(world: World, rival: Entity) -> None:
    cfg = RIVALS[rival.attrs["cfg"]]
    world.say(cfg.soften)
    world.say(
        f"Soon {cfg.label} was keeping the beat while the little mole kept the plan."
    )


def solve_scene(world: World, problem: Problem, plan: Plan, rival_joined: bool) -> None:
    if problem.id == "flood":
        ending = (
            "The runaway water swung into the new channel, curved away from the beans, "
            "and behaved itself like a scolded ribbon."
        )
    elif problem.id == "wagon":
        ending = (
            "The pie wagon bumped up, rolled free, and not one blueberry moon slid off its tin."
        )
    else:
        ending = (
            "The dust cloud hit the fresh dirt and split around it, leaving the schoolhouse bright and sneeze-free."
        )
    world.say(ending)
    if rival_joined:
        world.say(
            f"The crowd cheered so hard that hats bounced, pies rattled, and even the teasing sounded friendly at last."
        )
    else:
        world.say(
            f"The crowd cheered so hard that windows hummed, and the old teasing blew away like chaff."
        )


def ending_scene(world: World, mole: Entity, rival: Entity, helper_cfg: Helper, problem: Problem) -> None:
    joined = bool(rival.attrs.get("joined"))
    if joined:
        world.say(
            f'From then on, whenever anyone doubted a careful plan, {rival.label} was first to say, '
            f'"Listen to the mole and count each increment."'
        )
    else:
        world.say(
            f'{rival.label} tipped a sheepish head and said no more mean things that day.'
        )
    if helper_cfg.id == "none":
        world.say(
            f"And {mole.id}, the mole with dirt on his whiskers and sense in his head, walked home under a sunset so tall it looked like it needed its own ladder."
        )
    else:
        world.say(
            f"And {mole.id} walked home beside {helper_cfg.label}, both of them wearing dirt like medals while the town admired what steady thinking could do."
        )
    world.say(
        f"That is why people in that place still say a rhyme helps memory, but a plan helps everybody."
    )


def ordinal_tail(n: int) -> str:
    if 10 <= n % 100 <= 20:
        return "th"
    return {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")


def tell(terrain: Terrain, problem: Problem, plan: Plan, helper_cfg: Helper,
         rival_cfg: Rival, mole_name: str) -> World:
    world = World()
    mole = world.add(Entity(id=mole_name, kind="character", type="mole", role="hero"))
    town = world.add(Entity(id="Town", kind="character", type="town", role="town"))
    rival = world.add(
        Entity(
            id="rival",
            kind="character",
            type=rival_cfg.type,
            role="rival",
            label=rival_cfg.label,
            attrs={"cfg": rival_cfg.id, "openness": rival_cfg.openness, "joined": False},
        )
    )
    helper = world.add(
        Entity(
            id="helper",
            kind="character",
            type=helper_cfg.type,
            role="helper",
            label=helper_cfg.label,
            attrs={"cfg": helper_cfg.id, "helped": False},
        )
    )
    problem_ent = world.add(
        Entity(
            id="problem",
            kind="thing",
            type="problem",
            label=problem.target,
            attrs={"need_score": problem.severity},
        )
    )
    problem_ent.meters["active"] = 1.0
    work = world.add(
        Entity(
            id="work",
            kind="thing",
            type="work",
            label=plan.built_label,
            attrs={"plan_power": plan.power},
        )
    )
    work.meters["built"] = float(terrain.bonus)

    world.facts.update(
        terrain=terrain,
        problem_cfg=problem,
        plan_cfg=plan,
        helper_cfg=helper_cfg,
        rival_cfg=rival_cfg,
        mole=mole,
        town=town,
        rival=rival,
        helper=helper,
        problem=problem_ent,
        work=work,
        increment_lines=[],
        joined=False,
        solved=False,
    )

    introduce(world, mole, terrain, problem)
    propagate(world)
    alarm(world, town, mole, problem)

    world.para()
    taunt(world, rival, problem)
    plan_scene(world, mole, terrain, problem, plan)
    helper_arrives(world, helper_cfg)

    world.para()
    for increment_no in range(1, MAX_INCREMENTS + 1):
        events = work_increment(world, mole, helper, helper_cfg, plan, problem, increment_no)
        world.facts["increment_lines"].append(increment_no)
        if "__joined__" in events and not world.facts["joined"]:
            world.facts["joined"] = True
            rival_turn(world, rival)
        if "__solved__" in events:
            world.facts["solved"] = True
            world.facts["increments_used"] = increment_no
            break

    if not world.facts["solved"]:
        raise StoryError("(Story generation failed: the plan did not solve the problem in time.)")

    world.para()
    solve_scene(world, problem, plan, bool(rival.attrs.get("joined")))
    ending_scene(world, mole, rival, helper_cfg, problem)

    world.facts.update(
        target=problem.target,
        rival_joined=bool(rival.attrs.get("joined")),
        helper_used=helper_cfg.id != "none",
        increments_used=world.facts.get("increments_used", MAX_INCREMENTS),
        chant=world.facts["chant"],
        outcome="joined" if rival.attrs.get("joined") else "solo",
    )
    return world


def generation_prompts(world: World) -> list[str]:
    terrain = world.facts["terrain"]
    problem = world.facts["problem_cfg"]
    plan = world.facts["plan_cfg"]
    mole = world.facts["mole"]
    return [
        f'Write a tall tale for a 3-to-5-year-old about a mole who solves a big problem one increment at a time. Include the words "mole" and "increment".',
        f"Tell a rhyming problem-solving story set in {terrain.place} where {mole.id} uses a {plan.noun} to save {problem.target} after someone laughs at the idea.",
        f'Write a child-friendly tall tale with conflict, a practical plan, and a work chant that rhymes while a tiny hero handles oversized trouble.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    terrain = world.facts["terrain"]
    problem = world.facts["problem_cfg"]
    plan = world.facts["plan_cfg"]
    helper = world.facts["helper_cfg"]
    rival = world.facts["rival_cfg"]
    mole = world.facts["mole"]
    joined = world.facts["rival_joined"]
    increments_used = world.facts["increments_used"]
    chant = world.facts["chant"]

    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {mole.id}, a little mole in {terrain.place}. He faced a problem much bigger than he was, which is what makes the tale feel tall and grand."
        ),
        (
            f"What problem did {mole.id} have to solve?",
            f"{problem.threat} That was dangerous because it was heading for {problem.target}, so the town needed a real fix instead of just worry."
        ),
        (
            f"How did {mole.id} decide what to do?",
            f"He studied the ground and chose to {plan.verb}. He solved the problem by matching the plan to what the trouble needed, not by guessing wildly."
        ),
        (
            "What does the word increment mean in this story?",
            f"Here, an increment means one small measured piece of progress. {mole.id} kept making the {plan.built_label} bigger step by step until the whole job worked."
        ),
        (
            "What rhyme did the mole sing while working?",
            f'He sang, "{chant}" That rhyme helped keep the work steady and showed he was thinking clearly while he dug.'
        ),
    ]
    if helper.id == "none":
        qa.append(
            (
                f"Did anyone help {mole.id} at first?",
                f"No. He began alone, which made the conflict sharper because someone was teasing him while he worked. His steady digging proved that a small start can still matter."
            )
        )
    else:
        qa.append(
            (
                f"How did {helper.label} help?",
                f"{helper.label} came in and added a burst of strong work beside the mole. That extra help made the plan faster and showed that smart problem solving can welcome teamwork."
            )
        )
    qa.append(
        (
            f"How many increments did it take before the problem was solved?",
            f"It took {increments_used} increments in the story before the trouble was beaten. The count matters because the tale shows progress building a little at a time into something big."
        )
    )
    if joined:
        qa.append(
            (
                f"Why did {rival.label} stop teasing?",
                f"{rival.label} saw the plan working and heard the steady rhyme, so the teasing turned into respect. The change happened because the mole's careful actions were stronger than the rival's loud doubts."
            )
        )
    else:
        qa.append(
            (
                f"Did {rival.label} help in the end?",
                f"No, but the teasing stopped. The rival had to admit the mole's plan worked even without joining in."
            )
        )
    return qa


KNOWLEDGE = {
    "mole": [
        (
            "What is a mole?",
            "A mole is a small animal that digs underground with strong front paws. It is good at moving dirt and making tunnels."
        )
    ],
    "increment": [
        (
            "What is an increment?",
            "An increment is one small step or one small amount added to something. When many increments add up, they can make a big change."
        )
    ],
    "trench": [
        (
            "What is a trench?",
            "A trench is a long narrow ditch dug in the ground. People or animals can use one to guide water or make space for something to move."
        )
    ],
    "ramp": [
        (
            "What is a ramp?",
            "A ramp is a sloping path that helps something go up or down. It is useful when lifting or rolling heavy things."
        )
    ],
    "wall": [
        (
            "What does a wall do?",
            "A wall blocks or holds something back. A strong wall can stop wind, dust, or other things from rushing through."
        )
    ],
    "mound": [
        (
            "What is a mound?",
            "A mound is a raised heap of earth or other material. It can make a barrier or lift one side of something higher."
        )
    ],
    "rhyme": [
        (
            "What is a rhyme?",
            "A rhyme is when words sound alike at the end, like lane and grain. Rhymes can help people remember what they are doing."
        )
    ],
    "problem_solving": [
        (
            "What does problem solving mean?",
            "Problem solving means noticing what is wrong, thinking of a plan, and trying steps that fit the problem. Good problem solving uses both thinking and action."
        )
    ],
    "water": [
        (
            "Why can flood water be a problem?",
            "Flood water can move where it does not belong and soak plants, roads, or houses. A safe path for the water can help protect things nearby."
        )
    ],
    "dust": [
        (
            "Why is a dust storm hard for people?",
            "Dust can blow into eyes and noses and make it hard to see. Blocking or slowing it helps keep people safer and more comfortable."
        )
    ],
    "wagon": [
        (
            "Why can a wagon get stuck?",
            "A wagon can get stuck when its wheels sink into soft ground or mud. Lifting it or giving it a better path can help it roll again."
        )
    ],
    "badger": [
        (
            "What is a badger good at?",
            "A badger is a strong digging animal. Its claws are useful for scratching and moving earth."
        )
    ],
    "bison": [
        (
            "Why is a bison strong?",
            "A bison has a very big body and strong shoulders. That strength helps it push through hard places."
        )
    ],
}
KNOWLEDGE_ORDER = [
    "mole",
    "increment",
    "problem_solving",
    "rhyme",
    "trench",
    "ramp",
    "wall",
    "mound",
    "water",
    "dust",
    "wagon",
    "badger",
    "bison",
]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    problem = world.facts["problem_cfg"]
    plan = world.facts["plan_cfg"]
    helper = world.facts["helper_cfg"]
    tags = {"mole", "increment", "problem_solving", "rhyme", plan.id}
    tags |= set(problem.tags)
    tags |= set(helper.tags)
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


ASP_RULES = r"""
fits(Pb, Pl) :- problem(Pb), plan(Pl), need(Pb, N), solves(Pl, N).
grounded(T, Pl) :- terrain(T), plan(Pl), supports(T, Pl).
score(T, H, Pl, S) :- terrain(T), helper(H), plan(Pl),
                      bonus(T, B), helper_power(H, HP), plan_power(Pl, PP),
                      max_increments(M), S = B + HP + PP + M.
valid(T, Pb, Pl, H) :- fits(Pb, Pl), grounded(T, Pl), severity(Pb, Need),
                       score(T, H, Pl, S), S >= Need.

rival_joins(R, Pl) :- rival(R), plan(Pl), openness(R, O), plan_power(Pl, P), O + P >= 4.
outcome(joined) :- chosen_rival(R), chosen_plan(Pl), rival_joins(R, Pl).
outcome(solo) :- chosen_rival(R), chosen_plan(Pl), not rival_joins(R, Pl).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for terrain_id, terrain in TERRAINS.items():
        lines.append(asp.fact("terrain", terrain_id))
        lines.append(asp.fact("bonus", terrain_id, terrain.bonus))
        for plan_id in sorted(terrain.supports):
            lines.append(asp.fact("supports", terrain_id, plan_id))
    for problem_id, problem in PROBLEMS.items():
        lines.append(asp.fact("problem", problem_id))
        lines.append(asp.fact("need", problem_id, problem.need))
        lines.append(asp.fact("severity", problem_id, problem.severity))
    for plan_id, plan in PLANS.items():
        lines.append(asp.fact("plan", plan_id))
        lines.append(asp.fact("plan_power", plan_id, plan.power))
        for need in sorted(plan.solves):
            lines.append(asp.fact("solves", plan_id, need))
    for helper_id, helper in HELPERS.items():
        lines.append(asp.fact("helper", helper_id))
        lines.append(asp.fact("helper_power", helper_id, helper.power))
    for rival_id, rival in RIVALS.items():
        lines.append(asp.fact("rival", rival_id))
        lines.append(asp.fact("openness", rival_id, rival.openness))
    lines.append(asp.fact("max_increments", MAX_INCREMENTS))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join([
        asp.fact("chosen_rival", params.rival),
        asp.fact("chosen_plan", params.plan),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Tall-tale story world: a mole solves giant trouble one increment at a time."
    )
    ap.add_argument("--terrain", choices=sorted(TERRAINS))
    ap.add_argument("--problem", choices=sorted(PROBLEMS))
    ap.add_argument("--plan", choices=sorted(PLANS))
    ap.add_argument("--helper", choices=sorted(HELPERS))
    ap.add_argument("--rival", choices=sorted(RIVALS))
    ap.add_argument("--mole-name", choices=MOLE_NAMES)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combinations from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.terrain and args.problem and args.plan and args.helper:
        terrain = TERRAINS[args.terrain]
        problem = PROBLEMS[args.problem]
        plan = PLANS[args.plan]
        helper = HELPERS[args.helper]
        if not combo_succeeds(terrain, problem, plan, helper):
            raise StoryError(explain_rejection(terrain, problem, plan, helper))

    combos = [
        combo for combo in valid_combos()
        if (args.terrain is None or combo[0] == args.terrain)
        and (args.problem is None or combo[1] == args.problem)
        and (args.plan is None or combo[2] == args.plan)
        and (args.helper is None or combo[3] == args.helper)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    terrain_id, problem_id, plan_id, helper_id = rng.choice(sorted(combos))
    rival_id = args.rival or rng.choice(sorted(RIVALS))
    mole_name = args.mole_name or rng.choice(MOLE_NAMES)
    return StoryParams(
        terrain=terrain_id,
        problem=problem_id,
        plan=plan_id,
        helper=helper_id,
        rival=rival_id,
        mole_name=mole_name,
    )


def generate(params: StoryParams) -> StorySample:
    if params.terrain not in TERRAINS:
        raise StoryError(f"(Unknown terrain: {params.terrain})")
    if params.problem not in PROBLEMS:
        raise StoryError(f"(Unknown problem: {params.problem})")
    if params.plan not in PLANS:
        raise StoryError(f"(Unknown plan: {params.plan})")
    if params.helper not in HELPERS:
        raise StoryError(f"(Unknown helper: {params.helper})")
    if params.rival not in RIVALS:
        raise StoryError(f"(Unknown rival: {params.rival})")
    terrain = TERRAINS[params.terrain]
    problem = PROBLEMS[params.problem]
    plan = PLANS[params.plan]
    helper = HELPERS[params.helper]
    if not combo_succeeds(terrain, problem, plan, helper):
        raise StoryError(explain_rejection(terrain, problem, plan, helper))
    world = tell(terrain, problem, plan, helper, RIVALS[params.rival], params.mole_name)
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
    py_valid = set(valid_combos())
    asp_valid = set(asp_valid_combos())
    if py_valid == asp_valid:
        print(f"OK: valid combos match ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if py_valid - asp_valid:
            print("  only in python:", sorted(py_valid - asp_valid))
        if asp_valid - py_valid:
            print("  only in clingo:", sorted(asp_valid - py_valid))

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(20):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
        except StoryError:
            continue
        params.seed = seed
        cases.append(params)

    bad = 0
    for params in cases:
        expected = outcome_of(params)
        actual = asp_outcome(params)
        if expected != actual:
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcome checks differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("(Smoke test failed: empty story.)")
        print("OK: smoke test story generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/4.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (terrain, problem, plan, helper) combos:\n")
        for terrain_id, problem_id, plan_id, helper_id in combos:
            print(f"  {terrain_id:10} {problem_id:8} {plan_id:7} {helper_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        attempt = 0
        while len(samples) < args.n and attempt < max(args.n * 50, 50):
            seed = base_seed + attempt
            attempt += 1
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
            header = f"### {p.mole_name}: {p.problem} in {p.terrain} ({p.plan}, {p.helper}, {outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
