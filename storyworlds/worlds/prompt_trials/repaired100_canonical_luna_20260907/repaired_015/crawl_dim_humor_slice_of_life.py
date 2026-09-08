#!/usr/bin/env python3
"""
A small slice-of-life storyworld about a crawl-dim moment, where ordinary
household work turns funny and a child learns to ask for help.
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

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(HERE))))
sys.path.insert(0, ROOT)
from storyworlds.results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class StoryParams:
    name: str
    helper: str
    place: str
    object_name: str
    joke_style: str
    seed: Optional[int] = None


@dataclass(frozen=True)
class Trouble:
    key: str
    object_name: str
    cause: str
    clue: str
    repair: str
    ending: str


NAMES = ["Luna", "Milo", "Nia", "Owen", "Pia", "Theo"]
HELPERS = ["Dad", "Mom", "Grandma", "Grandpa", "Aunt Jo"]
PLACES = [
    "the hallway",
    "the living room",
    "the laundry room",
    "the kitchen",
    "the bedroom",
]
OBJECTS = ["a blue sock", "a wooden spoon", "a red toy car", "a tiny mitten", "a striped slipper"]
JOKE_STYLES = ["deadpan", "silly", "animal", "pretend-serious"]

TROUBLES = [
    Trouble(
        "sock",
        "a blue sock",
        "the sock had slid under the lowest shelf",
        "a fuzzy blue toe sticking out like a shy flag",
        "Luna reached with a ruler while the helper lifted the basket",
        "The sock joined its mate, and the laundry basket stopped looking suspicious.",
    ),
    Trouble(
        "spoon",
        "a wooden spoon",
        "the spoon had rolled behind the kitchen cart",
        "a brown handle peeking out beside one dusty crumb",
        "the helper moved the cart while Luna swept the spoon forward with a towel",
        "The spoon returned to the drawer, where it looked far too innocent.",
    ),
    Trouble(
        "car",
        "a red toy car",
        "the car had slipped beneath the sofa",
        "two bright wheels shining in the dim space",
        "Luna used a cardboard tube while the helper held a flashlight",
        "The car rolled free and immediately parked on the helper's foot.",
    ),
    Trouble(
        "mitten",
        "a tiny mitten",
        "the mitten had fallen behind a low coat basket",
        "one little thumb waving from the shadow",
        "the helper tipped the basket while Luna caught the mitten with both hands",
        "The mitten came home, still warm with the adventure of being lost.",
    ),
    Trouble(
        "slipper",
        "a striped slipper",
        "the slipper had tucked itself beneath the bed",
        "a stripe visible whenever the curtain moved",
        "Luna lay flat and pushed it out with a broom handle",
        "The slipper returned to its partner and became a very ordinary shoe again.",
    ),
]


@dataclass
class World:
    params: StoryParams
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

    def add(self, entity: Entity) -> None:
        self.entities[entity.id] = entity

    def say(self, text: str) -> None:
        self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def choose(items: list[str], seed: int, salt: int) -> str:
    return items[random.Random(seed + salt * 7919).randrange(len(items))]


def normalize_params(params: StoryParams) -> None:
    if params.name not in NAMES:
        raise StoryError(f"unknown child name: {params.name}")
    if params.helper not in HELPERS:
        raise StoryError(f"unknown helper: {params.helper}")
    if params.place not in PLACES:
        raise StoryError(f"unknown place: {params.place}")
    if params.object_name not in OBJECTS:
        raise StoryError(f"unknown object: {params.object_name}")
    if params.joke_style not in JOKE_STYLES:
        raise StoryError(f"unknown joke style: {params.joke_style}")


def build_world(params: StoryParams) -> World:
    normalize_params(params)
    seed = params.seed if params.seed is not None else 17
    trouble = next((t for t in TROUBLES if t.object_name == params.object_name), None)
    if trouble is None:
        raise StoryError(f"no crawl-dim trouble is available for {params.object_name}")

    world = World(params=params)
    world.add(Entity(
        id="child",
        kind="character",
        label=params.name,
        meters={"curiosity": 1.0, "frustration": 0.0, "confidence": 0.0},
        memes={"humor": 1.0, "helpfulness": 0.0},
    ))
    world.add(Entity(
        id="helper",
        kind="character",
        label=params.helper,
        meters={"patience": 2.0, "attention": 1.0},
        memes={"kindness": 1.0},
    ))
    world.add(Entity(
        id="lost_object",
        kind="object",
        label=params.object_name,
        meters={"distance": 1.0},
        memes={"importance": 1.0},
    ))
    world.facts["trouble"] = trouble
    world.facts["seed"] = seed
    world.facts["found"] = False
    return world


def crawl_dim_opening(world: World) -> None:
    p = world.params
    child = world.entities["child"]
    trouble: Trouble = world.facts["trouble"]  # type: ignore[assignment]
    child.meters["frustration"] += 1
    world.say(
        f"After lunch, {p.name} noticed that {trouble.object_name} was missing in {p.place}. "
        f"It had been there a moment ago, which was exactly long enough to become mysterious."
    )
    world.say(
        f"{p.name} knelt down and peered into the crawl-dim space beneath the furniture. "
        "It was not quite dark, but it was dark enough to make every dust ball look important."
    )


def humorous_search(world: World) -> None:
    p = world.params
    child = world.entities["child"]
    helper = world.entities["helper"]
    style = p.joke_style
    jokes = {
        "deadpan": f'"I am conducting a serious investigation," {p.name} announced.',
        "silly": f'"Maybe the floor ate it," {p.name} said.',
        "animal": f'"If I were a mouse, I would know where this is," {p.name} said.',
        "pretend-serious": f'"Nobody panic," {p.name} whispered, although nobody had panicked yet.',
    }
    world.say(jokes[style])
    world.say(f'{p.helper} looked down and asked, "What is your first clue?"')
    world.say(f'"The crawl-dim," {p.name} replied. "Things go in there and become almost visible."')
    world.say(
        f'{p.helper} said, "Then let us use a light and look carefully." '
        f'{p.name} answered, "Good plan. My eyes were only guessing."'
    )
    helper.meters["attention"] += 1
    child.memes["humor"] += 1


def reveal_clue(world: World) -> None:
    p = world.params
    child = world.entities["child"]
    trouble: Trouble = world.facts["trouble"]  # type: ignore[assignment]
    world.say(
        f"Together they looked from the side instead of from above. "
        f"Then they saw {trouble.clue}."
    )
    world.say(
        f"The clue explained the mystery: {trouble.cause}. "
        f"{p.name} stopped poking at random and chose a careful way to reach it."
    )
    child.meters["frustration"] -= 1
    child.meters["confidence"] += 1


def repair(world: World) -> None:
    p = world.params
    child = world.entities["child"]
    helper = world.entities["helper"]
    trouble: Trouble = world.facts["trouble"]  # type: ignore[assignment]
    world.say(f'{p.helper} said, "I can hold this steady while you try."')
    world.say(f'{p.name} said, "And I will tell you if I need a new idea."')
    world.say(trouble.repair + ".")
    world.say(
        f'The two worked slowly. When {trouble.object_name} finally came free, '
        f'{p.name} laughed and said, "It was hiding in the crawl-dim!"'
    )
    helper.meters["patience"] += 1
    child.meters["confidence"] += 1
    child.memes["helpfulness"] += 1
    world.facts["found"] = True


def resolve(world: World) -> None:
    p = world.params
    trouble: Trouble = world.facts["trouble"]  # type: ignore[assignment]
    if not world.facts["found"]:
        raise StoryError("the object must be found before the story can resolve")
    world.say(
        f'{p.name} put {trouble.object_name} where it belonged. '
        f'{trouble.ending}'
    )
    world.say(
        f'As they walked away, {p.helper} asked, "What did the crawl-dim teach you?" '
        f'{p.name} replied, "Look for a clue, and do not be too proud to ask for help."'
    )


def tell(params: StoryParams) -> World:
    world = build_world(params)
    crawl_dim_opening(world)
    humorous_search(world)
    world.para()
    reveal_clue(world)
    repair(world)
    world.para()
    resolve(world)
    return world


def story_qa(world: World) -> list[QAItem]:
    p = world.params
    trouble: Trouble = world.facts["trouble"]  # type: ignore[assignment]
    return [
        QAItem(
            question=f"Why did {p.name} look in the crawl-dim space in {p.place}?",
            answer=f"{p.name} looked there because {trouble.object_name} was missing and the clue showed that {trouble.cause}."
        ),
        QAItem(
            question=f"What did {p.name} and {p.helper} do to find {trouble.object_name}?",
            answer=f"They looked from the side, used a careful tool, and worked together while {p.helper} held things steady."
        ),
        QAItem(
            question=f"How did humor help during {p.name}'s ordinary search?",
            answer=f"{p.name}'s joke made the frustrating search feel lighter, so the problem became something they could solve calmly together."
        ),
        QAItem(
            question=f"What did {p.name} learn from the crawl-dim problem?",
            answer=f"{p.name} learned to look for a useful clue and ask for help instead of guessing and struggling alone."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a crawl space?",
            answer="A crawl space is a low, narrow area that a person may enter or look into by crouching or crawling."
        ),
        QAItem(
            question="Why is a flashlight useful in a dim place?",
            answer="A flashlight makes hidden objects and safe paths easier to see."
        ),
        QAItem(
            question="Why can asking for help be useful?",
            answer="Asking for help can bring another person's strength, attention, or idea to a problem."
        ),
        QAItem(
            question="What is slice-of-life storytelling?",
            answer="Slice-of-life storytelling focuses on a small everyday event and shows why that ordinary moment matters."
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    p = world.params
    return [
        f"Write a child-friendly slice-of-life story about {p.name} finding {p.object_name} in a crawl-dim place.",
        f"Include gentle Humor, a brief dialogue exchange with {p.helper}, and a practical solution.",
        "End with a concrete household image showing what changed.",
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


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== (3) World questions ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print("--- trace ---")
        for entity in sample.world.entities.values():
            meters = {k: v for k, v in entity.meters.items() if v}
            memes = {k: v for k, v in entity.memes.items() if v}
            print(f"{entity.label}: meters={meters} memes={memes}")
    if qa:
        print()
        print(format_qa(sample))


def asp_facts() -> str:
    import storyworlds.asp as asp
    return "\n".join([
        asp.fact("domain", "crawl_dim"),
        asp.fact("feature", "humor"),
        asp.fact("style", "slice_of_life"),
        asp.fact("requires", "clue"),
        asp.fact("supports", "asking_for_help"),
        asp.fact("ends_with", "ordinary_resolution"),
    ])


ASP_RULES = r"""
reasonable :-
    domain(crawl_dim),
    feature(humor),
    style(slice_of_life),
    requires(clue),
    supports(asking_for_help),
    ends_with(ordinary_resolution).
