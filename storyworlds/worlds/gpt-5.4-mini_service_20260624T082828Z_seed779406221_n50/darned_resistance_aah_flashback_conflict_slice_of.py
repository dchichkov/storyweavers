#!/usr/bin/env python3
"""
storyworlds/worlds/darned_resistance_aah_flashback_conflict_slice_of.py
=======================================================================

A small slice-of-life story world about a child facing a tiny household
problem: a stubborn lid, a little frustration, a flashback to useful advice,
and a calm resolution.

Seed-tale inspiration:
---
A child wants to open a stubborn jar. The lid has a lot of resistance, and the
child gets frustrated and says, "Darned lid!" A parent remembers a past moment
when a rubber grip helped, so they suggest using one. The child tries again,
the lid gives way, and they both say, "Aah!" in relief.
"""

from __future__ import annotations

import argparse
import copy
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
    protective: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class ItemSpec:
    label: str
    phrase: str
    resistance: float
    helps: str


@dataclass
class Setting:
    place: str = "the kitchen table"


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.trace: list[str] = []

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)
            self.trace.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.paragraphs = [[]]
        c.fired = set(self.fired)
        return c


@dataclass
class StoryParams:
    child: str
    gender: str
    parent: str
    item: str
    seed: Optional[int] = None


SETTINGS = {
    "kitchen": Setting("the kitchen table"),
}

CHILDREN = {
    "Mia": "girl",
    "Noah": "boy",
    "Luna": "girl",
    "Eli": "boy",
    "Ivy": "girl",
    "Theo": "boy",
}

PARENTS = ["mother", "father"]

ITEMS = {
    "jar": ItemSpec(
        label="jar",
        phrase="a small jar of strawberry jam",
        resistance=2.0,
        helps="rubber grip",
    ),
    "bottle": ItemSpec(
        label="bottle",
        phrase="a tight water bottle cap",
        resistance=1.8,
        helps="tea towel",
    ),
    "box": ItemSpec(
        label="box",
        phrase="a taped cereal box",
        resistance=1.4,
        helps="thumb tab",
    ),
}

FLASHBACK = {
    "jar": "last week, when the same rubber grip helped open a pickle jar",
    "bottle": "yesterday, when a tea towel made a slippery lid easier to hold",
    "box": "the afternoon before, when a thumb tab stopped a box from tearing",
}

TOOLS = {
    "jar": "rubber grip",
    "bottle": "tea towel",
    "box": "thumb tab",
}

ASP_RULES = r"""
problem(Item) :- item(Item), resistance(Item, R), R > 1.
has_fix(Item) :- item(Item), tool_for(Item, Tool), useful(Tool).
compatible(Item) :- problem(Item), has_fix(Item).
"""


def asp_facts() -> str:
    import asp
    lines = [asp.fact("setting", "kitchen")]
    for item_id, spec in ITEMS.items():
        lines.append(asp.fact("item", item_id))
        lines.append(asp.fact("resistance", item_id, int(spec.resistance * 10)))
        lines.append(asp.fact("tool_for", item_id, TOOLS[item_id]))
        lines.append(asp.fact("useful", TOOLS[item_id]))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show compatible/1."))
    clingo_items = sorted(set(asp.atoms(model, "compatible")))
    python_items = sorted([(k,) for k, v in ITEMS.items() if v.resistance > 1 and TOOLS.get(k)])
    if clingo_items == python_items:
        print(f"OK: clingo gate matches Python gate ({len(clingo_items)} items).")
        return 0
    print("MISMATCH")
    print("clingo:", clingo_items)
    print("python:", python_items)
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life story world: a stubborn lid, a flashback, and a gentle fix.")
    ap.add_argument("--child", choices=sorted(CHILDREN))
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=PARENTS)
    ap.add_argument("--item", choices=sorted(ITEMS))
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


def valid_combo(child: str, gender: str, item: str) -> bool:
    return CHILDREN[child] == gender and item in ITEMS


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    choices = []
    for child, gender in CHILDREN.items():
        if args.child and child != args.child:
            continue
        if args.gender and gender != args.gender:
            continue
        for item in ITEMS:
            if args.item and item != args.item:
                continue
            choices.append((child, gender, item))
    if not choices:
        raise StoryError("(No valid combination matches the given options.)")
    child, gender, item = rng.choice(sorted(choices))
    parent = args.parent or rng.choice(PARENTS)
    return StoryParams(child=child, gender=gender, parent=parent, item=item)


