#!/usr/bin/env python3
"""Gingham Magic: a small nursery-rhyme storyworld about a helpful cloth."""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pathlib import Path as _StoryPath
_storyworlds_root = next(parent for parent in _StoryPath(__file__).resolve().parents
                        if (parent / 'results.py').is_file() and (parent / 'asp.py').is_file())
sys.path.insert(0, str(_storyworlds_root))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Event:
    kind: str
    text: str
    cause: str
    result: str


@dataclass
class StoryParams:
    child: str = "Mina"
    companion: str = "Pip"
    color: str = "red and white"
    problem: str = "puddles"
    solution: str = "magic gingham"
    seed: Optional[int] = None


@dataclass
class World:
    params: StoryParams
    entities: dict[str, Entity] = field(default_factory=dict)
    history: list[Event] = field(default_factory=list)
    facts: dict[str, object] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def record(self, kind: str, text: str, cause: str, result: str) -> None:
        self.history.append(Event(kind, text, cause, result))
        self.say(text)

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


COLORS = ["red and white", "blue and white", "yellow and white"]
CHILDREN = ["Mina", "Nell", "Toby", "Pip", "Rosa", "Sam"]
COMPANIONS = ["Bunny", "Mouse", "Duck", "Kitten"]
SOLUTIONS = {"magic gingham"}
PROBLEMS = {"puddles"}

KNOWLEDGE = [
    QAItem(
        "What is gingham?",
        "Gingham is a woven cloth with a neat checked pattern of colored and white squares.",
    ),
    QAItem(
        "What is a puddle?",
        "A puddle is a little pool of water that gathers on the ground after rain.",
    ),
    QAItem(
        "Why can a cloth be useful near a puddle?",
        "A cloth can soak up water, wipe a wet place, or make a dry path for small feet.",
    ),
]


