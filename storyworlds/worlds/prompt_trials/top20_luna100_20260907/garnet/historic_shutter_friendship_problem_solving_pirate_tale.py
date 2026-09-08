#!/usr/bin/env python3
"""
A small pirate tale about a historic shutter, loyal friends, and solving a
stormy problem together.
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
    place: str
    seed: int
    facts: dict = field(default_factory=dict)

    def render(self) -> str:
        return self.facts.get("story", "")


@dataclass
class StoryParams:
    captain_name: str
    friend_name: str
    port: str
    seed: Optional[int] = None


CAPTAINS = ["Luna", "Pip", "Mara", "Finn", "Tessa", "Cora", "Nico", "Bram"]
FRIENDS = ["Pip", "Nell", "Bo", "Rafi", "Suki", "Mina", "Jory", "Tobin"]
PORTS = [
    "the old harbor",
    "Whistlehook Bay",
    "the crooked lighthouse",
    "Brass Anchor Island",
    "the Moonlit Wharf",
]


ASP_RULES = r"""
#show brave/1.
#show historic/1.
#show repaired/1.
#show friends/2.

brave(C) :- faces_storm(C).
historic(S) :- marked_shutter(S).
repaired(S) :- solves_problem(S).
friends(C,F) :- shares_plan(C,F).
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("faces_storm", "captain"),
            asp.fact("marked_shutter", "shutter"),
            asp.fact("solves_problem", "shutter"),
            asp.fact("shares_plan", "captain", "friend"),
        ]
    )


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def _asp_atoms(symbols) -> set[tuple[str, tuple]]:
    import clingo
    result = set()
    for atom in symbols:
        values = []
        for arg in atom.arguments:
            if arg.type == clingo.SymbolType.Number:
                values.append(arg.number)
            elif arg.type == clingo.SymbolType.String:
                values.append(arg.string)
            else:
                values.append(arg.name)
        result.add((atom.name, tuple(values)))
    return result


def asp_verify() -> int:
    try:
        import asp
        model = asp.one_model(
            asp_program(
                "\n".join(
                    [
                        "#show brave/1.",
                        "#show historic/1.",
                        "#show repaired/1.",
                        "#show friends/2.",
                    ]
                )
            )
        )
    except ImportError:
        print("ASP verification requires clingo.")
        return 1
    expected = {
        ("brave", ("captain",)),
        ("historic", ("shutter",)),
        ("repaired", ("shutter",)),
        ("friends", ("captain", "friend")),
    }
    actual = _asp_atoms(model)
    if actual == expected:
        print("OK: ASP parity verified.")
        return 0
    print("MISMATCH between ASP and Python expectations.")
    print("ASP:", sorted(actual))
    print("PY :", sorted(expected))
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Pirate tale about a historic shutter and friendship."
    )
    parser.add_argument("--captain-name", choices=CAPTAINS)
    parser.add_argument("--friend-name", choices=FRIENDS)
    parser.add_argument("--port", choices=PORTS)
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
    captain = args.captain_name or rng.choice(CAPTAINS)
    friend = args.friend_name or rng.choice(
        [name for name in FRIENDS if name != captain] or FRIENDS
    )
    return StoryParams(
        captain_name=captain,
        friend_name=friend,
        port=args.port or rng.choice(PORTS),
    )


def build_world(params: StoryParams) -> World:
    if params.captain_name == params.friend_name:
        raise StoryError("The captain and friend must have different names.")
    captain = Item(
        id="captain",
        label=params.captain_name,
        phrase=f"Captain {params.captain_name}",
        kind="character",
        meters={"courage": 0.7, "energy": 0.8},
        memes={"trust": 0.8, "curiosity": 0.7},
    )
    friend = Item(
        id="friend",
        label=params.friend_name,
        phrase=params.friend_name,
        kind="character",
        meters={"courage": 0.65, "energy": 0.75},
        memes={"trust": 0.85, "cleverness": 0.9},
    )
    shutter = Item(
        id="shutter",
        label="historic shutter",
        phrase="the historic blue shutter from an old captain's house",
        kind="artifact",
        meters={"distance_to_window": 0.0, "storm_risk": 0.8},
        memes={"memory": 1.0, "importance": 0.9},
    )
    seed = params.seed
    if seed is None:
        seed = sum(ord(ch) for ch in f"{params.captain_name}|{params.friend_name}|{params.port}")
    return World(captain=captain, friend=friend, shutter=shutter, place=params.port, seed=seed)


