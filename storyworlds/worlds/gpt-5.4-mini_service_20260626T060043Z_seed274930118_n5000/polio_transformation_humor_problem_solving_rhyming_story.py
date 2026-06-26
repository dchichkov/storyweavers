#!/usr/bin/env python3
"""
storyworlds/worlds/polio_transformation_humor_problem_solving_rhyming_story.py
==============================================================================

A small, self-contained story world for a rhyming, child-facing tale about
polio, transformation, humor, and problem solving.

The world is built around a tiny stage workshop where a paint-glove mishap
turns props into new shapes. The child and a helper must solve the mess with
careful steps, a bit of laughter, and a friendly transformation that brings
everything back into a happy, usable form.

The script supports the standard Storyweavers interface:
- default generation
- -n / --all / --seed / --trace / --qa / --json
- --asp / --verify / --show-asp
"""

from __future__ import annotations

import argparse
import json
import os
import random
import re
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    owner: Optional[str] = None
    carrier: Optional[str] = None
    transformed: bool = False
    broken: bool = False
    repaired: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character" and self.role in {"girl", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.kind == "character" and self.role in {"boy", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def name_or_label(self) -> str:
        return self.label or self.id


@dataclass
class Setting:
    place: str = "the little stage workshop"


@dataclass
class PropSpec:
    id: str
    label: str
    phrase: str
    shape: str
    transformed_shape: str
    rhymes_with: str
    splat: str
    fix: str


@dataclass
class StoryParams:
    place: str
    prop: str
    child_name: str
    child_role: str
    helper_role: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTING = Setting()

PROPS = {
    "hat": PropSpec(
        id="hat",
        label="hat",
        phrase="a bright polka-dot hat",
        shape="round and proud",
        transformed_shape="flat and loud",
        rhymes_with="cat",
        splat="plopped",
        fix="brushed it smooth and neat",
    ),
    "cape": PropSpec(
        id="cape",
        label="cape",
        phrase="a shiny red cape",
        shape="long and breezy",
        transformed_shape="squiggly and sneezy",
        rhymes_with="tape",
        splat="flipped",
        fix="folded it tidy with care",
    ),
    "shoe": PropSpec(
        id="shoe",
        label="shoe",
        phrase="a tiny stage shoe",
        shape="small and snug",
        transformed_shape="wobbly and bug",
        rhymes_with="glue",
        splat="squished",
        fix="popped it back into shape",
    ),
    "mask": PropSpec(
        id="mask",
        label="mask",
        phrase="a smiling paper mask",
        shape="smiling and white",
        transformed_shape="wibbly and bright",
        rhymes_with="task",
        splat="slid",
        fix="smoothed its grin",
    ),
}

CHILD_NAMES = ["Lina", "Milo", "Nora", "Tessa", "Owen", "Pip"]
TRAITS = ["cheery", "curious", "silly", "brave", "gentle", "spry"]


# ---------------------------------------------------------------------------
# World state
# ---------------------------------------------------------------------------
class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.facts: dict[str, object] = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, line: str) -> None:
        if line:
            self.lines.append(line)

    def render(self) -> str:
        return " ".join(self.lines)

    def trace(self) -> str:
        out = ["--- world model state ---"]
        for e in self.entities.values():
            bits = []
            if e.meters:
                bits.append(f"meters={e.meters}")
            if e.memes:
                bits.append(f"memes={e.memes}")
            if e.transformed:
                bits.append("transformed=True")
            if e.broken:
                bits.append("broken=True")
            if e.repaired:
                bits.append("repaired=True")
            out.append(f"  {e.id:10} ({e.kind:9}) {' '.join(bits)}")
        return "\n".join(out)


# ---------------------------------------------------------------------------
# Story engine
# ---------------------------------------------------------------------------
def rhyme_line(a: str, b: str) -> str:
    return f"{a} {b}"


