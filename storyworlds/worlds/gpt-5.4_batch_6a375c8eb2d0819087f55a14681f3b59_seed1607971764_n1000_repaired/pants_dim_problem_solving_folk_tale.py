#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/pants_dim_problem_solving_folk_tale.py
=================================================================

A standalone story world for a small folk-tale domain: a village child carries a
basket along a country path, meets a concrete obstacle, thinks instead of
forcing, and solves the problem with the right simple tool.

The required seed word appears in the story as part of the child's clothing:
"pants-dim" patched trousers, faded by many days of work and sun.

This world is built around one reasonableness constraint:
each obstacle requires a fitting tool. The tale refuses mismatched pairings
because the story is about problem solving, not magic coincidence.

Run it
------
    python storyworlds/worlds/gpt-5.4/pants_dim_problem_solving_folk_tale.py
    python storyworlds/worlds/gpt-5.4/pants_dim_problem_solving_folk_tale.py --setting creek_path --obstacle stream_gap --tool plank
    python storyworlds/worlds/gpt-5.4/pants_dim_problem_solving_folk_tale.py --obstacle stream_gap --tool oil_can
    python storyworlds/worlds/gpt-5.4/pants_dim_problem_solving_folk_tale.py --all
    python storyworlds/worlds/gpt-5.4/pants_dim_problem_solving_folk_tale.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/pants_dim_problem_solving_folk_tale.py --trace --seed 777
    python storyworlds/worlds/gpt-5.4/pants_dim_problem_solving_folk_tale.py --verify
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


# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "grandmother"}
        male = {"boy", "man", "father", "grandfather"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {
            "grandmother": "grandmother",
            "grandfather": "grandfather",
            "mother": "mother",
            "father": "father",
        }.get(self.type, self.label or self.type)


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class Setting:
    id: str
    place: str
    opening: str
    helper_kind: str
    helper_line: str
    affords: set[str] = field(default_factory=set)
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


@dataclass
class Obstacle:
    id: str
    label: str
    the: str
    trouble: str
    risk: str
    clue: str
    solved: str
    needs: str
    tags: set[str] = field(default_factory=set)

    @property
    def The(self) -> str:
        return self.the[0].upper() + self.the[1:]
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
class Tool:
    id: str
    label: str
    phrase: str
    method: str
    works_on: set[str] = field(default_factory=set)
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
class Errand:
    id: str
    item: str
    container: str
    warm_note: str
    thanks: str
    tags: set[str] = field(default_factory=set)


# ---------------------------------------------------------------------------
# World
# ---------------------------------------------------------------------------
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
        clone.facts = copy.deepcopy(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Causal rules
# ---------------------------------------------------------------------------
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


def _r_open_path(world: World) -> list[str]:
    obstacle = world.get("obstacle")
    path = world.get("path")
    if obstacle.meters["cleared"] < THRESHOLD:
        return []
    sig = ("open_path", obstacle.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    path.meters["open"] += 1
    world.get("hero").memes["hope"] += 1
    return []


def _r_deliver(world: World) -> list[str]:
    basket = world.get("basket")
    path = world.get("path")
    elder = world.get("elder")
    if basket.meters["carried"] < THRESHOLD or path.meters["open"] < THRESHOLD:
        return []
    sig = ("deliver", basket.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    basket.meters["delivered"] += 1
    elder.memes["gratitude"] += 1
    world.get("hero").memes["relief"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="open_path", tag="physical", apply=_r_open_path),
    Rule(name="deliver", tag="physical", apply=_r_deliver),
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
                produced.extend(out)
            elif any(sig[0] == rule.name for sig in world.fired):
                changed = True if False else changed
    if narrate:
        for line in produced:
            world.say(line)
    return produced


# ---------------------------------------------------------------------------
# Reasonableness
# ---------------------------------------------------------------------------
def obstacle_in_setting(setting: Setting, obstacle: Obstacle) -> bool:
    return obstacle.id in setting.affords


def tool_fits(tool: Tool, obstacle: Obstacle) -> bool:
    return obstacle.id in tool.works_on


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for sid, setting in SETTINGS.items():
        for oid, obstacle in OBSTACLES.items():
            if not obstacle_in_setting(setting, obstacle):
                continue
            for tid, tool in TOOLS.items():
                if tool_fits(tool, obstacle):
                    combos.append((sid, oid, tid))
    return combos


def explain_rejection(setting: Optional[Setting], obstacle: Obstacle, tool: Tool) -> str:
    if setting is not None and not obstacle_in_setting(setting, obstacle):
        return (
            f"(No story: {obstacle.the} does not belong on {setting.place}. "
            f"Choose an obstacle that fits that road.)"
        )
    return (
        f"(No story: {tool.phrase.capitalize()} would not solve {obstacle.the}. "
        f"This folk tale depends on a child noticing what the problem truly is and "
        f"using a fitting tool.)"
    )


# ---------------------------------------------------------------------------
# Prediction
# ---------------------------------------------------------------------------
def predict_rushing(world: World) -> dict:
    sim = world.copy()
    hero = sim.get("hero")
    basket = sim.get("basket")
    obstacle = sim.get("obstacle")
    hero.meters["stopped"] += 1
    hero.memes["worry"] += 1
    basket.meters["at_risk"] += 1
    obstacle.meters["blocking"] += 1
    return {
        "path_open": sim.get("path").meters["open"] >= THRESHOLD,
        "basket_safe": sim.get("basket").meters["at_risk"] < THRESHOLD,
        "risk": obstacle.attrs.get("risk_text", ""),
    }


# ---------------------------------------------------------------------------
# Story actions
# ---------------------------------------------------------------------------
def introduce(world: World, hero: Entity, parent: Entity, errand: Errand) -> None:
    world.say(
        "Long ago, when paths were narrow and every hedge was said to remember "
        "the feet that passed it, there lived a village child named "
        f"{hero.id}."
    )
    world.say(
        f"{hero.pronoun().capitalize()} wore pants-dim patched trousers, faded by sun and work, "
        f"and {hero.pronoun()} carried {errand.container} of {errand.item} "
        f"for {hero.attrs['elder_title']}."
    )
    world.say(
        f"Before {hero.pronoun()} left, {parent.label_word} touched the basket and said, "
        f'"Carry it steady. {errand.warm_note}"'
    )


def set_out(world: World, hero: Entity, setting: Setting) -> None:
    hero.memes["duty"] += 1
    hero.memes["courage"] += 1
    world.say(setting.opening)
    world.say(
        f"So {hero.id} set out along {setting.place}, where the stones listened "
        f"and even the wind seemed to wait for a wise step."
    )


def meet_obstacle(world: World, obstacle: Obstacle) -> None:
    ent = world.get("obstacle")
    ent.meters["blocking"] += 1
    world.say(
        f"Halfway there, {obstacle.the} stood across the way. {obstacle.trouble}"
    )


def consider_rush(world: World, hero: Entity, obstacle: Obstacle) -> None:
    pred = predict_rushing(world)
    world.facts["predicted_risk"] = pred["risk"]
    hero.memes["worry"] += 1
    world.say(
        f"{hero.id} nearly hurried straight at it. Then {hero.pronoun()} stopped and thought, "
        f'"If I rush, {pred["risk"]}."'
    )


def helper_appears(world: World, helper: Entity, obstacle: Obstacle) -> None:
    helper.memes["kindness"] += 1
    world.say(
        f"Just then, a {helper.label} nearby gave the child a wise look. "
        f'"{world.setting.helper_line} {obstacle.clue}"'
    )


def remember_tool(world: World, hero: Entity, tool: Tool) -> None:
    hero.memes["cleverness"] += 1
    world.say(
        f"Then {hero.id} remembered {tool.phrase}, tied beside the basket handle. "
        f'"A hard knot does not yield to wishing," {hero.pronoun()} murmured. '
        f'"It yields to the right hand and the right tool."'
    )


def solve_obstacle(world: World, hero: Entity, obstacle: Obstacle, tool: Tool) -> None:
    obs = world.get("obstacle")
    obs.meters["cleared"] += 1
    obs.meters["blocking"] = 0.0
    world.get("path").meters["tried"] += 1
    propagate(world, narrate=False)
    hero.memes["pride"] += 1
    world.say(
        f"With {tool.phrase}, {hero.id} {tool.method}. {obstacle.solved}"
    )


def arrive(world: World, hero: Entity, elder: Entity, errand: Errand) -> None:
    basket = world.get("basket")
    basket.meters["carried"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then {hero.id} walked on and reached {elder.label_word}'s door with the "
        f"{errand.container} still steady and warm."
    )
    world.say(
        f'{elder.label_word.capitalize()} smiled and said, "{errand.thanks}"'
    )


def ending(world: World, hero: Entity, tool: Tool, obstacle: Obstacle) -> None:
    hero.memes["peace"] += 1
    world.say(
        f"That evening, the story went from hearth to hearth: {obstacle.the} had not been beaten by force, "
        f"but answered by thought. After that, whenever children walked {world.setting.place}, "
        f"they remembered {hero.id} and {tool.label}, and chose their wits before their hurry."
    )


# ---------------------------------------------------------------------------
# Main screenplay
# ---------------------------------------------------------------------------
def tell(
    setting: Setting,
    obstacle: Obstacle,
    tool: Tool,
    errand: Errand,
    hero_name: str = "Mira",
    hero_gender: str = "girl",
    parent_type: str = "mother",
    elder_type: str = "grandmother",
) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender, label=hero_name))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="the parent"))
    elder = world.add(Entity(id="Elder", kind="character", type=elder_type, label="the elder"))
    helper = world.add(
        Entity(
            id="helper",
            kind="character",
            type="animal",
            label=setting.helper_kind,
            attrs={"voice": "wise"},
        )
    )
    path = world.add(Entity(id="path", type="path", label=setting.place))
    basket = world.add(
        Entity(
            id="basket",
            type="basket",
            label=errand.container,
            attrs={"contents": errand.item},
        )
    )
    obstacle_ent = world.add(
        Entity(
            id="obstacle",
            type="obstacle",
            label=obstacle.label,
            attrs={"risk_text": obstacle.risk},
            tags=set(obstacle.tags),
        )
    )
    tool_ent = world.add(
        Entity(
            id="tool",
            type="tool",
            label=tool.label,
            attrs={"tool_id": tool.id},
            tags=set(tool.tags),
        )
    )
    basket.meters["carried"] = 1.0
    path.meters["open"] = 0.0
    obstacle_ent.meters["blocking"] = 0.0
    obstacle_ent.meters["cleared"] = 0.0
    hero.attrs["elder_title"] = elder.label_word
    world.facts.update(
        hero=hero,
        parent=parent,
        elder=elder,
        helper=helper,
        setting=setting,
        obstacle_cfg=obstacle,
        tool_cfg=tool,
        errand=errand,
        obstacle=obstacle_ent,
        basket=basket,
    )

    introduce(world, hero, parent, errand)
    set_out(world, hero, setting)

    world.para()
    meet_obstacle(world, obstacle)
    consider_rush(world, hero, obstacle)
    helper_appears(world, helper, obstacle)

    world.para()
    remember_tool(world, hero, tool)
    solve_obstacle(world, hero, obstacle, tool)
    arrive(world, hero, elder, errand)

    world.para()
    ending(world, hero, tool, obstacle)

    world.facts.update(
        solved=world.get("obstacle").meters["cleared"] >= THRESHOLD,
        delivered=world.get("basket").meters["delivered"] >= THRESHOLD,
        path_open=world.get("path").meters["open"] >= THRESHOLD,
    )
    return world


