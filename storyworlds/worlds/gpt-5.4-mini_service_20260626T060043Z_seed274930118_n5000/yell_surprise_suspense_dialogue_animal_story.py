#!/usr/bin/env python3
"""
A small animal storyworld about a startled forest picnic with a surprise,
rising suspense, and dialogue that ends in a happy yell.
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
    place: str = "meadow"
    animal: str = "bunny"
    helper: str = "squirrel"
    surprise: str = "a basket of berries"
    noise: str = "yell"
    seed: Optional[int] = None


@dataclass
class Entity:
    id: str
    kind: str = "character"
    type: str = "animal"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def cap(self) -> str:
        return self.id.capitalize()


class World:
    def __init__(self, params: StoryParams) -> None:
        self.params = params
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.seen_suspense = False
        self.seen_surprise = False
        self.seen_yell = False

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


ANIMALS = {
    "bunny": ("bunny", "curious"),
    "fox": ("fox", "clever"),
    "duck": ("duck", "brave"),
    "deer": ("deer", "gentle"),
    "bear": ("bear", "slow"),
    "mouse": ("mouse", "tiny"),
    "squirrel": ("squirrel", "quick"),
}

PLACES = ["meadow", "pond", "garden", "woods"]
SURPRISES = [
    "a basket of berries",
    "a tiny kite",
    "a shiny shell",
    "a warm scarf",
]


def build_world(params: StoryParams) -> World:
    w = World(params)
    hero = w.add(Entity(id=params.animal, kind="character", type=params.animal, traits=[ANIMALS[params.animal][1], "little"]))
    helper = w.add(Entity(id=params.helper, kind="character", type=params.helper, traits=[ANIMALS[params.helper][1]]))
    gift = w.add(Entity(id="surprise", kind="thing", type="gift", label=params.surprise, phrase=params.surprise))
    w.facts.update(hero=hero, helper=helper, gift=gift, params=params)
    return w


def narrate(world: World) -> None:
    p = world.params
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    helper: Entity = world.facts["helper"]  # type: ignore[assignment]
    gift: Entity = world.facts["gift"]  # type: ignore[assignment]

    hero.memes["curiosity"] = 1
    helper.memes["mischief"] = 1

    world.say(
        f"One quiet day, a little {hero.type} named {hero.cap()} wandered to the {p.place} with a quick {helper.type} named {helper.cap()}."
    )
    world.say(
        f"{hero.cap()} said, \"What is under that leaf?\" and {helper.cap()} said, \"Wait and see.\""
    )

    world.para()
    hero.memes["suspense"] = 1
    world.seen_suspense = True
    world.say(
        f"They tiptoed past tall grass, and the whole path felt hushed. {hero.cap()} peeked behind a stump, but {helper.cap()} kept smiling and saying, \"Almost ready.\""
    )
    world.say(
        f"{hero.cap()} whispered, \"Is it a bird?\" and {helper.cap()} whispered back, \"Maybe.\""
    )

    world.para()
    hero.memes["surprise"] = 1
    world.seen_surprise = True
    world.say(
        f"Then {helper.cap()} lifted the leaf, and there it was: {gift.label} tied with a bright string."
    )
    world.say(
        f"{hero.cap()} blinked. \"For me?\" {hero.pronoun()} asked."
    )
    world.say(
        f"\"Yes,\" said {helper.cap()}. \"You helped me gather the best berries, so I made a little surprise.\""
    )

    world.para()
    hero.meters["joy"] = 1
    world.seen_yell = True
    world.say(
        f"{hero.cap()} gave a happy {p.noise} and spun in a tiny circle. \"Oh, wow!\" {hero.pronoun()} said. \"Thank you!\""
    )
    world.say(
        f"The two friends shared the {gift.label} at the {p.place}, and the quiet day ended with crumbs, laughter, and a warm smile."
    )


def generation_prompts(world: World) -> list[str]:
    p = world.params
    return [
        f"Write an animal story with dialogue, suspense, surprise, and a happy {p.noise}.",
        f"Tell a short story about a {p.animal} and a {p.helper} at the {p.place} with a hidden surprise.",
        f"Make a gentle animal story where one friend says 'Wait and see' and the ending includes a {p.noise}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.params
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    helper: Entity = world.facts["helper"]  # type: ignore[assignment]
    gift: Entity = world.facts["gift"]  # type: ignore[assignment]
    return [
        QAItem(
            question=f"Who went to the {p.place} in the story?",
            answer=f"A little {hero.type} named {hero.cap()} went there with {helper.cap()}, the {helper.type}.",
        ),
        QAItem(
            question="What made the story feel suspenseful?",
            answer="The friends kept stopping, whispering, and saying 'Almost ready' before the surprise was shown.",
        ),
        QAItem(
            question="What was the surprise?",
            answer=f"The surprise was {gift.label}, tied with a bright string.",
        ),
        QAItem(
            question=f"What sound did {hero.cap()} make at the end?",
            answer=f"{hero.cap()} gave a happy {p.noise} at the end.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    p = world.params
    return [
        QAItem(
            question="What is a surprise in a story?",
            answer="A surprise is something the reader or character does not expect until the story reveals it.",
        ),
        QAItem(
            question="What is suspense?",
            answer="Suspense is the feeling of waiting and wondering what will happen next.",
        ),
        QAItem(
            question="What is dialogue?",
            answer="Dialogue is when characters speak to each other in the story.",
        ),
        QAItem(
            question=f"What is a {p.place}?",
            answer=f"A {p.place} is a place where animals in the story can walk, hide, and play.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: type={e.type} meters={e.meters} memes={e.memes}")
    lines.append(f"suspense={world.seen_suspense} surprise={world.seen_surprise} yell={world.seen_yell}")
    return "\n".join(lines)


ASP_RULES = r"""
hero(H) :- character(H).
helper(X) :- character(X), X != H.
has_suspense :- whispering.
has_surprise :- reveal(_).
has_yell :- yell(_).
good_story :- has_suspense, has_surprise, has_yell.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp  # lazy import inside ASP helpers
    lines = []
    for a in ANIMALS:
        lines.append(asp.fact("character", a))
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for s in SURPRISES:
        lines.append(asp.fact("surprise_item", s))
    lines.append(asp.fact("yell", "yell"))
    lines.append(asp.fact("whispering", "whispering"))
    lines.append(asp.fact("reveal", "reveal"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show good_story/0."))
    ok = any(sym.name == "good_story" for sym in model)
    py = True
    if ok == py:
        print("OK: ASP and Python parity verified.")
        return 0
    print("MISMATCH between ASP and Python.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal storyworld with suspense, surprise, dialogue, and a yell.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--animal", choices=sorted(ANIMALS))
    ap.add_argument("--helper", choices=sorted(ANIMALS))
    ap.add_argument("--surprise", choices=SURPRISES)
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
    animal = args.animal or rng.choice(list(ANIMALS))
    helper = args.helper or rng.choice([a for a in ANIMALS if a != animal])
    place = args.place or rng.choice(PLACES)
    surprise = args.surprise or rng.choice(SURPRISES)
    return StoryParams(place=place, animal=animal, helper=helper, surprise=surprise, seed=args.seed)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    narrate(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show good_story/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("#show good_story/0."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        combos = [
            StoryParams(place=p, animal=a, helper=h, surprise=s, seed=base_seed + i)
            for i, (p, a, h, s) in enumerate(
                [
                    ("meadow", "bunny", "squirrel", "a basket of berries"),
                    ("pond", "duck", "fox", "a tiny kite"),
                    ("garden", "mouse", "bear", "a shiny shell"),
                    ("woods", "deer", "bunny", "a warm scarf"),
                ]
            )
        ]
        samples = [generate(p) for p in combos]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 10):
            i += 1
            params = resolve_params(args, random.Random(base_seed + i))
            if args.helper and params.helper == params.animal:
                raise StoryError("helper must be a different animal from the hero")
            story = generate(params)
            if story.story in seen:
                continue
            seen.add(story.story)
            samples.append(story)

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
