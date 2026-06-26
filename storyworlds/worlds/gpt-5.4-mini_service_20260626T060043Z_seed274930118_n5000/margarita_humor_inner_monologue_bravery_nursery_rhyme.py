#!/usr/bin/env python3
"""
A standalone story world for a tiny nursery-rhyme tale about Margarita,
humor, inner monologue, and bravery.

The world model tracks:
- a small character with meters and memes
- a playful obstacle that starts as a worry
- a simple brave action that turns worry into laughter

The prose is narrated in a child-facing, rhyming style, but the actual
story comes from state changes in the simulated world.
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
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class World:
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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


@dataclass
class StoryParams:
    place: str
    seed: Optional[int] = None


SETTINGS = {
    "nursery": "the nursery",
    "garden": "the garden",
    "playroom": "the playroom",
}

PLACES = list(SETTINGS.keys())


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A nursery-rhyme story world about Margarita, humor, inner monologue, and bravery."
    )
    ap.add_argument("--place", choices=PLACES)
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
    place = args.place or rng.choice(PLACES)
    return StoryParams(place=place)


def asp_facts() -> str:
    import asp
    lines = [asp.fact("place", pid) for pid in PLACES]
    for pid, label in SETTINGS.items():
        lines.append(asp.fact("named", pid, label))
    return "\n".join(lines)


ASP_RULES = r"""
valid(P) :- place(P).
#show valid/1.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_places() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/1."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = {(p,) for p in PLACES}
    cl = set(asp_valid_places())
    if py == cl:
        print(f"OK: clingo gate matches resolve_params choices ({len(py)} places).")
        return 0
    print("MISMATCH between clingo and python:")
    print(" python only:", sorted(py - cl))
    print(" clingo only:", sorted(cl - py))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = World(place=SETTINGS[params.place])

    margarita = world.add(
        Entity(
            id="Margarita",
            kind="character",
            type="girl",
            label="Margarita",
            traits=["little", "curious", "bright"],
            meters={"steps": 0.0, "courage": 0.0},
            memes={"worry": 0.0, "humor": 0.0, "bravery": 0.0, "joy": 0.0},
        )
    )
    toy = world.add(
        Entity(
            id="ToyDuck",
            kind="thing",
            type="toy",
            label="a squeaky toy duck",
            phrase="a squeaky toy duck",
        )
    )

    # Beginning: the rhyme's gentle setup.
    world.say(f"In {world.place}, lived Margarita, small and spry, with a twinkle in her eye.")
    world.say(f"She loved her squeaky toy duck, and she loved to sing a silly little sigh.")

    # Middle: she worries, but the worry lives in her inner monologue.
    world.para()
    margarita.memes["worry"] += 1
    world.say(
        "At the garden gate there stood a wobble-whoop puddle, round as a pie, "
        "and Margarita thought, 'Oh dear me, shall I splash it? Shall I slip? Shall I cry?'"
    )
    world.say(
        "Then she giggled to herself, 'If I tiptoe like a kitten, I may stay dry.'"
    )

    # Turn: bravery grows through a small, deliberate act.
    margarita.meters["steps"] += 3
    margarita.memes["bravery"] += 1
    margarita.memes["worry"] = 0
    margarita.memes["joy"] += 1

    world.para()
    world.say(
        "So Margarita lifted her chin like a queen of the air, and marched with a dainty, brave care."
    )
    world.say(
        "She stepped over the puddle, then bowed to the duck, and the duck gave a squeak that sounded like luck."
    )
    world.say(
        "Margarita laughed, 'Why, puddles are plunky, not spooky at all!' and the clouds seemed to clap from the wall."
    )

    # Ending image: changed state proves the story.
    world.para()
    world.say(
        "And there she went home with dry little shoes, a brave little heart, and a bellyful of amused blues."
    )
    world.say(
        "For Margarita found that a giggle and try can make a big puddle feel tiny and shy."
    )

    world.facts = {
        "margarita": margarita,
        "toy": toy,
        "place": params.place,
        "place_label": world.place,
    }

    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    return [
        'Write a short nursery-rhyme story about Margarita, a funny worry, and a brave choice.',
        f"Tell a gentle story set in {world.place} where Margarita hears her own thoughts, laughs, and then acts bravely.",
        'Write a child-friendly rhyme that includes Margarita, humor, inner monologue, and bravery.',
    ]


def story_qa(world: World) -> list[QAItem]:
    m = world.facts["margarita"]
    place = world.facts["place_label"]
    return [
        QAItem(
            question="Who is the story about?",
            answer="The story is about Margarita, a little girl with a bright, curious heart.",
        ),
        QAItem(
            question=f"What did Margarita worry about in {place}?",
            answer="She worried about a big puddle and wondered if she might splash or slip.",
        ),
        QAItem(
            question="What did Margarita tell herself before she crossed the puddle?",
            answer="She told herself she could tiptoe like a kitten and stay dry.",
        ),
        QAItem(
            question="How did Margarita feel after she crossed the puddle?",
            answer="She felt brave, happy, and funny inside, and she laughed at how small the puddle seemed.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a puddle?",
            answer="A puddle is a little pool of water on the ground, often after rain.",
        ),
        QAItem(
            question="What does bravery mean?",
            answer="Bravery means doing something even when it feels a little scary.",
        ),
        QAItem(
            question="What is an inner monologue?",
            answer="An inner monologue is the voice inside your head when you think to yourself.",
        ),
        QAItem(
            question="Why can humor help when you feel nervous?",
            answer="Humor can help because a silly thought or a laugh can make a scary moment feel lighter.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:10} ({e.kind:8}) {' '.join(bits)}")
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
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        places = asp_valid_places()
        print(f"{len(places)} valid places:\n")
        for (place,) in places:
            print(f"  {place}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for place in PLACES:
            params = StoryParams(place=place)
            params.seed = base_seed
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
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
