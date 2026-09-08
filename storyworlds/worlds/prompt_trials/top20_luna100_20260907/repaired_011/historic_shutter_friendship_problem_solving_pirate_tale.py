#!/usr/bin/env python3
"""
A small stand-alone pirate tale about a historic shutter, friendship, and problem solving.
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
class StoryParams:
    child: str
    captain: str
    friend: str
    island: str
    shutter: str
    clue: str
    incident: int = 0
    premise: int = 0
    song: int = 0
    ending: int = 0
    seed: Optional[int] = None


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

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
        return "\n\n".join(" ".join(part) for part in self.paragraphs if part)


CHILDREN = ["Luna", "Milo", "Nia", "Tavi", "Pia", "Owen"]
CAPTAINS = ["Captain Mara", "Captain Flint", "Captain Coral", "Captain Juniper"]
FRIENDS = ["Bram", "Kit", "Pip", "Sable", "Tess", "Wren"]
ISLANDS = ["Bellflower Isle", "Moonwake Island", "Old Lantern Cay", "Seashell Key"]
SHUTTERS = ["the blue harbor shutter", "the carved lighthouse shutter", "the red fort shutter", "the gold museum shutter"]
CLUES = ["a brass compass mark", "a painted parrot", "three silver stars", "a tiny anchor"]


PREMISES = [
    "{child} sailed with {friend} to {island}, where {captain} guarded {shutter}, a historic wooden shutter saved from an old pirate harbor.",
    "At dawn, {child} and {friend} reached {island}. The island museum held {shutter}, and {captain} said its story had guided sailors for generations.",
    "A salty breeze carried {child} and {friend} past the docks of {island}. Their treasure was not gold, but a look at {shutter}, a historic piece of pirate history.",
    "{captain} invited {child} and {friend} aboard for a history hunt at {island}. The first clue pointed straight toward {shutter}.",
    "The tide was low when {child} and {friend} climbed the museum steps on {island}. Behind a velvet rope waited {shutter}, bright with old paint and sea marks.",
]

INCIDENTS = [
    {
        "lead": "{captain} opened the museum door and showed them a small map beside the shutter.",
        "trigger": "A gust blew the map through a crack, and the historic shutter swung shut with a heavy clack.",
        "risk": "The map was trapped behind the shutter, while the tide crept toward the museum steps.",
        "action": "{child} noticed a loose rope above the window. {friend} held the lantern while {child} tied the rope to the handle and pulled gently.",
        "resolution": "The shutter opened without a scratch, and the map slid safely into {friend}'s hands.",
        "cause": "a gust blew the map behind the closing shutter",
        "deed": "noticed the loose rope and used it to open the shutter carefully",
        "result": "the map was recovered without harming the historic shutter",
    },
    {
        "lead": "{friend} found a brass key tucked beneath the shutter's old hinge.",
        "trigger": "When {captain} turned it, the shutter jammed halfway and blocked the only bright window.",
        "risk": "The room grew dim, and nobody could see which keyhole matched the hidden treasure box.",
        "action": "{child} asked {friend} to hold the lantern high. Together they spotted salt crust in the hinge, and {captain} brushed it away with a soft feather.",
        "resolution": "The hinge loosened, the shutter opened, and the matching keyhole gleamed in the lantern light.",
        "cause": "salt crust jammed the old shutter hinge",
        "deed": "used the lantern and helped find the salt blocking the hinge",
        "result": "the hinge opened gently and revealed the correct keyhole",
    },
    {
        "lead": "{captain} told them that sailors once watched the sea through the shutter.",
        "trigger": "A small wave struck the pier, shaking the museum wall and making one shutter peg tumble toward the floor.",
        "risk": "Without the peg, the heavy historic shutter might fall from its frame.",
        "action": "{child} called, 'Stay back!' while {friend} slid a coil of soft rope beneath the shutter. {captain} replaced the peg.",
        "resolution": "The rope held the shutter steady until the captain secured it, and the old wood stood safely again.",
        "cause": "a wave shook a peg loose from the shutter frame",
        "deed": "warned everyone and helped support the shutter with soft rope",
        "result": "the captain secured the shutter before it could fall",
    },
    {
        "lead": "{child} discovered a painted parrot hidden beneath the shutter latch.",
        "trigger": "The parrot's beak pointed to a tiny gap, but the clue card slipped into that gap before anyone could read it.",
        "risk": "The card might drift into the dark wall, taking the next part of the history hunt with it.",
        "action": "{friend} listened for the card while {child} lowered a ribbon through the gap. 'I hear paper!' called {friend}.",
        "resolution": "The ribbon caught the card, and the friends pulled it out together without scraping the old wood.",
        "cause": "the clue card slipped into a gap beside the shutter",
        "deed": "lowered a ribbon while listening with a friend for the hidden card",
        "result": "the friends pulled out the clue without damaging the shutter",
    },
    {
        "lead": "{captain} asked the friends to count the shutter's carved waves.",
        "trigger": "Their counting stopped when a bright shell rolled under the shutter and wedged against its bottom.",
        "risk": "The shutter could not close for the night, and the shell might crack beneath its weight.",
        "action": "{child} used a flat piece of driftwood as a slide. {friend} whispered, 'Slow as a sleepy turtle,' and guided the shell away.",
        "resolution": "The shell rolled onto a cloth, and the shutter closed snugly for the evening.",
        "cause": "a shell wedged beneath the shutter",
        "deed": "made a driftwood slide and guided the shell away with a friend",
        "result": "the shell was protected and the shutter closed safely",
    },
]

SONGS = [
    "{friend} sang, 'Heave and think, don't let it sink!' {child} answered, 'Friends who plan can save the day!'",
    "'A pirate rushes,' said {captain}, 'but a clever crew checks twice.' {child} and {friend} answered together, 'Aye, we check twice!'",
    "{child} made up a sea rhyme: 'When old boards creak and sea winds blow, kind friends work gently, slow by slow.'",
    "{friend} tapped the rail and called, 'Who knows the way?' {child} replied, 'The crew that listens!' Even {captain} gave a proud salute.",
    "The friends chanted, 'One lantern, two hands, a careful plan!' The words helped everyone move calmly.",
]

ENDINGS = [
    "That evening, the historic shutter glowed in the sunset. {child} and {friend} stood beside it, proud that their friendship had protected a piece of the past.",
    "Before sailing home, {captain} gave each friend a paper captain's badge. The shutter rested safely behind them, ready to tell its story again.",
    "The tide turned silver below the museum. {child} drew the shutter in the ship's log and wrote, 'A good crew solves trouble together.'",
    "At supper, the crew toasted with apple juice. The old shutter was quiet, the clue was safe, and {child} and {friend} laughed like two parrots sharing one joke.",
    "Moonlight shone through the open shutter. It painted a bright path across the floor, showing that careful hands and loyal friends had changed a scare into a story.",
]


ASP_RULES = r"""
#show valid/3.
#show valid_story/5.

