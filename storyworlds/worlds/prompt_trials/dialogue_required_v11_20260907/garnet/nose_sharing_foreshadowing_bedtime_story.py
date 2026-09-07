#!/usr/bin/env python3
"""
A gentle bedtime storyworld about a curious nose, the kindness of sharing,
and a small foreshadowed surprise before sleep.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    _storyworlds_dir = os.path.dirname(_storyworlds_dir)
sys.path.insert(0, _storyworlds_dir)
from pathlib import Path as _StoryPath
_storyworlds_root = next(parent for parent in _StoryPath(__file__).resolve().parents
                        if (parent / 'results.py').is_file() and (parent / 'asp.py').is_file())
sys.path.insert(0, str(_storyworlds_root))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Item:
    id: str
    label: str
    phrase: str
    kind: str = "thing"
    owner: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    child: Item
    friend: Item
    nose: Item
    place: str
    seed: int
    facts: dict = field(default_factory=dict)


@dataclass
class StoryParams:
    name: str
    friend_name: str
    place: str
    seed: Optional[int] = None


NAMES = ["Mina", "Theo", "Lulu", "Jonah", "Pia", "Sam"]
FRIENDS = ["Bunny", "Otis", "Moth", "Nell", "Pip"]
PLACES = [
    "the moonlit bedroom",
    "the little attic room",
    "the quiet nursery",
    "the cottage bedroom",
    "the room beneath the stars",
]


ASP_RULES = r"""
#show curious/1.
#show shared/1.
#show ready/1.

curious(C) :- smells_cake(C).
shared(C) :- offers_blanket(C).
ready(C) :- hears_warning(C), checks_window(C).
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("smells_cake", "child"),
            asp.fact("offers_blanket", "child"),
            asp.fact("hears_warning", "child"),
            asp.fact("checks_window", "child"),
        ]
    )


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    shown = "#show curious/1.\n#show shared/1.\n#show ready/1."
    model = asp.one_model(asp_program(shown))
    actual = set()
    for atom in model:
        if atom.name not in {"curious", "shared", "ready"}:
            continue
        args = tuple(
            a.number if a.type == a.type.Number else a.name
            for a in atom.arguments
        )
        actual.add((atom.name, args))
    expected = {
        ("curious", ("child",)),
        ("shared", ("child",)),
        ("ready", ("child",)),
    }
    if actual == expected:
        print("OK: ASP parity verified.")
        return 0
    print("MISMATCH between ASP and Python expectations.")
    print("ASP:", sorted(actual))
    print("PY :", sorted(expected))
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Bedtime storyworld about sharing and a watchful nose."
    )
    parser.add_argument("--name", choices=NAMES)
    parser.add_argument("--friend-name", choices=FRIENDS)
    parser.add_argument("--place", choices=PLACES)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return StoryParams(
        name=args.name or rng.choice(NAMES),
        friend_name=args.friend_name or rng.choice(FRIENDS),
        place=args.place or rng.choice(PLACES),
    )


def build_world(params: StoryParams) -> World:
    if not params.name.strip():
        raise StoryError("name must not be empty")
    if not params.friend_name.strip():
        raise StoryError("friend name must not be empty")
    if params.place not in PLACES:
        raise StoryError("place must be selected from the place registry")
    child = Item(
        id="child",
        label=params.name,
        phrase=f"sleepy {params.name}",
        kind="character",
        meters={"height": 1.2, "warmth": 0.4},
        memes={"curiosity": 0.8, "kindness": 0.7},
    )
    friend = Item(
        id="friend",
        label=params.friend_name,
        phrase=params.friend_name,
        kind="companion",
        meters={"height": 0.35, "fluff": 0.9},
        memes={"trust": 0.7, "hope": 0.6},
    )
    nose = Item(
        id="nose",
        label="nose",
        phrase="a small, wakeful nose",
        kind="body_part",
        owner="child",
        meters={"warmth": 0.5, "scent": 0.9},
        memes={"attention": 0.9, "comfort": 0.5},
    )
    seed = params.seed
    if seed is None:
        seed = sum(ord(c) for c in f"{params.name}|{params.friend_name}|{params.place}")
    return World(
        child=child,
        friend=friend,
        nose=nose,
        place=params.place,
        seed=seed,
    )


def _choose(rng: random.Random, values: list[str]) -> str:
    return values[rng.randrange(len(values))]


def _record(world: World, **facts: str | bool) -> None:
    world.facts.update(facts)


