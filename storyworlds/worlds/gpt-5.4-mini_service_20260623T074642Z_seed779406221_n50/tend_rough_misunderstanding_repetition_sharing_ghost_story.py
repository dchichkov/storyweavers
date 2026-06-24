#!/usr/bin/env python3
"""
storyworlds/worlds/tend_rough_misunderstanding_repetition_sharing_ghost_story.py
================================================================================

A small, self-contained storyworld in the style of a gentle ghost story.

Premise:
- A child tends a rough old attic room.
- A shy ghost keeps causing misunderstandings by repeating the same little sign.
- Sharing a lamp, a blanket, or a toy helps the child and ghost realize the room
  is not haunted badly; it is lonely and asking for care.

This world is intentionally small and constraint-checked: there are only a few
plausible combinations, and explicit invalid options raise StoryError.
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
class Place:
    key: str
    label: str
    mood: str
    has_roof: bool = True


@dataclass
class Item:
    key: str
    label: str
    phrase: str
    can_share: bool = True


@dataclass
class Ghost:
    key: str
    label: str
    repeat_sign: str
    needs: str
    soft: bool = True


@dataclass
class StoryParams:
    place: str
    item: str
    ghost: str
    name: str
    seed: Optional[int] = None


@dataclass
class World:
    place: Place
    item: Item
    ghost: Ghost
    child_name: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    shared: bool = False
    misunderstanding: bool = False
    repetition: int = 0
    story_bits: list[str] = field(default_factory=list)

    def say(self, text: str) -> None:
        if text:
            self.story_bits.append(text)

    def render(self) -> str:
        return "\n\n".join(self.story_bits)


PLACES = {
    "attic": Place(
        key="attic",
        label="the attic",
        mood="dusty and dim",
        has_roof=True,
    ),
    "shed": Place(
        key="shed",
        label="the shed",
        mood="small and chilly",
        has_roof=True,
    ),
    "hall": Place(
        key="hall",
        label="the old hall",
        mood="long and echoing",
        has_roof=True,
    ),
}

ITEMS = {
    "lamp": Item(
        key="lamp",
        label="a little lamp",
        phrase="a little lamp with a warm yellow glow",
        can_share=True,
    ),
    "blanket": Item(
        key="blanket",
        label="a soft blanket",
        phrase="a soft blanket with blue stars",
        can_share=True,
    ),
    "toy": Item(
        key="toy",
        label="a toy train",
        phrase="a toy train with shiny wheels",
        can_share=True,
    ),
}

GHOSTS = {
    "pale": Ghost(
        key="pale",
        label="a pale ghost",
        repeat_sign="three tiny taps",
        needs="company",
    ),
    "small": Ghost(
        key="small",
        label="a small ghost",
        repeat_sign="a gentle rattle",
        needs="kindness",
    ),
    "shy": Ghost(
        key="shy",
        label="a shy ghost",
        repeat_sign="one soft knock",
        needs="warmth",
    ),
}

NAMES = ["Mina", "Leo", "Nora", "Theo", "Maya", "Owen", "Iris", "Eli"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Gentle ghost story world with misunderstanding, repetition, and sharing."
    )
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--item", choices=sorted(ITEMS))
    ap.add_argument("--ghost", choices=sorted(GHOSTS))
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
    place = args.place or rng.choice(sorted(PLACES))
    item = args.item or rng.choice(sorted(ITEMS))
    ghost = args.ghost or rng.choice(sorted(GHOSTS))
    name = args.name or rng.choice(NAMES)

    if place == "hall" and item == "toy":
        raise StoryError("The old hall is too echoing for the toy-train story; choose another item.")

    if item == "lamp" and ghost == "small" and place == "shed":
        raise StoryError("That combination is too dark for the small ghost to be clearly seen.")

    return StoryParams(place=place, item=item, ghost=ghost, name=name)


def generate(params: StoryParams) -> StorySample:
    world = World(
        place=PLACES[params.place],
        item=ITEMS[params.item],
        ghost=GHOSTS[params.ghost],
        child_name=params.name,
        meters={"dust": 0.0, "warmth": 0.0},
        memes={"curiosity": 1.0, "worry": 0.0, "trust": 0.0},
    )

    world.say(
        f"{world.child_name} went into {world.place.label}, which felt {world.place.mood}."
    )
    world.say(
        f"{world.child_name} had brought {world.item.phrase} to help tend the rough little room."
    )
    world.say(
        f"At first, {world.child_name} heard {world.ghost.label} make {world.ghost.repeat_sign}."
    )
    world.repetition = 2
    world.memes["worry"] += 1.0
    world.misunderstanding = True
    world.say(
        f"{world.child_name} thought the sound meant the ghost was cross, so {world.child_name} whispered, "
        f'"Please stop. I do not want trouble."'
    )

    world.say(
        f"But the same {world.ghost.repeat_sign} came again, and then again, from the dusty corner."
    )
    world.repetition += 2

    world.say(
        f"Then {world.child_name} noticed the ghost was pointing at the {world.item.label}, not at the door."
    )
    world.say(
        f"The ghost only wanted {world.ghost.needs}, and the repeated sound was a little ask for sharing."
    )
    world.shared = True
    world.misunderstanding = False
    world.memes["trust"] += 2.0
    world.memes["worry"] = 0.0
    world.meters["warmth"] += 1.0

    world.say(
        f"So {world.child_name} shared the {world.item.label} and set it on a crate between them."
    )
    world.say(
        f"The room did not feel rough anymore. It felt quiet, warm, and kind, "
        f"with {world.child_name} and {world.ghost.label} sitting together under the glow."
    )

    prompts = [
        f"Write a gentle ghost story for a small child named {world.child_name} in {world.place.label}.",
        f"Tell a story where a repeated ghost sign causes a misunderstanding, then sharing fixes it.",
        f"Make a short, child-facing story about tending a rough room and learning what a ghost wants.",
    ]

    story_qa = [
        QAItem(
            question=f"Why did {world.child_name} think the ghost was upset at first?",
            answer=(
                f"{world.child_name} heard the same {world.ghost.repeat_sign} again and again, "
                f"so it sounded like a warning. That made the child worry before noticing the ghost was asking for help."
            ),
        ),
        QAItem(
            question=f"What did the ghost really want in {world.place.label}?",
            answer=(
                f"The ghost really wanted {world.ghost.needs}. The repeated sign was a way to get {world.child_name}'s attention."
            ),
        ),
        QAItem(
            question=f"How did {world.child_name} solve the problem?",
            answer=(
                f"{world.child_name} shared {world.item.label} and sat with the ghost instead of running away. "
                f"That turned the misunderstanding into a calm, friendly moment."
            ),
        ),
    ]

    world_qa = [
        QAItem(
            question="What is a misunderstanding?",
            answer=(
                "A misunderstanding happens when someone thinks a sign or action means one thing, "
                "but it really means something else."
            ),
        ),
        QAItem(
            question="What does repetition mean?",
            answer=(
                "Repetition means something happens or is said more than once, like a knock or a word coming back again and again."
            ),
        ),
        QAItem(
            question="What does sharing mean?",
            answer=(
                "Sharing means letting someone else use or enjoy something too, like a lamp, a blanket, or a toy."
            ),
        ),
    ]

    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts,
        story_qa=story_qa,
        world_qa=world_qa,
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


def dump_trace(world: World) -> str:
    return "\n".join(
        [
            "--- world model state ---",
            f"place={world.place.key}",
            f"item={world.item.key}",
            f"ghost={world.ghost.key}",
            f"misunderstanding={world.misunderstanding}",
            f"repetition={world.repetition}",
            f"shared={world.shared}",
            f"meters={world.meters}",
            f"memes={world.memes}",
        ]
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


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place in PLACES:
        for item in ITEMS:
            for ghost in GHOSTS:
                try:
                    _ = resolve_params(argparse.Namespace(place=place, item=item, ghost=ghost, name=None), random.Random(0))
                except StoryError:
                    continue
                out.append((place, item, ghost))
    return out


ASP_RULES = r"""
valid(P,I,G) :- place(P), item(I), ghost(G), not invalid(P,I,G).
invalid("hall","toy",_).
invalid("shed","lamp","small").
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for i in ITEMS:
        lines.append(asp.fact("item", i))
    for g in GHOSTS:
        lines.append(asp.fact("ghost", g))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and Python gates.")
    print("only in python:", sorted(py - cl))
    print("only in clingo:", sorted(cl - py))
    return 1


def build_story_params_from_all() -> list[StoryParams]:
    return [
        StoryParams("attic", "lamp", "pale", "Mina"),
        StoryParams("attic", "blanket", "shy", "Nora"),
        StoryParams("shed", "toy", "small", "Eli"),
    ]


def generate_many(params_list: list[StoryParams]) -> list[StorySample]:
    return [generate(p) for p in params_list]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("#show valid/3."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample]
    if args.all:
        samples = generate_many(build_story_params_from_all())
    else:
        samples = []
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            i += 1
            rng = random.Random(base_seed + i)
            try:
                params = resolve_params(args, rng)
            except StoryError as err:
                print(err)
                return
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

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.place} / {p.item} / {p.ghost}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
