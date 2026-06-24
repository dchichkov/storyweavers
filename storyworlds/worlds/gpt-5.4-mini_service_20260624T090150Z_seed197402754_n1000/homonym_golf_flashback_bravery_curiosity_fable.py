#!/usr/bin/env python3
"""
A small storyworld: a curious fable about homonyms on a golf course, with a
flashback that explains why bravery mattered.
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
class Place:
    name: str = "the green"
    detail: str = "a neat golf green with a little sand bunker"
    affords: set[str] = field(default_factory=lambda: {"golf"})


@dataclass
class Hero:
    name: str
    species: str
    trait: str
    meme: dict[str, float] = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=dict)


@dataclass
class ObjectThing:
    name: str
    phrase: str
    kind: str
    owner: Optional[str] = None


@dataclass
class StoryParams:
    name: str
    species: str
    trait: str
    place: str = "green"
    seed: Optional[int] = None


PLACES = {
    "green": Place(),
}

HEROES = {
    "fox": ("fox", ["curious", "brave", "gentle"]),
    "rabbit": ("rabbit", ["curious", "brave", "kind"]),
    "mole": ("mole", ["curious", "brave", "steady"]),
}

NAMES = {
    "fox": ["Fenn", "Ruby", "Milo", "Pip"],
    "rabbit": ["Hazel", "Bram", "Luna", "Toby"],
    "mole": ["Dot", "Nell", "Otis", "Wren"],
}


class World:
    def __init__(self, place: Place, hero: Hero, ball: ObjectThing):
        self.place = place
        self.hero = hero
        self.ball = ball
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def say(self, text: str) -> None:
        self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


ASP_RULES = r"""
homonym(golf, hole).
homonym(golf, whole).

curious(X) :- hero(X).
brave(X) :- hero(X), flashback_helped(X).
"""


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("place", "green"),
        asp.fact("activity", "golf"),
        asp.fact("hero", "hero"),
        asp.fact("flashback", "past_care"),
        asp.fact("quality", "bravery"),
        asp.fact("quality", "curiosity"),
        asp.fact("word", "homonym"),
        asp.fact("word", "golf"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny fable about homonyms and golf.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--name")
    ap.add_argument("--species", choices=sorted(HEROES))
    ap.add_argument("--trait")
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    species = args.species or rng.choice(list(HEROES))
    trait = args.trait or rng.choice(HEROES[species][1])
    name = args.name or rng.choice(NAMES[species])
    return StoryParams(name=name, species=species, trait=trait, place=args.place or "green")


def generate(params: StoryParams) -> StorySample:
    hero = Hero(name=params.name, species=params.species, trait=params.trait)
    place = PLACES[params.place]
    ball = ObjectThing(name="golf ball", phrase="a shiny golf ball", kind="ball", owner=hero.name)
    world = World(place, hero, ball)

    hero.meme["curiosity"] = 1.0
    world.say(
        f"On a quiet morning at {place.name}, {hero.name} the {hero.species} looked at "
        f"{ball.phrase} and wondered about the game of golf."
    )
    world.say(
        f"{hero.name} had once heard a flashback from an old owl: a golfer smiled and said "
        f"that a homonym can sound the same while meaning something else."
    )
    world.para()
    world.say(
        f"Today, {hero.name} found a sign for the hole by the green and paused, because "
        f"the word hole sounded like whole, and that made {hero.name} curious."
    )
    world.say(
        f"Instead of laughing at the mix-up, {hero.name} took a brave breath, asked a caddy "
        f"to explain, and learned that a golf hole is a place for the ball, while whole means complete."
    )
    world.para()
    hero.meme["bravery"] = 1.0
    world.say(
        f"With a brave heart and a curious mind, {hero.name} teed up the ball, took a careful swing, "
        f"and sent it toward the hole."
    )
    world.say(
        f"When the ball rolled in, {hero.name} smiled at the lesson: asking questions can be as wise "
        f"as winning a game."
    )

    world.facts = {
        "hero": hero,
        "place": place,
        "ball": ball,
        "flashback": True,
        "bravery": True,
        "curiosity": True,
    }

    prompts = [
        f"Write a fable about {params.name} the {params.species} who learns a homonym on a golf green.",
        f"Tell a short story with a flashback, bravery, and curiosity at {place.name}.",
        "Write a child-friendly fable where a golf word sounds like another word and the hero asks a question.",
    ]

    story_qa = [
        QAItem(
            question=f"Why did {params.name} pause when seeing the sign near the golf hole?",
            answer=(
                f"{params.name} paused because the word hole sounded like whole, and that homonym made "
                f"{params.name} curious."
            ),
        ),
        QAItem(
            question=f"What did the flashback teach {params.name} about the game of golf?",
            answer=(
                "The flashback explained that words can sound the same and mean different things, "
                "so it helped the hero understand the sign."
            ),
        ),
        QAItem(
            question=f"How did {params.name} show bravery in the story?",
            answer=(
                f"{params.name} showed bravery by asking for help, taking a careful swing, and trying again "
                f"instead of getting stuck on the confusing word."
            ),
        ),
    ]

    world_qa = [
        QAItem(
            question="What is a homonym?",
            answer="A homonym is a word that sounds like another word but has a different meaning.",
        ),
        QAItem(
            question="What is golf?",
            answer="Golf is a game where players try to get a ball into a hole with as few swings as they can.",
        ),
        QAItem(
            question="What is curiosity?",
            answer="Curiosity is the wish to learn and ask questions about things you do not yet understand.",
        ),
        QAItem(
            question="What is bravery?",
            answer="Bravery is doing something hard or scary even when you feel nervous.",
        ),
    ]

    return StorySample(params=params, story=world.render(), prompts=prompts, story_qa=story_qa, world_qa=world_qa, world=world)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print("--- world trace ---")
        hero = sample.world.facts["hero"]
        print(f"hero={hero.name} species={hero.species} meme={hero.meme}")
    if qa:
        print()
        print("== prompts ==")
        for p in sample.prompts:
            print(p)
        print()
        print("== story qa ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
        print()
        print("== world qa ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")


def verify() -> int:
    try:
        import asp
    except Exception as exc:
        raise StoryError(f"ASP verification requires clingo/asp helper: {exc}") from exc
    model = asp.one_model(asp_program("#show homonym/2."))
    atoms = set(asp.atoms(model, "homonym"))
    expected = {("golf", "hole"), ("golf", "whole")}
    if atoms != expected:
        print("MISMATCH between ASP and Python expectations")
        print("ASP:", sorted(atoms))
        print("PY :", sorted(expected))
        return 1
    sample = generate(StoryParams(name="Pip", species="fox", trait="curious"))
    if not sample.story.strip():
        print("Story generation failed")
        return 1
    print("OK: ASP parity and generated story check passed.")
    return 0


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show homonym/2."))
        return
    if args.verify:
        sys.exit(verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show homonym/2."))
        pairs = sorted(set(asp.atoms(model, "homonym")))
        print(f"{len(pairs)} homonym facts:")
        for a, b in pairs:
            print(f"  {a} -> {b}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        for species in sorted(HEROES):
            params = StoryParams(
                name=NAMES[species][0],
                species=species,
                trait=HEROES[species][1][0],
                place="green",
                seed=base_seed,
            )
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        for i in range(args.n):
            rng = random.Random(base_seed + i)
            params = resolve_params(args, rng)
            params.seed = base_seed + i
            sample = generate(params)
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

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
