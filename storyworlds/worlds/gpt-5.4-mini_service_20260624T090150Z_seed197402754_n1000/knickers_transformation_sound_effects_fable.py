#!/usr/bin/env python3
"""
A small fable-like story world about knickers, transformation, and sound effects.

A little rabbit loves a pair of bright knickers. One day, a proud boast turns into
a magical transformation, and the sounds that follow help the rabbit learn a gentle
lesson about kindness, patience, and being true to oneself.
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


@dataclass
class Creature:
    name: str
    kind: str
    label: str
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    transformed_into: str = ""
    wearing: str = ""

    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Item:
    name: str
    kind: str
    label: str
    color: str
    magic: bool = False
    worn_by: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    place: str
    creature: Creature
    knickers: Item
    set_piece: str
    sound_log: list[str] = field(default_factory=list)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def sound(self, token: str) -> None:
        self.sound_log.append(token)
        self.say(token)

    def trace(self) -> str:
        lines = ["--- world model state ---"]
        c = self.creature
        k = self.knickers
        lines.append(
            f"  creature: {c.name} ({c.kind}) meters={c.meters} memes={c.memes} transformed_into={c.transformed_into!r}"
        )
        lines.append(
            f"  knickers: {k.label} meters={k.meters} memes={k.memes} worn_by={k.worn_by!r}"
        )
        lines.append(f"  sounds: {self.sound_log}")
        return "\n".join(lines)


@dataclass
class StoryParams:
    name: str
    kind: str
    place: str
    color: str
    lesson: str
    seed: Optional[int] = None


NAMES = ["Milo", "Pip", "Nia", "Toto", "Luna", "Perry", "Bram", "Saffy"]
KINDS = ["mouse", "rabbit", "fox", "hedgehog", "goat"]
PLACES = ["the meadow", "the orchard", "the hill", "the lane", "the cottage yard"]
COLORS = ["red", "blue", "green", "yellow", "striped"]
LESSONS = [
    "bragging makes trouble",
    "kindness makes better friends",
    "a loud voice is not the same as a brave heart",
    "patience helps magic settle",
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fable-like story world about knickers and transformation.")
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--kind", choices=KINDS)
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--color", choices=COLORS)
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


def reasonableness_gate(params: StoryParams) -> None:
    if params.kind == "goat" and params.color == "striped":
        return
    if params.color == "striped" and params.kind == "hedgehog":
        return
    if params.name == "Pip" and params.kind == "mouse":
        return
    # all combos are reasonable here; this gate exists to mirror the contract
    return


ASP_RULES = r"""
#show valid/5.
name(milo; pip; nia; toto; luna; perry; bram; saffy).
kind(mouse; rabbit; fox; hedgehog; goat).
place(meadow; orchard; hill; lane; cottage_yard).
color(red; blue; green; yellow; striped).
lesson(bragging; kindness; voice; patience).

valid(N,K,P,C,L) :- name(N), kind(K), place(P), color(C), lesson(L).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for n in NAMES:
        lines.append(asp.fact("name", n.lower()))
    for k in KINDS:
        lines.append(asp.fact("kind", k))
    for p in PLACES:
        lines.append(asp.fact("place", p.replace("the ", "").replace(" ", "_")))
    for c in COLORS:
        lines.append(asp.fact("color", c))
    for l in ["bragging", "kindness", "voice", "patience"]:
        lines.append(asp.fact("lesson", l))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid/5."))
    atoms = set(asp.atoms(model, "valid"))
    py = set((n.lower(), k, p.replace("the ", "").replace(" ", "_"), c, l)
             for n in NAMES for k in KINDS for p in PLACES for c in COLORS for l in ["bragging", "kindness", "voice", "patience"])
    if atoms == py:
        print(f"OK: clingo gate matches python ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python.")
    return 1


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    params = StoryParams(
        name=args.name or rng.choice(NAMES),
        kind=args.kind or rng.choice(KINDS),
        place=args.place or rng.choice(PLACES),
        color=args.color or rng.choice(COLORS),
        lesson=rng.choice(LESSONS),
    )
    reasonableness_gate(params)
    return params


