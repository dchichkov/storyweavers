#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/haven_problem_solving_bravery_suspense_slice_of.py
===================================================================================

A small standalone storyworld for a slice-of-life tale about keeping a cozy
haven safe during a squally evening.

Premise:
- A child, a parent, and a cozy little room are preparing a calm "haven".
- A sudden problem appears: rainwater, a draft, or a noisy leak threatens the
  calm.
- The child must be brave enough to help solve it, usually by fetching a tool,
  patching something, or making the space cozier.
- The suspense comes from the uncertain moment before the fix works.
- The ending shows the haven restored or improved, with a concrete image of
  what changed.

The world is intentionally small and physical: entities have meters (physical
state) and memes (emotional state), and the prose is driven by the simulated
state rather than being a frozen paragraph with noun swaps.
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
SUSPENSE_MIN = 1.0


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
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class HavenSetting:
    id: str
    place: str
    cozy_image: str
    sound: str
    shelter_word: str
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
    name: str
    thing: str
    symptom: str
    danger: str
    source: str
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
    name: str
    phrase: str
    use_text: str
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
class Fix:
    id: str
    sense: int
    power: int
    text: str
    fail: str
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


def _r_settle(world: World) -> list[str]:
    out: list[str] = []
    for pid, problem in PROBLEMS.items():
        ent = world.entities.get(pid)
        if not ent or ent.meters["active"] < THRESHOLD:
            continue
        sig = ("settle", pid)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        world.get("haven").meters["unease"] += 1
        world.get("child").memes["suspense"] += 1
        out.append("__suspense__")
    return out


