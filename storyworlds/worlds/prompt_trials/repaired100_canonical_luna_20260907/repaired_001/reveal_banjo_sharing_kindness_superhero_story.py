#!/usr/bin/env python3
"""
A child-friendly superhero storyworld about a secret reveal, a banjo, sharing,
and kindness.

Luna discovers that a quiet neighbor has a special banjo song, but she learns
that a superhero's greatest power is not keeping applause. It is sharing joy
with someone who needs it.
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


PLACES = {
    "moonlit_park": "the moonlit park",
    "rooftop_square": "the rooftop square",
    "rainbow_market": "the Rainbow Market",
    "cloud_garden": "the cloud garden",
}

PLACE_DETAILS = {
    "moonlit_park": ("beside the silver fountain", "a row of sleepy trees"),
    "rooftop_square": ("between the water tower and the bright rooftop flags", "the city skyline"),
    "rainbow_market": ("under the striped awnings", "a cart of warm apples"),
    "cloud_garden": ("among the soft floating flowers", "a little windmill"),
}

HERO_NAMES = ["Luna", "Mira", "Nova", "Zara", "Pip"]
HELPER_NAMES = ["Jo", "Tess", "Ari", "Sam", "Niko"]
BANJO_STYLES = [
    ("sunny", "a bright, bouncing tune"),
    ("gentle", "a soft tune that sounded like rain"),
    ("sparkly", "a quick tune full of twinkling notes"),
    ("brave", "a bold tune that made feet want to march"),
]

INTRODUCTIONS = [
    "Luna wore her silver cape and watched over the neighborhood",
    "Luna practiced small rescues before breakfast",
    "Luna checked her kindness signal beneath the evening stars",
    "Luna promised herself to use her powers for everyone",
]


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character":
            return {"subject": "she", "object": "her", "possessive": "her"}.get(case, "she")
        return {"subject": "it", "object": "it", "possessive": "its"}.get(case, "it")


@dataclass
class World:
    place: str
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
        return "\n\n".join(" ".join(part) for part in self.paragraphs if part)


@dataclass
class StoryParams:
    place: str
    hero: str
    helper: str
    banjo_style: str = "sunny"
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate a superhero story about revealing a banjo song through kindness."
    )
    parser.add_argument("--place", choices=sorted(PLACES))
    parser.add_argument("--hero")
    parser.add_argument("--helper")
    parser.add_argument("--banjo-style", choices=[item[0] for item in BANJO_STYLES])
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
    place = args.place or rng.choice(list(PLACES))
    hero = args.hero or rng.choice(HERO_NAMES)
    helper = args.helper or rng.choice(HELPER_NAMES)
    style = args.banjo_style or rng.choice([item[0] for item in BANJO_STYLES])
    if hero == helper:
        raise StoryError("The hero and helper must have different names.")
    return StoryParams(place=place, hero=hero, helper=helper, banjo_style=style)


def tell(params: StoryParams, rng: random.Random) -> World:
    if params.place not in PLACES:
        raise StoryError(f"Unknown place: {params.place}")
    if params.hero == params.helper:
        raise StoryError("The hero and helper must have different names.")
    if params.banjo_style not in {item[0] for item in BANJO_STYLES}:
        raise StoryError(f"Unknown banjo style: {params.banjo_style}")

    world = World(place=PLACES[params.place])
    hero = world.add(
        Entity(
            id="hero",
            kind="character",
            label=params.hero,
            meters={"cape_power": 8.0, "kindness_power": 3.0},
            memes={"confidence": 2.0},
        )
    )
    helper = world.add(
        Entity(
            id="helper",
            kind="character",
            label=params.helper,
            meters={"music_power": 7.0},
            memes={"shyness": 5.0},
        )
    )
    banjo = world.add(
        Entity(
            id="banjo",
            label="a blue banjo",
            owner=helper.id,
            meters={"warmth": 4.0},
            memes={"hope": 2.0},
        )
    )

    style_word, tune = next(item for item in BANJO_STYLES if item[0] == params.banjo_style)
    landmark, background = PLACE_DETAILS[params.place]
    introduction = rng.choice(INTRODUCTIONS)
    listeners = rng.randint(2, 5)

    world.say(f"In {world.place}, {introduction}.")
    world.say(
        f"Then a strange musical glow floated from {landmark}. "
        f"{hero.label} followed it and found {helper.label} holding {banjo.label}."
    )
    world.say(
        f"{helper.label} played {tune}, and even {background} seemed to listen. "
        f"The music was a secret reveal: {helper.label} had practiced the banjo alone because "
        "being heard made the shy musician nervous."
    )
    world.para()
    world.say(
        f"Just then, {listeners} children hurried into the square. "
        f'"That song could brighten everyone\'s evening," said {hero.label}. '
        f'"But only if you want to share it."'
    )
    world.say(
        f'"What if I make a mistake?" asked {helper.label}. '
        f'"Then I will share the brave part with you," said {hero.label}. '
        "She took off her shining cape and spread it on the ground as a little stage."
    )
    hero.memes["kindness"] = 8.0
    helper.memes["courage"] = 7.0
    hero.meters["cape_power"] -= 1.0

    world.say(
        f"{helper.label} stepped onto the cape, and {hero.label} stood beside the banjo. "
        f"They shared the song together: {helper.label} played the melody while {hero.label} "
        "clapped a steady beat for every listener."
    )
    world.say(
        f"When a string gave a tiny twang, {hero.label} smiled instead of hiding it. "
        f"The children clapped, and {helper.label} finished the tune with a proud grin."
    )
    world.para()
    world.say(
        f"Afterward, {helper.label} handed the banjo to the children one at a time. "
        f"Each child tried a gentle note while {hero.label} reminded everyone, "
        '"A power grows brighter when it is shared."'
    )
    world.say(
        f"The final reveal was not a secret weapon or a flashing cape. "
        f"It was {helper.label}'s courage, unlocked by {hero.label}'s kindness. "
        f"Under {background}, the blue banjo shone like a small moon."
    )

    world.facts.update(
        hero=hero,
        helper=helper,
        banjo=banjo,
        style=style_word,
        tune=tune,
        landmark=landmark,
        background=background,
        listeners=listeners,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    hero = world.facts["hero"]
    helper = world.facts["helper"]
    return [
        f"Write a superhero story where {hero.label} uses kindness to help {helper.label} reveal a secret banjo talent.",
        "Tell a child-friendly story about sharing music instead of keeping applause.",
        f"Write a warm adventure in which {hero.label} and {helper.label} turn a banjo reveal into a brave shared performance.",
    ]


def story_qa(world: World) -> list[QAItem]:
    facts = world.facts
    hero = facts["hero"].label
    helper = facts["helper"].label
    return [
        QAItem(
            question=f"What did {helper} reveal in the story?",
            answer=(
                f"{helper} revealed that they could play {facts['style']} music on a blue banjo. "
                f"They had practiced alone because being heard made them nervous."
            ),
        ),
        QAItem(
            question=f"How did {hero} use kindness to help {helper}?",
            answer=(
                f"{hero} asked whether {helper} wanted to share the song, promised to stand beside "
                f"them, and spread her cape out as a small stage. She also clapped a steady beat "
                "so the performance felt safe."
            ),
        ),
        QAItem(
            question="What changed after the banjo music was shared?",
            answer=(
                f"{helper} became more courageous, the children enjoyed the song, and everyone got "
                "a turn to try a gentle note. The secret talent became a shared joy."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a banjo?",
            answer="A banjo is a stringed musical instrument with a round body that can make bright, lively sounds.",
        ),
        QAItem(
            question="What does sharing mean?",
            answer="Sharing means willingly letting other people enjoy, use, or take part in something with you.",
        ),
        QAItem(
            question="What is kindness?",
            answer="Kindness means treating people with care and helping them feel safe, valued, and included.",
        ),
        QAItem(
            question="What does reveal mean?",
            answer="To reveal something means to show or tell it after it was hidden or kept secret.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(sample.prompts)
    lines.extend(["", "== story QA =="])
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.extend(["", "== world QA =="])
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


ASP_RULES = r"""
concept(reveal).
concept(banjo).
value(sharing).
value(kindness).
heroic(kindness).
valid_story(P) :- place(P), concept(reveal), concept(banjo), value(sharing), value(kindness).
"""


def asp_facts() -> str:
    import asp
    lines = [asp.fact("place", place) for place in PLACES]
    lines.extend(
        [
            asp.fact("concept", "reveal"),
            asp.fact("concept", "banjo"),
            asp.fact("value", "sharing"),
            asp.fact("value", "kindness"),
        ]
    )
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
        model = asp.one_model(asp_program("#show valid_story/1."))
    except Exception as exc:
        print(f"ASP unavailable: {exc}")
        return 1

    observed = set(asp.atoms(model, "valid_story"))
    expected = {(place,) for place in PLACES}
    if observed != expected:
        print("MISMATCH between ASP and Python.")
        print("ASP:", sorted(observed))
        print("PY:", sorted(expected))
        return 1

    for index, place in enumerate(PLACES):
        sample = generate(
            StoryParams(
                place=place,
                hero=HERO_NAMES[index % len(HERO_NAMES)],
                helper=HELPER_NAMES[index % len(HELPER_NAMES)],
                banjo_style=BANJO_STYLES[index % len(BANJO_STYLES)][0],
                seed=index,
            )
        )
        required = ("banjo", "kindness", "share", "reveal")
        if not all(word in sample.story.lower() for word in required):
            print(f"Generated story failed content check for {place}.")
            return 1

    print(f"OK: ASP parity matches Python ({len(observed)} places), and generated stories pass.")
    return 0


def generate(params: StoryParams) -> StorySample:
    rng = random.Random(params.seed)
    world = tell(params, rng)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print("\n-- trace --")
        for entity in sample.world.entities.values():
            print(
                f"{entity.id}: label={entity.label} owner={entity.owner} "
                f"meters={entity.meters} memes={entity.memes}"
            )
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()

    if args.verify:
        sys.exit(asp_verify())
    if args.show_asp or args.asp:
        print(asp_program("#show valid_story/1."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for index, place in enumerate(PLACES):
            params = StoryParams(
                place=place,
                hero=HERO_NAMES[index % len(HERO_NAMES)],
                helper=HELPER_NAMES[index % len(HELPER_NAMES)],
                banjo_style=BANJO_STYLES[index % len(BANJO_STYLES)][0],
                seed=base_seed + index,
            )
            samples.append(generate(params))
    else:
        for index in range(args.n):
            rng = random.Random(base_seed + index)
            params = resolve_params(args, rng)
            params.seed = base_seed + index
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