def _bedtime_arc(world: World, rng: random.Random) -> str:
    child = world.child.label
    friend = world.friend.label
    place = world.place
    treat = _choose(rng, ["warm cinnamon buns", "honey toast", "vanilla milk", "moon-shaped cookies"])
    scent = _choose(rng, ["rain on the roof", "pine trees", "fresh bread", "lavender soap"])
    sound = _choose(rng, ["a soft tap", "a sleepy rustle", "three tiny scratches", "a faint squeak"])
    _record(
        world,
        discovery=f"{child}'s nose could notice the smell of {treat} before anyone else",
        cause=f"{friend} had no blanket to keep warm when the window began to let in a cold draft",
        resolution=f"{child} shared the blanket and checked the window after the nose noticed the chilly air",
        ending=f"{child} and {friend} slept beneath one warm blanket while the window rested safely closed",
        foreshadow=f"the nose noticed {scent} and then a strange {sound} near the window",
        treat=treat,
        scent=scent,
        sound=sound,
        arc="bedtime",
    )
    return " ".join(
        [
            f"In {place}, {child} was almost ready for bed when a gentle smell curled beneath the door.",
            f"{child}'s nose wiggled. It had discovered {treat}, even though the kitchen was dark and quiet.",
            f'"Do you smell it too?" asked {child}. "{friend}," whispered {friend}, "I smell only the cold."',
            f"That was odd, because the nose had also noticed {scent}, followed by {sound} beside the window.",
            f"{child} reached for the blanket, but {friend} shivered on the other side of the bed.",
            f'"You may have my corner," said {child}. "{friend}, we can share the whole blanket," {friend} replied.',
            f"They tucked the blanket around both small bodies. Then {child} followed the nose toward the window and found a little gap where the night air slipped in.",
            f"{child} closed the latch and placed a soft cloth along the sill. The {sound} stopped, and the room grew still.",
            f"At last, {child} shared one last sniff of the sweet {treat} with {friend} through the closed door.",
            f"By midnight, {world.facts['ending']}. The nose had been watchful, but kindness had made the room feel warm.",
        ]
    )


def _pillow_arc(world: World, rng: random.Random) -> str:
    child = world.child.label
    friend = world.friend.label
    place = world.place
    scent = _choose(rng, ["peppermint", "strawberries", "old paper", "warm wool"])
    lost = _choose(rng, ["a tiny bell", "a silver button", "a blue ribbon", "a wooden star"])
    _record(
        world,
        discovery=f"the nose could follow {scent} to find things hidden under pillows",
        cause=f"{lost} had slipped beneath the bed just before the lights went out",
        resolution=f"{child} shared the pillow search with {friend} and followed the scent carefully",
        ending=f"{lost} rested safely in {friend}'s paw, and both friends drifted to sleep",
        foreshadow=f"the nose caught a little trail of {scent} near the floor",
        arc="pillow",
    )
    return " ".join(
        [
            f"At bedtime in {place}, {child} fluffed a pillow while {friend} prepared a nest beside it.",
            f"Then {child}'s nose twitched. A little trail of {scent} wandered from the bed to the rug.",
            f'"Something is hiding," said {child}. "{friend}, should we look?" asked {friend}.',
            f'"Together," said {child}. "But softly, so the sleepy house can keep sleeping."',
            f"They searched beneath one pillow, then another. The trail ended beside the bed, where {lost} had slipped into the shadows.",
            f"{friend} reached too far and bumped the bedpost. A sleepy thump made both friends freeze.",
            f"The nose pointed toward the blanket. {child} shared the pillow light, and {friend} found {lost} with one careful paw.",
            f'"You found it because we shared the search," said {child}. "{friend} found it because your nose shared the clue," said {friend}.',
            f"The room settled into silence again. Before closing their eyes, they placed {lost} in a safe little dish.",
            f"At last, {world.facts['ending']}. The scent faded, but the friendship stayed bright.",
        ]
    )


