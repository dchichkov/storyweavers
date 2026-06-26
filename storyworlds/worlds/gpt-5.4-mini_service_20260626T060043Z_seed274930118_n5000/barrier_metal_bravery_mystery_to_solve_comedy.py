#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/barrier_metal_bravery_mystery_to_solve_comedy.py
====================================================================================================

A small comedy storyworld about a child, a barrier, and a shiny metal mystery.

Seed tale:
---
A curious child found a strange barrier in the yard. On the other side, something
kept making a tiny clink-clink sound. The child was nervous, but brave enough to
investigate. With a little help, the child solved the mystery and discovered the
clinking was only a metal spoon stuck in a toy bucket.

The story engine models:
- a barrier that blocks a path
- a metal object that reflects light and makes a noise
- bravery as a membrane of courage that can rise when the child acts
- mystery as a puzzle state that decreases when clues are followed
- a gentle comic turn where the "problem" is smaller than it first seemed
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
# Core thresholds and constants
# ---------------------------------------------------------------------------
THRESHOLD = 1.0

BARRIER_TYPES = {
    "fence": "a wobbly fence",
    "gate": "a little gate",
    "hedge": "a hedge with a narrow opening",
    "rope": "a rope barrier",
}

METAL_OBJECTS = {
    "spoon": "a shiny metal spoon",
    "key": "a small metal key",
    "bucket": "a metal bucket",
    "bell": "a tiny metal bell",
    "ladle": "a long metal ladle",
}

PLACES = {
    "yard": "the yard",
    "garden": "the garden",
    "playground": "the playground",
    "alley": "the alley behind the house",
}

HELPERS = {
    "parent": "parent",
    "neighbor": "neighbor",
    "friend": "friend",
    "grandparent": "grandparent",
}

NAMES = ["Maya", "Leo", "Nora", "Finn", "Ava", "Owen", "Zoe", "Milo", "Ivy", "Theo"]
TRAITS = ["curious", "brave", "cheerful", "silly", "careful", "bold"]

# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"bravery": 0.0, "mystery": 0.0, "joy": 0.0, "noise": 0.0}
        if not self.memes:
            self.memes = {"bravery": 0.0, "mystery": 0.0, "joy": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "grandmother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "grandfather"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the yard"


@dataclass
class StoryState:
    barrier: str
    metal_object: str
    place: str
    hero_name: str
    hero_type: str
    helper_type: str
    trait: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

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
# Parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    barrier: str
    metal_object: str
    name: str
    gender: str
    helper: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Reasonableness checks
# ---------------------------------------------------------------------------
def barrier_blocks_metal(barrier: str, metal_object: str) -> bool:
    return barrier in BARRIER_TYPES and metal_object in METAL_OBJECTS


def reasonable_pair(barrier: str, metal_object: str) -> bool:
    return barrier_blocks_metal(barrier, metal_object)


def explain_rejection(barrier: str, metal_object: str) -> str:
    return (
        f"(No story: the barrier '{barrier}' and metal object '{metal_object}' "
        f"do not fit this comic mystery setup.)"
    )


# ---------------------------------------------------------------------------
# Narrative helpers
# ---------------------------------------------------------------------------
def intro_line(hero: Entity, setting: Setting, barrier: str, metal_object: str) -> str:
    return (
        f"{hero.id} was a little {hero.type} who loved noticing odd things in {setting.place}. "
        f"One day, {hero.pronoun('subject')} spotted {BARRIER_TYPES[barrier]} and heard a faint clink from {METAL_OBJECTS[metal_object]} nearby."
    )


def bravery_line(hero: Entity) -> str:
    return (
        f"{hero.id} gulped, then stood a little straighter. "
        f"{hero.pronoun('subject').capitalize()} decided to be brave and take a closer look."
    )


def mystery_line(hero: Entity) -> str:
    return (
        f"The closer {hero.id} looked, the more puzzling it seemed. "
        f"Why would a shiny thing clink so softly in such an ordinary place?"
    )


def comic_turn_line(hero: Entity, helper: Entity, metal_object: Entity) -> str:
    return (
        f"{helper.id} peered over and laughed kindly. "
        f'"Oh! That is only {metal_object.phrase} stuck in a toy bucket," {helper.id} said. '
        f'{hero.id} blinked, then laughed too, because the great mystery was being a very tiny one.'
    )


def resolution_line(hero: Entity, helper: Entity) -> str:
    return (
        f"Together, they lifted the bucket free and set it right side up. "
        f"{hero.id} grinned at {helper.id}, proud of being brave enough to solve the mystery."
    )


# ---------------------------------------------------------------------------
# World simulation
# ---------------------------------------------------------------------------
def simulate(params: StoryParams) -> World:
    if not reasonable_pair(params.barrier, params.metal_object):
        raise StoryError(explain_rejection(params.barrier, params.metal_object))

    world = World(Setting(place=PLACES[params.place]))
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender))
    helper = world.add(Entity(id="Helper", kind="character", type=HELPERS[params.helper]))
    barrier = world.add(Entity(
        id="Barrier",
        type="barrier",
        label=BARRIER_TYPES[params.barrier],
        phrase=BARRIER_TYPES[params.barrier],
    ))
    metal = world.add(Entity(
        id="MetalObject",
        type="metal",
        label=METAL_OBJECTS[params.metal_object].replace("a ", "", 1),
        phrase=METAL_OBJECTS[params.metal_object],
    ))

    # State: the child is curious and the mystery is present.
    hero.memes["mystery"] += 1
    hero.memes["bravery"] += 0.5

    world.say(intro_line(hero, world.setting, params.barrier, params.metal_object))
    world.para()

    # Tension: the barrier blocks the way and the noise feels puzzling.
    world.say(
        f"The barrier blocked the best path, and the little clink seemed to come from behind it. "
        f"{hero.id} wanted to know what it was, but {hero.pronoun('subject')} also felt a flutter in {hero.pronoun('possessive')} tummy."
    )
    world.say(bravery_line(hero))
    hero.meters["bravery"] += 1
    hero.memes["bravery"] += 1
    hero.memes["mystery"] += 1
    world.para()

    # The child investigates, then discovers the clue.
    world.say(mystery_line(hero))
    helper.meters["joy"] += 1
    world.say(
        f"{hero.id} leaned closer and saw a flash of metal under the barrier. "
        f"It looked dramatic for a moment, but it was only {metal.phrase} making the silly little sound."
    )
    world.para()

    # Comic relief and resolution.
    world.say(comic_turn_line(hero, helper, metal))
    hero.memes["mystery"] = max(0.0, hero.memes["mystery"] - 1.0)
    hero.memes["joy"] += 1
    hero.meters["joy"] += 1
    world.para()

    world.say(resolution_line(hero, helper))
    world.say(
        f"In the end, the barrier was just a barrier, the metal was just a metal thing, and {hero.id} was the brave one who solved the mystery."
    )

    world.facts.update(
        hero=hero,
        helper=helper,
        barrier=barrier,
        metal=metal,
        params=params,
        state=StoryState(
            barrier=params.barrier,
            metal_object=params.metal_object,
            place=params.place,
            hero_name=params.name,
            hero_type=params.gender,
            helper_type=params.helper,
            trait=params.trait,
        ),
    )
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts["state"]
    return [
        f'Write a short comedy story for a young child about "{f.barrier}" and "{f.metal_object}" in {PLACES[f.place]}.',
        f"Tell a gentle story where {f.hero_name} is brave enough to investigate a barrier and solve a mystery.",
        f"Write a child-friendly funny story that includes a metal clue, a barrier, and a happy discovery.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero: Entity = world.facts["hero"]
    helper: Entity = world.facts["helper"]
    state: StoryState = world.facts["state"]
    barrier_label = BARRIER_TYPES[state.barrier]
    metal_phrase = METAL_OBJECTS[state.metal_object]

    return [
        QAItem(
            question=f"Who was the story about in {world.setting.place}?",
            answer=(
                f"It was about {hero.id}, a little {hero.type} who found a funny mystery in {world.setting.place}."
            ),
        ),
        QAItem(
            question=f"What blocked the way and started the mystery?",
            answer=(
                f"{barrier_label} blocked the way, so {hero.id} had to look carefully and be brave."
            ),
        ),
        QAItem(
            question=f"What was the shiny metal thing really?",
            answer=(
                f"It was {metal_phrase}, and it made the clinking sound that seemed so mysterious at first."
            ),
        ),
        QAItem(
            question=f"How did {hero.id} feel when the mystery was solved?",
            answer=(
                f"{hero.id} felt proud and happy, because being brave helped solve the mystery."
            ),
        ),
        QAItem(
            question=f"Who helped {hero.id} understand the clue?",
            answer=(
                f"{helper.id} helped by looking closely and laughing kindly when the answer turned out to be simple."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a barrier?",
            answer="A barrier is something that blocks a path or makes you stop and go around it.",
        ),
        QAItem(
            question="What is metal?",
            answer="Metal is a hard material that can shine, ring, and make a clinking sound.",
        ),
        QAItem(
            question="What does it mean to be brave?",
            answer="Being brave means you feel a little scared, but you still try to do the right thing.",
        ),
        QAItem(
            question="What is a mystery?",
            answer="A mystery is something puzzling that you do not understand right away.",
        ),
        QAItem(
            question="How can you solve a mystery?",
            answer="You solve a mystery by looking carefully, asking questions, and following clues.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A barrier-and-metal story is valid when the chosen barrier and metal object exist.
valid(B, M) :- barrier(B), metal(M).

% The story should be comic, so the metal object must be small enough to be harmlessly surprising.
comic(M) :- metal(M), small(M).

% A solvable mystery needs a helper and a clue.
solvable(B, M) :- valid(B, M), comic(M), clue(M), helper_available.

#show valid/2.
#show solvable/2.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for b in BARRIER_TYPES:
        lines.append(asp.fact("barrier", b))
    for m in METAL_OBJECTS:
        lines.append(asp.fact("metal", m))
    for m in {"spoon", "key", "bell"}:
        lines.append(asp.fact("small", m))
        lines.append(asp.fact("clue", m))
    lines.append(asp.fact("small", "ladle"))
    lines.append(asp.fact("helper_available"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_pairs() -> list[tuple[str, str]]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_solvable_pairs() -> list[tuple[str, str]]:
    import asp
    model = asp.one_model(asp_program("#show solvable/2."))
    return sorted(set(asp.atoms(model, "solvable")))


def asp_verify() -> int:
    py = {(b, m) for b in BARRIER_TYPES for m in METAL_OBJECTS}
    clingo_valid = set(asp_valid_pairs())
    if clingo_valid != py:
        print("MISMATCH between clingo and Python valid-pair gate:")
        if clingo_valid - py:
            print("  only in clingo:", sorted(clingo_valid - py))
        if py - clingo_valid:
            print("  only in python:", sorted(py - clingo_valid))
        return 1
    print(f"OK: clingo gate matches Python ({len(py)} valid pairs).")
    return 0


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A comedy storyworld about a barrier, a metal clue, and bravery."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--barrier", choices=BARRIER_TYPES)
    ap.add_argument("--metal-object", choices=METAL_OBJECTS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--name")
    ap.add_argument("--trait", choices=TRAITS)
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
    barrier = args.barrier or rng.choice(sorted(BARRIER_TYPES))
    metal_object = args.metal_object or rng.choice(sorted(METAL_OBJECTS))
    if not reasonable_pair(barrier, metal_object):
        raise StoryError(explain_rejection(barrier, metal_object))

    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES)
    helper = args.helper or rng.choice(sorted(HELPERS))
    trait = args.trait or rng.choice(TRAITS)
    place = args.place or rng.choice(sorted(PLACES))

    return StoryParams(
        place=place,
        barrier=barrier,
        metal_object=metal_object,
        name=name,
        gender=gender,
        helper=helper,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    world = simulate(params)
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
        print()
        print("--- world trace ---")
        for e in sample.world.entities.values():
            meters = {k: v for k, v in e.meters.items() if v}
            memes = {k: v for k, v in e.memes.items() if v}
            bits = []
            if meters:
                bits.append(f"meters={meters}")
            if memes:
                bits.append(f"memes={memes}")
            if e.label:
                bits.append(f"label={e.label}")
            print(f"{e.id}: {e.type} {' '.join(bits)}")
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams(place="yard", barrier="fence", metal_object="spoon", name="Maya", gender="girl", helper="parent", trait="curious"),
    StoryParams(place="garden", barrier="hedge", metal_object="bell", name="Leo", gender="boy", helper="neighbor", trait="brave"),
    StoryParams(place="playground", barrier="gate", metal_object="key", name="Nora", gender="girl", helper="friend", trait="silly"),
    StoryParams(place="alley", barrier="rope", metal_object="ladle", name="Finn", gender="boy", helper="grandparent", trait="careful"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show solvable/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        valid = asp_valid_pairs()
        solvable = asp_solvable_pairs()
        print(f"{len(valid)} valid pairs, {len(solvable)} solvable pairs")
        for b, m in valid:
            mark = "yes" if (b, m) in solvable else "no"
            print(f"  {b:8} {m:8} solvable={mark}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
            header = f"### {p.name}: {p.barrier} + {p.metal_object} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
