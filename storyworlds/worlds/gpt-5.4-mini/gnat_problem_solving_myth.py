#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/gnat_problem_solving_myth.py
=============================================================

A standalone story world about a small mythic problem: a gnat keeps ruining a
simple task, so the characters use clever, gentle problem solving to restore the
day. The style leans mythic -- a river, a hut, a moonlit helper, a tiny creature
with an outsized consequence -- while staying child-facing and state-driven.

This script follows the Storyweavers storyworld contract:
- stdlib-only
- imports storyworlds/results.py eagerly
- defines StoryParams, build_parser, resolve_params, generate, emit, main
- supports default run, -n, --all, --seed, --trace, --qa, --json, --asp,
  --verify, and --show-asp
- includes a Python reasonableness gate plus an inline ASP twin
- generates three QA sets from world state
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
    traits: list[str] = field(default_factory=list)
    role: str = ""
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict = field(default_factory=dict)
    tiny: bool = False
    noisy: bool = False
    fragrant: bool = False
    helpful: bool = False

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "goddess", "queen", "priestess"}
        male = {"boy", "father", "dad", "man", "god", "king", "priest"}
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
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

@dataclass
class MythFrame:
    name: str
    place: str
    opening: str
    task: str
    trouble: str
    helper_name: str
    helper_gift: str
    ending_image: str
    tone: str

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
    meddling: str
    damage: str
    target: str
    tiny: bool = True
    noisy: bool = True
    sting: bool = False
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
class Tool:
    id: str
    label: str
    phrase: str
    use: str
    strong_against: set[str]
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


