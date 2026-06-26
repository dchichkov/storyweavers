#!/usr/bin/env python3
"""
A tiny animal-story world about a baron, a boing, surprise, friendship, and humor.

The premise:
- A proud Baron animal plans a very serious little show.
- A boing sound keeps interrupting the scene.
- The surprise turns out to be friendly, and the joke ends in laughter.

This file is self-contained and follows the Storyweavers storyworld contract.
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


# ---------------------------------------------------------------------------
# Core model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing
    species: str = ""
    label: str = ""
    role: str = ""
    plural: bool = False
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    name: str
    outdoors: bool = True


@dataclass
class World:
    place: Place
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

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


# ---------------------------------------------------------------------------
# Params and registries
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    baron_species: str
    friend_species: str
    seed: Optional[int] = None


PLACES = {
    "meadow": Place("the meadow"),
    "barnyard": Place("the barnyard"),
    "orchard": Place("the orchard"),
    "hill": Place("the hill"),
    "pond": Place("the pond"),
}

BARON_SPECIES = ["cat", "dog", "fox", "rabbit", "badger", "goat"]
FRIEND_SPECIES = ["duck", "mouse", "squirrel", "pony", "hedgehog", "lamb"]

BARON_TITLES = {
    "cat": "Baron Whisker",
    "dog": "Baron Barkley",
    "fox": "Baron Foxglove",
    "rabbit": "Baron Hopper",
    "badger": "Baron Bramble",
    "goat": "Baron Gilly",
}

FRIEND_NAMES = {
    "duck": "Dottie",
    "mouse": "Mina",
    "squirrel": "Saffy",
    "pony": "Pippa",
    "hedgehog": "Hugo",
    "lamb": "Lulu",
}

SURPRISES = [
    "a popped popcorn cart",
    "a kite that bobbed like a silly cloud",
    "a little trumpet made of a tin cup",
    "a basket of shiny acorns",
    "a ribboned ball that bounced by itself",
]

LAUGHS = [
    "a giggle like pebbles in a pocket",
    "a snorty laugh that came out fast",
    "a chubby chuckle that shook the grass",
    "a bright laugh that rang like a bell",
]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
baron(B) :- baron_species(B).
friend(F) :- friend_species(F).
valid(P) :- place(P).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for s in BARON_SPECIES:
        lines.append(asp.fact("baron_species", s))
    for s in FRIEND_SPECIES:
        lines.append(asp.fact("friend_species", s))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid/1."))
    asp_places = sorted(set(x[0] for x in asp.atoms(model, "valid")))
    py_places = sorted(PLACES)
    if asp_places == py_places:
        print(f"OK: clingo gate matches Python registry ({len(py_places)} places).")
        return 0
    print("MISMATCH:")
    print("  clingo:", asp_places)
    print("  python:", py_places)
    return 1


# ---------------------------------------------------------------------------
# Story construction
# ---------------------------------------------------------------------------
def choose_surprise(rng: random.Random) -> str:
    return rng.choice(SURPRISES)


def choose_laugh(rng: random.Random) -> str:
    return rng.choice(LAUGHS)


def tell(params: StoryParams) -> World:
    rng = random.Random(params.seed)
    world = World(PLACES[params.place])

    baron_name = BARON_TITLES[params.baron_species]
    friend_name = FRIEND_NAMES[params.friend_species]

    baron = world.add(Entity(
        id="baron",
        kind="character",
        species=params.baron_species,
        label=baron_name,
        role="baron",
        meters={"pride": 1.0},
        memes={"seriousness": 1.0, "friendship": 0.0, "humor": 0.0, "surprise": 0.0},
    ))
    friend = world.add(Entity(
        id="friend",
        kind="character",
        species=params.friend_species,
        label=friend_name,
        role="friend",
        meters={"bounce": 1.0},
        memes={"friendship": 1.0, "humor": 0.0, "surprise": 0.0},
    ))
    surprise = choose_surprise(rng)
    laugh = choose_laugh(rng)

    world.facts.update(
        baron=baron,
        friend=friend,
        surprise=surprise,
        laugh=laugh,
        place=world.place.name,
    )

    # Act 1
    world.say(
        f"In {world.place.name}, Baron {baron.label.split(' ', 1)[1]} stood very straight "
        f"and looked very important."
    )
    world.say(
        f"{friend.label} the {friend.species} skipped nearby, hoping for a friendly hello."
    )
    world.para()

    # Act 2: boing + surprise
    world.say(
        f"Then came a loud boing from behind a hay bale, as if the day had bounced."
    )
    baron.memes["surprise"] += 1.0
    friend.memes["humor"] += 1.0
    world.say(
        f"The boing revealed {surprise}, and even Baron {baron.label.split(' ', 1)[1]} blinked in surprise."
    )
    world.say(
        f"{friend.label} smiled first, because the whole thing was so funny."
    )
    world.para()

    # Act 3: friendship + humor
    baron.memes["friendship"] += 1.0
    baron.memes["humor"] += 1.0
    friend.memes["friendship"] += 1.0

    world.say(
        f"Baron {baron.label.split(' ', 1)[1]} bowed to {friend.label} and said the boing was the best kind of surprise."
    )
    world.say(
        f"They laughed together at {laugh}, and the serious face on the baron melted into a happy grin."
    )
    world.say(
        f"By the end, the Baron had a new friend, and the little boing had turned into a joke they both kept smiling about."
    )

    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    baron: Entity = f["baron"]
    friend: Entity = f["friend"]
    return [
        "Write a short animal story with a baron, a boing sound, a surprise, and a friendly ending.",
        f"Tell a gentle tale where {baron.label} meets {friend.label} and a boing causes a funny surprise.",
        "Write a child-friendly animal story where seriousness turns into friendship and humor.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    baron: Entity = f["baron"]
    friend: Entity = f["friend"]
    surprise = f["surprise"]
    return [
        QAItem(
            question="Who is the story about?",
            answer=f"It is about Baron {baron.label.split(' ', 1)[1]} and {friend.label} the {friend.species}, who meet in {world.place.name}.",
        ),
        QAItem(
            question="What sound interrupted the baron?",
            answer="A loud boing interrupted the baron and made the moment feel playful.",
        ),
        QAItem(
            question="What did the boing reveal?",
            answer=f"It revealed {surprise}, which turned the scene into a surprise instead of a problem.",
        ),
        QAItem(
            question="How did the story end?",
            answer="It ended with friendship and humor, as the baron and the friend laughed together.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does a boing sound make you imagine?",
            answer="A boing sound makes you imagine something springy or bouncy, like a toy or a silly jump.",
        ),
        QAItem(
            question="What is friendship?",
            answer="Friendship is when friends care about each other, share good times, and help each other feel happy.",
        ),
        QAItem(
            question="What is humor?",
            answer="Humor is something funny that makes people smile or laugh.",
        ),
        QAItem(
            question="What is a surprise?",
            answer="A surprise is something unexpected that suddenly appears or happens.",
        ),
    ]


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal story world with a baron, boing, surprise, friendship, and humor.")
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--baron-species", choices=BARON_SPECIES)
    ap.add_argument("--friend-species", choices=FRIEND_SPECIES)
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
    place = args.place or rng.choice(sorted(PLACES))
    baron_species = args.baron_species or rng.choice(BARON_SPECIES)
    friend_species = args.friend_species or rng.choice(FRIEND_SPECIES)
    if args.baron_species and args.friend_species and args.baron_species == args.friend_species:
        raise StoryError("Baron and friend should be different animals for this story.")
    return StoryParams(place=place, baron_species=baron_species, friend_species=friend_species)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(
            f"  {e.id}: kind={e.kind} species={e.species} label={e.label} "
            f"meters={e.meters} memes={e.memes}"
        )
    return "\n".join(lines)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams(place="meadow", baron_species="cat", friend_species="duck"),
    StoryParams(place="barnyard", baron_species="fox", friend_species="mouse"),
    StoryParams(place="orchard", baron_species="rabbit", friend_species="squirrel"),
    StoryParams(place="hill", baron_species="goat", friend_species="pony"),
    StoryParams(place="pond", baron_species="dog", friend_species="lamb"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/1."))
        return
    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid/1."))
        vals = sorted(set(asp.atoms(model, "valid")))
        for (place,) in vals:
            print(place)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            p = resolve_params(args, random.Random(base_seed + i))
            p.seed = base_seed + i
            s = generate(p)
            if s.story not in seen:
                seen.add(s.story)
                samples.append(s)
            i += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for idx, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.place} / {p.baron_species} / {p.friend_species}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
