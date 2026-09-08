#!/usr/bin/env python3
"""
A heartwarming parade story about a sailor, an infantry drummer, and a quiet
twist that lets two friends march in one another's place.
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
    sailor_name: str = "Mara"
    infantry_name: str = "Theo"
    parade_name: str = "Harbor Day Parade"
    route: str = "the sunny harbor road"
    instrument: str = "brass whistle"
    twist: str = "shared_uniform"
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


TWISTS = {
    "shared_uniform": {
        "problem": "Mara's sailor jacket was too heavy for her sore shoulder, while Theo's infantry coat had a loose brass button.",
        "clue": "Theo noticed that Mara could still carry the parade flag if the coat's long strap held it close.",
        "change": "They exchanged only the useful parts: Mara wore Theo's light sash, and Theo fastened Mara's flag strap across his coat.",
        "result": "Mara marched comfortably, and Theo kept the flag steady beside the infantry drum.",
        "ending": "At the parade's finish, they pinned both uniforms on the same wooden stand, side by side.",
        "lesson": "help should fit the person who receives it",
    },
    "missing_drum": {
        "problem": "The infantry drum's strap snapped just before the parade, and Theo could not carry it and keep the marching beat.",
        "clue": "Mara saw that the sailor's signal rope was strong, soft, and long enough to make a new drum strap.",
        "change": "She braided the signal rope into a snug harness while Theo tested each step beside her.",
        "result": "The drum rested safely against Theo's chest, and the beat returned before the parade began.",
        "ending": "Children along the route tapped the rhythm on their knees as the repaired drum led everyone home.",
        "lesson": "a different skill can solve an unexpected problem",
    },
    "quiet_signal": {
        "problem": "A loud cannon salute frightened a little harbor dog, and the sailor's whistle could not be heard over the parade music.",
        "clue": "Theo noticed that infantry hand signals were clear even when the marching band grew noisy.",
        "change": "Mara and Theo taught the parade a gentle pattern of colored flags and hand waves instead of sharper sounds.",
        "result": "The dog found its family, and the parade kept moving without another frightening blast.",
        "ending": "At the final corner, the whole parade waved silently before cheering.",
        "lesson": "kindness can change the way a whole group acts",
    },
    "rainy_route": {
        "problem": "Rain turned the parade route muddy, and Mara's sailor shoes slipped whenever she carried the banner uphill.",
        "clue": "Theo remembered that infantry packs had wide straps that spread weight instead of letting it pull one way.",
        "change": "They tied the banner to a broad shoulder harness and marked a safer path with bright shells.",
        "result": "Mara climbed steadily, while Theo guided the marchers around every puddle.",
        "ending": "Rain shone on the banner like tiny stars when the parade reached the warm town hall.",
        "lesson": "careful preparation can make a difficult path kinder",
    },
}

PARADE_NAMES = ["Harbor Day Parade", "Lantern Homecoming", "Founders' Morning March"]
ROUTES = ["the sunny harbor road", "the hill beside the old lighthouse", "the square near the ferry docks"]
INSTRUMENTS = ["brass whistle", "small drum", "silver bell"]

ASP_RULES = r"""
parade(P) :- parade_name(P).
sailor(S) :- role(S, sailor).
infantry(I) :- role(I, infantry).
ready(P) :- parade_name(P), prepared(P).
helped(S, I) :- supports(S, I).
heartwarming(P) :- ready(P), helped(_, _), lesson_learned.
twist(P) :- parade_name(P), changed_plan(P).
"""


def asp_facts() -> str:
    import asp

    return "\n".join(
        [
            asp.fact("parade_name", "harbor_day_parade"),
            asp.fact("role", "mara", "sailor"),
            asp.fact("role", "theo", "infantry"),
            asp.fact("prepared", "harbor_day_parade"),
            asp.fact("supports", "mara", "theo"),
            asp.fact("changed_plan", "harbor_day_parade"),
            asp.fact("lesson_learned"),
        ]
    )


def asp_program(show: str = "#show heartwarming/1.\n#show twist/1.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program())
    names = {(sym.name, tuple(str(arg) for arg in sym.arguments)) for sym in model}
    expected = {
        ("heartwarming", ("harbor_day_parade",)),
        ("twist", ("harbor_day_parade",)),
    }
    if expected.issubset(names):
        print("OK: ASP and Python parity looks good.")
        return 0
    print("MISMATCH between ASP and Python reasoning.")
    print("ASP:", sorted(names))
    print("PY :", sorted(expected))
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate a heartwarming parade story about a sailor and infantry friend."
    )
    parser.add_argument("--sailor")
    parser.add_argument("--infantry")
    parser.add_argument("--parade", choices=PARADE_NAMES)
    parser.add_argument("--route", choices=ROUTES)
    parser.add_argument("--instrument", choices=INSTRUMENTS)
    parser.add_argument("--twist", choices=list(TWISTS))
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
    sailor_names = ["Mara", "Lina", "Jo", "Nell", "Suri"]
    infantry_names = ["Theo", "Ben", "Owen", "Cal", "Ira"]
    sailor = args.sailor or rng.choice(sailor_names)
    infantry = args.infantry or rng.choice([name for name in infantry_names if name != sailor])
    if sailor == infantry:
        raise StoryError("The sailor and infantry marcher must have different names.")
    return StoryParams(
        sailor_name=sailor,
        infantry_name=infantry,
        parade_name=args.parade or rng.choice(PARADE_NAMES),
        route=args.route or rng.choice(ROUTES),
        instrument=args.instrument or rng.choice(INSTRUMENTS),
        twist=args.twist or rng.choice(list(TWISTS)),
    )


def generate(params: StoryParams) -> StorySample:
    if params.twist not in TWISTS:
        raise StoryError(f"Unknown twist: {params.twist}")
    if params.sailor_name == params.infantry_name:
        raise StoryError("A sailor and an infantry marcher cannot be the same person.")

    rng = random.Random(
        params.seed
        if params.seed is not None
        else f"{params.sailor_name}:{params.infantry_name}:{params.twist}"
    )
    twist = TWISTS[params.twist]
    world = World()

    sailor = world.add(
        Entity(
            "sailor",
            "character",
            params.sailor_name,
            meters={"balance": 0.8, "strength": 0.7},
            memes={"pride": 0.7, "worry": 0.2},
        )
    )
    infantry = world.add(
        Entity(
            "infantry",
            "character",
            params.infantry_name,
            meters={"balance": 0.9, "strength": 0.8},
            memes={"pride": 0.6, "worry": 0.2},
        )
    )
    banner = world.add(
        Entity(
            "parade_banner",
            "object",
            "the blue harbor banner",
            meters={"wetness": 0.0, "stability": 0.6},
            memes={"belonging": 0.5},
        )
    )

    openings = [
        f"On the morning of the {params.parade_name}, {params.sailor_name} polished a brass button beside the harbor.",
        f"The {params.parade_name} was ready to begin along {params.route}, but {params.sailor_name} had one worry.",
        f"Flags fluttered above {params.route} as {params.sailor_name}, a cheerful sailor, joined the parade.",
    ]
    world.say(rng.choice(openings))
    world.say(
        f"Her friend {params.infantry_name}, an infantry marcher with a careful drumbeat, waited beside the {params.instrument}."
    )
    world.say(twist["problem"])
    sailor.memes["worry"] += 0.8
    banner.meters["stability"] -= 0.2

    world.say(
        f"“We still have time to find a kinder way,” {params.infantry_name} said. "
        f"“Will you look with me?”"
    )
    world.say(
        f"“Yes,” {params.sailor_name} answered. “I want everyone to enjoy the parade, not just watch me struggle.”"
    )
    world.say(
        f"They paused beside the parade cart instead of rushing into the street, and {params.infantry_name} studied what was safe to change."
    )
    world.say(twist["clue"])
    world.say(
        f"The clue mattered because it connected {params.sailor_name}'s sailor training with {params.infantry_name}'s infantry practice."
    )

    sailor.meters["balance"] += 0.2
    infantry.meters["strength"] += 0.1
    banner.meters["stability"] = 1.0
    banner.memes["belonging"] = 1.0
    world.say(twist["change"])
    world.say(
        f"Then they took three small practice steps along {params.route}. "
        f"The {params.instrument} stayed steady, and the banner moved gently instead of tugging."
    )
    world.say(twist["result"])
    world.say(
        f"“You did not march for me,” {params.sailor_name} told {params.infantry_name}. "
        f"“You helped me find my own good step.”"
    )
    world.say(
        f"{params.infantry_name} smiled. “And your sailor eyes noticed the rope I would have missed.”"
    )
    world.say(
        f"Together they led the parade past the harbor boats, where families waved from the sunny road."
    )
    world.say(twist["lesson"].capitalize() + ".")
    world.say(twist["ending"])

    world.facts.update(
        sailor=sailor,
        infantry=infantry,
        banner=banner,
        parade=params.parade_name,
        route=params.route,
        twist=params.twist,
        problem=twist["problem"],
        clue=twist["clue"],
        change=twist["change"],
        result=twist["result"],
        lesson=twist["lesson"],
        prepared=True,
        lesson_learned=True,
    )

    prompts = [
        f"Write a heartwarming story about sailor {params.sailor_name} and infantry marcher {params.infantry_name} at the {params.parade_name}.",
        f"Include a twist in which the friends solve this problem: {twist['problem']}",
        f"Show how this clue causes the change: {twist['clue']}",
    ]
    story_qa = [
        QAItem(
            question="What problem interrupted the parade?",
            answer=twist["problem"],
        ),
        QAItem(
            question=f"What clue did {params.infantry_name} notice?",
            answer=twist["clue"],
        ),
        QAItem(
            question="What was the twist in the plan?",
            answer=twist["change"],
        ),
        QAItem(
            question="What proved that the new plan worked?",
            answer=twist["result"],
        ),
        QAItem(
            question=f"What did {params.sailor_name} and {params.infantry_name} learn?",
            answer=f"They learned that {twist['lesson']}.",
        ),
    ]
    world_qa = [
        QAItem(
            question="What does a sailor do?",
            answer="A sailor works on or around boats and learns how to travel safely on water.",
        ),
        QAItem(
            question="What is infantry?",
            answer="Infantry are soldiers who travel and work on foot.",
        ),
        QAItem(
            question="Why do parades use flags and music?",
            answer="Flags and music help people celebrate together and make the parade easy to follow.",
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


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print("--- trace ---")
        for key, entity in sample.world.entities.items():
            print(f"{key}: {entity.label} meters={entity.meters} memes={entity.memes}")
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
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for index, twist in enumerate(TWISTS):
            params = StoryParams(
                sailor_name="Mara",
                infantry_name="Theo",
                parade_name=PARADE_NAMES[index % len(PARADE_NAMES)],
                route=ROUTES[index % len(ROUTES)],
                instrument=INSTRUMENTS[index % len(INSTRUMENTS)],
                twist=twist,
                seed=base_seed + index,
            )
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        index = 0
        while len(samples) < max(1, args.n) and index < max(50, args.n * 20):
            params = resolve_params(args, random.Random(base_seed + index))
            params.seed = base_seed + index
            sample = generate(params)
            if sample.story not in seen:
                samples.append(sample)
                seen.add(sample.story)
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
