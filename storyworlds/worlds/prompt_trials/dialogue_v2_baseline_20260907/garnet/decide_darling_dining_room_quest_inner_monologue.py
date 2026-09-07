#!/usr/bin/env python3
"""
A heartwarming dining-room quest about a child who must decide what to do
with a garnet, while an inner monologue grows brave enough to ask for help.
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
from pathlib import Path as _StoryPath
_storyworlds_root = next(parent for parent in _StoryPath(__file__).resolve().parents
                        if (parent / 'results.py').is_file() and (parent / 'asp.py').is_file())
sys.path.insert(0, str(_storyworlds_root))
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
    darling: Item
    garnet: Item
    room: str
    seed: int
    facts: dict = field(default_factory=dict)

    def render(self) -> str:
        return self.facts.get("story", "")


@dataclass
class StoryParams:
    name: str
    darling_name: str
    room: str
    seed: Optional[int] = None


NAMES = ["Mara", "Theo", "Lila", "Jonah", "Nell", "Sam", "Iris", "Owen"]
DARLINGS = ["Darling", "Mama", "Papa", "Aunt June", "Grandma Rose"]
ROOMS = ["the dining room", "the sunny dining room", "the little dining room"]


ASP_RULES = r"""
#show quest/1.
#show worried/1.
#show shared/1.
#show decided/1.

