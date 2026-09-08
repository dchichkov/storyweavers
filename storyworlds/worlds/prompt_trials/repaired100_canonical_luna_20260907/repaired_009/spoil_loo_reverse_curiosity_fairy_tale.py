#!/usr/bin/env python3
"""
A small fairy-tale storyworld about Luna, a curious child, a spoiled magic loo,
and a reverse spell that turns a messy problem into a useful surprise.
"""

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
from typing import Optional

_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    _storyworlds_dir = os.path.dirname(_storyworlds_dir)
sys.path.insert(0, _storyworlds_dir)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass(frozen=True)
class Tale:
    id: str
    problem: str
    danger: str
    discovery: str
    answer: str
    ending: str


@dataclass
class World:
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict[str, object] = field(default_factory=dict)

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


PLACES = {
    "moon_garden": "the Moon Garden",
    "old_tower": "the old tower",
    "rose_court": "the rose court",
}

NAMES = ["Luna", "Mira", "Pip", "Elian", "Nell"]
ROYAL_NAMES = ["Queen Orla", "King Rowan", "Aunt Bea"]
TRAITS = ["brave", "patient", "bright-eyed", "kind", "clever"]

TALES = {
    "silver_loo": Tale(
        id="silver_loo",
        problem="the palace loo had been spoiled by a goblin's muddy spell",
        danger="the muddy water was creeping toward the moon garden",
        discovery="a silver button hidden beneath the cistern",
        answer="Luna turned the charm in reverse, so the mud flowed back into the goblin's empty bucket",
        ending="the loo shone cleanly, and moon lilies opened around it",
    ),
    "backward_bubbles": Tale(
        id="backward_bubbles",
        problem="the enchanted loo was puffing soap bubbles through every room",
        danger="the bubbles were lifting the castle's small treasures toward the rafters",
        discovery="the bubbles popped whenever Luna whispered the spell backward",
        answer="Luna spoke the reverse charm and guided every bubble down into a waiting basin",
        ending="the treasures returned to their shelves, sparkling like stars",
    ),
    "royal_flush": Tale(
        id="royal_flush",
        problem="a spoiled loo had forgotten how to carry water away",
        danger="the rising water could soak the queen's storybooks",
        discovery="a crooked rune on the handle pointed in the reverse direction",
        answer="Luna reversed the rune and sent the water through a hidden pipe beneath the floor",
        ending="the storybooks stayed dry, and the loo gave a cheerful little chime",
    ),
    "singing_cistern": Tale(
        id="singing_cistern",
        problem="the castle loo sang one loud note after a fairy sprinkled it with pepper dust",
        danger="the endless song was frightening the sleeping dragons",
        discovery="the note changed when Luna turned the listening cup upside down",
        answer="Luna reversed the cup and caught the song inside it until the dragons slept peacefully",
        ending="the cup became a tiny bell that sang only at breakfast",
    ),
}

ASP_RULES = r"""
safe(T) :- tale(T), reverse(T), curiosity(T).
valid_tale(T) :- safe(T), has_problem(T), has_answer(T).
"""


def asp_facts() -> str:
    import asp

    lines = []
    for tale_id in TALES:
        lines.extend(
            [
                asp.fact("tale", tale_id),
                asp.fact("reverse", tale_id),
                asp.fact("curiosity", tale_id),
                asp.fact("has_problem", tale_id),
                asp.fact("has_answer", tale_id),
            ]
        )
    return "\n".join(lines)


def asp_program(show: str = "#show valid_tale/1.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> set[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return set(asp.atoms(model, "valid_tale"))


def valid_tales() -> set[tuple[str]]:
    return {(key,) for key in TALES}


@dataclass
class StoryParams:
    place: str
    name: str
    royal: str
    trait: str
    tale: str
    opening: int = 0
    turn: int = 0
    ending: int = 0
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A fairy-tale storyworld about Luna, curiosity, a spoiled loo, and a reverse spell."
    )
    parser.add_argument("--place", choices=PLACES)
    parser.add_argument("--name", choices=NAMES)
    parser.add_argument("--royal", choices=ROYAL_NAMES)
    parser.add_argument("--trait", choices=TRAITS)
    parser.add_argument("--tale", choices=TALES)
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
    tale_id = args.tale or rng.choice(sorted(TALES))
    return StoryParams(
        place=args.place or rng.choice(sorted(PLACES)),
        name=args.name or rng.choice(NAMES),
        royal=args.royal or rng.choice(ROYAL_NAMES),
        trait=args.trait or rng.choice(TRAITS),
        tale=tale_id,
        opening=rng.randrange(3),
        turn=rng.randrange(3),
        ending=rng.randrange(3),
    )


