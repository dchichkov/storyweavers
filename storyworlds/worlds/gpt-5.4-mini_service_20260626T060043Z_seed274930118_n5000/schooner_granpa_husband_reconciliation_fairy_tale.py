#!/usr/bin/env python3
"""
storyworlds/worlds/schooner_granpa_husband_reconciliation_fairy_tale.py
========================================================================

A tiny fairy-tale story world about a schooner, a granpa, and a husband who
must reconcile before they can sail together again.

The seed image is simple:
- A granpa keeps an old schooner by the harbor.
- His daughter's husband helps care for it, but the two men have had a quarrel.
- A small trouble on the boat gives them a reason to talk, mend, and forgive.
- In the end, they sail again with warm hearts and the schooner shining.

The world model tracks:
- physical meters: hull_firmness, rope_tangle, sail_health, lantern_brightness
- emotional memes: hurt, pride, worry, trust, relief, love, resolve

Story shape:
- Setup: the schooner and the strained relationship.
- Tension: a problem on the boat makes distance costly.
- Turn: one man chooses a humble repair and an honest apology.
- Resolution: reconciliation restores trust and the schooner becomes seaworthy again.
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

ASP_RULES = r"""
% A reconciliation is reasonable if both men have hurt, but the apology and
% repair make trust rise enough to end the quarrel.
needs_repair(B) :- boat(B), rope_tangle(B), sail_low(B).
can_mend(B) :- boat(B), needs_repair(B), has_line(B), has_patch(B).

conflict(H, G) :- person(H), person(G), hurt(H,G), pride(H), hurt(G,H).
reconcile(H, G) :- conflict(H, G), apologize(H, G), can_mend(boat1), trust_up(H,G), trust_up(G,H).

