#!/usr/bin/env python3
"""
A small fairy-tale storyworld about knickers, a shy sidle, and kindness that
solves a mystery.
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
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Setting:
    id: str
    place: str
    epithet: str
    affords: set[str]
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Mystery:
    id: str
    opening: str
    clue: str
    cause: str
    kindness: str
    proof: str
    ending: str


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
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


SETTINGS = {
    "moonlit_laundry": Setting(
        id="moonlit_laundry",
        place="the moonlit laundry garden",
        epithet="where silver sheets hung between the hawthorn trees",
        affords={"kindness_mystery"},
    )
}

MYSTERIES = {
    "kindness_mystery": Mystery(
        id="kindness_mystery",
        opening="the little prince's clean knickers had vanished before the Moonbeam Feast",
        clue="a trail of blue buttons leading from the clothesline to the old wishing well",
        cause="a frightened hedgehog had carried the knickers away to make a warm nest for her babies",
        kindness="introduced the hedgehog gently, offered her soft spare cloth, and returned the knickers after washing them",
        proof="the hedgehog's babies slept safely in the new nest and the prince had clean clothes for the feast",
        ending="the knickers fluttered like tiny flags while the hedgehog family watched from a basket lined with velvet",
    )
}

NAMES = {
    "girl": ["Luna", "Mira", "Elsie"],
    "boy": ["Theo", "Milo", "Pip"],
}
TRAITS = ["patient", "curious", "gentle", "brave"]
OPENINGS = [
    "Once upon a moon-bright evening, the laundry garden shimmered like a kingdom of stars.",
    "Long ago, behind a little castle, silver sheets danced in the night wind.",
    "In a kingdom where every button had a story, kindness began with noticing a small worry.",
]
WISE_WORDS = [
    "A gentle introduction can open a door that force would only close.",
    "Kindness is often the first clue in a mystery.",
    "When someone is frightened, patience helps the truth come out.",
]


@dataclass
class StoryParams:
    place: str
    mystery: str
    hero_name: str
    hero_type: str
    trait: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str]]:
    return [
        (place, mystery)
        for place, setting in SETTINGS.items()
        for mystery in setting.affords
        if mystery in MYSTERIES
    ]


def build_world(params: StoryParams) -> World:
    if (params.place, params.mystery) not in valid_combos():
        raise StoryError(
            f"Invalid story choice: {params.mystery} is not available in {params.place}."
        )
    setting = SETTINGS[params.place]
    mystery = MYSTERIES[params.mystery]
    rng = random.Random(params.seed)
    world = World(setting)

    hero = world.add(Entity(
        id="hero",
        kind=params.hero_type,
        label=params.hero_name,
        memes={"kindness": 0.5, "curiosity": 0.7},
    ))
    prince = world.add(Entity(
        id="prince",
        kind="child",
        label="the little prince",
        owner="castle",
        memes={"worry": 0.8},
    ))
    hedgehog = world.add(Entity(
        id="hedgehog",
        kind="animal",
        label="the shy hedgehog",
        memes={"fear": 0.9, "trust": 0.1},
    ))
    knickers = world.add(Entity(
        id="knickers",
        kind="clothing",
        label="the little prince's blue knickers",
        owner="prince",
        meters={"warmth": 0.2, "cleanliness": 1.0},
    ))

    opening = rng.choice(OPENINGS)
    reflection = rng.choice(WISE_WORDS)
    world.facts.update(
        hero=hero,
        prince=prince,
        hedgehog=hedgehog,
        knickers=knickers,
        mystery=mystery,
        opening=opening,
        reflection=reflection,
        resolved=False,
        clue_seen=False,
        hedgehog_introduced=False,
    )

    world.say(opening)
    world.say(
        f"{hero.label}, a {params.trait} child, came to help in {setting.place}, "
        f"{setting.epithet}."
    )
    world.say(f"There {mystery.opening}. The little prince searched every basket and cried.")

    world.para()
    world.say(
        f'"Do not worry," said {hero.label}. "We will look carefully, and we will be kind to whoever needs help."'
    )
    world.say(
        f'"What if someone took them?" asked the prince. "Then we must find out why," replied {hero.label}.'
    )
    world.say(f"{hero.label} began to sidle along the clothesline instead of stomping through the garden.")
    world.say(
        f"At the edge of the moonlight, {hero.label} noticed {mystery.clue}."
    )
    world.facts["clue_seen"] = True

    world.para()
    world.say(
        "A tiny rustle came from behind the wishing well. A hedgehog peeked out, holding one blue button."
    )
    world.say(
        f'"Please do not hide," said {hero.label}. "I would like to introduce myself. I am {hero.label}."'
    )
    world.say(
        f'"I am afraid," whispered the hedgehog. "I took the cloth because {mystery.cause[0].lower() + mystery.cause[1:]}"'
    )
    world.say(
        f"{hero.label} knelt at a safe distance and {mystery.kindness}. This made the hedgehog feel seen rather than scolded."
    )
    world.facts["hedgehog_introduced"] = True
    world.facts["cause"] = mystery.cause

    world.para()
    world.say(
        f"The prince received the clean knickers, and the hedgehog received a soft nest of spare cloth."
    )
    world.say(
        f"Everyone checked the result: {mystery.proof}."
    )
    world.say(
        f"{hero.label} said, 'A mystery can hide a need, not just a wrongdoer.' The prince nodded."
    )
    world.say(f"The lesson was clear: {reflection}")
    world.say(f"By moonrise, {mystery.ending}.")
    world.facts["resolved"] = True
    hero.memes["kindness"] = 1.0
    hedgehog.memes["trust"] = 1.0
    return world


KNOWLEDGE = [
    QAItem(
        question="What are knickers?",
        answer="Knickers are short trousers or underclothes worn on the lower part of the body.",
    ),
    QAItem(
        question="What does sidle mean?",
        answer="To sidle means to move quietly and a little sideways, often because someone feels shy or cautious.",
    ),
    QAItem(
        question="What does introduce mean?",
        answer="To introduce means to tell people who someone is or to help people meet for the first time.",
    ),
    QAItem(
        question="What is kindness?",
        answer="Kindness means treating someone with care, patience, and helpful respect.",
    ),
    QAItem(
        question="What is a mystery to solve?",
        answer="A mystery to solve is a puzzling problem that becomes clear when people gather clues and reason carefully.",
    ),
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a fairy tale about {f['hero'].label} solving a mystery involving knickers through kindness.",
        f"Tell a child-facing story in which a shy character sidles near a clue and someone introduces themselves gently.",
        "Write a mystery to solve where kindness reveals why something went missing.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    mystery = f["mystery"]
    return [
        QAItem(
            question="What went missing?",
            answer="The little prince's clean blue knickers went missing before the Moonbeam Feast.",
        ),
        QAItem(
            question="What clue did the hero find?",
            answer=f"The hero found {mystery.clue}.",
        ),
        QAItem(
            question="Who had taken the knickers, and why?",
            answer=f"A frightened hedgehog had taken them because {mystery.cause[0].lower() + mystery.cause[1:]}",
        ),
        QAItem(
            question="How did kindness help solve the mystery?",
            answer=f"The hero did not scold the hedgehog. Instead, the hero {mystery.kindness}, so the hedgehog felt safe enough to explain the truth.",
        ),
        QAItem(
            question="What changed at the end?",
            answer=f"{mystery.proof}. The prince had his clothes, and the hedgehog family had a safe nest.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return list(KNOWLEDGE)


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


ASP_RULES = r"""
#show valid/2.
valid(P, M) :- place(P), mystery(M), affords(P, M).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for place, setting in SETTINGS.items():
        lines.append(asp.fact("place", place))
        for mystery in setting.affords:
            lines.append(asp.fact("affords", place, mystery))
    for mystery in MYSTERIES:
        lines.append(asp.fact("mystery", mystery))
    return "\n".join(lines)


