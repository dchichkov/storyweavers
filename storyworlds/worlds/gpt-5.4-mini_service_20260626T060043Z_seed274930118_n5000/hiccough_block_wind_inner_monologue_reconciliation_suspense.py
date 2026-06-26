#!/usr/bin/env python3
"""
Story world: a tiny detective tale with hiccoughs, a blocking object, and wind.

A small, self-contained simulation built from a seed tale:
- a young detective follows clues in a windy place
- a hiccough interrupts thinking at the worst moment
- a block stands in the way of a useful clue
- an inner monologue helps the detective keep going
- suspense rises until a reconciliation with a helper resolves the case

The world is driven by state:
- physical meters: obstacle, wind, clue, progress, comfort
- emotional memes: suspense, doubt, determination, trust, relief

The prose is generated from the simulated state, not from a frozen template.
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

# ---------------------------------------------------------------------------
# Domain registries
# ---------------------------------------------------------------------------

PLACES = {
    "alley": "the narrow alley",
    "dock": "the old dock",
    "garden": "the quiet garden",
    "station": "the empty station platform",
}

BLOCKS = {
    "cart": "a tipped delivery cart",
    "crate": "a wooden crate",
    "fence": "a bent iron fence",
    "bench": "a heavy bench",
}

HELPERS = {
    "friend": "a friend",
    "neighbor": "a neighbor",
    "guard": "a kind guard",
    "seller": "a street seller",
}

# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------

@dataclass
class Entity:
    id: str
    kind: str
    label: str
    phrase: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    owner: Optional[str] = None
    moved: bool = False

    def __post_init__(self) -> None:
        for key in ("obstacle", "wind", "clue", "progress", "comfort"):
            self.meters.setdefault(key, 0.0)
        for key in ("suspense", "doubt", "determination", "trust", "relief"):
            self.memes.setdefault(key, 0.0)


@dataclass
class World:
    place: str
    weather: str
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict[str, object] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)

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
        clone = World(self.place, self.weather)
        clone.entities = dataclasses.deepcopy(self.entities) if hasattr(dataclasses, "deepcopy") else __import__("copy").deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone


# ---------------------------------------------------------------------------
# Story params
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    block: str
    helper: str
    name: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Reasoning helpers
# ---------------------------------------------------------------------------

def validate_params(params: StoryParams) -> None:
    if params.place not in PLACES:
        raise StoryError(f"Unknown place: {params.place}")
    if params.block not in BLOCKS:
        raise StoryError(f"Unknown block: {params.block}")
    if params.helper not in HELPERS:
        raise StoryError(f"Unknown helper: {params.helper}")


def reasonableness_gate(place: str, block: str, helper: str) -> bool:
    return place in PLACES and block in BLOCKS and helper in HELPERS


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for b in BLOCKS:
        lines.append(asp.fact("block", b))
    for h in HELPERS:
        lines.append(asp.fact("helper", h))
    # Compatibility facts: every place has wind, every block can obstruct a clue.
    for p in PLACES:
        lines.append(asp.fact("windy", p))
    for b in BLOCKS:
        lines.append(asp.fact("obstructs", b, "path"))
    for h in HELPERS:
        lines.append(asp.fact("can_reconcile", h))
    return "\n".join(lines)


ASP_RULES = r"""
#show valid/3.

valid(P, B, H) :- place(P), block(B), helper(H), windy(P), obstructs(B, path), can_reconcile(H).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


# ---------------------------------------------------------------------------
# Simulation
# ---------------------------------------------------------------------------

def make_world(params: StoryParams) -> World:
    world = World(place=PLACES[params.place], weather="windy")
    detective = world.add(Entity(id="detective", kind="character", label=params.name))
    helper = world.add(Entity(id="helper", kind="character", label=HELPERS[params.helper]))
    block = world.add(Entity(id="block", kind="thing", label=BLOCKS[params.block]))
    clue = world.add(Entity(id="clue", kind="thing", label="a torn clue card"))

    world.facts.update(
        detective=detective,
        helper=helper,
        block=block,
        clue=clue,
        place=params.place,
        block_kind=params.block,
        helper_kind=params.helper,
    )
    return world


