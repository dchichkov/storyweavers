#!/usr/bin/env python3
"""
A pirate tale about a historic shutter, friendship, and problem solving.
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

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    label: str
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
        self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


@dataclass(frozen=True)
class Problem:
    name: str
    danger: str
    clue: str
    shared_tool: str
    action: str
    result: str
    lesson: str
    ending: str


@dataclass
class StoryParams:
    island: str
    captain: str
    child: str
    child_gender: str
    friend: str
    problem: str
    seed: Optional[int] = None


PROBLEMS = {
    "moon_tide": Problem(
        "the moon-tide signal",
        "the rising tide could trap the crew in the cove",
        "the salt line on the old wood showed that the lower hinge had shifted",
        "a coil of rope and a silver spoon",
        "used the spoon to clear grit from the hinge while the friend held the rope tight",
        "the historic shutter opened just before the tide covered the stepping stones",
        "a hard puzzle becomes smaller when friends hold different parts of it together",
        "The moon rose over the cove, and the shutter clicked safely shut behind the laughing crew.",
    ),
    "storm_map": Problem(
        "the storm map",
        "a squall was racing toward the harbor",
        "a faded star beneath the shutter matched the oldest mark on the captain's map",
        "a red scarf and a piece of chalk",
        "marked the safe rocks with chalk while the friend used the scarf to signal the lookout",
        "the crew found a sheltered channel before the rain struck",
        "good friends compare what they notice instead of arguing over who is right",
        "Rain drummed on the deck while the crew sailed through the bright, safe channel.",
    ),
    "parrot_key": Problem(
        "the parrot's key",
        "the harbor gate would stay locked at sunset",
        "the parrot kept tapping one loose shutter slat with its beak",
        "a biscuit and a bent hairpin",
        "gave the parrot the biscuit so the friend could lift the slat and free the key",
        "the harbor gate opened for every boat before dark",
        "kind attention can reveal the answer hidden inside a noisy problem",
        "The parrot squawked from the mast as every friendly boat glided home.",
    ),
    "bell_wind": Problem(
        "the wind bell",
        "the warning bell might call sailors away from a safe dock",
        "the shutter's oldest nail rattled whenever the wind turned east",
        "a wooden spoon and a length of sailcloth",
        "tested the shutter in three winds while the friend tied the sailcloth around the loose nail",
        "the bell rang only when the sea truly grew rough",
        "careful tests help friends solve trouble without making new trouble",
        "At dawn, the bell gave one true ring, and the calm sea shone like blue glass.",
    ),
}

ISLANDS = ["Whispering Cay", "Copperhook Isle", "Starfish Key", "Old Lantern Island"]
CAPTAINS = ["Captain Mara", "Captain Sol", "Captain Brin", "Captain Tessa"]
CHILDREN = {
    "girl": ["Luna", "Nia", "Pia", "Rosa"],
    "boy": ["Finn", "Kito", "Jory", "Milo"],
}
FRIENDS = ["Tavi", "Bram", "Sella", "Pip"]
DIALOGUES = [
    ("Luna", "I see the trouble, but I do not see the answer yet."),
    ("friend", "Then let us each inspect one part and tell the truth about what we find."),
    ("Luna", "Will you hold this while I test the hinge?"),
    ("friend", "Aye. Your idea and my steady hands can make one good plan."),
]
ADJECTIVES = ["curious", "patient", "brave", "careful", "cheerful"]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A pirate tale about a historic shutter and friendship.")
    parser.add_argument("--island", choices=ISLANDS)
    parser.add_argument("--captain", choices=CAPTAINS)
    parser.add_argument("--child")
    parser.add_argument("--gender", choices=["girl", "boy"])
    parser.add_argument("--friend")
    parser.add_argument("--problem", choices=list(PROBLEMS))
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
    gender = args.gender or rng.choice(["girl", "boy"])
    child = args.child or rng.choice(CHILDREN[gender])
    return StoryParams(
        island=args.island or rng.choice(ISLANDS),
        captain=args.captain or rng.choice(CAPTAINS),
        child=child,
        child_gender=gender,
        friend=args.friend or rng.choice(FRIENDS),
        problem=args.problem or rng.choice(list(PROBLEMS)),
    )


def reasonableness_gate(params: StoryParams) -> None:
    if params.problem not in PROBLEMS:
        raise StoryError("That pirate problem is not in the story chart.")
    if params.child == params.friend:
        raise StoryError("The child and friend need different names so their conversation is clear.")
    if not params.island or not params.captain:
        raise StoryError("A pirate tale needs an island and a captain.")


def generate(params: StoryParams) -> StorySample:
    reasonableness_gate(params)
    problem = PROBLEMS[params.problem]
    world = World()

    child = world.add(Entity(params.child, "character", params.child))
    friend = world.add(Entity(params.friend, "character", params.friend))
    captain = world.add(Entity(params.captain, "character", params.captain))
    shutter = world.add(Entity("historic_shutter", "object", "the historic shutter"))

    child.memes.update(curiosity=1.0, worry=1.0)
    friend.memes.update(trust=1.0)
    shutter.meters.update(age=100.0, stuck=1.0)

    world.say(
        f"On {params.island}, {params.captain} kept a historic shutter above the harbor door. "
        "It had guarded sailors for so many years that every pirate treated its carved stars with respect."
    )
    world.say(
        f"{params.child}, a {random.Random(params.seed).choice(ADJECTIVES) if params.seed is not None else 'curious'} "
        f"{params.child_gender}, loved to study the shutter with {params.friend}, the ship's youngest deckhand."
    )
    world.para()

    world.say(
        f"One afternoon, {problem.danger}. The shutter would not move, and the old harbor chart could not be read."
    )
    world.say(
        f"{params.child} pulled hard. The shutter groaned, but the first idea did not help. "
        f"Then {params.friend} said, \"{DIALOGUES[1][1]}\""
    )
    world.say(
        f"\"{DIALOGUES[2][0]}\" asked {params.child}. "
        f"\"{DIALOGUES[3][1]}\" answered {params.friend}."
    )
    world.para()

    child.meters["observing"] = 1.0
    friend.meters["helping"] = 1.0
    world.say(f"Together they noticed the clue: {problem.clue}.")
    world.say(
        f"They shared {problem.shared_tool}. {params.child} {problem.action}, while {params.friend} watched the hinges and called out each small change."
    )
    child.memes["confidence"] = 1.0
    friend.memes["trust"] = 2.0
    shutter.meters["stuck"] = 0.0
    world.say(f"Their plan worked: {problem.result}.")
    world.para()

    world.say(
        f"{params.captain} smiled and said, \"A pirate crew is strongest when friendship helps every mind solve one problem.\""
    )
    world.say(
        f"{params.child} learned that {problem.lesson}. "
        f"{params.friend} painted a tiny pair of linked stars beside the historic shutter."
    )
    world.say(problem.ending)

    world.facts.update(problem=problem, child=child, friend=friend, captain=captain, shutter=shutter)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    problem: Problem = world.facts["problem"]
    child: Entity = world.facts["child"]
    return [
        f"Write a gentle pirate tale about {child.label}, friendship, and problem solving around a historic shutter.",
        f"Tell a pirate story in which friends solve this danger: {problem.danger}.",
        "Write a child-friendly adventure with spoken dialogue and an ending image that proves the friends succeeded.",
    ]


def story_qa(world: World) -> list[QAItem]:
    problem: Problem = world.facts["problem"]
    child: Entity = world.facts["child"]
    friend: Entity = world.facts["friend"]
    captain: Entity = world.facts["captain"]
    return [
        QAItem(
            f"Who worked beside {child.label}?",
            f"{friend.label} worked beside {child.label}, and their friendship helped them solve the harbor problem.",
        ),
        QAItem(
            "What made the problem dangerous?",
            f"It was dangerous because {problem.danger}.",
        ),
        QAItem(
            "What clue did the friends notice?",
            f"They noticed that {problem.clue}.",
        ),
        QAItem(
            "How did the friends solve the problem?",
            f"They shared {problem.shared_tool}; then {child.label} {problem.action}.",
        ),
        QAItem(
            "What did the captain teach them?",
            f"{captain.label} taught that a pirate crew is strongest when friendship helps every mind solve one problem.",
        ),
        QAItem(
            "What changed at the end?",
            f"The plan succeeded: {problem.result} The linked stars beside the shutter showed that the friends had changed the harbor's story.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What is a shutter?",
            "A shutter is a hinged covering that can open or close a window or doorway.",
        ),
        QAItem(
            "Why is friendship useful during problem solving?",
            "Friendship makes it easier to share observations, tools, and courage while people search for a safe answer.",
        ),
        QAItem(
            "What does historic mean?",
            "Historic means important because it belongs to the past and helps people remember what happened before.",
        ),
        QAItem(
            "What does a pirate crew do?",
            "A pirate crew works together aboard a ship, sharing duties such as steering, watching, and caring for the vessel.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== Story QA ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== World QA ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for entity in world.entities.values():
        lines.append(
            f"{entity.label}: kind={entity.kind} meters={entity.meters} memes={entity.memes}"
        )
    return "\n".join(lines)


ASP_RULES = r"""
valid(island, problem) :- island(island), problem(problem).
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("island", "pirate_island"),
            *(asp.fact("problem", name) for name in PROBLEMS),
        ]
    )


