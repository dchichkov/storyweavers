#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/terrific_opa_dare_children_s_museum_problem.py
=================================================================================================

A small standalone story world for a detective-style children's museum mystery.

Premise:
- A child and their opa visit a children's museum.
- Something important goes missing or gets blocked in a hands-on exhibit.
- The child notices clues, tests ideas, and solves the problem.

World shape:
- Physical state uses meters; emotional state uses memes.
- The story is built from a causal simulation, not from a fixed paragraph.
- The tone stays child-friendly, concrete, and gently detective-like.

Seed words used in the domain:
- terrific
- opa
- dare

Narrative instruments:
- Detective Story style
- Problem Solving
- children's museum setting
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    found_by: Optional[str] = None
    hidden: bool = False
    locked: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "mom", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "dad", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Setting:
    place: str = "the children's museum"
    affords: set[str] = field(default_factory=set)


@dataclass
class Problem:
    id: str
    label: str
    phrase: str
    clue: str
    solved_by: str
    difficulty: str
    keyword: str


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    helps_with: str
    method: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.trace: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)
            self.trace.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def copy(self) -> "World":
        import copy as _copy

        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "museum": Setting(place="the children's museum", affords={"blocks", "magnets", "tracks"}),
}

PROBLEMS = {
    "stuck-door": Problem(
        id="stuck-door",
        label="stuck door",
        phrase="a little door in the puzzle room that would not open",
        clue="the key-shaped piece was not in the slot",
        solved_by="find the hidden key card",
        difficulty="small",
        keyword="key",
    ),
    "missing-piece": Problem(
        id="missing-piece",
        label="missing piece",
        phrase="a bright puzzle piece that was missing from the floor map",
        clue="the map had one empty shape",
        solved_by="look behind the display table",
        difficulty="small",
        keyword="piece",
    ),
    "jammed-train": Problem(
        id="jammed-train",
        label="jammed train",
        phrase="a tiny museum train that would not roll on the track",
        clue="one wheel was caught on a bump",
        solved_by="push the bump aside",
        difficulty="small",
        keyword="track",
    ),
}

TOOLS = {
    "magnifying-glass": Tool(
        id="magnifying-glass",
        label="magnifying glass",
        phrase="a small magnifying glass",
        helps_with="clues",
        method="look closely",
    ),
    "ramp-card": Tool(
        id="ramp-card",
        label="ramp card",
        phrase="a flat ramp card",
        helps_with="tracks",
        method="slip it under the wheel",
    ),
    "flashlight": Tool(
        id="flashlight",
        label="flashlight",
        phrase="a tiny flashlight",
        helps_with="hidden spaces",
        method="shine it under and behind things",
    ),
}

CHILD_NAMES = ["Mia", "Noah", "Luna", "Ari", "Zoe", "Ben", "Ivy", "Max"]
OPA_NAMES = ["Opa", "Opa Ben", "Opa Theo", "Opa Sam"]

CURATED = [
    ("museum", "stuck-door", "magnifying-glass"),
    ("museum", "missing-piece", "flashlight"),
    ("museum", "jammed-train", "ramp-card"),
]


# ---------------------------------------------------------------------------
# Story params
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    problem: str
    tool: str
    child_name: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A problem is solvable if a tool helps the problem's hidden clue or mechanism.
solvable(P, T) :- problem(P), tool(T), helps(T, C), needs(P, C).

valid_story(Place, P, T) :- setting(Place), affords(Place, P), solvable(P, T).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for pid, p in PROBLEMS.items():
        lines.append(asp.fact("problem", pid))
        lines.append(asp.fact("needs", pid, p.keyword))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        lines.append(asp.fact("helps", tid, t.helps_with))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for pid, prob in PROBLEMS.items():
            if pid not in setting.affords and prob.keyword not in setting.affords:
                # museum affords activities, not problems; keep the gate simple and explicit.
                pass
            for tid, tool in TOOLS.items():
                if tool.helps_with == prob.keyword or tool.helps_with in {prob.keyword, "clues", "hidden spaces"}:
                    combos.append((place, pid, tid))
    return combos


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Simulation
# ---------------------------------------------------------------------------

def choose_problem_tool(problem: Problem, tool: Tool) -> bool:
    return tool.helps_with in {problem.keyword, "clues", "hidden spaces"} or problem.keyword in tool.phrase


def introduce(world: World, child: Entity, opa: Entity) -> None:
    world.say(
        f"{child.id} was a terrific little detective who loved visiting the children's museum with {opa.label}."
    )


def setup(world: World, child: Entity, opa: Entity, problem: Problem) -> None:
    world.say(
        f"One afternoon, {child.id} and {opa.label} reached {world.setting.place}, where {problem.phrase} was waiting like a mystery."
    )
    child.memes["curiosity"] = child.memes.get("curiosity", 0.0) + 1
    opa.memes["pride"] = opa.memes.get("pride", 0.0) + 1


def notice_clue(world: World, child: Entity, problem: Problem) -> None:
    child.memes["focus"] = child.memes.get("focus", 0.0) + 1
    world.say(
        f"{child.id} saw a clue: {problem.clue}. That made the case feel less puzzling."
    )


