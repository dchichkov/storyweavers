#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/splutter_knifer_temperament_transformation_problem_solving_adventure.py
===================================================================================================

A standalone story world for a tiny adventure domain built from a seed requiring
the words "splutter", "knifer", and "temperament", with the narrative features
Transformation and Problem Solving.

Premise
-------
A child explorer and a companion are on a small quest to reach a treasure place,
but the path is blocked. The eager child has a strong temperament and first wants
to solve the problem the rough way with a "knifer" -- a little pruning knife from
a grown-up's kit. The wiser companion suggests a safer transformation instead:
warming wax, watering dry vines, or thawing ice so the obstacle changes state and
the path opens without dangerous cutting.

The world model tracks:
- physical meters (stuck, soft, open, danger, transformed)
- emotional memes (joy, impatience, caution, relief, pride, trust)

A reasonableness gate ensures that each obstacle has a transformation method that
actually fits it. The inline ASP twin mirrors the Python gate and outcome model.

Run it
------
    python storyworlds/worlds/gpt-5.4/splutter_knifer_temperament_transformation_problem_solving_adventure.py
    python storyworlds/worlds/gpt-5.4/splutter_knifer_temperament_transformation_problem_solving_adventure.py --obstacle wax_gate
    python storyworlds/worlds/gpt-5.4/splutter_knifer_temperament_transformation_problem_solving_adventure.py --method warm_water
    python storyworlds/worlds/gpt-5.4/splutter_knifer_temperament_transformation_problem_solving_adventure.py --all
    python storyworlds/worlds/gpt-5.4/splutter_knifer_temperament_transformation_problem_solving_adventure.py --verify
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
SENSE_MIN = 2
BOLD_INIT = 6.0
CALM_TRAITS = {"patient", "careful", "steady", "thoughtful"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    dangerous: bool = False
    tool_kind: str = ""
    obstacle_kind: str = ""
    goal_kind: str = ""
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
        return self.label or self.type
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
class Quest:
    id: str
    scene: str
    opening: str
    goal: str
    goal_place: str
    send_off: str
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
class Obstacle:
    id: str
    label: str
    the: str
    texture: str
    problem: str
    opens_when: str
    transformed_into: str
    kind: str
    stubbornness: int
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
class Method:
    id: str
    label: str
    phrase: str
    changes: str
    suits: set[str]
    action: str
    result: str
    qa_text: str
    sense: int = 3
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
class UnsafeTool:
    id: str
    label: str
    phrase: str
    where: str
    warning: str
    dangerous: bool = True
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
class Guide:
    id: str
    title: str
    style: str
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


def _r_open_path(world: World) -> list[str]:
    obstacle = world.get("obstacle")
    if obstacle.meters["soft"] < THRESHOLD:
        return []
    sig = ("open_path", obstacle.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    obstacle.meters["open"] += 1
    obstacle.meters["stuck"] = 0.0
    world.get("path").meters["open"] += 1
    hero = world.get("hero")
    helper = world.get("helper")
    hero.memes["relief"] += 1
    helper.memes["relief"] += 1
    return ["__open__"]


def _r_danger_from_knifer(world: World) -> list[str]:
    tool = world.get("tool")
    hero = world.get("hero")
    if tool.meters["grabbed"] < THRESHOLD or hero.memes["impatience"] < THRESHOLD:
        return []
    sig = ("danger", tool.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    world.get("path").meters["danger"] += 1
    hero.memes["worry"] += 1
    world.get("helper").memes["caution"] += 1
    return ["__danger__"]


CAUSAL_RULES = [
    Rule(name="open_path", tag="physical", apply=_r_open_path),
    Rule(name="danger_from_knifer", tag="physical", apply=_r_danger_from_knifer),
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


def method_fits(obstacle: Obstacle, method: Method) -> bool:
    return obstacle.kind in method.suits


def sensible_methods() -> list[Method]:
    return [m for m in METHODS.values() if m.sense >= SENSE_MIN]


def predicted_open(obstacle: Obstacle, method: Method) -> bool:
    return method_fits(obstacle, method)


def calm_score(trait: str) -> float:
    return 5.0 if trait in CALM_TRAITS else 3.0


def guide_can_redirect(trait: str, trust: int) -> bool:
    return calm_score(trait) + (1.0 if trust >= 6 else 0.0) > 5.0


def predict_transform(world: World, method_id: str) -> dict:
    sim = world.copy()
    method = METHODS[method_id]
    obstacle = sim.get("obstacle")
    if method_fits(OBSTACLES[obstacle.obstacle_kind], method):
        obstacle.meters["soft"] += 1
        obstacle.meters["transformed"] += 1
        propagate(sim, narrate=False)
    return {
        "opens": obstacle.meters["open"] >= THRESHOLD,
        "danger": sim.get("path").meters["danger"],
    }


def introduce(world: World, hero: Entity, helper: Entity, quest: Quest, guide: Entity) -> None:
    hero.memes["joy"] += 1
    helper.memes["joy"] += 1
    world.say(
        f"Early one bright morning, {hero.id} and {helper.id} set out on {quest.scene}. "
        f"{quest.opening}"
    )
    world.say(
        f"They were following a ribbon of path toward {quest.goal_place}, where "
        f"{quest.goal} waited."
    )
    world.say(
        f"{guide.id}, {guide.attrs['title']}, walked behind them with a small satchel "
        f"and a smile that stayed calm even when the trail turned tricky."
    )


def set_temperament(world: World, hero: Entity) -> None:
    mood = "quick" if hero.attrs["temperament"] == "fiery" else "bouncy"
    world.say(
        f"{hero.id} had a {mood} temperament that made every clue feel urgent. "
        f"When adventure knocked, {hero.pronoun()} wanted to answer at once."
    )


def reach_obstacle(world: World, obstacle: Obstacle) -> None:
    ent = world.get("obstacle")
    ent.meters["stuck"] += 1
    world.say(
        f"But at the bend in the trail, {obstacle.the} blocked the way. "
        f"It was {obstacle.texture}, and {obstacle.problem}."
    )


def spot_knifer(world: World, hero: Entity, tool: UnsafeTool, guide: Entity) -> None:
    hero.memes["impatience"] += 1
    world.get("tool").meters["grabbed"] += 1
    propagate(world, narrate=False)
    world.say(
        f'"We can chop through it!" {hero.id} said. {hero.pronoun().capitalize()} '
        f"pointed to {tool.phrase} peeking from {guide.pronoun('possessive')} satchel. "
        f'"That little knifer could do it."'
    )


def warn(world: World, helper: Entity, hero: Entity, tool: UnsafeTool, obstacle: Obstacle, method: Method) -> None:
    pred = predict_transform(world, method.id)
    world.facts["predicted_opens"] = pred["opens"]
    helper.memes["caution"] += 1
    extra = ""
    if helper.memes["caution"] >= 6:
        extra = f" {helper.pronoun().capitalize()} kept {helper.pronoun('possessive')} voice soft but very firm."
    world.say(
        f'{helper.id} caught {hero.id}\'s sleeve. "{tool.warning}. '
        f"{obstacle.The} does not need a slash. It needs to change first.{extra}\""
    )


def guide_hint(world: World, guide: Entity, obstacle: Obstacle, method: Method) -> None:
    world.say(
        f'{guide.id} nodded. "{guide.attrs["style"]} is better than force," '
        f'{guide.pronoun()} said. "{obstacle.The} opens when {obstacle.opens_when}. '
        f"Let us try {method.phrase}." 
    )


def back_down(world: World, hero: Entity, tool: UnsafeTool) -> None:
    hero.memes["impatience"] = 0.0
    hero.memes["trust"] += 1
    world.get("tool").meters["grabbed"] = 0.0
    world.get("path").meters["danger"] = 0.0
    world.say(
        f"{hero.id} looked at the knifer, then at the blocked path, and took a slow breath. "
        f"{hero.pronoun().capitalize()} let the idea go."
    )


def transform(world: World, hero: Entity, helper: Entity, obstacle: Obstacle, method: Method) -> None:
    ent = world.get("obstacle")
    ent.meters["soft"] += 1
    ent.meters["transformed"] += 1
    hero.memes["patience"] += 1
    helper.memes["pride"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Together they {method.action}. At first nothing happened. Then {method.result}, "
        f"and {obstacle.the} began to change."
    )
    world.say(
        f"In a little while, {obstacle.the} had turned into {obstacle.transformed_into}."
    )


def pass_through(world: World, hero: Entity, helper: Entity, quest: Quest) -> None:
    hero.memes["joy"] += 1
    helper.memes["joy"] += 1
    world.say(
        f"The path opened at last. {hero.id} and {helper.id} hurried through and reached "
        f"{quest.goal_place}."
    )
    world.say(
        f"There, they found {quest.goal}. {quest.send_off}"
    )


def learned_end(world: World, hero: Entity, helper: Entity, guide: Entity) -> None:
    hero.memes["pride"] += 1
    hero.memes["lesson"] += 1
    helper.memes["lesson"] += 1
    world.say(
        f'{guide.id} gave {hero.id} a gentle pat on the shoulder. "That was true adventuring," '
        f'{guide.pronoun()} said. "You solved the problem by understanding it."'
    )
    world.say(
        f"{hero.id} grinned at {helper.id}. The quick spark in {hero.pronoun('possessive')} temperament "
        f"was still there, but now it had a steady hand beside it."
    )


def tell(
    quest: Quest,
    obstacle: Obstacle,
    method: Method,
    tool: UnsafeTool,
    guide_cfg: Guide,
    hero_name: str = "Nia",
    hero_gender: str = "girl",
    helper_name: str = "Toma",
    helper_gender: str = "boy",
    parent_type: str = "mother",
    helper_trait: str = "patient",
    temperament: str = "fiery",
    trust: int = 7,
    pet: str = "",
) -> World:
    world = World()
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_gender,
        role="hero",
        traits=["brave"],
        attrs={"temperament": temperament},
    ))
    helper = world.add(Entity(
        id=helper_name,
        kind="character",
        type=helper_gender,
        role="helper",
        traits=[helper_trait],
        attrs={"pet": pet},
    ))
    guide = world.add(Entity(
        id="Guide",
        kind="character",
        type=parent_type,
        role="guide",
        label=guide_cfg.title,
        attrs={"title": guide_cfg.title, "style": guide_cfg.style},
    ))
    path = world.add(Entity(id="path", type="path", label="the path"))
    obstacle_ent = world.add(Entity(
        id="obstacle",
        type="obstacle",
        label=obstacle.label,
        obstacle_kind=obstacle.kind,
    ))
    tool_ent = world.add(Entity(
        id="tool",
        type="tool",
        label=tool.label,
        dangerous=tool.dangerous,
        tool_kind=tool.id,
    ))
    goal = world.add(Entity(id="goal", type="goal", label=quest.goal, goal_kind=quest.id))

    hero.memes["bold"] = BOLD_INIT
    helper.memes["caution"] = calm_score(helper_trait)
    helper.memes["trust"] = float(trust)
    path.meters["danger"] = 0.0
    path.meters["open"] = 0.0
    obstacle_ent.meters["stuck"] = 0.0
    obstacle_ent.meters["soft"] = 0.0
    obstacle_ent.meters["open"] = 0.0
    obstacle_ent.meters["transformed"] = 0.0
    tool_ent.meters["grabbed"] = 0.0

    introduce(world, hero, helper, quest, guide)
    set_temperament(world, hero)
    world.para()
    reach_obstacle(world, obstacle)
    spot_knifer(world, hero, tool, guide)
    warn(world, helper, hero, tool, obstacle, method)
    guide_hint(world, guide, obstacle, method)

    if not guide_can_redirect(helper_trait, trust):
        raise StoryError("(No story: the helper is not calm enough in this setup to steer the hero toward the safer plan.)")

    back_down(world, hero, tool)
    world.para()
    transform(world, hero, helper, obstacle, method)
    pass_through(world, hero, helper, quest)
    if pet:
        world.say(f"Even {pet} trotted after them through the newly opened way.")
    world.para()
    learned_end(world, hero, helper, guide)

    world.facts.update(
        hero=hero,
        helper=helper,
        guide=guide,
        quest=quest,
        obstacle_cfg=obstacle,
        obstacle=obstacle_ent,
        tool_cfg=tool,
        tool=tool_ent,
        method=method,
        goal=goal,
        pet=pet,
        outcome="opened" if obstacle_ent.meters["open"] >= THRESHOLD else "stuck",
        transformed=obstacle_ent.meters["transformed"] >= THRESHOLD,
        path_open=path.meters["open"] >= THRESHOLD,
        trusted=hero.memes["trust"] >= THRESHOLD,
    )
    return world


QUESTS = {
    "maple_cave": Quest(
        id="maple_cave",
        scene="a small leaf-map adventure through the whispering garden",
        opening="In their pockets they carried a hand-drawn map with a red star on the last turn.",
        goal="a tin box of moonberry biscuits",
        goal_place="the maple cave",
        send_off="They sat on the warm stone step, shared the biscuits, and looked back proudly at the trail they had solved.",
        tags={"adventure", "map"},
    ),
    "lantern_hill": Quest(
        id="lantern_hill",
        scene="a winding adventure up Lantern Hill",
        opening="Above them, little glass lanterns bobbed on strings and clicked in the breeze.",
        goal="the hilltop bell that rang when a good pathfinder arrived",
        goal_place="the hilltop arch",
        send_off="When they touched the bell rope, the hill gave a bright, happy ring over the whole garden.",
        tags={"adventure", "lantern"},
    ),
    "reed_fort": Quest(
        id="reed_fort",
        scene="a brave march toward the reed fort by the pond",
        opening="Their map showed tiny fish, three stepping stones, and a secret mark beside the reeds.",
        goal="a blue ribbon hidden in the fort tower",
        goal_place="the reed fort",
        send_off="They tied the ribbon to a stick and let it flutter like a flag over their tiny victory.",
        tags={"adventure", "pond"},
    ),
}

OBSTACLES = {
    "wax_gate": Obstacle(
        id="wax_gate",
        label="wax gate",
        the="the wax gate",
        texture="thick and droopy with yellow ridges",
        problem="it had sagged shut across the path like a sleepy wall",
        opens_when="warm water softens the old wax",
        transformed_into="a soft, curled doorway with shiny edges",
        kind="wax",
        stubbornness=2,
        tags={"wax", "transformation"},
    ),
    "vine_knot": Obstacle(
        id="vine_knot",
        label="vine knot",
        the="the vine knot",
        texture="dry, twisted, and prickly",
        problem="its thirsty stems had wrapped themselves into a hard knot",
        opens_when="water wakes the vines and helps them loosen",
        transformed_into="green, loose loops with a doorway in the middle",
        kind="vine",
        stubbornness=2,
        tags={"vine", "transformation"},
    ),
    "ice_lock": Obstacle(
        id="ice_lock",
        label="ice lock",
        the="the ice lock",
        texture="clear and glittering like a frozen window",
        problem="it had sealed the trail in a cold, glassy sheet",
        opens_when="gentle warmth thaws the ice",
        transformed_into="silver puddles and a dripping gap in the rocks",
        kind="ice",
        stubbornness=2,
        tags={"ice", "transformation"},
    ),
}

METHODS = {
    "warm_water": Method(
        id="warm_water",
        label="warm water",
        phrase="the flask of warm water",
        changes="softening",
        suits={"wax"},
        action="poured the warm water in a careful silver line across the gate",
        result="the hard yellow ridges gave a little splutter and began to slump",
        qa_text="They used warm water to soften the wax until it curled open",
        sense=3,
        tags={"warm_water", "wax"},
    ),
    "watering_can": Method(
        id="watering_can",
        label="watering can",
        phrase="the little watering can",
        changes="loosening",
        suits={"vine"},
        action="tipped the watering can slowly over the thirsty knot",
        result="the dry stems drank with a tiny splutter and relaxed their twist",
        qa_text="They watered the dry vines until the knot loosened into loops",
        sense=3,
        tags={"water", "vines"},
    ),
    "sun_lantern": Method(
        id="sun_lantern",
        label="sun lantern",
        phrase="the sun lantern from the satchel",
        changes="thawing",
        suits={"ice"},
        action="held the warm sun lantern near the lock and waited together",
        result="the frost gave a faint splutter and clear drops ran down the ice",
        qa_text="They used the sun lantern's warmth to thaw the ice",
        sense=3,
        tags={"lantern", "ice"},
    ),
    "push_harder": Method(
        id="push_harder",
        label="pushing",
        phrase="their shoulders and all their pushing",
        changes="none",
        suits=set(),
        action="leaned with all their might against the obstacle",
        result="nothing but sore hands came of it",
        qa_text="They only pushed, which did not match the obstacle at all",
        sense=1,
        tags={"force"},
    ),
}

UNSAFE_TOOLS = {
    "garden_knifer": UnsafeTool(
        id="garden_knifer",
        label="knifer",
        phrase="a little garden knifer",
        where="in the guide's satchel",
        warning="Knifer blades are for grown-up hands, and slashing at a puzzle can hurt someone",
        dangerous=True,
        tags={"knife", "safety"},
    ),
}

GUIDES = {
    "ranger_mina": Guide(
        id="ranger_mina",
        title="Ranger Mina",
        style="understanding",
        tags={"guide"},
    ),
    "uncle_jo": Guide(
        id="uncle_jo",
        title="Uncle Jo",
        style="thinking",
        tags={"guide"},
    ),
}

GIRL_NAMES = ["Nia", "Lila", "Ava", "Mira", "Zoe", "Tess", "Runa", "Ivy"]
BOY_NAMES = ["Toma", "Finn", "Eli", "Milo", "Ben", "Noah", "Leo", "Pax"]
TRAITS = ["patient", "careful", "steady", "thoughtful", "curious", "gentle"]
TEMPERAMENTS = ["fiery", "bouncy"]
PETS = ["the duckling", "the little dog", "the kitten", ""]


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for quest_id in QUESTS:
        for obstacle_id, obstacle in OBSTACLES.items():
            for method_id, method in METHODS.items():
                for guide_id in GUIDES:
                    if method_fits(obstacle, method) and method.sense >= SENSE_MIN:
                        combos.append((quest_id, obstacle_id, method_id, guide_id))
    return combos


@dataclass
class StoryParams:
    quest: str
    obstacle: str
    method: str
    tool: str
    guide: str
    hero_name: str
    hero_gender: str
    helper_name: str
    helper_gender: str
    helper_trait: str
    guide_type: str
    temperament: str = "fiery"
    trust: int = 7
    pet: str = ""
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
    "knife": [(
        "What is a garden knife or knifer used for?",
        "A garden knife is a sharp cutting tool grown-ups may use for plants or string. Children should not grab one because sharp tools can slip and hurt people."
    )],
    "safety": [(
        "Why is cutting not always the best way to solve a problem?",
        "Cutting is not always best because some problems are not really about slicing. If you understand what the material needs, you can often solve the problem more safely."
    )],
    "wax": [(
        "What happens to wax when it gets warm?",
        "Warm wax gets softer and bendier than cold wax. That is why gentle heat or warm water can help it change shape."
    )],
    "vines": [(
        "Why can dry vines loosen after water?",
        "Dry vines can feel stiff, but water can make them less tight and easier to bend. The change is gentle, so the shape can open instead of snapping."
    )],
    "ice": [(
        "What happens to ice when it warms up?",
        "Ice melts when it gets warm enough. It changes from a hard solid into water."
    )],
    "lantern": [(
        "What is a lantern for?",
        "A lantern gives light, and some lanterns also give a little warmth. On an adventure, it helps people see and sometimes solve small problems carefully."
    )],
    "adventure": [(
        "What makes something an adventure?",
        "An adventure is a journey with a goal, a challenge, and a change along the way. The people in it have to be brave and think about what to do next."
    )],
    "transformation": [(
        "What is a transformation?",
        "A transformation is when something changes into a different state or shape. In stories, that change often helps solve the main problem."
    )],
}
KNOWLEDGE_ORDER = ["adventure", "knife", "safety", "wax", "vines", "ice", "lantern", "transformation"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, helper = f["hero"], f["helper"]
    obstacle, method, quest = f["obstacle_cfg"], f["method"], f["quest"]
    return [
        f'Write an adventure story for a 3-to-5-year-old that includes the words "splutter", "knifer", and "temperament". The problem should be a blocked path and the solution should come from transformation.',
        f"Tell a gentle adventure where {hero.id} wants to use a knifer to get past {obstacle.the}, but {helper.id} helps {hero.pronoun('object')} solve the problem by changing the obstacle instead.",
        f"Write a small quest story leading to {quest.goal_place}, where {obstacle.the} opens because of {method.label} and the hero learns to guide a quick temperament with patience."
    ]


def pair_noun(hero: Entity, helper: Entity) -> str:
    if hero.type == "girl" and helper.type == "girl":
        return "two young explorers"
    if hero.type == "boy" and helper.type == "boy":
        return "two young explorers"
    return "two young explorers"


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero, helper, guide = f["hero"], f["helper"], f["guide"]
    obstacle, method, tool, quest = f["obstacle_cfg"], f["method"], f["tool_cfg"], f["quest"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair_noun(hero, helper)}, {hero.id} and {helper.id}, and {guide.attrs['title']} guiding them on a quest. They were trying to reach {quest.goal_place}."
        ),
        (
            "What problem did they find on the trail?",
            f"They found {obstacle.the} blocking the path, so they could not reach their goal right away. The obstacle turned the adventure into a puzzle that needed thinking, not rushing."
        ),
        (
            f"Why did {hero.id} talk about the knifer?",
            f"{hero.id} wanted a fast answer because {hero.pronoun('possessive')} temperament was quick and eager. {hero.pronoun().capitalize()} thought the knifer could chop through the trouble in one move."
        ),
        (
            f"Why did {helper.id} and {guide.attrs['title']} say no to the knifer?",
            f"They said no because the knifer was a sharp grown-up tool and slashing would be unsafe. They also understood that {obstacle.the} would open better if it changed first instead of being cut."
        ),
        (
            "How did they solve the problem?",
            f"{method.qa_text}. The plan worked because it matched what {obstacle.the} needed in order to change."
        ),
        (
            "What transformation happened?",
            f"{obstacle.The} changed into {obstacle.transformed_into}, and the path opened. That transformation is what turned the blocked trail back into part of the adventure."
        ),
        (
            f"What did {hero.id} learn at the end?",
            f"{hero.id} learned that a quick temperament can still listen and think. The best adventure answer was the one that understood the obstacle instead of fighting it."
        ),
    ]
    pet = f.get("pet", "")
    if pet:
        qa.append((
            "Who came along after the path opened?",
            f"{pet.capitalize()} came along after them through the newly opened way. That small ending image shows how calm and safe the trail had become."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"adventure", "transformation"} | set(f["tool_cfg"].tags)
    obstacle = f["obstacle_cfg"]
    method = f["method"]
    if obstacle.kind == "wax":
        tags.add("wax")
    if obstacle.kind == "vine":
        tags.add("vines")
    if obstacle.kind == "ice":
        tags.add("ice")
    if "lantern" in method.tags:
        tags.add("lantern")
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
        if e.dangerous:
            bits.append("dangerous=True")
        if e.obstacle_kind:
            bits.append(f"obstacle_kind={e.obstacle_kind}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        quest="maple_cave",
        obstacle="wax_gate",
        method="warm_water",
        tool="garden_knifer",
        guide="ranger_mina",
        hero_name="Nia",
        hero_gender="girl",
        helper_name="Toma",
        helper_gender="boy",
        helper_trait="patient",
        guide_type="mother",
        temperament="fiery",
        trust=7,
        pet="the duckling",
    ),
    StoryParams(
        quest="lantern_hill",
        obstacle="ice_lock",
        method="sun_lantern",
        tool="garden_knifer",
        guide="uncle_jo",
        hero_name="Finn",
        hero_gender="boy",
        helper_name="Mira",
        helper_gender="girl",
        helper_trait="steady",
        guide_type="father",
        temperament="bouncy",
        trust=6,
        pet="",
    ),
    StoryParams(
        quest="reed_fort",
        obstacle="vine_knot",
        method="watering_can",
        tool="garden_knifer",
        guide="ranger_mina",
        hero_name="Ivy",
        hero_gender="girl",
        helper_name="Leo",
        helper_gender="boy",
        helper_trait="careful",
        guide_type="mother",
        temperament="fiery",
        trust=8,
        pet="the kitten",
    ),
]


