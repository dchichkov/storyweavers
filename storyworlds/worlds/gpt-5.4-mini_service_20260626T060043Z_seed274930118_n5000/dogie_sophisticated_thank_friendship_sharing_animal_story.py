#!/usr/bin/env python3
"""
A small animal story world about a dogie who learns friendship through sharing.

Premise:
A sophisticated little dogie wants a shiny ball. A friend also wants to play
with it. The dogie must choose between keeping the toy and keeping the friend.

World model:
- typed entities with meters and memes
- physical state: who owns the toy, who holds it, who shares it
- emotional state: joy, want, worry, gratitude, friendship
- causal turn: if the toy is held too long, the friend feels left out
- resolution: the dogie shares, says thank you, and friendship grows
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
# Entities and world model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" or "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    held_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"dog", "dogie"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

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
# Parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    name: str
    friend_name: str
    toy: str
    setting: str = "the sunny yard"
    seed: Optional[int] = None


NAMES = ["Milo", "Pip", "Coco", "Toby", "Benny", "Luna", "Daisy", "Poppy"]
TOYS = [
    ("red ball", "a shiny red ball"),
    ("yellow rope", "a bright yellow rope"),
    ("blue ring", "a blue ring toy"),
]
SETTINGS = ["the sunny yard", "the little park", "the quiet garden"]


# ---------------------------------------------------------------------------
# Story helpers
# ---------------------------------------------------------------------------
def _friendship_line(world: World, dogie: Entity, friend: Entity) -> None:
    world.say(
        f"{dogie.id} was a sophisticated little dogie who liked neat paws, tidy "
        f"whiskers, and careful manners."
    )
    world.say(
        f"{dogie.id} had a good friend named {friend.id}, and they loved playing "
        f"together."
    )


def _toy_line(world: World, dogie: Entity, toy: Entity) -> None:
    dogie.memes["want"] = dogie.memes.get("want", 0) + 1
    toy.held_by = dogie.id
    world.say(
        f"One day, {dogie.id} found {toy.phrase} and held it close with a proud little grin."
    )
    world.say(f"{dogie.pronoun().capitalize()} wanted to keep {toy.label} all to {dogie.pronoun('possessive')}self.")


def _turn_line(world: World, dogie: Entity, friend: Entity, toy: Entity) -> None:
    friend.memes["worry"] = friend.memes.get("worry", 0) + 1
    world.say(
        f"But {friend.id} watched from the grass and waited, and waiting made {friend.id} feel lonely."
    )
    world.say(
        f"{dogie.id} noticed the quiet face and felt {dogie.pronoun('possessive')} chest get a little tight."
    )


def _sharing_line(world: World, dogie: Entity, friend: Entity, toy: Entity) -> None:
    dogie.memes["kindness"] = dogie.memes.get("kindness", 0) + 1
    dogie.memes["thank"] = dogie.memes.get("thank", 0) + 1
    friend.memes["joy"] = friend.memes.get("joy", 0) + 1
    dogie.memes["friendship"] = dogie.memes.get("friendship", 0) + 1
    friend.memes["friendship"] = friend.memes.get("friendship", 0) + 1
    toy.held_by = None
    world.say(
        f"Then {dogie.id} smiled, said, \"Let's share,\" and nudged {toy.label} toward {friend.id}."
    )
    world.say(
        f"{friend.id} laughed, said, \"Thank you,\" and the two friends took turns pushing and chasing the toy."
    )
    world.say(
        f"By the end, {dogie.id} was still sophisticated, but now {dogie.pronoun('subject')} was also happy to share."
    )


def build_world(params: StoryParams) -> World:
    world = World()
    dogie = world.add(
        Entity(
            id=params.name,
            kind="character",
            type="dogie",
            label="dogie",
            traits=["sophisticated", "kind"],
            meters={"calm": 1.0},
            memes={"joy": 1.0, "friendship": 1.0},
        )
    )
    friend = world.add(
        Entity(
            id=params.friend_name,
            kind="character",
            type="dogie",
            label="friend",
            traits=["gentle", "playful"],
            meters={"calm": 1.0},
            memes={"joy": 1.0, "friendship": 1.0},
        )
    )
    toy = world.add(
        Entity(
            id="toy",
            kind="thing",
            type="toy",
            label=params.toy,
            phrase=f"the {params.toy}",
            owner=dogie.id,
            held_by=dogie.id,
            meters={"clean": 1.0},
        )
    )

    world.say(f"On {params.setting}, {dogie.id} and {friend.id} met for a game.")
    world.say(f"{params.name} was known as a sophisticated little dogie who liked to look neat and feel proud.")
    world.para()
    _friendship_line(world, dogie, friend)
    _toy_line(world, dogie, toy)
    world.para()
    _turn_line(world, dogie, friend, toy)
    world.para()
    _sharing_line(world, dogie, friend, toy)

    world.facts.update(
        dogie=dogie,
        friend=friend,
        toy=toy,
        setting=params.setting,
    )
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    dogie: Entity = f["dogie"]  # type: ignore[assignment]
    friend: Entity = f["friend"]  # type: ignore[assignment]
    toy: Entity = f["toy"]  # type: ignore[assignment]
    setting = f["setting"]
    return [
        f'Write a short animal story about a sophisticated dogie named {dogie.id} who learns to thank a friend.',
        f"Tell a gentle story set at {setting} where {dogie.id} and {friend.id} share {toy.label}.",
        f'Create a child-friendly story with the words "dogie", "sophisticated", and "thank".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    dogie: Entity = f["dogie"]  # type: ignore[assignment]
    friend: Entity = f["friend"]  # type: ignore[assignment]
    toy: Entity = f["toy"]  # type: ignore[assignment]
    setting = f["setting"]
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"The story is about {dogie.id}, a sophisticated little dogie, and {friend.id}, the friend who played with {toy.label} at {setting}.",
        ),
        QAItem(
            question=f"What did {dogie.id} learn to do with the toy?",
            answer=f"{dogie.id} learned to share {toy.label} instead of keeping it alone.",
        ),
        QAItem(
            question=f"Why did {friend.id} get happier in the middle of the story?",
            answer=f"{friend.id} got happier because {dogie.id} noticed the lonely waiting and shared the toy, which made play feel friendly again.",
        ),
        QAItem(
            question=f"What did {dogie.id} say at the end?",
            answer=f"{dogie.id} said, \"Let's share,\" and the friends played together after that.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is sharing?",
            answer="Sharing means letting someone else use or enjoy something too, so everyone can take part.",
        ),
        QAItem(
            question="What is friendship?",
            answer="Friendship is a warm connection between friends who care about each other and like spending time together.",
        ),
        QAItem(
            question="Why is saying thank you polite?",
            answer="Saying thank you is polite because it shows you notice kindness and feel grateful for help or gifts.",
        ),
    ]


# ---------------------------------------------------------------------------
# Parameters and generation
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal story world: friendship and sharing.")
    ap.add_argument("--name")
    ap.add_argument("--friend-name")
    ap.add_argument("--toy", choices=[t[0] for t in TOYS])
    ap.add_argument("--setting", choices=SETTINGS)
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
    name = args.name or rng.choice(NAMES)
    friend_choices = [n for n in NAMES if n != name]
    friend_name = args.friend_name or rng.choice(friend_choices)
    toy = args.toy or rng.choice([t[0] for t in TOYS])
    setting = args.setting or rng.choice(SETTINGS)
    return StoryParams(name=name, friend_name=friend_name, toy=toy, setting=setting)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.held_by:
            bits.append(f"held_by={e.held_by}")
        if e.owner:
            bits.append(f"owner={e.owner}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
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


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
setting(sunny_yard).
setting(little_park).
setting(quiet_garden).

character(D) :- dogie(D).
character(F) :- friend(F).

shares(D, T) :- dogie(D), toy(T).
happy_end(D, F, T) :- shares(D, T), friend(F), dogie(D).

#show happy_end/3.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for n in NAMES:
        lines.append(asp.fact("dogie", n))
        lines.append(asp.fact("friend", n))
    for toy, _phrase in TOYS:
        lines.append(asp.fact("toy", toy))
    for s in SETTINGS:
        lines.append(asp.fact("setting", s.replace("the ", "").replace(" ", "_")))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    # This world has a simple declarative twin; verify the program parses and solves.
    import asp
    model = asp.one_model(asp_program("#show happy_end/3."))
    if model is not None:
        print("OK: ASP twin solved successfully.")
        return 0
    print("ASP verification failed.")
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show happy_end/3."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for i, (toy, _phrase) in enumerate(TOYS):
            params = StoryParams(
                name=NAMES[i % len(NAMES)],
                friend_name=NAMES[(i + 1) % len(NAMES)],
                toy=toy,
                setting=SETTINGS[i % len(SETTINGS)],
                seed=base_seed + i,
            )
            samples.append(generate(params))
    else:
        seen: set[str] = set()
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
        header = ""
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
