#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/bathing_thin_problem_solving_slice_of_life.py
============================================================================================================

A small slice-of-life storyworld about bathing a thin little pet, a gentle
problem, and a practical solution.

Seed image:
---
A child notices that a thin little puppy is dusty after playing outside. The
bath looks too big and a little scary, but the parent helps solve the problem by
using a shallow tub, a soft cloth, and a warm towel. The puppy ends up clean,
dry, and proud.
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
    kind: str = "thing"  # character | pet | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    size: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "mom", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "dad", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the backyard"
    indoors: bool = False


@dataclass
class Problem:
    id: str
    trouble: str
    verb: str
    rush: str
    result: str
    tag: str


@dataclass
class Solution:
    id: str
    label: str
    prep: str
    tail: str
    helps: set[str]
    calm_bonus: float = 1.0


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.trace_bits: list[str] = []

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
        import copy

        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "home": Setting(place="the bathroom", indoors=True),
    "grandma": Setting(place="Grandma's bathroom", indoors=True),
}

PROBLEMS = {
    "dusty_puppy": Problem(
        id="dusty_puppy",
        trouble="dusty",
        verb="give the puppy a bath",
        rush="hurry toward the tub",
        result="clean and comfy",
        tag="bathing",
    ),
    "sticky_hair": Problem(
        id="sticky_hair",
        trouble="sticky",
        verb="wash the child's hair",
        rush="lean over the sink",
        result="fresh and neat",
        tag="bathing",
    ),
}

SOLUTIONS = [
    Solution(
        id="shallow_tub",
        label="a shallow tub",
        prep="fill a shallow tub with warm water",
        tail="used the shallow tub so the little body would not feel overwhelmed",
        helps={"dusty_puppy"},
        calm_bonus=1.0,
    ),
    Solution(
        id="soft_cloth",
        label="a soft cloth",
        prep="wet a soft cloth first",
        tail="wiped gently instead of splashing",
        helps={"dusty_puppy", "sticky_hair"},
        calm_bonus=1.0,
    ),
    Solution(
        id="warm_towel",
        label="a warm towel",
        prep="set out a warm towel",
        tail="wrapped the pet up right away",
        helps={"dusty_puppy", "sticky_hair"},
        calm_bonus=1.0,
    ),
    Solution(
        id="small_step",
        label="a little step stool",
        prep="bring over a little step stool",
        tail="made the sink easier to reach",
        helps={"sticky_hair"},
        calm_bonus=0.5,
    ),
]

NAMES = ["Mia", "Noah", "Lily", "Leo", "Ava", "Finn", "Zoe", "Owen"]
PARENTS = ["mother", "father"]
PETS = [
    ("puppy", "puppy", "pet"),
    ("kitten", "kitten", "pet"),
]
TRAITS = ["gentle", "curious", "patient", "careful", "cheerful"]


# ---------------------------------------------------------------------------
# Params
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    problem: str
    name: str
    parent: str
    pet: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
problem(P) :- problem_id(P).
solution(S) :- solution_id(S).

helps(S,P) :- solution(S), problem(P), helps_problem(S,P).
usable(P,S) :- problem(P), solution(S), helps(S,P).

valid(P,S) :- usable(P,S).
#show valid/2.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid in SETTINGS:
        lines.append(asp.fact("setting_id", pid))
    for pid in PROBLEMS:
        lines.append(asp.fact("problem_id", pid))
    for sid, sol in ((s.id, s) for s in SOLUTIONS):
        lines.append(asp.fact("solution_id", sid))
        for p in sorted(sol.helps):
            lines.append(asp.fact("helps_problem", sid, p))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_pairs() -> list[tuple[str, str]]:
    import asp

    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def reasonableness_gate(problem: Problem, solution: Solution) -> bool:
    return problem.id in solution.helps


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------

def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.problem and args.solution:
        prob = PROBLEMS[args.problem]
        sol = next(s for s in SOLUTIONS if s.id == args.solution)
        if not reasonableness_gate(prob, sol):
            raise StoryError(
                f"(No story: {sol.label} does not actually solve {prob.id}. "
                f"Pick a solution that helps with the bathing problem.)"
            )

    valid = [
        (place, prob_id)
        for place in SETTINGS
        for prob_id in PROBLEMS
        if (args.place is None or args.place == place)
        and (args.problem is None or args.problem == prob_id)
        and any(reasonableness_gate(PROBLEMS[prob_id], s) for s in SOLUTIONS)
    ]
    if not valid:
        raise StoryError("(No valid bathing story matches the given options.)")

    place, prob_id = rng.choice(valid)
    name = args.name or rng.choice(NAMES)
    parent = args.parent or rng.choice(PARENTS)
    pet = args.pet or rng.choice([p[0] for p in PETS])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, problem=prob_id, name=name, parent=parent, pet=pet, trait=trait)


def choose_solution(problem: Problem) -> Optional[Solution]:
    for sol in SOLUTIONS:
        if problem.id in sol.helps:
            return sol
    return None


