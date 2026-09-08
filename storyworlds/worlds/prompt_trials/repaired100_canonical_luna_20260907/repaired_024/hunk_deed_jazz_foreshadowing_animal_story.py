#!/usr/bin/env python3
"""
Animal storyworld: Hunk, Deed, and the Jazz Foreshadowing.

A small state-driven tale about Hunk the badger, a brave deed, and a strange
jazz rhythm that warns the woodland animals before a storm.
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
    type: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    carries: Optional[str] = None
    owner: Optional[str] = None


@dataclass
class Setting:
    name: str
    landmark: str
    shelter: str


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[str] = field(default_factory=set)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

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
    name: str
    place: str
    mood: str
    seed: Optional[int] = None


@dataclass(frozen=True)
class Tale:
    id: str
    warning_rhythm: str
    first_clue: str
    danger: str
    deed: str
    result: str
    final_image: str
    lesson: str


SETTINGS = {
    "reed marsh": Setting("the reed marsh", "the old footbridge", "the beaver lodge"),
    "pine hollow": Setting("pine hollow", "the fallen cedar", "the fox den"),
    "berry meadow": Setting("berry meadow", "the stone well", "the rabbit burrow"),
}

NAMES = ["Hunk", "Bram", "Moss", "Pip", "Juniper", "Tumble"]
MOODS = ["cheerful", "watchful", "kind", "curious"]

TALES = [
    Tale(
        "bridge_storm",
        "a soft jazz beat: tap, tap-tap, hush",
        "the reeds bent toward the bridge even though no wind touched them",
        "a swollen stream rushing beneath the old footbridge",
        "carried a coil of vine to the far bank so the smaller animals could cross",
        "The vine held fast, and every animal reached the beaver lodge before the rain burst open.",
        "Hunk's muddy footprints formed a brave little line from the bridge to the warm lodge.",
        "A warning becomes useful when someone listens and acts for others.",
    ),
    Tale(
        "cedar_lightning",
        "a low jazz rumble under the woodpecker's tapping",
        "the ants hurried uphill with crumbs still balanced on their backs",
        "lightning striking near the fallen cedar",
        "guided the frightened animals away from the cedar and into a fern-covered hollow",
        "The animals escaped just before a bright crack split the sky above the old tree.",
        "The fern hollow glowed with fireflies while the storm rolled safely past.",
        "Small signs can point toward a large danger.",
    ),
    Tale(
        "well_flood",
        "three jazz notes from the dry grass: plink, plonk, plink",
        "a ring of beetles climbed the stone well in a silent line",
        "rainwater flooding the path around the stone well",
        "dug a shallow channel that led the rising water away from the rabbit burrow",
        "The water flowed into the meadow, leaving the burrow dry and the beetles safe.",
        "At sunrise, the new channel shone like a silver ribbon beside the burrow.",
        "A thoughtful deed can turn fear into a safe path.",
    ),
]

OPENINGS = [
    "One bright morning",
    "Before breakfast",
    "When the first bees began to hum",
    "At the edge of a warm afternoon",
]

DIALOGUE_REQUESTS = [
    "Did you hear that beat?",
    "Should we follow the strange music?",
    "What do the animals know that we do not?",
]

ASP_RULES = r"""
warning :- jazz_sign, danger_near.
deed_ready :- warning, hunk_listens.
safe :- deed_ready, helpful_deed.
#show warning/0.
#show deed_ready/0.
#show safe/0.
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("jazz_sign"),
            asp.fact("danger_near"),
            asp.fact("hunk_listens"),
            asp.fact("helpful_deed"),
        ]
    )


def asp_program(show: str = "#show safe/0.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program())
    names = {atom.name for atom in model}
    expected = {"warning", "deed_ready", "safe"}
    if expected.issubset(names):
        print("OK: ASP and Python agree that the helpful deed makes the animals safe.")
        return 0
    print("MISMATCH: ASP did not derive the expected safe outcome.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate an animal story about Hunk, a deed, and jazz foreshadowing."
    )
    parser.add_argument("--name", choices=NAMES)
    parser.add_argument("--place", choices=sorted(SETTINGS))
    parser.add_argument("--mood", choices=MOODS)
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
        place=args.place or rng.choice(list(SETTINGS)),
        mood=args.mood or rng.choice(MOODS),
    )