def _do_try(world: World, child: Entity, item: Entity, narrate: bool = True) -> None:
    spec = ITEMS[item.id]
    child.meters["effort"] = child.meters.get("effort", 0) + 1
    if item.meters.get("open", 0) >= THRESHOLD:
        return
    item.meters["resistance"] = item.meters.get("resistance", 0) + spec.resistance
    child.memes["frustration"] = child.memes.get("frustration", 0) + 1
    if narrate:
        world.say(f"{child.id} tried to turn the {item.label} lid, but it still had too much resistance.")


def predict_open(world: World, child: Entity, item: Entity) -> bool:
    sim = world.copy()
    _do_try(sim, sim.get(child.id), sim.get(item.id), narrate=False)
    return sim.get(item.id).meters.get("resistance", 0) >= ITEMS[item.id].resistance


def tell(params: StoryParams) -> World:
    w = World(SETTINGS["kitchen"])
    child = w.add(Entity(id=params.child, kind="character", type=params.gender, label=params.child))
    parent = w.add(Entity(id=params.parent, kind="character", type=params.parent, label=f"the {params.parent}"))
    item_spec = ITEMS[params.item]
    item = w.add(Entity(id=params.item, label=item_spec.label, phrase=item_spec.phrase, caretaker=parent.id))
    w.facts.update(child=child, parent=parent, item=item, spec=item_spec, flashback=FLASHBACK[params.item], tool=TOOLS[params.item])

    w.say(f"{child.id} was at {w.setting.place}, looking at {item.phrase}.")
    w.say(f"{child.id} wanted to open it right away and said, 'Darned {item.label}.'")
    w.para()
    w.say(f"The lid had a lot of resistance, and {child.id} could feel it twist without moving.")
    w.say(f"{parent.label.capitalize()} noticed the worry on {child.id}'s face and remembered {FLASHBACK[params.item]}.")
    if predict_open(w, child, item):
        w.say(f"{parent.label.capitalize()} found a {TOOLS[params.item]} and said, 'Let's use this.'")
        w.say(f"{child.id} pressed harder with the {TOOLS[params.item]}, and the lid finally gave way.")
        item.meters["open"] = 1
        child.memes["frustration"] = 0
        child.memes["relief"] = 1
        w.para()
        w.say(f"Aah, the {item.label} opened at last, and the kitchen felt calm again.")
    else:
        raise StoryError("(No story: this item does not have a believable fix.)")
    w.facts["resolved"] = True
    return w


def generate_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short slice-of-life story for a child named {f["child"].id} about a stubborn {f["item"].label} lid.',
        f"Tell a gentle story where {f['child'].id} says 'darned' once, remembers a helpful flashback, and solves the problem with {f['tool']}.",
        f'Write a simple family story that includes the word "resistance" and ends with "aah".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, parent, item = f["child"], f["parent"], f["item"]
    tool = f["tool"]
    return [
        QAItem(
            question=f"What was {child.id} trying to open in {world.setting.place}?",
            answer=f"{child.id} was trying to open {item.phrase}. The lid was stubborn, so it took patience and help.",
        ),
        QAItem(
            question=f"Why did {parent.label} remember something from the past?",
            answer=f"{parent.label.capitalize()} remembered {f['flashback']} because that old idea could help with the same kind of problem again.",
        ),
        QAItem(
            question=f"How did {child.id} and {parent.label} solve the problem with the lid?",
            answer=f"They used a {tool} to get better grip, and then the {item.label} opened instead of staying stuck.",
        ),
        QAItem(
            question=f"How did {child.id} feel when the {item.label} finally opened?",
            answer=f"{child.id} felt relieved and said, 'Aah.' The tension in the kitchen melted away.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does resistance mean?",
            answer="Resistance is a force that pushes back and makes something harder to move or turn.",
        ),
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is a short look back at something that happened earlier, so the reader learns why a character remembers it now.",
        ),
        QAItem(
            question="Why can a rubber grip help with a lid?",
            answer="A rubber grip helps because rubber is less slippery, so your hand can hold on better and turn the lid.",
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
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generate_prompts(world),
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


def asp_valid_items() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show compatible/1."))
    return sorted(set(asp.atoms(model, "compatible")))


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show compatible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_items())} compatible items:\n")
        for (item,) in asp_valid_items():
            print(f"  {item}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams(child="Mia", gender="girl", parent="mother", item="jar"),
            StoryParams(child="Noah", gender="boy", parent="father", item="bottle"),
            StoryParams(child="Ivy", gender="girl", parent="mother", item="box"),
        ]
        samples = [generate(p) for p in curated]
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
            header = f"### {p.child}: {p.item}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
