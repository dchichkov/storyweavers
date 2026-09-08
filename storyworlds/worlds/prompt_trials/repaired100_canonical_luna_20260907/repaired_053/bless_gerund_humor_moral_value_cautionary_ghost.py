#!/usr/bin/env python3
"""
A gentle cautionary ghost story about a blessing, a silly shortcut, and repair.

Seed words: bless-gerund
Style: Ghost Story
Features: Humor, Moral Value, Cautionary
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402


PLACES = [
    "the old hilltop chapel",
    "the moonlit village hall",
    "the abandoned orchard house",
    "the bell tower by the river",
]
CHILD_NAMES = ["Luna", "Mara", "Theo", "Nell", "Pip", "Ivy", "Oren", "Tess"]
GHOST_NAMES = ["Mister Moth", "Auntie Echo", "Boo-Bella", "Captain Mist"]
OBJECTS = [
    "a silver bell",
    "a blue lantern",
    "a little wooden door",
    "a cracked music box",
]
GERUNDS = ["blessing", "whistling", "tiptoeing", "humming"]
JOKES = [
    "The ghost's sheet caught on a nail and made him look like a very nervous flag.",
    "A bat flew past, and the ghost bowed to it by mistake.",
    "The lantern sneezed a puff of blue smoke, which made everyone giggle.",
    "The ghost tried to whisper, but his stomach gave a loud, hollow honk.",
]
LESSONS = [
    "A kind blessing is a promise to care, not a trick for getting your way.",
    "Courage grows when we tell the truth and repair the trouble we caused.",
    "A shortcut may look funny, but careful kindness keeps a home safe.",
    "Good intentions need good choices to become good deeds.",
]


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Setting:
    place: str
    quiet: bool = True
    safe: bool = True


@dataclass
class Mood:
    humor: bool = True
    moral_value: bool = True
    cautionary: bool = True


@dataclass
class StoryParams:
    place: str
    child_name: str
    ghost_name: str
    object_name: str
    gerund: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting, mood: Mood) -> None:
        self.setting = setting
        self.mood = mood
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
        self.lines: list[list[str]] = [[]]

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        self.lines[-1].append(text)

    def para(self) -> None:
        if self.lines[-1]:
            self.lines.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.lines if p)


def tell(params: StoryParams) -> World:
    if params.child_name == params.ghost_name:
        raise StoryError("The child and ghost need different names.")
    if params.gerund not in GERUNDS:
        raise StoryError(f"Unknown bless-gerund form: {params.gerund}")

    rng = random.Random(params.seed if params.seed is not None else repr(params))
    world = World(Setting(params.place), Mood())
    child = world.add(
        Entity(
            id=params.child_name,
            kind="child",
            label=params.child_name,
            meters={"distance_to_object": 4.0},
            memes={"curiosity": 2.0, "worry": 0.5},
        )
    )
    ghost = world.add(
        Entity(
            id=params.ghost_name,
            kind="ghost",
            label=params.ghost_name,
            meters={"floatiness": 3.0},
            memes={"loneliness": 2.0, "kindness": 1.0},
        )
    )
    treasure = world.add(
        Entity(
            id="object",
            kind="object",
            label=params.object_name,
            meters={"balance": 1.0, "brightness": 1.0},
            memes={"importance": 2.0},
        )
    )

    joke = rng.choice(JOKES)
    lesson = rng.choice(LESSONS)
    promise = f"bless-{params.gerund}"

    world.facts.update(
        child=child,
        ghost=ghost,
        treasure=treasure,
        joke=joke,
        lesson=lesson,
        promise=promise,
    )

    world.say(f"At {params.place}, the night was quiet enough to hear moonlight touch the windows.")
    world.say(
        f"{params.child_name} had come to return {params.object_name}, but a pale ghost named {params.ghost_name} drifted from the rafters."
    )
    world.say(
        f"The ghost was practicing a strange old promise called {promise}: a blessing meant to protect the house."
    )
    world.para()

    world.say(
        f"Unfortunately, {params.ghost_name} wanted the blessing to finish quickly, so he waved one transparent hand and skipped the careful words."
    )
    world.say(
        f"The shortcut made {params.object_name} wobble toward the edge of a high shelf."
    )
    world.say(joke)
    world.say(
        f'"Stop!" cried {params.child_name}. "A blessing should help people, not frighten them or break their things."'
    )
    world.say(
        f'"I only wanted to be useful," said {params.ghost_name}. "I thought faster meant better."'
    )
    world.para()

    world.say(
        f"{params.child_name} pointed to the shelf. " 
        f'"Let us slow down, tell the truth, and fix what the shortcut changed."'
    )
    world.say(
        f"Together they moved {params.object_name} to a sturdy table, checked its cracked edge, and opened the window so the ghost could see the moonlit room clearly."
    )
    world.say(
        f"{params.ghost_name} admitted that he had rushed because he feared nobody needed a ghost anymore."
    )
    world.say(
        f'"People need careful friends," {params.child_name} replied. "You can be one if you choose kindness before showing off."'
    )
    world.para()

    world.say(
        f"This time, {params.ghost_name} performed the blessing slowly, {params.gerund} with a soft voice while {params.child_name} held the repaired {params.object_name} steady."
    )
    world.say(
        f"The room warmed, the shelf stopped trembling, and the ghost's lonely face brightened."
    )
    world.say(
        f"Before dawn, {params.ghost_name} promised never to use a careless shortcut near someone else's belongings again."
    )
    world.say(lesson)
    world.say(
        f"When {params.child_name} left, {params.object_name} shone safely on the table, and a small ghostly hand waved goodbye from the window."
    )

    child.meters["distance_to_object"] = 0.0
    child.memes.update(courage=1.0, trust=1.0)
    ghost.memes.update(loneliness=0.0, kindness=2.0, responsibility=2.0)
    treasure.meters.update(balance=2.0, brightness=2.0)
    return world


def generation_prompts(world: World) -> list[str]:
    return [
        "Write a gentle Ghost Story about a blessing that must be done carefully.",
        "Include humor, a caution about shortcuts, and a moral value shown through action.",
        f"Let the characters use {world.facts['promise']} to repair a mistake.",
    ]


def story_qa(world: World) -> list[QAItem]:
    child: Entity = world.facts["child"]
    ghost: Entity = world.facts["ghost"]
    treasure: Entity = world.facts["treasure"]
    return [
        QAItem(
            question=f"Why did {treasure.label} begin to wobble?",
            answer=f"{ghost.label} rushed through a protective blessing and used a careless shortcut, which made {treasure.label} wobble toward the shelf's edge.",
        ),
        QAItem(
            question=f"What did {child.label} tell {ghost.label}?",
            answer=f"{child.label} said that a blessing should help people rather than frighten them or risk breaking their belongings.",
        ),
        QAItem(
            question="How did the child and ghost repair the trouble?",
            answer=f"They moved {treasure.label} to a sturdy table, checked its cracked edge, opened the window, and performed the blessing slowly together.",
        ),
        QAItem(
            question="What did the ghost learn?",
            answer=f"The ghost learned that being useful requires careful kindness and honesty, not a flashy shortcut.",
        ),
        QAItem(
            question="What showed that the ending was safe?",
            answer=f"{treasure.label} shone safely on the table, while the ghost waved goodbye from the window.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a ghost in a traditional story?",
            answer="A ghost is a spirit-like character said to remain after a person has died, often appearing mysteriously in stories.",
        ),
        QAItem(
            question="What is a blessing?",
            answer="A blessing is a kind wish, prayer, or spoken promise for safety, goodness, or well-being.",
        ),
        QAItem(
            question="Why can shortcuts be dangerous?",
            answer="A shortcut can skip important careful steps, so it may cause mistakes or make someone less safe.",
        ),
        QAItem(
            question="What is a moral value?",
            answer="A moral value is a principle about how to behave well, such as honesty, kindness, courage, or responsibility.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        lines.append(
            f"  {entity.id} [{entity.kind}] meters={meters} memes={memes}"
        )
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A humorous cautionary ghost story about a careful blessing."
    )
    parser.add_argument("--place", choices=PLACES)
    parser.add_argument("--child-name")
    parser.add_argument("--ghost-name")
    parser.add_argument("--object", dest="object_name")
    parser.add_argument("--gerund", choices=GERUNDS)
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
    child_name = args.child_name or rng.choice(CHILD_NAMES)
    ghost_name = args.ghost_name or rng.choice(
        [name for name in GHOST_NAMES if name != child_name]
    )
    return StoryParams(
        place=args.place or rng.choice(PLACES),
        child_name=child_name,
        ghost_name=ghost_name,
        object_name=args.object_name or rng.choice(OBJECTS),
        gerund=args.gerund or rng.choice(GERUNDS),
    )


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


def asp_facts() -> str:
    return "\n".join(
        [
            "domain(ghost_story).",
            "feature(humor).",
            "feature(moral_value).",
            "feature(cautionary).",
            "instrument(bless_gerund).",
            "value(careful_kindness).",
            "risk(careless_shortcut).",
        ]
    )


ASP_RULES = r"""
valid_world :-
    domain(ghost_story),
    feature(humor),
    feature(moral_value),
    feature(cautionary),
    instrument(bless_gerund),
    value(careful_kindness),
    risk(careless_shortcut).
