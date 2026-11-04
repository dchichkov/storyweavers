#!/usr/bin/env python3
"""A heartwarming storyworld about helium balloons and the bravery to help."""

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
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    label: str
    kind: str
    owner: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    hero: Entity
    helper: Entity
    balloon: Entity
    place: str
    seed: int
    facts: dict = field(default_factory=dict)


@dataclass
class StoryParams:
    name: str
    helper_name: str
    place: str
    seed: Optional[int] = None


NAMES = ["Luna", "Maya", "Theo", "Sam", "Nell", "Ari"]
HELPERS = ["Aunt Jo", "Mr. Bell", "Grandma", "Rafi", "Ms. Kim"]
PLACES = ["the school garden", "the village fair", "the sunny park", "the library steps"]
BALLOON_COLORS = ["yellow", "blue", "red", "green"]
BALLOON_SHAPES = ["a star", "a moon", "a little heart", "a round sun"]

ASP_RULES = r"""
#show brave/1.
#show safe/1.
#show comforted/1.

brave(H) :- notices_danger(H), speaks_up(H).
safe(H) :- asks_helper(H), balloon_secured.
comforted(H) :- safe(H), shares_feeling(H).
"""


def asp_facts() -> str:
    import asp

    return "\n".join(
        [
            asp.fact("notices_danger", "hero"),
            asp.fact("speaks_up", "hero"),
            asp.fact("asks_helper", "hero"),
            asp.fact("balloon_secured"),
            asp.fact("shares_feeling", "hero"),
        ]
    )


