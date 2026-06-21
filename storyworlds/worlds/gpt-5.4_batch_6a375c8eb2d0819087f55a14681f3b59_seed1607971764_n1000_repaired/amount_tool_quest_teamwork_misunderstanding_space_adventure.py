#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/amount_tool_quest_teamwork_misunderstanding_space_adventure.py
=================================================================================================

A standalone story world for a tiny space-adventure tale about an exact amount,
the right tool, a quest across a moon station, a misunderstanding, and a
teamwork fix.

This world models a simple but state-driven domain:

- two child astronauts receive a quest
- the mission needs an exact amount of a material
- one child brings the wrong tool because of a misunderstanding
- the first attempt fails in a concrete, physical way
- the children work together to clear up the confusion
- they use the correct tool, carry the exact amount, and finish the quest

Run it
------
    python storyworlds/worlds/gpt-5.4/amount_tool_quest_teamwork_misunderstanding_space_adventure.py
    python storyworlds/worlds/gpt-5.4/amount_tool_quest_teamwork_misunderstanding_space_adventure.py --mission beacon --material star_sand
    python storyworlds/worlds/gpt-5.4/amount_tool_quest_teamwork_misunderstanding_space_adventure.py --tool scoop --wrong-tool scoop
    python storyworlds/worlds/gpt-5.4/amount_tool_quest_teamwork_misunderstanding_space_adventure.py --all
    python storyworlds/worlds/gpt-5.4/amount_tool_quest_teamwork_misunderstanding_space_adventure.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/amount_tool_quest_teamwork_misunderstanding_space_adventure.py --trace
    python storyworlds/worlds/gpt-5.4/amount_tool_quest_teamwork_misunderstanding_space_adventure.py --json
    python storyworlds/worlds/gpt-5.4/amount_tool_quest_teamwork_misunderstanding_space_adventure.py --verify
