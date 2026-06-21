#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/dessert_bash_problem_solving_cautionary_moral_value.py
======================================================================================

A standalone story world about a dessert bash where a small problem grows,
the kids solve it, and the ending carries a cautious moral lesson with a comic
tone. The seed words are "dessert" and "bash", and the world keeps the story
child-facing, concrete, and state-driven.

Premise:
- A dessert bash is being set up.
- A simple mistake threatens the treats.
- The kids notice, think, and fix it together.
- A cautionary moral lands at the end: being careful saves the party.

The engine uses typed entities with physical meters and emotional memes, a small
forward-chaining causal core, a Python reasonableness gate, and an inline ASP
twin for parity checks.
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
    role: str = ""
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
    scene: str
    table: str
    venue_word: str = "bash"
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
class Dessert:
    id: str
    label: str
    plural: bool = False
    fragile: bool = False
    sweet: bool = True
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
    risk: str
    source: str
    spread: int
    bad: bool = True
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
class Fix:
    id: str
    label: str
    sense: int
    power: int
    action: str
    fail: str
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
        w = World()
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
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


def _r_spoil(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.meters["mess"] < THRESHOLD:
            continue
        sig = ("spoil", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        if e.label in {"cupcakes", "cookies", "pudding"}:
            e.meters["ruined"] += 1
            out.append(f"The {e.label} looked sad and sticky.")
    return out


CAUSAL_RULES = [Rule("spoil", "physical", _r_spoil)]


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


def sensible_fixes() -> list[Fix]:
    return [f for f in FIXES.values() if f.sense >= SENSE_MIN]


def hazard(problem: Problem, dessert: Dessert) -> bool:
    return problem.bad and dessert.fragile


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for sid in SETTINGS:
        for pid, p in PROBLEMS.items():
            for did, d in DESSERTS.items():
                if hazard(p, d):
                    out.append((sid, pid, did))
    return out


def problem_severity(problem: Problem) -> int:
    return problem.spread


def fixed_by(fix: Fix, problem: Problem) -> bool:
    return fix.power >= problem_severity(problem)


def tell_setup(world: World, kids: tuple[Entity, Entity], setting: Setting, dessert: Dessert) -> None:
    a, b = kids
    a.memes["joy"] += 1
    b.memes["joy"] += 1
    world.say(
        f"At the {setting.place}, {setting.scene} made the whole {setting.venue_word} feel ready for a comic little bash."
    )
    world.say(
        f"{a.id} and {b.id} built the table. {setting.table} sat in the middle, and the {dessert.label} waited like tiny kings and queens."
    )
    world.say(
        f'"It is dessert time!" {a.id} said, and {b.id} clapped because the bash was about to begin.'
    )


def need_help(world: World, hero: Entity, problem: Problem) -> None:
    hero.memes["worry"] += 1
    world.say(
        f"Then a {problem.label} problem popped up. {problem.source} had made the {problem.risk}, and the plan suddenly felt wobbly."
    )
    world.say(
        f'"We need to solve this," {hero.id} said, looking serious in a very small and very funny way.'
    )


def inspect(world: World, helper: Entity, problem: Problem, dessert: Dessert) -> None:
    helper.memes["care"] += 1
    world.say(
        f'{helper.id} peered at the table and said, "If we do nothing, the {dessert.label} will get {problem.risk}."'
    )
    world.say("For once, the party was quiet enough to hear the sprinkles think.")


def try_fix(world: World, fixer: Entity, fix: Fix) -> None:
    fixer.memes["bravery"] += 1
    world.say(f'{fixer.id} nodded. "I know! {fix.label}."')
    world.say(f"So {fixer.id} {fix.action}.")


def solve(world: World, fix: Fix, dessert: Dessert, problem: Problem) -> None:
    if fixed_by(fix, problem):
        dessert.meters["ruined"] = 0.0
        dessert.meters["safe"] += 1
        world.say(
            f"That worked. The {dessert.label} stayed bright and cheerful, and the bash came back to life."
        )
    else:
        dessert.meters["ruined"] += 1
        world.say(
            f"That did not work. The {fix.label} was too small for the mess, and the {dessert.label} still looked doomed."
        )


def lesson(world: World, parent: Entity, kids: tuple[Entity, Entity], dessert: Dessert) -> None:
    a, b = kids
    for kid in kids:
        kid.memes["relief"] += 1
        kid.memes["lesson"] += 1
    world.say(
        f"Then {parent.label_word} smiled and said, \"A good bash needs a good plan. Be quick, be kind, and be careful with sweet things.\""
    )
    world.say(
        f"{a.id} and {b.id} promised to remember it. The dessert bash was still a bash, but now it was a wiser one."
    )
    world.say(
        f"In the end, the {dessert.label} sat safe on the table, and nobody had to eat frosting from their sleeve."
    )


def tell(setting: Setting, dessert: Dessert, problem: Problem, fix: Fix,
         kid1: str = "Mina", kid2: str = "Jo", parent_type: str = "mother") -> World:
    world = World()
    a = world.add(Entity(id=kid1, kind="character", type="girl", role="hero"))
    b = world.add(Entity(id=kid2, kind="character", type="boy", role="helper"))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="the parent"))
    cake = world.add(Entity(id="dessert", kind="thing", type="dessert", label=dessert.label))
    world.facts.update(setting=setting, dessert=dessert, problem=problem, fix=fix, hero=a, helper=b, parent=parent)

    tell_setup(world, (a, b), setting, dessert)
    world.para()
    need_help(world, a, problem)
    inspect(world, b, problem, dessert)
    try_fix(world, a, fix)
    solve(world, fix, cake, problem)
    world.para()
    lesson(world, parent, (a, b), dessert)
    world.facts["resolved"] = cake.meters["safe"] >= THRESHOLD
    world.facts["ruined"] = cake.meters["ruined"] >= THRESHOLD
    return world