def ask_opa(world: World, child: Entity, opa: Entity) -> None:
    opa.memes["helpful"] = opa.memes.get("helpful", 0.0) + 1
    world.say(
        f'"Maybe we should take a close look," said {opa.label}. "A careful eye can spot a tiny answer."'
    )


def test_tool(world: World, child: Entity, tool: Tool, problem: Problem) -> bool:
    if not choose_problem_tool(problem, tool):
        return False
    child.meters["trying"] = child.meters.get("trying", 0.0) + 1
    world.say(
        f"{child.id} used {tool.phrase} to {tool.method}. It seemed {tool.label} was a terrific choice."
    )
    return True


def solve_problem(world: World, child: Entity, opa: Entity, problem: Problem, tool: Tool) -> None:
    child.memes["joy"] = child.memes.get("joy", 0.0) + 1
    opa.memes["joy"] = opa.memes.get("joy", 0.0) + 1
    child.memes["confidence"] = child.memes.get("confidence", 0.0) + 1
    world.facts["solved"] = True
    world.say(
        f"At last, {child.id} found the answer. They used {tool.label} to {problem.solved_by}, and the mystery opened right up."
    )
    world.say(
        f"The door worked, the piece fit, or the train rolled again, and {opa.label} smiled at the clever fix."
    )


def tell(setting: Setting, problem: Problem, tool: Tool, child_name: str) -> World:
    world = World(setting)
    child = world.add(Entity(id=child_name, kind="character", type="child"))
    opa = world.add(Entity(id="Opa", kind="character", type="opa", label="opa"))

    world.facts.update(problem=problem, tool=tool, child=child, opa=opa, setting=setting)

    introduce(world, child, opa)
    setup(world, child, opa, problem)
    world.para()
    notice_clue(world, child, problem)
    ask_opa(world, child, opa)
    test_tool(world, child, tool, problem)
    world.para()
    solve_problem(world, child, opa, problem, tool)

    world.facts["child"] = child
    world.facts["opa"] = opa
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    problem = f["problem"]
    tool = f["tool"]
    return [
        f'Write a short detective story for a child in a children\'s museum using the word "{tool.label}".',
        f"Tell a story where {child.id} and opa solve a museum mystery with a calm clue and a clever tool.",
        f"Write a problem-solving adventure in the children's museum with a terrific ending and the word 'opa'.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    opa = f["opa"]
    problem = f["problem"]
    tool = f["tool"]
    return [
        QAItem(
            question=f"Who was the little detective in the story?",
            answer=f"The little detective was {child.id}, and {opa.label} came along to help look for clues.",
        ),
        QAItem(
            question=f"What mystery did they have to solve at the children's museum?",
            answer=f"They had to solve {problem.phrase}. The clue was {problem.clue}.",
        ),
        QAItem(
            question=f"What tool helped {child.id} finish the case?",
            answer=f"{tool.phrase} helped because it was good for {tool.helps_with}, so it could solve the problem.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with the mystery fixed, {child.id} feeling proud, and {opa.label} smiling at the terrific solution.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a detective?",
            answer="A detective is a person who looks for clues and tries to solve a mystery.",
        ),
        QAItem(
            question="What is a clue?",
            answer="A clue is a small piece of information that helps you figure something out.",
        ),
        QAItem(
            question="What is a museum?",
            answer="A museum is a place where people go to see interesting things and learn by looking and doing.",
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


# ---------------------------------------------------------------------------
# Trace / helpers
# ---------------------------------------------------------------------------

def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    if world.trace:
        lines.append("  events:")
        for t in world.trace:
            lines.append(f"    - {t}")
    return "\n".join(lines)


def explain_rejection(problem: Problem, tool: Tool) -> str:
    return (
        f"(No story: the tool '{tool.label}' does not reasonably help solve "
        f"'{problem.label}' in this detective world.)"
    )


# ---------------------------------------------------------------------------
# Standard interface
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Detective-style children's museum story world with problem solving."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--name")
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
    if args.problem and args.tool:
        if not choose_problem_tool(PROBLEMS[args.problem], TOOLS[args.tool]):
            raise StoryError(explain_rejection(PROBLEMS[args.problem], TOOLS[args.tool]))

    combos = [
        c for c in valid_combos()
        if (args.place is None or c[0] == args.place)
        and (args.problem is None or c[1] == args.problem)
        and (args.tool is None or c[2] == args.tool)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, problem_id, tool_id = rng.choice(sorted(combos))
    child_name = args.name or rng.choice(CHILD_NAMES)
    return StoryParams(place=place, problem=problem_id, tool=tool_id, child_name=child_name)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], PROBLEMS[params.problem], TOOLS[params.tool], params.child_name)
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
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, problem, tool) combos:\n")
        for place, prob, tool in combos:
            print(f"  {place:10} {prob:14} {tool}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        for i, (place, problem, tool) in enumerate(CURATED):
            p = StoryParams(place=place, problem=problem, tool=tool, child_name=CHILD_NAMES[i % len(CHILD_NAMES)], seed=base_seed + i)
            samples.append(generate(p))
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