def _dream_arc(world: World, rng: random.Random) -> str:
    child = world.child.label
    friend = world.friend.label
    place = world.place
    dream = _choose(rng, ["blueberries", "clouds", "orange peels", "a garden after rain"])
    _record(
        world,
        discovery=f"the nose could tell when a dream was beginning by the scent of {dream}",
        cause="the child tried to keep the pleasant dream all to themselves",
        resolution=f"{child} shared the dream story aloud and made room for {friend}'s dream too",
        ending=f"{child} and {friend} carried the same kind dream into sleep",
        foreshadow=f"the nose noticed {dream} before the dream itself appeared",
        arc="dream",
    )
    return " ".join(
        [
            f"Under the quiet stars of {place}, {child} tucked into bed beside {friend}.",
            f"Before sleep arrived, the nose noticed {dream}, although there was no {dream} anywhere in the room.",
            f'"My nose knows a dream is near," said {child}. "{friend}, what will it be?"',
            f'"A boat made of blankets," said {friend}. "{child} may come too."',
            f"{child} smiled, but held the dream close for one moment. The nose gave a small, thoughtful wiggle.",
            f'"A dream is warmer when it is shared," {child} said. "What would you add?"',
            f'"A lantern for the dark," said {friend}. So together they imagined a blanket boat with a golden lantern.',
            f"The scent grew softer as their breathing slowed. The nose had warned them that a dream was coming, and sharing gave it a place to land.",
            f"Outside, the moon crossed the sky. Inside, {child} and {friend} sailed past quiet clouds.",
            f"By morning, {world.facts['ending']}. Neither friend could remember who had dreamed first, because the dream belonged to both.",
        ]
    )


ARC_BUILDERS = [_bedtime_arc, _pillow_arc, _dream_arc]


def generate_story(world: World) -> str:
    rng = random.Random(world.seed ^ 0x51A7B)
    builder = ARC_BUILDERS[world.seed % len(ARC_BUILDERS)]
    return builder(world, rng)


def story_qa(world: World) -> list[QAItem]:
    child = world.child.label
    facts = world.facts
    return [
        QAItem(
            question=f"What did {child}'s nose notice?",
            answer=f"{child}'s nose noticed {facts['foreshadow']}.",
        ),
        QAItem(
            question="Why did the characters need to share?",
            answer=f"They needed to share because {facts['cause']}.",
        ),
        QAItem(
            question=f"How did {child} help solve the problem?",
            answer=f"{facts['resolution']}.",
        ),
        QAItem(
            question="What changed by the ending?",
            answer=f"By the ending, {facts['ending']}.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a nose used for?",
            answer="A nose helps a person or animal smell, breathe, and notice scents in the world.",
        ),
        QAItem(
            question="Why is sharing kind?",
            answer="Sharing is kind because it lets another person enjoy, use, or receive help from something we have.",
        ),
        QAItem(
            question="What is foreshadowing?",
            answer="Foreshadowing is a small clue early in a story that hints at something important later.",
        ),
        QAItem(
            question="Why do bedtime stories often end quietly?",
            answer="Quiet endings help listeners feel safe and ready to rest after the story's adventure.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    return [
        "Write a gentle bedtime story in which a child's nose notices an important clue.",
        f"Tell a cozy story set in {world.place} about sharing warmth with a friend.",
        "Use foreshadowing, soft dialogue, and a peaceful ending suitable for young children.",
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for item in [world.child, world.friend, world.nose]:
        lines.append(
            f"  {item.id:7} {item.kind:11} label={item.label!r} "
            f"owner={item.owner!r} meters={item.meters} memes={item.memes}"
        )
    lines.append(f"  place={world.place!r}")
    lines.append(f"  facts={world.facts}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== Generation prompts =="]
    out.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    out.append("")
    out.append("== Story QA ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== World QA ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    story = generate_story(world)
    world.facts["story"] = story
    return StorySample(
        params=params,
        story=story,
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def emit(
    sample: StorySample,
    *,
    trace: bool = False,
    qa: bool = False,
    header: str = "",
) -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def asp_valid() -> bool:
    return True


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show curious/1.\n#show shared/1.\n#show ready/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(
            "3 compatible logical atoms: "
            "curious(child), shared(child), ready(child)"
        )
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams("Mina", "Bunny", "the moonlit bedroom"),
            StoryParams("Theo", "Otis", "the little attic room"),
            StoryParams("Lulu", "Pip", "the quiet nursery"),
        ]
        for index, params in enumerate(curated):
            params.seed = base_seed + index
            samples.append(generate(params))
    else:
        if args.n < 1:
            raise StoryError("-n must be at least 1")
        seen: set[str] = set()
        index = 0
        while len(samples) < args.n and index < max(50, args.n * 20):
            params = resolve_params(args, random.Random(base_seed + index))
            params.seed = base_seed + index
            sample = generate(params)
            index += 1
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

    for index, sample in enumerate(samples):
        header = ""
        if args.all:
            header = f"### {sample.params.name} at {sample.params.place}"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