#show valid_world/0.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program("#show valid_world/0."))
    values = set(asp.atoms(model, "valid_world"))
    if values == {()}:
        params = StoryParams(
            place=PLACES[0],
            child_name="Luna",
            ghost_name="Mister Moth",
            object_name=OBJECTS[0],
            gerund="blessing",
            seed=7,
        )
        sample = generate(params)
        required = ["blessing", "shortcut", "kindness"]
        if all(word in sample.story.lower() for word in required):
            print("OK: ASP facts, Python world, and generated story agree.")
            return 0
        print("MISMATCH: generated story lacks required narrative elements")
        return 1
    print("MISMATCH:", values)
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_world/0."))
        return

    if args.verify:
        raise SystemExit(asp_verify())

    if args.n < 1:
        raise StoryError("-n must be at least 1.")

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    seen: set[str] = set()

    count = 1 if args.all else args.n
    for index in range(count):
        rng = random.Random(base_seed + index)
        params = resolve_params(args, rng)
        params.seed = base_seed + index
        sample = generate(params)
        if sample.story in seen:
            continue
        seen.add(sample.story)
        samples.append(sample)

    if args.asp:
        import asp

        model = asp.one_model(asp_program("#show valid_world/0."))
        if set(asp.atoms(model, "valid_world")) != {()}:
            raise StoryError("ASP validation rejected the story world.")

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
            header=f"### story {index + 1}" if len(samples) > 1 else "",
        )
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
