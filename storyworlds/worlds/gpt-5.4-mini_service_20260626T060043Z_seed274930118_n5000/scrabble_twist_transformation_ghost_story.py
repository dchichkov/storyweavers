#!/usr/bin/env python3
"""
A small story world about a friendly ghost, a scrabble board, a twist, and a
transformation.

Premise:
- A child finds a dusty scrabble set in an old attic room.
- A shy ghost loves letters but keeps mixing them up.
- The child wants to make a word, but the board twists the letters into a
  spooky message.

Turn:
- The ghost reveals it is not haunting the room; it is lonely and wants help
  making a kinder word.

Resolution:
- The child rearranges the tiles into a word that transforms the mood of the
  room, and the ghost becomes bright and friendly.
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
# World model
# ---------------------------------------------------------------------------
@dataclass
class LetterTile:
    ch: str
    glow: float = 0.0
    dusty: bool = True


@dataclass
class Ghost:
    name: str
    form: str = "misty"
    feeling: str = "lonely"
    glow: float = 0.2
    twist_level: float = 1.0
    friendly: bool = False


@dataclass
class Board:
    tiles: list[LetterTile] = field(default_factory=list)
    word: str = ""
    cursed: bool = False


@dataclass
class Room:
    place: str
    meters: dict[str, float] = field(default_factory=lambda: {"dust": 1.0, "light": 0.2, "tidy": 0.3})
    memes: dict[str, float] = field(default_factory=lambda: {"spook": 0.8, "wonder": 0.4, "warmth": 0.1})


@dataclass
class World:
    room: Room
    ghost: Ghost
    board: Board
    child_name: str
    events: list[str] = field(default_factory=list)
    facts: dict = field(default_factory=dict)

    def say(self, text: str) -> None:
        self.events.append(text)

    def render(self) -> str:
        return " ".join(self.events)


# ---------------------------------------------------------------------------
# Parameters and registries
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    child_name: str
    ghost_name: str
    seed: Optional[int] = None


PLACES = {
    "attic": "the attic",
    "library": "the old library",
    "hall": "the moonlit hall",
}

CHILD_NAMES = ["Mia", "Leo", "Nora", "Ben", "Ava", "Theo", "Lily", "Max"]
GHOST_NAMES = ["Murmur", "Pale Pete", "Wisp", "Echo", "Mistle", "Puff"]
REARRANGEMENTS = [
    ("scrabble", "scrabble", "a word game with letter tiles"),
    ("boo", "boo", "a tiny ghostly sound"),
    ("glow", "glow", "a warm light that changes a room"),
    ("kind", "kind", "a gentle word that helps feelings"),
]
TRIGGER_WORD = "scrabble"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Ghost story with scrabble, a twist, and a transformation.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--child-name")
    ap.add_argument("--ghost-name")
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
    place = args.place or rng.choice(list(PLACES))
    child_name = args.child_name or rng.choice(CHILD_NAMES)
    ghost_name = args.ghost_name or rng.choice(GHOST_NAMES)
    return StoryParams(place=place, child_name=child_name, ghost_name=ghost_name)


# ---------------------------------------------------------------------------
# Story engine
# ---------------------------------------------------------------------------
def _make_world(params: StoryParams) -> World:
    room = Room(place=PLACES[params.place])
    ghost = Ghost(name=params.ghost_name)
    board = Board(tiles=[LetterTile(ch=c) for c in "scrabble"])
    return World(room=room, ghost=ghost, board=board, child_name=params.child_name)


def _scramble_tiles(world: World) -> None:
    world.board.cursed = True
    world.board.word = "blaresc"
    world.room.meters["dust"] += 0.2
    world.room.memes["spook"] += 0.2
    world.say(
        f"In {world.room.place}, a dusty scrabble board waited on a small table, "
        f"and the letters seemed to twitch by themselves."
    )
    world.say(
        f"When {world.child_name} touched the tiles, the word twisted into a spooky jumble."
    )


def _reveal_ghost(world: World) -> None:
    world.ghost.feeling = "lonely"
    world.say(
        f"Then {world.ghost.name}, the pale little ghost, floated in and sighed. "
        f"\"I do not want to scare you,\" it whispered. \"I only know how to twist words.\""
    )
    world.say(
        f"{world.child_name} blinked and saw that the ghost's glow was thin, not fierce."
    )


def _transform(world: World) -> None:
    world.board.cursed = False
    world.board.word = "kind"
    world.ghost.form = "shimmering"
    world.ghost.feeling = "brave"
    world.ghost.friendly = True
    world.ghost.glow += 0.8
    world.room.meters["dust"] = 0.1
    world.room.meters["light"] = 1.0
    world.room.meters["tidy"] = 0.9
    world.room.memes["spook"] = 0.1
    world.room.memes["warmth"] = 1.0
    world.room.memes["wonder"] = 0.9
    world.say(
        f"{world.child_name} smiled, moved the tiles, and made a new word: kind."
    )
    world.say(
        f"The scrabble board stopped trembling, and the whole room transformed from spooky to gentle."
    )
    world.say(
        f"{world.ghost.name} brightened into a friendly shimmer, and the little ghost laughed instead of moaning."
    )
    world.say(
        f"By the end, {world.child_name} and the ghost were building words together under a warm, quiet light."
    )


def tell_story(params: StoryParams) -> World:
    world = _make_world(params)
    world.say(
        f"{params.child_name} found an old scrabble set in {PLACES[params.place]}."
    )
    world.say(
        f"The air felt chilly, and the tiles looked like they were waiting for a secret."
    )
    _scramble_tiles(world)
    _reveal_ghost(world)
    _transform(world)
    world.facts.update(
        place=params.place,
        child_name=params.child_name,
        ghost_name=params.ghost_name,
        start_word=TRIGGER_WORD,
        end_word=world.board.word,
        transformed=world.ghost.friendly,
    )
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a short ghost story for a child named {f['child_name']} that begins with a scrabble board in {world.room.place}.",
        f"Tell a gentle spooky story where a ghost named {f['ghost_name']} twists letters and then transforms the mood.",
        f"Make a child-friendly story about scrabble, a lonely ghost, and a happy word that changes the room.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    return [
        QAItem(
            question=f"What did {f['child_name']} find in {world.room.place}?",
            answer=f"{f['child_name']} found an old scrabble set in {world.room.place}.",
        ),
        QAItem(
            question=f"What happened when the child touched the tiles?",
            answer="The letters twisted into a spooky jumble before the ghost explained what was wrong.",
        ),
        QAItem(
            question=f"What new word did {f['child_name']} make to help the ghost?",
            answer="The child made the word kind, and that changed the feeling of the room.",
        ),
        QAItem(
            question=f"How did the ghost change by the end?",
            answer=f"{f['ghost_name']} became bright, friendly, and no longer lonely.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is scrabble?",
            answer="Scrabble is a letter game where players make words from tiles.",
        ),
        QAItem(
            question="What is a ghost in a story?",
            answer="A ghost in a story is often a see-through character that may seem spooky, but it can also be friendly or sad.",
        ),
        QAItem(
            question="What does transformation mean?",
            answer="Transformation means something changes into a new form or state.",
        ),
        QAItem(
            question="What does a twist do in a story?",
            answer="A twist changes what you expected and makes the story turn in a new direction.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== story qa ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== world qa ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    lines.append(f"room: {world.room.place}")
    lines.append(f"room.meters: {world.room.meters}")
    lines.append(f"room.memes: {world.room.memes}")
    lines.append(
        f"ghost: name={world.ghost.name} form={world.ghost.form} feeling={world.ghost.feeling} glow={world.ghost.glow}"
    )
    lines.append(f"board.word: {world.board.word} cursed={world.board.cursed}")
    lines.append("tiles: " + "".join(t.ch for t in world.board.tiles))
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A story is reasonable if it has a scrabble board, a ghost, a twist, and a transformation.
twist_happens(W) :- starts_with_scrabble(W), ghost_present(W), letters_change(W).
transforms(W) :- twist_happens(W), kind_word_made(W), ghost_becomes_friendly(W).

good_story(W) :- twist_happens(W), transforms(W).
#show good_story/1.
#show twist_happens/1.
#show transforms/1.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = [
        asp.fact("starts_with_scrabble", "story"),
        asp.fact("ghost_present", "story"),
        asp.fact("letters_change", "story"),
        asp.fact("kind_word_made", "story"),
        asp.fact("ghost_becomes_friendly", "story"),
    ]
    return "\n".join(lines)


def asp_program(show: str = "#show good_story/1.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program())
    atoms = {f"{sym.name}/{len(sym.arguments)}" for sym in model}
    expected = {"good_story/1", "twist_happens/1", "transforms/1"}
    if atoms == expected:
        print("OK: ASP twin matches the Python reasonableness gate.")
        return 0
    print("MISMATCH:", atoms, expected)
    return 1


# ---------------------------------------------------------------------------
# Generate / emit
# ---------------------------------------------------------------------------
def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
    story = world.render()
    return StorySample(
        params=params,
        story=story,
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def curated_params() -> list[StoryParams]:
    return [
        StoryParams(place="attic", child_name="Mia", ghost_name="Wisp"),
        StoryParams(place="library", child_name="Leo", ghost_name="Echo"),
        StoryParams(place="hall", child_name="Nora", ghost_name="Murmur"),
    ]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in curated_params()]
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
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
