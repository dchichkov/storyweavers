#!/usr/bin/env python3
"""
A tall tale about Luna, a progressive prance, a missing vowel, problem solving,
and reconciliation beneath a very tall schoolhouse bell.
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

_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_root, "results.py")):
    _root = os.path.dirname(_root)
sys.path.insert(0, _root)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)


@dataclass
class Setting:
    id: str
    label: str
    affordances: set[str]


@dataclass
class Problem:
    id: str
    label: str
    missing: str
    consequence: str
    clue: str
    tool: str


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, str] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    repaired: bool = False
    reconciled: bool = False

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


SETTINGS = {
    "bell_tower": Setting(
        "bell_tower",
        "the tallest bell tower in the county",
        {"prance", "write", "repair"},
    ),
    "hill_school": Setting(
        "hill_school",
        "the schoolhouse on Blueberry Hill",
        {"prance", "write", "repair"},
    ),
    "town_square": Setting(
        "town_square",
        "the wide town square",
        {"prance", "write", "repair"},
    ),
}

PROBLEMS = {
    "missing_o": Problem(
        "missing_o",
        "the vanished vowel",
        "the letter O",
        "the word PROGRESSIVE became PRGRESSIVE on the town banner",
        "a round bird nest shaped like a missing O rested beside the ink pot",
        "a loop of red ribbon",
    ),
    "missing_a": Problem(
        "missing_a",
        "the absent vowel",
        "the letter A",
        "the word PRANCE became PRNCE on the dance poster",
        "a small arch in the dust matched the shape of an A",
        "a bent willow twig",
    ),
    "missing_e": Problem(
        "missing_e",
        "the lost vowel",
        "the letter E",
        "the word RECONCILIATION became RCONCILIATION on the peace notice",
        "two friendly curves appeared where the letter had been",
        "a pale feather",
    ),
}

NAMES = ["Luna", "Mara", "Tessa", "Nell", "Pia"]
FRIENDS = ["Bram", "Ollie", "Theo", "Milo", "Finn"]
TRAITS = ["brave", "patient", "curious", "kind", "inventive"]


@dataclass(frozen=True)
class StoryParams:
    setting: str
    problem: str
    name: str
    friend: str
    trait: str
    seed: Optional[int] = None


def _meter(entity: Entity, key: str, amount: float = 1.0) -> None:
    entity.meters[key] = entity.meters.get(key, 0.0) + amount


def _meme(entity: Entity, key: str, amount: float = 1.0) -> None:
    entity.memes[key] = entity.memes.get(key, 0.0) + amount


def valid_combos() -> list[tuple[str, str]]:
    return [(s, p) for s in SETTINGS for p in PROBLEMS]


def build_world(params: StoryParams, rng: random.Random) -> World:
    if params.setting not in SETTINGS:
        raise StoryError(f"Unknown setting: {params.setting}")
    if params.problem not in PROBLEMS:
        raise StoryError(f"Unknown problem: {params.problem}")

    setting = SETTINGS[params.setting]
    problem = PROBLEMS[params.problem]
    world = World(setting)
    luna = world.add(Entity(params.name, "character", params.name, tags={params.trait}))
    friend = world.add(Entity(params.friend, "character", params.friend, tags={"friend"}))
    banner = world.add(Entity("banner", "object", "the enormous banner"))
    _meme(luna, "curiosity")
    _meme(friend, "hurt")

    opening = rng.choice([
        f"{params.name} was a {params.trait} child who could prance higher than a fence post.",
        f"{params.name} had a {params.trait} heart and a prance so grand that chickens applauded.",
        f"People said {params.name} could prance over a puddle, a pumpkin, and sometimes a whole paragraph.",
    ])
    world.say(opening)
    world.say(
        f"One bright morning, {params.name} climbed to {setting.label}, where a banner "
        "stretched so high that its top corner tickled the clouds."
    )
    world.say(
        "The banner announced a progressive prance for the town: each dancer would add "
        "one new step, and every neighbor would be invited."
    )
    world.say(
        f"But {problem.consequence}. Without {problem.missing}, the announcement sounded "
        "like a wagon with one wheel missing."
    )
    world.para()

    world.say(f"{params.friend} folded their arms. \"{params.name} did this on purpose!\"")
    world.say(
        f"\"I did not,\" said {params.name}. \"I wanted everyone to prance together. "
        "Let us find what happened before we blame anyone.\""
    )
    world.say(
        f"Their back-and-forth changed the morning: {params.friend} stopped pointing fingers, "
        f"and {params.name} stopped trying to fix the banner alone."
    )
    _meme(luna, "problem_solving")
    _meme(friend, "listening")
    world.say(
        f"They searched the tower stones, the ink pot, and the bell rope. At last, "
        f"{problem.clue}."
    )
    world.say(
        f"\"That shape is our clue,\" said {params.friend}. \"The vowel may have fallen "
        "where the wind could carry it.\""
    )
    world.say(
        f"\"Then we will test one place at a time,\" said {params.name}. "
        "\"No giant guesses, even in a giant tower.\""
    )
    world.para()

    world.say(
        f"Together they used {problem.tool} to measure the empty space, then checked the "
        "old copybook beneath the bell."
    )
    world.say(
        f"{params.name} discovered that a gust had lifted {problem.missing} from the wet ink, "
        f"while {params.friend} found it caught in a crack beside the bell."
    )
    world.say(
        f"They returned the vowel carefully. The banner straightened, the word became whole, "
        "and the tower gave one thunderous, happy ring."
    )
    world.repaired = True
    _meter(banner, "repaired")
    _meme(luna, "confidence")
    _meme(friend, "trust")

    world.say(
        f"\"I am sorry I blamed you,\" said {params.friend}. "
        f"\"I am sorry I hurried past your idea,\" said {params.name}."
    )
    world.say(
        "They shook hands beneath the enormous banner. Their reconciliation was not a "
        "fancy word anymore; it was a choice they made together."
    )
    world.reconciled = True
    world.say(
        f"Then the progressive prance began. {params.name} made the first step, "
        f"{params.friend} added the second, and the whole town followed with a "
        "growing rhythm of heel, toe, hop, and turn."
    )
    world.say(
        f"By sunset, the repaired vowel shone in the banner, and even the clouds seemed "
        f"to prance around {setting.label}."
    )

    world.facts.update({
        "hero": params.name,
        "friend": params.friend,
        "setting": setting.label,
        "problem": problem.label,
        "missing": problem.missing,
        "clue": problem.clue,
        "tool": problem.tool,
        "consequence": problem.consequence,
    })
    return world


def generate(params: StoryParams) -> StorySample:
    rng = random.Random(params.seed if params.seed is not None else f"{params.name}:{params.problem}")
    world = build_world(params, rng)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=[
            f"Write a tall tale about {params.name} solving a missing-vowel problem.",
            "Include a progressive prance that grows one step at a time.",
            "Show reconciliation through spoken dialogue and a shared repair.",
        ],
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    return [
        QAItem(
            "What went wrong with the town's announcement?",
            f"The announcement lost {f['missing']}, so {f['consequence']}.",
        ),
        QAItem(
            "What clue helped Luna and her friend?",
            f"They found that {f['clue']}.",
        ),
        QAItem(
            "How did they solve the problem?",
            f"They used {f['tool']} to measure the empty space, searched the bell tower, "
            f"found the missing vowel, and returned it carefully.",
        ),
        QAItem(
            "How did reconciliation happen?",
            f"They apologized to each other for blaming and hurrying, then shook hands "
            f"and repaired the banner together.",
        ),
        QAItem(
            "What changed at the end?",
            "The word became whole, the banner was repaired, and the whole town joined the progressive prance.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What is a vowel?",
            "A vowel is a speech sound and letter such as A, E, I, O, or U that helps form words.",
        ),
        QAItem(
            "What does progressive mean?",
            "Progressive means moving forward by adding improvements or new steps over time.",
        ),
        QAItem(
            "What is problem solving?",
            "Problem solving means noticing a difficulty, studying clues, testing a safe plan, and making a useful fix.",
        ),
        QAItem(
            "What is reconciliation?",
            "Reconciliation is the process of making peace after a disagreement by listening, apologizing, and repairing trust.",
        ),
        QAItem(
            "What is a prance?",
            "A prance is a lively, springy way of walking or dancing.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    lines.append(f"  setting: {world.setting.label}")
    lines.append(f"  repaired: {world.repaired}")
    lines.append(f"  reconciled: {world.reconciled}")
    for entity in world.entities.values():
        lines.append(
            f"  {entity.id}: kind={entity.kind}, meters={entity.meters}, memes={entity.memes}"
        )
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    lines.append("\n== (2) Story questions ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("\n== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines = []
    for setting, problem in valid_combos():
        lines.append(asp.fact("setting", setting))
        lines.append(asp.fact("problem", problem))
        lines.append(asp.fact("compatible", setting, problem))
    return "\n".join(sorted(set(lines)))


ASP_RULES = r"""
valid(S, P) :- setting(S), problem(P), compatible(S, P).
#show valid/2.
"""


def asp_program(show: str = "#show valid/2.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    expected = set(valid_combos())
    actual = set(asp_valid_combos())
    if expected != actual:
        print("ASP/Python mismatch.")
        print("Only Python:", sorted(expected - actual))
        print("Only ASP:", sorted(actual - expected))
        return 1
    for setting, problem in valid_combos():
        sample = generate(StoryParams(setting, problem, "Luna", "Bram", "patient", 7))
        if not sample.world or not sample.world.repaired or not sample.world.reconciled:
            print("Generated story failed its resolution checks.")
            return 1
    print(f"OK: ASP matches Python for {len(expected)} combinations, and stories resolve.")
    return 0


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting = args.setting or rng.choice(list(SETTINGS))
    problem = args.problem or rng.choice(list(PROBLEMS))
    if setting not in SETTINGS:
        raise StoryError(f"Unknown setting: {setting}")
    if problem not in PROBLEMS:
        raise StoryError(f"Unknown problem: {problem}")
    name = args.name or rng.choice(NAMES)
    friend = args.friend or rng.choice([x for x in FRIENDS if x != name])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(setting, problem, name, friend, trait, args.seed)


CURATED = [
    StoryParams("bell_tower", "missing_o", "Luna", "Bram", "brave", 101),
    StoryParams("hill_school", "missing_a", "Mara", "Ollie", "patient", 102),
    StoryParams("town_square", "missing_e", "Tessa", "Theo", "inventive", 103),
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A tall tale of vowels, prancing, problem solving, and reconciliation.")
    parser.add_argument("--setting", choices=sorted(SETTINGS))
    parser.add_argument("--problem", choices=sorted(PROBLEMS))
    parser.add_argument("--name")
    parser.add_argument("--friend")
    parser.add_argument("--trait")
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


def emit(sample: StorySample, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world:
        print(dump_trace(sample.world))
    if qa:
        print("\n" + format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        for combo in asp_valid_combos():
            print(combo)
        return

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        base = args.seed if args.seed is not None else random.randrange(2**31)
        samples = []
        for index in range(max(1, args.n)):
            rng = random.Random(base + index)
            params = resolve_params(args, rng)
            params = StoryParams(
                params.setting,
                params.problem,
                params.name,
                params.friend,
                params.trait,
                base + index,
            )
            samples.append(generate(params))

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
