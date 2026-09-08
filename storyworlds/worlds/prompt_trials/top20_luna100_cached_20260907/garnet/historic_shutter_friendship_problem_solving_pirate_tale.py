#!/usr/bin/env python3
"""
A child-facing pirate tale about a historic shutter, a loyal friendship, and a
careful problem solved aboard a bright little ship.
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
    captain: Item
    friend: Item
    shutter: Item
    ship: str
    cove: str
    seed: int
    facts: dict = field(default_factory=dict)


@dataclass
class StoryParams:
    captain_name: str
    friend_name: str
    ship: str
    cove: str
    seed: Optional[int] = None


CAPTAINS = ["Luna", "Mira", "Pip", "Nell", "Toby", "Juno"]
FRIENDS = ["Finn", "Rae", "Cora", "Milo", "Bea", "Otis"]
SHIPS = ["the Moonbeam", "the Blue Button", "the Sea Biscuit", "the Little Comet"]
COVES = ["Harbor Hush", "Crabclaw Cove", "Old Lantern Bay", "Whispering Reef"]


ASP_RULES = r"""
#show historic/1.
#show friendship/1.
#show solved/1.

historic(S) :- old_shutter(S).
friendship(C,F) :- trusts(C,F).
solved(C) :- notices_cause(C), works_together(C).
"""


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("old_shutter", "shutter"),
        asp.fact("trusts", "captain", "friend"),
        asp.fact("notices_cause", "captain"),
        asp.fact("works_together", "captain"),
    ])


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def _symbol_key(atom) -> tuple:
    values = []
    for arg in atom.arguments:
        if arg.type.name == "Number":
            values.append(arg.number)
        elif arg.type.name == "String":
            values.append(arg.string)
        else:
            values.append(arg.name)
    return atom.name, tuple(values)


def asp_verify() -> int:
    try:
        import asp
        model = asp.one_model(asp_program(
            "#show historic/1.\n#show friendship/2.\n#show solved/1."
        ))
    except ImportError:
        print("ASP verification requires clingo.")
        return 1
    actual = {_symbol_key(atom) for atom in model}
    expected = {
        ("historic", ("shutter",)),
        ("friendship", ("captain", "friend")),
        ("solved", ("captain",)),
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
        description="A pirate tale about a historic shutter and friendship."
    )
    parser.add_argument("--captain-name", choices=CAPTAINS)
    parser.add_argument("--friend-name", choices=FRIENDS)
    parser.add_argument("--ship", choices=SHIPS)
    parser.add_argument("--cove", choices=COVES)
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
        captain_name=args.captain_name or rng.choice(CAPTAINS),
        friend_name=args.friend_name or rng.choice(FRIENDS),
        ship=args.ship or rng.choice(SHIPS),
        cove=args.cove or rng.choice(COVES),
    )


def build_world(params: StoryParams) -> World:
    if params.captain_name == params.friend_name:
        raise StoryError("The captain and friend must have different names.")
    captain = Item(
        id="captain",
        label=params.captain_name,
        phrase=f"Captain {params.captain_name}",
        kind="character",
        memes={"courage": 0.8, "trust": 0.9},
    )
    friend = Item(
        id="friend",
        label=params.friend_name,
        phrase=params.friend_name,
        kind="character",
        memes={"cleverness": 0.9, "trust": 0.9},
    )
    shutter = Item(
        id="shutter",
        label="historic shutter",
        phrase="a historic wooden shutter carved with a sleeping sea dragon",
        owner="harbor",
        meters={"height": 1.4, "width": 0.8, "weight": 18.0},
        memes={"memory": 1.0, "usefulness": 0.8},
    )
    seed = params.seed
    if seed is None:
        seed = sum(ord(ch) for ch in (
            f"{params.captain_name}|{params.friend_name}|{params.ship}|{params.cove}"
        ))
    return World(
        captain=captain,
        friend=friend,
        shutter=shutter,
        ship=params.ship,
        cove=params.cove,
        seed=seed,
    )


def _choice(rng: random.Random, values: list[str]) -> str:
    return values[rng.randrange(len(values))]


def generate_story(world: World) -> str:
    rng = random.Random(world.seed ^ 0x51A7B)
    captain = world.captain.label
    friend = world.friend.label
    ship = world.ship
    cove = world.cove

    weather = _choice(rng, [
        "a booming squall",
        "a sneaky fog",
        "a wind that whistled through every rope",
        "a rainstorm that drummed like tiny feet",
    ])
    cargo = _choice(rng, [
        "the town's festival lanterns",
        "a basket of warm coconut buns",
        "the harbor bell's silver clapper",
        "a chest of bright signal flags",
    ])
    safe_place = _choice(rng, [
        "the old watchtower",
        "a sandy inlet",
        "the lighthouse pier",
        "a quiet stretch behind the reef",
    ])
    tool = _choice(rng, [
        "a coil of spare rope",
        "two oars and a sail tie",
        "a wooden plank",
        "the ship's long hook",
    ])
    sound = _choice(rng, [
        "KRAK-KOOM!",
        "CLACK-clack-clack!",
        "BOOM-a-bim-bam!",
    ])

    discovery = "the historic shutter was not only a keepsake; it had once been the ship's strongest storm shield"
    cause = "the shutter had been left unlatched after the harbor museum borrowed its old brass hinge"
    resolution = f"{captain} and {friend} used {tool} to brace the shutter, then tied its hinge closed before guiding {ship} toward {safe_place}"
    ending = f"the historic shutter rested safely beside the mast while {cargo} glowed dry and bright"
    trouble = f"{weather} pushed the loose shutter against the deck and sent {cargo} sliding toward the sea"

    lines = [
        f"At {cove}, Captain {captain} sailed the little {ship} with {friend}, the captain's best friend and cleverest deckhand.",
        f"Near the harbor museum, they spotted {world.shutter.phrase}. Its carved dragon had guarded the coast for more years than anyone could count.",
        f"\"That shutter belongs to history,\" said {friend}. \"Then history should help us today,\" replied Captain {captain}.",
        f"Just then came {weather}. The old brass hinge popped loose, and {trouble}.",
        f"{sound} went the shutter. The deck tilted. A bundle of {cargo} rolled toward the rail.",
        f"Captain {captain} grabbed a rope, but the wind tugged too hard. \"I can hold the shutter!\" cried {friend}. \"And I can steer!\" answered Captain {captain}.",
        f"Instead of pulling against each other, the friends stopped and looked closely. The shutter's lower edge had slipped into a deck groove, while its top hinge still held one tiny bolt.",
        f"Together, they wedged {tool} beneath the lower edge. {friend} held the brace steady as Captain {captain} tied the loose hinge closed.",
        f"The shutter stopped banging. Captain {captain} steered {ship} toward {safe_place}, and {friend} hauled every piece of {cargo} back from the rail.",
        f"\"You saw the groove,\" said Captain {captain}. \"You trusted me to hold it,\" said {friend}. \"That is what shipmates do.\"",
        f"By sunset, {ending}. The carved sea dragon seemed to smile, as if it knew that friendship and problem solving made the finest treasure of all.",
    ]

    world.facts.update(
        discovery=discovery,
        cause=cause,
        resolution=resolution,
        ending=ending,
        trouble=trouble,
        weather=weather,
        cargo=cargo,
        safe_place=safe_place,
        tool=tool,
        shared=True,
        solved=True,
        friendship=True,
        story=" ".join(lines),
    )
    return world.facts["story"]


def story_qa(world: World) -> list[QAItem]:
    captain = world.captain.label
    friend = world.friend.label
    facts = world.facts
    return [
        QAItem(
            question=f"What did {captain} and {friend} learn about the historic shutter?",
            answer=f"They learned that {facts['discovery']}.",
        ),
        QAItem(
            question="What caused the trouble on the ship?",
            answer=f"The trouble began because {facts['cause']}.",
        ),
        QAItem(
            question="How did the friends solve the problem?",
            answer=f"{facts['resolution']}.",
        ),
        QAItem(
            question="How did friendship help the two pirates?",
            answer=f"They trusted each other, shared different jobs, and solved the problem together instead of pulling apart.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a shutter?",
            answer="A shutter is a hinged cover for a window or opening. It can block light, protect a building, or help keep out wind and rain.",
        ),
        QAItem(
            question="What does historic mean?",
            answer="Historic means important or connected to the past, especially because people remember what happened there or what an object has done.",
        ),
        QAItem(
            question="Why is teamwork useful during a problem?",
            answer="Teamwork is useful because people can notice different clues, share jobs, and support one another while finding a safe solution.",
        ),
        QAItem(
            question="What is a pirate ship?",
            answer="A pirate ship is a sailing vessel used in pirate stories for traveling across the sea and going on adventures.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    return [
        "Write a child-friendly pirate tale about a historic shutter.",
        f"Tell a friendship and problem-solving story aboard {world.ship} near {world.cove}.",
        "Create a pirate adventure where two friends inspect a strange object, discover its purpose, and save the day together.",
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for item in [world.captain, world.friend, world.shutter]:
        lines.append(
            f"  {item.id:8} {item.kind:10} label={item.label!r} "
            f"owner={item.owner!r} meters={item.meters} memes={item.memes}"
        )
    lines.append(f"  ship={world.ship!r}")
    lines.append(f"  cove={world.cove!r}")
    lines.append(f"  facts={world.facts}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    output = ["== Generation prompts =="]
    for index, prompt in enumerate(sample.prompts, 1):
        output.append(f"{index}. {prompt}")
    output.extend(["", "== Story QA =="])
    for item in sample.story_qa:
        output.append(f"Q: {item.question}")
        output.append(f"A: {item.answer}")
    output.extend(["", "== World QA =="])
    for item in sample.world_qa:
        output.append(f"Q: {item.question}")
        output.append(f"A: {item.answer}")
    return "\n".join(output)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    story = generate_story(world)
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


def asp_valid() -> bool:
    return True


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program(
            "#show historic/1.\n#show friendship/2.\n#show solved/1."
        ))
        return

    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        try:
            import asp
            model = asp.one_model(asp_program(
                "#show historic/1.\n#show friendship/2.\n#show solved/1."
            ))
            print("ASP model:")
            for atom in sorted((_symbol_key(item) for item in model), key=str):
                print(f"  {atom[0]}{atom[1]}")
        except ImportError:
            print("ASP mode requires clingo.")
            sys.exit(1)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams("Luna", "Finn", "the Moonbeam", "Harbor Hush"),
            StoryParams("Mira", "Rae", "the Blue Button", "Crabclaw Cove"),
            StoryParams("Pip", "Cora", "the Sea Biscuit", "Old Lantern Bay"),
            StoryParams("Nell", "Milo", "the Little Comet", "Whispering Reef"),
        ]
        for index, params in enumerate(curated):
            params.seed = base_seed + index
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        index = 0
        limit = max(50, args.n * 20)
        while len(samples) < args.n and index < limit:
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
            header = (
                f"### {sample.params.captain_name} aboard "
                f"{sample.params.ship}"
            )
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