def asp_program(show: str = "#show valid/2.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    return sorted(set(asp.atoms(asp.one_model(asp_program()), "valid")))


def valid_combos() -> list[tuple[str, str]]:
    return [("pirate_island", name) for name in PROBLEMS]


def asp_verify() -> int:
    expected = set(valid_combos())
    actual = set(asp_valid_combos())
    if expected != actual:
        print(f"MISMATCH: Python={sorted(expected)} ASP={sorted(actual)}")
        return 1
    rng = random.Random(17)
    for _ in range(3):
        params = resolve_params(build_parser().parse_args([]), rng)
        generate(params)
    print(f"OK: ASP matches Python ({len(expected)} combinations); generated stories pass.")
    return 0


def emit(sample: StorySample, trace: bool, qa: bool, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams("Whispering Cay", "Captain Mara", "Luna", "girl", "Tavi", "moon_tide"),
    StoryParams("Copperhook Isle", "Captain Sol", "Finn", "boy", "Sella", "storm_map"),
    StoryParams("Starfish Key", "Captain Brin", "Nia", "girl", "Bram", "parrot_key"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp or args.asp:
        print(asp_program())
        return
    if args.verify:
        raise SystemExit(asp_verify())

    seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for offset in range(args.n):
            rng = random.Random(seed + offset)
            params = resolve_params(args, rng)
            params.seed = seed + offset
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        header = f"### variant {index + 1}" if len(samples) > 1 else ""
        emit(sample, args.trace, args.qa, header)
        if index + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
