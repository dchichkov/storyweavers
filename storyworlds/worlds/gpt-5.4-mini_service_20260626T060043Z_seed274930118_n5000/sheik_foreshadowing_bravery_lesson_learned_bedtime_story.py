#!/usr/bin/env python3
"""
A small bedtime-story world about a young sheik, a little foreshadowing, a brave choice,
and a lesson learned under the lantern light.
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
class StoryParams:
    seed: Optional[int] = None
    name: str = "Amina"
    title: str = "sheik"
    place: str = "the oasis"
    threat: str = "a windy night"
    helper: str = "a lantern"
    lesson: str = "listening first keeps everyone safer"


@dataclass
class World:
    params: StoryParams
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
    trace: list[str] = field(default_factory=list)

    def note(self, text: str) -> None:
        self.trace.append(text)


NAMES = ["Amina", "Nuri", "Safa", "Mina", "Leila", "Tariq", "Hadi", "Zayn"]
THREATS = [
    ("a windy night", "the lantern rope", "the lesson was to check the knots before the wind came"),
    ("a desert hush", "the camel bells", "the lesson was to stay calm and listen for small signs"),
    ("a moonless evening", "the little bridge", "the lesson was to bring help before stepping forward"),
]
LESSONS = [
    "listening first keeps everyone safer",
    "brave hands are best when they are careful too",
    "a quiet warning can be a kind gift",
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime story world: sheik, foreshadowing, bravery, lesson learned.")
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--place", default="the oasis")
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
    name = args.name or rng.choice(NAMES)
    threat, helper, lesson = rng.choice(THREATS)
    lesson = args.seed is not None and rng.choice(LESSONS) or lesson
    return StoryParams(
        seed=None,
        name=name,
        title="sheik",
        place=args.place,
        threat=threat,
        helper=helper,
        lesson=lesson,
    )


def tell(params: StoryParams) -> World:
    world = World(params=params)
    p = params
    world.meters["night_quiet"] = 1.0
    world.memes["curiosity"] = 1.0
    world.note(f"{p.name} was a little sheik who lived near {p.place}.")
    world.note(f"Each night, {p.name} listened to the desert as if it were telling a sleepy secret.")

    world.note(f"One evening, before {p.threat}, {p.name} noticed {p.helper} hanging by the door.")
    world.facts["foreshadowing"] = True
    world.facts["helper"] = p.helper
    world.facts["threat"] = p.threat

    world.note(
        f"That was a small hint, because the wind had begun to tug at the tents and whisper around the stones."
    )
    world.note(
        f"When the gusts rose, {p.name} wanted to help. {p.name} felt a tiny wobble of fear, but stood up anyway."
    )
    world.memes["bravery"] = 1.0
    world.meters["wind"] = 1.0

    world.note(
        f"Bravely, {p.name} carried {p.helper} to the path and held it steady while the family tied the ropes tight."
    )
    world.note(
        f"The lantern glowed, the tents stayed safe, and the desert seemed to breathe more softly again."
    )
    world.note(
        f"At bedtime, {p.name} smiled and learned that {p.lesson}."
    )
    world.facts["lesson"] = p.lesson
    world.facts["resolved"] = True
    return world


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    story = " ".join(world.trace)
    return StorySample(
        params=params,
        story=story,
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    p = world.params
    return [
        f"Write a bedtime story about a young {p.title} named {p.name} near {p.place}.",
        f"Tell a gentle story with foreshadowing, bravery, and a lesson learned.",
        f"Make a short story where {p.name} notices a clue, acts bravely, and learns a kind lesson.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.params
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"The story is about {p.name}, a little {p.title} near {p.place}.",
        ),
        QAItem(
            question=f"What clue helped foreshadow the problem?",
            answer=f"The clue was {p.helper}, which was noticed before {p.threat} arrived.",
        ),
        QAItem(
            question=f"What brave thing did {p.name} do?",
            answer=f"{p.name} bravely carried {p.helper} and helped keep the family safe.",
        ),
        QAItem(
            question=f"What lesson was learned at the end?",
            answer=f"The lesson was that {p.lesson}.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is foreshadowing?",
            answer="Foreshadowing is a small hint that something important may happen later.",
        ),
        QAItem(
            question="What does bravery mean?",
            answer="Bravery means doing something even when you feel a little scared.",
        ),
        QAItem(
            question="Why is a lantern useful at night?",
            answer="A lantern gives light so people can see their way in the dark.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story Q&A ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World Q&A ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    lines.append(f"params.name={world.params.name}")
    lines.append(f"params.place={world.params.place}")
    lines.append(f"meters={world.meters}")
    lines.append(f"memes={world.memes}")
    lines.append(f"facts={world.facts}")
    return "\n".join(lines)


ASP_RULES = r"""
foreshadowing :- hint(clue).
bravery :- acts_bravely(hero).
lesson_learned :- resolves_problem(hero).
"""


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("hero", "sheik"),
        asp.fact("theme", "foreshadowing"),
        asp.fact("theme", "bravery"),
        asp.fact("theme", "lesson_learned"),
    ])


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
    except Exception as err:
        print(f"ASP unavailable: {err}")
        return 1
    model = asp.one_model(asp_program("#show foreshadowing/0. #show bravery/0. #show lesson_learned/0."))
    atoms = {str(a) for a in model}
    expected = {"foreshadowing", "bravery", "lesson_learned"}
    if expected.issubset(atoms):
        print("OK: ASP twin recognizes foreshadowing, bravery, and lesson learned.")
        return 0
    print("MISMATCH: ASP twin did not return expected atoms.")
    return 1


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
        print(asp_program("#show foreshadowing/0. #show bravery/0. #show lesson_learned/0."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    rng = random.Random(base_seed)

    samples: list[StorySample] = []
    if args.all:
        params = [
            StoryParams(name="Amina", place="the oasis", threat=t[0], helper=t[1], lesson=t[2])
            for t in THREATS
        ]
        samples = [generate(p) for p in params]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

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
