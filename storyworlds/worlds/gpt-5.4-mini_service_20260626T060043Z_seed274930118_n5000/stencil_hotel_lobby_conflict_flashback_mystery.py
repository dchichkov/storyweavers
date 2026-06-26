#!/usr/bin/env python3
"""
A small story world: a hotel lobby mystery built around a stencil, conflict,
and a flashback.

Seed tale premise:
A child notices strange repeating marks in a hotel lobby. An argument starts
over whether the marks mean trouble. A flashback reminds the child of a stencil
used in art class. The mystery resolves when the marks are traced to a hotel
sign and the lobby becomes calm again.
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
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the hotel lobby"
    affords: set[str] = field(default_factory=set)


@dataclass
class Mystery:
    id: str
    clue: str
    reveal: str
    flashback_trigger: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    mystery: str
    name: str
    gender: str
    companion: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.weather = ""
        self.fired: set[tuple] = set()

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


def _n(word: str, count: int) -> str:
    return word if count == 1 else word + "s"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Story world: hotel lobby mystery with a stencil and a flashback.")
    ap.add_argument("--mystery", choices=sorted(MYSTERIES))
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--companion", choices=["mother", "father"])
    ap.add_argument("--trait", choices=["curious", "careful", "brave", "quiet", "bright"])
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


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("setting", "hotel_lobby"),
        asp.fact("affords", "hotel_lobby", "stencil"),
        asp.fact("affords", "hotel_lobby", "mystery"),
    ]
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        for t in sorted(m.tags):
            lines.append(asp.fact("tag", mid, t))
    return "\n".join(lines)


ASP_RULES = r"""
mystery_ready(M) :- mystery(M), tag(M, stencil), tag(M, conflict), tag(M, flashback).
#show mystery_ready/1.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show mystery_ready/1."))
    got = set(asp.atoms(model, "mystery_ready"))
    expect = {(mid,) for mid, m in MYSTERIES.items() if {"stencil", "conflict", "flashback"} <= m.tags}
    if got == expect:
        print(f"OK: clingo gate matches Python gate ({len(got)} mysteries).")
        return 0
    print("MISMATCH between clingo and Python gate.")
    print("  clingo:", sorted(got))
    print("  python:", sorted(expect))
    return 1


