#!/usr/bin/env python3
"""
A tiny pirate-tale world about solving a problem beneath a leaky glass dome.
"""

from __future__ import annotations

# Locate the shared StoryWorld helpers from any batch depth.
from pathlib import Path as _StoryPath
import sys as _StorySys
_storyworlds_root = next(parent for parent in _StoryPath(__file__).resolve().parents
                        if (parent / 'results.py').is_file() and (parent / 'asp.py').is_file())
_StorySys.path.insert(0, str(_storyworlds_root.parent))
_StorySys.path.insert(0, str(_storyworlds_root))


import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field

_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    _storyworlds_dir = os.path.dirname(_storyworlds_dir)
sys.path.insert(0, _storyworlds_dir)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass(frozen=True)
class Dome:
    id: str
    label: str
    place: str
    material: str
    leak: str
    purpose: str


@dataclass(frozen=True)
class Problem:
    id: str
    title: str
    clue: str
    first_idea: str
    solution: str
    result: str
    lesson: str


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    dome: Dome
    problem: Problem
    hero: Entity
    helper: Entity
    entities: list[Entity]
    facts: dict[str, object] = field(default_factory=dict)

    def render(self) -> str:
        f = self.facts
        return "\n\n".join(
            [
                str(f["opening"]),
                str(f["discovery"]),
                str(f["exchange"]),
                str(f["clue"]),
                str(f["solution_scene"]),
                str(f["ending"]),
            ]
        )


DOMES = {
    "star_dome": Dome(
        "star_dome",
        "the Star-Shell Dome",
        "Treasure Island's old observatory",
        "green glass and brass",
        "a thin stream of rainwater",
        "keeping the captain's star maps dry",
    ),
    "moon_dome": Dome(
        "moon_dome",
        "the Moonlight Dome",
        "a rocky cove above the sea",
        "silver glass and cedar",
        "a drip beside the northern window",
        "showing sailors the moon's path",
    ),
    "coral_dome": Dome(
        "coral_dome",
        "the Coral Dome",
        "a little island harbor",
        "blue glass and copper",
        "salt water slipping through a seam",
        "protecting the harbor's signal lantern",
    ),
}

PROBLEMS = {
    "blocked_gutter": Problem(
        "blocked_gutter",
        "the blocked gutter",
        "A palm leaf was wedged above the brass gutter, so rain had nowhere to go.",
        "Captain Luna wanted to climb straight up and tug the leaf free.",
        "Luna used a boat hook from the dry walkway while Finn held the lantern and watched the footing.",
        "The leaf came loose, the gutter carried the rain away, and the maps stayed dry.",
        "A clever sailor checks the cause before choosing the quickest-looking fix.",
    ),
    "loose_panel": Problem(
        "loose_panel",
        "the loose glass panel",
        "One copper pin had slipped from a window frame, leaving a narrow gap.",
        "Luna planned to stuff a treasure rag into the gap and sail on.",
        "She marked the spot, fetched a spare pin, and asked the shipwright to fasten the panel from the safe side.",
        "The panel held firm while the wind sang harmlessly over the dome.",
        "A temporary cover is useful, but a lasting repair solves the real problem.",
    ),
    "fogged_lens": Problem(
        "fogged_lens",
        "the fogged lookout lens",
        "Warm sea air had clouded the lens that guided ships toward the harbor.",
        "Luna almost polished it with a rough sailcloth.",
        "She tested a corner with a soft clean cloth, opened the vent, and waited for the glass to clear.",
        "The harbor light shone sharply again, and every ship could read the safe channel.",
        "Good problem solving uses gentle tests instead of hurried guesses.",
    ),
}

HEROES = ["Luna", "Marin", "Pip", "Tessa"]
HELPERS = ["Finn", "Old Mira", "Boatswain Jo", "Aunt Coral"]

OPENINGS = [
    "{hero} sailed before sunrise to inspect {dome}.",
    "The sea was quiet when {hero} climbed the hill toward {dome}.",
    "At dawn, {hero} heard the rigging bell ring beside {dome}.",
    "{hero} had promised to protect the harbor maps beneath {dome}.",
]


@dataclass
class StoryParams:
    dome: str
    problem: str
    name: str
    helper: str
    seed: int | None = None


def reasonability_gate(dome: Dome, problem: Problem) -> bool:
    return bool(dome.purpose and problem.clue and problem.solution)


def valid_combos() -> list[tuple[str, str]]:
    return [
        (dome_id, problem_id)
        for dome_id, dome in DOMES.items()
        for problem_id, problem in PROBLEMS.items()
        if reasonability_gate(dome, problem)
    ]


