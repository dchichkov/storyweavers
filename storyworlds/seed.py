#!/usr/bin/env python3
"""
storyworlds/seed.py
===================

Tiny generator of *story seeds* -- short prompts that pin a handful of words plus
narrative instruments and a style, e.g.:

    Write a story that includes the following words and narrative instruments.
    Words: ride, moon, upset
    Setting: school garden
    Features: Dialogue, Cautionary, Conflict
    Style: Fairy Tale

It just enumerates pools (words / settings / features / styles) and samples a random,
reproducible combination.

Run it
------
    python storyworlds/seed.py                 # one random seed
    python storyworlds/seed.py -n 5 --seed 7   # five reproducible seeds
    python storyworlds/seed.py --words 4        # pin how many words to include
"""
from __future__ import annotations

import argparse
import random
from dataclasses import dataclass
from pathlib import Path


CHILDES_VOCAB_PATH = Path(__file__).resolve().parent / "data" / "childes" / "childes_eng_na_vocab.txt"


def _load_childes_words(path: Path) -> list[str]:
    words: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line or line.startswith("#"):
            continue
        words.append(line.split("\t", 1)[0])
    if not words:
        raise RuntimeError(f"no words found in {path}")
    return words


WORDS = list(dict.fromkeys(
    _load_childes_words(CHILDES_VOCAB_PATH)
))
SETTING_PROBABILITY = 0.10

FEATURES = [
    "Dialogue",
    "Conflict",
    "Cautionary",
    "Moral Value",
    "Twist",
    "Foreshadowing",
    "Bad Ending",
    "Happy Ending",
    "Friendship",
    "Problem Solving",
    "Repetition",
    "Surprise",
    "Humor",
    "Suspense",
    "Lesson Learned",
    "Teamwork",
    "Kindness",
    "Bravery",
    "Mystery to Solve",
    "Quest",
    "Transformation",
    "Misunderstanding",
    "Reconciliation",
    "Sharing",
    "Curiosity",
    "Magic",
    "Rhyme",
    "Sound Effects",
    "Inner Monologue",
    "Flashback",
]

SETTINGS = [
    "beach",
    "seaside promenade",
    "tidal pool",
    "airport",
    "train station",
    "bus stop",
    "school",
    "kindergarten",
    "classroom",
    "school library",
    "art room",
    "music room",
    "science corner",
    "playground",
    "sandbox",
    "splash pad",
    "skate park",
    "soccer field",
    "swimming pool",
    "community center",
    "children's museum",
    "aquarium",
    "zoo",
    "petting zoo",
    "farmyard",
    "orchard",
    "flower field",
    "vegetable garden",
    "kitchen",
    "bakery",
    "grocery store",
    "market",
    "laundromat",
    "doctor's waiting room",
    "dentist office",
    "hair salon",
    "post office",
    "fire station",
    "neighborhood park",
    "picnic meadow",
    "forest trail",
    "campground",
    "pond",
    "river path",
    "community garden",
    "grandparent's house",
    "friend's backyard",
    "apartment courtyard",
    "toy store",
    "bookstore",
    "living room",
    "bedroom",
    "playroom",
    "bathroom",
    "dining room",
    "mudroom",
    "daycare room",
    "nap room",
    "indoor gym",
    "dance studio",
    "swim school",
    "craft workshop",
    "building blocks corner",
    "puppet theater",
    "toy library",
    "reading nook",
    "museum gallery",
    "indoor play cafe",
    "shopping mall",
    "hotel lobby",
    "construction site",
    "road repair",
    "busy street crossing",
    "flooded street",
    "storm drain",
    "parking lot",
    "train platform",
    "subway station",
    "escalator",
    "elevator",
    "workshop",
    "garage",
    "tool shed",
    "dock",
    "pier",
    "rocky shore",
    "icy sidewalk",
    "steep hill path",
    "deep puddle",
    "crowded market",
    "driveway",
    "bike lane",
    "railroad crossing",
    "bus depot",
    "ferry terminal",
    "boat ramp",
    "marina",
    "canal path",
    "riverbank",
    "cliff lookout",
    "quarry edge",
    "fallen tree trail",
    "muddy slope",
    "snowy curb",
    "wet stairs",
    "loose gravel path",
    "basement stairs",
    "attic ladder",
    "laundry room",
    "storage closet",
    "loading dock",
    "warehouse aisle",
    "hardware store",
    "garden center",
    "animal enclosure",
]

STYLES = [
    "Fairy Tale",
    "Fable",
    "Bedtime Story",
    "Adventure",
    "Comedy",
    "Mystery",
    "Tall Tale",
    "Slice of Life",
    "Nursery Rhyme",
    "Myth",
    "Folk Tale",
    "Detective Story",
    "Superhero Story",
    "Ghost Story",
    "Pirate Tale",
    "Space Adventure",
    "Animal Story",
    "Rhyming Story",
    "Whodunit",
    "Heartwarming",
]


@dataclass
class StorySeed:
    words: list[str]
    setting: str
    features: list[str]
    style: str

    def render(self) -> str:
        lines = [
            "Write a story that includes the following words and narrative instruments.",
            f"Words: {', '.join(self.words)}",
        ]
        if self.setting:
            lines.append(f"Setting: {self.setting}")
        lines.extend([
            f"Features: {', '.join(self.features)}",
            f"Style: {self.style}",
        ])
        return "\n".join(lines)


def sample(rng: random.Random, n_words: int = 3, n_features: int = 3) -> StorySeed:
    """A random, reproducible combination drawn from the pools above."""
    setting = rng.choice(SETTINGS) if rng.random() < SETTING_PROBABILITY else ""
    return StorySeed(
        words=rng.sample(WORDS, n_words),
        setting=setting,
        features=rng.sample(FEATURES, n_features),
        style=rng.choice(STYLES),
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Generate random story seeds.")
    ap.add_argument("-n", type=int, default=1, help="number of seeds to emit")
    ap.add_argument("--seed", type=int, default=None,
                    help="base seed for reproducible sampling")
    ap.add_argument("--words", type=int, default=None,
                    help="how many words to pin (default: random 1-3)")
    ap.add_argument("--features", type=int, default=None,
                    help="how many narrative instruments to pin (default: random 1-3)")
    return ap


def main() -> None:
    args = build_parser().parse_args()
    base = args.seed if args.seed is not None else random.randrange(2 ** 31)
    for i in range(args.n):
        rng = random.Random(base + i)
        n_words = args.words if args.words is not None else rng.randint(1, 3)
        n_features = args.features if args.features is not None else rng.randint(1, 3)
        print(sample(rng, n_words, n_features).render())
        if i < args.n - 1:
            print()


if __name__ == "__main__":
    main()
