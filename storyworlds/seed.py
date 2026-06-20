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

# ---------------------------------------------------------------------------
# Pools -- the swappable vocabulary.  Keep words simple/concrete (TinyStories
# level); settings are everyday story places; features are narrative instruments;
# styles are the overall register.
# ---------------------------------------------------------------------------
_CORE_SEEDS = [
    "ride", "moon", "puddle", "jacket", "dog", "garden", "boat", "kite",
    "cake", "lantern", "forest", "river", "shell", "ladder", "balloon",
    "mirror", "key", "snow", "bell", "nest", "blanket", "candle", "broom",
    "treasure", "feather", "bridge", "star", "drum", "seed", "cloud",
    "rainbow", "pumpkin", "button", "whistle", "pillow", "marble", "sock",
    "teapot", "umbrella", "cookie", "scarf", "pebble", "wagon", "swing",
    "tent", "map", "crown", "mitten", "spoon", "window", "garden gnome",
    "anchor", "compass", "snail", "owl", "frog", "butterfly", "kitten",
    "jump", "hide", "share", "build", "wander", "rescue", "whisper", "climb",
    "spill", "promise", "search", "forgive", "chase", "fix", "wait",
    "bake", "paint", "dance", "sneak", "giggle", "stumble", "gather",
    "knock", "float", "dig", "wave", "sing", "tiptoe", "sparkle", "tumble",
    "upset", "brave", "curious", "gentle", "lonely", "proud", "scared",
    "stubborn", "kind", "clumsy", "sleepy", "jealous", "cheerful", "shy",
    "grumpy", "worried", "excited", "silly", "patient", "bold", "tiny",
    "giant", "sparkly", "muddy", "cozy", "noisy", "honest", "greedy",
]

_EMOTIONS = [
    "happy", "sad", "angry", "scared", "excited", "lonely", "proud", "jealous", 
    "curious", "nervous", "hopeful", "confused", "grateful", "guilty", "relieved", 
    "bored", "anxious",
]

_NOUNS = [
    "acorn", "airship", "beacon", "beehive", "bench", "blossom", "breeze",
    "bucket", "butter", "cactus", "carpet", "cave", "cello", "chest", "cigar",
    "clock", "clove", "cloud", "coach", "cobblestone", "cove", "cradle",
    "crystal", "dam", "dandelion", "diary", "dish", "dove", "dragonfly", "drumstick",
    "dune", "earring", "ember", "fence", "ferry", "flint", "frost", "garage",
    "garland", "goblet", "harbor", "harvest", "helmet", "honey", "island",
    "jewel", "jungle", "kettle", "kitchen", "ladder", "lamplight", "ledger",
    "letter", "lighthouse", "lilypad", "linens", "lodge", "lumber", "mackerel",
    "magnolia", "market", "meadow", "mural", "muffin", "mural", "mustache",
    "oasis", "orchard", "otter", "outpost", "pail", "pantry", "pebble",
    "picket", "pinecone", "plate", "plank", "plaza", "pocket", "quill", "raccoon",
    "rain", "ribbon", "riverbank", "sand", "satchel", "saucer", "scarf", "sculpture",
    "shackle", "sheep", "silk", "silt", "sledge", "snorkel", "stair", "station",
    "stone", "sundial", "syrup", "talisman", "telescope", "thistle", "tinsel",
    "topiary", "totem", "tusk", "twig", "umbrella", "vault", "vessel", "village",
    "violin", "warden", "watch", "willow", "windmill", "xylophone", "yarn", "zephyr",
]

_VERBS = [
    "admire", "amble", "blow", "bundle", "button", "cajole", "chase", "cling",
    "cling", "clasp", "climb", "collect", "crash", "decorate", "dip", "drift",
    "dwell", "echo", "enjoy", "escort", "exchange", "feast", "flip", "flicker",
    "float", "forge", "freckle", "fume", "gather", "gaze", "glimmer", "glide",
    "hammer", "hasten", "hover", "howl", "imitate", "inflate", "inspect", "invite",
    "jam", "juggle", "kneel", "laugh", "linger", "lurk", "murmur", "nuzzle",
    "paddle", "peek", "pounce", "pounce", "prance", "preen", "quiver", "rattle",
    "riddle", "roam", "sip", "sniff", "soar", "spark", "stamp", "stitch",
    "sway", "tailspin", "tiptoe", "trickle", "troop", "vex", "whisper", "wilt",
    "wink", "wobble", "yawn", "zip", "zoom", "look", "see", "run", "jump", "hide",
    "share", "build", "wander", "rescue", "whisper", "climb", "spill", "promise", 
    "search", "forgive", "chase", "love", "fix", "wait", "bake", "paint", "dance",
    "sneak", "giggle", "stumble", "gather", "knock", "float", "dig", "wave", "sing", 
    "tiptoe", "sparkle",
]

_ADJECTIVES = [
    "agile", "brisk", "breezy", "careful", "cheerful", "clingy", "cozy", "crisp",
    "curious", "damp", "dark", "dashing", "dizzy", "eager", "faint", "flickering",
    "fragrant", "friendly", "frosty", "fuzzy", "gentle", "gilded", "golden",
    "graceful", "greasy", "grubby", "happy", "hushed", "icy", "jealous", "jolly",
    "knotty", "lively", "lonely", "lumpy", "lucky", "mellow", "misty", "muddy",
    "nervy", "noisy", "patient", "peppy", "pensive", "petite", "playful", "proud",
    "quirky", "quiet", "rainy", "ragged", "risky", "rusty", "sassy", "sly",
    "smoky", "soggy", "sparkly", "speedy", "sunny", "tactful", "tiny", "timid",
    "trembling", "tricky", "vivid", "wandering", "waxy", "windy", "wobbly",
    "wondrous", "yummy", "zealous", 
]

_COMPOUND_MODIFIERS = [
    "bright", "cozy", "crystal", "dusty", "fuzzy", "golden", "icy", "loud",
    "misty", "quiet", "rusty", "shiny", "silent", "sparkly", "twinkling", "whispering",
    "wondrous", "wobbly"
]

_COMPOUND_SUBJECTS = [
    "cat", "duck", "fox", "fox cub", "moon", "river", "bridge", "tower", "garden",
    "train", "path", "storm", "star", "lamp", "trail", "cabin", "forest", "cloud",
    "moss", "island", "harbor", "village", "hill", "field", "gate", "pond", "cave",
    "castle", "ship", "wagon", "tent", "tree", "flower", "rock", "bush", "street",
    "window", "door", "fountain", "statue", "bench", "sign", "lighthouse", 
]

WORDS = list(dict.fromkeys(
    _CORE_SEEDS
    + _NOUNS
    + _VERBS
    + _ADJECTIVES
    + _EMOTIONS
    + [f"{m} {n}" for m in _COMPOUND_MODIFIERS for n in _COMPOUND_SUBJECTS]
))

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
        return (
            "Write a story that includes the following words and narrative "
            "instruments.\n"
            f"Words: {', '.join(self.words)}\n"
            f"Setting: {self.setting}\n"
            f"Features: {', '.join(self.features)}\n"
            f"Style: {self.style}"
        )


def sample(rng: random.Random, n_words: int = 3, n_features: int = 3) -> StorySeed:
    """A random, reproducible combination drawn from the pools above."""
    return StorySeed(
        words=rng.sample(WORDS, n_words),
        setting=rng.choice(SETTINGS),
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
