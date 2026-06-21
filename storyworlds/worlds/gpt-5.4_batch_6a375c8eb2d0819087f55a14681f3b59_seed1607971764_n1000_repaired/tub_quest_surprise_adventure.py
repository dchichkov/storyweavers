#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/tub_quest_surprise_adventure.py
==========================================================

A standalone story world about a child who turns wash time into a tiny adventure.
The hero sets out on a quest in a tub to rescue a small floating friend or find
a treasure, but a problem appears: something needed for the quest is out of
reach, sinking, or drifting away. A caring grown-up helps in a sensible way, and
the ending includes a gentle surprise that proves the quest changed into happy
bath time instead of frustration.

The world model tracks simple physical meters (floating, drifting, wet reach,
bubbles, found) and emotional memes (eager, worry, relief, pride, surprise).
State drives prose, Q&A, and the ASP twin.

Run it
------
    python storyworlds/worlds/gpt-5.4/tub_quest_surprise_adventure.py
    python storyworlds/worlds/gpt-5.4/tub_quest_surprise_adventure.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/tub_quest_surprise_adventure.py --all
    python storyworlds/worlds/gpt-5.4/tub_quest_surprise_adventure.py --trace --seed 9
    python storyworlds/worlds/gpt-5.4/tub_quest_surprise_adventure.py --verify
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
    floats: bool = False
    can_scoop: bool = False
    can_reach: bool = False
    gives_bubbles: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)
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
    sea_name: str
    launch_line: str
    goal_text: str
    cheer: str
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
class Goal:
    id: str
    label: str
    phrase: str
    drifts: bool
    sinks_when_splashed: bool
    treasure: bool
    helper_need: str
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
class Trouble:
    id: str
    label: str
    risk_text: str
    method_blocked: str
    needs_tool: str
    solvable_by: set[str] = field(default_factory=set)
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
class Tool:
    id: str
    label: str
    phrase: str
    can_scoop: bool = False
    can_reach: bool = False
    gives_bubbles: bool = False
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
class Surprise:
    id: str
    label: str
    reveal_text: str
    ending_image: str
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


