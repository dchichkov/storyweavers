#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/lingo_reinforce_tighten_teamwork_friendship_space_adventure.py
=========================================================================================

A standalone story world for a tiny space-adventure domain: two friends are
about to launch a pretend mission when a part of their little ship is loose.
The problem cannot be solved by one child alone. One friend must brace and
reinforce the shaky part while the other uses the right tool to tighten it.
They use their own made-up space lingo to coordinate, and the ending image
shows both the ship and their friendship steadier than before.

Run it
------
    python storyworlds/worlds/gpt-5.4/lingo_reinforce_tighten_teamwork_friendship_space_adventure.py
    python storyworlds/worlds/gpt-5.4/lingo_reinforce_tighten_teamwork_friendship_space_adventure.py --mission moon_base --problem antenna --tool wrench --brace mast_hold
    python storyworlds/worlds/gpt-5.4/lingo_reinforce_tighten_teamwork_friendship_space_adventure.py --tool patch_kit
    python storyworlds/worlds/gpt-5.4/lingo_reinforce_tighten_teamwork_friendship_space_adventure.py --all --qa
    python storyworlds/worlds/gpt-5.4/lingo_reinforce_tighten_teamwork_friendship_space_adventure.py --verify
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
TRUST_SMOOTH = 5


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother"}
        male = {"boy", "man", "father"}
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
class Mission:
    id: str
    scene: str
    ship: str
    launch: str
    goal: str
    afford_problems: set[str] = field(default_factory=set)
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
    label: str
    the: str
    need: str
    brace_need: str
    detail: str
    severity: int
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
    fixes: str
    action: str
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
class Brace:
    id: str
    label: str
    phrase: str
    supports: str
    action: str
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

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"leader", "friend"}]

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


def _r_loose_risk(world: World) -> list[str]:
    out: list[str] = []
    problem = world.get("problem")
    ship = world.get("ship")
    if problem.meters["loose"] >= THRESHOLD:
        sig = ("risk", problem.id)
        if sig not in world.fired:
            world.fired.add(sig)
            ship.meters["risk"] += 1
            for kid in world.kids():
                kid.memes["worry"] += 1
            out.append("__risk__")
    return out


