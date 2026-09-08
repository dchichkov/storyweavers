#!/usr/bin/env python3
"""
A small nursery-rhyme storyworld about Sake, a brave little moon-moth,
and a penny-sized promise that transforms a dark garden.
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


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    type: str = "thing"
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)


@dataclass
class Setting:
    place: str
    affords: set[str]
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass(frozen=True)
class Verse:
    trouble: str
    danger: str
    clue: str
    action: str
    change: str
    ending: str
    trouble_answer: str
    bravery_answer: str


@dataclass
class StoryParams:
    name: str
    companion: str
    mood: str
    seed: Optional[int] = None


SETTING = Setting(
    place="the moonlit garden",
    affords={"sake", "pence", "bravery", "transformation"},
)

NAMES = ["Luna", "Pip", "Mira", "Nell", "Tansy", "Bram"]
COMPANIONS = ["a cricket", "a mouse", "a robin", "a small fox", "a sleepy frog"]
MOODS = ["bold", "gentle", "quiet", "cheerful"]

VERSES = [
    Verse(
        trouble="the silver gate was shut with a thread of midnight frost",
        danger="the garden's sleepy flowers could not open before dawn",
        clue="one warm penny shining beneath the thyme",
        action="{hero} held the penny near the frost while {companion} hummed a tiny tune",
        change="The penny glowed, the frost became dew, and the gate swung wide",
        ending="The flowers woke in a row, each wearing a bright drop like a crown",
        trouble_answer="A thread of midnight frost had shut the silver garden gate.",
        bravery_answer="{hero} bravely held the warm penny near the frost while {companion} hummed beside {hero}.",
    ),
    Verse(
        trouble="a black cloud had covered the lantern that guided the lost fireflies home",
        danger="the little fireflies circled sadly without its kindly glow",
        clue="three pence tucked inside an old acorn cup",
        action="{hero} climbed the bent lavender stem while {companion} steadied it below",
        change="The pence caught the moonlight and changed into a clear golden lantern",
        ending="The fireflies flew home in a twinkling ring around the garden pond",
        trouble_answer="A black cloud had covered the lantern that guided the fireflies.",
        bravery_answer="{hero} climbed the lavender stem while {companion} kept it steady, and together they raised the pence.",
    ),
    Verse(
        trouble="the wishing well had forgotten how to sing its silver song",
        danger="without the song, the garden's courage began to fade",
        clue="a small cup of sake left beside the well",
        action="{hero} poured one careful drop while {companion} tapped the well three times",
        change="The well changed its silence into a merry bubbling tune",
        ending="Even the shyest snail tapped its shell in time with the music",
        trouble_answer="The wishing well had stopped singing its silver song.",
        bravery_answer="{hero} poured one careful drop of sake while {companion} tapped the well three times.",
    ),
    Verse(
        trouble="a long shadow had turned the moonflowers into drooping bells",
        danger="the flowers would lose their soft light before morning",
        clue="a single penny hidden under a blue leaf",
        action="{hero} carried the penny into the shadow while {companion} called out a steady rhyme",
        change="The shadow folded into a small black seed, and the moonflowers stood tall",
        ending="Their pale bells rang softly whenever the night breeze passed",
        trouble_answer="A long shadow had made the moonflowers droop.",
        bravery_answer="{hero} carried the penny into the shadow while {companion} encouraged {hero} with a steady rhyme.",
    ),
]

MORALS = [
    "Bravery is a small light that can begin a great transformation.",
    "A brave heart and a helping friend can turn a dark spell into a bright song.",
    "When courage takes one step, the world may change its tune.",
]


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple[str, str]] = set()

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


def valid_params(params: StoryParams) -> None:
    if params.name not in NAMES:
        raise StoryError(f"unknown hero name: {params.name}")
    if params.companion not in COMPANIONS:
        raise StoryError(f"unknown companion: {params.companion}")
    if params.mood not in MOODS:
        raise StoryError(f"unknown mood: {params.mood}")


def generation_prompts(world: World) -> list[str]:
    verse = world.facts["verse"]
    return [
        'Write a Nursery Rhyme about sake, pence, bravery, and transformation.',
        f"Tell a rhyming garden tale about {world.facts['hero'].label} and {world.facts['companion'].label}.",
        f"Write a gentle rhyme in which bravery solves this trouble: {verse.trouble}.",
    ]


def story_questions(world: World) -> list[QAItem]:
    verse: Verse = world.facts["verse"]  # type: ignore[assignment]
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    companion: Entity = world.facts["companion"]  # type: ignore[assignment]
    return [
        QAItem(
            "Who helped the garden?",
            f"{hero.label} and {companion.label} helped the garden together.",
        ),
        QAItem("What trouble did they find?", verse.trouble_answer),
        QAItem("What clue helped them?", f"They found {verse.clue}."),
        QAItem("How did bravery change the trouble?", verse.bravery_answer),
        QAItem("What transformation happened?", f"{verse.change}."),
        QAItem(
            "What lesson did the rhyme teach?",
            str(world.facts["moral"]),
        ),
    ]


def world_questions(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What is bravery?",
            "Bravery means doing what is right even when something feels scary.",
        ),
        QAItem(
            "What is transformation?",
            "Transformation is a change from one shape, state, or condition into another.",
        ),
        QAItem(
            "What are pence?",
            "Pence are small units of money used in the United Kingdom.",
        ),
        QAItem(
            "What is sake?",
            "Sake is a drink made from fermented rice and is often served carefully in a small cup.",
        ),
    ]


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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    lines.append(f"  setting: {world.setting.place}")
    for entity in world.entities.values():
        lines.append(
            f"  {entity.id}: type={entity.type}, "
            f"meters={entity.meters}, memes={entity.memes}, tags={sorted(entity.tags)}"
        )
    lines.append(f"  fired rules: {sorted(world.fired)}")
    return "\n".join(lines)


def tell(params: StoryParams) -> World:
    valid_params(params)
    stable_seed = params.seed
    if stable_seed is None:
        stable_seed = sum(
            (i + 1) * ord(char)
            for i, char in enumerate(
                f"{params.name}:{params.companion}:{params.mood}"
            )
        )
    rng = random.Random(stable_seed)
    verse = rng.choice(VERSES)
    moral = rng.choice(MORALS)

    world = World(SETTING)
    hero = world.add(
        Entity(
            id="hero",
            kind="character",
            type="moth",
            label=params.name,
            meters={"courage": 0.0, "fear": 0.0},
            memes={"hope": 0.0, "joy": 0.0},
        )
    )
    companion = world.add(
        Entity(
            id="companion",
            kind="character",
            type="friend",
            label=params.companion,
            meters={"steadiness": 1.0},
            memes={"care": 1.0},
        )
    )
    world.add(
        Entity(
            id="pence",
            kind="object",
            type="coin",
            label="three bright pence",
            meters={"warmth": 0.0},
            memes={},
        )
    )
    world.add(
        Entity(
            id="sake",
            kind="object",
            type="cup",
            label="a tiny cup of sake",
            meters={"fullness": 1.0},
            memes={},
        )
    )

    world.facts.update(
        hero=hero,
        companion=companion,
        verse=verse,
        moral=moral,
    )

    companion_cap = companion.label[0].upper() + companion.label[1:]
    world.say(
        f"By the moonlit garden, {hero.label} fluttered light, "
        f"a {params.mood} moth in the night."
    )
    world.say(
        f"With {companion.label} near and a tiny cup of sake, "
        f"they carried bright pence for the garden's sake."
    )
    world.say(
        "“Where shall we go?” said the friend with a peep. "
        "“Wherever a flower has forgotten to sleep,” said "
        f"{hero.label}."
    )
    world.para()

    world.setting.meters["darkness"] = 1.0
    hero.meters["fear"] = 1.0
    hero.memes["hope"] = 0.0
    world.say(
        f"But {verse.trouble}. {verse.danger.capitalize()} "
        "The moon hid her face behind a gray cloud."
    )
    world.say(
        f"{hero.label} trembled beneath a leaf. "
        f"{companion_cap} whispered, “A trembling wing can still be brave.”"
    )
    world.say(
        f"“I will try,” said {hero.label}. “And I will not try alone,” "
        f"said {companion.label}."
    )
    world.para()

    hero.meters["courage"] = 1.0
    hero.meters["fear"] = 0.4
    hero.memes["hope"] = 1.0
    companion.memes["care"] = 2.0
    world.fired.add(("bravery", "hero"))
    world.say(f"Under the thyme they found {verse.clue}.")
    world.say(verse.action.format(hero=hero.label, companion=companion.label) + ".")
    world.say(verse.change + ".")
    world.para()

    world.setting.meters["darkness"] = 0.0
    hero.memes["joy"] = 1.0
    companion.memes["joy"] = 1.0
    world.fired.add(("transformation", "garden"))
    world.say(
        f"The garden changed its tune. {hero.label} laughed, and "
        f"{companion.label} danced a tiny circle."
    )
    world.say(verse.ending + ".")
    world.say(f"And the rhyme ended: {moral}")
    return world


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_questions(world),
        world_qa=world_questions(world),
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
    import asp

    lines = [
        asp.fact("setting", "moonlit_garden"),
        asp.fact("resource", "sake"),
        asp.fact("resource", "pence"),
        asp.fact("feature", "bravery"),
        asp.fact("feature", "transformation"),
    ]
    return "\n".join(lines)


ASP_RULES = r"""
valid_story(moonlit_garden, sake, pence) :-
    setting(moonlit_garden),
    resource(sake),
    resource(pence),
    feature(bravery),
    feature(transformation).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def valid_combos() -> list[tuple[str, str, str]]:
    return [("moonlit_garden", "sake", "pence")]


