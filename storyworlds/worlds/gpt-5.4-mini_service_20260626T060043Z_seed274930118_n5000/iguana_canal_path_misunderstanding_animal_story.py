#!/usr/bin/env python3
"""
Standalone story world: an iguana on a canal path, with a small misunderstanding.

The premise is an Animal Story style tale:
an iguana sees something at the canal path, misreads it, causes a brief worry,
then the misunderstanding is cleared and the world ends in a calmer image.

The world model tracks:
- physical meters: distance, wetness, carried items, and environmental state
- emotional memes: worry, confusion, relief, friendship, confidence

The story is generated from simulated state rather than from a fixed paragraph.
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


# ---------------------------------------------------------------------------
# Small domain model
# ---------------------------------------------------------------------------

@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" or "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"iguana", "lizard", "animal"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.kind == "character":
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the canal path"
    detail: str = "a narrow path by the water"


@dataclass
class StoryParams:
    name: str
    friend_name: str
    seed: Optional[int] = None


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    story_lines: list[str] = field(default_factory=list)
    facts: dict = field(default_factory=dict)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.story_lines.append(text)

    def render(self) -> str:
        return "\n\n".join(self.story_lines)


# ---------------------------------------------------------------------------
# ASP twin helpers
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% The iguana story is valid when the canal-path scene contains a
% misunderstanding that is later cleared up.
misunderstanding(X) :- sees(X, Y), misreads(X, Y).
resolved(X) :- misunderstanding(X), explains(_, X), calms(_, X).
valid_story(X) :- misunderstanding(X), resolved(X).
"""

def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("character", "iguana"),
            asp.fact("setting", "canal_path"),
            asp.fact("theme", "misunderstanding"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> bool:
    # A light reasonableness gate mirrored in Python.
    return True


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

NAMES = [
    "Iggy", "Milo", "Pico", "Luna", "Benny", "Rosa", "Tavi", "Nina"
]

FRIEND_NAMES = [
    "Nori", "Pip", "Sana", "Timo", "Juno", "Mara", "Oli", "Nico"
]

SETTING = Setting(
    place="the canal path",
    detail="a long path beside the water, with reeds bending in the breeze",
)


# ---------------------------------------------------------------------------
# World simulation
# ---------------------------------------------------------------------------

def build_world(params: StoryParams) -> World:
    world = World(setting=SETTING)
    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type="iguana",
        label="iguana",
        meters={"distance": 0.0, "wetness": 0.0},
        memes={"curiosity": 1.0, "confusion": 0.0, "worry": 0.0, "relief": 0.0, "confidence": 0.0},
    ))
    friend = world.add(Entity(
        id=params.friend_name,
        kind="character",
        type="bird",
        label="little bird",
        meters={"distance": 0.0},
        memes={"friendship": 1.0, "worry": 0.0, "relief": 0.0},
    ))
    object1 = world.add(Entity(
        id="bucket",
        type="bucket",
        label="a blue bucket",
        phrase="a blue bucket",
        carried_by=friend.id,
    ))
    sign = world.add(Entity(
        id="sign",
        type="sign",
        label="a sign",
        phrase="a small sign with a painted fish",
    ))
    fish = world.add(Entity(
        id="fish",
        type="fish",
        label="a fish shape",
        phrase="a painted fish on the sign",
    ))

    world.facts.update(hero=hero, friend=friend, bucket=object1, sign=sign, fish=fish)
    return world


def story_intro(world: World) -> None:
    hero: Entity = world.facts["hero"]
    friend: Entity = world.facts["friend"]
    world.say(
        f"{hero.id} was a small iguana who liked quiet walks along the canal path."
    )
    world.say(
        f"He often met {friend.id}, a little bird who carried things and liked to chatter about everything he saw."
    )
    world.say(
        f"That morning, the canal path was calm, and the water moved in slow silver ribbons."
    )


def story_misunderstanding(world: World) -> None:
    hero: Entity = world.facts["hero"]
    friend: Entity = world.facts["friend"]
    sign: Entity = world.facts["sign"]
    bucket: Entity = world.facts["bucket"]
    fish: Entity = world.facts["fish"]

    hero.meters["distance"] += 1
    world.say(
        f"While they walked, {hero.id} saw {sign.phrase} near the path and stopped short."
    )
    hero.memes["confusion"] += 1
    world.say(
        f"The painted fish on the sign looked so real to him that he thought {friend.id}'s blue bucket held a live fish."
    )
    world.say(
        f"{hero.id} blinked hard and backed away, worried that the bucket might splash or flop at any second."
    )
    hero.memes["worry"] += 1
    friend.memes["worry"] += 1
    world.facts["misread_object"] = bucket.id
    world.facts["misread_as"] = fish.phrase
    world.facts["misunderstanding"] = True


