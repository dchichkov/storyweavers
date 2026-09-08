#!/usr/bin/env python3
"""
A small folk-tale story world about a vanished bridge, a clever repair, and
the sounds that guide a village home.
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
from typing import Optional

_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    _storyworlds_dir = os.path.dirname(_storyworlds_dir)
sys.path.insert(0, _storyworlds_dir)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "girl":
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.kind == "boy":
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass(frozen=True)
class Setting:
    id: str
    place: str
    affordances: tuple[str, ...]
    meters: tuple[str, ...]
    memes: tuple[str, ...]


@dataclass(frozen=True)
class Tool:
    id: str
    label: str
    purpose: str
    sound: str


@dataclass(frozen=True)
class Problem:
    id: str
    title: str
    warning: str
    clue: str
    fix: str
    result: str
    lesson: str
    sound: str


SETTINGS = {
    "bellwood": Setting(
        "bellwood",
        "Bellwood village beside the whispering river",
        ("listen", "inspect", "repair", "cross"),
        ("distance", "water_level"),
        ("courage", "patience"),
    ),
}

TOOLS = {
    "rope": Tool("rope", "a braided willow rope", "to draw a safe line across the river", "swish"),
    "bell": Tool("bell", "a little bronze bell", "to send a signal through the fog", "ting"),
    "pebbles": Tool("pebbles", "three smooth river pebbles", "to test the hidden stepping stones", "plip"),
}

PROBLEMS = [
    Problem(
        "fog_bridge",
        "the bridge that would not appear",
        "The river fog had swallowed the old bridge, and no one could see where its first plank rested.",
        "A robin flew low, then turned sharply at one patch of pale water.",
        "Mara tied the willow rope to an oak, listened for the echo of the bell, and placed pebbles where the water answered with a hollow plip.",
        "One by one, the hidden stones appeared beneath the lifting mist, making a safe path for the villagers.",
        "When sight is lost, patient listening can reveal the road.",
        "swish, ting, plip",
    ),
    Problem(
        "fallen_marker",
        "the crooked milestone",
        "A fallen marker had made two forest paths look exactly alike before the market began.",
        "Moss grew thickly on one side of the stone, showing which way had faced north.",
        "Toma rolled the stone back with a branch as a lever, then rang the bell so travelers could follow the true path.",
        "The marker stood straight again, and the bell's clear ting led every traveler toward the market.",
        "A careful clue can solve what a hurried guess makes worse.",
        "creak, thump, ting",
    ),
    Problem(
        "silent_well",
        "the well that lost its song",
        "The village well had stopped echoing, so the people feared its bucket had fallen deep below.",
        "A faint drip came from behind a loose stone, not from the dark center of the well.",
        "Lina moved the loose stone with a wooden spoon handle and tied the rope around the bucket before lifting.",
        "Water rose safely, and the old well began to sing again with a bright plip.",
        "A small sound may point toward a large answer.",
        "scrape, swish, plip",
    ),
]

NAMES = ["Luna", "Mara", "Toma", "Lina", "Niko"]
ROLES = ["goatherd", "baker's child", "woodcutter's child", "village helper"]
OPENINGS = [
    "Long ago, when the hills wore silver mist,",
    "In a valley where every tree had a name,",
    "One morning beneath a pearly sky,",
    "At the edge of an old green forest,",
]


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
    events: list[str] = field(default_factory=list)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity


@dataclass
class StoryParams:
    setting: str = "bellwood"
    name: str = "Luna"
    role: str = "goatherd"
    problem: str = "fog_bridge"
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A folk tale of problem solving and sound effects.")
    parser.add_argument("--setting", choices=SETTINGS)
    parser.add_argument("--name", choices=NAMES)
    parser.add_argument("--role", choices=ROLES)
    parser.add_argument("--problem", choices=[p.id for p in PROBLEMS])
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
    setting = args.setting or "bellwood"
    name = args.name or rng.choice(NAMES)
    role = args.role or rng.choice(ROLES)
    problem = args.problem or rng.choice([p.id for p in PROBLEMS])
    if setting not in SETTINGS:
        raise StoryError(f"Unknown setting: {setting}")
    if problem not in {p.id for p in PROBLEMS}:
        raise StoryError(f"Unknown problem: {problem}")
    return StoryParams(setting=setting, name=name, role=role, problem=problem)


def _problem(params: StoryParams) -> Problem:
    for problem in PROBLEMS:
        if problem.id == params.problem:
            return problem
    raise StoryError(f"No such problem: {params.problem}")


def build_world(params: StoryParams) -> World:
    setting = SETTINGS.get(params.setting)
    if setting is None:
        raise StoryError(f"The setting {params.setting!r} is not supported.")
    problem = _problem(params)
    world = World(setting)
    hero_kind = "girl" if params.name in {"Luna", "Mara", "Lina"} else "boy"
    hero = world.add(Entity(params.name, hero_kind, params.name))
    elder = world.add(Entity("elder", "person", "Old Ansel"))
    world.facts.update(
        hero=hero,
        elder=elder,
        problem=problem,
        tools=[TOOLS["rope"], TOOLS["bell"], TOOLS["pebbles"]],
        opening=random.Random(params.seed or 0).choice(OPENINGS),
    )
    hero.meters.update({"attention": 1.0, "distance": 0.0})
    hero.memes.update({"worry": 1.0, "courage": 0.0, "patience": 0.0})
    return world


def tell(world: World, sentence: str) -> None:
    world.events.append(sentence)


def solve_problem(world: World) -> None:
    hero: Entity = world.facts["hero"]
    problem: Problem = world.facts["problem"]
    hero.memes["patience"] = 1.0
    hero.memes["courage"] = 1.0
    hero.meters["distance"] = 1.0
    tell(world, f"{hero.label} followed the clue instead of rushing after a guess.")
    tell(world, f"{problem.fix}")
    tell(world, f"{problem.sound}!")
    tell(world, problem.result)


def render_story(world: World) -> str:
    hero: Entity = world.facts["hero"]
    elder: Entity = world.facts["elder"]
    problem: Problem = world.facts["problem"]
    opening: str = world.facts["opening"]
    tell(world, f"{opening} {hero.label}, a young {world.facts.get('role', 'helper')}, lived in Bellwood village.")
    tell(world, f"One day, {problem.warning}")
    tell(world, f'"How shall we find the way?" asked {hero.label}.')
    tell(world, f'"Do not chase what you cannot see. Listen for what the world tells you," said {elder.label}.')
    tell(world, f"{problem.clue}")
    tell(world, f"{hero.label} took a slow breath and began to solve the problem.")
    solve_problem(world)
    tell(world, f'"I heard the answer before I could see it," said {hero.label}.')
    tell(world, f'"Then your careful ears have made a road for everyone," said {elder.label}.')
    tell(world, f"The villagers crossed safely, and the lost way seemed to {problem.sound.split(',')[0]} and appear beneath the morning sun.")
    tell(world, f"From that day on, Bellwood children remembered: {problem.lesson}")
    return " ".join(world.events)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    world.facts["role"] = params.role
    story = render_story(world)
    problem: Problem = world.facts["problem"]
    hero: Entity = world.facts["hero"]
    prompts = [
        f"Write a folk tale in which {hero.label} solves {problem.title}.",
        "Use concrete sound effects to show how a hidden answer becomes clear.",
        f"End with the lesson: {problem.lesson}",
    ]
    story_qa = [
        QAItem(
            f"What problem did {hero.label} face?",
            f"{hero.label} faced {problem.warning} The missing or confusing way made the village uncertain.",
        ),
        QAItem(
            f"What clue helped {hero.label} solve the problem?",
            f"The important clue was that {problem.clue} This clue gave {hero.label} a safer plan than guessing.",
        ),
        QAItem(
            "How did the sounds help?",
            f"The sounds {problem.sound} marked each careful step, helping the characters notice where the solution was.",
        ),
        QAItem(
            "What changed at the end?",
            f"{problem.result} The villagers could move forward because the problem had been solved carefully.",
        ),
        QAItem(
            "What lesson did the folk tale teach?",
            f"It taught that {problem.lesson}",
        ),
    ]
    world_qa = [
        QAItem(
            "Why can sounds help with problem solving?",
            "Sounds can reveal distance, movement, or hidden spaces when eyes cannot show the whole answer.",
        ),
        QAItem(
            "What is a clue?",
            "A clue is a small piece of information that helps someone understand a problem and choose a solution.",
        ),
    ]
    return StorySample(
        params=params,
        story=story,
        prompts=prompts,
        story_qa=story_qa,
        world_qa=world_qa,
        world=world,
    )


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        lines.append(
            f"  {entity.id}: meters={entity.meters} memes={entity.memes}"
        )
    lines.append(f"  setting: {world.setting.place}")
    lines.append(f"  events: {len(world.events)}")
    return "\n".join(lines)


ASP_RULES = r"""
solvable(S,P) :- setting(S), problem(P), affords(S,inspect), affords(S,repair).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for setting in SETTINGS.values():
        lines.append(asp.fact("setting", setting.id))
        for affordance in setting.affordances:
            lines.append(asp.fact("affords", setting.id, affordance))
    for problem in PROBLEMS:
        lines.append(asp.fact("problem", problem.id))
    return "\n".join(lines)


