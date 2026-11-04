#!/usr/bin/env python3
"""
A small animal-story world set in a picnic meadow.

Seed tale:
---
At a picnic in the meadow, a young raccoon gathered every treat for himself.
A kind rabbit offered to share a basket, but he would not listen. A gust
tumbled his pile into the grass, and the other animals went home while he sat
beside an empty blanket. The rabbit offered to help him clean up, but the
raccoon had already lost the feast. He learned that keeping everything can
leave you with nothing to share.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

for _parent in Path(__file__).resolve().parents:
    if (_parent / "results.py").is_file():
        sys.path.insert(0, str(_parent))
        break
from results import QAItem, StoryError, StorySample  # noqa: E402


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str
    type: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Setting:
    id: str
    place: str
    affords: set[str] = field(default_factory=set)


@dataclass
class StoryState:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    scenario: str
    hero_animal: str
    friend_animal: str
    hero_name: str
    friend_name: str
    opening: int = 0
    seed: Optional[int] = None


SETTING = Setting(
    id="picnic_meadow",
    place="the picnic meadow",
    affords={"picnic", "sharing", "animal_friends"},
)

ANIMALS = {
    "raccoon": "raccoon",
    "squirrel": "squirrel",
    "magpie": "magpie",
    "rabbit": "rabbit",
    "mouse": "mouse",
    "hedgehog": "hedgehog",
}
HERO_ANIMALS = ("raccoon", "squirrel", "magpie")
FRIEND_ANIMALS = ("rabbit", "mouse", "hedgehog")

NAMES = {
    "raccoon": ("Rollo", "Mittens", "Pebble"),
    "squirrel": ("Tansy", "Acorn", "Pip"),
    "magpie": ("Mira", "Jingle", "Skye"),
    "rabbit": ("Fern", "Clover", "Bramble"),
    "mouse": ("Pip", "Dot", "Nim"),
    "hedgehog": ("Hazel", "Prickle", "Moss"),
}

SCENARIOS = {
    "berries": {
        "food": "strawberries",
        "container": "a little tin pail",
        "hoard": "heaped every strawberry into his own pail",
        "offer": "We could put the berries in one basket and share them.",
        "decline": "I want them all for myself. I can manage my own pail.",
        "warning": "The pail is nearly full, and the handle is caught on the blanket.",
        "event": "a gust tugged the blanket and tipped the pail",
        "loss": "The strawberries bounced into the long grass, where their red skins split.",
        "ending": "The blanket lay bare, and Rollo sat beside his empty pail as his friends headed home.",
        "lesson": "keeping every treat left him with none to enjoy",
        "prop": "tin pail",
    },
    "seedcakes": {
        "food": "seedcakes",
        "container": "a blue cloth",
        "hoard": "stacked every seedcake in a tall tower on the cloth",
        "offer": "Let's make two small piles so everyone can have one.",
        "decline": "No, the tallest pile is mine. I can keep it steady.",
        "warning": "That tower is wobbling, and the cloth is on a slope.",
        "event": "the top seedcake slid and the whole tower toppled",
        "loss": "The cakes crumbled in the dusty grass before anyone could catch them.",
        "ending": "The blue cloth was empty, and Squirrel watched his friends walk home without a snack.",
        "lesson": "a treat kept only for himself could not make a happy picnic",
        "prop": "blue cloth",
    },
    "apples": {
        "food": "apple slices",
        "container": "a flat picnic plate",
        "hoard": "piled all the apple slices high on one plate",
        "offer": "We can pass the plate around so everyone gets a slice.",
        "decline": "I want the whole pile close to me. Nobody needs to pass it.",
        "warning": "The plate is balanced on that round stump.",
        "event": "the plate rocked when a breeze shook the stump",
        "loss": "Apple slices slid into the grass and picked up little bits of dirt.",
        "ending": "The stump stood bare, and Magpie watched the others leave while she faced her empty plate.",
        "lesson": "sharing would have kept the picnic pleasant for everyone",
        "prop": "picnic plate",
    },
    "corn": {
        "food": "sweet corn pieces",
        "container": "a yellow napkin",
        "hoard": "wrapped every sweet corn piece in his own napkin",
        "offer": "We can set the corn out where all our friends can reach it.",
        "decline": "I will keep it tucked right beside me. It is all mine.",
        "warning": "The corner of your napkin is fluttering in the wind.",
        "event": "a stronger gust lifted the napkin from the blanket",
        "loss": "The corn scattered through the grass, and the hungry ants found it first.",
        "ending": "The yellow napkin was empty, and Squirrel sat alone as his friends walked home.",
        "lesson": "kindness would have made the picnic better than keeping everything",
        "prop": "yellow napkin",
    },
}

OPENINGS = [
    "Sunlight warmed the picnic meadow as {hero} spread a bright blanket for a feast with friends.",
    "A soft breeze wandered through the picnic meadow while {hero} brought a basket of {food} to the blanket.",
    "At the picnic meadow, {hero} and {friend} found a sunny spot beneath a leafy tree.",
    "Birdsong filled the picnic meadow as {hero} set out a treat for the afternoon picnic.",
]

ASP_RULES = r"""
#show valid/2.

