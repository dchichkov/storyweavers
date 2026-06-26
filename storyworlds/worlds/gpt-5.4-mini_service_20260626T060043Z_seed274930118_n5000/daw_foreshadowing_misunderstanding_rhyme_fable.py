#!/usr/bin/env python3
"""
A small fable-like storyworld about a daw, a misunderstanding, and a foreshadowed turn.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import re
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character":
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Place:
    id: str
    label: str
    feature: str


@dataclass
class Goal:
    id: str
    want: str
    action: str
    caution: str
    rhyme_a: str
    rhyme_b: str


class World:
    def __init__(self, place: Place):
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.facts: dict = {}
        self.paragraphs: list[list[str]] = [[]]
        self.trace_lines: list[str] = []

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


PLACES = {
    "mill": Place("mill", "the old mill lane", "a cracked bell"),
    "pond": Place("pond", "the willow pond", "a silver reed"),
    "barn": Place("barn", "the quiet barnyard", "a leaning gate"),
}

GOALS = {
    "seed": Goal(
        id="seed",
        want="carry a seed",
        action="hop to the barn",
        caution="the lane can hide sharp stones",
        rhyme_a="stone",
        rhyme_b="bone",
    ),
    "ring": Goal(
        id="ring",
        want="deliver a ring",
        action="cross the lane",
        caution="the ditch can swallow a careless step",
        rhyme_a="lane",
        rhyme_b="rain",
    ),
    "leaf": Goal(
        id="leaf",
        want="bring a leaf",
        action="reach the pond",
        caution="the wind may twist a loose gift away",
        rhyme_a="wing",
        rhyme_b="spring",
    ),
}

CURATED = ["seed", "ring", "leaf"]


@dataclass
class StoryParams:
    place: str
    goal: str
    seed: Optional[int] = None
    name: str = "Daw"
    parent_name: str = "Fablekeeper"


ASP_RULES = r"""
place(mill). place(pond). place(barn).
goal(seed). goal(ring). goal(leaf).

foreshadows(seed, stone, bone).
foreshadows(ring, lane, rain).
foreshadows(leaf, wing, spring).

misunderstanding(seed, crow, seed).
misunderstanding(ring, fox, ring).
misunderstanding(leaf, wind, leaf).

valid(P,G) :- place(P), goal(G).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for gid in GOALS:
        lines.append(asp.fact("goal", gid))
    for gid, g in GOALS.items():
        lines.append(asp.fact("foreshadows", gid, g.rhyme_a, g.rhyme_b))
        lines.append(asp.fact("misunderstanding", gid, "crow" if gid == "seed" else "fox" if gid == "ring" else "wind", gid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str]]:
    return [(p, g) for p in PLACES for g in GOALS]


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    if py - cl:
        print("  only in python:", sorted(py - cl))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny fable world about a daw.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--goal", choices=GOALS)
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
    combos = valid_combos()
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.goal:
        combos = [c for c in combos if c[1] == args.goal]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, goal = rng.choice(combos)
    return StoryParams(place=place, goal=goal)


def _story_lines(place: Place, goal: Goal) -> list[str]:
    bird = "A daw"
    lines = [
        f"{bird} lived near {place.label}.",
        f"{bird} wanted to {goal.want}, because a fable should carry a small duty in its beak.",
        f"Still, {bird.lower()} paused when it saw {place.feature}; that was a foreshadowing sign.",
        f"One day, a crow called out, and the noise made the daw misunderstand the warning.",
        f"It thought the crow was asking for the {goal.id}, so the daw held it tighter and hurried on.",
        f"Then the path showed why the first sign mattered: {goal.caution}.",
        f"The daw remembered the line, \"A slow wing is safer than a proud spring,\" and chose the safer way.",
        f"It shared the {goal.id}, reached {goal.action}, and nobody was hurt by haste.",
        f"So the daw learned that a warning can sound like a quarrel, and a careful heart flies farthest.",
    ]
    return lines


def generate(params: StoryParams) -> StorySample:
    place = PLACES[params.place]
    goal = GOALS[params.goal]
    world = World(place)
    daw = world.add(Entity(id="daw", kind="character", type="bird", label="daw"))
    world.facts.update(place=place, goal=goal, daw=daw)

    world.say(_story_lines(place, goal)[0])
    world.say(_story_lines(place, goal)[1])
    world.say(_story_lines(place, goal)[2])
    world.para()
    for line in _story_lines(place, goal)[3:]:
        world.say(line)

    story = world.render()
    prompts = [
        f"Write a short fable about a daw at {place.label} with foreshadowing, a misunderstanding, and a rhyme.",
        f"Tell a child-friendly story where a daw wants to {goal.want} but first mistakes a warning for help.",
        f"Write a simple moral tale about {goal.id}, {place.label}, and a wiser second choice.",
    ]
    story_qa = [
        QAItem(
            question="What kind of bird is the main character?",
            answer="The main character is a daw.",
        ),
        QAItem(
            question=f"What did the daw want to do at {place.label}?",
            answer=f"The daw wanted to {goal.want}.",
        ),
        QAItem(
            question="What went wrong in the middle of the story?",
            answer="The daw misunderstood a crow's call and thought it was asking for the gift.",
        ),
        QAItem(
            question="What sign foreshadowed the problem?",
            answer=f"The cracked place detail, {place.feature}, was a foreshadowing sign that warned the daw to be careful.",
        ),
        QAItem(
            question="How did the story end?",
            answer="The daw chose the safer way, shared the gift, and learned to listen more carefully.",
        ),
    ]
    world_qa = [
        QAItem(
            question="What is a fable?",
            answer="A fable is a short story that teaches a lesson, often with an animal character.",
        ),
        QAItem(
            question="What is foreshadowing?",
            answer="Foreshadowing is a clue early in a story that hints something important may happen later.",
        ),
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding happens when someone gets the meaning of a word, signal, or action wrong.",
        ),
        QAItem(
            question="What is a rhyme?",
            answer="A rhyme is when words sound alike at the end, like stone and bone.",
        ),
    ]
    return StorySample(params=params, story=story, prompts=prompts, story_qa=story_qa, world_qa=world_qa, world=world)


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
    lines.append(f"place={world.place.label} feature={world.place.feature}")
    for e in world.entities.values():
        lines.append(f"  {e.id}: kind={e.kind} type={e.type}")
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible (place, goal) combos:\n")
        for p, g in triples:
            print(f"  {p:5} {g:5}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(StoryParams(place="mill", goal=g)) for g in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
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

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
