#!/usr/bin/env python3
"""
A standalone story world for a small Animal Story about a misunderstanding on a branch.
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


@dataclass
class Creature:
    id: str
    kind: str = "animal"
    species: str = "animal"
    name: str = ""
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=lambda: {"balance": 0.0, "leaf": 0.0})
    memes: dict[str, float] = field(default_factory=lambda: {"worry": 0.0, "confusion": 0.0, "relief": 0.0, "kindness": 0.0})
    perched_on: str = ""
    holding: str = ""

    def label(self) -> str:
        return self.name or self.id


@dataclass
class Branch:
    id: str = "branch"
    meters: dict[str, float] = field(default_factory=lambda: {"sway": 0.0, "leaves": 1.0})


class World:
    def __init__(self) -> None:
        self.creatures: dict[str, Creature] = {}
        self.branch = Branch()
        self.lines: list[str] = []
        self.facts: dict = {}

    def add(self, c: Creature) -> Creature:
        self.creatures[c.id] = c
        return c

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def render(self) -> str:
        return " ".join(self.lines)


@dataclass
class StoryParams:
    seed: Optional[int] = None
    name_a: str = "Milo"
    name_b: str = "Pip"
    species_a: str = "squirrel"
    species_b: str = "bird"
    trait_a: str = "careful"
    trait_b: str = "tiny"
    setting: str = "the oak tree"
    misunderstanding: str = "needs help"
    object: str = "a berry"


SPECIES = ["squirrel", "bird", "rabbit", "fox", "mouse"]
TRAITS = ["careful", "curious", "brave", "tiny", "bouncy", "gentle"]
NAMES = ["Milo", "Pip", "Nia", "Toby", "Luna", "Mina", "Bea", "Ollie"]
OBJECTS = ["a berry", "a leaf cap", "a shiny acorn", "a nest twig"]
SETTINGS = ["the oak tree", "the apple tree", "the park tree"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal Story world with a misunderstanding on a branch.")
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    ap.add_argument("--name-a")
    ap.add_argument("--name-b")
    ap.add_argument("--species-a", choices=SPECIES)
    ap.add_argument("--species-b", choices=SPECIES)
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return StoryParams(
        seed=args.seed,
        name_a=args.name_a or rng.choice(NAMES),
        name_b=args.name_b or rng.choice([n for n in NAMES if n != (args.name_a or "")]),
        species_a=args.species_a or rng.choice(SPECIES),
        species_b=args.species_b or rng.choice(SPECIES),
        trait_a=rng.choice(TRAITS),
        trait_b=rng.choice(TRAITS),
        setting=rng.choice(SETTINGS),
        misunderstanding="needs help",
        object=rng.choice(OBJECTS),
    )


def reasonableness_gate(params: StoryParams) -> None:
    if params.species_a == params.species_b and params.name_a == params.name_b:
        raise StoryError("The two animals must be different enough to make a real misunderstanding.")
    if not params.setting or "tree" not in params.setting:
        raise StoryError("This story needs a branch setting.")
    if params.object not in OBJECTS:
        raise StoryError("Unknown object for the branch story.")


def ASP_RULES() -> str:
    return r"""
    on_branch(a).
    on_branch(b).
    misunderstanding(a,b) :- worry(a), sees(b), on_branch(a), on_branch(b).
    resolved(a,b) :- explain(a,b), misunderstanding(a,b).
    """


def asp_facts() -> str:
    import storyworlds.asp as asp
    return "\n".join([
        asp.fact("worry", "a"),
        asp.fact("sees", "b"),
        asp.fact("on_branch", "a"),
        asp.fact("on_branch", "b"),
        asp.fact("explain", "a", "b"),
    ])


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES()}\n{show}\n"


def asp_verify() -> int:
    try:
        import storyworlds.asp as asp
    except Exception:
        print("clingo/asp helper unavailable.")
        return 1
    model = asp.one_model(asp_program("#show misunderstanding/2. #show resolved/2."))
    atoms = {(a.name, tuple(arg.name if arg.type == 1 else arg.string if arg.type == 3 else arg.number for arg in a.arguments)) for a in model}
    expected = {("misunderstanding", ("a", "b")), ("resolved", ("a", "b"))}
    if atoms == expected:
        print("OK: ASP parity check passed.")
        return 0
    print("Mismatch:", atoms, expected)
    return 1


def generate(params: StoryParams) -> StorySample:
    reasonableness_gate(params)
    world = World()
    a = world.add(Creature(id="a", species=params.species_a, name=params.name_a, traits=[params.trait_a]))
    b = world.add(Creature(id="b", species=params.species_b, name=params.name_b, traits=[params.trait_b]))
    world.branch.meters["sway"] = 0.5

    a.perched_on = world.branch.id
    b.perched_on = world.branch.id
    a.memes["worry"] += 1
    a.memes["confusion"] += 1
    a.meters["leaf"] += 1

    world.say(f"One day, {a.label()} the {a.species} was on {params.setting}, high on a branch.")
    world.say(f"{a.label()} saw {b.label()} and thought {b.label()} {params.misunderstanding} {params.object}.")
    world.say(f"So {a.label()} hurried over and picked up {params.object}, trying to be kind.")
    world.say(f"But {b.label()} blinked and laughed softly. {params.object.capitalize()} was not lost at all.")
    world.say(f"It had been part of a small game, and {b.label()} only wanted to share it.")

    a.memes["worry"] = 0.0
    a.memes["confusion"] = 0.0
    a.memes["relief"] += 1
    a.memes["kindness"] += 1
    b.memes["relief"] += 1
    b.memes["kindness"] += 1
    world.branch.meters["sway"] = 0.0
    world.branch.meters["leaves"] += 0.5

    world.say(f"{a.label()} smiled, gave back {params.object}, and the two animals shared it on the branch.")
    world.say(f"Before long, the branch was calm again, and the little animals sat together under the leaves.")

    world.facts = {"a": a, "b": b, "params": params}
    story_qa = [
        QAItem(
            question=f"Why did {a.label()} bring over {params.object}?",
            answer=f"{a.label()} misunderstood what {b.label()} needed and thought {b.label()} was looking for {params.object}.",
        ),
        QAItem(
            question=f"What fixed the misunderstanding?",
            answer=f"{b.label()} explained that {params.object} was part of a game, and then both animals shared it kindly.",
        ),
        QAItem(
            question=f"Where did the story happen?",
            answer=f"It happened on a branch at {params.setting}, high in the tree.",
        ),
    ]
    world_qa = [
        QAItem(question="What is a branch?", answer="A branch is a part of a tree that grows out from the trunk and can hold leaves, nests, or small animals."),
        QAItem(question="Why do animals sometimes misunderstand each other?", answer="Animals can misunderstand when they do not see the whole situation and guess the wrong reason for another animal's behavior."),
    ]
    prompts = [
        f"Write a gentle Animal Story about two animals on a branch who have a misunderstanding.",
        f"Tell a short story where {a.label()} thinks {b.label()} needs help with {params.object}, but that is not true.",
        f"Write a child-friendly story using the words improvise and branch, ending with kindness and relief.",
    ]
    return StorySample(params=params, story=world.render(), prompts=prompts, story_qa=story_qa, world_qa=world_qa, world=world)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        w = sample.world
        print("--- trace ---")
        for c in w.creatures.values():
            print(c.id, c.species, c.name, dict(c.meters), dict(c.memes), c.perched_on)
        print("branch", dict(w.branch.meters))
    if qa:
        print()
        for item in sample.story_qa:
            print(f"Q: {item.question}\nA: {item.answer}")
        for item in sample.world_qa:
            print(f"Q: {item.question}\nA: {item.answer}")


def curated() -> list[StoryParams]:
    return [
        StoryParams(name_a="Milo", name_b="Pip", species_a="squirrel", species_b="bird", trait_a="careful", trait_b="tiny", setting="the oak tree", object="a berry"),
        StoryParams(name_a="Nia", name_b="Toby", species_a="rabbit", species_b="mouse", trait_a="curious", trait_b="gentle", setting="the apple tree", object="a leaf cap"),
    ]


def main() -> None:
    args = build_parser().parse_args()
    if args.verify:
        sys.exit(asp_verify())
    if args.show_asp:
        print(asp_program("#show misunderstanding/2. #show resolved/2."))
        return

    if args.all:
        samples = [generate(p) for p in curated()]
    else:
        base = args.seed if args.seed is not None else random.randrange(2**31)
        samples = []
        seen = set()
        i = 0
        while len(samples) < args.n and i < args.n * 20 + 20:
            params = resolve_params(args, random.Random(base + i))
            i += 1
            try:
                sample = generate(params)
            except StoryError as e:
                print(e)
                return
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

    for idx, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {idx + 1}" if len(samples) > 1 else "")
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