def _r_drift(world: World) -> list[str]:
    out: list[str] = []
    if not world.facts.get("started_quest"):
        return out
    goal = world.get("goal")
    trouble = world.facts.get("trouble")
    if not goal.floats or trouble != "drift_away":
        return out
    sig = ("drift", goal.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    goal.meters["drifting"] += 1
    world.get("hero").memes["worry"] += 1
    out.append("__drift__")
    return out


def _r_sink(world: World) -> list[str]:
    out: list[str] = []
    if not world.facts.get("splash_happened"):
        return out
    goal = world.get("goal")
    trouble = world.facts.get("trouble")
    if trouble != "sudden_sink" or not world.facts.get("goal_cfg").sinks_when_splashed:
        return out
    sig = ("sink", goal.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    goal.meters["sunken"] += 1
    goal.meters["floating"] = 0.0
    world.get("hero").memes["worry"] += 1
    out.append("__sink__")
    return out


def _r_out_of_reach(world: World) -> list[str]:
    out: list[str] = []
    if not world.facts.get("started_quest"):
        return out
    trouble = world.facts.get("trouble")
    if trouble != "far_side":
        return out
    sig = ("far", "goal")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("goal").meters["far"] += 1
    world.get("hero").memes["worry"] += 1
    out.append("__far__")
    return out


CAUSAL_RULES = [
    Rule(name="drift", tag="physical", apply=_r_drift),
    Rule(name="sink", tag="physical", apply=_r_sink),
    Rule(name="far", tag="physical", apply=_r_out_of_reach),
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


def goal_at_risk(goal: Goal, trouble: Trouble) -> bool:
    if trouble.id == "drift_away":
        return goal.drifts
    if trouble.id == "sudden_sink":
        return goal.sinks_when_splashed
    if trouble.id == "far_side":
        return True
    return False


def tool_works(tool: Tool, trouble: Trouble) -> bool:
    if trouble.needs_tool == "scoop":
        return tool.can_scoop
    if trouble.needs_tool == "reach":
        return tool.can_reach
    return False


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for quest_id in QUESTS:
        for goal_id, goal in GOALS.items():
            for trouble_id, trouble in TROUBLES.items():
                if not goal_at_risk(goal, trouble):
                    continue
                for tool_id, tool in TOOLS.items():
                    if tool_works(tool, trouble):
                        combos.append((quest_id, goal_id, trouble_id, tool_id))
    return combos


def predict_resolution(goal: Goal, trouble: Trouble, tool: Tool) -> dict:
    success = goal_at_risk(goal, trouble) and tool_works(tool, trouble)
    return {
        "success": success,
        "need": trouble.needs_tool,
        "risk": trouble.risk_text,
    }


def introduce(world: World, hero: Entity, parent: Entity) -> None:
    world.say(
        f"After supper, {hero.id}'s {parent.label_word} filled the tub with warm water."
    )
    world.say(
        f"{hero.id} climbed in and watched the shiny water make the whole bathroom feel like a tiny harbor."
    )


def launch_quest(world: World, hero: Entity, quest: Quest, goal_ent: Entity, tool_ent: Entity) -> None:
    hero.memes["eager"] += 1
    world.facts["started_quest"] = True
    world.say(
        f'"{quest.launch_line}" {hero.id} said. In {hero.pronoun("possessive")} mind, the tub became {quest.sea_name}.'
    )
    world.say(
        f"{goal_ent.label.capitalize()} bobbed nearby, and {tool_ent.phrase} waited like trusty gear for the quest."
    )


def name_goal(world: World, quest: Quest, goal: Goal) -> None:
    world.say(
        f"The mission was clear: {quest.goal_text} {goal.phrase}."
    )


def trouble_appears(world: World, hero: Entity, goal_ent: Entity, trouble: Trouble) -> None:
    world.para()
    if trouble.id == "drift_away":
        propagate(world, narrate=False)
        world.say(
            f"But then {goal_ent.label} began to drift toward the far side of the tub. {trouble.risk_text}"
        )
    elif trouble.id == "sudden_sink":
        world.facts["splash_happened"] = True
        propagate(world, narrate=False)
        world.say(
            f"But a quick splash rolled across the water, and {goal_ent.label} dipped low. {trouble.risk_text}"
        )
    elif trouble.id == "far_side":
        propagate(world, narrate=False)
        world.say(
            f"But the tub was wider than it had looked at first, and {goal_ent.label} was resting on the far side. {trouble.risk_text}"
        )
    else:
        raise StoryError("(Unknown trouble.)")
    world.say(f"{hero.id} sat up straight. This part of the adventure felt real.")


def worry_and_call(world: World, hero: Entity, parent: Entity, trouble: Trouble, goal: Goal) -> None:
    world.say(
        f'"Oh no," {hero.id} said. "{trouble.method_blocked}"'
    )
    world.say(
        f"{hero.id}'s {parent.label_word} came closer when {hero.pronoun()} called. {hero.pronoun().capitalize()} wanted to finish the quest without losing {goal.phrase}."
    )


def help_offer(world: World, parent: Entity, tool: Tool, trouble: Trouble) -> None:
    pred = predict_resolution(world.facts["goal_cfg"], TROUBLES[world.facts["trouble"]], tool)
    world.facts["predicted_success"] = pred["success"]
    world.facts["predicted_need"] = pred["need"]
    if not pred["success"]:
        raise StoryError("(The chosen tool cannot solve this tub problem.)")
    world.say(
        f'"Let\'s try {tool.phrase}," {parent.label_word} said. "It can help with that."'
    )


def solve(world: World, hero: Entity, parent: Entity, goal_ent: Entity, tool: Tool, trouble: Trouble) -> None:
    hero.memes["relief"] += 1
    hero.memes["pride"] += 1
    goal_ent.meters["found"] += 1
    goal_ent.meters["safe"] += 1
    if trouble.id == "drift_away":
        goal_ent.meters["drifting"] = 0.0
        world.say(
            f"Together they used {tool.phrase} to guide {goal_ent.label} back through the warm water."
        )
    elif trouble.id == "sudden_sink":
        goal_ent.meters["sunken"] = 0.0
        goal_ent.meters["floating"] += 1
        world.say(
            f"Together they used {tool.phrase} to scoop gently under {goal_ent.label} and lift it up before it could disappear under the bubbles."
        )
    elif trouble.id == "far_side":
        goal_ent.meters["far"] = 0.0
        world.say(
            f"Together they stretched out {tool.phrase} and reached across the tub until {goal_ent.label} slid back within easy reach."
        )
    else:
        raise StoryError("(Unknown trouble in solve.)")
    world.say(
        f'"{world.facts["quest"].cheer}" {hero.id} shouted, splashing just a little this time.'
    )


def reveal_surprise(world: World, hero: Entity, parent: Entity, surprise: Surprise, goal: Goal, tool: Tool) -> None:
    world.para()
    hero.memes["surprise"] += 1
    if tool.gives_bubbles:
        world.get("water").meters["bubbles"] += 1
    world.say(
        f"Then {parent.label_word} smiled and showed the surprise: {surprise.reveal_text}"
    )
    world.say(
        f"{surprise.ending_image} {hero.id} hugged {goal.label} and looked at the tub as if it were the best sea in the world."
    )


def tell(
    quest: Quest,
    goal: Goal,
    trouble: Trouble,
    tool: Tool,
    surprise: Surprise,
    hero_name: str = "Milo",
    hero_gender: str = "boy",
    parent_type: str = "mother",
    helper_name: str = "Parent",
) -> World:
    world = World()
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender, role="hero"))
    parent = world.add(Entity(id=helper_name, kind="character", type=parent_type, role="parent", label="the parent"))
    water = world.add(Entity(id="water", type="water", label="water"))
    goal_ent = world.add(
        Entity(
            id="goal",
            type="goal",
            label=goal.label,
            floats=goal.drifts or goal.treasure,
            attrs={"treasure": goal.treasure},
        )
    )
    if goal.drifts:
        goal_ent.meters["floating"] = 1.0
    tool_ent = world.add(
        Entity(
            id="tool",
            type="tool",
            label=tool.label,
            can_scoop=tool.can_scoop,
            can_reach=tool.can_reach,
            gives_bubbles=tool.gives_bubbles,
        )
    )

    world.facts.update(
        quest=quest,
        goal_cfg=goal,
        trouble=trouble.id,
        trouble_cfg=trouble,
        tool_cfg=tool,
        surprise=surprise,
        started_quest=False,
        splash_happened=False,
    )

    introduce(world, hero, parent)
    launch_quest(world, hero, quest, goal_ent, tool_ent)
    name_goal(world, quest, goal)
    trouble_appears(world, hero, goal_ent, trouble)
    worry_and_call(world, hero, parent, trouble, goal)
    help_offer(world, parent, tool, trouble)
    world.para()
    solve(world, hero, parent, goal_ent, tool, trouble)
    reveal_surprise(world, hero, parent, surprise, goal, tool)

    world.facts.update(
        hero=hero,
        parent=parent,
        goal=goal_ent,
        tool=tool_ent,
        solved=goal_ent.meters["found"] >= THRESHOLD,
    )
    return world


QUESTS = {
    "captain": Quest(
        id="captain",
        sea_name="the Silver Bubble Sea",
        launch_line="Captain Splash is setting out on a brave quest",
        goal_text="to rescue",
        cheer="Quest complete",
        tags={"quest", "adventure"},
    ),
    "explorer": Quest(
        id="explorer",
        sea_name="the Foamy Explorer Bay",
        launch_line="Explorer waves away, because a bath-time quest has begun",
        goal_text="to find",
        cheer="I found it",
        tags={"quest", "adventure"},
    ),
    "rescuer": Quest(
        id="rescuer",
        sea_name="the Deep Cozy Harbor",
        launch_line="Tonight I am the rescuer of the tub",
        goal_text="to bring home",
        cheer="Safe at last",
        tags={"quest", "adventure"},
    ),
}

GOALS = {
    "duck": Goal(
        id="duck",
        label="little yellow duck",
        phrase="the little yellow duck",
        drifts=True,
        sinks_when_splashed=False,
        treasure=False,
        helper_need="reach",
        tags={"duck", "float"},
    ),
    "boat": Goal(
        id="boat",
        label="tiny red boat",
        phrase="the tiny red boat",
        drifts=True,
        sinks_when_splashed=False,
        treasure=False,
        helper_need="reach",
        tags={"boat", "float"},
    ),
    "shell": Goal(
        id="shell",
        label="shiny shell",
        phrase="the shiny shell",
        drifts=False,
        sinks_when_splashed=True,
        treasure=True,
        helper_need="scoop",
        tags={"shell", "treasure"},
    ),
    "star_coin": Goal(
        id="star_coin",
        label="gold star coin",
        phrase="the gold star coin",
        drifts=False,
        sinks_when_splashed=True,
        treasure=True,
        helper_need="scoop",
        tags={"treasure", "coin"},
    ),
}

TROUBLES = {
    "drift_away": Trouble(
        id="drift_away",
        label="drifting away",
        risk_text="The water kept nudging it farther from small fingers.",
        method_blocked="It's sailing away",
        needs_tool="reach",
        solvable_by={"ladle", "long_spoon"},
        tags={"drift"},
    ),
    "sudden_sink": Trouble(
        id="sudden_sink",
        label="sudden sink",
        risk_text="For a moment it looked as if the treasure might vanish below the water.",
        method_blocked="It's sinking and I can't grab it softly",
        needs_tool="scoop",
        solvable_by={"cup", "ladle"},
        tags={"sink"},
    ),
    "far_side": Trouble(
        id="far_side",
        label="far side",
        risk_text="It was safe, but it was still too far away to finish the mission alone.",
        method_blocked="It's too far across the tub",
        needs_tool="reach",
        solvable_by={"ladle", "long_spoon"},
        tags={"reach"},
    ),
}

TOOLS = {
    "cup": Tool(
        id="cup",
        label="small cup",
        phrase="a small cup",
        can_scoop=True,
        can_reach=False,
        gives_bubbles=False,
        tags={"cup"},
    ),
    "ladle": Tool(
        id="ladle",
        label="little ladle",
        phrase="the little ladle",
        can_scoop=True,
        can_reach=True,
        gives_bubbles=False,
        tags={"ladle"},
    ),
    "long_spoon": Tool(
        id="long_spoon",
        label="long spoon",
        phrase="the long spoon",
        can_scoop=False,
        can_reach=True,
        gives_bubbles=False,
        tags={"spoon"},
    ),
    "bubble_cup": Tool(
        id="bubble_cup",
        label="bubble cup",
        phrase="the bubble cup",
        can_scoop=True,
        can_reach=False,
        gives_bubbles=True,
        tags={"cup", "bubbles"},
    ),
}

SURPRISES = {
    "foam_crown": Surprise(
        id="foam_crown",
        label="foam crown",
        reveal_text="a puffy foam crown waiting on the side of the tub",
        ending_image="Soon a wobbly foam crown sat on the captain's head, and silver bubbles glittered on the water.",
        tags={"surprise", "bubbles"},
    ),
    "hidden_sticker": Surprise(
        id="hidden_sticker",
        label="hidden sticker",
        reveal_text="a shiny star sticker tucked under the towel just for the brave explorer",
        ending_image="The star sticker gleamed on the soap bottle like a secret prize from the adventure.",
        tags={"surprise", "sticker"},
    ),
    "extra_boat": Surprise(
        id="extra_boat",
        label="extra boat",
        reveal_text="a second tiny boat that had been waiting behind the soap",
        ending_image="Now two little boats rocked in the tub together, as if the sea had sent a friend at the last minute.",
        tags={"surprise", "boat"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy"]
BOY_NAMES = ["Milo", "Ben", "Leo", "Finn", "Theo", "Max"]


@dataclass
class StoryParams:
    quest: str
    goal: str
    trouble: str
    tool: str
    surprise: str
    name: str
    gender: str
    parent: str
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
    "tub": [
        (
            "What is a tub?",
            "A tub is a big bath basin that holds warm water for washing. Children often call it a bathtub."
        )
    ],
    "duck": [
        (
            "Why does a toy duck float?",
            "A toy duck floats when its shape and the air inside it help the water hold it up. That is why it can bob on top instead of sinking."
        )
    ],
    "boat": [
        (
            "Why can a toy boat float on water?",
            "A toy boat is shaped to spread its weight across the water. That shape helps the water support it."
        )
    ],
    "treasure": [
        (
            "What is treasure in a pretend adventure?",
            "Treasure is something special the explorer wants to find or keep safe. In pretend play, it can be any object that feels important."
        )
    ],
    "bubbles": [
        (
            "What makes bubbles in bath water?",
            "Soap and moving water can trap tiny bits of air and make bubbles. That is why splashing and bubble bath make the tub look foamy."
        )
    ],
    "ladle": [
        (
            "What is a ladle used for?",
            "A ladle is a deep spoon with a handle. It can scoop liquid or gently lift small things."
        )
    ],
    "cup": [
        (
            "How can a cup help pick something up from water?",
            "A cup can scoop under a floating or sinking object and lift it carefully. That makes it gentler than grabbing with fingers."
        )
    ],
    "reach": [
        (
            "Why is a long tool helpful when something is far away?",
            "A long tool lets you reach farther without leaning too much. It helps bring something close safely."
        )
    ],
}
KNOWLEDGE_ORDER = ["tub", "duck", "boat", "treasure", "bubbles", "ladle", "cup", "reach"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    quest = f["quest"]
    goal = f["goal_cfg"]
    trouble = f["trouble_cfg"]
    surprise = f["surprise"]
    return [
        f'Write an adventure story for a 3-to-5-year-old that includes the word "tub" and follows a small quest.',
        f"Tell a bath-time adventure where {hero.id} turns the tub into {quest.sea_name}, faces the problem of {trouble.label}, and finishes the quest with help.",
        f"Write a gentle quest story with a surprise ending where {goal.phrase} is part of the mission and the final reveal is {surprise.label}.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    parent = f["parent"]
    goal_cfg = f["goal_cfg"]
    trouble = f["trouble_cfg"]
    tool_cfg = f["tool_cfg"]
    surprise = f["surprise"]
    quest = f["quest"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id} and {hero.pronoun('possessive')} {parent.label_word} during bath time. {hero.id} turned the tub into {quest.sea_name} and made a quest out of washing up."
        ),
        (
            "What was the quest?",
            f"The quest was {quest.goal_text} {goal_cfg.phrase}. It felt important because the tub became an adventure sea in {hero.id}'s imagination."
        ),
        (
            "What problem came up in the tub?",
            f"The problem was {trouble.label}. {trouble.risk_text} That is why {hero.id} worried the mission might fail."
        ),
        (
            f"How did {hero.id} solve the problem?",
            f"{hero.id} and {parent.label_word} used {tool_cfg.phrase} to help. The tool worked because this problem needed something that could {trouble.needs_tool}."
        ),
        (
            "What was the surprise at the end?",
            f"The surprise was {surprise.reveal_text}. It changed the ending from simple relief into a happy reward after the quest was done."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"tub"}
    goal_cfg = f["goal_cfg"]
    tool_cfg = f["tool_cfg"]
    surprise = f["surprise"]
    if "duck" in goal_cfg.tags:
        tags.add("duck")
    if "boat" in goal_cfg.tags:
        tags.add("boat")
    if goal_cfg.treasure:
        tags.add("treasure")
    if tool_cfg.id == "ladle":
        tags.add("ladle")
    if "cup" in tool_cfg.tags:
        tags.add("cup")
    if f["trouble_cfg"].needs_tool == "reach":
        tags.add("reach")
    if "bubbles" in surprise.tags or tool_cfg.gives_bubbles:
        tags.add("bubbles")
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        flags = []
        if ent.floats:
            flags.append("floats")
        if ent.can_scoop:
            flags.append("can_scoop")
        if ent.can_reach:
            flags.append("can_reach")
        if ent.gives_bubbles:
            flags.append("gives_bubbles")
        if flags:
            bits.append(f"flags={flags}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        quest="captain",
        goal="duck",
        trouble="drift_away",
        tool="ladle",
        surprise="foam_crown",
        name="Milo",
        gender="boy",
        parent="mother",
    ),
    StoryParams(
        quest="explorer",
        goal="shell",
        trouble="sudden_sink",
        tool="cup",
        surprise="hidden_sticker",
        name="Lily",
        gender="girl",
        parent="father",
    ),
    StoryParams(
        quest="rescuer",
        goal="boat",
        trouble="far_side",
        tool="long_spoon",
        surprise="extra_boat",
        name="Finn",
        gender="boy",
        parent="mother",
    ),
    StoryParams(
        quest="captain",
        goal="star_coin",
        trouble="sudden_sink",
        tool="bubble_cup",
        surprise="foam_crown",
        name="Ava",
        gender="girl",
        parent="father",
    ),
]


def explain_rejection(goal: Goal, trouble: Trouble, tool: Tool) -> str:
    if not goal_at_risk(goal, trouble):
        return (
            f"(No story: {goal.phrase} does not fit the problem '{trouble.label}', so the quest would have no honest turn.)"
        )
    if not tool_works(tool, trouble):
        need = trouble.needs_tool
        return (
            f"(No story: {tool.phrase} cannot solve '{trouble.label}'. This problem needs a tool that can {need}.)"
        )
    return "(No story: this combination does not make a reasonable quest.)"


ASP_RULES = r"""
goal_at_risk(G,T) :- trouble(T), goal(G), drift_trouble(T), goal_drifts(G).
goal_at_risk(G,T) :- trouble(T), goal(G), sink_trouble(T), sinkable_goal(G).
goal_at_risk(G,T) :- trouble(T), goal(G), far_trouble(T).

tool_works(Use,T) :- tool(Use), trouble(T), needs(T, reach), can_reach(Use).
tool_works(Use,T) :- tool(Use), trouble(T), needs(T, scoop), can_scoop(Use).

valid(Q,G,T,Use) :- quest(Q), goal(G), trouble(T), tool(Use), goal_at_risk(G,T), tool_works(Use,T).

solved :- chosen_goal(G), chosen_trouble(T), chosen_tool(Use), goal_at_risk(G,T), tool_works(Use,T).
:- not solved.

#show valid/4.
#show solved/0.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for quest_id in QUESTS:
        lines.append(asp.fact("quest", quest_id))
    for goal_id, goal in GOALS.items():
        lines.append(asp.fact("goal", goal_id))
        if goal.drifts:
            lines.append(asp.fact("goal_drifts", goal_id))
        if goal.sinks_when_splashed:
            lines.append(asp.fact("sinkable_goal", goal_id))
    for trouble_id, trouble in TROUBLES.items():
        lines.append(asp.fact("trouble", trouble_id))
        lines.append(asp.fact("needs", trouble_id, trouble.needs_tool))
        if trouble.id == "drift_away":
            lines.append(asp.fact("drift_trouble", trouble_id))
        if trouble.id == "sudden_sink":
            lines.append(asp.fact("sink_trouble", trouble_id))
        if trouble.id == "far_side":
            lines.append(asp.fact("far_trouble", trouble_id))
    for tool_id, tool in TOOLS.items():
        lines.append(asp.fact("tool", tool_id))
        if tool.can_scoop:
            lines.append(asp.fact("can_scoop", tool_id))
        if tool.can_reach:
            lines.append(asp.fact("can_reach", tool_id))
    return "\n".join(lines)


def asp_program(extra: str = "", show_override: str = "") -> str:
    show = show_override if show_override else ""
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", ""))
    return sorted(set(asp.atoms(model, "valid")))


def asp_solved(params: StoryParams) -> bool:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_goal", params.goal),
            asp.fact("chosen_trouble", params.trouble),
            asp.fact("chosen_tool", params.tool),
        ]
    )
    model = asp.one_model(asp_program(extra, ""))
    return bool(asp.atoms(model, "solved"))


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if cl - py:
            print("  only in clingo:", sorted(cl - py))
        if py - cl:
            print("  only in python:", sorted(py - cl))

    for params in CURATED:
        py_ok = True
        try:
            generate(params)
        except Exception as err:  # pragma: no cover - verification path
            rc = 1
            py_ok = False
            print(f"SMOKE TEST FAILED for curated story {params}: {err}")
        if py_ok and not asp_solved(params):
            rc = 1
            print(f"MISMATCH: ASP could not solve curated params {params}")

    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(123)))
        if not sample.story.strip():
            raise StoryError("(Smoke test generated an empty story.)")
        emit(sample, trace=False, qa=False, header="")
        print("OK: normal generate/emit smoke test passed.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED during normal generation: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Bath-time adventure storyworld: a tiny quest in a tub with a surprise ending."
    )
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--goal", choices=GOALS)
    ap.add_argument("--trouble", choices=TROUBLES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--surprise", choices=SURPRISES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.goal and args.trouble and args.tool:
        goal = GOALS[args.goal]
        trouble = TROUBLES[args.trouble]
        tool = TOOLS[args.tool]
        if not (goal_at_risk(goal, trouble) and tool_works(tool, trouble)):
            raise StoryError(explain_rejection(goal, trouble, tool))

    combos = [
        combo
        for combo in valid_combos()
        if (args.quest is None or combo[0] == args.quest)
        and (args.goal is None or combo[1] == args.goal)
        and (args.trouble is None or combo[2] == args.trouble)
        and (args.tool is None or combo[3] == args.tool)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    quest_id, goal_id, trouble_id, tool_id = rng.choice(sorted(combos))
    surprise_id = args.surprise or rng.choice(sorted(SURPRISES))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(
        quest=quest_id,
        goal=goal_id,
        trouble=trouble_id,
        tool=tool_id,
        surprise=surprise_id,
        name=name,
        gender=gender,
        parent=parent,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        quest = QUESTS[params.quest]
        goal = GOALS[params.goal]
        trouble = TROUBLES[params.trouble]
        tool = TOOLS[params.tool]
        surprise = SURPRISES[params.surprise]
    except KeyError as err:
        raise StoryError(f"(Unknown parameter value: {err.args[0]})") from None

    if not goal_at_risk(goal, trouble) or not tool_works(tool, trouble):
        raise StoryError(explain_rejection(goal, trouble, tool))

    world = tell(
        quest=quest,
        goal=goal,
        trouble=trouble,
        tool=tool,
        surprise=surprise,
        hero_name=params.name,
        hero_gender=params.gender,
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
        print(asp_program("", ""))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (quest, goal, trouble, tool) combos:\n")
        for quest_id, goal_id, trouble_id, tool_id in combos:
            print(f"  {quest_id:9} {goal_id:10} {trouble_id:12} {tool_id}")
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.quest} / {p.goal} / {p.trouble} / {p.tool}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
