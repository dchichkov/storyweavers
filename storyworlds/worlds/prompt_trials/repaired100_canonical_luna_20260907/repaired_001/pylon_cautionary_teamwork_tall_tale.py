#!/usr/bin/env python3
"""
A cautionary tall tale about a pylon, a proud plan, and teamwork.

Luna wants to raise the tallest pylon in town. She thinks one pair of hands
can do everything, but a gust of wind and a wobbly base teach her that tall
things need careful plans and many helpers.
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
    "hill": "the windy hill",
    "square": "the town square",
    "marsh": "the edge of the blue marsh",
    "meadow": "the wide meadow",
}
NAMES = ["Luna", "Milo", "Pip", "Tess", "Orin", "Mara"]
HELPERS = ["Grandma", "the baker", "the shepherd", "the teacher"]
MATERIALS = ["painted poles", "smooth pine beams", "bright cedar lengths"]
FLAGS = ["a red flag", "a golden flag", "a blue flag"]


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    count: int = 0


@dataclass
class World:
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


@dataclass
class StoryParams:
    place: str
    name: str
    helper: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A cautionary teamwork tall tale about a pylon.")
    parser.add_argument("--place", choices=sorted(PLACES))
    parser.add_argument("--name", choices=NAMES)
    parser.add_argument("--helper", choices=HELPERS)
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
    place = args.place or rng.choice(list(PLACES))
    name = args.name or rng.choice(NAMES)
    helper = args.helper or rng.choice(HELPERS)
    return StoryParams(place=place, name=name, helper=helper)


def tell(params: StoryParams, rng: random.Random) -> World:
    world = World(PLACES[params.place])
    hero = world.add(Entity("hero", "character", params.name, memes={"pride": 2}))
    helper = world.add(Entity("helper", "character", params.helper, memes={"patience": 2}))
    pylon = world.add(Entity("pylon", "structure", "the pylon", meters={"height": 0.0, "stability": 0.0}))
    ropes = world.add(Entity("ropes", "tool", "four strong ropes", count=4))
    material = rng.choice(MATERIALS)
    flag = rng.choice(FLAGS)
    needed = rng.choice([6, 7, 8])
    first_load = needed - 2
    second_load = 2
    gust = rng.choice(["a sharp gust", "a dancing wind", "a sudden hill wind"])

    world.say(
        f"One bright morning in {world.place}, {params.name} announced that "
        f"{hero.label} would raise the tallest pylon anyone had ever seen."
    )
    world.say(
        f"{params.name} gathered {material} and {flag}. The plan was grand, "
        f"but the pylon needed {needed} pieces and a steady base before it could touch the clouds."
    )
    world.say(
        f"{params.helper} carried {ropes.label}, but {params.name} waved them away. "
        f"\"I can raise this pylon alone,\" said {params.name}. \"My arms are stronger than a storm!\""
    )
    world.para()
    world.say(
        f"{params.helper} pointed to the sloping ground. \"A tall pylon needs a level base and helping hands,\" "
        f"{params.helper} warned. \"Will you let us brace it together?\""
    )
    world.say(
        f"\"No need!\" cried {params.name}. \"Watch my mighty work!\" "
        "The boast made the nearby birds flap out of the trees."
    )
    world.say(
        f"{params.name} stacked {first_load} pieces, then hurried for the last {second_load}. "
        f"The unfinished pylon leaned while {params.name} tried to hold it with one shoulder."
    )
    pylon.meters["height"] = float(first_load)
    pylon.meters["stability"] = 1.0
    world.say(
        f"Just then, {gust} swept across the ground. The leaning pylon groaned, "
        "and the flag whipped around like a red bird."
    )
    world.say(
        f"\"Now! Grab the ropes!\" shouted {params.name}. \"I cannot hold it alone!\""
    )
    world.say(
        f"{params.helper} called to the baker, the shepherd, and the children nearby. "
        f"Together they pulled the ropes tight, lowered the pylon safely, and leveled its base."
    )
    pylon.meters["stability"] = 4.0
    hero.memes["pride"] = 1
    hero.memes["gratitude"] = 3
    helper.memes["trust"] = 3
    world.say(
        f"Then everyone counted carefully: {first_load} pieces and {second_load} pieces made {needed}. "
        f"With teamwork, they raised the pylon again and tied {flag} to its top."
    )
    pylon.meters["height"] = float(needed)
    world.para()
    world.say(
        f"The pylon stood straight above {world.place}, and its flag waved over every roof. "
        f"{params.name} bowed to the helpers."
    )
    world.say(
        f"\"A tall pylon may begin with one dream,\" said {params.name}, "
        "\"but it stays standing because many people care for it.\""
    )
    world.say(
        f"From that day on, {params.name} tested every base, listened to every warning, "
        "and never mistook a loud boast for a strong plan."
    )

    world.facts.update(
        hero=hero,
        helper=helper,
        pylon=pylon,
        ropes=ropes,
        material=material,
        flag=flag,
        needed=needed,
        first_load=first_load,
        second_load=second_load,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a cautionary tall tale about {f['hero'].label} trying to raise a pylon.",
        "Tell a child-friendly story showing why teamwork makes a tall structure safe.",
        "Write a tall tale with a warning, a pylon, a sudden wind, and a happy teamwork ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    return [
        QAItem(
            question=f"What did {f['hero'].label} try to build?",
            answer=(
                f"{f['hero'].label} tried to build the tallest pylon anyone had ever seen in "
                f"{world.place}, using {f['material']} and {f['flag']}."
            ),
        ),
        QAItem(
            question=f"Why did the pylon begin to lean?",
            answer=(
                f"The pylon began to lean because {f['hero'].label} rushed ahead without leveling "
                f"the base or using the four strong ropes. It was still missing {f['second_load']} "
                f"pieces when the wind pushed against it."
            ),
        ),
        QAItem(
            question="How did the helpers save the pylon?",
            answer=(
                f"{f['helper'].label} called other people to help. Together they pulled the ropes, "
                "lowered the pylon safely, leveled its base, counted all the pieces, and raised it again."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a pylon?",
            answer="A pylon is a tall post or frame that can hold wires, lights, signs, or flags.",
        ),
        QAItem(
            question="Why should a tall structure have a steady base?",
            answer="A steady base helps keep a tall structure from tipping when wind or movement pushes it.",
        ),
        QAItem(
            question="What does teamwork mean?",
            answer="Teamwork means people joining their skills and effort to reach a shared goal.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(sample.prompts)
    lines.append("")
    lines.append("== story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


ASP_RULES = r"""
structure(pylon).
virtue(teamwork).
lesson(caution).
needs_base(pylon).
needs_helpers(pylon).
safe(pylon) :- needs_base(pylon), needs_helpers(pylon), virtue(teamwork).
valid_story :- structure(pylon), lesson(caution), safe(pylon).
#show valid_story/0.
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("structure", "pylon"),
            asp.fact("virtue", "teamwork"),
            asp.fact("lesson", "caution"),
        ]
    )


def asp_program(show: str = "#show valid_story/0.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
    except Exception as exc:
        print(f"ASP unavailable: {exc}")
        return 1
    model = asp.one_model(asp_program())
    found = set(asp.atoms(model, "valid_story"))
    if found == {()}:
        print("OK: ASP parity matches Python.")
        return 0
    print("MISMATCH between ASP and Python.")
    print("ASP:", sorted(found))
    print("PY:", [()])
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(params, random.Random(params.seed))
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
                f"{entity.id}: kind={entity.kind} label={entity.label} "
                f"count={entity.count} meters={entity.meters} memes={entity.memes}"
            )
    if qa:
        print("\n" + format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()

    if args.verify:
        raise SystemExit(asp_verify())
    if args.show_asp or args.asp:
        print(asp_program())
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for place in PLACES:
            for name in NAMES[:2]:
                params = StoryParams(
                    place=place,
                    name=name,
                    helper=HELPERS[0],
                    seed=base_seed,
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
