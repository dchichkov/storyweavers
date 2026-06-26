#!/usr/bin/env python3
"""
storyworlds/worlds/carve_bad_ending_rhyming_story.py
=====================================================

A tiny, standalone story world for a Rhyming Story with a bad ending.
The seed idea is a child who wants to carve something special, but the
choice is too rushed or too rough, and the ending lands on a sad note.

This world keeps the simulation small:
- a child wants to carve a seasonal object
- a grown-up gives a careful warning
- the child ignores the warning and makes a mess
- the story ends with a broken, ruined, or spoiled result

The narrative is rhyming in spirit, with short, child-facing lines and a
clear state-driven turn.
"""

from __future__ import annotations

import argparse
import dataclasses
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
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def reflexive(self) -> str:
        if self.type in {"girl", "mother", "woman"}:
            return "herself"
        if self.type in {"boy", "father", "man"}:
            return "himself"
        return "itself"


@dataclass
class CarveObject:
    id: str
    label: str
    phrase: str
    surface: str
    mess: str
    can_be_ruined: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    object_id: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.trace: list[str] = []

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


OBJECTS: dict[str, CarveObject] = {
    "pumpkin": CarveObject(
        id="pumpkin",
        label="pumpkin",
        phrase="a round orange pumpkin",
        surface="shell",
        mess="squash",
        tags={"fall", "orange", "sharp"},
    ),
    "soap": CarveObject(
        id="soap",
        label="soap",
        phrase="a smooth bar of soap",
        surface="soft soap",
        mess="shavings",
        tags={"bath", "soft", "sharp"},
    ),
    "wood": CarveObject(
        id="wood",
        label="wood",
        phrase="a small piece of wood",
        surface="grain",
        mess="chips",
        tags={"tree", "brown", "sharp"},
    ),
}

GIRL_NAMES = ["Mia", "Lily", "Zoe", "Ava", "Nora", "Ivy", "Ella"]
BOY_NAMES = ["Leo", "Ben", "Max", "Finn", "Noah", "Theo", "Sam"]
TRAITS = ["eager", "curious", "cheery", "bouncy", "stubborn", "brave"]


def rhyme(a: str, b: str) -> str:
    return f"{a} {b}"


def opening_line(child: Entity, obj: CarveObject) -> str:
    return f"{child.id} found {obj.phrase}, a shape to adore."


def love_carving(child: Entity, obj: CarveObject) -> str:
    child.memes["want"] = child.memes.get("want", 0.0) + 1
    return f"{child.pronoun().capitalize()} wanted to carve it, to make it a score."


def warn_line(parent: Entity, obj: CarveObject) -> str:
    parent.memes["worry"] = parent.memes.get("worry", 0.0) + 1
    return f'"Take it slow," {parent.pronoun("subject")} said low, "or you may make a sore."'


def act_carve(world: World, child: Entity, obj: CarveObject) -> None:
    child.meters["carving"] = child.meters.get("carving", 0.0) + 1
    child.memes["excitement"] = child.memes.get("excitement", 0.0) + 1
    if obj.id == "pumpkin":
        child.meters["mess"] = child.meters.get("mess", 0.0) + 1
    elif obj.id == "soap":
        child.meters["slip"] = child.meters.get("slip", 0.0) + 1
    else:
        child.meters["chips"] = child.meters.get("chips", 0.0) + 1


def bad_turn(world: World, child: Entity, parent: Entity, obj: CarveObject) -> str:
    child.memes["defiance"] = child.memes.get("defiance", 0.0) + 1
    child.memes["regret"] = child.memes.get("regret", 0.0) + 1
    obj_bad = obj.label
    if obj.id == "pumpkin":
        world.facts["ruin"] = "the pumpkin split and slumped in the floor"
        return f"{child.id} carved too fast, with a twist and a blast; the pumpkin split wide and could not last."
    if obj.id == "soap":
        world.facts["ruin"] = "the soap grew tiny and slippery, then dropped to the floor"
        return f"{child.id} carved too hard in a slippery wave; the soap slid away and rolled in the cave."
    world.facts["ruin"] = "the wood chipped off in rough little chunks"
    return f"{child.id} carved at the wood with a hurry and scorn; the rough little chips made the neat shape look torn."


def ending_line(child: Entity, parent: Entity, obj: CarveObject) -> str:
    child.memes["sad"] = child.memes.get("sad", 0.0) + 1
    return (
        f"In the end, {child.id} looked down with a frown; "
        f"{obj.label} was ruined, and the room was a mess on the ground."
    )


