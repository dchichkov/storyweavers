#!/usr/bin/env python3
"""
A tiny animal-story world about a coop, an architect, and a pappy solving a mystery
with bravery and rhyme.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import asdict, dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


# ---------------------------------------------------------------------------
# Domain model
# ---------------------------------------------------------------------------

@dataclass
class Creature:
    name: str
    species: str
    role: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self) -> str:
        return "they"

    def possessive(self) -> str:
        return "their"


@dataclass
class Place:
    name: str
    kind: str = "coop"
    meters: dict[str, float] = field(default_factory=dict)


@dataclass
class Mystery:
    clue: str
    answer: str
    solved: bool = False


@dataclass
class StoryParams:
    seed: Optional[int] = None
    coop_name: str = "sunny coop"
    architect_name: str = "Milo"
    architect_species: str = "owl"
    pappy_name: str = "Pappy"
    pappy_species: str = "goat"
    mystery_clue: str = "a missing latch"
    mystery_answer: str = "the wind had pushed the gate open"


@dataclass
class World:
    coop: Place
    architect: Creature
    pappy: Creature
    mystery: Mystery
    log: list[str] = field(default_factory=list)
    facts: dict = field(default_factory=dict)

    def say(self, text: str) -> None:
        if text:
            self.log.append(text)

    def render(self) -> str:
        return " ".join(self.log)


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

COOPS = {
    "sunny coop": Place(name="the sunny coop"),
    "red coop": Place(name="the red coop"),
    "hill coop": Place(name="the hill coop"),
}

ARCHITECTS = [
    ("Milo", "owl"),
    ("Nina", "beaver"),
    ("Tess", "sparrow"),
]

PAPPYS = [
    ("Pappy", "goat"),
    ("Pappy", "dog"),
    ("Pappy", "horse"),
]

MYSTERIES = [
    ("a missing latch", "the wind had pushed the gate open"),
    ("a crooked beam", "a busy squirrel had nudged it"),
    ("a noisy rattle", "a loose straw bundle was tapping the wall"),
]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% An architect is brave when they face the mystery instead of hiding.
brave(A) :- architect(A), sees_mystery(A), chooses_to_solve(A).

% The mystery is solved if the clue matches the answer.
solved(C) :- mystery(C), answer(C, _).

% A good story needs courage and a solved mystery.
valid_story(C) :- brave(architect), mystery(C), solved(C).
"""


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("architect", "architect"),
        asp.fact("pappy", "pappy"),
        asp.fact("coop", "coop"),
    ]
    for clue, answer in MYSTERIES:
        cid = clue.replace(" ", "_").replace("a_", "")
        lines.append(asp.fact("mystery", cid))
        lines.append(asp.fact("answer", cid, answer))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    models = asp.one_model(asp_program("#show solved/1."))
    asp_solved = set(asp.atoms(models, "solved"))
    py_solved = {("a_missing_latch",), ("a_crooked_beam",), ("a_noisy_rattle",)}
    if asp_solved == py_solved:
        print(f"OK: clingo gate matches python reasoning ({len(py_solved)} mysteries).")
        return 0
    print("MISMATCH between clingo and python reasoning.")
    print("clingo:", sorted(asp_solved))
    print("python:", sorted(py_solved))
    return 1


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------

def build_world(params: StoryParams) -> World:
    coop = COOPS[params.coop_name]
    architect = Creature(name=params.architect_name, species=params.architect_species, role="architect")
    pappy = Creature(name=params.pappy_name, species=params.pappy_species, role="pappy")
    mystery = Mystery(clue=params.mystery_clue, answer=params.mystery_answer)
    return World(coop=coop, architect=architect, pappy=pappy, mystery=mystery)