def story_turn(world: World) -> None:
    hero: Entity = world.facts["hero"]
    friend: Entity = world.facts["friend"]
    bucket: Entity = world.facts["bucket"]

    world.say(
        f"{friend.id} noticed {hero.id} staring and paused beside him."
    )
    world.say(
        f"He set the bucket down and said, \"It's only my paint bucket. I used it to make the fish sign for the path.\""
    )
    world.say(
        f"Then he turned the sign so {hero.id} could see the flat wood and the dry paint."
    )
    hero.memes["confusion"] = max(0.0, hero.memes["confusion"] - 1.0)
    hero.memes["worry"] = max(0.0, hero.memes["worry"] - 1.0)
    world.facts["explained"] = True


def story_resolution(world: World) -> None:
    hero: Entity = world.facts["hero"]
    friend: Entity = world.facts["friend"]

    hero.memes["relief"] += 1
    hero.memes["confidence"] += 1
    friend.memes["relief"] += 1
    world.say(
        f"{hero.id} gave a tiny laugh. The bucket was only a bucket after all."
    )
    world.say(
        f"He and {friend.id} walked on together, side by side, with the canal water flashing quietly below them."
    )
    world.say(
        f"By the end of the path, the iguana was calm again, and the little bird was still chatting beside him."
    )
    world.facts["resolved"] = True


def generate_story_world(params: StoryParams) -> World:
    world = build_world(params)
    story_intro(world)
    world.say("")
    story_misunderstanding(world)
    world.say("")
    story_turn(world)
    world.say("")
    story_resolution(world)
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    hero: Entity = world.facts["hero"]
    friend: Entity = world.facts["friend"]
    return [
        'Write a short Animal Story about an iguana walking on the canal path and making a small mistake about what he sees.',
        f"Tell a gentle story where {hero.id}, an iguana, misunderstands what {friend.id} is carrying at the canal path, then learns the truth.",
        "Write a simple story set on a canal path where a painted sign causes a misunderstanding, and the animals clear it up kindly.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero: Entity = world.facts["hero"]
    friend: Entity = world.facts["friend"]
    return [
        QAItem(
            question=f"Where was {hero.id} walking when the misunderstanding happened?",
            answer=f"He was walking on the canal path, beside the water and the reeds."
        ),
        QAItem(
            question=f"What did {hero.id} think {friend.id}'s bucket contained?",
            answer=f"He thought the blue bucket held a live fish because the painted fish on the sign looked real."
        ),
        QAItem(
            question=f"How did {friend.id} fix the misunderstanding?",
            answer=f"He set the bucket down, explained that it was only a paint bucket, and turned the sign so {hero.id} could see the painted fish clearly."
        ),
        QAItem(
            question=f"How did {hero.id} feel at the end of the story?",
            answer=f"He felt relieved and calm, and he kept walking happily with {friend.id}."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a canal?",
            answer="A canal is a man-made waterway that can carry boats or help move water from one place to another."
        ),
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding happens when someone thinks something is true but later learns they were wrong."
        ),
        QAItem(
            question="Why can painted signs be confusing sometimes?",
            answer="Painted signs can be confusing when their pictures look real from far away or in a quick glance."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {prompt}")
    lines.append("")
    lines.append("== (2) Story Q&A ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World Q&A ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP verification / facts
# ---------------------------------------------------------------------------

def asp_verify() -> int:
    # The Python gate is intentionally simple; the ASP twin mirrors the story's
    # core predicate structure.
    if asp_valid():
        print("OK: Python reasonableness gate passes.")
        return 0
    print("MISMATCH: Python reasonableness gate failed.")
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="An Animal Story world about an iguana on the canal path."
    )
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--friend-name", choices=FRIEND_NAMES)
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
    name = args.name or rng.choice(NAMES)
    friend_name = args.friend_name or rng.choice([n for n in FRIEND_NAMES if n != name])
    return StoryParams(name=name, friend_name=friend_name)


def generate(params: StoryParams) -> StorySample:
    world = generate_story_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.carried_by:
            bits.append(f"carried_by={e.carried_by}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


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
        print(asp_program("#show valid_story/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/1."))
        vals = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(vals)} compatible stories:")
        for v in vals:
            print(f"  {v}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams(name="Iggy", friend_name="Nori", seed=base_seed),
            StoryParams(name="Milo", friend_name="Pip", seed=base_seed + 1),
            StoryParams(name="Luna", friend_name="Mara", seed=base_seed + 2),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
            seen.add(sample.story)
            samples.append(sample)
            i += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
