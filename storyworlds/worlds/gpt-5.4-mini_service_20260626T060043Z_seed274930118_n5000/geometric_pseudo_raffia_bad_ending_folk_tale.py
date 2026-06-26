#!/usr/bin/env python3
"""
storyworlds/worlds/geometric_pseudo_raffia_bad_ending_folk_tale.py
===================================================================

A small folk-tale storyworld about geometric patterns, pseudo raffia, and a
bad ending that comes from trusting the wrong material.

Seed tale:
---
In a little village, a clever child wanted to weave a beautiful mat with a
geometric pattern for the spring feast. The child found a bundle of pseudo
raffia that looked bright and fine, but the old weaver warned that it was only
a fake mimic and would not hold strong. The child insisted anyway, because the
pattern looked perfect in the morning light.

The child worked all day, but when the wind rose that evening, the fake fibers
snapped and the mat came apart. The feast hall stayed bare, and the child had
to watch the ruined pieces blow into the dark.
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
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "grandmother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "grandfather"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the village yard"


@dataclass
class Material:
    id: str
    label: str
    phrase: str
    kind: str
    flexible: bool
    strong: bool
    pattern: str
    risk: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Gear:
    id: str
    label: str
    phrase: str
    guards: set[str]
    helps: set[str]


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[str] = set()

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
SETTINGS = {
    "village": Setting(place="the village yard"),
    "barn": Setting(place="the old barn"),
    "hall": Setting(place="the feast hall"),
}

MATERIALS = {
    "pseudo_raffia": Material(
        id="pseudo_raffia",
        label="pseudo raffia",
        phrase="a bright bundle of pseudo raffia",
        kind="fiber",
        flexible=True,
        strong=False,
        pattern="geometric",
        risk="snapped apart",
        tags={"geometric", "pseudo", "raffia"},
    ),
    "raffia": Material(
        id="raffia",
        label="raffia",
        phrase="a real bundle of raffia",
        kind="fiber",
        flexible=True,
        strong=True,
        pattern="geometric",
        risk="held firm",
        tags={"geometric", "raffia"},
    ),
}

GEAR = [
    Gear(
        id="loom",
        label="a wooden loom",
        phrase="a sturdy wooden loom",
        guards={"geometric"},
        helps={"raffia"},
    ),
    Gear(
        id="needle",
        label="a bone needle",
        phrase="a smooth bone needle",
        guards={"raffia"},
        helps={"geometric"},
    ),
]

NAMES = ["Mira", "Niko", "Lina", "Tavi", "Anya", "Bela"]
ELDER_NAMES = ["Grandmother", "Old Mara", "Aunt Sela", "Grandfather Orin"]
TRAITS = ["clever", "small", "bright-eyed", "patient", "stubborn"]


# ---------------------------------------------------------------------------
# Params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str = "village"
    material: str = "pseudo_raffia"
    name: str = "Mira"
    elder: str = "Grandmother"
    trait: str = "clever"
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for place in SETTINGS:
        for material in MATERIALS:
            if material == "pseudo_raffia":
                combos.append((place, material))
    return combos


def explain_rejection(material: Material) -> str:
    return (
        f"(No story: the tale needs a fragile, deceptive material, so {material.label} "
        f"isn't the right seed here.)"
    )


def build_story(params: StoryParams) -> World:
    world = World(SETTINGS[params.place])
    child = world.add(Entity(id=params.name, kind="character", type="girl"))
    elder = world.add(Entity(id="elder", kind="character", type="grandmother", label=params.elder))
    mat = world.add(Entity(
        id="mat",
        type=MATERIALS[params.material].kind,
        label=MATERIALS[params.material].label,
        phrase=MATERIALS[params.material].phrase,
        owner=child.id,
        caretaker=elder.id,
    ))
    world.facts.update(child=child, elder=elder, mat=mat, material=MATERIALS[params.material])
    return world


def tell(world: World) -> None:
    f = world.facts
    child: Entity = f["child"]
    elder: Entity = f["elder"]
    mat: Entity = f["mat"]
    material: Material = f["material"]

    world.say(
        f"{child.id} was a {params_trait(child)} child who loved straight lines and bright corners."
    )
    world.say(
        f"{child.id} dreamed of making a {material.pattern} mat for the spring feast."
    )
    world.say(
        f"At the edge of {world.setting.place}, {child.id} found {material.phrase}, and {elder.label} frowned."
    )

    world.para()
    world.say(
        f'"That is only pseudo raffia," {elder.label} warned. "It looks fine, but it will not stay strong."'
    )
    world.say(
        f'{"But" if True else ""} {child.id} tied the fibers anyway, chasing every neat angle of the pattern.'
    )
    child.memes["want"] = 1
    child.memes["stubborn"] = 1
    mat.meters["made"] = 1

    world.para()
    world.say(
        f"All afternoon the mat grew wider, with little diamonds and squares marching across it."
    )
    world.say(
        f"Then the evening wind came across {world.setting.place}, and the weak fibers gave way."
    )
    mat.meters["broken"] = 1
    mat.memes["ruined"] = 1
    child.memes["loss"] = 1
    elder.memes["worry"] = 1

    world.para()
    world.say(
        f"The mat split in the middle, {material.risk}, and the pieces spun into the dusk."
    )
    world.say(
        f"{child.id} stood in silence while {elder.label} gathered the scraps, and the feast hall stayed bare."
    )
    world.say(
        f"In the end, the geometric dream was only a flutter of broken pseudo raffia on the dark ground."
    )


def params_trait(child: Entity) -> str:
    return "small and stubborn"


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a short folk tale about a child, a geometric craft, and a bad ending using the words "geometric", "pseudo", and "raffia".',
        f"Tell a simple village story where {f['child'].id} tries to make a geometric mat from pseudo raffia and learns too late that it is weak.",
        "Write a child-friendly folk tale ending sadly after a fake fiber craft comes apart in the wind.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = f["child"]
    elder: Entity = f["elder"]
    material: Material = f["material"]
    return [
        QAItem(
            question=f"What did {child.id} want to make?",
            answer="The child wanted to make a geometric mat for the spring feast.",
        ),
        QAItem(
            question=f"What did {elder.label} warn about?",
            answer=f"{elder.label} warned that the bundle was only pseudo raffia and would not stay strong.",
        ),
        QAItem(
            question="What happened when the wind came?",
            answer=f"The weak fibers snapped, the mat split apart, and the pieces blew into the dusk.",
        ),
        QAItem(
            question="How did the story end?",
            answer="It ended badly, with the feast hall still bare and the ruined mat gone to the dark ground.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is raffia?",
            answer="Raffia is a plant fiber that people can weave into mats, baskets, and other hand-made things.",
        ),
        QAItem(
            question="What does geometric mean?",
            answer="Geometric means made of shapes like squares, triangles, circles, and straight lines.",
        ),
        QAItem(
            question="What does pseudo mean?",
            answer="Pseudo means fake or not quite real, like something that only looks right on the outside.",
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
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A story is valid when a place and a fake-but-tasty-looking fiber choice exist.
fragile_material(pseudo_raffia).
valid_story(Place, Material) :- setting(Place), fragile_material(Material).
"""

