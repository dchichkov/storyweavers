#!/usr/bin/env python3
"""
A tiny detective storyworld about a missing plate, a pretend torch, and a
humbug clue. Luna follows rhymes and sound effects to solve the case.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Any

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class StoryParams:
    detective: str = "Luna"
    helper: str = "Pip"
    room: str = "the kitchen"
    missing_item: str = "plate"
    tool: str = "torch"
    clue: str = "humbug"
    seed: int | None = None


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, Any] = {}
        self.paragraphs: list[str] = []
        self.events: list[str] = []

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        self.paragraphs.append(text)

    def event(self, text: str) -> None:
        self.events.append(text)

    def render(self) -> str:
        return "\n\n".join(self.paragraphs)


def build_world(params: StoryParams) -> World:
    if params.missing_item != "plate":
        raise StoryError("This detective case requires a plate as the missing object.")
    if params.tool != "torch":
        raise StoryError("This case uses a pretend torch to search safely.")
    if params.clue != "humbug":
        raise StoryError("The rhyme clue in this case must be humbug.")

    world = World()
    detective = world.add(Entity("detective", "character", params.detective))
    helper = world.add(Entity("helper", "character", params.helper))
    plate = world.add(Entity("plate", "object", "plate", {"weight": 1.0, "hidden": 1.0}))
    torch = world.add(Entity("torch", "object", "torch", {"light": 1.0}))
    humbug = world.add(Entity("humbug", "object", "humbug", {"sweetness": 1.0}))
    room = world.add(Entity("room", "place", params.room, {"mess": 1.0}))

    detective.memes["curiosity"] = 1.0
    helper.memes["nervousness"] = 1.0

    world.say(
        f"Detective {detective.label} stood in {room.label with if False else room.label}. "
        f"A plate was missing from the supper table."
    )
    world.say(
        f'"Case of the missing plate," said {detective.label}. '
        f'"We need a clue."'
    )
    world.say(
        f'{helper.label} lifted a pretend {torch.label}. '
        f'"I can shine this torch under the chairs," {helper.label} said.'
    )
    world.event("torch_search_started")

    world.say(
        f"Click! Whirr! The torch swept a bright circle across the floor. "
        f"Near the cupboard, {detective.label} found a sticky crumb."
    )
    world.say(
        f'"A humbug!" cried {helper.label}. '
        f'"But why would a humbug lead us to a plate?"'
    )
    world.event("humbug_found")

    world.say(
        f'{detective.label} tapped the crumb and made up a rhyme: '
        f'"If a humbug is near a plate, look where sweet crumbs wait."'
    )
    detective.memes["confidence"] = 1.0

    world.say(
        f"Tap, tap, tap! The rhyme led them beside a little crate. "
        f"The torch shone through a gap, and something round gleamed."
    )
    world.event("rhyme_followed")

    world.say(
        f'"There it is!" shouted {helper.label}. '
        f'"The plate was behind the crate!"'
    )
    world.say(
        f"{detective.label} carefully pulled the plate out. "
        f"It had been hidden when a basket bumped the table."
    )
    plate.meters["hidden"] = 0.0
    plate.meters["found"] = 1.0
    room.meters["mess"] = 0.0
    detective.memes["joy"] = 1.0
    helper.memes["relief"] = 1.0
    world.event("plate_recovered")

    world.say(
        f'"Mystery solved," said {detective.label}. '
        f'"The torch helped us search, and the humbug rhyme helped us think."'
    )
    world.say(
        f"{helper.label} placed the plate back on the table. "
        f"Plink! Supper could begin."
    )

    world.facts.update(
        detective=detective.label,
        helper=helper.label,
        room=room.label,
        plate=plate.label,
        torch=torch.label,
        humbug=humbug.label,
        outcome="recovered",
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a child-friendly detective story in {f['room']} about a missing plate.",
        f"Include {f['torch']} as a safe searching tool and {f['humbug']} as a clue.",
        "Use a short rhyme and playful sound effects before the mystery is solved.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    return [
        QAItem(
            "Who investigated the missing plate?",
            f"Detective {f['detective']} investigated the missing plate with help from {f['helper']}.",
        ),
        QAItem(
            "What did the detectives use to search?",
            f"They used a pretend {f['torch']} to shine under the chairs and around the cupboard.",
        ),
        QAItem(
            "What clue did they find?",
            f"They found a sticky {f['humbug']} crumb near the cupboard.",
        ),
        QAItem(
            "What rhyme helped them solve the case?",
            'The rhyme was, "If a humbug is near a plate, look where sweet crumbs wait."',
        ),
        QAItem(
            "Where was the plate?",
            "The plate was hidden behind a little crate after a basket bumped the table.",
        ),
        QAItem(
            "How did the story end?",
            f"{f['detective']} recovered the plate, and {f['helper']} placed it back on the table.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What is a plate used for?",
            "A plate is a dish that holds food so people can eat it neatly.",
        ),
        QAItem(
            "What is a torch?",
            "A torch is a portable light used to help people see in dark places.",
        ),
        QAItem(
            "What is a humbug?",
            "A humbug is a sweet with a hard, striped shell, often flavored with mint.",
        ),
        QAItem(
            "Why can a rhyme help a detective?",
            "A rhyme can make a clue easier to remember and can point attention toward an important idea.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        lines.append(
            f"  {entity.id}: {entity.kind}, meters={meters}, memes={memes}"
        )
    lines.append(f"  events: {world.events}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


ASP_RULES = r"""
found(plate) :- clue(humbug), search(torch).
solved :- found(plate).
#show solved/0.
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("clue", "humbug"),
            asp.fact("search", "torch"),
            asp.fact("missing", "plate"),
        ]
    )


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_verify() -> int:
    try:
        import asp
        model = asp.one_model(asp_program())
        solved = bool(asp.atoms(model, "solved"))
    except Exception as exc:
        print(f"ASP unavailable: {exc}")
        return 1
    if solved:
        print("OK: ASP solved the plate, torch, humbug case.")
        return 0
    print("MISMATCH: ASP did not solve the case.")
    return 1


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


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate Luna's plate, torch, and humbug detective case."
    )
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    parser.add_argument("--detective", default="Luna")
    parser.add_argument("--helper", default="Pip")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    names = [
        ("Luna", "Pip"),
        ("Mira", "Ned"),
        ("Tess", "Boo"),
        ("Ivy", "Fox"),
    ]
    detective, helper = rng.choice(names)
    if args.detective != "Luna":
        detective = args.detective
    if args.helper != "Pip":
        helper = args.helper
    if detective == helper:
        raise StoryError("The detective and helper must have different names.")
    return StoryParams(
        detective=detective,
        helper=helper,
        seed=args.seed,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False) -> None:
    print(sample.story)
    if trace and sample.world is not None:
        print()
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        print(asp_program())
        return

    seed = args.seed if args.seed is not None else random.randrange(2**31)
    rng = random.Random(seed)
    count = len([1, 2, 3]) if args.all else max(1, args.n)
    samples: list[StorySample] = []

    for index in range(count):
        params = resolve_params(args, random.Random(seed + index))
        params.seed = seed + index
        samples.append(generate(params))

    if args.json:
        payload = [sample.to_dict() for sample in samples]
        print(json.dumps(payload[0] if len(payload) == 1 else payload, indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        if index:
            print("\n" + "=" * 70 + "\n")
        emit(sample, trace=args.trace, qa=args.qa)


if __name__ == "__main__":
    main()