child_name(N) :- child(N).
captain_name(C) :- captain(C).
friend_name(F) :- friend(F).
island_name(I) :- island(I).
shutter_name(S) :- shutter(S).
clue_name(C) :- clue(C).
valid(N, F, S) :- child(N), friend(F), shutter(S).
valid_story(N, F, I, S, C) :- valid(N, F, S), island(I), clue(C).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for value in CHILDREN:
        lines.append(asp.fact("child", value))
    for value in CAPTAINS:
        lines.append(asp.fact("captain", value))
    for value in FRIENDS:
        lines.append(asp.fact("friend", value))
    for value in ISLANDS:
        lines.append(asp.fact("island", value))
    for value in SHUTTERS:
        lines.append(asp.fact("shutter", value))
    for value in CLUES:
        lines.append(asp.fact("clue", value))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A pirate tale about a historic shutter and friendship.")
    parser.add_argument("--child", choices=CHILDREN)
    parser.add_argument("--captain", choices=CAPTAINS)
    parser.add_argument("--friend", choices=FRIENDS)
    parser.add_argument("--island", choices=ISLANDS)
    parser.add_argument("--shutter", choices=SHUTTERS)
    parser.add_argument("--clue", choices=CLUES)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def valid_combos() -> list[tuple[str, str, str]]:
    return [(child, friend, shutter) for child in CHILDREN for friend in FRIENDS if child != friend for shutter in SHUTTERS]


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(asp.atoms(model, "valid"))


def asp_verify() -> int:
    python_count = len(valid_combos())
    clingo_count = len(asp_valid_combos())
    if python_count == clingo_count:
        print(f"OK: clingo gate matches valid_combos() ({python_count} combinations).")
        return 0
    print(f"MISMATCH: Python has {python_count}; clingo has {clingo_count}.")
    return 1


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.child and args.friend and args.child == args.friend:
        raise StoryError("A child cannot be their own friend; choose two different crew members.")
    child = args.child or rng.choice(CHILDREN)
    friends = [friend for friend in FRIENDS if friend != child]
    friend = args.friend or rng.choice(friends)
    return StoryParams(
        child=child,
        captain=args.captain or rng.choice(CAPTAINS),
        friend=friend,
        island=args.island or rng.choice(ISLANDS),
        shutter=args.shutter or rng.choice(SHUTTERS),
        clue=args.clue or rng.choice(CLUES),
        incident=rng.randrange(len(INCIDENTS)),
        premise=rng.randrange(len(PREMISES)),
        song=rng.randrange(len(SONGS)),
        ending=rng.randrange(len(ENDINGS)),
    )


