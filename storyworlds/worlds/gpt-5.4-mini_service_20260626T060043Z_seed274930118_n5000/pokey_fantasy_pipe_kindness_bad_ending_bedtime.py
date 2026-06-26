#!/usr/bin/env python3
"""
Storyworld: pokey fantasy pipe kindness bad ending bedtime.

A small bedtime-story simulation about a child, a pokey fantasy pipe,
a gentle act of kindness, and a careful but sad ending.
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

THEME_WORDS = ("pokey", "fantasy", "pipe")
DEFAULT_SEED = 274930118

NAMES = ["Mina", "Toby", "Lila", "Pip", "Nico", "Wren"]
GUARDIANS = ["mother", "father", "grandmother", "grandfather"]
TRAITS = ["sleepy", "gentle", "brave", "curious", "quiet"]


@dataclass
class StoryParams:
    name: str
    guardian: str
    trait: str
    place: str = "the bedtime room"
    seed: Optional[int] = None


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    type: str = "thing"
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "grandmother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "grandfather", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Pipe:
    name: str = "silver pipe"
    pokey: bool = True
    fantasy: bool = True
    warmth: int = 0
    hush: int = 0
    listens: bool = False
    broken: bool = False


class World:
    def __init__(self, place: str) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.pipe = Pipe()
        self.lines: list[str] = []
        self.facts: dict[str, object] = {}
        self.fired: set[str] = set()

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def para(self) -> None:
        if self.lines and self.lines[-1] != "":
            self.lines.append("")

    def render(self) -> str:
        out: list[str] = []
        buf: list[str] = []
        for line in self.lines:
            if line == "":
                if buf:
                    out.append(" ".join(buf))
                    buf = []
            else:
                buf.append(line)
        if buf:
            out.append(" ".join(buf))
        return "\n\n".join(out)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime storyworld: pokey fantasy pipe kindness bad ending.")
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--guardian", choices=GUARDIANS)
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    name = args.name or rng.choice(NAMES)
    guardian = args.guardian or rng.choice(GUARDIANS)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(name=name, guardian=guardian, trait=trait)


def _subject_name(world: World) -> Entity:
    return world.entities["child"]


def tell(params: StoryParams) -> World:
    world = World(place="the bedtime room")
    child = world.add(Entity(id="child", kind="character", label=params.name, type="child"))
    guardian = world.add(Entity(id="guardian", kind="character", label=f"the {params.guardian}", type=params.guardian))
    pipe = world.pipe

    child.memes["sleepy"] = 1
    child.memes["want"] = 1

    world.say(f"At bedtime, {child.label} was a {params.trait} little child who could not fall asleep.")
    world.say(f"On the quilt lay a pokey fantasy pipe, shining like it had fallen out of a dream.")
    world.say(f"{child.label} whispered, “I want to keep the pipe near me tonight.”")

    world.para()
    pipe.listens = True
    pipe.warmth += 1
    world.say(f"The {params.guardian} sat beside the pillow and spoke with kindness.")
    world.say(f"“We can be gentle with it,” {guardian.pronoun()} said. “It is pokey, but we can wrap it in a soft cloth.”")
    world.say(f"{child.label} helped fold the cloth around the pipe, trying to make it safe for sleepy hands.")
    world.say(f"The pipe grew warm and hush-quiet, as if it liked being treated kindly.")

    world.para()
    pipe.hush += 1
    child.memes["hope"] = 1
    world.say(f"For a little while, the room felt calm. The lamp glowed low, and the fantasy pipe looked almost friendly.")
    world.say(f"But the pipe had one sharp edge that still poked through the cloth.")

    world.para()
    pipe.broken = True
    child.memes["sadness"] = 2
    guardian.meters = {"cleaning": 1}
    world.say(f"When {child.label} rolled over in sleep, the pokey edge snagged the blanket and the cloth slipped away.")
    world.say(f"The pipe fell with a tiny clink and cracked on the floor.")
    world.say(f"{child.label} woke up with tears in {child.pronoun('possessive')} eyes, and the {params.guardian} held {child.pronoun('object')} close.")
    world.say(f"They cleaned up the pieces together, but the fantasy was over, and the room felt sad and very still.")

    world.facts = {
        "child": child,
        "guardian": guardian,
        "pipe": pipe,
        "params": params,
        "ending": "bad",
        "kindness": True,
        "theme_words": THEME_WORDS,
    }
    return world


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    return [
        f'Write a bedtime story for a small child about a pokey fantasy pipe and a kind grownup.',
        f"Tell a gentle story where {p.name} wants to keep a fantasy pipe near bed, and kindness changes the moment.",
        f'Write a soft bedtime tale that includes the words "pokey", "fantasy", and "pipe" and ends with a bad ending.',
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    child = world.facts["child"]
    guardian = world.facts["guardian"]
    pipe = world.facts["pipe"]
    return [
        QAItem(
            question=f"Who was trying to fall asleep in the bedtime room?",
            answer=f"{child.label} was trying to fall asleep in the bedtime room."
        ),
        QAItem(
            question=f"What did {child.label} want to keep near the bed?",
            answer=f"{child.label} wanted to keep the pokey fantasy pipe near the bed."
        ),
        QAItem(
            question=f"How did the {p.guardian} show kindness?",
            answer=f"The {p.guardian} showed kindness by wrapping the pipe in a soft cloth and staying beside {child.label}."
        ),
        QAItem(
            question="What happened at the end of the story?",
            answer="The pipe slipped, cracked on the floor, and the story ended sadly."
        ),
        QAItem(
            question=f"Was the pipe still whole at the end?",
            answer=f"No. The fantasy pipe cracked when it fell, so it was no longer whole."
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does kind help usually sound like?",
            answer="Kind help usually sounds gentle, calm, and careful."
        ),
        QAItem(
            question="What does pokey mean?",
            answer="Pokey means pointy or sharp enough to poke skin or cloth."
        ),
        QAItem(
            question="What is a fantasy thing in a story?",
            answer="A fantasy thing is something magical or dreamlike that could not happen in ordinary life."
        ),
        QAItem(
            question="Why can a pipe be dangerous if it is pokey?",
            answer="A pokey pipe can snag cloth, scratch hands, or break if it falls."
        ),
    ]


def dump_trace(world: World) -> str:
    p = world.facts["params"]
    pipe = world.facts["pipe"]
    child = world.facts["child"]
    guardian = world.facts["guardian"]
    lines = [
        "--- world trace ---",
        f"place: {world.place}",
        f"child: {child.label}, memes={child.memes}",
        f"guardian: {guardian.label}, meters={getattr(guardian, 'meters', {})}",
        f"pipe: pokey={pipe.pokey}, fantasy={pipe.fantasy}, warmth={pipe.warmth}, hush={pipe.hush}, listens={pipe.listens}, broken={pipe.broken}",
        f"params: {p}",
    ]
    return "\n".join(lines)


ASP_RULES = r"""
child_wants_pipe.
kindness_offered :- child_wants_pipe.
pokey_pipe :- pipe.
bad_ending :- pokey_pipe, kindness_offered.
#show child_wants_pipe/0.
#show kindness_offered/0.
#show bad_ending/0.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    return "\n".join([
        asp.fact("pipe"),
        asp.fact("pokey_pipe"),
        asp.fact("fantasy_pipe"),
        asp.fact("child_wants_pipe"),
        asp.fact("kindness_possible"),
    ])


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_models():
    import storyworlds.asp as asp
    return asp.one_model(asp_program())


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp_models()
    atoms = {s.name for s in model}
    expected = {"child_wants_pipe", "kindness_offered", "bad_ending"}
    if atoms >= expected:
        print("OK: ASP model is consistent with the bedtime storyworld.")
        return 0
    print("MISMATCH: ASP model missing expected atoms.")
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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
        for i, p in enumerate(sample.prompts, 1):
            print(f"P{i}: {p}")
        print()
        for item in sample.story_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
        print()
        for item in sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")


CURATED = [
    StoryParams(name="Mina", guardian="mother", trait="gentle"),
    StoryParams(name="Toby", guardian="father", trait="curious"),
    StoryParams(name="Lila", guardian="grandmother", trait="sleepy"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else DEFAULT_SEED
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 30):
            rng = random.Random(base_seed + i)
            i += 1
            params = resolve_params(args, rng)
            params.seed = base_seed + i
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

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
