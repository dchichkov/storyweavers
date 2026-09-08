#!/usr/bin/env python3
"""A gentle ghost story about a silly mistake, a golden thread, and curiosity."""

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
class Entity:
    id: str
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Setting:
    id: str
    label: str
    landmark: str


@dataclass
class Mystery:
    id: str
    clue: str
    false_belief: str
    investigation: str
    reveal: str
    repair: str
    ending: str


@dataclass
class StoryParams:
    setting: str = "old_house"
    mystery: str = "thread_in_stairwell"
    name: str = "Luna"
    ghost_name: str = "Morrow"
    opening: int = 0
    question: int = 0
    reflection: int = 0
    seed: Optional[int] = None
    samples: list = field(default_factory=list)


SETTINGS = {
    "old_house": Setting(
        "old_house",
        "the old house at the edge of town",
        "a narrow staircase with a moon-shaped window",
    ),
    "lighthouse": Setting(
        "lighthouse",
        "the empty lighthouse above the sea",
        "a spiral stair wrapped around a cold lantern room",
    ),
    "train_station": Setting(
        "train_station",
        "the closed station beside the sleeping tracks",
        "a waiting-room clock that had stopped at midnight",
    ),
}

MYSTERIES = {
    "thread_in_stairwell": Mystery(
        "thread_in_stairwell",
        "A silver thread ran from the moon-shaped window down the stairs and disappeared beneath a locked door.",
        "Luna decided the thread was a stupid ghost trap and tugged it hard.",
        "She followed the thread slowly, asked where it led, and watched which floorboards trembled.",
        "The thread belonged to Morrow, a lonely ghost, and marked the way to a tin box holding his lost house key.",
        "Luna loosened the thread, found the key, and opened the dusty music room so Morrow could hear his old piano again.",
        "At dawn, the silver thread became a warm gold line that curled into a small, thankful bow.",
    ),
    "bell_in_attic": Mystery(
        "bell_in_attic",
        "A tiny bell rang in the attic whenever the wind touched the roof.",
        "Luna called it a stupid haunting and planned to throw the bell away.",
        "She counted the rings, compared them with the gusts, and searched for a place where the sound changed.",
        "The bell was tied to a loose shutter, and the ghost had been using its rhythm to ask for help.",
        "Luna repaired the shutter and hung the bell where it could ring safely above the attic door.",
        "That night, the bell gave one clear note, and a pale hand waved goodbye through the rafters.",
    ),
    "footprints_by_fireplace": Mystery(
        "footprints_by_fireplace",
        "Small wet footprints appeared beside the cold fireplace and ended at a blank stone.",
        "Luna thought the ghost was being stupid and hiding behind the wall.",
        "She measured the prints, listened for a hollow sound, and pressed each stone only once.",
        "The blank stone opened a hidden cubby where a ghost child's wooden boat had been forgotten.",
        "Luna placed the boat in a basin of rainwater and set it beside the fireplace.",
        "The wet footprints dried into bright little stars before fading from the floor.",
    ),
}

OPENINGS = [
    "On a rainy evening, Luna entered the house because curiosity tugged harder than fear.",
    "The moon was thin, the windows were dark, and Luna followed a sound no one else could hear.",
    "Everyone in town avoided the old place, but Luna wanted to know why.",
    "At midnight, a pale shape crossed the upstairs hall, and Luna decided to look twice.",
]

QUESTIONS = [
    '"Why would a ghost leave a thread here?" Luna asked.',
    '"Is this truly a haunting, or is there a cause I can discover?" Luna wondered aloud.',
    '"What are you trying to show me?" Luna called into the darkness.',
    '"If I look carefully, will the mystery become kinder?" Luna asked.',
]

REFLECTIONS = [
    "Curiosity did not make the house less strange; it helped Luna meet its strangeness carefully.",
    "The mistake had been silly, but asking a better question made the next choice wiser.",
    "A ghost can frighten a person, yet a patient question can open a door fear keeps shut.",
    "Luna learned that calling something stupid is easy, while understanding it takes attention.",
]

NAMES = ["Luna", "Mara", "Nell", "Iris", "Tessa"]


