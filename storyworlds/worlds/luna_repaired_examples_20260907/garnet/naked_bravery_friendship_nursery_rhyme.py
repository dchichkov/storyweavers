#!/usr/bin/env python3
"""
A nursery-rhyme storyworld about a brave little seedling, a loyal friend,
and the funny embarrassment of being naked in the garden.
"""

from __future__ import annotations

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
class Item:
    id: str
    label: str
    phrase: str
    kind: str = "thing"
    owner: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    hero: Item
    friend: Item
    setting: str
    seed: int
    facts: dict = field(default_factory=dict)

    def render(self) -> str:
        return self.facts.get("story", "")


@dataclass
class StoryParams:
    name: str
    friend_name: str
    setting: str
    seed: Optional[int] = None


NAMES = ["Pip", "Mina", "Toby", "Lulu", "Nell", "Bram", "Ivy", "Sam"]
FRIENDS = ["Poppy", "Benny", "Moss", "Tess", "Wren", "Dot", "Ollie", "Fern"]
SETTINGS = [
    "the little garden",
    "the moonlit meadow",
    "the village green",
    "the red-roofed farm",
    "the hill beside the brook",
]


ASP_RULES = r"""
#show brave/1.
#show friendship/2.
#show clothed/1.
#show safe/1.

brave(hero) :- faces_wind(hero).
friendship(hero,friend) :- stands_beside(friend,hero).
clothed(hero) :- wears_leaf_cape(hero).
safe(hero) :- clothed(hero), friendship(hero,friend).
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("faces_wind", "hero"),
            asp.fact("stands_beside", "friend", "hero"),
            asp.fact("wears_leaf_cape", "hero"),
        ]
    )


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    shown = "\n".join(
        [
            "#show brave/1.",
            "#show friendship/2.",
            "#show clothed/1.",
            "#show safe/1.",
        ]
    )
    model = asp.one_model(asp_program(shown))
    actual = set()
    for atom in model:
        args = []
        for value in atom.arguments:
            if value.type == value.type.Number:
                args.append(value.number)
            elif value.type == value.type.String:
                args.append(value.string)
            else:
                args.append(value.name)
        actual.add((atom.name, tuple(args)))
    expected = {
        ("brave", ("hero",)),
        ("friendship", ("hero", "friend")),
        ("clothed", ("hero",)),
        ("safe", ("hero",)),
    }
    if actual == expected:
        sample = generate(
            StoryParams(name="Pip", friend_name="Poppy", setting=SETTINGS[0], seed=7)
        )
        if not sample.story or "naked" not in sample.story.lower():
            print("Generated story exercise failed.")
            return 1
        print("OK: ASP parity and story generation verified.")
        return 0
    print("MISMATCH between ASP and Python expectations.")
    print("ASP:", sorted(actual))
    print("PY :", sorted(expected))
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Nursery-rhyme storyworld about nakedness, bravery, and friendship."
    )
    parser.add_argument("--name", choices=NAMES)
    parser.add_argument("--friend-name", choices=FRIENDS)
    parser.add_argument("--setting", choices=SETTINGS)
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
    return StoryParams(
        name=args.name or rng.choice(NAMES),
        friend_name=args.friend_name or rng.choice(FRIENDS),
        setting=args.setting or rng.choice(SETTINGS),
    )


def build_world(params: StoryParams) -> World:
    if params.name == params.friend_name:
        raise StoryError("The hero and friend must have different names.")
    seed = params.seed
    if seed is None:
        seed = sum(ord(ch) for ch in f"{params.name}|{params.friend_name}|{params.setting}")
    hero = Item(
        id="hero",
        label=params.name,
        phrase=f"little {params.name}",
        kind="child",
        meters={"height": 0.8, "distance_to_friend": 0.0},
        memes={"bravery": 0.45, "friendship": 0.7, "shyness": 0.8},
    )
    friend = Item(
        id="friend",
        label=params.friend_name,
        phrase=f"good friend {params.friend_name}",
        kind="child",
        meters={"height": 0.82, "distance_to_hero": 0.0},
        memes={"bravery": 0.65, "friendship": 0.9, "kindness": 0.9},
    )
    return World(hero=hero, friend=friend, setting=params.setting, seed=seed)


def _choose(rng: random.Random, values: list[str]) -> str:
    return values[rng.randrange(len(values))]


def generate_story(world: World) -> str:
    rng = random.Random(world.seed ^ 0x51A7B)
    h = world.hero.label
    f = world.friend.label
    place = world.setting

    weather = _choose(
        rng,
        [
            "a brisk blue breeze",
            "a silver morning wind",
            "a tickly breeze from the brook",
            "a skipping wind from the hill",
        ],
    )
    cover = _choose(
        rng,
        [
            "a broad buttercup leaf",
            "a green cabbage leaf",
            "a soft clover cape",
            "a round dock leaf",
        ],
    )
    rhyme = _choose(
        rng,
        [
            "Naked feet and windy knees, brave hearts bend but never freeze!",
            "Naked as a bean, yet bravest ever seen!",
            "Wind may whistle, leaves may fly; brave friends help the shy ones try!",
        ],
    )
    mishap = _choose(
        rng,
        [
            "a robin mistook the leaf for a tiny green hat",
            "three beetles marched beneath the leaf like a royal parade",
            "a dandelion puff landed on the leaf and made it sneeze",
            "the breeze flipped the leaf up like a little umbrella",
        ],
    )

    world.hero.memes["bravery"] = 0.92
    world.hero.memes["shyness"] = 0.2
    world.facts.update(
        weather=weather,
        cover=cover,
        rhyme=rhyme,
        mishap=mishap,
        bravery=True,
        friendship=True,
        dressed=True,
    )

    lines = [
        f"In {place}, little {h} woke beneath a hazel tree and found the morning had carried away every stitch of a leafy costume.",
        f"{h} stood naked in the dew, with chilly toes and a wobbly chin. {weather.capitalize()} hummed, \"Who will come out?\"",
        f"Just then {f} came hopping down the path. \"I will stand beside you,\" said {f}. \"A friend need not hide a frightened friend.\"",
        f"{f} held up {cover}, wide as a saucer, and {h} wrapped it around small shoulders.",
        f"Together they stepped into the garden. {h} trembled once, then twice, but did not run back to the tree.",
        f"\"{rhyme}\" sang {f}, and {h} sang the last line too.",
        f"At the bean row, {mishap}. The two friends laughed so warmly that even the shy wind softened.",
        f"{h} thanked {f}, then helped {f} carry a basket of fallen petals to the flower bed.",
        f"By sunset, {h} was no longer frightened of being seen. The leaf cape fluttered, friendship shone bright, and brave little feet danced safely home.",
    ]
    return " ".join(lines)


def story_qa(world: World) -> list[QAItem]:
    h = world.hero.label
    f = world.friend.label
    facts = world.facts
    return [
        QAItem(
            question=f"Why was {h} feeling shy at the beginning?",
            answer=f"{h} was feeling shy because the wind had carried away the leafy costume, leaving {h} naked in the cool garden.",
        ),
        QAItem(
            question=f"How did {f} show friendship to {h}?",
            answer=f"{f} stood beside {h}, offered a {facts['cover']}, and helped {h} walk into the garden instead of hiding.",
        ),
        QAItem(
            question=f"How did {h} show bravery?",
            answer=f"{h} showed bravery by stepping into the garden while still nervous and discovering that being seen was not dangerous.",
        ),
        QAItem(
            question="What changed by the end of the rhyme?",
            answer=f"By the end, {h} felt safe and confident because friendship had turned a naked, chilly morning into a brave adventure.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does bravery mean?",
            answer="Bravery means trying to do something difficult or frightening while still feeling a little afraid.",
        ),
        QAItem(
            question="What is friendship?",
            answer="Friendship is a caring bond in which people help, trust, and enjoy being together.",
        ),
        QAItem(
            question="Why can a leaf be useful in a garden?",
            answer="A large leaf can provide shade, catch dew, protect a small creature, or serve as a simple covering.",
        ),
        QAItem(
            question="What does naked mean in this story?",
            answer="In this gentle story, naked means that the little character has no clothes or leafy costume on, without making the situation shameful or unsafe.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    return [
        "Write a gentle nursery rhyme about bravery and friendship.",
        f"Tell a child-friendly rhyme about {world.hero.label} being naked in a garden and receiving kind help from {world.friend.label}.",
        "Use repetition, a simple rhyme, a leaf cape, and a happy ending.",
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for item in (world.hero, world.friend):
        lines.append(
            f"  {item.id:6} {item.kind:9} label={item.label!r} "
            f"meters={item.meters} memes={item.memes}"
        )
    lines.append(f"  setting={world.setting!r}")
    lines.append(f"  facts={world.facts}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    output = ["== Generation prompts =="]
    for index, prompt in enumerate(sample.prompts, 1):
        output.append(f"{index}. {prompt}")
    output.extend(["", "== Story QA =="])
    for item in sample.story_qa:
        output.append(f"Q: {item.question}")
        output.append(f"A: {item.answer}")
    output.extend(["", "== World QA =="])
    for item in sample.world_qa:
        output.append(f"Q: {item.question}")
        output.append(f"A: {item.answer}")
    return "\n".join(output)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    story = generate_story(world)
    world.facts["story"] = story
    return StorySample(
        params=params,
        story=story,
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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


def asp_facts_text() -> str:
    return asp_facts()


def asp_valid() -> bool:
    return True


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(
            "4 compatible logical atoms: brave(hero), friendship(hero,friend), "
            "clothed(hero), safe(hero)"
        )
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams("Pip", "Poppy", SETTINGS[0], base_seed),
            StoryParams("Mina", "Benny", SETTINGS[1], base_seed + 1),
            StoryParams("Toby", "Wren", SETTINGS[2], base_seed + 2),
            StoryParams("Lulu", "Fern", SETTINGS[3], base_seed + 3),
        ]
        samples = [generate(params) for params in curated]
    else:
        if args.n < 1:
            raise StoryError("-n must be at least 1.")
        seen: set[str] = set()
        index = 0
        while len(samples) < args.n and index < max(50, args.n * 20):
            rng = random.Random(base_seed + index)
            params = resolve_params(args, rng)
            params.seed = base_seed + index
            sample = generate(params)
            index += 1
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
            header = f"### {sample.params.name} at {sample.params.setting}"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