# ---------------------------------------------------------------------------
# Content
# ---------------------------------------------------------------------------
SETTINGS = {
    "birch_lane": Setting(
        id="birch_lane",
        place="the birch lane",
        opening="The birch leaves flashed like small coins above the road.",
        helper_kind="sparrow",
        helper_line="Little traveler, do not wrestle every trouble.",
        affords={"thorn_bush", "stuck_gate"},
    ),
    "creek_path": Setting(
        id="creek_path",
        place="the creek path",
        opening="The creek spoke in a silver voice beside the path.",
        helper_kind="frog",
        helper_line="A quick foot is not always a safe foot.",
        affords={"stream_gap", "fallen_branch"},
    ),
    "orchard_road": Setting(
        id="orchard_road",
        place="the orchard road",
        opening="Wind moved through the orchard and shook the sweet smell of apples loose.",
        helper_kind="field mouse",
        helper_line="The world opens more easily to the child who notices.",
        affords={"fallen_branch", "stuck_gate", "thorn_bush"},
    ),
}

OBSTACLES = {
    "thorn_bush": Obstacle(
        id="thorn_bush",
        label="thorn bush",
        the="the thorn bush",
        trouble="Its hooked branches had knitted themselves across the footpath and tugged at anything that brushed past.",
        risk="the thorns will tear my clothes and tip the basket",
        clue="Thorns do not listen to pushing. They listen to clean cutting.",
        solved="Soon a neat opening showed through the brambles, wide enough for one careful child and one basket.",
        needs="pruning_hook",
        tags={"thorns", "cutting"},
    ),
    "stream_gap": Obstacle(
        id="stream_gap",
        label="stream gap",
        the="the stream gap",
        trouble="Rain had carried off the stepping stones, and water skipped laughing through the empty place.",
        risk="the water will splash the basket and I may slip",
        clue="Water is crossed best by making a path where none is left.",
        solved="A narrow crossing lay firm above the water, and the creek had to let the child pass.",
        needs="plank",
        tags={"stream", "crossing"},
    ),
    "stuck_gate": Obstacle(
        id="stuck_gate",
        label="stuck gate",
        the="the stuck gate",
        trouble="The wooden gate to the pasture had swollen in the damp and would not swing, no matter how it was pulled.",
        risk="I will yank so hard that the basket will tumble from my arm",
        clue="A dry hinge grows stubborn, and stubborn things need easing, not anger.",
        solved="The hinge gave a low groan, then the gate swung open as gently as a bow.",
        needs="oil_can",
        tags={"gate", "hinge"},
    ),
    "fallen_branch": Obstacle(
        id="fallen_branch",
        label="fallen branch",
        the="the fallen branch",
        trouble="A storm branch, thick as a calf, lay across the road and would not budge for a child's hands alone.",
        risk="I will strain and spill the meal before the branch moves an inch",
        clue="Heavy wood respects a long arm more than a strong tug.",
        solved="The branch rolled off the path and settled in the grass like a beast finally choosing sleep.",
        needs="lever_pole",
        tags={"branch", "lever"},
    ),
}

