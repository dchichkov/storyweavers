#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/imbalance_win_quest_teamwork_sharing_space_adventure.py
===================================================================================

A standalone storyworld about a small space quest where an *imbalance* in the
crew's cargo stops progress, and the children learn to fix it through teamwork
and sharing so they can *win* together.

The domain is intentionally small and constraint-checked:

* Two children and a little helper robot head out on a quest.
* They load glowing mission cargo onto a small rover.
* If one child hoards too much on one side, the rover tilts from imbalance.
* A sensible fix must actually rebalance the load and involve sharing.
* The ending proves the change: the rover rolls straight, the quest succeeds,
  and the team wins together.

Run it
------
    python storyworlds/worlds/gpt-5.4/imbalance_win_quest_teamwork_sharing_space_adventure.py
    python storyworlds/worlds/gpt-5.4/imbalance_win_quest_teamwork_sharing_space_adventure.py --mission beacon --cargo crystals
    python storyworlds/worlds/gpt-5.4/imbalance_win_quest_teamwork_sharing_space_adventure.py --fix keep_all
    python storyworlds/worlds/gpt-5.4/imbalance_win_quest_teamwork_sharing_space_adventure.py --all
    python storyworlds/worlds/gpt-5.4/imbalance_win_quest_teamwork_sharing_space_adventure.py -n 5 --seed 7
    python storyworlds/worlds/gpt-5.4/imbalance_win_quest_teamwork_sharing_space_adventure.py --qa --json
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2


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
    side: str = ""
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Mission:
    id: str
    place: str
    sky: str
    goal: str
    problem: str
    finish: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Cargo:
    id: str
    label: str
    phrase: str
    unit: str
    left_stack: str
    right_stack: str
    reward: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Vehicle:
    id: str
    label: str
    phrase: str
    left_bin: str
    right_bin: str
    path: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Helper:
    id: str
    label: str
    beep: str
    gift: str
    tags: set[str] = field(default_factory=set)


@dataclass
class FixPlan:
    id: str
    sense: int
    balances: bool
    shares: bool
    text: str
    qa_text: str
    ending: str
    tags: set[str] = field(default_factory=set)


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
        return self.entities[eid]

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"captain", "copilot"}]

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


def _r_detect_imbalance(world: World) -> list[str]:
    rover = world.get("rover")
    left = rover.meters["left_load"]
    right = rover.meters["right_load"]
    gap = abs(left - right)
    if gap < THRESHOLD:
        return []
    sig = ("imbalance", int(left), int(right))
    if sig in world.fired:
        return []
    world.fired.add(sig)
    rover.meters["imbalance"] = float(gap)
    rover.meters["stuck"] = 1.0
    for kid in world.kids():
        kid.memes["worry"] += 1
    return ["__imbalance__"]


def _r_balance_rolls(world: World) -> list[str]:
    rover = world.get("rover")
    left = rover.meters["left_load"]
    right = rover.meters["right_load"]
    if abs(left - right) >= THRESHOLD or left <= 0 or right <= 0:
        return []
    sig = ("balanced", int(left), int(right))
    if sig in world.fired:
        return []
    world.fired.add(sig)
    rover.meters["steady"] = 1.0
    rover.meters["stuck"] = 0.0
    for kid in world.kids():
        kid.memes["hope"] += 1
    return []


