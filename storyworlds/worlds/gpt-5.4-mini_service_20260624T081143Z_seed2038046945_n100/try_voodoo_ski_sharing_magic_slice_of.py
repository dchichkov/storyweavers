#!/usr/bin/env python3
"""
storyworlds/worlds/try_voodoo_ski_sharing_magic_slice_of.py
===========================================================

A small slice-of-life storyworld about children, shared ski gear, and a tiny
bit of voodoo-style magic that helps them try again kindly.

Premise:
- A child wants to try skiing.
- The child has to share a pair of skis or other winter gear with a sibling/
  friend.
- A small magical charm, called voodoo in-story as a make-believe good-luck
  practice, helps them calm down and cooperate.
- The story resolves with sharing, practice, and a warm ending image.

This script follows the Storyweavers storyworld contract:
- self-contained stdlib script
- imports shared results eagerly
- lazy import of storyworlds.asp only in ASP helpers
- implements StoryParams, registries, build_parser, resolve_params,
  generate, emit, and main
- supports default run, -n, --all, --seed, --trace, --qa, --json, --asp,
  --verify, and --show-asp
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass(frozen=True)
class Place:
    id: str
    name: str
    setting: str
    detail: str
    indoor: bool = False


@dataclass(frozen=True)
class ChildSpec:
    id: str
    name: str
    type: str
    trait: str


@dataclass(frozen=True)
class SharedItem:
    id: str
    label: str
    phrase: str
    kind: str
    used_for: str
    plural: bool = False


@dataclass(frozen=True)
class MagicCharm:
    id: str
    label: str
    phrase: str
    effect: str
    comfort: str


@dataclass(frozen=True)
class WorldState:
    place: Place
    child: ChildSpec
    friend: ChildSpec
    item: SharedItem
    charm: MagicCharm
    try_count: int = 0
    calm: int = 0
    sharing: int = 0
    confidence: int = 0
    success: bool = False
    story_points: tuple[str, ...] = ()


@dataclass
class StoryParams:
    place: str
    child: str
    friend: str
    item: str
    charm: str
    seed: Optional[int] = None


PLACES = {
    "small_hill": Place(
        id="small_hill",
        name="the little ski hill",
        setting="the little ski hill",
        detail="The hill was soft and friendly, with a short path up to the rope tow.",
        indoor=False,
    ),
    "backyard_slope": Place(
        id="backyard_slope",
        name="the backyard slope",
        setting="the backyard slope",
        detail="The backyard slope had a shallow dip and a fence lined with twinkling lights.",
        indoor=False,
    ),
    "lodge_corner": Place(
        id="lodge_corner",
        name="the lodge corner",
        setting="the lodge corner",
        detail="The lodge corner smelled like cocoa and wet mittens, with a bench by the window.",
        indoor=True,
    ),
}

CHILDREN = {
    "mila": ChildSpec("mila", "Mila", "girl", "curious"),
    "noah": ChildSpec("noah", "Noah", "boy", "patient"),
    "ava": ChildSpec("ava", "Ava", "girl", "gentle"),
    "leo": ChildSpec("leo", "Leo", "boy", "brave"),
    "zoe": ChildSpec("zoe", "Zoe", "girl", "bright"),
    "max": ChildSpec("max", "Max", "boy", "thoughtful"),
}

ITEMS = {
    "ski": SharedItem("ski", "skis", "a pair of skis", "ski", "skiing", plural=True),
    "boots": SharedItem("boots", "boots", "warm ski boots", "boots", "skiing", plural=True),
    "poles": SharedItem("poles", "poles", "a set of ski poles", "poles", "balancing", plural=True),
    "hat": SharedItem("hat", "hat", "a fuzzy hat", "hat", "keeping warm"),
}

CHARMS = {
    "voodoo_button": MagicCharm(
        "voodoo_button",
        "a little voodoo button",
        "a tiny voodoo button with a stitched smile",
        "brings brave thoughts and calm hands",
        "The charm felt warm in a pocket, like a secret promise to try again.",
    ),
    "voodoo_string": MagicCharm(
        "voodoo_string",
        "a voodoo string doll",
        "a small voodoo string doll tied with a red ribbon",
        "helps a child share without fuss",
        "The ribbon bounced softly whenever the children remembered to take turns.",
    ),
    "magic_stone": MagicCharm(
        "magic_stone",
        "a magic stone",
        "a smooth magic stone painted with a star",
        "makes wobbly knees feel steady",
        "The stone stayed cool in a mitten and seemed to whisper, keep going.",
    ),
}

GENDERS = ["girl", "boy"]

ASP_RULES = r"""
#show valid_story/4.

