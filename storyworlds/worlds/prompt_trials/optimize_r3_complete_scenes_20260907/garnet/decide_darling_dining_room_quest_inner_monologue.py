#!/usr/bin/env python3
"""
A heartwarming dining-room quest about deciding what kindness requires.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

_here = os.path.abspath(__file__)
_storyworlds = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(_here)))))
if not os.path.exists(os.path.join(_storyworlds, "results.py")):
    _storyworlds = os.path.dirname(os.path.dirname(_storyworlds))
sys.path.insert(0, _storyworlds)
from pathlib import Path as _StoryPath
_storyworlds_root = next(parent for parent in _StoryPath(__file__).resolve().parents
                        if (parent / 'results.py').is_file() and (parent / 'asp.py').is_file())
sys.path.insert(0, str(_storyworlds_root))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Item:
    id: str
    label: str
    kind: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    hero: Item
    darling: Item
    room: str
    seed: int
    path: str = ""
    facts: dict[str, str] = field(default_factory=dict)


@dataclass
class StoryParams:
    name: str
    darling_name: str
    room: str = "the dining room"
    seed: Optional[int] = None


NAMES = ["Mara", "Theo", "Lina", "Jonah", "Pia", "Sam"]
DARLINGS = ["Darling", "Aunt Rose", "Grandma June", "Uncle Ben", "Mina"]
ROOMS = ["the dining room"]

ASP_RULES = r"""
#show quest_ready/1.
#show truth_shared/1.
#show kindness_done/1.

