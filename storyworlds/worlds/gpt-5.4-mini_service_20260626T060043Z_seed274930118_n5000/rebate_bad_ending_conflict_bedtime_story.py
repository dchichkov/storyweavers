#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/rebate_bad_ending_conflict_bedtime_story.py
==============================================================================================================

A small bedtime story world about a child, a promised rebate, and a conflict
that does not get fixed in time.

Seed idea:
- A child and a parent stay up a little too late trying to claim a rebate.
- They discover that one important paper is missing.
- The child wants the rebate badly, but the night gets sleepy and the ending
  stays bad: the rebate is not received, and the child falls asleep disappointed.

This script is self-contained and follows the shared storyworld contract.
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
    plural: bool = False
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

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the kitchen table"
    bedtime: bool = True
    quiet: bool = True


@dataclass
class RebateKit:
    id: str
    brand: str
    item: str
    amount: str
    missing_piece: str
    denial_reason: str
    deadline: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.lines: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[tuple] = set()

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.lines[-1].append(text)

    def para(self) -> None:
        if self.lines[-1]:
            self.lines.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.lines if p)

    def copy(self) -> "World":
        import copy as _copy

        w = World(self.setting)
        w.entities = _copy.deepcopy(self.entities)
        w.lines = [[]]
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        return w


# ---------------------------------------------------------------------------
# Story parameters and registries
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    name: str
    gender: str
    parent: str
    brand: str
    item: str
    amount: str
    missing_piece: str
    seed: Optional[int] = None


NAMES = {
    "girl": ["Mia", "Nora", "Lily", "Ava", "Zoe"],
    "boy": ["Leo", "Ben", "Finn", "Theo", "Max"],
}
PARENTS = ["mother", "father"]
AMOUNTS = ["five dollars", "twelve dollars", "twenty dollars", "a small refund"]
BRANDS = ["moonlight", "cozyhome", "snugglebug", "starsoft"]
ITEMS = ["nightlight", "pillow", "blanket", "pajamas"]
MISSING_PIECES = [
    ("receipt", "the store wanted the receipt, and without it the rebate could not be sent"),
    ("stamp", "the envelope needed a stamp, and without it the form could not go anywhere"),
    ("barcode", "the form needed the barcode cut from the box, and without it the claim could not be read"),
]

SETTING = Setting(place="the kitchen table", bedtime=True, quiet=True)


def build_kit(brand: str, item: str, amount: str, missing_piece: str) -> RebateKit:
    reason = dict(MISSING_PIECES)[missing_piece]
    return RebateKit(
        id="rebate-kit",
        brand=brand,
        item=item,
        amount=amount,
        missing_piece=missing_piece,
        denial_reason=reason,
        deadline="before bedtime",
    )


# ---------------------------------------------------------------------------
# World simulation
# ---------------------------------------------------------------------------

def _do_search(world: World, child: Entity, parent: Entity, kit: RebateKit) -> None:
    child.memes["hope"] += 1
    world.say(
        f"At the kitchen table, {child.id} and {parent.pronoun('possessive')} {parent.type} "
        f"spread out the {kit.brand} box and the rebate form."
    )
    world.say(
        f"{child.id} wanted the {kit.amount} rebate because it would help pay for the {kit.item}."
    )


def _check_papers(world: World, child: Entity, parent: Entity, kit: RebateKit) -> None:
    child.memes["worry"] += 1
    parent.memes["worry"] += 1
    world.say(
        f"They checked every paper twice, but the {kit.missing_piece} was still missing."
    )
    world.say(
        f"{parent.pronoun().capitalize()} tapped the form and said, "
        f'"We need {kit.missing_piece} for this rebate."'
    )


def _conflict(world: World, child: Entity, parent: Entity, kit: RebateKit) -> None:
    child.memes["conflict"] += 1
    child.memes["sadness"] += 1
    world.say(
        f"{child.id} frowned and held the paper tighter. "
        f'"But I want the rebate now," {child.pronoun()} said.'
    )
    world.say(
        f"{parent.pronoun().capitalize()} tried to explain that the claim could not be sent "
        f"without {kit.missing_piece}."
    )


def _bad_ending(world: World, child: Entity, parent: Entity, kit: RebateKit) -> None:
    child.memes["tired"] += 1
    parent.memes["tired"] += 1
    world.say(
        f"The clock got late, the room got sleepy, and the rebate form stayed on the table."
    )
    world.say(
        f"In the end, there was no rebate to count that night, and {child.id} fell asleep "
        f"with a disappointed sigh while {parent.pronoun('possessive')} {parent.type} "
        f"folded the unanswered papers away."
    )


def tell_story(params: StoryParams) -> World:
    world = World(SETTING)
    kit = build_kit(params.brand, params.item, params.amount, params.missing_piece)

    child = world.add(
        Entity(
            id=params.name,
            kind="character",
            type=params.gender,
            meters={},
            memes={"hope": 0.0, "worry": 0.0, "conflict": 0.0, "sadness": 0.0, "tired": 0.0},
        )
    )
    parent = world.add(
        Entity(
            id="Parent",
            kind="character",
            type=params.parent,
            label="parent",
            meters={},
            memes={"worry": 0.0, "tired": 0.0},
        )
    )

    world.facts.update(child=child, parent=parent, kit=kit, params=params)

    _do_search(world, child, parent, kit)
    world.para()
    _check_papers(world, child, parent, kit)
    _conflict(world, child, parent, kit)
    world.para()
    _bad_ending(world, child, parent, kit)

    return world