def asp_program(show: str = "#show brave/1.\n#show safe/1.\n#show comforted/1.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> bool:
    return True


def asp_verify() -> int:
    import asp

    symbols = asp.one_model(asp_program())
    found = {(atom.name, tuple(
        arg.number if arg.type == arg.type.Number else arg.name
        for arg in atom.arguments
    )) for atom in symbols}
    expected = {
        ("brave", ("hero",)),
        ("safe", ("hero",)),
        ("comforted", ("hero",)),
    }
    if found != expected or not asp_valid():
        print("MISMATCH between ASP and Python expectations.")
        print("ASP:", sorted(found))
        print("PY :", sorted(expected))
        return 1

    for seed in range(12):
        sample = generate(
            StoryParams(name=NAMES[seed % len(NAMES)],
                        helper_name=HELPERS[seed % len(HELPERS)],
                        place=PLACES[seed % len(PLACES)], seed=seed)
        )
        if not sample.story or not all(mark in sample.story for mark in ['"', "."]):
            print(f"Generated-story check failed for seed {seed}.")
            return 1
        if not sample.world.facts.get("secured"):
            print(f"Resolution check failed for seed {seed}.")
            return 1
    print("OK: ASP parity and generated stories verified.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A heartwarming helium-balloon storyworld about bravery."
    )
    parser.add_argument("--name", choices=NAMES)
    parser.add_argument("--helper-name", choices=HELPERS)
    parser.add_argument("--place", choices=PLACES)
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
    if args.n < 0:
        raise StoryError("-n must be zero or greater.")
    return StoryParams(
        name=args.name or rng.choice(NAMES),
        helper_name=args.helper_name or rng.choice(HELPERS),
        place=args.place or rng.choice(PLACES),
    )


def build_world(params: StoryParams) -> World:
    if params.name not in NAMES:
        raise StoryError(f"Unknown child name: {params.name!r}.")
    if params.helper_name not in HELPERS:
        raise StoryError(f"Unknown helper name: {params.helper_name!r}.")
    if params.place not in PLACES:
        raise StoryError(f"Unknown place: {params.place!r}.")
    seed = params.seed
    if seed is None:
        seed = sum(ord(ch) for ch in f"{params.name}|{params.helper_name}|{params.place}")
    hero = Entity("hero", params.name, "child",
                  meters={"courage": 0.25, "worry": 0.65},
                  memes={"kindness": 0.8, "bravery": 0.3})
    helper = Entity("helper", params.helper_name, "adult",
                    meters={"distance": 2.0},
                    memes={"patience": 0.9, "kindness": 0.8})
    balloon = Entity("balloon", "helium balloon", "toy", owner="hero",
                     meters={"height": 1.0, "tether_strength": 0.3},
                     memes={"comfort": 0.7})
    return World(hero, helper, balloon, params.place, seed)


def generate_story(world: World) -> str:
    rng = random.Random(world.seed ^ 0x51A7)
    h, helper, place = world.hero.label, world.helper.label, world.place
    color = rng.choice(BALLOON_COLORS)
    shape = rng.choice(BALLOON_SHAPES)
    wind = rng.choice(["a sudden breeze", "a playful gust", "a puff of wind"])
    comfort = rng.choice(["a soft smile", "a little squeeze of the hand", "a warm laugh"])
    world.balloon.label = f"{color} helium balloon"
    world.facts.update(
        color=color,
        shape=shape,
        wind=wind,
        secured=True,
        brave=True,
        helper=helper,
        comfort=comfort,
    )
    world.hero.meters.update(courage=0.9, worry=0.2)
    world.balloon.meters.update(height=0.0, tether_strength=1.0)
    world.balloon.owner = "shared"

    return " ".join(
        [
            f"At {place}, {h} carried a {color} helium balloon shaped like {shape}.",
            f"It bobbed above the little tables until {wind} tugged the ribbon from {h}'s fingers.",
            f'"My balloon is going!" {h} cried. "{helper}, could you help me?"',
            f'"I’m here," {helper} answered, reaching for the ribbon as it fluttered past.',
            f"{h} was still afraid to step into the busy path, but the balloon was drifting toward a tall gate.",
            f'"Please hold the gate, everyone!" {h} called. The nearby children made room, and {helper} caught the ribbon just in time.',
            f'"You told us what you needed," said {helper}. "That was brave." {h} held the ribbon while they tied it safely to a low post.',
            f"{h} took a breath and shared {comfort} with a younger child who had been watching.",
            f"By the time the fair lights glowed, the balloon rested beside {h}, gently tapping the post like a cheerful little hello.",
        ]
    )


def story_qa(world: World) -> list[QAItem]:
    h = world.hero.label
    f = world.facts
    return [
        QAItem(
            question=f"What happened to {h}'s balloon?",
            answer=f"A gust pulled {h}'s {f['color']} helium balloon toward a tall gate, but {h} and {f['helper']} caught it and tied it safely to a low post.",
        ),
        QAItem(
            question=f"How did {h} show bravery?",
            answer=f"{h} felt afraid but called out for help and asked everyone to hold the gate so the balloon could be caught.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"The balloon rested safely beside {h}, tied to a low post, and {h} comforted a younger child at the fair.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is helium?",
            answer="Helium is a very light gas. A balloon filled with helium can float because the gas is lighter than the air around it.",
        ),
        QAItem(
            question="Why can a helium balloon float away?",
            answer="A helium balloon floats upward, and wind can carry it away if its ribbon is not held or tied securely.",
        ),
        QAItem(
            question="What does bravery mean?",
            answer="Bravery means doing something helpful or right even when you feel nervous or afraid.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    return [
        "Write a heartwarming story for young children about helium and bravery.",
        f"Tell a gentle story at {world.place} where a child asks for help when a helium balloon drifts away.",
        "Show a child's courage through a kind choice, spoken dialogue, and a safe, comforting ending.",
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in (world.hero, world.helper, world.balloon):
        lines.append(
            f"  {entity.id:7} {entity.kind:8} label={entity.label!r} "
            f"owner={entity.owner!r} meters={entity.meters} memes={entity.memes}"
        )
    lines.append(f"  place={world.place!r} facts={world.facts}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    lines.extend(["", "== Story QA =="])
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.extend(["", "== World QA =="])
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp

        symbols = asp.one_model(asp_program())
        print("Compatible logical atoms:", ", ".join(sorted(str(s) for s in symbols)))
        return
    if args.n < 0:
        raise StoryError("-n must be zero or greater.")

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [
            generate(StoryParams(name=NAMES[i], helper_name=HELPERS[i % len(HELPERS)],
                                 place=PLACES[i % len(PLACES)], seed=base_seed + i))
            for i in range(len(NAMES))
        ]
    else:
        samples = []
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples],
                             indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            header = f"### {sample.params.name} at {sample.params.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
