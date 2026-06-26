#!/usr/bin/env python3
"""
storyworlds/worlds/canadian_squeamish_problem_solving_kindness_happy_ending.py
===============================================================================

A myth-flavored storyworld about a squeamish Canadian child, a small northern
problem, and a kind solution that leaves everyone happier than before.

Seed tale:
---
Long ago, by a cold silver lake, a small Canadian child named Rowan lived near
a cedar dock and a lantern shrine. One foggy morning, a river otter spirit
carried a cradle-shell full of lost sparks to the wrong side of the stream, and
the village's warm lantern began to dim. Rowan was squeamish about cold mud,
slimy reeds, and anything that wriggled, but Rowan still wanted to help.

Rowan watched the stream, noticed a fallen branch, tied on dry mittens, and
carefully made a little path of stones. The otter spirit was kind in return,
nudging the shell closer with its nose. Together they lifted the sparks back to
the shrine, the lantern glowed bright, and the whole lake looked golden again.

Causal state updates:
---
    problem noticed                -> desire for repair + attention to threat
    squeamish contact              -> discomfort + retreat impulse
    careful planning               -> confidence + progress
    kind help offered/accepted     -> gratitude + trust
    solved problem                 -> relief + joy + ending image
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
    kind: str = "thing"   # character | thing | spirit | place
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the lake shore"
    weather: str = "foggy"


@dataclass
class Problem:
    id: str
    source: str
    obstruction: str
    need: str
    risk: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Solution:
    id: str
    tool: str
    action: str
    effect: str
    finish: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[str] = set()
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


@dataclass
class StoryParams:
    place: str
    problem: str
    solution: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


PLACES = {
    "lake": Setting(place="the silver lake", weather="foggy"),
    "river": Setting(place="the cedar riverbank", weather="misty"),
    "shore": Setting(place="the northern shore", weather="windy"),
}

PROBLEMS = {
    "spark": Problem(
        id="spark",
        source="lantern shrine",
        obstruction="a cradle-shell of lost sparks drifted across the stream",
        need="the shrine needed its light back",
        risk="the cold water made the path slippery and the reeds were slimy",
        keyword="lantern",
        tags={"water", "light", "spirit"},
    ),
    "bridge": Problem(
        id="bridge",
        source="old rope bridge",
        obstruction="the old rope bridge had sagged into the creek",
        need="the far path had to be crossed safely",
        risk="the ropes looked damp and wobbly",
        keyword="bridge",
        tags={"water", "repair"},
    ),
    "bread": Problem(
        id="bread",
        source="winter bakery",
        obstruction="a basket of warm maple bread had fallen near the docks",
        need="the villagers needed the bread before it cooled",
        risk="the dock boards were muddy and scattered with wet leaves",
        keyword="bread",
        tags={"food", "kindness"},
    ),
}

SOLUTIONS = {
    "stones": Solution(
        id="stones",
        tool="a line of flat stones",
        action="placed the stones one by one",
        effect="made a dry path across the wet ground",
        finish="walked back and forth until the path was steady",
        tags={"water", "repair"},
    ),
    "mittens": Solution(
        id="mittens",
        tool="dry wool mittens",
        action="pulled on the mittens first",
        effect="kept the cold, slimy feeling away",
        finish="held the shell gently without squeamish flinching",
        tags={"water", "light", "kindness"},
    ),
    "branch": Solution(
        id="branch",
        tool="a long cedar branch",
        action="used the branch like a careful hook",
        effect="nudged the heavy thing closer without breaking it",
        finish="lifted it free with patient hands",
        tags={"repair", "kindness"},
    ),
}

NAMES = ["Rowan", "Mira", "Iris", "Kai", "June", "Eden", "Niko", "Sage"]
TRAITS = ["kind", "brave", "gentle", "patient", "thoughtful", "steady"]
GENDERS = ["girl", "boy"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A mythic storyworld about squeamish kindness and problem solving.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--solution", choices=SOLUTIONS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=GENDERS)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--trait", choices=TRAITS)
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place in PLACES:
        for problem in PROBLEMS:
            for solution in SOLUTIONS:
                if _compatible(problem, solution):
                    combos.append((place, problem, solution))
    return combos


def _compatible(problem_id: str, solution_id: str) -> bool:
    p = PROBLEMS[problem_id]
    s = SOLUTIONS[solution_id]
    return bool(p.tags & s.tags) or problem_id == "bread" and solution_id in {"branch", "stones"}


def explain_rejection(problem_id: str, solution_id: str) -> str:
    p, s = PROBLEMS[problem_id], SOLUTIONS[solution_id]
    return f"(No story: {s.tool} does not truly solve the problem of {p.obstruction}.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.problem and args.solution and not _compatible(args.problem, args.solution):
        raise StoryError(explain_rejection(args.problem, args.solution))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.problem is None or c[1] == args.problem)
              and (args.solution is None or c[2] == args.solution)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, problem, solution = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(GENDERS)
    name = args.name or rng.choice(NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, problem=problem, solution=solution, name=name, gender=gender, parent=parent, trait=trait)


def make_world(params: StoryParams) -> World:
    world = World(PLACES[params.place])
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender, meters={}, memes={"squeamish": 1.0, "kindness": 1.0}))
    parent = world.add(Entity(id="parent", kind="character", type=params.parent, label=f"the {params.parent}", meters={}, memes={"worry": 1.0}))
    problem = PROBLEMS[params.problem]
    solution = SOLUTIONS[params.solution]
    helper = world.add(Entity(id="otter", kind="spirit", type="otter spirit", label="the river otter spirit", meters={}, memes={"gratitude": 1.0, "kindness": 1.0}))
    world.facts.update(hero=hero, parent=parent, problem=problem, solution=solution, helper=helper)
    return world


def _begin(world: World, hero: Entity, parent: Entity, problem: Problem) -> None:
    world.say(f"Long ago, {hero.id} was a {world.facts['params'].trait} Canadian child who lived near {world.setting.place}.")
    world.say(f"{hero.pronoun().capitalize()} was kind, but also squeamish about cold mud, slimy reeds, and anything that wriggled.")
    world.say(f"One morning, {problem.obstruction}, and that meant {problem.need}.")


def _middle(world: World, hero: Entity, helper: Entity, problem: Problem, solution: Solution) -> None:
    hero.memes["squeamish"] += 1.0
    world.say(f"{hero.id} peered at the water and wrinkled {hero.pronoun('possessive')} nose at the damp reeds.")
    world.say(f"Still, {hero.id} looked closely, noticed {solution.tool}, and chose a careful plan.")
    world.say(f"{hero.id} {solution.action}, and the kind river otter spirit {solution.effect}.")
    world.say(f"Together they worked softly: {hero.id} stayed gentle, and the otter spirit nudged with its nose instead of pushing hard.")


def _end(world: World, hero: Entity, parent: Entity, problem: Problem, solution: Solution) -> None:
    world.say(f"In the end, the problem was solved because {hero.id} did not ignore the worry; {hero.id} answered it with kindness and thought.")
    world.say(f"The lost light returned / the path opened / the bread was saved, and the lake looked gold in the fog.")


def tell_story(params: StoryParams) -> World:
    world = make_world(params)
    world.facts["params"] = params
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    parent: Entity = world.facts["parent"]  # type: ignore[assignment]
    helper: Entity = world.facts["helper"]  # type: ignore[assignment]
    problem: Problem = world.facts["problem"]  # type: ignore[assignment]
    solution: Solution = world.facts["solution"]  # type: ignore[assignment]

    _begin(world, hero, parent, problem)
    world.para()
    _middle(world, hero, helper, problem, solution)
    world.para()
    if params.problem == "spark":
        world.say("The lantern shrine brightened again, and its little sparks climbed home like fireflies.")
    elif params.problem == "bridge":
        world.say("The path became safe, and the far bank welcomed them like an old friend.")
    else:
        world.say("The bread stayed warm, and every hungry face smiled as if a star had touched the basket.")
    world.say(f"{hero.id} felt relief bloom in {hero.pronoun('possessive')} chest, and the whole place seemed kinder than before.")
    _end(world, hero, parent, problem, solution)
    return world


def generation_prompts(world: World) -> list[str]:
    p: StoryParams = world.facts["params"]  # type: ignore[assignment]
    prob: Problem = world.facts["problem"]  # type: ignore[assignment]
    return [
        f"Write a short mythic story about a Canadian child named {p.name} who is squeamish but kind.",
        f"Tell a gentle problem-solving tale where {p.name} faces {prob.obstruction} and finds a way to help.",
        "Write a happy-ending story with cold northern air, careful hands, and a kind solution.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p: StoryParams = world.facts["params"]  # type: ignore[assignment]
    prob: Problem = world.facts["problem"]  # type: ignore[assignment]
    sol: Solution = world.facts["solution"]  # type: ignore[assignment]
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    return [
        QAItem(question=f"Who was the story about?", answer=f"It was about {p.name}, a {p.trait} Canadian child who was squeamish but kind."),
        QAItem(question=f"What problem had to be solved?", answer=f"The problem was that {prob.obstruction}, so {prob.need}."),
        QAItem(question=f"How was the problem solved?", answer=f"{p.name} used {sol.tool}, made a careful plan, and solved it kindly."),
        QAItem(question=f"How did {p.name} feel at the end?", answer=f"{p.name} felt relief and joy because the ending was happy and the danger was gone."),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What does squeamish mean?", answer="Squeamish means someone feels uneasy about messy, slimy, or unpleasant things."),
        QAItem(question="What is kindness?", answer="Kindness is being gentle and helpful to someone else."),
        QAItem(question="What is problem solving?", answer="Problem solving means noticing a difficulty and finding a smart way to fix it."),
        QAItem(question="What makes a happy ending?", answer="A happy ending is when the trouble is solved and things turn out well."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
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
        print("\n--- trace ---")
        for line in sample.world.trace:
            print(line)
    if qa:
        print()
        print(format_qa(sample))


ASP_RULES = r"""
problem(P) :- problem_id(P).
solution(S) :- solution_id(S).
compatible(P,S) :- problem(P), solution(S), shares_tag(P,S).
happy(P,S) :- compatible(P,S).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for pid, p in PROBLEMS.items():
        lines.append(asp.fact("problem_id", pid))
        for t in sorted(p.tags):
            lines.append(asp.fact("problem_tag", pid, t))
    for sid, s in SOLUTIONS.items():
        lines.append(asp.fact("solution_id", sid))
        for t in sorted(s.tags):
            lines.append(asp.fact("solution_tag", sid, t))
    for pid, p in PROBLEMS.items():
        for sid, s in SOLUTIONS.items():
            for t in sorted(p.tags & s.tags):
                lines.append(asp.fact("shares_tag", pid, sid, t))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show compatible/2."))
    return sorted(set(asp.atoms(model, "compatible")))