def _choice(rng: random.Random, values: list[str]) -> str:
    return values[rng.randrange(len(values))]


def _record(
    world: World,
    *,
    arc: str,
    discovery: str,
    trouble: str,
    cause: str,
    plan: str,
    resolution: str,
    ending: str,
    lesson: str,
    lines: list[str],
) -> str:
    world.facts.update(
        arc=arc,
        discovery=discovery,
        trouble=trouble,
        cause=cause,
        plan=plan,
        resolution=resolution,
        ending=ending,
        lesson=lesson,
        historic=True,
        friendship=True,
        solved=True,
    )
    return " ".join(lines)


def _storm_arc(world: World, rng: random.Random) -> str:
    c, f, p = world.captain.label, world.friend.label, world.place
    rope = _choice(rng, ["a coil of red rope", "a fishing net", "three sailcloth ribbons"])
    discovery = "the historic shutter carried an old brass hook that fit the lighthouse bell"
    trouble = "a fast storm tore the harbor signal loose and left boats searching for the safe channel"
    cause = "the shutter's hook had been removed from the lighthouse years ago, so the warning bell could not be secured"
    plan = f"{c} and {f} tied the shutter to the bell rope with {rope}"
    resolution = f"Together, {c} and {f} used the shutter's hook to fasten the bell rope and rang a clear warning through the rain"
    ending = "the restored blue shutter stood beside the lighthouse bell while safe boats glided into harbor"
    lesson = "friends solve bigger problems when they share what each one notices"
    lines = [
        f"At {p}, Captain {c} and {f} found the historic blue shutter leaning against an abandoned lighthouse.",
        f"A brass plate on it read, \"From the first keeper, who guarded every sailor.\" Then the sky turned black, and a hard storm rushed toward the bay.",
        f"The harbor signal snapped loose. Boats bumped in the dark water, searching for the safe channel.",
        f'"We need a plan!" cried {c}. "We need two plans," said {f}. "You watch the boats, and I will watch the old things."',
        f"{f} spotted a brass hook on the shutter. {c} recognized its shape from the lighthouse bell, but the hook was too high to reach.",
        f'"I can climb," said {c}. "I can tie knots," said {f}. "Then we climb and tie together!"',
        f"With {rope}, {c} climbed the wet steps while {f} looped a careful knot below. They fastened the shutter's old hook to the bell rope.",
        f"The bell rang across the storm. Boats turned toward its brave sound and slipped safely between the rocks.",
        f"By morning, {ending}. The friends learned that a historic object could still help when careful hands gave it a new job.",
    ]
    world.shutter.meters["storm_risk"] = 0.1
    return _record(
        world,
        arc="storm",
        discovery=discovery,
        trouble=trouble,
        cause=cause,
        plan=plan,
        resolution=resolution,
        ending=ending,
        lesson=lesson,
        lines=lines,
    )


def _map_arc(world: World, rng: random.Random) -> str:
    c, f, p = world.captain.label, world.friend.label, world.place
    mark = _choice(rng, ["a silver crab", "a tiny moon", "a three-pointed star"])
    discovery = f"the historic shutter hid a faded map marked with {mark}"
    trouble = "the crew followed the map's old directions and became tangled among shifting sandbars"
    cause = "the shoreline had changed since the map was painted, but the map still showed the shutter's original window"
    plan = f"{f} compared the map with the tide while {c} watched the stars"
    resolution = f"{c} steered by the stars and {f} corrected the old map with a charcoal line"
    ending = "the shutter hung above the cabin door with the corrected map tucked safely behind it"
    lesson = "good problem solving means checking old clues against what is true now"
    lines = [
        f"Captain {c} and {f} were polishing a historic shutter aboard their little pirate ship near {p}.",
        f"Behind a loose hinge, they found a faded map marked with {mark}. A red X pointed toward a chest of cinnamon coins.",
        f'"Treasure!" shouted {c}. "Careful," said {f}. "This map may be old enough to have a beard."',
        f"They followed the first arrow, then the second, and soon the ship bumped into a sandbar. The tide tugged the boat sideways.",
        f"{c} studied the stars. {f} studied the water. Together they noticed that the shoreline no longer matched the painted map.",
        f'"The map remembers the past," said {f}. "The tide tells us about today," said {c}.',
        f"{f} marked a safer channel with charcoal while {c} steered by the stars. The ship slid free and reached the treasure cove.",
        f"They found the cinnamon coins beneath a stone shaped like a sleeping fish. Before sailing home, they tucked the corrected map behind the shutter.",
        f"At sunset, {ending}. The friends kept the treasure, but their better prize was learning how to listen to two clues at once.",
    ]
    world.shutter.meters["distance_to_window"] = 0.0
    return _record(
        world,
        arc="map",
        discovery=discovery,
        trouble=trouble,
        cause=cause,
        plan=plan,
        resolution=resolution,
        ending=ending,
        lesson=lesson,
        lines=lines,
    )


