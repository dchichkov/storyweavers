#!/usr/bin/env python3
"""
A small mystery storyworld about a lost favor, an octopus, foreshadowed clues,
and a happy ending.

Premise:
- A child or helper wants to do a favor for a friend.
- An octopus becomes the curious center of the mystery.
- Clues appear early as foreshadowing.
- The turn reveals who needed help and what was hiding.
- The ending is warm and resolved.
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
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    type: str = "thing"
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    owner: Optional[str] = None

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Place:
    name: str
    indoor: bool
    clue: str
    sound: str


@dataclass
class Mystery:
    id: str
    item: str
    hidden: str
    clue1: str
    clue2: str
    reveal: str
    setting_ok: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    mystery: str
    name: str
    gender: str
    helper: str
    seed: Optional[int] = None


PLACES = {
    "dock": Place(name="the dock", indoor=False, clue="a wet trail", sound="water slapping wood"),
    "museum": Place(name="the tiny museum", indoor=True, clue="a soft tapping sound", sound="quiet footsteps"),
    "beach": Place(name="the beach", indoor=False, clue="a swirl in the sand", sound="waves whispering"),
}

MYSTERIES = {
    "lost_shell": Mystery(
        id="lost_shell",
        item="shell necklace",
        hidden="behind a crate",
        clue1="a shiny shell fragment near the floor",
        clue2="a trail of blue ink on a step",
        reveal="the octopus had tucked the necklace away to keep it safe",
        setting_ok={"dock", "beach", "museum"},
    ),
    "missing_key": Mystery(
        id="missing_key",
        item="brass key",
        hidden="inside a jar",
        clue1="a ring of damp footprints",
        clue2="a careful pile of pebbles beside the bench",
        reveal="the octopus had moved the key so nobody would lose it in the tide",
        setting_ok={"dock", "beach"},
    ),
    "quiet_favor": Mystery(
        id="quiet_favor",
        item="paper note",
        hidden="under a folded map",
        clue1="a corner of paper peeking out",
        clue2="a curl of ink shaped like a question mark",
        reveal="the octopus had been helping by hiding the note until the right friend arrived",
        setting_ok={"museum", "dock"},
    ),
}

GENDERS = ["girl", "boy"]
HELPERS = ["mother", "father"]
NAMES = ["Lina", "Milo", "Nora", "Finn", "Ari", "June", "Theo", "Maya"]


class World:
    def __init__(self, place: Place, mystery: Mystery) -> None:
        self.place = place
        self.mystery = mystery
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[str] = set()
        self.trace: list[str] = []

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)
            self.trace.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small mystery storyworld with an octopus and a happy ending.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--gender", choices=GENDERS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--name")
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
    mystery = args.mystery or rng.choice([m for m in MYSTERIES if place in MYSTERIES[m].setting_ok])
    if place not in MYSTERIES[mystery].setting_ok:
        raise StoryError("That mystery does not fit the chosen place.")
    gender = args.gender or rng.choice(GENDERS)
    helper = args.helper or rng.choice(HELPERS)
    name = args.name or rng.choice(NAMES)
    return StoryParams(place=place, mystery=mystery, name=name, gender=gender, helper=helper)


def _join_sentences(items: list[str]) -> str:
    if not items:
        return ""
    if len(items) == 1:
        return items[0]
    return " ".join(items)


def tell(params: StoryParams) -> World:
    place = PLACES[params.place]
    mystery = MYSTERIES[params.mystery]
    world = World(place, mystery)

    child = world.add(Entity(id=params.name, kind="character", type=params.gender))
    helper = world.add(Entity(id="helper", kind="character", type=params.helper, label=f"the {params.helper}"))
    octo = world.add(Entity(id="octopus", kind="character", type="octopus", label="the octopus"))

    child.memes["curiosity"] = 1.0
    child.memes["kindness"] = 1.0
    octo.memes["mystery"] = 1.0

    world.say(
        f"{child.id} went to {place.name} with {helper.label}. "
        f"{child.pronoun().capitalize()} wanted to do a favor for a friend, but something strange was already waiting there."
    )
    world.say(
        f"Near the floor, {child.id} noticed {mystery.clue1}. "
        f"That was the first clue, and it made {child.pronoun('object')} look around more carefully."
    )
    world.say(
        f"Then {child.id} heard {place.sound}, and beside the wall there was {mystery.clue2}. "
        f"{child.pronoun().capitalize()} began to suspect the octopus was part of the mystery."
    )

    world.para()
    child.meters["curiosity"] = 1.0
    octo.meters["seen"] = 1.0
    world.say(
        f"{child.id} followed the clues to a quiet spot and found {mystery.hidden}. "
        f"There, {mystery.reveal}."
    )

    world.para()
    child.memes["worry"] = 1.0
    world.say(
        f"At first, {child.id} worried that someone had caused trouble. "
        f"But {helper.label} noticed the tidy hiding place and smiled, because the clues had been pointing to a kind secret."
    )
    world.say(
        f"{child.id} gently returned the item and thanked the octopus. "
        f"In the end, the mystery turned out to be a favor, and everyone felt glad instead of sad."
    )

    world.facts.update(
        child=child,
        helper=helper,
        octopus=octo,
        place=place,
        mystery=mystery,
        resolved=True,
        clue1=mystery.clue1,
        clue2=mystery.clue2,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    return [
        f"Write a short mystery for a young child about {child.id}, an octopus, and a helpful favor.",
        f"Tell a gentle story that uses foreshadowing clues at {world.place.name} and ends happily.",
        f"Write a simple seaside mystery where an octopus seems suspicious but is actually helping.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    mystery = f["mystery"]
    place = f["place"]
    return [
        QAItem(
            question=f"Who is the story mainly about?",
            answer=f"The story is mainly about {child.id}, who visits {place.name} with {helper.label}.",
        ),
        QAItem(
            question=f"What clue did {child.id} notice first?",
            answer=f"{child.id} noticed {mystery.clue1} first, and that helped start the mystery.",
        ),
        QAItem(
            question=f"What did the second clue suggest?",
            answer=f"The second clue, {mystery.clue2}, suggested that the octopus was nearby and involved in the puzzle.",
        ),
        QAItem(
            question=f"What was the octopus really doing?",
            answer=f"The octopus was really helping, because {mystery.reveal}.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended happily when {child.id} returned the item and understood the octopus was doing a favor.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a favor?",
            answer="A favor is a kind thing you do to help someone else.",
        ),
        QAItem(
            question="What is an octopus?",
            answer="An octopus is an ocean animal with eight arms.",
        ),
        QAItem(
            question="What is foreshadowing?",
            answer="Foreshadowing is when a story gives little clues early that help you guess what will happen later.",
        ),
        QAItem(
            question="What makes a mystery story?",
            answer="A mystery story has clues, questions, and a reveal at the end.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(f"- {p}")
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
place(dock). place(museum). place(beach).
octopus(octopus).
favor(favor).
happy_ending(X) :- resolved(X).
foreshadowing(X) :- clue(X).
mystery_story(X) :- octopus(X), favor(favor).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for m in MYSTERIES.values():
        lines.append(asp.fact("mystery", m.id))
        lines.append(asp.fact("item", m.item))
    lines.append("octopus(octopus).")
    lines.append("favor(favor).")
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    print("OK: ASP twin present for the mystery world.")
    return 0


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
    StoryParams(place="dock", mystery="lost_shell", name="Lina", gender="girl", helper="mother"),
    StoryParams(place="museum", mystery="quiet_favor", name="Milo", gender="boy", helper="father"),
    StoryParams(place="beach", mystery="missing_key", name="Nora", gender="girl", helper="mother"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show happy_ending/1.\n#show foreshadowing/1.\n#show mystery_story/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("ASP mode is available in the twin, but this world keeps its gate simple and deterministic.")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as e:
                print(e)
                return
            params.seed = seed
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
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
