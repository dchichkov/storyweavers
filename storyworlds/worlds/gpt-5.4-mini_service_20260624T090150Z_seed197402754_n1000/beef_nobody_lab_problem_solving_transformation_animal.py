#!/usr/bin/env python3
"""
A tiny animal-story world about a lab problem that gets solved by a helpful
transformation.

Premise:
- A small animal crew is in a lab.
- They have a problem: a hungry helper needs beef, but the beef is in the wrong form.
- The crew figures out how to transform the beef into something safe and useful.

Story shape:
- Beginning: the lab, the animals, the problem.
- Middle: trial, worry, and a clever idea.
- End: the transformed beef solves the problem and changes the mood.

This world keeps the prose child-facing and concrete, with a strong causal turn.
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
# Core world model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" or "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    wearer: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        mapping = {
            "subject": "it",
            "object": "it",
            "possessive": "its",
        }
        return mapping[case]

    def name_or_label(self) -> str:
        return self.label or self.id


@dataclass
class Setting:
    place: str = "the lab"
    indoors: bool = True


@dataclass
class Problem:
    id: str
    what: str
    risk: str
    fix_idea: str
    solved_by: str


@dataclass
class Transformation:
    id: str
    input_item: str
    output_item: str
    method: str
    result_phrase: str


class World:
    def __init__(self, setting: Setting):
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

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = {k: Entity(**{
            "id": v.id,
            "kind": v.kind,
            "type": v.type,
            "label": v.label,
            "phrase": v.phrase,
            "owner": v.owner,
            "wearer": v.wearer,
            "meters": dict(v.meters),
            "memes": dict(v.memes),
        }) for k, v in self.entities.items()}
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTING = Setting(place="the lab", indoors=True)

ANIMALS = {
    "mouse": {"type": "mouse", "label": "Mousey", "phrase": "a tiny mouse"},
    "cat": {"type": "cat", "label": "Mimi", "phrase": "a curious cat"},
    "dog": {"type": "dog", "label": "Ruff", "phrase": "a friendly dog"},
    "rabbit": {"type": "rabbit", "label": "Bun", "phrase": "a quick rabbit"},
}

PROBLEMS = {
    "beef_blocked": Problem(
        id="beef_blocked",
        what="the beef is frozen solid",
        risk="nobody can eat it yet",
        fix_idea="thaw it safely",
        solved_by="warm_machine",
    ),
    "beef_hidden": Problem(
        id="beef_hidden",
        what="the beef is inside a locked cooler",
        risk="nobody can reach the dinner",
        fix_idea="open the cooler with a clever tool",
        solved_by="tool_key",
    ),
    "beef_messy": Problem(
        id="beef_messy",
        what="the beef is too messy to serve",
        risk="nobody wants sticky food",
        fix_idea="transform it into neat meatballs",
        solved_by="meatball_maker",
    ),
}

TRANSFORMATIONS = {
    "thaw": Transformation(
        id="thaw",
        input_item="beef",
        output_item="soft beef",
        method="warmed it just enough",
        result_phrase="the beef turned soft and ready",
    ),
    "shape": Transformation(
        id="shape",
        input_item="beef",
        output_item="meatballs",
        method="rolled it into small round bites",
        result_phrase="the beef became neat little meatballs",
    ),
    "cut": Transformation(
        id="cut",
        input_item="beef",
        output_item="pieces of beef",
        method="cut it into small pieces",
        result_phrase="the beef became easy-to-share pieces",
    ),
}

NAMES = [v["label"] for v in ANIMALS.values()]
SMALL_THINGS = ["beef", "beef bowl", "beef cube", "beef tray"]


# ---------------------------------------------------------------------------
# Story parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    animal: str
    problem: str
    transformation: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def problem_can_be_solved(problem: Problem, transformation: Transformation) -> bool:
    if problem.id == "beef_blocked" and transformation.id == "thaw":
        return True
    if problem.id == "beef_messy" and transformation.id == "shape":
        return True
    if problem.id == "beef_hidden" and transformation.id == "cut":
        return True
    return False


def explain_rejection(problem: Problem, transformation: Transformation) -> str:
    return (
        f"(No story: {problem.what}, but the chosen transformation '{transformation.id}' "
        f"does not honestly solve it. Pick the matching fix.)"
    )


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
problem_ok(P,T) :- problem(P), transform(T), match(P,T).
valid_story(A,P,T) :- animal(A), problem_ok(P,T), fits_animal(A).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for a in ANIMALS:
        lines.append(asp.fact("animal", a))
        lines.append(asp.fact("fits_animal", a))
    for p in PROBLEMS:
        lines.append(asp.fact("problem", p))
    for t in TRANSFORMATIONS:
        lines.append(asp.fact("transform", t))
    lines.extend([
        asp.fact("match", "beef_blocked", "thaw"),
        asp.fact("match", "beef_messy", "shape"),
        asp.fact("match", "beef_hidden", "cut"),
    ])
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = sorted((a, p, t) for a in ANIMALS for p in PROBLEMS for t in TRANSFORMATIONS if problem_can_be_solved(PROBLEMS[p], TRANSFORMATIONS[t]))
    asp_set = asp_valid_stories()
    if py == asp_set:
        print(f"OK: clingo gate matches Python gate ({len(py)} stories).")
        return 0
    print("MISMATCH between clingo and Python gates.")
    print("Python only:", sorted(set(py) - set(asp_set)))
    print("ASP only:", sorted(set(asp_set) - set(py)))
    return 1


# ---------------------------------------------------------------------------
# World logic
# ---------------------------------------------------------------------------
def introduce(world: World, animal: Entity) -> None:
    world.say(
        f"In the lab, {animal.label} was a small animal with bright eyes and quick paws."
    )


def state_problem(world: World, animal: Entity, problem: Problem) -> None:
    world.say(
        f"{animal.label} looked at the table and saw that {problem.what}, so {problem.risk}."
    )


def try_fixes(world: World, animal: Entity, problem: Problem, trans: Transformation) -> None:
    world.say(
        f"{animal.label} sniffed the air, tapped the bowl, and thought, "
        f"\"Maybe I can {problem.fix_idea}.\""
    )
    world.say(
        f"After a careful try, {animal.label} {trans.method}, and {trans.result_phrase}."
    )


def resolve(world: World, animal: Entity, problem: Problem, trans: Transformation) -> None:
    world.say(
        f"That solved the problem. Now {animal.label} could share the {trans.output_item}, "
        f"and nobody in the lab had to stay hungry."
    )
    world.say(
        f"{animal.label} smiled as the lab felt calm and tidy again."
    )


def tell(animal_id: str, problem_id: str, transformation_id: str) -> World:
    problem = PROBLEMS[problem_id]
    trans = TRANSFORMATIONS[transformation_id]
    if not problem_can_be_solved(problem, trans):
        raise StoryError(explain_rejection(problem, trans))

    world = World(SETTING)
    animal_cfg = ANIMALS[animal_id]
    animal = world.add(Entity(
        id=animal_id,
        kind="character",
        type=animal_cfg["type"],
        label=animal_cfg["label"],
        phrase=animal_cfg["phrase"],
        meters={"curiosity": 1.0},
        memes={"hope": 1.0},
    ))
    beef = world.add(Entity(
        id="beef",
        kind="thing",
        type="beef",
        label="beef",
        phrase="a small plate of beef",
        owner=animal.id,
        meters={"cold": 1.0 if problem.id == "beef_blocked" else 0.0, "mess": 1.0 if problem.id == "beef_messy" else 0.0},
    ))

    introduce(world, animal)
    world.para()
    state_problem(world, animal, problem)
    world.say(f"The beef sat there, waiting for a clever fix.")
    world.para()
    try_fixes(world, animal, problem, trans)
    resolve(world, animal, problem, trans)

    world.facts.update(animal=animal, beef=beef, problem=problem, trans=trans)
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    animal = f["animal"]
    problem = f["problem"]
    trans = f["trans"]
    return [
        f'Write a short animal story set in a lab where {animal.label} notices {problem.what} and solves it.',
        f"Tell a simple story about a small animal in the lab who uses {trans.id} to fix a beef problem.",
        f'Write a child-friendly animal story that includes a lab, beef, and a clever transformation.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    animal = f["animal"]
    problem = f["problem"]
    trans = f["trans"]
    return [
        QAItem(
            question=f"Who was in the lab story?",
            answer=f"It was about {animal.label}, a small animal in the lab.",
        ),
        QAItem(
            question=f"What problem did {animal.label} see?",
            answer=f"{animal.label} saw that {problem.what}, which meant {problem.risk}.",
        ),
        QAItem(
            question=f"How was the problem solved?",
            answer=f"{animal.label} solved it by using a careful transformation: {trans.method}.",
        ),
        QAItem(
            question=f"What changed at the end?",
            answer=f"At the end, the beef was transformed into {trans.output_item}, and the lab felt calm again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a lab?",
            answer="A lab is a place where people or animals test ideas, mix things, and try careful experiments.",
        ),
        QAItem(
            question="What is beef?",
            answer="Beef is meat that comes from a cow, and people can cook it for food.",
        ),
        QAItem(
            question="What does transformation mean?",
            answer="Transformation means something changes into a different form or shape.",
        ),
        QAItem(
            question="Why is problem solving important?",
            answer="Problem solving helps you find a smart way to fix trouble instead of giving up.",
        ),
    ]


# ---------------------------------------------------------------------------
# CLI helpers
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal story world: a lab problem solved by transformation.")
    ap.add_argument("--animal", choices=ANIMALS.keys())
    ap.add_argument("--problem", choices=PROBLEMS.keys())
    ap.add_argument("--transformation", choices=TRANSFORMATIONS.keys())
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
    if args.problem and args.transformation:
        if not problem_can_be_solved(PROBLEMS[args.problem], TRANSFORMATIONS[args.transformation]):
            raise StoryError(explain_rejection(PROBLEMS[args.problem], TRANSFORMATIONS[args.transformation]))
    animal = args.animal or rng.choice(list(ANIMALS))
    if args.problem and not args.transformation:
        possible = [t for t in TRANSFORMATIONS if problem_can_be_solved(PROBLEMS[args.problem], TRANSFORMATIONS[t])]
        if not possible:
            raise StoryError("(No valid transformation for the chosen problem.)")
        transformation = rng.choice(possible)
        problem = args.problem
    elif args.transformation and not args.problem:
        possible = [p for p in PROBLEMS if problem_can_be_solved(PROBLEMS[p], TRANSFORMATIONS[args.transformation])]
        if not possible:
            raise StoryError("(No valid problem for the chosen transformation.)")
        problem = rng.choice(possible)
        transformation = args.transformation
    else:
        problem, transformation = rng.choice([
            (p, t) for p in PROBLEMS for t in TRANSFORMATIONS if problem_can_be_solved(PROBLEMS[p], TRANSFORMATIONS[t])
        ])
    return StoryParams(animal=animal, problem=problem, transformation=transformation)


def generate(params: StoryParams) -> StorySample:
    world = tell(params.animal, params.problem, params.transformation)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id} ({e.kind}/{e.type}) {' '.join(bits)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World questions ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(animal="mouse", problem="beef_blocked", transformation="thaw"),
    StoryParams(animal="cat", problem="beef_messy", transformation="shape"),
    StoryParams(animal="rabbit", problem="beef_hidden", transformation="cut"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/3."))
        triples = asp.atoms(model, "valid_story")
        print(f"{len(triples)} compatible animal/problem/transformation stories:")
        for t in sorted(triples):
            print("  ", t)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
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
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