def explain_rejection(obstacle: Obstacle, method: Method) -> str:
    if method.sense < SENSE_MIN:
        return (f"(No story: '{method.id}' is known to the world, but it is not a sensible "
                f"problem-solving method here. Pick a method that safely transforms {obstacle.the}.)")
    return (f"(No story: {method.label} does not fit {obstacle.the}. This obstacle opens when "
            f"{obstacle.opens_when}, so the method must match that change.)")


ASP_RULES = r"""
sensible_method(M) :- method(M), sense(M, S), sense_min(Min), S >= Min.
fits(O, M) :- obstacle(O), method(M), obstacle_kind(O, K), suits(M, K).
valid(Q, O, M, G) :- quest(Q), obstacle(O), method(M), guide(G), fits(O, M), sensible_method(M).

calm_helper(T) :- helper_trait(T), is_calm(T).
bonus(1) :- trust(T), T >= 6.
bonus(0) :- trust(T), T < 6.
redirects :- calm_helper(T), bonus(B), calm_score(T, S), S + B > 5.

opens :- chosen_obstacle(O), chosen_method(M), fits(O, M).
outcome(opened) :- redirects, opens.
outcome(stuck) :- not redirects.
outcome(stuck) :- redirects, not opens.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for qid in QUESTS:
        lines.append(asp.fact("quest", qid))
    for oid, obstacle in OBSTACLES.items():
        lines.append(asp.fact("obstacle", oid))
        lines.append(asp.fact("obstacle_kind", oid, obstacle.kind))
    for mid, method in METHODS.items():
        lines.append(asp.fact("method", mid))
        lines.append(asp.fact("sense", mid, method.sense))
        for suit in sorted(method.suits):
            lines.append(asp.fact("suits", mid, suit))
    for gid in GUIDES:
        lines.append(asp.fact("guide", gid))
    for trait in sorted(TRAITS):
        lines.append(asp.fact("helper_trait", trait))
        lines.append(asp.fact("calm_score", trait, int(calm_score(trait))))
        if trait in CALM_TRAITS:
            lines.append(asp.fact("is_calm", trait))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def outcome_of(params: StoryParams) -> str:
    if not guide_can_redirect(params.helper_trait, params.trust):
        return "stuck"
    return "opened" if method_fits(OBSTACLES[params.obstacle], METHODS[params.method]) else "stuck"


def asp_outcome(params: StoryParams) -> str:
    import asp
    scenario = "\n".join([
        asp.fact("chosen_obstacle", params.obstacle),
        asp.fact("chosen_method", params.method),
        asp.fact("trust", params.trust),
        asp.fact("helper_trait", params.helper_trait),
    ])
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
        if asp_set - py_set:
            print("  only in clingo:", sorted(asp_set - py_set))
        if py_set - asp_set:
            print("  only in python:", sorted(py_set - asp_set))

    cases = list(CURATED)
    parser = build_parser()
    for s in range(40):
        try:
            p = resolve_params(parser.parse_args([]), random.Random(s))
        except StoryError:
            continue
        cases.append(p)
    bad = 0
    for p in cases:
        if asp_outcome(p) != outcome_of(p):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("(Smoke test failed: empty story.)")
        emit(smoke, trace=False, qa=False, header="")
        print("OK: smoke test generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Adventure storyworld: a blocked path, a quick temperament, and a safer transformation-based solution."
    )
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--obstacle", choices=OBSTACLES)
    ap.add_argument("--method", choices=METHODS)
    ap.add_argument("--tool", choices=UNSAFE_TOOLS)
    ap.add_argument("--guide", choices=GUIDES)
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
    ap.add_argument("--guide-type", choices=["mother", "father"])
    ap.add_argument("--temperament", choices=TEMPERAMENTS)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.obstacle and args.method:
        obstacle = OBSTACLES[args.obstacle]
        method = METHODS[args.method]
        if not (method_fits(obstacle, method) and method.sense >= SENSE_MIN):
            raise StoryError(explain_rejection(obstacle, method))

    combos = [
        c for c in valid_combos()
        if (args.quest is None or c[0] == args.quest)
        and (args.obstacle is None or c[1] == args.obstacle)
        and (args.method is None or c[2] == args.method)
        and (args.guide is None or c[3] == args.guide)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    quest_id, obstacle_id, method_id, guide_id = rng.choice(sorted(combos))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or rng.choice(["girl", "boy"])
    hero_name = pick_name(rng, hero_gender)
    helper_name = pick_name(rng, helper_gender, avoid=hero_name)
    helper_trait = rng.choice(TRAITS)
    trust = rng.randint(6, 10)
    tool = args.tool or "garden_knifer"
    temperament = args.temperament or rng.choice(TEMPERAMENTS)
    guide_type = args.guide_type or rng.choice(["mother", "father"])
    pet = rng.choice(PETS)
    return StoryParams(
        quest=quest_id,
        obstacle=obstacle_id,
        method=method_id,
        tool=tool,
        guide=guide_id,
        hero_name=hero_name,
        hero_gender=hero_gender,
        helper_name=helper_name,
        helper_gender=helper_gender,
        helper_trait=helper_trait,
        guide_type=guide_type,
        temperament=temperament,
        trust=trust,
        pet=pet,
    )


def generate(params: StoryParams) -> StorySample:
    if params.quest not in QUESTS:
        raise StoryError(f"(Invalid quest: {params.quest})")
    if params.obstacle not in OBSTACLES:
        raise StoryError(f"(Invalid obstacle: {params.obstacle})")
    if params.method not in METHODS:
        raise StoryError(f"(Invalid method: {params.method})")
    if params.tool not in UNSAFE_TOOLS:
        raise StoryError(f"(Invalid tool: {params.tool})")
    if params.guide not in GUIDES:
        raise StoryError(f"(Invalid guide: {params.guide})")
    if params.helper_trait not in TRAITS:
        raise StoryError(f"(Invalid helper trait: {params.helper_trait})")
    if params.hero_gender not in {"girl", "boy"} or params.helper_gender not in {"girl", "boy"}:
        raise StoryError("(Invalid gender choice.)")
    if params.guide_type not in {"mother", "father"}:
        raise StoryError("(Invalid guide type.)")
    if params.temperament not in TEMPERAMENTS:
        raise StoryError("(Invalid temperament choice.)")
    obstacle = OBSTACLES[params.obstacle]
    method = METHODS[params.method]
    if not (method_fits(obstacle, method) and method.sense >= SENSE_MIN):
        raise StoryError(explain_rejection(obstacle, method))

    world = tell(
        quest=QUESTS[params.quest],
        obstacle=obstacle,
        method=method,
        tool=UNSAFE_TOOLS[params.tool],
        guide_cfg=GUIDES[params.guide],
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        helper_name=params.helper_name,
        helper_gender=params.helper_gender,
        parent_type=params.guide_type,
        helper_trait=params.helper_trait,
        temperament=params.temperament,
        trust=params.trust,
        pet=params.pet,
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
        print(f"{len(combos)} compatible (quest, obstacle, method, guide) combos:\n")
        for quest_id, obstacle_id, method_id, guide_id in combos:
            print(f"  {quest_id:12} {obstacle_id:10} {method_id:12} {guide_id}")
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
            header = f"### {p.hero_name} & {p.helper_name}: {p.obstacle} via {p.method} ({p.quest})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
