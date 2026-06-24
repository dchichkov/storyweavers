#!/usr/bin/env python3
"""
Aisle Passey Quest: a tiny nursery-rhyme storyworld about a little quest,
a misunderstanding, and a softly foreshadowed ending.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field, asdict
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


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
        if self.type in {"girl", "child", "mouse", "rabbit"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class World:
    setting: str
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

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


@dataclass
class StoryParams:
    seed: Optional[int] = None
    place: str = "shop"
    hero: str = "Passey"
    hero_type: str = "child"
    helper: str = "Milo"
    helper_type: str = "mouse"
    prize: str = "blue ribbon"
    quest: str = "find the little bell"
    misunderstanding: str = "the ribbon is lost in the aisle"
    foreshadowing: str = "crumbs by the shelf"
    setting: str = "the shop aisle"


SETTINGS = {
    "shop": "the shop aisle",
    "bakery": "the bakery aisle",
    "market": "the market aisle",
}

QUESTS = {
    "bell": "find the little bell",
    "basket": "carry the basket home",
    "cookie": "bring the cookie tin to the counter",
}

PRIZES = {
    "ribbon": "blue ribbon",
    "crumb": "crumb cake",
    "toy": "tiny toy boat",
}

FORESHADOWS = [
    "crumbs by the shelf",
    "a bell-shaped shadow under the cart",
    "a ribbon peeked from behind a sack",
    "tiny footprints near the flour bin",
]


@dataclass
class StoryState:
    quest_started: bool = False
    misunderstanding: bool = False
    clue_seen: bool = False
    resolved: bool = False


ASP_RULES = r"""
quest_started :- begin.
misunderstanding :- begin, not clue_seen.
clue_seen :- foreshadowing.
resolved :- quest_started, clue_seen, misunderstanding.
#show quest_started/0.
#show misunderstanding/0.
#show clue_seen/0.
#show resolved/0.
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("begin"),
            asp.fact("foreshadowing"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show quest_started/0.#show misunderstanding/0.#show clue_seen/0.#show resolved/0."))
    shown = {sym.name for sym in model}
    expected = {"quest_started", "misunderstanding", "clue_seen", "resolved"}
    if shown == expected:
        print("OK: ASP gate matches the intended foreshadowed quest shape.")
        return 0
    print(f"MISMATCH: {sorted(shown)} != {sorted(expected)}")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A nursery-rhyme storyworld about an aisle quest and a misunderstanding.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--foreshadow", choices=list(range(1, 5)))
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
    place = args.place or rng.choice(list(SETTINGS))
    quest_key = args.quest or rng.choice(list(QUESTS))
    prize_key = args.prize or rng.choice(list(PRIZES))
    foresh = FORESHADOWS[(args.foreshadow - 1) % len(FORESHADOWS)] if args.foreshadow else rng.choice(FORESHADOWS)
    return StoryParams(
        place=place,
        hero="Passey",
        hero_type="child",
        helper=rng.choice(["Milo", "Nina", "Wren"]),
        helper_type=rng.choice(["mouse", "rabbit"]),
        prize=PRIZES[prize_key],
        quest=QUESTS[quest_key],
        misunderstanding=f"the {PRIZES[prize_key]} is lost in the aisle",
        foreshadowing=foresh,
        setting=SETTINGS[place],
    )


def generate(params: StoryParams) -> StorySample:
    world = World(setting=params.setting)
    state = StoryState()

    hero = world.add(Entity(id="Passey", kind="character", type=params.hero_type, label="Passey", location=params.setting))
    helper = world.add(Entity(id="Helper", kind="character", type=params.helper_type, label=params.helper, location=params.setting))
    prize = world.add(Entity(id="Prize", kind="thing", type="thing", label=params.prize, phrase=params.prize, owner=helper.id, location=params.setting))

    state.quest_started = True
    hero.memes["hope"] = 1
    world.say(
        f"Passey skipped along the {params.setting}, as cheerful as a song, "
        f"and whispered a little Quest: {params.quest}."
    )
    world.say(
        f"But there was a Misunderstanding too; Passey thought {params.misunderstanding}, "
        f"and {helper.label} only blinked and looked on."
    )

    world.para()
    helper.meters["attention"] = 1
    hero.memes["worry"] = 1
    world.say(
        f"Along the shelf there shone {params.foreshadowing}, soft as snow in spring, "
        f"and that was the first Foreshadowing of the thing."
    )
    state.clue_seen = True

    if "crumb" in params.foreshadowing or "bell" in params.foreshadowing or "ribbon" in params.foreshadowing:
        world.say(
            f"Passey peeped and paused, then followed the little sign; "
            f"the clue was not a trap at all, but a path that felt just fine."
        )

    world.para()
    state.misunderstanding = True
    world.say(
        f"So Passey and {helper.label} searched the aisle with care, "
        f"until the helper laughed and pointed: the {prize.label} was there."
    )
    world.say(
        f"The quest was not for a lost thing after all; it was to carry a treasure home, "
        f"and Passey held the prize with both hands while walking toward the dome of light."
    )
    state.resolved = True
    hero.memes["joy"] = 2
    hero.memes["worry"] = 0
    helper.memes["warmth"] = 1

    world.facts.update(
        hero=hero,
        helper=helper,
        prize=prize,
        params=params,
        state=state,
    )

    prompts = [
        f"Write a short nursery-rhyme story about Passey in the {params.setting} with a Quest and a gentle misunderstanding.",
        f"Tell a child-friendly tale where {params.hero} follows a Foreshadowing clue and learns the truth in an aisle.",
        f"Write a tiny rhyme where a helper and Passey search for {params.prize} and the ending feels warm and clear.",
    ]

    story_qa = [
        QAItem(
            question="What did Passey think was wrong at the start?",
            answer=f"Passey thought {params.misunderstanding}.",
        ),
        QAItem(
            question="What clue helped Passey notice the truth?",
            answer=f"{params.foreshadowing} helped Passey see where to look next.",
        ),
        QAItem(
            question="What was Passey's Quest in the story?",
            answer=f"Passey's Quest was to {params.quest}.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended with Passey and {helper.label} finding the {prize.label} and walking home happily.",
        ),
    ]

    world_qa = [
        QAItem(
            question="What is an aisle?",
            answer="An aisle is a long path between shelves or rows where people walk and look at things.",
        ),
        QAItem(
            question="What is a foreshadowing clue?",
            answer="A foreshadowing clue is a small hint that helps you guess what may happen later.",
        ),
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding happens when someone thinks one thing is true, but the real truth is different.",
        ),
    ]

    return StorySample(params=params, story=world.render(), prompts=prompts, story_qa=story_qa, world_qa=world_qa, world=world)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print("--- trace ---")
        for e in sample.world.entities.values():
            print(f"{e.id}: kind={e.kind} type={e.type} meters={e.meters} memes={e.memes}")
    if qa:
        print()
        for title, items in (
            ("Generation prompts", sample.prompts),
            ("Story Q&A", sample.story_qa),
            ("World Q&A", sample.world_qa),
        ):
            print(f"== {title} ==")
            if isinstance(items, list) and items and isinstance(items[0], QAItem):
                for item in items:
                    print(f"Q: {item.question}")
                    print(f"A: {item.answer}")
            else:
                for i, p in enumerate(items, 1):
                    print(f"{i}. {p}")
            print()


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show resolved/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("This world uses a tiny ASP twin; run --show-asp to inspect it.")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for place in SETTINGS:
            params = StoryParams(
                seed=base_seed,
                place=place,
                hero="Passey",
                hero_type="child",
                helper="Milo",
                helper_type="mouse",
                prize=PRIZES["ribbon"],
                quest=QUESTS["bell"],
                misunderstanding=f"the {PRIZES['ribbon']} is lost in the aisle",
                foreshadowing=FORESHADOWS[0],
                setting=SETTINGS[place],
            )
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        for i in range(max(1, args.n)):
            params = resolve_params(args, random.Random(base_seed + i))
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
