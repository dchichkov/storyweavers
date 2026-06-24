#!/usr/bin/env python3
"""
A small slice-of-life storyworld about Baba, a puzzling doody, and a corpus of clues.

Premise:
- Baba notices a mysterious doody in the yard.
- The child narrator keeps a quiet inner monologue while trying to solve it.
- The mystery is resolved through ordinary, gentle observations rather than drama.
- The ending is a reconciliation: everyone feels less worried, and the yard is calm again.

This world models:
- physical meters: cleanliness, cluefulness, tidiness
- emotional memes: worry, patience, relief, warmth

Narrative instruments:
- Inner Monologue
- Mystery to Solve
- Reconciliation

The prose is intended to feel like a small, concrete slice of life.
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    role: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self) -> str:
        if self.kind == "character" and self.role in {"baba", "mother", "father"}:
            return "she" if self.role == "mother" else "he"
        return "it"

    def possessive(self) -> str:
        if self.kind == "character" and self.role in {"baba", "mother", "father"}:
            return "her" if self.role == "mother" else "his"
        return "its"


@dataclass
class StoryParams:
    name: str
    baba_role: str
    setting: str
    doody_source: str
    clue_source: str
    seed: Optional[int] = None


NAMES = ["Mina", "Noor", "Ivy", "Eli", "Sami", "Lena", "Owen", "Aria"]
BABA_ROLES = ["baba", "father"]
SETTINGS = [
    "the little backyard",
    "the quiet kitchen",
    "the sunny porch",
    "the side path by the garden",
]
DOODY_SOURCES = [
    "the dog had stepped there earlier",
    "a bird had visited the fence",
    "the puppy had hidden behind the flower pot",
]
CLUE_SOURCES = [
    "a muddy paw print",
    "a smudge on the gate",
    "a half-chewed leaf",
    "a tiny trail of dirt",
]


class World:
    def __init__(self, params: StoryParams) -> None:
        self.params = params
        self.entities: dict[str, Entity] = {}
        self.parts: list[str] = []
        self.facts: dict[str, object] = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.parts.append(text)

    def para(self) -> None:
        if self.parts and self.parts[-1] != "\n":
            self.parts.append("\n")

    def render(self) -> str:
        out: list[str] = []
        buf: list[str] = []
        for part in self.parts:
            if part == "\n":
                if buf:
                    out.append(" ".join(buf))
                    buf = []
            else:
                buf.append(part)
        if buf:
            out.append(" ".join(buf))
        return "\n\n".join(out)


def setup_world(params: StoryParams) -> World:
    world = World(params)
    child = world.add(Entity(
        id="child",
        kind="character",
        label=params.name,
        role="child",
        meters={"cluefulness": 0.0, "tidiness": 1.0},
        memes={"worry": 0.0, "patience": 0.0, "relief": 0.0},
    ))
    baba = world.add(Entity(
        id="baba",
        kind="character",
        label="Baba",
        role=params.baba_role,
        meters={"tidiness": 1.0},
        memes={"worry": 0.0, "warmth": 1.0, "relief": 0.0},
    ))
    doody = world.add(Entity(
        id="doody",
        kind="thing",
        label="doody",
        role="mystery",
        owner="yard",
        meters={"mess": 1.0},
    ))
    corpus = world.add(Entity(
        id="corpus",
        kind="thing",
        label="corpus",
        role="clue collection",
        owner="child",
        meters={"clues": 0.0},
    ))
    world.facts.update(
        child=child,
        baba=baba,
        doody=doody,
        corpus=corpus,
        place=params.setting,
        doody_source=params.doody_source,
        clue_source=params.clue_source,
    )
    return world


def inner_monologue(world: World, child: Entity) -> None:
    world.say(
        f"{child.label} stood very still and thought, "
        f'"Why is there a doody here?" '
        f'The question felt small, but it filled {child.label}\'s whole head.'
    )
    child.memes["worry"] += 1
    child.memes["patience"] += 0.5


def mystery_setup(world: World) -> None:
    p = world.params
    world.say(
        f"In {p.setting}, Baba looked at the doody and frowned a little. "
        f"It was not a big problem, but it was still a mystery to solve."
    )
    world.say(
        f"{p.name} opened the little corpus of clues in {p.name}'s mind: "
        f"{p.clue_source}, the scuffed edge near the step, and the quiet smell of dirt."
    )
    world.get("corpus").meters["clues"] += 1
    world.get("child").meters["cluefulness"] += 1


def investigate(world: World) -> None:
    child = world.get("child")
    baba = world.get("baba")
    world.say(
        f"{child.label} walked closer and found {world.params.clue_source}. "
        f'"Maybe the answer is simple," {child.label} thought. '
        f'"Maybe someone just made a little mess and forgot to clean it."'
    )
    child.meters["cluefulness"] += 1
    child.memes["patience"] += 0.5
    baba.memes["worry"] += 0.5
    world.say(
        f"Baba nodded and said the yard could wait. "
        f"{baba.label} did not rush the moment; {baba.label} just let the clues speak."
    )


def solve(world: World) -> None:
    p = world.params
    child = world.get("child")
    baba = world.get("baba")
    doody = world.get("doody")
    corpus = world.get("corpus")
    world.say(
        f"At last, {child.label} matched the clue to the memory: {p.doody_source}. "
        f"The doody was not a scary surprise at all. It was just an ordinary little accident."
    )
    doody.meters["mess"] = 0.0
    corpus.meters["clues"] += 1
    child.memes["worry"] = 0.0
    child.memes["relief"] += 1
    baba.memes["worry"] = 0.0
    baba.memes["relief"] += 1
    world.say(
        f"{child.label} got a paper towel, Baba got a bucket, and together they cleaned up the doody. "
        f"The corpus of clues had done its job, and the mystery lost its shadows."
    )


def reconciliation(world: World) -> None:
    child = world.get("child")
    baba = world.get("baba")
    world.say(
        f"Afterward, {child.label} looked up and smiled. "
        f'"Sorry for worrying so much," {child.label} said, even though the worry was already gone.'
    )
    world.say(
        f"Baba smiled back and rubbed {baba.possessive()} hands on a towel. "
        f'"It is okay," Baba said. "We solved it together." '
        f'The yard felt peaceful again, and {child.label} felt close to Baba.'
    )


def tell_story(params: StoryParams) -> World:
    world = setup_world(params)
    child = world.get("child")
    world.say(
        f"{params.name} was a quiet child who liked noticing small things."
    )
    world.say(
        f"One afternoon in {params.setting}, {params.name} found a mysterious doody."
    )
    inner_monologue(world, child)
    world.para()
    mystery_setup(world)
    investigate(world)
    world.para()
    solve(world)
    reconciliation(world)
    return world


def generation_prompts(world: World) -> list[str]:
    p = world.params
    return [
        f"Write a gentle slice-of-life story about {p.name}, Baba, and a mysterious doody in {p.setting}.",
        f"Tell a short story with an inner monologue, a mystery to solve, and a reconciliation.",
        f"Write a child-friendly story where a small corpus of clues helps solve a yard mystery.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.params
    return [
        QAItem(
            question=f"What mystery did {p.name} notice in {p.setting}?",
            answer="The child noticed a mysterious doody and wondered where it came from.",
        ),
        QAItem(
            question=f"What did {p.name} think about while looking at the doody?",
            answer="The child kept thinking that the answer was probably simple and that the clues could help.",
        ),
        QAItem(
            question="How was the mystery solved?",
            answer=f"{p.name} and Baba followed the clues, realized it was just a small accident, and cleaned it up together.",
        ),
        QAItem(
            question="How did the story end?",
            answer="It ended with Baba and the child feeling calm again and close to each other.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a clue?",
            answer="A clue is a small bit of information that helps someone figure out an answer.",
        ),
        QAItem(
            question="What does reconciliation mean?",
            answer="Reconciliation means people stop feeling upset and feel okay with each other again.",
        ),
        QAItem(
            question="What is an inner monologue?",
            answer="An inner monologue is the quiet thinking a character does inside their own head.",
        ),
        QAItem(
            question="What is a mystery?",
            answer="A mystery is something confusing that needs to be figured out.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Story questions ==",]
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for ent in world.entities.values():
        lines.append(
            f"{ent.id}: label={ent.label!r} kind={ent.kind!r} meters={ent.meters} memes={ent.memes}"
        )
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life mystery about Baba, doody, and a corpus of clues.")
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--baba-role", choices=BABA_ROLES)
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--doody-source", choices=DOODY_SOURCES)
    ap.add_argument("--clue-source", choices=CLUE_SOURCES)
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
    name = args.name or rng.choice(NAMES)
    baba_role = args.baba_role or rng.choice(BABA_ROLES)
    setting = args.setting or rng.choice(SETTINGS)
    doody_source = args.doody_source or rng.choice(DOODY_SOURCES)
    clue_source = args.clue_source or rng.choice(CLUE_SOURCES)
    return StoryParams(
        name=name,
        baba_role=baba_role,
        setting=setting,
        doody_source=doody_source,
        clue_source=clue_source,
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
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    rng = random.Random(base_seed)

    if args.all:
        samples = [generate(StoryParams(
            name=name,
            baba_role=baba_role,
            setting=setting,
            doody_source=doody_source,
            clue_source=clue_source,
        )) for name in NAMES[:2]
            for baba_role in BABA_ROLES[:1]
            for setting in SETTINGS[:2]
            for doody_source in DOODY_SOURCES[:2]
            for clue_source in CLUE_SOURCES[:2]][:max(1, args.n)]
    else:
        samples = []
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
        emit(sample, trace=args.trace, qa=args.qa, header=f"### story {i + 1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
