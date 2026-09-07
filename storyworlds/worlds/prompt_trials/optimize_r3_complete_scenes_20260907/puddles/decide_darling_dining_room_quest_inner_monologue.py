#!/usr/bin/env python3
"""A small dining-room quest about deciding with care."""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

_here = Path(__file__).resolve()
for parent in (_here.parent, *_here.parents):
    candidate = parent / "results.py"
    if candidate.exists():
        sys.path.insert(0, str(parent))
        break
from pathlib import Path as _StoryPath
_storyworlds_root = next(parent for parent in _StoryPath(__file__).resolve().parents
                        if (parent / 'results.py').is_file() and (parent / 'asp.py').is_file())
sys.path.insert(0, str(_storyworlds_root))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Event:
    kind: str
    text: str
    cause: str
    result: str


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    history: list[Event] = field(default_factory=list)
    facts: dict[str, object] = field(default_factory=dict)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def event(self, kind: str, text: str, cause: str, result: str) -> None:
        self.history.append(Event(kind, text, cause, result))


@dataclass
class StoryParams:
    path: str
    child: str
    darling: str
    seed: Optional[int] = None


PATHS = ("candle", "missing_card", "wobbly_table")
CHILDREN = ("Nora", "Milo", "Lena", "Theo")
DARLINGS = ("Grandma", "Dad", "Aunt May", "Grandpa")

OPENINGS = {
    "candle": (
        "Nora carried a little birthday cake into the dining room for her darling Grandma.",
        "Milo carried a warm pie into the dining room for his darling Dad.",
        "Lena carried a little cake into the dining room for her darling Aunt May.",
        "Theo carried a fruit tart into the dining room for his darling Grandpa.",
    ),
    "missing_card": (
        "Nora came to the dining room with a card for her darling Grandma.",
        "Milo came to the dining room with a card for his darling Dad.",
        "Lena came to the dining room with a card for her darling Aunt May.",
        "Theo came to the dining room with a card for his darling Grandpa.",
    ),
    "wobbly_table": (
        "Nora set a bowl of berries on the dining-room table for her darling Grandma.",
        "Milo set a bowl of berries on the dining-room table for his darling Dad.",
        "Lena set a bowl of berries on the dining-room table for her darling Aunt May.",
        "Theo set a bowl of berries on the dining-room table for his darling Grandpa.",
    ),
}

PATH_DATA = {
    "candle": {
        "trouble": "A candle leaned close to the paper napkins, and the flame made a nervous little shadow.",
        "question": "Why did the child move the cake?",
        "learn": "The darling explained that a small flame could catch a paper napkin, even when nobody meant harm.",
        "decision": "The child decided to carry the cake away from the napkins and ask for a sturdy plate.",
        "resolution": "The cake rested safely on the clear plate while the napkins stayed far from the flame.",
        "knowledge": "A candle should be kept away from paper because a flame can make paper burn.",
    },
    "missing_card": {
        "trouble": "The card was not in the bright envelope, and the dining-room table suddenly felt much too quiet.",
        "question": "How did the child find the missing card?",
        "learn": "The darling remembered seeing the envelope beside the bread basket before dinner.",
        "decision": "The child decided to retrace each step instead of guessing or giving up.",
        "resolution": "The card was found beneath the bread basket and was placed in the envelope with a happy sigh.",
        "knowledge": "Retracing your steps can help you find something that has gone missing.",
    },
    "wobbly_table": {
        "trouble": "One leg of the dining-room table wobbled, and the bowl of berries slid toward the edge.",
        "question": "Why did the child wait before serving the berries?",
        "learn": "The darling noticed that a folded napkin could steady the short table leg.",
        "decision": "The child decided to ask for help before placing any more dishes on the table.",
        "resolution": "The napkin steadied the leg, and the berries sat safely in the middle of the table.",
        "knowledge": "A small support under a short table leg can help steady a wobbly table.",
    },
}


def build_world(params: StoryParams, rng: random.Random) -> World:
    if params.path not in PATHS:
        raise StoryError("The quest path must be candle, missing_card, or wobbly_table.")
    world = World()
    child = world.add(Entity(params.child, "character", params.child))
    darling = world.add(Entity(params.darling, "character", params.darling))
    room = world.add(Entity("dining_room", "place", "dining room"))
    child.memes["care"] = 1
    child.memes["suspense"] = 1
    world.facts.update(child=child, darling=darling, room=room, path=params.path)
    opening = OPENINGS[params.path][CHILDREN.index(params.child)]
    world.event(
        "arrival",
        opening + " The chairs stood neatly around the table, and the room smelled ready for a celebration.",
        "The child wanted to make a thoughtful surprise.",
        "The child entered the dining room with a special gift.",
    )
    data = PATH_DATA[params.path]
    world.event("trouble", data["trouble"], data["trouble"], "The child paused because the surprise might go wrong.")
    if params.path == "candle":
        spoken = rng.choice((
            f'"Should I blow it out?" {params.child} asked.',
            f'"Is this safe here?" {params.child} asked.',
        ))
        reply = f'"Not beside the napkins," {params.darling} said. "Let us give the flame more room."'
        result = "The child learned where the danger was."
    elif params.path == "missing_card":
        spoken = rng.choice((
            f'"Did I lose my surprise?" {params.child} asked.',
            f'"Where can my card be?" {params.child} asked.',
        ))
        reply = f'"Think about where you carried the envelope," {params.darling} said. "I saw it near the bread basket."'
        result = "The child learned a useful clue."
    else:
        spoken = rng.choice((
            f'"Why is the table moving?" {params.child} asked.',
            f'"Should I put down the bowl?" {params.child} asked.',
        ))
        reply = f'"Wait a moment," {params.darling} said. "A napkin may support the short leg."'
        result = "The child learned how the table could be steadied."
    world.event("learning", spoken + " " + reply + " " + data["learn"], data["trouble"], result)
    world.event(
        "decision",
        f'{data["decision"]} "{params.darling}, will you help me?" {params.child} asked. '
        f'"Of course, darling," {params.darling} replied.',
        data["learn"],
        "The child chose a careful next step with the darling's help.",
    )
    world.event("resolution", data["resolution"], data["decision"], data["resolution"])
    child.memes["suspense"] = 0
    child.memes["relief"] = 1
    return world


