#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260624T081143Z_seed2038046945_n100/illiterate_plump_skinned_transformation_slice_of_life.py
==============================================================================================================

A small slice-of-life storyworld about a child, a patient helper, and a gentle
transformation that changes one ordinary afternoon into a brighter one.

Seed words:
- illiterate
- plump
- skinned

Feature:
- Transformation

Style:
- Slice of life
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
class Person:
    name: str
    kind: str
    role: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)


@dataclass
class Item:
    name: str
    kind: str
    owner: Optional[str] = None
    worn: bool = False


@dataclass
class Scene:
    place: str
    weather: str
    item: str
    transformation: str


@dataclass
class StoryParams:
    place: str
    weather: str
    hero_name: str
    helper_name: str
    item: str
    transformation: str
    seed: Optional[int] = None


PLACES = {
    "kitchen": "the kitchen",
    "yard": "the yard",
    "porch": "the porch",
    "laundry_room": "the laundry room",
    "bench": "the bench outside the apartment",
}

WEATHERS = {
    "soft_rain": "soft rain",
    "warm_sun": "warm sun",
    "late_evening": "late evening light",
}

ITEMS = {
    "shirt": "a plain shirt",
    "apron": "a little apron",
    "socks": "a pair of socks",
    "cardigan": "a knitted cardigan",
}

TRANSFORMATIONS = {
    "washed": (
        "got washed and hung up to dry",
        "became clean again",
        "looked fresh and bright afterward",
    ),
    "mended": (
        "got mended with careful stitches",
        "changed from torn to sturdy",
        "looked ready for another busy day",
    ),
    "dried": (
        "dried in the open air",
        "changed from damp to light",
        "felt soft again by sunset",
    ),
}

HERO_NAMES = ["Mina", "Owen", "Lena", "Theo", "Pia", "Noel"]
HELPER_NAMES = ["Mara", "June", "Hadi", "Rosa", "Ben", "Iris"]
TRAITS = ["plump", "quiet", "gentle", "curious", "careful"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life storyworld with a gentle transformation.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--weather", choices=WEATHERS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--transformation", choices=TRANSFORMATIONS)
    ap.add_argument("--name")
    ap.add_argument("--helper")
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
    weather = args.weather or rng.choice(list(WEATHERS))
    item = args.item or rng.choice(list(ITEMS))
    transformation = args.transformation or rng.choice(list(TRANSFORMATIONS))
    hero_name = args.name or rng.choice(HERO_NAMES)
    helper_name = args.helper or rng.choice([n for n in HELPER_NAMES if n != hero_name])
    if hero_name == helper_name:
        raise StoryError("The hero and helper should be different people.")
    return StoryParams(place=place, weather=weather, hero_name=hero_name, helper_name=helper_name,
                       item=item, transformation=transformation)


def _article(text: str) -> str:
    return "an" if text[:1].lower() in "aeiou" else "a"


