#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/exploratory_announce_abject_repetition_problem_solving_mystery.py
================================================================================================

A compact mystery storyworld about a child making an exploratory search, publicly
announcing clues, feeling abject frustration, and using repetition plus problem
solving to crack a small puzzle.

The world is built to be:
- state-driven rather than template-swapped
- child-facing and concrete
- compatible with the Storyweavers storyworld contract
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
MOOD_LOW = -1.0


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
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
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
class Setting:
    id: str
    place: str
    detail: str
    shadow: str
    echo: str
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
class Clue:
    id: str
    kind: str
    label: str
    where: str
    repeats: str
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
    blocked_by: str
    fix: str
    method: str
    solution_text: str
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
    helps: str
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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c


@dataclass
class Rule:
    name: str
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


def _r_repetition(world: World) -> list[str]:
    out: list[str] = []
    for clue in world.facts.get("clues", []):
        sig = ("repeat", clue.id)
        if sig in world.fired:
            continue
        if clue.kind == "pattern":
            world.fired.add(sig)
            kid = world.get("kid")
            kid.memes["attention"] += 1
            clue_ent = world.get(clue.id)
            clue_ent.meters["noticed"] += 1
            out.append(f"The same little sign kept coming back.")
    return out


def _r_problem_solving(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("problem_solved"):
        return out
    if world.get("box").meters["opened"] >= THRESHOLD and world.get("map").meters["matched"] >= THRESHOLD:
        sig = ("solve",)
        if sig in world.fired:
            return out
        world.fired.add(sig)
        world.facts["problem_solved"] = True
        world.get("kid").memes["relief"] += 1
        out.append("The pieces fit together at last.")
    return out


CAUSAL_RULES = [Rule("repetition", _r_repetition), Rule("problem_solving", _r_problem_solving)]


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
        for s in produced:
            world.say(s)
    return produced


SETTING_REGISTRY = {
    "hall": Setting(
        id="hall",
        place="the quiet hall",
        detail="The hallway smelled like old wood and raincoats.",
        shadow="a long shadow near the umbrella stand",
        echo="every step made a soft echo",
    ),
    "attic": Setting(
        id="attic",
        place="the dusty attic",
        detail="The attic held boxes, a slanted roof, and a little square of light.",
        shadow="a dark corner behind stacked trunks",
        echo="the floorboards creaked with each step",
    ),
    "library": Setting(
        id="library",
        place="the tiny library nook",
        detail="The nook had tall books, a lamp, and a sleepy chair.",
        shadow="a shadow under the reading table",
        echo="whispers bounced gently from shelf to shelf",
    ),
}

CLUE_REGISTRY = {
    "scratch": Clue(
        id="scratch",
        kind="pattern",
        label="a scratch mark",
        where="on the floor",
        repeats="it curved again and again in the same direction",
        tags={"pattern", "mystery"},
    ),
    "note": Clue(
        id="note",
        kind="paper",
        label="a folded note",
        where="inside a book",
        repeats="the same word was written twice",
        tags={"paper", "mystery"},
    ),
    "pebble": Clue(
        id="pebble",
        kind="pattern",
        label="tiny pebbles",
        where="near the doorway",
        repeats="the pebbles made a trail, then the trail came back",
        tags={"pattern", "mystery"},
    ),
}

PROBLEM_REGISTRY = {
    "box": Problem(
        id="box",
        label="a locked little box",
        blocked_by="a jammed latch",
        fix="a paper clip and a careful wiggle",
        method="open the box",
        solution_text="opened the box with a paper clip and a careful wiggle",
        tags={"problem", "mystery"},
    ),
    "drawer": Problem(
        id="drawer",
        label="a stuck drawer",
        blocked_by="a crooked spoon",
        fix="pull the spoon aside and try again slowly",
        method="pull the drawer open",
        solution_text="pulled the spoon aside and opened the drawer slowly",
        tags={"problem", "mystery"},
    ),
    "panel": Problem(
        id="panel",
        label="a tiny panel",
        blocked_by="two bent nails",
        fix="lift the nails with a coin",
        method="open the panel",
        solution_text="lifted the nails with a coin and opened the panel",
        tags={"problem", "mystery"},
    ),
}

TOOL_REGISTRY = {
    "clip": Tool(id="clip", label="a paper clip", helps="a paper clip could slip the latch"),
    "coin": Tool(id="coin", label="a coin", helps="a coin could lift the nails"),
    "ruler": Tool(id="ruler", label="a ruler", helps="a ruler could nudge the note free"),
}

NAMES = ["Mina", "Toby", "Nora", "Eli", "Zoe", "Finn", "Ivy", "Theo"]
TRAITS = ["curious", "careful", "patient", "quiet", "brave"]


@dataclass
class StoryParams:
    setting: str
    clue: str
    problem: str
    tool: str
    name: str
    trait: str
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for sid in SETTING_REGISTRY:
        for cid in CLUE_REGISTRY:
            for pid in PROBLEM_REGISTRY:
                if sid == "hall" and cid in {"scratch", "pebble"} and pid == "box":
                    combos.append((sid, cid, pid))
                if sid == "attic" and cid in {"pebble", "note"} and pid in {"drawer", "panel"}:
                    combos.append((sid, cid, pid))
                if sid == "library" and cid in {"note", "scratch"} and pid in {"box", "drawer"}:
                    combos.append((sid, cid, pid))
    return combos


def clue_matches_problem(clue: Clue, problem: Problem) -> bool:
    if clue.kind == "pattern":
        return problem.id in {"box", "panel", "drawer"}
    return clue.kind == "paper" and problem.id in {"box", "drawer"}


def reasonableness_gate(clue: Clue, problem: Problem, tool: Tool) -> bool:
    if problem.id == "box" and tool.id != "clip":
        return False
    if problem.id == "drawer" and tool.id not in {"clip", "ruler"}:
        return False
    if problem.id == "panel" and tool.id != "coin":
        return False
    return clue_matches_problem(clue, problem)


def predict(world: World, problem_id: str) -> dict:
    sim = world.copy()
    sim.get(problem_id).meters["opened"] += 1
    propagate(sim, narrate=False)
    return {"solved": sim.facts.get("problem_solved", False)}


def setup(world: World, kid: Entity, setting: Setting, clue: Clue) -> None:
    kid.memes["curiosity"] += 1
    world.say(
        f"{kid.id} went into {setting.place} on an exploratory little search. "
        f"{setting.detail}"
    )
    world.say(f"{setting.echo}, and {setting.shadow} felt like it might hide something.")
    world.say(f"{kid.id} wanted to know what the clue meant: {clue.label} {clue.where}.")


def announce(world: World, kid: Entity, clue: Clue) -> None:
    kid.memes["announcement"] += 1
    world.say(
        f'{kid.id} stopped and announced, "Look! {clue.label} {clue.where}!" '
        f'Then {kid.pronoun()} said it again, just to be sure: "{clue.label} {clue.where}!"'
    )


def abject(world: World, kid: Entity) -> None:
    kid.memes["frustration"] += 1
    world.say(
        f"For a moment, {kid.id} felt abject and small. "
        f"Nothing made sense, and the quiet room felt even quieter."
    )


def repeat_clue(world: World, clue: Clue) -> None:
    clue_ent = world.get(clue.id)
    clue_ent.meters["noticed"] += 1
    world.say(f"The clue kept repeating itself: {clue.repeats}.")


def solve_problem(world: World, kid: Entity, problem: Problem, tool: Tool) -> None:
    kid.memes["hope"] += 1
    world.say(
        f"{kid.id} looked at the problem again and again. "
        f"Then {kid.pronoun()} tried a new plan with {tool.label}."
    )
    if problem.id == "box":
        world.get("box").meters["opened"] += 1
    elif problem.id == "drawer":
        world.get("drawer").meters["opened"] += 1
    else:
        world.get("panel").meters["opened"] += 1
    propagate(world, narrate=False)
    world.say(f"It worked: {problem.solution_text}.")


def ending(world: World, kid: Entity, clue: Clue, problem: Problem) -> None:
    if world.facts.get("problem_solved"):
        kid.memes["relief"] += 1
        world.say(
            f"Inside, there was a tiny answer that matched the clue. "
            f"{kid.id} smiled, because the mystery was not magic after all. "
            f"It was only a puzzle waiting for a patient mind."
        )
    else:
        world.say(
            f"The clue stayed strange, but {kid.id} promised to come back "
            f"with a clearer plan the next day."
        )


def tell(setting: Setting, clue: Clue, problem: Problem, tool: Tool, name: str, trait: str) -> World:
    world = World()
    kid = world.add(Entity(id=name, kind="character", type="girl" if name in {"Mina", "Nora", "Zoe", "Ivy"} else "boy", role="seeker", traits=[trait]))
    box = world.add(Entity(id="box", label=problem.label))
    drawer = world.add(Entity(id="drawer", label=problem.label))
    panel = world.add(Entity(id="panel", label=problem.label))
    clue_ent = world.add(Entity(id=clue.id, label=clue.label))
    world.add(Entity(id="tool", label=tool.label))
    world.facts["clues"] = [clue]
    world.facts.update(setting=setting, clue=clue, problem=problem, tool=tool)

    setup(world, kid, setting, clue)
    world.para()
    announce(world, kid, clue)
    repeat_clue(world, clue)
    abject(world, kid)
    world.para()
    world.say(f"{kid.id} noticed that the problem was {problem.blocked_by}.")
    world.say(f"The fix was simple once {kid.pronoun()} thought of it: {problem.fix}.")
    if reasonableness_gate(clue, problem, tool):
        solve_problem(world, kid, problem, tool)
        world.facts["problem_solved"] = True
    else:
        world.say(f"{kid.id} tried a few ideas, but none of them fit.")
        world.facts["problem_solved"] = False
    world.para()
    ending(world, kid, clue, problem)
    world.facts.update(kid=kid, clue_ent=clue_ent, box=box, drawer=drawer, panel=panel)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a child-facing mystery story that includes the words "exploratory", "announce", and "abject".',
        f"Tell a small story where {f['kid'].id} makes an exploratory search, notices a repeating clue, and solves the problem by thinking carefully.",
        f"Write a mystery for young children with repetition and problem solving, ending with a clear answer and a calm discovery.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    kid = f["kid"]
    clue = f["clue"]
    problem = f["problem"]
    answers = [
        QAItem(
            question="What kind of story is this?",
            answer="It is a small mystery story. A child looks for clues, gets stuck, and then solves a puzzle by thinking carefully.",
        ),
        QAItem(
            question=f"Why did {kid.id} feel abject?",
            answer=f"{kid.id} felt abject because the clue did not make sense at first, and the room felt very quiet and puzzling. The feeling changed once {kid.id} kept looking and found a better plan.",
        ),
        QAItem(
            question=f"How did the clue help solve the problem?",
            answer=f"The clue repeated itself, so {kid.id} realized it was pointing toward the same hidden place again and again. That repetition helped {kid.id} figure out where to use {f['tool'].label} and solve the problem.",
        ),
    ]
    if f.get("problem_solved"):
        answers.append(
            QAItem(
                question="How did the story end?",
                answer=f"It ended with the box or door opening and the answer turning out to be simple. {kid.id} felt relieved because the mystery was solved, not scary anymore.",
            )
        )
    else:
        answers.append(
            QAItem(
                question="How did the story end?",
                answer=f"It ended with the mystery still open, but {kid.id} had a better idea for next time. The story stayed calm and thoughtful instead of giving a big answer too soon.",
            )
        )
    return answers


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a clue?",
            answer="A clue is a small piece of information that helps someone solve a mystery. It can be a mark, a note, or a pattern that keeps showing up.",
        ),
        QAItem(
            question="What does it mean to solve a problem?",
            answer="To solve a problem means to figure out what to do and make the trouble stop. In a mystery, it often means using clues to find the right answer.",
        ),
        QAItem(
            question="Why can repetition help?",
            answer="Repetition can help because the same thing showing up again and again may be important. It can point to a pattern that tells you where to look next.",
        ),
    ]


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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