SETTINGS = {
    "kitchen": Setting(id="kitchen", place="the kitchen", scene="streamers on the chairs", table="The long table", venue_word="bash"),
    "backyard": Setting(id="backyard", place="the backyard", scene="paper lanterns in the trees", table="A picnic table", venue_word="bash"),
}

DESSERTS = {
    "cupcakes": Dessert(id="cupcakes", label="cupcakes", plural=True, fragile=True),
    "cookies": Dessert(id="cookies", label="cookies", plural=True, fragile=True),
    "pudding": Dessert(id="pudding", label="pudding cups", fragile=True),
}

PROBLEMS = {
    "topple": Problem(id="topple", label="topple", risk="frosting was spilling", source="A bumped tray", spread=1),
    "wind": Problem(id="wind", label="wind", risk="napkins were blowing over the treats", source="A silly gust of air", spread=1),
    "crumbs": Problem(id="crumbs", label="crumbs", risk="crumbs had sprinkled onto the plate", source="A cookie broken in half", spread=2),
}

FIXES = {
    "steady": Fix(id="steady", label="a steady hand", sense=3, power=1, action="held the tray level and moved it to the center", fail="tried to hold it steady, but the tray was still wobbling"),
    "napkin": Fix(id="napkin", label="a clean napkin shield", sense=2, power=1, action="tucked a napkin over the top to block the wind", fail="waved a napkin around, but it only made the mess dance"),
    "tray": Fix(id="tray", label="the sturdy tray", sense=3, power=2, action="swapped the treats onto the sturdy tray and carried them carefully", fail="moved the treats once, but then the tray tipped again"),
}


@dataclass
class StoryParams:
    setting: str
    dessert: str
    problem: str
    fix: str
    kid1: str = "Mina"
    kid2: str = "Jo"
    parent_type: str = "mother"
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
    "dessert": [("What is dessert?", "Dessert is the sweet food people eat after a meal. It can be cake, cookies, pudding, and many other treats.")],
    "bash": [("What is a bash?", "A bash is a lively party. People laugh, eat, and celebrate together.")],
    "careful": [("Why should you be careful with food at a party?", "Careful hands help keep food clean and safe. That way the treats stay nice for everyone.")],
    "problem": [("What does it mean to solve a problem?", "It means finding a good way to fix what is wrong. A smart solution can turn a hard moment into a better one.")],
    "moral": [("What is a moral in a story?", "A moral is the lesson the story wants to teach. It often helps us choose a kinder or safer way next time.")],
}

