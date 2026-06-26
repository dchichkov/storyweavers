#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/girdle_bad_ending_inner_monologue_animal_story.py
===========================================================================================================

A small animal-story world with a single strained comfort problem: an animal
tries to wear a girdle for a special outing, listens to its own anxious inner
voice, and ends with a bad outcome.

The world is intentionally tiny and classical:
- typed entities with physical meters and emotional memes
- a state-driven turn from want -> discomfort -> refusal -> bad ending
- a Python reasonableness gate plus an inline ASP twin
- child-facing prose, but with an unhappy ending as requested
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
# World model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"sheep", "rabbit", "cat", "fox", "mouse", "owl"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Place:
    id: str
    label: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Garment:
    id: str
    label: str
    phrase: str
    fits: set[str] = field(default_factory=set)
    tight: bool = False


@dataclass
class StoryParams:
    animal: str
    place: str
    garment: str
    name: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[str] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
PLACES = {
    "garden": Place("garden", "the garden", {"show"}),
    "barn": Place("barn", "the barn", {"show"}),
    "meadow": Place("meadow", "the meadow", {"show"}),
    "porch": Place("porch", "the porch", {"show"}),
}

ANIMALS = {
    "rabbit": {"type": "rabbit", "kind_word": "rabbit", "body": "waist"},
    "cat": {"type": "cat", "kind_word": "cat", "body": "waist"},
    "fox": {"type": "fox", "kind_word": "fox", "body": "waist"},
    "sheep": {"type": "sheep", "kind_word": "sheep", "body": "waist"},
    "mouse": {"type": "mouse", "kind_word": "mouse", "body": "waist"},
}

GARMENTS = {
    "girdle": Garment(
        id="girdle",
        label="girdle",
        phrase="a snug girdle",
        fits={"waist"},
        tight=True,
    ),
}

NAMES = {
    "rabbit": ["Mina", "Lulu", "Nia"],
    "cat": ["Pip", "Momo", "Tia"],
    "fox": ["Rin", "Vivi", "Fay"],
    "sheep": ["Bess", "Mina", "Dot"],
    "mouse": ["Squeak", "Mimi", "Pip"],
}


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def valid_combo(place: str, animal: str, garment: str) -> bool:
    return place in PLACES and animal in ANIMALS and garment in GARMENTS and "show" in PLACES[place].affords


def valid_combos() -> list[tuple[str, str, str]]:
    return [(p, a, g) for p in PLACES for a in ANIMALS for g in GARMENTS if valid_combo(p, a, g)]


def explain_rejection(place: str, animal: str, garment: str) -> str:
    return (
        f"(No story: the {garment} does not make sense outside a small show-like outing "
        f"in this world, so the animal's worry would not have a clear cause.)"
    )


# ---------------------------------------------------------------------------
# State updates and narration
# ---------------------------------------------------------------------------
def setup(world: World, name: str, animal_key: str, garment_key: str) -> None:
    animal_cfg = ANIMALS[animal_key]
    garment_cfg = GARMENTS[garment_key]
    hero = world.add(Entity(
        id=name,
        kind="character",
        type=animal_cfg["type"],
        label=name,
        meters={"comfort": 5.0, "energy": 5.0},
        memes={"hope": 1.0, "worry": 0.0, "shame": 0.0, "stubborn": 0.0},
    ))
    garment = world.add(Entity(
        id=garment_cfg.id,
        type="garment",
        label=garment_cfg.label,
        phrase=garment_cfg.phrase,
        owner=hero.id,
        meters={"tightness": 0.0},
    ))
    world.facts.update(hero=hero, garment=garment, garment_cfg=garment_cfg)


def open_story(world: World) -> None:
    hero: Entity = world.facts["hero"]
    garment: Entity = world.facts["garment"]
    world.say(
        f"{hero.label} was a little {hero.type} who loved dressing up for the village show."
    )
    world.say(
        f"One morning, {hero.label} found {garment.phrase} on the chair and thought, "
        f"\"If I wear this, I will look neat and important.\""
    )
    hero.memes["hope"] += 1.0
    garment.worn_by = hero.id


def inner_monologue(world: World, stage: str) -> None:
    hero: Entity = world.facts["hero"]
    garment: Entity = world.facts["garment"]
    if stage == "first_try":
        world.say(
            f"{hero.label} pulled the girdle on and then listened to {hero.pronoun('possessive')} own thoughts: "
            f"\"It is a little tight, but maybe I will get used to it.\""
        )
    elif stage == "worse":
        world.say(
            f"After a few steps, {hero.label} thought, "
            f"\"It is squeezing me. My belly feels all pinched. I should say something.\""
        )
    elif stage == "final":
        world.say(
            f"{hero.label} looked at the snapped girdle and thought, "
            f"\"I wanted to look proud, but now I only feel small and sore.\""
        )