def _r_solo_fail(world: World) -> list[str]:
    out: list[str] = []
    problem = world.get("problem")
    if problem.meters["loose"] < THRESHOLD or problem.meters["solo_try"] < THRESHOLD:
        return out
    if problem.meters["braced"] >= THRESHOLD:
        return out
    sig = ("solo_fail", problem.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    problem.meters["wobble"] += 1
    problem.meters["loose"] += 1
    for kid in world.kids():
        kid.memes["frustration"] += 1
    out.append("__solo_fail__")
    return out


def _r_team_fix(world: World) -> list[str]:
    out: list[str] = []
    problem = world.get("problem")
    tool = world.get("tool")
    brace = world.get("brace")
    ship = world.get("ship")
    if problem.meters["loose"] < THRESHOLD:
        return out
    if problem.meters["tighten_turn"] < THRESHOLD or problem.meters["braced"] < THRESHOLD:
        return out
    if tool.attrs.get("fixes") != problem.attrs.get("need"):
        return out
    if brace.attrs.get("supports") != problem.attrs.get("brace_need"):
        return out
    sig = ("team_fix", problem.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    problem.meters["secure"] += 1
    problem.meters["loose"] = 0.0
    ship.meters["steady"] += 1
    ship.meters["risk"] = 0.0
    for kid in world.kids():
        kid.memes["worry"] = 0.0
        kid.memes["joy"] += 1
        kid.memes["pride"] += 1
        kid.memes["friendship"] += 1
    out.append("__team_fix__")
    return out


CAUSAL_RULES = [
    Rule(name="loose_risk", tag="physical", apply=_r_loose_risk),
    Rule(name="solo_fail", tag="physical", apply=_r_solo_fail),
    Rule(name="team_fix", tag="social", apply=_r_team_fix),
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


def tool_fits(problem: Problem, tool: Tool) -> bool:
    return problem.need == tool.fixes


def brace_fits(problem: Problem, brace: Brace) -> bool:
    return problem.brace_need == brace.supports


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for mission_id, mission in MISSIONS.items():
        for problem_id in sorted(mission.afford_problems):
            problem = PROBLEMS[problem_id]
            for tool_id, tool in TOOLS.items():
                if not tool_fits(problem, tool):
                    continue
                for brace_id, brace in BRACES.items():
                    if brace_fits(problem, brace):
                        combos.append((mission_id, problem_id, tool_id, brace_id))
    return sorted(combos)


def outcome_of(params: "StoryParams") -> str:
    return "smooth_fix" if params.trust >= TRUST_SMOOTH else "mended_fix"


def predict_solo(world: World) -> dict:
    sim = world.copy()
    problem = sim.get("problem")
    problem.meters["solo_try"] += 1
    problem.meters["tighten_turn"] += 1
    propagate(sim, narrate=False)
    return {
        "still_loose": problem.meters["loose"] >= THRESHOLD,
        "wobble": problem.meters["wobble"],
        "risk": sim.get("ship").meters["risk"],
    }


def introduce(world: World, leader: Entity, friend: Entity, mission: Mission) -> None:
    leader.memes["joy"] += 1
    friend.memes["joy"] += 1
    ship = world.get("ship")
    world.say(
        f"On a bright afternoon, {leader.id} and {friend.id} turned a stack of boxes, silver blankets, "
        f"and a painted tunnel into {mission.scene}. Their ship was {ship.label}, and today it was ready for {mission.launch}."
    )
    world.say(
        f"They had even made up space lingo for the mission. When one of them said, "
        f'"Star hands," it meant, "Work together now."'
    )


def discover(world: World, leader: Entity, friend: Entity, mission: Mission, problem: Problem) -> None:
    world.say(
        f'Just as they were about to head for {mission.goal}, {friend.id} noticed something wrong. '
        f"{problem.The} {problem.detail}"
    )
    propagate(world, narrate=False)
    world.say(
        f'"Wait," {friend.id} said. "If we blast off like this, the ship will rattle all over the moon dust."'
    )


def explain_danger(world: World, leader: Entity, problem: Problem) -> None:
    pred = predict_solo(world)
    world.facts["predicted_wobble"] = pred["wobble"]
    world.facts["predicted_still_loose"] = pred["still_loose"]
    world.say(
        f'{leader.id} reached for it first, but then {leader.pronoun()} stopped. '
        f'"I can tighten it," {leader.pronoun()} said, "but not if it keeps wobbling."'
    )


def rush_alone(world: World, leader: Entity, problem: Problem) -> None:
    problem_ent = world.get("problem")
    problem_ent.meters["solo_try"] += 1
    problem_ent.meters["tighten_turn"] += 1
    propagate(world, narrate=False)
    leader.memes["impulse"] += 1
    world.say(
        f"Still, {leader.id} tried alone for one quick second. {problem.The} shook harder instead of settling down, "
        f"and the little ship gave a worried creak."
    )


def hurt_pause(world: World, leader: Entity, friend: Entity) -> None:
    friend.memes["hurt"] += 1
    leader.memes["regret"] += 1
    world.say(
        f'{friend.id} took a small step back. "{leader.id}, I was trying to help," {friend.pronoun()} said.'
    )
    world.say(
        f'{leader.id} looked at the wobbling ship and then at {friend.id}. '
        f'"You were right," {leader.pronoun()} said. "I need my co-pilot."'
    )


def smooth_plan(world: World, leader: Entity, friend: Entity, tool: Tool, brace: Brace) -> None:
    leader.memes["trust"] += 1
    friend.memes["trust"] += 1
    world.say(
        f'"Star hands," {leader.id} said, using their favorite lingo. "{friend.id}, {brace.action}, and I\'ll use {tool.phrase}."'
    )


def mend_plan(world: World, leader: Entity, friend: Entity, tool: Tool, brace: Brace) -> None:
    leader.memes["trust"] += 1
    friend.memes["trust"] += 1
    friend.memes["forgiveness"] += 1
    world.say(
        f'{friend.id} nodded. "{brace.action.capitalize()}," {friend.pronoun()} said. '
        f'"Then you can use {tool.phrase}."'
    )
    world.say(
        f'Together they repeated their lingo very softly: "Star hands." The words helped them remember to listen as well as move.'
    )


def brace_it(world: World, friend: Entity, brace: Brace) -> None:
    brace_ent = world.get("brace")
    problem = world.get("problem")
    brace_ent.meters["used"] += 1
    problem.meters["braced"] += 1
    friend.memes["focus"] += 1
    world.say(
        f"{friend.id} {brace.action}. That helped reinforce the shaky part so it stopped dancing away from every touch."
    )


def tighten_it(world: World, leader: Entity, tool: Tool) -> None:
    tool_ent = world.get("tool")
    problem = world.get("problem")
    tool_ent.meters["used"] += 1
    problem.meters["tighten_turn"] += 1
    leader.memes["focus"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then {leader.id} used {tool.phrase} to tighten it, one careful turn at a time."
    )


def success(world: World, leader: Entity, friend: Entity, mission: Mission, problem: Problem) -> None:
    world.say(
        f"The wobble disappeared. {problem.The} stayed firm, the ship stood steady, and both friends let out the same happy breath."
    )
    world.say(
        f'"Launch!" they shouted together. Their mission to {mission.goal} could finally begin, and the ship felt as ready as their hearts did.'
    )


def ending_image(world: World, leader: Entity, friend: Entity, mission: Mission) -> None:
    world.say(
        f"As they counted down and ducked through the silver tunnel, {leader.id} bumped shoulders with {friend.id}. "
        f"Their pretend rocket did not shake anymore, and neither did their friendship. It had been tightened and reinforced by teamwork."
    )
def tell(
    leader_name: str,
    leader_gender: str,
    friend_name: str,
    friend_gender: str,
    trust: Trust,
) -> World:
    world = World()
    leader = world.add(Entity(
        id=leader_name,
        kind="character",
        type=leader_gender,
        label=leader_name,
        role="leader",
        attrs={"trust": trust},
    ))
    friend = world.add(Entity(
        id=friend_name,
        kind="character",
        type=friend_gender,
        label=friend_name,
        role="friend",
        attrs={"trust": trust},
    ))
    ship = world.add(Entity(
        id="ship",
        kind="thing",
        type="ship",
        label=mission.ship,
        attrs={"mission": mission.id},
    ))
    problem = world.add(Entity(
        id="problem",
        kind="thing",
        type="problem",
        label=problem_cfg.label,
        attrs={"need": problem_cfg.need, "brace_need": problem_cfg.brace_need},
    ))
    tool = world.add(Entity(
        id="tool",
        kind="thing",
        type="tool",
        label=tool_cfg.label,
        attrs={"fixes": tool_cfg.fixes},
    ))
    brace = world.add(Entity(
        id="brace",
        kind="thing",
        type="brace",
        label=brace_cfg.label,
        attrs={"supports": brace_cfg.supports},
    ))

    problem.meters["loose"] = float(problem_cfg.severity)
    ship.meters["steady"] = 0.0
    ship.meters["risk"] = 0.0
    leader.memes["friendship"] = 1.0
    friend.memes["friendship"] = 1.0
    leader.memes["trust"] = float(trust)
    friend.memes["trust"] = float(trust)
    leader.memes["worry"] = 0.0
    friend.memes["worry"] = 0.0

    world.facts.update(
        mission=mission,
        problem_cfg=problem_cfg,
        tool_cfg=tool_cfg,
        brace_cfg=brace_cfg,
        leader=leader,
        friend=friend,
        ship=ship,
        trust=trust,
        friendship_mode=outcome_of(StoryParams(
            mission=mission.id,
            problem=problem_cfg.id,
            tool=tool_cfg.id,
            brace=brace_cfg.id,
            leader=leader_name,
            leader_gender=leader_gender,
            friend=friend_name,
            friend_gender=friend_gender,
            trust=trust,
        )),
    )

    introduce(world, leader, friend, mission)
    world.para()
    discover(world, leader, friend, mission, problem_cfg)
    explain_danger(world, leader, problem_cfg)

    world.para()
    if trust >= TRUST_SMOOTH:
        smooth_plan(world, leader, friend, tool_cfg, brace_cfg)
    else:
        rush_alone(world, leader, problem_cfg)
        hurt_pause(world, leader, friend)
        mend_plan(world, leader, friend, tool_cfg, brace_cfg)

    world.para()
    brace_it(world, friend, brace_cfg)
    tighten_it(world, leader, tool_cfg)
    success(world, leader, friend, mission, problem_cfg)

    world.para()
    ending_image(world, leader, friend, mission)

    world.facts.update(
        outcome=outcome_of(StoryParams(
            mission=mission.id,
            problem=problem_cfg.id,
            tool=tool_cfg.id,
            brace=brace_cfg.id,
            leader=leader_name,
            leader_gender=leader_gender,
            friend=friend_name,
            friend_gender=friend_gender,
            trust=trust,
        )),
        fixed=problem.meters["secure"] >= THRESHOLD,
        smooth=trust >= TRUST_SMOOTH,
    )
    return world
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


MISSIONS = {
    "moon_base": Mission(
        id="moon_base",
        scene="a moon-base rescue station under a blanket-fort sky",
        ship="the Crater Hopper",
        launch="a dusty moon launch",
        goal="the echo caves",
        afford_problems={"antenna", "hatch"},
        tags={"space", "moon"},
    ),
    "comet_dock": Mission(
        id="comet_dock",
        scene="a comet-dock with glowing chalk stars on the floor",
        ship="the Comet Skipper",
        launch="a sparkling comet chase",
        goal="the ice tail",
        afford_problems={"antenna", "cargo_net"},
        tags={"space", "comet"},
    ),
    "ring_station": Mission(
        id="ring_station",
        scene="a ring station built from cushions and silver tape",
        ship="the Orbit Runner",
        launch="an orbit-ring glide",
        goal="the blue window of Saturn",
        afford_problems={"hatch", "cargo_net"},
        tags={"space", "station"},
    ),
}

PROBLEMS = {
    "antenna": Problem(
        id="antenna",
        label="antenna mast",
        the="the antenna mast",
        need="bolt",
        brace_need="mast",
        detail="was tapping against the roof of the ship because one silver bolt had gone loose.",
        severity=1,
        tags={"antenna", "wobble"},
    ),
    "hatch": Problem(
        id="hatch",
        label="hatch wheel",
        the="the hatch wheel",
        need="wheel",
        brace_need="frame",
        detail="was slipping on its latch, so the pretend airlock would not stay snug.",
        severity=1,
        tags={"hatch", "tighten"},
    ),
    "cargo_net": Problem(
        id="cargo_net",
        label="cargo net strap",
        the="the cargo net strap",
        need="strap",
        brace_need="crate",
        detail="had sagged low, and the snack-box moon rocks kept sliding toward the floor.",
        severity=1,
        tags={"cargo", "strap"},
    ),
}

TOOLS = {
    "wrench": Tool(
        id="wrench",
        label="tiny wrench",
        phrase="the tiny wrench",
        fixes="bolt",
        action="turn the bolt tight",
        tags={"wrench", "tool"},
    ),
    "wheel_key": Tool(
        id="wheel_key",
        label="round hatch key",
        phrase="the round hatch key",
        fixes="wheel",
        action="set the hatch wheel snug",
        tags={"hatch", "tool"},
    ),
    "strap_hook": Tool(
        id="strap_hook",
        label="strap hook",
        phrase="the strap hook",
        fixes="strap",
        action="pull the strap tight",
        tags={"cargo", "tool"},
    ),
    "patch_kit": Tool(
        id="patch_kit",
        label="patch kit",
        phrase="the patch kit",
        fixes="tear",
        action="cover a rip",
        tags={"patch", "tool"},
    ),
}

BRACES = {
    "mast_hold": Brace(
        id="mast_hold",
        label="mast brace",
        phrase="the mast brace",
        supports="mast",
        action="held the mast steady with both hands",
        tags={"antenna", "brace"},
    ),
    "frame_hold": Brace(
        id="frame_hold",
        label="frame clamp",
        phrase="the frame clamp",
        supports="frame",
        action="pressed the hatch frame still and firm",
        tags={"hatch", "brace"},
    ),
    "crate_anchor": Brace(
        id="crate_anchor",
        label="anchor line",
        phrase="the anchor line",
        supports="crate",
        action="pulled the crate and net straight toward the wall",
        tags={"cargo", "brace"},
    ),
}

GIRL_NAMES = ["Mira", "Lina", "Nora", "Zoe", "Ava", "Ivy", "Luna", "Tess"]
BOY_NAMES = ["Kai", "Leo", "Finn", "Max", "Jude", "Noah", "Eli", "Owen"]


KNOWLEDGE = {
    "lingo": [
        (
            "What is lingo?",
            "Lingo means special words that a group likes to use with each other. Friends sometimes make up playful lingo for a game so they can feel like a team.",
        )
    ],
    "wrench": [
        (
            "What does a wrench do?",
            "A wrench helps turn a nut or bolt so it can become tighter or looser. When something metal wiggles, a wrench can help a grown-up tighten it.",
        )
    ],
    "hatch": [
        (
            "What is a hatch?",
            "A hatch is a little door or opening that can shut tightly. On a pretend spaceship, a hatch helps children imagine going in and out of an airlock.",
        )
    ],
    "antenna": [
        (
            "What is an antenna?",
            "An antenna is a part that sticks up to send or receive signals. If it is loose, it can wobble and stop working well.",
        )
    ],
    "cargo": [
        (
            "What is cargo?",
            "Cargo is the load a ship carries from one place to another. A cargo net helps hold those things in place so they do not slide around.",
        )
    ],
    "teamwork": [
        (
            "Why is teamwork helpful?",
            "Teamwork helps when one person cannot do every part alone. One friend can hold something steady while another friend finishes the job.",
        )
    ],
    "friendship": [
        (
            "How can friendship grow stronger after a problem?",
            "Friendship grows stronger when friends listen, forgive, and help each other. Solving a problem together can make both friends feel more trusting and proud.",
        )
    ],
}
KNOWLEDGE_ORDER = ["lingo", "antenna", "hatch", "cargo", "wrench", "teamwork", "friendship"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    leader = f["leader"]
    friend = f["friend"]
    mission = f["mission"]
    problem = f["problem_cfg"]
    return [
        f'Write a short space-adventure story for a 3-to-5-year-old that uses the words "lingo," "reinforce," and "tighten."',
        f"Tell a gentle story where two friends, {leader.id} and {friend.id}, must use teamwork to fix {problem.the} before a pretend launch to {mission.goal}.",
        f"Write a child-facing story about friendship in a cardboard spaceship, where made-up space lingo helps two children listen and work together.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    leader = f["leader"]
    friend = f["friend"]
    mission = f["mission"]
    problem = f["problem_cfg"]
    tool = f["tool_cfg"]
    brace = f["brace_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about two friends, {leader.id} and {friend.id}, playing a space adventure together. They are getting their pretend ship ready for a mission to {mission.goal}.",
        ),
        (
            "What problem did they find before launch?",
            f"They found that {problem.the} was loose. That made the ship feel shaky, so they knew they had to fix it before they could play safely and happily.",
        ),
        (
            "What did their space lingo mean?",
            'Their lingo was the phrase "Star hands." It meant, "Work together now," so the words helped them stop and act like a team.',
        ),
    ]
    if f.get("smooth"):
        qa.append(
            (
                f"How did {leader.id} and {friend.id} solve the problem?",
                f"{friend.id} {brace.action}, and {leader.id} used {tool.phrase} to tighten the loose part. One friend held it steady so the other could finish the fix, which is why the ship stopped wobbling.",
            )
        )
    else:
        qa.append(
            (
                f"Why did the friends need a pause before fixing the ship?",
                f"{leader.id} first tried to do the job alone, but the part shook harder instead of settling down. After that, the friends listened to each other, used their lingo, and fixed it together.",
            )
        )
        qa.append(
            (
                "How did the problem change their friendship?",
                f"The problem gave them a chance to apologize and work as a team. By the end, the ship was steady and their friendship felt steadier too because they listened and helped each other.",
            )
        )
    qa.append(
        (
            "How did the story end?",
            f"It ended with the friends launching their pretend mission at last. The steady ship showed that their teamwork had really changed something in the world around them.",
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"lingo", "teamwork", "friendship"}
    tags |= set(f["problem_cfg"].tags)
    if f["tool_cfg"].id == "wrench":
        tags.add("wrench")
    if f["problem_cfg"].id == "hatch":
        tags.add("hatch")
    if f["problem_cfg"].id == "antenna":
        tags.add("antenna")
    if f["problem_cfg"].id == "cargo_net":
        tags.add("cargo")
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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        attrs = {k: v for k, v in ent.attrs.items() if v}
        bits = []
        if attrs:
            bits.append(f"attrs={attrs}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.role:
            bits.append(f"role={ent.role}")
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)
@dataclass
class StoryParams:
    mission: str
    problem: str
    tool: str
    brace: str
    leader: str
    leader_gender: str
    friend: str
    friend_gender: str
    trust: int = 7
    seed: Optional[int] = None




CURATED = [
    StoryParams(
        mission="moon_base",
        problem="antenna",
        tool="wrench",
        brace="mast_hold",
        leader="Kai",
        leader_gender="boy",
        friend="Mira",
        friend_gender="girl",
        trust=8,
    ),
    StoryParams(
        mission="ring_station",
        problem="hatch",
        tool="wheel_key",
        brace="frame_hold",
        leader="Luna",
        leader_gender="girl",
        friend="Leo",
        friend_gender="boy",
        trust=3,
    ),
    StoryParams(
        mission="comet_dock",
        problem="cargo_net",
        tool="strap_hook",
        brace="crate_anchor",
        leader="Max",
        leader_gender="boy",
        friend="Ivy",
        friend_gender="girl",
        trust=6,
    ),
    StoryParams(
        mission="moon_base",
        problem="hatch",
        tool="wheel_key",
        brace="frame_hold",
        leader="Nora",
        leader_gender="girl",
        friend="Finn",
        friend_gender="boy",
        trust=2,
    ),
]


def explain_rejection(problem_id: str, tool_id: str, brace_id: str, mission_id: str) -> str:
    pieces: list[str] = []
    if mission_id in MISSIONS and problem_id in PROBLEMS:
        mission = MISSIONS[mission_id]
        problem = PROBLEMS[problem_id]
        if problem_id not in mission.afford_problems:
            pieces.append(
                f"{problem.the} does not belong in {mission.scene}, so that mission/problem pair is not part of this world"
            )
    if problem_id in PROBLEMS and tool_id in TOOLS:
        problem = PROBLEMS[problem_id]
        tool = TOOLS[tool_id]
        if not tool_fits(problem, tool):
            pieces.append(
                f"{tool.label} cannot fix {problem.the}; it solves {tool.fixes}, not {problem.need}"
            )
    if problem_id in PROBLEMS and brace_id in BRACES:
        problem = PROBLEMS[problem_id]
        brace = BRACES[brace_id]
        if not brace_fits(problem, brace):
            pieces.append(
                f"{brace.label} cannot steady {problem.the}; it supports {brace.supports}, not {problem.brace_need}"
            )
    if not pieces:
        return "(No valid combination matches the given options.)"
    return "(No story: " + "; ".join(pieces) + ".)"


ASP_RULES = r"""
problem_in_mission(M, P) :- affords(M, P).
tool_fits(P, T) :- needs(P, Need), fixes(T, Need).
brace_fits(P, B) :- brace_need(P, Need), supports(B, Need).

valid(M, P, T, B) :- mission(M), problem(P), tool(T), brace(B),
                     problem_in_mission(M, P), tool_fits(P, T), brace_fits(P, B).

smooth_fix :- trust(T), smooth_min(M), T >= M.
mended_fix :- trust(T), smooth_min(M), T < M.

outcome(smooth_fix) :- smooth_fix.
outcome(mended_fix) :- mended_fix.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for mission_id, mission in MISSIONS.items():
        lines.append(asp.fact("mission", mission_id))
        for problem_id in sorted(mission.afford_problems):
            lines.append(asp.fact("affords", mission_id, problem_id))
    for problem_id, problem in PROBLEMS.items():
        lines.append(asp.fact("problem", problem_id))
        lines.append(asp.fact("needs", problem_id, problem.need))
        lines.append(asp.fact("brace_need", problem_id, problem.brace_need))
    for tool_id, tool in TOOLS.items():
        lines.append(asp.fact("tool", tool_id))
        lines.append(asp.fact("fixes", tool_id, tool.fixes))
    for brace_id, brace in BRACES.items():
        lines.append(asp.fact("brace", brace_id))
        lines.append(asp.fact("supports", brace_id, brace.supports))
    lines.append(asp.fact("smooth_min", TRUST_SMOOTH))
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
        asp.fact("trust", params.trust),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0
    cset = set(asp_valid_combos())
    pset = set(valid_combos())
    if cset == pset:
        print(f"OK: gate matches valid_combos() ({len(cset)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if cset - pset:
            print("  only in clingo:", sorted(cset - pset))
        if pset - cset:
            print("  only in python:", sorted(pset - cset))

    cases = list(CURATED)
    parser = build_parser()
    for s in range(20):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(s))
        except StoryError:
            rc = 1
            print(f"FAILED: resolve_params raised unexpectedly for seed {s}.")
            continue
        cases.append(params)

    bad = [p for p in cases if asp_outcome(p) != outcome_of(p)]
    if not bad:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {len(bad)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("smoke test generated empty story")
        emit(sample, trace=False, qa=False, header="")
        print("OK: smoke generation/emit passed.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"FAILED: smoke generation crashed: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: two friends use space lingo and teamwork to steady a pretend ship."
    )
    ap.add_argument("--mission", choices=MISSIONS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--brace", choices=BRACES)
    ap.add_argument("--trust", type=int, choices=list(range(0, 11)))
    ap.add_argument("--leader")
    ap.add_argument("--friend")
    ap.add_argument("--leader-gender", choices=["girl", "boy"])
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
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


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.mission and args.problem and args.problem not in MISSIONS[args.mission].afford_problems:
        raise StoryError(explain_rejection(args.problem, args.tool or "wrench", args.brace or "mast_hold", args.mission))
    if args.problem and args.tool and not tool_fits(PROBLEMS[args.problem], TOOLS[args.tool]):
        raise StoryError(explain_rejection(args.problem, args.tool, args.brace or "mast_hold", args.mission or "moon_base"))
    if args.problem and args.brace and not brace_fits(PROBLEMS[args.problem], BRACES[args.brace]):
        raise StoryError(explain_rejection(args.problem, args.tool or "wrench", args.brace, args.mission or "moon_base"))

    combos = [
        c for c in valid_combos()
        if (args.mission is None or c[0] == args.mission)
        and (args.problem is None or c[1] == args.problem)
        and (args.tool is None or c[2] == args.tool)
        and (args.brace is None or c[3] == args.brace)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    mission_id, problem_id, tool_id, brace_id = rng.choice(combos)
    leader_gender = args.leader_gender or rng.choice(["girl", "boy"])
    friend_gender = args.friend_gender or rng.choice(["girl", "boy"])
    leader_name = args.leader or _pick_name(rng, leader_gender)
    friend_name = args.friend or _pick_name(rng, friend_gender, avoid=leader_name)
    trust = args.trust if args.trust is not None else rng.randint(0, 10)
    return StoryParams(
        mission=mission_id,
        problem=problem_id,
        tool=tool_id,
        brace=brace_id,
        leader=leader_name,
        leader_gender=leader_gender,
        friend=friend_name,
        friend_gender=friend_gender,
        trust=trust,
    )


def generate(params: StoryParams) -> StorySample:
    if params.mission not in MISSIONS:
        raise StoryError(f"(Unknown mission: {params.mission})")
    if params.problem not in PROBLEMS:
        raise StoryError(f"(Unknown problem: {params.problem})")
    if params.tool not in TOOLS:
        raise StoryError(f"(Unknown tool: {params.tool})")
    if params.brace not in BRACES:
        raise StoryError(f"(Unknown brace: {params.brace})")

    combo = (params.mission, params.problem, params.tool, params.brace)
    if combo not in set(valid_combos()):
        raise StoryError(explain_rejection(params.problem, params.tool, params.brace, params.mission))

    world = tell(
        MISSIONS[params.mission],
        PROBLEMS[params.problem],
        TOOLS[params.tool],
        BRACES[params.brace],
        leader_name=params.leader,
        leader_gender=params.leader_gender,
        friend_name=params.friend,
        friend_gender=params.friend_gender,
        trust=params.trust,
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
        print(f"{len(combos)} compatible (mission, problem, tool, brace) combos:\n")
        for mission_id, problem_id, tool_id, brace_id in combos:
            print(f"  {mission_id:11} {problem_id:10} {tool_id:10} {brace_id}")
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
            header = f"### {p.leader} & {p.friend}: {p.problem} on {p.mission} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