KNOWLEDGE_ORDER = ["dessert", "bash", "careful", "problem", "moral"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a funny, child-friendly story that includes the words "dessert" and "bash" and shows a small problem being solved.',
        f"Tell a comedy story about a dessert bash where {f['hero'].id} notices trouble, thinks fast, and fixes it with help from {f['helper'].id}.",
        f"Write a cautionary moral story for a little kid: a dessert bash goes wrong for a moment, then the children make a sensible choice and save the treats.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    dessert = f["dessert"]
    problem = f["problem"]
    fix = f["fix"]
    hero = f["hero"]
    helper = f["helper"]
    parent = f["parent"]
    qa = [
        ("What was the story about?", f"It was about a dessert bash where {hero.id} and {helper.id} tried to keep the treats safe. The party started cheerful and turned into a tiny problem that needed a quick fix."),
        ("What went wrong?", f"A {problem.label} problem appeared, and the {dessert.label} started to get {problem.risk}. That was the risky part, because the treats could have been ruined."),
        ("How did they fix it?", f"They used {fix.label} and solved the problem together. {helper.id} noticed what was needed, and {hero.id} carried out the plan before the bash got messier."),
        ("What moral did the story teach?", f"It taught that being careful and solving problems early keeps good things from turning into sad, sticky things. A little caution saved the dessert bash."),
    ]
    if f.get("resolved"):
        qa.append(("How did the story end?", f"It ended happily, with the {dessert.label} safe on the table and everyone laughing again. The bash stayed fun because they handled the trouble in time."))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    tags = {"dessert", "bash", "careful", "problem", "moral"}
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
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
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(setting="kitchen", dessert="cupcakes", problem="topple", fix="steady", kid1="Mina", kid2="Jo", parent_type="mother"),
    StoryParams(setting="backyard", dessert="cookies", problem="wind", fix="napkin", kid1="Tara", kid2="Bo", parent_type="father"),
    StoryParams(setting="kitchen", dessert="pudding", problem="crumbs", fix="tray", kid1="Nia", kid2="Leo", parent_type="mother"),
]


def explain_rejection(problem: Problem, dessert: Dessert) -> str:
    return f"(No story: this problem does not plausibly threaten the {dessert.label}, so the bash has no real cautionary turn.)"


def valid_fix(problem: Problem, fix: Fix) -> bool:
    return fix.sense >= SENSE_MIN and fixed_by(fix, problem)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.problem and args.fix:
        p, fx = PROBLEMS[args.problem], FIXES[args.fix]
        if not valid_fix(p, fx):
            raise StoryError(explain_rejection(p, DESSERTS[args.dessert] if args.dessert else next(iter(DESSERTS.values()))))
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.problem is None or c[1] == args.problem)
              and (args.dessert is None or c[2] == args.dessert)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, problem, dessert = rng.choice(sorted(combos))
    fix = args.fix or rng.choice(sorted(k for k, v in FIXES.items() if v.sense >= SENSE_MIN and fixed_by(v, PROBLEMS[problem])))
    return StoryParams(setting=setting, dessert=dessert, problem=problem, fix=fix)


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.dessert not in DESSERTS or params.problem not in PROBLEMS or params.fix not in FIXES:
        raise StoryError("Invalid params supplied.")
    if not valid_fix(PROBLEMS[params.problem], FIXES[params.fix]):
        raise StoryError(explain_rejection(PROBLEMS[params.problem], DESSERTS[params.dessert]))
    world = tell(SETTINGS[params.setting], DESSERTS[params.dessert], PROBLEMS[params.problem], FIXES[params.fix])
    return StorySample(params=params, story=world.render(), prompts=generation_prompts(world), story_qa=[QAItem(q, a) for q, a in story_qa(world)], world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)], world=world)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


ASP_RULES = r"""
problem(P) :- problem_id(P).
dessert(D) :- dessert_id(D).
hazard(P,D) :- bad_problem(P), fragile(D).
fixable(P,F) :- fix_id(F), sense(F,S), sense_min(M), S >= M.
valid(S,P,D) :- setting_id(S), problem_id(P), dessert_id(D), hazard(P,D), fixable(P,F).
resolved(P,F) :- power(F, Pow), severity(P, Sev), Pow >= Sev.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting_id", sid))
    for did, d in DESSERTS.items():
        lines.append(asp.fact("dessert_id", did))
        if d.fragile:
            lines.append(asp.fact("fragile", did))
    for pid, p in PROBLEMS.items():
        lines.append(asp.fact("problem_id", pid))
        if p.bad:
            lines.append(asp.fact("bad_problem", pid))
        lines.append(asp.fact("severity", pid, p.spread))
    for fid, f in FIXES.items():
        lines.append(asp.fact("fix_id", fid))
        lines.append(asp.fact("sense", fid, f.sense))
        lines.append(asp.fact("power", fid, f.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import io
    import contextlib

    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        rc = 1
        print("MISMATCH: ASP and Python valid_combos differ.")
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            sample = generate(CURATED[0])
            emit(sample, trace=False, qa=False)
    except Exception as e:
        print(f"MISMATCH: smoke test failed: {e}")
        return 1
    print("OK: ASP parity and smoke test passed.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Story world: a dessert bash with a comic problem, a fix, and a moral lesson.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--dessert", choices=DESSERTS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--fix", choices=FIXES)
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_valid_combos())
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            i += 1
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        if args.all:
            p = sample.params
            header = f"### {p.setting} / {p.dessert} / {p.problem} / {p.fix}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