TOOLS = {
    "pruning_hook": Tool(
        id="pruning_hook",
        label="pruning hook",
        phrase="the small pruning hook",
        method="trimmed the grasping stems one by one",
        works_on={"thorn_bush"},
        tags={"pruning_hook", "cutting"},
    ),
    "plank": Tool(
        id="plank",
        label="plank",
        phrase="the smooth plank",
        method="laid it from one safe bank to the other",
        works_on={"stream_gap"},
        tags={"plank", "crossing"},
    ),
    "oil_can": Tool(
        id="oil_can",
        label="oil can",
        phrase="the little oil can",
        method="tipped a shining drop into the complaining hinge and pushed once more",
        works_on={"stuck_gate"},
        tags={"oil_can", "hinge"},
    ),
    "lever_pole": Tool(
        id="lever_pole",
        label="lever pole",
        phrase="the sturdy lever pole",
        method="set the pole under the wood and bore down with all the sense in {hero}'s small body",
        works_on={"fallen_branch"},
        tags={"lever", "pole"},
    ),
}

ERRANDS = {
    "soup": Errand(
        id="soup",
        item="onion soup",
        container="lidded basket",
        warm_note="The old soup should arrive hot, and so should your good sense.",
        thanks="You brought both the meal and your wits. That is a double kindness.",
        tags={"soup", "basket"},
    ),
    "cakes": Errand(
        id="cakes",
        item="honey cakes",
        container="round basket",
        warm_note="Sweet things travel best in steady hands.",
        thanks="Honey is sweet, child, but wiser still is the mind that brought it here.",
        tags={"cakes", "basket"},
    ),
    "bread": Errand(
        id="bread",
        item="barley bread",
        container="covered basket",
        warm_note="Bread feeds the belly, but thought feeds the road ahead.",
        thanks="You have brought bread, yes, but also a lesson worth keeping.",
        tags={"bread", "basket"},
    ),
}

