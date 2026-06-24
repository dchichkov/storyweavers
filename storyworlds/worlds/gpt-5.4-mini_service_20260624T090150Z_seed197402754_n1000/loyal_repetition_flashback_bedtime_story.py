#!/usr/bin/env python3
"""
A small bedtime-story world about a child, a loyal companion, a repeated bedtime
routine, and a gentle flashback that explains why the bond matters.
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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class World:
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    lines: list[str] = field(default_factory=list)
    facts: dict = field(default_factory=dict)

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def render(self) -> str:
        return " ".join(self.lines)

    def trace(self) -> str:
        out = ["--- world model state ---"]
        for e in self.entities.values():
            bits = []
            if e.meters:
                bits.append(f"meters={e.meters}")
            if e.memes:
                bits.append(f"memes={e.memes}")
            out.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
        return "\n".join(out)


@dataclass
class StoryParams:
    child_name: str
    child_type: str
    parent_type: str
    companion_name: str
    companion_type: str
    room: str
    seed: Optional[int] = None


CHILD_NAMES = ["Mia", "Noah", "Lily", "Theo", "Ava", "Ben"]
COMPANIONS = [
    ("Pip", "dog"),
    ("Milo", "cat"),
    ("Bunny", "rabbit"),
    ("Star", "stuffed bear"),
]
ROOMS = ["nursery", "bedroom", "small room", "cozy room"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime story world with loyalty, repetition, and flashback.")
    ap.add_argument("--name", choices=CHILD_NAMES)
    ap.add_argument("--companion")
    ap.add_argument("--room", choices=ROOMS)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    name = args.name or rng.choice(CHILD_NAMES)
    room = args.room or rng.choice(ROOMS)
    if args.companion:
        comp_name = args.companion
        comp_type = "dog"
    else:
        comp_name, comp_type = rng.choice(COMPANIONS)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(
        child_name=name,
        child_type="girl" if name in {"Mia", "Lily", "Ava"} else "boy",
        parent_type=parent,
        companion_name=comp_name,
        companion_type=comp_type,
        room=room,
    )


def generate_world(params: StoryParams) -> World:
    w = World(place=params.room)
    child = w.add(Entity(id="child", kind="character", type=params.child_type, label=params.child_name))
    parent = w.add(Entity(id="parent", kind="character", type=params.parent_type, label=f"the {params.parent_type}"))
    comp = w.add(Entity(id="companion", kind="character", type=params.companion_type, label=params.companion_name))
    bed = w.add(Entity(id="bed", type="bed", label="bed", phrase="a soft bed"))
    blanket = w.add(Entity(id="blanket", type="blanket", label="blanket", phrase="a warm blanket", owner=child.id))

    child.memes["sleepy"] = 1
    comp.memes["loyal"] = 1
    parent.memes["gentle"] = 1
    bed.meters["soft"] = 1
    blanket.meters["warm"] = 1

    w.say(f"{params.child_name} lived in a {params.room} and got sleepy when the sky turned dark.")
    w.say(f"Each night, {params.child_name} whispered, 'Good night, {params.companion_name}.'")
    w.say(f"{params.companion_name} stayed close, because {params.companion_name} was loyal and never wandered off.")

    w.say(f"Then came bedtime again.")
    w.say(f"Again, {params.child_name} climbed into bed.")
    w.say(f"Again, {params.companion_name} curled beside the bed.")
    w.say(f"Again, {params.parent_type} tucked in the warm blanket and dimmed the light.")

    child.memes["comfort"] = 1
    comp.memes["loyal"] = 2
    parent.memes["calm"] = 1

    w.say(f"{params.child_name} smiled, because the same kind hands and the same loyal friend made the room feel safe.")

    w.say(f"That made {params.child_name} remember an old night when a storm tapped on the window.")
    w.say(f"Back then, {params.companion_name} had pressed close and waited until the thunder passed.")
    w.say(f"So tonight felt easy by comparison, and the memory made the present feel even kinder.")

    w.say(f"{params.child_name} yawned, hugged {params.companion_name}, and drifted into sleep.")
    w.say(f"{params.companion_name} stayed right there, loyal and still, while the room grew quiet.")

    w.facts.update(child=child, parent=parent, companion=comp, bed=bed, blanket=blanket)
    return w


def generation_prompts(world: World) -> list[str]:
    p = world.facts["child"]
    c = world.facts["companion"]
    return [
        f"Write a bedtime story about {p.label} and a loyal friend named {c.label}.",
        f"Tell a gentle story that repeats bedtime steps and includes a flashback about why {c.label} is trusted.",
        "Write a cozy story for children with repetition, a soft room, and a loyal companion.",
    ]


def story_qa(world: World) -> list[QAItem]:
    c = world.facts["child"]
    comp = world.facts["companion"]
    parent = world.facts["parent"]
    return [
        QAItem(
            question=f"Who was loyal in the story?",
            answer=f"{comp.label} was loyal and stayed close to {c.label} at bedtime.",
        ),
        QAItem(
            question=f"What repeated three times as bedtime came?",
            answer="The story repeated that bedtime came again, the child climbed into bed again, and the companion curled beside the bed again.",
        ),
        QAItem(
            question=f"What old memory came back to {c.label}?",
            answer=f"{c.label} remembered a stormy night when {comp.label} stayed close until the thunder passed.",
        ),
        QAItem(
            question=f"How did the parent help at bedtime?",
            answer=f"The {parent.type} tucked in the blanket and dimmed the light so the room felt safe and calm.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does loyal mean?",
            answer="Loyal means staying by someone's side and not leaving when they need you.",
        ),
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is when a story briefly remembers something that happened earlier.",
        ),
        QAItem(
            question="Why do bedtime routines feel comforting?",
            answer="Bedtime routines feel comforting because the same gentle steps happen in the same calm order every night.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
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
child(X) :- child_name(X).
loyal(C) :- companion(C).
repeated(bedtime) :- bedtime_step(again).
flashback(remember_storm) :- old_night(storm).
safe_end :- loyal(C), flashback(remember_storm).
#show loyal/1.
#show repeated/1.
#show flashback/1.
#show safe_end/0.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    return "\n".join([
        asp.fact("child_name", "child"),
        asp.fact("companion", "companion"),
        asp.fact("bedtime_step", "again"),
        asp.fact("old_night", "storm"),
    ])


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show safe_end/0."))
    ok = any(sym.name == "safe_end" for sym in model)
    if ok:
        print("OK: ASP twin recognizes the loyal flashback bedtime pattern.")
        return 0
    print("MISMATCH: ASP twin did not produce the expected model.")
    return 1


def build_params_list(args: argparse.Namespace, rng: random.Random) -> list[StoryParams]:
    if args.all:
        out = []
        for name in CHILD_NAMES[:3]:
            comp_name, comp_type = COMPANIONS[0]
            out.append(StoryParams(name, "girl" if name in {"Mia", "Lily", "Ava"} else "boy", args.parent or "mother", comp_name, comp_type, args.room or "bedroom"))
        return out
    return [resolve_params(args, rng)]


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(sample.world.trace())
    if qa:
        print()
        print(format_qa(sample))


def generate(params: StoryParams) -> StorySample:
    world = generate_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show safe_end/0."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    params_list = build_params_list(args, random.Random(base_seed))

    samples = []
    for i, params in enumerate(params_list[: max(1, args.n)]):
        params.seed = base_seed + i
        samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {i + 1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
