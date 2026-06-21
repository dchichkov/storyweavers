#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/milk_dim_hallelujahs_teamwork_misunderstanding_tall_tale.py
======================================================================================

A standalone storyworld for a tall-tale misunderstanding: in a milk-dim dawn,
two children try to help a whole town hoist something absurdly large, fetch the
wrong kind of line, and tangle the job before teamwork sets it right.

This world is built around:
- a child-sized misunderstanding with a giant-sized consequence,
- teamwork as the real solution,
- exaggerated tall-tale scale without leaving common sense behind.

Run it
------
    python storyworlds/worlds/gpt-5.4/milk_dim_hallelujahs_teamwork_misunderstanding_tall_tale.py
    python storyworlds/worlds/gpt-5.4/milk_dim_hallelujahs_teamwork_misunderstanding_tall_tale.py --task banner --mixup clothesline
    python storyworlds/worlds/gpt-5.4/milk_dim_hallelujahs_teamwork_misunderstanding_tall_tale.py --fix windlass --team-size 1
    python storyworlds/worlds/gpt-5.4/milk_dim_hallelujahs_teamwork_misunderstanding_tall_tale.py --all
    python storyworlds/worlds/gpt-5.4/milk_dim_hallelujahs_teamwork_misunderstanding_tall_tale.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/milk_dim_hallelujahs_teamwork_misunderstanding_tall_tale.py --json
    python storyworlds/worlds/gpt-5.4/milk_dim_hallelujahs_teamwork_misunderstanding_tall_tale.py --verify
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
        female = {"girl", "mother", "aunt", "woman"}
        male = {"boy", "father", "uncle", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def title(self) -> str:
        return {"aunt": "Aunt", "uncle": "Uncle"}.get(self.type, self.label or self.type)
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
class Task:
    id: str
    label: str
    target_label: str
    opening: str
    scale: str
    place: str
    goal_text: str
    ending_image: str
    needed_kind: str = "haul_line"
    heft: int = 4
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
class Mixup:
    id: str
    heard_for: str
    mistaken_label: str
    mistaken_phrase: str
    wrong_kind: str
    confusion: str
    snag_text: str
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


@dataclass
class Fix:
    id: str
    label: str
    method: str
    helpers_needed: int
    power: int
    qa_text: str
    ending_text: str
    required_kind: str = "haul_line"
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
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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


def _r_snag(world: World) -> list[str]:
    target = world.get("target")
    wrong = world.get("wrong_line")
    if wrong.meters["attached"] < THRESHOLD:
        return []
    sig = ("snag", wrong.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    target.meters["snagged"] += 1
    target.meters["raised"] = 0.0
    for kid_id in ("kid1", "kid2"):
        world.get(kid_id).memes["worry"] += 1
    world.get("caller").memes["alarm"] += 1
    return ["__snag__"]


def _r_raise(world: World) -> list[str]:
    target = world.get("target")
    right = world.get("right_line")
    team = world.get("team")
    if right.meters["attached"] < THRESHOLD:
        return []
    if team.meters["hands"] < world.facts["helpers_needed"]:
        return []
    if team.meters["pull"] + world.facts["fix_power"] < world.facts["task_heft"]:
        return []
    sig = ("raise", right.id, int(team.meters["hands"]))
    if sig in world.fired:
        return []
    world.fired.add(sig)
    target.meters["snagged"] = 0.0
    target.meters["raised"] += 1
    team.memes["pride"] += 1
    for kid_id in ("kid1", "kid2"):
        world.get(kid_id).memes["relief"] += 1
        world.get(kid_id).memes["pride"] += 1
    world.get("square").memes["joy"] += 1
    return ["__raised__"]


CAUSAL_RULES = [
    Rule(name="snag", tag="physical", apply=_r_snag),
    Rule(name="raise", tag="physical", apply=_r_raise),
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
        for sent in produced:
            world.say(sent)
    return produced


TASKS = {
    "banner": Task(
        id="banner",
        label="sunrise banner",
        target_label="the breakfast banner",
        opening="The town of Clover Fork woke in a milk-dim dawn with one job left before breakfast fair.",
        scale="The banner was so broad it could have shaded a pasture and so long it needed one end tied to the mill and the other to the grain tower.",
        place="across Main Street between the old mill and the grain tower",
        goal_text="hoist the giant breakfast banner before the first biscuit came out of the oven",
        ending_image="When it finally flew overhead, the painted flapjacks on it looked big enough to feed the county.",
        heft=4,
        tags={"banner", "fair"},
    ),
    "kite": Task(
        id="kite",
        label="parade kite",
        target_label="the parade kite",
        opening="The town of Clover Fork woke in a milk-dim dawn on the day of the wind parade.",
        scale="The kite was stitched from flour sacks and bright scraps until it looked less like a toy and more like a sky-sized rooster with a tail over three fences long.",
        place="above the town square and the pumpkin patch behind it",
        goal_text="pull the parade kite into the wind before the fiddlers reached the square",
        ending_image="Once it climbed, its tail combed the clouds and made the crows fly in formation.",
        heft=3,
        tags={"kite", "parade"},
    ),
    "bell": Task(
        id="bell",
        label="breakfast bell",
        target_label="the breakfast bell",
        opening="The town of Clover Fork woke in a milk-dim dawn needing one more miracle before morning stew.",
        scale="The bell was so grand that when it rang proper, spoons trembled in cupboards clear out by the creek.",
        place="onto the high frame beside the smokehouse",
        goal_text="haul the breakfast bell into its frame before the cooks needed to call the field hands",
        ending_image="At the end it hung high and steady, and its first boom rolled over the hills like a friendly thunderclap.",
        heft=5,
        tags={"bell", "breakfast"},
    ),
}

MIXUPS = {
    "clothesline": Mixup(
        id="clothesline",
        heard_for="haul_line",
        mistaken_label="clothesline",
        mistaken_phrase="the clean washing line from behind the boardinghouse",
        wrong_kind="laundry_line",
        confusion='heard "line" and thought any line would do',
        snag_text="The thin line sang one brave note, then bit into the load, twisted sideways, and wrapped the job into a knot as cross as a nest of snakes.",
        qa_text="They used a clothesline, which was far too thin for such a giant job. It tangled instead of hauling, because washing line is for shirts, not town-sized lifting.",
        tags={"line", "clothesline"},
    ),
    "fishing_line": Mixup(
        id="fishing_line",
        heard_for="haul_line",
        mistaken_label="fishing line",
        mistaken_phrase="a shiny spool of fishing line from the bait shed",
        wrong_kind="fishing_line",
        confusion='heard "line" and ran for the finest line by the river',
        snag_text="The shiny line flashed in the dawn, went tight for a blink, and then sawed itself into a glittery snarl that held nothing except trouble.",
        qa_text="They fetched fishing line because they focused on the word line and forgot the hauling part. Fishing line is clever for trout, but much too slight for lifting a giant town thing.",
        tags={"line", "fishing"},
    ),
    "reins": Mixup(
        id="reins",
        heard_for="haul_line",
        mistaken_label="wagon reins",
        mistaken_phrase="the long wagon reins from the feed shed",
        wrong_kind="reins",
        confusion='heard the call in a hurry and brought the leather lines used for steering mules',
        snag_text="The reins slapped, stretched crooked, and dragged the load half sideways until the whole business sat there sulking and stuck.",
        qa_text="They brought wagon reins, which can guide an animal but are not made to hoist a huge load. The mistake pulled the job sideways and left it stuck.",
        tags={"line", "wagon"},
    ),
}

FIXES = {
    "porch_pull": Fix(
        id="porch_pull",
        label="porch pull",
        method="looped the real haul line through the high pulley and had everyone on the porch rail lean back together on the count of three",
        helpers_needed=2,
        power=2,
        qa_text="They used the real haul line and pulled together in one steady rhythm. Teamwork mattered because one child alone could not make the lift smooth or strong enough.",
        ending_text="The porch boards hummed, boots slid, elbows locked, and up the load went as if the whole town had become one pair of giant hands.",
        tags={"teamwork", "pull"},
    ),
    "mule_team": Fix(
        id="mule_team",
        label="mule team",
        method="hitched the real haul line to Old June and Old Jasper, the calmest mules in Clover Fork, while the children guided the slack and shouted the count",
        helpers_needed=1,
        power=3,
        qa_text="They switched to the real haul line and let the mule team provide the heavy pull while the children helped guide it. That worked because the mules added strength and the people added care.",
        ending_text="The mules leaned as steady as sunrise, and the load rose so smooth it looked as if the morning itself was lifting it.",
        tags={"teamwork", "mules"},
    ),
    "windlass": Fix(
        id="windlass",
        label="windlass",
        method="wrapped the real haul line around the old windlass by the smokehouse while every helper took a handle and walked it around together",
        helpers_needed=3,
        power=1,
        qa_text="They fed the real haul line through the windlass and turned it together. The machine gave control, but it still needed several helpers working as one.",
        ending_text="Round and round they went until the windlass groaned like a sleepy giant and the load climbed one patient click at a time.",
        tags={"teamwork", "windlass"},
    ),
}

GIRL_NAMES = ["Mabel", "Josie", "Ruth", "Nell", "Ada", "Birdie", "Liza", "Maybelle"]
BOY_NAMES = ["Eli", "Hank", "Otis", "Wade", "Finn", "Levi", "Jude", "Cal"]
CALLERS = [
    ("Aunt Tilda", "aunt"),
    ("Uncle Buck", "uncle"),
    ("Miss Rowena", "woman"),
]


def valid_combo(task: Task, mixup: Mixup, fix: Fix, team_size: int) -> bool:
    if task.needed_kind != mixup.heard_for:
        return False
    if task.needed_kind != fix.required_kind:
        return False
    if team_size < fix.helpers_needed:
        return False
    if team_size + fix.power < task.heft:
        return False
    return True


def valid_combos() -> list[tuple[str, str, str, int]]:
    out: list[tuple[str, str, str, int]] = []
    for task_id, task in TASKS.items():
        for mix_id, mixup in MIXUPS.items():
            for fix_id, fix in FIXES.items():
                for team_size in range(1, 5):
                    if valid_combo(task, mixup, fix, team_size):
                        out.append((task_id, mix_id, fix_id, team_size))
    return out


def explain_rejection(task: Task, mixup: Mixup, fix: Fix, team_size: int) -> str:
    if task.needed_kind != mixup.heard_for:
        return (f"(No story: the misunderstanding '{mixup.id}' does not fit the job "
                f"'{task.id}' because that job is not asking for the same kind of line.)")
    if task.needed_kind != fix.required_kind:
        return (f"(No story: the fix '{fix.id}' does not use the sturdy haul line this "
                f"job requires, so it would not honestly solve the tangle.)")
    if team_size < fix.helpers_needed:
        return (f"(No story: {fix.label} needs at least {fix.helpers_needed} helpers, "
                f"but team-size {team_size} is too small for real teamwork.)")
    if team_size + fix.power < task.heft:
        return (f"(No story: even with {team_size} helpers, {fix.label} is too weak for "
                f"the giant {task.label}. Pick a stronger fix or a bigger team.)")
    return "(No story: that combination does not pass the reasonableness gate.)"


def predict_snag(world: World) -> bool:
    sim = world.copy()
    sim.get("wrong_line").meters["attached"] += 1
    propagate(sim, narrate=False)
    return sim.get("target").meters["snagged"] >= THRESHOLD


def dawn_setup(world: World, task: Task, kid1: Entity, kid2: Entity, caller: Entity) -> None:
    for kid in (kid1, kid2):
        kid.memes["joy"] += 1
        kid.memes["eagerness"] += 1
    world.say(task.opening)
    world.say(task.scale)
    world.say(
        f"{caller.id} clapped once and said that if the children helped {task.goal_text}, "
        f"the whole street would remember them till next winter."
    )


def assign_job(world: World, task: Task, caller: Entity, kid1: Entity, kid2: Entity) -> None:
    world.say(
        f'"You two scamper and fetch me the haul line," {caller.id} called. '
        f'"We need it {task.place} before the sun gets bossy."'
    )
    world.say(
        f"{kid1.id} and {kid2.id} tore off so fast that dust tried to keep up with them and lost."
    )


def fetch_wrong_line(world: World, kid1: Entity, kid2: Entity, mixup: Mixup) -> None:
    kid1.memes["confidence"] += 1
    kid2.memes["confidence"] += 1
    world.say(
        f"But {kid1.id} {mixup.confusion}, and {kid2.id} agreed before anybody stopped to ask twice."
    )
    world.say(
        f"So back they came dragging {mixup.mistaken_phrase}, sure they had saved the whole morning."
    )


def wrong_attempt(world: World, task: Task, mixup: Mixup, caller: Entity) -> None:
    world.get("wrong_line").meters["attached"] += 1
    propagate(world, narrate=False)
    target = world.get("target")
    if target.meters["snagged"] >= THRESHOLD:
        world.say(
            f"They tied on the {mixup.mistaken_label} and gave one mighty yank at {task.target_label}."
        )
        world.say(mixup.snag_text)
        world.say(
            f'{caller.id} threw both hands in the air. "That is a fine line for its own chores," '
            f'{world.get("caller").pronoun()} said, "but not for this one!"'
        )


def realize(world: World, kid1: Entity, kid2: Entity, mixup: Mixup, caller: Entity) -> None:
    kid1.memes["embarrassment"] += 1
    kid2.memes["embarrassment"] += 1
    world.say(
        f"{kid1.id} stared at the knot, and {kid2.id} stared at {kid1.pronoun('object')}, "
        f"and both of them understood the mix-up at the same moment."
    )
    world.say(
        f'"We brought the wrong kind of line," {kid2.id} admitted. '
        f'{caller.id} nodded, already reaching to untwist the snarl instead of scolding.'
    )


def gather_team(world: World, kid1: Entity, kid2: Entity, caller: Entity, task: Task, fix: Fix) -> None:
    team = world.get("team")
    world.say(
        f"{caller.id} sent word down the street, and in no time neighbors appeared on porches, "
        f"from the bakery door, and out of the feed shed until there were {int(team.meters['hands'])} helpers in all."
    )
    world.say(
        f"{kid1.id} fetched the real haul line this time, and {kid2.id} helped clear the last twist from {task.target_label}."
    )
    world.say(
        f"Then everybody {fix.method}."
    )


def lift_together(world: World, task: Task, fix: Fix) -> None:
    world.get("right_line").meters["attached"] += 1
    propagate(world, narrate=False)
    target = world.get("target")
    if target.meters["raised"] >= THRESHOLD:
        world.say(fix.ending_text)
        world.say(task.ending_image)
        world.say(
            f"When the job was done, cheers leapt up and rolled into a full armload of hallelujahs."
        )


def closing(world: World, kid1: Entity, kid2: Entity, caller: Entity, task: Task) -> None:
    kid1.memes["trust"] += 1
    kid2.memes["trust"] += 1
    world.say(
        f'{caller.id} bent down with a grin. "A mistake can knot a morning," {caller.pronoun()} said, '
        f'"but a town that works together can unknot it before breakfast."'
    )
    world.say(
        f"{kid1.id} and {kid2.id} grinned at each other, dusty and proud, while {task.target_label} shone high over Clover Fork."
    )


def tell(
    task: Task,
    mixup: Mixup,
    fix: Fix,
    team_size: int,
    kid1_name: str,
    kid1_gender: str,
    kid2_name: str,
    kid2_gender: str,
    caller_name: str,
    caller_type: str,
) -> World:
    world = World()
    kid1 = world.add(Entity(id="kid1", kind="character", type=kid1_gender, label=kid1_name, role="lead"))
    kid2 = world.add(Entity(id="kid2", kind="character", type=kid2_gender, label=kid2_name, role="partner"))
    caller = world.add(Entity(id="caller", kind="character", type=caller_type, label=caller_name, role="caller"))
    square = world.add(Entity(id="square", type="place", label="the square"))
    target = world.add(Entity(id="target", type="load", label=task.target_label))
    wrong_line = world.add(Entity(id="wrong_line", type=mixup.wrong_kind, label=mixup.mistaken_label))
    right_line = world.add(Entity(id="right_line", type="haul_line", label="haul line"))
    team = world.add(Entity(id="team", type="crew", label="the helpers"))

    team.meters["hands"] = float(team_size)
    team.meters["pull"] = float(team_size)

    world.facts.update(
        task=task,
        mixup=mixup,
        fix=fix,
        team_size=team_size,
        helpers_needed=fix.helpers_needed,
        fix_power=fix.power,
        task_heft=task.heft,
        target_before=False,
        target_after=False,
    )

    dawn_setup(world, task, kid1, kid2, caller)
    world.para()
    assign_job(world, task, caller, kid1, kid2)
    fetch_wrong_line(world, kid1, kid2, mixup)
    wrong_attempt(world, task, mixup, caller)
    world.facts["target_before"] = target.meters["snagged"] >= THRESHOLD

    world.para()
    realize(world, kid1, kid2, mixup, caller)
    gather_team(world, kid1, kid2, caller, task, fix)
    lift_together(world, task, fix)
    world.facts["target_after"] = target.meters["raised"] >= THRESHOLD

    world.para()
    closing(world, kid1, kid2, caller, task)

    world.facts.update(
        kid1=kid1,
        kid2=kid2,
        caller=caller,
        square=square,
        target=target,
        wrong_line=wrong_line,
        right_line=right_line,
        team=team,
        outcome="raised" if target.meters["raised"] >= THRESHOLD else "stuck",
    )
    return world


def display_name(ent: Entity) -> str:
    return ent.label or ent.id


def generation_prompts(world: World) -> list[str]:
    task = world.facts["task"]
    mixup = world.facts["mixup"]
    fix = world.facts["fix"]
    kid1 = world.facts["kid1"]
    kid2 = world.facts["kid2"]
    return [
        f'Write a tall-tale story for a young child that uses the words "milk-dim" and "hallelujahs" and centers on teamwork after a misunderstanding.',
        f"Tell a giant-hearted frontier story where {display_name(kid1)} and {display_name(kid2)} fetch the wrong line for a huge town job, then help fix it together.",
        f"Write a cheerful tall tale about {task.label}, a mix-up with {mixup.mistaken_label}, and a teamwork solution using {fix.label}.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    task = world.facts["task"]
    mixup = world.facts["mixup"]
    fix = world.facts["fix"]
    kid1 = world.facts["kid1"]
    kid2 = world.facts["kid2"]
    caller = world.facts["caller"]
    team_size = int(world.facts["team_size"])
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {display_name(kid1)} and {display_name(kid2)}, two children helping {display_name(caller)} with {task.label} in Clover Fork. The whole town matters too, because the job is far too big for one person.",
        ),
        (
            f"What were they trying to do?",
            f"They were trying to {task.goal_text}. In tall-tale style, the job was so enormous it took the whole town's attention.",
        ),
        (
            "What was the misunderstanding?",
            f"{display_name(kid1)} and {display_name(kid2)} were told to fetch the haul line, but they brought {mixup.mistaken_phrase} instead. They latched onto the word line and missed the part about needing the strong kind for lifting.",
        ),
        (
            "What happened when they used the wrong line?",
            f"{mixup.qa_text} That is why the giant job snagged instead of rising.",
        ),
        (
            "How did they solve the problem?",
            f"{fix.qa_text} There were {team_size} helpers, so the children were part of a real team instead of trying to fix the trouble alone.",
        ),
        (
            "How did the story end?",
            f"{task.target_label.capitalize()} ended up high where it belonged, and the town cheered with hallelujahs. The ending proves what changed: the knot of misunderstanding turned into a smooth piece of teamwork.",
        ),
    ]
    return qa


KNOWLEDGE = {
    "line": [
        (
            "Why does a big lifting job need a strong line?",
            "A big load pulls hard, so the line must be thick and sturdy enough to hold steady. A weak line can twist, snap, or tangle instead of helping.",
        )
    ],
    "clothesline": [
        (
            "What is a clothesline for?",
            "A clothesline is for hanging wet clothes so they can dry in the air. It is not meant for lifting giant heavy things.",
        )
    ],
    "fishing": [
        (
            "What is fishing line used for?",
            "Fishing line is used to catch fish because it is thin and light. That makes it useful in water, but much too slight for hauling a huge load.",
        )
    ],
    "wagon": [
        (
            "What are wagon reins for?",
            "Wagon reins help guide an animal pulling a wagon. They steer, but they are not the same as a hauling rope for lifting.",
        )
    ],
    "teamwork": [
        (
            "Why can teamwork solve a job better than one person?",
            "Teamwork lets people share strength, timing, and careful watching. One person may pull hard, but several people working together can pull hard in the same direction.",
        )
    ],
    "mules": [
        (
            "Why are mules good at pulling?",
            "Mules are strong and steady, and they do not rush when the work gets heavy. That makes them good helpers for slow, careful pulling.",
        )
    ],
    "windlass": [
        (
            "What does a windlass do?",
            "A windlass is a turning machine that winds up rope or line bit by bit. It helps lift heavy things in a slower, more controlled way.",
        )
    ],
    "banner": [
        (
            "What is a banner?",
            "A banner is a big sign made of cloth or fabric, often hung up where lots of people can see it. People use banners for fairs, parades, and celebrations.",
        )
    ],
    "kite": [
        (
            "What helps a kite rise?",
            "A kite rises when wind pushes against it and a line keeps it guided. If the line tangles, the kite cannot fly properly.",
        )
    ],
    "bell": [
        (
            "Why do towns ring bells?",
            "Bells can call people to meals, work, or gatherings because their sound travels far. A big bell is like a voice the whole town can hear.",
        )
    ],
}
KNOWLEDGE_ORDER = [
    "line",
    "clothesline",
    "fishing",
    "wagon",
    "teamwork",
    "mules",
    "windlass",
    "banner",
    "kite",
    "bell",
]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    task = world.facts["task"]
    mixup = world.facts["mixup"]
    fix = world.facts["fix"]
    tags = set(task.tags) | set(mixup.tags) | set(fix.tags)
    tags.add("line")
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
        lines.append(f"  {ent.id:10} ({ent.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


@dataclass
class StoryParams:
    task: str
    mixup: str
    fix: str
    team_size: int
    kid1_name: str
    kid1_gender: str
    kid2_name: str
    kid2_gender: str
    caller_name: str
    caller_type: str
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
        task="banner",
        mixup="clothesline",
        fix="porch_pull",
        team_size=2,
        kid1_name="Mabel",
        kid1_gender="girl",
        kid2_name="Eli",
        kid2_gender="boy",
        caller_name="Aunt Tilda",
        caller_type="aunt",
    ),
    StoryParams(
        task="kite",
        mixup="fishing_line",
        fix="mule_team",
        team_size=1,
        kid1_name="Josie",
        kid1_gender="girl",
        kid2_name="Hank",
        kid2_gender="boy",
        caller_name="Uncle Buck",
        caller_type="uncle",
    ),
    StoryParams(
        task="bell",
        mixup="reins",
        fix="mule_team",
        team_size=2,
        kid1_name="Ruth",
        kid1_gender="girl",
        kid2_name="Otis",
        kid2_gender="boy",
        caller_name="Miss Rowena",
        caller_type="woman",
    ),
    StoryParams(
        task="banner",
        mixup="fishing_line",
        fix="windlass",
        team_size=3,
        kid1_name="Ada",
        kid1_gender="girl",
        kid2_name="Levi",
        kid2_gender="boy",
        caller_name="Uncle Buck",
        caller_type="uncle",
    ),
    StoryParams(
        task="kite",
        mixup="reins",
        fix="porch_pull",
        team_size=2,
        kid1_name="Birdie",
        kid1_gender="girl",
        kid2_name="Cal",
        kid2_gender="boy",
        caller_name="Aunt Tilda",
        caller_type="aunt",
    ),
]


ASP_RULES = r"""
heard_for(M,K) :- misunderstanding(M), mixup_for(M,K).
usable_fix(F,K) :- fix(F), requires(F,K).

valid(T,M,F,N) :- task(T), misunderstanding(M), fix(F), team_size(N),
                  needs_kind(T,K), heard_for(M,K), usable_fix(F,K),
                  helpers_needed(F,H), N >= H,
                  power(F,P), heft(T,W), N + P >= W.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for task_id, task in TASKS.items():
        lines.append(asp.fact("task", task_id))
        lines.append(asp.fact("needs_kind", task_id, task.needed_kind))
        lines.append(asp.fact("heft", task_id, task.heft))
    for mix_id, mixup in MIXUPS.items():
        lines.append(asp.fact("misunderstanding", mix_id))
        lines.append(asp.fact("mixup_for", mix_id, mixup.heard_for))
    for fix_id, fix in FIXES.items():
        lines.append(asp.fact("fix", fix_id))
        lines.append(asp.fact("requires", fix_id, fix.required_kind))
        lines.append(asp.fact("helpers_needed", fix_id, fix.helpers_needed))
        lines.append(asp.fact("power", fix_id, fix.power))
    for n in range(1, 5):
        lines.append(asp.fact("team_size", n))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def smoke_story() -> None:
    sample = generate(CURATED[0])
    if not sample.story.strip():
        raise StoryError("Smoke test failed: generated story was empty.")
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        emit(sample, trace=False, qa=False, header="SMOKE")
    if "SMOKE" not in buf.getvalue():
        raise StoryError("Smoke test failed: emit() did not print the sample header.")


def asp_verify() -> int:
    rc = 0
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: ASP gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH between ASP and Python valid_combos():")
        if clingo_set - python_set:
            print("  only in ASP:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in Python:", sorted(python_set - clingo_set))

    try:
        smoke_story()
        default_params = resolve_params(build_parser().parse_args([]), random.Random(0))
        default_params.seed = 0
        sample = generate(default_params)
        if not sample.story.strip():
            raise StoryError("Default generate() returned an empty story.")
        sample.to_json()
        print("OK: smoke test passed for emit(), generate(), and JSON serialization.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Tall-tale storyworld: a misunderstood line, a giant town job, and teamwork that sets it right."
    )
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--mixup", choices=MIXUPS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--team-size", type=int, choices=[1, 2, 3, 4])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP gate and run smoke tests")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_kid(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.task and args.mixup and args.fix and args.team_size:
        task = TASKS[args.task]
        mixup = MIXUPS[args.mixup]
        fix = FIXES[args.fix]
        if not valid_combo(task, mixup, fix, args.team_size):
            raise StoryError(explain_rejection(task, mixup, fix, args.team_size))

    combos = [
        combo for combo in valid_combos()
        if (args.task is None or combo[0] == args.task)
        and (args.mixup is None or combo[1] == args.mixup)
        and (args.fix is None or combo[2] == args.fix)
        and (args.team_size is None or combo[3] == args.team_size)
    ]
    if not combos:
        if args.task and args.mixup and args.fix and args.team_size:
            raise StoryError(explain_rejection(TASKS[args.task], MIXUPS[args.mixup], FIXES[args.fix], args.team_size))
        raise StoryError("(No valid combination matches the given options.)")

    task_id, mixup_id, fix_id, team_size = rng.choice(sorted(combos))
    kid1_name, kid1_gender = _pick_kid(rng)
    kid2_name, kid2_gender = _pick_kid(rng, avoid=kid1_name)
    caller_name, caller_type = rng.choice(CALLERS)
    return StoryParams(
        task=task_id,
        mixup=mixup_id,
        fix=fix_id,
        team_size=team_size,
        kid1_name=kid1_name,
        kid1_gender=kid1_gender,
        kid2_name=kid2_name,
        kid2_gender=kid2_gender,
        caller_name=caller_name,
        caller_type=caller_type,
    )


def generate(params: StoryParams) -> StorySample:
    if params.task not in TASKS:
        raise StoryError(f"(Unknown task: {params.task})")
    if params.mixup not in MIXUPS:
        raise StoryError(f"(Unknown mixup: {params.mixup})")
    if params.fix not in FIXES:
        raise StoryError(f"(Unknown fix: {params.fix})")
    if params.team_size not in {1, 2, 3, 4}:
        raise StoryError(f"(Invalid team-size: {params.team_size})")

    task = TASKS[params.task]
    mixup = MIXUPS[params.mixup]
    fix = FIXES[params.fix]
    if not valid_combo(task, mixup, fix, params.team_size):
        raise StoryError(explain_rejection(task, mixup, fix, params.team_size))

    world = tell(
        task=task,
        mixup=mixup,
        fix=fix,
        team_size=params.team_size,
        kid1_name=params.kid1_name,
        kid1_gender=params.kid1_gender,
        kid2_name=params.kid2_name,
        kid2_gender=params.kid2_gender,
        caller_name=params.caller_name,
        caller_type=params.caller_type,
    )
    return StorySample(
        params=params,
        story=world.render().replace("kid1", params.kid1_name).replace("kid2", params.kid2_name).replace("caller", params.caller_name),
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
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (task, mixup, fix, team-size) combos:\n")
        for task_id, mixup_id, fix_id, team_size in combos:
            print(f"  {task_id:7} {mixup_id:13} {fix_id:10} team={team_size}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        samples: list[StorySample] = []
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
            header = f"### {p.task} / {p.mixup} / {p.fix} / team {p.team_size}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
