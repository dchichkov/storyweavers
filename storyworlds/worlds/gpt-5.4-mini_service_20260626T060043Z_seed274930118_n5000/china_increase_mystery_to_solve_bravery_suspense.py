#!/usr/bin/env python3
"""
A standalone story world about a bedtime mystery with a brave child and a
delicate china keepsake.

The premise:
- A child notices that something made of china keeps changing in a puzzling way.
- Small clues increase over the evening.
- A little bravery, plus a careful search, solves the mystery before bedtime.

The world model:
- Physical meters track clue strength, carefulness, and whether objects are safe.
- Emotional memes track worry, bravery, suspense, relief, and trust.
- State changes drive the story instead of a fixed paragraph with swapped names.

Supported story shape:
- beginning: a cozy bedtime setup
- middle: suspense grows as clues increase
- turn: the child acts bravely and follows a clue trail
- ending: the mystery is solved and the world becomes calm again
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
# World constants
# ---------------------------------------------------------------------------
THRESHOLD = 1.0
CHILD_NAMES = ["Maya", "Theo", "Nina", "Sam", "Lila", "Noah", "Ivy", "Ben"]
ADULT_NAMES = ["Mom", "Dad", "Aunt June", "Grandma", "Uncle Ray"]
TRAITS = ["gentle", "curious", "quiet", "brave", "careful", "sleepy"]
ROOMS = ["kitchen", "hall", "library", "porch", "bedroom"]
CHINA_ITEMS = {
    "teacup": "a tiny china teacup with blue flowers",
    "plate": "a round china plate with a gold rim",
    "bowl": "a shallow china bowl with painted birds",
}
CLUES = ["soft clink", "tiny footprint", "missing shine", "sliver of ribbon", "warm light"]

# ---------------------------------------------------------------------------
# Entity model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    room: str = ""
    fragile: bool = False
    found: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for k in ("clue", "care", "safe", "search", "quiet"):
            self.meters.setdefault(k, 0.0)
        for k in ("worry", "bravery", "suspense", "relief", "trust"):
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character" and self.type in {"girl", "child"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.kind == "character" and self.type in {"boy"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class World:
    setting: str
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
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

# ---------------------------------------------------------------------------
# Params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    china_item: str
    name: str
    adult: str
    trait: str
    seed: Optional[int] = None

# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def valid_choice(place: str, china_item: str) -> bool:
    return place in ROOMS and china_item in CHINA_ITEMS

def explain_rejection(place: str, china_item: str) -> str:
    return f"(No story: I don't know a china mystery for {china_item!r} in {place!r}.)"

# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
#show valid/2.
#show story/3.

valid(P, C) :- room(P), china(C).
story(P, C, brave) :- valid(P, C), mystery(P, C), solved(P, C).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for r in ROOMS:
        lines.append(asp.fact("room", r))
    for c in CHINA_ITEMS:
        lines.append(asp.fact("china", c))
        lines.append(asp.fact("mystery", "bedtime", c))
    return "\n".join(lines)

def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"

def asp_valid() -> set[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return set(asp.atoms(model, "valid"))

# ---------------------------------------------------------------------------
# Simulation
# ---------------------------------------------------------------------------
def _increase_suspense(world: World, child: Entity, china: Entity) -> None:
    child.memes["suspense"] += 1
    child.meters["clue"] += 1
    china.meters["care"] += 1
    world.say(
        f"At bedtime, {child.id} noticed something odd about {china.label}. "
        f"One clue became another, and the mystery felt a little bigger."
    )

def _hear_clue(world: World, child: Entity, clue: str) -> None:
    child.meters["search"] += 1
    child.memes["worry"] += 0.5
    world.say(f"{child.id} heard a {clue} from the dark hall and looked more carefully.")

def _be_brave(world: World, child: Entity) -> None:
    child.memes["bravery"] += 1
    child.memes["suspense"] += 0.5
    world.say(f"{child.id} took a small brave breath and stepped forward anyway.")

def _solve(world: World, child: Entity, adult: Entity, china: Entity) -> None:
    child.memes["relief"] += 1.5
    child.memes["trust"] += 1
    china.found = True
    china.room = "kitchen"
    world.say(
        f"Together, {child.id} and {adult.id} found the missing {china.label}. "
        f"It had been safe all along, tucked where warm light could reach it."
    )
    world.say(
        f"The suspense melted into relief, and {child.id} smiled as the little china piece "
        f"shone softly in the night."
    )

def tell(setting: str, china_key: str, child_name: str, adult_name: str, trait: str) -> World:
    world = World(setting=setting)
    child = world.add(Entity(id=child_name, kind="character", type="child"))
    adult = world.add(Entity(id=adult_name, kind="character", type="adult"))
    china = world.add(Entity(
        id="china",
        kind="thing",
        type="china",
        label=china_key,
        phrase=CHINA_ITEMS[china_key],
        room=setting,
        fragile=True,
    ))

    world.say(
        f"{child.id} was a {trait} little child who loved bedtime stories and soft lamps."
    )
    world.say(
        f"One night, {child.id} noticed {china.phrase} was not where it should be."
    )
    world.say(
        f"That made the room feel quiet in a strange way, and the mystery began to grow."
    )

    world.para()
    _increase_suspense(world, child, china)
    _hear_clue(world, child, random.choice(CLUES))
    _hear_clue(world, child, random.choice(CLUES))

    world.para()
    world.say(
        f"{adult.id} listened carefully and said the clues might lead somewhere hidden."
    )
    _be_brave(world, child)
    _hear_clue(world, child, random.choice(CLUES))

    world.para()
    _solve(world, child, adult, china)
    world.say(
        f"After that, {child.id} felt sleepy again, and the house seemed peaceful and kind."
    )

    world.facts.update(
        child=child,
        adult=adult,
        china=china,
        setting=setting,
        solved=china.found,
    )
    return world

# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a bedtime story about a small mystery that slowly becomes clearer.',
        f"Tell a gentle story where {f['child'].id} notices a missing {f['china'].label} and stays brave.",
        f"Write a suspenseful but cozy story with clues that increase until the mystery is solved.",
    ]

def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = f["child"]
    adult: Entity = f["adult"]
    china: Entity = f["china"]
    return [
        QAItem(
            question=f"What was the mystery in the story?",
            answer=(
                f"The mystery was where the {china.label} went and why the room felt so strange. "
                f"{child.id} noticed the clues and helped solve it."
            ),
        ),
        QAItem(
            question=f"How did {child.id} show bravery?",
            answer=(
                f"{child.id} showed bravery by taking a small brave breath, stepping into the hall, "
                f"and following the clues instead of hiding from the suspense."
            ),
        ),
        QAItem(
            question=f"What happened at the end of the story?",
            answer=(
                f"The missing {china.label} was found safely, the mystery was solved, and "
                f"{child.id} felt sleepy and relieved again."
            ),
        ),
    ]

def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is china in a house?",
            answer=(
                "China is a delicate kind of dishware or pottery. People handle it carefully "
                "because it can crack or break if it is dropped."
            ),
        ),
        QAItem(
            question="What does increase mean?",
            answer=(
                "Increase means to become larger or more. A sound, a number, or a feeling can all increase."
            ),
        ),
        QAItem(
            question="What is bravery?",
            answer=(
                "Bravery is feeling afraid but still doing the careful thing that needs to be done."
            ),
        ),
        QAItem(
            question="What is suspense?",
            answer=(
                "Suspense is the tense feeling you get when you want to know what will happen next."
            ),
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
# ASP helpers
# ---------------------------------------------------------------------------
def asp_verify() -> int:
    py = {(p, c) for p in ROOMS for c in CHINA_ITEMS}
    cl = asp_valid()
    if py == cl:
        print(f"OK: clingo gate matches valid choices ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    print("only in python:", sorted(py - cl))
    print("only in clingo:", sorted(cl - py))
    return 1

# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------
def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(ROOMS)
    china_item = args.china_item or rng.choice(list(CHINA_ITEMS))
    if not valid_choice(place, china_item):
        raise StoryError(explain_rejection(place, china_item))
    name = args.name or rng.choice(CHILD_NAMES)
    adult = args.adult or rng.choice(ADULT_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, china_item=china_item, name=name, adult=adult, trait=trait)

def generate(params: StoryParams) -> StorySample:
    world = tell(params.place, params.china_item, params.name, params.adult, params.trait)
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
        if e.room:
            bits.append(f"room={e.room}")
        if e.fragile:
            bits.append("fragile=True")
        if e.found:
            bits.append("found=True")
        lines.append(f"  {e.id:8} ({e.kind:9}) {' '.join(bits)}")
    return "\n".join(lines)

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime mystery storyworld with china, increase, bravery, and suspense.")
    ap.add_argument("--place", choices=ROOMS)
    ap.add_argument("--china-item", choices=list(CHINA_ITEMS))
    ap.add_argument("--name")
    ap.add_argument("--adult", choices=ADULT_NAMES)
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

CURATED = [
    StoryParams(place="kitchen", china_item="teacup", name="Maya", adult="Mom", trait="curious"),
    StoryParams(place="library", china_item="plate", name="Theo", adult="Grandma", trait="careful"),
    StoryParams(place="porch", china_item="bowl", name="Lila", adult="Aunt June", trait="brave"),
]

def asp_show_program() -> str:
    return asp_program("#show valid/2.\n#show story/3.")

def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_show_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid/2."))
        triples = sorted(set(asp.atoms(model, "valid")))
        print(f"{len(triples)} valid (place, china_item) combos:")
        for t in triples:
            print("  ", t)
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
            header = f"### {p.name}: {p.china_item} in the {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")

if __name__ == "__main__":
    main()
