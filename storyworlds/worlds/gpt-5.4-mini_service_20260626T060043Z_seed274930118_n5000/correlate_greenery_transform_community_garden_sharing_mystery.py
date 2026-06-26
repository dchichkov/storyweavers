#!/usr/bin/env python3
"""
storyworlds/worlds/correlate_greenery_transform_community_garden_sharing_mystery.py
===================================================================================

A standalone storyworld about a small community garden mystery:
children and grown-ups notice clues, share tools, and transform a patch
of tired greenery into a thriving bed.

Seed tale premise:
---
In a community garden, a child notices that the green leaves on one bed
look different from the others. The child and a neighbor start to correlate
the clues: muddy footprints, a missing watering can, and a pile of torn twine.
They share what they know, follow the signs, and discover the real cause.
By working together, they transform the garden patch into something healthier
and happier than before.
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
    kind: str = "thing"  # "character" | "thing" | "place"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    shared_with: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        for k in ("dryness", "greenery", "loss", "order", "water", "trust", "curiosity", "joy", "worry"):
            self.meters.setdefault(k, 0.0)
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Bed:
    id: str
    name: str
    greenery: float
    dryness: float
    clue: str
    cause: str
    transform: str
    needs_share: str


@dataclass
class Tool:
    id: str
    label: str
    helps: set[str]
    shared: bool = True


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.bed: Optional[Bed] = None
        self.tool: Optional[Tool] = None

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


@dataclass
class StoryParams:
    child_name: str
    helper_name: str
    bed: str
    seed: Optional[int] = None


BEDS = {
    "basil": Bed(
        id="basil",
        name="the basil bed",
        greenery=0.45,
        dryness=0.75,
        clue="its leaves curled at the edges",
        cause="the watering can had been moved away",
        transform="the basil stood up bright and glossy again",
        needs_share="a shared watering plan",
    ),
    "beans": Bed(
        id="beans",
        name="the bean trellis bed",
        greenery=0.40,
        dryness=0.70,
        clue="a few vines had snapped loose from the twine",
        cause="someone had borrowed the twine cutter and forgotten to bring it back",
        transform="the bean vines climbed neatly again",
        needs_share="shared twine and careful hands",
    ),
    "lettuce": Bed(
        id="lettuce",
        name="the lettuce patch",
        greenery=0.38,
        dryness=0.80,
        clue="the leaves looked dull instead of crisp",
        cause="the shade cloth had been folded away after lunch",
        transform="the lettuce looked fresh and ruffled once more",
        needs_share="a shared turn with the shade cloth",
    ),
}

TOOLS = {
    "watering_can": Tool(id="watering_can", label="the blue watering can", helps={"water"}),
    "twine": Tool(id="twine", label="the twine spool", helps={"tie"}),
    "shade_cloth": Tool(id="shade_cloth", label="the green shade cloth", helps={"shade"}),
}

NAMES = ["Maya", "Nina", "Leo", "Iris", "Owen", "Zoe", "Ari", "Milo", "Mina", "Theo"]
HELPERS = ["Mrs. Park", "Mr. Reed", "Sam", "June", "Tara", "Ben"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Community-garden mystery about sharing and transformation.")
    ap.add_argument("--child-name", choices=NAMES)
    ap.add_argument("--helper-name", choices=HELPERS)
    ap.add_argument("--bed", choices=BEDS)
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
    bed = args.bed or rng.choice(list(BEDS))
    return StoryParams(
        child_name=args.child_name or rng.choice(NAMES),
        helper_name=args.helper_name or rng.choice(HELPERS),
        bed=bed,
    )


def _share_tool(world: World, child: Entity, helper: Entity, tool: Tool) -> None:
    child.shared_with.add(helper.id)
    helper.shared_with.add(child.id)
    child.memes["trust"] += 1
    helper.memes["trust"] += 1
    world.say(f"{child.id} and {helper.id} shared {tool.label} so neither of them had to guess alone.")


def _investigate(world: World, child: Entity, helper: Entity, bed: Bed, tool: Tool) -> None:
    child.memes["curiosity"] += 1
    helper.memes["curiosity"] += 1
    world.say(
        f"In the community garden, {child.id} noticed that {bed.clue}. "
        f"{child.id} and {helper.id} started to correlate the clues: the footprints, the empty hook, and the dusty path."
    )
    world.say(
        f"They walked slowly around the bed, sharing {tool.label}, and the little mystery began to make sense."
    )


def _solve(world: World, child: Entity, helper: Entity, bed: Bed, tool: Tool) -> None:
    child.memes["worry"] = max(0.0, child.memes["worry"] - 1)
    helper.memes["worry"] = max(0.0, helper.memes["worry"] - 1)
    child.memes["joy"] += 1
    helper.memes["joy"] += 1
    world.facts["solved"] = True
    world.say(
        f"They found that {bed.cause}. Once they put it back and used {tool.label}, the bed could breathe again."
    )
    world.say(
        f"After that, the garden began to transform: {bed.transform}, and the whole row looked more alive."
    )


def tell(params: StoryParams) -> World:
    if params.bed not in BEDS:
        raise StoryError("Unknown bed choice.")
    world = World()
    bed = BEDS[params.bed]
    world.bed = bed
    tool = TOOLS["watering_can"] if bed.id == "basil" else TOOLS["twine"] if bed.id == "beans" else TOOLS["shade_cloth"]
    world.tool = tool

    child = world.add(Entity(id=params.child_name, kind="character", type="child", traits=["curious", "kind"]))
    helper = world.add(Entity(id=params.helper_name, kind="character", type="adult", traits=["helpful", "patient"]))
    bed_ent = world.add(Entity(id=f"bed_{bed.id}", kind="place", type="garden_bed", label=bed.name, phrase=bed.name))
    bed_ent.meters["greenery"] = bed.greenery
    bed_ent.meters["dryness"] = bed.dryness

    world.say(
        f"{child.id} liked the community garden because the greenery there was never exactly the same twice."
    )
    world.say(
        f"One morning, {child.id} saw that {bed.name} looked different, and {child.id}'s curiosity felt as big as the whole fence."
    )
    world.para()
    _investigate(world, child, helper, bed, tool)
    world.say(
        f"{helper.id} said that a good mystery gets easier when people share what they know instead of keeping it hidden."
    )
    _share_tool(world, child, helper, tool)
    world.para()
    _solve(world, child, helper, bed, tool)
    world.say(
        f"By afternoon, {child.id} could point at the healthy leaves and remember how sharing helped them transform the problem into a better day."
    )

    world.facts.update(child=child, helper=helper, bed=bed, tool=tool, bed_ent=bed_ent)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    bed: Bed = f["bed"]
    return [
        f'Write a short mystery story for young children set in a community garden, using the word "correlate".',
        f"Tell a gentle story about {f['child'].id} and {f['helper'].id} sharing a garden tool to solve a clue about {bed.name}.",
        f'Write a child-friendly story where greenery changes, clues are correlated, and the garden can transform after people share the right tool.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = f["child"]
    helper: Entity = f["helper"]
    bed: Bed = f["bed"]
    tool: Tool = f["tool"]
    return [
        QAItem(
            question=f"What kind of place was the story set in?",
            answer="It was set in a community garden, where people worked together among the plants and paths.",
        ),
        QAItem(
            question=f"What did {child.id} and {helper.id} do with the clues?",
            answer=f"They tried to correlate the clues and see which small problem explained why {bed.name} looked wrong.",
        ),
        QAItem(
            question=f"What did they share while solving the mystery?",
            answer=f"They shared {tool.label} so they could fix the bed together instead of one person doing everything alone.",
        ),
        QAItem(
            question=f"What changed after they solved the problem?",
            answer=f"The tired bed began to transform, and {bed.transform}.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does greenery mean?",
            answer="Greenery means the green plants, leaves, and growing things in a place like a garden.",
        ),
        QAItem(
            question="What does it mean to share something?",
            answer="To share means to let other people use, hold, or enjoy something too.",
        ),
        QAItem(
            question="What does transform mean?",
            answer="To transform means to change into something different, often in a big and noticeable way.",
        ),
        QAItem(
            question="What is a mystery?",
            answer="A mystery is something puzzling that people need clues to understand.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Story questions =="]
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(
            f"  {e.id}: kind={e.kind} type={e.type} meters={{{', '.join(f'{k}: {v}' for k, v in e.meters.items() if v)}}} "
            f"memes={{{', '.join(f'{k}: {v}' for k, v in e.memes.items() if v)}}}"
        )
    return "\n".join(lines)


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for bid, bed in BEDS.items():
        lines.append(asp.fact("bed", bid))
        lines.append(asp.fact("greenery", bid, int(bed.greenery * 100)))
        lines.append(asp.fact("dryness", bid, int(bed.dryness * 100)))
    for tid, tool in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        for h in tool.helps:
            lines.append(asp.fact("helps", tid, h))
    lines.append(asp.fact("theme", "sharing"))
    lines.append(asp.fact("style", "mystery"))
    return "\n".join(lines)


ASP_RULES = r"""
#show valid_bed/1.
#show shared_fix/2.
valid_bed(B) :- bed(B), greenery(B,_).
shared_fix(B,T) :- bed(B), tool(T), helps(T,_).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_beds() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_bed/1."))
    return sorted(set(asp.atoms(model, "valid_bed")))


def asp_verify() -> int:
    py = sorted((bid,) for bid in BEDS)
    clingo = asp_valid_beds()
    if py == clingo:
        print(f"OK: clingo gate matches Python registry ({len(py)} beds).")
        return 0
    print("MISMATCH between clingo and Python:")
    print("python:", py)
    print("clingo:", clingo)
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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


CURATED = [
    StoryParams(child_name="Maya", helper_name="Mrs. Park", bed="basil"),
    StoryParams(child_name="Leo", helper_name="Sam", bed="beans"),
    StoryParams(child_name="Iris", helper_name="June", bed="lettuce"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_bed/1.\n#show shared_fix/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show valid_bed/1.\n#show shared_fix/2."))
        print(f"{len(asp.atoms(model, 'valid_bed'))} beds; {len(asp.atoms(model, 'shared_fix'))} shared fixes")
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
