#!/usr/bin/env python3
"""
A standalone Storyweavers world: broccoli, pelt, derive, with Friendship,
Flashback, and Curiosity in a post office.

The story is a small rhyming tale about a child who spots a strange green parcel
at the post office, remembers a friendship from a flashback, and uses curiosity
to derive the right destination.
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

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    location: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character" and self.type in {"girl", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.kind == "character" and self.type in {"boy", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class World:
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    trace_log: list[str] = field(default_factory=list)

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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

    def log(self, text: str) -> None:
        self.trace_log.append(text)

    def copy(self) -> "World":
        import copy

        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


@dataclass
class StoryParams:
    name: str
    friend: str
    item: str
    seed: Optional[int] = None


POST_OFFICE = "the post office"

NAMES = ["Mina", "Toby", "Lena", "Noah", "Pia", "Eli"]
FRIENDS = ["June", "Ravi", "Ivy", "Milo", "Nia", "Zed"]

ASP_RULES = r"""
#show valid_story/2.
valid_story(Name, Friend) :- person(Name), person(Friend), Name != Friend.
"""


def asp_facts() -> str:
    import asp
    lines = [asp.fact("place", "post_office"), asp.fact("story_theme", "rhyming")]
    for n in NAMES:
        lines.append(asp.fact("person", n))
    for n in FRIENDS:
        lines.append(asp.fact("person", n))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple[str, str]]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def _reasonableness_gate(params: StoryParams) -> None:
    if params.name == params.friend:
        raise StoryError("The child and friend must be different people.")
    if params.item not in {"broccoli", "pelt", "derive"}:
        raise StoryError("Unknown seed word for this world.")


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Rhyming post-office friendship storyworld.")
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--friend", choices=FRIENDS)
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
    friend = args.friend or rng.choice([f for f in FRIENDS if f != name])
    params = StoryParams(name=name, friend=friend, item="broccoli")
    _reasonableness_gate(params)
    return params


def _update_trace(world: World, text: str) -> None:
    world.log(text)


def generate(params: StoryParams) -> StorySample:
    _reasonableness_gate(params)
    world = World(POST_OFFICE)

    child = world.add(Entity(id=params.name, kind="character", type="child", label=params.name))
    friend = world.add(Entity(id=params.friend, kind="character", type="child", label=params.friend))
    clerk = world.add(Entity(id="clerk", kind="character", type="adult", label="the clerk"))
    parcel = world.add(Entity(
        id="parcel",
        kind="thing",
        type="parcel",
        label="parcel",
        phrase="a green parcel with a broccoli bow",
        owner=friend.id,
        location="counter",
    ))
    pelt = world.add(Entity(
        id="pelt",
        kind="thing",
        type="pelt",
        label="pelt",
        phrase="a soft pelt cap in the lost-and-found",
        owner=clerk.id,
        location="shelf",
    ))

    child.memes["curiosity"] = 1
    child.memes["friendship"] = 1
    friend.memes["friendship"] = 1

    world.say(
        f"At the post office, {params.name} went in with a skip and a grin, "
        f"where letters flew fast and parcels tucked in."
    )
    world.say(
        f"{params.name} spied a green parcel tied neat with care, "
        f"and a broccoli bow bobbed like a leafy dare."
    )

    world.para()
    world.say(
        f"{params.name} felt curiosity dance and whirl, "
        f"for the parcel looked odd in a mail-room swirl."
    )
    _update_trace(world, f"{params.name} is curious about the broccoli parcel.")
    child.meters["curiosity"] = 1

    world.say(
        f"Then came a flashback, soft as rain on a pane: "
        f"{params.name} remembered {params.friend} sharing lunch in the rain."
    )
    child.memes["flashback"] = 1
    child.memes["friendship"] += 1

    world.para()
    world.say(
        f"In that old bright memory, they traded a snack, "
        f"and promised to help if the mail got off track."
    )
    world.say(
        f"So {params.name} did a little deriving right there: "
        f"if the bow was broccoli, the parcel should go where it would share."
    )
    child.memes["derive"] = 1

    world.say(
        f"{params.name} asked the clerk, 'Who is this for?' with a spark, "
        f"and the clerk checked the tag in the postal dark."
    )
    parcel.meters["moved"] = 1

    world.say(
        f"'It's for {params.friend},' said the clerk with a cheer. "
        f"'They wrote the address so the route is clear.'"
    )
    friend.memes["joy"] = 1
    friend.location = "counter"

    world.para()
    world.say(
        f"{params.name} smiled at {params.friend} and stood side by side, "
        f"as friendship shone warm like a lantern inside."
    )
    world.say(
        f"The pelt cap stayed on the shelf, safe and dry, "
        f"while the broccoli parcel went wandering by."
    )
    child.memes["joy"] = 1
    child.meters["peace"] = 1
    friend.meters["peace"] = 1

    world.facts.update(
        child=child.id,
        friend=friend.id,
        clerk=clerk.id,
        parcel=parcel.id,
        pelt=pelt.id,
        place=POST_OFFICE,
        theme="rhyming",
    )

    story = world.render()
    prompts = [
        "Write a rhyming story set in a post office about a child who notices a broccoli parcel, remembers a friendship, and figures out what it means.",
        f"Tell a gentle rhyming tale where {params.name} uses curiosity to derive the right mail destination for {params.friend}.",
        "Write a short child-friendly story about a flashback, a friendship, and a strange broccoli bow at the post office.",
    ]

    story_qa = [
        QAItem(
            question=f"Where was {params.name} when the story happened?",
            answer=f"{params.name} was at the post office, where letters and parcels were being sorted.",
        ),
        QAItem(
            question=f"What made {params.name} curious?",
            answer=f"{params.name} was curious about the green parcel with the broccoli bow.",
        ),
        QAItem(
            question=f"What did {params.name} remember in the flashback?",
            answer=f"{params.name} remembered a happy time with {params.friend}, when they shared lunch and promised to help each other.",
        ),
        QAItem(
            question=f"What did {params.name} derive from the clue?",
            answer=f"{params.name} derived that the parcel should go to {params.friend}, because the address tag and the broccoli bow pointed to the right friend.",
        ),
    ]

    world_qa = [
        QAItem(
            question="What is a post office for?",
            answer="A post office is a place where people send, sort, and pick up letters and parcels.",
        ),
        QAItem(
            question="What is curiosity?",
            answer="Curiosity is the wish to learn more about something that seems interesting or puzzling.",
        ),
        QAItem(
            question="What is a flashback?",
            answer="A flashback is a story moment that remembers something from before.",
        ),
        QAItem(
            question="What does derive mean?",
            answer="To derive something means to figure it out from clues or reasons.",
        ),
        QAItem(
            question="What is broccoli?",
            answer="Broccoli is a green vegetable with a bumpy top that looks like tiny trees.",
        ),
        QAItem(
            question="What is a pelt?",
            answer="A pelt is animal skin with fur still on it, often used to make something warm.",
        ),
    ]

    return StorySample(
        params=params,
        story=story,
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
        print("--- world trace ---")
        for line in sample.world.trace_log:
            print(line)
    if qa:
        print()
        for i, item in enumerate(sample.prompts, 1):
            print(f"P{i}: {item}")
        print()
        for item in sample.story_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
        print()
        for item in sample.world_qa:
            print(f"WQ: {item.question}")
            print(f"WA: {item.answer}")


def asp_verify() -> int:
    py = {(n, f) for n in NAMES for f in FRIENDS if n != f}
    cl = set(asp_valid_stories())
    if py == cl:
        print(f"OK: ASP matches Python ({len(py)} compatible pairs).")
        return 0
    print("MISMATCH between ASP and Python:")
    print("only in python:", sorted(py - cl))
    print("only in ASP:", sorted(cl - py))
    return 1


def generate_all(args: argparse.Namespace) -> list[StorySample]:
    samples = []
    for n in NAMES:
        for f in FRIENDS:
            if n == f:
                continue
            samples.append(generate(StoryParams(name=n, friend=f, item="broccoli")))
    return samples


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        pairs = asp_valid_stories()
        print(f"{len(pairs)} compatible stories:")
        for n, f in pairs:
            print(f"  {n} + {f}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    if args.all:
        samples = generate_all(args)
    else:
        samples = []
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
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
        header = ""
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
