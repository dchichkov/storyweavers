#!/usr/bin/env python3
"""
A compact storyworld about a carnival fable with a flashback and a lesson learned.

Premise:
A small animal at a carnival wants the brightest prize, but a memory from before
helps them choose wisely, and the ending proves the choice changed them.
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
class Entity:
    id: str
    kind: str = "thing"
    species: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.species in {"fox", "wolf", "mouse", "rabbit", "cat", "bear"}:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Character:
    species: str
    name: str
    trait: str


@dataclass
class Prize:
    id: str
    label: str
    phrase: str
    sparkly: bool = False


@dataclass
class Carnival:
    place: str = "the carnival"
    sounds: str = "music and laughter"
    lights: str = "bright lights"


@dataclass
class StoryParams:
    character: str
    name: str
    trait: str
    prize: str
    seed: Optional[int] = None


CHARACTERS = {
    "fox": Character("fox", "Fenn", "clever"),
    "rabbit": Character("rabbit", "Pip", "quick"),
    "mouse": Character("mouse", "Mina", "small"),
    "cat": Character("cat", "Tess", "curious"),
}

PRIZES = {
    "whistle": Prize("whistle", "golden whistle", "a golden whistle", sparkly=True),
    "balloon": Prize("balloon", "red balloon", "a red balloon"),
    "mask": Prize("mask", "painted mask", "a painted mask", sparkly=True),
    "cookie": Prize("cookie", "sweet cookie", "a sweet cookie"),
}

CARNIVAL = Carnival()
TRAITS = ["curious", "proud", "careful", "restless", "bright-eyed"]


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[str] = set()

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def flashback_text(hero: Entity, prize: Entity) -> str:
    return (
        f"Long ago, {hero.id} had rushed after a shiny thing without thinking, "
        f"and the choice had ended in tears. That memory came back as {hero.id} "
        f"looked at {prize.label}."
    )


def lesson_text(hero: Entity) -> str:
    return (
        f"{hero.id} learned that the brightest prize is not always the best prize. "
        f"Patience could save a happy day."
    )


def tell(params: StoryParams) -> World:
    if params.character not in CHARACTERS:
        raise StoryError("unknown character")
    if params.prize not in PRIZES:
        raise StoryError("unknown prize")

    data = CHARACTERS[params.character]
    prize_cfg = PRIZES[params.prize]
    world = World()

    hero = world.add(Entity(
        id=params.name,
        kind="character",
        species=data.species,
        label=params.name,
        phrase=f"a {params.trait} {data.species}",
        memes={"desire": 0.0, "wisdom": 0.0, "regret": 0.0},
    ))
    prize = world.add(Entity(
        id="prize",
        species="thing",
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        owner=hero.id,
        meters={"value": 1.0 if prize_cfg.sparkly else 0.7},
    ))

    world.say(
        f"At {CARNIVAL.place}, the {CARNIVAL.lights} blinked over the stalls, "
        f"and {CARNIVAL.sounds} floated through the air."
    )
    world.say(
        f"{hero.id} was a {params.trait} {data.species} who loved wandering past the games."
    )
    world.say(
        f"One booth held {prize.phrase}, and {hero.id} wanted it at once."
    )

    world.para()
    world.say(flashback_text(hero, prize))
    hero.memes["regret"] += 1.0
    hero.memes["wisdom"] += 1.0
    world.say(
        f"This time, {hero.id} stopped and listened to that old warning inside."
    )
    world.say(
        f"Instead of grabbing {prize.label}, {hero.id} waited for the game to be played fairly."
    )

    hero.memes["desire"] += 1.0
    world.para()
    world.say(
        f"The game ended well, and {hero.id} won {prize.phrase} only after earning it."
    )
    world.say(
        f"{hero.id} smiled, shared a little cheer with the crowd, and walked away with a lighter heart."
    )
    world.say(lesson_text(hero))

    world.facts.update(
        hero=hero,
        prize=prize,
        character=data,
        prize_cfg=prize_cfg,
        lesson=True,
        flashback=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]
    prize: Entity = f["prize"]
    return [
        f"Write a small fable about {hero.id} at a carnival, using a flashback and a lesson learned.",
        f"Tell a child-friendly story where {hero.id} sees {prize.label} at the carnival and remembers an old mistake.",
        f"Write a short moral tale set at a carnival where a character chooses patience over grabbing.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    prize: Entity = f["prize"]
    return [
        QAItem(
            question=f"What did {hero.id} want at the carnival?",
            answer=f"{hero.id} wanted {prize.phrase}."
        ),
        QAItem(
            question=f"What helped {hero.id} make a better choice?",
            answer=(
                f"A flashback helped {hero.id} remember a time when rushing led to trouble, "
                f"so {hero.id} chose patience."
            ),
        ),
        QAItem(
            question="What lesson did the story teach?",
            answer="It taught that patience is wiser than grabbing the brightest thing right away.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a carnival?",
            answer="A carnival is a lively place with games, music, lights, and prizes.",
        ),
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is a memory from before that helps explain what a character does now.",
        ),
        QAItem(
            question="What does 'lesson learned' mean?",
            answer="A lesson learned is the good idea a character understands after something happens.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts ==",]
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


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for ent in world.entities.values():
        lines.append(
            f"{ent.id}: kind={ent.kind} species={ent.species} meters={ent.meters} memes={ent.memes}"
        )
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Carnival fable storyworld.")
    ap.add_argument("--character", choices=sorted(CHARACTERS))
    ap.add_argument("--name")
    ap.add_argument("--trait", choices=sorted(TRAITS))
    ap.add_argument("--prize", choices=sorted(PRIZES))
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
    character = args.character or rng.choice(sorted(CHARACTERS))
    prize = args.prize or rng.choice(sorted(PRIZES))
    trait = args.trait or rng.choice(TRAITS)
    name = args.name or CHARACTERS[character].name
    return StoryParams(character=character, name=name, trait=trait, prize=prize)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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


ASP_RULES = r"""
story(Character, Prize) :- character(Character), prize(Prize).
flashback_story(Character) :- story(Character, _).
lesson_learned(Character) :- story(Character, _).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for cid in CHARACTERS:
        lines.append(asp.fact("character", cid))
    for pid in PRIZES:
        lines.append(asp.fact("prize", pid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import storyworlds.asp as asp  # lazy, as required
    except Exception as e:
        print(f"ASP unavailable: {e}")
        return 1
    model = asp.one_model(asp_program("#show story/2. #show flashback_story/1. #show lesson_learned/1."))
    atoms = {(sym.name, len(sym.arguments)) for sym in model}
    expected = {("story", 2), ("flashback_story", 1), ("lesson_learned", 1)}
    if atoms >= expected:
        print("OK: ASP twin verified.")
        return 0
    print("MISMATCH: ASP twin failed.")
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show story/2. #show flashback_story/1. #show lesson_learned/1."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for character in sorted(CHARACTERS):
            for prize in sorted(PRIZES):
                params = StoryParams(character=character, name=CHARACTERS[character].name, trait="curious", prize=prize)
                samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
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

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
