#!/usr/bin/env python3
"""
A tiny nursery-rhyme storyworld about gingham magic, a careful child, and a
little cloth spell that works only when two friends listen to each other.
"""

from __future__ import annotations

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
from pathlib import Path as _StoryPath
_storyworlds_root = next(parent for parent in _StoryPath(__file__).resolve().parents
                        if (parent / 'results.py').is_file() and (parent / 'asp.py').is_file())
sys.path.insert(0, str(_storyworlds_root))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Thing:
    id: str
    label: str
    phrase: str
    kind: str
    owner: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    hero: Thing
    helper: Thing
    cloth: Thing
    place: str
    seed: int
    path: str = ""
    facts: dict[str, object] = field(default_factory=dict)


@dataclass
class StoryParams:
    name: str
    helper_name: str
    place: str
    problem: str
    solution: str
    seed: Optional[int] = None


NAMES = ["Mina", "Toby", "Pip", "Lulu", "Nell", "Ollie"]
HELPERS = ["Aunt May", "Grandma June", "Uncle Ben", "Miss Rose", "Old Nan"]
PLACES = ["the checkerboard meadow", "the moonlit kitchen", "the red-brick lane", "the sleepy village green"]
PROBLEMS = ["lost_moon", "sleepy_bell", "runaway_rain", "silent_song"]
SOLUTIONS = ["tie", "turn"]
PATHS = {
    "lost_moon": {
        "tie": {
            "clue": "the moon had slipped because the cloth's four corners were loose",
            "actions": ["find_corner", "tie_corners", "sing_spell"],
            "changes": {"moon_held": True, "magic_shared": True},
            "ending": "the moon rested in the sky, round and bright above the snugly tied gingham",
        },
        "turn": {
            "clue": "the moon's silver shine appeared only when the gingham's blue checks faced the stars",
            "actions": ["turn_cloth", "show_pattern", "sing_spell"],
            "changes": {"moon_held": True, "magic_shared": True},
            "ending": "the moon climbed back above the lane, shining through a neat blue-and-white window",
        },
    },
    "sleepy_bell": {
        "tie": {
            "clue": "the bell had lost its peal because its loose ribbon was tangled in the cloth",
            "actions": ["find_ribbon", "tie_ribbon", "sing_spell"],
            "changes": {"bell_ringing": True, "magic_shared": True},
            "ending": "the village bell rang one clear note while the tied gingham danced below",
        },
        "turn": {
            "clue": "the bell's golden check was hidden on the cloth's underside",
            "actions": ["turn_cloth", "show_pattern", "sing_spell"],
            "changes": {"bell_ringing": True, "magic_shared": True},
            "ending": "the bell chimed awake when its golden check faced the morning",
        },
    },
    "runaway_rain": {
        "tie": {
            "clue": "the rain was pouring through a gap where the gingham curtain had come untied",
            "actions": ["find_corner", "tie_corners", "sing_spell"],
            "changes": {"rain_stopped": True, "magic_shared": True},
            "ending": "the rain tucked itself into clouds, and the tied gingham kept the doorstep dry",
        },
        "turn": {
            "clue": "the dry side of the gingham was marked with a tiny silver raindrop",
            "actions": ["turn_cloth", "show_pattern", "sing_spell"],
            "changes": {"rain_stopped": True, "magic_shared": True},
            "ending": "the rain became a soft patter beyond the window, leaving the silver check bright",
        },
    },
    "silent_song": {
        "tie": {
            "clue": "the songbird's tune was caught in a loose gingham loop",
            "actions": ["find_ribbon", "tie_ribbon", "sing_spell"],
            "changes": {"song_returned": True, "magic_shared": True},
            "ending": "the bird sang from the tied gingham bough, trilling three notes for dawn",
        },
        "turn": {
            "clue": "the song was printed on the hidden side of the gingham in tiny red notes",
            "actions": ["turn_cloth", "show_pattern", "sing_spell"],
            "changes": {"song_returned": True, "magic_shared": True},
            "ending": "the songbird found the red notes and filled the green with music",
        },
    },
}


