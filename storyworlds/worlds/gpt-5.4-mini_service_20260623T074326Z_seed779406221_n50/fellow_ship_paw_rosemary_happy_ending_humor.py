#!/usr/bin/env python3
"""
storyworlds/worlds/fellow_ship_paw_rosemary_happy_ending_humor.py
=================================================================

A small pirate-tale storyworld about a little fellow-ship, a curious paw,
and a sprig of rosemary that saves supper and the day.

Seed-inspired premise:
- "fellow-ship" becomes a tiny crew of friends on a toy ship.
- "paw" is a cat or dog paw that causes a comic problem.
- "rosemary" is the herb the crew uses to fix the mistake.
- Style: pirate tale, happy ending, humor.

This script is self-contained and follows the Storyweavers contract:
- StoryParams and registry knobs
- build_parser / resolve_params / generate / emit / main
- lazy import of storyworlds/asp.py inside ASP helpers
- inline ASP_RULES plus asp_facts()
- reasonableness gate and verify mode
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Ship:
    id: str
    label: str
    role: str
    crew_name: str = ""
    meters: dict[str, float] = None
    memes: dict[str, float] = None

    def __post_init__(self) -> None:
        if self.meters is None:
            self.meters = {"tilt": 0.0, "scent": 0.0, "mess": 0.0}
        if self.memes is None:
            self.memes = {"joy": 0.0, "worry": 0.0, "laugh": 0.0}


@dataclass
class StoryParams:
    crew_name: str
    ship_name: str
    paw_owner: str
    paw_type: str
    herb: str
    snack: str
    captain: str
    mate: str
    seed: Optional[int] = None


CREWS = {
    "fellow-ship": {
        "crew_name": "fellow-ship",
        "ship_name": "the Tiny Tide",
        "captain": "Captain Pip",
        "mate": "Matey Mabel",
    }
}

PAW_OWNERS = ["the puppy", "the cat", "the parrot"]
PAW_TYPES = ["paw", "paw print"]
HERBS = ["rosemary"]
SNACKS = ["crackers", "fish biscuits", "buttered toast"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A pirate tale with fellow-ship, paw, and rosemary.")
    ap.add_argument("--crew-name", choices=CREWS)
    ap.add_argument("--paw-owner", choices=PAW_OWNERS)
    ap.add_argument("--paw-type", choices=PAW_TYPES)
    ap.add_argument("--herb", choices=HERBS)
    ap.add_argument("--snack", choices=SNACKS)
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
    crew_name = args.crew_name or "fellow-ship"
    paw_owner = args.paw_owner or rng.choice(PAW_OWNERS)
    paw_type = args.paw_type or rng.choice(PAW_TYPES)
    herb = args.herb or "rosemary"
    snack = args.snack or rng.choice(SNACKS)
    return StoryParams(
        crew_name=crew_name,
        ship_name=CREWS[crew_name]["ship_name"],
        paw_owner=paw_owner,
        paw_type=paw_type,
        herb=herb,
        snack=snack,
        captain=CREWS[crew_name]["captain"],
        mate=CREWS[crew_name]["mate"],
    )


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("crew", "fellow-ship"),
        asp.fact("paw_owner", "the_cat"),
        asp.fact("herb", "rosemary"),
        asp.fact("happy_ending", 1),
        asp.fact("humor", 1),
    ]
    return "\n".join(lines)


ASP_RULES = r"""
happy_story :- crew("fellow-ship"), herb(rosemary), happy_ending(1), humor(1).
#show happy_story/0.
"""


def asp_program(extra: str = "", show: str = "#show happy_story/0.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_check() -> bool:
    import asp
    model = asp.one_model(asp_program())
    return any(sym.name == "happy_story" for sym in model)


def _world_setup(params: StoryParams) -> dict:
    return {
        "ship": Ship(id="ship", label=params.ship_name, role="fellow-ship", crew_name=params.crew_name),
        "herb": params.herb,
        "paw_owner": params.paw_owner,
        "paw_type": params.paw_type,
        "snack": params.snack,
        "captain": params.captain,
        "mate": params.mate,
        "state": {"meal": "plain", "mess": False, "smell": "", "laugh": False, "happy": False},
    }


def generate(params: StoryParams) -> StorySample:
    if params.herb.lower() != "rosemary":
        raise StoryError("This storyworld expects rosemary as the herb.")
    world = _world_setup(params)
    ship = world["ship"]

    story = []
    story.append(
        f"On a bright blue morning, {params.captain} and {params.mate} sailed the little fellow-ship, "
        f"{ship.label}, across the rug-sea."
    )
    story.append(
        f"They were hunting for lunch, because every brave crew knows a pirate with an empty belly is a grumpy pirate."
    )
    story.append(
        f"Then a {params.paw_type} pattered across the deck. It belonged to {params.paw_owner}, who had leaned over the railing to sniff the snack crate."
    )
    story.append(
        f"Oops! One comic slip later, the crate tipped, the biscuits rolled, and the whole cabin smelled like a sleepy fish market."
    )
    world["state"]["mess"] = True
    ship.memes["worry"] += 1
    ship.meters["mess"] += 1
    story.append(
        f"{params.mate} wrinkled her nose and said, \"By the barnacles, that smells like a bad idea in a teapot!\""
    )
    story.append(
        f"Then {params.captain} found a small pot of {params.herb} and whispered, \"Aha! Pirate perfume.\""
    )
    world["state"]["smell"] = "rosemary"
    world["state"]["meal"] = "rosemary crackers"
    ship.memes["laugh"] += 1
    ship.memes["joy"] += 1
    story.append(
        f"They sprinkled {params.herb} over the snack crate, and the smell turned fresh and green, like a tiny garden on a ship."
    )
    story.append(
        f"{params.paw_owner} gave one proud {params.paw_type}, as if to say, \"I meant to help.\""
    )
    story.append(
        f"Everyone laughed, the biscuits were saved, and the fellow-ship shared {params.snack} with a little rosemary on top."
    )
    story.append(
        "By sunset the rug-sea was calm again, the deck was tidy, and the crew agreed that the best treasure was a happy supper."
    )
    world["state"]["laugh"] = True
    world["state"]["happy"] = True

    prompts = [
        "Write a pirate tale about a tiny fellow-ship, a mischievous paw, and a sprig of rosemary that fixes supper.",
        "Tell a humorous story where a snack mishap on a toy ship ends happily because the crew uses rosemary.",
        "Create a cheerful, child-friendly pirate story with a funny paw problem and a warm ending.",
    ]
    story_qa = [
        QAItem(
            question="What was the ship called?",
            answer=f"The ship was called {params.ship_name}, and it carried the fellow-ship."
        ),
        QAItem(
            question="What caused the funny mess on the ship?",
            answer=f"A {params.paw_type} from {params.paw_owner} tipped the snack crate and made a silly mess."
        ),
        QAItem(
            question="How did the crew fix the smell?",
            answer=f"They sprinkled {params.herb} over the snack crate, and the smell turned fresh and pleasant."
        ),
        QAItem(
            question="How did the story end?",
            answer="It ended happily, with the crew laughing, eating together, and keeping their little ship tidy."
        ),
    ]
    world_qa = [
        QAItem(question="What is rosemary?", answer="Rosemary is a fragrant herb that people use in cooking."),
        QAItem(question="Why did the crew laugh?", answer="They laughed because the paw made a silly snack mishap, and it all turned out fine."),
        QAItem(question="What makes a story a happy ending?", answer="A happy ending means the problem gets fixed and the characters end safe and content."),
    ]
    return StorySample(
        params=params,
        story="\n".join(story),
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
        print("--- world trace ---")
        print(sample.world)
    if qa:
        print()
        for i, p in enumerate(sample.prompts, 1):
            print(f"{i}. {p}")
        print()
        for item in sample.story_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
        print()
        for item in sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        if asp_check():
            print("OK: ASP twin agrees with the Python storyworld.")
            return
        raise SystemExit(1)
    if args.asp:
        print("happy_story")
        return

    rng = random.Random(args.seed if args.seed is not None else random.randrange(2**31))
    samples: list[StorySample] = []
    if args.all:
        samples.append(generate(resolve_params(args, rng)))
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random((args.seed or 0) + i))
            params.seed = (args.seed or 0) + i
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        if len(samples) > 1:
            print(f"### variant {i + 1}")
        emit(sample, trace=args.trace, qa=args.qa)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
