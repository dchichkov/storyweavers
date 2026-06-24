#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260624T090150Z_seed197402754_n1000/amateur_toil_expect_misunderstanding_happy_ending_ghost.py
================================================================================================

A small story world in a ghost-story style: a timid amateur lantern-keeper
expects a haunting, runs into a misunderstanding, works through a little toil,
and ends in a happy ending.

Seed tale premise:
---
An amateur night watch helper named Mina expects a ghost in the old attic room.
She hears creaks, sees a pale shape, and worries the place is haunted. After some
toil, she learns the "ghost" is only her friend under a bedsheet, and the two
share a happy ending with lantern light and laughter.

This file models that premise as a simulated world with:
- physical meters: light, chill, dust, toil
- emotional memes: expect, fear, misunderstanding, relief, joy
- a state-driven turn: a mistaken identity, then a reveal
- child-facing prose that reads like a complete short story
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
    plural: bool = False
    owner: Optional[str] = None
    wore: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the old attic room"
    dark: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class GhostThing:
    id: str
    label: str
    phrase: str
    illusion: str
    reveal: str
    cause: str


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    helps: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.trace_bits: list[str] = []

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

    def copy(self) -> "World":
        import copy
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.fired = set(self.fired)
        w.facts = dict(self.facts)
        return w


def _ensure(ent: Entity, key: str) -> None:
    ent.meters.setdefault(key, 0.0)
    ent.memes.setdefault(key, 0.0)


def _narrate_turn(world: World, actor: Entity, ghost: Entity) -> None:
    actor.memes["misunderstanding"] += 1
    actor.memes["fear"] += 1
    actor.meters["toil"] += 1
    world.say(
        f"{actor.id} froze when {actor.pronoun('possessive')} lantern flickered. "
        f"A pale shape drifted by the rafters, and {actor.id} expected a real ghost."
    )
    world.say(
        f"{actor.pronoun().capitalize()} had already done some toil sweeping dust from the floor, "
        f"so the room felt extra quiet."
    )
    world.facts["misunderstanding"] = True


def _resolve(world: World, actor: Entity, friend: Entity, tool: Entity, ghost: Entity) -> None:
    actor.memes["relief"] += 1
    actor.memes["joy"] += 1
    actor.memes["fear"] = 0.0
    actor.memes["misunderstanding"] = 0.0
    world.say(
        f"Then {tool.label} shone on the pale shape, and {actor.id} laughed. "
        f"The 'ghost' was only {friend.id} under a white sheet, carrying {friend.pronoun('possessive')} "
        f"{ghost.label} to make a spooky game."
    )
    world.say(
        f"{friend.id} apologized for the surprise, but {actor.id} smiled and said the mistake was funny now. "
        f"Together they finished the last little chores, and the attic room felt warm and safe."
    )
    world.say(
        f"In the happy ending, {actor.id} set the lantern on the crate, the sheet came off, and "
        f"the two friends left the old room laughing instead of trembling."
    )
    world.facts["resolved"] = True


def tell() -> World:
    setting = Setting()
    world = World(setting)

    hero = world.add(Entity(id="Mina", kind="character", type="girl"))
    friend = world.add(Entity(id="Pip", kind="character", type="boy"))
    ghost = world.add(Entity(id="shape", type="thing", label="lantern", phrase="a small lantern"))
    tool = world.add(Entity(id="Lantern", type="thing", label="lantern", phrase="a brass lantern"))

    for e in (hero, friend, ghost, tool):
        _ensure(e, "toil")
        _ensure(e, "fear")
        _ensure(e, "misunderstanding")
        _ensure(e, "relief")
        _ensure(e, "joy")
        _ensure(e, "expect")

    hero.memes["expect"] += 1
    hero.meters["toil"] += 1
    world.say(
        f"Mina was an amateur night watch helper who expected a quiet evening in {setting.place}. "
        f"She liked to keep the little room neat, even if the work was slow."
    )
    world.say(
        f"She carried a lantern, listened to every creak, and told herself the old house only sounded spooky."
    )

    world.para()
    world.say(
        f"One night, Mina heard a bump near the beams and saw a pale shape move in the corner."
    )
    _narrate_turn(world, hero, ghost)

    world.para()
    world.say(
        f"She took a careful breath, walked closer, and lifted the lantern higher."
    )
    _resolve(world, hero, friend, tool, ghost)

    world.facts.update(hero=hero, friend=friend, ghost=ghost, tool=tool, setting=setting)
    return world