valid(S, bad_ending) :-
    scenario(S),
    selfish_choice(S),
    kindness_offer(S),
    loss(S).
"""


def asp_facts() -> str:
    import asp

    lines = []
    for scenario in SCENARIOS:
        lines.extend(
            [
                asp.fact("scenario", scenario),
                asp.fact("selfish_choice", scenario),
                asp.fact("kindness_offer", scenario),
                asp.fact("loss", scenario),
            ]
        )
    return "\n".join(lines)


def asp_program(show: str = "#show valid/2.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def python_valid() -> list[tuple]:
    return sorted((scenario, "bad_ending") for scenario in SCENARIOS)


def asp_verify() -> int:
    asp_combos = set(asp_valid())
    python_combos = set(python_valid())
    if asp_combos == python_combos:
        print(f"OK: clingo gate matches Python gate ({len(asp_combos)} combinations).")
        return 0
    print("MISMATCH between clingo and Python:")
    if asp_combos - python_combos:
        print("  only in clingo:", sorted(asp_combos - python_combos))
    if python_combos - asp_combos:
        print("  only in Python:", sorted(python_combos - asp_combos))
    return 1


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------
def _check_name(name: str) -> bool:
    return bool(re.fullmatch(r"[A-Za-z][A-Za-z'-]{0,19}", name))


def build_world(params: StoryParams) -> StoryState:
    if params.scenario not in SCENARIOS:
        raise StoryError(f"Unknown picnic scenario: {params.scenario!r}.")
    if params.hero_animal not in HERO_ANIMALS:
        raise StoryError(f"Unknown hero animal: {params.hero_animal!r}.")
    if params.friend_animal not in FRIEND_ANIMALS:
        raise StoryError(f"Unknown friend animal: {params.friend_animal!r}.")
    if not _check_name(params.hero_name) or not _check_name(params.friend_name):
        raise StoryError("Names must be 1–20 letters, apostrophes, or hyphens.")
    if params.hero_name.casefold() == params.friend_name.casefold():
        raise StoryError("The hero and friend need different names.")

    scene = SCENARIOS[params.scenario]
    world = StoryState(setting=SETTING)
    hero = world.add(
        Entity(
            id="hero",
            kind="character",
            type=params.hero_animal,
            label=params.hero_name,
            meters={"fullness": 0.2, "distance_from_friends": 0.0},
            memes={"greed": 0.2, "loneliness": 0.0},
        )
    )
    friend = world.add(
        Entity(
            id="friend",
            kind="character",
            type=params.friend_animal,
            label=params.friend_name,
            meters={"fullness": 0.2, "distance_from_friends": 0.0},
            memes={"kindness": 0.8, "concern": 0.2},
        )
    )
    food = world.add(
        Entity(
            id="picnic_food",
            kind="thing",
            type="food",
            label=scene["food"],
            meters={"amount": 1.0, "tidiness": 0.8},
            memes={"shared": 0.0},
        )
    )
    prop = world.add(
        Entity(
            id="picnic_prop",
            kind="thing",
            type="picnic_gear",
            label=scene["prop"],
            meters={"stability": 0.8},
            memes={"usefulness": 0.7},
        )
    )

    opening = OPENINGS[params.opening % len(OPENINGS)].format(
        hero=params.hero_name, friend=params.friend_name, food=scene["food"]
    )
    world.say(opening)
    world.say(
        f"{params.friend_name}, a kind {params.friend_animal}, smiled. "
        f'"The {scene["food"]} smells lovely. {scene["offer"]}"'
    )
    world.say(
        f"{params.hero_name} gathered the treats and {scene['hoard']}. "
        f'"{scene["decline"]}"'
    )
    hero.memes["greed"] = 1.0
    food.memes["shared"] = 0.0
    world.facts["kindness_offered"] = True
    world.facts["sharing_refused"] = True

    world.para()
    world.say(
        f"{params.friend_name} pointed to the trouble. "
        f'"{scene["warning"]} Let me help you arrange it safely."'
    )
    world.say(
        f'"I know what I am doing," said {params.hero_name}, turning away from the offer.'
    )
    world.say(f"Just then, {scene['event']}. {scene['loss']}")
    prop.meters["stability"] = 0.0
    food.meters["amount"] = 0.0
    food.meters["tidiness"] = 0.0
    hero.meters["distance_from_friends"] = 1.0
    hero.memes["loneliness"] = 1.0
    friend.memes["concern"] = 0.8
    world.facts["bad_ending"] = True
    world.facts["food_lost"] = True

    world.para()
    world.say(
        f"{params.friend_name} still offered a paw. "
        f'"I can help you tidy up, {params.hero_name}. I am sorry the food is gone."'
    )
    world.say(
        f"{params.hero_name} looked at the scattered crumbs, but there was nothing left "
        f"to share. {params.friend_name} waited kindly while the other animals folded "
        f"the blanket and started for home."
    )
    world.say(
        f"At last, {params.hero_name} understood that {scene['lesson']}. "
        f"{scene['ending']}"
    )

    world.facts.update(
        hero=hero,
        friend=friend,
        food=food,
        prop=prop,
        scene=scene,
        place=SETTING.place,
    )
    return world


# ---------------------------------------------------------------------------
# Questions and answers
# ---------------------------------------------------------------------------
def generation_prompts(world: StoryState) -> list[str]:
    facts = world.facts
    scene = facts["scene"]
    hero = facts["hero"].label
    friend = facts["friend"].label
    return [
        f"Write an animal story in {facts['place']} where {hero} learns what happens after refusing to share {scene['food']}.",
        f"Tell a child-friendly bad-ending picnic story with a selfish choice and a kind offer from {friend}.",
        f"Include the whimsical seed word tuvwxy, a brief spoken exchange, and a clear consequence for the animals.",
    ]


def story_qa(world: StoryState) -> list[QAItem]:
    facts = world.facts
    scene = facts["scene"]
    hero = facts["hero"].label
    friend = facts["friend"].label
    return [
        QAItem(
            question=f"What did {hero} do with the picnic food?",
            answer=f"{hero} kept the {scene['food']} to himself instead of sharing it with the other animals. When {scene['event']}, the food was lost.",
        ),
        QAItem(
            question=f"How did {friend} try to show kindness?",
            answer=f"{friend} offered to share the food and warned {hero} about the trouble. Later, {friend} still offered to help tidy up after the food was lost.",
        ),
        QAItem(
            question=f"Why did the picnic end badly for {hero}?",
            answer=f"{hero} refused to share and ignored {friend}'s warning. Then {scene['loss']} With no food left, the friends went home.",
        ),
        QAItem(
            question=f"What did {hero} learn at the end?",
            answer=f"{hero} learned that {scene['lesson']}. The empty {scene['prop']} showed what the choice had cost.",
        ),
    ]


def world_knowledge_qa(world: StoryState) -> list[QAItem]:
    return [
        QAItem(
            question="Why can sharing help friends enjoy a picnic?",
            answer="Sharing lets everyone have a turn and helps friends enjoy the meal together.",
        ),
        QAItem(
            question="How can someone respond kindly when a friend makes a mistake?",
            answer="Someone can speak gently, offer practical help, and give the friend a chance to make a better choice next time.",
        ),
        QAItem(
            question="What might a breeze do to a picnic blanket?",
            answer="A breeze can lift a loose blanket or napkin, so picnic things should be kept steady and secure.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    lines.extend(["", "== (2) Story questions =="])
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.extend(["", "== (3) World-knowledge questions =="])
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def dump_trace(world: StoryState) -> str:
    lines = ["--- world model state ---", f"  setting: {world.setting.place}"]
    for entity in world.entities.values():
        lines.append(
            f"  {entity.label:16} ({entity.type:12}) "
            f"meters={entity.meters} memes={entity.memes}"
        )
    lines.append(
        "  outcome: "
        + ("bad ending after food was lost" if world.facts.get("bad_ending") else "unresolved")
    )
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------
def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    scenario = args.scenario or rng.choice(tuple(SCENARIOS))
    hero_animal = args.hero_animal or rng.choice(HERO_ANIMALS)
    friend_animal = args.friend_animal or rng.choice(FRIEND_ANIMALS)

    hero_name = args.hero_name or rng.choice(NAMES[hero_animal])
    friend_name = args.friend_name or rng.choice(NAMES[friend_animal])
    if friend_name.casefold() == hero_name.casefold():
        alternatives = [n for n in NAMES[friend_animal] if n.casefold() != hero_name.casefold()]
        friend_name = rng.choice(alternatives)
    return StoryParams(
        scenario=scenario,
        hero_animal=hero_animal,
        friend_animal=friend_animal,
        hero_name=hero_name,
        friend_name=friend_name,
        opening=rng.randrange(len(OPENINGS)),
        seed=args.seed,
    )


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


# ---------------------------------------------------------------------------
# Verification and command line
# ---------------------------------------------------------------------------
def verify_stories() -> int:
    failures = []
    for i, scenario in enumerate(SCENARIOS):
        params = StoryParams(
            scenario=scenario,
            hero_animal="raccoon",
            friend_animal="rabbit",
            hero_name="Rollo",
            friend_name="Fern",
            opening=i % len(OPENINGS),
            seed=i,
        )
        sample = generate(params)
        text = sample.story
        if "tuvwxy" not in text:
            failures.append(f"{scenario}: missing seed word")
        if "said " not in text or '"' not in text:
            failures.append(f"{scenario}: missing spoken dialogue")
        if "empty" not in text or "home" not in text:
            failures.append(f"{scenario}: missing consequence or ending image")
        if not sample.story_qa or not sample.world_qa:
            failures.append(f"{scenario}: missing questions")
        if "{" in text or "}" in text or "None" in text:
            failures.append(f"{scenario}: unresolved text")
    if failures:
        print("Story verification failed:")
        for failure in failures:
            print(f"  {failure}")
        return 1
    print(f"OK: all {len(SCENARIOS)} generated stories have dialogue, consequences, and endings.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Animal story world: kindness and a bad picnic ending in the meadow."
    )
    ap.add_argument("--scenario", choices=SCENARIOS)
    ap.add_argument("--hero-animal", choices=HERO_ANIMALS)
    ap.add_argument("--friend-animal", choices=FRIEND_ANIMALS)
    ap.add_argument("--hero-name")
    ap.add_argument("--friend-name")
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def main() -> None:
    args = build_parser().parse_args()

    if args.n < 1 and not args.all:
        raise StoryError("-n must be at least 1.")
    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        import asp

        sys.exit(asp_verify() or verify_stories())
    if args.asp:
        combos = asp_valid()
        print(f"{len(combos)} valid combinations:\n")
        for scenario, ending in combos:
            print(f"  {scenario:12} {ending}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for i, scenario in enumerate(SCENARIOS):
            params = StoryParams(
                scenario=scenario,
                hero_animal="raccoon",
                friend_animal="rabbit",
                hero_name="Rollo",
                friend_name="Fern",
                opening=i % len(OPENINGS),
                seed=base_seed + i,
            )
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        attempts = 0
        while len(samples) < args.n and attempts < max(100, args.n * 40):
            rng = random.Random(base_seed + attempts)
            attempts += 1
            params = resolve_params(args, rng)
            params.seed = base_seed + attempts
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
        if len(samples) < args.n:
            raise StoryError(
                f"Could generate only {len(samples)} distinct stories from the chosen options."
            )

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