% The story is valid only when the schooner is at risk and a fair repair exists.
valid_story :- boat1, needs_repair(boat1), can_mend(boat1).
"""

# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.id in {"Granpa"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.id in {"Husband"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the harbor"
    sky: str = "golden dawn"


@dataclass
class StoryParams:
    place: str = "the harbor"
    seed: Optional[int] = None


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
# Story logic
# ---------------------------------------------------------------------------
def build_world(params: StoryParams) -> World:
    world = World(Setting(place=params.place))
    granpa = world.add(Entity(id="Granpa", kind="character", label="granpa"))
    husband = world.add(Entity(id="Husband", kind="character", label="husband"))
    schooner = world.add(Entity(
        id="Schooner",
        kind="thing",
        label="schooner",
        phrase="an old white schooner with a blue sail",
        owner="Granpa",
        meters={"hull_firmness": 2.0, "rope_tangle": 1.0, "sail_health": 1.0, "lantern_brightness": 1.0},
    ))

    granpa.memes.update(hurt=1.0, pride=1.0, worry=1.0, trust=0.5, love=1.0)
    husband.memes.update(hurt=1.0, pride=1.0, worry=1.0, trust=0.5, love=1.0)
    schooner.meters["rope_tangle"] = 1.0
    schooner.meters["sail_health"] = 1.0

    # Act 1
    world.say(
        f"Once upon a time, at {world.setting.place}, there stood an old schooner named the Moonwake."
    )
    world.say(
        f"Granpa kept her polished and proud, and his husband helped mend her ropes, "
        f"but the two of them had been stiff with hurt for many days."
    )
    world.say(
        f"They still loved the schooner, yet each one waited for the other to speak first."
    )

    # Act 2
    world.para()
    world.say(
        f"One misty morning, a hard gust worried the schooner's sail and knotted a line tight."
    )
    schooner.meters["rope_tangle"] += 1.0
    schooner.meters["sail_health"] -= 0.5
    granpa.memes["worry"] += 1.0
    husband.memes["worry"] += 1.0
    world.say(
        f"That meant the Moonwake could not sail until someone climbed aboard with a steady hand."
    )
    world.say(
        f"Granpa frowned at the knot, and husband looked away, for both still carried old hurt."
    )

    # Turn: apology and repair
    world.para()
    husband.memes["resolve"] = 1.0
    husband.memes["pride"] = 0.0
    granpa.memes["resolve"] = 1.0
    world.say(
        f"Then husband took a deep breath, touched the rail, and said, "
        f'"Granpa, I was wrong to leave you feeling alone. Will you let me help?"'
    )
    world.say(
        f"Granpa's eyes softened like candlelight. He set aside his pride and answered, "
        f'"I was wrong too. Come, let us mend the Moonwake together."'
    )
    world.say(
        f"Husband cut a fresh line, Granpa held the lantern, and together they loosened the knot."
    )
    schooner.meters["rope_tangle"] = 0.0
    schooner.meters["sail_health"] = 2.0
    schooner.meters["hull_firmness"] = 2.5
    granpa.memes["hurt"] = 0.0
    husband.memes["hurt"] = 0.0
    granpa.memes["trust"] = 2.0
    husband.memes["trust"] = 2.0
    granpa.memes["love"] += 1.0
    husband.memes["love"] += 1.0
    granpa.memes["relief"] = 1.0
    husband.memes["relief"] = 1.0

    # Resolution
    world.para()
    world.say(
        f"When the line was smooth again, the sail filled sweetly and the Moonwake glowed in the morning."
    )
    world.say(
        f"Granpa and husband laughed together, and their old quarrel drifted away like fog."
    )
    world.say(
        f"By sunset, the schooner was ready, and the two men sailed side by side with warm hearts."
    )

    world.facts.update(
        granpa=granpa,
        husband=husband,
        schooner=schooner,
        place=world.setting.place,
        reconciled=True,
        repaired=True,
    )
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    return [
        "Write a fairy tale about a schooner, a granpa, and a husband who forgive one another.",
        "Tell a gentle story where a broken boat gives two family members a reason to reconcile.",
        "Write a short story for children that ends with an old schooner sailing again after an apology.",
    ]


def story_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="Who lived by the harbor and cared about the old schooner?",
            answer="Granpa lived by the harbor and cared about the old schooner with his husband.",
        ),
        QAItem(
            question="What problem kept the schooner from sailing at first?",
            answer="A gust tightened a rope and left the schooner's line knotted, so the boat could not sail safely.",
        ),
        QAItem(
            question="What did husband do that helped fix the quarrel?",
            answer="Husband apologized first, asked for help, and then worked with Granpa to mend the line.",
        ),
        QAItem(
            question="How did the story end?",
            answer="Granpa and husband reconciled, the schooner was repaired, and they sailed together again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a schooner?",
            answer="A schooner is a sailing ship with tall masts and big sails that can catch the wind.",
        ),
        QAItem(
            question="What does reconcile mean?",
            answer="Reconcile means to make peace again after a disagreement or hurt feelings.",
        ),
        QAItem(
            question="Why do sailors mend ropes?",
            answer="Sailors mend ropes so the boat can be steered and sailed safely without trouble.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: round(v, 3) for k, v in e.meters.items() if v}
        memes = {k: round(v, 3) for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.kind:7}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP helpers
# ---------------------------------------------------------------------------
def asp_facts() -> str:
    import asp
    lines: list[str] = []
    lines.append(asp.fact("boat", "boat1"))
    lines.append(asp.fact("person", "granpa"))
    lines.append(asp.fact("person", "husband"))
    lines.append(asp.fact("has_line", "boat1"))
    lines.append(asp.fact("has_patch", "boat1"))
    lines.append(asp.fact("rope_tangle", "boat1"))
    lines.append(asp.fact("sail_low", "boat1"))
    lines.append(asp.fact("needs_repair", "boat1"))
    lines.append(asp.fact("trust_up", "granpa", "husband"))
    lines.append(asp.fact("trust_up", "husband", "granpa"))
    lines.append(asp.fact("apologize", "husband", "granpa"))
    lines.append(asp.fact("apologize", "granpa", "husband"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/0."))
    ok = any(sym.name == "valid_story" for sym in model)
    if ok:
        print("OK: ASP gate accepts the story shape.")
        return 0
    print("MISMATCH: ASP gate rejected the story shape.")
    return 1


# ---------------------------------------------------------------------------
# Generation / CLI
# ---------------------------------------------------------------------------
def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy tale story world: schooner, granpa, husband, reconciliation.")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    ap.add_argument("--place", default="the harbor")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return StoryParams(place=args.place, seed=args.seed)


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid_story/0."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(StoryParams(place="the harbor", seed=base_seed))]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

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
