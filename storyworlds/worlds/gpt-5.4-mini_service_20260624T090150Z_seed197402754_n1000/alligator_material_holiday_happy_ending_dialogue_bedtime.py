#!/usr/bin/env python3
"""
Standalone storyworld: an alligator, a special material, and a holiday bedtime.

Premise:
A child wants a cozy bedtime comfort item for a holiday night. A friendly alligator
helps pick the right material, but the first choice is too scratchy or too stiff.
The story turns when they try a softer material and make something gentle and warm.
The ending image proves the change: calm bedtime, happy holiday, and a snug finish.

This world is intentionally small, classical, and state-driven. It includes:
- typed entities with physical meters and emotional memes
- a reasonableness gate for valid story combinations
- inline ASP rules mirroring the Python logic
- dialogue and a happy ending in a bedtime-story tone
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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    worn_by: Optional[str] = None
    material: str = ""

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"child", "boy", "girl"}:
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        if self.type == "alligator":
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        if self.type == "parent":
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Material:
    id: str
    label: str
    phrase: str
    soft: bool
    warm: bool
    quiet: bool
    bedtime_ok: bool


@dataclass
class Holiday:
    id: str
    label: str
    clue: str
    cozy: bool = True


@dataclass
class StoryParams:
    material: str
    holiday: str
    child_name: str
    seed: Optional[int] = None


class World:
    def __init__(self, holiday: Holiday) -> None:
        self.holiday = holiday
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
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

    def copy(self) -> "World":
        import copy as _copy

        clone = World(self.holiday)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

MATERIALS = {
    "paper": Material(
        id="paper",
        label="paper",
        phrase="a shiny sheet of paper",
        soft=False,
        warm=False,
        quiet=False,
        bedtime_ok=False,
    ),
    "felt": Material(
        id="felt",
        label="felt",
        phrase="a soft piece of felt",
        soft=True,
        warm=True,
        quiet=True,
        bedtime_ok=True,
    ),
    "cotton": Material(
        id="cotton",
        label="cotton",
        phrase="a cozy cotton cloth",
        soft=True,
        warm=True,
        quiet=True,
        bedtime_ok=True,
    ),
    "silk": Material(
        id="silk",
        label="silk",
        phrase="a smooth silk ribbon",
        soft=True,
        warm=False,
        quiet=True,
        bedtime_ok=False,
    ),
    "wood": Material(
        id="wood",
        label="wood",
        phrase="a stiff little board",
        soft=False,
        warm=False,
        quiet=False,
        bedtime_ok=False,
    ),
}

HOLIDAYS = {
    "birthday": Holiday(id="birthday", label="birthday", clue="birthday candles"),
    "winter_holiday": Holiday(id="winter_holiday", label="winter holiday", clue="holiday lights"),
    "sleepy_holiday": Holiday(id="sleepy_holiday", label="holiday", clue="a special bedtime song"),
}

CHILD_NAMES = ["Mila", "Noah", "Ivy", "Leo", "Maya", "Eli"]


# ---------------------------------------------------------------------------
# Narrative helpers
# ---------------------------------------------------------------------------

def material_is_reasonable(material: Material) -> bool:
    return material.soft and material.warm and material.quiet and material.bedtime_ok


def valid_combos() -> list[tuple[str, str]]:
    return [(hid, mid) for hid, h in HOLIDAYS.items() for mid, m in MATERIALS.items() if material_is_reasonable(m)]


def choose_material(material_id: str) -> Material:
    if material_id not in MATERIALS:
        raise StoryError(f"Unknown material: {material_id}")
    return MATERIALS[material_id]


def choose_holiday(holiday_id: str) -> Holiday:
    if holiday_id not in HOLIDAYS:
        raise StoryError(f"Unknown holiday: {holiday_id}")
    return HOLIDAYS[holiday_id]


def tell(world: World, child_name: str, material: Material) -> World:
    child = world.add(Entity(id=child_name, kind="character", type="child", label=child_name))
    alligator = world.add(Entity(id="Gus", kind="character", type="alligator", label="Gus"))
    parent = world.add(Entity(id="Parent", kind="character", type="parent", label="Mom"))

    blanket = world.add(
        Entity(
            id="blanket",
            kind="thing",
            type="blanket",
            label="blanket",
            phrase=f"a bedtime blanket made from {material.phrase}",
            owner=child.id,
            caretaker=parent.id,
            material=material.id,
        )
    )

    child.memes["sleepy"] = 0.0
    child.memes["hope"] = 0.0
    child.memes["worry"] = 0.0
    child.memes["joy"] = 0.0
    alligator.memes["helpful"] = 0.0
    alligator.memes["pride"] = 0.0
    blanket.meters["softness"] = 1.0 if material.soft else 0.0
    blanket.meters["warmth"] = 1.0 if material.warm else 0.0

    world.say(f"On a quiet {world.holiday.label} evening, {child.id} was sleepy and wanted a cozy bedtime blanket.")
    world.say(f'"Can we make one tonight?" {child.id} asked. "Yes," said Mom, "if we choose the right material."')
    world.say(f'Gus the alligator peered over the table. "I can help," he said. "I know a little about building soft things."')

    # Tension: first choice may be wrong.
    world.para()
    child.memes["hope"] += 1
    world.say(f"{child.id} picked up the {material.label} and whispered, \"Is this good for bedtime?\"")
    if material.soft:
        world.say(f'"It feels nice," said Gus. "Soft things are gentle at night."')
    else:
        child.memes["worry"] += 1
        world.say(f'"Hmm," said Mom. "This one is too rough and too loud for sleepy ears."')
        world.say(f'Gus nodded. "It would not be a cozy bedtime friend."')

    # Turn: if not reasonable, switch to a better material.
    if not material_is_reasonable(material):
        good = MATERIALS["felt"]
        blanket.material = good.id
        blanket.phrase = f"a bedtime blanket made from {good.phrase}"
        blanket.meters["softness"] = 1.0
        blanket.meters["warmth"] = 1.0
        child.memes["worry"] = 0.0
        child.memes["hope"] += 1
        alligator.memes["helpful"] += 1
        world.para()
        world.say(f'"Then let us try felt," said Gus. "It is soft, warm, and quiet."')
        world.say(f'{child.id} touched the felt and smiled. "That feels right," they said.')
        world.say(f"Mom stitched the edges while Gus held the blanket still with careful claws.")

    # Resolution.
    world.para()
    child.memes["joy"] += 1
    child.memes["sleepy"] += 1
    alligator.memes["pride"] += 1
    world.say(f'At bedtime, {child.id} curled up under the blanket and yawned. "Thank you, Gus," they said.')
    world.say(f'"You helped make it cozy," said Mom. Gus smiled and whispered, "Happy {world.holiday.label} night."')
    world.say(f'By the time the moon looked in the window, {child.id} was asleep, the blanket was soft and warm, and everyone was smiling.')

    world.facts.update(
        child=child,
        alligator=alligator,
        parent=parent,
        blanket=blanket,
        material=material,
        holiday=world.holiday,
        resolved=material_is_reasonable(material),
    )
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    material = f["material"]
    holiday = f["holiday"]
    return [
        f'Write a gentle bedtime story for a child named {child.id} that includes the word "{material.label}".',
        f"Tell a holiday story where a friendly alligator helps make something cozy for bedtime.",
        f"Write a short story about choosing a material for a blanket on a {holiday.label} night, with dialogue and a happy ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, alligator, blanket, material, holiday = f["child"], f["alligator"], f["blanket"], f["material"], f["holiday"]
    return [
        QAItem(
            question=f"What did {child.id} want to make on the {holiday.label} night?",
            answer=f"{child.id} wanted to make a cozy bedtime blanket for the {holiday.label} night.",
        ),
        QAItem(
            question="Who helped choose the material?",
            answer=f"Gus the alligator helped choose the material and keep the blanket-making calm.",
        ),
        QAItem(
            question=f"Which material did the story end with?",
            answer=f"The story ended with {material.label}, which made the blanket soft, warm, and quiet.",
        ),
        QAItem(
            question=f"How did {child.id} feel at the end?",
            answer=f"{child.id} felt happy and sleepy, and fell asleep under the cozy blanket.",
        ),
        QAItem(
            question=f"What proved the story had a happy ending?",
            answer=f"At the end, the blanket was soft and warm, {child.id} was asleep, and everyone was smiling.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    out = [
        QAItem(
            question="What is felt like?",
            answer="Felt is a soft fabric that feels gentle and can be good for cozy things.",
        ),
        QAItem(
            question="Why do people like cozy blankets at bedtime?",
            answer="Cozy blankets help bodies feel warm and safe, which can make it easier to fall asleep.",
        ),
        QAItem(
            question="What is a holiday?",
            answer="A holiday is a special day people celebrate in a different and happy way.",
        ),
        QAItem(
            question="Can alligators be friendly in stories?",
            answer="Yes. In stories, alligators can be kind helpers, especially when the story wants a gentle surprise.",
        ),
    ]
    return out


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


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
soft_material(M) :- material(M), soft(M), warm(M), quiet(M), bedtime_ok(M).
valid_combo(H, M) :- holiday(H), soft_material(M).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for hid, h in HOLIDAYS.items():
        lines.append(asp.fact("holiday", hid))
        if h.cozy:
            lines.append(asp.fact("cozy_holiday", hid))
    for mid, m in MATERIALS.items():
        lines.append(asp.fact("material", mid))
        if m.soft:
            lines.append(asp.fact("soft", mid))
        if m.warm:
            lines.append(asp.fact("warm", mid))
        if m.quiet:
            lines.append(asp.fact("quiet", mid))
        if m.bedtime_ok:
            lines.append(asp.fact("bedtime_ok", mid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple[str, str]]:
    import asp

    model = asp.one_model(asp_program("#show valid_combo/2."))
    return sorted(set(asp.atoms(model, "valid_combo")))


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
# Generation
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A bedtime storyworld with an alligator, material, and a holiday.")
    ap.add_argument("--material", choices=MATERIALS)
    ap.add_argument("--holiday", choices=HOLIDAYS)
    ap.add_argument("--name", dest="child_name", choices=CHILD_NAMES)
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
    mats = [m for m in MATERIALS if MATERIALS[m].bedtime_ok]
    holidays = list(HOLIDAYS)

    material_id = args.material or rng.choice(mats)
    holiday_id = args.holiday or rng.choice(holidays)
    material = choose_material(material_id)

    if not material_is_reasonable(material):
        raise StoryError("The chosen material is not gentle enough for a bedtime story.")

    child_name = args.child_name or rng.choice(CHILD_NAMES)
    return StoryParams(material=material_id, holiday=holiday_id, child_name=child_name)


def generate(params: StoryParams) -> StorySample:
    holiday = choose_holiday(params.holiday)
    material = choose_material(params.material)
    world = World(holiday)
    world = tell(world, params.child_name, material)
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
        if e.material:
            bits.append(f"material={e.material}")
        lines.append(f"  {e.id:8} ({e.type:9}) {' '.join(bits)}")
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


CURATED = [
    StoryParams(material="felt", holiday="winter_holiday", child_name="Mila"),
    StoryParams(material="cotton", holiday="sleepy_holiday", child_name="Noah"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_combo/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp

        combos = asp_valid_combos()
        print(f"{len(combos)} compatible holiday-material combos:\n")
        for holiday, material in combos:
            print(f"  {holiday:16} {material}")
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
            header = f"### {p.child_name}: {p.material} on {p.holiday}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
