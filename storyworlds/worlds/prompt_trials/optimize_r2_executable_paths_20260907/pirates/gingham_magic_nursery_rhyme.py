#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from pathlib import Path as _StoryPath
_storyworlds_root = next(parent for parent in _StoryPath(__file__).resolve().parents
                        if (parent / 'results.py').is_file() and (parent / 'asp.py').is_file())
sys.path.insert(0, str(_storyworlds_root))
from results import QAItem, StoryError, StorySample


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))


@dataclass(frozen=True)
class Problem:
    id: str
    trouble: str
    clue: str
    object_label: str
    object_phrase: str


@dataclass(frozen=True)
class Solution:
    id: str
    need: str
    actions: tuple[str, ...]
    change: str
    ending: str
    method_label: str


@dataclass(frozen=True)
class Path:
    id: str
    problem: str
    solution: str


@dataclass
class StoryParams:
    problem: str
    solution: str
    child: str
    helper: str
    path: str = ""
    seed: int | None = None


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.history: list[str] = []

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        self.paragraphs[-1].append(text)
        self.history.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


PROBLEMS = {
    "tear": Problem(
        "tear",
        "a tear opened in the gingham moon",
        "a silver needle can stitch moonlight",
        "moon",
        "the gingham moon",
    ),
    "sleep": Problem(
        "sleep",
        "the baby star could not fall asleep",
        "a soft rhyme and a blue bell can make dreams",
        "star",
        "the baby star",
    ),
    "rain": Problem(
        "rain",
        "a rain cloud forgot how to sprinkle",
        "a red ribbon can guide its drops",
        "cloud",
        "the rain cloud",
    ),
    "song": Problem(
        "song",
        "the nursery rhyme lost its last line",
        "a golden thimble can catch a missing word",
        "rhyme",
        "the nursery rhyme",
    ),
}

SOLUTIONS = {
    "needle": Solution(
        "needle",
        "the silver needle and a careful counting spell",
        ("find the silver needle", "count three moon stitches", "tie a gingham knot"),
        "the tear is sewn shut",
        "the moon shines whole above the nursery",
        "the silver needle",
    ),
    "ribbon": Solution(
        "ribbon",
        "the red ribbon and a dancing rhyme",
        ("find the red ribbon", "twirl it in a circle", "sing the rain rhyme"),
        "the cloud remembers its rhythm",
        "rain taps softly on the window",
        "the red ribbon",
    ),
    "bell": Solution(
        "bell",
        "the blue bell and a lullaby",
        ("find the blue bell", "ring three quiet notes", "whisper the lullaby"),
        "the star's sleepy glow returns",
        "the star hums above a peaceful crib",
        "the blue bell",
    ),
    "thimble": Solution(
        "thimble",
        "the golden thimble and a word-catching charm",
        ("find the golden thimble", "catch the wandering word", "place it at the rhyme's end"),
        "the missing line comes home",
        "the nursery rhyme skips brightly to its ending",
        "the golden thimble",
    ),
}

PATHS = {
    "tear_needle": Path("tear_needle", "tear", "needle"),
    "rain_ribbon": Path("rain_ribbon", "rain", "ribbon"),
    "sleep_bell": Path("sleep_bell", "sleep", "bell"),
    "song_thimble": Path("song_thimble", "song", "thimble"),
}

NAMES = ["Mina", "Pip", "Nell", "Toby", "Lulu", "Bram"]
HELPERS = ["Moon-Mouse", "Button-Bird", "Clover-Cat", "Dandelion-Duck"]


def valid_paths() -> list[Path]:
    return list(PATHS.values())


def resolve_path(problem: str | None, solution: str | None, rng: random.Random) -> Path:
    choices = [
        p for p in valid_paths()
        if (problem is None or p.problem == problem)
        and (solution is None or p.solution == solution)
    ]
    if not choices:
        raise StoryError("That problem and solution cannot travel together in this magic nursery.")
    return rng.choice(choices)


def build_world(params: StoryParams) -> World:
    path = PATHS[params.path]
    problem = PROBLEMS[path.problem]
    solution = SOLUTIONS[path.solution]
    world = World()

    child = world.add(Entity(params.child, "character", params.child))
    helper = world.add(Entity(params.helper, "character", params.helper))
    object_entity = world.add(Entity("object", "magical thing", problem.object_label))
    tool = world.add(Entity("tool", "magic tool", solution.method_label))

    child.memes["curiosity"] += 1
    helper.memes["wisdom"] += 1
    object_entity.meters["trouble"] += 1

    world.say(
        f"At bedtime, {params.child} wore a gingham cap and danced beside "
        f"the nursery moon. Magic winked in every button and spoon."
    )
    world.say(
        f'"A tiddle-dee, a tiddle-doo," sang {params.child}. '
        f'"What has gone wrong in our rhyme?"'
    )
    world.say(
        f"Then {params.helper} fluttered from a painted teacup. "
        f'"I know the trouble," said {params.helper}. '
        f'"{problem.trouble}; we need {solution.need}."'
    )
    world.para()
    world.say(
        f'{params.child} asked, "Will that truly help?" '
        f'{params.helper} replied, "Only if we follow the magic in the right order."'
    )
    world.say(
        f"Together they {solution.actions[0]}, then {solution.actions[1]}, "
        f"and finally they {solution.actions[2]}."
    )

    object_entity.meters["trouble"] = 0
    object_entity.meters["restored"] += 1
    child.memes["confidence"] += 1
    helper.memes["joy"] += 1

    world.para()
    world.say(
        f"A tiny golden shimmer twirled around {problem.object_phrase}, and "
        f"{solution.change}. {solution.ending.capitalize()}."
    )
    world.say(
        f'"Magic works best with a careful heart," said {params.helper}. '
        f'"And a gingham rhyme helps us remember."'
    )
    world.say(
        f'{params.child} smiled. "Then I will help, not hurry, whenever a '
        f'nursery wonder needs me."'
    )
    world.say(
        f"Off they skipped: {params.child}, {params.helper}, and the magic "
        f"gingham sparkle, singing, \"Tiddle-tum, the work is done!\""
    )

    world.facts.update(
        path=path,
        problem=problem,
        solution=solution,
        child=child,
        helper=helper,
        object=object_entity,
        tool=tool,
        solved=True,
    )
    return world


