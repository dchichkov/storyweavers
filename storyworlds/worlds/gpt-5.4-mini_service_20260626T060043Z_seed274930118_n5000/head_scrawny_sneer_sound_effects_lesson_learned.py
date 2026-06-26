#!/usr/bin/env python3
"""Fable-style storyworld about a scrawny creature, a sneer, and a lesson learned.

A small woodland tale:
- A scrawny hare wants a place at the berry patch.
- A smug badger sneers at the hare's tiny head and thin frame.
- The hare proves worth with a careful, noisy rescue.
- The sneer fades, and the lesson is shared at the end.
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
    type: str = "thing"
    label: str = ""
    plural: bool = False
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"hare", "rabbit", "fox", "squirrel", "badger"}:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    lines: list[str] = field(default_factory=list)

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def render(self) -> str:
        return " ".join(self.lines)


@dataclass
class Meadow:
    place: str = "the meadow"
    has_patch: bool = True
    has_stream: bool = True


@dataclass
class StoryParams:
    seed: Optional[int] = None
    name: str = "Pip"
    rival: str = "Grub"
    helper: str = "Moss"
    place: str = "meadow"


NAMES = ["Pip", "Tilly", "Nip", "Wren", "Birch", "Pipkin"]
RIVALS = ["Grub", "Bram", "Muck", "Thorn"]
HELPERS = ["Moss", "Fern", "Sage", "Willow"]


ASP_RULES = r"""
#show lesson/1.
#show sneer/2.

lesson(L) :- learned(L).
sneer(R, H) :- proud(R), scorns(R, H).
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("proud", "badger"),
            asp.fact("scorns", "badger", "hare"),
            asp.fact("learned", "kindness_is_stronger_than_mockery"),
            asp.fact("learned", "small_can_still_be_brave"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fable storyworld: scrawny, sneer, and a lesson learned.")
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--rival", choices=RIVALS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--place", default="meadow")
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
    return StoryParams(
        seed=args.seed,
        name=args.name or rng.choice(NAMES),
        rival=args.rival or rng.choice(RIVALS),
        helper=args.helper or rng.choice(HELPERS),
        place=args.place or "meadow",
    )


def generate(params: StoryParams) -> StorySample:
    world = World()
    meadow = Meadow(place=f"the {params.place}")
    world.facts["meadow"] = meadow

    hare = world.add(Entity(id=params.name, kind="character", type="hare", label=params.name))
    badger = world.add(Entity(id=params.rival, kind="character", type="badger", label=params.rival))
    helper = world.add(Entity(id=params.helper, kind="character", type="mouse", label=params.helper))

    hare.meters["scrawny"] = 1.0
    hare.memes["hope"] = 1.0
    badger.memes["pride"] = 1.0

    world.say(f"In {meadow.place}, a scrawny hare named {hare.id} kept its head high beside the berry patch.")
    world.say(f"One morning, {badger.id} looked down and gave a sharp sneer. 'Such a tiny thing,' it said.")
    world.say("The words went, hiss, like wind over dry grass.")
    world.say(f"{hare.id} felt small, but it did not run away. Instead, it listened for trouble.")

    world.say(f"Then came a sudden cry: splish-splash! A young sparrow had slipped near the stream.")
    world.say(f"{hare.id} darted forward with a quick hop-hop-hop, and {helper.id} helped from the reeds.")
    world.say("Splash! Thump! The little rescue made more noise than anyone expected.")
    hare.memes["bravery"] = 1.0
    badger.memes["shame"] = 1.0
    badger.memes["sneer"] = 0.0

    world.say(
        f"{badger.id} blinked, then lowered its head. 'I laughed too soon,' it muttered. "
        f"{hare.id} only twitched its nose and smiled."
    )
    world.say("Lesson learned: a scrawny body can hold a brave heart, and a sneer can turn into respect.")

    world.facts.update(
        hare=hare,
        badger=badger,
        helper=helper,
        meadow=meadow,
        lesson="small_can_still_be_brave",
        sneer=True,
        sound_effects=["hiss", "splish-splash", "hop-hop-hop", "Splash", "Thump"],
    )

    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hare = f["hare"]
    badger = f["badger"]
    return [
        f"Write a short fable about a scrawny {hare.type} whose head stays high after a sneer.",
        f"Tell a child-friendly story where {badger.id} sneers, but kindness and courage change the ending.",
        "Write a fable with sound effects and a clear lesson learned at the end.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hare = f["hare"]
    badger = f["badger"]
    helper = f["helper"]
    return [
        QAItem(
            question=f"Who was scrawny in the story?",
            answer=f"{hare.id} was the scrawny hare with a small body but a brave heart.",
        ),
        QAItem(
            question=f"Who gave the sneer at the berry patch?",
            answer=f"{badger.id} gave the sneer and acted proud and unkind at first.",
        ),
        QAItem(
            question=f"What did the helper do when trouble came near the stream?",
            answer=f"{helper.id} helped during the rescue, and together they saved the young sparrow.",
        ),
        QAItem(
            question="What lesson was learned?",
            answer="The lesson learned was that small size does not stop a brave heart, and mockery can be replaced by respect.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a sneer?",
            answer="A sneer is a mean or mocking look or smile that shows scorn.",
        ),
        QAItem(
            question="What does scrawny mean?",
            answer="Scrawny means thin and not very strong-looking.",
        ),
        QAItem(
            question="Why can sound effects make a story fun to read?",
            answer="Sound effects like hiss, splash, and thump help the reader imagine what is happening.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  facts: {sorted(world.facts.keys())}")
    return "\n".join(lines)


def asp_verify() -> int:
    import asp
    python = {
        ("badger", "hare"),
    }
    model = asp.one_model(asp_program("#show sneer/2."))
    clingo_set = set(asp.atoms(model, "sneer"))
    if clingo_set == python:
        print("OK: clingo parity matches Python gate.")
        return 0
    print("MISMATCH between clingo and Python gate.")
    print("  clingo:", sorted(clingo_set))
    print("  python:", sorted(python))
    return 1


CURATED = [
    StoryParams(name="Pip", rival="Grub", helper="Moss", place="meadow"),
    StoryParams(name="Tilly", rival="Bram", helper="Fern", place="meadow"),
    StoryParams(name="Nip", rival="Muck", helper="Sage", place="meadow"),
]


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show sneer/2.\n#show lesson/1."))
    return sorted(set(asp.atoms(model, "sneer")))


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
        print(asp_program("#show sneer/2.\n#show lesson/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid())} ASP-suggested sneer facts")
        for t in asp_valid():
            print(t)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for p in CURATED:
            samples.append(generate(p))
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 30):
            params = resolve_params(args, random.Random(base_seed + i))
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
            seen.add(sample.story)
            samples.append(sample)
            i += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            header = f"### {sample.params.name}: sneer at the meadow"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