def build_world(params: StoryParams) -> World:
    if params.dome not in DOMES:
        raise StoryError(f"Unknown dome: {params.dome}")
    if params.problem not in PROBLEMS:
        raise StoryError(f"Unknown problem: {params.problem}")
    dome = DOMES[params.dome]
    problem = PROBLEMS[params.problem]
    hero = Entity(params.name, "pirate", params.name)
    helper = Entity(params.helper, "helper", params.helper)
    hero.meters["distance_to_dome"] = 0.0
    hero.memes["curiosity"] = 1.0
    helper.memes["trust"] = 1.0

    opening = random.Random(params.seed).choice(OPENINGS).format(hero=hero.label, dome=dome.label)
    discovery = (
        f"Inside {dome.label}, {hero.label} found trouble: {problem.title}. "
        f"{problem.clue} The dome's job was {dome.purpose}, but the {dome.leak} threatened to spoil that work."
    )
    exchange = (
        f'"I can fix it in one leap," said {hero.label}. '
        f'"First tell me what is making the trouble," said {helper.label}. '
        f'"Then we can choose a safe tool." {hero.label} lowered the rope and listened.'
    )
    clue = f"The clue was clear: {problem.clue} {hero.label} pointed to it and said, \"Now we know where to begin.\""
    solution_scene = (
        f"{problem.solution} {helper.label} called, \"Slow hands, sharp eyes!\" "
        f"{hero.label} answered, \"Aye, and we will test the repair before we cheer.\" "
        f"Together they checked the frame, the walkway, and the flow of water."
    )
    ending = (
        f"{problem.result} A bright patch of sea appeared through the clean {dome.material}, "
        f"and the pirate flag below snapped proudly in the wind. "
        f"The lesson of the story was simple: {problem.lesson}"
    )
    world = World(dome, problem, hero, helper, [hero, helper])
    world.facts.update(
        opening=opening,
        discovery=discovery,
        exchange=exchange,
        clue=clue,
        solution_scene=solution_scene,
        ending=ending,
        resolved=True,
        safe_tool=True,
    )
    hero.meters["distance_to_dome"] = 1.0
    hero.memes["confidence"] = 1.0
    helper.memes["trust"] = 2.0
    return world


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    dome = world.dome
    problem = world.problem
    return StorySample(
        params=params,
        story=world.render(),
        prompts=[
            f"Write a pirate tale about {params.name} solving {problem.title} beneath {dome.label}.",
            f"Tell a problem-solving story in which a clue changes {params.name}'s plan.",
            f"Write a child-friendly story ending with the dome safe and useful again.",
        ],
        story_qa=[
            QAItem(f"What problem did {params.name} find?", f"{params.name} found {problem.title}."),
            QAItem("What clue explained the trouble?", problem.clue),
            QAItem(f"How did {params.name} solve it?", problem.solution),
            QAItem("What changed at the end?", problem.result),
            QAItem("What lesson did the story teach?", problem.lesson),
        ],
        world_qa=[
            QAItem("What is a dome?", "A dome is a rounded roof or building cover that can protect a space below it."),
            QAItem("Why is a clue useful when solving a problem?", "A clue gives information about the cause, helping someone choose a sensible solution."),
            QAItem("Why should pirates test a repair?", "Testing shows whether the repair is safe and actually fixes the problem."),
        ],
        world=world,
    )


ASP_RULES = r"""
usable_dome(D) :- dome(D), protects(D).
solvable(P) :- problem(P), has_clue(P), has_solution(P).
valid(D,P) :- usable_dome(D), solvable(P).
#show valid/2.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for dome_id, dome in DOMES.items():
        lines += [
            asp.fact("dome", dome_id),
            asp.fact("protects", dome_id),
        ]
    for problem_id, problem in PROBLEMS.items():
        lines += [
            asp.fact("problem", problem_id),
            asp.fact("has_clue", problem_id),
            asp.fact("has_solution", problem_id),
        ]
    return "\n".join(lines)


def asp_program() -> str:
    return asp_facts() + "\n" + ASP_RULES


def asp_verify() -> int:
    import asp
    python = set(valid_combos())
    model = asp.one_model(asp_program())
    clingo = set(asp.atoms(model, "valid"))
    if python == clingo:
        print(f"OK: ASP matches Python ({len(python)} combinations).")
        return 0
    print("Mismatch between ASP and Python.")
    print("Python only:", sorted(python - clingo))
    print("ASP only:", sorted(clingo - python))
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A pirate problem-solving dome storyworld.")
    parser.add_argument("--dome", choices=DOMES)
    parser.add_argument("--problem", choices=PROBLEMS)
    parser.add_argument("--name", choices=HEROES)
    parser.add_argument("--helper", choices=HELPERS)
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [
        pair for pair in valid_combos()
        if not args.dome or pair[0] == args.dome
        if not args.problem or pair[1] == args.problem
    ]
    if not combos:
        raise StoryError("No valid dome and problem combination matches the request.")
    dome, problem = rng.choice(combos)
    return StoryParams(
        dome=dome,
        problem=problem,
        name=args.name or rng.choice(HEROES),
        helper=args.helper or rng.choice(HELPERS),
    )


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(f"- {prompt}" for prompt in sample.prompts)
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    lines.append(f"  dome: {world.dome.id} material={world.dome.material}")
    lines.append(f"  problem: {world.problem.id} resolved={world.facts['resolved']}")
    for entity in world.entities:
        lines.append(f"  {entity.id}: meters={entity.meters} memes={entity.memes}")
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program())
        for item in sorted(set(asp.atoms(model, "valid"))):
            print(item)
        return

    seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    if args.all:
        for index, (dome, problem) in enumerate(valid_combos()):
            params = StoryParams(
                dome=dome,
                problem=problem,
                name=HEROES[index % len(HEROES)],
                helper=HELPERS[index % len(HELPERS)],
                seed=seed + index,
            )
            samples.append(generate(params))
    else:
        for index in range(args.n):
            params = resolve_params(args, random.Random(seed + index))
            params.seed = seed + index
            samples.append(generate(params))

    if args.json:
        payload = samples[0].to_dict() if len(samples) == 1 else [sample.to_dict() for sample in samples]
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {index + 1}" if len(samples) > 1 else "")
        if index + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
