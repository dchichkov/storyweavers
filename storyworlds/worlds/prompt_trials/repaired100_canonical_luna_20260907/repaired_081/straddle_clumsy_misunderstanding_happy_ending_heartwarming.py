#!/usr/bin/env python3
"""
Story world: a heartwarming garden tale about straddling a puddle, a clumsy
mistake, and a misunderstanding that ends in kindness.
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
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parents[3]
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
    friend_name: str = "Mara"
    object_name: str = "the little garden cart"
    place: str = "the community garden"
    problem: str = "mud"
    seed: Optional[int] = None


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
    lines: list[str] = field(default_factory=list)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        self.lines.append(text)

    def render(self) -> str:
        return " ".join(self.lines)


HERO_NAMES = ["Luna", "Nia", "Pip", "Tessa", "Milo"]
FRIEND_NAMES = ["Mara", "Owen", "Suri", "Ben", "Ivy"]
PLACES = [
    "the community garden",
    "the sunny school garden",
    "the little neighborhood orchard",
    "the flower-filled courtyard",
]
OBJECTS = [
    "the little garden cart",
    "a basket of warm seed packets",
    "the blue watering can",
    "a tray of tiny tomato plants",
]
PROBLEMS = ["mud", "a puddle", "a loose wheel", "a fallen branch"]

ASP_RULES = r"""
hero(H) :- role(H, hero).
friend(F) :- role(F, friend).
straddle(H) :- balanced(H), crossed(H).
clumsy(H) :- stumble(H).
misunderstanding :- friend(F), thinks(F, upset), not truth_explained.
happy_ending :- misunderstanding, truth_explained, repaired.
kind_choice(H) :- hero(H), apologizes(H).
"""


def asp_facts() -> str:
    import asp

    return "\n".join(
        [
            asp.fact("role", "luna", "hero"),
            asp.fact("role", "mara", "friend"),
            asp.fact("balanced", "luna"),
            asp.fact("crossed", "luna"),
            asp.fact("stumble", "luna"),
            asp.fact("thinks", "mara", "upset"),
            asp.fact("truth_explained"),
            asp.fact("repaired"),
            asp.fact("apologizes", "luna"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    shown = (
        "#show straddle/1.\n"
        "#show clumsy/1.\n"
        "#show misunderstanding/0.\n"
        "#show happy_ending/0.\n"
        "#show kind_choice/1."
    )
    model = asp.one_model(asp_program(shown))
    atoms = {str(symbol) for symbol in model}
    wanted = {
        "straddle(luna)",
        "clumsy(luna)",
        "misunderstanding",
        "happy_ending",
        "kind_choice(luna)",
    }
    if atoms == wanted:
        print("OK: ASP and Python parity looks good.")
        return 0
    print("MISMATCH between ASP and Python reasoning.")
    print("ASP:", sorted(atoms))
    print("PY :", sorted(wanted))
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A heartwarming story world about a clumsy misunderstanding."
    )
    parser.add_argument("--name")
    parser.add_argument("--friend")
    parser.add_argument("--place", choices=PLACES)
    parser.add_argument("--object", dest="object_name", choices=OBJECTS)
    parser.add_argument("--problem", choices=PROBLEMS)
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
    friend = args.friend or rng.choice([name for name in FRIEND_NAMES if name != hero])
    if hero == friend:
        raise StoryError("The hero and friend must be different people.")
    return StoryParams(
        hero_name=hero,
        friend_name=friend,
        object_name=args.object_name or rng.choice(OBJECTS),
        place=args.place or rng.choice(PLACES),
        problem=args.problem or rng.choice(PROBLEMS),
    )


def generate(params: StoryParams) -> StorySample:
    if params.hero_name == params.friend_name:
        raise StoryError("A character cannot be both the hero and the friend.")
    if params.problem not in PROBLEMS:
        raise StoryError(f"Unknown problem: {params.problem}")

    seed = params.seed if params.seed is not None else f"{params.hero_name}:{params.problem}"
    rng = random.Random(seed)
    world = World()

    hero = world.add(
        Entity(
            "hero",
            "character",
            params.hero_name,
            meters={"balance": 0.2, "mud": 0.0},
            memes={"confidence": 0.7, "worry": 0.0, "kindness": 0.5},
        )
    )
    friend = world.add(
        Entity(
            "friend",
            "character",
            params.friend_name,
            meters={"distance": 0.0},
            memes={"trust": 0.8, "hurt": 0.0},
        )
    )
    object_entity = world.add(
        Entity(
            "garden_object",
            "object",
            params.object_name,
            meters={"stability": 0.8, "mud": 0.0},
            memes={"importance": 0.6},
        )
    )

    world.say(
        f"At {params.place}, {params.hero_name} and {params.friend_name} were carrying "
        f"{params.object_name} toward a row of new seedlings."
    )
    world.say(
        f"A wide {params.problem} patch blocked the path, so {params.hero_name} tried to "
        f"straddle it while keeping the load steady."
    )
    hero.meters["balance"] = 0.9
    hero.meters["mud"] = 0.4
    world.say(
        f"{params.hero_name} stretched one foot to each side, but the plan was clumsy; "
        f"one shoe slipped and the garden object tipped into the soft ground."
    )
    object_entity.meters["stability"] = 0.2
    object_entity.meters["mud"] = 0.8
    hero.memes["worry"] = 0.8
    friend.memes["hurt"] = 0.5

    world.say(
        f"“You did that on purpose!” {params.friend_name} cried, pulling the seedlings away."
    )
    world.say(
        f"“No, I was trying to straddle the {params.problem} so we would not step on the plants,” "
        f"{params.hero_name} said, blinking at the muddy mess."
    )
    world.say(
        f"The friends had a misunderstanding: {params.friend_name} saw a careless shove, "
        f"while {params.hero_name} had been trying to protect the seedlings."
    )
    world.say(
        f"“I thought you were angry with me,” {params.friend_name} admitted. "
        f"“I thought you were angry with the garden,” {params.hero_name} answered."
    )
    world.say(
        f"That honest back-and-forth changed the feeling between them. "
        f"They looked at the footprints, the bent handle, and the safe seedlings together."
    )

    world.say(
        f"{params.hero_name} took a breath. “I was clumsy, and I should have asked for help. "
        f"I am sorry.”"
    )
    hero.memes["kindness"] = 1.0
    friend.memes["hurt"] = 0.0
    world.say(
        f"{params.friend_name} smiled. “I am sorry too. Let us repair {params.object_name} together.”"
    )
    world.say(
        f"They lifted the muddy object, wiped its handle, and used a flat board to bridge the "
        f"{params.problem} instead of trying to straddle it."
    )
    object_entity.meters["stability"] = 1.0
    object_entity.meters["mud"] = 0.0
    hero.meters["balance"] = 1.0
    hero.meters["mud"] = 0.1
    world.say(
        f"Then they carried the seedlings safely to the garden bed, where every small green "
        f"leaf stood straight in the afternoon light."
    )
    world.say(
        f"The misunderstanding was gone. {params.hero_name} and {params.friend_name} were "
        f"laughing again, and their repaired path made the work easier for everyone."
    )
    world.say(
        f"Before going home, {params.hero_name} painted a little sign: “Ask, listen, and help.” "
        f"{params.friend_name} added two bright hearts beneath it."
    )

    world.facts.update(
        hero=hero,
        friend=friend,
        object=object_entity,
        straddled=True,
        clumsy=True,
        misunderstanding=True,
        truth_explained=True,
        repaired=True,
        happy_ending=True,
    )

    prompts = [
        f"Write a heartwarming story about {params.hero_name} and {params.friend_name} at {params.place}.",
        f"Show how a clumsy attempt to straddle a {params.problem} causes a misunderstanding.",
        "End with honest dialogue, a repair, and a happy ending.",
    ]
    story_qa = [
        QAItem(
            question=f"Why did {params.hero_name} try to straddle the {params.problem}?",
            answer=(
                f"{params.hero_name} tried to straddle the {params.problem} to avoid stepping "
                f"on the seedlings while carrying {params.object_name}."
            ),
        ),
        QAItem(
            question="What caused the misunderstanding?",
            answer=(
                f"{params.hero_name}'s clumsy slip made {params.friend_name} think the garden "
                f"object had been shoved on purpose, although {params.hero_name} was trying to help."
            ),
        ),
        QAItem(
            question="How did the friends resolve the misunderstanding?",
            answer=(
                f"They explained what each person had thought, apologized, and repaired "
                f"{params.object_name} together."
            ),
        ),
        QAItem(
            question="What proved that the ending was happy?",
            answer=(
                f"The seedlings were planted safely, the path was repaired, and the friends "
                f"laughed together while making a kind sign."
            ),
        ),
    ]
    world_qa = [
        QAItem(
            question="What does it mean to straddle something?",
            answer="To straddle something means to stand or sit with it between your legs.",
        ),
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding happens when someone interprets a situation differently from what was meant.",
        ),
        QAItem(
            question="Why can asking questions help friends?",
            answer="Questions let people share what they meant, so mistakes and hurt feelings can be understood more fairly.",
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
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
        print("\n== world qa ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(
            asp_program(
                "#show straddle/1.\n"
                "#show clumsy/1.\n"
                "#show misunderstanding/0.\n"
                "#show happy_ending/0.\n"
                "#show kind_choice/1."
            )
        )
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for index, place in enumerate(PLACES):
            params = StoryParams(
                hero_name=HERO_NAMES[index % len(HERO_NAMES)],
                friend_name=FRIEND_NAMES[index % len(FRIEND_NAMES)],
                object_name=OBJECTS[index % len(OBJECTS)],
                place=place,
                problem=PROBLEMS[index % len(PROBLEMS)],
                seed=base_seed + index,
            )
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        attempt = 0
        while len(samples) < max(0, args.n) and attempt < max(50, args.n * 20):
            rng = random.Random(base_seed + attempt)
            params = resolve_params(args, rng)
            params.seed = base_seed + attempt
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            attempt += 1

    if args.asp:
        import asp

        model = asp.one_model(
            asp_program(
                "#show straddle/1.\n"
                "#show clumsy/1.\n"
                "#show misunderstanding/0.\n"
                "#show happy_ending/0."
            )
        )
        print("ASP model:")
        for symbol in model:
            print(symbol)
        return

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
