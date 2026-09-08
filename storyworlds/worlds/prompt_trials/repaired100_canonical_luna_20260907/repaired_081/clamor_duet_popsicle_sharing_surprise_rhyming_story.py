#!/usr/bin/env python3
"""
A tiny rhyming storyworld about clamor, a duet, and sharing a surprise popsicle.
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
    place: str = "the sunny town square"
    hero_name: str = "Luna"
    friend_name: str = "Milo"
    flavor: str = "blueberry"
    instrument: str = "a tiny red drum"
    seed: Optional[int] = None


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
    lines: list[str] = field(default_factory=list)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, line: str) -> None:
        self.lines.append(line)

    def render(self) -> str:
        return " ".join(self.lines)


PLACES = [
    "the sunny town square",
    "the little park by the fountain",
    "the market beside the old clock",
    "the bright schoolyard",
]

HERO_NAMES = ["Luna", "Nia", "Tavi", "Pip", "Mara"]
FRIEND_NAMES = ["Milo", "Zoe", "Jasper", "Ivy", "Theo"]
FLAVORS = ["blueberry", "strawberry", "lemon", "orange", "raspberry"]
INSTRUMENTS = ["a tiny red drum", "a silver bell", "a wooden flute", "two shiny spoons"]

ASP_RULES = r"""
character(X) :- character_name(X).
treat(T) :- treat_name(T).
has_treat(X,T) :- holder(X,T).
shared(T) :- shared_treat(T).
surprise(T) :- surprise_treat(T).
duet(X,Y) :- duet_pair(X,Y).
happy(X) :- smiling(X).
good_ending :- shared(T), surprise(T), duet(X,Y), happy(X), happy(Y).
"""


def asp_facts() -> str:
    import asp

    return "\n".join(
        [
            asp.fact("character_name", "hero"),
            asp.fact("character_name", "friend"),
            asp.fact("treat_name", "popsicle"),
            asp.fact("holder", "hero", "popsicle"),
            asp.fact("shared_treat", "popsicle"),
            asp.fact("surprise_treat", "popsicle"),
            asp.fact("duet_pair", "hero", "friend"),
            asp.fact("smiling", "hero"),
            asp.fact("smiling", "friend"),
        ]
    )


def asp_program(show: str = "#show good_ending/0.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program())
    names = {symbol.name for symbol in model}
    if "good_ending" in names:
        print("OK: ASP and Python parity looks good.")
        return 0
    print("MISMATCH between ASP and Python reasoning.")
    print("ASP:", sorted(names))
    print("PY :", ["good_ending"])
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A rhyming storyworld about clamor, a duet, and sharing a surprise popsicle."
    )
    parser.add_argument("--place", choices=PLACES)
    parser.add_argument("--name")
    parser.add_argument("--friend")
    parser.add_argument("--flavor", choices=FLAVORS)
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
        raise StoryError("The two friends must have different names.")
    return StoryParams(
        place=args.place or rng.choice(PLACES),
        hero_name=hero,
        friend_name=friend,
        flavor=args.flavor or rng.choice(FLAVORS),
        instrument=rng.choice(INSTRUMENTS),
    )


def generate(params: StoryParams) -> StorySample:
    if params.hero_name == params.friend_name:
        raise StoryError("Sharing works best when the friends have different names.")
    if params.flavor not in FLAVORS:
        raise StoryError(f"Unknown popsicle flavor: {params.flavor}.")

    rng = random.Random(
        params.seed
        if params.seed is not None
        else f"{params.place}:{params.hero_name}:{params.friend_name}:{params.flavor}"
    )
    world = World()

    hero = world.add(
        Entity(
            "hero",
            "character",
            params.hero_name,
            meters={"volume": 0.2, "happiness": 0.5},
            memes={"generosity": 0.3, "surprise": 0.0},
        )
    )
    friend = world.add(
        Entity(
            "friend",
            "character",
            params.friend_name,
            meters={"volume": 0.2, "happiness": 0.4},
            memes={"friendship": 0.5, "surprise": 0.0},
        )
    )
    popsicle = world.add(
        Entity(
            "popsicle",
            "treat",
            f"a tall {params.flavor} popsicle",
            meters={"whole": 1.0, "drip": 0.0},
            memes={"delight": 1.0, "surprise": 0.0},
        )
    )

    world.say(
        f"In {params.place}, where bright banners swayed, "
        f"{params.hero_name} tapped {params.instrument} in a parade."
    )
    world.say(
        f"The beat grew big, the people came near; "
        f"it made a bustling clamor for all to hear."
    )
    world.say(
        f"Then {params.friend_name} hummed a tune, soft and sweet, "
        f"and {params.hero_name} matched the beat."
    )
    world.say(
        f"“May I join your song?” asked {params.friend_name}. "
        f"“Yes!” said {params.hero_name}. “Let us make a duet again!”"
    )
    world.say(
        f"Together they played with a bounce and a sway, "
        f"until the loud clamor danced away."
    )

    popsicle.meters["whole"] = 0.5
    popsicle.meters["drip"] = 1.0
    hero.memes["surprise"] = 1.0
    world.say(
        f"After the music, {params.hero_name} found a surprise: "
        f"a {params.flavor} popsicle, cool as ice."
    )
    world.say(
        f"“It is yours,” said {params.friend_name}, “for leading the cheer.” "
        f"{params.hero_name} smiled. “Then sharing will make it dear.”"
    )
    world.say(
        f"They snapped it in two with a careful little crack, "
        f"and gave one half forward, then gave one half back."
    )
    popsicle.meters["whole"] = 0.0
    popsicle.memes["surprise"] = 1.0
    hero.meters["happiness"] = 1.0
    friend.meters["happiness"] = 1.0
    hero.memes["generosity"] = 1.0
    world.say(
        f"They licked and they laughed as the sun shone bright; "
        f"the sharing surprise made the whole square light."
    )
    world.say(
        f"Then one final duet rose, gentle and clear: "
        f"“A shared little treat makes a friendship grow near!”"
    )

    world.facts.update(
        hero=hero,
        friend=friend,
        popsicle=popsicle,
        clamor=True,
        duet=True,
        sharing=True,
        surprise=True,
        ending="The friends shared the popsicle and finished with a duet.",
    )

    prompts = [
        f"Write a rhyming story about {params.hero_name} and {params.friend_name} making music in {params.place}.",
        f"Include clamor, a duet, a surprise {params.flavor} popsicle, and sharing.",
        "End with a warm image showing how sharing changes the friends' day.",
    ]

    story_qa = [
        QAItem(
            question="What caused the clamor?",
            answer=f"{params.hero_name}'s lively playing drew a crowd and made a bustling clamor in {params.place}.",
        ),
        QAItem(
            question="How did the friends make a duet?",
            answer=f"{params.hero_name} played {params.instrument} while {params.friend_name} hummed, and then they matched their sounds together.",
        ),
        QAItem(
            question="What was the surprise?",
            answer=f"The surprise was a {params.flavor} popsicle offered after the music.",
        ),
        QAItem(
            question="How did the friends share the popsicle?",
            answer=f"They carefully snapped the popsicle in two and each enjoyed one half.",
        ),
        QAItem(
            question="What changed after they shared?",
            answer="Their shared treat made them happier and inspired one final joyful duet.",
        ),
    ]

    world_qa = [
        QAItem(
            question="What is a duet?",
            answer="A duet is a performance made by two people singing or playing together.",
        ),
        QAItem(
            question="Why can sharing be kind?",
            answer="Sharing lets another person enjoy something with you and can make a friendship feel stronger.",
        ),
        QAItem(
            question="What is a popsicle?",
            answer="A popsicle is a frozen sweet treat served on a stick.",
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
        print("--- trace ---")
        for key, entity in sample.world.entities.items():
            print(
                f"{key}: {entity.label} "
                f"meters={entity.meters} memes={entity.memes}"
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
        print(asp_program())
        return
    if args.verify:
        raise SystemExit(asp_verify())

    if args.asp:
        import asp

        model = asp.one_model(asp_program())
        print("ASP model:")
        for symbol in model:
            print(symbol)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for index, place in enumerate(PLACES):
            params = StoryParams(
                place=place,
                hero_name=HERO_NAMES[index % len(HERO_NAMES)],
                friend_name=FRIEND_NAMES[index % len(FRIEND_NAMES)],
                flavor=FLAVORS[index % len(FLAVORS)],
                instrument=INSTRUMENTS[index % len(INSTRUMENTS)],
                seed=base_seed + index,
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