quest_ready(H) :- enters_dining_room(H).
truth_shared(H) :- asks_gently(H), receives_answer(H).
kindness_done(H) :- chooses_kindly(H), helps_darling(H).
"""


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("enters_dining_room", "hero"),
        asp.fact("asks_gently", "hero"),
        asp.fact("receives_answer", "hero"),
        asp.fact("chooses_kindly", "hero"),
        asp.fact("helps_darling", "hero"),
    ])


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    symbols = asp.one_model(asp_program())
    got = {(a.name, tuple(
        x.number if x.type == x.type.Number else x.name
        for x in a.arguments
    )) for a in symbols}
    expected = {
        ("quest_ready", ("hero",)),
        ("truth_shared", ("hero",)),
        ("kindness_done", ("hero",)),
    }
    if got == expected:
        print("OK: ASP parity verified.")
        return 0
    print("MISMATCH between ASP and Python expectations.")
    print("ASP:", sorted(got))
    print("PY :", sorted(expected))
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A heartwarming dining-room decision quest.")
    parser.add_argument("--name", choices=NAMES)
    parser.add_argument("--darling-name", choices=DARLINGS)
    parser.add_argument("--room", choices=ROOMS, default="the dining room")
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
        darling_name=args.darling_name or rng.choice(DARLINGS),
        room=args.room,
    )


def build_world(params: StoryParams) -> World:
    if params.room != "the dining room":
        raise StoryError("This quest must take place in the dining room.")
    hero = Item("hero", params.name, "child", {"reach": 1.0}, {"courage": 0.7})
    darling = Item("darling", params.darling_name, "helper", {"reach": 1.0}, {"trust": 0.8})
    seed = params.seed if params.seed is not None else sum(ord(c) for c in params.name + params.darling_name)
    return World(hero, darling, params.room, seed)


def _choose(rng: random.Random, values: list[str]) -> str:
    return values[rng.randrange(len(values))]


def _set_facts(world: World, **facts: str) -> None:
    world.facts.update(facts)


def _path_cake(world: World, rng: random.Random) -> str:
    h, d, room = world.hero.label, world.darling.label, world.room
    scent = _choose(rng, ["cinnamon", "warm apples", "vanilla"])
    line = _choose(rng, [
        "The room smelled of cinnamon and waiting.",
        "A gentle vanilla smell floated above the quiet table.",
    ])
    _set_facts(
        world,
        path="cake",
        trouble="the birthday cake was hidden in the dark pantry and the candles had not been counted",
        learned="the cake was meant for a tired neighbor who had never been given a birthday party",
        decision=f"{h} decided to carry the cake carefully and let {d} light only the candles that were safe",
        resolution=f"{h} and {d} carried the cake into the dining room and welcomed the surprised neighbor",
        ending="the last candle shone in a slice of cake shared around the table",
        lesson="asking before acting helped the children protect both the surprise and the person it was meant to comfort",
    )
    return " ".join([
        f"Late one afternoon, {h} entered {room} and found {d} watching a cake beneath a cloth.",
        f"{line} A small trail of {scent} led toward the pantry, where the cake waited beside a box of candles.",
        f'"Should we bring it out now?" {h} asked. {d} shook their head. "First we must know whom it is for."',
        f"The question made {h} pause. In the pantry, {d} explained that the cake was for a neighbor who had been working alone and had never had a birthday party.",
        f"Then {h} noticed two candles had bent wicks. The suspense felt like a held breath, but the answer was clear: a surprise mattered less than keeping everyone safe.",
        f'"I decide we carry it slowly," {h} said. "And we use only the good candles." {d} nodded and moved the unsafe ones away.',
        f"Together they crossed the room with both hands under the plate. The neighbor arrived, and {d} told the truth before the candles were lit.",
        f"The neighbor smiled through tears. At last, {world.facts['ending']}.",
    ])


def _path_letter(world: World, rng: random.Random) -> str:
    h, d, room = world.hero.label, world.darling.label, world.room
    object_name = _choose(rng, ["a blue envelope", "a folded card", "a little white letter"])
    _set_facts(
        world,
        path="letter",
        trouble=f"{object_name} had fallen beneath the dining table and its name side was hidden",
        learned="the letter was a thank-you note for a friend who had been afraid to ask for help",
        decision=f"{h} decided not to open the letter and instead asked {d} to help find its owner",
        resolution=f"{d} recognized the handwriting, and {h} carried the sealed letter to its grateful owner",
        ending="the sealed letter rested in its owner's hands while two cups of tea warmed the table",
        lesson="respecting a secret while seeking its owner allowed gratitude to arrive safely",
    )
    return " ".join([
        f"While setting plates in {room}, {h} saw {object_name} slide beneath the table.",
        f"{d} reached for it, but the name side was pressed against the floor. The quiet envelope made the room feel full of suspense.",
        f'"We could open it and find out," {h} whispered. {d} answered, "We could also ask without reading what is not ours."',
        f"That answer changed what {h} knew. The letter was not a puzzle to conquer; it was a message that deserved its own person.",
        f"{h} looked for clues without opening it and noticed a silver thread from the sewing basket caught on the corner.",
        f"{d} remembered that the thread belonged to a friend who had been afraid to ask for help. The thank-you note was meant for that friend.",
        f'"Then I decide we keep it sealed," {h} said. {d} led the way, and {h} carried the letter gently across the room.',
        f"The owner read it and hugged them both. By evening, {world.facts['ending']}.",
    ])


def _path_bowl(world: World, rng: random.Random) -> str:
    h, d, room = world.hero.label, world.darling.label, world.room
    food = _choose(rng, ["soup", "stew", "porridge"])
    _set_facts(
        world,
        path="bowl",
        trouble=f"a full bowl of {food} had been left at the edge of the table, where a small cat could knock it down",
        learned=f"{d} had set the {food} aside for a hungry delivery worker who was delayed by rain",
        decision=f"{h} decided to move the bowl to the safe middle of the table and wait with {d}",
        resolution=f"{h} placed the bowl safely, and {d} shared it with the delivery worker when they arrived",
        ending=f"the empty bowl gleamed beside the dry umbrella while the delivery worker laughed with relief",
        lesson="waiting with someone turned a risky accident into a welcome meal",
    )
    return " ".join([
        f"Rain tapped the windows when {h} came into {room}. At the table, a full bowl of {food} stood close to the edge.",
        f"A kitten crept beneath the chair, and the bowl wobbled. {h} felt the suspense tighten in their chest.",
        f'"Should I grab it?" {h} asked. "Not yet," said {d}. "Tell me why it is there."',
        f"{d} explained that the bowl was for a hungry delivery worker delayed by the rain. The worker had promised to come, but the promise had no exact time.",
        f"{h} understood that rushing could spill the meal, while waiting alone might leave {d} worried. The child moved the bowl to the safe middle of the table.",
        f'"I decide we wait together," {h} said. {d} smiled and brought two dry napkins.',
        f"When the worker finally arrived, {d} offered the meal, and {h} explained how carefully they had guarded it.",
        f"The worker laughed with relief. Soon, {world.facts['ending']}.",
    ])


PATHS = [_path_cake, _path_letter, _path_bowl]


def generate_story(world: World) -> str:
    rng = random.Random(world.seed ^ 0x5A17C)
    builder = PATHS[world.seed % len(PATHS)]
    return builder(world, rng)


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    h = world.hero.label
    return [
        QAItem(
            question=f"What trouble did {h} find in the dining room?",
            answer=f"{h} found that {f['trouble']}.",
        ),
        QAItem(
            question="What did the characters learn?",
            answer=f"They learned that {f['learned']}.",
        ),
        QAItem(
            question=f"What did {h} decide to do?",
            answer=f"{f['decision']}.",
        ),
        QAItem(
            question="How did the quest end?",
            answer=f"It ended when {f['resolution']}.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="Why is it wise to ask before opening someone else's letter?",
            answer="Asking first respects the writer and the person who is meant to receive the letter.",
        ),
        QAItem(
            question="Why should hot food be kept away from an edge?",
            answer="Keeping hot food away from an edge helps prevent spills, burns, and broken dishes.",
        ),
        QAItem(
            question="What does suspense do in a story?",
            answer="Suspense makes readers wonder what will happen next while a character waits or makes an important choice.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    return [
        "Write a heartwarming dining-room quest about deciding what kindness requires.",
        f"Write a suspenseful story in which {world.hero.label} and {world.darling.label} learn something before acting.",
        "Use an inner monologue, gentle dialogue, and a visible ending image to show a caring decision.",
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for item in (world.hero, world.darling):
        lines.append(
            f"  {item.id:7} {item.kind:8} label={item.label!r} "
            f"meters={item.meters} memes={item.memes}"
        )
    lines.append(f"  room={world.room!r}")
    lines.append(f"  path={world.path!r}")
    for key, value in world.facts.items():
        lines.append(f"  {key}={value!r}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== Generation prompts =="]
    out.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    out.append("")
    out.append("== Story QA ==")
    for item in sample.story_qa:
        out.extend([f"Q: {item.question}", f"A: {item.answer}"])
    out.append("")
    out.append("== World QA ==")
    for item in sample.world_qa:
        out.extend([f"Q: {item.question}", f"A: {item.answer}"])
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


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
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
        print(asp_program("#show quest_ready/1.\n#show truth_shared/1.\n#show kindness_done/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("3 compatible logical atoms: quest_ready(hero), truth_shared(hero), kindness_done(hero)")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        presets = [
            StoryParams("Mara", "Darling", seed=base_seed),
            StoryParams("Theo", "Aunt Rose", seed=base_seed + 1),
            StoryParams("Lina", "Grandma June", seed=base_seed + 2),
        ]
        samples = [generate(p) for p in presets]
    else:
        for index in range(max(0, args.n)):
            rng = random.Random(base_seed + index)
            params = resolve_params(args, rng)
            params.seed = base_seed + index
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        header = ""
        if args.all:
            header = f"### {sample.params.name} in {sample.params.room}"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
