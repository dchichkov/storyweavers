#!/usr/bin/env python3
"""
Storyworld: Oomph, Fiftieth, Britches Transformation
====================================================

A small animal-story simulation about a tired little animal, a special fiftieth
treat, and a surprising transformation that changes what fits.

Premise seed:
- An animal hero is proud of a favorite pair of britches.
- On the fiftieth day of something special, a burst of oomph triggers a magical
  transformation.
- The hero must decide whether to panic or adapt.

The world model tracks:
- physical meters: size, snugness, sparkle, wear
- emotional memes: pride, surprise, worry, delight
- a single transformation turn that changes the hero's form and the fit of the
  britches

The story should read like a short animal tale with a clear beginning, turn,
and ending image.
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

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"mouse", "cat", "fox", "rabbit", "dog", "bear", "deer", "bird"}:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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
class Animal:
    id: str
    species: str
    adjective: str
    voice: str
    transformed_species: str
    transformed_adjective: str
    transformed_voice: str


@dataclass
class Britches:
    label: str = "britches"
    phrase: str = "a tidy pair of britches"
    color: str = "blue"
    pattern: str = "striped"
    fit: str = "snug"


@dataclass
class StoryParams:
    animal: str
    name: str
    seed: Optional[int] = None


ANIMALS = {
    "mouse": Animal("mouse", "mouse", "small", "squeak", "chipmunk", "slightly fluffier", "chitter"),
    "rabbit": Animal("rabbit", "rabbit", "quick", "thump", "hare", "longer-legged", "sniff"),
    "fox": Animal("fox", "fox", "curious", "yip", "kit", "golden", "chirp"),
    "cat": Animal("cat", "cat", "soft", "mew", "lynx", "bigger-eared", "purr"),
}

NAMES = ["Milo", "Pip", "Tansy", "Nell", "Otis", "Junie", "Bram", "Fern"]
ANIMAL_ORDER = list(ANIMALS.keys())


class StoryWorld:
    def __init__(self, animal: Animal, name: str) -> None:
        self.world = World()
        self.animal = animal
        self.name = name
        self.hero = self.world.add(Entity(
            id=name,
            kind="character",
            type=animal.species,
            label=name,
            meters={"size": 1.0, "snugness": 1.0, "sparkle": 0.0, "wear": 0.0},
            memes={"pride": 1.0, "worry": 0.0, "surprise": 0.0, "delight": 0.0},
        ))
        self.britches = self.world.add(Entity(
            id="britches",
            kind="thing",
            type="britches",
            label="britches",
            phrase="a tidy pair of britches",
            owner=name,
            worn_by=name,
            plural=True,
            meters={"snugness": 1.0, "wear": 0.0},
        ))
        self.world.facts["animal"] = animal
        self.world.facts["britches"] = self.britches

    def transform(self) -> None:
        self.hero.type = self.animal.transformed_species
        self.hero.meters["size"] += 1.0
        self.hero.meters["sparkle"] += 1.0
        self.hero.memes["surprise"] += 1.0
        self.hero.memes["delight"] += 0.5
        self.britches.meters["snugness"] -= 1.0
        self.britches.meters["wear"] += 0.5

    def story(self) -> World:
        w = self.world
        a = self.animal

        w.say(
            f"On a bright morning, {self.name} the {a.adjective} {a.species} loved "
            f"{a.voice}-ing through the grass in {self.britches.phrase}."
        )
        w.say(
            f"It was the fiftieth day of the little meadow fair, and everyone said "
            f"that a fiftieth turn ought to end with extra oomph."
        )

        w.para()
        w.say(
            f"{self.name} found a round seed pod in the clover and gave it a tiny tap."
        )
        w.say(
            f"With a surprising oomph, the pod burst warm and golden, and {self.name} began to change."
        )
        self.transform()

        w.say(
            f"{self.name} stretched into a {a.transformed_adjective} {a.transformed_species}, "
            f"and the britches suddenly felt far too snug."
        )
        self.hero.memes["worry"] += 1.0

        w.para()
        if self.hero.meters["size"] > 1.5 and self.britches.meters["snugness"] <= 0:
            w.say(
                f"For a moment, {self.name} blinked at the little buttons and nearly fretted."
            )
            w.say(
                f"But then {self.name} giggled, wiggled free, and decided the day was too fine for grumbling."
            )
            self.hero.memes["worry"] = 0.0
        else:
            w.say(
                f"{self.name} breathed in, found that the britches still held, and smiled at the new shape."
            )

        w.say(
            f"By sunset, {self.name} was still wearing the same britches, only now they were a silly souvenir of the fiftieth day."
        )
        w.say(
            f"{self.name} sat in the grass as a {a.transformed_species}, bright-eyed and happy, with the britches resting nearby and the meadow smelling like clover."
        )

        w.facts.update(hero=self.hero, name=self.name, britches=self.britches)
        return w


def valid_names() -> list[str]:
    return NAMES[:]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal story world with a fiftieth-day transformation and britches.")
    ap.add_argument("--animal", choices=ANIMAL_ORDER)
    ap.add_argument("--name", choices=valid_names())
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
    animal = args.animal or rng.choice(ANIMAL_ORDER)
    name = args.name or rng.choice(NAMES)
    return StoryParams(animal=animal, name=name)


def generate(params: StoryParams) -> StorySample:
    if params.animal not in ANIMALS:
        raise StoryError("Unknown animal.")
    if params.name not in NAMES:
        raise StoryError("Unknown name.")
    sim = StoryWorld(ANIMALS[params.animal], params.name)
    world = sim.story()
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    animal = f["animal"]
    return [
        f"Write a short animal story about {hero.id}, a {animal.adjective} {animal.species}, and a fiftieth-day oomph.",
        f"Tell a gentle transformation story where {hero.id} wears britches and something magical changes {hero.id}.",
        f"Write a child-friendly story that includes the words oomph, fiftieth, and britches.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    animal = f["animal"]
    britches = f["britches"]
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"It is about {hero.id}, a {animal.adjective} {animal.species} who loves its britches.",
        ),
        QAItem(
            question=f"What happened on the fiftieth day?",
            answer=f"On the fiftieth day, a burst of oomph made {hero.id} transform into a {animal.transformed_adjective} {animal.transformed_species}.",
        ),
        QAItem(
            question=f"What happened to the britches after the transformation?",
            answer=f"The britches became too snug, so they turned into a funny reminder of the change.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does transformation mean?",
            answer="Transformation means changing from one form into another.",
        ),
        QAItem(
            question="What is oomph?",
            answer="Oomph is a burst of energy or force that makes something happen with a lot of power.",
        ),
        QAItem(
            question="What are britches?",
            answer="Britches are old-fashioned pants or trousers.",
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
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


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
        if e.worn_by:
            bits.append(f"worn_by={e.worn_by}")
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
hero(h).
britches(b).
can_transform(h).
oomph_day(50).
transforms(h) :- hero(h), can_transform(h), oomph_day(50).
snug(b) :- britches(b).
too_tight(b) :- transforms(h), britches(b), snug(b).
"""

