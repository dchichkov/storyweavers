#!/usr/bin/env python3
"""
A small Tall Tale storyworld about a vendor, a sixteenth-day fair, and a tiny
apostrophe that causes suspense until sharing reveals the moral value.
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


@dataclass
class StoryParams:
    place: str
    vendor_name: str
    item_name: str
    shared_item: str
    crowd_name: str
    seed: Optional[int] = None


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    phrase: str = ""
    meters: dict[str, float] = None
    memes: dict[str, float] = None

    def __post_init__(self):
        if self.meters is None:
            self.meters = {"weight": 0.0}
        if self.memes is None:
            self.memes = {"hope": 0.0, "worry": 0.0, "joy": 0.0, "trust": 0.0}


class World:
    def __init__(self, place: str):
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


SETTINGS = {
    "fair": "the sixteenth-day fair",
    "market": "the lantern market",
    "square": "the old town square",
}

VENDOR_NAMES = ["Aunt Bell", "Mister Moss", "Old Jory", "Mama June", "Uncle Pine"]
ITEMS = [
    ("apple pies", "apple pies"),
    ("blue ribbons", "blue ribbons"),
    ("honey cakes", "honey cakes"),
    ("orange kites", "orange kites"),
]
SHARED_ITEMS = {
    "apple pies": "one warm pie for the smallest child",
    "blue ribbons": "two bright ribbons for the girls at the gate",
    "honey cakes": "a plate of honey cakes for the hungry musicians",
    "orange kites": "three orange kites for the boys and girls who waited",
}
CROWD_NAMES = ["the children", "the farmers", "the fiddlers", "the neighbors", "the whole town"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall Tale storyworld: vendor, suspense, sharing, moral value.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--vendor-name", choices=VENDOR_NAMES)
    ap.add_argument("--item-name", choices=[i for i, _ in ITEMS])
    ap.add_argument("--shared-item", choices=list(SHARED_ITEMS))
    ap.add_argument("--crowd-name", choices=CROWD_NAMES)
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
    place = args.place or rng.choice(list(SETTINGS))
    vendor_name = args.vendor_name or rng.choice(VENDOR_NAMES)
    item_name = args.item_name or rng.choice([i for i, _ in ITEMS])
    shared_item = args.shared_item or item_name
    crowd_name = args.crowd_name or rng.choice(CROWD_NAMES)
    return StoryParams(place=place, vendor_name=vendor_name, item_name=item_name, shared_item=shared_item, crowd_name=crowd_name)


def tell(params: StoryParams) -> World:
    world = World(SETTINGS[params.place])
    vendor = world.add(Entity(id="vendor", kind="character", label=params.vendor_name, phrase=f"{params.vendor_name}, the vendor"))
    crowd = world.add(Entity(id="crowd", kind="character", label=params.crowd_name, phrase=params.crowd_name))
    sign = world.add(Entity(id="sign", label="a little sign", phrase="a little sign with an apostrophe"))
    item = world.add(Entity(id="item", label=params.item_name, phrase=params.item_name))
    gift = world.add(Entity(id="gift", label=params.shared_item, phrase=SHARED_ITEMS[params.shared_item]))

    vendor.memes["hope"] += 1
    world.say(f"At {world.place}, {vendor.label} was the kind of vendor who could sell moonshine to a shadow and laughter to a fence.")
    world.say(f"Near the {world.place}, {vendor.label} set up {sign.phrase} that read \"{vendor.label}'s {item.label}\".")
    world.say(f"The sixteenth bell had not yet rung, and that made the whole square feel as if it were holding its breath.")

    world.para()
    vendor.memes["worry"] += 1
    world.say(f"Then a breeze fluttered the apostrophe sign, and the crowd thought the stall said \"{vendor.label} {item.label}\" instead.")
    world.say(f"{crowd.label.capitalize()} began to whisper, because nobody knew if the vendor meant to keep the good thing hidden or to share it.")

    world.para()
    world.say(f"At last, {vendor.label} lifted the basket high and laughed like thunder rolling over cornfields.")
    world.say(f"\"A stall is only lucky,\" {vendor.label} said, \"when it gives its best taste to more than one hungry heart.\"")
    vendor.memes["joy"] += 1
    vendor.memes["trust"] += 1
    crowd.memes["joy"] += 1
    crowd.memes["trust"] += 1
    world.say(f"So {vendor.label} shared {gift.phrase}, and the children, the fiddlers, and the neighbors all got a piece.")
    world.say(f"By the time the sixteenth bell rang, the apostrophe was still there, but the fear was gone, and the town learned that sharing made the sweetest kind of value.")

    world.facts.update(
        vendor=vendor,
        crowd=crowd,
        sign=sign,
        item=item,
        gift=gift,
        place=params.place,
        params=params,
        suspense=True,
        sharing=True,
        moral_value=True,
    )
    return world


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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
    vendor = f["vendor"].label
    return [
        f"Write a tall tale about {vendor}, a vendor at {world.place}, where an apostrophe causes suspense before sharing brings a moral lesson.",
        f"Tell a child-friendly story with the words vendor, sixteenth, and apostrophe, ending with everyone sharing.",
        f"Create a brisk tall tale about a market sign, a worried crowd, and the value of sharing what you have.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    vendor = f["vendor"].label
    crowd = f["crowd"].label
    item = f["item"].label
    gift = f["gift"].label
    return [
        QAItem(
            question=f"Who was the vendor in the story?",
            answer=f"The vendor was {vendor}, who stood at {world.place} with a sign and a good heart.",
        ),
        QAItem(
            question=f"What caused the suspense before the sharing?",
            answer=f"The apostrophe on the sign caused suspense, because the crowd first wondered if {vendor} meant to keep {item} to themselves.",
        ),
        QAItem(
            question=f"What did the vendor share with {crowd}?",
            answer=f"{vendor} shared {gift}, and that is what turned the worry into joy.",
        ),
        QAItem(
            question="What moral value did the story show?",
            answer="The story showed that sharing makes value grow, because kindness can feed more people than holding everything back.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a vendor?",
            answer="A vendor is a person who sells things, often at a market, fair, or roadside stand.",
        ),
        QAItem(
            question="What is an apostrophe?",
            answer="An apostrophe is a small mark in writing that can show possession or a missing letter.",
        ),
        QAItem(
            question="What does sharing mean?",
            answer="Sharing means giving some of what you have so other people can enjoy it too.",
        ),
        QAItem(
            question="What is suspense?",
            answer="Suspense is the feeling of wondering what will happen next, especially when something important is not yet clear.",
        ),
    ]


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
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(f"  {e.id}: label={e.label!r} meters={e.meters} memes={e.memes}")
    return "\n".join(lines)


ASP_RULES = r"""
place(fair).
place(market).
place(square).