def apply_seeded_structure(params: StoryParams, seed: int) -> None:
    params.incident = seed % len(INCIDENTS)
    params.premise = (seed // len(INCIDENTS)) % len(PREMISES)
    params.song = (seed // 3) % len(SONGS)
    params.ending = (seed // 5) % len(ENDINGS)


def generate(params: StoryParams) -> StorySample:
    values = {
        "child": params.child,
        "captain": params.captain,
        "friend": params.friend,
        "island": params.island,
        "shutter": params.shutter,
        "clue": params.clue,
    }
    incident = INCIDENTS[params.incident % len(INCIDENTS)]

    world = World()
    child = world.add(Entity(params.child, "character", params.child, memes={"curiosity": 0.0}))
    friend = world.add(Entity(params.friend, "character", params.friend, memes={"trust": 0.0}))
    captain = world.add(Entity(params.captain, "character", params.captain))
    shutter = world.add(Entity("historic_shutter", "artifact", params.shutter, meters={"stability": 1.0}, memes={"history": 1.0}))
    clue = world.add(Entity("clue", "artifact", params.clue, memes={"importance": 1.0}))

    world.say(PREMISES[params.premise % len(PREMISES)].format(**values))
    world.say(f"The salt wind smelled of rope and rain, and {captain.label} warned them to touch the historic wood only with care.")
    world.say(incident["lead"].format(**values))

    world.para()
    shutter.meters["stability"] = 0.5
    child.memes["curiosity"] = 1.0
    friend.memes["trust"] = 1.0
    world.say(incident["trigger"].format(**values))
    world.say(incident["risk"].format(**values))
    world.say(f"'{incident['deed'].capitalize()}!' cried {child.label}. '{incident['deed'].capitalize()},' agreed {friend.label}, and the two friends worked side by side.")
    world.say(incident["action"].format(**values))

    world.para()
    shutter.meters["stability"] = 1.0
    child.memes["courage"] = 1.0
    friend.memes["joy"] = 1.0
    world.facts.update(
        child=params.child,
        friend=params.friend,
        captain=params.captain,
        island=params.island,
        shutter=params.shutter,
        clue=params.clue,
        cause=incident["cause"],
        action=incident["deed"],
        result=incident["result"],
        friendship=True,
        resolved=True,
    )
    world.say(incident["resolution"].format(**values))
    world.say(SONGS[params.song % len(SONGS)].format(**values))
    world.say(ENDINGS[params.ending % len(ENDINGS)].format(**values))

    prompts = [
        "Write a child-friendly pirate tale about a historic shutter, friendship, and problem solving.",
        f"Tell a pirate adventure in which {params.child} and {params.friend} protect {params.shutter} with a careful plan.",
        f"Write a story about {params.child}, {params.friend}, and {params.captain} solving a problem at {params.island}.",
    ]
    story_qa = [
        QAItem("Who worked together in the tale?", f"{params.child} and {params.friend} worked together as a friendly pirate crew, with help from {params.captain}."),
        QAItem("What caused the trouble?", f"The trouble began because {incident['cause']}."),
        QAItem(f"How did {params.child} and {params.friend} solve it?", f"They {incident['deed']}, which let the crew solve the problem carefully."),
        QAItem("What happened to the historic shutter?", f"{incident['result']}. The historic shutter remained safe and ready to share its history."),
        QAItem("What did the friends learn?", f"They learned that listening, planning, and helping one another can solve a frightening problem."),
    ]
    world_qa = [
        QAItem("What is a shutter?", "A shutter is a movable cover for a window or opening."),
        QAItem("What does historic mean?", "Historic means important in history or connected to the past."),
        QAItem("Why should an old object be handled gently?", "An old object may be fragile and may carry clues about people who lived long ago."),
        QAItem("What is problem solving?", "Problem solving means noticing a difficulty, thinking of possible choices, and trying a safe helpful plan."),
        QAItem("How does friendship help during trouble?", "Friendship helps because people can listen, share ideas, and support one another."),
    ]
    return StorySample(params=params, story=world.render(), prompts=prompts, story_qa=story_qa, world_qa=world_qa, world=world)


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
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
    for entity in world.entities.values():
        lines.append(f"  {entity.id:16} ({entity.kind:9}) meters={entity.meters} memes={entity.memes}")
    lines.append(f"  facts={world.facts}")
    return "\n".join(lines)


def build_curated() -> list[StoryParams]:
    return [
        StoryParams("Luna", "Captain Mara", "Bram", "Bellflower Isle", "the blue harbor shutter", "a brass compass mark", 0, 0, 0, 0),
        StoryParams("Milo", "Captain Flint", "Kit", "Moonwake Island", "the carved lighthouse shutter", "a painted parrot", 1, 1, 1, 1),
        StoryParams("Nia", "Captain Coral", "Sable", "Old Lantern Cay", "the red fort shutter", "three silver stars", 2, 2, 2, 2),
        StoryParams("Tavi", "Captain Juniper", "Wren", "Seashell Key", "the gold museum shutter", "a tiny anchor", 3, 3, 3, 3),
    ]


CURATED = build_curated()


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid_story/5."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} valid child-friend-shutter combinations.")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        for offset in range(max(50, args.n * 50)):
            if len(samples) >= args.n:
                break
            seed = base_seed + offset
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as error:
                print(error)
                return
            params.seed = seed
            apply_seeded_structure(params, seed)
            sample = generate(params)
            if sample.story not in seen:
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
            header = f"### {sample.params.child}: the historic shutter at {sample.params.island}"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
