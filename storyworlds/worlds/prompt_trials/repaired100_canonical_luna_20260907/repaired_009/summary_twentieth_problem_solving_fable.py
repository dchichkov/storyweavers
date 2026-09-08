#!/usr/bin/env python3
"""
A small fable storyworld about problem solving and a twentieth seed.
Luna learns that a summary can point to a problem, but careful questions and
shared work are what solve it.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    _storyworlds_dir = os.path.dirname(_storyworlds_dir)
sys.path.insert(0, _storyworlds_dir)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    label: str
    kind: str = "thing"
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass(frozen=True)
class Problem:
    id: str
    obstacle: str
    clue: str
    tool: str
    action: str
    result: str
    lesson: str


@dataclass
class World:
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


PLACES = {
    "orchard": "the quiet orchard",
    "meadow": "the sunny meadow",
    "hill": "the green hill",
}

PROBLEMS = {
    "bridge": Problem(
        "bridge",
        "the little footbridge had lost two wooden planks",
        "the missing planks lay beside the stream",
        "a coil of vine and three straight branches",
        "measure the gap, lash the branches together, and test them gently",
        "the rabbits crossed safely to gather clover",
        "A careful measure is stronger than a hasty guess.",
    ),
    "well": Problem(
        "well",
        "the village well had a bucket stuck deep below",
        "the rope was frayed just above the water",
        "a spare rope and a sturdy hook",
        "tie the new rope to the hook and lower it slowly",
        "the bucket rose full of cool water",
        "A patient plan can lift what hurried hands cannot.",
    ),
    "beehive": Problem(
        "beehive",
        "a fallen branch blocked the bees' path to their hive",
        "a narrow path remained under the branch",
        "smooth stones and a long forked stick",
        "mark the safe path and roll the branch away from the hive",
        "the bees returned without a single frightened buzz",
        "A good solution protects the smallest neighbor.",
    ),
    "cart": Problem(
        "cart",
        "the farmer's cart wheel had sunk into soft mud",
        "flat stones rested beneath the nearby fern",
        "a shovel and the flat stones",
        "dig around the wheel and build a firm road beneath it",
        "the cart rolled free with its apples still safe",
        "A problem grows smaller when its pieces are noticed.",
    ),
}

NAMES = ["Luna", "Pip", "Mara", "Sol", "Tavi"]
HELPERS = ["the patient tortoise", "the bright fox", "the old crow", "the gentle deer"]
TRAITS = ["curious", "steady", "kind", "clever"]
OPENINGS = [
    "Luna was the {trait} keeper of {place}, where every bird and beetle had a place to rest.",
    "In {place}, Luna carried a little notebook and listened whenever the creatures needed help.",
    "The animals of {place} trusted Luna because she never called a puzzle impossible.",
    "On the morning of the twentieth gathering, Luna walked through {place} with her helper nearby.",
]
TURNS = [
    "Luna did not pull at the trouble at once. She asked, “What do we know, and what should we check next?”",
    "The helper shook their head. “A summary tells us the trouble,” they said, “but it does not yet tell us the best answer.”",
    "Luna studied the ground, the tools, and the worried faces. “Let us solve one small part at a time,” she said.",
    "They made a short summary together, then tested its clue instead of trusting a guess.",
]
ENDINGS = [
    "When the work was done, Luna wrote a new summary: problem, clue, plan, and result. The twentieth gathering ended with thankful smiles.",
    "That evening, the creatures placed a smooth gold leaf beside Luna's notebook. It marked the twentieth problem solved by patient thinking.",
    "The helper smiled. “Your summary is useful now,” they said. Luna nodded, because the living proof was all around them.",
    "At sunset, the path was safe again, and Luna's twentieth lesson traveled from one small animal to another.",
]


@dataclass
class StoryParams:
    place: str
    problem: str
    name: str
    helper: str
    trait: str
    opening: int = 0
    turn: int = 0
    ending: int = 0
    seed: Optional[int] = None


ASP_RULES = r"""
solvable(P) :- problem(P), has_clue(P), has_tool(P), has_action(P).
valid_story(S, P) :- setting(S), problem(P), affords(S, P), solvable(P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in PLACES:
        lines.append(asp.fact("setting", sid))
        for pid in PROBLEMS:
            lines.append(asp.fact("affords", sid, pid))
    for pid, problem in PROBLEMS.items():
        lines.extend([
            asp.fact("problem", pid),
            asp.fact("has_clue", pid),
            asp.fact("has_tool", pid),
            asp.fact("has_action", pid),
        ])
    return "\n".join(lines)


def asp_program(show: str = "#show valid_story/2.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str]]:
    return [(place, problem) for place in PLACES for problem in PROBLEMS]


def asp_valid() -> set[tuple[str, str]]:
    import asp
    model = asp.one_model(asp_program())
    return set(asp.atoms(model, "valid_story"))


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if args.place:
        combos = [pair for pair in combos if pair[0] == args.place]
    if args.problem:
        combos = [pair for pair in combos if pair[1] == args.problem]
    if not combos:
        raise StoryError("No setting and problem combination matches the requested choices.")
    place, problem = rng.choice(combos)
    return StoryParams(
        place=place,
        problem=problem,
        name=args.name or rng.choice(NAMES),
        helper=args.helper or rng.choice(HELPERS),
        trait=args.trait or rng.choice(TRAITS),
        opening=rng.randrange(len(OPENINGS)),
        turn=rng.randrange(len(TURNS)),
        ending=rng.randrange(len(ENDINGS)),
    )


def build_world(params: StoryParams) -> World:
    if params.place not in PLACES:
        raise StoryError(f"Unknown place: {params.place}")
    if params.problem not in PROBLEMS:
        raise StoryError(f"Unknown problem: {params.problem}")

    problem = PROBLEMS[params.problem]
    world = World(PLACES[params.place])
    luna = world.add(Entity(params.name, params.name, "character", memes={"curiosity": 1.0}))
    helper = world.add(Entity("helper", params.helper, "character", memes={"trust": 1.0}))
    obstacle = world.add(Entity("obstacle", problem.obstacle, "obstacle", meters={"difficulty": 1.0}))
    world.facts.update(luna=luna, helper=helper, obstacle=obstacle, problem=problem)

    values = {
        "name": params.name,
        "place": world.place,
        "trait": params.trait,
        "helper": params.helper,
        "summary": "problem, clue, plan, and result",
    }
    world.say(OPENINGS[params.opening % len(OPENINGS)].format(**values))
    world.say(f"It was the twentieth puzzle on Luna's list, and {problem.obstacle}.")
    world.para()

    world.say(f"{params.helper.capitalize()} pointed toward the trouble. “The summary says what happened,” they said, “but which clue can help us?”")
    world.say(f"Luna answered, “We will look closely before we choose.” She discovered that {problem.clue}.")
    world.para()

    world.say(TURNS[params.turn % len(TURNS)])
    world.say(f"Together, Luna and {params.helper} used {problem.tool} to {problem.action}.")
    obstacle.meters["difficulty"] = 0.0
    luna.memes["confidence"] = 1.0
    helper.memes["pride"] = 1.0
    world.say(f"The plan worked: {problem.result}.")
    world.para()

    world.say(ENDINGS[params.ending % len(ENDINGS)])
    world.say(f"The wise old crow added, “{problem.lesson}”")
    return world


def prompts(world: World) -> list[str]:
    problem: Problem = world.facts["problem"]  # type: ignore[assignment]
    return [
        f"Write a fable about Luna solving a problem in {world.place}.",
        f"Tell a child-friendly story whose summary includes {problem.obstacle}, a clue, a plan, and a result.",
        "Write a fable about careful problem solving and the twentieth lesson.",
    ]


def story_qa(world: World) -> list[QAItem]:
    problem: Problem = world.facts["problem"]  # type: ignore[assignment]
    luna: Entity = world.facts["luna"]  # type: ignore[assignment]
    helper: Entity = world.facts["helper"]  # type: ignore[assignment]
    return [
        QAItem("What problem did Luna need to solve?", f"Luna needed to solve this problem: {problem.obstacle}."),
        QAItem("What clue did Luna discover?", f"Luna discovered that {problem.clue}."),
        QAItem(
            "How did Luna and her helper solve it?",
            f"They used {problem.tool} to {problem.action}, and then {problem.result}.",
        ),
        QAItem(
            "What did the twentieth problem teach Luna?",
            f"It taught Luna that {problem.lesson.lower()}",
        ),
        QAItem(
            "Who helped Luna?",
            f"{helper.label.capitalize()} helped {luna.label} by asking questions and working beside her.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What is a summary?",
            "A summary is a short account of the most important parts of something.",
        ),
        QAItem(
            "What is problem solving?",
            "Problem solving means noticing a difficulty, finding useful information, choosing a plan, and checking whether the plan works.",
        ),
        QAItem(
            "What is a fable?",
            "A fable is a short story, often with talking animals, that teaches a lesson.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    sections = ["== prompts =="]
    sections.extend(sample.prompts)
    sections.append("")
    sections.append("== story qa ==")
    for item in sample.story_qa:
        sections.append(f"Q: {item.question}")
        sections.append(f"A: {item.answer}")
    sections.append("")
    sections.append("== world qa ==")
    for item in sample.world_qa:
        sections.append(f"Q: {item.question}")
        sections.append(f"A: {item.answer}")
    return "\n".join(sections)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for entity in world.entities.values():
        meters = {key: value for key, value in entity.meters.items() if value}
        memes = {key: value for key, value in entity.memes.items() if value}
        lines.append(f"{entity.id}: meters={meters} memes={memes}")
    return "\n".join(lines)


def emit(sample: StorySample, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A fable storyworld about Luna, summaries, and problem solving.")
    parser.add_argument("--place", choices=sorted(PLACES))
    parser.add_argument("--problem", choices=sorted(PROBLEMS))
    parser.add_argument("--name")
    parser.add_argument("--helper", choices=HELPERS)
    parser.add_argument("--trait", choices=TRAITS)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--seed", type=int)
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def asp_verify() -> int:
    python_pairs = set(valid_combos())
    asp_pairs = asp_valid()
    if python_pairs != asp_pairs:
        print("Mismatch between ASP and Python.")
        print("Only Python:", sorted(python_pairs - asp_pairs))
        print("Only ASP:", sorted(asp_pairs - python_pairs))
        return 1
    for params in [
        StoryParams("orchard", "bridge", "Luna", "the patient tortoise", "curious"),
        StoryParams("meadow", "beehive", "Pip", "the old crow", "kind"),
    ]:
        sample = generate(params)
        if not sample.story or "twentieth" not in sample.story:
            print("Generated-story verification failed.")
            return 1
    print(f"OK: ASP and Python agree on {len(python_pairs)} valid combinations; stories pass.")
    return 0


CURATED = [
    StoryParams("orchard", "bridge", "Luna", "the patient tortoise", "curious", 0, 0, 0),
    StoryParams("meadow", "beehive", "Pip", "the old crow", "kind", 1, 1, 1),
    StoryParams("hill", "cart", "Mara", "the bright fox", "steady", 2, 2, 2),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp or args.asp:
        print(asp_program())
        return
    if args.verify:
        raise SystemExit(asp_verify())

    seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        samples = []
        seen: set[str] = set()
        for index in range(max(1, args.n)):
            params = resolve_params(args, random.Random(seed + index))
            params.seed = seed + index
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        emit(
            sample,
            trace=args.trace,
            qa=args.qa,
            header=f"### variant {index + 1}" if len(samples) > 1 else "",
        )
        if index + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