quest(H) :- finds_garnet(H).
worried(H) :- hears_ticking(H).
shared(H) :- asks_for_help(H).
decided(H) :- makes_careful_choice(H).
"""


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("finds_garnet", "hero"),
        asp.fact("hears_ticking", "hero"),
        asp.fact("asks_for_help", "hero"),
        asp.fact("makes_careful_choice", "hero"),
    ])


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program(
        "#show quest/1.\n"
        "#show worried/1.\n"
        "#show shared/1.\n"
        "#show decided/1."
    ))
    atoms = set()
    for atom in model:
        args = []
        for value in atom.arguments:
            args.append(value.number if value.type.name == "Number" else value.name)
        atoms.add((atom.name, tuple(args)))
    expected = {
        ("quest", ("hero",)),
        ("worried", ("hero",)),
        ("shared", ("hero",)),
        ("decided", ("hero",)),
    }
    if atoms == expected:
        print("OK: ASP parity verified.")
        return 0
    print("MISMATCH between ASP and Python expectations.")
    print("ASP:", sorted(atoms))
    print("PY :", sorted(expected))
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Heartwarming garnet quest in a dining room."
    )
    parser.add_argument("--name", choices=NAMES)
    parser.add_argument("--darling-name", choices=DARLINGS)
    parser.add_argument("--room", choices=ROOMS)
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
    if args.n < 1:
        raise StoryError("-n must be at least 1.")
    return StoryParams(
        name=args.name or rng.choice(NAMES),
        darling_name=args.darling_name or rng.choice(DARLINGS),
        room=args.room or rng.choice(ROOMS),
    )


def build_world(params: StoryParams) -> World:
    if params.name == params.darling_name:
        raise StoryError("The child and the darling must have different names.")
    hero = Item(
        id="hero",
        label=params.name,
        phrase=params.name,
        kind="character",
        meters={"reach": 1.0, "distance_to_table": 0.6},
        memes={"curiosity": 0.8, "courage": 0.4, "worry": 0.3},
    )
    darling = Item(
        id="darling",
        label=params.darling_name,
        phrase=params.darling_name,
        kind="character",
        meters={"reach": 1.7, "distance_to_table": 0.2},
        memes={"warmth": 1.0, "patience": 0.9},
    )
    garnet = Item(
        id="garnet",
        label="garnet",
        phrase="a warm red garnet",
        owner="unknown",
        meters={"size": 0.04, "distance_to_table": 0.0},
        memes={"meaning": 0.8, "mystery": 0.9},
    )
    seed = params.seed
    if seed is None:
        seed = sum(ord(ch) for ch in f"{params.name}|{params.darling_name}|{params.room}")
    return World(
        hero=hero,
        darling=darling,
        garnet=garnet,
        room=params.room,
        seed=seed,
    )


def _choice(rng: random.Random, values: list[str]) -> str:
    return values[rng.randrange(len(values))]


def _record(
    world: World,
    *,
    discovery: str,
    suspense: str,
    cause: str,
    decision: str,
    resolution: str,
    ending: str,
    thought: str,
    lines: list[str],
) -> str:
    world.facts.update(
        discovery=discovery,
        suspense=suspense,
        cause=cause,
        decision=decision,
        resolution=resolution,
        ending=ending,
        thought=thought,
        quest=True,
        worried=True,
        shared=True,
        decided=True,
    )
    world.hero.memes["courage"] = 1.0
    world.hero.memes["worry"] = 0.1
    world.garnet.owner = world.darling.id
    return " ".join(lines)


def _build_story(world: World, rng: random.Random) -> str:
    h = world.hero.label
    d = world.darling.label
    room = world.room
    hiding_place = _choice(rng, [
        "beneath the folded napkin",
        "behind the salt cellar",
        "under the blue serving bowl",
        "beside the bread basket",
    ])
    sound = _choice(rng, [
        "a tiny tick",
        "a soft tap",
        "one careful click",
    ])
    keepsake = _choice(rng, [
        "a ribbon from an old birthday dress",
        "a brass button from a favorite coat",
        "a small blue bead from a family bracelet",
    ])
    thought = _choice(rng, [
        "If I hide it, nobody will know I found it. But if I ask, maybe the mystery will become a memory.",
        "A secret feels heavy when it sits alone. Perhaps a question can make it lighter.",
        "I want to keep the shining thing, but I want to do the right thing more.",
    ])
    discovery = f"{h} found the garnet {hiding_place}"
    suspense = f"the garnet made {sound} whenever the dining-room clock neared the same minute"
    cause = "the stone had slipped from a little keepsake box and was resting against the clock's wooden base"
    decision = f"{h} decided to ask {d} before touching or keeping the garnet"
    resolution = f"{d} recognized it as a family keepsake and invited {h} to place it safely beside {keepsake}"
    ending = f"the garnet rested in the keepsake box while {h} and {d} finished setting the table together"
    lines = [
        f"In {room}, {h} was helping set out spoons when a red glimmer winked from {hiding_place}.",
        f"{h} lifted the napkin and discovered {discovery.lower()}. It was round, warm-colored, and bright enough to make the soup bowls look as if they were smiling.",
        f"Then the garnet made {sound}. The clock had not moved, but the sound came again when its long hand reached twelve.",
        f"{h} held the stone close. Inside the child's thoughts, a small voice whispered, \"{thought}\"",
        f"The dining room grew very quiet. {h} imagined slipping the garnet into a pocket, then imagined {d} searching for it with a worried face.",
        f"At last {h} said, \"{d}, darling, I found something. I do not know what it is, and I do not want to decide alone.\"",
        f"{d} came close, and together they watched the clock hand tremble toward twelve. The garnet clicked once more against the wooden base.",
        f"{d} smiled with relief. \"You made a kind decision,\" {d} said. \"This belonged in our keepsake box. It fell out when we polished the table.\"",
        f"{h} placed the garnet in the box beside {keepsake}. The ticking stopped because the stone no longer touched the clock.",
        f"By the time supper was ready, {ending}. {h}'s question had turned a suspenseful secret into something the whole family could cherish.",
    ]
    return _record(
        world,
        discovery=discovery,
        suspense=suspense,
        cause=cause,
        decision=decision,
        resolution=resolution,
        ending=ending,
        thought=thought,
        lines=lines,
    )


def generate_story(world: World) -> str:
    rng = random.Random(world.seed ^ 0x4D3A21)
    return _build_story(world, rng)


def story_qa(world: World) -> list[QAItem]:
    h = world.hero.label
    d = world.darling.label
    facts = world.facts
    return [
        QAItem(
            question=f"What did {h} find in the dining room?",
            answer=f"{h} found that {facts['discovery']}.",
        ),
        QAItem(
            question="Why did the garnet seem suspenseful?",
            answer=f"It seemed suspenseful because {facts['suspense']}.",
        ),
        QAItem(
            question=f"What did {h} decide to do?",
            answer=f"{h} decided to ask {d} before touching or keeping the garnet.",
        ),
        QAItem(
            question="How did the problem end?",
            answer=f"{facts['resolution']}.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a garnet?",
            answer="A garnet is a hard gemstone that can be red, brown, or another deep color. It may shine when light reaches its surface.",
        ),
        QAItem(
            question="What is an inner monologue?",
            answer="An inner monologue is the private stream of thoughts a character has inside their mind.",
        ),
        QAItem(
            question="Why is asking before keeping a found object thoughtful?",
            answer="Asking gives the owner a chance to identify the object and helps the finder make a fair, caring choice.",
        ),
        QAItem(
            question="What creates suspense in a story?",
            answer="Suspense grows when a character faces uncertainty or a possible problem and the reader wants to know what will happen next.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    return [
        "Write a heartwarming story about a child who must decide what to do with a garnet.",
        f"Set a gentle quest in {world.room}, using suspense and an inner monologue.",
        "Include the words decide and darling in a story about honesty, courage, and family.",
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in [world.hero, world.darling, world.garnet]:
        lines.append(
            f"  {entity.id:8} {entity.kind:10} label={entity.label!r} "
            f"owner={entity.owner!r} meters={entity.meters} memes={entity.memes}"
        )
    lines.append(f"  room={world.room!r}")
    lines.append(f"  facts={world.facts}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== Generation prompts =="]
    for index, prompt in enumerate(sample.prompts, 1):
        out.append(f"{index}. {prompt}")
    out.extend(["", "== Story QA =="])
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.extend(["", "== World QA =="])
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


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
        print(asp_program(
            "#show quest/1.\n"
            "#show worried/1.\n"
            "#show shared/1.\n"
            "#show decided/1."
        ))
        return

    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        import asp
        model = asp.one_model(asp_program(
            "#show quest/1.\n"
            "#show worried/1.\n"
            "#show shared/1.\n"
            "#show decided/1."
        ))
        print("ASP model:", ", ".join(str(atom) for atom in model))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams(
                name="Mara",
                darling_name="Darling",
                room="the dining room",
                seed=base_seed,
            ),
            StoryParams(
                name="Theo",
                darling_name="Grandma Rose",
                room="the sunny dining room",
                seed=base_seed + 1,
            ),
            StoryParams(
                name="Lila",
                darling_name="Mama",
                room="the little dining room",
                seed=base_seed + 2,
            ),
            StoryParams(
                name="Owen",
                darling_name="Aunt June",
                room="the dining room",
                seed=base_seed + 3,
            ),
        ]
        samples = [generate(params) for params in curated]
    else:
        seen: set[str] = set()
        index = 0
        while len(samples) < args.n and index < max(50, args.n * 20):
            rng = random.Random(base_seed + index)
            params = resolve_params(args, rng)
            params.seed = base_seed + index
            sample = generate(params)
            index += 1
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps(
                [sample.to_dict() for sample in samples],
                indent=2,
                ensure_ascii=False,
            ))
        return

    for index, sample in enumerate(samples):
        header = ""
        if args.all:
            params = sample.params
            header = f"### {params.name} in {params.room}"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
