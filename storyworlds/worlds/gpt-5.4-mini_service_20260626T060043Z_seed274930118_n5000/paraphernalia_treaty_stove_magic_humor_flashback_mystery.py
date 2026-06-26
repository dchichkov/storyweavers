#!/usr/bin/env python3
"""
A small mystery storyworld about a missing treaty, odd paraphernalia, a stove,
and a harmless bit of magic with a flashback-shaped reveal.

The domain is intentionally tiny and classical:
- A child notices strange clues around a kitchen.
- The clues point to the stove and a bundle of paraphernalia.
- A treaty between two pretend kingdoms has gone missing.
- A flashback explains why the treaty was hidden.
- Humor and a little magic help solve the mystery.
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Any, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------

@dataclass
class Entity:
    id: str
    kind: str
    label: str
    phrase: str
    owner: Optional[str] = None
    keeper: Optional[str] = None
    location: str = ""
    hidden: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"order": 0.0, "mystery": 0.0, "warmth": 0.0, "smoke": 0.0}
        if not self.memes:
            self.memes = {"curiosity": 0.0, "worry": 0.0, "relief": 0.0, "humor": 0.0, "magic": 0.0}

    def pronoun(self) -> str:
        return "it" if self.kind != "character" else "they"


@dataclass
class Place:
    name: str
    indoors: bool = True
    affordances: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    hero: str
    helper: str
    flashback_years_ago: int
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, Any] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.trace: list[str] = []

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def note(self, text: str) -> None:
        self.trace.append(text)


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

PLACES = {
    "kitchen": Place(name="the kitchen", indoors=True, affordances={"stove", "magic", "humor", "flashback"}),
    "back_room": Place(name="the back room", indoors=True, affordances={"stove", "magic", "humor", "flashback"}),
    "museum_kitchen": Place(name="the museum kitchen", indoors=True, affordances={"stove", "magic", "humor", "flashback"}),
}

HERO_NAMES = ["Mina", "Toby", "Nora", "Pip", "Lena", "Milo"]
HELPER_NAMES = ["Aunt Joy", "Uncle Ben", "Ms. Roo", "Mr. Bell"]

PARAPHERNALIA = {
    "ribbon_bundle": {
        "label": "a bundle of paraphernalia",
        "phrase": "a bundle of odd paraphernalia tied with blue ribbon",
        "location": "on the table",
    },
    "magnets": {
        "label": "a tin of paraphernalia",
        "phrase": "a tin full of tiny paraphernalia and shiny magnets",
        "location": "on a shelf",
    },
    "keys": {
        "label": "a ring of paraphernalia",
        "phrase": "a ring of little paraphernalia labels and brass keys",
        "location": "beside the stove",
    },
}

TREATIES = {
    "sun_moon": {
        "label": "the treaty",
        "phrase": "a peace treaty between the Sun Garden and the Moon Garden",
    },
    "river_meadow": {
        "label": "the treaty",
        "phrase": "a treaty for sharing the River Path and the Meadow Gate",
    },
    "owl_fox": {
        "label": "the treaty",
        "phrase": "a treaty that let the Owl Library and Fox Post share one quiet hall",
    },
}


# ---------------------------------------------------------------------------
# Parameters and parser
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mystery storyworld with magic, humor, and flashback.")
    ap.add_argument("--place", choices=PLACES.keys())
    ap.add_argument("--hero")
    ap.add_argument("--helper")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(list(PLACES.keys()))
    hero = args.hero or rng.choice(HERO_NAMES)
    helper = args.helper or rng.choice(HELPER_NAMES)
    flashback_years_ago = rng.choice([1, 2, 3, 4, 5])
    return StoryParams(place=place, hero=hero, helper=helper, flashback_years_ago=flashback_years_ago)


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------

def _mystery_seed() -> tuple[str, str]:
    treaty_key = random.choice(list(TREATIES.keys()))
    paraphernalia_key = random.choice(list(PARAPHERNALIA.keys()))
    return treaty_key, paraphernalia_key


def generate(params: StoryParams) -> StorySample:
    place = PLACES[params.place]
    world = World(place)

    treaty_key, paraphernalia_key = _mystery_seed()
    treaty_cfg = TREATIES[treaty_key]
    par_cfg = PARAPHERNALIA[paraphernalia_key]

    hero = world.add(Entity(
        id="hero",
        kind="character",
        label=params.hero,
        phrase=f"{params.hero}, a curious child",
        location=place.name,
    ))
    helper = world.add(Entity(
        id="helper",
        kind="character",
        label=params.helper,
        phrase=f"{params.helper}, the helper",
        location=place.name,
    ))
    stove = world.add(Entity(
        id="stove",
        kind="thing",
        label="stove",
        phrase="the old stove with a round iron door",
        location=place.name,
    ))
    paraphernalia = world.add(Entity(
        id="paraphernalia",
        kind="thing",
        label="paraphernalia",
        phrase=par_cfg["phrase"],
        location=par_cfg["location"],
    ))
    treaty = world.add(Entity(
        id="treaty",
        kind="thing",
        label="treaty",
        phrase=treaty_cfg["phrase"],
        location="hidden behind the stove",
        hidden=True,
    ))

    # Physical/emotional state
    hero.memes["curiosity"] += 2
    hero.memes["worry"] += 1
    helper.memes["humor"] += 1
    stove.meters["warmth"] += 1
    stove.meters["mystery"] += 2
    paraphernalia.meters["mystery"] += 1
    treaty.meters["mystery"] += 2

    # Setup
    world.say(f"{hero.label} lived in {place.name} and liked noticing small odd things.")
    world.say(f"One afternoon, {hero.label} saw {par_cfg['phrase']} {par_cfg['location']} near {stove.label}.")
    world.say(f"Something was missing too: {treaty_cfg['phrase']}, and nobody could find {treaty.label}.")

    # Mystery turn
    world.para()
    world.say(f"{hero.label} peered at the stove, because the handle was warm even though nobody had cooked yet.")
    world.say(f"{hero.label} also found a clue: a faint ribbon mark on the floor, as if something had been dragged and hidden.")
    world.say(f"{helper.label} looked serious for one second, then said, 'This is a proper kitchen mystery.'")
    hero.memes["curiosity"] += 1
    hero.memes["worry"] += 1

    # Flashback
    world.para()
    world.say(f"Then the room flickered, and the story slipped into a flashback from {params.flashback_years_ago} years ago.")
    world.say(f"Back then, {helper.label} had tucked {treaty.label} behind the stove during a game of 'Important Papers, Very Secret.'")
    world.say(f"{helper.label} had also stored {par_cfg['phrase']} nearby because one of the little tags looked like a clue, but it was only a joke.")
    world.say(f"That was funny now, because the 'secret hideout' was just the warm space where dust bunnies went to nap.")

    # Magic and resolution
    world.para()
    world.say(f"{hero.label} gently tapped the stove door, and a tiny sparkle danced out like a shy firefly.")
    hero.memes["magic"] += 1
    world.say(f"The sparkle pointed straight behind the stove, where {treaty.label} had been hiding all along.")
    treaty.hidden = False
    treaty.location = place.name
    world.say(f"{hero.label} pulled out {treaty_cfg['phrase']}.")
    world.say(f"{helper.label} laughed and said the stove had been acting like a stubborn old vault, which was silly because it was just a stove.")
    hero.memes["humor"] += 1
    hero.memes["relief"] += 2
    helper.memes["relief"] += 1
    world.say(f"In the end, the treaty was safe, the paraphernalia was no longer suspicious, and the mystery was solved.")

    world.facts.update({
        "hero": hero,
        "helper": helper,
        "stove": stove,
        "paraphernalia": paraphernalia,
        "treaty": treaty,
        "place": place,
        "flashback_years_ago": params.flashback_years_ago,
        "treaty_phrase": treaty_cfg["phrase"],
        "paraphernalia_phrase": par_cfg["phrase"],
    })

    prompts = [
        f"Write a short mystery for children set in {place.name} with a stove, a treaty, and a bundle of paraphernalia.",
        f"Tell a gentle story where {params.hero} and {params.helper} solve a kitchen mystery with a tiny bit of magic.",
        f"Write a funny flashback story about a missing treaty hiding behind a stove.",
    ]

    story_qa = [
        QAItem(
            question=f"What was missing from {place.name}?",
            answer=f"The missing thing was {treaty_cfg['phrase']}.",
        ),
        QAItem(
            question=f"Where was the treaty found?",
            answer="It was found behind the stove.",
        ),
        QAItem(
            question=f"Why did the story have a flashback?",
            answer=f"It flashed back to {params.flashback_years_ago} years ago to explain why the treaty had been hidden.",
        ),
        QAItem(
            question=f"What helped solve the mystery?",
            answer="A tiny sparkle of magic pointed to the hiding spot, and that helped them find the treaty.",
        ),
        QAItem(
            question=f"What made the story a little funny?",
            answer=f"The helper said the stove was acting like a stubborn old vault, which was silly because it was only a stove.",
        ),
    ]

    world_qa = [
        QAItem(
            question="What is a treaty?",
            answer="A treaty is an agreement between groups or people about how they will share, help, or stay peaceful.",
        ),
        QAItem(
            question="What is paraphernalia?",
            answer="Paraphernalia means a collection of extra tools, objects, or things used for a task or activity.",
        ),
        QAItem(
            question="What does a stove do?",
            answer="A stove is used for cooking and heating food.",
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
        print("\n--- trace ---")
        for line in sample.world.trace:
            print(line)
    if qa:
        print("\n--- prompts ---")
        for i, p in enumerate(sample.prompts, 1):
            print(f"{i}. {p}")
        print("\n--- story qa ---")
        for item in sample.story_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
        print("\n--- world qa ---")
        for item in sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")


def to_jsonable(sample: StorySample) -> dict:
    return sample.to_dict()


def main() -> None:
    args = build_parser().parse_args()
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    if args.show_asp:
        print("% No ASP twin is used in this compact world.")
        return
    if args.verify:
        print("OK: no ASP rules to verify in this world.")
        return
    if args.asp:
        print("[]")
        return

    samples: list[StorySample] = []

    if args.all:
        combos = [
            StoryParams(place=place, hero=hero, helper=helper, flashback_years_ago=2)
            for place in PLACES
            for hero in HERO_NAMES[:2]
            for helper in HELPER_NAMES[:1]
        ]
        for params in combos:
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            rng = random.Random(base_seed + i)
            i += 1
            params = resolve_params(args, rng)
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if args.json:
        if len(samples) == 1:
            print(json.dumps(to_jsonable(samples[0]), indent=2, ensure_ascii=False))
        else:
            print(json.dumps([to_jsonable(s) for s in samples], indent=2, ensure_ascii=False))
        return

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
