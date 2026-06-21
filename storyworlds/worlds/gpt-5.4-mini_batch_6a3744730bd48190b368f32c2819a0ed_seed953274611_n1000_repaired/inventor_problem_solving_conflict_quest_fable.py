#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/inventor_problem_solving_conflict_quest_fable.py
=================================================================================

A standalone story world in a fable-like style about an inventor, a conflict,
and a quest that ends in thoughtful problem solving.

The premise is small and classical: a clever inventor must cross the market to
reach a broken bell, but a proud rival blocks the way until the inventor solves
the problem in a kinder, wiser way. The world is simulated with physical meters
and emotional memes, and the prose is rendered from that state rather than from
a frozen template.

The story aims for a fable feel: simple animals or folk figures, a clear lesson,
and a concrete ending image that proves what changed.
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
    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "queen", "hen", "she"}
        male = {"boy", "father", "man", "king", "fox", "he"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.id
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
    detail: str
    quest_goal: str
    lesson: str
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
class Problem:
    id: str
    label: str
    cause: str
    symptom: str
    risk: str
    hard: int = 1
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
class Tool:
    id: str
    label: str
    phrase: str
    method: str
    solves: set[str] = field(default_factory=set)
    clever: int = 1
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

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Rival:
    id: str
    label: str
    shout: str
    barrier: str
    conflict_gain: int = 1
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
        w = World()
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = copy.deepcopy(self.facts)
        return w


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


def _r_think(world: World) -> list[str]:
    out: list[str] = []
    inv = world.get("inventor")
    if inv.memes["curiosity"] >= THRESHOLD and inv.memes["resolve"] < THRESHOLD:
        sig = ("think",)
        if sig not in world.fired:
            world.fired.add(sig)
            inv.memes["resolve"] += 1
            out.append("__think__")
    return out


def _r_fix(world: World) -> list[str]:
    out: list[str] = []
    problem = world.get("problem")
    tool = world.get("tool")
    if problem.meters["broken"] < THRESHOLD:
        return out
    if tool.meters["used"] < THRESHOLD:
        return out
    sig = ("fix",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    problem.meters["broken"] = 0.0
    problem.meters["working"] = 1.0
    out.append("__fixed__")
    return out


def _r_rival_softens(world: World) -> list[str]:
    out: list[str] = []
    rival = world.get("rival")
    inv = world.get("inventor")
    if rival.memes["heat"] < THRESHOLD:
        return out
    if inv.meters["plan"] < THRESHOLD:
        return out
    sig = ("soften",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    rival.memes["heat"] = 0.0
    rival.memes["respect"] += 1
    inv.memes["hope"] += 1
    out.append("__soften__")
    return out


CAUSAL_RULES = [
    Rule("think", "mind", _r_think),
    Rule("fix", "physical", _r_fix),
    Rule("soften", "social", _r_rival_softens),
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


def _do_use(world: World, tool: Entity) -> None:
    tool.meters["used"] += 1
    world.get("inventor").meters["plan"] += 1
    propagate(world, narrate=False)


def predict(world: World, problem_id: str) -> dict:
    sim = world.copy()
    _do_use(sim, sim.get("tool"))
    return {
        "fixed": sim.get(problem_id).meters["working"] >= THRESHOLD,
        "plan": sim.get("inventor").meters["plan"],
    }


def setting_intro(world: World, setting: Setting, inventor: Entity) -> None:
    inventor.memes["curiosity"] += 1
    world.say(
        f"Long ago, in {setting.place}, there lived a small inventor named {inventor.id}. "
        f"{inventor.id} liked to watch the world, ask questions, and mend what others ignored."
    )
    world.say(setting.detail)


def problem_appears(world: World, setting: Setting, problem: Problem) -> None:
    p = world.get("problem")
    p.meters["broken"] = 1.0
    p.meters["blocked"] = 1.0
    world.say(
        f"One morning, {setting.place} grew troubled. {problem.cause} had left {problem.label} broken, "
        f"and {problem.symptom}."
    )
    world.say(
        f"Without it, the little folk could not reach {setting.quest_goal} the way they wished."
    )


def quest_call(world: World, inventor: Entity, setting: Setting, rival: Rival) -> None:
    inventor.memes["quest"] += 1
    world.say(
        f"{inventor.id} set out on a quest through {setting.place}, carrying hope in one hand and a lantern in the other."
    )
    world.say(
        f"But at the bridge stood {rival.label}, who shouted, '{rival.shout}' and made the path feel small and mean."
    )


def conflict(world: World, inventor: Entity, rival: Rival) -> None:
    inventor.memes["frustration"] += 1
    rival_ent = world.get("rival")
    rival_ent.memes["heat"] += rival.conflict_gain
    world.say(
        f"{inventor.id} did not shout back. Still, the words stung, and the road was barred by {rival.barrier}."
    )
    world.say(
        f"For a moment, the quest seemed stuck between anger and silence."
    )


def think_and_notice(world: World, inventor: Entity, problem: Problem, tool: Tool) -> None:
    pred = predict(world, problem.id)
    inventor.memes["curiosity"] += 1
    world.facts["predicted_fix"] = pred["fixed"]
    world.say(
        f"{inventor.id} stopped, looked closely, and studied the broken thing like a patient bird studies a nest."
    )
    world.say(
        f"Then {inventor.id} noticed that {problem.risk}."
    )
    world.say(
        f"So {inventor.id} reached for {tool.phrase} and tried {tool.method}."
    )


def use_tool(world: World, inventor: Entity, tool: Tool, problem: Problem) -> None:
    _do_use(world, world.get("tool"))
    world.say(
        f"The tool worked because it was made for this kind of trouble."
    )
    world.say(
        f"Little by little, the broken part became steady again."
    )


def resolve_conflict(world: World, inventor: Entity, rival: Rival, setting: Setting) -> None:
    rival_ent = world.get("rival")
    if rival_ent.memes["respect"] >= THRESHOLD:
        world.say(
            f"Seeing the careful work, {rival.label} grew quiet. Pride softened into respect."
        )
    inventor.memes["joy"] += 1
    inventor.memes["resolve"] += 1
    world.say(
        f"{inventor.id} finished the repair and smiled, because the quest had been won without meanness."
    )
    world.say(
        f"At last, the path to {setting.quest_goal} opened again, and the whole place felt lighter."
    )


def lesson(world: World, setting: Setting, problem: Problem) -> None:
    world.say(
        f"The fable said this: {setting.lesson}."
    )
    world.say(
        f"That is why the people remembered the inventor, not for being loud, but for solving the problem wisely."
    )


def tell(setting: Setting, problem: Problem, tool: Tool, rival: Rival,
         inventor_name: str = "Ivo", inventor_type: str = "fox",
         rival_type: str = "crow") -> World:
    world = World()
    inventor = world.add(Entity(
        id=inventor_name,
        kind="character",
        type=inventor_type,
        role="inventor",
        traits=["clever", "patient"],
    ))
    rival_ent = world.add(Entity(
        id=rival.label,
        kind="character",
        type=rival_type,
        role="rival",
        label=rival.label,
    ))
    problem_ent = world.add(Entity(
        id="problem",
        kind="thing",
        type="thing",
        label=problem.label,
    ))
    tool_ent = world.add(Entity(
        id="tool",
        kind="thing",
        type="tool",
        label=tool.label,
    ))
    world.facts["setting"] = setting
    world.facts["problem_cfg"] = problem
    world.facts["tool_cfg"] = tool
    world.facts["rival_cfg"] = rival

    setting_intro(world, setting, inventor)
    problem_appears(world, setting, problem)
    world.para()
    quest_call(world, inventor, setting, rival)
    conflict(world, inventor, rival)
    world.para()
    think_and_notice(world, inventor, problem, tool)
    use_tool(world, inventor, tool, problem)
    resolve_conflict(world, inventor, rival, setting)
    world.para()
    lesson(world, setting, problem)

    world.facts.update(
        inventor=inventor,
        rival=rival_ent,
        problem=problem_ent,
        tool=tool_ent,
        outcome="fixed" if problem_ent.meters["working"] >= THRESHOLD else "broken",
    )
    return world


SETTINGS = {
    "village": Setting(
        id="village",
        place="a small village",
        detail="The wells, the carts, and the market stalls all leaned on one another like old friends.",
        quest_goal="the fountain gate",
        lesson="A clever hand and a calm heart can mend more than anger ever can",
    ),
    "harbor": Setting(
        id="harbor",
        place="a windy harbor",
        detail="The ropes creaked, the gulls argued, and every boat waited for a tide that would not be bullied.",
        quest_goal="the lantern dock",
        lesson="A good idea is stronger when it serves everyone, not just the loudest voice",
    ),
    "orchard": Setting(
        id="orchard",
        place="an orchard",
        detail="The trees stood in tidy rows, and even the bees seemed to hum in careful order.",
        quest_goal="the top of the hill",
        lesson="Patience can turn a hard problem into a gentle path",
    ),
}

PROBLEMS = {
    "bell_rope": Problem(
        id="bell_rope",
        label="the bell rope",
        cause="A storm",
        symptom="the rope had snapped into two frayed pieces",
        risk="the village bell could not call the folk to gather",
        hard=1,
    ),
    "water_gate": Problem(
        id="water_gate",
        label="the water gate",
        cause="A rusty hinge",
        symptom="the gate would not stay open",
        risk="the harbor lanterns could not be refilled on time",
        hard=1,
    ),
    "tree_latch": Problem(
        id="tree_latch",
        label="the tree latch",
        cause="Years of sun",
        symptom="the latch had warped and stuck",
        risk="the orchard ladders could not reach the high fruit",
        hard=1,
    ),
}

TOOLS = {
    "spool": Tool(
        id="spool",
        label="a spool of strong thread",
        phrase="a spool of strong thread and a little hook",
        method="tying the broken ends together and making the rope whole again",
        solves={"bell_rope"},
        clever=2,
    ),
    "oil": Tool(
        id="oil",
        label="a small tin of oil",
        phrase="a small tin of oil and a soft cloth",
        method="loosening the rusty hinge until the gate could swing freely",
        solves={"water_gate"},
        clever=2,
    ),
    "wood_wedge": Tool(
        id="wood_wedge",
        label="a carved wooden wedge",
        phrase="a carved wooden wedge and a hammer",
        method="nudging the warped latch back into its proper shape",
        solves={"tree_latch"},
        clever=2,
    ),
}

RIVALS = {
    "crow": Rival(
        id="crow",
        label="Crow",
        shout="This is my bridge, and no one may cross it!",
        barrier="a patchwork of twigs and feathers",
        conflict_gain=1,
    ),
    "goat": Rival(
        id="goat",
        label="Goat",
        shout="Only the strongest may pass!",
        barrier="two stubborn horns in the path",
        conflict_gain=1,
    ),
    "mole": Rival(
        id="mole",
        label="Mole",
        shout="I dug this tunnel, so stay out!",
        barrier="a mound of fresh earth",
        conflict_gain=1,
    ),
}

NAMES = ["Ivo", "Mina", "Tavi", "Lena", "Pip", "Orin", "Nell", "Sora"]
ANIMALS = ["fox", "hare", "mouse", "owl", "badger", "cat"]


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for pid, problem in PROBLEMS.items():
            for tid, tool in TOOLS.items():
                if pid in tool.solves:
                    for rid in RIVALS:
                        combos.append((sid, pid, tid, rid))
    return combos


@dataclass
class StoryParams:
    setting: str
    problem: str
    tool: str
    rival: str
    inventor_name: str = "Ivo"
    inventor_type: str = "fox"
    rival_type: str = "crow"
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
    "inventor": [(
        "What is an inventor?",
        "An inventor is a person who makes or improves things to solve problems. Inventors often try ideas until they find one that works.",
    )],
    "quest": [(
        "What is a quest?",
        "A quest is a journey with a purpose, like finding something, fixing something, or helping someone.",
    )],
    "conflict": [(
        "What is conflict in a story?",
        "Conflict is the trouble or disagreement that makes a story tense. It can be a fight, a barrier, or a hard choice.",
    )],
    "problem": [(
        "What is a problem?",
        "A problem is something that is not working right and needs attention. A good solution makes the problem better or disappears.",
    )],
    "tool": [(
        "What is a tool?",
        "A tool is an object people use to do a job more easily. The right tool can help fix a broken thing safely.",
    )],
    "fable": [(
        "What is a fable?",
        "A fable is a short story that teaches a lesson. Fables often end with a simple moral that helps readers think about choices.",
    )],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    s, p, t, r = f["setting"], f["problem_cfg"], f["tool_cfg"], f["rival_cfg"]
    return [
        f'Write a fable about an inventor who goes on a quest in {s.place} to fix {p.label}. Include the word "inventor".',
        f"Tell a child-friendly story where {f['inventor'].id} faces conflict with {r.label} and solves {p.risk} using {t.label}.",
        f"Write a short quest story in a fable style where a clever inventor chooses problem solving over anger.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    inventor = f["inventor"]
    rival = f["rival"]
    setting = f["setting"]
    problem = f["problem_cfg"]
    tool = f["tool_cfg"]
    qa = [
        QAItem(
            question="Who is the story about?",
            answer=f"It is about {inventor.id}, a small inventor who set out to help {setting.place}.",
        ),
        QAItem(
            question="What problem did the inventor want to solve?",
            answer=f"{problem.risk}. That trouble began when {problem.cause.lower()} left {problem.label} unable to work.",
        ),
        QAItem(
            question="What caused the conflict?",
            answer=f"{rival.label} blocked the way and shouted, '{rival.shout}' The inventor had to keep calm while the path was closed.",
        ),
        QAItem(
            question="How was the problem solved?",
            answer=f"{inventor.id} used {tool.label} and carefully repaired the broken part. The fix worked because it matched the problem instead of fighting it.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"The quest ended with {setting.quest_goal} open again, and the village learned from the inventor's wise choice. The ending shows that patience can solve what anger cannot.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = {"inventor", "quest", "conflict", "problem", "tool", "fable"}
    out: list[QAItem] = []
    for key, items in KNOWLEDGE.items():
        if key in tags:
            for q, a in items:
                out.append(QAItem(question=q, answer=a))
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
        if e.traits:
            bits.append(f"traits={e.traits}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


ASP_RULES = r"""
inventor(I) :- entity(I), role(I,inventor).
quest(Q) :- entity(Q), role(Q,quest).
conflict(C) :- entity(C), role(C,conflict).
problem(P) :- entity(P), role(P,problem).
tool(T) :- entity(T), role(T,tool).

broken_problem(P) :- problem(P), broken(P).
solves(T,P) :- tool(T), can_solve(T,P), problem(P).
reasonable(P,T) :- problem(P), tool(T), solves(T,P).

ending(fixed) :- inventor(I), problem(P), tool(T), reasonable(P,T).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for pid in PROBLEMS:
        lines.append(asp.fact("problem", pid))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        for p in sorted(t.solves):
            lines.append(asp.fact("can_solve", tid, p))
    for rid in RIVALS:
        lines.append(asp.fact("rival", rid))
    for name in ("inventor", "quest", "conflict", "problem", "tool"):
        lines.append(asp.fact("entity", name))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program(show="#show reasonable/2."))
    return sorted(set(asp.atoms(model, "reasonable")))


def asp_verify() -> int:
    ok = set(asp_valid_combos()) == {(p, t) for _, p, t, _ in valid_combos()}
    if ok:
        print("OK: ASP reasonableness matches Python valid_combos().")
        return 0
    print("MISMATCH: ASP and Python differ.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fable-like inventor quest world.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--rival", choices=RIVALS)
    ap.add_argument("--inventor-name")
    ap.add_argument("--inventor-type", choices=ANIMALS)
    ap.add_argument("--rival-type", default="crow")
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.problem is None or c[1] == args.problem)
              and (args.tool is None or c[2] == args.tool)
              and (args.rival is None or c[3] == args.rival)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, problem, tool, rival = rng.choice(sorted(combos))
    inv_name = args.inventor_name or rng.choice(NAMES)
    inv_type = args.inventor_type or rng.choice(ANIMALS)
    rival_type = args.rival_type or "crow"
    return StoryParams(
        setting=setting,
        problem=problem,
        tool=tool,
        rival=rival,
        inventor_name=inv_name,
        inventor_type=inv_type,
        rival_type=rival_type,
    )


def generate(params: StoryParams) -> StorySample:
    for field_name, table in [("setting", SETTINGS), ("problem", PROBLEMS), ("tool", TOOLS), ("rival", RIVALS)]:
        if getattr(params, field_name) not in table:
            raise StoryError(f"Unknown {field_name}: {getattr(params, field_name)!r}")
    world = tell(
        SETTINGS[params.setting],
        PROBLEMS[params.problem],
        TOOLS[params.tool],
        RIVALS[params.rival],
        inventor_name=params.inventor_name,
        inventor_type=params.inventor_type,
        rival_type=params.rival_type,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
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
    StoryParams(setting="village", problem="bell_rope", tool="spool", rival="crow", inventor_name="Ivo", inventor_type="fox", rival_type="crow"),
    StoryParams(setting="harbor", problem="water_gate", tool="oil", rival="goat", inventor_name="Mina", inventor_type="hare", rival_type="goat"),
    StoryParams(setting="orchard", problem="tree_latch", tool="wood_wedge", rival="mole", inventor_name="Nell", inventor_type="owl", rival_type="mole"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program(show="#show reasonable/2."))
        return
    if args.verify:
        try:
            sample = generate(CURATED[0])
            _ = sample.story
        except Exception as exc:
            print(f"SMOKE TEST FAILED: {exc}")
            sys.exit(1)
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} reasonable problem/tool pairs:\n")
        for p, t in combos:
            print(f"  {p:12} {t}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
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
            header = f"### {p.inventor_name}: {p.setting} / {p.problem} / {p.tool}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
