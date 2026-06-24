#!/usr/bin/env python3
"""
A tiny slice-of-life storyworld about a kid, a baseball game, and a kind,
suspenseful ending where a small RBI can feel triumphant.

The seed words are woven into the world on purpose:
- triumphant
- adjective
- rbi
- Kindness
- Suspense
- Slice of Life
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
# Story model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        mapping = {
            "girl": {"subject": "she", "object": "her", "possessive": "her"},
            "boy": {"subject": "he", "object": "him", "possessive": "his"},
        }
        return mapping.get(self.type, {"subject": "they", "object": "them", "possessive": "their"})[case]

    def it(self) -> str:
        return "them" if self.type.endswith("s") else "it"


@dataclass
class Setting:
    place: str = "the little ball field"
    afford_game: bool = True


@dataclass
class Game:
    name: str
    action: str
    suspense: str
    score_event: str
    outcome_word: str = "triumphant"
    keyword: str = "rbi"


@dataclass
class StoryParams:
    name: str
    gender: str
    parent: str
    friend: str
    place: str
    game: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
# Content registry
# ---------------------------------------------------------------------------
SETTINGS = {
    "ballfield": Setting(place="the little ball field"),
    "park": Setting(place="the park diamond"),
    "backyard": Setting(place="the backyard bases"),
}

GAMES = {
    "baseball": Game(
        name="baseball",
        action="bat the ball",
        suspense="everyone held their breath as the pitcher wound up",
        score_event="a single hit sent a runner home",
        outcome_word="triumphant",
        keyword="rbi",
    ),
}

FRIENDS = ["Maya", "Noah", "Lena", "Eli", "Zoe", "Owen", "Mila", "Theo"]
TRAITS = ["quiet", "curious", "patient", "bright", "careful", "gentle"]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
place(ballfield).
place(park).
place(backyard).

game(baseball).
keyword(baseball,rbi).

compatible(P,G) :- place(P), game(G).

#show compatible/2.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in SETTINGS:
        lines.append(asp.fact("place", p))
    for g in GAMES.values():
        lines.append(asp.fact("game", g.name))
        lines.append(asp.fact("keyword", g.name, g.keyword))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show compatible/2."))
    return sorted(set(asp.atoms(model, "compatible")))


def asp_verify() -> int:
    py = {(p, g) for p in SETTINGS for g in GAMES}
    cl = set(asp_valid())
    if py == cl:
        print(f"OK: clingo gate matches python ({len(py)} combos).")
        return 0
    print("Mismatch:")
    print("only python:", sorted(py - cl))
    print("only clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Simulation
# ---------------------------------------------------------------------------
def tell(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    game = GAMES[params.game]
    world = World(setting)

    hero = world.add(Entity(id=params.name, kind="character", type=params.gender))
    parent = world.add(Entity(id="Parent", kind="character", type=params.parent, label=params.parent))
    friend = world.add(Entity(id=params.friend, kind="character", type="child", label=params.friend))

    hero.memes["hope"] = 1
    hero.memes["kindness"] = 1

    world.say(
        f"{hero.id} was a {random.choice(TRAITS)} child who loved the sound of a ball game "
        f"and the warm smell of grass at {setting.place}."
    )
    world.say(
        f"{hero.pronoun().capitalize()} kept a small adjective card in {hero.pronoun('possessive')} pocket; "
        f"the teacher had asked everyone to pick one word that fit the day."
    )

    world.para()
    world.say(
        f"That afternoon, {hero.id}, {friend.id}, and {hero.pronoun('possessive')} {parent.label} went to {setting.place}."
    )
    world.say(
        f"{game.suspense.capitalize()}, and the score stayed close enough that every swing felt important."
    )
    hero.memes["suspense"] = 1

    world.para()
    world.say(
        f"When {friend.id} missed a pitch, {hero.id} did something kind: {hero.pronoun()} ran over, picked up the bat, "
        f"and said, \"Try again. I've got you.\""
    )
    friend.memes["comforted"] = 1
    hero.memes["kindness"] += 1

    world.say(
        f"The next pitch came fast. {hero.id} swung, the ball rolled fair, and {game.score_event}."
    )
    hero.meters["rbi"] = 1
    hero.memes["relief"] = 1

    world.para()
    world.say(
        f"{hero.pronoun('possessive').capitalize()} {parent.label} smiled so wide it looked almost triumphant."
        f" {hero.id} had not only helped {friend.id}; {hero.pronoun()} had also made the team's little rbi count."
    )
    world.say(
        f"By the time they walked home, the sky was soft and orange, and {hero.id}'s adjective card said "
        f"\"triumphant\"."
    )

    world.facts.update(hero=hero, parent=parent, friend=friend, setting=setting, game=game)
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    game = f["game"]
    return [
        f'Write a gentle slice-of-life story with kindness and suspense that uses the word "{game.keyword}".',
        f"Tell a short story about {hero.id}, a friendly game, and a small triumphant moment.",
        f'Write a child-friendly baseball story that includes the words "adjective" and "{game.keyword}".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    parent = f["parent"]
    friend = f["friend"]
    game = f["game"]
    return [
        QAItem(
            question=f"What kind of day was {hero.id} having at {f['setting'].place}?",
            answer=f"{hero.id} was having a gentle, suspenseful day at {f['setting'].place} with {friend.id} and {parent.label}.",
        ),
        QAItem(
            question=f"Why did the story feel suspenseful before {hero.id} hit the ball?",
            answer=f"It felt suspenseful because the score was close and everyone was waiting to see what would happen next.",
        ),
        QAItem(
            question=f"What kind thing did {hero.id} do for {friend.id}?",
            answer=f"{hero.id} was kind and encouraged {friend.id} after a missed pitch, then helped with the bat.",
        ),
        QAItem(
            question=f"What small baseball success did the story mention?",
            answer=f"The story mentioned a small rbi, when {hero.id}'s hit sent a runner home.",
        ),
        QAItem(
            question=f"What word was written on {hero.id}'s adjective card at the end?",
            answer="The adjective card said \"triumphant.\"",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does rbi mean in baseball?",
            answer="RBI means runs batted in. It is a way to count how a hit helps a runner score.",
        ),
        QAItem(
            question="What is kindness?",
            answer="Kindness means being gentle, helpful, and caring toward someone else.",
        ),
        QAItem(
            question="What is suspense?",
            answer="Suspense is the feeling of waiting nervously to see what will happen next.",
        ),
        QAItem(
            question="What is an adjective?",
            answer="An adjective is a word that describes a person, place, or thing, like \"triumphant\" or \"small.\"",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== story qa ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== world qa ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"{e.id}: {e.kind}/{e.type} " + " ".join(bits))
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Params / generation
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life storyworld: kindness, suspense, and a triumphant rbi.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--game", choices=GAMES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--friend")
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
    if args.place and args.place not in SETTINGS:
        raise StoryError("Unknown place.")
    place = args.place or rng.choice(list(SETTINGS))
    game = args.game or "baseball"
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(["Lily", "Mia", "Noah", "Ben", "Ava", "Leo"])
    parent = args.parent or rng.choice(["mother", "father"])
    friend = args.friend or rng.choice(FRIENDS)
    return StoryParams(name=name, gender=gender, parent=parent, friend=friend, place=place, game=game)


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
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show compatible/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid()
        print(f"{len(combos)} compatible combos:")
        for c in combos:
            print(" ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    if args.all:
        samples = [generate(StoryParams(
            name="Lily", gender="girl", parent="mother", friend="Maya", place=place, game="baseball"
        )) for place in SETTINGS]
    else:
        samples = []
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
            seen.add(sample.story)
            samples.append(sample)
            i += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for idx, sample in enumerate(samples):
        if len(samples) > 1:
            print(f"### variant {idx + 1}")
        emit(sample, trace=args.trace, qa=args.qa)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
