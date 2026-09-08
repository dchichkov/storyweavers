#!/usr/bin/env python3
"""
Storyworld: only_sharing_space_adventure

A small space-adventure world about learning that sharing a limited space
makes room for everyone.
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
class Astronaut:
    id: str
    name: str
    role: str
    home: str
    meters: dict[str, float] = field(
        default_factory=lambda: {"space": 1.0, "supply": 0.0, "cooperation": 0.0}
    )
    memes: dict[str, float] = field(
        default_factory=lambda: {"greed": 0.0, "trust": 0.0, "relief": 0.0, "pride": 0.0}
    )


@dataclass
class Thing:
    id: str
    label: str
    kind: str
    owner: str = ""
    meters: dict[str, float] = field(
        default_factory=lambda: {"space": 0.0, "supply": 0.0, "shared": 0.0}
    )


@dataclass
class StoryParams:
    hero_name: str
    friend_name: str
    captain_name: str
    station: str
    cabin: str
    treasure: str
    shared_tool: str
    mission: str
    telling_mode: str = "arrival"
    seed: Optional[int] = None


STATIONS = {
    "Luna Station": {
        "cabins": ["moon-view cabin", "small repair cabin"],
        "treasures": ["a silver moon map", "a glowing moon pebble"],
        "tools": ["a star scanner", "a moon-wrench"],
        "missions": [
            "find a safe path through the shadowed crater",
            "repair the beacon before the lunar night",
            "carry samples from a quiet ridge",
        ],
    },
    "Comet Harbor": {
        "cabins": ["tail-watch cabin", "icy storage cabin"],
        "treasures": ["a blue comet crystal", "a jar of sparkling ice dust"],
        "tools": ["a comet compass", "a warm cable reel"],
        "missions": [
            "guide a small shuttle through the comet tail",
            "keep the harbor lights shining",
            "collect a sample before the comet turns away",
        ],
    },
    "Orion Outpost": {
        "cabins": ["windowed scout cabin", "red-sand cabin"],
        "treasures": ["a red planet feather", "a tiny meteor shell"],
        "tools": ["a signal mirror", "a rover key"],
        "missions": [
            "send a signal across the silent valley",
            "map a safe route beyond the landing pad",
            "bring medicine to the rover crew",
        ],
    },
}

HERO_NAMES = ["Luna", "Mara", "Niko", "Pia", "Sol"]
FRIEND_NAMES = ["Tavi", "Rin", "Kiko", "Uma", "Jori"]
CAPTAIN_NAMES = ["Captain Vega", "Captain Noor", "Captain Aria", "Captain Finn"]

TELLING_MODES = (
    "arrival",
    "dialogue",
    "alarm",
    "quiet",
    "countdown",
    "window",
)

SHARING_BEATS = (
    '"There is only one safe space here," {hero} said. "Then we must make room by sharing it," answered {friend}.',
    "{captain} asked them to count what they had, what they needed, and what another traveler could use. The list made the cramped cabin seem easier to understand.",
    "{hero} looked at the narrow shelf and imagined keeping every item alone. Then {hero} noticed the empty hands of the waiting crew.",
    "The cabin was too small for two private piles, but it was large enough for one careful shared station.",
    '"Only one of us can hold the tool at a time," {friend} explained. "That does not mean only one of us can benefit from it."',
    "{hero} drew a line down the supply board, then erased it. A schedule would work better than a wall.",
)

CLOSING_EXCHANGES = (
    '"Only sharing made enough room," {hero} said. {friend} smiled and handed over the next turn.',
    '"Your turn now," said {friend}. "Our mission," replied {hero}.',
    "{captain} thanked both travelers for making a shared plan instead of guarding separate piles.",
    '"I thought sharing meant losing," {hero} admitted. "It meant helping everyone continue," said {friend}.',
)


class World:
    def __init__(self, params: StoryParams) -> None:
        self.params = params
        self.astronauts: dict[str, Astronaut] = {}
        self.things: dict[str, Thing] = {}
        self.lines: list[str] = []
        self.facts: dict[str, object] = {}

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def para(self) -> None:
        if self.lines and self.lines[-1] != "":
            self.lines.append("")

    def render(self) -> str:
        paragraphs: list[str] = []
        current: list[str] = []
        for line in self.lines:
            if line == "":
                if current:
                    paragraphs.append(" ".join(current))
                    current = []
            else:
                current.append(line)
        if current:
            paragraphs.append(" ".join(current))
        return "\n\n".join(paragraphs)


def build_world(params: StoryParams) -> World:
    if params.station not in STATIONS:
        raise StoryError(f"Unknown station: {params.station}")
    if not params.hero_name or not params.friend_name:
        raise StoryError("Astronaut names cannot be empty.")
    if params.hero_name == params.friend_name:
        raise StoryError("The two astronauts need different names.")

    world = World(params)
    hero = Astronaut("hero", params.hero_name, "young explorer", params.station)
    friend = Astronaut("friend", params.friend_name, "mission helper", params.station)
    captain = Astronaut("captain", params.captain_name, "captain", params.station)
    treasure = Thing("treasure", params.treasure, "mission sample", owner="mission")
    tool = Thing("tool", params.shared_tool, "shared equipment", owner="station")
    cabin = Thing("cabin", params.cabin, "small spacecraft room", owner="crew")

    world.astronauts.update(hero=hero, friend=friend, captain=captain)
    world.things.update(treasure=treasure, tool=tool, cabin=cabin)

    openings = {
        "arrival": (
            f"When {hero.name} arrived at {params.station}, the {params.cabin} was already "
            f"holding {params.treasure} and {params.shared_tool}."
        ),
        "dialogue": (
            f'"I found the {params.treasure}," said {hero.name}, stepping into the '
            f"{params.cabin} at {params.station}."
        ),
        "alarm": (
            f"The station alarm blinked just as {hero.name} entered the {params.cabin} "
            f"with the {params.treasure}."
        ),
        "quiet": (
            f"In the quiet orbit above the stars, {hero.name} discovered that the "
            f"{params.cabin} held a {params.treasure} and one {params.shared_tool}."
        ),
        "countdown": (
            f"With only a short time before the mission began, {hero.name} carried the "
            f"{params.treasure} into the {params.cabin}."
        ),
        "window": (
            f"Through the round window of the {params.cabin}, {hero.name} saw the stars "
            f"and the single {params.shared_tool} waiting beside the {params.treasure}."
        ),
    }

    world.say(openings[params.telling_mode])
    world.say(
        f"The cabin was built for careful teamwork, but it had room for only one open "
        f"worktable, one storage shelf, and one traveler moving at a time."
    )
    world.say(
        f"{hero.name} quickly placed the {params.treasure} and the {params.shared_tool} "
        f"on the best spots, leaving {friend.name} nowhere to prepare for the mission to "
        f"{params.mission}."
    )
    hero.meters["space"] += 1.0
    hero.memes["greed"] += 1.0
    world.para()

    world.say(
        f'{friend.name} floated at the doorway and asked, "May I use the table when you are done?"'
    )
    world.say(
        f'"There is only one table," {hero.name} replied. "I need it for everything."'
    )
    world.say(
        f'{captain.name} entered and pointed to the crowded shelf. "Only one of each item is available, '
        f'but this mission belongs to the whole crew."'
    )
    beat_rng = random.Random((params.seed or 0) ^ 0x51A2E)
    world.say(
        beat_rng.choice(SHARING_BEATS).format(
            hero=hero.name,
            friend=friend.name,
            captain=captain.name,
        )
    )
    hero.memes["worry"] = hero.memes.get("worry", 0.0) + 1.0
    friend.memes["trust"] += 1.0
    world.para()

    world.say(
        f"{hero.name} studied the tight cabin again. The answer was not to hide the "
        f"{params.treasure} or keep the {params.shared_tool}; it was to share the space "
        f"with a clear order."
    )
    world.say(
        f"{hero.name} moved the {params.treasure} into its padded case, clipped the "
        f"{params.shared_tool} to the wall, and made a simple turn list."
    )
    world.say(
        f'"You may use the table first for the signal check," {hero.name} told {friend.name}. '
        f'"Then I will record the results, and we can return the tool to its hook."'
    )
    world.say(
        f'"That gives both of us a place," {friend.name} said. "And it keeps the mission moving."'
    )
    hero.meters["cooperation"] += 1.0
    friend.meters["cooperation"] += 1.0
    tool.meters["shared"] += 1.0
    treasure.meters["shared"] += 1.0
    hero.memes["greed"] = 0.0
    hero.memes["trust"] += 1.0
    world.para()

    world.say(
        f"The shared plan worked. {friend.name} used the table to prepare the first part "
        f"of the mission, then {hero.name} used the same space to guide the next step."
    )
    world.say(
        f"Together they completed the mission to {params.mission}, while the {params.treasure} "
        f"stayed protected and the {params.shared_tool} returned to its wall hook."
    )
    hero.memes["relief"] += 1.0
    friend.memes["relief"] += 1.0
    captain.memes["pride"] += 1.0
    world.say(
        f"{beat_rng.choice(CLOSING_EXCHANGES).format(hero=hero.name, friend=friend.name, captain=captain.name)}"
    )
    world.say(
        f"Outside the round window, the station lights glowed in a neat circle, showing "
        f"that even a small space could welcome everyone when no one tried to own it alone."
    )

    world.facts.update(
        hero=hero,
        friend=friend,
        captain=captain,
        treasure=treasure,
        tool=tool,
        cabin=cabin,
        mission=params.mission,
        station=params.station,
        selfish_action=f"placed the {params.treasure} and the {params.shared_tool} on the best spots",
        problem="the cabin had one table and one shared tool for several crew members",
        clue="the table could serve everyone if they used it in turns",
        safer_action="made a turn list, stored the sample safely, and returned the tool after each use",
        result=f"both astronauts used the same table and tool to complete the mission to {params.mission}",
        lesson="sharing a limited space helps everyone do useful work",
        ending="the station lights glowed in a neat circle outside the round window",
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Astronaut = f["hero"]
    friend: Astronaut = f["friend"]
    return [
        f"Write a space adventure about {hero.name} learning to share a small cabin with {friend.name}.",
        f"Tell a story in which there is only one table and one {f['tool'].label}, but two astronauts must complete a mission.",
        f"Write a child-friendly adventure showing that {f['lesson']}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Astronaut = f["hero"]
    friend: Astronaut = f["friend"]
    tool: Thing = f["tool"]
    treasure: Thing = f["treasure"]
    return [
        QAItem(
            question=f"What did {hero.name} do at first with the {treasure.label} and the {tool.label}?",
            answer=(
                f"{hero.name} placed the {treasure.label} and the {tool.label} on the best spots, "
                f"leaving {friend.name} nowhere to prepare. The small cabin became difficult to use."
            ),
        ),
        QAItem(
            question=f"What did {hero.name} discover about the limited space?",
            answer=(
                f"{hero.name} discovered that {f['clue']}. The space was not enough for two private "
                f"work areas, but it was enough for a shared schedule."
            ),
        ),
        QAItem(
            question=f"How did {hero.name} and {friend.name} share the cabin?",
            answer=(
                f"They {f['safer_action']}. Each astronaut received a turn, so both could help with "
                f"the mission without crowding the other."
            ),
        ),
        QAItem(
            question="What happened after the astronauts shared?",
            answer=(
                f"They succeeded because {f['result']}. The tool was returned to its hook and the "
                f"mission supplies stayed safe."
            ),
        ),
        QAItem(
            question="What final image shows that sharing changed the station?",
            answer=(
                f"The final image is that {f['ending']}. It shows the small station becoming welcoming "
                f"through cooperation."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does sharing mean?",
            answer="Sharing means allowing other people to use, enjoy, or help with something instead of keeping it only for yourself.",
        ),
        QAItem(
            question="Why can a schedule help people share a small space?",
            answer="A schedule gives each person a clear turn, so people can use the same space without pushing or blocking one another.",
        ),
        QAItem(
            question="What is a space station?",
            answer="A space station is a spacecraft where astronauts can live, work, and study while orbiting a planet or moon.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== Story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for astronaut in world.astronauts.values():
        lines.append(
            f"{astronaut.id}: name={astronaut.name} role={astronaut.role} "
            f"meters={dict(astronaut.meters)} memes={dict(astronaut.memes)}"
        )
    for thing in world.things.values():
        lines.append(
            f"{thing.id}: label={thing.label} kind={thing.kind} "
            f"owner={thing.owner} meters={dict(thing.meters)}"
        )
    return "\n".join(lines)


ASP_RULES = r"""
sharing_adventure(S) :- story(S), only_one_space(S), shared_plan(S), mission_complete(S).
only_one_space(S) :- story(S), limited_cabin(S).
shared_plan(S) :- story(S), takes_turns(S), shared_tool(S).
mission_complete(S) :- story(S), cooperation(S).
"""


def asp_facts(params: StoryParams) -> str:
    import asp

    return "\n".join(
        [
            asp.fact("story", "s1"),
            asp.fact("limited_cabin", "s1"),
            asp.fact("only_one_space", "s1"),
            asp.fact("shared_tool", "s1"),
            asp.fact("takes_turns", "s1"),
            asp.fact("shared_plan", "s1"),
            asp.fact("cooperation", "s1"),
            asp.fact("mission_complete", "s1"),
        ]
    )


def asp_program() -> str:
    params = StoryParams(
        hero_name="Luna",
        friend_name="Tavi",
        captain_name="Captain Vega",
        station="Luna Station",
        cabin="moon-view cabin",
        treasure="a silver moon map",
        shared_tool="a star scanner",
        mission="find a safe path through the shadowed crater",
    )
    return f"{asp_facts(params)}\n{ASP_RULES}\n#show sharing_adventure/1.\n"


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program())
    found = set(asp.atoms(model, "sharing_adventure"))
    if found != {("s1",)}:
        print("MISMATCH: ASP did not recognize the sharing adventure.")
        return 1

    params = StoryParams(
        hero_name="Luna",
        friend_name="Tavi",
        captain_name="Captain Vega",
        station="Luna Station",
        cabin="moon-view cabin",
        treasure="a silver moon map",
        shared_tool="a star scanner",
        mission="find a safe path through the shadowed crater",
        seed=17,
    )
    sample = generate(params)
    required = ("share", "mission", "turn")
    if not all(word in sample.story.lower() for word in required):
        print("MISMATCH: generated story does not exercise sharing.")
        return 1

    print("OK: ASP gate and generated-story sharing checks pass.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Space adventure world about sharing a limited cabin."
    )
    parser.add_argument("--hero-name")
    parser.add_argument("--friend-name")
    parser.add_argument("--captain-name")
    parser.add_argument("--station", choices=sorted(STATIONS))
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
    station = args.station or rng.choice(sorted(STATIONS))
    config = STATIONS[station]
    hero_name = args.hero_name or rng.choice(HERO_NAMES)
    friend_name = args.friend_name or rng.choice(
        [name for name in FRIEND_NAMES if name != hero_name]
    )
    captain_name = args.captain_name or rng.choice(CAPTAIN_NAMES)
    return StoryParams(
        hero_name=hero_name,
        friend_name=friend_name,
        captain_name=captain_name,
        station=station,
        cabin=rng.choice(config["cabins"]),
        treasure=rng.choice(config["treasures"]),
        shared_tool=rng.choice(config["tools"]),
        mission=rng.choice(config["missions"]),
        telling_mode=rng.choice(TELLING_MODES),
    )


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
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


CURATED = [
    StoryParams(
        hero_name="Luna",
        friend_name="Tavi",
        captain_name="Captain Vega",
        station="Luna Station",
        cabin="moon-view cabin",
        treasure="a silver moon map",
        shared_tool="a star scanner",
        mission="find a safe path through the shadowed crater",
        telling_mode="window",
    ),
    StoryParams(
        hero_name="Mara",
        friend_name="Rin",
        captain_name="Captain Noor",
        station="Comet Harbor",
        cabin="tail-watch cabin",
        treasure="a blue comet crystal",
        shared_tool="a comet compass",
        mission="guide a small shuttle through the comet tail",
        telling_mode="alarm",
    ),
    StoryParams(
        hero_name="Sol",
        friend_name="Uma",
        captain_name="Captain Aria",
        station="Orion Outpost",
        cabin="red-sand cabin",
        treasure="a red planet feather",
        shared_tool="a rover key",
        mission="bring medicine to the rover crew",
        telling_mode="quiet",
    ),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return

    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        import asp

        print(asp.one_model(asp_program()))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for index, params in enumerate(CURATED):
            params.seed = base_seed + index
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        index = 0
        while len(samples) < args.n and index < max(50, args.n * 20):
            rng = random.Random(base_seed + index)
            params = resolve_params(args, rng)
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
        header = f"### variant {index + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