def build_world(params: StoryParams) -> World:
    if params.place not in PLACES:
        raise StoryError(f"Unknown fairy-tale place: {params.place}")
    if params.tale not in TALES:
        raise StoryError(f"Unknown tale: {params.tale}")

    tale = TALES[params.tale]
    world = World(PLACES[params.place])
    luna = world.add(
        Entity(
            id="hero",
            kind="child",
            label=params.name,
            meters={"damp": 0.0, "mess": 0.0},
            memes={"curiosity": 1.0, "courage": 0.0, "wonder": 0.0},
        )
    )
    royal = world.add(
        Entity(
            id="royal",
            kind="helper",
            label=params.royal,
            meters={"worry": 1.0},
            memes={"trust": 0.0},
        )
    )
    loo = world.add(
        Entity(
            id="loo",
            kind="enchanted_fixture",
            label="the enchanted loo",
            meters={"spoil": 1.0, "overflow": 1.0},
            memes={"happiness": 0.0},
        )
    )

    openings = [
        f"{params.name} was the most {params.trait} child in {world.place}, and curiosity followed {params.name} like a little golden bird.",
        f"In {world.place}, {params.name} noticed things no one else did. Even a creaky door and a dripping tap could become a mystery.",
        f"One moonlit morning, {params.name} hurried through {world.place} when a very peculiar sound came from the enchanted loo.",
    ]
    turns = [
        f"{params.name} knelt beside the cistern and studied the marks instead of grabbing the nearest broom.",
        f"Curiosity made {params.name} look behind the loose tile, where a tiny clue waited in the dust.",
        f"{params.name} remembered that fairy spells often hide their answer in their opposite, and began to turn the charm in reverse.",
    ]
    endings = [
        f"After that, {params.name} kept the silver charm in a safe drawer, and {world.place} stayed bright and dry.",
        f"{params.ending + 1} little bells rang in celebration, while {params.name} smiled at the lesson: a curious question can open a careful door.",
        f"From then on, everyone praised {params.name}'s curiosity, especially when a problem looked too strange to touch.",
    ]

    world.say(openings[params.opening % len(openings)])
    world.say(f"But {tale.problem}.")
    world.para()

    world.say(f"{params.royal} hurried in and cried, \"Please help! {tale.danger.capitalize()}!\"")
    world.say(f"\"I will look closely before I act,\" {params.name} replied.")
    royal.memes["trust"] += 1
    luna.memes["curiosity"] += 1
    world.say(f"{tale.discovery.capitalize()} lay beneath the old fitting.")
    world.para()

    world.say(turns[params.turn % len(turns)])
    world.say(f"\"What happens if we do the opposite?\" {params.name} asked.")
    world.say(f"\"A reverse spell? Try it gently,\" said {params.royal}.")
    luna.memes["courage"] += 1
    loo.meters["overflow"] = 0.0
    loo.meters["spoil"] = 0.0
    loo.memes["happiness"] = 1.0
    world.say(f"{tale.answer.capitalize()}.")
    world.para()

    world.say(f"{tale.ending.capitalize()}.")
    world.say(endings[params.ending % len(endings)])

    world.facts.update(hero=luna, royal=royal, loo=loo, tale=tale)
    return world


def prompts(world: World) -> list[str]:
    tale = world.facts["tale"]
    hero = world.facts["hero"]
    return [
        f"Write a fairy tale about {hero.label}'s curiosity and a spoiled loo.",
        f"Tell a gentle story in which {hero.label} uses a reverse spell to solve this problem: {tale.problem}.",
        "Write a child-friendly fairy tale about curiosity, a magical bathroom, and a surprising opposite spell.",
    ]


def story_qa(world: World) -> list[QAItem]:
    tale: Tale = world.facts["tale"]  # type: ignore[assignment]
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    royal: Entity = world.facts["royal"]  # type: ignore[assignment]
    return [
        QAItem("What problem did the story begin with?", f"The story began because {tale.problem}."),
        QAItem(
            f"Why did {royal.label} ask {hero.label} for help?",
            f"{royal.label} was worried because {tale.danger}.",
        ),
        QAItem(
            f"How did {hero.label} solve the problem?",
            f"{hero.label} used curiosity to find {tale.discovery}, then {tale.answer}.",
        ),
        QAItem("What showed that the spell worked?", f"It worked because {tale.ending}."),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What does curiosity mean?",
            "Curiosity is a wish to learn, ask questions, and look closely at something mysterious.",
        ),
        QAItem(
            "What does reverse mean?",
            "Reverse means to turn something around or make it go in the opposite direction.",
        ),
        QAItem(
            "What does spoil mean in this story?",
            "To spoil something means to make it dirty, damaged, or no longer work as it should.",
        ),
        QAItem(
            "What is a loo?",
            "A loo is a polite word for a bathroom or toilet.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(sample.prompts)
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for entity in world.entities.values():
        meters = {key: value for key, value in entity.meters.items() if value}
        memes = {key: value for key, value in entity.memes.items() if value}
        lines.append(f"{entity.label}: meters={meters} memes={memes}")
    return "\n".join(lines)


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


def asp_verify() -> int:
    python_values = valid_tales()
    asp_values = asp_valid()
    if python_values == asp_values:
        print(f"OK: ASP and Python agree on {len(python_values)} valid tales.")
        for params in CURATED:
            sample = generate(params)
            if not sample.story or "{" in sample.story or "}" in sample.story:
                print("Generated-story check failed.")
                return 1
        print("OK: generated stories passed the prose check.")
        return 0
    print("Mismatch between ASP and Python:")
    print("Only Python:", sorted(python_values - asp_values))
    print("Only ASP:", sorted(asp_values - python_values))
    return 1


CURATED = [
    StoryParams(
        place="moon_garden",
        name="Luna",
        royal="Queen Orla",
        trait="bright-eyed",
        tale="silver_loo",
        opening=0,
        turn=0,
        ending=0,
    ),
    StoryParams(
        place="old_tower",
        name="Mira",
        royal="King Rowan",
        trait="clever",
        tale="backward_bubbles",
        opening=1,
        turn=1,
        ending=1,
    ),
    StoryParams(
        place="rose_court",
        name="Pip",
        royal="Aunt Bea",
        trait="brave",
        tale="royal_flush",
        opening=2,
        turn=2,
        ending=2,
    ),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return

    if args.verify:
        raise SystemExit(asp_verify())

    if args.asp:
        print(asp_program())
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        attempts = 0
        while len(samples) < args.n and attempts < max(50, args.n * 50):
            rng = random.Random(base_seed + attempts)
            params = resolve_params(args, rng)
            params.seed = base_seed + attempts
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            attempts += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        header = f"### variant {index + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