"""


def asp_program(show: str = "#show reasonable/0.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program())
    if asp.atoms(model, "reasonable"):
        for params in CURATED:
            sample = generate(StoryParams(**params.__dict__))
            if not sample.story or "crawl-dim" not in sample.story:
                print("MISMATCH: generated story failed its crawl-dim check.")
                return 1
        print("OK: ASP and Python gates agree; generated stories pass.")
        return 0
    print("MISMATCH: ASP gate failed.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A crawl-dim slice-of-life storyworld with humor.")
    parser.add_argument("--name", choices=NAMES)
    parser.add_argument("--helper", choices=HELPERS)
    parser.add_argument("--place", choices=PLACES)
    parser.add_argument("--object", dest="object_name", choices=OBJECTS)
    parser.add_argument("--joke-style", choices=JOKE_STYLES)
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
        helper=args.helper or rng.choice(HELPERS),
        place=args.place or rng.choice(PLACES),
        object_name=args.object_name or rng.choice(OBJECTS),
        joke_style=args.joke_style or rng.choice(JOKE_STYLES),
        seed=args.seed,
    )


CURATED = [
    StoryParams("Luna", "Dad", "the hallway", "a blue sock", "deadpan", 101),
    StoryParams("Milo", "Grandma", "the living room", "a red toy car", "silly", 202),
    StoryParams("Nia", "Mom", "the kitchen", "a wooden spoon", "pretend-serious", 303),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp
        print(asp.atoms(asp.one_model(asp_program()), "reasonable"))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(StoryParams(**p.__dict__)) for p in CURATED]
    else:
        samples = []
        for index in range(args.n):
            seed = base_seed + index
            rng = random.Random(seed)
            params = resolve_params(args, rng)
            params.seed = seed
            samples.append(generate(params))

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
        if index + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