def strain(world: World) -> None:
    hero: Entity = world.facts["hero"]
    garment: Entity = world.facts["garment"]
    hero.meters["comfort"] -= 2.0
    garment.meters["tightness"] += 2.0
    hero.memes["worry"] += 1.0
    hero.memes["stubborn"] += 1.0


def warn(world: World) -> None:
    hero: Entity = world.facts["hero"]
    world.say(
        f"{hero.label}'s friend peeked at the girdle and said, "
        f"\"That looks too tight for dancing.\""
    )


def refuse_help(world: World) -> None:
    hero: Entity = world.facts["hero"]
    hero.memes["stubborn"] += 1.0
    world.say(
        f"But {hero.label} shook {hero.pronoun('possessive')} head and stayed quiet, "
        f"telling {hero.pronoun('object')}self, \"I can do it. I can do it.\""
    )


def bad_end(world: World) -> None:
    hero: Entity = world.facts["hero"]
    garment: Entity = world.facts["garment"]
    world.say(
        f"Then the girdle pulled once too hard, and with a little snap it broke."
    )
    hero.meters["comfort"] = 0.0
    hero.meters["energy"] -= 1.0
    hero.memes["shame"] += 2.0
    world.say(
        f"The show had to start without {hero.label}, and {hero.label} sat on the porch, "
        f"trying not to cry."
    )
    inner_monologue(world, "final")
    world.say(
        f"The broken girdle lay still on the floor, and the bright morning felt cold."
    )
    garment.worn_by = None


def tell_story(params: StoryParams) -> World:
    world = World(PLACES[params.place])
    setup(world, params.name, params.animal, params.garment)
    open_story(world)
    world.para()
    inner_monologue(world, "first_try")
    strain(world)
    warn(world)
    inner_monologue(world, "worse")
    refuse_help(world)
    world.para()
    bad_end(world)
    world.facts.update(place=world.place, params=params)
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]
    return [
        f"Write an animal story about {hero.label} and a girdle that ends badly.",
        f"Tell a short story where a little {hero.type} thinks to itself while trying to wear a girdle.",
        f"Write a simple, child-facing animal story with a tight girdle, a warning, and a sad ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero: Entity = world.facts["hero"]
    garment: Entity = world.facts["garment"]
    place: Place = world.facts["place"]
    return [
        QAItem(
            question=f"What did {hero.label} want to do at {place.label}?",
            answer=f"{hero.label} wanted to dress up for the village show and wear {garment.phrase}.",
        ),
        QAItem(
            question=f"What did {hero.label} think after putting on the girdle?",
            answer=f"{hero.label} thought it was a little tight, then later thought it was pinching and hurting.",
        ),
        QAItem(
            question=f"How did the story end for {hero.label}?",
            answer=f"It ended badly. The girdle snapped, the show went on without {hero.label}, and {hero.label} sat on the porch feeling small and sore.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a girdle?",
            answer="A girdle is a tight garment worn around the waist to shape or hold clothes in place.",
        ),
        QAItem(
            question="Why can tight clothes feel bad?",
            answer="Tight clothes can pinch, squeeze, and make it hard to move or breathe comfortably.",
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


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
valid_story(P, A, G) :- place(P), animal(A), garment(G), affords(P, show).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        for act in sorted(place.affords):
            lines.append(asp.fact("affords", pid, act))
    for aid in ANIMALS:
        lines.append(asp.fact("animal", aid))
    for gid in GARMENTS:
        lines.append(asp.fact("garment", gid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("  only in clingo:", sorted(clingo_set - python_set))
    print("  only in python:", sorted(python_set - clingo_set))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(animal="rabbit", place="garden", garment="girdle", name="Mina"),
    StoryParams(animal="cat", place="porch", garment="girdle", name="Pip"),
    StoryParams(animal="fox", place="meadow", garment="girdle", name="Rin"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal story world with a girdle and a bad ending.")
    ap.add_argument("--animal", choices=sorted(ANIMALS))
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--garment", choices=sorted(GARMENTS))
    ap.add_argument("--name")
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
    if args.place and args.animal and args.garment:
        if not valid_combo(args.place, args.animal, args.garment):
            raise StoryError(explain_rejection(args.place, args.animal, args.garment))
    combos = [
        c for c in valid_combos()
        if (args.place is None or c[0] == args.place)
        and (args.animal is None or c[1] == args.animal)
        and (args.garment is None or c[2] == args.garment)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, animal, garment = rng.choice(sorted(combos))
    name = args.name or rng.choice(NAMES[animal])
    return StoryParams(animal=animal, place=place, garment=garment, name=name)


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
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
        lines.append(
            f"  {e.id}: type={e.type} meters={{{', '.join(f'{k}: {v}' for k, v in e.meters.items())}}} "
            f"memes={{{', '.join(f'{k}: {v}' for k, v in e.memes.items())}}}"
        )
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
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, animal, garment) combos:\n")
        for p, a, g in combos:
            print(f"  {p:8} {a:8} {g:8}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
                return
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
            header = f"### {p.name}: {p.animal} in {p.place} with {p.garment}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
