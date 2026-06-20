#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/tiki_damper_gondola_swim_school_problem_solving.py
===================================================================================

A standalone story world for a small swim-school problem-solving tale.

Seeded premise:
- Setting: swim school
- Words: tiki, damper, gondola
- Features: Problem Solving, Conflict, Cautionary
- Style: Rhyming Story

The world models a child at swim school who wants to use a tiki prop to reach a
gondola-like pool toy, meets a cautionary conflict, and learns a safer way with
help from a grown-up and simple problem-solving gear.
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
SENSE_MIN = 2


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
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

@dataclass
class Setting:
    id: str
    place: str
    details: str
    sound: str

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Prop:
    id: str
    label: str
    phrase: str
    risky: bool = False
    safe: bool = False
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Problem:
    id: str
    label: str
    noun: str
    needed: str
    danger: str
    rhyme: str
    spread: int
    risky: bool = True
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Aid:
    id: str
    label: str
    phrase: str
    power: int
    sense: int
    text: str
    fail: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


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

    def characters(self) -> list[Entity]:
        return [e for e in list(self.entities.values()) if e.kind == "character"]

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
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    for e in world.characters():
        if e.memes["worry"] < THRESHOLD:
            continue
        sig = ("worry", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["tension"] += 1
        out.append("__worry__")
    return out


def _r_spill(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.meters["splashed"] < THRESHOLD:
            continue
        sig = ("spill", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        if "pool" in world.entities:
            world.get("pool").meters["ripple"] += 1
        for c in world.characters():
            c.memes["alarm"] += 1
        out.append("__spill__")
    return out


CAUSAL_RULES = [Rule("worry", "social", _r_worry), Rule("spill", "physical", _r_spill)]


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
        for s in produced:
            world.say(s)
    return produced


def problem_at_risk(problem: Problem, prop: Prop) -> bool:
    return problem.risky and prop.risky


def is_sensible(aid: Aid) -> bool:
    return aid.sense >= SENSE_MIN


def severity(problem: Problem, delay: int) -> int:
    return problem.spread + delay


def contained(aid: Aid, problem: Problem, delay: int) -> bool:
    return aid.power >= severity(problem, delay)


def foresee(world: World, prop_id: str) -> dict:
    sim = world.copy()
    _attempt(sim, sim.get(prop_id), narrate=False)
    return {"splashed": sim.get(prop_id).meters["splashed"] >= THRESHOLD,
            "ripple": sim.get("pool").meters["ripple"]}


def _attempt(world: World, prop: Entity, narrate: bool = True) -> None:
    prop.meters["splashed"] += 1
    propagate(world, narrate=narrate)


def setup(world: World, child: Entity, parent: Entity, setting: Setting, problem: Problem) -> None:
    child.memes["joy"] += 1
    world.say(
        f"At swim school, {child.id} and {parent.label_word} came in with a splash; "
        f"{setting.details}"
    )
    world.say(
        f"{child.id} saw the {problem.label} and grinned, ready to make a song to begin."
    )


def want(world: World, child: Entity, problem: Problem) -> None:
    child.memes["worry"] += 1
    world.say(
        f'"I need the {problem.needed}," said {child.id}, "to reach the {problem.noun} with style."'
    )


def warn(world: World, parent: Entity, child: Entity, problem: Problem, prop: Prop) -> None:
    pred = foresee(world, "tiki")
    child.memes["worry"] += 1
    world.facts["predicted"] = pred
    world.say(
        f'"Careful," said {parent.label_word}, "that {prop.label} is a tricky old thing; '
        f'it can tip and slip and make a mess of the ring."'
    )
    if pred["splashed"]:
        world.say(f'"If it falls, it will splash the {problem.noun} and make the whole lane feel wrong."')


def defy(world: World, child: Entity, prop: Prop) -> None:
    child.memes["defiance"] += 1
    world.say(
        f"{child.id} shook {child.pronoun('possessive')} head with a little grin of pride, "
        f"and reached for the {prop.label} to carry it inside."
    )


def grabback(world: World, parent: Entity, child: Entity) -> None:
    child.memes["grabbed"] += 1
    child.memes["conflict"] += 1
    world.say(
        f"But {parent.label_word} held {child.pronoun('possessive')} hand and stayed calm and near, "
        f"\"We can solve this safely; let's listen, dear.\""
    )


def resolve_story(world: World, parent: Entity, child: Entity, aid: Aid, problem: Problem,
                  prop: Prop, alt: Prop) -> None:
    child.memes["joy"] += 1
    child.memes["relief"] += 1
    world.say(
        f"{parent.label_word.capitalize()} smiled, then pointed to {alt.phrase}, neat as can be: "
        f"\"Use this to reach the {problem.noun}; the {prop.label} stays dry by the sea.\""
    )
    world.say(
        f"{child.id} nodded and cheered, and the little plan worked with a bright little chime, "
        f"{aid.text}."
    )
    world.say(
        f"At the end of the lesson, the {problem.noun} stayed safe and the song found its rhyme."
    )


def fail_resolve(world: World, parent: Entity, child: Entity, aid: Aid, problem: Problem, prop: Prop) -> None:
    child.memes["fear"] += 1
    world.say(
        f"{parent.label_word.capitalize()} hurried in, but {aid.fail}; the splash spread fast like a stormy refrain."
    )
    world.say(
        f"The {prop.label} tipped, the water leapt up, and the {problem.noun} was soggy with rain."
    )
    world.say(
        "Everyone got out safely, but the lesson was stern: unsafe shortcuts can turn to a spill."
    )


def tell(setting: Setting, problem: Problem, prop: Prop, aid: Aid, alt: Prop,
         child_name: str = "Mia", child_gender: str = "girl",
         parent_gender: str = "mother", delay: int = 0, caution_first: bool = True) -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_gender, role="parent"))
    world.add(Entity(id="pool", type="pool", label="the pool lane"))
    world.add(Entity(id="tiki", type="prop", label="the tiki prop"))
    world.add(Entity(id="gondola", type="prop", label="the gondola toy"))
    world.add(Entity(id="damper", type="tool", label="the damper"))
    child.memes["worry"] = 1.0 if caution_first else 0.0

    setup(world, child, parent, setting, problem)
    world.para()
    want(world, child, problem)
    warn(world, parent, child, problem, prop)
    if caution_first and child.memes["worry"] > 1.5:
        world.say(f"{child.id} paused, then nodded; the warning won before the waves began.")
        world.para()
        resolve_story(world, parent, child, aid, problem, prop, alt)
        outcome = "averted"
    else:
        defy(world, child, prop)
        grabback(world, parent, child)
        world.para()
        _attempt(world, world.get("tiki"))
        world.say(f'"Oops!" shouted {child.id}, as the {prop.label} rocked and the water rose high.')
        if contained(aid, problem, delay):
            world.para()
            resolve_story(world, parent, child, aid, problem, prop, alt)
            outcome = "contained"
        else:
            world.para()
            fail_resolve(world, parent, child, aid, problem, prop)
            outcome = "burned"

    world.facts.update(child=child, parent=parent, setting=setting, problem=problem,
                       prop=prop, alt=alt, aid=aid, delay=delay, outcome=outcome,
                       caution_first=caution_first)
    return world


SETTINGS = {
    "swim_school": Setting(
        "swim_school",
        "swim school",
        "The pool had blue tiles, soft lanes, and a whistle that kept the day in tune.",
        "drip-drip"),
}

PROBLEMS = {
    "gondola": Problem("gondola", "gondola", "gondola toy", "tiki", "tip and splash", "slow boat", 2, tags={"gondola"}),
    "lane_marker": Problem("lane_marker", "lane marker", "lane marker", "the damper", "slip and drift", "pool line", 1, tags={"lane"}),
}

PROPS = {
    "tiki": Prop("tiki", "tiki", "the tiki", risky=True, tags={"tiki"}),
    "damper": Prop("damper", "damper", "the damper", risky=True, tags={"damper"}),
    "gondola": Prop("gondola", "gondola", "the gondola", risky=True, tags={"gondola"}),
    "float": Prop("float", "float board", "the float board", safe=True, tags={"float"}),
}

AIDS = {
    "damper": Aid("damper", "damper", "the damper slowed the slip and the water calmed the trim", 3, 3,
                  "the damper slowed the slip and the water calmed the trim",
                  "the damper was too late, and the splash kept on sailing", tags={"damper"}),
    "pole": Aid("pole", "pool pole", "the pool pole reached the far toy in time", 2, 2,
                "the pool pole reached the far toy in time",
                "the pool pole could not catch the toy before the splash", tags={"pole"}),
    "net": Aid("net", "net", "the net lifted the toy and kept the lane from a fright", 4, 3,
               "the net lifted the toy and kept the lane from a fright",
               "the net slipped in the rush and the lane stayed wet", tags={"net"}),
}



@dataclass
class StoryParams:
    setting: str
    problem: str
    prop: str
    aid: str
    alt: str
    child: str
    child_gender: str
    parent_gender: str
    delay: int = 0
    caution_first: bool = True
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")

CURATED = [
    ("swim_school", "gondola", "tiki", "damper", "float", "Mia", "girl", "mother", 0, True),
    ("swim_school", "gondola", "tiki", "pole", "float", "Noah", "boy", "father", 1, True),
    ("swim_school", "lane_marker", "damper", "net", "gondola", "Ava", "girl", "mother", 0, False),
]



def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for pid, problem in PROBLEMS.items():
            for propid, prop in PROPS.items():
                if problem_at_risk(problem, prop):
                    combos.append((sid, pid, propid))
    return combos


KNOWLEDGE = {
    "tiki": [("What is a tiki?",
              "A tiki is a carved island-style decoration. It is often used as a prop or a fun symbol in stories and games.")],
    "damper": [("What does a damper do?",
                "A damper helps slow or quiet a motion, so something moves less and is easier to control.")],
    "gondola": [("What is a gondola?",
                 "A gondola is a small boat or a boat-shaped ride that moves gently on water or along a line.")],
    "swim_school": [("What is swim school?",
                     "Swim school is a place where children learn water safety and practice swimming with help.")],
    "cautionary": [("What is a cautionary story?",
                   "A cautionary story warns about a risky choice and shows a safer choice instead.")],
    "problem_solving": [("What is problem solving?",
                         "Problem solving means finding a smart way to fix a problem without making it worse.")],
    "conflict": [("What is a conflict in a story?",
                  "A conflict is the part where characters want different things or disagree for a moment.")],
}
KNOWLEDGE_ORDER = ["swim_school", "tiki", "damper", "gondola", "problem_solving", "conflict", "cautionary"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a rhyming story set in swim school that includes the words "{f["prop"].label}", "{f["aid"].label}", and "{f["problem"].label}".',
        f"Tell a cautionary swim-school story where {f['child'].id} wants to use {f['prop'].label} to reach the {f['problem'].noun}, but {f['parent'].label_word} warns {f['child'].pronoun('object')} and they solve it safely.",
        f"Write a problem-solving story with a little conflict, a safe helper, and a clear ending image about the {f['problem'].noun}.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child, parent, problem, prop, aid = f["child"], f["parent"], f["problem"], f["prop"], f["aid"]
    qa = [
        ("Who is the story about?",
         f"It is about {child.id} at swim school with {parent.label_word}. {child.id} wants to solve a pool problem, but the choice has to be safe."),
        ("What did {0} want to use?".format(child.id),
         f"{child.id} wanted to use {prop.label} to reach the {problem.noun}. That idea sounded quick, but it was not the safest path."),
        ("Why did the grown-up warn them?",
         f"{parent.label_word.capitalize()} warned them because the {prop.label} could tip and splash the {problem.noun}. The warning was a cautionary one, meant to stop a bigger mess."),
    ]
    if f["outcome"] == "averted":
        qa.append(("How did they solve the problem?",
                   f"They listened right away and used the {f['alt'].label} instead. That kept the {problem.noun} steady and let the day stay bright and fine."))
    elif f["outcome"] == "contained":
        qa.append(("How did they solve the problem?",
                   f"They had a small spill first, but then {parent.label_word} used {aid.label} to settle it down. After that, the {problem.noun} was safe again and the worry was done."))
    else:
        qa.append(("How did the story end?",
                   f"Everyone got out safely, but the splash got bigger than the plan. The lesson was to slow down and choose the safer tool next time."))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["problem"].tags) | set(world.facts["prop"].tags) | set(world.facts["aid"].tags)
    out = []
    for key in KNOWLEDGE_ORDER:
        if key in tags:
            out.extend(KNOWLEDGE[key])
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
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


def explain_rejection(prop: Prop, problem: Problem) -> str:
    if not problem_at_risk(problem, prop):
        return f"(No story: the {prop.label} is not a real hazard for the {problem.noun}.)"
    return "(No story: this combination does not support a sensible problem-solving turn.)"


def outcome_of(params: StoryParams) -> str:
    if params.caution_first:
        return "averted"
    return "contained" if contained(AIDS[params.aid], PROBLEMS[params.problem], params.delay) else "burned"


ASP_RULES = r"""
hazard(P, Pr) :- problem(P), prop(Pr), risky(Pr).
sensible(A) :- aid(A), sense(A, S), sense_min(M), S >= M.
outcome(averted) :- caution_first.
severity(P, D) :- problem(P), spread(P, S), delay(D), V = S + D.
outcome(contained) :- not caution_first, chosen_aid(A), aid(A), power(A, P), severity(Prob, D), P >= D + 1.
outcome(burned) :- not caution_first, not outcome(contained).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for pid, p in PROBLEMS.items():
        lines.append(asp.fact("problem", pid))
        lines.append(asp.fact("spread", pid, p.spread))
        if p.risky:
            lines.append(asp.fact("risky_problem", pid))
    for gid, g in PROPS.items():
        lines.append(asp.fact("prop", gid))
        if g.risky:
            lines.append(asp.fact("risky", gid))
    for aid, a in AIDS.items():
        lines.append(asp.fact("aid", aid))
        lines.append(asp.fact("sense", aid, a.sense))
        lines.append(asp.fact("power", aid, a.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show hazard/2."))
    return sorted(set(asp.atoms(model, "hazard")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        rc = 1
        print("MISMATCH in valid combos")
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, problem=None, prop=None, aid=None, alt=None, child=None, child_gender=None, parent_gender=None, delay=None, caution_first=None), random.Random(777)))
        _ = sample.story
        print("OK: generate smoke test passed.")
    except Exception as e:
        print(f"SMOKE TEST FAILED: {e}")
        return 1
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Swim-school rhyming story world.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--prop", choices=PROPS)
    ap.add_argument("--aid", choices=AIDS)
    ap.add_argument("--alt", choices=PROPS)
    ap.add_argument("--child")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--parent-gender", choices=["mother", "father"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2])
    ap.add_argument("--caution-first", action="store_true")
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
              and (args.prop is None or c[2] == args.prop)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, problem, prop = rng.choice(sorted(combos))
    aid = args.aid or rng.choice(sorted(AIDS))
    alt = args.alt or "float"
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    child = args.child or rng.choice(["Mia", "Noah", "Ava", "Leo", "Zoe"])
    parent_gender = args.parent_gender or rng.choice(["mother", "father"])
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    caution_first = args.caution_first or rng.choice([True, False])
    return StoryParams(setting, problem, prop, aid, alt, child, child_gender, parent_gender, delay, caution_first)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], PROBLEMS[params.problem], PROPS[params.prop],
                 AIDS[params.aid], PROPS[params.alt], params.child, params.child_gender,
                 params.parent_gender, params.delay, params.caution_first)
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
        print(asp_program("", "#show hazard/2.\n#show sensible/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("\n".join(f"{a} {b}" for a, b in asp_valid_combos()))
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(StoryParams(*p)) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {i+1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