def _r_annoy(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.meters["annoying"] < THRESHOLD:
            continue
        sig = ("annoy", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        if "hero" in world.entities:
            world.get("hero").memes["frustration"] += 1
        out.append("__annoy__")
    return out


def _r_wisdom(world: World) -> list[str]:
    out: list[str] = []
    if "hero" not in world.entities or "helper" not in world.entities:
        return out
    hero = world.get("hero")
    helper = world.get("helper")
    if hero.memes["frustration"] < THRESHOLD or helper.memes["calm"] < THRESHOLD:
        return out
    sig = ("wisdom",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["hope"] += 1
    helper.memes["care"] += 1
    out.append("__wisdom__")
    return out


CAUSAL_RULES = [Rule("annoy", "physical", _r_annoy), Rule("wisdom", "social", _r_wisdom)]


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


def problem_at_risk(problem: Problem, task: str) -> bool:
    return problem.target == task


def sensible_tools() -> list[Tool]:
    return [t for t in TOOLS.values() if t.label and t.id != "swat"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for myth in MYTHS:
        for pid, prob in PROBLEMS.items():
            for tid, tool in TOOLS.items():
                if problem_at_risk(prob, myth.task) and tool.id in prob.tags:
                    combos.append((myth.name, pid, tid))
    return combos


def tool_power(tool: Tool, problem: Problem) -> int:
    return 2 if problem.id in tool.strong_against else 0


def outcome_of(params: "StoryParams") -> str:
    if params.tool not in TOOLS:
        return "?"
    tool = TOOLS[params.tool]
    prob = PROBLEMS[params.problem]
    if tool.id == "swat":
        return "stung"
    return "solved" if tool_power(tool, prob) >= 1 else "stung"


def _solve_problem(world: World, hero: Entity, helper: Entity, problem: Problem, tool: Tool) -> None:
    problem_ent = world.get("problem")
    problem_ent.meters["annoying"] += 1
    hero.memes["frustration"] += 1
    propagate(world, narrate=False)
    if tool.id == "swat":
        world.say(f"{hero.id} swung a hand, but the {problem.label} only darted away laughing.")
        hero.memes["frustration"] += 1
        return
    if tool_power(tool, problem) >= 1:
        problem_ent.meters["annoying"] = 0
        hero.memes["frustration"] = 0
        helper.memes["calm"] += 1
        world.say(f"{helper.id} lifted {tool.phrase} and used {tool.use}.")
        world.say(f"The {problem.label} stopped its buzzing, and the trouble around the task grew quiet.")
    else:
        world.say(f"{helper.id} tried {tool.phrase}, but it was not the right answer for the {problem.label}.")
        world.say(f"The little trouble stayed in the air, and the task could not finish.")


def myth_opening(world: World, frame: MythFrame, hero: Entity, helper: Entity, problem: Problem) -> None:
    world.say(frame.opening)
    world.say(f"{hero.id} and {helper.id} were working on {frame.task} when {problem.label} came humming by.")
    world.say(f"It had one small habit: {problem.meddling}.")


def warn_and_choose(world: World, hero: Entity, helper: Entity, problem: Problem, tool: Tool) -> None:
    helper.memes["calm"] += 1
    pred = predict(world, tool.id)
    world.facts["predicted"] = pred
    world.say(f"{helper.id} noticed the trouble could grow if nobody solved it soon.")
    world.say(f'"{hero.id}, we should use {tool.label}," {helper.id} said, because it can {tool.use}.')
    if hero.memes["frustration"] >= THRESHOLD:
        world.say(f"{hero.id} frowned, but listened.")
    if pred["solved"]:
        world.say(f"The plan felt wise before it even began.")


def predict(world: World, tool_id: str) -> dict:
    sim = world.copy()
    hero = sim.get("hero")
    helper = sim.get("helper")
    problem = sim.get("problem_cfg")
    tool = TOOLS[tool_id]
    _solve_problem(sim, hero, helper, problem, tool)
    return {"solved": sim.get("problem").meters["annoying"] < THRESHOLD}


def ending(world: World, frame: MythFrame, hero: Entity, helper: Entity) -> None:
    hero.memes["joy"] += 1
    helper.memes["joy"] += 1
    world.say(frame.ending_image)
    world.say(f"{hero.id} smiled at {helper.id}, and the day felt bright again.")


def tell(frame: MythFrame, problem: Problem, tool: Tool, hero_name: str = "Mira", hero_type: str = "girl",
         helper_name: str = "Old Sage", helper_type: str = "man") -> World:
    world = World()
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, role="hero"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_type, role="helper"))
    world.add(Entity(id="problem", type="problem", label=problem.label, tiny=problem.tiny, noisy=problem.noisy, attrs={"problem_id": problem.id}))
    world.add(Entity(id="problem_cfg", type="problem", label=problem.label, tiny=problem.tiny, noisy=problem.noisy, attrs={"problem_id": problem.id}))
    myth_opening(world, frame, hero, helper, problem)
    world.para()
    warn_and_choose(world, hero, helper, problem, tool)
    _solve_problem(world, hero, helper, problem, tool)
    world.para()
    ending(world, frame, hero, helper)
    world.facts.update(hero=hero, helper=helper, frame=frame, problem=problem, problem_cfg=problem, tool=tool,
                       outcome=outcome_of(StoryParams(frame.name, problem.id, tool.id, hero_name, hero_type, helper_name, helper_type)),
                       solved=world.get("problem").meters["annoying"] < THRESHOLD)
    return world


MYTHS = [
    MythFrame(
        name="river-hut", place="a river hut",
        opening="In the old days, beside a silver river, there stood a quiet hut with a reed roof.",
        task="sorting seeds for the spring basket",
        trouble="the baskets had to be counted before sunset",
        helper_name="Old Sage", helper_gift="a reed fan",
        ending_image="At last the baskets sat in a neat moonlit line, each one still and ready.",
        tone="gentle",
    ),
    MythFrame(
        name="moon-garden", place="a moon garden",
        opening="Long ago, under the pale moon, a little garden listened to the night insects.",
        task="watering the moonflowers",
        trouble="the flowers needed peace to open",
        helper_name="Moon Aunt", helper_gift="a silver cup",
        ending_image="The moonflowers opened wide, and their pale petals shone like bowls of milk.",
        tone="wise",
    ),
    MythFrame(
        name="hill-shrine", place="a hill shrine",
        opening="On a high hill, where the wind taught the grass to bow, a tiny shrine watched the dawn.",
        task="offering honey to the stones",
        trouble="the bowl had to stay steady",
        helper_name="River Uncle", helper_gift="a smooth stone",
        ending_image="The honey bowl rested safely at last, glowing like amber in the sun.",
        tone="patient",
    ),
]

PROBLEMS = {
    "gnat": Problem("gnat", "gnat", "buzzing into faces", "stopped the work", target="seeds", tiny=True, noisy=True, sting=False, tags={"fan", "water", "stone"}),
    "midge": Problem("midge", "midge", "looping around the bowl", "made the task hard", target="flowers", tiny=True, noisy=True, sting=False, tags={"fan", "water", "stone"}),
    "mosquito": Problem("mosquito", "mosquito", "singing near the ear", "broke the calm", target="honey", tiny=True, noisy=True, sting=True, tags={"fan", "water", "stone"}),
}

TOOLS = {
    "fan": Tool("fan", "a reed fan", "a reed fan", "wave cool air", {"gnat", "midge", "mosquito"}),
    "water": Tool("water", "a silver cup of water", "a silver cup of water", "gently rinse the air and settle the buzzing", {"gnat", "midge"}),
    "stone": Tool("stone", "a smooth river stone", "a smooth river stone", "hold the bowl steady and make a calm place to work", {"mosquito"}),
    "swat": Tool("swat", "a bare hand", "a bare hand", "shoo the insect away by force", set()),
}

NAMES = ["Mira", "Tala", "Nia", "Sera", "Kora", "Anya", "Leah", "Pia"]
HELPERS = ["Old Sage", "Moon Aunt", "River Uncle", "Sky Mother"]
TRAITS = ["patient", "clever", "gentle", "steady"]


@dataclass
@dataclass
class StoryParams:
    frame: str
    problem: str
    tool: str
    hero_name: str
    hero_type: str
    helper_name: str
    helper_type: str
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


KNOWLEDGE = {
    "gnat": [("What is a gnat?", "A gnat is a very small flying insect. It can buzz around people and be annoying, especially near food or faces.")],
    "midge": [("What is a midge?", "A midge is a tiny flying bug like a gnat. It can crowd around water, light, or flowers and make a quiet job hard.")],
    "mosquito": [("What is a mosquito?", "A mosquito is a flying insect that can buzz near ears and sometimes bite. People try to keep mosquitoes away so they can stay comfortable.")],
    "fan": [("What does a fan do?", "A fan moves air. A strong, gentle fan can help push tiny flying bugs away without hurting them.")],
    "water": [("Why might water help with buzzing insects?", "A little water can calm dust and make the air less dry and dusty, which can help a tiny insect leave a place alone.")],
    "stone": [("Why use a stone in a careful task?", "A stone is heavy and steady. It can hold something in place so a small problem does not knock it over.")],
    "problem": [("What is problem solving?", "Problem solving means noticing what is wrong, thinking of a good plan, and trying a smart step to fix it.")],
    "myth": [("What is a myth?", "A myth is an old story about people, nature, or gods that explains a wise idea or a special event.")],
}
KNOWLEDGE_ORDER = ["problem", "myth", "gnat", "midge", "mosquito", "fan", "water", "stone"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a mythic story for a child that includes the word "{f["problem"].label}".',
        f"Tell a gentle myth where {f['hero'].id} and {f['helper'].id} solve a small buzzing problem without getting angry.",
        f"Write a story in a myth style about problem solving, where a tiny insect interrupts an important task and a wise helper chooses a calm answer.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, helper, problem, tool = f["hero"], f["helper"], f["problem"], f["tool"]
    qs = [
        QAItem(
            question="Who was the story about?",
            answer=f"It was about {hero.id} and {helper.id}. They were trying to finish a quiet task when the {problem.label} started buzzing around.",
        ),
        QAItem(
            question="What problem did they have?",
            answer=f"A {problem.label} kept buzzing into faces and making the work hard to finish. The problem was small, but it still needed a smart plan.",
        ),
        QAItem(
            question="How did they solve it?",
            answer=f"They used {tool.label} and chose a calm way instead of swatting. That helped the buzzing stop so the task could be finished.",
        ),
    ]
    if f.get("solved"):
        qs.append(QAItem(
            question="How did the story end?",
            answer=f"It ended happily, with the work finished and the air calm again. The tiny trouble was gone, and the ending image showed everything neat and still.",
        ))
    else:
        qs.append(QAItem(
            question="How did the story end?",
            answer=f"It ended with the problem still bothering them, because the first plan was not strong enough. They had to keep looking for a better answer.",
        ))
    return qs


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    tags = set(f["problem"].tags) | set(f["tool"].tags) | {"problem", "myth"}
    out: list[QAItem] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags and tag in KNOWLEDGE:
            q, a = KNOWLEDGE[tag][0]
            out.append(QAItem(q, a))
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
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


def explain_rejection(problem: Problem, tool: Tool) -> str:
    return f"(No story: the {tool.label} is not a plausible answer for the {problem.label}. Pick a tool that really helps.)"


ASP_RULES = r"""
problem_at_risk(P, T) :- problem(P), task(T), target(P, T).
sensible(T) :- tool(T), T != swat.
solved(P, T) :- problem(P), tool(T), strong_against(T, P).
outcome(solved) :- solved(P, T).
outcome(stung) :- tool(swat).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for fid, frame in enumerate(MYTHS):
        lines.append(asp.fact("myth", frame.name))
        lines.append(asp.fact("task", frame.task))
    for pid, prob in PROBLEMS.items():
        lines.append(asp.fact("problem", pid))
        lines.append(asp.fact("target", pid, prob.target))
    for tid, tool in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        for p in sorted(tool.strong_against):
            lines.append(asp.fact("strong_against", tid, p))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show problem_at_risk/2."))
    return sorted(set(asp.atoms(model, "problem_at_risk")))


def asp_outcome(params: StoryParams) -> str:
    return outcome_of(params)


def asp_verify() -> int:
    rc = 0
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if clingo_set == python_set:
        print(f"OK: gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in the gate:")
        print("  only in clingo:", sorted(clingo_set - python_set))
        print("  only in python:", sorted(python_set - clingo_set))
    sample = generate(CURATED[0])
    if not sample.story.strip():
        rc = 1
        print("MISMATCH: smoke test failed to render story.")
    else:
        print("OK: smoke test generated a story.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic problem-solving storyworld about a gnat and a wise fix.")
    ap.add_argument("--myth", choices=[m.name for m in MYTHS])
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--hero", choices=NAMES)
    ap.add_argument("--helper", choices=HELPERS)
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
              if (args.myth is None or c[0] == args.myth)
              and (args.problem is None or c[1] == args.problem)
              and (args.tool is None or c[2] == args.tool)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    myth, problem, tool = rng.choice(sorted(combos))
    hero = args.hero or rng.choice(NAMES)
    helper = args.helper or rng.choice([h for h in HELPERS if h != hero])
    return StoryParams(myth, problem, tool, hero, "girl", helper, "man")


def generate(params: StoryParams) -> StorySample:
    frame = next(m for m in MYTHS if m.name == params.frame)
    world = World()
    hero = world.add(Entity(id=params.hero_name, kind="character", type=params.hero_type, role="hero"))
    helper = world.add(Entity(id=params.helper_name, kind="character", type=params.helper_type, role="helper"))
    problem = PROBLEMS[params.problem]
    tool = TOOLS[params.tool]
    world.add(Entity(id="problem", type="problem", label=problem.label, tiny=True, noisy=True))
    world.facts["problem_cfg"] = problem
    world.facts["frame"] = frame
    world.facts["hero"] = hero
    world.facts["helper"] = helper
    world.facts["problem"] = problem
    world.facts["tool"] = tool
    myth_opening(world, frame, hero, helper, problem)
    world.para()
    warn_and_choose(world, hero, helper, problem, tool)
    _solve_problem(world, hero, helper, problem, tool)
    world.para()
    ending(world, frame, hero, helper)
    world.facts["solved"] = world.get("problem").meters["annoying"] < THRESHOLD
    world.facts["outcome"] = outcome_of(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


CURATED = [
    StoryParams("river-hut", "gnat", "fan", "Mira", "girl", "Old Sage", "man"),
    StoryParams("moon-garden", "midge", "water", "Tala", "girl", "Moon Aunt", "woman"),
    StoryParams("hill-shrine", "mosquito", "stone", "Nia", "girl", "River Uncle", "man"),
]


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
        print(asp_program("", "#show problem_at_risk/2.\n#show sensible/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos.")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
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
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