def _parrot_arc(world: World, rng: random.Random) -> str:
    c, f, p = world.captain.label, world.friend.label, world.place
    bird = _choice(rng, ["a green parrot", "a blue macaw", "a tiny talking gull"])
    discovery = f"the historic shutter made a perfect shelter for {bird}'s nest"
    trouble = f"{bird} repeated a false alarm until the whole crew raced to the wrong side of the ship"
    cause = "wind rattled the loose shutter, and the bird copied the sound as if it were the ship's emergency call"
    plan = f"{c} listened for the pattern while {f} held the shutter still"
    resolution = f"{c} and {f} secured the shutter with a soft sailcloth tie and taught {bird} a new signal"
    ending = f"the historic shutter rested quietly while {bird} called only when a real wave splashed the deck"
    lesson = "friends can solve confusion by listening carefully before rushing"
    lines = [
        f"Near {p}, Captain {c} and {f} rescued a historic shutter from a wrecked captain's house.",
        f"They carried it aboard, where {bird} tucked a nest into its corner. The shutter had faded blue paint and a brass moon.",
        f"CLACK! CLACK! The shutter rattled, and {bird} cried, \"Pirates overboard!\"",
        f"The crew rushed left. Nothing. Then the shutter rattled again, and everyone rushed right.",
        f'"The parrot is calling trouble," puffed {c}. "The shutter is making the call," said {f}.',
        f"{f} held the shutter still while {c} counted the sounds. The false alarm always came in pairs.",
        f"They tied the shutter gently with a soft sailcloth tie. Then they taught {bird} to call, \"Sailor safe!\" whenever the deck was calm.",
        f"A real wave splashed over the bow. {bird} cried, \"Sailor safe! Splash!\" Everyone laughed and pulled the sail tight.",
        f"That evening, {ending}. The ship grew peaceful because the friends had solved the mystery instead of blaming the noisy bird.",
    ]
    return _record(
        world,
        arc="parrot",
        discovery=discovery,
        trouble=trouble,
        cause=cause,
        plan=plan,
        resolution=resolution,
        ending=ending,
        lesson=lesson,
        lines=lines,
    )


def _fort_arc(world: World, rng: random.Random) -> str:
    c, f, p = world.captain.label, world.friend.label, world.place
    tool = _choice(rng, ["a wooden spoon", "a brass compass", "a rolled-up sail"])
    discovery = "the historic shutter was built from strong cedar and still had two sturdy hinges"
    trouble = "the crew's supply cart lost a wheel while carrying food toward the island fort"
    cause = "the cart needed a broad, flat support, and the shutter was the only strong board nearby"
    plan = f"{c} measured the cart while {f} searched for a safe way to brace it with {tool}"
    resolution = f"They used the shutter as a temporary cart side, secured the wheel, and carried the food to the fort"
    ending = "the historic shutter returned to the fort wall, where its old hinges shone in the morning sun"
    lesson = "a clever solution can respect the past while helping with a present problem"
    lines = [
        f"At {p}, Captain {c} and {f} found a historic shutter beside the island fort.",
        f"It was made of cedar, painted sea-blue, and carved with a tiny ship. The fort keeper said it had guarded the gate for a hundred years.",
        f"Suddenly the supply cart broke a wheel. Sacks of flour rolled toward the shore.",
        f'"Save the flour!" cried {c}. "And save the shutter," said {f}. "It belongs to the fort."',
        f"{c} measured the cart while {f} searched for a careful solution with {tool}. They saw that the shutter could brace the cart without being nailed or cut.",
        f"Together they slid the shutter against the cart, tied it with rope, and lifted the loose wheel back into place.",
        f"The flour reached the fort kitchen before supper. No nail pierced the old wood, and not one carved ship was scratched.",
        f"After the cart was repaired, they returned the shutter to the wall. {ending}.",
        f"{c} grinned. " + f'"A strong friend is like a strong board." {f} nodded. "Useful, careful, and never left behind."',
    ]
    return _record(
        world,
        arc="fort",
        discovery=discovery,
        trouble=trouble,
        cause=cause,
        plan=plan,
        resolution=resolution,
        ending=ending,
        lesson=lesson,
        lines=lines,
    )


