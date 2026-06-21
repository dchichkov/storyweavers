#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/stairs_invincible_rhyme_problem_solving_happy_ending.py
=======================================================================================

A small heartwarming storyworld about a child, a tricky staircase, and a
kindly problem-solving turn that ends in a bright, safe, happy image.

Seed words:
- stairs
- invincible

Features:
- Rhyme
- Problem Solving
- Happy Ending
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

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

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


@dataclass
class Staircase:
    id: str
    label: str
    steepness: int
    has_rail: bool
    wants_rhyme: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Problem:
    id: str
    label: str
    danger: int
    fix_need: str
    prompt_line: str
    solved_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Solution:
    id: str
    label: str
    power: int
    method: str
    closing: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.facts: dict = {}
        self.fired: set[str] = set()
        self.paragraphs: list[list[str]] = [[]]

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
        import copy
        w = World()
        w.entities = copy.deepcopy(self.entities)
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


STAIRCASES = {
    "old_hall": Staircase(
        id="old_hall",
        label="the old stairs in the hall",
        steepness=3,
        has_rail=True,
        wants_rhyme="up, up, up they go",
        tags={"stairs", "home"},
    ),
    "tree_house": Staircase(
        id="tree_house",
        label="the narrow stairs to the tree house",
        steepness=2,
        has_rail=False,
        wants_rhyme="step, step, tiptoe slow",
        tags={"stairs", "outdoor"},
    ),
    "library_loft": Staircase(
        id="library_loft",
        label="the tall stairs by the library loft",
        steepness=4,
        has_rail=True,
        wants_rhyme="one by one they climb and know",
        tags={"stairs", "library"},
    ),
}

PROBLEMS = {
    "night_light": Problem(
        id="night_light",
        label="a dark stairway",
        danger=2,
        fix_need="light",
        prompt_line="The steps looked shadowy and long, so the child wanted a little light.",
        solved_line="A lamp would help the steps feel friendly again.",
        tags={"light", "stairs"},
    ),
    "scattered_blocks": Problem(
        id="scattered_blocks",
        label="toy blocks on a step",
        danger=3,
        fix_need="clear_path",
        prompt_line="A few blocks were scattered on the stairs like a tiny surprise.",
        solved_line="The path needed clearing before anybody could climb safely.",
        tags={"blocks", "stairs"},
    ),
    "wobbly_boot": Problem(
        id="wobbly_boot",
        label="a wobbly boot lace",
        danger=1,
        fix_need="tie_lace",
        prompt_line="One lace was loose, and that made the climb feel uncertain.",
        solved_line="A snug tie would make the first step feel steady.",
        tags={"shoe", "stairs"},
    ),
}

SOLUTIONS = {
    "lamp": Solution(
        id="lamp",
        label="a warm lamp",
        power=2,
        method="turned on a warm lamp and set it near the wall",
        closing="the staircase glowed softly again",
        tags={"light"},
    ),
    "basket": Solution(
        id="basket",
        label="a basket",
        power=3,
        method="picked up the blocks and tucked them into a basket",
        closing="the stairs stood neat and clear",
        tags={"blocks"},
    ),
    "tie": Solution(
        id="tie",
        label="a careful knot",
        power=1,
        method="knelt down and tied the loose lace into a careful knot",
        closing="the shoe felt snug and strong",
        tags={"shoe"},
    ),
}


@dataclass
class StoryParams:
    staircase: str = "old_hall"
    problem: str = "night_light"
    solution: str = "lamp"
    child_name: str = "Mia"
    child_gender: str = "girl"
    helper_name: str = "Dad"
    helper_gender: str = "man"
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for s_id, stair in STAIRCASES.items():
        for p_id, prob in PROBLEMS.items():
            if prob.fix_need not in {"light", "clear_path", "tie_lace"}:
                continue
            for sol_id, sol in SOLUTIONS.items():
                if prob.fix_need in sol.tags:
                    combos.append((s_id, p_id, sol_id))
    return combos