def setup(world: World) -> None:
    det = world.get("detective")
    helper = world.get("helper")
    block = world.get("block")
    clue = world.get("clue")

    det.memes["determination"] += 1
    det.memes["suspense"] += 1
    block.meters["obstacle"] += 1
    clue.meters["clue"] += 1
    world.say(
        f"{det.label} was a little detective in {world.place}, where the wind kept sliding between the walls."
    )
    world.say(
        f"One day, {det.label} found a clue card, but {block.label} sat in the path like a stubborn question."
    )
    world.say(
        f"{helper.label} came along just in time, because the case already felt full of suspense."
    )


def wind_event(world: World) -> None:
    det = world.get("detective")
    block = world.get("block")
    clue = world.get("clue")

    if ("wind", "stirs") in world.fired:
        return
    world.fired.add(("wind", "stirs"))
    det.memes["suspense"] += 1
    clue.meters["wind"] += 1
    world.say(
        f"The wind worried at the clue card and tried to flip it away from view."
    )
    world.say(
        f"{det.label} narrowed {det.label.lower() == det.label and 'their' or 'their'} eyes and wondered what the card was hiding."
    )


def hiccough_event(world: World) -> None:
    det = world.get("detective")
    if det.memes["doubt"] > 0:
        return
    det.memes["doubt"] += 1
    det.memes["suspense"] += 1
    world.say(
        f"Then {det.label} gave a sudden hiccough, so small and sharp that it broke the thought in two."
    )
    world.say(
        f"{det.label} had to pause and listen to the own heartbeat before the answer could come back."
    )


def inner_monologue(world: World) -> None:
    det = world.get("detective")
    if ("inner", "monologue") in world.fired:
        return
    world.fired.add(("inner", "monologue"))
    det.memes["determination"] += 1
    det.memes["doubt"] = max(0.0, det.memes["doubt"] - 0.5)
    world.say(
        f"In {det.label}'s head, a quiet voice said, 'Slow down. Look at the wind, the block, and the clue. The answer is still here.'"
    )
    world.say(
        f"That private pep talk steadied {det.label} like a lantern in a dark hallway."
    )


def inspect_block(world: World) -> None:
    det = world.get("detective")
    block = world.get("block")
    if block.meters["obstacle"] < 1:
        return
    det.memes["suspense"] += 1
    world.say(
        f"{det.label} crouched beside {block.label} and noticed a scuff mark pointing past it."
    )


def reconciliation(world: World) -> None:
    det = world.get("detective")
    helper = world.get("helper")
    block = world.get("block")
    clue = world.get("clue")

    if ("reconcile", "done") in world.fired:
        return
    world.fired.add(("reconcile", "done"))
    helper.memes["trust"] += 1
    det.memes["trust"] += 1
    det.memes["relief"] += 1
    det.memes["suspense"] = max(0.0, det.memes["suspense"] - 1.5)
    block.moved = True
    block.meters["obstacle"] = 0
    clue.meters["progress"] += 1
    world.say(
        f"At last {helper.label} smiled and said they had seen the same thing from the other side."
    )
    world.say(
        f"{det.label} nodded, and the two of them agreed to move the block together."
    )
    world.say(
        f"Once the path opened, the clue card stopped shivering in the wind, and the case made sense at once."
    )


def resolve_case(world: World) -> None:
    det = world.get("detective")
    helper = world.get("helper")
    clue = world.get("clue")
    det.memes["relief"] += 1
    det.memes["determination"] += 1
    clue.meters["clue"] += 1
    world.say(
        f"{det.label} read the clue again and saw that it pointed straight to the missing mitten under the bench."
    )
    world.say(
        f"The answer had been there all along, and now {det.label} and {helper.label} could laugh about the windy mystery."
    )


