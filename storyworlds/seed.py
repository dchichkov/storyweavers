#!/usr/bin/env python3
"""
storyworlds/seed.py
===================

Tiny generator of *story seeds* -- short prompts that pin a handful of words plus
narrative instruments and a style, e.g.:

    Write a story that includes the following words and narrative instruments.
    Words: ride, moon, upset
    Features: Dialogue, Cautionary, Conflict
    Style: Fairy Tale

It just enumerates pools (words / features / styles) and samples a random,
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

# ---------------------------------------------------------------------------
# Pools -- the swappable vocabulary.  Keep words simple/concrete (TinyStories
# level); features are narrative instruments; styles are the overall register.
# ---------------------------------------------------------------------------
WORDS = [
    # nouns
    "ride", "moon", "puddle", "jacket", "dog", "garden", "boat", "kite",
    "cake", "lantern", "forest", "river", "shell", "ladder", "balloon",
    "mirror", "key", "snow", "bell", "nest", "blanket", "candle", "broom",
    "treasure", "feather", "bridge", "star", "drum", "seed", "cloud",
    "rainbow", "pumpkin", "button", "whistle", "pillow", "marble", "sock",
    "teapot", "umbrella", "cookie", "scarf", "pebble", "wagon", "swing",
    "tent", "map", "crown", "mitten", "spoon", "window", "garden gnome",
    "anchor", "compass", "snail", "owl", "frog", "butterfly", "kitten",
    # verbs
    "jump", "hide", "share", "build", "wander", "rescue", "whisper", "climb",
    "spill", "promise", "search", "forgive", "chase", "fix", "wait",
    "bake", "paint", "dance", "sneak", "giggle", "stumble", "gather",
    "knock", "float", "dig", "wave", "sing", "tiptoe", "sparkle", "tumble",
    # adjectives / feelings
    "upset", "brave", "curious", "gentle", "lonely", "proud", "scared",
    "stubborn", "kind", "clumsy", "sleepy", "jealous", "cheerful", "shy",
    "grumpy", "worried", "excited", "silly", "patient", "bold", "tiny",
    "giant", "sparkly", "muddy", "cozy", "noisy", "honest", "greedy",
]

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
    features: list[str]
    style: str

    def render(self) -> str:
        return (
            "Write a story that includes the following words and narrative "
            "instruments.\n"
            f"Words: {', '.join(self.words)}\n"
            f"Features: {', '.join(self.features)}\n"
            f"Style: {self.style}"
        )


def sample(rng: random.Random, n_words: int = 3, n_features: int = 3) -> StorySeed:
    """A random, reproducible combination drawn from the pools above."""
    return StorySeed(
        words=rng.sample(WORDS, n_words),
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