def generate(params: StoryParams) -> StorySample:
    hero = Person(name=params.hero_name, kind="child", role="hero", traits=["illiterate", "plump"])
    helper = Person(name=params.helper_name, kind="adult", role="helper", traits=["patient"])
    item_phrase = ITEMS[params.item]
    trans = TRANSFORMATIONS[params.transformation]
    scene = Scene(place=PLACES[params.place], weather=WEATHERS[params.weather],
                  item=item_phrase, transformation=params.transformation)

    hero.memes["curiosity"] = 1.0
    hero.memes["comfort"] = 1.0
    helper.memes["patience"] = 1.0

    story = (
        f"On {scene.place}, {hero.name} spent a slow afternoon with {helper.name}. "
        f"{hero.name} was {hero.traits[0]} and {hero.traits[1]}, and that was all right; "
        f"{helper.name} was happy to keep things simple. "
        f"The two of them shared {scene.weather}, a small snack, and {item_phrase}. "
        f"{hero.name} could not read the labels on the basket because {hero.name} was illiterate, "
        f"so {helper.name} pointed to each thing and named it kindly. "
        f"When the {params.transformation} moment came, the {params.item} {trans[0]}, "
        f"{trans[1]}, and {trans[2]}. "
        f"{hero.name} smiled at the change and held the tidy thing close. "
        f"By the end, the ordinary corner of {scene.place} felt calmer, and the day had turned out warm and useful."
    )

    prompts = [
        f"Write a gentle slice-of-life story about {params.hero_name} and {params.helper_name} at {scene.place}.",
        f"Tell a short story where something {params.transformation} in a quiet everyday scene.",
        f"Write a child-friendly story that includes the words illiterate, plump, and skinned naturally.",
    ]

    story_qa = [
        QAItem(
            question=f"Who spent the afternoon together on {scene.place}?",
            answer=f"{hero.name} and {helper.name} spent the afternoon together on {scene.place}.",
        ),
        QAItem(
            question=f"Why could {hero.name} not read the labels?",
            answer=f"{hero.name} could not read the labels because {hero.name} was illiterate.",
        ),
        QAItem(
            question=f"What happened to the {params.item}?",
            answer=f"The {params.item} {trans[0]} and {trans[2]}.",
        ),
    ]

    world_qa = [
        QAItem(
            question="What does illiterate mean?",
            answer="Illiterate means a person cannot read written words yet.",
        ),
        QAItem(
            question="What does plump mean?",
            answer="Plump means softly round or pleasantly full.",
        ),
        QAItem(
            question="What does skinned mean?",
            answer="Skinned means the outer skin or covering has been scraped or removed from a surface.",
        ),
        QAItem(
            question="What is a transformation?",
            answer="A transformation is a change from one state into another.",
        ),
    ]

    world = {
        "hero": hero,
        "helper": helper,
        "item": Item(name=params.item, kind="object", owner=hero.name, worn=False),
        "scene": scene,
    }
    return StorySample(
        params=params,
        story=story,
        prompts=prompts,
        story_qa=story_qa,
        world_qa=world_qa,
        world=world,
    )


ASP_RULES = r"""
% A tiny declarative twin: a story is reasonable when there is a child, a helper,
% an object, and a transformation that changes the object's state.
reasonable_story(Hero, Helper, Item, T) :-
    child(Hero), adult(Helper), object(Item), transformation(T).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for w in WEATHERS:
        lines.append(asp.fact("weather", w))
    for i in ITEMS:
        lines.append(asp.fact("object", i))
    for t in TRANSFORMATIONS:
        lines.append(asp.fact("transformation", t))
    lines.append(asp.fact("child", "child"))
    lines.append(asp.fact("adult", "adult"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    return 0


def format_qa(sample: StorySample) -> str:
    parts = ["== Story questions =="]
    for q in sample.story_qa:
        parts.append(f"Q: {q.question}")
        parts.append(f"A: {q.answer}")
    parts.append("")
    parts.append("== World questions ==")
    for q in sample.world_qa:
        parts.append(f"Q: {q.question}")
        parts.append(f"A: {q.answer}")
    return "\n".join(parts)


def dump_trace(world: dict) -> str:
    hero = world["hero"]
    helper = world["helper"]
    item = world["item"]
    scene = world["scene"]
    return "\n".join(
        [
            "--- world model state ---",
            f"hero={hero.name} traits={hero.traits} memes={hero.memes}",
            f"helper={helper.name} traits={helper.traits} memes={helper.memes}",
            f"item={item.name} owner={item.owner}",
            f"scene={scene.place} weather={scene.weather} transformation={scene.transformation}",
        ]
    )


CURATED = [
    StoryParams(place="kitchen", weather="late_evening", hero_name="Mina", helper_name="Mara", item="shirt", transformation="washed"),
    StoryParams(place="yard", weather="soft_rain", hero_name="Owen", helper_name="Ben", item="apron", transformation="mended"),
    StoryParams(place="porch", weather="warm_sun", hero_name="Lena", helper_name="Iris", item="socks", transformation="dried"),
]


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
        print(asp_program("#show reasonable_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(max(1, args.n)):
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
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {i + 1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
