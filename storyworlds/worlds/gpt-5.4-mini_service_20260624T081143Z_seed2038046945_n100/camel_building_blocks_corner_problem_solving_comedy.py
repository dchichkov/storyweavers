#!/usr/bin/env python3
"""
Camel Building Blocks Corner: a small comedy problem-solving storyworld.
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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    props: dict[str, str] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type == "camel":
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        if self.type in {"child", "girl", "boy"}:
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def name_or_label(self) -> str:
        return self.label or self.id


@dataclass
class Place:
    id: str
    label: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Problem:
    id: str
    label: str
    premise: str
    hint: str
    mess: str
    risk: str
    fix_kind: str
    fix_label: str
    fix_action: str
    solution: str
    punchline: str
    affects: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    helps: set[str]
    covers: set[str]
    action: str
    tail: str


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.trace: list[str] = []

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
        import copy as _copy
        w = World(self.place)
        w.entities = _copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

PLACES = {
    "corner": Place(id="corner", label="building blocks corner", affords={"build", "sort", "stack"}),
}

PROBLEMS = {
    "tippy_tower": Problem(
        id="tippy_tower",
        label="a wobbly tower",
        premise="the blocks keep leaning like a sleepy giraffe",
        hint="the bottom block is too small",
        mess="tumble",
        risk="falling blocks",
        fix_kind="wide_base",
        fix_label="wide flat blocks",
        fix_action="make a wider base",
        solution="the tower stands up straighter",
        punchline="the camel gives it a proud nod and one block stays put for once",
        affects={"stack"},
    ),
    "missing_red": Problem(
        id="missing_red",
        label="the red block pile",
        premise="the red blocks are hidden under a mountain of blue ones",
        hint="the wrong blocks got piled on top",
        mess="search",
        risk="can’t reach the red blocks",
        fix_kind="sorting_tray",
        fix_label="a sorting tray",
        fix_action="sort the blocks by color",
        solution="the red blocks pop back into view",
        punchline="the camel finds the red block wearing a very important grin",
        affects={"sort"},
    ),
    "stuck_bridge": Problem(
        id="stuck_bridge",
        label="a bridge that keeps getting stuck",
        premise="two long pieces will not line up and keep bonking noses",
        hint="the blocks are too far apart",
        mess="bonk",
        risk="a bridge that will not connect",
        fix_kind="helper_piece",
        fix_label="a tiny connector block",
        fix_action="add a tiny connector block",
        solution="the pieces finally meet in the middle",
        punchline="the camel says it was only a little dramatic for a bridge",
        affects={"build"},
    ),
}

TOOLS = {
    "wide_base": Tool("wide_base", "wide flat blocks", {"stack"}, {"base"}, "make a wider base", "Soon the top got a steadier seat."),
    "sorting_tray": Tool("sorting_tray", "a sorting tray", {"sort"}, {"sorted"}, "sort the blocks by color", "After that, the colors stopped hiding from one another."),
    "helper_piece": Tool("helper_piece", "a tiny connector block", {"build"}, {"join"}, "add a tiny connector block", "After that, the pieces touched noses and stayed there."),
}

CAMEL_NAMES = ["Coco", "Milo", "Tari", "Baba", "Nori", "Lulu"]
COMPANIONS = ["child", "friend", "helper"]
COMEDY_BEATS = [
    "It looked serious for one second, which was already a bit silly.",
    "The camel blinked as if the blocks had told a joke only it understood.",
    "Even the dust seemed to scoot closer to watch.",
]


@dataclass
class StoryParams:
    place: str
    problem: str
    name: str
    companion: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# ASP twin and Python reasonableness gate
# ---------------------------------------------------------------------------

ASP_RULES = r"""
place(corner).
problem(tippy_tower). problem(missing_red). problem(stuck_bridge).

solvable(P) :- problem(P), has_tool(P).
has_tool(tippy_tower) :- tool(wide_base).
has_tool(missing_red) :- tool(sorting_tray).
has_tool(stuck_bridge) :- tool(helper_piece).