place(P) :- place_fact(P).
child(C) :- child_fact(C).
item(I) :- item_fact(I).
charm(H) :- charm_fact(H).

good_pair(C1,C2) :- child(C1), child(C2), C1 != C2.
shareable(I) :- item(I).

valid_story(P,C1,C2,I,H) :- place(P), good_pair(C1,C2), shareable(I), charm(H).
"""


def asp_facts() -> str:
    import asp

    lines = []
    for p in PLACES.values():
        lines.append(asp.fact("place_fact", p.id))
        if p.indoor:
            lines.append(asp.fact("indoor_place", p.id))
    for c in CHILDREN.values():
        lines.append(asp.fact("child_fact", c.id))
    for i in ITEMS.values():
        lines.append(asp.fact("item_fact", i.id))
        if i.plural:
            lines.append(asp.fact("plural_item", i.id))
    for h in CHARMS.values():
        lines.append(asp.fact("charm_fact", h.id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid_story/5."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    combos = set(valid_combos())
    asp_set = {(p, c1, c2, i, h) for (p, c1, c2, i, h) in asp_valid_stories()}
    if combos == asp_set:
        print(f"OK: clingo gate matches Python gate ({len(combos)} stories).")
        return 0
    print("MISMATCH between clingo and Python gates:")
    print("  only in python:", sorted(combos - asp_set))
    print("  only in clingo:", sorted(asp_set - combos))
    return 1


def valid_combos() -> list[tuple[str, str, str, str, str]]:
    combos = []
    for p in PLACES:
        for c1 in CHILDREN:
            for c2 in CHILDREN:
                if c1 == c2:
                    continue
                for i in ITEMS:
                    for h in CHARMS:
                        combos.append((p, c1, c2, i, h))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A slice-of-life story about trying ski time, sharing, and a little voodoo magic."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--child", choices=CHILDREN)
    ap.add_argument("--friend", choices=CHILDREN)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--charm", choices=CHARMS)
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
    if args.child and args.friend and args.child == args.friend:
        raise StoryError("The child and friend must be different people.")
    place = args.place or rng.choice(list(PLACES))
    child = args.child or rng.choice(list(CHILDREN))
    friend_choices = [c for c in CHILDREN if c != child]
    friend = args.friend or rng.choice(friend_choices)
    item = args.item or rng.choice(list(ITEMS))
    charm = args.charm or rng.choice(list(CHARMS))
    return StoryParams(place=place, child=child, friend=friend, item=item, charm=charm)


def _story_state(params: StoryParams) -> WorldState:
    return WorldState(
        place=PLACES[params.place],
        child=CHILDREN[params.child],
        friend=CHILDREN[params.friend],
        item=ITEMS[params.item],
        charm=CHARMS[params.charm],
    )


def generate(params: StoryParams) -> StorySample:
    world = _story_state(params)
    c = world.child
    f = world.friend
    p = world.place
    item = world.item
    charm = world.charm

    prompts = [
        f"Write a small slice-of-life story about {c.name} and {f.name} sharing {item.phrase} at {p.name}, with a little voodoo magic.",
        f"Tell a gentle story where children try to ski, take turns, and use {charm.phrase} to stay calm.",
        f"Write a child-friendly story using the words try, voodoo, ski, sharing, and magic.",
    ]

    sents = []
    sents.append(f"{c.name} had been waiting all week to try ski time at {p.name}.")
    sents.append(f"{f.name} came along too, and they only had {item.phrase} to share.")
    sents.append(f"{p.detail}")
    sents.append(f"When {c.name} reached for the gear first, {f.name} paused and looked a little worried.")
    sents.append(f"Then {c.name} found {charm.phrase} tucked inside a mitten pocket.")
    sents.append(f"It was their pretend voodoo good-luck charm, and it {charm.effect}.")
    sents.append(f"{c.name} smiled, handed the {item.label} over, and said they could take turns.")
    sents.append(f"{f.name} laughed, because sharing felt easier with {charm.phrase} nearby.")
    sents.append(f"One child tried a wobbly slide, then the other tried too, and soon both were grinning.")
    sents.append(f"By the end, {c.name} and {f.name} were ski-ing slowly down the little hill together, warm cheeks glowing and the charm still safe in a pocket.")

    story = " ".join(sents)

    world = WorldState(
        place=world.place,
        child=world.child,
        friend=world.friend,
        item=world.item,
        charm=world.charm,
        try_count=2,
        calm=1,
        sharing=1,
        confidence=1,
        success=True,
        story_points=tuple(sents),
    )

    return StorySample(
        params=params,
        story=story,
        prompts=prompts,
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def story_qa(world: WorldState) -> list[QAItem]:
    c, f, p, item, charm = world.child, world.friend, world.place, world.item, world.charm
    return [
        QAItem(
            question=f"Who wanted to try skiing at {p.name}?",
            answer=f"{c.name} wanted to try skiing at {p.name}, and {f.name} came along to share the fun.",
        ),
        QAItem(
            question=f"What did the children share?",
            answer=f"They shared {item.phrase}, which meant they had to take turns and be patient.",
        ),
        QAItem(
            question=f"What magical thing helped them get along?",
            answer=f"{charm.phrase} helped them stay calm, share more easily, and keep trying.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended with both children smiling, taking turns, and skiing together in a happy, ordinary afternoon.",
        ),
    ]


def world_qa(world: WorldState) -> list[QAItem]:
    return [
        QAItem(
            question="What does sharing mean?",
            answer="Sharing means letting other people use something too, so everyone gets a turn.",
        ),
        QAItem(
            question="What is magic in a story?",
            answer="Magic in a story is something wonderful or impossible that helps the characters in a special way.",
        ),
        QAItem(
            question="What are skis for?",
            answer="Skis help people slide over snow so they can move and play on a snowy hill.",
        ),
        QAItem(
            question="What does it mean to try again?",
            answer="Trying again means making another effort after a mistake or a wobble instead of giving up.",
        ),
    ]


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        w = sample.world
        print("\n--- world trace ---")
        print(f"place={w.place.id} child={w.child.name} friend={w.friend.name} item={w.item.label} charm={w.charm.label}")
        print(f"try_count={w.try_count} calm={w.calm} sharing={w.sharing} confidence={w.confidence} success={w.success}")
    if qa:
        print("\n== QA ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
        print()
        for item in sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")


def format_json(sample: StorySample) -> str:
    return sample.to_json()


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/5."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        stories = asp_valid_stories()
        print(f"{len(stories)} compatible stories")
        for s in stories[:50]:
            print(s)
        return

    if args.all:
        samples = []
        for p in [StoryParams(place=p, child=c1, friend=c2, item=i, charm=h)
                  for p in PLACES for c1 in CHILDREN for c2 in CHILDREN if c1 != c2
                  for i in ITEMS for h in CHARMS]:
            samples.append(generate(p))
    else:
        base_seed = args.seed if args.seed is not None else random.randrange(2**31)
        samples = []
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            rng = random.Random(base_seed + i)
            i += 1
            params = resolve_params(args, rng)
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if args.json:
        if len(samples) == 1:
            print(format_json(samples[0]))
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for idx, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.child} and {p.friend} at {p.place} with {p.item} and {p.charm}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