def _r_finish(world: World) -> list[str]:
    rover = world.get("rover")
    if rover.meters["steady"] < THRESHOLD:
        return []
    beacon = world.get("goal")
    if beacon.meters["powered"] >= THRESHOLD:
        return []
    sig = ("finish",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    beacon.meters["powered"] = 1.0
    for kid in world.kids():
        kid.memes["joy"] += 1
        kid.memes["lesson"] += 1
    return ["__finish__"]


CAUSAL_RULES = [
    Rule(name="detect_imbalance", tag="physical", apply=_r_detect_imbalance),
    Rule(name="balance_rolls", tag="physical", apply=_r_balance_rolls),
    Rule(name="finish", tag="physical", apply=_r_finish),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for sent in produced:
            world.say(sent)
    return produced


def sensible_fixes() -> list[FixPlan]:
    return [plan for plan in FIXES.values() if plan.sense >= SENSE_MIN]


def valid_combo(mission_id: str, cargo_id: str, vehicle_id: str, helper_id: str, fix_id: str) -> bool:
    fix = FIXES[fix_id]
    return fix.sense >= SENSE_MIN and fix.balances and fix.shares


def valid_combos() -> list[tuple[str, str, str, str, str]]:
    combos: list[tuple[str, str, str, str, str]] = []
    for mission_id in MISSIONS:
        for cargo_id in CARGOES:
            for vehicle_id in VEHICLES:
                for helper_id in HELPERS:
                    for fix_id in FIXES:
                        if valid_combo(mission_id, cargo_id, vehicle_id, helper_id, fix_id):
                            combos.append((mission_id, cargo_id, vehicle_id, helper_id, fix_id))
    return combos


def predict_roll(world: World) -> dict:
    sim = world.copy()
    propagate(sim, narrate=False)
    rover = sim.get("rover")
    return {
        "left": rover.meters["left_load"],
        "right": rover.meters["right_load"],
        "imbalance": rover.meters["imbalance"],
        "stuck": rover.meters["stuck"] >= THRESHOLD,
    }


def setup_scene(world: World, captain: Entity, copilot: Entity, mission: Mission,
                vehicle: Vehicle, helper: Helper) -> None:
    for kid in (captain, copilot):
        kid.memes["wonder"] += 1
    world.say(
        f"Under {mission.sky}, {captain.id} and {copilot.id} turned the yard into {mission.place}. "
        f"Their {vehicle.label} waited by the stepping-stone launch pad, and {helper.label} blinked nearby."
    )
    world.say(
        f'"Crew ready!" {captain.id} said. "Our quest is to {mission.goal}."'
    )
    world.say(
        f'{helper.beep} {helper.label.capitalize()} flashed a tiny light as if it agreed.'
    )


def mission_need(world: World, copilot: Entity, mission: Mission, cargo: Cargo) -> None:
    copilot.memes["care"] += 1
    world.say(
        f"But first they had to carry {cargo.phrase} across {world.get('rover').attrs['path']} to {mission.problem}."
    )
    world.say(
        f'{copilot.id} looked at the glowing {cargo.label}. "If we bring them there, we can {mission.finish}," {copilot.pronoun()} said.'
    )


def grab_too_much(world: World, captain: Entity, copilot: Entity, cargo: Cargo, vehicle: Vehicle) -> None:
    rover = world.get("rover")
    captain.memes["eager"] += 1
    captain.memes["grabby"] += 1
    rover.meters["left_load"] = 3.0
    rover.meters["right_load"] = 1.0
    world.facts["initial_split"] = {"left": 3, "right": 1}
    world.say(
        f"{captain.id} hurried first and stacked three {cargo.unit}s into {vehicle.left_bin}. "
        f"{copilot.id} only had time to place one in {vehicle.right_bin}."
    )
    propagate(world, narrate=False)


def warn_imbalance(world: World, copilot: Entity, captain: Entity, cargo: Cargo, vehicle: Vehicle) -> None:
    pred = predict_roll(world)
    rover = world.get("rover")
    world.facts["predicted_imbalance"] = pred["imbalance"]
    world.say(
        f'{copilot.id} grabbed the handle and felt the {vehicle.label} lean. "Wait," {copilot.pronoun()} said. '
        f'"There is an imbalance. {vehicle.left_bin.capitalize()} is heavier than {vehicle.right_bin}, so we cannot roll straight."'
    )
    if pred["stuck"]:
        world.say(
            f"The front wheel wobbled against a moon-rock bump, and the quest stopped before it had truly begun."
        )
    rover.meters["stuck"] = 1.0


def feelings_turn(world: World, captain: Entity, copilot: Entity) -> None:
    captain.memes["frustration"] += 1
    copilot.memes["patience"] += 1
    world.say(
        f'{captain.id} frowned. "{world.facts["mission"].goal.capitalize()} is my idea. I wanted to be first so we could win."'
    )
    world.say(
        f'{copilot.id} touched the side of the {world.get("rover").label}. "We only win if the whole crew gets there together," {copilot.pronoun()} said.'
    )


def apply_fix(world: World, captain: Entity, copilot: Entity, helper: Helper,
              cargo: Cargo, vehicle: Vehicle, fix: FixPlan) -> None:
    rover = world.get("rover")
    captain.memes["sharing"] += 1 if fix.shares else 0
    copilot.memes["sharing"] += 1 if fix.shares else 0
    captain.memes["teamwork"] += 1 if fix.balances else 0
    copilot.memes["teamwork"] += 1 if fix.balances else 0
    helper.memes["helping"] += 1
    world.say(fix.text.format(
        captain=captain.id,
        copilot=copilot.id,
        helper=helper.label,
        cargo_unit=cargo.unit,
        cargo_label=cargo.label,
        left_bin=vehicle.left_bin,
        right_bin=vehicle.right_bin,
    ))
    if fix.balances:
        rover.meters["left_load"] = 2.0
        rover.meters["right_load"] = 2.0
        world.facts["final_split"] = {"left": 2, "right": 2}
    propagate(world, narrate=False)


def travel_and_win(world: World, captain: Entity, copilot: Entity, mission: Mission,
                   cargo: Cargo, vehicle: Vehicle, helper: Helper, fix: FixPlan) -> None:
    rover = world.get("rover")
    beacon = world.get("goal")
    if rover.meters["steady"] < THRESHOLD or beacon.meters["powered"] < THRESHOLD:
        raise StoryError("The chosen fix did not lead to a completed quest.")
    captain.memes["pride"] += 1
    copilot.memes["pride"] += 1
    world.say(
        f"Now the {vehicle.label} rolled smoothly along {vehicle.path}. "
        f"{captain.id} pulled on one side, {copilot.id} steered the other, and {helper.label} danced ahead."
    )
    world.say(
        f"When they reached {mission.problem}, the crew set down the {cargo.label}, and a soft glow spread over it."
    )
    world.say(
        f"{mission.finish.capitalize()}, and the team gave a little jump. They had won the quest by sharing the work instead of grabbing it alone."
    )
    world.say(
        fix.ending.format(
            captain=captain.id,
            copilot=copilot.id,
            helper=helper.label,
            reward=cargo.reward,
            gift=helper.gift,
        )
    )


def tell(mission: Mission, cargo: Cargo, vehicle: Vehicle, helper_cfg: Helper,
         fix: FixPlan, captain_name: str = "Milo", captain_type: str = "boy",
         copilot_name: str = "Nova", copilot_type: str = "girl",
         parent_type: str = "mother") -> World:
    world = World()
    captain = world.add(Entity(id=captain_name, kind="character", type=captain_type, role="captain"))
    copilot = world.add(Entity(id=copilot_name, kind="character", type=copilot_type, role="copilot"))
    helper = world.add(Entity(id="helper", kind="character", type="robot", role="helper",
                              label=helper_cfg.label, phrase=helper_cfg.label, tags=set(helper_cfg.tags)))
    parent = world.add(Entity(id="parent", kind="character", type=parent_type, role="parent", label="the parent"))
    rover = world.add(Entity(id="rover", type="vehicle", label=vehicle.label, phrase=vehicle.phrase,
                             attrs={"path": vehicle.path}))
    goal = world.add(Entity(id="goal", type="goal", label=mission.problem, phrase=mission.problem))

    world.facts.update(
        mission=mission,
        cargo=cargo,
        vehicle=vehicle,
        helper_cfg=helper_cfg,
        fix=fix,
        captain=captain,
        copilot=copilot,
        helper=helper,
        parent=parent,
    )

    setup_scene(world, captain, copilot, mission, vehicle, helper_cfg)
    mission_need(world, copilot, mission, cargo)

    world.para()
    grab_too_much(world, captain, copilot, cargo, vehicle)
    warn_imbalance(world, copilot, captain, cargo, vehicle)
    feelings_turn(world, captain, copilot)

    world.para()
    apply_fix(world, captain, copilot, helper, cargo, vehicle, fix)
    travel_and_win(world, captain, copilot, mission, cargo, vehicle, helper_cfg, fix)

    world.facts.update(
        outcome="won",
        imbalanced=world.get("rover").meters["imbalance"] >= THRESHOLD,
        steady=world.get("rover").meters["steady"] >= THRESHOLD,
        powered=world.get("goal").meters["powered"] >= THRESHOLD,
        shared=fix.shares,
    )
    return world


MISSIONS = {
    "beacon": Mission(
        id="beacon",
        place="a silver little moon base",
        sky="a dark blue evening full of paper stars",
        goal="light the sleepy beacon tower",
        problem="the sleepy beacon tower at the far crater",
        finish="the beacon tower shone like a safe star for every explorer coming home",
        tags={"beacon", "quest"},
    ),
    "garden": Mission(
        id="garden",
        place="a tiny Mars garden station",
        sky="a purple dusk with one bright planet hanging low",
        goal="wake the thirsty moon garden",
        problem="the thirsty moon garden beyond the dusty ridge",
        finish="the moon garden blinked green, and its leaves lifted toward the light",
        tags={"garden", "quest"},
    ),
    "flag": Mission(
        id="flag",
        place="a red-rock planet path",
        sky="a velvet sky where the first stars were peeking out",
        goal="power the singing flag post",
        problem="the singing flag post on the windy hill",
        finish="the flag post began to hum a brave tune across the hill",
        tags={"flag", "quest"},
    ),
}

CARGOES = {
    "crystals": Cargo(
        id="crystals",
        label="star crystals",
        phrase="four glowing star crystals",
        unit="crystal",
        left_stack="left crystal stack",
        right_stack="right crystal stack",
        reward="the empty crystal box like a treasure chest",
        tags={"crystals", "sharing"},
    ),
    "water": Cargo(
        id="water",
        label="water pods",
        phrase="four round water pods",
        unit="pod",
        left_stack="left pod stack",
        right_stack="right pod stack",
        reward="the shiny blue pod case",
        tags={"water", "sharing"},
    ),
    "seeds": Cargo(
        id="seeds",
        label="sun-seed jars",
        phrase="four warm sun-seed jars",
        unit="jar",
        left_stack="left jar stack",
        right_stack="right jar stack",
        reward="the little seed tray",
        tags={"seeds", "sharing"},
    ),
}

VEHICLES = {
    "rover": Vehicle(
        id="rover",
        label="moon rover",
        phrase="a squat moon rover with two side bins",
        left_bin="the left bin",
        right_bin="the right bin",
        path="a bumpy ribbon of moon dust",
        tags={"rover"},
    ),
    "cart": Vehicle(
        id="cart",
        label="rocket cart",
        phrase="a red rocket cart with two side baskets",
        left_bin="the left basket",
        right_bin="the right basket",
        path="a glittery lane between cardboard craters",
        tags={"cart"},
    ),
    "sled": Vehicle(
        id="sled",
        label="comet sled",
        phrase="a smooth comet sled with two cargo trays",
        left_bin="the left tray",
        right_bin="the right tray",
        path="a pale track over soft silver sand",
        tags={"sled"},
    ),
}

HELPERS = {
    "pip": Helper(
        id="pip",
        label="Pip the robot",
        beep="Bip-bip!",
        gift="a tiny sticker shaped like a comet",
        tags={"robot", "helper"},
    ),
    "twirl": Helper(
        id="twirl",
        label="Twirl the robot",
        beep="Whirr-zip!",
        gift="a paper badge with a gold star",
        tags={"robot", "helper"},
    ),
    "dot": Helper(
        id="dot",
        label="Dot the robot",
        beep="Beep-beep!",
        gift="a bright ribbon for the rover handle",
        tags={"robot", "helper"},
    ),
}

FIXES = {
    "share_evenly": FixPlan(
        id="share_evenly",
        sense=3,
        balances=True,
        shares=True,
        text="{helper} blinked at the bins, and {captain} laughed a little. Then {captain} handed one {cargo_unit} to {copilot}, and together they moved the stacks until each side held two.",
        qa_text="They shared the cargo evenly, with two on each side of the rover.",
        ending="{helper} spun in a happy circle, and {captain} let {copilot} hold {gift} while they carried {reward} back home together.",
        tags={"sharing", "teamwork"},
    ),
    "count_together": FixPlan(
        id="count_together",
        sense=3,
        balances=True,
        shares=True,
        text='"Let us count as a team," said {copilot}. {captain}, {copilot}, and {helper} tapped each {cargo_unit} one by one, then traded places until the load matched on both sides.',
        qa_text="They counted the cargo together and traded pieces until both sides matched.",
        ending="Back at base, {captain} and {copilot} took turns wearing {gift}, because winning felt better when it was shared.",
        tags={"sharing", "teamwork", "counting"},
    ),
    "robot_points": FixPlan(
        id="robot_points",
        sense=2,
        balances=True,
        shares=True,
        text="{helper} pointed first to {left_bin}, then to {right_bin}. {captain} understood, passed one {cargo_unit} across to {copilot}, and the crew rearranged the rest side by side.",
        qa_text="The robot helped them notice the heavy side, and then they shared the cargo to balance it.",
        ending="{captain} grinned at {copilot}. They let {helper} ride home on top of {reward}, because the whole crew had earned the ride.",
        tags={"sharing", "teamwork", "robot"},
    ),
    "keep_all": FixPlan(
        id="keep_all",
        sense=1,
        balances=False,
        shares=False,
        text="{captain} tried to keep almost everything on one side and simply pull harder.",
        qa_text="The captain tried to keep all the cargo alone.",
        ending="The rover still leaned.",
        tags={"selfish"},
    ),
}

GIRL_NAMES = ["Nova", "Luna", "Mia", "Zoe", "Ava", "Ruby", "Nora", "Ivy"]
BOY_NAMES = ["Milo", "Leo", "Finn", "Max", "Eli", "Theo", "Kai", "Sam"]


@dataclass
class StoryParams:
    mission: str
    cargo: str
    vehicle: str
    helper: str
    fix: str
    captain_name: str
    captain_gender: str
    copilot_name: str
    copilot_gender: str
    parent: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "imbalance": [
        (
            "What does imbalance mean?",
            "Imbalance means one side has more weight or force than the other side. When things are out of balance, they can wobble, lean, or get stuck.",
        )
    ],
    "sharing": [
        (
            "What does sharing mean?",
            "Sharing means letting other people use or carry part of something instead of keeping it all for yourself. Sharing can make a job fairer and friendlier.",
        )
    ],
    "teamwork": [
        (
            "What is teamwork?",
            "Teamwork is when people help each other do one job together. A team can do better when everyone takes a part.",
        )
    ],
    "rover": [
        (
            "What is a rover?",
            "A rover is a little vehicle that rolls over the ground. In space stories, rovers carry people or supplies across rough places.",
        )
    ],
    "robot": [
        (
            "What is a robot helper?",
            "A robot helper is a machine that can beep, point, or carry out simple jobs. It can help people notice problems and work together.",
        )
    ],
    "beacon": [
        (
            "What is a beacon?",
            "A beacon is a light or signal that helps others find their way. It can show where to go or help people feel safe.",
        )
    ],
    "win": [
        (
            "Can a whole team win together?",
            "Yes. A team wins together when everyone helps and the group reaches its goal. Winning does not have to belong to just one person.",
        )
    ],
}
KNOWLEDGE_ORDER = ["imbalance", "sharing", "teamwork", "rover", "robot", "beacon", "win"]


def pair_noun(a: Entity, b: Entity) -> str:
    if a.type == "boy" and b.type == "boy":
        return "two young space captains"
    if a.type == "girl" and b.type == "girl":
        return "two young space captains"
    return "two young space friends"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    mission = f["mission"]
    cargo = f["cargo"]
    vehicle = f["vehicle"]
    captain = f["captain"]
    copilot = f["copilot"]
    return [
        f'Write a short Space Adventure story for a 3-to-5-year-old that includes the word "imbalance" and ends with the team saying they win together.',
        f"Tell a gentle quest story where {captain.id} and {copilot.id} load {cargo.label} into a {vehicle.label}, discover an imbalance, and fix it through teamwork and sharing.",
        f"Write a child-friendly adventure about a crew trying to {mission.goal}, where the problem is not a monster but a lopsided load that must be balanced fairly.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    captain = f["captain"]
    copilot = f["copilot"]
    helper = f["helper_cfg"]
    mission = f["mission"]
    cargo = f["cargo"]
    vehicle = f["vehicle"]
    fix = f["fix"]
    pair = pair_noun(captain, copilot)
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair}, {captain.id} and {copilot.id}, and {helper.label} on a space quest. They were trying to {mission.goal}.",
        ),
        (
            "What problem stopped the quest at first?",
            f"The {vehicle.label} had an imbalance because one side held more {cargo.label} than the other. That made it lean and stop instead of rolling straight.",
        ),
        (
            f"Why did {captain.id} put too much on one side?",
            f"{captain.id} wanted to be first and hoped the team could win faster that way. But grabbing too much alone made the rover harder to move, not easier.",
        ),
        (
            "How did they fix the imbalance?",
            f"{fix.qa_text} That worked because the load became even, so the {vehicle.label} could roll smoothly again.",
        ),
        (
            "How did sharing help them win?",
            f"Sharing spread the work fairly between both children. Once the cargo was balanced, the whole crew could reach {mission.problem} and finish the quest together.",
        ),
        (
            "How did the story end?",
            f"It ended with the mission working and the children feeling proud together. They won the quest because teamwork was stronger than trying to do everything alone.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"imbalance", "sharing", "teamwork", "win", "robot"}
    mission = world.facts["mission"]
    vehicle = world.facts["vehicle"]
    if "beacon" in mission.tags:
        tags.add("beacon")
    if vehicle.tags:
        tags.add("rover")
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
    for ent in world.entities.values():
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        mission="beacon",
        cargo="crystals",
        vehicle="rover",
        helper="pip",
        fix="share_evenly",
        captain_name="Milo",
        captain_gender="boy",
        copilot_name="Nova",
        copilot_gender="girl",
        parent="mother",
    ),
    StoryParams(
        mission="garden",
        cargo="water",
        vehicle="cart",
        helper="twirl",
        fix="count_together",
        captain_name="Luna",
        captain_gender="girl",
        copilot_name="Leo",
        copilot_gender="boy",
        parent="father",
    ),
    StoryParams(
        mission="flag",
        cargo="seeds",
        vehicle="sled",
        helper="dot",
        fix="robot_points",
        captain_name="Finn",
        captain_gender="boy",
        copilot_name="Ruby",
        copilot_gender="girl",
        parent="mother",
    ),
]


