#!/usr/bin/env python3
"""
A small nursery-rhyme story world about a market stall, a knickknack, a skillet,
and a brave kind choice made through dialogue.
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
class Item:
    id: str
    name: str
    kind: str
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    place: str
    entities: dict[str, Item] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    history: list[str] = field(default_factory=list)

    def add(self, item: Item) -> Item:
        self.entities[item.id] = item
        return item

    def get(self, eid: str) -> Item:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.history.append(text)

    def render(self) -> str:
        return " ".join(self.history)


@dataclass
class StoryParams:
    place: str
    child_name: str
    merchant_name: str
    seed: Optional[int] = None


PLACES = {
    "market": "the market",
    "fair": "the fair",
    "square": "the village square",
    "lane": "the sunny lane",
}

CHILD_NAMES = ["Mina", "Toby", "Nell", "Pip", "Sera", "Jory"]
MERCHANT_NAMES = ["Moss", "Mara", "Gus", "Dot", "Bram", "Wren"]


ASP_RULES = r"""
#show brave/1.
#show kind/1.
#show talks/2.
brave(X) :- child(X), has_challenge(X).
kind(X) :- child(X), offers_help(X).
talks(X,Y) :- child(X), speaks_to(X,Y).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for place in PLACES:
        lines.append(asp.fact("place", place))
    lines.append(asp.fact("item", "knickknack"))
    lines.append(asp.fact("item", "skillet"))
    lines.append(asp.fact("child", "child"))
    lines.append(asp.fact("merchant", "merchant"))
    lines.append(asp.fact("has_challenge", "child"))
    lines.append(asp.fact("offers_help", "child"))
    lines.append(asp.fact("speaks_to", "child", "merchant"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show brave/1.\n#show kind/1.\n#show talks/2."))
    brave = set(asp.atoms(model, "brave"))
    kind = set(asp.atoms(model, "kind"))
    talks = set(asp.atoms(model, "talks"))
    if brave == {("child",)} and kind == {("child",)} and talks == {("child", "merchant")}:
        print("OK: ASP twin matches the reasonableness gate.")
        return 0
    print("MISMATCH: ASP twin did not match expected facts.")
    print("brave:", brave)
    print("kind:", kind)
    print("talks:", talks)
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Nursery-rhyme story world: a child, a knicknack, and a skillet.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--name")
    ap.add_argument("--merchant")
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
    name = args.name or rng.choice(CHILD_NAMES)
    merchant = args.merchant or rng.choice(MERCHANT_NAMES)
    return StoryParams(place=place, child_name=name, merchant_name=merchant)


def _validate(params: StoryParams) -> None:
    if params.place not in PLACES:
        raise StoryError("The stall needs a real place to stand.")
    if not params.child_name or not params.merchant_name:
        raise StoryError("The story needs both a child and a stallkeeper.")


def generate(params: StoryParams) -> StorySample:
    _validate(params)
    world = World(place=PLACES[params.place])

    child = world.add(Item(id="child", name=params.child_name, kind="child"))
    merchant = world.add(Item(id="merchant", name=params.merchant_name, kind="merchant"))
    knicknack = world.add(Item(id="knicknack", name="a tiny knicknack", kind="object", owner=merchant.id))
    skillet = world.add(Item(id="skillet", name="a shiny skillet", kind="tool", owner=merchant.id))

    child.memes["wonder"] = 1.0
    child.memes["bravery"] = 1.0
    merchant.memes["kindness"] = 1.0

    story = []
    story.append(
        f"At {world.place}, little {child.name} toddled by a stall where {merchant.name} smiled so bright."
    )
    story.append(
        f"On a cloth lay a knicknack, small as a bean, and near it sat a skillet, round and white."
    )
    story.append(
        f'"What is that pretty thing?" said {child.name}. "A knicknack," said {merchant.name}, "for one who likes a trinket light."'
    )
    story.append(
        f'"And what is that?" asked {child.name} again. "{skillet.name}," said {merchant.name}, "for pancakes in the morn."'
    )

    child.memes["curiosity"] = 1.0
    merchant.memes["kindness"] = 2.0
    world.say(" ".join(story[:2]))
    world.say(story[2])
    world.say(story[3])

    world.facts.update(
        child=child, merchant=merchant, knicknack=knicknack, skillet=skillet,
        place=params.place, place_name=world.place
    )

    story.append(
        f"{child.name} had no coin at all, but did not frown or scorn. Instead {child.name} stood up straight and took a brave small breath."
    )
    child.memes["bravery"] = 2.0
    child.memes["kindness"] = 1.0
    merchant.memes["warmth"] = 1.0
    story.append(
        f'"If I sweep your stones and tidy your stall, may I peek once more?" {child.name} asked, soft as a song.'
    )
    story.append(
        f'{merchant.name} laughed, for kind words are golden. "Yes, brave little friend," said {merchant.name}, "and you may hold the knicknack, too."'
    )
    story.append(
        f"So {child.name} swept and shone the floor, then held the knicknack in both hands while the skillet gleamed like the moon."
    )
    story.append(
        f'And {merchant.name} gave a little nod. "{child.name}, you have a kind heart and a brave voice," said {merchant.name}, "and that is a finer treasure than any stall can show."'
    )
    story.append(
        f"So home went {child.name} with a happy hum, and the market breeze blew sweet and cool."
    )
    story.append(
        f"The tiny knicknack stayed at the stall, and the skillet stayed in its place, but {child.name} carried kindness and bravery all the way through."
    )

    full_story = " ".join(story)
    sample = StorySample(
        params=params,
        story=full_story,
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )
    return sample


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    merchant = f["merchant"]
    return [
        "Write a gentle nursery-rhyme story about a child at a stall with a knicknack and a skillet.",
        f"Tell a small rhyming tale where {child.name} speaks kindly to {merchant.name} at {world.place}.",
        "Write a child-facing story in a sing-song style that ends with bravery and kindness.",
    ]


def story_qa(world: World) -> list[QAItem]:
    child = world.facts["child"]
    merchant = world.facts["merchant"]
    return [
        QAItem(
            question="Who was the story about?",
            answer=f"The story was about little {child.name}, who visited {world.place} and met {merchant.name} at a stall.",
        ),
        QAItem(
            question="What two things were at the stall?",
            answer="A tiny knicknack and a shiny skillet were at the stall.",
        ),
        QAItem(
            question="How did the child get what was wanted?",
            answer=f"{child.name} spoke kindly, offered to help sweep the stall, and then was allowed to hold the knicknack.",
        ),
        QAItem(
            question="What changed by the end of the story?",
            answer=f"{child.name} ended the story feeling brave and kind, while the stall kept its knicknack and skillet safe and tidy.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a stall?",
            answer="A stall is a small place where someone sets out things to buy or look at, often at a market or fair.",
        ),
        QAItem(
            question="What is a knicknack?",
            answer="A knicknack is a tiny pretty object, often kept because it is charming or fun to look at.",
        ),
        QAItem(
            question="What is a skillet?",
            answer="A skillet is a pan used for cooking food, often on a stove or over heat.",
        ),
        QAItem(
            question="What does kindness mean?",
            answer="Kindness means choosing gentle, helpful words and actions that make another person feel cared for.",
        ),
        QAItem(
            question="What does bravery mean?",
            answer="Bravery means doing the right thing even when you feel shy, worried, or unsure.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(f"  {e.id}: name={e.name}, kind={e.kind}, owner={e.owner}, carried_by={e.carried_by}, meters={e.meters}, memes={e.memes}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for p in sample.prompts:
        out.append(p)
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


CURATED = [
    StoryParams(place="market", child_name="Mina", merchant_name="Moss"),
    StoryParams(place="fair", child_name="Toby", merchant_name="Mara"),
    StoryParams(place="square", child_name="Nell", merchant_name="Gus"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show brave/1.\n#show kind/1.\n#show talks/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show brave/1.\n#show kind/1.\n#show talks/2."))
        print("brave:", asp.atoms(model, "brave"))
        print("kind:", asp.atoms(model, "kind"))
        print("talks:", asp.atoms(model, "talks"))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for p in CURATED:
            samples.append(generate(p))
    else:
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
        header = f"### variant {i + 1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
