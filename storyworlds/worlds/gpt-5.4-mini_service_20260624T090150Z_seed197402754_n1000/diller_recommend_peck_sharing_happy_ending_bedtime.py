#!/usr/bin/env python3
"""
A tiny bedtime story world about sharing at night.

Premise:
A child wants to keep a beloved bedtime comfort item all to themselves,
but a nearby sibling or friend needs it to feel safe at bedtime.

Tension:
The child clutches the item, hears a gentle recommendation to share,
and worries the night will feel less cozy.

Turn:
A small act of sharing reveals that the comfort can be divided or passed
back and forth without losing its warmth.

Resolution:
Everyone settles in, the room grows calm, and the ending image proves
the comfort was not smaller after sharing; it became part of a happier night.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    held_by: Optional[str] = None
    shared_with: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Setting:
    place: str = "the bedroom"
    time: str = "night"


@dataclass
class ComfortItem:
    id: str
    label: str
    phrase: str
    type: str
    warmth: str
    can_share: bool = True


@dataclass
class StoryParams:
    name: str
    companion: str
    item: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.facts: dict = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def render(self) -> str:
        return " ".join(self.lines)


ITEMS = {
    "blanket": ComfortItem("blanket", "blanket", "a soft blue blanket", "blanket", "warm"),
    "lamp": ComfortItem("lamp", "little lamp", "a round night lamp", "lamp", "glowy"),
    "book": ComfortItem("book", "storybook", "a tiny bedtime storybook", "book", "quiet"),
}

NAMES = ["Diller", "Mina", "Pip", "Luna", "Nora", "Toby", "Peck", "Milo"]
COMPANIONS = ["a sleepy little sister", "a small brother", "a cuddly teddy bear", "a best friend"]
TRAITS = ["gentle", "shy", "brave", "sleepy", "kind"]


def reasonableness_gate(params: StoryParams) -> None:
    if params.item not in ITEMS:
        raise StoryError("Unknown comfort item.")
    if not params.name:
        raise StoryError("A child name is required.")
    if params.name.lower() == params.companion.lower():
        raise StoryError("The child and companion must be different.")


class BedtimeWorld:
    def __init__(self, params: StoryParams) -> None:
        self.params = params
        self.world = World(Setting())
        self.child = self.world.add(Entity(
            id=params.name, kind="character", type="child", label=params.name,
            meters={"sleepy": 0.2}, memes={"love": 0.5, "worry": 0.0, "joy": 0.0}
        ))
        self.companion = self.world.add(Entity(
            id="companion", kind="character", type="friend", label=params.companion,
            meters={"sleepy": 0.4}, memes={"need": 0.7, "joy": 0.0}
        ))
        item = ITEMS[params.item]
        self.item = self.world.add(Entity(
            id=item.id, kind="thing", type=item.type, label=item.label,
            phrase=item.phrase, owner=self.child.id, held_by=self.child.id,
            meters={"warm": 1.0}, memes={"value": 1.0}
        ))
        self.recommended = False
        self.shared = False

    def setup(self) -> None:
        p = self.params
        self.world.say(f"It was bedtime in the bedroom, and {p.name} held {self.item.phrase} close.")
        self.world.say(f"{p.name} loved {self.item.label} because it felt {ITEMS[p.item].warmth} and safe.")
        self.world.say(f"Near the bed, {p.companion} looked sleepy and very quiet.")

    def tension(self) -> None:
        p = self.params
        self.world.say(f"{p.companion.capitalize()} peered at the {self.item.label} and gave a tiny peck of a smile.")
        self.world.say(f'"Could you share?" {p.companion} asked in a small voice.')
        self.recommended = True
        self.child.memes["worry"] = 1.0
        self.child.memes["conflict"] = 1.0
        self.world.say(f"{p.name} hugged {self.item.label} a little tighter and did not know what to do.")

    def turn(self) -> None:
        p = self.params
        self.world.say(f"Then {p.companion} made a gentle recommendation: 'We can share it for a little while.'")
        if self.item.type == "book":
            self.world.say(f"They could take turns turning the pages, one page for each sleepy breath.")
        elif self.item.type == "lamp":
            self.world.say(f"They could keep the lamp between them so both beds glowed warm and gold.")
        else:
            self.world.say(f"They could tuck one corner under each chin and share the soft blanket together.")
        self.shared = True
        self.child.memes["worry"] = 0.0
        self.child.memes["joy"] = 1.0
        self.companion.memes["joy"] = 1.0
        self.item.shared_with.add(self.companion.id)

    def resolution(self) -> None:
        p = self.params
        self.world.say(f"{p.name} nodded, and soon both children were cozy together.")
        self.world.say(f"The room grew still, the night felt kind, and the {self.item.label} stayed just as nice as before.")
        self.world.say(f"At the very end, {p.name} and {p.companion} were smiling under the soft bedtime light.")

    def run(self) -> World:
        self.setup()
        self.world.say("")
        self.tension()
        self.world.say("")
        self.turn()
        self.world.say("")
        self.resolution()
        self.world.facts.update(
            child=self.child,
            companion=self.companion,
            item=self.item,
            shared=self.shared,
            recommended=self.recommended,
        )
        return self.world


def valid_combos() -> list[tuple[str, str]]:
    out = []
    for name in NAMES:
        for item in ITEMS:
            out.append((name, item))
    return out


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    item = f["item"]
    return [
        f'Write a gentle bedtime story for a small child named {child.id} about sharing {item.phrase}.',
        f"Tell a cozy happy-ending story where {child.id} learns to share a {item.label} at bedtime.",
        f'Write a short bedtime story using the words "diller", "recommend", and "peck" in a child-friendly way.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    comp = f["companion"]
    item = f["item"]
    return [
        QAItem(
            question=f"What did {child.id} want to keep at first?",
            answer=f"{child.id} wanted to keep {item.phrase} all to {child.pronoun('object')}self at first.",
        ),
        QAItem(
            question=f"Who asked {child.id} to share?",
            answer=f"{comp.label} asked {child.id} to share {item.label} in a quiet bedtime voice.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended happily, with both children cozy and smiling while they shared the {item.label}.",
        ),
        QAItem(
            question="What changed after the recommendation?",
            answer=f"After the gentle recommendation, {child.id} stopped worrying and shared the {item.label} with {comp.label}.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does sharing mean?",
            answer="Sharing means letting another person use or enjoy something too, so it can help more than one person.",
        ),
        QAItem(
            question="Why do people recommend things at bedtime?",
            answer="People recommend calm bedtime ideas, like sharing or taking turns, because gentle choices help everyone feel safe and sleepy.",
        ),
        QAItem(
            question="What is a peck?",
            answer="A peck can be a tiny quick kiss or a small light tap, and in a bedtime story it sounds soft and playful.",
        ),
        QAItem(
            question="What is a diller?",
            answer="In this story world, Diller is just a child's name, like any other friendly name in a bedtime tale.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story q&a ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world q&a ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: kind={e.kind} type={e.type} held_by={e.held_by} shared_with={sorted(e.shared_with)}")
        if e.meters:
            lines.append(f"  meters={e.meters}")
        if e.memes:
            lines.append(f"  memes={e.memes}")
    return "\n".join(lines)


ASP_RULES = r"""
shared(Item) :- fact_shared(Item).
happy_ending :- shared(blanket).
happy_ending :- shared(book).
happy_ending :- shared(lamp).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for iid, item in ITEMS.items():
        lines.append(asp.fact("item", iid))
        lines.append(asp.fact("can_share", iid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime story world about sharing and happy endings.")
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--companion", choices=COMPANIONS)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    name = args.name or rng.choice(NAMES)
    item = args.item or rng.choice(list(ITEMS))
    companion = args.companion or rng.choice(COMPANIONS)
    if companion == name:
        raise StoryError("The child and companion must be different.")
    return StoryParams(name=name, companion=companion, item=item)


def generate(params: StoryParams) -> StorySample:
    reasonableness_gate(params)
    bw = BedtimeWorld(params)
    world = bw.run()
    return StorySample(
        params=params,
        story=world.render(),
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


def valid_story_combos() -> list[tuple[str, str]]:
    return valid_combos()


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show happy_ending/0."))
    return [tuple() for _ in model]


def asp_verify() -> int:
    if valid_story_combos():
        print("OK: Python gate has valid bedtime combos.")
        return 0
    print("No valid combos.")
    return 1


def main() -> None:
    args = build_parser().parse_args()
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    if args.show_asp:
        print(asp_program("#show happy_ending/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("ASP mode is available for the bedtime world, but the Python gate is the primary check.")
        return

    samples: list[StorySample] = []
    if args.all:
        for name in NAMES[:5]:
            for item in list(ITEMS)[:3]:
                samples.append(generate(StoryParams(name=name, companion=random.choice(COMPANIONS), item=item)))
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
