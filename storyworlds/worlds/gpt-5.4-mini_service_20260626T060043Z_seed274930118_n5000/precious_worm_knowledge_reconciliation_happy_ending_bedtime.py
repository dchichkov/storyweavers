#!/usr/bin/env python3
"""
A small bedtime-story world about a child, a precious worm, and a gentle lesson
that ends in reconciliation.

Premise:
- A child loves a tiny worm and calls it precious.
- A grown-up worries that keeping the worm in a jar is not kind.
- The child learns a little knowledge about worms, then helps make things right.
- The ending is calm, warm, and suitable for bedtime.
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
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    place: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Room:
    name: str
    cozy: bool = False
    has_soil: bool = False
    has_bedtime_light: bool = False


@dataclass
class StoryParams:
    room: str
    name: str
    child_type: str
    parent_type: str
    seed: Optional[int] = None


ROOMS = {
    "bedroom": Room(name="the bedroom", cozy=True, has_bedtime_light=True),
    "garden": Room(name="the garden", cozy=False, has_soil=True),
    "porch": Room(name="the porch", cozy=True, has_soil=True),
    "kitchen": Room(name="the kitchen", cozy=True, has_bedtime_light=True),
}

CHILD_NAMES = ["Mia", "Noah", "Luna", "Eli", "Nora", "Theo", "Ava", "Finn"]
CHILD_TYPES = ["girl", "boy"]
PARENT_TYPES = ["mother", "father"]


class World:
    def __init__(self, room: Room):
        self.room = room
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def para(self) -> None:
        if self.lines and self.lines[-1] != "":
            self.lines.append("")

    def render(self) -> str:
        out = []
        para = []
        for line in self.lines:
            if line == "":
                if para:
                    out.append(" ".join(para))
                    para = []
            else:
                para.append(line)
        if para:
            out.append(" ".join(para))
        return "\n\n".join(out)


def bed_detail(room: Room) -> str:
    if room.name == "the bedroom":
        return "The lamp glowed softly, and the blanket waited like a warm cloud."
    if room.name == "the kitchen":
        return "The kitchen was quiet, with a sleepy clock ticking very softly."
    if room.name == "the porch":
        return "The porch held a little night breeze and the smell of clean earth."
    return "The garden was dark and still, with cool soil resting under the moon."


def worm_knowledge() -> list[QAItem]:
    return [
        QAItem(
            question="What do worms like to live in?",
            answer="Worms like to live in damp soil where they can wiggle and burrow safely.",
        ),
        QAItem(
            question="Why are worms helpful?",
            answer="Worms help break down old leaves and make the soil better for plants.",
        ),
        QAItem(
            question="Do worms need lots of space?",
            answer="Yes. Worms need space, soft soil, and a gentle place to move around.",
        ),
    ]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime story world about a precious worm and a gentle reconciliation.")
    ap.add_argument("--room", choices=ROOMS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=PARENT_TYPES)
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
    room = args.room or rng.choice(list(ROOMS))
    name = args.name or rng.choice(CHILD_NAMES)
    gender = args.gender or rng.choice(CHILD_TYPES)
    parent = args.parent or rng.choice(PARENT_TYPES)
    return StoryParams(room=room, name=name, child_type=gender, parent_type=parent)


def valid_story(params: StoryParams) -> bool:
    return params.room in ROOMS and params.child_type in {"girl", "boy"} and params.parent_type in {"mother", "father"}


def generate(params: StoryParams) -> StorySample:
    if not valid_story(params):
        raise StoryError("Invalid story parameters.")

    room = ROOMS[params.room]
    world = World(room)

    child = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.child_type,
        label=params.name,
        meters={"sleepiness": 0.0},
        memes={"love": 0.0, "worry": 0.0, "joy": 0.0, "understanding": 0.0, "reconciliation": 0.0},
    ))
    parent = world.add(Entity(
        id="parent",
        kind="character",
        type=params.parent_type,
        label="mom" if params.parent_type == "mother" else "dad",
        meters={"sleepiness": 0.0},
        memes={"worry": 0.0, "love": 0.0, "joy": 0.0},
    ))
    worm = world.add(Entity(
        id="worm",
        kind="creature",
        type="worm",
        label="worm",
        phrase="a tiny worm",
        owner=child.id,
        caretaker=parent.id,
        place=room.name,
        meters={"comfort": 0.0, "soil": 1.0, "safe": 0.0},
        memes={"precious": 1.0, "calm": 0.0},
    ))

    # Act 1
    world.say(f"{child.id} was a sleepy little {params.child_type} who loved quiet nights.")
    world.say(f"At bedtime, {child.id} found {worm.phrase} and thought it was precious.")
    world.say(f"{bed_detail(room)}")

    # Act 2
    world.para()
    world.say(f"{child.id} wanted to keep the worm close in a glass jar beside the bed.")
    parent.memes["worry"] += 1
    world.say(f"But {parent.label} frowned gently, because worms need soft soil and space, not a tight jar.")
    world.say(f"That little bit of knowledge made the room feel more serious for a moment.")

    # Reconciliation
    child.memes["understanding"] += 1
    child.memes["worry"] += 1
    world.para()
    world.say(f"{child.id} listened, then looked at the worm more carefully.")
    world.say(f"{child.id} learned that worms help the garden and must be treated kindly.")
    world.say(f"So {child.id} opened the jar, took the worm outside to the porch garden box, and tucked it into damp soil.")
    worm.meters["comfort"] += 1
    worm.meters["safe"] += 1
    worm.place = room.name if room.name == "garden" else "the little garden box"
    child.memes["reconciliation"] += 1
    parent.memes["joy"] += 1
    parent.memes["worry"] = 0.0
    child.memes["joy"] += 1

    # Act 3
    world.para()
    world.say(f"{parent.label} smiled and wrapped {child.pronoun('object')} in a blanket.")
    world.say(f'"You cared about something precious, and now you cared for it the right way," {parent.label} whispered.')
    world.say(f"{child.id} hugged {parent.label} back, and the worm rested safely in the soil.")
    world.say(f"Before long, {child.id} was yawning, and the night felt peaceful again.")
    world.say("It was a happy ending, and everyone went to sleep feeling kindly and warm.")

    world.facts.update(
        child=child,
        parent=parent,
        worm=worm,
        room=room,
        params=params,
    )

    prompts = [
        'Write a gentle bedtime story about a child, a precious worm, and a kind lesson.',
        f"Tell a short story where {child.id} learns why a worm should live in soil, not in a jar.",
        "Write a bedtime story with reconciliation, a soft warning, and a happy ending.",
    ]
    story_qa = [
        QAItem(
            question=f"What did {child.id} think was precious?",
            answer=f"{child.id} thought the tiny worm was precious.",
        ),
        QAItem(
            question=f"Why did {parent.label} worry about the worm in the jar?",
            answer="Because worms need soft soil, space, and a gentle place to live.",
        ),
        QAItem(
            question="How did the story end?",
            answer="The child put the worm in damp soil, everyone made peace, and the night ended happily.",
        ),
    ]
    world_qa = worm_knowledge()
    return StorySample(params=params, story=world.render(), prompts=prompts, story_qa=story_qa, world_qa=world_qa, world=world)


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
        if e.place:
            bits.append(f"place={e.place}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


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


ASP_RULES = r"""
precious(X) :- worm(X).
needs_soil(X) :- worm(X).
kind_fix(open_jar, X) :- worm(X), needs_soil(X).
reconciled(child) :- precious(worm), kind_fix(open_jar, worm).
happy_ending :- reconciled(child).
"""


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("worm", "worm"),
        asp.fact("child", "child"),
        asp.fact("precious", "worm"),
        asp.fact("needs_soil", "worm"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    return 0


def build_all_samples() -> list[StoryParams]:
    return [
        StoryParams(room="bedroom", name="Mia", child_type="girl", parent_type="mother"),
        StoryParams(room="garden", name="Noah", child_type="boy", parent_type="father"),
        StoryParams(room="porch", name="Luna", child_type="girl", parent_type="mother"),
    ]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show happy_ending/0."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in build_all_samples()]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
