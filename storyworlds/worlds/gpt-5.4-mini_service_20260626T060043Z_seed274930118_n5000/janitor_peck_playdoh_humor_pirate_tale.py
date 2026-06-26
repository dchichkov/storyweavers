#!/usr/bin/env python3
"""
A tiny pirate-humor storyworld about a ship's janitor, a cheeky peck, and a
barrel of playdoh that makes a mess before a clever fix.
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
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {}
        if not self.memes:
            self.memes = {}

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character" and self.type in {"woman", "girl", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.kind == "character" and self.type in {"man", "boy", "father", "captain", "pirate"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class StoryParams:
    place: str = "the pirate ship"
    seed: Optional[int] = None


@dataclass
class World:
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A pirate-humor storyworld about a janitor, a peck, and playdoh.")
    ap.add_argument("--place", default="the pirate ship")
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
    return StoryParams(place=args.place, seed=args.seed if args.seed is not None else rng.randrange(1 << 30))


def _setup_world(params: StoryParams) -> World:
    w = World(place=params.place)
    janitor = w.add(Entity(id="Mopbeard", kind="character", type="pirate", label="the ship janitor"))
    bird = w.add(Entity(id="Pecker", kind="character", type="parrot", label="a stubborn parrot"))
    playdoh = w.add(Entity(id="playdoh", type="thing", label="playdoh", owner=janitor.id, caretaker=janitor.id))
    barrel = w.add(Entity(id="barrel", type="thing", label="a little barrel"))
    w.facts.update(janitor=janitor, bird=bird, playdoh=playdoh, barrel=barrel, place=params.place)
    return w


def tell_story(w: World) -> None:
    janitor = w.facts["janitor"]
    bird = w.facts["bird"]
    playdoh = w.facts["playdoh"]
    barrel = w.facts["barrel"]

    w.say(
        f"On the {w.place}, Mopbeard was the ship janitor, and he liked to keep the deck shipshape even when the wind was feeling silly."
    )
    w.say(
        f"One bright morning, he found a little barrel of playdoh by the mast and chuckled. "
        f'"This stuff is softer than a soggy biscuit," he said, and he gave it a careful pat.'
    )
    w.para()
    w.say(
        f"Then Pecker the parrot hopped over, blinked at the playdoh, and gave it a quick peck just to be mischievous."
    )
    bird.memes["mischief"] = 1
    playdoh.meters["squashed"] = 1
    playdoh.meters["messy"] = 1
    janitor.memes["surprise"] = 1
    janitor.memes["annoyed"] = 1
    w.say(
        f"The peck made the playdoh squish over the barrel's rim and slap onto the deck like a greenish puddle of goo. "
        f"Mopbeard stared at it and laughed so hard he nearly dropped his mop."
    )
    w.say(
        f'"That bird has a peck for trouble," he muttered, "and now I have a sticky deck to scrub!"'
    )
    w.para()
    janitor.memes["plan"] = 1
    playdoh.meters["collected"] = 1
    w.say(
        f"Instead of grumbling forever, Mopbeard rolled the playdoh into a lumpy sea-creature and tucked it back into the barrel. "
        f"Then he tossed a rag over the worst of the mess and used a mop to sweep the rest straight away."
    )
    janitor.memes["joy"] = 1
    janitor.memes["humor"] = 1
    bird.memes["curious"] = 1
    w.say(
        f"Pecker leaned close, saw the lumpy sea-creature, and cocked his head as if it were the finest joke on the whole ship. "
        f"Mopbeard grinned, the deck sparkled again, and the parrot pecked the air instead of the playdoh."
    )
    w.say(
        f"By sunset, the barrel sat tidy, the deck was clean, and even the silly bird seemed proud of the work it had started."
    )


def generation_prompts(world: World) -> list[str]:
    return [
        "Write a short pirate tale for young children about a janitor, a peck, and playdoh.",
        "Tell a funny story on a pirate ship where a parrot pecks some playdoh and the janitor fixes the mess.",
        "Write a gentle humorous pirate story that ends with the deck clean and the playdoh safe in a barrel.",
    ]


def story_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="Who kept the pirate ship tidy in the story?",
            answer="Mopbeard kept the pirate ship tidy. He was the ship janitor, so cleaning the deck was his job.",
        ),
        QAItem(
            question="What did the parrot peck?",
            answer="The parrot pecked the playdoh, and that made the soft stuff squish over the barrel and onto the deck.",
        ),
        QAItem(
            question="How did Mopbeard fix the mess?",
            answer="He laughed, rolled the playdoh back into a lumpy sea-creature, covered the worst spot with a rag, and swept the rest clean with his mop.",
        ),
        QAItem(
            question="How did the story end?",
            answer="The deck was clean again, the playdoh was back in its barrel, and the parrot was pecking the air instead of making trouble.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a janitor's job?",
            answer="A janitor's job is to clean places and keep them neat.",
        ),
        QAItem(
            question="What is a parrot?",
            answer="A parrot is a bird that can have bright feathers and can copy sounds or words.",
        ),
        QAItem(
            question="What is playdoh?",
            answer="Playdoh is soft, colorful clay that children can squish, roll, and shape into fun things.",
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
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
% Tiny declarative twin for the story choice:
% a peck can make playdoh messy, and a janitor can clean it.
messy(playdoh) :- peck(parrot, playdoh).
cleaned(playdoh) :- janitor(J), messy(playdoh).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    return "\n".join(
        [
            asp.fact("janitor", "mopbeard"),
            asp.fact("parrot", "pecker"),
            asp.fact("thing", "playdoh"),
            asp.fact("place", "pirate_ship"),
            asp.fact("peck", "pecker", "playdoh"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show messy/1. #show cleaned/1."))
    atoms = set(asp.atoms(model, "messy")) | set(asp.atoms(model, "cleaned"))
    expected = {("playdoh",)}
    if expected.issubset(atoms):
        print("OK: ASP twin is sane.")
        return 0
    print("MISMATCH: ASP twin failed.")
    return 1


def generate(params: StoryParams) -> StorySample:
    world = _setup_world(params)
    tell_story(world)
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show messy/1. #show cleaned/1."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(1 << 30)
    rng = random.Random(base_seed)
    samples: list[StorySample] = []

    if args.all:
        samples.append(generate(resolve_params(args, rng)))
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