def asp_program(show: str = "#show solvable/2.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str]]:
    return [("bellwood", problem.id) for problem in PROBLEMS]


def asp_valid_combos() -> list[tuple]:
    import asp
    symbols = asp.one_model(asp_program())
    return sorted(set(asp.atoms(symbols, "solvable")))


def asp_verify() -> int:
    expected = set(valid_combos())
    actual = set(asp_valid_combos())
    if expected != actual:
        print("MISMATCH:")
        print("python only:", sorted(expected - actual))
        print("clingo only:", sorted(actual - expected))
        return 1
    for params in (
        StoryParams(problem="fog_bridge", seed=1),
        StoryParams(problem="fallen_marker", seed=2),
        StoryParams(problem="silent_well", seed=3),
    ):
        sample = generate(params)
        if "appear" not in sample.story or not sample.story_qa:
            print("Generated-story verification failed.")
            return 1
    print(f"OK: ASP and Python agree on {len(expected)} problem combinations.")
    return 0


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
    StoryParams(name="Luna", role="goatherd", problem="fog_bridge", seed=10),
    StoryParams(name="Mara", role="baker's child", problem="fallen_marker", seed=11),
    StoryParams(name="Toma", role="woodcutter's child", problem="silent_well", seed=12),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        rows = asp_valid_combos()
        print(f"{len(rows)} solvable combinations:")
        for row in rows:
            print(" ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        for index in range(max(args.n, 1) * 20):
            if len(samples) >= max(args.n, 1):
                break
            seed = base_seed + index
            rng = random.Random(seed)
            params = resolve_params(args, rng)
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        emit(
            sample,
            trace=args.trace,
            qa=args.qa,
            header=f"### variant {index + 1}" if len(samples) > 1 else "",
        )
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
