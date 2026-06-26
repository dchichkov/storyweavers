#!/usr/bin/env python3
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


@dataclass
class Thing:
    id: str
    kind: str
    label: str
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    safe: bool = True
    locked: bool = False
    handled_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class StoryParams:
    seed: Optional[int] = None
    child_name: str = "Mina"
    parent_name: str = "Mom"
    place: str = "the attic"
    magic: str = "gentle light"
    object_kind: str = "cocaine"
    helper_kind: str = "glow"
    mood: str = "curious"


@dataclass
class World:
    params: StoryParams
    entities: dict[str, Thing] = field(default_factory=dict)
    story_bits: list[str] = field(default_factory=list)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def add(self, thing: Thing) -> Thing:
        self.entities[thing.id] = thing
        return thing

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


ASP_RULES = r"""
% Cocaine is unsafe when a child can reach it.
unsafe(item) :- cocaine(item), reachable_by_child(item).

% Magic may make the item safe by locking it away.
resolved(item) :- unsafe(item), locked(item), not reachable_by_child(item).

#show unsafe/1.
#show resolved/1.
"""


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("cocaine", "packet"),
        asp.fact("reachable_by_child", "packet"),
        asp.fact("locked", "packet"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming magic storyworld with a careful cocaine-themed safety turn.")
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
    return StoryParams(
        seed=args.seed,
        child_name=rng.choice(["Mina", "Jules", "Pip", "Nora"]),
        parent_name=rng.choice(["Mom", "Dad", "Grandma"]),
        place=rng.choice(["the attic", "the hallway closet", "the garage shelf"]),
        magic=rng.choice(["gentle light", "tiny sparkles", "a warm glow"]),
        object_kind="cocaine",
        helper_kind=rng.choice(["glow", "lock", "wrap"]),
        mood=rng.choice(["curious", "careful", "soft"]),
    )


def generate(params: StoryParams) -> StorySample:
    world = World(params=params)

    child = world.add(Thing(id="child", kind="character", label=params.child_name, owner=params.child_name))
    parent = world.add(Thing(id="parent", kind="character", label=params.parent_name, owner=params.parent_name))
    packet = world.add(Thing(id="packet", kind="thing", label="a small packet labeled cocaine", safe=False, locked=False))
    box = world.add(Thing(id="box", kind="thing", label="a little wooden box", safe=True, locked=True))

    child.memes["curiosity"] = 1.0
    parent.memes["care"] = 1.0
    packet.meters["danger"] = 1.0

    world.say(
        f"{params.child_name} was a {params.mood} child who liked looking at old things with {params.parent_name}."
    )
    world.say(
        f"One afternoon, they were in {params.place}, where a dusty shelf held {packet.label}."
    )
    world.say(
        f"{params.child_name} leaned close, but {params.parent_name} gently said, "
        f'"That is cocaine, and it is not for children."'
    )
    world.para()
    world.say(
        f"{params.parent_name} lifted a hand, and {params.magic} drifted over the packet like a soft blanket."
    )
    packet.locked = True
    packet.handled_by = params.parent_name
    box.handled_by = params.parent_name
    world.say(
        f"The little packet was sealed inside {box.label}, and the box clicked shut with a tiny, safe sound."
    )
    world.say(
        f"Then {params.parent_name} called for grown-up help, while {params.child_name} carried out the empty paper scraps."
    )
    world.para()
    world.say(
        f"After that, {params.child_name} and {params.parent_name} made hot cocoa together."
    )
    world.say(
        f"The cocoa steamed in two mugs, and the warm kitchen felt brighter than the dusty shelf ever had."
    )

    world.facts.update(child=child, parent=parent, packet=packet, box=box, params=params)
    story = world.render()
    prompts = [
        "Write a heartwarming story about a child and a parent who find something unsafe and use gentle magic to keep everyone safe.",
        "Tell a simple story where the word cocaine appears in a careful, child-friendly way and the ending feels warm and kind.",
    ]
    story_qa = [
        QAItem(
            question="What did the parent say the packet was?",
            answer="The parent said it was cocaine and that it was not for children.",
        ),
        QAItem(
            question="How did the magic help?",
            answer="The magic helped seal the packet inside a little wooden box so it could be kept safe.",
        ),
        QAItem(
            question="What did the child and parent do at the end?",
            answer="They made hot cocoa together and sat in the warm kitchen after everything was safely put away.",
        ),
    ]
    world_qa = [
        QAItem(
            question="What should a child do if they find something unsafe?",
            answer="A child should stay away from it and tell a trusted grown-up right away.",
        ),
        QAItem(
            question="What is a safe choice when something might be dangerous?",
            answer="A safe choice is to let a grown-up handle it and keep your hands back.",
        ),
    ]
    return StorySample(params=params, story=story, prompts=prompts, story_qa=story_qa, world_qa=world_qa, world=world)


def format_qa(sample: StorySample) -> str:
    out = ["== Prompts =="]
    for p in sample.prompts:
        out.append(p)
    out.append("")
    out.append("== Story QA ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== World QA ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: {e.label} safe={e.safe} locked={e.locked} handled_by={e.handled_by}")
    return "\n".join(lines)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show unsafe/1.\n#show resolved/1."))
    atoms = set((s.name, tuple(a.string if a.type == s.type.String else a.number if a.type == s.type.Number else a.name for a in s.arguments)) for s in model)
    expected = {("unsafe", ("packet",))}
    if atoms == expected:
        print("OK: ASP twin matches Python safety model.")
        return 0
    print("MISMATCH")
    print(sorted(atoms))
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show unsafe/1.\n#show resolved/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show unsafe/1.\n#show resolved/1."))
        print(sorted((s.name, tuple(a.string if a.type == s.type.String else a.number if a.type == s.type.Number else a.name for a in s.arguments)) for s in model))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    for i in range(args.n if not args.all else 1):
        rng = random.Random(base_seed + i)
        params = resolve_params(args, rng)
        sample = generate(params)
        samples.append(sample)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], ensure_ascii=False, indent=2))
        return

    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {i+1}" if len(samples) > 1 else "")
        if i + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
