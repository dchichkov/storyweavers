#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/comparison_flashback_kindness_slice_of_life.py
=========================================================================

A standalone storyworld about a small classroom craft time: a child makes a
paper project, feels the sting of comparison, remembers an earlier kind moment,
accepts help, and ends by carrying that kindness forward in an ordinary,
slice-of-life way.

The domain is intentionally small and constraint-checked. A story is only valid
when the chosen classroom problem can really be repaired by the chosen kind act,
and when the chosen helper can plausibly do that act. The prose is driven by the
simulated state: comparison raises "smallness," a flashback steadies the child,
a fitting repair changes the project, and the ending image proves what changed.

Run it
------
    python storyworlds/worlds/gpt-5.4/comparison_flashback_kindness_slice_of_life.py
    python storyworlds/worlds/gpt-5.4/comparison_flashback_kindness_slice_of_life.py --task card --problem dull_colors --action share_markers --helper peer
    python storyworlds/worlds/gpt-5.4/comparison_flashback_kindness_slice_of_life.py --problem loose_loop --task card
    python storyworlds/worlds/gpt-5.4/comparison_flashback_kindness_slice_of_life.py --all
    python storyworlds/worlds/gpt-5.4/comparison_flashback_kindness_slice_of_life.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/comparison_flashback_kindness_slice_of_life.py --verify
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
    phrase: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "teacher_f"}
        male = {"boy", "father", "man", "teacher_m"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        if self.type in {"teacher_f", "teacher_m"}:
            return "teacher"
        if self.type == "mother":
            return "mom"
        if self.type == "father":
            return "dad"
        return self.type


@dataclass
class Task:
    id: str
    label: str
    phrase: str
    opening: str
    closing: str
    allows: set[str] = field(default_factory=set)
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
class Problem:
    id: str
    label: str
    appears: str
    needs: str
    fix_result: str
    compare_line: str
    task_ids: set[str] = field(default_factory=set)
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
class Action:
    id: str
    label: str
    repairs: set[str] = field(default_factory=set)
    helpers: set[str] = field(default_factory=set)
    text: str = ""
    qa_text: str = ""
    leaves_spare: bool = False
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
class Memory:
    id: str
    helper: str
    scene: str
    line: str
    effect: str
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
        self.facts: dict = {
            "comparison_triggered": False,
            "flashback": False,
            "fixed": False,
            "passed_forward": False,
            "ending": "",
        }

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


def _r_comparison_sting(world: World) -> list[str]:
    hero = world.get("hero")
    project = world.get("project")
    out: list[str] = []
    if project.meters["problem"] >= THRESHOLD and hero.memes["comparison"] >= THRESHOLD:
        sig = ("comparison_sting",)
        if sig not in world.fired:
            world.fired.add(sig)
            hero.memes["small"] += 1
            out.append("__comparison__")
    return out


def _r_memory_steadies(world: World) -> list[str]:
    hero = world.get("hero")
    out: list[str] = []
    if hero.memes["flashback"] >= THRESHOLD:
        sig = ("memory_steadies",)
        if sig not in world.fired:
            world.fired.add(sig)
            hero.memes["steady"] += 1
            hero.memes["trust"] += 1
            out.append("__flashback__")
    return out


def _r_kindness_fixes(world: World) -> list[str]:
    hero = world.get("hero")
    project = world.get("project")
    helper = world.get("helper")
    out: list[str] = []
    if world.facts.get("action_applied") and project.meters["problem"] >= THRESHOLD:
        sig = ("kindness_fixes",)
        if sig not in world.fired:
            world.fired.add(sig)
            project.meters["problem"] = 0.0
            project.meters["ready"] += 1
            hero.memes["relief"] += 1
            hero.memes["gratitude"] += 1
            helper.memes["kindness"] += 1
            out.append("__fixed__")
    return out


def _r_gratitude_spreads(world: World) -> list[str]:
    hero = world.get("hero")
    out: list[str] = []
    if hero.memes["gratitude"] >= THRESHOLD and world.facts.get("leaves_spare"):
        sig = ("gratitude_spreads",)
        if sig not in world.fired:
            world.fired.add(sig)
            hero.memes["kindness"] += 1
            out.append("__passforward__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="comparison_sting", tag="emotional", apply=_r_comparison_sting),
    Rule(name="memory_steadies", tag="emotional", apply=_r_memory_steadies),
    Rule(name="kindness_fixes", tag="physical", apply=_r_kindness_fixes),
    Rule(name="gratitude_spreads", tag="social", apply=_r_gratitude_spreads),
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
            if sent == "__comparison__":
                world.facts["comparison_triggered"] = True
            elif sent == "__flashback__":
                world.facts["flashback"] = True
            elif sent == "__fixed__":
                world.facts["fixed"] = True
            elif sent == "__passforward__":
                world.facts["passed_forward"] = True
    return produced


TASKS = {
    "card": Task(
        id="card",
        label="thank-you card",
        phrase="a folded thank-you card",
        opening="making thank-you cards for the helpers who kept the school running",
        closing="stood the card up to dry by the window",
        allows={"dull_colors", "torn_corner"},
        tags={"paper", "card"},
    ),
    "bookmark": Task(
        id="bookmark",
        label="bookmark",
        phrase="a paper bookmark with a string loop",
        opening="making bookmarks for the library basket",
        closing="slid the bookmark between the pages of a class book",
        allows={"dull_colors", "torn_corner", "loose_loop"},
        tags={"paper", "bookmark", "library"},
    ),
    "flower": Task(
        id="flower",
        label="paper flower",
        phrase="a paper flower for the windowsill jar",
        opening="cutting paper flowers to brighten the room",
        closing="set the flower in the jar on the windowsill",
        allows={"dull_colors", "torn_corner"},
        tags={"paper", "flower"},
    ),
}

PROBLEMS = {
    "dull_colors": Problem(
        id="dull_colors",
        label="dull colors",
        appears="the bright markers were all gone, and only two tired crayons were left in the tray",
        needs="color",
        fix_result="fresh color returned to the project",
        compare_line="The comparison felt sharp because the project beside it glowed while theirs looked faded.",
        task_ids={"card", "bookmark", "flower"},
        tags={"marker", "color"},
    ),
    "torn_corner": Problem(
        id="torn_corner",
        label="torn corner",
        appears="one corner ripped when the paper caught under a small elbow",
        needs="edge",
        fix_result="the ripped corner was patched neatly",
        compare_line="The comparison felt sharp because the torn edge made the project look clumsy next to the smooth one nearby.",
        task_ids={"card", "bookmark", "flower"},
        tags={"paper", "tape"},
    ),
    "loose_loop": Problem(
        id="loose_loop",
        label="loose loop",
        appears="the string loop slipped right back out of the punched hole",
        needs="loop",
        fix_result="the loop held fast and stopped sliding free",
        compare_line="The comparison felt sharp because the neat bookmark next door already had a tidy loop, and this one would not stay together.",
        task_ids={"bookmark"},
        tags={"string", "bookmark"},
    ),
}

ACTIONS = {
    "share_markers": Action(
        id="share_markers",
        label="share markers",
        repairs={"color"},
        helpers={"peer", "teacher"},
        text="opened a marker case and slid the sunny colors across the table",
        qa_text="shared bright markers",
        leaves_spare=True,
        tags={"marker", "sharing"},
    ),
    "tape_patch": Action(
        id="tape_patch",
        label="tape patch",
        repairs={"edge"},
        helpers={"teacher"},
        text="tore off a small piece of clear tape and showed how to smooth the ripped corner flat",
        qa_text="patched the torn paper with clear tape",
        leaves_spare=False,
        tags={"tape", "repair"},
    ),
    "retie_loop": Action(
        id="retie_loop",
        label="retie loop",
        repairs={"loop"},
        helpers={"peer", "teacher"},
        text="pinched the string carefully and tied a tighter little knot behind the hole",
        qa_text="retied the loop so it would stay in place",
        leaves_spare=False,
        tags={"string", "repair"},
    ),
}

MEMORIES = {
    "peer": Memory(
        id="peer_memory",
        helper="peer",
        scene="last week at the same table",
        line="Last week, when a line of glue had wrinkled the paper, the child beside them had quietly made room and shared what they had.",
        effect="The memory reminded the hero that kindness could make a table feel wide again.",
        tags={"memory", "sharing"},
    ),
    "teacher": Memory(
        id="teacher_memory",
        helper="teacher",
        scene="the first rainy Monday of the month",
        line="On the first rainy Monday of the month, the teacher had knelt beside them, smoothed a bent page, and said that mistakes were smaller than they looked.",
        effect="The memory reminded the hero that a gentle voice could make a big feeling settle down.",
        tags={"memory", "teacher"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Nora", "Maya"]
BOY_NAMES = ["Ben", "Max", "Leo", "Sam", "Noah", "Finn", "Eli", "Theo"]
TRAITS = ["careful", "quiet", "thoughtful", "sensitive", "patient", "gentle"]


def valid_combo(task_id: str, problem_id: str, action_id: str, helper_id: str) -> bool:
    if task_id not in TASKS or problem_id not in PROBLEMS or action_id not in ACTIONS:
        return False
    task = TASKS[task_id]
    problem = PROBLEMS[problem_id]
    action = ACTIONS[action_id]
    if problem_id not in task.allows:
        return False
    if task_id not in problem.task_ids:
        return False
    if problem.needs not in action.repairs:
        return False
    if helper_id not in action.helpers:
        return False
    return True


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for task_id in TASKS:
        for problem_id in PROBLEMS:
            for action_id in ACTIONS:
                for helper_id in ("peer", "teacher"):
                    if valid_combo(task_id, problem_id, action_id, helper_id):
                        combos.append((task_id, problem_id, action_id, helper_id))
    return sorted(combos)


@dataclass
class StoryParams:
    task: str
    problem: str
    action: str
    helper: str
    hero_name: str
    hero_gender: str
    peer_name: str
    peer_gender: str
    teacher_name: str
    teacher_gender: str
    trait: str
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


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices)


def _helper_phrase(world: World) -> str:
    helper = world.get("helper")
    if helper.role == "teacher":
        return f"{helper.attrs['title']} {helper.id}"
    return helper.id


def predict_fix(task_id: str, problem_id: str, action_id: str, helper_id: str) -> dict:
    return {
        "valid": valid_combo(task_id, problem_id, action_id, helper_id),
        "leaves_spare": ACTIONS[action_id].leaves_spare if action_id in ACTIONS else False,
    }


def introduce(world: World, task: Task) -> None:
    hero = world.get("hero")
    peer = world.get("peer")
    world.say(
        f"After lunch, the class was {task.opening}. {hero.id} sat beside {peer.id} at the long table, with scraps of paper, string, and marker caps making a soft little mess between them."
    )
    world.say(
        f"{hero.id} liked quiet jobs with hands and paper. Today {hero.pronoun()} wanted {hero.pronoun('possessive')} {task.label} to look especially nice."
    )


def show_problem(world: World, task: Task, problem: Problem) -> None:
    hero = world.get("hero")
    project = world.get("project")
    hero.memes["comparison"] += 1
    project.meters["problem"] += 1
    world.facts["problem_seen"] = problem.id
    world.say(
        f"But then {problem.appears}. {hero.id} glanced at the neat {task.label} growing under {world.get('peer').id}'s hands and felt a quick pinch of comparison in {hero.pronoun('possessive')} chest."
    )
    propagate(world, narrate=True)
    if hero.memes["small"] >= THRESHOLD:
        world.say(problem.compare_line)


def flashback(world: World, memory: Memory) -> None:
    hero = world.get("hero")
    hero.memes["flashback"] += 1
    propagate(world, narrate=True)
    world.say(
        f"For a moment, {hero.id} remembered {memory.scene}. {memory.line} {memory.effect}"
    )


def hide_then_accept(world: World) -> None:
    hero = world.get("hero")
    helper = world.get("helper")
    hp = _helper_phrase(world)
    world.say(
        f"{hero.id} almost turned {hero.pronoun('possessive')} project a little sideways, as if hiding it might make the feeling smaller. Then {hp} noticed anyway and paused beside the table."
    )
    if helper.role == "teacher":
        world.say(
            f'"Let me see," {helper.attrs["title"]} {helper.id} said in a quiet voice.'
        )
    else:
        world.say(
            f'"Do you want a hand?" {helper.id} asked, not in a bragging way, just kindly.'
        )


def apply_kindness(world: World, action: Action, problem: Problem) -> None:
    helper = world.get("helper")
    hero = world.get("hero")
    world.facts["action_applied"] = True
    world.facts["leaves_spare"] = action.leaves_spare
    propagate(world, narrate=True)
    world.say(
        f"{_helper_phrase(world)} {action.text}. {hero.id} watched, took a breath, and let the help land."
    )
    if world.facts.get("fixed"):
        world.say(
            f"Soon {problem.fix_result}. The worried tightness in {hero.id}'s shoulders loosened."
        )
    if helper.role == "teacher":
        world.say(
            f'"There," {helper.attrs["title"]} {helper.id} said. "Paper can be mended, and so can a hard minute."'
        )
    else:
        world.say(
            f'"There," {helper.id} said. "Now it looks like yours again."'
        )


def finish_project(world: World, task: Task) -> None:
    hero = world.get("hero")
    project = world.get("project")
    project.meters["finished"] += 1
    hero.memes["pride"] += 1
    world.say(
        f"{hero.id} bent over the table again and finished the last small parts without hurrying. When {hero.pronoun()} was done, {hero.pronoun()} {task.closing}."
    )


def pass_kindness_forward(world: World, task: Task) -> None:
    hero = world.get("hero")
    neighbor = world.get("neighbor")
    world.facts["ending"] = "pass_forward"
    world.say(
        f"Across from them, {neighbor.id} whispered that {neighbor.pronoun('possessive')} green marker had dried up too. Because a few bright colors were still lying open between them, {hero.id} slid one over without making a fuss."
    )
    world.say(
        f'"Here," {hero.pronoun()} said. "{task.label.capitalize()}s do not have to match to be good." The table stayed busy and easy, and the comparison from before no longer felt like the biggest thing in the room.'
    )


def quiet_kind_ending(world: World, task: Task) -> None:
    hero = world.get("hero")
    helper = world.get("helper")
    world.facts["ending"] = "quiet_finish"
    target = "the librarian" if task.id == "bookmark" else "the hallway helper"
    if task.id == "flower":
        target = "the custodian who watered the plants"
    world.say(
        f"On the back, {hero.id} added one more line for {target}: \"Thank you for helping even on ordinary days.\""
    )
    world.say(
        f"When {hero.pronoun()} set the finished {task.label} down, {hero.pronoun()} looked up at {_helper_phrase(world)} and smiled a real smile this time. The room was still full of other people's projects, but the comparison had gone soft."
    )


def tell(
    task: Task,
    problem: Problem,
    action: Action,
    memory: Memory,
    hero_name: str,
    hero_gender: str,
    peer_name: str,
    peer_gender: str,
    teacher_name: str,
    teacher_gender: str,
    trait: str,
    helper_kind: str,
) -> World:
    world = World()

    hero = world.add(
        Entity(
            id=hero_name,
            kind="character",
            type=hero_gender,
            role="hero",
            traits=[trait],
            attrs={"trait": trait},
        )
    )
    peer = world.add(
        Entity(
            id=peer_name,
            kind="character",
            type=peer_gender,
            role="peer",
            attrs={},
        )
    )
    teacher_type = "teacher_f" if teacher_gender == "girl" else "teacher_m"
    teacher = world.add(
        Entity(
            id=teacher_name,
            kind="character",
            type=teacher_type,
            role="teacher",
            attrs={"title": "Ms." if teacher_gender == "girl" else "Mr."},
        )
    )
    helper = peer if helper_kind == "peer" else teacher
    project = world.add(
        Entity(
            id="project",
            type="project",
            label=task.label,
            phrase=task.phrase,
            attrs={"task": task.id},
        )
    )
    neighbor = world.add(
        Entity(
            id=_pick_name(random.Random((len(hero_name) + len(peer_name) + len(task.id)) * 17), "girl" if hero_gender == "boy" else "boy", avoid=hero_name),
            kind="character",
            type="girl" if hero_gender == "boy" else "boy",
            role="neighbor",
            attrs={},
        )
    )

    world.entities["helper"] = helper
    world.facts.update(
        hero=hero,
        peer=peer,
        teacher=teacher,
        helper=helper,
        project=project,
        neighbor=neighbor,
        task=task,
        problem=problem,
        action=action,
        memory=memory,
        action_applied=False,
        leaves_spare=action.leaves_spare,
    )

    hero.memes["comparison"] = 0.0
    hero.memes["small"] = 0.0
    hero.memes["flashback"] = 0.0
    hero.memes["steady"] = 0.0
    hero.memes["trust"] = 0.0
    hero.memes["gratitude"] = 0.0
    hero.memes["kindness"] = 0.0
    hero.memes["pride"] = 0.0
    project.meters["problem"] = 0.0
    project.meters["ready"] = 0.0
    project.meters["finished"] = 0.0

    introduce(world, task)

    world.para()
    show_problem(world, task, problem)
    flashback(world, memory)
    hide_then_accept(world)

    world.para()
    apply_kindness(world, action, problem)
    finish_project(world, task)

    if world.facts.get("passed_forward"):
        pass_kindness_forward(world, task)
    else:
        quiet_kind_ending(world, task)

    return world


KNOWLEDGE = {
    "comparison": [
        (
            "What is comparison?",
            "Comparison is when you look at one thing beside another and notice what seems bigger, brighter, faster, or neater. It can help you see differences, but it can also make feelings hurt if you start deciding that different means worse."
        )
    ],
    "flashback": [
        (
            "What is a flashback in a story?",
            "A flashback is a short look back to something that happened earlier. It helps us understand why a character feels or chooses something in the present."
        )
    ],
    "kindness": [
        (
            "What is kindness?",
            "Kindness is choosing to help, comfort, or care for someone in a gentle way. Small kind acts can change how a whole moment feels."
        )
    ],
    "marker": [
        (
            "Why do markers help with paper crafts?",
            "Markers make strong, bright lines and colors on paper. Sharing them can help someone finish a project that looks faded."
        )
    ],
    "tape": [
        (
            "What does tape do on paper?",
            "Tape can hold torn paper together and keep a rip from opening wider. A small patch can make a paper project usable again."
        )
    ],
    "string": [
        (
            "Why do bookmarks sometimes have loops or strings?",
            "A loop gives your fingers something easy to grab and can make a bookmark feel special. If the knot is loose, the string can slide right out."
        )
    ],
    "library": [
        (
            "What does a librarian do?",
            "A librarian helps people find books, keeps shelves in order, and takes care of a place for reading. Libraries work best when many small caring jobs are done."
        )
    ],
    "paper": [
        (
            "Can torn paper be fixed?",
            "Sometimes yes. Paper cannot become brand-new again, but a careful patch can help it stay flat and strong enough to use."
        )
    ],
}
KNOWLEDGE_ORDER = ["comparison", "flashback", "kindness", "marker", "tape", "string", "library", "paper"]


def generation_prompts(world: World) -> list[str]:
    hero = world.facts["hero"]
    task = world.facts["task"]
    helper = world.facts["helper"]
    problem = world.facts["problem"]
    return [
        f'Write a slice-of-life story for a 3-to-5-year-old that includes the word "comparison" and shows a child doing a small paper craft in class.',
        f"Tell a gentle classroom story where {hero.id} feels bad after a comparison with another child's {task.label}, then has a flashback to an earlier kind moment and accepts help.",
        f"Write a quiet story about {problem.label} during craft time, where kindness changes the mood and the ending image shows ordinary life feeling warm again after help from {helper.id}.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    hero = world.facts["hero"]
    task = world.facts["task"]
    helper = world.facts["helper"]
    problem = world.facts["problem"]
    action = world.facts["action"]
    memory = world.facts["memory"]
    neighbor = world.facts["neighbor"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id} during classroom craft time. {hero.pronoun('possessive').capitalize()} feelings change after a small problem, a flashback, and a kind helper."
        ),
        (
            f"What was {hero.id} making?",
            f"{hero.id} was making {task.phrase}. The project mattered because {hero.pronoun()} wanted it to look especially nice."
        ),
        (
            f"Why did {hero.id} feel bad at first?",
            f"{hero.id} noticed {problem.label} and then looked at the neat work nearby, so the comparison stung. The problem made {hero.pronoun('possessive')} own project feel smaller than it really was."
        ),
        (
            "What happened in the flashback, and why did it matter?",
            f"In the flashback, {memory.line} It mattered because the remembered kindness helped {hero.id} stop hiding and trust the help being offered now."
        ),
        (
            f"How was the problem fixed?",
            f"{_helper_phrase(world)} {action.qa_text}. That changed the project itself, and it also helped the tight worried feeling in {hero.id} loosen."
        ),
    ]
    if world.facts.get("ending") == "pass_forward":
        qa.append(
            (
                f"How did {hero.id} pass the kindness on?",
                f"After getting help, {hero.id} noticed that {neighbor.id} also needed a color and quietly shared one. The second kind act shows that the earlier help changed what {hero.id} did next, not just how {hero.pronoun()} felt."
            )
        )
    else:
        qa.append(
            (
                f"How did the story end?",
                f"{hero.id} finished the {task.label} and added an extra thankful line for someone who helped on ordinary days. The ending shows that the comparison faded once kindness made the moment feel steadier and more personal."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"comparison", "flashback", "kindness"} | set(world.facts["task"].tags) | set(world.facts["problem"].tags) | set(world.facts["action"].tags) | set(world.facts["memory"].tags)
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
        lines.append(f"  {ent.id:10} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        task="card",
        problem="dull_colors",
        action="share_markers",
        helper="peer",
        hero_name="Lily",
        hero_gender="girl",
        peer_name="Ben",
        peer_gender="boy",
        teacher_name="Mora",
        teacher_gender="girl",
        trait="thoughtful",
        seed=101,
    ),
    StoryParams(
        task="bookmark",
        problem="loose_loop",
        action="retie_loop",
        helper="teacher",
        hero_name="Max",
        hero_gender="boy",
        peer_name="Mia",
        peer_gender="girl",
        teacher_name="Asha",
        teacher_gender="girl",
        trait="careful",
        seed=102,
    ),
    StoryParams(
        task="flower",
        problem="torn_corner",
        action="tape_patch",
        helper="teacher",
        hero_name="Ella",
        hero_gender="girl",
        peer_name="Noah",
        peer_gender="boy",
        teacher_name="Reed",
        teacher_gender="boy",
        trait="sensitive",
        seed=103,
    ),
    StoryParams(
        task="bookmark",
        problem="dull_colors",
        action="share_markers",
        helper="teacher",
        hero_name="Theo",
        hero_gender="boy",
        peer_name="Ava",
        peer_gender="girl",
        teacher_name="June",
        teacher_gender="girl",
        trait="quiet",
        seed=104,
    ),
]


def explain_rejection(task_id: str, problem_id: str, action_id: str, helper_id: str) -> str:
    if task_id in TASKS and problem_id in PROBLEMS:
        task = TASKS[task_id]
        problem = PROBLEMS[problem_id]
        if problem_id not in task.allows or task_id not in problem.task_ids:
            return (
                f"(No story: {problem.label} does not fit a {task.label}. The classroom problem has to be one this kind of project could really have.)"
            )
    if problem_id in PROBLEMS and action_id in ACTIONS:
        problem = PROBLEMS[problem_id]
        action = ACTIONS[action_id]
        if problem.needs not in action.repairs:
            return (
                f"(No story: {action.label} does not fix {problem.label}. The kind act has to repair the actual trouble, not just sound nice.)"
            )
    if action_id in ACTIONS:
        action = ACTIONS[action_id]
        if helper_id not in action.helpers:
            return (
                f"(No story: {helper_id} is not the right helper for {action.label} in this world model.)"
            )
    return "(No story: this combination is not reasonable in the classroom world.)"


def outcome_of(params: StoryParams) -> str:
    if params.action not in ACTIONS:
        return "?"
    return "pass_forward" if ACTIONS[params.action].leaves_spare else "quiet_finish"


ASP_RULES = r"""
problem_fits(T, P) :- task(T), problem(P), allows(T, P), task_of_problem(P, T).
action_fits(P, A) :- problem(P), action(A), needs(P, N), repairs(A, N).
helper_fits(A, H) :- action(A), helper_kind(H), helper_can(A, H).
valid(T, P, A, H) :- problem_fits(T, P), action_fits(P, A), helper_fits(A, H).

outcome(pass_forward) :- chosen_action(A), leaves_spare(A).
outcome(quiet_finish) :- chosen_action(A), not leaves_spare(A).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for task_id, task in TASKS.items():
        lines.append(asp.fact("task", task_id))
        for problem_id in sorted(task.allows):
            lines.append(asp.fact("allows", task_id, problem_id))
    for problem_id, problem in PROBLEMS.items():
        lines.append(asp.fact("problem", problem_id))
        lines.append(asp.fact("needs", problem_id, problem.needs))
        for task_id in sorted(problem.task_ids):
            lines.append(asp.fact("task_of_problem", problem_id, task_id))
    for action_id, action in ACTIONS.items():
        lines.append(asp.fact("action", action_id))
        for need in sorted(action.repairs):
            lines.append(asp.fact("repairs", action_id, need))
        for helper_id in sorted(action.helpers):
            lines.append(asp.fact("helper_can", action_id, helper_id))
        if action.leaves_spare:
            lines.append(asp.fact("leaves_spare", action_id))
    for helper_id in ("peer", "teacher"):
        lines.append(asp.fact("helper_kind", helper_id))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = asp.fact("chosen_action", params.action)
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def _smoke_test() -> None:
    sample = generate(CURATED[0])
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        emit(sample, trace=False, qa=True, header="### smoke")
    if not sample.story or "comparison" not in sample.story:
        raise StoryError("(Smoke test failed: generated story text is incomplete.)")


def asp_verify() -> int:
    rc = 0
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: valid combo gate matches ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    cases = list(CURATED)
    for seed in range(120):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(params)

    bad = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        _smoke_test()
        print("OK: smoke test generate()/emit() passed.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: comparison, flashback, and kindness during classroom craft time."
    )
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--helper", choices=["peer", "teacher"])
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--peer-name")
    ap.add_argument("--peer-gender", choices=["girl", "boy"])
    ap.add_argument("--teacher-name")
    ap.add_argument("--teacher-gender", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combos derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP model against Python")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if (
        args.task is not None
        and args.problem is not None
        and args.action is not None
        and args.helper is not None
        and not valid_combo(args.task, args.problem, args.action, args.helper)
    ):
        raise StoryError(explain_rejection(args.task, args.problem, args.action, args.helper))

    combos = [
        combo
        for combo in valid_combos()
        if (args.task is None or combo[0] == args.task)
        and (args.problem is None or combo[1] == args.problem)
        and (args.action is None or combo[2] == args.action)
        and (args.helper is None or combo[3] == args.helper)
    ]
    if not combos:
        tid = args.task or next(iter(TASKS))
        pid = args.problem or next(iter(PROBLEMS))
        aid = args.action or next(iter(ACTIONS))
        hid = args.helper or "peer"
        raise StoryError(explain_rejection(tid, pid, aid, hid))

    task_id, problem_id, action_id, helper_id = rng.choice(sorted(combos))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    peer_gender = args.peer_gender or ("boy" if hero_gender == "girl" else "girl")
    teacher_gender = args.teacher_gender or rng.choice(["girl", "boy"])
    hero_name = args.hero_name or _pick_name(rng, hero_gender)
    peer_name = args.peer_name or _pick_name(rng, peer_gender, avoid=hero_name)
    teacher_name = args.teacher_name or _pick_name(rng, teacher_gender, avoid=hero_name)
    trait = rng.choice(TRAITS)

    return StoryParams(
        task=task_id,
        problem=problem_id,
        action=action_id,
        helper=helper_id,
        hero_name=hero_name,
        hero_gender=hero_gender,
        peer_name=peer_name,
        peer_gender=peer_gender,
        teacher_name=teacher_name,
        teacher_gender=teacher_gender,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if not valid_combo(params.task, params.problem, params.action, params.helper):
        raise StoryError(explain_rejection(params.task, params.problem, params.action, params.helper))
    if params.task not in TASKS or params.problem not in PROBLEMS or params.action not in ACTIONS:
        raise StoryError("(No story: unknown registry key in params.)")
    if params.helper not in {"peer", "teacher"}:
        raise StoryError("(No story: helper must be 'peer' or 'teacher'.)")

    task = TASKS[params.task]
    problem = PROBLEMS[params.problem]
    action = ACTIONS[params.action]
    memory = MEMORIES[params.helper]

    world = tell(
        task=task,
        problem=problem,
        action=action,
        memory=memory,
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        peer_name=params.peer_name,
        peer_gender=params.peer_gender,
        teacher_name=params.teacher_name,
        teacher_gender=params.teacher_gender,
        trait=params.trait,
        helper_kind=params.helper,
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
        print(f"{len(combos)} compatible (task, problem, action, helper) combos:\n")
        for task_id, problem_id, action_id, helper_id in combos:
            print(f"  {task_id:10} {problem_id:12} {action_id:14} {helper_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    if args.all:
        samples = [generate(p) for p in CURATED]
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
            header = f"### {p.hero_name}: {p.task}, {p.problem}, {p.action}, {p.helper}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