feature(suspense).
feature(sharing).
feature(moral_value).

has_seed_word(vendor).
has_seed_word(sixteenth).
has_seed_word(apostrophe).

compatible_story(P) :- place(P).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in SETTINGS:
        lines.append(asp.fact("place", p))
    for f in ["suspense", "sharing", "moral_value"]:
        lines.append(asp.fact("feature", f))
    for w in ["vendor", "sixteenth", "apostrophe"]:
        lines.append(asp.fact("has_seed_word", w))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show compatible_story/1."))
    atoms = set(asp.atoms(model, "compatible_story"))
    python_set = {(p,) for p in SETTINGS}
    if atoms == python_set:
        print(f"OK: clingo gate matches Python registry ({len(atoms)} places).")
        return 0
    print("MISMATCH between clingo and Python registry.")
    print("clingo:", sorted(atoms))
    print("python:", sorted(python_set))
    return 1


def asp_available() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show compatible_story/1."))
    return sorted(set(asp.atoms(model, "compatible_story")))


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams(place="fair", vendor_name="Aunt Bell", item_name="apple pies", shared_item="apple pies", crowd_name="the children"),
    StoryParams(place="market", vendor_name="Old Jory", item_name="honey cakes", shared_item="honey cakes", crowd_name="the fiddlers"),
    StoryParams(place="square", vendor_name="Mama June", item_name="blue ribbons", shared_item="blue ribbons", crowd_name="the neighbors"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show compatible_story/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_available())} compatible places:")
        for (p,) in asp_available():
            print(f"  {p}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
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
        if args.all:
            p = sample.params
            header = f"### {p.vendor_name} at {p.place} with {p.item_name}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
