#!/usr/bin/env python3
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
class Character:
    id: str
    role: str
    name: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self) -> str:
        return "they"


@dataclass
class ObjectThing:
    id: str
    label: str
    owner: Optional[str] = None
    location: str = "unknown"
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    setting: str
    mood: str
    characters: dict[str, Character] = field(default_factory=dict)
    objects: dict[str, ObjectThing] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def add_character(self, c: Character) -> Character:
        self.characters[c.id] = c
        return c

    def add_object(self, o: ObjectThing) -> ObjectThing:
        self.objects[o.id] = o
        return o


@dataclass
class StoryParams:
    place: str
    hero: str
    sidekick: str
    culprit: str
    seed: Optional[int] = None


PLACES = {
    "bakery": {
        "setting": "the little bakery",
        "sound": "ding!",
        "echo": "clang-clink",
        "smell": "warm bread",
    },
    "kitchen": {
        "setting": "the bright kitchen",
        "sound": "tap-tap",
        "echo": "whirr",
        "smell": "butter and toast",
    },
    "market": {
        "setting": "the crowded market stall",
        "sound": "shhff!",
        "echo": "rustle-rustle",
        "smell": "sweet spice",
    },
}

HEROES = ["Mina", "Leo", "Tia", "Noah", "Ivy", "Omar"]
SIDEKICKS = ["Pip", "Nia", "Bram", "Zuzu", "Milo", "Fern"]
CULPRITS = ["the cat", "a sneaky crow", "the windy door", "a rolling cart"]

CURATED = [
    StoryParams(place="bakery", hero="Mina", sidekick="Pip", culprit="a sneaky crow"),
    StoryParams(place="kitchen", hero="Leo", sidekick="Nia", culprit="the windy door"),
    StoryParams(place="market", hero="Ivy", sidekick="Bram", culprit="the cat"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mystery storyworld with bagels, sound effects, and a bad ending.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--name")
    ap.add_argument("--sidekick")
    ap.add_argument("--culprit", choices=CULPRITS)
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
    hero = args.name or rng.choice(HEROES)
    sidekick = args.sidekick or rng.choice([x for x in SIDEKICKS if x != hero])
    culprit = args.culprit or rng.choice(CULPRITS)
    if sidekick == hero:
        raise StoryError("The hero and sidekick must be different characters.")
    return StoryParams(place=place, hero=hero, sidekick=sidekick, culprit=culprit)


def asp_facts() -> str:
    import asp
    lines = []
    for place, data in PLACES.items():
        lines.append(asp.fact("place", place))
        lines.append(asp.fact("setting_name", place, data["setting"]))
        lines.append(asp.fact("sound", place, data["sound"]))
    for c in CULPRITS:
        lines.append(asp.fact("culprit", c))
    return "\n".join(lines)


ASP_RULES = r"""
valid_story(P,C) :- place(P), culprit(C).
#show valid_story/2.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = {(p, c) for p in PLACES for c in CULPRITS}
    cl = set(asp_valid())
    if py == cl:
        print(f"OK: ASP matches Python gate ({len(py)} combinations).")
        return 0
    print("MISMATCH")
    print("only python:", sorted(py - cl))
    print("only asp:", sorted(cl - py))
    return 1


def validate_explicit(args: argparse.Namespace) -> None:
    if args.sidekick and args.name and args.sidekick == args.name:
        raise StoryError("The sidekick must not be the same as the hero.")
    if args.place and args.culprit and args.place not in PLACES:
        raise StoryError("Unknown place.")


def generate(params: StoryParams) -> StorySample:
    place = PLACES[params.place]
    world = World(setting=place["setting"], mood="mysterious")
    hero = world.add_character(Character(id="hero", role="hero", name=params.hero))
    sidekick = world.add_character(Character(id="sidekick", role="sidekick", name=params.sidekick))
    culprit = world.add_character(Character(id="culprit", role="culprit", name=params.culprit))
    bagel = world.add_object(ObjectThing(id="bagel", label="bagel", owner=hero.id, location="table"))

    hero.meters["worry"] = 1.0
    sidekick.memes["curious"] = 1.0
    world.facts["place"] = params.place
    world.facts["hero"] = params.hero
    world.facts["sidekick"] = params.sidekick
    world.facts["culprit"] = params.culprit

    world.say(f"In {place['setting']}, {params.hero} found a bagel on the table and frowned.")
    world.say(f'The room answered with {place["sound"]} and a soft {place["echo"]}.')
    world.say(f"{params.hero} and {params.sidekick} decided to unite and look for clues together.")
    world.para()
    world.say(f"They followed the crumbs past the sink, where the smell of {place['smell']} hung in the air.")
    world.say(f"Then came {place['sound']} again, and the bagel vanished from the table.")
    world.say(f"{params.sidekick} pointed at an open window while {params.hero} listened to the tiny scuff of feet.")
    world.say(f"They united their clues, but the trail led only to {params.culprit}, and that made the mystery worse.")
    world.para()
    bagel.location = "gone"
    culprit.memes["guilty"] = 1.0
    hero.memes["sad"] = 1.0
    sidekick.memes["sad"] = 1.0
    world.say(f"At the end, the bagel was still gone, and the friends had to sit with an empty plate.")
    world.say(f"The bad ending left {params.hero} and {params.sidekick} quiet, while the last crumbs stayed on the floor.")

    world.facts["bagel_location"] = bagel.location
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    p = world.facts["place"]
    h = world.facts["hero"]
    s = world.facts["sidekick"]
    return [
        f"Write a short mystery story for children set in the {p} with {h} and {s}, featuring a bagel and the word unite.",
        f"Tell a gentle, clue-filled story where two friends unite to search for a missing bagel in the {p}.",
        f"Write a simple mystery with sound effects, a bagel, and a bad ending at the {p}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What were the friends looking for?",
            answer="They were looking for the missing bagel.",
        ),
        QAItem(
            question="What did the friends do together to solve the mystery?",
            answer="They united and looked for clues together.",
        ),
        QAItem(
            question="Did the story end happily?",
            answer="No. It ended badly because the bagel was still gone.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a bagel?",
            answer="A bagel is a round bread roll with a hole in the middle.",
        ),
        QAItem(
            question="What does it mean to unite?",
            answer="To unite means to come together as one team or group.",
        ),
        QAItem(
            question="Why do stories use sound effects?",
            answer="Sound effects help show what is happening and make the scene feel lively.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for c in world.characters.values():
        lines.append(f"  {c.id}: name={c.name} role={c.role} meters={c.meters} memes={c.memes}")
    for o in world.objects.values():
        lines.append(f"  {o.id}: label={o.label} owner={o.owner} location={o.location}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    out.extend(sample.prompts)
    out.append("")
    out.append("== story qa ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== world qa ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


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
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        pairs = asp_valid()
        print(f"{len(pairs)} valid stories:")
        for place, culprit in pairs:
            print(f"  {place} / {culprit}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for p in CURATED:
            samples.append(generate(p))
    else:
        for i in range(args.n):
            rng = random.Random(base_seed + i)
            try:
                validate_explicit(args)
                p = resolve_params(args, rng)
            except StoryError as e:
                print(e)
                return
            p.seed = base_seed + i
            samples.append(generate(p))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, s in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(s, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