ARC_BUILDERS = [_storm_arc, _map_arc, _parrot_arc, _fort_arc]


def generate_story(world: World) -> str:
    rng = random.Random(world.seed ^ 0x74A91C)
    builder = ARC_BUILDERS[world.seed % len(ARC_BUILDERS)]
    return builder(world, rng)


def story_qa(world: World) -> list[QAItem]:
    facts = world.facts
    c = world.captain.label
    return [
        QAItem(
            question=f"What did Captain {c} discover about the historic shutter?",
            answer=f"Captain {c} discovered that {facts['discovery']}.",
        ),
        QAItem(
            question="What problem did the friends face?",
            answer=f"They faced a problem because {facts['cause']}.",
        ),
        QAItem(
            question=f"How did the friends solve the problem?",
            answer=f"{facts['resolution']}.",
        ),
        QAItem(
            question="What did the story show about friendship?",
            answer=f"The story showed that {facts['lesson']}.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    common = [
        QAItem(
            question="What is a shutter?",
            answer="A shutter is a hinged cover that can close over a window or opening.",
        ),
        QAItem(
            question="Why can a historic object matter?",
            answer="A historic object can matter because it connects people with earlier lives, work, and memories.",
        ),
        QAItem(
            question="What is problem solving?",
            answer="Problem solving means understanding a difficulty, thinking of possible actions, and choosing a safe way to improve the situation.",
        ),
    ]
    arc_item = {
        "storm": QAItem(
            question="Why are harbor signals useful during a storm?",
            answer="Harbor signals help sailors find a safe route when rain, wind, and darkness make familiar landmarks hard to see.",
        ),
        "map": QAItem(
            question="Why should an old map be checked against the present landscape?",
            answer="Land and water can change, so an old map may need to be compared with current tides, paths, and landmarks.",
        ),
        "parrot": QAItem(
            question="Why might a loose wooden shutter make a repeated sound?",
            answer="Wind can push a loose shutter against its frame again and again, making a repeated clacking sound.",
        ),
        "fort": QAItem(
            question="Why should people protect historic wood?",
            answer="Historic wood can carry old marks and memories, so people should use it carefully and avoid damaging it.",
        ),
    }[world.facts["arc"]]
    return [common[0], arc_item, common[1]]


def generation_prompts(world: World) -> list[str]:
    return [
        "Write a pirate tale for young children about a historic shutter and loyal friends.",
        f"Tell a problem-solving adventure for Captain {world.captain.label} and {world.friend.label} near {world.place}.",
        "Write a warm, exciting story showing that friendship helps people use old clues in a new way.",
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in [world.captain, world.friend, world.shutter]:
        lines.append(
            f"  {entity.id:8} {entity.kind:10} label={entity.label!r} "
            f"owner={entity.owner!r} meters={entity.meters} memes={entity.memes}"
        )
    lines.append(f"  place={world.place!r}")
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
        print(
            asp_program(
                "\n".join(
                    [
                        "#show brave/1.",
                        "#show historic/1.",
                        "#show repaired/1.",
                        "#show friends/2.",
                    ]
                )
            )
        )
        return

    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        print(
            "4 compatible logical atoms: brave(captain), historic(shutter), "
            "repaired(shutter), friends(captain,friend)"
        )
        return

    if args.n < 1:
        raise StoryError("-n must be at least 1.")

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams("Luna", "Pip", "the old harbor"),
            StoryParams("Mara", "Nell", "Whistlehook Bay"),
            StoryParams("Finn", "Bo", "the crooked lighthouse"),
            StoryParams("Cora", "Mina", "Brass Anchor Island"),
        ]
        for index, params in enumerate(curated):
            params.seed = base_seed + index
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        index = 0
        while len(samples) < args.n and index < max(50, args.n * 20):
            params = resolve_params(args, random.Random(base_seed + index))
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        header = ""
        if args.all:
            header = f"### {sample.params.captain_name} at {sample.params.port}"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