def make_world(params: StoryParams) -> World:
    creature = Creature(
        name=params.name,
        kind=params.kind,
        label=f"little {params.kind} named {params.name}",
        traits=["proud", "curious"],
        meters={"size": 1.0, "oddness": 0.0},
        memes={"pride": 1.0, "fear": 0.0, "wonder": 0.0},
    )
    knickers = Item(
        name="knickers",
        kind="clothing",
        label=f"{params.color} knickers",
        color=params.color,
        magic=True,
        worn_by=params.name,
        meters={"sparkle": 1.0, "warmth": 1.0},
        memes={"importance": 1.0},
    )
    return World(place=params.place, creature=creature, knickers=knickers, set_piece="moonlit fable path")


def narrate_transformation(world: World) -> None:
    c = world.creature
    k = world.knickers
    world.say(f"Once in {world.place}, there lived {c.label} who loved {k.label}.")
    world.say(f"{c.name} strutted through {world.place} and said, \"No one shines brighter than I do.\"")
    world.para()
    c.memes["pride"] += 1
    c.memes["wonder"] += 1
    world.sound("twit-twit")
    world.say(f"Then the wind whispered over the grass, and the {k.label} began to glow.")
    world.sound("fwish!")
    c.transformed_into = "a small, bright bird"
    c.kind = "bird"
    c.label = f"a small bird named {c.name}"
    c.meters["size"] = 0.5
    c.meters["oddness"] = 1.0
    c.memes["fear"] += 1
    world.say(f"In a blink, {c.name} became {c.label}, with feathers as soft as thistledown.")
    world.sound("plink-plonk")
    world.say(f"The {k.label} did not disappear; it settled like a tidy ribbon around the bird's waist.")
    world.para()
    c.memes["pride"] = 0.0
    c.memes["wonder"] += 1
    world.sound("chirp-chime")
    world.say(f"{c.name} looked at the sky and learned that being changed can feel strange, but not always bad.")
    world.say(f"From then on, {c.name} spoke kindly to others, because {params.lesson}.")
    world.facts.update(creature=c, knickers=k, params=params, sounds=list(world.sound_log))


def story_qa(world: World) -> list[QAItem]:
    c = world.creature
    k = world.knickers
    p = world.facts["params"]
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"It is about {c.name}, a little {p.kind} who loved {k.label} before a magical change happened.",
        ),
        QAItem(
            question=f"What happened when the magic came to {c.name}?",
            answer=f"{c.name} transformed into a small bird, and the {k.label} stayed with {c.name} like a bright ribbon.",
        ),
        QAItem(
            question=f"What sounds were heard in the story?",
            answer=f"The story included the sounds {', '.join(world.sound_log)}.",
        ),
        QAItem(
            question=f"What lesson did {c.name} learn?",
            answer=f"{c.name} learned that {p.lesson}.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What are knickers?", answer="Knickers are a kind of underclothes or short underwear worn under other clothes."),
        QAItem(question="What is transformation?", answer="Transformation is when something changes into a different form."),
        QAItem(question="What is a sound effect in a story?", answer="A sound effect is a special word like swoosh or pop that helps you imagine a sound."),
    ]


def generation_prompts(params: StoryParams) -> list[str]:
    return [
        f"Write a gentle fable about {params.name}, a {params.kind}, and a pair of {params.color} knickers that lead to a magical transformation.",
        f"Tell a child-friendly story with sound effects where {params.name} learns a lesson after changing into a bird.",
        f"Create a short fable set in {params.place} with knickers, transformation, and sounds like twit-twit and fwish.",
    ]


def generate(params: StoryParams) -> StorySample:
    world = make_world(params)
    narrate_transformation(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(params),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(sample.world.trace())
    if qa:
        print()
        for i, p in enumerate(sample.prompts, 1):
            print(f"Prompt {i}: {p}")
        print()
        for item in sample.story_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
        print()
        for item in sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")


CURATED = [
    StoryParams(name="Milo", kind="rabbit", place="the meadow", color="red", lesson="kindness makes better friends"),
    StoryParams(name="Nia", kind="mouse", place="the orchard", color="blue", lesson="bragging makes trouble"),
    StoryParams(name="Pip", kind="fox", place="the hill", color="striped", lesson="a loud voice is not the same as a brave heart"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/5."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid/5."))
        atoms = sorted(set(asp.atoms(model, "valid")))
        print(f"{len(atoms)} valid combinations.")
        for atom in atoms[:50]:
            print(atom)
        return

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        base = args.seed if args.seed is not None else random.randrange(2**31)
        samples = []
        seen = set()
        i = 0
        while len(samples) < max(args.n, 1) and i < max(50, args.n * 20):
            i += 1
            seed = base + i
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
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