def build_world(params: StoryParams) -> World:
    world = World(SETTING)
    child = world.add(Entity(id=params.child_name, kind="character", role=params.child_role))
    helper = world.add(Entity(id="Helper", kind="character", role=params.helper_role, label="the helper"))
    prop_spec = PROPS[params.prop]
    prop = world.add(Entity(
        id=prop_spec.id,
        kind="thing",
        label=prop_spec.label,
        phrase=prop_spec.phrase,
        owner=child.id,
        carrier=child.id,
    ))
    world.facts.update(child=child, helper=helper, prop=prop, spec=prop_spec, params=params)

    # Setup
    world.say(
        f"At {world.setting.place}, {child.id} had {prop_spec.phrase}, neat and light."
    )
    world.say(
        f"{child.id} loved the little show; the props were just right for rhyme and light."
    )

    # Problem
    world.say(
        f"But on a busy day, a paint-glove went {prop_spec.splat}, then slid with a sight."
    )
    prop.transformed = True
    prop.meters["mess"] = 1.0
    prop.memes["confusion"] = 1.0
    world.say(
        f"Then {prop_spec.label} changed shape in a goofy way, from {prop_spec.shape} to {prop_spec.transformed_shape} tonight."
    )

    # Humor
    world.say(
        f"{child.id} blinked and laughed, 'Oh no-oh!' as it wiggled like jelly in the light."
    )

    # Problem solving
    world.say(
        f"The helper said, 'No big storm. We can fix this in a calm, careful fight.'"
    )
    world.say(
        f"First we wipe, then we fold, then we set it flat, and soon it will feel right."
    )
    prop.broken = False
    prop.repaired = True
    prop.transformed = False
    prop.meters["mess"] = 0.0
    prop.memes["confusion"] = 0.0
    helper.memes["calm"] = 1.0
    child.memes["joy"] = 1.0

    # Resolution
    world.say(
        f"So {child.id} and {helper.label} worked side by side, with a grin and a glue-free glide."
    )
    world.say(
        f"By the end, {prop_spec.label} was {prop_spec.fix}, and {child.id} could go on with pride."
    )
    world.say(
        f"In the glow of the stage, the funny little mess had turned into a show, not a fright."
    )

    return world


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def valid_combo(place: str, prop: str, child_role: str) -> bool:
    return place == SETTING.place and prop in PROPS and child_role in {"girl", "boy"}


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for prop in PROPS:
        for role in ("girl", "boy"):
            if valid_combo(SETTING.place, prop, role):
                out.append((SETTING.place, prop, role))
    return out


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    params: StoryParams = f["params"]  # type: ignore[assignment]
    spec: PropSpec = f["spec"]  # type: ignore[assignment]
    return [
        f'Write a rhyming story for a young child about "{params.child_name}" and a {spec.label} that changes shape.',
        f"Tell a funny story where {params.child_name} solves a small stage problem with help and kindness.",
        f"Write a short rhyming tale that includes polio, a mix-up, and a gentle fix at {params.place}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    params: StoryParams = f["params"]  # type: ignore[assignment]
    spec: PropSpec = f["spec"]  # type: ignore[assignment]
    child: Entity = f["child"]  # type: ignore[assignment]
    helper: Entity = f["helper"]  # type: ignore[assignment]
    return [
        QAItem(
            question=f"What happened to the {spec.label} at first?",
            answer=f"It got splatted by paint and changed from {spec.shape} into {spec.transformed_shape}.",
        ),
        QAItem(
            question=f"How did {params.child_name} feel when the {spec.label} changed?",
            answer=f"{params.child_name} laughed because the shape change was so silly and surprising.",
        ),
        QAItem(
            question=f"How did {params.child_name} and {helper.label} fix the problem?",
            answer=f"They worked slowly and calmly, then brushed, folded, and smoothed the {spec.label} until it was ready again.",
        ),
        QAItem(
            question=f"Why is this story about polio and problem solving?",
            answer="Because the story turns a tricky mix-up into a safe, helpful fix, and the word polio appears in the tale.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a stage workshop?",
            answer="A stage workshop is a place where people make, fix, and try out props for a show.",
        ),
        QAItem(
            question="What does it mean to transform something?",
            answer="To transform something means to change it into a different form or shape.",
        ),
        QAItem(
            question="Why can a funny mistake help a story?",
            answer="A funny mistake can make characters laugh and then work together to solve the problem.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
place_ok(P) :- place(P).
prop_ok(X) :- prop(X).
role_ok(R) :- role(R), R = girl; R = boy.

valid(P, X, R) :- place_ok(P), prop_ok(X), role_ok(R).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    lines.append(asp.fact("place", SETTING.place))
    for pid in PROPS:
        lines.append(asp.fact("prop", pid))
    lines.append(asp.fact("role", "girl"))
    lines.append(asp.fact("role", "boy"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Sampling
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Rhyming story world with polio, humor, and problem solving.")
    ap.add_argument("--place", choices=[SETTING.place])
    ap.add_argument("--prop", choices=sorted(PROPS))
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--trait", choices=TRAITS)
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
    place = args.place or SETTING.place
    prop = args.prop or rng.choice(sorted(PROPS))
    gender = args.gender or rng.choice(["girl", "boy"])
    if args.name:
        name = args.name
    else:
        name = rng.choice(CHILD_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS)
    if args.gender is not None and args.gender not in {"girl", "boy"}:
        raise StoryError("Invalid gender.")
    if args.prop and args.prop not in PROPS:
        raise StoryError("Unknown prop.")
    return StoryParams(place=place, prop=prop, child_name=name, child_role=gender, helper_role=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
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
        print(sample.world.trace())
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible combos:\n")
        for t in triples:
            print("  ", t)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for prop in sorted(PROPS):
            params = StoryParams(
                place=SETTING.place,
                prop=prop,
                child_name=CHILD_NAMES[sorted(PROPS).index(prop) % len(CHILD_NAMES)],
                child_role="girl" if sorted(PROPS).index(prop) % 2 == 0 else "boy",
                helper_role="mother" if sorted(PROPS).index(prop) % 2 == 0 else "father",
                trait=TRAITS[sorted(PROPS).index(prop) % len(TRAITS)],
            )
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
        header = f"### variant {i + 1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
