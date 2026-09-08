#!/usr/bin/env python3
"""
A standalone heartwarming storyworld about consent, a ravenous friend, and a
small twist that turns sharing into care.
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

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "storyworlds"))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"hunger": 0.0, "fullness": 0.0, "warmth": 0.0}
        if not self.memes:
            self.memes = {"worry": 0.0, "trust": 0.0, "joy": 0.0}


@dataclass(frozen=True)
class Setting:
    id: str
    place: str
    affordance: str


@dataclass(frozen=True)
class Feast:
    title: str
    food: str
    smell: str
    twist: str
    helper: str
    lesson: str
    ending: str


@dataclass
class StoryParams:
    setting: str
    hero_type: str
    friend_type: str
    hero_name: str
    friend_name: str
    seed: Optional[int] = None


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
    paragraphs: list[str] = field(default_factory=list)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        self.paragraphs.append(text)

    def render(self) -> str:
        return "\n\n".join(self.paragraphs)


SETTINGS = {
    "cottage": Setting("cottage", "the little cottage kitchen", "a wide table for sharing"),
    "garden": Setting("garden", "the sunny garden shelter", "a clean picnic cloth"),
    "lighthouse": Setting("lighthouse", "the warm lighthouse kitchen", "a sturdy wooden bench"),
}

ANIMALS = ["rabbit", "fox", "bear", "raven", "badger", "hedgehog"]

NAMES = {
    "rabbit": ["Luna", "Pip", "Mina"],
    "fox": ["Finn", "Tara", "Roo"],
    "bear": ["Bram", "Mara", "Tess"],
    "raven": ["Raven", "Kite", "Nell"],
    "badger": ["Bix", "Dora", "Moss"],
    "hedgehog": ["Holly", "Puck", "Nia"],
}

FEASTS = [
    Feast(
        "the berry supper",
        "a basket of warm berry buns",
        "sweet berries and toasted oats",
        "the basket held one last bun hidden beneath the napkin",
        "Grandmother Badger",
        "Asking before taking lets sharing feel safe and kind",
        "The last bun was cut into two warm, equal halves.",
    ),
    Feast(
        "the moonlit picnic",
        "a pot of pumpkin soup and soft rolls",
        "cinnamon, pumpkin, and fresh bread",
        "the supposedly empty pot still held a small serving under its ladle",
        "Auntie Raven",
        "A hungry friend needs kindness, but kindness should never erase another friend's choice",
        "Two spoons tapped the bowl while moonlight silvered the picnic cloth.",
    ),
    Feast(
        "the orchard breakfast",
        "a cloth bag of apple cakes",
        "baked apples and honey",
        "the bag contained a second cake saved for someone who had not arrived",
        "Uncle Fox",
        "Care includes asking who the food belongs to before we share it",
        "The arriving neighbor found a cake waiting beside a cup of warm tea.",
    ),
    Feast(
        "the rain-day table",
        "a tray of cheese stars and carrot sticks",
        "melted cheese and crisp carrots",
        "a folded note under the tray said, 'Please ask before opening the blue tin'",
        "Mama Bear",
        "Consent makes a generous surprise feel like a welcome rather than a demand",
        "The blue tin opened only after everyone agreed, and its bright treats made the room glow.",
    ),
]


def _stable_seed(*parts: str) -> int:
    return sum((i + 1) * ord(ch) for i, ch in enumerate("|".join(parts)))


def validate_params(params: StoryParams) -> None:
    if params.setting not in SETTINGS:
        raise StoryError(f"Unknown setting: {params.setting}")
    if params.hero_type not in ANIMALS or params.friend_type not in ANIMALS:
        raise StoryError("Both characters must be animals from the registry.")
    if not params.hero_name.strip() or not params.friend_name.strip():
        raise StoryError("Both characters need names.")
    if params.hero_name == params.friend_name:
        raise StoryError("The two characters must have different names.")


def build_story(world: World, params: StoryParams, feast: Feast, rng: random.Random) -> None:
    hero = world.entities["hero"]
    friend = world.entities["friend"]
    helper = world.entities["helper"]

    opening = [
        f"At {world.setting.place}, {hero.id} the {hero.type} arranged {feast.food} for {feast.title}.",
        f"{hero.id} the {hero.type} had planned {feast.title} at {world.setting.place}, where {world.setting.affordance} waited beneath the window.",
        f"The kitchen smelled of {feast.smell} when {hero.id} the {hero.type} set the table for {feast.title}.",
    ][rng.randrange(3)]
    world.say(opening)

    friend.meters["hunger"] = 2.0
    friend.memes["worry"] = 1.0
    world.say(
        f"Then {friend.id} the {friend.type} arrived ravenous, with a rumbling belly and tired eyes. "
        f'"May I have one?" {friend.id} asked. "You may," said {hero.id}, "but let us decide together which one."'
    )

    world.say(
        f"{hero.id} offered a piece, but paused before reaching for the plate. "
        f'"Would you like me to serve it, or would you rather choose for yourself?" {hero.id} asked. '
        f'"I would like to choose," said {friend.id}.'
    )

    world.say(
        f"Just then, {helper} noticed the napkin and smiled. "
        f'"There is something beneath it," said {helper}. '
        f'"The twist is that the last piece was saved for a neighbor who has not arrived yet."'
    )

    world.facts["consent_requested"] = True
    world.facts["consent_given"] = True
    world.facts["twist_revealed"] = True
    world.facts["food_owner_considered"] = True

    friend.meters["hunger"] = 0.5
    friend.meters["fullness"] = 1.5
    friend.memes["worry"] = 0.0
    friend.memes["trust"] = 2.0
    hero.memes["trust"] = 2.0
    hero.memes["joy"] = 1.0

    world.say(
        f"{hero.id} and {friend.id} did not grab the hidden food. They asked who it belonged to, "
        f"and {helper} explained that the waiting neighbor had a choice too."
    )
    world.say(
        f"Together they {feast.twist.lower()} Then {helper} helped them make a fair plan: "
        f"the ravenous friend could eat the offered portion, while the saved portion stayed safe."
    )
    world.say(
        f'"Thank you for asking instead of guessing," said {friend.id}. '
        f'"Thank you for telling me what you wanted," {hero.id} replied. '
        f'{feast.lesson}.'
    )
    world.say(
        f"{feast.ending} {friend.id}'s belly felt calm, and the table felt welcoming because every guest's choice mattered."
    )

    world.facts.update(
        feast=feast,
        hero=hero,
        friend=friend,
        helper=helper,
        setting=world.setting,
    )


def tell(params: StoryParams) -> World:
    validate_params(params)
    rng = random.Random(
        params.seed
        if params.seed is not None
        else _stable_seed(
            params.setting,
            params.hero_type,
            params.friend_type,
            params.hero_name,
            params.friend_name,
        )
    )
    setting = SETTINGS[params.setting]
    world = World(setting)
    world.add(Entity("hero", "character", params.hero_type, params.hero_name))
    world.add(Entity("friend", "character", params.friend_type, params.friend_name))
    helper_type = rng.choice(["badger", "raven", "bear"])
    helper_name = rng.choice(NAMES[helper_type])
    world.add(Entity("helper", "character", helper_type, helper_name))
    world.add(Entity("meal", "thing", "food", "shared meal"))
    feast = rng.choice(FEASTS)
    build_story(world, params, feast, rng)
    return world


def generation_prompts(world: World) -> list[str]:
    feast: Feast = world.facts["feast"]  # type: ignore[assignment]
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    friend: Entity = world.facts["friend"]  # type: ignore[assignment]
    return [
        f"Write a heartwarming story about {hero.id} asking {friend.id}'s consent before sharing {feast.food}.",
        f"Tell a gentle story in which a ravenous friend is helped without anyone taking away their choice.",
        f"Write a story with a surprising twist: food saved for another guest changes how the characters share.",
    ]


def story_qa(world: World) -> list[QAItem]:
    feast: Feast = world.facts["feast"]  # type: ignore[assignment]
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    friend: Entity = world.facts["friend"]  # type: ignore[assignment]
    helper: Entity = world.facts["helper"]  # type: ignore[assignment]
    setting: Setting = world.facts["setting"]  # type: ignore[assignment]
    return [
        QAItem(
            f"Where did {hero.id} prepare the meal?",
            f"{hero.id} prepared {feast.title} at {setting.place}, using {setting.affordance}.",
        ),
        QAItem(
            f"Why did {friend.id} need food?",
            f"{friend.id} was ravenous, so their belly was rumbling and they needed a kind, safe serving.",
        ),
        QAItem(
            f"How did {hero.id} show respect for consent?",
            f"{hero.id} asked whether {friend.id} wanted the food served or wanted to choose independently, and waited for an answer.",
        ),
        QAItem(
            "What was the twist?",
            f"The twist was that {feast.twist}. The characters realized that the saved food had another person's choice attached to it.",
        ),
        QAItem(
            f"How did {helper.id} help?",
            f"{helper.id} explained who the hidden portion was for and helped the group make a fair plan.",
        ),
        QAItem(
            "What changed by the ending?",
            f"The hungry friend ate the offered portion, the saved portion remained safe, and everyone felt welcome because choices were respected.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What does consent mean?",
            "Consent means freely agreeing to something after understanding what is being asked. A person may also say no or change their mind.",
        ),
        QAItem(
            "What does ravenous mean?",
            "Ravenous means extremely hungry.",
        ),
        QAItem(
            "Why is it important to ask before sharing or taking food?",
            "Asking helps people know what will happen and respects who the food belongs to, whether they want it, and whether they have allergies or other needs.",
        ),
        QAItem(
            "What makes a surprise kind?",
            "A surprise is kind when it does not pressure anyone and still respects each person's choices and belongings.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        lines.append(
            f"  {entity.id}: type={entity.type}, meters={meters}, memes={memes}"
        )
    lines.append(f"  facts={sorted(world.facts)}")
    return "\n".join(lines)


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


ASP_RULES = r"""
animal(rabbit;fox;bear;raven;badger;hedgehog).
setting(cottage;garden;lighthouse).
needs_consent(food).
ravenous(friend).
has_helper.
twist(hidden_saved_food).
valid_story(S) :- setting(S), needs_consent(food), ravenous(friend), has_helper, twist(hidden_saved_food).
"""


def asp_facts() -> str:
    import asp

    facts = []
    for name in SETTINGS:
        facts.append(asp.fact("setting", name))
    for name in ANIMALS:
        facts.append(asp.fact("animal", name))
    facts.extend(
        [
            asp.fact("needs_consent", "food"),
            asp.fact("ravenous", "friend"),
            asp.fact("has_helper"),
            asp.fact("twist", "hidden_saved_food"),
        ]
    )
    return "\n".join(facts)


def asp_program(show: str = "#show valid_story/1.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> set[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return set(asp.atoms(model, "valid_story"))


def asp_verify() -> int:
    import importlib.util

    expected = {("cottage",), ("garden",), ("lighthouse",)}
    actual = asp_valid()
    if actual != expected:
        print("MISMATCH between ASP and Python:", sorted(actual), sorted(expected))
        return 1
    print("OK: ASP gate matches Python expectations.")
    return 0


CURATED = [
    StoryParams("cottage", "rabbit", "raven", "Luna", "Kite"),
    StoryParams("garden", "fox", "hedgehog", "Finn", "Holly"),
    StoryParams("lighthouse", "bear", "rabbit", "Mara", "Pip"),
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Heartwarming consent and sharing storyworld."
    )
    parser.add_argument("--setting", choices=SETTINGS)
    parser.add_argument("--hero-type", choices=ANIMALS)
    parser.add_argument("--friend-type", choices=ANIMALS)
    parser.add_argument("--hero-name")
    parser.add_argument("--friend-name")
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
    hero_type = args.hero_type or rng.choice(ANIMALS)
    friend_type = args.friend_type or rng.choice(ANIMALS)
    hero_name = args.hero_name or rng.choice(NAMES[hero_type])
    friend_name = args.friend_name or rng.choice(
        [name for name in NAMES[friend_type] if name != hero_name]
        or NAMES[friend_type]
    )
    if hero_name == friend_name:
        raise StoryError("Generated character names must be different.")
    return StoryParams(
        setting=args.setting or rng.choice(list(SETTINGS)),
        hero_type=hero_type,
        friend_type=friend_type,
        hero_name=hero_name,
        friend_name=friend_name,
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
        print(asp_program())
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        rows = sorted(asp_valid())
        print(f"{len(rows)} compatible settings:")
        for row in rows:
            print(" ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for index, params in enumerate(CURATED):
            params.seed = base_seed + index
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        attempt = 0
        while len(samples) < max(1, args.n):
            seed = base_seed + attempt
            attempt += 1
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        header = ""
        if args.all:
            params = sample.params
            header = f"### {params.hero_name}: {params.setting}"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