def explain_rejection(clue: Clue, problem: Problem, tool: Tool) -> str:
    return (
        f"(No story: {tool.label} does not fit this mystery well enough for {problem.label}. "
        f"Pick a better tool or a different clue/problem pair.)"
    )


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTING_REGISTRY:
        lines.append(asp.fact("setting", sid))
    for cid, clue in CLUE_REGISTRY.items():
        lines.append(asp.fact("clue", cid))
        lines.append(asp.fact("clue_kind", cid, clue.kind))
    for pid, prob in PROBLEM_REGISTRY.items():
        lines.append(asp.fact("problem", pid))
    for tid in TOOL_REGISTRY:
        lines.append(asp.fact("tool", tid))
    return "\n".join(lines)


ASP_RULES = r"""
compatible(S,C,P) :- setting(S), clue(C), problem(P), valid_pair(S,C,P).
valid_pair(hall,scratch,box).
valid_pair(hall,pebble,box).
valid_pair(attic,pebble,drawer).
valid_pair(attic,note,drawer).
valid_pair(attic,pebble,panel).
valid_pair(library,note,box).
valid_pair(library,scratch,drawer).
valid_pair(library,note,drawer).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show compatible/3."))
    return sorted(set(asp.atoms(model, "compatible")))


def asp_verify() -> int:
    import io
    import contextlib

    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: ASP gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH: ASP gate and valid_combos() differ.")

    try:
        sample = generate(default_sample_params())
        _ = sample.story
        print("OK: default generation smoke test succeeded.")
    except Exception as exc:  # noqa: BLE001
        print(f"FAILED: default generation smoke test crashed: {exc}")
        return 1

    try:
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            emit(sample, trace=False, qa=False)
        print("OK: emit smoke test succeeded.")
    except Exception as exc:  # noqa: BLE001
        print(f"FAILED: emit smoke test crashed: {exc}")
        rc = 1

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Mystery storyworld: exploratory searching, public clues, abject frustration, and problem solving."
    )
    ap.add_argument("--setting", choices=SETTING_REGISTRY)
    ap.add_argument("--clue", choices=CLUE_REGISTRY)
    ap.add_argument("--problem", choices=PROBLEM_REGISTRY)
    ap.add_argument("--tool", choices=TOOL_REGISTRY)
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--trait", choices=TRAITS)
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


def default_sample_params() -> StoryParams:
    return StoryParams(
        setting="hall",
        clue="scratch",
        problem="box",
        tool="clip",
        name="Mina",
        trait="curious",
        seed=0,
    )


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.tool and args.problem:
        if not reasonableness_gate(CLUE_REGISTRY[args.clue or "scratch"], PROBLEM_REGISTRY[args.problem], TOOL_REGISTRY[args.tool]):
            raise StoryError(explain_rejection(CLUE_REGISTRY[args.clue or "scratch"], PROBLEM_REGISTRY[args.problem], TOOL_REGISTRY[args.tool]))

    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.clue is None or c[1] == args.clue)
              and (args.problem is None or c[2] == args.problem)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting, clue, problem = rng.choice(sorted(combos))
    tool = args.tool
    if tool is None:
        if problem == "box":
            tool = "clip"
        elif problem == "drawer":
            tool = rng.choice(["clip", "ruler"])
        else:
            tool = "coin"
    name = args.name or rng.choice(NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(setting=setting, clue=clue, problem=problem, tool=tool, name=name, trait=trait)


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTING_REGISTRY:
        raise StoryError("Unknown setting.")
    if params.clue not in CLUE_REGISTRY:
        raise StoryError("Unknown clue.")
    if params.problem not in PROBLEM_REGISTRY:
        raise StoryError("Unknown problem.")
    if params.tool not in TOOL_REGISTRY:
        raise StoryError("Unknown tool.")
    setting = SETTING_REGISTRY[params.setting]
    clue = CLUE_REGISTRY[params.clue]
    problem = PROBLEM_REGISTRY[params.problem]
    tool = TOOL_REGISTRY[params.tool]
    world = tell(setting, clue, problem, tool, params.name, params.trait)
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show compatible/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, clue, problem) triples:")
        for s, c, p in combos:
            print(f"  {s:8} {c:8} {p}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        curated = [
            StoryParams(setting="hall", clue="scratch", problem="box", tool="clip", name="Mina", trait="curious"),
            StoryParams(setting="attic", clue="note", problem="drawer", tool="ruler", name="Toby", trait="patient"),
            StoryParams(setting="library", clue="note", problem="box", tool="clip", name="Ivy", trait="quiet"),
        ]
        samples = [generate(p) for p in curated]
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
        header = f"### variant {i + 1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