def story_qa(world: World) -> list[QAItem]:
    data = PATH_DATA[world.facts["path"]]
    return [
        QAItem(data["question"], f'{world.history[1].result} {data["learn"]}'),
        QAItem("What did the child decide to do?", world.history[3].text),
        QAItem("How did the quest end?", world.history[4].result),
    ]


def world_qa(world: World) -> list[QAItem]:
    data = PATH_DATA[world.facts["path"]]
    return [QAItem("What can this dining-room quest teach us?", data["knowledge"])]


def prompts(world: World) -> list[str]:
    child = world.facts["child"].id
    darling = world.facts["darling"].id
    return [
        f"Write a heartwarming dining-room quest in which {child} must decide what to do and learns from {darling}.",
        f"Tell a suspenseful story about {child}, {darling}, a careful decision, and a safe ending.",
    ]


def generate(params: StoryParams) -> StorySample:
    rng = random.Random(params.seed)
    world = build_world(params, rng)
    story = " ".join(event.text for event in world.history)
    return StorySample(
        params=params,
        story=story,
        prompts=prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


ASP_RULES = """
safe(candle) :- learned(candle), decided(candle).
safe(missing_card) :- learned(missing_card), decided(missing_card).
safe(wobbly_table) :- learned(wobbly_table), decided(wobbly_table).
#show safe/1.
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        asp.fact("learned", path) + "\n" + asp.fact("decided", path)
        for path in PATHS
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Dining-room decision quests.")
    parser.add_argument("--path", choices=PATHS)
    parser.add_argument("--child", choices=CHILDREN)
    parser.add_argument("--darling", choices=DARLINGS)
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
    path = args.path or rng.choice(PATHS)
    child = args.child or rng.choice(CHILDREN)
    darling = args.darling or rng.choice(DARLINGS)
    if child == darling:
        raise StoryError("The child and darling must be different characters.")
    return StoryParams(path=path, child=child, darling=darling)


def trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        lines.append(f"  {entity.id}: {entity.kind} ({entity.label})")
    lines.append("--- events ---")
    lines.extend(f"  {event.kind}: {event.text}" for event in world.history)
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== Story questions =="]
    for item in sample.story_qa:
        lines += [f"Q: {item.question}", f"A: {item.answer}"]
    lines.append("== World knowledge ==")
    for item in sample.world_qa:
        lines += [f"Q: {item.question}", f"A: {item.answer}"]
    return "\n".join(lines)


def verify() -> int:
    for path in PATHS:
        sample = generate(StoryParams(path, "Nora", "Grandma", 9))
        assert sample.story
        assert len(sample.story_qa) == 3
        assert all(event.text in sample.story for event in sample.world.history)
    try:
        import asp
        program = asp_facts() + "\n" + ASP_RULES
        assert asp.one_model(program)
    except ImportError:
        pass
    print("OK: three complete causal quest paths verified.")
    return 0


def emit(sample: StorySample, args: argparse.Namespace) -> None:
    print(sample.story)
    if args.trace:
        print(trace(sample.world))
    if args.qa:
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()
    if args.n < 1:
        raise SystemExit("-n must be at least 1")
    if args.show_asp:
        print(asp_facts() + "\n" + ASP_RULES)
        return
    if args.verify:
        raise SystemExit(verify())
    if args.asp:
        print(" ".join(PATHS))
        return
    if args.all:
        samples = [
            generate(StoryParams(path, CHILDREN[i], DARLINGS[i], args.seed))
            for i, path in enumerate(PATHS)
        ]
    else:
        base = args.seed if args.seed is not None else random.randrange(2**31)
        samples = []
        for i in range(args.n):
            rng = random.Random(base + i)
            params = resolve_params(args, rng)
            params.seed = base + i
            samples.append(generate(params))
    if args.json:
        payload = [sample.to_dict() for sample in samples]
        print(json.dumps(payload[0] if len(payload) == 1 else payload, indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        if i:
            print("\n" + "=" * 60 + "\n")
        emit(sample, args)


if __name__ == "__main__":
    main()
