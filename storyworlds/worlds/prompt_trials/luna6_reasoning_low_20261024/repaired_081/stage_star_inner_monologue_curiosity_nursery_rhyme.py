#!/usr/bin/env python3
"""
A nursery-rhyme storyworld about a curious child, a little stage, and a star
that needs the right light to shine.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "storyworlds"))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class StoryParams:
    hero_name: str = "Luna"
    helper_name: str = "Pip"
    stage_name: str = "the little moonlit stage"
    show_name: str = "the bedtime play"
    telling_mode: str = "curious opening"
    seed: Optional[int] = None


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
        self.lines: list[str] = []

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def render(self) -> str:
        return " ".join(self.lines)


HERO_NAMES = ["Luna", "Milo", "Nia", "Tess", "Kit"]
HELPER_NAMES = ["Pip", "Bo", "Mira", "Sol", "Rue"]
STAGES = [
    "the little moonlit stage",
    "the schoolroom stage",
    "the garden's tiny stage",
    "the red-curtained stage",
]
SHOWS = ["the bedtime play", "the moon-and-mouse play", "the evening show"]
TELLING_MODES = ["curious opening", "rhyme opening", "quiet opening"]

ASP_RULES = r"""
star(S) :- star_name(S).
stage(T) :- stage_name(T).
bright(S) :- star_state(S, bright).
ready(T) :- stage_state(T, ready).
solved(H) :- curious(H), bright(star).
"""


def asp_facts() -> str:
    import asp

    return "\n".join(
        [
            asp.fact("star_name", "paper_star"),
            asp.fact("stage_name", "tiny_stage"),
            asp.fact("star_state", "paper_star", "bright"),
            asp.fact("stage_state", "tiny_stage", "ready"),
            asp.fact("curious", "hero"),
        ]
    )


def asp_program(show: str = "#show bright/1.\n#show ready/1.\n#show solved/1.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    shown = asp.one_model(asp_program())
    actual = {
        (sym.name, tuple(
            arg.string if arg.type == arg.type.String
            else arg.number if arg.type == arg.type.Number
            else arg.name
            for arg in sym.arguments
        ))
        for sym in shown
    }
    expected = {
        ("bright", ("star",)),
        ("ready", ("tiny_stage",)),
        ("solved", ("hero",)),
    }
    if actual != expected:
        print("MISMATCH between ASP and Python reasoning.")
        print("ASP:", sorted(actual))
        print("PY :", sorted(expected))
        return 1

    params = StoryParams()
    sample = generate(params)
    if not sample.story.endswith("bright."):
        print("MISMATCH: generated story lacks its changed ending image.")
        return 1
    if not any("“" in line and "?”" in line for line in sample.story.split()):
        # The direct dialogue check below handles punctuation across tokens.
        if "?" not in sample.story or "“" not in sample.story or "”" not in sample.story:
            print("MISMATCH: generated story lacks spoken dialogue.")
            return 1
    print("OK: ASP/Python parity and generated-story checks look good.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A nursery-rhyme storyworld about a curious child and a paper star."
    )
    parser.add_argument("--name")
    parser.add_argument("--helper")
    parser.add_argument("--stage", choices=STAGES)
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
    hero = args.name or rng.choice(HERO_NAMES)
    helper = args.helper or rng.choice([name for name in HELPER_NAMES if name != hero])
    if hero == helper:
        raise StoryError("The helper should be a different person from the hero.")
    return StoryParams(
        hero_name=hero,
        helper_name=helper,
        stage_name=args.stage or rng.choice(STAGES),
        show_name=rng.choice(SHOWS),
        telling_mode=rng.choice(TELLING_MODES),
    )


def generate(params: StoryParams) -> StorySample:
    if not params.hero_name.strip() or not params.helper_name.strip():
        raise StoryError("Hero and helper names must not be empty.")
    if params.hero_name == params.helper_name:
        raise StoryError("The helper should be a different person from the hero.")
    if params.stage_name not in STAGES:
        raise StoryError(f"Unknown stage: {params.stage_name}")
    if params.telling_mode not in TELLING_MODES:
        raise StoryError(f"Unknown telling mode: {params.telling_mode}")

    rng = random.Random(
        params.seed if params.seed is not None
        else f"{params.hero_name}:{params.helper_name}:{params.stage_name}:{params.show_name}"
    )
    world = World()
    hero = world.add(Entity(
        "hero", "character", params.hero_name,
        meters={"curiosity": 1.0, "confidence": 0.4},
        memes={"wonder": 1.0, "worry": 0.2, "pride": 0.0},
    ))
    helper = world.add(Entity(
        "helper", "character", params.helper_name,
        meters={"helpfulness": 1.0},
        memes={"patience": 1.0},
    ))
    star = world.add(Entity(
        "star", "prop", "paper star",
        meters={"brightness": 0.0, "tilt": 1.0},
        memes={"hope": 1.0},
    ))
    stage = world.add(Entity(
        "stage", "place", params.stage_name,
        meters={"readiness": 0.0, "lamp_alignment": 0.0},
        memes={"welcome": 1.0},
    ))

    openings = {
        "curious opening": f"On {params.stage_name}, {params.hero_name} set a paper star in place for {params.show_name}.",
        "rhyme opening": f"Upon {params.stage_name}, beneath the night, {params.hero_name} hung a star of white.",
        "quiet opening": f"The curtains rested softly on {params.stage_name}, while {params.hero_name} prepared {params.show_name}.",
    }
    world.say(openings[params.telling_mode])
    world.say(
        f"But though the star was made to glow, it looked as dim as falling snow; "
        f"the little lamp shone past its face and left it dark in its own place."
    )
    world.say(
        f"“I thought my star would sparkle bright,” {params.hero_name} said. "
        f"“Why does it hide from all this light?”"
    )
    world.say(
        f"“Let us look before we guess,” {params.helper_name} replied. "
        f"“What do you notice on the stage?”"
    )
    world.say(
        f"In a quiet inner monologue, {params.hero_name} wondered, "
        f"“The lamp is warm, the star is still; perhaps the curtain blocks its spill.”"
    )
    world.say(
        f"With curious eyes, {params.hero_name} watched the beam fall on the curtain, "
        f"then watched a little strip of light slide around its edge."
    )
    world.say(
        f"“The lamp points away!” {params.hero_name} cried. "
        f"“May we turn it gently this way?”"
    )
    world.say(
        f"{params.helper_name} checked that the lamp was cool and safe to move, "
        f"then helped {params.hero_name} turn its shade toward the paper star."
    )

    star.meters.update(brightness=1.0, tilt=0.0)
    stage.meters.update(readiness=1.0, lamp_alignment=1.0)
    hero.meters["confidence"] = 1.0
    hero.memes.update(wonder=1.0, worry=0.0, pride=1.0)
    star.memes["hope"] = 1.0

    world.say(
        f"Now starry points shone on the wall, and golden light danced over all; "
        f"the darkened star became bright, a tiny moon against the night."
    )
    world.say(
        f"“I found the why by watching first,” {params.hero_name} said. "
        f"{params.helper_name} smiled as the curtains opened for {params.show_name}."
    )
    world.say(
        f"Above the ready stage, the paper star gleamed while the children sang their gentle rhyme."
    )

    world.facts.update(
        hero=hero,
        helper=helper,
        star=star,
        stage=stage,
        clue="The lamp beam fell on the curtain instead of the paper star.",
        solution="They safely turned the lamp shade toward the paper star.",
        changed=True,
    )

    prompts = [
        f"Tell a gentle nursery rhyme about {params.hero_name} preparing a star on {params.stage_name}.",
        f"Show how curiosity and an inner thought help {params.hero_name} discover why the paper star looks dim.",
        f"Include a spoken exchange with {params.helper_name} and end with a clear image of the changed stage.",
    ]
    story_qa = [
        QAItem(
            question="Why did the paper star look dim?",
            answer="The lamp beam fell on the curtain instead of shining on the paper star.",
        ),
        QAItem(
            question=f"What did {params.hero_name} wonder in their inner monologue?",
            answer=f"{params.hero_name} wondered whether the curtain was blocking the lamp's light from the star.",
        ),
        QAItem(
            question="How did the friends make the star shine?",
            answer=f"{params.helper_name} checked that the lamp was safe, then helped {params.hero_name} turn its shade toward the paper star.",
        ),
        QAItem(
            question="What showed that their solution worked?",
            answer="Golden light danced over the stage, and the paper star gleamed brightly.",
        ),
    ]
    world_qa = [
        QAItem(
            question="What is a stage?",
            answer="A stage is a raised or marked place where people perform for an audience.",
        ),
        QAItem(
            question="What does curiosity help someone do?",
            answer="Curiosity helps someone ask questions and look closely to find out how something works.",
        ),
        QAItem(
            question="What is an inner monologue?",
            answer="An inner monologue is a character's unspoken thought, shared with the reader but not said aloud.",
        ),
    ]

    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts,
        story_qa=story_qa,
        world_qa=world_qa,
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print("--- trace ---")
        for key, entity in sample.world.entities.items():
            print(f"{key}: {entity.label} meters={entity.meters} memes={entity.memes}")
    if qa:
        print("\n== prompts ==")
        for prompt in sample.prompts:
            print(prompt)
        print("\n== story qa ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}\nA: {item.answer}")
        print("\n== world qa ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}\nA: {item.answer}")


def main() -> None:
    args = build_parser().parse_args()
    if args.n < 1:
        raise StoryError("-n must be at least 1.")
    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp

        model = asp.one_model(asp_program())
        print("ASP model:", " ".join(str(atom) for atom in model))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        for stage in STAGES:
            params = StoryParams(
                hero_name=HERO_NAMES[0],
                helper_name=HELPER_NAMES[0],
                stage_name=stage,
                show_name=SHOWS[0],
                telling_mode="rhyme opening",
                seed=base_seed + len(samples),
            )
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        attempt = 0
        while len(samples) < args.n and attempt < max(50, args.n * 20):
            params = resolve_params(args, random.Random(base_seed + attempt))
            params.seed = base_seed + attempt
            sample = generate(params)
            if sample.story not in seen:
                samples.append(sample)
                seen.add(sample.story)
            attempt += 1

    if args.json:
        output = samples[0].to_json() if len(samples) == 1 else json.dumps(
            [sample.to_dict() for sample in samples], indent=2, ensure_ascii=False
        )
        print(output)
        return

    for index, sample in enumerate(samples):
        emit(
            sample,
            trace=args.trace,
            qa=args.qa,
            header=f"### variant {index + 1}" if len(samples) > 1 else "",
        )
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