"""

from __future__ import annotations

import argparse
import contextlib
import copy
import io
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
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman"}
        male = {"boy", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


# ---------------------------------------------------------------------------
# Domain registries
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
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Mission:
    id: str
    place: str
    goal_name: str
    problem: str
    success: str
    ending_image: str
    material: str
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
class Material:
    id: str
    label: str
    phrase: str
    amount: int
    unit: str
    wrong_effect: str
    right_effect: str
    tool: str
    storage: str
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
class ToolCfg:
    id: str
    label: str
    phrase: str
    verb: str
    storage: str
    works_for: set[str] = field(default_factory=set)
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
class Misunderstanding:
    id: str
    cause: str
    line: str
    discovery: str
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
class TeamMove:
    id: str
    text: str
    proof: str
    supports: set[str] = field(default_factory=set)
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
        return [e for e in self.entities.values() if e.role in {"captain", "partner"}]

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


# ---------------------------------------------------------------------------
# Rules
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


def _r_wrong_tool_confusion(world: World) -> list[str]:
    payload = world.get("payload")
    tool = world.get("active_tool")
    if payload.meters["attempted"] < THRESHOLD:
        return []
    if payload.meters["exact"] >= THRESHOLD:
        return []
    sig = ("wrong_tool_confusion", tool.attrs.get("tool_id"))
    if sig in world.fired:
        return []
    if tool.attrs.get("tool_id") == world.facts["material"].tool:
        return []
    world.fired.add(sig)
    for kid in world.kids():
        kid.memes["worry"] += 1
    world.get("goal").meters["waiting"] += 1
    return ["__wrong_tool__"]


def _r_exact_amount(world: World) -> list[str]:
    payload = world.get("payload")
    tool = world.get("active_tool")
    if payload.meters["prepared"] < THRESHOLD:
        return []
    sig = ("exact_amount", int(payload.meters["amount"]), tool.attrs.get("tool_id"))
    if sig in world.fired:
        return []
    if (
        int(payload.meters["amount"]) == world.facts["material"].amount
        and tool.attrs.get("tool_id") == world.facts["material"].tool
    ):
        world.fired.add(sig)
        payload.meters["exact"] += 1
        return []
    return []


def _r_goal_ready(world: World) -> list[str]:
    payload = world.get("payload")
    goal = world.get("goal")
    if payload.meters["delivered"] < THRESHOLD or payload.meters["exact"] < THRESHOLD:
        return []
    sig = ("goal_ready", world.facts["mission"].id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    goal.meters["solved"] += 1
    goal.meters["waiting"] = 0.0
    for kid in world.kids():
        kid.memes["relief"] += 1
        kid.memes["pride"] += 1
    return ["__goal_ready__"]


CAUSAL_RULES: list[Rule] = [
    Rule(name="wrong_tool_confusion", tag="social", apply=_r_wrong_tool_confusion),
    Rule(name="exact_amount", tag="physical", apply=_r_exact_amount),
    Rule(name="goal_ready", tag="physical", apply=_r_goal_ready),
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


# ---------------------------------------------------------------------------
# Constraint helpers
# ---------------------------------------------------------------------------
def mission_matches_material(mission: Mission, material: Material) -> bool:
    return mission.material == material.id


def tool_works_for(tool: ToolCfg, material: Material) -> bool:
    return material.id in tool.works_for


def plausible_confusion(correct_tool: ToolCfg, wrong_tool: ToolCfg) -> bool:
    return correct_tool.id != wrong_tool.id and correct_tool.storage == wrong_tool.storage


def move_solves(teamwork: TeamMove, misunderstanding: Misunderstanding) -> bool:
    return misunderstanding.id in teamwork.supports


def valid_combos() -> list[tuple[str, str, str, str, str, str]]:
    combos: list[tuple[str, str, str, str, str, str]] = []
    for mission_id, mission in MISSIONS.items():
        material = MATERIALS[mission.material]
        for tool_id, tool in TOOLS.items():
            if not tool_works_for(tool, material):
                continue
            for wrong_id, wrong in TOOLS.items():
                if not plausible_confusion(tool, wrong):
                    continue
                if tool_works_for(wrong, material):
                    continue
                for mis_id, mis in MISUNDERSTANDINGS.items():
                    for team_id, team in TEAM_MOVES.items():
                        if move_solves(team, mis):
                            combos.append((mission_id, material.id, tool_id, wrong_id, mis_id, team_id))
    return combos


def explain_combo_rejection(
    mission: Mission,
    material: Material,
    tool: ToolCfg,
    wrong_tool: ToolCfg,
    misunderstanding: Misunderstanding,
    teamwork: TeamMove,
) -> str:
    if not mission_matches_material(mission, material):
        return (
            f"(No story: the {mission.goal_name} needs {MATERIALS[mission.material].label}, "
            f"not {material.label}. The quest only works when the mission and material match.)"
        )
    if not tool_works_for(tool, material):
        return (
            f"(No story: {tool.label} cannot carry the exact amount of {material.label}. "
            f"Use the right measuring tool for that material.)"
        )
    if wrong_tool.id == tool.id:
        return "(No story: the misunderstanding needs a different wrong tool, not the same one.)"
    if tool_works_for(wrong_tool, material):
        return (
            f"(No story: {wrong_tool.label} would also work for {material.label}, "
            f"so there would be no real misunderstanding to fix.)"
        )
    if not plausible_confusion(tool, wrong_tool):
        return (
            f"(No story: {tool.label} and {wrong_tool.label} are not stored together, "
            f"so mixing them up would not be a very plausible mistake.)"
        )
    if not move_solves(teamwork, misunderstanding):
        return (
            f"(No story: the teamwork move '{teamwork.id}' does not clearly solve the "
            f"misunderstanding '{misunderstanding.id}'.)"
        )
    return "(No story: this combination is not reasonable.)"


# ---------------------------------------------------------------------------
# Prediction
# ---------------------------------------------------------------------------
def predict_attempt(world: World, tool_id: str) -> dict:
    sim = world.copy()
    tool_cfg = TOOLS[tool_id]
    active = sim.get("active_tool")
    active.attrs["tool_id"] = tool_cfg.id
    active.label = tool_cfg.label
    sim.get("payload").meters["attempted"] += 1
    sim.get("payload").meters["amount"] = float(sim.facts["material"].amount)
    sim.get("payload").meters["prepared"] = 0.0
    propagate(sim, narrate=False)
    return {
        "exact": sim.get("payload").meters["exact"] >= THRESHOLD,
        "waiting": sim.get("goal").meters["waiting"] >= THRESHOLD,
    }


# ---------------------------------------------------------------------------
# Story actions
# ---------------------------------------------------------------------------
def introduce(world: World, captain: Entity, partner: Entity, mission: Mission) -> None:
    for kid in (captain, partner):
        kid.memes["wonder"] += 1
        kid.memes["excitement"] += 1
    world.say(
        f"On the little moon station, {captain.id} and {partner.id} zipped through the silver hall "
        f"like two tiny astronauts on a grand quest."
    )
    world.say(
        f"Beyond the round window, stars sparkled over {mission.place}, where {mission.problem}."
    )


def mission_brief(world: World, captain: Entity, partner: Entity, mission: Mission, material: Material) -> None:
    world.say(
        f"Today their job was important: they had to carry exactly {material.amount} {material.unit} of "
        f"{material.label} to the {mission.goal_name}."
    )
    world.say(
        f'"The right amount matters," {partner.id} said. "If we bring too little or too much, it will not work."'
    )


def assign_tool(world: World, captain: Entity, tool: ToolCfg, wrong_tool: ToolCfg, misunderstanding: Misunderstanding) -> None:
    captain.memes["confidence"] += 1
    world.say(
        f'{captain.id} hurried to the supply drawer. {misunderstanding.cause} '
        f'{captain.pronoun("subject")} thought the note said to bring {wrong_tool.phrase}, not {tool.phrase}.'
    )
    world.say(misunderstanding.line)


def start_quest(world: World, captain: Entity, partner: Entity, mission: Mission) -> None:
    world.say(
        f"So off they went across the humming station, over the glass bridge, and down the blue-lit ramp "
        f"toward {mission.place}."
    )
    world.say(
        f"The quest felt thrilling, and both children held their helmets a little higher."
    )


def wrong_attempt(
    world: World,
    captain: Entity,
    partner: Entity,
    material: Material,
    wrong_tool: ToolCfg,
) -> None:
    active = world.get("active_tool")
    payload = world.get("payload")
    active.attrs["tool_id"] = wrong_tool.id
    active.label = wrong_tool.label
    payload.meters["attempted"] += 1
    payload.meters["amount"] = float(material.amount)
    payload.meters["prepared"] = 0.0
    payload.meters["exact"] = 0.0
    propagate(world, narrate=False)
    world.say(
        f"But when {captain.id} tried to {wrong_tool.verb} {material.label} with the wrong tool, {material.wrong_effect}."
    )
    world.say(
        f'"Oh no," said {partner.id}. "We still do not have the exact amount, and the {mission_name(world)} is waiting."'
    )


def mission_name(world: World) -> str:
    return world.facts["mission"].goal_name


def detect_problem(world: World, partner: Entity, misunderstanding: Misunderstanding) -> None:
    partner.memes["care"] += 1
    world.say(
        f'{partner.id} stopped and looked from the note to the drawer tag. {misunderstanding.discovery}'
    )


def teamwork_fix(
    world: World,
    captain: Entity,
    partner: Entity,
    material: Material,
    tool: ToolCfg,
    teamwork: TeamMove,
) -> None:
    for kid in (captain, partner):
        kid.memes["trust"] += 1
        kid.memes["focus"] += 1
    world.facts["clarified"] = True
    world.say(teamwork.text)
    world.say(
        f"Together they fetched {tool.phrase}. One held the jar steady while the other counted the exact amount aloud."
    )
    active = world.get("active_tool")
    payload = world.get("payload")
    active.attrs["tool_id"] = tool.id
    active.label = tool.label
    payload.meters["prepared"] += 1
    payload.meters["amount"] = float(material.amount)
    propagate(world, narrate=False)
    world.say(
        f"At last they had exactly {material.amount} {material.unit} of {material.label}, measured with the right tool."
    )
    world.say(teamwork.proof)


def deliver(world: World, captain: Entity, partner: Entity, mission: Mission, material: Material) -> None:
    payload = world.get("payload")
    payload.meters["delivered"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{captain.id} and {partner.id} carried the glowing container all the way to the {mission.goal_name} "
        f"and poured in the careful amount."
    )
    world.say(material.right_effect)
    world.say(mission.success)
    world.say(mission.ending_image)


# ---------------------------------------------------------------------------
# The screenplay
# ---------------------------------------------------------------------------
def tell(
    *,
    mission: Mission,
    material: Material,
    tool: ToolCfg,
    wrong_tool: ToolCfg,
    misunderstanding: Misunderstanding,
    teamwork: TeamMove,
    captain_name: str,
    captain_gender: str,
    partner_name: str,
    partner_gender: str,
) -> World:
    world = World()

    captain = world.add(
        Entity(
            id=captain_name,
            kind="character",
            type=captain_gender,
            role="captain",
            traits=["brave", "quick"],
            attrs={},
        )
    )
    partner = world.add(
        Entity(
            id=partner_name,
            kind="character",
            type=partner_gender,
            role="partner",
            traits=["careful", "kind"],
            attrs={},
        )
    )
    world.add(Entity(id="goal", type="machine", label=mission.goal_name, attrs={}, meters=defaultdict(float), memes=defaultdict(float)))
    world.add(Entity(id="payload", type="cargo", label=material.label, attrs={}, meters=defaultdict(float), memes=defaultdict(float)))
    world.add(
        Entity(
            id="active_tool",
            type="tool",
            label=wrong_tool.label,
            attrs={"tool_id": wrong_tool.id},
            meters=defaultdict(float),
            memes=defaultdict(float),
        )
    )

    world.facts = {
        "mission": mission,
        "material": material,
        "tool": tool,
        "wrong_tool": wrong_tool,
        "misunderstanding": misunderstanding,
        "teamwork": teamwork,
        "captain": captain,
        "partner": partner,
        "clarified": False,
    }

    # Initialize meters/memes that rules may read.
    world.get("goal").meters["waiting"] = 0.0
    world.get("goal").meters["solved"] = 0.0
    world.get("payload").meters["attempted"] = 0.0
    world.get("payload").meters["prepared"] = 0.0
    world.get("payload").meters["amount"] = 0.0
    world.get("payload").meters["exact"] = 0.0
    world.get("payload").meters["delivered"] = 0.0
    captain.memes["worry"] = 0.0
    captain.memes["trust"] = 0.0
    partner.memes["worry"] = 0.0
    partner.memes["trust"] = 0.0

    introduce(world, captain, partner, mission)
    mission_brief(world, captain, partner, mission, material)

    world.para()
    assign_tool(world, captain, tool, wrong_tool, misunderstanding)
    start_quest(world, captain, partner, mission)
    wrong_attempt(world, captain, partner, material, wrong_tool)

    world.para()
    detect_problem(world, partner, misunderstanding)
    teamwork_fix(world, captain, partner, material, tool, teamwork)
    deliver(world, captain, partner, mission, material)

    world.facts["solved"] = world.get("goal").meters["solved"] >= THRESHOLD
    world.facts["amount_ok"] = world.get("payload").meters["exact"] >= THRESHOLD
    world.facts["waiting"] = world.get("goal").meters["waiting"] >= THRESHOLD
    return world


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
MISSIONS = {
    "beacon": Mission(
        id="beacon",
        place="the crater beacon",
        goal_name="beacon bowl",
        problem="the path lights on the far ridge had gone dark",
        success="The crater beacon woke with a bright whoomph, and a ribbon of safe light ran along the ridge for the night walkers.",
        ending_image="Hand in hand, the two friends watched the line of moon lamps blink on, one by one, like stars learning a new song.",
        material="star_sand",
        tags={"beacon", "quest"},
    ),
    "garden": Mission(
        id="garden",
        place="the moon garden dome",
        goal_name="seed ring",
        problem="the baby comet beans inside the dome were drooping in their trays",
        success="A soft silver mist rose through the dome, and the tiny comet beans lifted their shining leaves again.",
        ending_image="Soon the glass dome glimmered with green sparks, and the children could see their smiling faces beside the waking plants.",
        material="comet_water",
        tags={"garden", "quest"},
    ),
    "map": Mission(
        id="map",
        place="the cave map tower",
        goal_name="map engine",
        problem="the cave map on the wall had faded to a sleepy blur",
        success="The map engine hummed, and silver lines spread across the wall to show the twisting tunnels again.",
        ending_image="The children stood shoulder to shoulder under the glowing map, its bright paths curling above them like moon rivers.",
        material="spark_crystals",
        tags={"map", "quest"},
    ),
}

MATERIALS = {
    "star_sand": Material(
        id="star_sand",
        label="star sand",
        phrase="a jar of star sand",
        amount=3,
        unit="scoops",
        wrong_effect="the sand slipped in uneven little heaps and kept sliding off the edge",
        right_effect="The grains settled with a gentle fizz, perfectly level in the bowl.",
        tool="scoop",
        storage="silver_drawer",
        tags={"amount", "sand"},
    ),
    "comet_water": Material(
        id="comet_water",
        label="comet water",
        phrase="a flask of comet water",
        amount=2,
        unit="vials",
        wrong_effect="the water splashed and dribbled, so nobody could tell the right amount",
        right_effect="The shining drops fell in two neat measures and spread through the ring like liquid moonlight.",
        tool="vial",
        storage="blue_drawer",
        tags={"amount", "water"},
    ),
    "spark_crystals": Material(
        id="spark_crystals",
        label="spark crystals",
        phrase="a pouch of spark crystals",
        amount=4,
        unit="crystals",
        wrong_effect="the crystals clinked and bounced, and one rolled away before they could count properly",
        right_effect="Each crystal clicked into place with a bright little ping.",
        tool="magnet_claw",
        storage="gold_drawer",
        tags={"amount", "crystal"},
    ),
}

TOOLS = {
    "scoop": ToolCfg(
        id="scoop",
        label="scoop",
        phrase="the little moon scoop",
        verb="scoop up",
        storage="silver_drawer",
        works_for={"star_sand"},
        tags={"tool", "scoop"},
    ),
    "brush": ToolCfg(
        id="brush",
        label="brush",
        phrase="the star brush",
        verb="sweep up",
        storage="silver_drawer",
        works_for=set(),
        tags={"tool", "brush"},
    ),
    "vial": ToolCfg(
        id="vial",
        label="vial",
        phrase="the measuring vial",
        verb="pour",
        storage="blue_drawer",
        works_for={"comet_water"},
        tags={"tool", "vial"},
    ),
    "fan": ToolCfg(
        id="fan",
        label="fan",
        phrase="the cooling fan",
        verb="blow at",
        storage="blue_drawer",
        works_for=set(),
        tags={"tool", "fan"},
    ),
    "magnet_claw": ToolCfg(
        id="magnet_claw",
        label="magnet claw",
        phrase="the magnet claw",
        verb="pick up",
        storage="gold_drawer",
        works_for={"spark_crystals"},
        tags={"tool", "magnet"},
    ),
    "polisher": ToolCfg(
        id="polisher",
        label="polisher",
        phrase="the crystal polisher",
        verb="rub",
        storage="gold_drawer",
        works_for=set(),
        tags={"tool", "polisher"},
    ),
}

MISUNDERSTANDINGS = {
    "echo": Misunderstanding(
        id="echo",
        cause="The radio crackled inside the helmets, and through the echo",
        line='"I brought the tool from the right drawer," said the captain, but the note had been heard wrong.',
        discovery="Then the careful child remembered the fuzzy radio echo and realized the message itself had been the problem.",
        tags={"misunderstanding", "radio"},
    ),
    "point": Misunderstanding(
        id="point",
        cause="A gloved finger had pointed toward the drawer too quickly, and because of that",
        line='"I thought you meant this one," the captain said, staring at the shiny drawer handle.',
        discovery="At the drawer they both saw the tiny arrow sticker pointing to a different shelf.",
        tags={"misunderstanding", "gesture"},
    ),
    "assumption": Misunderstanding(
        id="assumption",
        cause="Nobody stopped to read the label twice, so",
        line='"I just guessed," the captain admitted. "I thought any silver tool would do."',
        discovery="The partner smoothed the note flat and saw that the label had always named one exact tool.",
        tags={"misunderstanding", "labels"},
    ),
}

TEAM_MOVES = {
    "read_label": TeamMove(
        id="read_label",
        text="They set the jar down, took a slow breath, and read the shelf label together until every letter was clear.",
        proof="Now the mistake made sense, and neither child felt cross; the problem had been a mix-up, not meanness.",
        supports={"point", "assumption"},
        tags={"teamwork", "labels"},
    ),
    "replay_radio": TeamMove(
        id="replay_radio",
        text="They tapped the helmet recorder and listened to the message again together, this time all the way to the end.",
        proof="Hearing the full message together untangled the misunderstanding at once.",
        supports={"echo"},
        tags={"teamwork", "radio"},
    ),
    "ask_rover": TeamMove(
        id="ask_rover",
        text='They asked the little station rover to shine its lamp on the drawer tags, and together they checked the note one line at a time.',
        proof="With both children checking and the rover holding the light still, the mixed-up moment turned into a plan.",
        supports={"echo", "point", "assumption"},
        tags={"teamwork", "robot"},
    ),
    "count_together": TeamMove(
        id="count_together",
        text="They lined up the jars, pointed to the symbols together, and matched the tool picture to the note before anyone moved again.",
        proof="Doing the checking together made the mission feel calm again.",
        supports={"point", "assumption"},
        tags={"teamwork", "count"},
    ),
}

GIRL_NAMES = ["Luna", "Mira", "Nova", "Zia", "Tess", "Ivy", "Nia", "Skye"]
BOY_NAMES = ["Leo", "Kai", "Orin", "Milo", "Jett", "Finn", "Nico", "Arlo"]


# ---------------------------------------------------------------------------
# Per-world params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    mission: str
    material: str
    tool: str
    wrong_tool: str
    misunderstanding: str
    teamwork: str
    captain: str
    captain_gender: str
    partner: str
    partner_gender: str
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
    "amount": [
        (
            "What does amount mean?",
            "Amount means how much of something there is. In this story, the children needed the exact amount so the machine would work properly.",
        )
    ],
    "tool": [
        (
            "What is a tool?",
            "A tool is something you use to help do a job. The right tool makes careful work easier and safer.",
        )
    ],
    "teamwork": [
        (
            "What is teamwork?",
            "Teamwork means people help each other do one job together. When one person misses something, another person can notice it and help fix the problem.",
        )
    ],
    "misunderstanding": [
        (
            "What is a misunderstanding?",
            "A misunderstanding happens when people hear, see, or guess something the wrong way. It can often be fixed by slowing down and checking together.",
        )
    ],
    "scoop": [
        (
            "What does a scoop do?",
            "A scoop helps you lift a small measured bit of powder or sand. It is useful when you need the same amount each time.",
        )
    ],
    "vial": [
        (
            "What is a measuring vial?",
            "A measuring vial is a small container used to hold one careful measure of liquid. It helps you pour the right amount.",
        )
    ],
    "magnet": [
        (
            "Why would a magnet claw help with crystals?",
            "A magnet claw can pick up small pieces one by one. That makes it easier to count them exactly.",
        )
    ],
    "radio": [
        (
            "Why can a crackly radio cause trouble?",
            "A crackly radio can make words hard to hear. Then people may think they heard the right thing when they really missed part of the message.",
        )
    ],
    "labels": [
        (
            "Why are labels helpful?",
            "Labels tell you what something is. Reading them carefully can stop mix-ups before they grow into bigger problems.",
        )
    ],
    "robot": [
        (
            "How can a robot helper be useful?",
            "A robot helper can hold a light, carry things, or check a task with you. It helps the team notice details they might miss alone.",
        )
    ],
    "count": [
        (
            "Why does counting together help?",
            "Counting together gives two chances to notice a mistake. It also helps everyone agree on the exact amount.",
        )
    ],
}
KNOWLEDGE_ORDER = [
    "amount",
    "tool",
    "teamwork",
    "misunderstanding",
    "radio",
    "labels",
    "robot",
    "count",
    "scoop",
    "vial",
    "magnet",
]


def generation_prompts(world: World) -> list[str]:
    mission = world.facts["mission"]
    material = world.facts["material"]
    captain = world.facts["captain"]
    partner = world.facts["partner"]
    wrong_tool = world.facts["wrong_tool"]
    tool = world.facts["tool"]
    return [
        f'Write a short space adventure for a 3-to-5-year-old that includes the words "amount" and "tool" and centers on a quest.',
        f"Tell a gentle story where {captain.id} and {partner.id} need the exact amount of {material.label} for {mission.goal_name}, but a misunderstanding leads to the wrong tool first.",
        f"Write a teamwork story on a moon station where children fix a misunderstanding, find the right tool, and finish an important quest together.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    mission = world.facts["mission"]
    material = world.facts["material"]
    tool = world.facts["tool"]
    wrong_tool = world.facts["wrong_tool"]
    misunderstanding = world.facts["misunderstanding"]
    teamwork = world.facts["teamwork"]
    captain = world.facts["captain"]
    partner = world.facts["partner"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about two young astronauts, {captain.id} and {partner.id}. They were working together on a moon-station quest.",
        ),
        (
            "What was their quest?",
            f"They had to take exactly {material.amount} {material.unit} of {material.label} to the {mission.goal_name}. The exact amount mattered because that was what the mission needed to work.",
        ),
        (
            f"Why did they have trouble at first?",
            f"They had trouble because of a misunderstanding and brought {wrong_tool.label} instead of {tool.label}. With the wrong tool, they could not measure the exact amount properly.",
        ),
        (
            f"How did {partner.id} help fix the problem?",
            f"{partner.id} slowed down and helped check what had gone wrong. That careful teamwork let both children understand the misunderstanding instead of blaming each other.",
        ),
        (
            "How did they solve the quest?",
            f"They used {teamwork.id.replace('_', ' ')} and then fetched {tool.label}. After that, they measured exactly {material.amount} {material.unit} of {material.label} and delivered it together.",
        ),
        (
            "How did the story end?",
            f"The mission worked, and {mission.success} The ending shows that working together changed a mistake into success.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"amount", "tool", "teamwork", "misunderstanding"}
    tags |= set(world.facts["tool"].tags)
    tags |= set(world.facts["misunderstanding"].tags)
    tags |= set(world.facts["teamwork"].tags)
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


# ---------------------------------------------------------------------------
# Trace
# ---------------------------------------------------------------------------
def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v or v == 0}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:12} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
required_material(M, Mat) :- mission(M), mission_needs(M, Mat).
good_tool(Mat, T) :- material(Mat), tool(T), compatible(Mat, T).
bad_tool(Mat, T) :- material(Mat), tool(T), not compatible(Mat, T).
plausible_wrong(T, W) :- tool(T), tool(W), same_storage(T, W), T != W.
fixes(Mis, Team) :- misunderstanding(Mis), team_move(Team), supports(Team, Mis).

valid(M, Mat, T, W, Mis, Team) :-
    mission(M), material(Mat), tool(T), tool(W), misunderstanding(Mis), team_move(Team),
    required_material(M, Mat),
    good_tool(Mat, T),
    plausible_wrong(T, W),
    bad_tool(Mat, W),
    fixes(Mis, Team).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for mission_id, mission in MISSIONS.items():
        lines.append(asp.fact("mission", mission_id))
        lines.append(asp.fact("mission_needs", mission_id, mission.material))
    for material_id in MATERIALS:
        lines.append(asp.fact("material", material_id))
    for tool_id, tool in TOOLS.items():
        lines.append(asp.fact("tool", tool_id))
        for mat in sorted(tool.works_for):
            lines.append(asp.fact("compatible", mat, tool_id))
    for a_id, a in TOOLS.items():
        for b_id, b in TOOLS.items():
            if a_id != b_id and a.storage == b.storage:
                lines.append(asp.fact("same_storage", a_id, b_id))
    for mis_id in MISUNDERSTANDINGS:
        lines.append(asp.fact("misunderstanding", mis_id))
    for team_id, team in TEAM_MOVES.items():
        lines.append(asp.fact("team_move", team_id))
        for mis in sorted(team.supports):
            lines.append(asp.fact("supports", team_id, mis))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/6."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: ASP gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH between ASP and Python valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    smoke_params = CURATED[0]
    try:
        sample = generate(smoke_params)
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            emit(sample, trace=True, qa=True, header="### smoke")
        if not sample.story.strip():
            raise StoryError("smoke test generated an empty story")
        print("OK: smoke generation and emit succeeded.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


# ---------------------------------------------------------------------------
# Parser / resolve / generate / emit
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: a moon-station quest about an exact amount, the right tool, a misunderstanding, and teamwork."
    )
    ap.add_argument("--mission", choices=MISSIONS)
    ap.add_argument("--material", choices=MATERIALS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--wrong-tool", dest="wrong_tool", choices=TOOLS)
    ap.add_argument("--misunderstanding", choices=MISUNDERSTANDINGS)
    ap.add_argument("--teamwork", choices=TEAM_MOVES)
    ap.add_argument("--captain")
    ap.add_argument("--captain-gender", dest="captain_gender", choices=["girl", "boy"])
    ap.add_argument("--partner")
    ap.add_argument("--partner-gender", dest="partner_gender", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the valid combinations derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.mission and args.material:
        mission = MISSIONS[args.mission]
        material = MATERIALS[args.material]
        tool_id = args.tool or material.tool
        wrong_id = args.wrong_tool or next(iter(TOOLS))
        mis_id = args.misunderstanding or next(iter(MISUNDERSTANDINGS))
        team_id = args.teamwork or next(iter(TEAM_MOVES))
        tool = TOOLS[tool_id]
        wrong = TOOLS[wrong_id]
        mis = MISUNDERSTANDINGS[mis_id]
        team = TEAM_MOVES[team_id]
        combo = (mission.id, material.id, tool.id, wrong.id, mis.id, team.id)
        if combo not in valid_combos():
            raise StoryError(explain_combo_rejection(mission, material, tool, wrong, mis, team))

    combos = [
        combo
        for combo in valid_combos()
        if (args.mission is None or combo[0] == args.mission)
        and (args.material is None or combo[1] == args.material)
        and (args.tool is None or combo[2] == args.tool)
        and (args.wrong_tool is None or combo[3] == args.wrong_tool)
        and (args.misunderstanding is None or combo[4] == args.misunderstanding)
        and (args.teamwork is None or combo[5] == args.teamwork)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    mission_id, material_id, tool_id, wrong_id, mis_id, team_id = rng.choice(sorted(combos))
    captain_gender = args.captain_gender or rng.choice(["girl", "boy"])
    partner_gender = args.partner_gender or rng.choice(["girl", "boy"])
    captain = args.captain or _pick_name(rng, captain_gender)
    partner = args.partner or _pick_name(rng, partner_gender, avoid=captain)
    return StoryParams(
        mission=mission_id,
        material=material_id,
        tool=tool_id,
        wrong_tool=wrong_id,
        misunderstanding=mis_id,
        teamwork=team_id,
        captain=captain,
        captain_gender=captain_gender,
        partner=partner,
        partner_gender=partner_gender,
    )


def _lookup(mapping: dict, key: str, label: str):
    if key not in mapping:
        raise StoryError(f"(No story: unknown {label} '{key}'.)")
    return mapping[key]


def generate(params: StoryParams) -> StorySample:
    mission = _lookup(MISSIONS, params.mission, "mission")
    material = _lookup(MATERIALS, params.material, "material")
    tool = _lookup(TOOLS, params.tool, "tool")
    wrong_tool = _lookup(TOOLS, params.wrong_tool, "wrong tool")
    misunderstanding = _lookup(MISUNDERSTANDINGS, params.misunderstanding, "misunderstanding")
    teamwork = _lookup(TEAM_MOVES, params.teamwork, "teamwork")

    combo = (mission.id, material.id, tool.id, wrong_tool.id, misunderstanding.id, teamwork.id)
    if combo not in valid_combos():
        raise StoryError(explain_combo_rejection(mission, material, tool, wrong_tool, misunderstanding, teamwork))

    world = tell(
        mission=mission,
        material=material,
        tool=tool,
        wrong_tool=wrong_tool,
        misunderstanding=misunderstanding,
        teamwork=teamwork,
        captain_name=params.captain,
        captain_gender=params.captain_gender,
        partner_name=params.partner,
        partner_gender=params.partner_gender,
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


# ---------------------------------------------------------------------------
# Curated set
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(
        mission="beacon",
        material="star_sand",
        tool="scoop",
        wrong_tool="brush",
        misunderstanding="echo",
        teamwork="replay_radio",
        captain="Luna",
        captain_gender="girl",
        partner="Nico",
        partner_gender="boy",
    ),
    StoryParams(
        mission="garden",
        material="comet_water",
        tool="vial",
        wrong_tool="fan",
        misunderstanding="point",
        teamwork="read_label",
        captain="Kai",
        captain_gender="boy",
        partner="Mira",
        partner_gender="girl",
    ),
    StoryParams(
        mission="map",
        material="spark_crystals",
        tool="magnet_claw",
        wrong_tool="polisher",
        misunderstanding="assumption",
        teamwork="ask_rover",
        captain="Nova",
        captain_gender="girl",
        partner="Finn",
        partner_gender="boy",
    ),
    StoryParams(
        mission="beacon",
        material="star_sand",
        tool="scoop",
        wrong_tool="brush",
        misunderstanding="point",
        teamwork="count_together",
        captain="Arlo",
        captain_gender="boy",
        partner="Skye",
        partner_gender="girl",
    ),
]


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/6."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid (mission, material, tool, wrong_tool, misunderstanding, teamwork) combos:\n")
        for mission, material, tool, wrong_tool, misunderstanding, teamwork in combos:
            print(f"  {mission:7} {material:14} {tool:12} {wrong_tool:12} {misunderstanding:14} {teamwork}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(params) for params in CURATED]
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
            header = (
                f"### {p.captain} & {p.partner}: {p.mission} with {p.material} "
                f"({p.tool} vs {p.wrong_tool}, {p.misunderstanding}, {p.teamwork})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