def asp_verify() -> int:
    python_set = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if python_set != asp_set:
        print("MISMATCH between Python and ASP story gates.")
        print("Only in Python:", sorted(python_set - asp_set))
        print("Only in ASP:", sorted(asp_set - python_set))
        return 1
    for params in [
        StoryParams("Luna", "a cricket", "bold", 1),
        StoryParams("Pip", "a mouse", "gentle", 2),
        StoryParams("Mira", "a robin", "quiet", 3),
    ]:
        sample = generate(params)
        if not sample.story or "brave" not in sample.story.lower():
            print("Generated-story verification failed.")
            return 1
    print("OK: ASP/Python parity and generated stories verified.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A Nursery Rhyme about sake, pence, bravery, and transformation."
    )
    parser.add_argument("--name", choices=NAMES)
    parser.add_argument("--companion", choices=COMPANIONS)
    parser.add_argument("--mood", choices=MOODS)
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
    return StoryParams(
        name=args.name or rng.choice(NAMES),
        companion=args.companion or rng.choice(COMPANIONS),
        mood=args.mood or rng.choice(MOODS),
    )


CURATED = [
    StoryParams("Luna", "a cricket", "bold", 101),
    StoryParams("Pip", "a mouse", "gentle", 102),
    StoryParams("Mira", "a robin", "quiet", 103),
    StoryParams("Nell", "a small fox", "cheerful", 104),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return

    if args.verify:
        raise SystemExit(asp_verify())

    if args.asp:
        import asp

        model = asp.one_model(asp_program("#show valid_story/3."))
        print(sorted(set(asp.atoms(model, "valid_story"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        if args.n < 1:
            raise StoryError("-n must be at least 1")
        for index in range(args.n):
            rng = random.Random(base_seed + index)
            params = resolve_params(args, rng)
            params.seed = base_seed + index
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(
                json.dumps(
                    [sample.to_dict() for sample in samples],
                    indent=2,
                    ensure_ascii=False,
                )
            )
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