ASP_RULES = r"""
at_risk(puddle_path).
has_magic_gingham(magic_cloth).
safe_path(puddle_path) :- at_risk(puddle_path), has_magic_gingham(magic_cloth).
valid_story :- safe_path(puddle_path).
#show valid_story/0.
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("at_risk", "puddle_path"),
            asp.fact("has_magic_gingham", "magic_cloth"),
        ]
    )


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def build_world(params: StoryParams) -> World:
    if params.problem not in PROBLEMS:
        raise StoryError("The story problem must be puddles.")
    if params.solution not in SOLUTIONS:
        raise StoryError("The story needs the magic gingham solution.")

    world = World(params)
    child = world.add(
        Entity(
            "child",
            "character",
            params.child,
            memes={"hope": 1.0, "care": 0.0, "joy": 0.0},
        )
    )
    companion = world.add(
        Entity(
            "companion",
            "animal",
            params.companion,
            memes={"trust": 1.0},
        )
    )
    cloth = world.add(
        Entity(
            "gingham",
            "cloth",
            f"{params.color} gingham cloth",
            meters={"dryness": 1.0, "magic": 1.0, "folded": 1.0},
        )
    )
    puddle = world.add(
        Entity(
            "puddle",
            "place",
            "puddle",
            meters={"water": 1.0, "blocking": 1.0},
        )
    )
    world.facts.update(child=child, companion=companion, cloth=cloth, puddle=puddle)

    world.record(
        "arrival",
        f"{params.child} went tip-tap down the lane with {params.companion} at "
        f"{params.child}'s side. Rain had left a round puddle before the little gate, "
        f"and the two friends wished to reach the garden.",
        "Rain had filled the lane with water.",
        "The puddle blocked their way to the garden.",
    )

    world.para()
    child.memes["worry"] = 1.0
    world.record(
        "problem",
        f'"Oh dear, oh dear," cried {params.child}. "{params.companion} is small, '
        f'and the puddle is wide. How shall we cross?" {params.companion} gave a '
        f"tiny, worried peep.",
        "The puddle was too wide for the small companion to cross safely.",
        "The friends needed a dry path.",
    )

    world.para()
    cloth.meters["folded"] = 0.0
    cloth.meters["dryness"] = 0.0
    cloth.meters["magic"] = 0.0
    child.memes["care"] += 1.0
    companion.memes["trust"] += 1.0
    world.record(
        "magic",
        f"Then {params.child} remembered the {params.color} gingham cloth tucked in "
        f'a basket. {params.child} spread it wide and whispered, "Square by square, '
        f'make a way!" The magic gingham shimmered with a gentle moonlit glow.',
        "The friends used the checked cloth with a kind wish.",
        "The ordinary cloth woke its quiet magic.",
    )

    world.para()
    puddle.meters["blocking"] = 0.0
    puddle.meters["water"] = 0.5
    cloth.meters["path"] = 1.0
    child.memes["joy"] += 1.0
    companion.memes["joy"] = 1.0
    world.record(
        "crossing",
        f"The gingham grew long, then strong, then bright, making a dry little bridge "
        f"over the puddle. Step-step went {params.companion}; skip-skip went "
        f"{params.child}. Not one small toe slipped into the water.",
        "The magic gingham covered the wet space and held firm.",
        "Both friends crossed safely.",
    )

    world.para()
    cloth.meters["magic"] = 1.0
    cloth.meters["folded"] = 1.0
    cloth.meters["path"] = 0.0
    child.memes["worry"] = 0.0
    child.memes["joy"] += 1.0
    world.record(
        "ending",
        f"At the garden gate, the gingham folded itself into a tiny square again. "
        f"{params.child} tucked it away, and {params.companion} danced beneath the "
        f'flowers. "Gingham, gingham, checked and bright—'
        f'you made our rainy pathway right!" sang {params.child}.',
        "The friends reached the garden and cared for the magical cloth.",
        "The cloth rested safely, ready to help another day.",
    )
    return world


def generation_prompts(world: World) -> list[str]:
    p = world.params
    return [
        f"Write a short Nursery Rhyme style story about {p.child} and {p.companion} "
        f"finding a magic gingham cloth beside puddles.",
        f"Tell a child-facing tale in which {p.color} gingham becomes a safe path "
        f"across rainwater.",
    ]


def story_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "Why could the friends not go straight to the garden?",
            world.history[0].cause + " " + world.history[0].result,
        ),
        QAItem(
            "What did the gingham cloth do?",
            world.history[2].cause + " " + world.history[2].result,
        ),
        QAItem(
            "How did the story end?",
            world.history[4].cause + " " + world.history[4].result,
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return list(KNOWLEDGE)


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}\nA: {item.answer}")
    lines.append("")
    lines.append("== World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}\nA: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        lines.append(
            f"  {entity.id}: {entity.label}; meters={meters}; memes={memes}"
        )
    lines.append("--- events ---")
    for event in world.history:
        lines.append(f"  {event.kind}: {event.text}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    if params.child == params.companion:
        raise StoryError("The child and companion must have different names.")
    world = build_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def check_sample(sample: StorySample) -> None:
    world = sample.world
    assert world is not None
    assert "gingham" in sample.story.lower()
    assert "magic" in sample.story.lower()
    assert "puddle" in sample.story.lower()
    assert len(world.history) == 5
    assert world.facts["cloth"].meters["path"] == 0.0
    assert world.facts["puddle"].meters["blocking"] == 0.0
    assert all("{" not in text and "}" not in text for text in sample.story.split())
    assert all(len(item.answer.split()) >= 8 for item in sample.story_qa)


def asp_verify() -> int:
    import asp
    models = asp.solve(asp_program(), models=1)
    if not models or not asp.atoms(models[0], "valid_story"):
        print("ASP verification failed.")
        return 1
    sample = generate(StoryParams())
    check_sample(sample)
    print("OK: ASP parity and generated-story checks passed.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A magic gingham Nursery Rhyme storyworld."
    )
    parser.add_argument("--child", choices=CHILDREN)
    parser.add_argument("--companion", choices=COMPANIONS)
    parser.add_argument("--color", choices=COLORS)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    child = args.child or rng.choice(CHILDREN)
    companion = args.companion or rng.choice(COMPANIONS)
    if child == companion:
        companion = rng.choice([x for x in COMPANIONS if x != child])
    return StoryParams(
        child=child,
        companion=companion,
        color=args.color or rng.choice(COLORS),
        seed=args.seed,
    )


def emit(
    sample: StorySample,
    *,
    trace: bool = False,
    qa: bool = False,
    header: str = "",
) -> None:
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
    if args.n < 1:
        raise SystemExit("-n must be at least 1")

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program())
        print("valid_story:", bool(asp.atoms(model, "valid_story")))
        return

    rng = random.Random(args.seed)
    samples: list[StorySample] = []
    if args.all:
        choices = [
            ("Mina", "Bunny", "red and white"),
            ("Toby", "Mouse", "blue and white"),
            ("Rosa", "Duck", "yellow and white"),
        ]
        for child, companion, color in choices:
            samples.append(
                generate(
                    StoryParams(
                        child=child,
                        companion=companion,
                        color=color,
                    )
                )
            )
    else:
        for index in range(args.n):
            params = resolve_params(args, random.Random((args.seed or 0) + index))
            params.seed = (args.seed or 0) + index
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2))
        return

    for index, sample in enumerate(samples):
        header = f"### {sample.params.child} and {sample.params.companion}" if args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
