#!/usr/bin/env python3
"""
A tiny bedtime-story world about a small tent, a repeated first task,
and a gentle twist at the end.

This world is built around three seed words:
- twit
- bunt
- first

The story domain:
A child named Pip tries to do the first part of bedtime alone, but keeps
making a small twit-like mistake (a silly sound, a little stumble, or a tiny
bump). A soft repetition helps them try again, and the twist is that the
mistake turns out to be the beginning of something comforting rather than a
problem.
"""

from __future__ import annotations

import argparse
import copy
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

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Room:
    name: str = "the nursery"
    bedtime: bool = True
    affords: set[str] = field(default_factory=lambda: {"first", "twit", "bunt"})


@dataclass
class StoryParams:
    room: str = "nursery"
    first_task: str = "tidy-toys"
    twist: str = "lamp-hug"
    name: str = "Pip"
    gender: str = "boy"
    parent: str = "mother"
    seed: Optional[int] = None


@dataclass
class Task:
    id: str
    verb: str
    gerund: str
    little_mistake: str
    repeat_line: str
    reveal_line: str
    outcome: str
    tags: set[str] = field(default_factory=set)


ROOMS = {
    "nursery": Room(name="the nursery", bedtime=True, affords={"first", "twit", "bunt"}),
    "bedroom": Room(name="the bedroom", bedtime=True, affords={"first", "twit", "bunt"}),
}

TASKS = {
    "tidy-toys": Task(
        id="tidy-toys",
        verb="put the toys in the basket",
        gerund="putting the toys away",
        little_mistake="made a tiny twit and dropped one teddy on the rug",
        repeat_line="So he tried the first step again, slowly and carefully.",
        reveal_line="This time, the basket waited open like a moon-shaped hug.",
        outcome="soon the room felt quiet and neat",
        tags={"first", "repetition", "bedtime"},
    ),
    "count-stars": Task(
        id="count-stars",
        verb="count the stars from the window",
        gerund="counting the stars",
        little_mistake="gave a silly twit because one star looked like a grin",
        repeat_line="So she counted from the first star again, soft as a whisper.",
        reveal_line="Then the sky seemed to answer with three little sparkles in a row.",
        outcome="and sleep felt near",
        tags={"first", "repetition", "twist", "bedtime"},
    ),
    "fold-blanket": Task(
        id="fold-blanket",
        verb="fold the blanket into a square",
        gerund="folding the blanket",
        little_mistake="bumped the blanket into a funny bunt on the bed",
        repeat_line="So they began with the first corner again, slow and even.",
        reveal_line="The bunt was not a mistake at all; it made the blanket puff into a cozy pillow.",
        outcome="and the bed looked extra snuggly",
        tags={"bunt", "first", "twist", "bedtime"},
    ),
}


NAME_POOL = ["Pip", "Milo", "Nia", "Luna", "Toby", "Zoe", "Finn", "Ivy"]
TRAITS = ["sleepy", "gentle", "small", "curious", "quiet"]


class World:
    def __init__(self, room: Room) -> None:
        self.room = room
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

    def copy(self) -> "World":
        other = World(self.room)
        other.entities = copy.deepcopy(self.entities)
        other.paragraphs = [[]]
        other.facts = copy.deepcopy(self.facts)
        other.fired = set(self.fired)
        return other


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny bedtime story world with repetition and a twist.")
    ap.add_argument("--room", choices=ROOMS)
    ap.add_argument("--first-task", choices=TASKS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["boy", "girl"])
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
    room = args.room or rng.choice(list(ROOMS))
    task = args.first_task or rng.choice(list(TASKS))
    gender = args.gender or rng.choice(["boy", "girl"])
    name = args.name or rng.choice(NAME_POOL)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(room=room, first_task=task, twist="lamp-hug", name=name, gender=gender, parent=parent)


def _article(word: str) -> str:
    return "an" if word[:1].lower() in "aeiou" else "a"