def _r_fix(world: World) -> list[str]:
    out: list[str] = []
    if world.get("haven").meters["unease"] < THRESHOLD:
        return out
    sig = ("fixable",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    out.append("__fix__")
    return out


CAUSAL_RULES = [Rule("settle", _r_settle), Rule("fix", _r_fix)]


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


def problem_risky(problem: Problem) -> bool:
    return True


def sensible_fixes() -> list[Fix]:
    return [f for f in FIXES.values() if f.sense >= SENSE_MIN]


def best_fix() -> Fix:
    return max(FIXES.values(), key=lambda f: f.sense)


def fix_succeeds(fix: Fix, problem: Problem, delay: int) -> bool:
    return fix.power >= 1 + delay


def predict_problem(world: World, problem_id: str) -> dict:
    sim = world.copy()
    _trigger_problem(sim, sim.get(problem_id), narrate=False)
    return {
        "unease": sim.get("haven").meters["unease"],
        "suspense": sim.get("child").memes["suspense"],
    }


def _trigger_problem(world: World, problem_ent: Entity, narrate: bool = True) -> None:
    problem_ent.meters["active"] += 1
    propagate(world, narrate=narrate)


def intro(world: World, child: Entity, parent: Entity, setting: HavenSetting) -> None:
    child.memes["joy"] += 1
    world.say(
        f"In the evening, {child.id} and {parent.id} made a little haven in "
        f"{setting.place}. {setting.cozy_image}"
    )
    world.say(
        f'The room felt like a safe nest. It was the kind of place where a small '
        f'problem could still feel big.'
    )


def problem_appears(world: World, problem: Problem, setting: HavenSetting) -> None:
    world.say(
        f"Then a {problem.name} started to bother the haven. {problem.symptom} "
        f"{problem.source} the peace, and the cozy corner did not feel so calm anymore."
    )


def worry(world: World, child: Entity, parent: Entity, problem: Problem) -> None:
    child.memes["worry"] += 1
    world.say(
        f'{child.id} frowned. "If we leave it, {problem.danger}," '
        f"{parent.label_word} said quietly."
    )


def brave_step(world: World, child: Entity, tool: Tool) -> None:
    child.memes["bravery"] += 1
    world.say(
        f'{child.id} took a breath and said, "I can help." '
        f'{child.pronoun().capitalize()} went to get {tool.phrase}.'
    )


def suspense_beat(world: World, child: Entity, problem: Problem) -> None:
    if world.get("haven").meters["unease"] >= SUSPENSE_MIN:
        world.say(
            f"The hallway was darker than the cozy room, and for one slow moment "
            f"{child.id} listened to the sound of {problem.source}ing."
        )


def fix_problem(world: World, parent: Entity, child: Entity, problem: Problem, fix: Fix) -> None:
    world.get("haven").meters["unease"] = 0.0
    child.memes["worry"] = 0.0
    child.memes["suspense"] = 0.0
    child.memes["joy"] += 1
    body = fix.text.replace("{problem}", problem.thing)
    world.say(
        f"{parent.label_word.capitalize()} watched {child.id} use {body}."
    )
    world.say(
        f"The {problem.name} eased, and the haven felt steady again."
    )


def fix_fails(world: World, parent: Entity, child: Entity, problem: Problem, fix: Fix) -> None:
    world.get("haven").meters["unease"] += 1
    body = fix.fail.replace("{problem}", problem.thing)
    world.say(f"{parent.label_word.capitalize()} helped, but {body}.")
    world.say(
        "They had to try again, because the haven was still not quite settled."
    )


def ending(world: World, child: Entity, parent: Entity, setting: HavenSetting, problem: Problem, fixed: bool) -> None:
    if fixed:
        world.say(
            f'At last, {setting.cozy_image.lower()} now sat under a dry, quiet window. '
            f'{child.id} curled up beside {parent.id}, and the little haven felt safe.'
        )
    else:
        world.say(
            f'By the end, the room was still a work in progress, but {child.id} and '
            f'{parent.id} stayed together and kept trying.'
        )


def tell(setting: HavenSetting, problem: Problem, tool: Tool, fix: Fix, delay: int = 0,
         child_name: str = "Mia", child_gender: str = "girl",
         parent_name: str = "Mom", parent_gender: str = "mother") -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    parent = world.add(Entity(id=parent_name, kind="character", type=parent_gender, role="parent"))
    haven = world.add(Entity(id="haven", type="room", label="haven"))
    prob = world.add(Entity(id=problem.id, type="problem", label=problem.name))
    tool_ent = world.add(Entity(id=tool.id, type="tool", label=tool.name))
    world.facts["delay"] = delay

    intro(world, child, parent, setting)
    world.para()
    problem_appears(world, problem, setting)
    worry(world, child, parent, problem)
    _trigger_problem(world, prob)
    suspense_beat(world, child, problem)
    world.para()
    brave_step(world, child, tool)
    if fix_succeeds(fix, problem, delay):
        fix_problem(world, parent, child, problem, fix)
        ending(world, child, parent, setting, problem, True)
        world.facts["outcome"] = "fixed"
    else:
        fix_fails(world, parent, child, problem, fix)
        ending(world, child, parent, setting, problem, False)
        world.facts["outcome"] = "unfinished"
    world.facts.update(
        setting=setting, problem=problem, tool=tool, fix=fix, child=child, parent=parent,
        fixed=world.facts["outcome"] == "fixed",
    )
    return world


SETTINGS = {
    "window_nook": HavenSetting(
        id="window_nook",
        place="the window nook",
        cozy_image="A quilt, a stack of picture books, and a little lamp made a soft glow",
        sound="rain tapping on the glass",
        shelter_word="nook",
        tags={"haven", "window"},
    ),
    "living_room": HavenSetting(
        id="living_room",
        place="the living room corner",
        cozy_image="A blanket fort, two pillows, and a small rug made it feel like a tiny home",
        sound="a kettle humming in the kitchen",
        shelter_word="corner",
        tags={"haven", "living"},
    ),
    "porch_den": HavenSetting(
        id="porch_den",
        place="the covered porch",
        cozy_image="A folding chair, a warm throw, and a lantern made the porch feel like a haven",
        sound="wind nudging the screen door",
        shelter_word="porch",
        tags={"haven", "porch"},
    ),
}

PROBLEMS = {
    "drip": Problem(
        id="drip",
        name="drip",
        thing="the drip",
        symptom="A thin line of water kept tapping the sill",
        danger="the books might get damp",
        source="drip",
        tags={"water", "suspense"},
    ),
    "draft": Problem(
        id="draft",
        name="draft",
        thing="the draft",
        symptom="A cold breeze sneaked under the door",
        danger="the little lamp might wobble and flicker",
        source="whisper",
        tags={"wind", "suspense"},
    ),
    "noise": Problem(
        id="noise",
        name="noise",
        thing="the noise",
        symptom="A creak from the attic made everyone look up",
        danger="the quiet haven would stop feeling calm",
        source="creak",
        tags={"sound", "suspense"},
    ),
}

TOOLS = {
    "towel": Tool(id="towel", name="a towel", phrase="a folded towel", use_text="roll up"),
    "lamp": Tool(id="lamp", name="the lamp", phrase="the little lamp", use_text="turn on"),
    "tape": Tool(id="tape", name="some tape", phrase="a strip of tape", use_text="patch with"),
    "bookstack": Tool(id="bookstack", name="a stack of books", phrase="a stack of books", use_text="brace"),
}

FIXES = {
    "towel_patch": Fix(
        id="towel_patch", sense=3, power=2,
        text="rolled up {problem} with a folded towel and tucked it under the sill",
        fail="the towel was not enough to hold back {problem}",
        qa_text="rolled up the problem with a towel and tucked it under the sill",
    ),
    "tape_patch": Fix(
        id="tape_patch", sense=3, power=3,
        text="patched the loose edge with a strip of tape until it held firm",
        fail="the tape kept peeling away from {problem}",
        qa_text="patched the loose edge with tape until it held firm",
    ),
    "bookbrace": Fix(
        id="bookbrace", sense=2, power=1,
        text="braced the rattling door with a stack of books",
        fail="the stack of books slid away from {problem}",
        qa_text="braced the rattling door with books",
    ),
    "ignore": Fix(
        id="ignore", sense=1, power=0,
        text="looked at {problem} and hoped it would stop on its own",
        fail="didn't manage to help {problem} at all",
        qa_text="ignored the problem",
    ),
}


GIRL_NAMES = ["Mia", "Lily", "Nora", "Ava", "Zoe", "Ella"]
BOY_NAMES = ["Leo", "Finn", "Max", "Noah", "Theo", "Ben"]
TRAITS = ["careful", "curious", "brave", "calm", "thoughtful"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for pid, problem in PROBLEMS.items():
            for tid, tool in TOOLS.items():
                for fid, fix in FIXES.items():
                    if fix.sense >= SUSPENSE_MIN:
                        combos.append((sid, pid, fid))
    return combos


@dataclass
class StoryParams:
    setting: str
    problem: str
    tool: str
    fix: str
    child_name: str
    child_gender: str
    parent_name: str
    parent_gender: str
    trait: str
    delay: int = 0
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
    "haven": [("What is a haven?",
               "A haven is a safe, comforting place where someone can relax and feel protected.")],
    "drip": [("What is a drip?",
              "A drip is a little bit of liquid that falls one drop at a time.")],
    "draft": [("What is a draft?",
               "A draft is a little flow of air that sneaks through a crack or under a door.")],
    "noise": [("What is a creak?",
              "A creak is a squeaky sound that wood or a door can make when it moves.")],
    "towel": [("What does a towel do?",
               "A towel can soak up water or help dry something off.")],
    "tape": [("What is tape for?",
              "Tape can hold things together or cover a small crack for a while.")],
    "bravery": [("What does bravery mean?",
                 "Bravery means doing something hard or a little scary when it needs to be done.")],
    "problem": [("What is problem solving?",
                  "Problem solving means noticing what is wrong and trying smart steps until it gets better.")],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a slice-of-life story for a 3-to-5-year-old that includes the word "haven".',
        f"Tell a gentle story where {f['child'].id} helps keep a cozy haven safe when {f['problem'].name} appears.",
        f"Write a small brave story where a child solves a home problem and the ending shows the haven feeling calm again.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    setting = f["setting"]
    problem = f["problem"]
    fix = f["fix"]
    qa = [
        ("What were they trying to make?",
         f"They were trying to make a haven, a cozy place where they could feel calm and safe. The room had soft things in it so it could feel warm and peaceful."),
        ("What problem showed up?",
         f"{problem.symptom}. That small trouble made the haven feel uneasy for a little while."),
        ("What did the child do?",
         f"{child.id} stayed brave, found a way to help, and used {fix.qa_text}. It was a careful fix, not a big dramatic rescue."),
    ]
    if world.get("haven").meters["unease"] < THRESHOLD:
        qa.append((
            "How did the story end?",
            f"It ended with the haven calm again. The problem was handled, and {child.id} could settle in beside {parent.id}.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["setting"].tags) | set(world.facts["problem"].tags) | {"haven", "problem", "bravery"}
    out = []
    for key, pairs in KNOWLEDGE.items():
        if key in tags:
            out.extend(pairs)
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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="window_nook",
        problem="drip",
        tool="towel",
        fix="towel_patch",
        child_name="Mia",
        child_gender="girl",
        parent_name="Mom",
        parent_gender="mother",
        trait="careful",
        delay=0,
    ),
    StoryParams(
        setting="living_room",
        problem="draft",
        tool="tape",
        fix="tape_patch",
        child_name="Leo",
        child_gender="boy",
        parent_name="Dad",
        parent_gender="father",
        trait="brave",
        delay=0,
    ),
    StoryParams(
        setting="porch_den",
        problem="noise",
        tool="bookstack",
        fix="bookbrace",
        child_name="Nora",
        child_gender="girl",
        parent_name="Mom",
        parent_gender="mother",
        trait="thoughtful",
        delay=0,
    ),
]


def explain_rejection(setting: HavenSetting, problem: Problem, fix: Fix) -> str:
    return (
        f"(No story: the chosen fix is not a strong enough problem-solving answer "
        f"for this haven problem. Pick a better fix or a different problem.)"
    )


def outcome_of(params: StoryParams) -> str:
    return "fixed" if fix_succeeds(FIXES[params.fix], PROBLEMS[params.problem], params.delay) else "unfinished"


def explain_fix(fid: str) -> str:
    f = FIXES[fid]
    better = ", ".join(sorted(k for k, v in FIXES.items() if v.sense >= SUSPENSE_MIN))
    return f"(Refusing fix '{fid}': sense too low. Try one of: {better}.)"


ASP_RULES = r"""
valid(S,P,F) :- setting(S), problem(P), fix(F), fix_sense(F, X), xmin(M), X >= M.
fixed(P,F) :- problem(P), fix(F), fix_power(F, Pwr), delay(D), Pwr >= D + 1.
outcome(fixed) :- fixed(_, _).
outcome(unfinished) :- not outcome(fixed).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for pid in PROBLEMS:
        lines.append(asp.fact("problem", pid))
    for fid, f in FIXES.items():
        lines.append(asp.fact("fix", fid))
        lines.append(asp.fact("fix_sense", fid, f.sense))
        lines.append(asp.fact("fix_power", fid, f.power))
    lines.append(asp.fact("xmin", int(SUSPENSE_MIN)))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    scenario = "\n".join([asp.fact("delay", params.delay)])
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        rc = 1
        print("MISMATCH in valid_combos.")
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        if not sample.story.strip():
            raise RuntimeError("empty story")
        print("OK: generate() smoke test passed.")
    except Exception as exc:
        print(f"FAILED: generate() smoke test: {exc}")
        return 1
    cases = CURATED[:]
    bad = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if bad:
        rc = 1
        print(f"MISMATCH: {bad} outcomes differ.")
    else:
        print("OK: ASP parity verified.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A slice-of-life haven storyworld.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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
    if args.fix and FIXES[args.fix].sense < SUSPENSE_MIN:
        raise StoryError(explain_fix(args.fix))
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.problem is None or c[1] == args.problem)
              and (args.fix is None or c[2] == args.fix)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, problem, fix = rng.choice(sorted(combos))
    tool = args.tool or rng.choice(sorted(TOOLS))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(
        setting=setting, problem=problem, tool=tool, fix=fix,
        child_name=name, child_gender=gender, parent_name=parent.capitalize(), parent_gender=parent,
        trait=trait, delay=0,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.problem not in PROBLEMS or params.fix not in FIXES or params.tool not in TOOLS:
        raise StoryError("Invalid params.")
    world = tell(SETTINGS[params.setting], PROBLEMS[params.problem], TOOLS[params.tool], FIXES[params.fix],
                 delay=params.delay, child_name=params.child_name, child_gender=params.child_gender,
                 parent_name=params.parent_name, parent_gender=params.parent_gender)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
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
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("", "#show valid/3."))
        print(f"{len(asp.atoms(model, 'valid'))} valid combos")
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
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
            header = f"### {p.child_name}: {p.problem} in {p.setting} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
