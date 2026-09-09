"""Deterministic TinyStories-style seed ingredients."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
import random


KERNELS = {
    "Quest": ("Discovery", "Friendship", "Conflict", "Rescue", "Transformation"),
    "Journey": ("Discovery", "Friendship", "Conflict", "Rescue", "Transformation"),
    "Cautionary": ("Conflict", "Discovery", "Reconciliation", "Transformation"),
    "Mystery": ("Discovery", "Conflict", "Friendship", "Rescue", "Reconciliation"),
    "Friendship": ("Conflict", "Discovery", "Rescue", "Reconciliation", "Transformation"),
    "Conflict": ("Friendship", "Discovery", "Rescue", "Reconciliation", "Transformation"),
    "Discovery": ("Quest", "Journey", "Friendship", "Conflict", "Transformation"),
    "Rescue": ("Quest", "Journey", "Friendship", "Conflict", "Reconciliation"),
    "Transformation": ("Quest", "Journey", "Cautionary", "Friendship", "Discovery"),
    "Reconciliation": ("Cautionary", "Friendship", "Conflict", "Rescue", "Transformation"),
}
STRUCTURAL_KERNELS = ("Quest", "Journey", "Cautionary", "Mystery")

BEGINNINGS = (
    "Once upon a time",
    "One bright morning",
    "Long ago",
    "On the first day of spring",
    "In a small and busy town",
    "At the edge of a quiet wood",
    "Before breakfast one morning",
    "On a windy afternoon",
    "Not far from here",
    "When the moon first appeared",
)
ENDINGS = (
    "happy ending",
    "earned celebration",
    "quiet reconciliation",
    "lesson shown by a final image",
    "surprising but hopeful ending",
    "safe return home",
    "new friendship",
    "problem solved together",
    "bittersweet acceptance",
    "mystery resolved",
)
BASIC_PLOTS = (
    "Overcoming the Monster",
    "Rags to Riches",
    "The Quest",
    "Voyage and Return",
    "Comedy",
    "Tragedy",
    "Rebirth",
)
ATU_TYPES = (
    "The Helpful Animal",
    "The Animal Bride or Bridegroom",
    "The Magic Helper",
    "The Giant or Ogre Defeated",
    "The Clever Child",
    "The Lost Child Returns",
    "The Three Tasks",
    "The Grateful Dead",
    "The Robbers Outwitted",
    "The Kind and Unkind Siblings",
)
GENRES = (
    "educational",
    "young reader",
    "fantasy",
    "romance",
    "detective",
    "adventure",
    "fable",
    "comedy",
    "bedtime",
    "folk tale",
)
SITUATIONS = (
    "going to school",
    "playing at a playground",
    "taking a forest hike",
    "camping overnight",
    "visiting a post office",
    "visiting a zoo",
    "playing pirates",
    "preparing a birthday surprise",
    "looking for a lost object",
    "helping at a neighborhood event",
)
LOCATIONS = (
    "living room",
    "classroom",
    "playground",
    "forest trail",
    "campground",
    "post office",
    "zoo",
    "backyard",
    "library",
    "seaside",
)
FALLBACK_WORDS = ("apple", "bridge", "button", "cloud", "drum", "feather", "garden", "lamp", "pocket", "whistle")


def child_words() -> list[str]:
    """Load the existing CHILDES pool used by storyworlds, with a tiny fallback."""
    path = Path(__file__).resolve().parents[1] / "storyworlds/data/childes/childes_eng_na_vocab.txt"
    if not path.exists():
        return list(FALLBACK_WORDS)
    words = [line.split("\t", 1)[0].strip().lower() for line in path.read_text(encoding="utf-8").splitlines()
             if line and not line.startswith("#")]
    return list(dict.fromkeys(word for word in words if word.isalpha() and 3 <= len(word) <= 12))


@dataclass(frozen=True)
class StorySeed:
    index: int
    seed: int
    words: tuple[str, str, str]
    kernels: tuple[str, ...]
    beginning: str
    ending: str
    basic_plot: str
    atu_type: str
    genre: str
    situation: str
    location: str
    dialogue_required: bool

    def to_dict(self) -> dict:
        value = asdict(self)
        value["words"], value["kernels"] = list(self.words), list(self.kernels)
        return value


def sample_seed(base_seed: int, index: int) -> StorySeed:
    rng = random.Random((base_seed << 16) ^ index)
    structural = rng.choice(STRUCTURAL_KERNELS)
    compatible = list(KERNELS[structural])
    supporting = rng.sample(compatible, rng.randint(2, min(4, len(compatible))))
    return StorySeed(
        index=index,
        seed=rng.getrandbits(32),
        words=tuple(rng.sample(child_words(), 3)),
        kernels=(structural, *supporting),
        beginning=rng.choice(BEGINNINGS),
        ending=rng.choice(ENDINGS),
        basic_plot=rng.choice(BASIC_PLOTS),
        atu_type=rng.choice(ATU_TYPES),
        genre=rng.choice(GENRES),
        situation=rng.choice(SITUATIONS),
        location=rng.choice(LOCATIONS),
        dialogue_required=index % 2 == 0,
    )
