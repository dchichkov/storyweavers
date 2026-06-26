#!/usr/bin/env python3
"""
A small slice-of-life story world about a guppy, a cashew, a misunderstanding,
and a brave little fix.
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
class Character:
    name: str
    kind: str
    meme: dict[str, float] = field(default_factory=dict)
    meter: dict[str, float] = field(default_factory=dict)


@dataclass
class StoryParams:
    name: str
    friend_name: str
    place: str
    seed: Optional[int] = None


@dataclass
class World:
    hero: Character
    friend: Character
    place: str
    cashew_state: str = "safe"
    misunderstanding: bool = False
    bravery: bool = False
    facts: dict = field(default_factory=dict)

    def render(self) -> str:
        return self.facts.get("story", "")


NAMES = ["Mina", "Pip", "Nori", "Luna", "Tavi", "Roo", "Milo", "Suri"]
PLACES = ["the pond", "the little market", "the fish bowl", "the sunny kitchen", "the dock"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life guppy/cashew story world.")
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--friend-name", choices=NAMES)
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def valid_places() -> list[str]:
    return list(PLACES)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(valid_places())
    name = args.name or rng.choice(NAMES)
    friend = args.friend_name or rng.choice([n for n in NAMES if n != name])
    return StoryParams(name=name, friend_name=friend, place=place)


def _reasonableness_gate(params: StoryParams) -> None:
    if params.name == params.friend_name:
        raise StoryError("The hero and friend need different names for the misunderstanding to work.")
    if params.place not in PLACES:
        raise StoryError("That place does not belong in this little world.")


def generate(params: StoryParams) -> StorySample:
    _reasonableness_gate(params)

    hero = Character(name=params.name, kind="guppy", meme={"curious": 1.0, "brave": 1.0})
    friend = Character(name=params.friend_name, kind="child", meme={"kind": 1.0})
    world = World(hero=hero, friend=friend, place=params.place)

    lines: list[str] = []
    lines.append(
        f"{hero.name} was a tiny guppy who liked bright mornings and quiet swims at {params.place}."
    )
    lines.append(
        f"One day, {hero.name} found a cashew on a warm stone near {params.place} and stared at it."
    )
    lines.append(
        f"{hero.name} thought the cashew was a tiny shell for fish to hide in, so {hero.name} nudged it closer with care."
    )
    world.misunderstanding = True
    world.facts["misunderstanding"] = "shell"
    lines.append(
        f"{friend.name} saw the little nudges and thought {hero.name} was trying to take the snack away."
    )
    lines.append(
        f"{friend.name} frowned, but {hero.name} lifted a fin and bravely stayed still instead of darting off."
    )
    world.bravery = True
    world.facts["bravery"] = "stayed still"

    lines.append(
        f"Then {hero.name} tapped the cashew and pointed at a hollow leaf beside it, as if to ask a question."
    )
    lines.append(
        f"{friend.name} looked again, laughed softly, and realized the cashew was not a shell at all."
    )
    lines.append(
        f"It was only a snack, and {hero.name} had been trying to share a curious little discovery."
    )
    world.cashew_state = "shared"
    lines.append(
        f"Together they set the cashew on a dry rock, and {hero.name} swam away feeling proud and understood."
    )

    world.facts["story"] = " ".join(lines)

    prompts = [
        "Write a gentle slice-of-life story about a guppy and a cashew.",
        f"Tell a short story set at {params.place} where a small misunderstanding becomes a kind moment.",
        "Write a child-friendly story with a brave guppy and a snack that is mistaken for something else.",
    ]

    story_qa = [
        QAItem(
            question=f"Why did {params.friend_name} first get worried at {params.place}?",
            answer=(
                f"{params.friend_name} got worried because it looked like {params.name} was moving the cashew away, "
                f"when really {params.name} was only being careful and curious."
            ),
        ),
        QAItem(
            question=f"What brave thing did {params.name} do when the misunderstanding happened?",
            answer=(
                f"{params.name} stayed still, lifted a fin, and kept being gentle instead of darting away."
            ),
        ),
        QAItem(
            question="What did they learn about the cashew?",
            answer=(
                "They learned that the cashew was just a snack, not a tiny shell for hiding."
            ),
        ),
    ]

    world_qa = [
        QAItem(
            question="What is a guppy?",
            answer="A guppy is a small fish that can swim quickly and lives in water.",
        ),
        QAItem(
            question="What is a cashew?",
            answer="A cashew is a curved nut that people can eat as a snack.",
        ),
        QAItem(
            question="What does bravery mean?",
            answer="Bravery means staying calm and doing the right thing even when you feel worried.",
        ),
    ]

    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts,
        story_qa=story_qa,
        world_qa=world_qa,
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print()
        print("--- trace ---")
        w = sample.world
        print(f"hero={w.hero.name}, kind={w.hero.kind}, meme={w.hero.meme}, meter={w.hero.meter}")
        print(f"friend={w.friend.name}, kind={w.friend.kind}, meme={w.friend.meme}, meter={w.friend.meter}")
        print(f"place={w.place}, misunderstanding={w.misunderstanding}, bravery={w.bravery}, cashew_state={w.cashew_state}")
    if qa:
        print()
        print("== prompts ==")
        for i, p in enumerate(sample.prompts, 1):
            print(f"{i}. {p}")
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


ASP_RULES = r"""
place(pond; market; bowl; kitchen; dock).

misunderstanding(hero,cashew) :- place(P), hero(H), friend(F), H != F.
brave(hero) :- misunderstanding(hero,cashew).

#show valid_place/1.
valid_place(P) :- place(P).
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [asp.fact("place", "pond"),
         asp.fact("place", "market"),
         asp.fact("place", "bowl"),
         asp.fact("place", "kitchen"),
         asp.fact("place", "dock")]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_places() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_place/1."))
    return sorted(set(asp.atoms(model, "valid_place")))


def asp_verify() -> int:
    py = set((p,) for p in valid_places())
    cl = set(asp_valid_places())
    if py == cl:
        print(f"OK: clingo gate matches valid_places() ({len(py)} places).")
        return 0
    print("MISMATCH between clingo and Python gate:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def generation_samples(args: argparse.Namespace) -> list[StoryParams]:
    if args.all:
        out: list[StoryParams] = []
        for i, place in enumerate(PLACES):
            name = NAMES[i % len(NAMES)]
            friend = NAMES[(i + 1) % len(NAMES)]
            if friend == name:
                friend = NAMES[(i + 2) % len(NAMES)]
            out.append(StoryParams(name=name, friend_name=friend, place=place))
        return out
    base = args.seed if args.seed is not None else random.randrange(2**31)
    rng = random.Random(base)
    return [resolve_params(args, random.Random(base + i)) for i in range(args.n)]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid_place/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("\n".join(f"{p[0]}" for p in asp_valid_places()))
        return

    samples: list[StorySample] = []
    for i, params in enumerate(generation_samples(args)):
        params.seed = (args.seed if args.seed is not None else 0) + i
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
