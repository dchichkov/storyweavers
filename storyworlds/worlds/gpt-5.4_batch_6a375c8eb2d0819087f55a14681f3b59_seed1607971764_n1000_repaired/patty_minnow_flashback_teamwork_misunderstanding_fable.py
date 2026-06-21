#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/patty_minnow_flashback_teamwork_misunderstanding_fable.py
=====================================================================================

A standalone story world for a small fable-shaped pond tale: Patty, a careful
pond creature, misunderstands a minnow's secretive behavior while trying to
solve a simple community problem. A flashback explains the fear behind the
mistake, teamwork repairs the situation, and the ending image proves the lesson.

Run it
------
    python storyworlds/worlds/gpt-5.4/patty_minnow_flashback_teamwork_misunderstanding_fable.py
    python storyworlds/worlds/gpt-5.4/patty_minnow_flashback_teamwork_misunderstanding_fable.py --task banner --misread hiding
    python storyworlds/worlds/gpt-5.4/patty_minnow_flashback_teamwork_misunderstanding_fable.py --task stepping_stones --helper frog
    python storyworlds/worlds/gpt-5.4/patty_minnow_flashback_teamwork_misunderstanding_fable.py --all --qa
    python storyworlds/worlds/gpt-5.4/patty_minnow_flashback_teamwork_misunderstanding_fable.py --trace --seed 7
    python storyworlds/worlds/gpt-5.4/patty_minnow_flashback_teamwork_misunderstanding_fable.py --verify
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
TRUST_FLOOR = 2
TEAMWORK_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    tools: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "hen", "duck", "goose"}
        male = {"boy", "father", "drake"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def title(self) -> str:
        if self.label:
            return self.label
        return self.id
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
    need: str
    place: str
    opening: str
    goal: str
    object_label: str
    build_label: str
    gather_verb: str
    finish_image: str
    helper_method: str
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
class Misread:
    id: str
    cue: str
    suspicion: str
    reveal: str
    ask: str
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
class HelperKind:
    id: str
    species: str
    label: str
    skill: str
    motion: str
    contribution: str
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


def _r_hurt_from_misread(world: World) -> list[str]:
    out: list[str] = []
    patty = world.get("patty")
    helper = world.get("helper")
    if patty.memes["blurted"] >= THRESHOLD and helper.memes["accused"] < THRESHOLD:
        sig = ("hurt", helper.id)
        if sig not in world.fired:
            world.fired.add(sig)
            helper.memes["hurt"] += 1
            helper.memes["accused"] += 1
            patty.memes["trust"] -= 1
            out.append("__hurt__")
    return out


def _r_plan_if_shared(world: World) -> list[str]:
    out: list[str] = []
    patty = world.get("patty")
    helper = world.get("helper")
    task = world.get("task")
    if helper.memes["explained"] >= THRESHOLD and patty.memes["listened"] >= THRESHOLD:
        sig = ("plan", task.id)
        if sig not in world.fired:
            world.fired.add(sig)
            patty.memes["trust"] += 2
            patty.memes["shame"] += 1
            helper.memes["forgiveness"] += 1
            patty.meters["teamwork"] += 1
            helper.meters["teamwork"] += 1
            out.append("__plan__")
    return out


def _r_finish_if_enough_hands(world: World) -> list[str]:
    out: list[str] = []
    patty = world.get("patty")
    helper = world.get("helper")
    task = world.get("task")
    if patty.meters["teamwork"] + helper.meters["teamwork"] >= TEAMWORK_MIN:
        sig = ("finish", task.id)
        if sig not in world.fired:
            world.fired.add(sig)
            task.meters["built"] += 1
            patty.memes["relief"] += 1
            helper.memes["relief"] += 1
            out.append("__finished__")
    return out


CAUSAL_RULES = [
    Rule(name="hurt_from_misread", tag="social", apply=_r_hurt_from_misread),
    Rule(name="plan_if_shared", tag="social", apply=_r_plan_if_shared),
    Rule(name="finish_if_enough_hands", tag="physical", apply=_r_finish_if_enough_hands),
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


TASKS = {
    "banner": Task(
        id="banner",
        need="the pond feast could not begin until a lily-ribbon banner was hung",
        place="the old willow root by the clear pond",
        opening="The reeds had been braided, but the banner still drooped in the mud.",
        goal="hang the lily-ribbon banner above the feast path",
        object_label="the lily-ribbon banner",
        build_label="a neat green arch",
        gather_verb="pull the ribbon through the reeds",
        finish_image="the banner swayed over the path like a green smile",
        helper_method="thread the ribbon through the narrow water gaps",
        tags={"banner", "feast", "teamwork"},
    ),
    "stepping_stones": Task(
        id="stepping_stones",
        need="the ducklings could not reach the berry patch unless a safe crossing was set in place",
        place="the shallow bend where the brook met the pond",
        opening="Flat stones lay nearby, but the line across the water was not finished.",
        goal="set a path of stepping stones across the brook",
        object_label="the stone path",
        build_label="a tidy stepping path",
        gather_verb="nudge each stone into the right place",
        finish_image="the stones sat still as buttons from bank to bank",
        helper_method="show where the water was calmest underneath",
        tags={"stones", "crossing", "teamwork"},
    ),
    "shade_sail": Task(
        id="shade_sail",
        need="the tadpoles' resting corner was too bright until a leaf sail was tied up",
        place="the sunny edge of the cattail pool",
        opening="A broad leaf waited on the bank, but one side kept slipping down.",
        goal="tie a leaf sail above the tadpoles' resting pool",
        object_label="the leaf sail",
        build_label="a cool leaf roof",
        gather_verb="fasten the leaf corners to the cattail stems",
        finish_image="the leaf roof cast a soft green shadow on the water",
        helper_method="guide the cord below the surface and back up again",
        tags={"shade", "tadpoles", "teamwork"},
    ),
}

MISREADS = {
    "hiding": Misread(
        id="hiding",
        cue="kept darting behind the rushes with little loops and splashes",
        suspicion="Patty thought the minnow was hiding pieces away for himself",
        reveal="the minnow had tucked the pieces in the still water so the current would not steal them",
        ask='“Why are you hiding things?” Patty cried.',
        tags={"hiding", "misunderstanding"},
    ),
    "whispering": Misread(
        id="whispering",
        cue="kept whispering with the snails under the bank",
        suspicion="Patty thought the minnow was gossiping instead of helping",
        reveal="the minnow was asking the snails which side of the bank was firmest",
        ask='“Why are you whispering when work is waiting?” Patty asked.',
        tags={"whispering", "misunderstanding"},
    ),
    "circling": Misread(
        id="circling",
        cue="kept circling the same dark patch of water",
        suspicion="Patty thought the minnow was playing while everyone else worried",
        reveal="the minnow was testing the tug of the current before anyone laid a piece there",
        ask='“Why are you playing in circles?” Patty said.',
        tags={"circling", "misunderstanding"},
    ),
}

HELPERS = {
    "minnow": HelperKind(
        id="minnow",
        species="minnow",
        label="a silver minnow",
        skill="quick underwater eyes",
        motion="flicked through the water like a bright needle",
        contribution="could see what the current was doing where feet could not reach",
        tags={"minnow", "water", "teamwork"},
    ),
    "frog": HelperKind(
        id="frog",
        species="frog",
        label="a mossy frog",
        skill="springy pushing legs",
        motion="splashed from stone to stone with easy hops",
        contribution="could push and brace heavy things with strong wet feet",
        tags={"frog", "teamwork"},
    ),
    "beetle": HelperKind(
        id="beetle",
        species="beetle",
        label="a lacquer-black beetle",
        skill="steady gripping feet",
        motion="hurried along stems with shiny patience",
        contribution="could hold knots in place without slipping",
        tags={"beetle", "teamwork"},
    ),
}


def valid_combo(task_id: str, helper_id: str) -> bool:
    task = TASKS[task_id]
    helper = HELPERS[helper_id]
    if helper_id == "minnow":
        return True
    if helper_id == "frog":
        return task_id in {"stepping_stones", "shade_sail"}
    if helper_id == "beetle":
        return task_id in {"banner", "shade_sail"}
    return False


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for task_id in TASKS:
        for misread_id in MISREADS:
            for helper_id in HELPERS:
                if valid_combo(task_id, helper_id):
                    combos.append((task_id, misread_id, helper_id))
    return combos


@dataclass
class StoryParams:
    task: str
    misread: str
    helper: str
    patty_kind: str = "turtle"
    elder: str = "heron"
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


def opening(world: World, patty: Entity, task: Task, helper_kind: HelperKind) -> None:
    patty.memes["duty"] += 1
    world.say(
        f"At {task.place}, Patty the {patty.type} had promised to {task.goal}. "
        f"{task.need}."
    )
    world.say(task.opening)
    world.say(
        f"Near her worked {helper_kind.label}, who {helper_kind.motion} and "
        f"offered {helper_kind.contribution}."
    )


def begin_work(world: World, patty: Entity, helper: Entity, task: Task) -> None:
    patty.meters["effort"] += 1
    helper.meters["effort"] += 1
    world.say(
        f"Patty bent to {task.gather_verb}, and the little helper moved close to {task.helper_method}."
    )
    world.say(
        f"For a while, the two seemed to labor toward the same good end."
    )


def flashback(world: World, patty: Entity, elder: Entity) -> None:
    patty.memes["memory"] += 1
    patty.memes["fear"] += 1
    world.say(
        f"Yet when the water made a sly little sucking sound, Patty remembered another morning. "
        f"In that older hour, {elder.label} had warned her not to judge by splashes alone."
    )
    world.say(
        "She had ignored the warning then, snatched at a drifting reed by herself, "
        "and watched the current carry the whole bundle away. Ever since, haste had sat in her shell beside caution."
    )


def misread_scene(world: World, patty: Entity, helper: Entity, misread: Misread) -> None:
    patty.memes["suspicion"] += 1
    helper.attrs["cue"] = misread.id
    world.say(
        f"But the helper {misread.cue}, and {misread.suspicion}."
    )
    world.say(misread.ask)
    patty.memes["blurted"] += 1
    propagate(world, narrate=False)


def consequence(world: World, patty: Entity, helper: Entity, task: Task) -> None:
    if helper.memes["hurt"] >= THRESHOLD:
        world.say(
            f"The little helper stopped short. The work on {task.object_label} stopped too, "
            f"for hurt feelings can tangle a plan as surely as weeds tangle a string."
        )


def reveal(world: World, helper: Entity, task: Task, misread: Misread) -> None:
    helper.memes["explained"] += 1
    world.say(
        f'The helper answered softly, "I was not hiding from the work. {misread.reveal}."'
    )
    world.say(
        f'"If I do my part below and you do yours above, we can finish {task.object_label} together."'
    )


def listen_and_repair(world: World, patty: Entity, helper: Entity) -> None:
    patty.memes["listened"] += 1
    propagate(world, narrate=False)
    world.say(
        "Then Patty grew quiet enough to hear more than her own worry."
    )
    world.say(
        '“I spoke too soon,” she said. “A busy splash is not always a selfish splash. Show me your part, and I will show you mine.”'
    )


def finish_task(world: World, patty: Entity, helper: Entity, task: Task) -> None:
    propagate(world, narrate=False)
    if world.get("task").meters["built"] < THRESHOLD:
        raise StoryError("(Internal story error: teamwork should have completed the task.)")
    world.say(
        f"So Patty worked above the water while the helper worked below it, and their two small skills fitted together like reed and knot."
    )
    world.say(
        f"Before long they had made {task.build_label}, and {task.finish_image}."
    )


def moral(world: World, patty: Entity, helper: Entity, helper_kind: HelperKind) -> None:
    world.say(
        f"From then on, Patty looked twice before she blamed once, especially when {helper_kind.species} work seemed strange from the bank."
    )
    world.say(
        "For in ponds as in the wide world, many a good friend appears odd only because he is helping from another side."
    )


def tell(
    task: Task,
    misread: Misread,
    helper_kind: HelperKind,
    patty_kind: str = "turtle",
    elder_kind: str = "heron",
) -> World:
    world = World()
    patty = world.add(Entity(
        id="patty",
        kind="character",
        type=patty_kind,
        label=f"Patty the {patty_kind}",
        role="patty",
        attrs={"memory_source": elder_kind},
    ))
    helper = world.add(Entity(
        id="helper",
        kind="character",
        type=helper_kind.species,
        label=helper_kind.label,
        role="helper",
        attrs={"species_name": helper_kind.species},
    ))
    elder = world.add(Entity(
        id="elder",
        kind="character",
        type=elder_kind,
        label=f"the old {elder_kind}",
        role="elder",
    ))
    task_ent = world.add(Entity(
        id="task",
        kind="thing",
        type="project",
        label=task.object_label,
        role="task",
    ))

    patty.memes["trust"] = 3
    patty.memes["listened"] = 0
    patty.memes["blurted"] = 0
    helper.memes["explained"] = 0
    helper.memes["hurt"] = 0
    helper.memes["forgiveness"] = 0
    patty.meters["teamwork"] = 0
    helper.meters["teamwork"] = 0
    task_ent.meters["built"] = 0

    world.facts.update(
        task_cfg=task,
        misread_cfg=misread,
        helper_cfg=helper_kind,
        patty=patty,
        helper=helper,
        elder=elder,
        task=task_ent,
        misunderstanding=False,
        repaired=False,
        built=False,
    )

    opening(world, patty, task, helper_kind)
    begin_work(world, patty, helper, task)

    world.para()
    flashback(world, patty, elder)
    misread_scene(world, patty, helper, misread)
    consequence(world, patty, helper, task)

    world.para()
    reveal(world, helper, task, misread)
    listen_and_repair(world, patty, helper)
    finish_task(world, patty, helper, task)
    moral(world, patty, helper, helper_kind)

    world.facts["misunderstanding"] = helper.memes["hurt"] >= THRESHOLD
    world.facts["repaired"] = patty.memes["trust"] >= 4 and helper.memes["forgiveness"] >= THRESHOLD
    world.facts["built"] = task_ent.meters["built"] >= THRESHOLD
    world.facts["lesson"] = "look twice before blaming once"
    return world


KNOWLEDGE = {
    "minnow": [(
        "What is a minnow?",
        "A minnow is a very small fish that can move quickly through shallow water. Because it is so small, it can notice little currents and tight watery spaces."
    )],
    "teamwork": [(
        "What is teamwork?",
        "Teamwork means two or more helpers using their different skills for the same job. A task often becomes easier when each helper does the part they can do best."
    )],
    "misunderstanding": [(
        "What is a misunderstanding?",
        "A misunderstanding happens when someone thinks they know another person's meaning, but they are wrong. Asking and listening can untie a misunderstanding before it grows."
    )],
    "flashback": [(
        "What is a flashback in a story?",
        "A flashback is a short look back at something that happened earlier. It helps explain why a character feels afraid, angry, or careful in the present."
    )],
    "pond": [(
        "Why can work look different above water and below water?",
        "Above water you can see banks, leaves, and ropes, but below water the current pushes things in hidden ways. That is why one helper may understand a part of the job another helper cannot see."
    )],
    "moral": [(
        "What lesson does this fable teach?",
        "It teaches that strange-looking help is not always bad help. You should ask before blaming and listen before deciding."
    )],
}
KNOWLEDGE_ORDER = ["minnow", "teamwork", "misunderstanding", "flashback", "pond", "moral"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    task = f["task_cfg"]
    misread = f["misread_cfg"]
    helper = f["helper_cfg"]
    return [
        f'Write a short fable that includes the words "patty" and "minnow", uses a flashback, and ends with a teamwork lesson.',
        f"Tell a pond fable where Patty misunderstands {helper.species} behavior while trying to {task.goal}, then learns the truth and works together.",
        f"Write a gentle animal fable about a misunderstanding caused by someone who {misread.cue}, with a clear moral about asking before blaming.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    patty = f["patty"]
    helper = f["helper"]
    task = f["task_cfg"]
    misread = f["misread_cfg"]
    elder = f["elder"]
    helper_kind = f["helper_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {patty.label} and {helper.label} at the pond. They were trying to {task.goal}."
        ),
        (
            "What problem needed to be solved?",
            f"They needed to {task.goal}, because {task.need}. The unfinished work meant others could not use that part of the pond properly."
        ),
        (
            "What did Patty misunderstand?",
            f"Patty saw that the helper {misread.cue}, and she thought that meant something selfish or lazy. Really, the helper was doing a hidden part of the work where Patty could not see clearly."
        ),
        (
            "What was the flashback about?",
            f"The flashback returned to an older morning when {elder.label} had warned Patty not to judge by splashes alone. Patty remembered losing a bundle of reeds when she acted too quickly by herself, which is why fear mixed with her caution."
        ),
    ]
    if f["repaired"]:
        qa.append((
            "How did they fix the misunderstanding?",
            f"The helper explained what was really happening under the water, and Patty became quiet enough to listen. Then she apologized and invited the helper to show their part, which turned blame into a shared plan."
        ))
    if f["built"]:
        qa.append((
            "How did teamwork help them finish the job?",
            f"Patty worked above the water while the helper worked below it, so each one handled the part the other could not reach well. Their different skills fit together, and that is why the task was finished."
        ))
        qa.append((
            "How did the story end?",
            f"It ended with the work completed and {task.finish_image}. That final picture shows that trust had been repaired as well as the task."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"teamwork", "misunderstanding", "flashback", "pond", "moral"}
    helper_kind = world.facts["helper_cfg"]
    if helper_kind.id == "minnow":
        tags.add("minnow")
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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:8} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


def explain_rejection(task_id: str, helper_id: str) -> str:
    task = TASKS[task_id]
    helper = HELPERS[helper_id]
    return (
        f"(No story: {helper.label} is not a reasonable helper for {task.object_label}. "
        f"This world only keeps combinations where the helper's body and skill fit the task.)"
    )


CURATED = [
    StoryParams(
        task="banner",
        misread="hiding",
        helper="minnow",
        patty_kind="turtle",
        elder="heron",
    ),
    StoryParams(
        task="stepping_stones",
        misread="circling",
        helper="frog",
        patty_kind="turtle",
        elder="crane",
    ),
    StoryParams(
        task="shade_sail",
        misread="whispering",
        helper="beetle",
        patty_kind="turtle",
        elder="heron",
    ),
    StoryParams(
        task="shade_sail",
        misread="hiding",
        helper="minnow",
        patty_kind="turtle",
        elder="otter",
    ),
]


ASP_RULES = r"""
valid_helper(T,H) :- task(T), helper(H), can_help(H,T).
valid(T,M,H) :- task(T), misread(M), valid_helper(T,H).

% Social outcome model for this world.
misunderstanding :- misread(_).
hurt(1) :- misunderstanding.
trust_after_repair(4) :- hurt(1).
teamwork_total(2) :- trust_after_repair(4).
built :- teamwork_total(T), teamwork_min(M), T >= M.
repaired :- trust_after_repair(T), trust_floor(F), T >= F.

#show valid/3.
#show built/0.
#show repaired/0.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for task_id in TASKS:
        lines.append(asp.fact("task", task_id))
    for misread_id in MISREADS:
        lines.append(asp.fact("misread", misread_id))
    for helper_id in HELPERS:
        lines.append(asp.fact("helper", helper_id))
    for task_id in TASKS:
        for helper_id in HELPERS:
            if valid_combo(task_id, helper_id):
                lines.append(asp.fact("can_help", helper_id, task_id))
    lines.append(asp.fact("teamwork_min", TEAMWORK_MIN))
    lines.append(asp.fact("trust_floor", TRUST_FLOOR))
    return "\n".join(lines)


def asp_program(extra: str = "") -> str:
    return f"{asp_facts()}\n{extra}\n{ASP_RULES}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> tuple[bool, bool]:
    import asp

    extra = "\n".join([
        asp.fact("chosen_task", params.task),
        asp.fact("chosen_misread", params.misread),
        asp.fact("chosen_helper", params.helper),
    ])
    model = asp.one_model(asp_program(extra))
    built = bool(asp.atoms(model, "built"))
    repaired = bool(asp.atoms(model, "repaired"))
    return built, repaired


def outcome_of(params: StoryParams) -> tuple[bool, bool]:
    if not valid_combo(params.task, params.helper):
        return False, False
    return True, True


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
        params.seed = seed
        cases.append(params)

    mismatches = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            mismatches += 1
    if mismatches == 0:
        print(f"OK: outcome model matches Python on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {mismatches}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("(Smoke test failed: empty story.)")
        emit(smoke, trace=False, qa=False, header="")
        print("OK: smoke test generate/emit passed.")
    except Exception as err:  # pragma: no cover - verify path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: Patty, a misunderstanding, a flashback, and teamwork at the pond."
    )
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--misread", choices=MISREADS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--patty-kind", choices=["turtle"], dest="patty_kind")
    ap.add_argument("--elder", choices=["heron", "crane", "otter"])
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
    if args.task and args.helper and not valid_combo(args.task, args.helper):
        raise StoryError(explain_rejection(args.task, args.helper))

    combos = [
        combo for combo in valid_combos()
        if (args.task is None or combo[0] == args.task)
        and (args.misread is None or combo[1] == args.misread)
        and (args.helper is None or combo[2] == args.helper)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    task_id, misread_id, helper_id = rng.choice(sorted(combos))
    patty_kind = args.patty_kind or "turtle"
    elder = args.elder or rng.choice(["heron", "crane", "otter"])
    return StoryParams(
        task=task_id,
        misread=misread_id,
        helper=helper_id,
        patty_kind=patty_kind,
        elder=elder,
    )


def generate(params: StoryParams) -> StorySample:
    if params.task not in TASKS:
        raise StoryError(f"(Unknown task: {params.task})")
    if params.misread not in MISREADS:
        raise StoryError(f"(Unknown misread: {params.misread})")
    if params.helper not in HELPERS:
        raise StoryError(f"(Unknown helper: {params.helper})")
    if not valid_combo(params.task, params.helper):
        raise StoryError(explain_rejection(params.task, params.helper))

    world = tell(
        task=TASKS[params.task],
        misread=MISREADS[params.misread],
        helper_kind=HELPERS[params.helper],
        patty_kind=params.patty_kind,
        elder_kind=params.elder,
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
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (task, misread, helper) combos:\n")
        for task_id, misread_id, helper_id in combos:
            print(f"  {task_id:15} {misread_id:10} {helper_id}")
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
            header = f"### {p.task} / {p.misread} / {p.helper}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