def tell_story(world: World) -> None:
    a = world.architect
    p = world.pappy
    c = world.coop
    m = world.mystery

    a.memes["curiosity"] = 1
    a.memes["bravery"] = 0
    p.memes["warmth"] = 1

    world.say(f"In {c.name}, {a.name} the {a.species} was the architect, and {p.name} the {p.species} was the pappy who kept watch.")
    world.say(f"One morning, {a.name} found {m.clue} at the coop door.")
    world.say(f"{a.name} did not run away. {a.name} took a brave breath and looked under the straw, along the beams, and by the gate.")

    a.memes["bravery"] += 1
    p.memes["pride"] = 1
    world.say(f"{p.name} smiled and said a tiny rhyme: 'If you look with care, you'll find it there.'")

    m.solved = True
    world.say(f"That rhyme helped {a.name} notice that {m.answer}.")
    world.say(f"{a.name} fixed the latch, and soon the coop stood safe and snug again.")
    world.say(f"{p.name} fluffed up with pride, because bravery had turned the mystery into a happy ending.")

    world.facts.update(
        architect=a,
        pappy=p,
        coop=c,
        mystery=m,
        solved=m.solved,
        bravery=a.memes["bravery"],
    )


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    tell_story(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    a = world.facts["architect"]
    p = world.facts["pappy"]
    m = world.facts["mystery"]
    return [
        f"Write an animal story about {a.name}, an architect, finding {m.clue} in a coop.",
        f"Tell a gentle story where a brave {a.species} and a caring pappy solve a mystery with a rhyme.",
        f"Write a short children’s story about a coop, bravery, and a mystery that gets solved.",
    ]


def story_qa(world: World) -> list[QAItem]:
    a = world.facts["architect"]
    p = world.facts["pappy"]
    c = world.facts["coop"]
    m = world.facts["mystery"]
    return [
        QAItem(
            question=f"Who was the architect in {c.name}?",
            answer=f"{a.name}, the {a.species}, was the architect in {c.name}.",
        ),
        QAItem(
            question=f"What mystery did {a.name} find at the coop door?",
            answer=f"{a.name} found {m.clue} at the coop door.",
        ),
        QAItem(
            question=f"How did {a.name} solve the mystery?",
            answer=f"{a.name} solved it by being brave, listening to {p.name}, and noticing that {m.answer}.",
        ),
        QAItem(
            question=f"What did {p.name} do to help?",
            answer=f"{p.name} shared a rhyme that helped {a.name} look carefully and stay brave.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a coop?",
            answer="A coop is a little shelter or pen where birds or farm animals can stay safe.",
        ),
        QAItem(
            question="What does an architect do?",
            answer="An architect plans how a place should be built so it is useful and safe.",
        ),
        QAItem(
            question="What is bravery?",
            answer="Bravery means trying to do something hard or scary even when you feel worried.",
        ),
        QAItem(
            question="What is a rhyme?",
            answer="A rhyme is a little bit of song or verse where words sound alike at the end.",
        ),
    ]


# ---------------------------------------------------------------------------
# CLI helpers
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal story world: coop, architect, pappy, bravery, mystery, rhyme.")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    ap.add_argument("--coop", choices=sorted(COOPS))
    ap.add_argument("--architect-name")
    ap.add_argument("--pappy-name")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    coop_name = args.coop or rng.choice(sorted(COOPS))
    arch_name, arch_species = rng.choice(ARCHITECTS)
    pappy_name, pappy_species = rng.choice(PAPPYS)
    clue, answer = rng.choice(MYSTERIES)
    if args.architect_name:
        arch_name = args.architect_name
    if args.pappy_name:
        pappy_name = args.pappy_name
    return StoryParams(
        seed=args.seed,
        coop_name=coop_name,
        architect_name=arch_name,
        architect_species=arch_species,
        pappy_name=pappy_name,
        pappy_species=pappy_species,
        mystery_clue=clue,
        mystery_answer=answer,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        for i, p in enumerate(sample.prompts, 1):
            print(f"Prompt {i}: {p}")
        print()
        for item in sample.story_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
        print()
        for item in sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for ent in [world.coop, world.architect, world.pappy]:
        lines.append(f"{ent.name}: meters={ent.meters} memes={ent.memes}")
    lines.append(f"mystery: clue={world.mystery.clue!r} answer={world.mystery.answer!r} solved={world.mystery.solved}")
    return "\n".join(lines)


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show solved/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show solved/1."))
        print(sorted(set(asp.atoms(model, "solved"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for i in range(3):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
