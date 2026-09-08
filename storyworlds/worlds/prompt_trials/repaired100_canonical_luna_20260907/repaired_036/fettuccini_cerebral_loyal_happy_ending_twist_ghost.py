#!/usr/bin/env python3
"""
A standalone Ghost Story world about fettuccini, a cerebral mystery, and loyal
friendship. A small twist turns a frightening haunting into a happy ending.
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


NAMES = ["Luna", "Milo", "Nia", "Theo", "Ivy", "Sam"]
GHOST_NAMES = ["Ada", "Bea", "Cora", "Elsie"]
PLACES = ["the Moonbell House", "the old riverside kitchen", "the lantern inn"]
PASTAS = ["fettuccini", "ravioli", "spaghetti"]
TOOLS = ["a silver spoon", "a candle", "a recipe card", "a bell"]
MOODS = ["curious", "brave", "gentle", "thoughtful"]
CLUES = [
    "three floury footprints stopped beside the cold stove",
    "a recipe card slid across the table without anyone touching it",
    "the kitchen bell rang once whenever the moon appeared",
]
TWISTS = [
    "the ghost was not trying to frighten anyone; she was searching for the recipe she had written for her lost family",
    "the rattling cupboard hid a tiny music box, and its tune was calling the ghost home",
    "the pale figure was the house's former cook, whose lonely spirit had mistaken the warm kitchen for a vanished celebration",
]

ASP_RULES = r"""
valid_pasta(P) :- pasta(P).
valid_clue(C) :- clue(C).
valid_story(P,C) :- valid_pasta(P), valid_clue(C), P = fettuccini.
#show valid_story/2.
"""


@dataclass
class StoryParams:
    child: str
    ghost: str
    place: str
    pasta: str
    tool: str
    mood: str
    seed: Optional[int] = None


@dataclass
class Ghost:
    name: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    params: StoryParams
    ghost: Ghost
    facts: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def say(self, line: str) -> None:
        self.facts.setdefault("lines", []).append(line)

    def render(self) -> str:
        return " ".join(self.facts.get("lines", []))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A cerebral fettuccini ghost story with a loyal happy ending.")
    parser.add_argument("--child", choices=NAMES)
    parser.add_argument("--ghost", choices=GHOST_NAMES)
    parser.add_argument("--place", choices=PLACES)
    parser.add_argument("--pasta", choices=PASTAS)
    parser.add_argument("--tool", choices=TOOLS)
    parser.add_argument("--mood", choices=MOODS)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def valid_combo(params: StoryParams) -> bool:
    return params.pasta == "fettuccini" and params.child != params.ghost


def asp_facts() -> str:
    import asp
    lines = []
    for pasta in PASTAS:
        lines.append(asp.fact("pasta", pasta))
    for clue in CLUES:
        lines.append(asp.fact("clue", clue))
    return "\n".join(lines)


def asp_program(show: str = "#show valid_story/2.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> set[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return set(asp.atoms(model, "valid_story"))


def asp_verify() -> int:
    python_pairs = {("fettuccini", clue) for clue in CLUES}
    clingo_pairs = asp_valid()
    if python_pairs == clingo_pairs:
        print(f"OK: clingo gate matches Python ({len(clingo_pairs)} combinations).")
        return 0
    print("MISMATCH:")
    print("only in clingo:", sorted(clingo_pairs - python_pairs))
    print("only in python:", sorted(python_pairs - clingo_pairs))
    return 1


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    params = StoryParams(
        child=args.child or rng.choice(NAMES),
        ghost=args.ghost or rng.choice(GHOST_NAMES),
        place=args.place or rng.choice(PLACES),
        pasta=args.pasta or rng.choice(PASTAS),
        tool=args.tool or rng.choice(TOOLS),
        mood=args.mood or rng.choice(MOODS),
    )
    if not valid_combo(params):
        raise StoryError("This story requires fettuccini and two different names for the child and ghost.")
    return params


def make_world(params: StoryParams) -> World:
    seed = params.seed
    if seed is None:
        seed = sum((i + 1) * ord(ch) for i, ch in enumerate("|".join(vars(params).values().__iter__().__next__() if False else [str(v) for v in vars(params).values()])))
    rng = random.Random(seed)
    ghost = Ghost(
        params.ghost,
        meters={"visibility": 0.4, "warmth": 0.2},
        memes={"loneliness": 1.0, "hope": 0.0},
    )
    return World(
        params=params,
        ghost=ghost,
        meters={"distance_to_kitchen": 3.0, "warmth": 0.0},
        memes={"fear": 0.0, "trust": 0.0, "loyalty": 1.0},
        facts={
            "clue": rng.choice(CLUES),
            "twist": rng.choice(TWISTS),
            "opening": rng.choice([
                "Rain tapped the windows after supper.",
                "The moon rose over the quiet rooftops.",
                "A silver fog curled around the garden gate.",
            ]),
            "ending": rng.choice([
                "a bright bowl of fettuccini steamed beneath the moon",
                "the kitchen bell chimed like a tiny star",
                "the old recipe card rested safely beside the warm stove",
            ]),
        },
    )


def generate_story(world: World) -> None:
    p = world.params
    g = world.ghost
    world.say(
        f"{world.facts['opening']} {p.child}, a {p.mood} child, was in {p.place} when a cold breeze "
        "slipped through the kitchen."
    )
    world.say(
        f"On the table lay a plate of {p.pasta}, but no one had cooked it. "
        f"Then {world.facts['clue']}."
    )
    world.memes["fear"] += 0.5
    world.say(
        f'"Who is there?" asked {p.child}. A pale shape appeared near the stove. '
        f'"I am {g.name}," said the ghost. "Please do not run."'
    )
    world.say(
        f'"Are you here to scare me?" asked {p.child}. '
        f'"No," said {g.name}. "I need someone {p.mood} enough to listen."'
    )
    world.memes["trust"] += 1.0
    world.say(
        f"{p.child} held up {p.tool} and studied the room. It was a cerebral puzzle: "
        f"the cold plate, the wandering clue, and the silent oven all pointed toward one forgotten memory."
    )
    world.say(
        f"{p.child} remembered a promise to stay loyal to anyone who needed help. "
        f'"Tell me what happened," {p.child} said.'
    )
    world.say(f'"I have been waiting for a family recipe," said {g.name}. "It was for {p.pasta}."')
    world.say(
        f"Then came the twist: {world.facts['twist']}. The ghost had never wanted to hurt anyone."
    )
    world.say(
        f"{p.child} found the recipe card beneath a loose floorboard, and together they followed its "
        f"small instructions. Soon the kitchen smelled of garlic, butter, and warm {p.pasta}."
    )
    world.meters["warmth"] = 1.0
    world.ghost.memes["loneliness"] = 0.0
    world.ghost.memes["hope"] = 1.0
    world.say(
        f"{g.name} smiled for the first time in many years. "
        f'"You kept your promise," said {g.name}. "Your loyal heart made this house feel like home."'
    )
    world.say(
        f"{p.child} smiled back. The ghost faded into a soft golden glow, leaving {world.facts['ending']}."
    )


def story_qa(world: World) -> list[QAItem]:
    p = world.params
    g = world.ghost
    return [
        QAItem(
            question=f"Where was {p.child} when the ghost appeared?",
            answer=f"{p.child} was in {p.place}, near the kitchen, when the ghost appeared.",
        ),
        QAItem(
            question=f"What food was on the table?",
            answer=f"A plate of {p.pasta} was on the table, even though no one had cooked it.",
        ),
        QAItem(
            question=f"What did {g.name} really want?",
            answer=f"{g.name} wanted help finding a forgotten family recipe, not a chance to frighten {p.child}.",
        ),
        QAItem(
            question="What was the twist?",
            answer=f"The twist was that {world.facts['twist']}.",
        ),
        QAItem(
            question=f"How did {p.child} help {g.name}?",
            answer=f"{p.child} stayed loyal, listened carefully, found the recipe card, and cooked {p.pasta} with {g.name}.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"The ghost found peace and faded into a warm glow while {world.facts['ending']}.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a ghost story?",
            answer="A ghost story is a tale about a spirit or mysterious presence, often with a surprising discovery.",
        ),
        QAItem(
            question="What does loyal mean?",
            answer="Loyal means staying faithful and helpful to someone, especially when things are difficult.",
        ),
        QAItem(
            question="What does cerebral mean?",
            answer="Cerebral means connected with careful thinking, puzzles, or the mind.",
        ),
        QAItem(
            question="What makes a happy ending?",
            answer="A happy ending resolves the trouble in a hopeful way and shows that the characters are safer or kinder than before.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    p = world.params
    return [
        f"Write a child-friendly ghost story about {p.child}, {p.pasta}, and a loyal promise in {p.place}.",
        f"Make the mystery cerebral: use the clue '{world.facts['clue']}' to reveal what {world.ghost.name} truly wants.",
        f"Include a twist and a happy ending in which {p.child} helps {world.ghost.name} find peace.",
    ]


def dump_trace(world: World) -> str:
    return "\n".join([
        "--- world model state ---",
        f"child={world.params.child} ghost={world.ghost.name} place={world.params.place}",
        f"pasta={world.params.pasta} tool={world.params.tool}",
        f"meters={world.meters}",
        f"memes={world.memes}",
        f"ghost_memes={world.ghost.memes}",
        f"clue={world.facts['clue']}",
        f"twist={world.facts['twist']}",
    ])


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== story QA ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== world QA ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


CURATED = [
    StoryParams("Luna", "Ada", "the Moonbell House", "fettuccini", "a silver spoon", "brave"),
    StoryParams("Milo", "Bea", "the old riverside kitchen", "fettuccini", "a recipe card", "curious"),
    StoryParams("Nia", "Cora", "the lantern inn", "fettuccini", "a candle", "gentle"),
]


def generate(params: StoryParams) -> StorySample:
    world = make_world(params)
    generate_story(world)
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
        print(asp_program())
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for index, params in enumerate(CURATED):
            params.seed = base_seed + index
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        for index in range(max(args.n, 1) * 100):
            if len(samples) >= args.n:
                break
            rng = random.Random(base_seed + index)
            try:
                params = resolve_params(args, rng)
            except StoryError:
                continue
            params.seed = base_seed + index
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
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