GIRL_NAMES = ["Mira", "Anya", "Lina", "Tessa", "Rosa", "Nella", "Iva", "Marta"]
BOY_NAMES = ["Ivo", "Milan", "Toma", "Petar", "Niko", "Jori", "Luka", "Stefan"]


# ---------------------------------------------------------------------------
# Story params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    setting: str
    obstacle: str
    tool: str
    errand: str
    hero: str
    gender: str
    parent: str
    elder: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
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
    "thorns": [
        (
            "Why can thorn bushes be hard to pass?",
            "Thorn bushes have sharp points and hooked branches. They can catch clothes and scratch skin if you push through them."
        )
    ],
    "cutting": [
        (
            "Why is a pruning hook useful for brambles?",
            "A pruning hook is made for cutting stems and small branches. It helps you make a safe opening instead of forcing your way through."
        )
    ],
    "stream": [
        (
            "Why can a stream crossing be slippery?",
            "Water makes stones and mud slick. Feet can slide when the ground is wet and uneven."
        )
    ],
    "crossing": [
        (
            "What does a plank do across a gap?",
            "A plank makes a flat path from one side to the other. It helps people step over water or a hole more safely."
        )
    ],
    "gate": [
        (
            "Why can a wooden gate get stuck?",
            "Wood can swell when it gets damp, and hinges can turn stiff. Then a gate may not swing open easily."
        )
    ],
    "hinge": [
        (
            "What does oil do for a squeaky hinge?",
            "Oil helps the hinge move more smoothly. It lowers the rubbing that makes the hinge stiff and noisy."
        )
    ],
    "branch": [
        (
            "Why does a long pole help move something heavy?",
            "A long pole can work like a lever. It lets a person use their strength in a smarter way."
        )
    ],
    "lever": [
        (
            "What is a lever?",
            "A lever is a bar you use to lift or move something. It helps a small push do bigger work."
        )
    ],
    "soup": [
        (
            "Why should soup be carried steadily?",
            "Soup can spill if the basket swings or tips. Carrying it steadily keeps the meal warm and clean."
        )
    ],
    "cakes": [
        (
            "Why are honey cakes best carried carefully?",
            "Honey cakes can slide or crumble if they are jostled. A steady basket helps them arrive whole."
        )
    ],
    "bread": [
        (
            "Why does bread belong in a covered basket?",
            "A covered basket helps keep bread clean and dry. It also makes it easier to carry from one house to another."
        )
    ],
    "basket": [
        (
            "Why is a basket useful on an errand?",
            "A basket holds things together and leaves your hands freer. It helps you carry food without dropping it."
        )
    ],
}
KNOWLEDGE_ORDER = [
    "thorns",
    "cutting",
    "stream",
    "crossing",
    "gate",
    "hinge",
    "branch",
    "lever",
    "soup",
    "cakes",
    "bread",
    "basket",
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    obstacle = f["obstacle_cfg"]
    errand = f["errand"]
    return [
        'Write a short folk tale for a 3-to-5-year-old about a child who solves a path problem by thinking first. Include the word "pants-dim".',
        f"Tell a folk-style story where {hero.id} carries {errand.item} in a basket, meets {obstacle.the}, and solves the trouble with careful problem solving instead of force.",
        f'Write a gentle old-fashioned tale with a wise helper, a blocked road, and a happy ending that teaches children to use their wits before rushing.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    elder = f["elder"]
    obstacle = f["obstacle_cfg"]
    tool = f["tool_cfg"]
    errand = f["errand"]
    helper = f["helper"]
    risk = f.get("predicted_risk", "")
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, a child carrying {errand.item} to {elder.label_word}. The tale follows how {hero.pronoun()} solves a real problem on the road."
        ),
        (
            "What problem did the child meet on the path?",
            f"{obstacle.The} blocked the way, so {hero.id} could not simply walk on. The trouble mattered because the basket had to arrive safe and steady."
        ),
        (
            f"Why did {hero.id} stop and think instead of rushing?",
            f"{hero.id} realized that if {hero.pronoun()} rushed, {risk}. That second thought turned the story from a struggle into a problem to solve."
        ),
        (
            f"How did the {helper.label} help?",
            f"The {helper.label} did not fix the trouble by itself. It gave a wise clue that helped {hero.id} understand what kind of solution the obstacle needed."
        ),
        (
            f"How did {hero.id} solve the problem?",
            f"{hero.pronoun().capitalize()} used {tool.phrase} to deal with {obstacle.the}. The tool fit the problem, so the path opened and the basket stayed safe."
        ),
        (
            "How did the story end?",
            f"{hero.id} reached {elder.label_word}'s door with the food still warm, and the village remembered the lesson. The ending shows that careful thinking changed the journey."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["obstacle_cfg"].tags) | set(f["tool_cfg"].tags) | set(f["errand"].tags)
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


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
available_obstacle(S, O) :- setting(S), obstacle(O), affords(S, O).
fit(T, O) :- tool(T), obstacle(O), works_on(T, O).
valid(S, O, T) :- available_obstacle(S, O), fit(T, O).

#show valid/3.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for oid in OBSTACLES:
        lines.append(asp.fact("obstacle", oid))
    for tid in TOOLS:
        lines.append(asp.fact("tool", tid))
    for sid, setting in SETTINGS.items():
        for oid in sorted(setting.affords):
            lines.append(asp.fact("affords", sid, oid))
    for tid, tool in TOOLS.items():
        for oid in sorted(tool.works_on):
            lines.append(asp.fact("works_on", tid, oid))
    return "\n".join(lines)


def asp_program(show: str = "#show valid/3.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    cset = set(asp_valid_combos())
    pset = set(valid_combos())
    if cset == pset:
        print(f"OK: ASP gate matches valid_combos() ({len(cset)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if cset - pset:
            print("  only in clingo:", sorted(cset - pset))
        if pset - cset:
            print("  only in python:", sorted(pset - cset))

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("empty story from smoke test")
        print("OK: smoke generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    try:
        parser = build_parser()
        params = resolve_params(parser.parse_args([]), random.Random(123))
        sample = generate(params)
        if not sample.story.strip():
            raise StoryError("empty story from default random generation")
        print("OK: default random generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"DEFAULT GENERATION FAILED: {err}")

    return rc


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
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
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        lines.append(f"  {ent.id:8} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(sig[0] for sig in world.fired))}")
    return "\n".join(lines)


def _render_tool_method(tool: Tool, hero: Entity) -> Tool:
    if "{hero}" not in tool.method:
        return tool
    return Tool(
        id=tool.id,
        label=tool.label,
        phrase=tool.phrase,
        method=tool.method.format(hero=hero.id),
        works_on=set(tool.works_on),
        tags=set(tool.tags),
    )


# ---------------------------------------------------------------------------
# CLI contract
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a folk-tale child solves a blocked-path problem with the fitting tool."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--obstacle", choices=OBSTACLES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--errand", choices=ERRANDS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--hero")
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--elder", choices=["grandmother", "grandfather"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.obstacle and args.tool:
        setting = SETTINGS[args.setting]
        obstacle = OBSTACLES[args.obstacle]
        tool = TOOLS[args.tool]
        if not (obstacle_in_setting(setting, obstacle) and tool_fits(tool, obstacle)):
            raise StoryError(explain_rejection(setting, obstacle, tool))

    combos = [
        combo for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.obstacle is None or combo[1] == args.obstacle)
        and (args.tool is None or combo[2] == args.tool)
    ]
    if not combos:
        if args.obstacle and args.tool:
            obstacle = OBSTACLES[args.obstacle]
            tool = TOOLS[args.tool]
            setting = SETTINGS[args.setting] if args.setting else None
            raise StoryError(explain_rejection(setting, obstacle, tool))
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, obstacle_id, tool_id = rng.choice(sorted(combos))
    errand_id = args.errand or rng.choice(sorted(ERRANDS))
    gender = args.gender or rng.choice(["girl", "boy"])
    hero = args.hero or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    elder = args.elder or rng.choice(["grandmother", "grandfather"])
    return StoryParams(
        setting=setting_id,
        obstacle=obstacle_id,
        tool=tool_id,
        errand=errand_id,
        hero=hero,
        gender=gender,
        parent=parent,
        elder=elder,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting: {params.setting})")
    if params.obstacle not in OBSTACLES:
        raise StoryError(f"(Unknown obstacle: {params.obstacle})")
    if params.tool not in TOOLS:
        raise StoryError(f"(Unknown tool: {params.tool})")
    if params.errand not in ERRANDS:
        raise StoryError(f"(Unknown errand: {params.errand})")
    if params.gender not in {"girl", "boy"}:
        raise StoryError(f"(Unknown gender: {params.gender})")
    if params.parent not in {"mother", "father"}:
        raise StoryError(f"(Unknown parent type: {params.parent})")
    if params.elder not in {"grandmother", "grandfather"}:
        raise StoryError(f"(Unknown elder type: {params.elder})")

    setting = SETTINGS[params.setting]
    obstacle = OBSTACLES[params.obstacle]
    tool = TOOLS[params.tool]
    if not obstacle_in_setting(setting, obstacle) or not tool_fits(tool, obstacle):
        raise StoryError(explain_rejection(setting, obstacle, tool))

    hero_name = params.hero.strip()
    if not hero_name:
        raise StoryError("(Hero name cannot be empty.)")

    story_tool = _render_tool_method(tool, Entity(id=hero_name, type=params.gender))
    world = tell(
        setting=setting,
        obstacle=obstacle,
        tool=story_tool,
        errand=ERRANDS[params.errand],
        hero_name=hero_name,
        hero_gender=params.gender,
        parent_type=params.parent,
        elder_type=params.elder,
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


CURATED = [
    StoryParams(
        setting="birch_lane",
        obstacle="thorn_bush",
        tool="pruning_hook",
        errand="cakes",
        hero="Mira",
        gender="girl",
        parent="mother",
        elder="grandmother",
    ),
    StoryParams(
        setting="creek_path",
        obstacle="stream_gap",
        tool="plank",
        errand="soup",
        hero="Ivo",
        gender="boy",
        parent="father",
        elder="grandfather",
    ),
    StoryParams(
        setting="orchard_road",
        obstacle="fallen_branch",
        tool="lever_pole",
        errand="bread",
        hero="Rosa",
        gender="girl",
        parent="mother",
        elder="grandfather",
    ),
    StoryParams(
        setting="birch_lane",
        obstacle="stuck_gate",
        tool="oil_can",
        errand="cakes",
        hero="Niko",
        gender="boy",
        parent="father",
        elder="grandmother",
    ),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, obstacle, tool) combos:\n")
        for setting, obstacle, tool in combos:
            print(f"  {setting:12} {obstacle:13} {tool}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples: list[StorySample] = []
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
            header = f"### {p.hero}: {p.obstacle} on {p.setting} ({p.tool})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