show_story(P) :- place(corner), solvable(P).
#show show_story/1.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = [asp.fact("place", "corner")]
    for pid in PROBLEMS:
        lines.append(asp.fact("problem", pid))
    for tid in TOOLS:
        lines.append(asp.fact("tool", tid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def python_reasonable(problem: Problem) -> bool:
    return problem.id in PROBLEMS and problem.fix_kind in TOOLS


def asp_reasonable_ids() -> set[str]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show solvable/1."))
    return {a[0] for a in asp.atoms(model, "solvable")}


# ---------------------------------------------------------------------------
# Simulation
# ---------------------------------------------------------------------------

def make_world(params: StoryParams) -> World:
    place = PLACES[params.place]
    problem = PROBLEMS[params.problem]
    world = World(place)
    camel = world.add(Entity(id=params.name, kind="character", type="camel", label=params.name))
    companion = world.add(Entity(id="companion", kind="character", type=params.companion, label=f"the {params.companion}"))
    blocks = world.add(Entity(id="blocks", kind="thing", type="blocks", label="blocks", caretaker=camel.id))
    world.facts.update(camel=camel, companion=companion, blocks=blocks, problem=problem, tool=TOOLS[problem.fix_kind])

    world.say(f"{camel.label} was a camel who loved the building blocks corner.")
    world.say(f"One day, {camel.label} and {companion.label} found {problem.label}; {problem.premise}.")
    world.say(random.choice(COMEDY_BEATS))

    world.para()
    world.say(f"{camel.label} sniffed the pile and said, “We need a plan for {problem.risk}.”")
    world.say(f"{companion.label.capitalize()} pointed at {problem.hint}, and {camel.label} nodded like a tiny architect.")
    world.say(f"Then they chose {TOOLS[problem.fix_kind].label} to {TOOLS[problem.fix_kind].action}.")

    world.para()
    world.say(f"{camel.label} carefully used {TOOLS[problem.fix_kind].label}; {problem.solution}.")
    world.say(f"{problem.punchline} {TOOLS[problem.fix_kind].tail}")
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def prompts(world: World) -> list[str]:
    p = world.facts["problem"]
    camel = world.facts["camel"]
    return [
        "Write a funny story about a camel solving a problem in a building blocks corner.",
        f"Tell a comedy story where {camel.label} notices {p.label} and fixes it with a useful tool.",
        "Create a small, child-friendly problem-solving tale with blocks, a camel, and a happy ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    camel: Entity = world.facts["camel"]  # type: ignore[assignment]
    comp: Entity = world.facts["companion"]  # type: ignore[assignment]
    prob: Problem = world.facts["problem"]  # type: ignore[assignment]
    tool: Tool = world.facts["tool"]  # type: ignore[assignment]
    return [
        QAItem(
            question=f"Who helped solve the problem in the building blocks corner?",
            answer=f"{camel.label} the camel and {comp.label} worked together to solve it.",
        ),
        QAItem(
            question=f"What was the problem in the story?",
            answer=f"It was {prob.label}, where {prob.premise}.",
        ),
        QAItem(
            question=f"What did they use to fix it?",
            answer=f"They used {tool.label} to {tool.action}, and that made the blocks behave better.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a camel?",
            answer="A camel is a big desert animal with long legs and a gentle face.",
        ),
        QAItem(
            question="What are building blocks for?",
            answer="Building blocks are for stacking, sorting, and building little shapes and towers.",
        ),
        QAItem(
            question="Why do people solve small problems when playing?",
            answer="People solve small problems so play can keep going safely and happily.",
        ),
    ]


# ---------------------------------------------------------------------------
# Generation interface
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Camel storyworld set in building blocks corner.")
    ap.add_argument("--place", choices=PLACES.keys(), default="corner")
    ap.add_argument("--problem", choices=PROBLEMS.keys())
    ap.add_argument("--name", choices=CAMEL_NAMES)
    ap.add_argument("--companion", choices=COMPANIONS)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.problem and args.problem not in PROBLEMS:
        raise StoryError("unknown problem")
    problem_id = args.problem or rng.choice(list(PROBLEMS))
    problem = PROBLEMS[problem_id]
    if not python_reasonable(problem):
        raise StoryError("that problem is not solvable in this tiny world")
    return StoryParams(
        place=args.place,
        problem=problem_id,
        name=args.name or rng.choice(CAMEL_NAMES),
        companion=args.companion or rng.choice(COMPANIONS),
        seed=args.seed,
    )


def generate(params: StoryParams) -> StorySample:
    world = make_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = [f"place: {world.place.label}"]
    for e in world.entities.values():
        lines.append(f"{e.id}: type={e.type} label={e.label}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(f"- {p}" for p in sample.prompts)
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def asp_verify() -> int:
    import storyworlds.asp as asp
    py = {pid for pid, prob in PROBLEMS.items() if python_reasonable(prob)}
    cl = asp_reasonable_ids()
    if py == cl:
        print(f"OK: ASP and Python agree on {len(py)} solvable problems.")
        return 0
    print("Mismatch:")
    print("python-only:", sorted(py - cl))
    print("asp-only:", sorted(cl - py))
    return 1


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show solvable/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show solvable/1."))
        print(sorted(asp.atoms(model, "solvable")))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        for pid in PROBLEMS:
            params = StoryParams(place="corner", problem=pid, name="Coco", companion="child")
            samples.append(generate(params))
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {i + 1}" if len(samples) > 1 else "")
        if i + 1 < len(samples):
            print("\n" + "=" * 60 + "\n")


if __name__ == "__main__":
    main()