def asp_verify() -> int:
    py = {(p, s) for _, p, s in valid_combos()}
    asps = set(asp_valid_combos())
    if py == asps:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("python only:", sorted(py - asps))
    print("clingo only:", sorted(asps - py))
    return 1


CURATED = [
    StoryParams(place="lake", problem="spark", solution="mittens", name="Rowan", gender="boy", parent="mother", trait="kind"),
    StoryParams(place="river", problem="bridge", solution="stones", name="Mira", gender="girl", parent="father", trait="patient"),
    StoryParams(place="shore", problem="bread", solution="branch", name="Iris", gender="girl", parent="mother", trait="gentle"),
]


def asp_facts_program() -> str:
    return asp_program("#show compatible/2.")


def build_story_combos(args: argparse.Namespace, rng: random.Random) -> list[tuple[str, str, str]]:
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.problem is None or c[1] == args.problem)
              and (args.solution is None or c[2] == args.solution)]
    return combos


def valid_story_combo(place: str, problem: str, solution: str) -> bool:
    return (place in PLACES) and _compatible(problem, solution)


def resolve_story(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = build_story_combos(args, rng)
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, problem, solution = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(GENDERS)
    name = args.name or rng.choice(NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, problem=problem, solution=solution, name=name, gender=gender, parent=parent, trait=trait)


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show compatible/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show compatible/2."))
        print(f"{len(asp_valid_combos())} compatible problem/solution pairs:\n")
        for a, b in asp.atoms(model, "compatible"):
            print(f"  {a:10} {b}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            params = resolve_story(args, random.Random(seed))
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
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.problem} via {p.solution} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