GIRL_NAMES = ["Mina", "Lina", "Nora", "Iris", "Tess"]
BOY_NAMES = ["Pip", "Owen", "Theo", "Ned", "Milo"]


@dataclass
class StoryParams:
    name: str = "Mina"
    friend: str = "Pip"
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Ghost-story style world with a misunderstanding and happy ending.")
    ap.add_argument("--name", choices=GIRL_NAMES)
    ap.add_argument("--friend", choices=BOY_NAMES)
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
    name = args.name or rng.choice(GIRL_NAMES)
    friend = args.friend or rng.choice(BOY_NAMES)
    if name == friend:
        raise StoryError("The watcher and the friend should be different characters.")
    return StoryParams(name=name, friend=friend, seed=args.seed)


def generate(params: StoryParams) -> StorySample:
    world = tell()
    world.get("Mina").id = params.name
    world.get("Pip").id = params.friend
    story = world.render().replace("Mina", params.name).replace("Pip", params.friend)
    prompts = [
        f'Write a short ghost-story for a child about an amateur helper named {params.name} who expects a ghost, but the surprise is harmless.',
        f"Tell a gentle story where {params.name} does some toil in an old room, sees a pale shape, and learns it was only {params.friend} in disguise.",
        f'Write a story with a misunderstanding and a happy ending in a spooky attic room.',
    ]
    story_qa = [
        QAItem(
            question=f"Why did {params.name} feel scared in the old room?",
            answer=f"{params.name} expected a ghost after seeing a pale shape and hearing a strange bump in the attic room."
        ),
        QAItem(
            question=f"What caused the misunderstanding?",
            answer=f"The misunderstanding happened because {params.name} thought the pale shape was a ghost, but it was really {params.friend} under a white sheet."
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended happily when {params.name} saw the truth, relaxed, and laughed with {params.friend}."
        ),
    ]
    world_qa = [
        QAItem(
            question="What is a lantern for?",
            answer="A lantern gives off light so people can see in dark places."
        ),
        QAItem(
            question="What does toil mean?",
            answer="Toil means hard work that can take time and effort."
        ),
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding is when someone thinks something is true, but they are mistaken."
        ),
    ]
    return StorySample(params=params, story=story, prompts=prompts, story_qa=story_qa, world_qa=world_qa, world=world)


ASP_RULES = r"""
watcher(X) :- hero(X).
friend(Y) :- helper(Y).
expect_ghost(X) :- expect(X), watcher(X).
misunderstanding(X) :- expect_ghost(X), pale_shape_seen(X).
happy_ending(X) :- misunderstanding(X), reveal_kind(X).
"""


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("hero", "mina"),
        asp.fact("helper", "pip"),
        asp.fact("expect", "mina"),
        asp.fact("pale_shape_seen", "mina"),
        asp.fact("reveal_kind", "mina"),
    ])


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    return 0


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print("--- trace ---")
        for e in sample.world.entities.values():
            print(f"{e.id}: meters={e.meters} memes={e.memes}")
    if qa:
        print()
        print("== Prompts ==")
        for p in sample.prompts:
            print(p)
        print("\n== Story Q&A ==")
        for q in sample.story_qa:
            print(f"Q: {q.question}")
            print(f"A: {q.answer}")
        print("\n== World Q&A ==")
        for q in sample.world_qa:
            print(f"Q: {q.question}")
            print(f"A: {q.answer}")


CURATED = [StoryParams(name="Mina", friend="Pip")]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show happy_ending/1."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, s in enumerate(samples):
        emit(s, trace=args.trace, qa=args.qa, header=f"### variant {i + 1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