def prompts(world: World) -> list[str]:
    p: Problem = world.facts["problem"]
    s: Solution = world.facts["solution"]
    child: Entity = world.facts["child"]
    helper: Entity = world.facts["helper"]
    return [
        f"Write a nursery rhyme about {child.id} solving {p.trouble} with Magic and gingham.",
        f"Tell a rhyming story where {helper.id} teaches {child.id} to use {s.method_label} in the correct order.",
        f"End with {p.object_phrase} restored and a gentle spoken lesson about careful magic.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p: Problem = world.facts["problem"]
    s: Solution = world.facts["solution"]
    child: Entity = world.facts["child"]
    helper: Entity = world.facts["helper"]
    return [
        QAItem(
            f"What trouble did {child.id} discover?",
            f"{child.id} discovered that {p.trouble}.",
        ),
        QAItem(
            f"Who helped {child.id} solve the nursery problem?",
            f"{helper.id} helped {child.id} by explaining that {s.need} was needed.",
        ),
        QAItem(
            f"What did {child.id} and {helper.id} do with {s.method_label}?",
            f"They {s.actions[0]}, then {s.actions[1]}, and finally they {s.actions[2]}.",
        ),
        QAItem(
            "How did the story end?",
            f"The problem was solved: {s.change}, and {s.ending}.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What is gingham?",
            "Gingham is a woven cloth with a simple checked pattern, often made in cheerful colors.",
        ),
        QAItem(
            "What is magic in a nursery rhyme?",
            "Magic in a nursery rhyme is an imaginative wonder that helps ordinary things act in a surprising way.",
        ),
        QAItem(
            "Why should a magic spell be followed carefully?",
            "Following a spell carefully helps each part happen in the right order and keeps the story's wonder gentle and safe.",
        ),
    ]


def generate(params: StoryParams) -> StorySample:
    if params.path not in PATHS:
        raise StoryError("Unknown story path.")
    expected = PATHS[params.path]
    if expected.problem != params.problem or expected.solution != params.solution:
        raise StoryError("The selected problem and solution do not match the advertised path.")
    world = build_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        lines.append(f"  {entity.id}: meters={meters} memes={memes}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    lines.append("\n== Story questions ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("\n== World knowledge ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


ASP_RULES = r"""
solvable(P,S) :- path(P,S).
restored(P,S) :- solvable(P,S).
"""


def asp_facts() -> str:
    import importlib
    asp = importlib.import_module("storyworlds.asp") if "storyworlds.asp" in sys.modules else importlib.import_module("asp")
    return "\n".join(asp.fact("path", p.problem, p.solution) for p in PATHS.values())


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Gingham Magic Nursery Rhyme storyworld")
    parser.add_argument("--problem", choices=PROBLEMS)
    parser.add_argument("--solution", choices=SOLUTIONS)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    path = resolve_path(args.problem, args.solution, rng)
    child = rng.choice(NAMES)
    helper = rng.choice([h for h in HELPERS if h != child])
    return StoryParams(
        problem=path.problem,
        solution=path.solution,
        path=path.id,
        child=child,
        helper=helper,
    )


def verify() -> int:
    for path in valid_paths():
        params = StoryParams(
            problem=path.problem,
            solution=path.solution,
            path=path.id,
            child="Mina",
            helper="Moon-Mouse",
        )
        sample = generate(params)
        if "gingham" not in sample.story.lower():
            return 1
        if "Magic" not in sample.story and "magic" not in sample.story:
            return 1
        if '"' not in sample.story:
            return 1
        if any("{" in text or "}" in text for text in [sample.story]):
            return 1
    print(f"OK: verified {len(valid_paths())} executable paths.")
    return 0


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_facts())
        print(ASP_RULES)
        return
    if args.verify:
        raise SystemExit(verify())
    if args.asp:
        print("compatible paths:")
        for path in valid_paths():
            print(f"  {path.id}: {path.problem} + {path.solution}")
        return

    seed = args.seed if args.seed is not None else random.randrange(2**31)
    rng = random.Random(seed)
    if args.all:
        samples = [
            generate(StoryParams(
                problem=p.problem,
                solution=p.solution,
                path=p.id,
                child="Mina",
                helper="Moon-Mouse",
                seed=seed,
            ))
            for p in valid_paths()
        ]
    else:
        samples = []
        for index in range(args.n):
            params = resolve_params(args, random.Random(seed + index))
            params.seed = seed + index
            samples.append(generate(params))

    if args.json:
        payload = samples[0].to_dict() if len(samples) == 1 else [s.to_dict() for s in samples]
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        if len(samples) > 1:
            print(f"### story {index + 1}\n")
        print(sample.story)
        if args.trace:
            print("\n" + dump_trace(sample.world))
        if args.qa:
            print("\n" + format_qa(sample))
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
