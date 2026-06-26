#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/chipper_peter_monopoly_seaside_promenade_mystery_to.py
==============================================================================================================================

A small nursery-rhyme-flavored story world about chipper Peter, a seaside
promenade, and a little mystery to solve.

Seed tale:
---
Peter was a chipper little child who loved his Monopoly board. One bright day,
he walked the seaside promenade with a small board game tucked under one arm.
But then a mystery began: one board piece went missing, and Peter could not
start the game. He looked near the rail, by the sweet shop, and by the penny
arcade, until he spotted the missing piece in a shell-lined nook. Peter smiled,
shared the game, and the promenade felt cheerful again.
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

PROMENADE = "the seaside promenade"


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    carried_by: Optional[str] = None
    location: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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


@dataclass
class StoryParams:
    hero: str = "Peter"
    mood: str = "chipper"
    game: str = "Monopoly"
    place: str = PROMENADE
    seed: Optional[int] = None


@dataclass
class Setting:
    place: str
    sights: list[str]


@dataclass
class Mystery:
    problem: str
    clue: str
    hiding_spot: str
    found_sentence: str
    solved_sentence: str


SETTING = Setting(
    place=PROMENADE,
    sights=["the rail", "the sweet shop", "the penny arcade", "a shell-lined nook"],
)

MYSTERY = Mystery(
    problem="one little Monopoly piece was missing",
    clue="tiny shell marks pointed toward a shell-lined nook",
    hiding_spot="a shell-lined nook",
    found_sentence="There, tucked in the shells, was the missing Monopoly piece all neat and snug.",
    solved_sentence="Peter put the piece back, and the game was ready at last.",
)

KNOWLEDGE = {
    "monopoly": [
        QAItem(
            question="What is Monopoly?",
            answer="Monopoly is a board game where players move pieces around a board and try to buy places and collect money.",
        )
    ],
    "promenade": [
        QAItem(
            question="What is a promenade?",
            answer="A promenade is a walkway by the sea where people can stroll, look at the water, and enjoy the fresh air.",
        )
    ],
    "mystery": [
        QAItem(
            question="What is a mystery?",
            answer="A mystery is something unknown that people try to figure out by looking for clues.",
        )
    ],
}


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Nursery-rhyme story world about Peter, Monopoly, and a seaside mystery.")
    ap.add_argument("--name", default="Peter")
    ap.add_argument("--mood", choices=["chipper", "bright", "cheerful"], default="chipper")
    ap.add_argument("--game", default="Monopoly")
    ap.add_argument("--place", default=PROMENADE)
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
    place = args.place or PROMENADE
    if place != PROMENADE:
        raise StoryError("This world only tells stories at the seaside promenade.")
    if args.game.lower() != "monopoly":
        raise StoryError("This story world is built around Monopoly.")
    return StoryParams(
        hero=args.name or "Peter",
        mood=args.mood or "chipper",
        game="Monopoly",
        place=place,
    )


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("setting", "promenade"),
        asp.fact("place_name", "seaside_promenade"),
        asp.fact("hero", "peter"),
        asp.fact("game", "monopoly"),
        asp.fact("mood", "chipper"),
        asp.fact("mystery", "missing_piece"),
        asp.fact("clue", "shell_marks"),
        asp.fact("hiding_spot", "shell_line_nook"),
        asp.fact("solves", "peter", "missing_piece"),
    ]
    return "\n".join(lines)


ASP_RULES = r"""
#show valid_story/1.

valid_story(peter) :- hero(peter), game(monopoly), setting(promenade), mystery(missing_piece), solves(peter, missing_piece).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/1."))
    found = sorted(set(asp.atoms(model, "valid_story")))
    expected = [("peter",)]
    if found == expected:
        print("OK: ASP parity verified.")
        return 0
    print("MISMATCH between ASP and Python:")
    print("  ASP:", found)
    print("  PY :", expected)
    return 1


def solve_mystery(world: World, hero: Entity, game: Entity) -> None:
    hero.memes["curious"] = hero.memes.get("curious", 0) + 1
    world.say(
        f"{hero.id} was a {hero.memes.get('mood_word', 'chipper')} little child, and {hero.pronoun().capitalize()} loved {game.label}."
    )
    world.say(
        f"One day {hero.id} went to {world.facts['setting'].place} with a {game.label} tucked under {hero.pronoun('possessive')} arm."
    )
    world.say(f"But oh dear, a mystery appeared: {MYSTERY.problem}.")
    world.para()
    world.say(
        f"{hero.id} looked by {SETTING.sights[0]}, then by {SETTING.sights[1]}, and then by {SETTING.sights[2]}."
    )
    hero.meters["search"] = hero.meters.get("search", 0) + 1
    world.say(f"{hero.id} stayed chipper, because a mystery is best solved step by step.")
    world.say(f"At last, {MYSTERY.clue}.")
    world.say(MYSTERY.found_sentence)
    game.meters["complete"] = 1
    hero.memes["joy"] = hero.memes.get("joy", 0) + 1
    world.para()
    world.say(
        f"{MYSTERY.solved_sentence} Soon {hero.id} could play {game.label} beside the sea, and the promenade shone bright and merry."
    )


def generate_world(params: StoryParams) -> World:
    world = World()
    hero = world.add(Entity(id=params.hero, kind="character", type="boy", label=params.hero))
    game = world.add(Entity(id="monopoly_game", type="game", label=params.game, phrase=f"a {params.game} board"))
    world.facts["setting"] = SETTING
    hero.memes["mood_word"] = params.mood
    hero.memes["joy"] = 1
    solve_mystery(world, hero, game)
    world.facts.update(hero=hero, game=game, mystery=MYSTERY, params=params)
    return world


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    return [
        "Write a gentle nursery-rhyme story about Peter, Monopoly, and a mystery to solve at the seaside promenade.",
        f"Tell a chipper story where {p.hero} loses part of {p.game} and finds it by following clues along the promenade.",
        "Make the story sound bright and sing-song, with a small problem, a clue, and a happy ending by the sea.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"The story is about {p.hero}, a {p.mood} little child who loves {p.game}.",
        ),
        QAItem(
            question=f"What mystery had to be solved at {p.place}?",
            answer=f"The mystery was that one little Monopoly piece was missing at {p.place}.",
        ),
        QAItem(
            question="Where did Peter find the missing piece?",
            answer=f"Peter found it in {MYSTERY.hiding_spot}, after following shell marks.",
        ),
        QAItem(
            question="How did the story end?",
            answer="The missing piece was put back, Peter could play again, and the promenade felt cheerful and bright.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return list(KNOWLEDGE["monopoly"]) + list(KNOWLEDGE["promenade"]) + list(KNOWLEDGE["mystery"])


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {prompt}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World knowledge questions ==")
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
        lines.append(f"  {e.id:12} ({e.type}) {' '.join(bits)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = generate_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/1."))
        print(sorted(set(asp.atoms(model, "valid_story"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        params = StoryParams(hero="Peter", mood="chipper", game="Monopoly", place=PROMENADE, seed=base_seed)
        samples = [generate(params)]
    else:
        for i in range(max(1, args.n)):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
