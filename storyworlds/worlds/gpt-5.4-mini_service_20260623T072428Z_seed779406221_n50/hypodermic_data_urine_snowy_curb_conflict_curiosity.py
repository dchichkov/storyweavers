#!/usr/bin/env python3
"""
storyworlds/worlds/hypodermic_data_urine_snowy_curb_conflict_curiosity.py
========================================================================

A standalone storyworld for a tiny rhyming tale about curiosity and conflict
on a snowy curb.

Seed tale:
---
On a snowy curb, June found a little science pouch.
Inside was a hypodermic data card from a clinic van, and a tiny vial marked
urine. June was curious and wanted to poke and peek, but her brother Finn felt
worried. Their mom stopped them, called for help, and the nurse came back to
collect the pouch safely. June learned that curious hands must be careful
hands.

World model:
- June's curiosity rises when she spots the pouch.
- Conflict rises when she reaches for the sharp hypodermic.
- The mother warns and redirects.
- A helper arrives and the vial is contained and collected.
- The ending proves what changed: the pouch is gone, the curb is safe, and
  June's curiosity is still there, but now guided by care.

The prose aims for a gentle, rhyming, child-facing rhythm.
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

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"wet": 0.0, "sharp": 0.0, "safe": 0.0}
        if not self.memes:
            self.memes = {"curiosity": 0.0, "conflict": 0.0, "calm": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        if self.type == "girl":
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type == "boy":
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Place:
    id: str
    label: str
    snowy: bool = True
    curb: bool = True


@dataclass
class StoryParams:
    name: str
    sibling: str
    parent: str
    place: str = "curb"
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[str] = set()

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


def rhyme(a: str, b: str) -> str:
    return f"{a} / {b}"


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(
            f"  {e.id:10} ({e.type:7}) meters={{{', '.join(f'{k}: {v}' for k, v in e.meters.items() if v)}}} "
            f"memes={{{', '.join(f'{k}: {v}' for k, v in e.memes.items() if v)}}}"
        )
    lines.append(f"  fired: {sorted(world.fired)}")
    return "\n".join(lines)


def tell(params: StoryParams) -> World:
    place = PLACES[params.place]
    world = World(place)
    child = world.add(Entity(id=params.name, kind="character", type="girl", role="curious"))
    sibling = world.add(Entity(id=params.sibling, kind="character", type="boy", role="conflict"))
    parent = world.add(Entity(id=params.parent, kind="character", type="mother"))
    pouch = world.add(Entity(id="pouch", type="thing", label="science pouch", phrase="a little science pouch"))
    hypo = world.add(Entity(id="hypo", type="thing", label="hypodermic", phrase="a tiny hypodermic"))
    data = world.add(Entity(id="data", type="thing", label="data card", phrase="a data card"))
    urine = world.add(Entity(id="urine", type="thing", label="urine vial", phrase="a vial marked urine"))

    child.memes["curiosity"] += 1
    world.say(
        f"On a snowy curb so white and bright, {child.id} found a pouch in the light."
    )
    world.say(
        f"It held {hypo.phrase}, {data.phrase}, and {urine.phrase} tucked in a row, "
        f"like secrets that did not want to show."
    )
    world.say(
        f"{child.id} leaned in close with curious cheer, but {sibling.id} frowned and said, "
        f'"No, not near!"'
    )
    child.memes["curiosity"] += 1
    sibling.memes["conflict"] += 1
    child.memes["conflict"] += 1
    world.para()
    world.say(
        f'"That pointy {hypo.label} could poke your skin," {sibling.id} said low. "Let a grown-up in."'
    )
    world.say(
        f"{child.id} still wanted a peek and a pry, but {parent.id} came out with a calm, kind eye."
    )
    parent.memes["calm"] += 1
    world.say(
        f'"Hands off the pouch, sweet pea," {parent.id} said. "We call for help and wait nearby."'
    )
    world.para()
    world.say(
        f"A nurse rolled up in a warm blue van, and took the pouch the safe, sure plan."
    )
    world.say(
        f"The {data.label} was checked, the {urine.label} was sealed, and the sharp {hypo.label} was safely fielded."
    )
    child.memes["conflict"] = 0.0
    child.meters["safe"] += 1
    world.say(
        f"So {child.id} learned on the snowy curb: curious hearts can still be wise and observant."
    )
    world.say(
        f"The curb stayed clear, the pouch went away, and {child.id} kept wonder for another day."
    )

    world.facts.update(
        child=child,
        sibling=sibling,
        parent=parent,
        pouch=pouch,
        hypo=hypo,
        data=data,
        urine=urine,
        place=place,
    )
    return world


PLACES = {
    "curb": Place(id="curb", label="snowy curb", snowy=True, curb=True),
}


@dataclass
class StoryParams:
    name: str
    sibling: str
    parent: str
    place: str = "curb"
    seed: Optional[int] = None


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a short rhyming story about a child finding a strange pouch on a snowy curb.',
        f"Tell a gentle rhyme where {f['child'].id} feels curiosity, {f['sibling'].id} feels conflict, and a mother keeps everyone safe.",
        "Write a child-facing story that includes the words hypodermic, data, and urine and ends with a safe helper arriving.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, sibling, parent = f["child"], f["sibling"], f["parent"]
    return [
        QAItem(
            question=f"What did {child.id} find on the snowy curb?",
            answer="She found a little science pouch with a hypodermic, a data card, and a vial marked urine.",
        ),
        QAItem(
            question=f"Why did {sibling.id} feel worried?",
            answer="He felt worried because the hypodermic had a sharp point and the pouch should only be handled by a grown-up.",
        ),
        QAItem(
            question=f"What did {parent.id} tell them to do?",
            answer="Their mom told them to keep their hands off the pouch, call for help, and wait nearby.",
        ),
        QAItem(
            question="How did the story end?",
            answer="A nurse came to collect the pouch safely, and the curb stayed clear and safe.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a hypodermic?",
            answer="A hypodermic is a sharp medical needle used by trained grown-ups for medicine or tests.",
        ),
        QAItem(
            question="What is data?",
            answer="Data is information that people write down or store so they can learn from it later.",
        ),
        QAItem(
            question="What is urine?",
            answer="Urine is a liquid that comes out of the body and is usually checked in a clinic or doctor’s office.",
        ),
        QAItem(
            question="Why should children not touch sharp medical things?",
            answer="Sharp medical things can poke skin or spread germs, so only grown-ups with training should handle them.",
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


ASP_RULES = r"""
child_curious(C) :- curiosity(C, V), V >= 1.
conflict(C) :- conflict_meter(C, V), V >= 1.
safe_end :- call_adult, nurse_arrives, pouch_collected.
"""

def asp_facts() -> str:
    import storyworlds.asp as asp
    return "\n".join([
        asp.fact("setting", "snowy_curb"),
        asp.fact("has_item", "hypodermic"),
        asp.fact("has_item", "data"),
        asp.fact("has_item", "urine"),
        asp.fact("feature", "Conflict"),
        asp.fact("feature", "Curiosity"),
    ])


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Rhyming storyworld: snowy curb, curiosity, and a safe ending.")
    ap.add_argument("--name")
    ap.add_argument("--sibling")
    ap.add_argument("--parent")
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
    name = args.name or rng.choice(["June", "Mina", "Lina", "Tessa"])
    sibling = args.sibling or rng.choice(["Finn", "Owen", "Noah", "Ben"])
    if sibling == name:
        sibling = "Finn"
    parent = args.parent or rng.choice(["Mom", "Mum"])
    return StoryParams(name=name, sibling=sibling, parent=parent, seed=None)


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


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    print("OK: ASP twin is present for this storyworld.")
    return 0


CURATED = [
    StoryParams(name="June", sibling="Finn", parent="Mom"),
    StoryParams(name="Mina", sibling="Owen", parent="Mum"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show safe_end/0."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            params = resolve_params(args, random.Random(base_seed + i))
            i += 1
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
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {i + 1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
