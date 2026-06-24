#!/usr/bin/env python3
"""
storyworlds/worlds/triangle_kindness_surprise_mystery.py
========================================================

A small mystery-style storyworld about a child, a triangle-shaped object,
kindness, and a surprise reveal.

Premise seed:
- A child notices a triangle-shaped thing is missing.
- The child follows small clues, meets someone in need, and chooses kindness.
- The surprise is that the "mystery" is caused by a helpful act, not theft.
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
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    carries: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.label:
            self.label = self.type

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class StoryParams:
    place: str
    hero_name: str
    hero_type: str
    helper_type: str
    triangle_kind: str
    clue_kind: str
    seed: Optional[int] = None


@dataclass
class World:
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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


SETTINGS = {
    "schoolyard": "the schoolyard",
    "garden": "the garden",
    "attic": "the attic room",
    "library": "the library corner",
}

HERO_NAMES = ["Mia", "Noah", "Luna", "Eli", "Ava", "Theo"]
HELPER_TYPES = ["friend", "neighbor", "sister", "brother"]
HERO_TYPES = ["girl", "boy"]
TRIANGLE_KINDS = [
    ("triangle kite", "kite"),
    ("triangle card", "card"),
    ("triangle flag", "flag"),
    ("triangle note", "note"),
]
CLUE_KINDS = [
    ("chalk mark", "chalk"),
    ("paper scrap", "paper"),
    ("string loop", "string"),
]


class Story:
    def __init__(self, world: World, hero: Entity, helper: Entity, triangle: Entity, clue: Entity):
        self.world = world
        self.hero = hero
        self.helper = helper
        self.triangle = triangle
        self.clue = clue

    def setup(self) -> None:
        w = self.world
        h = self.hero
        t = self.triangle
        w.say(
            f"{h.id} was a little {h.type} who loved solving quiet mysteries at {w.place}."
        )
        w.say(
            f"{h.id} had a special {t.label}, and {t.phrase} seemed to matter more than any toy."
        )
        w.say(
            f"One morning, {h.id} looked everywhere, but the {t.label} was gone."
        )

    def tension(self) -> None:
        w = self.world
        h = self.hero
        clue = self.clue
        w.para()
        h.memes["curiosity"] = h.memes.get("curiosity", 0) + 1
        h.memes["worry"] = h.memes.get("worry", 0) + 1
        w.say(
            f"{h.id} found a tiny {clue.label} near the steps, and the little clue made the mystery feel bigger."
        )
        w.say(
            f"{h.id} whispered, 'Who left this behind?' and began to follow the trail with careful feet."
        )
        self.helper_arrives()

    def helper_arrives(self) -> None:
        w = self.world
        h = self.hero
        helper = self.helper
        w.say(
            f"Then {helper.id} appeared, carrying a basket and looking a little flustered."
        )
        helper.memes["kindness"] = helper.memes.get("kindness", 0) + 1
        w.say(
            f"{helper.id} saw {h.id} searching and asked a gentle question instead of grabbing the clue."
        )

    def turn(self) -> None:
        w = self.world
        h = self.hero
        helper = self.helper
        t = self.triangle
        clue = self.clue
        w.para()
        h.memes["kindness"] = h.memes.get("kindness", 0) + 1
        w.say(
            f"{h.id} decided to be kind and listen carefully. That choice made the mystery feel safer."
        )
        w.say(
            f"{helper.id} explained that the {t.label} had not been stolen at all."
        )
        w.say(
            f"It had been moved to help a smaller child reach a shelf, and the {clue.label} was the last piece of the surprise."
        )
        t.meters["found"] = 1
        t.meters["helped"] = 1

    def ending(self) -> None:
        w = self.world
        h = self.hero
        helper = self.helper
        t = self.triangle
        w.para()
        h.memes["relief"] = h.memes.get("relief", 0) + 1
        w.say(
            f"{h.id} smiled when the surprise made sense."
        )
        w.say(
            f"Together, {h.id} and {helper.id} put the {t.label} back in its place, and the room felt neat and bright again."
        )
        w.say(
            f"By the end, the triangle was safe, the kindness was noticed, and the mystery had turned into a happy story."
        )


def build_world(params: StoryParams) -> World:
    world = World(place=SETTINGS[params.place])
    hero = world.add(Entity(id=params.hero_name, kind="character", type=params.hero_type))
    helper = world.add(Entity(id="Helper", kind="character", type=params.helper_type))
    triangle = world.add(
        Entity(
            id="triangle",
            type="thing",
            label=params.triangle_kind,
            phrase=f"a bright {params.triangle_kind} with three neat corners",
            owner=hero.id,
        )
    )
    clue = world.add(
        Entity(
            id="clue",
            type="thing",
            label=params.clue_kind,
            phrase=f"a small {params.clue_kind} clue",
        )
    )
    world.facts.update(hero=hero, helper=helper, triangle=triangle, clue=clue, params=params)
    return world


def tell(params: StoryParams) -> World:
    world = build_world(params)
    s = Story(world, world.get(params.hero_name), world.get("Helper"), world.get("triangle"), world.get("clue"))
    s.setup()
    s.tension()
    s.turn()
    s.ending()
    return world


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    return [
        "Write a short mystery story for a child about a triangle and a kind surprise.",
        f"Tell a gentle mystery where {p.hero_name} searches for a {p.triangle_kind} and learns why it moved.",
        f"Make a tiny story with kindness, a surprise, and the word triangle set at {world.place}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    h = world.facts["hero"]
    helper = world.facts["helper"]
    triangle = world.facts["triangle"]
    return [
        QAItem(
            question=f"What was {h.id} looking for at {world.place}?",
            answer=f"{h.id} was looking for {triangle.label}, a triangle-shaped thing that had gone missing.",
        ),
        QAItem(
            question=f"Who helped explain the surprise in the story?",
            answer=f"{helper.id} helped explain it by speaking gently instead of making the mystery scarier.",
        ),
        QAItem(
            question=f"Why was the triangle moved?",
            answer="It was moved to help a smaller child reach a shelf, so the mystery was really a kind act.",
        ),
        QAItem(
            question=f"How did {h.id} solve the mystery?",
            answer=f"{h.id} followed a tiny clue, listened carefully, and learned that the triangle had been moved to help someone.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a triangle?",
            answer="A triangle is a shape with three straight sides and three corners.",
        ),
        QAItem(
            question="What does kindness mean?",
            answer="Kindness means being gentle, helpful, and caring to other people.",
        ),
        QAItem(
            question="What is a surprise?",
            answer="A surprise is something unexpected that can make people gasp, smile, or wonder.",
        ),
        QAItem(
            question="What is a mystery?",
            answer="A mystery is a puzzle or question that you need to think about and solve.",
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Triangle kindness surprise mystery storyworld.")
    ap.add_argument("--place", choices=sorted(SETTINGS))
    ap.add_argument("--name", choices=HERO_NAMES)
    ap.add_argument("--gender", choices=HERO_TYPES)
    ap.add_argument("--helper", choices=HELPER_TYPES)
    ap.add_argument("--triangle", choices=[t[0] for t in TRIANGLE_KINDS])
    ap.add_argument("--clue", choices=[c[0] for c in CLUE_KINDS])
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
    place = args.place or rng.choice(sorted(SETTINGS))
    name = args.name or rng.choice(HERO_NAMES)
    gender = args.gender or rng.choice(HERO_TYPES)
    helper = args.helper or rng.choice(HELPER_TYPES)
    triangle = args.triangle or rng.choice([t[0] for t in TRIANGLE_KINDS])
    clue = args.clue or rng.choice([c[0] for c in CLUE_KINDS])
    if place not in SETTINGS:
        raise StoryError("unknown place")
    if gender not in HERO_TYPES:
        raise StoryError("unknown hero type")
    return StoryParams(place=place, hero_name=name, hero_type=gender, helper_type=helper, triangle_kind=triangle, clue_kind=clue)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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
        print("--- trace ---")
        for e in sample.world.entities.values():
            print(e.id, e.kind, e.type, dict(e.meters), dict(e.memes))
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams("schoolyard", "Mia", "girl", "friend", "triangle kite", "chalk mark"),
    StoryParams("garden", "Noah", "boy", "neighbor", "triangle card", "paper scrap"),
]


ASP_RULES = r"""
triangle_shape(T) :- triangle(T).
kind_act(k) :- kindness(k).
surprise_act(s) :- surprise(s).
mystery_story(P) :- place(P), triangle_shape(_), kind_act(_), surprise_act(_).

show_story(P) :- mystery_story(P).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for place in SETTINGS:
        lines.append(asp.fact("place", place))
    for tri, _ in TRIANGLE_KINDS:
        lines.append(asp.fact("triangle", tri))
    lines.append(asp.fact("kindness", "kindness"))
    lines.append(asp.fact("surprise", "surprise"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show mystery_story/1."))
    atoms = set(asp.atoms(model, "mystery_story"))
    python = {(p,) for p in SETTINGS}
    if atoms == python:
        print(f"OK: ASP matches Python ({len(python)} places).")
        return 0
    print("MISMATCH")
    print("ASP:", sorted(atoms))
    print("PY :", sorted(python))
    return 1


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show mystery_story/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
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
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