class World:
    def __init__(self, setting: Setting):
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
        self.trace: list[str] = []

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity


def build_world(params: StoryParams) -> World:
    if params.setting not in SETTINGS:
        raise StoryError(f"Unknown setting: {params.setting}")
    if params.mystery not in MYSTERIES:
        raise StoryError(f"Unknown mystery: {params.mystery}")
    if not params.name.strip() or not params.ghost_name.strip():
        raise StoryError("Character names must not be empty.")
    if params.name.strip().lower() == params.ghost_name.strip().lower():
        raise StoryError("The child and ghost need different names.")

    setting = SETTINGS[params.setting]
    mystery = MYSTERIES[params.mystery]
    world = World(setting)
    child = world.add(Entity(params.name, "child", params.name, {"curiosity": 1}, {"curiosity": 1}))
    ghost = world.add(Entity(params.ghost_name, "ghost", params.ghost_name, {"loneliness": 1}, {"memory": 1}))
    world.facts.update(child=child, ghost=ghost, mystery=mystery, repaired=False)
    return world


def tell(params: StoryParams) -> World:
    world = build_world(params)
    child: Entity = world.facts["child"]  # type: ignore[assignment]
    ghost: Entity = world.facts["ghost"]  # type: ignore[assignment]
    mystery: Mystery = world.facts["mystery"]  # type: ignore[assignment]
    opening = OPENINGS[params.opening % len(OPENINGS)]
    question = QUESTIONS[params.question % len(QUESTIONS)]
    reflection = REFLECTIONS[params.reflection % len(REFLECTIONS)]

    paragraphs = [
        f"{opening} The place was {world.setting.label}, where {world.setting.landmark} cast a long shadow. "
        f"{child.label} carried a small lantern and listened to the rain.",
        f"{mystery.clue} A pale figure named {ghost.label} appeared at the top stair. "
        f"{child.label} thought the whole thing was stupid and pulled at the clue. The house answered with a cold sigh.",
        f'"{question.strip(chr(34))}" {child.label} asked. '
        f'"Please do not pull it," whispered {ghost.label}. "It is the only path I remember." '
        f"{child.label} stopped. Curiosity became stronger than the wish to run.",
        f"{mystery.investigation} {child.label} followed the clue one careful step at a time. "
        f"The ghost showed a faint memory, and the hidden truth became clear: {mystery.reveal}",
        f'"I am sorry I called it stupid," said {child.label}. '
        f'"You looked again," said {ghost.label}. "That is how lost things find their way home." '
        f"{mystery.repair}",
        f"The room warmed with a sound that had been missing for many years. "
        f"{reflection} {mystery.ending}",
    ]
    world.facts["repaired"] = True
    world.facts["ending"] = mystery.ending
    world.trace.extend(
        [
            "curiosity noticed an unusual clue",
            "a hurried tug increased the risk of losing the clue",
            "careful questions revealed the ghost's need",
            "the lost object was repaired or returned",
            "the ghost received a peaceful ending",
        ]
    )
    world.facts["paragraphs"] = paragraphs
    return world


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    mystery: Mystery = world.facts["mystery"]  # type: ignore[assignment]
    child: Entity = world.facts["child"]  # type: ignore[assignment]
    ghost: Entity = world.facts["ghost"]  # type: ignore[assignment]
    story = "\n\n".join(world.facts["paragraphs"])  # type: ignore[arg-type]
    prompts = [
        "Write a gentle ghost story in which curiosity replaces a quick judgment.",
        f"Include {child.label}, {ghost.label}, a thread or other clue, and a repaired mystery.",
        f"Show why calling the mystery stupid was less useful than asking what caused it.",
    ]
    story_qa = [
        QAItem(
            f"Why did {child.label} first call the mystery stupid?",
            "The child was frightened and made a quick judgment before understanding what the clue meant.",
        ),
        QAItem(
            f"What did {child.label}'s curiosity change?",
            f"Curiosity led {child.label} to investigate carefully, discover that {ghost.label} needed help, and repair the lost connection.",
        ),
        QAItem(
            "How did the ghost story end?",
            mystery.ending,
        ),
    ]
    world_qa = [
        QAItem(
            "What is curiosity?",
            "Curiosity is a wish to learn or understand something by looking, listening, and asking questions.",
        ),
        QAItem(
            "What is a ghost story?",
            "A ghost story is a tale about a spirit or strange presence, often using mystery, suspense, and a meaningful reveal.",
        ),
        QAItem(
            "What is a thread?",
            "A thread is a thin strand of material used for sewing, tying, weaving, or marking a path.",
        ),
    ]
    return StorySample(
        params=params,
        story=story,
        prompts=prompts,
        story_qa=story_qa,
        world_qa=world_qa,
        world=world,
    )


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    name = args.name or rng.choice(NAMES)
    ghost_name = args.ghost_name or rng.choice([n for n in NAMES if n != name] + ["Morrow", "Eve"])
    return StoryParams(
        setting=args.setting or rng.choice(list(SETTINGS)),
        mystery=args.mystery or rng.choice(list(MYSTERIES)),
        name=name,
        ghost_name=ghost_name,
        opening=rng.randrange(len(OPENINGS)),
        question=rng.randrange(len(QUESTIONS)),
        reflection=rng.randrange(len(REFLECTIONS)),
    )


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    lines.append("\n== (2) Story questions ==")
    for item in sample.story_qa:
        lines += [f"Q: {item.question}", f"A: {item.answer}"]
    lines.append("\n== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines += [f"Q: {item.question}", f"A: {item.answer}"]
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        lines.append(
            f"  {entity.label}: kind={entity.kind}, meters={entity.meters}, memes={entity.memes}"
        )
    lines.append(f"  repaired={world.facts.get('repaired')}")
    lines.append("  events:")
    lines.extend(f"    - {event}" for event in world.trace)
    return "\n".join(lines)


ASP_RULES = r"""
curious(child).
clue_found(child).
ghost_needs_help(ghost).
truth_found(child) :- curious(child), clue_found(child), ghost_needs_help(ghost).
mystery_repaired :- truth_found(child).
peaceful_ending :- mystery_repaired.
#show truth_found/1.
#show mystery_repaired/0.
#show peaceful_ending/0.
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("curious", "child"),
            asp.fact("clue_found", "child"),
            asp.fact("ghost_needs_help", "ghost"),
        ]
    )


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(
        asp_program("#show truth_found/1. #show mystery_repaired/0. #show peaceful_ending/0.")
    )
    rendered = {str(atom) for atom in model}
    expected = {"truth_found(child)", "mystery_repaired", "peaceful_ending"}
    if expected.issubset(rendered):
        print("OK: ASP twin matches the curiosity-and-repair gate.")
        return 0
    print("MISMATCH between ASP and Python.")
    print("  asp:", sorted(rendered))
    print("  expected:", sorted(expected))
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A gentle ghost story about curiosity.")
    parser.add_argument("--setting", choices=SETTINGS)
    parser.add_argument("--mystery", choices=MYSTERIES)
    parser.add_argument("--name")
    parser.add_argument("--ghost-name", dest="ghost_name")
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


def emit(sample: StorySample, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print("\n" + format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()
    if args.verify:
        raise SystemExit(asp_verify())
    if args.show_asp:
        print(asp_program("#show truth_found/1. #show mystery_repaired/0. #show peaceful_ending/0."))
        return
    if args.asp:
        import asp
        model = asp.one_model(
            asp_program("#show truth_found/1. #show mystery_repaired/0. #show peaceful_ending/0.")
        )
        print("\n".join(sorted(str(atom) for atom in model)))
        return

    seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        combinations = [
            (setting, mystery)
            for setting in SETTINGS
            for mystery in MYSTERIES
        ]
        samples = []
        for index, (setting, mystery) in enumerate(combinations):
            params = StoryParams(
                setting=setting,
                mystery=mystery,
                name="Luna",
                ghost_name="Morrow",
                opening=index % len(OPENINGS),
                question=index % len(QUESTIONS),
                reflection=index % len(REFLECTIONS),
                seed=seed + index,
            )
            samples.append(generate(params))
    else:
        samples = []
        for index in range(args.n):
            rng = random.Random(seed + index)
            params = resolve_params(args, rng)
            params.seed = seed + index
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
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