def asp_program(show: str = "#show valid/2.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py != cl:
        print("Mismatch between Python and ASP compatibility gates.")
        print("Only Python:", sorted(py - cl))
        print("Only ASP:", sorted(cl - py))
        return 1
    print(f"OK: ASP and Python agree on {len(py)} compatible story choices.")
    for params in CURATED:
        sample = generate(params)
        if not sample.story or not sample.story_qa:
            print("Generated story verification failed.")
            return 1
    print("OK: generated stories and grounded questions are present.")
    return 0


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        lines.append(
            f"  {entity.id}: kind={entity.kind}, label={entity.label}, "
            f"meters={entity.meters}, memes={entity.memes}"
        )
    lines.append(f"  clue_seen={world.facts.get('clue_seen')}")
    lines.append(f"  hedgehog_introduced={world.facts.get('hedgehog_introduced')}")
    lines.append(f"  resolved={world.facts.get('resolved')}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Fairy-tale storyworld about knickers, sidling, introduction, and kindness."
    )
    parser.add_argument("--place", choices=SETTINGS)
    parser.add_argument("--mystery", choices=MYSTERIES)
    parser.add_argument("--name")
    parser.add_argument("--gender", choices=["girl", "boy"])
    parser.add_argument("--trait", choices=TRAITS)
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
    combos = valid_combos()
    if args.place:
        combos = [combo for combo in combos if combo[0] == args.place]
    if args.mystery:
        combos = [combo for combo in combos if combo[1] == args.mystery]
    if not combos:
        raise StoryError("No compatible place and mystery choices were found.")
    place, mystery = rng.choice(combos)
    gender = args.gender or rng.choice(["girl", "boy"])
    return StoryParams(
        place=place,
        mystery=mystery,
        hero_name=args.name or rng.choice(NAMES[gender]),
        hero_type=gender,
        trait=args.trait or rng.choice(TRAITS),
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


CURATED = [
    StoryParams(
        place="moonlit_laundry",
        mystery="kindness_mystery",
        hero_name="Luna",
        hero_type="girl",
        trait="gentle",
        seed=20260907,
    )
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for place, mystery in asp_valid_combos():
            print(f"{place}: {mystery}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        samples = []
        seen = set()
        for index in range(max(args.n, 1) * 50):
            if len(samples) >= args.n:
                break
            seed = base_seed + index
            rng = random.Random(seed)
            params = resolve_params(args, rng)
            params.seed = seed
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)

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
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