def tell(params: StoryParams) -> World:
    validate_params(params)
    world = make_world(params)
    setup(world)
    world.para()
    wind_event(world)
    hiccough_event(world)
    inspect_block(world)
    inner_monologue(world)
    world.para()
    reconciliation(world)
    resolve_case(world)
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    p = world.facts
    return [
        f"Write a short detective story for children set in {world.place} with a hiccough, a block, and wind.",
        f"Tell a suspenseful but gentle story about {p['detective'].label} and {p['helper'].label} solving a clue in the wind.",
        "Write a small mystery where an inner monologue helps a detective and reconciliation clears the way.",
    ]


def story_qa(world: World) -> list[QAItem]:
    d = world.get("detective")
    h = world.get("helper")
    b = world.get("block")
    q: list[QAItem] = [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about {d.label}, a little detective in {world.place}, and the helpful {h.label} who came along during the mystery.",
        ),
        QAItem(
            question=f"What made the clue hard to read?",
            answer=f"The wind kept worrying at the clue card, and {b.label} blocked the path so the detective had to stop and think.",
        ),
        QAItem(
            question="Why did the detective pause in the middle of the case?",
            answer=f"A sudden hiccough broke the detective's thoughts, so there was a quiet moment before the answer could be found.",
        ),
        QAItem(
            question="How did the detective keep going?",
            answer="The detective used a quiet inner monologue to slow down, notice the details, and keep the case from feeling too scary.",
        ),
        QAItem(
            question="How was the problem solved?",
            answer=f"{d.label} and {h.label} reached a reconciliation, moved the block together, and found that the clue led straight to the missing mitten.",
        ),
    ]
    return q


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does wind do?",
            answer="Wind is moving air. It can push light things around, like paper or leaves.",
        ),
        QAItem(
            question="What is a hiccough?",
            answer="A hiccough is a quick little jump in your breathing that can make you make a small sudden sound.",
        ),
        QAItem(
            question="What is a block?",
            answer="A block is something that can stand in the way and stop you from moving forward easily.",
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
        meters = {k: round(v, 2) for k, v in e.meters.items() if v}
        memes = {k: round(v, 2) for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.moved:
            bits.append("moved=True")
        lines.append(f"  {e.id:10} ({e.kind:9}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP verification
# ---------------------------------------------------------------------------

def asp_verify() -> int:
    import asp
    py = {(p, b, h) for p in PLACES for b in BLOCKS for h in HELPERS if reasonableness_gate(p, b, h)}
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP gate matches Python gate ({len(py)} combos).")
        return 0
    print("MISMATCH between ASP and Python gates:")
    print("python only:", sorted(py - cl))
    print("asp only:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Storyworld interface
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Detective story world with hiccoughs, blocks, and wind.")
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--block", choices=sorted(BLOCKS))
    ap.add_argument("--helper", choices=sorted(HELPERS))
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
    place = args.place or rng.choice(list(PLACES))
    block = args.block or rng.choice(list(BLOCKS))
    helper = args.helper or rng.choice(list(HELPERS))
    if not reasonableness_gate(place, block, helper):
        raise StoryError("The requested combination cannot form a reasonable detective story.")
    name = args.name or rng.choice(["Mina", "Toby", "June", "Eli", "Nia"])
    return StoryParams(place=place, block=block, helper=helper, name=name)


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
    StoryParams(place="alley", block="cart", helper="friend", name="Mina"),
    StoryParams(place="dock", block="crate", helper="guard", name="Toby"),
    StoryParams(place="garden", block="bench", helper="neighbor", name="June"),
    StoryParams(place="station", block="fence", helper="seller", name="Eli"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for p, b, h in combos:
            print(f"  {p:8} {b:8} {h:8}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        for p in CURATED:
            samples.append(generate(p))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            rng = random.Random(seed)
            try:
                params = resolve_params(args, rng)
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
            header = f"### {p.name}: {p.place} / {p.block} / {p.helper}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
