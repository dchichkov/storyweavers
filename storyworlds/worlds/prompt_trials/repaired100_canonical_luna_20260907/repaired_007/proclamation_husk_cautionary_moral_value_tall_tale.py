#!/usr/bin/env python3
"""
A small tall-tale storyworld about a proclamation, a husk, and the moral value
of checking a boast before everyone follows it.
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    place: str
    hero: Entity
    helper: Entity
    husk: Entity
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

    def say(self, text: str) -> None:
        self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


@dataclass(frozen=True)
class Arc:
    key: str
    opening: tuple[str, str]
    trouble: tuple[str, str]
    turn: tuple[str, str]
    ending: tuple[str, str]
    problem: str
    action: str
    result: str


ARCS = (
    Arc(
        "corn-crown",
        (
            "In {place}, {hero} found a golden husk beside the grain mill.",
            "It was only a dry corn husk, but in {hero}'s hands it looked taller than a flag.",
        ),
        (
            "{hero} raised it high and made a proclamation: “This husk can hold up the sky!”",
            "The villagers cheered, and three goats began tugging the clouds to see if he was right.",
        ),
        (
            "“Let us test it before the whole town climbs aboard,” said {helper}.",
            "{hero} pressed the husk against a small basket, and it crackled flat as a leaf.",
        ),
        (
            "{hero} lowered the proclamation and used the husk to wrap warm bread instead.",
            "The village laughed kindly. From then on, they checked a thing before making it king of the world.",
        ),
        "the villagers nearly trusted a dry husk to support the sky",
        "the friends tested the husk against a small basket before anyone climbed on it",
        "the husk became a useful bread wrapper instead of a dangerous sky brace",
    ),
    Arc(
        "river-sail",
        (
            "By the wide river at {place}, {hero} discovered a striped husk caught in the reeds.",
            "He called it a sail, though it was no bigger than a soup spoon.",
        ),
        (
            "{hero} made a proclamation: “This mighty sail will carry our wagon across the river!”",
            "The wagon rolled toward the water, while ducks paddled away from the enormous plan.",
        ),
        (
            "“A bold claim needs a careful test,” said {helper}.",
            "They tied the husk to a toy boat first. The boat spun once and sailed nowhere.",
        ),
        (
            "{hero} stopped the wagon before its wheels kissed the river.",
            "They dried the husk and used it as a little flag. The moral was plain: courage is good, but care keeps courage from becoming a splash.",
        ),
        "the wagon was about to enter the river behind a tiny husk sail",
        "the friends tested the claimed sail on a toy boat first",
        "the wagon stayed safe and the husk became a harmless flag",
    ),
    Arc(
        "windy-roof",
        (
            "On the tallest hill in {place}, {hero} found a silver husk shining in the grass.",
            "He held it above his head, and the wind made it hum like a trumpet.",
        ),
        (
            "{hero} shouted a proclamation: “This husk can stop every storm!”",
            "The neighbors hurried to nail it onto the school roof before the next cloud arrived.",
        ),
        (
            "“Before we nail a promise to a roof, let us ask the wind,” said {helper}.",
            "They placed the husk in a basket and blew a bellows at it. The husk flew three steps and landed in a puddle.",
        ),
        (
            "{hero} called off the roof plan and tied the husk to a weather vane instead.",
            "When the wind came, the vane spun merrily. The town remembered that a tested idea can guide people better than a grand proclamation.",
        ),
        "the town nearly trusted a husk to stop a storm",
        "the friends tested the husk with a bellows before putting it on the roof",
        "the husk became a safe weather vane and no one climbed onto the roof",
    ),
)


@dataclass
class StoryParams:
    place: str
    hero_name: str
    helper_name: str
    hero_gender: str = "boy"
    helper_gender: str = "girl"
    seed: Optional[int] = None


PLACES = {
    "bell_valley": "Bell Valley",
    "giant_meadow": "Giant Meadow",
    "whistling_hill": "Whistling Hill",
}
NAMES = {
    "boy": ["Luna", "Milo", "Tavi", "Pip"],
    "girl": ["Nora", "Luna", "Mara", "Zia"],
}


def build_world(params: StoryParams) -> World:
    if params.place not in PLACES:
        raise StoryError("Unknown place.")
    if params.hero_name == params.helper_name:
        raise StoryError("Hero and helper must have different names.")
    rng = random.Random(params.seed if params.seed is not None else 0)
    arc = ARCS[rng.randrange(len(ARCS))]
    hero = Entity(params.hero_name, "character", params.hero_gender, params.hero_name)
    helper = Entity(params.helper_name, "character", params.helper_gender, params.helper_name)
    husk = Entity("husk", "object", "husk", "dry husk")
    world = World(PLACES[params.place], hero, helper, husk)

    values = {"place": world.place, "hero": hero.label, "helper": helper.label}
    for line in arc.opening:
        world.say(line.format(**values))
    world.para()

    hero.meters["boast"] = 1
    husk.meters["untested"] = 1
    hero.memes["pride"] = 1
    for line in arc.trouble:
        world.say(line.format(**values))
    world.para()

    helper.memes["wisdom"] = 1
    husk.meters["tested"] = 1
    husk.meters["dangerous_plan"] = 0
    for line in arc.turn:
        world.say(line.format(**values))
    world.para()

    hero.meters["boast"] = 0
    husk.meters["useful"] = 1
    hero.memes["humility"] = 1
    helper.memes["care"] = 1
    for line in arc.ending:
        world.say(line.format(**values))

    world.facts.update(
        arc=arc.key,
        proclamation="a proclamation that the husk could perform an enormous task",
        problem=arc.problem,
        action=arc.action,
        result=arc.result,
        moral="Check a boast before asking others to trust it.",
        ending=arc.ending[-1].format(**values),
        tested=True,
    )
    return world


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=[
            "Write a child-friendly tall tale containing the words proclamation and husk.",
            f"Tell a cautionary story about {params.hero_name} learning to test a boast.",
            "Show a moral value through a concrete choice and a changed ending.",
        ],
        story_qa=[
            QAItem(
                "What was the proclamation?",
                f"The proclamation was {world.facts['proclamation']}. It sounded grand, but it had not been tested."
            ),
            QAItem(
                "How did the characters avoid trouble?",
                f"They avoided trouble because {world.facts['action']}. Testing the idea changed what they decided to do."
            ),
            QAItem(
                "What moral value did the story teach?",
                world.facts["moral"],
            ),
        ],
        world_qa=[
            QAItem(
                "What is a husk?",
                "A husk is a dry outer covering around a seed, grain, or plant part."
            ),
            QAItem(
                "Why should people test a bold claim?",
                "Testing a bold claim can reveal whether it is safe and useful before other people rely on it."
            ),
        ],
        world=world,
    )


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
    for entity in (world.hero, world.helper, world.husk):
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        lines.append(f"  {entity.id}: meters={meters}, memes={memes}")
    lines.append(f"  tested={world.facts.get('tested')}")
    lines.append(f"  moral={world.facts.get('moral')}")
    return "\n".join(lines)


ASP_RULES = r"""
untested(husk).
proclamation(boast).
careful_test :- untested(husk), proclamation(boast).
safe_choice :- careful_test.
moral_value(caution).
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("husk", "husk"),
            asp.fact("boast", "boast"),
            asp.fact("place", "bell_valley"),
        ]
    )


