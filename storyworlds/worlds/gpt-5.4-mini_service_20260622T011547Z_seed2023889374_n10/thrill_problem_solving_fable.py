#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260622T011547Z_seed2023889374_n10/thrill_problem_solving_fable.py
==============================================================================================================

A small fable-style storyworld about a shared problem, careful thinking, and a
thrill that comes from solving things together. The world is concrete: animals
and objects have meters and memes, causes change state, and the prose is rendered
from the simulated outcome rather than from a frozen template.
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
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
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

    def pronoun(self, case: str = "subject") -> str:
        female = {"fox", "rabbit", "hen", "cat", "mouse"}
        male = {"wolf", "bear", "owl", "goat", "crow"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Setting:
    id: str
    place: str
    problem: str
    clue: str
    solution_need: str
    ending_image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Problem:
    id: str
    name: str
    cause: str
    risk: str
    fix: str
    solved_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    name: str
    action: str
    effect: str
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
class StoryParams:
    setting: str
    problem: str
    tool: str
    solver: str
    helper: str
    seed: Optional[int] = None


SETTINGS = {
    "brook": Setting(
        id="brook",
        place="the little brook",
        problem="the bridge had slipped apart",
        clue="the broken planks floated downstream",
        solution_need="something sturdy to make a crossing",
        ending_image="the brook was crossed by a neat little bridge",
        tags={"water", "bridge"},
    ),
    "orchard": Setting(
        id="orchard",
        place="the orchard path",
        problem="the apples kept rolling out of the basket",
        clue="one basket handle was torn",
        solution_need="something to hold the apples safely",
        ending_image="the basket sat snug and full under the trees",
        tags={"basket", "fruit"},
    ),
    "hill": Setting(
        id="hill",
        place="the windy hill",
        problem="the kite string kept tangling in the grass",
        clue="each gust made the knot tighter",
        solution_need="a careful way to untwist the string",
        ending_image="the kite rose clean and bright above the hill",
        tags={"kite", "wind"},
    ),
}

PROBLEMS = {
    "bridge": Problem(
        id="bridge",
        name="broken bridge",
        cause="the path had washed away after rain",
        risk="the animals could not cross the brook",
        fix="build a bridge from fallen sticks",
        solved_line="the sticks fit together into a safe crossing",
        tags={"bridge", "water"},
    ),
    "basket": Problem(
        id="basket",
        name="torn basket",
        cause="one handle had snapped on the long walk home",
        risk="the apples would spill into the grass",
        fix="line the basket with broad leaves and tie it with vine",
        solved_line="the leaves held the apples in a soft green cradle",
        tags={"basket", "fruit"},
    ),
    "knot": Problem(
        id="knot",
        name="tight knot",
        cause="the string had wrapped around a thorny tuft of grass",
        risk="the kite could not climb while the knot stayed hard",
        fix="use a smooth twig to lift the loops apart",
        solved_line="the twig loosened the knot and set the string free",
        tags={"kite", "wind"},
    ),
}

TOOLS = {
    "sticks": Tool("sticks", "fallen sticks", "gather", "make a bridge frame", tags={"bridge"}),
    "leaves": Tool("leaves", "broad leaves", "line", "cushion the fruit", tags={"basket"}),
    "twig": Tool("twig", "smooth twig", "lift", "untwist the string", tags={"kite"}),
}

NAMES = ["Milo", "Fern", "Pip", "Luna", "Bram", "Tansy", "Robin", "Moss"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for pid, problem in PROBLEMS.items():
            if pid not in setting.tags:
                continue
            for tid, tool in TOOLS.items():
                if pid in tool.tags:
                    combos.append((sid, pid, tid))
    return combos


def reasonableness_gate(problem: Problem, tool: Tool) -> bool:
    return problem.id in tool.tags


def solve_problem(world: World, setting: Setting, problem: Problem, tool: Tool) -> None:
    world.get("problem").meters["trouble"] = 1.0
    world.get("problem").memes["worry"] = 1.0
    world.get("tool").meters["useful"] = 1.0
    world.get("solver").memes["hope"] = 1.0
    world.get("helper").memes["care"] = 1.0
    world.get("helper").memes["thrill"] = 0.0
    world.facts["solved"] = False

    world.say(
        f"At {setting.place}, {world.get('solver').id} and {world.get('helper').id} "
        f"found a problem: {problem.name}. {setting.clue.capitalize()}."
    )
    world.say(
        f'"We need to {problem.fix}," said {world.get("helper").id}, who liked to notice '
        f"what each thing could do."
    )
    world.say(
        f"{world.get('solver').id} looked at the {tool.name} and tried a careful plan."
    )

    world.get("problem").meters["trouble"] = 0.0
    world.get("problem").memes["worry"] = 0.0
    world.get("solver").memes["relief"] = 1.0
    world.get("helper").memes["thrill"] = 1.0
    world.facts["solved"] = True

    world.say(
        f"They used the {tool.name} to {tool.action} and {tool.effect}. "
        f"{problem.solved_line.capitalize()}."
    )
    world.say(
        f"In the end, {setting.ending_image}, and {world.get('helper').id} felt a small "
        f"thrill from solving the trouble with a clear head."
    )


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    p = f["problem"]
    s = f["setting"]
    t = f["tool"]
    return [
        QAItem(
            question=f"What problem did {f['solver'].id} and {f['helper'].id} face at {s.place}?",
            answer=f"They faced {p.name}. It mattered because {p.risk}.",
        ),
        QAItem(
            question=f"How did they solve the {p.name}?",
            answer=f"They used the {t.name} to {t.action} and {t.effect}. That turned the problem into a safe and useful result.",
        ),
        QAItem(
            question=f"How did the helper feel at the end?",
            answer=f"The helper felt a small thrill because the problem was solved by thinking carefully. The ending image shows the change clearly.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    p = world.facts["problem"]
    return [
        QAItem(
            question="What is a problem?",
            answer="A problem is something that is stuck, broken, or in the way. People and animals can solve problems by noticing clues and choosing a good plan.",
        ),
        QAItem(
            question="Why do helpers think before acting?",
            answer="Helpers think before acting so they can pick a safe and useful answer. Careful thinking can turn trouble into a fix.",
        ),
        QAItem(
            question=f"Why is a {p.name} tricky?",
            answer=f"A {p.name} is tricky because it can stop progress until someone finds the right fix. Once the right fix is used, the trouble can disappear.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a fable about {f['solver'].id} and {f['helper'].id} solving {f['problem'].name} with a clever tool.",
        f"Tell a short story that includes the word thrill and ends with a useful solution at {f['setting'].place}.",
        f"Write a child-friendly fable where careful thinking solves a problem instead of panic.",
    ]


def format_qa(sample: StorySample) -> str:
    parts = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        parts.append(f"{i}. {p}")
    parts.append("")
    parts.append("== story qa ==")
    for q in sample.story_qa:
        parts.append(f"Q: {q.question}")
        parts.append(f"A: {q.answer}")
    parts.append("")
    parts.append("== world qa ==")
    for q in sample.world_qa:
        parts.append(f"Q: {q.question}")
        parts.append(f"A: {q.answer}")
    return "\n".join(parts)


def tell(setting: Setting, problem: Problem, tool: Tool, solver: Entity, helper: Entity) -> World:
    world = World()
    world.add(solver)
    world.add(helper)
    world.add(Entity(id="problem", kind="thing", type="problem", label=problem.name))
    world.add(Entity(id="tool", kind="thing", type="tool", label=tool.name))
    world.facts.update(setting=setting, problem=problem, tool=tool, solver=solver, helper=helper)
    solve_problem(world, setting, problem, tool)
    return world


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny fable about problem solving and thrill.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
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
              and (args.tool is None or c[2] == args.tool)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    sid, pid, tid = rng.choice(sorted(combos))
    return StoryParams(
        setting=sid,
        problem=pid,
        tool=tid,
        solver=rng.choice(NAMES),
        helper=rng.choice([n for n in NAMES if n != sid]),
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.problem not in PROBLEMS or params.tool not in TOOLS:
        raise StoryError("Unknown StoryParams choice.")
    setting = SETTINGS[params.setting]
    problem = PROBLEMS[params.problem]
    tool = TOOLS[params.tool]
    if not reasonableness_gate(problem, tool):
        raise StoryError("The chosen tool does not really solve that problem.")
    solver = Entity(id=params.solver, kind="character", type="fox", role="solver")
    helper = Entity(id=params.helper, kind="character", type="owl", role="helper")
    world = tell(setting, problem, tool, solver, helper)
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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.kind:7}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(setting="brook", problem="bridge", tool="sticks", solver="Milo", helper="Fern"),
    StoryParams(setting="orchard", problem="basket", tool="leaves", solver="Pip", helper="Luna"),
    StoryParams(setting="hill", problem="knot", tool="twig", solver="Robin", helper="Moss"),
]


ASP_RULES = r"""
valid(S,P,T) :- setting(S), problem(P), tool(T), can_pair(S,P), solves(T,P).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for pid in PROBLEMS:
        lines.append(asp.fact("problem", pid))
    for tid in TOOLS:
        lines.append(asp.fact("tool", tid))
    for sid, setting in SETTINGS.items():
        for pid in setting.tags:
            lines.append(asp.fact("can_pair", sid, pid))
    for tid, tool in TOOLS.items():
        for pid in tool.tags:
            lines.append(asp.fact("solves", tid, pid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import storyworlds.asp as asp
    ok = set(asp_valid_combos()) == set(valid_combos())
    if not ok:
        print("MISMATCH in ASP parity.")
        return 1
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, problem=None, tool=None), random.Random(7)))
        _ = sample.story
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    print("OK: ASP parity and generation smoke test passed.")
    return 0


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for row in asp_valid_combos():
            print(row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            s = generate(params)
            if s.story not in seen:
                seen.add(s.story)
                samples.append(s)
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
