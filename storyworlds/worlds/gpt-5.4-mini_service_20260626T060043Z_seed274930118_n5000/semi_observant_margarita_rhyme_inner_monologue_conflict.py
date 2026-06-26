#!/usr/bin/env python3
"""
A nursery-rhyme story world about an observant child, a semi truck, and a small
conflict that ends with a kinder, safer choice.
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


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"dust": 0.0, "stuck": 0.0, "tired": 0.0}
        if not self.memes:
            self.memes = {"curiosity": 0.0, "worry": 0.0, "conflict": 0.0, "joy": 0.0}

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
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


# ---------------------------------------------------------------------------
# Story configuration
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str = "the little market"
    name: str = "Margarita"
    seed: Optional[int] = None


SETTINGS = {
    "market": "the little market",
    "bridge": "the little bridge",
    "lane": "the sunny lane",
    "yard": "the tidy yard",
}

NAMES = ["Margarita", "Miri", "Mina", "Nora", "Tia", "Lola"]
TRAITS = ["observant", "careful", "bright-eyed", "gentle", "curious"]


# ---------------------------------------------------------------------------
# Narration helpers
# ---------------------------------------------------------------------------

def rhyme_line(a: str, b: str) -> str:
    return f"{a} {b}"


def intro(world: World, child: Entity, truck: Entity) -> None:
    world.say(
        f"Little {child.id}, so observant and sweet, "
        f"watched the bright world on skipping feet."
    )
    world.say(
        f"Down rolled a semi, big and gray, "
        f"with a rumble and tumble on its way."
    )


def child_inner_monologue(world: World, child: Entity, truck: Entity) -> None:
    child.memes["curiosity"] += 1
    world.say(
        f"{child.id} thought, 'That semi is huge as a hill; "
        f"if it bumps the gate, it surely will spill.'"
    )


def conflict(world: World, child: Entity, truck: Entity, gate: Entity) -> None:
    child.memes["worry"] += 1
    child.memes["conflict"] += 1
    truck.meters["stuck"] += 1
    gate.meters["shut"] += 1
    world.say(
        f"The semi got stuck by the tiny front gate, "
        f"and {child.id} frowned, for the moment felt late."
    )
    world.say(
        f"{child.id} thought, 'Oh dear, oh dear, what should I do? "
        f"Help the driver, or watch the wheels chew?'"
    )


def turn(world: World, child: Entity, truck: Entity, gate: Entity) -> None:
    child.memes["curiosity"] += 1
    truck.meters["stuck"] -= 1
    truck.meters["dust"] += 1
    gate.meters["shut"] -= 1
    world.say(
        f"{child.id} tapped on the latch with a careful tap, "
        f"and called to the driver with a friendly clap."
    )
    world.say(
        f"'Back up a little, then turn with care; "
        f"there's room for your wheels if you steer with flair.'"
    )
    world.say(
        f"The semi rolled free with a slow, soft whir, "
        f"and all of the dust gave a tiny purr."
    )


def ending(world: World, child: Entity, truck: Entity) -> None:
    child.memes["joy"] += 1
    child.memes["conflict"] = 0.0
    world.say(
        f"Now {child.id} smiled wide by the bright front gate, "
        f"for kindness and patience had fixed the weight."
    )
    world.say(
        f"The semi drove off with a hum and a glow, "
        f"and {child.id} waved goodbye nice and slow."
    )


def tell_story(params: StoryParams) -> World:
    world = World(place=SETTINGS[params.place])
    child = world.add(Entity(id=params.name, kind="character", type="girl"))
    truck = world.add(Entity(id="semi", kind="thing", type="truck", label="semi truck"))
    gate = world.add(Entity(id="gate", kind="thing", type="gate", label="front gate"))

    world.facts.update(child=child, truck=truck, gate=gate, place=world.place)
    intro(world, child, truck)
    world.para()
    child_inner_monologue(world, child, truck)
    conflict(world, child, truck, gate)
    world.para()
    turn(world, child, truck, gate)
    ending(world, child, truck)
    return world


# ---------------------------------------------------------------------------
# Q&A generation
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    return [
        'Write a short nursery-rhyme story about an observant child, a semi truck, and a small problem that gets fixed kindly.',
        f"Tell a gentle rhyming story where {world.facts['child'].id} notices a stuck semi and helps with a careful idea.",
        "Write a child-friendly rhyme with an inner thought, a worry, and a happy ending at a little place.",
    ]


def story_qa(world: World) -> list[QAItem]:
    child = world.facts["child"]
    truck = world.facts["truck"]
    gate = world.facts["gate"]
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"The story is about {child.id}, an observant little child who notices the semi truck and the front gate.",
        ),
        QAItem(
            question=f"What problem did {truck.label} have near the gate?",
            answer=f"The semi truck got stuck by the tiny front gate, so it could not roll forward right away.",
        ),
        QAItem(
            question=f"How did {child.id} help?",
            answer=f"{child.id} called to the driver and suggested backing up a little and turning with care, which freed the semi truck.",
        ),
        QAItem(
            question=f"What changed at the end?",
            answer=f"At the end, the semi truck rolled free, the worry went away, and {child.id} smiled and waved goodbye.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a semi truck?",
            answer="A semi truck is a very big truck that carries heavy things on long roads.",
        ),
        QAItem(
            question="What does observant mean?",
            answer="Observant means noticing little details carefully.",
        ),
        QAItem(
            question="What is a gate?",
            answer="A gate is a part that opens and closes to let people, pets, or vehicles pass through.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story Q&A ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World Q&A ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
child_observant(C) :- child(C).
truck(T) :- semi(T).
problem(T) :- semi(T), stuck(T).
helpful_move(C,T) :- child(C), semi(T), careful(C).
resolved(T) :- problem(T), helpful_move(_,T).
#show child_observant/1.
#show problem/1.
#show resolved/1.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    return "\n".join(
        [
            asp.fact("child", "margarita"),
            asp.fact("semi", "semi"),
            asp.fact("stuck", "semi"),
            asp.fact("careful", "margarita"),
        ]
    )


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program())
    shown = {s.name for s in model}
    expected = {"child_observant", "problem", "resolved"}
    if expected.issubset(shown):
        print("OK: ASP twin produced expected atoms.")
        return 0
    print("MISMATCH: ASP twin did not produce expected atoms.")
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A nursery-rhyme story world with an observant child and a semi truck.")
    ap.add_argument("--place", choices=SETTINGS.keys())
    ap.add_argument("--name", choices=NAMES)
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
    place = args.place or rng.choice(list(SETTINGS.keys()))
    name = args.name or rng.choice(NAMES)
    return StoryParams(place=place, name=name, seed=args.seed)


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program())
        print(f"ASP model atoms: {len(model)}")
        for sym in model:
            print(sym)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        for i, name in enumerate(NAMES[:5]):
            params = StoryParams(place=SETTINGS[list(SETTINGS.keys())[i % len(SETTINGS)]], name=name, seed=base_seed + i)
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
