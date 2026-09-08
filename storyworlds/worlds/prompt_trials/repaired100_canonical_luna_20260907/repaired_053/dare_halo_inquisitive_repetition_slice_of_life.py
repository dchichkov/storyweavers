#!/usr/bin/env python3
"""
A small slice-of-life story world about an inquisitive child, a halo of light,
and a dare that becomes a careful repeated experiment.

Seed words: dare, halo, inquisitive
Feature: Repetition
Style: Slice of Life
"""

from __future__ import annotations

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
    "the apartment courtyard",
    "the neighborhood laundromat",
    "the little kitchen",
    "the bus stop near the bakery",
    "the community garden",
    "the library steps",
]
NAMES = ["Luna", "Mara", "Theo", "Inez", "Sam", "Niko", "June", "Owen"]
HELPER_NAMES = ["Ari", "Mina", "Jo", "Ravi", "Bea", "Noah", "Tess", "Kai"]
OBJECTS = [
    "a paper cup",
    "a blue marble",
    "a cardboard star",
    "a red button",
    "a smooth pebble",
    "a folded napkin",
]
LIGHT_SOURCES = [
    "a desk lamp",
    "the setting sun",
    "a bicycle light",
    "the hallway bulb",
    "a jar lantern",
]
DARES = [
    "make the little halo appear three times",
    "find out whether the halo follows the object",
    "repeat the light trick without touching the lamp",
    "show that the bright ring is not a secret doorway",
]
OPENINGS = [
    "After dinner, the ordinary room became interesting for no obvious reason.",
    "The day was almost over when a bright ring appeared on the floor.",
    "Nothing special was planned, which was exactly why Luna noticed the small change.",
    "At first, everyone was busy with an ordinary household task.",
    "A quiet patch of light slipped across the room and caught one curious eye.",
]
LESSONS = [
    "Luna learned that repeating a small test can turn a guess into something she can explain.",
    "The family discovered that curiosity works best when a dare includes care.",
    "The halo stayed mysterious for a minute, but patient repetition made its cause plain.",
    "A brave question did not need a risky stunt; it needed a safe test and careful noticing.",
]
WORLD_DEFINITIONS = [
    ("What is a dare?", "A dare is a challenge someone invites another person to try, but a good dare should be safe and sensible."),
    ("What is a halo?", "A halo is a ring or glow of light around something bright."),
    ("What does inquisitive mean?", "Inquisitive means eager to learn by asking questions and looking closely."),
    ("Why repeat a test?", "Repeating a test helps show whether the same cause produces the same result."),
]


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Setting:
    place: str


@dataclass
class Mood:
    curiosity: float = 0.0
    courage: float = 0.0
    caution: float = 0.0


@dataclass
class StoryParams:
    place: str
    hero_name: str
    helper_name: str
    object_name: str
    light_source: str
    dare: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting, mood: Mood) -> None:
        self.setting = setting
        self.mood = mood
        self.entities: dict[str, Entity] = {}
        self.lines: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        if text:
            self.lines[-1].append(text)

    def para(self) -> None:
        if self.lines[-1]:
            self.lines.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.lines if p)