def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for m in MATERIALS:
        lines.append(asp.fact("material", m))
    lines.append(asp.fact("fragile_material", "pseudo_raffia"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches Python ({len(py)} combos).")
        return 0
    print("MISMATCH between ASP and Python:")
    print("  only in python:", sorted(py - cl))
    print("  only in ASP:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Core API
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Folk tale world about geometric pseudo raffia and a bad ending.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--material", choices=MATERIALS)
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--elder", choices=ELDER_NAMES)
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
    if args.material and args.material != "pseudo_raffia":
        raise StoryError(explain_rejection(MATERIALS[args.material]))
    combos = valid_combos()
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.material:
        combos = [c for c in combos if c[1] == args.material]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, material = rng.choice(sorted(combos))
    return StoryParams(
        place=place,
        material=material,
        name=args.name or rng.choice(NAMES),
        elder=args.elder or rng.choice(ELDER_NAMES),
        trait=args.trait or rng.choice(TRAITS),
    )


def generate(params: StoryParams) -> StorySample:
    world = build_story(params)
    tell(world)
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
    StoryParams(place="village", material="pseudo_raffia", name="Mira", elder="Grandmother", trait="clever"),
    StoryParams(place="barn", material="pseudo_raffia", name="Niko", elder="Old Mara", trait="stubborn"),
    StoryParams(place="hall", material="pseudo_raffia", name="Lina", elder="Aunt Sela", trait="patient"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible stories:")
        for combo in combos:
            print(" ", combo)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            i += 1
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
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
            header = f"### {p.name} in {p.place} with {p.material}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
