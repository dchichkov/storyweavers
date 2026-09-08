#!/usr/bin/env python3
"""
A heartwarming magic story about a rinse, a dim crab, and a helpful child.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

ROOT = next(
    parent for parent in Path(__file__).resolve().parents
    if (parent / "storyworlds" / "results.py").is_file()
)
sys.path.insert(0, str(ROOT / "storyworlds"))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    owner: Optional[str] = None


@dataclass
class World:
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


@dataclass
class StoryParams:
    name: str
    place: str
    shell_color: str
    seed: Optional[int] = None


PLACES = {
    "moonlit cove": "the moonlit cove",
    "silver beach": "the silver beach",
    "lantern pier": "the lantern pier",
}

NAMES = ["Luna", "Mara", "Nia", "Pia", "Suri", "Tala"]
SHELL_COLORS = ["pearl-white", "sea-green", "rose-pink", "sky-blue"]

MAGIC_SIGNS = [
    "a little star glimmered beneath its shell",
    "a blue spark trembled beside its claw",
    "a tiny moon shone on its back",
    "a warm golden glow flickered in its eyes",
]

RINSE_METHODS = [
    "a cup of clean rainwater",
    "a small shell filled at the tide pool",
    "a folded leaf holding fresh spring water",
]

ASP_RULES = r"""
bright(C) :- crab(C), rinsed(C).
happy(C) :- bright(C), cared_for(C).
magic_restored :- bright(crab).
#show rinsed/1.
#show bright/1.
#show happy/1.
#show magic_restored/0.
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("crab", "crab"),
            asp.fact("rinsed", "crab"),
            asp.fact("cared_for", "crab"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show magic_restored/0."))
    restored = any(atom.name == "magic_restored" for atom in model)
    if restored:
        print("OK: ASP predicts restored crab magic.")
        return 0
    print("MISMATCH: ASP did not predict restored crab magic.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A heartwarming magic story about rinsing a dim crab."
    )
    parser.add_argument("--name", choices=NAMES)
    parser.add_argument("--place", choices=sorted(PLACES))
    parser.add_argument("--shell-color", choices=SHELL_COLORS)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return StoryParams(
        name=args.name or rng.choice(NAMES),
        place=args.place or rng.choice(list(PLACES)),
        shell_color=args.shell_color or rng.choice(SHELL_COLORS),
    )


def tell(params: StoryParams) -> World:
    if params.place not in PLACES:
        raise StoryError(f"Unknown place: {params.place}")
    if params.shell_color not in SHELL_COLORS:
        raise StoryError(f"Unknown shell color: {params.shell_color}")

    seed = params.seed
    if seed is None:
        seed = sum(ord(char) for char in f"{params.name}|{params.place}|{params.shell_color}")
    rng = random.Random(seed)

    world = World(place=PLACES[params.place])
    child = world.add(
        Entity(
            id="child",
            kind="character",
            label=params.name,
            memes={"kindness": 1.0, "worry": 0.0, "joy": 0.0},
        )
    )
    crab = world.add(
        Entity(
            id="crab",
            kind="animal",
            label="crab",
            meters={"dim": 1.0, "wet": 0.0, "safe": 0.0},
            memes={"hope": 0.2},
        )
    )
    shell = world.add(
        Entity(
            id="shell",
            kind="object",
            label=f"{params.shell_color} shell",
            owner="crab",
            meters={"clean": 0.0},
        )
    )
    world.facts.update(
        child=child,
        crab=crab,
        shell=shell,
        sign=rng.choice(MAGIC_SIGNS),
        rinse_method=rng.choice(RINSE_METHODS),
    )

    child.memes["worry"] = 1.0
    world.say(
        f"At {world.place}, {params.name} found a small crab beneath a {params.shell_color} shell."
    )
    world.say(
        f"The crab looked crab-dim, and {world.facts['sign']}."
    )

    world.para()
    world.say(
        f'"Are you lost?" {params.name} asked. "I can stay with you until you feel better."'
    )
    world.say(
        '"The sand is cloudy and cold," whispered the crab. "My little magic cannot shine through it."'
    )
    world.say(
        f'"Then we will try something gentle," said {params.name}, reaching for {world.facts["rinse_method"]}.'
    )

    world.para()
    world.say(
        f"{params.name} did not scrub or hurry. Instead, {params.name} let the clean water rinse the shell one quiet drop at a time."
    )
    shell.meters["clean"] = 1.0
    crab.meters["wet"] = 1.0
    crab.meters["dim"] = 0.0
    crab.meters["safe"] = 1.0
    crab.memes["hope"] = 1.0
    child.memes["worry"] = 0.0
    world.say(
        '"That tickles," said the crab. "The dark sand is floating away."'
    )
    world.say(
        f'"You are doing it," {params.name} replied. "You do not have to shine all at once."'
    )

    world.para()
    crab.memes["joy"] = 1.0
    child.memes["joy"] = 1.0
    world.say(
        f"When the last grain drifted into the tide, {world.facts['sign'].capitalize()}."
    )
    world.say(
        "A soft light spread across the water, not bright enough to hurt the eyes, but warm enough to guide a lost gull home."
    )
    world.say(
        f'"My magic came back because you helped me slowly," said the crab.'
    )
    world.say(
        f'"Your magic was there all along," said {params.name}. "The rinse only helped everyone see it."'
    )
    world.say(
        f"The crab waved one careful claw, and {params.name} walked home beneath a trail of friendly golden ripples."
    )
    return world


def generation_prompts(world: World) -> list[str]:
    child = world.facts["child"]
    return [
        f"Write a heartwarming magic story about {child.label} helping a crab-dim crab at {world.place}.",
        f"Include a gentle rinse, a magical change, and dialogue between {child.label} and the crab.",
        "Show that patient kindness can reveal a light that was already there.",
    ]


def story_qa(world: World) -> list[QAItem]:
    child: Entity = world.facts["child"]  # type: ignore[assignment]
    crab: Entity = world.facts["crab"]  # type: ignore[assignment]
    shell: Entity = world.facts["shell"]  # type: ignore[assignment]
    return [
        QAItem(
            question="Who found the crab?",
            answer=f"{child.label} found the crab beneath a {shell.label}.",
        ),
        QAItem(
            question="Why did the crab look crab-dim?",
            answer="The crab's shell was covered with cloudy, cold sand, so its small magic could not shine through.",
        ),
        QAItem(
            question="How did the child help the crab?",
            answer=f"{child.label} used {world.facts['rinse_method']} to rinse the shell gently, one quiet drop at a time.",
        ),
        QAItem(
            question="What changed after the rinse?",
            answer="The dark sand floated away, the crab's hope returned, and warm magic spread across the water to guide a lost gull home.",
        ),
        QAItem(
            question="What did the crab learn from the child's kindness?",
            answer="The crab learned that patient help could reveal its own magic without forcing it to shine all at once.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a crab?",
            answer="A crab is a small sea animal with a hard shell, jointed legs, and claws.",
        ),
        QAItem(
            question="What does rinse mean?",
            answer="To rinse something means to wash it lightly with clean water.",
        ),
        QAItem(
            question="Why can gentle help be useful?",
            answer="Gentle help gives someone support without frightening, hurting, or rushing them.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(f"- {prompt}" for prompt in sample.prompts)
    lines.append("")
    lines.append("== story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for entity in world.entities.values():
        lines.append(
            f"{entity.id}: kind={entity.kind} label={entity.label} "
            f"meters={entity.meters} memes={entity.memes}"
        )
    return "\n".join(lines)


CURATED = [
    StoryParams("Luna", "moonlit cove", "pearl-white", 101),
    StoryParams("Mara", "silver beach", "sea-green", 202),
    StoryParams("Nia", "lantern pier", "rose-pink", 303),
]


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

    if args.show_asp:
        print(asp_program("#show magic_restored/0."))
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show magic_restored/0."))
        print("magic restored:", any(atom.name == "magic_restored" for atom in model))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        index = 0
        while len(samples) < max(0, args.n):
            params = resolve_params(args, random.Random(base_seed + index))
            params.seed = base_seed + index
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            index += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        emit(
            sample,
            trace=args.trace,
            qa=args.qa,
            header=f"### variant {index + 1}" if len(samples) > 1 else "",
        )
        if index < len(samples) - 1:
            print("\n" + "=" * 72 + "\n")


if __name__ == "__main__":
    main()
