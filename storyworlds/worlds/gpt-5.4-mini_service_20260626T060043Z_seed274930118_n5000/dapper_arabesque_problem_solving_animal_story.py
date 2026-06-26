#!/usr/bin/env python3
"""
A small animal storyworld about a dapper dancer who solves a problem with
careful thinking, clever tools, and a little arabesque flair.
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


@dataclass
class Animal:
    name: str
    kind: str
    role: str
    dapper: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Place:
    name: str
    setting_note: str


@dataclass
class Problem:
    issue: str
    blocked: str
    fix_tool: str
    solved_image: str


@dataclass
class StoryParams:
    place: str
    hero_kind: str
    helper_kind: str
    problem: str
    name: str
    seed: Optional[int] = None


PLACES = {
    "meadow": Place(name="the meadow", setting_note="The grass was soft, and a little stage stood under a striped cloth."),
    "barnyard": Place(name="the barnyard", setting_note="The hay was neat, and the fence had been turned into a tiny show ring."),
    "garden": Place(name="the garden", setting_note="The hedges made a green tunnel, and a small path curved like a ribbon."),
}

ANIMALS = {
    "fox": "fox",
    "rabbit": "rabbit",
    "hedgehog": "hedgehog",
    "squirrel": "squirrel",
    "mouse": "mouse",
    "cat": "cat",
}

PROBLEMS = {
    "ribbon": Problem(
        issue="a bright ribbon snagged on a branch",
        blocked="the ending dance",
        fix_tool="a smooth stick and a patient paw",
        solved_image="the ribbon floating free again while the dancers finished in a neat line",
    ),
    "bridge": Problem(
        issue="a little bridge over the stream tilted sideways",
        blocked="the parade across the water",
        fix_tool="three flat stones and a steady push",
        solved_image="the bridge standing firm, with tiny feet crossing one by one",
    ),
    "lantern": Problem(
        issue="the lantern string came loose",
        blocked="the night show",
        fix_tool="a knot and a borrowed twig",
        solved_image="the lantern shining high above the stage again",
    ),
}


class World:
    def __init__(self, params: StoryParams) -> None:
        self.params = params
        self.place = PLACES[params.place]
        self.problem = PROBLEMS[params.problem]
        self.hero = Animal(name=params.name, kind=params.hero_kind, role="hero", dapper=True)
        helper_name = {
            "fox": "Fenn",
            "rabbit": "Pip",
            "hedgehog": "Nell",
            "squirrel": "Tuck",
            "mouse": "Milo",
            "cat": "Mina",
        }[params.helper_kind]
        if helper_name == self.hero.name:
            helper_name = helper_name + "y"
        self.helper = Animal(name=helper_name, kind=params.helper_kind, role="helper", dapper=False)
        self.facts: dict[str, str] = {}
        self.paragraphs: list[list[str]] = [[]]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal storyworld with dapper problem solving and an arabesque turn.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--hero-kind", choices=sorted(ANIMALS))
    ap.add_argument("--helper-kind", choices=sorted(ANIMALS))
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--name")
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
    choices = []
    for place in PLACES:
        for problem in PROBLEMS:
            for hero in ANIMALS:
                for helper in ANIMALS:
                    if hero == helper:
                        continue
                    choices.append((place, hero, helper, problem))
    filtered = [
        c for c in choices
        if (args.place is None or c[0] == args.place)
        and (args.hero_kind is None or c[1] == args.hero_kind)
        and (args.helper_kind is None or c[2] == args.helper_kind)
        and (args.problem is None or c[3] == args.problem)
    ]
    if not filtered:
        raise StoryError("No valid animal story matches the requested options.")
    place, hero_kind, helper_kind, problem = rng.choice(filtered)
    name = args.name or rng.choice(["Dottie", "Miso", "Bram", "Tilly", "Nico", "Pippa"])
    return StoryParams(place=place, hero_kind=hero_kind, helper_kind=helper_kind, problem=problem, name=name)


def intro(world: World) -> None:
    world.say(
        f"In {world.place.name}, there lived a dapper {world.hero.kind} named {world.hero.name}. "
        f"{world.place.setting_note}"
    )
    world.say(
        f"{world.hero.name} loved to practice an arabesque, lifting one foot and stretching like a ribbon in the breeze."
    )


def problem_start(world: World) -> None:
    world.para()
    world.say(
        f"One day, {world.problem.issue} and blocked {world.problem.blocked}."
    )
    world.say(
        f"{world.hero.name} looked at the snag and did not panic. "
        f"{world.hero.name} thought first, then called for {world.helper.name}, a clever {world.helper.kind} friend."
    )


def solve(world: World) -> None:
    world.say(
        f"Together they studied the branch, the ribbon, and the little stage."
    )
    world.say(
        f"{world.helper.name} held the branch still while {world.hero.name} used {world.problem.fix_tool}."
    )
    world.say(
        f"With one careful tug, the problem gave way."
    )
    world.para()
    world.say(
        f"Soon {world.problem.solved_image}. {world.hero.name} twirled into an arabesque, neat and proud, and the whole show could begin."
    )


def tell(params: StoryParams) -> World:
    world = World(params)
    world.facts["place"] = params.place
    world.facts["hero_kind"] = params.hero_kind
    world.facts["helper_kind"] = params.helper_kind
    world.facts["problem"] = params.problem
    intro(world)
    problem_start(world)
    solve(world)
    return world


def generation_prompts(world: World) -> list[str]:
    return [
        f"Write a short animal story about a dapper {world.hero.kind} who solves a problem in {world.place.name}.",
        f"Tell a gentle story where {world.hero.name} uses careful thinking and an arabesque to fix {world.problem.issue}.",
        f"Write a child-friendly animal story with a clear problem, a clever helper, and a happy ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question=f"Who was the dapper animal in the story?",
            answer=f"The dapper animal was {world.hero.name}, a {world.hero.kind}.",
        ),
        QAItem(
            question=f"What problem did they need to solve?",
            answer=f"They needed to solve the problem where {world.problem.issue}.",
        ),
        QAItem(
            question=f"How did the animals fix it?",
            answer=f"{world.hero.name} and {world.helper.name} fixed it by using {world.problem.fix_tool}.",
        ),
        QAItem(
            question=f"What dance shape did {world.hero.name} do at the end?",
            answer=f"{world.hero.name} finished with an arabesque, which made the ending look graceful and proud.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does dapper mean?",
            answer="Dapper means neat, stylish, and nicely dressed.",
        ),
        QAItem(
            question="What is an arabesque?",
            answer="An arabesque is a ballet pose where one leg is stretched out behind the body for a graceful shape.",
        ),
        QAItem(
            question="What does it mean to solve a problem?",
            answer="To solve a problem means to find a good way to fix something that is not working.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== Story questions ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== World questions ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    lines.append(f"place: {world.place.name}")
    lines.append(f"hero: {world.hero.name} ({world.hero.kind})")
    lines.append(f"helper: {world.helper.name} ({world.helper.kind})")
    lines.append(f"problem: {world.problem.issue}")
    return "\n".join(lines)


ASP_RULES = r"""
hero(X) :- hero_kind(X).
helper(X) :- helper_kind(X).
problem(P) :- problem_kind(P).
compatible_story(Place, Hero, Helper, Problem) :- place_kind(Place), hero_kind(Hero), helper_kind(Helper), problem_kind(Problem), Hero != Helper.
"""

def asp_facts() -> str:
    import asp
    lines = []
    for p in PLACES:
        lines.append(asp.fact("place_kind", p))
    for a in ANIMALS:
        lines.append(asp.fact("hero_kind", a))
        lines.append(asp.fact("helper_kind", a))
    for p in PROBLEMS:
        lines.append(asp.fact("problem_kind", p))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show compatible_story/4."))
    clingo_set = set(asp.atoms(model, "compatible_story"))
    python_set = set((p, h, k, pr) for p in PLACES for h in ANIMALS for k in ANIMALS if h != k for pr in PROBLEMS)
    if clingo_set == python_set:
        print(f"OK: clingo gate matches Python ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and Python.")
    return 1


def valid_combos() -> list[tuple[str, str, str, str]]:
    return [(p, h, k, pr) for p in PLACES for h in ANIMALS for k in ANIMALS if h != k for pr in PROBLEMS]


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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


CURATED = [
    StoryParams(place="meadow", hero_kind="fox", helper_kind="rabbit", problem="ribbon", name="Dottie"),
    StoryParams(place="barnyard", hero_kind="cat", helper_kind="hedgehog", problem="bridge", name="Mina"),
    StoryParams(place="garden", hero_kind="squirrel", helper_kind="mouse", problem="lantern", name="Bram"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show compatible_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show compatible_story/4."))
        combos = sorted(set(asp.atoms(model, "compatible_story")))
        for combo in combos:
            print(combo)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
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

    for idx, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.hero_kind} in {p.place} with {p.helper_kind} ({p.problem})"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