ASP_RULES = r"""
#show clue_ready/1.
#show magic_works/1.
#show problem_solved/1.

clue_ready(H) :- knows_clue(H).
magic_works(H) :- clue_ready(H), speaks_together(H).
problem_solved(H) :- magic_works(H), performs_solution(H).
"""


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("knows_clue", "hero"),
        asp.fact("speaks_together", "hero"),
        asp.fact("performs_solution", "hero"),
    ])


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Nursery-rhyme storyworld of gingham magic.")
    parser.add_argument("--name", choices=NAMES)
    parser.add_argument("--helper-name", choices=HELPERS)
    parser.add_argument("--place", choices=PLACES)
    parser.add_argument("--problem", choices=PROBLEMS)
    parser.add_argument("--solution", choices=SOLUTIONS)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    problem = args.problem or rng.choice(PROBLEMS)
    solution = args.solution or rng.choice(SOLUTIONS)
    if problem not in PATHS or solution not in PATHS[problem]:
        raise StoryError(f"Unsupported gingham path: {problem} with {solution}.")
    return StoryParams(
        name=args.name or rng.choice(NAMES),
        helper_name=args.helper_name or rng.choice(HELPERS),
        place=args.place or rng.choice(PLACES),
        problem=problem,
        solution=solution,
    )


def build_world(params: StoryParams) -> World:
    if params.problem not in PATHS:
        raise StoryError(f"Unknown problem: {params.problem}.")
    if params.solution not in PATHS[params.problem]:
        raise StoryError(f"The {params.solution} solution cannot solve {params.problem}.")
    hero = Thing("hero", params.name, f"young {params.name}", "character",
                 meters={"courage": 1.0}, memes={"curiosity": 1.0})
    helper = Thing("helper", params.helper_name, params.helper_name, "character",
                   meters={"patience": 1.0}, memes={"trust": 1.0})
    cloth = Thing("gingham", "gingham", "a square of blue-and-white gingham", "magical cloth",
                  owner=hero.id, meters={"order": 0.0}, memes={"magic": 1.0})
    seed = params.seed if params.seed is not None else sum(ord(c) for c in params.name + params.problem)
    return World(hero, helper, cloth, params.place, seed)


def _pick(rng: random.Random, values: list[str]) -> str:
    return values[rng.randrange(len(values))]


def generate_story(world: World) -> str:
    rng = random.Random(world.seed ^ 0x51A7)
    h, e, p = world.hero.label, world.helper.label, world.place
    path = PATHS[world.facts["problem"]][world.facts["solution"]]
    world.path = f"{world.facts['problem']}:{world.facts['solution']}"
    world.facts["clue"] = path["clue"]
    world.facts["actions"] = list(path["actions"])
    world.facts["ending"] = path["ending"]

    openings = [
        f"At {p}, {h} found a square of gingham beneath a silver spoon.",
        f"In {p}, {h} found blue-and-white gingham fluttering beside the gate.",
        f"By {p}, {h} picked up a gingham square that hummed, \"Hush and hurry!\"",
    ]
    refrains = [
        "Check by check, magic wake!",
        "Blue and white, make things right!",
        "Gingham bright, mend the night!",
    ]
    rhyme = _pick(rng, refrains)
    lines = [_pick(rng, openings)]

    problem = world.facts["problem"]
    if problem == "lost_moon":
        lines.append(f"The moon was missing from the sky, and the dark lane looked sadly shy.")
        trouble = "the owls bumped into hats and the mice mistook a bucket for the moon"
    elif problem == "sleepy_bell":
        lines.append(f"The village bell would not ring, though dawn tugged hard at its golden string.")
        trouble = "the bakers slept past breakfast and the ducks marched without a morning song"
    elif problem == "runaway_rain":
        lines.append(f"Rain ran sideways through the room, drumming a wet and wobbly tune.")
        trouble = "the boots floated like boats and a teacup sailed beneath the table"
    else:
        lines.append(f"The garden bird had lost its song, leaving the green as quiet as a stone.")
        trouble = "the flowers drooped because nobody heard the bird's cheerful tune"

    lines.append(f'"What can this gingham do?" asked {h}.')
    lines.append(f'"Ask it kindly, then listen closely," said {e}.')
    lines.append(f'{h} replied, "{rhyme}"; {e} answered, "{rhyme}"')
    lines.append(f"First they noticed that {path['clue']}.")
    lines.append(f"The trouble grew: {trouble}.")
    if world.facts["solution"] == "tie":
        lines.append(f"{h} followed the clue, while {e} held the gingham steady. Together they tied the needed loop, corner, or ribbon.")
        world.cloth.meters["order"] = 1.0
    else:
        lines.append(f"{h} turned the gingham slowly, and {e} watched its checks. A hidden mark appeared exactly where the clue promised.")
        world.cloth.meters["order"] = 1.0
    lines.append(f'"Now we know the way," said {h}. "Together," said {e}.')
    lines.append(f"They spoke the little rhyme once more: \"{rhyme}\" The gingham gave a warm, small glow.")
    lines.append(f"Then the magic changed the world: {path['ending']}.")
    lines.append(f"{h} smiled at {e}. " + _pick(rng, [
        "The rhyme had worked because neither friend tried to do it alone.",
        "The checks looked tiny, but their careful teamwork made a very large difference.",
        "From then on, every blue square and white square seemed to know their names.",
    ]))
    world.facts["resolved"] = True
    world.facts["shared_words"] = True
    return " ".join(lines)


