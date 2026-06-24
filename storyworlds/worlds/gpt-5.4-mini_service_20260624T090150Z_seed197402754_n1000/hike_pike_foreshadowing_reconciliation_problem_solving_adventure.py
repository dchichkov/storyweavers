#!/usr/bin/env python3
"""
A small adventure storyworld about a hike, a pike, and a worried friendship that
moves through foreshadowing, a problem, a practical fix, and reconciliation.
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

ASP_RULES = r"""
% The declarative twin of the Python reasonableness gate.

problem(H) :- trail(H), has_bridge(H), storm(H).
solution(H) :- problem(H), has_rope(H), has_map(H).
resolve(H) :- solution(H).

compatible(Place, H) :- setting(Place), hike(H), problem(H), solution(H).
"""


@dataclass
class StoryParams:
    setting: str
    hero: str
    friend: str
    pike_name: str
    seed: Optional[int] = None


@dataclass
class Person:
    name: str
    kind: str = "child"
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Place:
    name: str
    trail_name: str
    has_bridge: bool = True
    has_rope: bool = True
    has_map: bool = True
    storm: bool = True
    pike: str = "pike"
    clues: list[str] = field(default_factory=list)


@dataclass
class World:
    place: Place
    hero: Person
    friend: Person
    facts: dict = field(default_factory=dict)

    def render(self) -> str:
        return "\n\n".join(self.facts.get("paragraphs", []))


SETTINGS = {
    "ridge": Place(
        name="the pine ridge",
        trail_name="the narrow trail",
        has_bridge=True,
        has_rope=True,
        has_map=True,
        storm=True,
        pike="a sharp pike",
        clues=["dark clouds", "a loose plank", "a snapped twig"],
    ),
    "creek": Place(
        name="the creek path",
        trail_name="the wet trail",
        has_bridge=True,
        has_rope=True,
        has_map=True,
        storm=True,
        pike="a rusty pike",
        clues=["mud on the stones", "a rope tied to a post", "far thunder"],
    ),
}

HEROES = ["Mina", "Theo", "Lina", "Jasper", "Nora", "Eli"]
FRIENDS = ["Pip", "Milo", "Tess", "Rae", "Kit", "June"]


def asp_facts() -> str:
    import asp
    lines = []
    for sid, place in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        lines.append(asp.fact("trail", sid))
        if place.has_bridge:
            lines.append(asp.fact("has_bridge", sid))
        if place.has_rope:
            lines.append(asp.fact("has_rope", sid))
        if place.has_map:
            lines.append(asp.fact("has_map", sid))
        if place.storm:
            lines.append(asp.fact("storm", sid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show compatible/2."))
    clingo_set = set(asp.atoms(model, "compatible"))
    python_set = set((k, v) for k, v in valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for sid, place in SETTINGS.items():
        if place.has_bridge and place.has_rope and place.has_map and place.storm:
            combos.append((sid, place.trail_name))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure storyworld: a hike, a pike, and a repair.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--hero")
    ap.add_argument("--friend")
    ap.add_argument("--pike-name")
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.setting not in SETTINGS:
        raise StoryError("Unknown setting.")
    setting = args.setting or rng.choice(list(SETTINGS))
    hero = args.hero or rng.choice(HEROES)
    friend = args.friend or rng.choice([n for n in FRIENDS if n != hero])
    pike_name = args.pike_name or rng.choice(["Pike", "Old Pike", "Pike the Boat Hook"])
    return StoryParams(setting=setting, hero=hero, friend=friend, pike_name=pike_name)


def generate(params: StoryParams) -> StorySample:
    place = SETTINGS[params.setting]
    hero = Person(params.hero)
    friend = Person(params.friend)

    paragraphs = []
    paragraphs.append(
        f"{hero.name} and {friend.name} set out on a hike at {place.name}. "
        f"They had heard a small warning before they left: a shiny {place.pike} had been found near {place.trail_name}."
    )
    paragraphs.append(
        f"On the way up, they noticed {place.clues[0]} and {place.clues[1]}. "
        f"That made {hero.name} slow down and look more carefully ahead."
    )
    paragraphs.append(
        f"Then the trail turned rough. A washed-out step blocked the path, and the wind shook the trees. "
        f"{friend.name} wanted to turn back, but {hero.name} saw a better way."
    )
    paragraphs.append(
        f"{hero.name} used the rope to steady the climb, while {friend.name} checked the map. "
        f"Together they found a safe path around the broken step and reached the top."
    )
    paragraphs.append(
        f"At the ridge, they found the forgotten {params.pike_name} stuck beside an old sign. "
        f"Instead of fighting over it, they carried it down carefully and returned it to the ranger station."
    )
    paragraphs.append(
        f"By the time they headed home, the scare had turned into a shared story. "
        f"{hero.name} and {friend.name} laughed again, glad they had solved the trouble together."
    )

    story = " ".join(paragraphs)

    world = World(place=place, hero=hero, friend=friend)
    world.facts["paragraphs"] = paragraphs
    world.facts["setting"] = params.setting
    world.facts["hero"] = params.hero
    world.facts["friend"] = params.friend
    world.facts["pike_name"] = params.pike_name
    world.facts["foreshadowing"] = "warning before they left"
    world.facts["problem"] = "washed-out step"
    world.facts["solution"] = "rope and map"
    world.facts["reconciliation"] = "laughed again"

    prompts = [
        f"Write a short adventure story about {params.hero} and {params.friend} on a hike, with a warning about a pike.",
        f"Tell a child-friendly trail adventure where a problem is solved with a rope and a map.",
        f"Write a story that begins with foreshadowing, has a hiking problem, and ends in reconciliation.",
    ]

    story_qa = [
        QAItem(
            question=f"Where did {params.hero} and {params.friend} go at the start of the story?",
            answer=f"They went on a hike at {place.name}.",
        ),
        QAItem(
            question="What warning hinted that trouble might happen?",
            answer=f"They heard a warning about a {place.pike} near the trail before they left.",
        ),
        QAItem(
            question="What problem blocked the hikers?",
            answer="A washed-out step blocked the path and made the trail hard to cross.",
        ),
        QAItem(
            question="How did they solve the problem?",
            answer="They used the rope to steady the climb and checked the map to find a safe way around.",
        ),
        QAItem(
            question="How did the story end for the two friends?",
            answer="They laughed again and felt better after solving the trouble together.",
        ),
    ]

    world_qa = [
        QAItem(
            question="What is a hike?",
            answer="A hike is a walk outdoors on a trail or path, often in nature.",
        ),
        QAItem(
            question="What is foreshadowing in a story?",
            answer="Foreshadowing is a small clue that hints that something important or difficult may happen later.",
        ),
        QAItem(
            question="What is reconciliation?",
            answer="Reconciliation is when people stop arguing or worrying and become friendly again.",
        ),
        QAItem(
            question="What is problem solving?",
            answer="Problem solving means finding a smart way to fix a difficulty or get past an obstacle.",
        ),
    ]

    return StorySample(params=params, story=story, prompts=prompts, story_qa=story_qa, world_qa=world_qa, world=world)


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(sample: StorySample) -> str:
    w = sample.world
    if w is None:
        return ""
    lines = ["--- world model state ---"]
    lines.append(f"  setting: {w.place.name} / {w.place.trail_name}")
    lines.append(f"  hero: {w.hero.name}")
    lines.append(f"  friend: {w.friend.name}")
    lines.append(f"  pike: {w.facts.get('pike_name')}")
    lines.append(f"  foreshadowing: {w.facts.get('foreshadowing')}")
    lines.append(f"  problem: {w.facts.get('problem')}")
    lines.append(f"  solution: {w.facts.get('solution')}")
    lines.append(f"  reconciliation: {w.facts.get('reconciliation')}")
    return "\n".join(lines)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample))
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show compatible/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show compatible/2."))
        atoms = sorted(set(asp.atoms(model, "compatible")))
        print(f"{len(atoms)} compatible combos:")
        for setting, trail in atoms:
            print(f"  {setting}: {trail}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for setting, _trail in valid_combos():
            params = StoryParams(
                setting=setting,
                hero=HEROES[0],
                friend=FRIENDS[0],
                pike_name="Pike",
            )
            samples.append(generate(params))
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
