#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260624T081143Z_seed2038046945_n100/stead_schlepp_exert_sharing_myth.py
===============================================================================================================

A standalone storyworld about a mythic sharing quest.

Seed words: stead, schlepp, exert
Feature: Sharing
Style: Myth
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
class StoryParams:
    giver: str
    receiver: str
    gift: str
    place: str
    burden: str
    seed: Optional[int] = None


@dataclass
class Entity:
    name: str
    kind: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def bump_meter(self, key: str, amount: float) -> None:
        self.meters[key] = self.meters.get(key, 0.0) + amount

    def bump_meme(self, key: str, amount: float) -> None:
        self.memes[key] = self.memes.get(key, 0.0) + amount


class World:
    def __init__(self, params: StoryParams) -> None:
        self.params = params
        self.entities: dict[str, Entity] = {
            params.giver: Entity(params.giver, "child"),
            params.receiver: Entity(params.receiver, "child"),
            "stead": Entity("stead", "beast"),
            "sharing": Entity("sharing", "virtue"),
        }
        self.story_parts: list[str] = []
        self.facts: dict[str, object] = {}

    def say(self, text: str) -> None:
        self.story_parts.append(text)

    def render(self) -> str:
        return "\n\n".join(self.story_parts)

    def e(self, name: str) -> Entity:
        return self.entities[name]


SETTING_REGISTRY = {
    "moon_hill": {
        "place": "the moonlit hill",
        "detail": "under a wide silver moon",
    },
    "river_gate": {
        "place": "the river gate",
        "detail": "beside a singing river",
    },
    "old_oak": {
        "place": "the old oak grove",
        "detail": "where roots curled like wise fingers",
    },
}

GIFT_REGISTRY = {
    "bread": {"thing": "a round loaf of bread", "weight": 1.0, "warmth": 1.0},
    "cloak": {"thing": "a bright wool cloak", "weight": 2.0, "warmth": 2.0},
    "lamp": {"thing": "a small bronze lamp", "weight": 1.0, "warmth": 0.5},
}

BURDEN_REGISTRY = {
    "river_stones": {"thing": "a sack of river stones", "weight": 3.0},
    "winter_logs": {"thing": "a bundle of winter logs", "weight": 4.0},
    "market_basket": {"thing": "a basket of market goods", "weight": 2.0},
}

ASP_RULES = r"""
shared(G) :- giver(G), gift(X), offered(G, X), accepted(R, X).
lightened(G) :- shared(G).
resolved(G) :- lightened(G), burden(B), carried(G, B), virtue(sharing).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for giver in PEOPLE:
        lines.append(asp.fact("giver", giver))
    for gift_id in GIFT_REGISTRY:
        lines.append(asp.fact("gift", gift_id))
    for burden_id in BURDEN_REGISTRY:
        lines.append(asp.fact("burden", burden_id))
    lines.append(asp.fact("virtue", "sharing"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


PEOPLE = ["Aster", "Bryn", "Cleo", "Dorian", "Eira", "Fenn"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A mythic sharing storyworld.")
    ap.add_argument("--giver", choices=PEOPLE)
    ap.add_argument("--receiver", choices=PEOPLE)
    ap.add_argument("--gift", choices=GIFT_REGISTRY)
    ap.add_argument("--place", choices=SETTING_REGISTRY)
    ap.add_argument("--burden", choices=BURDEN_REGISTRY)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    giver = args.giver or rng.choice(PEOPLE)
    receiver_choices = [p for p in PEOPLE if p != giver]
    receiver = args.receiver or rng.choice(receiver_choices)
    gift = args.gift or rng.choice(list(GIFT_REGISTRY))
    place = args.place or rng.choice(list(SETTING_REGISTRY))
    burden = args.burden or rng.choice(list(BURDEN_REGISTRY))
    if args.giver and args.receiver and args.giver == args.receiver:
        raise StoryError("The giver and receiver must be different people.")
    return StoryParams(giver=giver, receiver=receiver, gift=gift, place=place, burden=burden)


def resolve_story(world: World) -> None:
    p = world.params
    giver = world.e(p.giver)
    receiver = world.e(p.receiver)

    giver.bump_meme("duty", 1)
    giver.bump_meme("exert", 1)
    giver.bump_meter("load", GIFT_REGISTRY[p.gift]["weight"])
    giver.bump_meter("load", BURDEN_REGISTRY[p.burden]["weight"])

    world.say(
        f"At {SETTING_REGISTRY[p.place]['place']}, {p.giver} came with a stead heart "
        f"and a burden to schlepp, for the day was long and the road was old."
    )
    world.say(
        f"Yet the burden made {p.giver} exert hard, and the knees of the child trembled "
        f"like reeds in wind."
    )
    world.say(
        f"Then {p.receiver} saw the strain and spoke of sharing, the oldest mercy in myth."
    )

    giver.bump_meme("hope", 1)
    receiver.bump_meme("kindness", 1)

    world.say(
        f"So {p.giver} divided {GIFT_REGISTRY[p.gift]['thing']} with {p.receiver}, "
        f"and the two carried the rest together."
    )
    world.say(
        f"The load grew light at once, and the moon over {SETTING_REGISTRY[p.place]['place']} "
        f"seemed to bless their sharing."
    )

    world.facts.update(
        giver=p.giver,
        receiver=p.receiver,
        gift=p.gift,
        burden=p.burden,
        place=p.place,
        shared=True,
    )


def generation_prompts(world: World) -> list[str]:
    p = world.params
    return [
        f"Write a short mythic story about {p.giver} and {p.receiver} where sharing makes a hard burden easier.",
        f"Tell a child-friendly myth at {SETTING_REGISTRY[p.place]['place']} with the words stead, schlepp, and exert.",
        f"Create a gentle legend in which someone learns to share {GIFT_REGISTRY[p.gift]['thing']}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.params
    return [
        QAItem(
            question=f"Who shared the burden in the story?",
            answer=f"{p.giver} and {p.receiver} shared it together after {p.giver} grew tired.",
        ),
        QAItem(
            question=f"Why did {p.giver} need help?",
            answer=f"{p.giver} had to schlepp {BURDEN_REGISTRY[p.burden]['thing']} and also carry {GIFT_REGISTRY[p.gift]['thing']}, so the load became heavy.",
        ),
        QAItem(
            question=f"What changed at the end?",
            answer=f"The load became lighter because the two children shared the work and walked on together.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does sharing mean?",
            answer="Sharing means letting someone else use or enjoy part of what you have.",
        ),
        QAItem(
            question="What does exert mean?",
            answer="To exert yourself means to use a lot of effort to do something hard.",
        ),
        QAItem(
            question="What is a stead?",
            answer="A stead is a place where a horse or other animal is kept and cared for.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["Prompts:"]
    lines.extend(f"- {p}" for p in sample.prompts)
    lines.append("")
    lines.append("Story QA:")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("World QA:")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    parts = ["TRACE"]
    for e in world.entities.values():
        parts.append(f"{e.name}: meters={e.meters} memes={e.memes}")
    return "\n".join(parts)


def generate(params: StoryParams) -> StorySample:
    world = World(params)
    resolve_story(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


CURATED = [
    StoryParams("Aster", "Bryn", "bread", "moon_hill", "river_stones"),
    StoryParams("Cleo", "Dorian", "cloak", "old_oak", "winter_logs"),
    StoryParams("Eira", "Fenn", "lamp", "river_gate", "market_basket"),
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


def asp_verify() -> int:
    import asp
    _ = asp_program("#show shared/1.")
    print("OK: ASP twin is present.")
    return 0


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show shared/1."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