def asp_facts() -> str:
    import asp
    lines = []
    lines.append(asp.fact("hero", "h"))
    lines.append(asp.fact("britches", "b"))
    lines.append(asp.fact("can_transform", "h"))
    lines.append(asp.fact("oomph_day", 50))
    lines.append(asp.fact("snug", "b"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    return 0


CURATED = [
    StoryParams(animal="mouse", name="Pip"),
    StoryParams(animal="rabbit", name="Milo"),
    StoryParams(animal="fox", name="Tansy"),
    StoryParams(animal="cat", name="Fern"),
]


def resolve_all_samples(args: argparse.Namespace, base_seed: int) -> list[StorySample]:
    samples: list[StorySample] = []
    if args.all:
        for p in CURATED:
            samples.append(generate(p))
        return samples
    seen = set()
    i = 0
    while len(samples) < args.n and i < max(50, args.n * 20):
        p = resolve_params(args, random.Random(base_seed + i))
        p.seed = base_seed + i
        sample = generate(p)
        if sample.story not in seen:
            seen.add(sample.story)
            samples.append(sample)
        i += 1
    return samples


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show hero/1.\n#show britches/1.\n#show transforms/1.\n#show too_tight/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("ASP mode is intentionally minimal for this world.")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = resolve_all_samples(args, base_seed)

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
