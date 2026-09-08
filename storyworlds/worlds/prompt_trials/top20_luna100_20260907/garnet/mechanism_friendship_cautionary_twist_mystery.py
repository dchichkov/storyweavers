#!/usr/bin/env python3
"""
A small mystery storyworld about a friendship, a strange mechanism, and the
cautionary twist that comes from opening a locked clockwork box too quickly.
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
    hero: Item
    friend: Item
    mechanism: Item
    place: str
    seed: int
    facts: dict = field(default_factory=dict)

    def render(self) -> str:
        return self.facts.get("story", "")


@dataclass
class StoryParams:
    name: str
    friend_name: str
    place: str
    seed: Optional[int] = None


NAMES = ["Luna", "Milo", "Nia", "Tess", "Owen", "Ivy", "Pip", "Mara"]
FRIENDS = ["Rowan", "Bea", "Jules", "Finn", "Suki", "Theo", "Ada", "Max"]
PLACES = [
    "the old clock tower",
    "the foggy museum",
    "the shuttered train station",
    "the moonlit harbor",
    "the attic above the bakery",
]


ASP_RULES = r"""
#show curious/1.
#show trusts/1.
#show cautious/1.
#show solved/1.

curious(H) :- finds_mechanism(H).
trusts(H,F) :- asks_friend(H,F).
cautious(H) :- reads_warning(H).
solved(H) :- uses_key(H), mechanism_safe.
mechanism_safe :- warning_present, friend_present.
"""


def asp_facts() -> str:
    import asp

    return "\n".join(
        [
            asp.fact("finds_mechanism", "hero"),
            asp.fact("asks_friend", "hero", "friend"),
            asp.fact("reads_warning", "hero"),
            asp.fact("uses_key", "hero"),
            asp.fact("warning_present"),
            asp.fact("friend_present"),
        ]
    )


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    shown = "\n".join(
        [
            "#show curious/1.",
            "#show trusts/2.",
            "#show cautious/1.",
            "#show solved/1.",
        ]
    )
    model = asp.one_model(asp_program(shown))
    actual = {
        (sym.name, tuple(
            arg.number if arg.type == arg.type.Number
            else arg.string if arg.type == arg.type.String
            else arg.name
            for arg in sym.arguments
        ))
        for sym in model
    }
    expected = {
        ("curious", ("hero",)),
        ("trusts", ("hero", "friend")),
        ("cautious", ("hero",)),
        ("solved", ("hero",)),
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
        description="Mystery storyworld about friendship and a hidden mechanism."
    )
    parser.add_argument("--name", choices=NAMES)
    parser.add_argument("--friend-name", choices=FRIENDS)
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
        friend_name=args.friend_name or rng.choice(FRIENDS),
        place=args.place or rng.choice(PLACES),
    )


def build_world(params: StoryParams) -> World:
    if params.name == params.friend_name:
        raise StoryError("The hero and friend must have different names.")
    hero = Item(
        id="hero",
        label=params.name,
        phrase=f"young {params.name}",
        kind="character",
        meters={"distance": 0.0, "risk": 0.0},
        memes={"curiosity": 0.8, "trust": 0.7},
    )
    friend = Item(
        id="friend",
        label=params.friend_name,
        phrase=params.friend_name,
        kind="character",
        meters={"distance": 0.0, "risk": 0.0},
        memes={"caution": 0.9, "trust": 0.8},
    )
    mechanism = Item(
        id="mechanism",
        label="brass moon mechanism",
        phrase="a palm-sized brass moon mechanism with three turning rings",
        kind="device",
        meters={"weight": 0.4, "risk": 0.6},
        memes={"mystery": 1.0, "friendship": 0.8},
    )
    seed = params.seed
    if seed is None:
        seed = sum(ord(ch) for ch in f"{params.name}|{params.friend_name}|{params.place}")
    return World(
        hero=hero,
        friend=friend,
        mechanism=mechanism,
        place=params.place,
        seed=seed,
    )


def _choice(rng: random.Random, values: list[str]) -> str:
    return values[rng.randrange(len(values))]


def _record(
    world: World,
    *,
    discovery: str,
    clue: str,
    danger: str,
    cause: str,
    resolution: str,
    twist: str,
    ending: str,
    refrain: str,
    lines: list[str],
) -> str:
    world.facts.update(
        discovery=discovery,
        clue=clue,
        danger=danger,
        cause=cause,
        resolution=resolution,
        twist=twist,
        ending=ending,
        refrain=refrain,
        friendship=True,
        cautionary=True,
    )
    world.hero.meters["risk"] = 0.2
    world.friend.meters["risk"] = 0.2
    return " ".join(lines)


def _bell_arc(world: World, rng: random.Random) -> str:
    h, f, p = world.hero.label, world.friend.label, world.place
    sound = _choice(rng, ["three soft chimes", "a silver click", "a whispering tick"])
    hiding_place = _choice(rng, ["behind a loose brick", "inside a dusty cabinet", "under a cracked floorboard"])
    discovery = f"the mechanism was hidden {hiding_place} and answered with {sound}"
    clue = "a line of fresh brass dust led from the floor to the moon-shaped rings"
    danger = "turning the rings in the wrong order would release the heavy clock bell above them"
    cause = "the mechanism was a safety lock for the tower bell, not a treasure box"
    resolution = f"{h} and {f} followed the brass dust, read the tiny warning, and turned the rings only after matching the bell marks"
    twist = "the mysterious box was protecting the town from an untimely bell, rather than hiding a prize"
    ending = "the bell gave one gentle note while the mechanism rested safely between its friends"
    refrain = "Look twice before you turn"
    lines = [
        f"At {p}, {h} and {f} found {discovery}.",
        f'"{sound}," said {h}. "Something inside is awake."',
        f'"Then we should wake our eyes first," {f} replied. "{refrain}."',
        f"{h} lifted one ring, but {f} noticed {clue}. The brass dust matched a warning scratched beneath the lid.",
        f"The warning explained that {danger}.",
        f"{h} wanted to twist the nearest ring. {f} placed a hand over it. \"A mystery is not worth hurting someone,\" {f} said.",
        f"Together they copied the marks, tested the order with a wooden pencil, and discovered that {cause}.",
        f"The lock opened with a sigh instead of a snap. {twist}.",
        f"They tied a bright ribbon around the safe handle and told the caretaker what they had found. By moonrise, {ending}.",
    ]
    return _record(
        world,
        discovery=discovery,
        clue=clue,
        danger=danger,
        cause=cause,
        resolution=resolution,
        twist=twist,
        ending=ending,
        refrain=refrain,
        lines=lines,
    )


def _lantern_arc(world: World, rng: random.Random) -> str:
    h, f, p = world.hero.label, world.friend.label, world.place
    shadow = _choice(rng, ["a long-fingered bird", "a crooked giant", "a dancing spider"])
    mark = _choice(rng, ["a crescent scratch", "two blue dots", "a tiny arrow"])
    discovery = f"the mechanism cast the shadow of {shadow} whenever its middle ring moved"
    clue = f"{mark} appeared on the wall only when the lantern was covered"
    danger = "the moving shadow could make visitors rush into the unstable gallery"
    cause = "a hidden shutter inside the mechanism was changing the lantern's shape"
    resolution = f"{h} and {f} covered the lantern, observed the {mark}, and slid the shutter closed instead of forcing the ring"
    twist = "the frightening figure was only a warning signal aimed at anyone who entered too quickly"
    ending = "the wall showed an ordinary little moon while the friends left a clear sign for the next visitor"
    refrain = "A shadow is a clue, not a command"
    lines = [
        f"Near {p}, {h} noticed {discovery}.",
        f"The shadow stretched across the wall, and {h} stepped back. \"It knows we are here!\"",
        f'"Or it wants us to notice something," {f} said. "{refrain}."',
        f"When they covered the lantern, {clue}. Behind a panel, they found a warning about the gallery floor.",
        f"{danger}, so {h} reached toward the ring and then stopped.",
        f"{f} pointed to the safer question: what changed when the light changed? They tested the lantern from a distance and saw the shadow move with the shutter.",
        f"Carefully, they used a long paintbrush to slide it closed. The shadow shrank, and {cause}.",
        f"{twist}. The friends marked the weak floor with chalk.",
        f"Outside, the fog lifted. By the doorway, {ending}.",
    ]
    return _record(
        world,
        discovery=discovery,
        clue=clue,
        danger=danger,
        cause=cause,
        resolution=resolution,
        twist=twist,
        ending=ending,
        refrain=refrain,
        lines=lines,
    )


def _harbor_arc(world: World, rng: random.Random) -> str:
    h, f, p = world.hero.label, world.friend.label, world.place
    object_name = _choice(rng, ["a toy boat", "a copper key", "a blue bottle"])
    discovery = f"the mechanism made {object_name} slide across a table whenever the tide bell rang"
    clue = "a wet trail stopped exactly beneath a loose wooden panel"
    danger = "opening the panel during high tide would let water rush into the lower room"
    cause = "the mechanism was connected to a tide gate under the building"
    resolution = f"{h} and {f} waited for low tide, followed the wet trail, and secured the gate with a rope before opening the panel"
    twist = "the moving object had not been a ghostly message; it had been pulled by the tide"
    ending = "the tide bell rang over a dry floor, and the little boat floated in a basin instead of across the room"
    refrain = "Wait for the water to tell"
    lines = [
        f"At {p}, {h} saw {discovery}.",
        f'"It moves by itself," whispered {h}.',
        f'"Then let us ask what moves it," said {f}. "{refrain}."',
        f"They watched the table and found {clue}. A note beside the panel warned that {danger}.",
        f"{h} reached for the latch, but {f} held up the rope. Friendship meant stopping together, not racing alone.",
        f"They returned when the tide dropped, measured the quiet gap, and tied the gate shut.",
        f"Behind the panel, they learned that {cause}.",
        f"{twist}. The mechanism was clever, but it had never been haunted.",
        f"After the caretaker repaired the seal, {ending}.",
    ]
    return _record(
        world,
        discovery=discovery,
        clue=clue,
        danger=danger,
        cause=cause,
        resolution=resolution,
        twist=twist,
        ending=ending,
        refrain=refrain,
        lines=lines,
    )


def _train_arc(world: World, rng: random.Random) -> str:
    h, f, p = world.hero.label, world.friend.label, world.place
    destination = _choice(rng, ["the baggage room", "the empty platform", "the signal shed"])
    discovery = f"the mechanism clicked toward {destination} each time a distant train whistle sounded"
    clue = "three red pins on its face matched the three lamps outside"
    danger = "pulling the silver lever could send a false signal to a passing train"
    cause = "the mechanism was an old signal tester left in place during repairs"
    resolution = f"{h} and {f} compared the pins with the lamps, placed a guard over the lever, and called the station keeper"
    twist = "the mysterious directions were not leading to a secret room; they were testing whether anyone was paying attention to the signals"
    ending = "the next train rolled safely past while the brass tester clicked only in the keeper's careful hands"
    refrain = "Mystery first, lever last"
    lines = [
        f"Inside {p}, {h} discovered that {discovery}.",
        f'"It points somewhere," said {h}.',
        f'"Maybe it is warning us not to follow yet," said {f}. "{refrain}."',
        f"They examined the face and found {clue}. Under the lever was a faded label explaining that {danger}.",
        f"{h} imagined a hidden treasure in {destination}, but {f} asked why the outside lamps mattered more than the pointed arrow.",
        f"That question changed the search. They matched the pins to the lamps, blocked the lever with a wooden crate, and called the station keeper.",
        f"The keeper explained that {cause}.",
        f"{twist}. The friends felt proud that their answer came from patience rather than a lucky guess.",
        f"When the whistle sounded again, {ending}.",
    ]
    return _record(
        world,
        discovery=discovery,
        clue=clue,
        danger=danger,
        cause=cause,
        resolution=resolution,
        twist=twist,
        ending=ending,
        refrain=refrain,
        lines=lines,
    )


ARC_BUILDERS = [_bell_arc, _lantern_arc, _harbor_arc, _train_arc]


def generate_story(world: World) -> str:
    rng = random.Random(world.seed ^ 0x4D454348)
    builder = ARC_BUILDERS[world.seed % len(ARC_BUILDERS)]
    return builder(world, rng)


def story_qa(world: World) -> list[QAItem]:
    h = world.hero.label
    f = world.friend.label
    facts = world.facts
    return [
        QAItem(
            question=f"What did {h} and {f} discover?",
            answer=f"{h} and {f} discovered that {facts['discovery']}.",
        ),
        QAItem(
            question="What clue helped solve the mystery?",
            answer=f"The important clue was that {facts['clue']}.",
        ),
        QAItem(
            question="Why did the friends act cautiously?",
            answer=f"They acted cautiously because {facts['danger']}.",
        ),
        QAItem(
            question="What was the twist?",
            answer=f"The twist was that {facts['twist']}.",
        ),
        QAItem(
            question=f"How did {h} and {f} solve the problem?",
            answer=f"They solved it when {facts['resolution']}.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a mechanism?",
            answer="A mechanism is a group of parts that work together to make something move, change, or perform a task.",
        ),
        QAItem(
            question="Why is caution useful around an unknown machine?",
            answer="Caution is useful because an unknown machine may move suddenly, contain stored energy, or control something dangerous.",
        ),
        QAItem(
            question="How can friendship help solve a mystery?",
            answer="Friends can notice different clues, question one another's guesses, and stop each other from taking an unsafe risk.",
        ),
        QAItem(
            question="What is a twist in a mystery story?",
            answer="A twist is a surprising change in understanding that makes earlier clues mean something new.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    return [
        "Write a child-friendly mystery about a strange mechanism and two friends.",
        f"Tell a cautious mystery set at {world.place}, where friendship helps reveal a surprising twist.",
        "Create a suspenseful but gentle story in which a clue explains how an unusual machine works.",
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for ent in [world.hero, world.friend, world.mechanism]:
        lines.append(
            f"  {ent.id:10} {ent.kind:10} label={ent.label!r} "
            f"owner={ent.owner!r} meters={ent.meters} memes={ent.memes}"
        )
    lines.append(f"  place={world.place!r}")
    for key in ["discovery", "clue", "danger", "cause", "twist", "ending"]:
        if key in world.facts:
            lines.append(f"  {key}={world.facts[key]!r}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== Generation prompts =="]
    for index, prompt in enumerate(sample.prompts, 1):
        out.append(f"{index}. {prompt}")
    out.append("")
    out.append("== Story QA ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== World QA ==")
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

    if args.n < 1:
        raise StoryError("-n must be at least 1.")

    if args.show_asp:
        print(
            asp_program(
                "\n".join(
                    [
                        "#show curious/1.",
                        "#show trusts/2.",
                        "#show cautious/1.",
                        "#show solved/1.",
                    ]
                )
            )
        )
        return

    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        import asp

        model = asp.one_model(
            asp_program(
                "\n".join(
                    [
                        "#show curious/1.",
                        "#show trusts/2.",
                        "#show cautious/1.",
                        "#show solved/1.",
                    ]
                )
            )
        )
        print(
            "ASP model:",
            ", ".join(str(atom) for atom in sorted(model, key=str)),
        )
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams(
                name="Luna",
                friend_name="Rowan",
                place="the old clock tower",
                seed=base_seed,
            ),
            StoryParams(
                name="Milo",
                friend_name="Bea",
                place="the foggy museum",
                seed=base_seed + 1,
            ),
            StoryParams(
                name="Nia",
                friend_name="Finn",
                place="the moonlit harbor",
                seed=base_seed + 2,
            ),
            StoryParams(
                name="Tess",
                friend_name="Ada",
                place="the shuttered train station",
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        header = ""
        if args.all:
            params = sample.params
            header = f"### {params.name} and {params.friend_name} at {params.place}"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