def asp_program(show: str = "#show safe_choice/0.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    try:
        model = asp.one_model(asp_program())
        if not asp.atoms(model, "safe_choice"):
            print("ASP parity failed: no safe choice.")
            return 1
        sample = generate(
            StoryParams(
                place="bell_valley",
                hero_name="Luna",
                helper_name="Nora",
                seed=1,
            )
        )
        if not sample.story.strip() or "proclamation" not in sample.story or "husk" not in sample.story:
            print("Story smoke test failed.")
            return 1
    except Exception as exc:
        print(f"Verification failed: {exc}")
        return 1
    print("OK: smoke tests passed.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A cautionary tall tale about a proclamation and a husk.")
    parser.add_argument("--place", choices=PLACES)
    parser.add_argument("--hero")
    parser.add_argument("--helper")
    parser.add_argument("--hero-gender", choices=["boy", "girl"], default="boy")
    parser.add_argument("--helper-gender", choices=["boy", "girl"], default="girl")
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int)
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
    hero_gender = args.hero_gender
    helper_gender = args.helper_gender
    hero = args.hero or rng.choice(NAMES[hero_gender])
    possible = [name for name in NAMES[helper_gender] if name != hero]
    helper = args.helper or rng.choice(possible)
    return StoryParams(
        place=place,
        hero_name=hero,
        helper_name=helper,
        hero_gender=hero_gender,
        helper_gender=helper_gender,
        seed=args.seed,
    )


CURATED = [
    StoryParams("bell_valley", "Luna", "Nora", seed=1),
    StoryParams("giant_meadow", "Milo", "Mara", seed=2),
    StoryParams("whistling_hill", "Tavi", "Zia", seed=3),
]


def emit(sample: StorySample, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world:
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
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program())
        print(asp.atoms(model, "safe_choice"))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples = []
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
