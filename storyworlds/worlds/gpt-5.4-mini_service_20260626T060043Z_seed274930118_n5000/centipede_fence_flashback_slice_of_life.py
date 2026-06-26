#!/usr/bin/env python3
"""
A tiny slice-of-life story world about a child, a fence, and a centipede,
with a brief flashback that changes how the moment feels.

The story premise:
- A child notices a centipede near a fence.
- A flashback reminds them why they are careful around the fence.
- A small, ordinary choice turns the moment from worry into calm curiosity.

This module is self-contained and follows the Storyweavers world contract.
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
# Registries / constants
# ---------------------------------------------------------------------------

CHILD_NAMES = ["Mina", "Eli", "Nora", "Toby", "Lila", "Arun", "June", "Pia"]
ADULT_NAMES = ["Mom", "Dad", "Aunt Rosa", "Uncle Ben", "Grandma", "Grandpa"]
CHILD_TRAITS = ["curious", "quiet", "careful", "thoughtful", "gentle", "playful"]

# Simple physical/emotional thresholds for narration.
THRESHOLD = 1.0

# ---------------------------------------------------------------------------
# World entities
# ---------------------------------------------------------------------------


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretakers: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=lambda: {"distance": 0.0, "danger": 0.0})
    memes: dict[str, float] = field(default_factory=lambda: {"worry": 0.0, "calm": 0.0, "curiosity": 0.0})

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character" and self.type in {"girl", "woman", "mother", "aunt", "grandmother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.kind == "character" and self.type in {"boy", "man", "father", "uncle", "grandfather"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the little backyard"
    affords: set[str] = field(default_factory=lambda: {"walk", "look", "sit"})
    has_fence: bool = True
    has_path: bool = True


@dataclass
class Creature:
    id: str = "centipede"
    label: str = "a centipede"
    phrase: str = "a long little centipede with many tiny legs"
    legs: int = 20
    speed: str = "quickly"
    harmless: bool = True


@dataclass
class StoryParams:
    name: str
    adult: str
    trait: str
    place: str = "backyard"
    seed: Optional[int] = None


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    centipede: Creature = field(default_factory=Creature)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    flashback_seen: bool = False

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

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

    def copy(self) -> "World":
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.centipede = copy.deepcopy(self.centipede)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        clone.fired = set(self.fired)
        clone.flashback_seen = self.flashback_seen
        return clone


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------


def is_reasonable(params: StoryParams) -> bool:
    return params.name in CHILD_NAMES and params.adult in ADULT_NAMES


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
child(Name) :- child_name(Name).
adult(Name) :- adult_name(Name).

compatible_story(Name, Adult) :- child(Name), adult(Adult).
#show compatible_story/2.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for n in CHILD_NAMES:
        lines.append(asp.fact("child_name", n))
    for a in ADULT_NAMES:
        lines.append(asp.fact("adult_name", a))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_pairs() -> list[tuple[str, str]]:
    import asp
    model = asp.one_model(asp_program("#show compatible_story/2."))
    return sorted(set(asp.atoms(model, "compatible_story")))


def python_valid_pairs() -> list[tuple[str, str]]:
    return sorted((c, a) for c in CHILD_NAMES for a in ADULT_NAMES)


def asp_verify() -> int:
    a = set(asp_valid_pairs())
    p = set(python_valid_pairs())
    if a == p:
        print(f"OK: clingo gate matches python gate ({len(a)} pairs).")
        return 0
    print("MISMATCH between clingo and python:")
    if a - p:
        print("  only in clingo:", sorted(a - p))
    if p - a:
        print("  only in python:", sorted(p - a))
    return 1


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------


def flashback_text(hero: Entity, adult: Entity) -> str:
    return (
        f"For a moment, {hero.id} remembered being much smaller, "
        f"when {adult.id} had lifted {hero.pronoun('object')} away from the fence "
        f"because a loose board had made a sharp scrape."
    )


def tell_story(params: StoryParams) -> World:
    if not is_reasonable(params):
        raise StoryError("The chosen child or adult is not part of this small story world.")

    world = World(Setting(place=f"the {params.place}"))
    hero = world.add(Entity(id=params.name, kind="character", type="child", label=params.name))
    adult = world.add(Entity(id=params.adult, kind="character", type="adult", label=params.adult))
    fence = world.add(Entity(id="fence", kind="thing", type="fence", label="the fence", phrase="a wooden fence"))
    centipede = world.add(Entity(id="centipede", kind="creature", type="centipede", label="the centipede", phrase=world.centipede.phrase))

    hero.memes["curiosity"] += 1
    fence.meters["distance"] = 1.0
    centipede.meters["distance"] = 0.5
    world.facts.update(hero=hero, adult=adult, fence=fence, centipede=centipede, setting=world.setting)

    # Beginning
    world.say(
        f"{hero.id} was a {params.trait} child who liked quiet afternoons in {world.setting.place}."
    )
    world.say(
        f"One warm day, {hero.id} noticed {centipede.phrase} crawling near {fence.label}."
    )

    # Middle turn with flashback
    world.para()
    hero.memes["worry"] += 1
    world.say(
        f"{hero.id} paused at the path and watched the little creature move along the boards."
    )
    world.say(flashback_text(hero, adult))
    world.flashback_seen = True
    world.say(
        f"That memory made {hero.id} step back a little and keep {hero.pronoun('possessive')} hands to {hero.pronoun('possessive')} self."
    )

    # Resolution
    world.para()
    hero.memes["worry"] = max(0.0, hero.memes["worry"] - 1.0)
    hero.memes["calm"] += 1
    world.say(
        f"{adult.id} came over, smiled, and said the centipede was only trying to find a cool place to rest."
    )
    world.say(
        f"Together they looked from a safe spot, and {hero.id} felt calm again while the centipede slipped behind the fence."
    )
    world.say(
        f"By the time the sun moved lower, {hero.id} was still thinking about the tiny legs, but now the memory felt gentle instead of scary."
    )

    world.facts["resolved"] = True
    return world


# ---------------------------------------------------------------------------
# Q&A generation
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    adult = f["adult"]
    return [
        f'Write a short slice-of-life story for a young child about {hero.id}, a fence, and a centipede.',
        f"Tell a gentle story where {hero.id} sees a centipede near a fence and remembers something from the past with {adult.id}.",
        "Write a calm everyday story with a small flashback and an ending that feels safe and ordinary.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    adult: Entity = f["adult"]
    qas = [
        QAItem(
            question=f"Who saw the centipede near the fence?",
            answer=f"{hero.id} saw the centipede near the fence.",
        ),
        QAItem(
            question=f"What did {hero.id} remember in the flashback?",
            answer=(
                f"{hero.id} remembered being smaller, when {adult.id} had lifted "
                f"{hero.pronoun('object')} away from the fence after noticing a loose board."
            ),
        ),
        QAItem(
            question=f"How did {hero.id} feel at the end of the story?",
            answer=f"{hero.id} felt calm again and watched from a safe spot.",
        ),
    ]
    return qas


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a centipede?",
            answer="A centipede is a small crawling creature with many legs.",
        ),
        QAItem(
            question="What is a fence for?",
            answer="A fence marks a boundary, keeps spaces apart, and can help show where a yard ends.",
        ),
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is a brief memory of something that happened before the main scene.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
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
        lines.append(f"  {e.id:10} ({e.kind:10}) {' '.join(bits)}")
    lines.append(f"  flashback_seen={world.flashback_seen}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
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


# ---------------------------------------------------------------------------
# CLI helpers
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life story world: centipede, fence, and a flashback.")
    ap.add_argument("--name", choices=CHILD_NAMES)
    ap.add_argument("--adult", choices=ADULT_NAMES)
    ap.add_argument("--trait", choices=CHILD_TRAITS)
    ap.add_argument("--place", default="backyard")
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
    name = args.name or rng.choice(CHILD_NAMES)
    adult = args.adult or rng.choice(ADULT_NAMES)
    trait = args.trait or rng.choice(CHILD_TRAITS)
    params = StoryParams(name=name, adult=adult, trait=trait, place=args.place)
    if not is_reasonable(params):
        raise StoryError("The chosen parameters do not form a story in this world.")
    return params


def curated() -> list[StoryParams]:
    return [
        StoryParams(name="Mina", adult="Mom", trait="curious", place="backyard"),
        StoryParams(name="Eli", adult="Dad", trait="careful", place="garden"),
        StoryParams(name="Nora", adult="Grandma", trait="thoughtful", place="side yard"),
    ]


def asp_check() -> int:
    import asp
    model = asp.one_model(asp_program("#show compatible_story/2."))
    facts = set(asp.atoms(model, "compatible_story"))
    python = set(python_valid_pairs())
    if facts == python:
        print(f"OK: clingo gate matches python gate ({len(python)} pairs).")
        return 0
    print("MISMATCH between clingo and python gates.")
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show compatible_story/2."))
        return
    if args.verify:
        sys.exit(asp_check())
    if args.asp:
        pairs = asp_valid_pairs()
        print(f"{len(pairs)} compatible child/adult pairs:\n")
        for c, a in pairs:
            print(f"  {c:8} {a}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for p in curated():
            samples.append(generate(p))
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
            header = f"### {p.name} with {p.adult} in {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