def rhymed_line(stair: Staircase, problem: Problem, solution: Solution) -> str:
    if stair.id == "old_hall":
        return f"Up the stairs, soft and small, they found a way to shine for all."
    if stair.id == "tree_house":
        return f"Step by step on the wooden way, they made the trouble slip away."
    return f"One by one on the lofty flight, they turned the worry into light."


def reasonableness_gate(stair: Staircase, problem: Problem, solution: Solution) -> None:
    if (problem.fix_need not in solution.tags) or (
        problem.fix_need == "light" and solution.power < 2
    ):
        raise StoryError(
            f"(No story: {solution.label} does not solve {problem.label} on {stair.label}.)"
        )


def build_story(world: World, child: Entity, helper: Entity, stair: Staircase,
                problem: Problem, solution: Solution) -> None:
    child.memes["hope"] = 1.0
    child.memes["pride"] = 0.5
    helper.memes["care"] = 1.0

    world.say(
        f"{child.id} and {helper.id} came to {stair.label}. The child felt a tiny spark of courage, "
        f"almost invincible, because the day was bright and the home was warm."
    )
    world.say(problem.prompt_line)
    world.say(
        f'"It may look tricky," said {helper.id}, "but we can solve it." '
        f"{child.id} liked that gentle tune in the air."
    )

    if problem.id == "night_light":
        world.say(
            f"{helper.id} did not rush. Instead, {helper.pronoun()} "
            f"{solution.method}. The dark corners softened at once."
        )
    elif problem.id == "scattered_blocks":
        world.say(
            f"{helper.id} smiled and {solution.method}. {child.id} helped carry the basket, "
            f"and the little job felt like a game."
        )
    else:
        world.say(
            f"{helper.id} crouched beside the shoe and {solution.method}. "
            f"{child.id} stood still and watched the wobble disappear."
        )

    world.say(
        f"Then {child.id} took a breath and climbed. {rhymed_line(stair, problem, solution)}"
    )
    world.say(
        f"At the top, {problem.solved_line} {solution.closing.capitalize()}, and "
        f"{child.id} grinned at {helper.id} with a heart as bright as morning."
    )

    child.memes["joy"] = 2.0
    child.memes["safety"] = 1.0
    helper.memes["joy"] = 1.5

    world.facts.update(
        child=child,
        helper=helper,
        stair=stair,
        problem=problem,
        solution=solution,
        solved=True,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    stair: Staircase = f["stair"]
    problem: Problem = f["problem"]
    solution: Solution = f["solution"]
    return [
        f'Write a heartwarming story for a small child that includes the word "stairs" and the feeling of being "invincible".',
        f"Tell a gentle rhyming story where {f['child'].id} faces {problem.label} on {stair.label} and uses {solution.label} to solve it.",
        f"Write a happy problem-solving story about climbing stairs safely, with a rhyme near the end and a warm family feeling.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child: Entity = f["child"]
    helper: Entity = f["helper"]
    stair: Staircase = f["stair"]
    problem: Problem = f["problem"]
    solution: Solution = f["solution"]
    return [
        (
            "Why did the child feel worried at first?",
            f"The {stair.label} had {problem.label}, so the climb did not feel easy. "
            f"That is why the child needed a calm plan before going up."
        ),
        (
            "How did they solve the problem?",
            f"{helper.id} used {solution.method}, and that fixed the trouble. "
            f"Once the problem was handled, the stairs felt safe again."
        ),
        (
            "How did the story end?",
            f"It ended happily, with {child.id} smiling at {helper.id} at the top of the stairs. "
            f"The child felt brave, warm, and almost invincible in the best way."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What are stairs?",
            answer="Stairs are a set of steps that help people go up or down from one level to another. "
                   "They are safest when people take them one step at a time."
        ),
        QAItem(
            question="What does invincible mean?",
            answer="Invincible means it feels like nothing can stop you. In a story, a child might feel invincible when they feel brave and supported."
        ),
        QAItem(
            question="Why is problem solving helpful?",
            answer="Problem solving helps people find a safe or clever way to fix a hard situation. "
                   "It can turn worry into relief."
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
    for e in world.entities.values():
        parts = []
        if e.meters:
            parts.append(f"meters={e.meters}")
        if e.memes:
            parts.append(f"memes={e.memes}")
        if e.role:
            parts.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(parts)}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,P,L) :- stair(S), problem(P), solution(L), solves(P,L).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in STAIRCASES:
        lines.append(asp.fact("stair", sid))
    for pid, p in PROBLEMS.items():
        lines.append(asp.fact("problem", pid))
        lines.append(asp.fact("solves", pid, p.fix_need))
    for lid, s in SOLUTIONS.items():
        lines.append(asp.fact("solution", lid))
        for t in s.tags:
            lines.append(asp.fact("tag", lid, t))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program(show="#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    rc = 0
    if py == cl:
        print(f"OK: ASP gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combo gate.")
        print(" only python:", sorted(py - cl))
        print(" only asp:", sorted(cl - py))

    try:
        sample = generate(resolve_params(argparse.Namespace(
            staircase=None, problem=None, solution=None, child_name=None,
            child_gender=None, helper_name=None, helper_gender=None, seed=None
        ), random.Random(777)))
        _ = sample.story
        print("OK: smoke test generation succeeded.")
    except Exception as exc:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming stairs storyworld.")
    ap.add_argument("--staircase", choices=STAIRCASES)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--solution", choices=SOLUTIONS)
    ap.add_argument("--name", dest="child_name")
    ap.add_argument("--gender", dest="child_gender", choices=["girl", "boy"])
    ap.add_argument("--helper", dest="helper_name")
    ap.add_argument("--helper-gender", dest="helper_gender", choices=["woman", "man"])
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
    combos = [c for c in valid_combos()
              if (args.staircase is None or c[0] == args.staircase)
              and (args.problem is None or c[1] == args.problem)
              and (args.solution is None or c[2] == args.solution)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    staircase, problem, solution = rng.choice(sorted(combos))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or rng.choice(["woman", "man"])
    child_name = args.child_name or rng.choice(["Mia", "Leo", "Nora", "Ben", "Ava"])
    helper_name = args.helper_name or rng.choice(["Mom", "Dad", "Aunt June", "Uncle Ray"])
    return StoryParams(
        staircase=staircase,
        problem=problem,
        solution=solution,
        child_name=child_name,
        child_gender=child_gender,
        helper_name=helper_name,
        helper_gender=helper_gender,
    )


def generate(params: StoryParams) -> StorySample:
    if params.staircase not in STAIRCASES:
        raise StoryError("Unknown staircase.")
    if params.problem not in PROBLEMS:
        raise StoryError("Unknown problem.")
    if params.solution not in SOLUTIONS:
        raise StoryError("Unknown solution.")
    stair = STAIRCASES[params.staircase]
    problem = PROBLEMS[params.problem]
    solution = SOLUTIONS[params.solution]
    reasonableness_gate(stair, problem, solution)

    world = World()
    child = world.add(Entity(id=params.child_name, kind="character", type=params.child_gender, role="child"))
    helper = world.add(Entity(id=params.helper_name, kind="character", type=params.helper_gender, role="helper"))

    build_story(world, child, helper, stair, problem, solution)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
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
    StoryParams(staircase="old_hall", problem="night_light", solution="lamp", child_name="Mia", child_gender="girl", helper_name="Dad", helper_gender="man"),
    StoryParams(staircase="tree_house", problem="scattered_blocks", solution="basket", child_name="Leo", child_gender="boy", helper_name="Mom", helper_gender="woman"),
    StoryParams(staircase="library_loft", problem="wobbly_boot", solution="tie", child_name="Nora", child_gender="girl", helper_name="Aunt June", helper_gender="woman"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program(show="#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for c in combos:
            print(" ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
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

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