def tell(params: StoryParams) -> World:
    world = World()

    child_type = params.gender
    child = world.add(Entity(
        id=params.name,
        kind="character",
        type=child_type,
        meters={"mess": 0.0},
        memes={"want": 0.0, "defiance": 0.0, "regret": 0.0, "sad": 0.0},
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=params.parent,
        label="parent",
        memes={"worry": 0.0},
    ))
    obj = OBJECTS[params.object_id]
    world.facts.update(child=child, parent=parent, obj=obj)

    world.say(opening_line(child, obj))
    world.say(love_carving(child, obj))
    world.say(warn_line(parent, obj))
    world.para()

    world.say(f'The {obj.label} sat in the light, all bright and in sight.')
    world.say(f"{child.id} started to carve, with a grin and a swipe.")
    act_carve(world, child, obj)
    world.say(bad_turn(world, child, parent, obj))
    world.para()

    world.say(ending_line(child, parent, obj))
    world.facts["bad_ending"] = True
    return world


def valid_combos() -> list[tuple[str, str]]:
    return [(obj_id, gender) for obj_id in OBJECTS for gender in ("girl", "boy")]


@dataclass
class ASPChoice:
    object_id: str
    gender: str


ASP_RULES = r"""
valid(Object, Gender) :- object(Object), gender(Gender).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for oid in OBJECTS:
        lines.append(asp.fact("object", oid))
    for g in ("girl", "boy"):
        lines.append(asp.fact("gender", g))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple[str, str]]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A short rhyming story with a bad ending about carving.")
    ap.add_argument("--object", dest="object_id", choices=OBJECTS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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
    if args.object_id and args.gender is None:
        pass
    if args.object_id and args.gender and args.object_id not in OBJECTS:
        raise StoryError("Unknown object.")
    if args.gender and args.name is None:
        pass

    combos = valid_combos()
    if args.object_id:
        combos = [c for c in combos if c[0] == args.object_id]
    if args.gender:
        combos = [c for c in combos if c[1] == args.gender]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    object_id, gender = rng.choice(sorted(combos))
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(
        object_id=object_id,
        name=name,
        gender=gender,
        parent=parent,
        trait=trait,
    )


def generation_prompts(world: World) -> list[str]:
    child = world.facts["child"]
    obj = world.facts["obj"]
    parent = world.facts["parent"]
    return [
        f'Write a short rhyming story for a small child about carving {obj.label} and getting a bad ending.',
        f"Tell a simple story where {child.id} wants to carve {obj.phrase}, but {parent.pronoun('subject')} warns {child.pronoun('object')} to slow down.",
        f'Write a child-facing rhyme with the word "carve" and end with a ruined {obj.label}.',
    ]


def story_qa(world: World) -> list[QAItem]:
    child = world.facts["child"]
    parent = world.facts["parent"]
    obj = world.facts["obj"]
    return [
        QAItem(
            question=f"What did {child.id} want to do with the {obj.label}?",
            answer=f"{child.id} wanted to carve the {obj.label} and make it look neat and bright.",
        ),
        QAItem(
            question=f"Why did {parent.pronoun('subject')} warn {child.id}?",
            answer=f"{parent.pronoun('subject').capitalize()} warned {child.id} because carving too fast could ruin the {obj.label} and make a mess.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended badly: the {obj.label} was ruined, and {child.id} felt sad at the end.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    obj = world.facts["obj"]
    items = [
        QAItem(
            question="What does carve mean?",
            answer="To carve means to cut or shape something carefully with a tool or a sharp edge.",
        ),
        QAItem(
            question=f"Why can a {obj.label} be hard to carve?",
            answer=f"A {obj.label} can be hard to carve because its surface can slip, crack, or break if you rush.",
        ),
    ]
    return items


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for p in sample.prompts:
        lines.append(f"- {p}")
    lines.append("")
    lines.append("== Story QA ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={dict(e.meters)}")
        if e.memes:
            bits.append(f"memes={dict(e.memes)}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  facts: {world.facts.get('ruin', '')}")
    return "\n".join(lines)


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
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams(object_id="pumpkin", name="Mia", gender="girl", parent="mother", trait="eager"),
    StoryParams(object_id="soap", name="Leo", gender="boy", parent="father", trait="curious"),
    StoryParams(object_id="wood", name="Nora", gender="girl", parent="mother", trait="stubborn"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} valid combos:")
        for obj_id, gender in asp_valid_combos():
            print(f"  {obj_id} {gender}")
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