def explain_fix_rejection(fix_id: str) -> str:
    fix = FIXES[fix_id]
    better = ", ".join(sorted(plan.id for plan in sensible_fixes()))
    if fix.sense < SENSE_MIN:
        return (
            f"(Refusing fix '{fix_id}': it is not sensible enough for this storyworld. "
            f"Choose a fix that rebalances the cargo through sharing, such as {better}.)"
        )
    if not fix.balances:
        return f"(Refusing fix '{fix_id}': it does not actually correct the imbalance.)"
    if not fix.shares:
        return f"(Refusing fix '{fix_id}': this world requires sharing as part of the solution.)"
    return "(Refusing fix: invalid plan.)"


ASP_RULES = r"""
sensible_fix(F) :- fix(F), sense(F, S), sense_min(M), S >= M.
valid(M, C, V, H, F) :- mission(M), cargo(C), vehicle(V), helper(H), sensible_fix(F), balances(F), shares(F).

outcome(won) :- chosen_fix(F), balances(F), shares(F), sensible_fix(F).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for mission_id in MISSIONS:
        lines.append(asp.fact("mission", mission_id))
    for cargo_id in CARGOES:
        lines.append(asp.fact("cargo", cargo_id))
    for vehicle_id in VEHICLES:
        lines.append(asp.fact("vehicle", vehicle_id))
    for helper_id in HELPERS:
        lines.append(asp.fact("helper", helper_id))
    for fix_id, fix in FIXES.items():
        lines.append(asp.fact("fix", fix_id))
        lines.append(asp.fact("sense", fix_id, fix.sense))
        if fix.balances:
            lines.append(asp.fact("balances", fix_id))
        if fix.shares:
            lines.append(asp.fact("shares", fix_id))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/5."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join([asp.fact("chosen_fix", params.fix)])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0

    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    cases = list(CURATED)
    for seed in range(20):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(params)

    bad = 0
    for params in cases:
        expected = "won" if valid_combo(params.mission, params.cargo, params.vehicle, params.helper, params.fix) else "?"
        got = asp_outcome(params)
        if got != expected:
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("Generated empty story during verify.")
        print("OK: smoke-tested ordinary story generation.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a space quest where imbalance is solved by teamwork and sharing."
    )
    ap.add_argument("--mission", choices=MISSIONS)
    ap.add_argument("--cargo", choices=CARGOES)
    ap.add_argument("--vehicle", choices=VEHICLES)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--fix", choices=FIXES)
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


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.fix is not None and not valid_combo(
        args.mission or next(iter(MISSIONS)),
        args.cargo or next(iter(CARGOES)),
        args.vehicle or next(iter(VEHICLES)),
        args.helper or next(iter(HELPERS)),
        args.fix,
    ):
        raise StoryError(explain_fix_rejection(args.fix))

    combos = [
        combo for combo in valid_combos()
        if (args.mission is None or combo[0] == args.mission)
        and (args.cargo is None or combo[1] == args.cargo)
        and (args.vehicle is None or combo[2] == args.vehicle)
        and (args.helper is None or combo[3] == args.helper)
        and (args.fix is None or combo[4] == args.fix)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    mission_id, cargo_id, vehicle_id, helper_id, fix_id = rng.choice(sorted(combos))
    captain_gender = rng.choice(["girl", "boy"])
    copilot_gender = rng.choice(["girl", "boy"])
    captain_name = _pick_name(rng, captain_gender)
    copilot_name = _pick_name(rng, copilot_gender, avoid=captain_name)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(
        mission=mission_id,
        cargo=cargo_id,
        vehicle=vehicle_id,
        helper=helper_id,
        fix=fix_id,
        captain_name=captain_name,
        captain_gender=captain_gender,
        copilot_name=copilot_name,
        copilot_gender=copilot_gender,
        parent=parent,
    )


def generate(params: StoryParams) -> StorySample:
    if params.mission not in MISSIONS:
        raise StoryError(f"Unknown mission: {params.mission}")
    if params.cargo not in CARGOES:
        raise StoryError(f"Unknown cargo: {params.cargo}")
    if params.vehicle not in VEHICLES:
        raise StoryError(f"Unknown vehicle: {params.vehicle}")
    if params.helper not in HELPERS:
        raise StoryError(f"Unknown helper: {params.helper}")
    if params.fix not in FIXES:
        raise StoryError(f"Unknown fix: {params.fix}")
    if not valid_combo(params.mission, params.cargo, params.vehicle, params.helper, params.fix):
        raise StoryError(explain_fix_rejection(params.fix))

    world = tell(
        mission=MISSIONS[params.mission],
        cargo=CARGOES[params.cargo],
        vehicle=VEHICLES[params.vehicle],
        helper_cfg=HELPERS[params.helper],
        fix=FIXES[params.fix],
        captain_name=params.captain_name,
        captain_type=params.captain_gender,
        copilot_name=params.copilot_name,
        copilot_type=params.copilot_gender,
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
        print(asp_program("", "#show valid/5.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (mission, cargo, vehicle, helper, fix) combos:\n")
        for mission_id, cargo_id, vehicle_id, helper_id, fix_id in combos:
            print(f"  {mission_id:8} {cargo_id:8} {vehicle_id:7} {helper_id:7} {fix_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
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
            header = f"### {p.captain_name} & {p.copilot_name}: {p.mission} quest with {p.cargo} ({p.fix})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