# ---------------------------------------------------------------------------
# Story QA and world QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    kit = f["kit"]
    return [
        f'Write a gentle bedtime story about a child named {child.id} who wants a {kit.amount} rebate.',
        f"Tell a short story where {child.id} and a {child.pronoun('possessive')} {f['parent'].type} look for a missing {kit.missing_piece} before bedtime.",
        f'Write a bedtime story with the word "rebate" that ends in disappointment rather than a fix.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    kit = f["kit"]

    return [
        QAItem(
            question=f"What was {child.id} hoping to get from the {kit.brand} rebate?",
            answer=f"{child.id} was hoping to get {kit.amount} back so the family could help pay for the {kit.item}.",
        ),
        QAItem(
            question=f"Why couldn't they send the rebate form?",
            answer=f"They could not send it because the {kit.missing_piece} was missing, and the claim needed that paper first.",
        ),
        QAItem(
            question=f"How did {child.id} feel when the rebate could not be finished?",
            answer=f"{child.id} felt upset and disappointed, and the feeling grew into a bedtime conflict with {parent.id}.",
        ),
        QAItem(
            question=f"What happened by the end of the story?",
            answer=f"The papers stayed on the table, there was no rebate that night, and {child.id} fell asleep feeling sad.",
        ),
    ]


KNOWLEDGE = {
    "rebate": [
        QAItem(
            question="What is a rebate?",
            answer="A rebate is money you can get back after you buy something, if you follow the rules and send in the right form.",
        )
    ],
    "receipt": [
        QAItem(
            question="What is a receipt?",
            answer="A receipt is a paper that shows what you bought and how much you paid.",
        )
    ],
    "stamp": [
        QAItem(
            question="What is a stamp for?",
            answer="A stamp helps mail travel through the post so the letter can be delivered.",
        )
    ],
    "barcode": [
        QAItem(
            question="What is a barcode?",
            answer="A barcode is a set of lines and spaces that a store or machine can read to find the right item.",
        )
    ],
    "bedtime": [
        QAItem(
            question="Why do kids get sleepy at bedtime?",
            answer="Kids get sleepy at bedtime because their bodies and brains are ready to rest after a long day.",
        )
    ],
}


def world_qa(world: World) -> list[QAItem]:
    f = world.facts
    kit = f["kit"]
    out = [QAItem(question=q.question, answer=q.answer) for q in KNOWLEDGE["rebate"]]
    out.extend(QAItem(question=q.question, answer=q.answer) for q in KNOWLEDGE[kit.missing_piece])
    out.extend(QAItem(question=q.question, answer=q.answer) for q in KNOWLEDGE["bedtime"])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
rebate_possible(B, I, M) :- brand(B), item(I), missing(M), can_end_badly(B, I, M).
conflict_story(B, I, M) :- rebate_possible(B, I, M).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for b in BRANDS:
        lines.append(asp.fact("brand", b))
    for i in ITEMS:
        lines.append(asp.fact("item", i))
    for m, _reason in MISSING_PIECES:
        lines.append(asp.fact("missing", m))
    for b in BRANDS:
        for i in ITEMS:
            for m, _reason in MISSING_PIECES:
                lines.append(asp.fact("can_end_badly", b, i, m))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_combos() -> list[tuple[str, str, str]]:
    import asp
    model = asp.one_model(asp_program("#show rebate_possible/3."))
    return sorted(set(asp.atoms(model, "rebate_possible")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and Python valid_combos()")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Validation and generation
# ---------------------------------------------------------------------------

def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for b in BRANDS:
        for i in ITEMS:
            for m, _reason in MISSING_PIECES:
                combos.append((b, i, m))
    return combos


def explain_rejection() -> str:
    return "(No story: this world always has a rebate problem, so the bad ending stays consistent.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A bedtime story world about a rebate, conflict, and a bad ending.")
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=PARENTS)
    ap.add_argument("--brand", choices=BRANDS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--amount", choices=AMOUNTS)
    ap.add_argument("--missing-piece", choices=[m for m, _ in MISSING_PIECES])
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
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES[gender])
    parent = args.parent or rng.choice(PARENTS)
    brand = args.brand or rng.choice(BRANDS)
    item = args.item or rng.choice(ITEMS)
    amount = args.amount or rng.choice(AMOUNTS)
    missing_piece = args.missing_piece or rng.choice([m for m, _ in MISSING_PIECES])
    return StoryParams(
        name=name,
        gender=gender,
        parent=parent,
        brand=brand,
        item=item,
        amount=amount,
        missing_piece=missing_piece,
    )


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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show rebate_possible/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_combos()
        print(f"{len(combos)} compatible rebate story combos:\n")
        for b, i, m in combos:
            print(f"  {b:10} {i:10} {m}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        curated = [
            StoryParams("Mia", "girl", "mother", "moonlight", "nightlight", "five dollars", "receipt"),
            StoryParams("Leo", "boy", "father", "cozyhome", "blanket", "twelve dollars", "stamp"),
            StoryParams("Nora", "girl", "mother", "snugglebug", "pajamas", "twenty dollars", "barcode"),
        ]
        samples = [generate(p) for p in curated]
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: rebate story with {p.brand}, {p.item}, missing {p.missing_piece}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