def story_qa(world: World) -> list[QAItem]:
    h, e = world.hero.label, world.helper.label
    return [
        QAItem(
            f"What problem did {h} and {e} face?",
            f"They faced a problem with {world.facts['problem'].replace('_', ' ')}: {world.facts['clue']}.",
        ),
        QAItem(
            "What did the gingham reveal?",
            f"The gingham revealed that {world.facts['clue']}.",
        ),
        QAItem(
            f"How did {h} and {e} use the magic?",
            f"They used the {world.facts['solution']} solution, followed the clue, and spoke the rhyme together before the magic worked.",
        ),
        QAItem(
            "What proved that the problem was solved?",
            f"The ending showed the change: {world.facts['ending']}.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What is gingham?",
            "Gingham is a woven fabric with a repeated check pattern, often made with two colors such as blue and white.",
        ),
        QAItem(
            "What is magic in this storyworld?",
            "Magic is a special force in the gingham that responds when someone notices its clue and shares the rhyme with a helper.",
        ),
        QAItem(
            "Why did the characters need to work together?",
            "They needed to work together because the gingham magic required one character to act while the other listened, helped, and answered.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    return [
        f"Write a nursery rhyme about {world.hero.label} and {world.helper.label} using magical gingham.",
        f"Tell a child-friendly rhyme set in {world.place}, where gingham helps solve a strange problem.",
        "Use a brief spoken exchange and a repeated rhyme to show how teamwork awakens magic.",
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for item in (world.hero, world.helper, world.cloth):
        lines.append(
            f"  {item.id:8} {item.kind:14} label={item.label!r} "
            f"owner={item.owner!r} meters={item.meters} memes={item.memes}"
        )
    lines.append(f"  place={world.place!r} path={world.path!r} facts={world.facts}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    parts = ["== Generation prompts =="]
    parts.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    parts.append("")
    parts.append("== Story QA ==")
    for item in sample.story_qa:
        parts.extend([f"Q: {item.question}", f"A: {item.answer}"])
    parts.append("")
    parts.append("== World QA ==")
    for item in sample.world_qa:
        parts.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(parts)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    world.facts["problem"] = params.problem
    world.facts["solution"] = params.solution
    story = generate_story(world)
    world.facts["story"] = story
    return StorySample(
        params=params,
        story=story,
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


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program(
        "#show clue_ready/1.\n#show magic_works/1.\n#show problem_solved/1."
    ))
    actual = {(atom.name, tuple(
        arg.number if arg.type.name == "Number" else arg.name
        for arg in atom.arguments
    )) for atom in model}
    expected = {
        ("clue_ready", ("hero",)),
        ("magic_works", ("hero",)),
        ("problem_solved", ("hero",)),
    }
    if actual != expected:
        print("MISMATCH between ASP and Python expectations.")
        print("ASP:", sorted(actual))
        print("PY :", sorted(expected))
        return 1
    for problem in PROBLEMS:
        for solution in SOLUTIONS:
            params = StoryParams("Mina", "Aunt May", PLACES[0], problem, solution, 17)
            sample = generate(params)
            if not sample.world or not sample.world.facts.get("resolved"):
                print(f"Python path failed: {problem}:{solution}")
                return 1
            if "{" in sample.story or "}" in sample.story:
                print(f"Unresolved prose on path: {problem}:{solution}")
                return 1
            if "said" not in sample.story or "asked" not in sample.story:
                print(f"Missing dialogue on path: {problem}:{solution}")
                return 1
    print("OK: ASP parity and all gingham paths verified.")
    return 0


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program(
            "#show clue_ready/1.\n#show magic_works/1.\n#show problem_solved/1."
        ))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("3 compatible logical atoms: clue_ready(hero), magic_works(hero), problem_solved(hero)")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        params_list = [
            StoryParams("Mina", "Aunt May", PLACES[0], problem, solution, base_seed + i)
            for i, (problem, solution) in enumerate(
                (("lost_moon", "tie"), ("sleepy_bell", "turn"),
                 ("runaway_rain", "tie"), ("silent_song", "turn"))
            )
        ]
    else:
        params_list = []
        for i in range(args.n):
            rng = random.Random(base_seed + i)
            params = resolve_params(args, rng)
            params.seed = base_seed + i
            params_list.append(params)

    samples = [generate(params) for params in params_list]
    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        header = ""
        if args.all:
            header = f"### {sample.params.problem} / {sample.params.solution}"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
