#!/usr/bin/env python3
"""
A tiny superhero story world about bacon, an unexpected twist, and reconciliation.
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
    kind: str = "thing"
    label: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class StoryParams:
    city: str = "Brightbell City"
    hero_name: str = "Luna"
    helper_name: str = "Pip"
    power: str = "moonlight shield"
    challenge: str = "stolen breakfast"
    seed: Optional[int] = None


@dataclass
class World:
    city: str
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


CITY_REGISTRY = {
    "Brightbell City": "a city of sunny rooftops and ringing street bells",
    "Maple Harbor": "a harbor city where red boats bobbed beside tall warehouses",
    "Cloudstep Town": "a town of bridges, windmills, and floating gardens",
}

HERO_NAMES = ["Luna", "Nova", "Mira", "Sol", "Rae"]
HELPER_NAMES = ["Pip", "Tess", "Jax", "Ollie", "Bee"]
POWERS = ["moonlight shield", "super speed", "kindness beam", "wind jump"]
CHALLENGES = ["stolen breakfast", "silent alarm", "runaway food cart", "missing picnic"]

ASP_RULES = r"""
hero(H) :- hero_name(H).
helper(H) :- helper_name(H).
food(F) :- food_name(F).
twist(T) :- twist_fact(T).
reconciled(H, A) :- hero_name(H), helper_name(A), apology(H), apology(A), shared_meal.
saved(H) :- hero_name(H), rescued_food, reconciled(H, A).
"""


def asp_facts() -> str:
    import asp

    facts = []
    for city in CITY_REGISTRY:
        facts.append(asp.fact("city_name", city))
    facts.extend(
        [
            asp.fact("hero_name", "hero"),
            asp.fact("helper_name", "helper"),
            asp.fact("food_name", "bacon"),
            asp.fact("twist_fact", "bacon_was_for_rescue_dog"),
            asp.fact("rescued_food"),
            asp.fact("apology", "hero"),
            asp.fact("apology", "helper"),
            asp.fact("shared_meal"),
        ]
    )
    return "\n".join(facts)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    shown = asp.one_model(
        asp_program(
            "#show reconciled/2.\n#show saved/1.\n#show twist/1."
        )
    )
    got = set()
    for symbol in shown:
        args = tuple(
            a.string
            if a.type == a.type.String
            else a.number
            if a.type == a.type.Number
            else a.name
            for a in symbol.arguments
        )
        got.add((symbol.name, args))
    expected = {
        ("reconciled", ("hero", "helper")),
        ("saved", ("hero",)),
        ("twist", ("bacon_was_for_rescue_dog",)),
    }
    if got == expected:
        print("OK: ASP and Python parity looks good.")
        return 0
    print("MISMATCH between ASP and Python reasoning.")
    print("ASP:", sorted(got))
    print("PY :", sorted(expected))
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A superhero story world about bacon, a twist, and reconciliation."
    )
    parser.add_argument("--city", choices=CITY_REGISTRY)
    parser.add_argument("--name")
    parser.add_argument("--helper")
    parser.add_argument("--power", choices=POWERS)
    parser.add_argument("--challenge", choices=CHALLENGES)
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
        raise StoryError("The hero and helper must be different characters.")
    return StoryParams(
        city=args.city or rng.choice(list(CITY_REGISTRY)),
        hero_name=hero,
        helper_name=helper,
        power=args.power or rng.choice(POWERS),
        challenge=args.challenge or rng.choice(CHALLENGES),
    )


def generate(params: StoryParams) -> StorySample:
    if params.city not in CITY_REGISTRY:
        raise StoryError(f"Unknown city: {params.city}")
    if params.hero_name == params.helper_name:
        raise StoryError("The hero and helper must be different characters.")

    rng = random.Random(
        params.seed
        if params.seed is not None
        else f"{params.city}:{params.hero_name}:{params.helper_name}:{params.power}"
    )
    world = World(params.city)

    hero = world.add(
        Entity(
            id="hero",
            kind="character",
            label=params.hero_name,
            memes={"courage": 1.0, "frustration": 0.0, "trust": 0.5},
        )
    )
    helper = world.add(
        Entity(
            id="helper",
            kind="character",
            label=params.helper_name,
            memes={"worry": 1.0, "trust": 0.5},
        )
    )
    bacon = world.add(
        Entity(
            id="bacon",
            kind="food",
            label="a warm strip of bacon",
            owner=helper.id,
            meters={"warmth": 1.0, "distance": 0.0},
            memes={"importance": 1.0},
        )
    )
    cape = world.add(
        Entity(
            id="cape",
            kind="gear",
            label="a silver superhero cape",
            owner=hero.id,
            meters={"flutter": 0.0, "brightness": 1.0},
            memes={"pride": 1.0},
        )
    )

    place = CITY_REGISTRY[params.city]
    world.say(
        f"In {params.city}, {place}, {params.hero_name} wore {cape.label} and watched over the morning streets."
    )
    world.say(
        f"{params.helper_name} carried {bacon.label} from a breakfast stall while the city prepared for its heroes' parade."
    )
    world.say(
        f"Then a gust swept the bacon into a nearby alley, and {params.hero_name} rushed after it with a {params.power}."
    )
    world.say(
        f"“Stand back! I will remove the danger,” {params.hero_name} called, lifting the bacon away from a rattling drain."
    )
    world.say(
        f"“Wait!” {params.helper_name} answered. “That bacon is not danger. I was carrying it to the hungry rescue dog behind the bakery.”"
    )
    world.say(
        f"{params.hero_name} stopped. The rescue dog peeked from behind a crate, and the real twist became clear: the missing bacon had been meant as a meal, not a snack."
    )
    world.say(
        f"{params.hero_name} lowered the {params.power} and said, “I am sorry. I tried to remove the problem before asking what was happening.”"
    )
    world.say(
        f"{params.helper_name} smiled and replied, “I am sorry too. I should have told you where I was going.”"
    )

    bacon.meters["distance"] = 0.0
    bacon.memes["importance"] = 2.0
    hero.memes["frustration"] = 0.0
    hero.memes["trust"] = 1.0
    helper.memes["worry"] = 0.0
    helper.memes["trust"] = 1.0
    cape.meters["flutter"] = 1.0

    world.say(
        f"Together they removed the bacon from the drain, carried it to the rescue dog, and shared a fresh breakfast roll at the bakery."
    )
    world.say(
        f"The reconciliation made their friendship stronger: {params.hero_name} promised to ask first, and {params.helper_name} promised to explain sooner."
    )
    world.say(
        f"When the parade bells rang, the rescue dog wagged beneath the silver cape, and the two friends marched side by side as a true superhero team."
    )

    world.facts.update(
        hero=hero,
        helper=helper,
        bacon=bacon,
        cape=cape,
        twist="The bacon was for a rescue dog.",
        reconciled=True,
        removed_danger=True,
        lesson="Ask before acting, and explain before others worry.",
    )

    prompts = [
        f"Write a Superhero Story about {params.hero_name} protecting {params.city}.",
        f"Include bacon, a moment when {params.hero_name} tries to remove a problem, a surprising twist, and reconciliation with {params.helper_name}.",
        "Make the dialogue change what the heroes understand and do.",
    ]

    story_qa = [
        QAItem(
            question="What did the hero try to remove?",
            answer="The hero tried to remove what seemed to be a dangerous piece of bacon near a rattling drain.",
        ),
        QAItem(
            question="What was the twist?",
            answer="The twist was that the bacon was meant as a meal for a hungry rescue dog, not as a dangerous object or a stolen snack.",
        ),
        QAItem(
            question="How did the friends reconcile?",
            answer=f"{params.hero_name} apologized for acting before asking, and {params.helper_name} apologized for not explaining where the bacon was going.",
        ),
        QAItem(
            question="What lesson did the superhero team learn?",
            answer="They learned to ask questions before acting and to explain their plans so friends do not worry.",
        ),
        QAItem(
            question="What proved that the problem was solved?",
            answer="The bacon reached the rescue dog, the friends shared breakfast, and they marched together in the parade.",
        ),
    ]

    world_qa = [
        QAItem(
            question="What is reconciliation?",
            answer="Reconciliation is making peace after a disagreement by listening, apologizing, and choosing to trust one another again.",
        ),
        QAItem(
            question="Why should a hero ask questions before removing something?",
            answer="A hero should ask questions first because an object that looks dangerous may have an important purpose.",
        ),
        QAItem(
            question="What makes someone a superhero?",
            answer="A superhero uses courage and care to help others, and also learns from mistakes.",
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
            print(
                f"{key}: {entity.label} meters={entity.meters} memes={entity.memes}"
            )
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
                "#show reconciled/2.\n#show saved/1.\n#show twist/1."
            )
        )
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for city in CITY_REGISTRY:
            params = StoryParams(
                city=city,
                hero_name=HERO_NAMES[0],
                helper_name=HELPER_NAMES[0],
                power=POWERS[0],
                challenge=CHALLENGES[0],
                seed=base_seed,
            )
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        index = 0
        while len(samples) < args.n and index < max(50, args.n * 20):
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
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