def tell(room: Room, task: Task, hero_name: str, gender: str, parent_type: str) -> World:
    world = World(room)
    hero = world.add(Entity(id=hero_name, kind="character", type=gender, label=hero_name))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label=f"the {parent_type}"))
    blanket = world.add(Entity(id="blanket", type="thing", label="blanket", phrase="a soft blue blanket", owner=hero.id))
    stars = world.add(Entity(id="stars", type="thing", label="stars", phrase="the little stars", plural=True))

    world.say(f"At bedtime in {room.name}, {hero.id} was still awake and very small in the quiet room.")
    world.say(f"{hero.pronoun().capitalize()} wanted to {task.verb}, and {hero.pronoun('possessive')} {parent.label} sat nearby with a smile.")
    world.say(f"First, {hero.id} tried to do it just right, but {task.little_mistake}.")
    world.para()
    world.say(f"{hero.pronoun().capitalize()} paused, listened to the hush, and tried the first step again.")
    world.say(task.repeat_line)
    world.say(f"That gentle repetition made the room feel calmer, like the same lullaby sung twice.")
    world.para()
    world.say(task.reveal_line)
    if "twist" in task.tags:
        world.say(f"The twist was sweet: what looked a little odd at first was actually helping.")
    world.say(f"Soon {task.outcome}, and {hero.id} smiled up at {hero.pronoun('possessive')} {parent.label}, ready for dreams.")
    world.say(f"By the end, the room was soft and still, and even the {stars.label} seemed to glow more kindly.")

    world.facts.update(hero=hero, parent=parent, task=task, blanket=blanket, stars=stars)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, task = f["hero"], f["task"]
    return [
        f'Write a gentle bedtime story for young children that uses the words "twit", "bunt", and "first".',
        f"Tell a small bedtime story where {hero.id} must do the first part of {task.verb} again after a tiny twit.",
        f"Write a calm story with repetition and a twist ending about a child at bedtime in {world.room.name}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, task = f["hero"], f["parent"], f["task"]
    return [
        QAItem(
            question=f"What did {hero.id} want to do at bedtime?",
            answer=f"{hero.id} wanted to {task.verb}.",
        ),
        QAItem(
            question=f"What happened the first time {hero.id} tried?",
            answer=f"The first time, {task.little_mistake}.",
        ),
        QAItem(
            question="What helped the child keep going?",
            answer=f"The child tried the first step again, and the repetition made the task feel calmer and easier.",
        ),
        QAItem(
            question="What was the twist in the story?",
            answer=f"The twist was that the odd little moment turned out to help instead of hurt, especially when {task.reveal_line.lower()}",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does repetition mean in a story?",
            answer="Repetition means saying or doing something again, which can make a story feel gentle and easy to follow.",
        ),
        QAItem(
            question="What is a twist in a story?",
            answer="A twist is a surprising turn that changes how we understand what is happening.",
        ),
        QAItem(
            question="Why are bedtime stories often calm?",
            answer="Bedtime stories are often calm because they help children feel safe, slow down, and get ready for sleep.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(f"  {e.id}: type={e.type} kind={e.kind} owner={e.owner or '-'}")
    lines.append(f"  room={world.room.name}")
    return "\n".join(lines)


ASP_RULES = r"""
task(first).
task(twit).
task(bunt).

story_ok(R, T) :- room(R), task(T).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for rid in ROOMS:
        lines.append(asp.fact("room", rid))
    for tid in TASKS:
        lines.append(asp.fact("task", tid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    # Minimal parity check: the declarative twin should at least admit every registry pair.
    try:
        import asp
    except Exception as err:
        print(f"ASP unavailable: {err}")
        return 1
    model = asp.one_model(asp_program("#show story_ok/2."))
    atoms = set(asp.atoms(model, "story_ok"))
    py = {(r, t) for r in ROOMS for t in TASKS}
    if atoms == py:
        print(f"OK: ASP matches Python registry coverage ({len(py)} pairs).")
        return 0
    print("MISMATCH between ASP and Python.")
    print("only in asp:", sorted(atoms - py))
    print("only in python:", sorted(py - atoms))
    return 1


def generate(params: StoryParams) -> StorySample:
    room = ROOMS[params.room]
    task = TASKS[params.first_task]
    world = tell(room, task, params.name, params.gender, params.parent)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


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
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
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


CURATED = [
    StoryParams(room="nursery", first_task="tidy-toys", twist="lamp-hug", name="Pip", gender="boy", parent="mother"),
    StoryParams(room="bedroom", first_task="count-stars", twist="lamp-hug", name="Luna", gender="girl", parent="father"),
    StoryParams(room="nursery", first_task="fold-blanket", twist="lamp-hug", name="Milo", gender="boy", parent="mother"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show story_ok/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show story_ok/2."))
        pairs = sorted(set(asp.atoms(model, "story_ok")))
        for p in pairs:
            print(p)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
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
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.first_task} in {p.room}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
