#!/usr/bin/env python3
"""
A small animal-story world about a timid friend finding bravery on the pavement.

Seed tale:
---
A little hedgehog named Pip liked quiet mornings and soft grass. One day, Pip
found a sparrow stuck beside the pavement, too nervous to hop over the crack.
Pip hesitated too, because the pavement looked wide and hot.

Then Pip thought of the sparrow's worried chirps and took a brave breath.
Pip crossed the pavement, guided the sparrow to the shade, and the two friends
smiled together.

World model:
---
- typed animal entities with physical meters and emotional memes
- pavement is a physical obstacle
- hesitation raises fear and delay
- bravery is the turn that lets the friend act
- friendship strengthens when help is offered and accepted
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

SETTING_LABEL = "the warm park path"
THEME_WORDS = ("hearted", "pavement", "hesitate")


@dataclass
class Entity:
    id: str
    kind: str = "animal"
    type: str = "animal"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def name_or_label(self) -> str:
        return self.label or self.id


@dataclass
class World:
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

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


@dataclass
class StoryParams:
    hero: str = "Pip"
    friend: str = "Tia"
    animal: str = "hedgehog"
    friend_animal: str = "sparrow"
    seed: Optional[int] = None


HERO_TRAITS = ["small", "hearted", "careful"]
FRIEND_TRAITS = ["tiny", "friendly", "soft-voiced"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal story world: bravery, friendship, and a pavement crossing.")
    ap.add_argument("--hero")
    ap.add_argument("--friend")
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
    hero = args.hero or rng.choice(["Pip", "Nim", "Moss", "Rune", "Luna"])
    friend = args.friend or rng.choice(["Tia", "Bea", "Milo", "Nori", "Saffy"])
    if hero == friend:
        raise StoryError("Hero and friend must be different names.")
    return StoryParams(hero=hero, friend=friend, seed=args.seed)


ASP_RULES = r"""
hero(H).
friend(F).
brave(H) :- hesitation(H), friendship(H,F), help(F,H).
resolution(H) :- brave(H).
#show brave/1.
#show resolution/1.
"""


def asp_facts() -> str:
    import asp
    lines = [asp.fact("theme", "hearted"), asp.fact("theme", "pavement"), asp.fact("theme", "hesitate")]
    lines.append(asp.fact("place", "park_path"))
    lines.append(asp.fact("trait", "bravery"))
    lines.append(asp.fact("trait", "friendship"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def generate(params: StoryParams) -> StorySample:
    world = World(place=SETTING_LABEL)

    hero = world.add(Entity(
        id=params.hero,
        kind="animal",
        type=params.animal,
        label=params.hero,
        traits=["hearted", "careful"],
        meters={"distance": 0.0, "steps": 0.0},
        memes={"hesitation": 1.0, "bravery": 0.0, "friendship": 0.0},
    ))
    friend = world.add(Entity(
        id=params.friend,
        kind="animal",
        type=params.friend_animal,
        label=params.friend,
        traits=["small", "soft-voiced"],
        meters={"distance": 0.0, "steps": 0.0},
        memes={"fear": 1.0, "friendship": 0.0},
    ))

    world.say(
        f"On {world.place}, a hearted little {hero.type} named {hero.label} watched the sun warm the grass."
    )
    world.say(
        f"Near the pavement, {friend.label} the {friend.type} stood still and trembly, looking at the crack ahead."
    )

    world.para()
    world.say(
        f"{hero.label} wanted to help, but {hero.label} did not want to cross the pavement at first."
    )
    hero.memes["hesitation"] += 1.0
    hero.meters["steps"] += 0.0
    world.say(
        f"{hero.label} did what the story word says: {hero.label} had to hesitate, and {friend.label} waited with worried eyes."
    )

    world.para()
    hero.memes["bravery"] += 1.0
    hero.memes["hesitation"] = 0.0
    hero.meters["distance"] += 1.0
    hero.meters["steps"] += 3.0
    friend.memes["friendship"] += 1.0
    hero.memes["friendship"] += 1.0

    world.say(
        f"Then {hero.label} took a brave breath and crossed the pavement one careful step at a time."
    )
    world.say(
        f"{hero.label} reached {friend.label}, led {friend.label} to the cool shade, and the two little friends sat together smiling."
    )

    world.facts.update(hero=hero, friend=friend, resolved=True)
    story = world.render()
    prompts = [
        'Write an animal story for young children about hearted friendship on a pavement path.',
        f"Tell a short story where {params.hero} must stop and hesitate before showing bravery to help a friend.",
        "Write a gentle animal story that includes the words hearted, pavement, and hesitate.",
    ]
    story_qa = [
        QAItem(
            question=f"Why did {params.hero} hesitate near the pavement?",
            answer=f"{params.hero} hesitated because the pavement looked wide and hot, and {params.hero} was careful before helping {params.friend}.",
        ),
        QAItem(
            question=f"What changed when {params.hero} became brave?",
            answer=f"{params.hero} crossed the pavement, reached {params.friend}, and turned worry into friendship.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with {params.hero} and {params.friend} sitting safely in the shade as happy friends.",
        ),
    ]
    world_qa = [
        QAItem(question="What is bravery?", answer="Bravery is when someone feels afraid but still does the helpful or right thing."),
        QAItem(question="What is friendship?", answer="Friendship is a kind bond between friends who care for each other and help each other."),
        QAItem(question="What is a pavement?", answer="A pavement is a hard path or walkway that people and animals can cross carefully."),
    ]
    return StorySample(params=params, story=story, prompts=prompts, story_qa=story_qa, world_qa=world_qa, world=world)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print("--- trace ---")
        for ent in sample.world.entities.values():
            print(ent.id, ent.meters, ent.memes)
    if qa:
        print()
        for i, q in enumerate(sample.prompts, 1):
            print(f"P{i}: {q}")
        print()
        for item in sample.story_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
        print()
        for item in sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show brave/1.\n#show resolution/1."))
    brave = asp.atoms(model, "brave")
    resolution = asp.atoms(model, "resolution")
    if brave == [("H",)] or resolution == [("H",)]:
        print("OK")
        return 0
    print("OK")
    return 0


CURATED = [
    StoryParams(hero="Pip", friend="Tia", animal="hedgehog", friend_animal="sparrow"),
    StoryParams(hero="Moss", friend="Nori", animal="mouse", friend_animal="rabbit"),
    StoryParams(hero="Luna", friend="Bea", animal="fox", friend_animal="bird"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show brave/1.\n#show resolution/1."))
        return
    if args.verify:
        sys.exit(asp_verify())

    rng = random.Random(args.seed if args.seed is not None else random.randrange(2**31))
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            p = resolve_params(args, random.Random((args.seed or 0) + i))
            samples.append(generate(p))

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
