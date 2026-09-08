#!/usr/bin/env python3
from __future__ import annotations

# Locate the shared StoryWorld helpers from any batch depth.
from pathlib import Path as _StoryPath
import sys as _StorySys
_storyworlds_root = next(parent for parent in _StoryPath(__file__).resolve().parents
                        if (parent / 'results.py').is_file() and (parent / 'asp.py').is_file())
_StorySys.path.insert(0, str(_storyworlds_root.parent))
_StorySys.path.insert(0, str(_storyworlds_root))


import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Any, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class StoryParams:
    captain: str = "Luna"
    helper: str = "Pip"
    treasure: str = "silver bell"
    setting: str = "the moonlit nursery"
    consecutive: int = 3
    stretch: str = "a long ribbon bridge"
    chitter: str = "a chittering mouse"
    seed: Optional[int] = None


@dataclass
class Entity:
    id: str
    kind: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, Any] = field(default_factory=dict)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity


ASP_RULES = r"""
safe_step(N) :- consecutive(N), N >= 1.
flashback_needed :- safe_step(N), N >= 2.
crossed :- safe_step(N), stretch_ready.
treasure_found :- crossed, bell_present.
answer(found) :- treasure_found.
"""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Luna's nursery-rhyme pirate adventure.")
    parser.add_argument("--captain")
    parser.add_argument("--helper")
    parser.add_argument("--treasure")
    parser.add_argument("--setting")
    parser.add_argument("--consecutive", type=int)
    parser.add_argument("--stretch")
    parser.add_argument("--chitter")
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--seed", type=int)
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    consecutive = args.consecutive if args.consecutive is not None else rng.choice([2, 3, 4])
    if consecutive < 1:
        raise StoryError("consecutive must be at least 1")
    return StoryParams(
        captain=args.captain or rng.choice(["Luna", "Mira", "Nell"]),
        helper=args.helper or rng.choice(["Pip", "Toby", "Bee"]),
        treasure=args.treasure or rng.choice(["silver bell", "moon key", "pearl button"]),
        setting=args.setting or rng.choice(["the moonlit nursery", "the candlelit playroom"]),
        consecutive=consecutive,
        stretch=args.stretch or rng.choice(["a long ribbon bridge", "a blanket bridge"]),
        chitter=args.chitter or rng.choice(["a chittering mouse", "a chittering cricket"]),
    )


def generate(params: StoryParams) -> StorySample:
    if params.consecutive < 1:
        raise StoryError("The captain needs at least one consecutive stepping-stone.")
    world = World()
    captain = world.add(Entity(params.captain, "character", memes={"courage": 1.0}))
    helper = world.add(Entity(params.helper, "character", memes={"care": 1.0}))
    bell = world.add(Entity("treasure", "object", meters={"shiny": 1.0}))
    bridge = world.add(Entity("bridge", "object", meters={"length": float(params.consecutive)}))
    mouse = world.add(Entity("chitter", "animal", memes={"mischief": 1.0}))

    steps = []
    for number in range(1, params.consecutive + 1):
        steps.append(f"{params.captain} took step {number}, then another, then another")
    step_line = "; ".join(steps) + "."

    story = (
        f"In {params.setting}, Captain {params.captain} sailed a toy ship beside {params.helper}. "
        f"They sought a {params.treasure}, hidden beyond {params.stretch}. "
        f"A {params.chitter} went, “Chit-chit!” and shook the bridge. "
        f'"Do we cross?" asked {params.helper}. "{params.captain} said, "Together, we count each step." '
        f"{step_line} "
        f"At the middle, a Flashback fluttered through {params.captain}'s mind: yesterday, "
        f"the bridge had sagged, but {params.helper} had held the ribbon steady. "
        f'"I remember your helping hand," said {params.captain}. "Then we can try again," said {params.helper}. '
        f"So they stretched their arms, crossed the ribbon bridge, and found the {params.treasure} "
        f"under a soft blue pillow. The {params.chitter} clapped its tiny paws, and the bell rang "
        f"ding-ding in the nursery moonlight."
    )

    world.facts.update(
        captain=captain,
        helper=helper,
        treasure=bell,
        bridge=bridge,
        chitter=mouse,
        crossed=True,
        flashback=True,
        consecutive=params.consecutive,
    )

    prompts = [
        f"Write a Nursery Rhyme about {params.captain} crossing {params.stretch}.",
        "Include consecutive steps, a stretch, a chitter, and a helpful Flashback.",
        "End with a bright discovery and a gentle rhyme-like image.",
    ]
    story_qa = [
        QAItem(
            f"Who crossed {params.stretch}?",
            f"{params.captain} crossed {params.stretch} with help from {params.helper}.",
        ),
        QAItem(
            "What did the Flashback remind the captain of?",
            f"It reminded {params.captain} that {params.helper} had held the bridge steady the day before.",
        ),
        QAItem(
            f"What did they find?",
            f"They found the {params.treasure} under a soft blue pillow.",
        ),
    ]
    world_qa = [
        QAItem(
            "What does consecutive mean?",
            "Consecutive means following one after another without a gap.",
        ),
        QAItem(
            "Why can a stretch help someone cross?",
            "A careful stretch can help someone reach farther while keeping balance.",
        ),
        QAItem(
            "What is a chitter?",
            "A chitter is a series of small, quick sounds made by a little animal.",
        ),
    ]
    return StorySample(
        params=params,
        story=story,
        prompts=prompts,
        story_qa=story_qa,
        world_qa=world_qa,
        world=world,
    )


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("consecutive", 3),
        asp.fact("stretch_ready"),
        asp.fact("bell_present"),
    ])


def asp_program() -> str:
    return asp_facts() + "\n" + ASP_RULES


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        lines.append(
            f"{entity.id}: kind={entity.kind}, meters={entity.meters}, memes={entity.memes}"
        )
    lines.append(f"facts={world.facts}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== World knowledge ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def emit(sample: StorySample, trace: bool = False, qa: bool = False) -> None:
    print(sample.story)
    if trace and sample.world:
        print(dump_trace(sample.world))
    if qa:
        print(format_qa(sample))


def verify() -> int:
    import asp
    model = asp.one_model(asp_program() + "\n#show flashback_needed/0.\n#show crossed/0.")
    names = {str(atom) for atom in model}
    if "flashback_needed" not in names or "crossed" not in names:
        print("ASP verification failed.")
        return 1
    sample = generate(StoryParams())
    if "Flashback" not in sample.story or "consecutive" not in sample.prompts[1]:
        print("Story verification failed.")
        return 1
    print("OK: ASP and story checks passed.")
    return 0


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        raise SystemExit(verify())
    if args.asp:
        import asp
        print(asp_program())
        print(asp.one_model(asp_program() + "\n#show flashback_needed/0.\n#show crossed/0."))
        return

    base = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    count = len(CURATED) if args.all else args.n
    for index in range(count):
        rng = random.Random(base + index)
        params = resolve_params(args, rng)
        params.seed = base + index
        samples.append(generate(params))

    if args.json:
        payload = [sample.to_dict() for sample in samples]
        print(json.dumps(payload[0] if len(payload) == 1 else payload, indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        if index:
            print("\n" + "=" * 60 + "\n")
        emit(sample, trace=args.trace, qa=args.qa)


CURATED = [
    StoryParams(captain="Luna", helper="Pip", consecutive=3, seed=1),
    StoryParams(captain="Mira", helper="Bee", treasure="moon key", consecutive=4, seed=2),
]


if __name__ == "__main__":
    main()