def tell(params: StoryParams) -> World:
    if params.place not in SETTINGS:
        raise StoryError(f"Unknown place: {params.place}")
    if params.name not in NAMES:
        raise StoryError(f"Unknown animal name: {params.name}")

    base = params.seed
    if base is None:
        base = sum(ord(c) for c in f"{params.name}|{params.place}|{params.mood}")
    cursor = base
    tale = TALES[cursor % len(TALES)]
    cursor //= len(TALES)
    opening = OPENINGS[cursor % len(OPENINGS)]
    cursor //= len(OPENINGS)
    question = DIALOGUE_REQUESTS[cursor % len(DIALOGUE_REQUESTS)]

    world = World(SETTINGS[params.place])
    hunk = world.add(
        Entity(
            id="hunk",
            kind="animal",
            label=params.name,
            type="badger",
            memes={"courage": 0.0, "attention": 0.0, "care": 1.0},
        )
    )
    jazz = world.add(
        Entity(
            id="jazz",
            kind="sound",
            label="jazz",
            type="warning_rhythm",
            memes={"urgency": 1.0},
        )
    )
    danger = world.add(
        Entity(
            id="danger",
            kind="threat",
            label=tale.danger,
            type="weather_danger",
            meters={"near": 1.0},
        )
    )
    world.facts.update(tale=tale, hunk=hunk, jazz=jazz, danger=danger, question=question)

    world.say(f"{opening}, {params.name} the badger explored {world.setting.name}.")
    world.say(
        f"Near {world.setting.landmark}, {params.name} heard {tale.warning_rhythm} behind the grass."
    )
    world.say(f"The sound was jazz, but it did not feel like music for dancing.")

    world.para()
    hunk.memes["attention"] = 1.0
    world.say(f"{params.name} noticed that {tale.first_clue}.")
    world.say(f'"{question}" asked Pip the field mouse.')
    world.say(f'"It may be a warning," said {params.name}. "Let us watch before we run."')
    world.say(
        f"Far away, the animals heard {tale.danger}; the strange jazz had told the truth."
    )

    world.para()
    hunk.memes["courage"] = 1.0
    hunk.meters["chose_deed"] = 1.0
    world.say(f"{params.name} chose a brave deed and {tale.deed}.")
    world.say(
        f"Pip squeaked, \"That is dangerous!\" {params.name} answered, \"Then stay close and help me think.\""
    )
    world.say(tale.result)
    hunk.meters["animals_safe"] = 1.0
    world.fired.add("warning")
    world.fired.add("helpful_deed")

    world.para()
    world.say(
        f"When the danger passed, the animals thanked {params.name}. {tale.lesson}"
    )
    world.say(f"{tale.final_image} The jazz faded into a gentle evening rhythm.")
    return world


def generation_prompts(world: World) -> list[str]:
    tale: Tale = world.facts["tale"]  # type: ignore[assignment]
    hunk: Entity = world.facts["hunk"]  # type: ignore[assignment]
    return [
        f"Write an animal story about {hunk.label} the badger hearing jazz that foreshadows {tale.danger}.",
        f"Tell how {hunk.label} performs a brave deed: {tale.deed}.",
        f"Write a child-facing story ending with this image: {tale.final_image}",
    ]


def story_qa(world: World) -> list[QAItem]:
    tale: Tale = world.facts["tale"]  # type: ignore[assignment]
    hunk: Entity = world.facts["hunk"]  # type: ignore[assignment]
    return [
        QAItem(
            "Who was Hunk in the story?",
            f"{hunk.label} was a watchful badger who cared about the other animals.",
        ),
        QAItem(
            "What did the jazz foreshadow?",
            f"The strange jazz foreshadowed {tale.danger}.",
        ),
        QAItem(
            f"What deed did {hunk.label} do?",
            f"{hunk.label} {tale.deed}.",
        ),
        QAItem(
            "How did the story end?",
            tale.result,
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What is foreshadowing?",
            "Foreshadowing is a clue early in a story that hints at something that will happen later.",
        ),
        QAItem(
            "What is jazz?",
            "Jazz is a kind of music with lively rhythms and room for musicians to respond to one another.",
        ),
        QAItem(
            "What is a deed?",
            "A deed is something a person or animal does, especially an action that can have an important result.",
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
            f"{entity.id}: {entity.type} {entity.label} "
            f"meters={entity.meters} memes={entity.memes}"
        )
    lines.append(f"fired={sorted(world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("Hunk", "reed marsh", "watchful", 101),
    StoryParams("Moss", "pine hollow", "kind", 202),
    StoryParams("Juniper", "berry meadow", "curious", 303),
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
        print(asp_program())
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program())
        print("safe:", any(atom.name == "safe" for atom in model))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        samples = []
        seen: set[str] = set()
        index = 0
        while len(samples) < max(0, args.n):
            rng = random.Random(base_seed + index)
            params = resolve_params(args, rng)
            params.seed = base_seed + index
            sample = generate(params)
            if sample.story not in seen:
                samples.append(sample)
                seen.add(sample.story)
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