def reasonableness_gate(mystery: Mystery) -> bool:
    return {"stencil", "conflict", "flashback"} <= mystery.tags


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    choices = [m for m in MYSTERIES if reasonableness_gate(MYSTERIES[m])]
    if args.mystery:
        if args.mystery not in choices:
            raise StoryError("That mystery does not fit the stencil/conflict/flashback pattern.")
        choices = [args.mystery]
    mystery = rng.choice(sorted(choices))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    companion = args.companion or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(mystery=mystery, name=name, gender=gender, companion=companion, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = World(SETTING)
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender))
    companion = world.add(Entity(id="companion", kind="character", type=params.companion, label=f"the {params.companion}"))
    mystery = MYSTERIES[params.mystery]
    clue = world.add(Entity(id="clue", type="thing", label="stencil mark", phrase="a row of neat stencil marks"))
    tool = world.add(Entity(id="stencil", type="thing", label="stencil", phrase="a cardboard stencil"))
    sign = world.add(Entity(id="sign", type="thing", label="lobby sign", phrase="a painted lobby sign"))
    world.facts.update(hero=hero, companion=companion, mystery=mystery, clue=clue, tool=tool, sign=sign)

    hero.memes["curiosity"] = 1
    world.say(f"{hero.id} was a {params.trait} {params.gender} who noticed small details.")
    world.say(f"One afternoon, {hero.id} stood in {SETTING.place} and spotted {mystery.clue}.")
    world.say(f"The marks looked odd, and that made {hero.id}'s mind feel full of questions.")

    world.para()
    hero.memes["conflict"] = 1
    companion.memes["worry"] = 1
    world.say(f"{hero.id} thought the marks might mean someone had caused trouble.")
    world.say(f"{hero.pronoun('possessive').capitalize()} {params.companion} disagreed, and the two of them began to argue softly near the front desk.")
    world.say(f"{mystery.reveal.split('.')[0]}.")
    world.say(f"The lobby felt tense, like everyone was waiting to learn the truth.")

    world.para()
    hero.memes["flashback"] = 1
    world.say(f"Then {hero.id} had a flashback to art class, where a teacher had pressed paint through a {tool.label}.")
    world.say(f"In the memory, the same tiny shapes had made a pattern again and again.")
    world.say(f"{hero.id} looked back at the wall and realized the marks were not a warning at all.")

    world.para()
    hero.memes["conflict"] = 0
    companion.memes["worry"] = 0
    world.say(f"The mystery was simple: the marks came from a stencil used to guide the fresh lobby sign.")
    world.say(f"A hotel worker had been touching up the letters, and {sign.label} now shone clean and bright above the chairs.")
    world.say(f"{hero.id} smiled, and {params.companion} did too, because the strange clue had turned into an ordinary answer.")
    world.say(f"By the end, {hero.id} was calmer, the lobby was quiet again, and the little stencil mark story had a clear ending.")

    world.facts["resolved"] = True
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    mystery = f["mystery"]
    return [
        f'Write a short mystery story for a child in a hotel lobby that includes the word "{mystery.id}".',
        f"Tell a gentle story where {hero.id} sees a clue, feels conflict, remembers a flashback, and learns what the stencil means.",
        f'Write a child-friendly mystery set in a hotel lobby with a stencil clue and a calm ending.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    companion = f["companion"]
    mystery = f["mystery"]
    return [
        QAItem(
            question=f"What did {hero.id} notice in the hotel lobby?",
            answer=f"{hero.id} noticed {mystery.clue} in {SETTING.place}.",
        ),
        QAItem(
            question=f"Why did {hero.id} and {companion.label} have conflict?",
            answer=f"They argued because {hero.id} thought the clue might mean trouble, while {companion.label} wanted to wait and look again.",
        ),
        QAItem(
            question=f"What flashback helped {hero.id} solve the mystery?",
            answer=f"{hero.id} remembered art class and a teacher using a {f['tool'].label}. That memory showed that the strange marks were made with a stencil.",
        ),
        QAItem(
            question=f"What was the real answer to the mystery?",
            answer=f"The marks came from a stencil used to help paint the lobby sign, so the clue was harmless and the lobby stayed neat.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a stencil?",
            answer="A stencil is a cut-out tool that helps you make the same shape or letter again and again.",
        ),
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is when a story briefly goes back to something that happened earlier, like a memory.",
        ),
        QAItem(
            question="What is a hotel lobby?",
            answer="A hotel lobby is the front waiting area in a hotel, where people check in and sit down.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
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


GIRL_NAMES = ["Maya", "Nora", "Lily", "Zoe", "Ava", "Mina"]
BOY_NAMES = ["Leo", "Noah", "Eli", "Finn", "Theo", "Max"]
TRAITS = ["curious", "careful", "brave", "quiet", "bright"]


MYSTERIES = {
    "stencil_sign": Mystery(
        id="stencil",
        clue="a row of neat stencil marks near the wall",
        reveal="The marks were not a secret code; they were guide marks for a sign painter",
        flashback_trigger="stencil",
        tags={"stencil", "conflict", "flashback", "mystery"},
    ),
    "stencil_tiles": Mystery(
        id="stencil",
        clue="tiny repeating shapes on the lobby floor tiles",
        reveal="The shapes were part of a decorative stencil used for repairs",
        flashback_trigger="stencil",
        tags={"stencil", "conflict", "flashback", "mystery"},
    ),
}


SETTING = Setting(place="the hotel lobby", affords={"stencil", "mystery"})


def valid_mysteries() -> list[str]:
    return [m for m, v in MYSTERIES.items() if reasonableness_gate(v)]


def generate_story(params: StoryParams) -> StorySample:
    return generate(params)


def asp_valid_mysteries() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show mystery_ready/1."))
    return sorted(set(asp.atoms(model, "mystery_ready")))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show mystery_ready/1."))
        return
    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        items = asp_valid_mysteries()
        print(f"{len(items)} compatible mysteries:")
        for (mid,) in items:
            print(f"  {mid}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for m in valid_mysteries():
            p = StoryParams(
                mystery=m,
                name="Mia",
                gender="girl",
                companion="mother",
                trait="curious",
                seed=base_seed,
            )
            samples.append(generate_story(p))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
                return
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
        header = f"### variant {i + 1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