def tell(params: StoryParams) -> World:
    world = World(Setting(params.place), Mood())
    hero = world.add(
        Entity(
            id=params.hero_name,
            kind="character",
            label="inquisitive child",
            memes={"curiosity": 1.0, "uncertainty": 1.0},
        )
    )
    helper = world.add(
        Entity(
            id=params.helper_name,
            kind="character",
            label="careful companion",
            memes={"patience": 1.0},
        )
    )
    prop = world.add(
        Entity(
            id="object",
            kind="object",
            label=params.object_name,
            owner=params.hero_name,
        )
    )
    lamp = world.add(
        Entity(
            id="light",
            kind="object",
            label=params.light_source,
        )
    )

    seed_value: object = params.seed
    if seed_value is None:
        seed_value = "|".join(
            [
                params.place,
                params.hero_name,
                params.helper_name,
                params.object_name,
                params.light_source,
                params.dare,
            ]
        )
    rng = random.Random(seed_value)
    opening = rng.choice(OPENINGS)
    lesson = rng.choice(LESSONS)
    ring_size = rng.choice(["small", "thin", "soft", "bright"])
    direction = rng.choice(["left", "right", "toward the window", "toward the wall"])
    test_count = rng.choice([3, 4])

    hero.meters["distance_from_light"] = 1.0
    prop.meters["shadow_length"] = 1.0
    lamp.meters["brightness"] = 1.0

    world.say(opening)
    world.say(
        f"In {world.setting.place}, {params.hero_name} noticed a {ring_size} halo around "
        f"{params.object_name} when {params.light_source} shone from one side."
    )
    world.say(
        f"{params.hero_name} was inquisitive, so the first question was not, "
        f'"Is it magic?" but "What changes when I move the object?"'
    )
    world.para()
    world.say(
        f"{params.helper_name} smiled and offered a dare: "
        f'"{params.dare.capitalize()}."'
    )
    world.say(
        f'"Only if we keep it safe," {params.hero_name} replied. '
        f'"No climbing, no hot bulbs, and no running."'
    )
    world.say(
        f'"Agreed," said {params.helper_name}. "We will change one thing at a time."'
    )
    world.say(
        f"They placed the {params.object_name} on the floor and moved it {direction}. "
        f"The halo moved too, while the shadow stretched the other way."
    )
    world.para()
    world.say(
        f"The first try was interesting but not enough. A passing bag blocked the "
        f"{params.light_source}, and the halo disappeared."
    )
    world.say(
        f'"Let us repeat it,' said {params.hero_name}. "Same light, same object, one careful change."'
    )
    world.say(
        f"They tried again. On the second test, the halo returned when the light was uncovered."
    )
    world.say(
        f"They repeated the test {test_count} times, moving only the {params.object_name} "
        f"each time. The ring appeared when the light reached its smooth bright edge, "
        f"and it vanished when the light was blocked."
    )
    world.say(
        f"{params.helper_name} pointed at the floor. "
        f'"The halo is not following your hand. It is part of the light and shadow."'
    )
    world.say(
        f'"So the dare was solved by noticing a pattern," {params.hero_name} said. '
        f'"And by repeating it instead of guessing."'
    )
    world.para()
    world.say(
        f"They put everything away, leaving the {params.object_name} on the table and "
        f"turning the {params.light_source} back to its ordinary place."
    )
    world.say(
        f"The final halo slipped across the floor, thin and bright, before fading when "
        f"the light was switched off."
    )
    world.say(lesson)

    world.mood.curiosity = 1.0
    world.mood.courage = 1.0
    world.mood.caution = 1.0
    hero.memes.update(understanding=1.0, confidence=1.0)
    helper.memes.update(trust=1.0, teamwork=1.0)
    prop.meters.update(tested=1.0, safe=1.0)
    lamp.meters["brightness"] = 0.0
    world.facts.update(
        hero=hero,
        helper=helper,
        prop=prop,
        lamp=lamp,
        ring_size=ring_size,
        direction=direction,
        test_count=test_count,
        lesson=lesson,
        dare=params.dare,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    return [
        "Write a gentle slice-of-life story about an inquisitive child and a halo of light.",
        f"Include a safe dare: {world.facts['dare']}.",
        "Use repetition to show how careful testing changes a guess into understanding.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero: Entity = world.facts["hero"]
    helper: Entity = world.facts["helper"]
    prop: Entity = world.facts["prop"]
    lamp: Entity = world.facts["lamp"]
    test_count = world.facts["test_count"]
    lesson = world.facts["lesson"]
    return [
        QAItem(
            question=f"What did {hero.id} notice at the beginning?",
            answer=(
                f"{hero.id} noticed a small halo around {prop.label} when "
                f"{lamp.label} shone from one side."
            ),
        ),
        QAItem(
            question=f"What dare did {helper.id} offer?",
            answer=f"{helper.id} dared {hero.id} to {world.facts['dare']}.",
        ),
        QAItem(
            question=f"How did {hero.id} and {helper.id} keep the dare safe?",
            answer=(
                "They agreed not to climb, touch anything hot, or run, and they changed "
                "only one part of the test at a time."
            ),
        ),
        QAItem(
            question="Why did they repeat the test?",
            answer=(
                f"They repeated it {test_count} times to see whether the same light-and-object "
                "pattern would happen again instead of trusting one guess."
            ),
        ),
        QAItem(
            question="What did the repeated tests show?",
            answer=(
                "The halo appeared when the light reached the object's bright edge and "
                "vanished when the light was blocked, so it came from light and shadow."
            ),
        ),
        QAItem(
            question=f"What did {hero.id} learn?",
            answer=lesson,
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [QAItem(question=q, answer=a) for q, a in WORLD_DEFINITIONS]


def dump_trace(world: World) -> str:
    out = ["--- world model state ---"]
    out.append(
        f"  setting={world.setting.place} curiosity={world.mood.curiosity} "
        f"courage={world.mood.courage} caution={world.mood.caution}"
    )
    for entity in world.entities.values():
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        out.append(f"  {entity.id} ({entity.label}) {' '.join(bits)}")
    return "\n".join(out)


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for index, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{index}. {prompt}")
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
        description="Slice-of-life story world about a dare, a halo, and inquisitive repetition."
    )
    parser.add_argument("--place", choices=PLACES)
    parser.add_argument("--hero-name")
    parser.add_argument("--helper-name")
    parser.add_argument("--object", dest="object_name", choices=OBJECTS)
    parser.add_argument("--light-source", choices=LIGHT_SOURCES)
    parser.add_argument("--dare", choices=DARES)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    hero_name = args.hero_name or rng.choice(NAMES)
    helper_pool = [name for name in HELPER_NAMES if name != hero_name]
    helper_name = args.helper_name or rng.choice(helper_pool)
    return StoryParams(
        place=args.place or rng.choice(PLACES),
        hero_name=hero_name,
        helper_name=helper_name,
        object_name=args.object_name or rng.choice(OBJECTS),
        light_source=args.light_source or rng.choice(LIGHT_SOURCES),
        dare=args.dare or rng.choice(DARES),
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
    from storyworlds import asp

    facts = [
        asp.fact("domain", "slice_of_life"),
        asp.fact("seed_word", "dare"),
        asp.fact("seed_word", "halo"),
        asp.fact("seed_word", "inquisitive"),
        asp.fact("feature", "repetition"),
        asp.fact("safe_test"),
        asp.fact("dialogue"),
        asp.fact("ending_change"),
    ]
    return "\n".join(facts)


ASP_RULES = r"""
valid_world :- domain(slice_of_life), seed_word(dare), seed_word(halo),
               seed_word(inquisitive), feature(repetition),
               safe_test, dialogue, ending_change.
#show valid_world/0.
"""


def asp_program(show: str = "#show valid_world/0.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import importlib

    asp = importlib.import_module("storyworlds.asp")
    model = asp.one_model(asp_program())
    values = set(asp.atoms(model, "valid_world"))
    if values != {()}:
        print("MISMATCH:", values, "{()}")
        return 1

    params = StoryParams(
        place=PLACES[0],
        hero_name="Luna",
        helper_name="Ari",
        object_name=OBJECTS[0],
        light_source=LIGHT_SOURCES[0],
        dare=DARES[0],
        seed=7,
    )
    sample = generate(params)
    required = ["dare", "halo", "inquisitive", "repeat", "Luna", "Ari"]
    missing = [word for word in required if word.lower() not in sample.story.lower()]
    if missing:
        print("MISMATCH: generated story is missing", missing)
        return 1
    if len(sample.story_qa) < 4:
        print("MISMATCH: generated story lacks grounded questions")
        return 1
    print("OK: ASP facts, Python world, and generated story agree.")
    return 0


def main() -> None:
    args = build_parser().parse_args()

    if args.n < 1:
        raise StoryError("-n must be at least 1")

    if args.show_asp:
        print(asp_program())
        return

    if args.asp:
        import importlib

        asp = importlib.import_module("storyworlds.asp")
        model = asp.one_model(asp_program())
        print("\n".join(str(symbol) for symbol in model))
        return

    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        params = resolve_params(args, random.Random(base_seed))
        params.seed = base_seed
        samples.append(generate(params))
    else:
        seen: set[str] = set()
        index = 0
        while len(samples) < args.n and index < max(100, args.n * 30):
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
        header = f"### story {index + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
