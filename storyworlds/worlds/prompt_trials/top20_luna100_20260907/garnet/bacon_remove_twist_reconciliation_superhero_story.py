#!/usr/bin/env python3
"""
A small superhero storyworld about bacon, a surprising twist, and reconciliation.
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
    rival: Item
    bacon: Item
    place: str
    seed: int
    facts: dict = field(default_factory=dict)


@dataclass
class StoryParams:
    name: str
    rival_name: str
    place: str
    seed: Optional[int] = None


NAMES = ["Luna", "Maya", "Nova", "Zara", "Theo", "Juno", "Pip", "Kai"]
RIVALS = ["Captain Crumb", "Dr. Sizzle", "The Grease Goblin", "Baron Butter", "Mister Munch"]
PLACES = [
    "the rooftop breakfast lab",
    "the bright city square",
    "the pancake tower",
    "the moonlit food truck lane",
    "the superhero clubhouse",
]


ASP_RULES = r"""
#show brave/1.
#show reconciled/1.
#show rescued/1.

brave(H) :- faces_danger(H).
rescued(H) :- removes_bacon(H).
reconciled(H) :- shares_bacon(H), understands_rival(H).
"""


def asp_facts() -> str:
    import asp

    return "\n".join(
        [
            asp.fact("faces_danger", "hero"),
            asp.fact("removes_bacon", "hero"),
            asp.fact("shares_bacon", "hero"),
            asp.fact("understands_rival", "hero"),
        ]
    )


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    shown = "#show brave/1.\n#show rescued/1.\n#show reconciled/1."
    model = asp.one_model(asp_program(shown))
    actual = set()
    for atom in model:
        if atom.name not in {"brave", "rescued", "reconciled"}:
            continue
        args = tuple(
            value.number if value.type.name == "Number" else value.name
            for value in atom.arguments
        )
        actual.add((atom.name, args))
    expected = {
        ("brave", ("hero",)),
        ("rescued", ("hero",)),
        ("reconciled", ("hero",)),
    }
    if actual == expected:
        print("OK: ASP parity verified.")
        return 0
    print("MISMATCH between ASP and Python expectations.")
    print("ASP:", sorted(actual))
    print("PY :", sorted(expected))
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Superhero storyworld about bacon, removal, and reconciliation."
    )
    parser.add_argument("--name", choices=NAMES)
    parser.add_argument("--rival-name", choices=RIVALS)
    parser.add_argument("--place", choices=PLACES)
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
        rival_name=args.rival_name or rng.choice(RIVALS),
        place=args.place or rng.choice(PLACES),
    )


def build_world(params: StoryParams) -> World:
    if not params.name or not params.rival_name or not params.place:
        raise StoryError("A hero, rival, and place are required.")
    seed = params.seed
    if seed is None:
        seed = sum(ord(ch) for ch in f"{params.name}|{params.rival_name}|{params.place}")
    hero = Item(
        id="hero",
        label=params.name,
        phrase=f"hero {params.name}",
        kind="character",
        memes={"courage": 0.7, "trust": 0.3},
    )
    rival = Item(
        id="rival",
        label=params.rival_name,
        phrase=params.rival_name,
        kind="character",
        memes={"loneliness": 0.8, "trust": 0.1},
    )
    bacon = Item(
        id="bacon",
        label="bacon",
        phrase="a sizzling strip of rescue bacon",
        owner="rival",
        meters={"warmth": 0.8, "saltiness": 0.9},
        memes={"comfort": 0.9, "misunderstanding": 0.6},
    )
    return World(hero=hero, rival=rival, bacon=bacon, place=params.place, seed=seed)


def _choice(rng: random.Random, values: list[str]) -> str:
    return values[rng.randrange(len(values))]


def _record(
    world: World,
    *,
    danger: str,
    twist: str,
    cause: str,
    removal: str,
    reconciliation: str,
    ending: str,
    lines: list[str],
) -> str:
    world.facts.update(
        danger=danger,
        twist=twist,
        cause=cause,
        removal=removal,
        reconciliation=reconciliation,
        ending=ending,
        rescued=True,
        reconciled=True,
    )
    world.hero.memes["trust"] = 0.9
    world.rival.memes["trust"] = 0.8
    world.rival.memes["loneliness"] = 0.1
    world.bacon.owner = "shared"
    world.bacon.memes["misunderstanding"] = 0.0
    return " ".join(lines)


def _build_story(world: World, rng: random.Random) -> str:
    hero = world.hero.label
    rival = world.rival.label
    place = world.place
    danger = _choice(
        rng,
        [
            "a runaway breakfast balloon",
            "a giant hungry robot",
            "a wobbling stack of pancake boxes",
            "a city-sized toaster",
        ],
    )
    landing = _choice(
        rng,
        [
            "the library roof",
            "a soft pile of parade cushions",
            "the clubhouse trampoline",
            "the mayor's enormous picnic blanket",
        ],
    )
    reveal = _choice(
        rng,
        [
            "the bacon was a signal beacon, not a weapon",
            "the rival had been saving the bacon for frightened children",
            "the smoky smell was hiding a broken emergency alarm",
            "the bacon machine could only be stopped by sharing its power",
        ],
    )
    danger_fact = f"{danger} threatened to crash toward {landing}"
    twist = f"{rival} was not trying to cause trouble; {reveal}"
    cause = "the heroes mistook a rescue plan for a bacon-powered attack"
    removal = f"{hero} used a cooling gust to remove the bacon from the machine and pull the emergency lever"
    reconciliation = (
        f"{hero} listened to {rival}, apologized for the mistake, and shared the rescued bacon"
    )
    ending = f"the two former enemies stood together above {place}, guarding a warm breakfast for everyone"
    lines = [
        f"At {place}, {hero} spotted {danger} rolling through the sky while {rival} waved a sizzling strip of bacon.",
        f'"Drop the bacon!" shouted {hero}. "Never!" cried {rival}. "It is the key to saving the city!"',
        f"{hero} fired a silver lasso, but the bacon machine spun faster and sent sparks over the rooftops.",
        f'"I am trying to help!" {rival} yelled. "Then why does everything look worse?" {hero} called back.',
        f"That question made {hero} pause. The smoke smelled strange, and the machine's warning light blinked in a careful rhythm.",
        f"The twist appeared when {hero} read the blinking pattern: {reveal}.",
        f"{hero} flew close, used a cooling gust to remove the bacon from the machine, and pulled the emergency lever. The runaway danger slowed before it reached {landing}.",
        f'"You thought I was stealing breakfast," said {rival. "I thought you were wrecking the city," admitted {hero}.',
        f"{hero} lowered the cape, listened to the whole plan, and apologized. Then {hero} and {rival} shared the rescued bacon with the waiting crowd.",
        f"By sunset, {ending}. The city learned that even a superhero sometimes has to stop, listen, and make room for a friend.",
    ]
    return _record(
        world,
        danger=danger_fact,
        twist=twist,
        cause=cause,
        removal=removal,
        reconciliation=reconciliation,
        ending=ending,
        lines=lines,
    )


def generate_story(world: World) -> str:
    rng = random.Random(world.seed ^ 0xBACA0)
    return _build_story(world, rng)


def story_qa(world: World) -> list[QAItem]:
    hero = world.hero.label
    facts = world.facts
    return [
        QAItem(
            question=f"What was the twist about {world.rival.label}?",
            answer=f"The twist was that {facts['twist']}.",
        ),
        QAItem(
            question="Why did the danger begin?",
            answer=f"The danger began because {facts['cause']}.",
        ),
        QAItem(
            question=f"How did {hero} remove the bacon and stop the danger?",
            answer=f"{facts['removal']}.",
        ),
        QAItem(
            question="How were the two characters reconciled?",
            answer=f"{facts['reconciliation']}.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is bacon?",
            answer="Bacon is meat, usually from pork, that is often cured and cooked until crisp or chewy.",
        ),
        QAItem(
            question="What does it mean to remove something?",
            answer="To remove something means to take it away from a place or situation.",
        ),
        QAItem(
            question="What is a twist in a story?",
            answer="A twist is a surprising change in what the audience believes is happening.",
        ),
        QAItem(
            question="What is reconciliation?",
            answer="Reconciliation is the process of repairing a disagreement and becoming friendly or peaceful again.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    return [
        "Write a child-friendly superhero story involving bacon and a brave removal.",
        f"Tell a superhero adventure for {world.hero.label} at {world.place}, with a surprising twist.",
        "Write a story in which two rivals reconcile after learning the truth.",
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in [world.hero, world.rival, world.bacon]:
        lines.append(
            f"  {entity.id:6} {entity.kind:10} label={entity.label!r} "
            f"owner={entity.owner!r} meters={entity.meters} memes={entity.memes}"
        )
    lines.append(f"  place={world.place!r}")
    lines.append(f"  facts={world.facts}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    output = ["== Generation prompts =="]
    output.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    output.append("")
    output.append("== Story QA ==")
    for item in sample.story_qa:
        output.append(f"Q: {item.question}")
        output.append(f"A: {item.answer}")
    output.append("")
    output.append("== World QA ==")
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
        print(asp_program("#show brave/1.\n#show rescued/1.\n#show reconciled/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(
            "3 compatible logical atoms: brave(hero), rescued(hero), reconciled(hero)"
        )
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams(
                name="Luna",
                rival_name="Captain Crumb",
                place="the rooftop breakfast lab",
                seed=101,
            ),
            StoryParams(
                name="Maya",
                rival_name="Dr. Sizzle",
                place="the bright city square",
                seed=202,
            ),
            StoryParams(
                name="Nova",
                rival_name="The Grease Goblin",
                place="the pancake tower",
                seed=303,
            ),
            StoryParams(
                name="Zara",
                rival_name="Baron Butter",
                place="the superhero clubhouse",
                seed=404,
            ),
        ]
        samples = [generate(params) for params in curated]
    else:
        seen: set[str] = set()
        index = 0
        limit = max(50, args.n * 20)
        while len(samples) < args.n and index < limit:
            params = resolve_params(args, random.Random(base_seed + index))
            params.seed = base_seed + index
            sample = generate(params)
            index += 1
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if not samples:
        raise StoryError("No stories could be generated.")

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        header = ""
        if args.all:
            params = sample.params
            header = f"### {params.name} at {params.place}"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