def simulate(params: StoryParams) -> World:
    world = World(SETTINGS[params.place])
    child = world.add(Entity(id=params.name, kind="character", type="child", label=params.name))
    parent = world.add(Entity(id="Parent", kind="character", type=params.parent, label=f"the {params.parent}"))
    pet = world.add(Entity(
        id="Pet",
        kind="pet",
        type=params.pet,
        label=f"a thin little {params.pet}",
        phrase=f"a thin little {params.pet}",
        owner=child.id,
    ))
    problem = PROBLEMS[params.problem]
    solution = choose_solution(problem)
    if solution is None:
        raise StoryError("This storyworld requires a problem with a real solution.")

    world.facts.update(child=child, parent=parent, pet=pet, problem=problem, solution=solution)

    # Setup
    world.say(f"{child.id} had a thin little {params.pet} who was still dusty from playing outside.")
    world.say(f"{child.pronoun('possessive').capitalize()} {params.parent} said it was time to {problem.verb}.")
    world.para()

    # Problem
    child.memes["care"] = 1
    pet.meters["dust"] = 1
    pet.memes["nervous"] = 1
    world.say(f"But the bath looked big, and the thin little {params.pet} scooted back.")
    world.say(f"{child.id} wanted to help, but {problem.trouble} fur can be hard to wash without a calm plan.")
    world.para()

    # Solution
    child.memes["problem_solving"] = 1
    parent.memes["helpfulness"] = 1
    world.say(f"Then {child.id}'s {params.parent} thought for a moment and came up with a better way.")
    world.say(f"They chose {solution.label}: {solution.prep}.")
    world.say(f"It was a gentle choice, because {solution.tail}.")
    pet.meters["dust"] = 0
    pet.meters["clean"] = 1
    pet.memes["nervous"] = 0
    pet.memes["proud"] = 1
    child.memes["joy"] = 1
    parent.memes["relief"] = 1
    world.para()

    # Ending
    world.say(f"Soon the thin little {params.pet} was clean, warm, and wagging happily.")
    world.say(f"{child.id} smiled at the neat little result, and the bathroom felt peaceful again.")
    world.facts["resolved"] = True
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    prob = f["problem"]
    sol = f["solution"]
    return [
        f"Write a short slice-of-life story for a young child about {child.id} and {prob.tag}.",
        f"Tell a gentle story where a thin little {f['pet'].type} needs bathing and the family solves the problem kindly.",
        f"Write a simple story about {sol.label} helping with {prob.verb}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    pet = f["pet"]
    prob = f["problem"]
    sol = f["solution"]
    return [
        QAItem(
            question=f"Why did {child.id} and {parent.label} need to think of a new plan?",
            answer=(
                f"They needed a new plan because the {pet.type} was thin and dusty, "
                f"and a big bath felt a little scary. The old way would not have been the kindest way to do it."
            ),
        ),
        QAItem(
            question=f"What problem was the family trying to solve for the thin little {pet.type}?",
            answer=(
                f"They were trying to solve the bathing problem by getting the thin little {pet.type} clean without upsetting it."
            ),
        ),
        QAItem(
            question=f"What helped make {prob.verb} easier?",
            answer=(
                f"{sol.label} helped. The family used it so the bath could stay gentle and the little {pet.type} could feel safe."
            ),
        ),
        QAItem(
            question=f"How did the story end?",
            answer=(
                f"It ended with the thin little {pet.type} clean, warm, and happy, while {child.id} felt proud of helping."
            ),
        ),
    ]


WORLD_KNOWLEDGE = [
    QAItem(
        question="Why do people use warm water for bathing?",
        answer="Warm water helps washing feel comfortable, so a bath is less shocking and more relaxing.",
    ),
    QAItem(
        question="What is a towel for?",
        answer="A towel is used to dry wet skin or fur after washing.",
    ),
    QAItem(
        question="Why can a shallow tub be helpful?",
        answer="A shallow tub keeps the water lower, which can make bathing feel safer for a small animal or child.",
    ),
]


def world_qa(world: World) -> list[QAItem]:
    return list(WORLD_KNOWLEDGE)


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== Story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP helpers
# ---------------------------------------------------------------------------

def asp_verify() -> int:
    import asp

    clingo_pairs = set(asp_valid_pairs())
    python_pairs = {
        (prob_id, sol.id)
        for prob_id, prob in PROBLEMS.items()
        for sol in SOLUTIONS
        if reasonableness_gate(prob, sol)
    }
    if clingo_pairs == python_pairs:
        print(f"OK: clingo gate matches Python gate ({len(clingo_pairs)} pairs).")
        return 0
    print("Mismatch between clingo and Python:")
    print(" only in clingo:", sorted(clingo_pairs - python_pairs))
    print(" only in python:", sorted(python_pairs - clingo_pairs))
    return 1


def show_asp() -> str:
    return asp_program("#show valid/2.")


# ---------------------------------------------------------------------------
# Public interface
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A small bathing problem-solving slice-of-life storyworld."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--solution", choices=[s.id for s in SOLUTIONS])
    ap.add_argument("--name")
    ap.add_argument("--parent", choices=PARENTS)
    ap.add_argument("--pet", choices=[p[0] for p in PETS])
    ap.add_argument("--trait", choices=TRAITS)
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


def generate(params: StoryParams) -> StorySample:
    world = simulate(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.label:
            bits.append(f"label={e.label!r}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(show_asp())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        pairs = asp_valid_pairs()
        print(f"{len(pairs)} valid problem/solution pairs:\n")
        for prob_id, sol_id in pairs:
            print(f"  {prob_id:14} {sol_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    if args.all:
        params_list = [
            StoryParams(place="home", problem="dusty_puppy", name="Mia", parent="mother", pet="puppy", trait="gentle"),
            StoryParams(place="grandma", problem="sticky_hair", name="Leo", parent="father", pet="kitten", trait="careful"),
        ]
        samples = [generate(p) for p in params_list]
    else:
        samples: list[StorySample] = []
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
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
        header = ""
        if len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
