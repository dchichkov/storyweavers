#!/usr/bin/env python3
"""
A small storyworld: a nursery-rhyme-like visit to a dentist office with
tapioca, repetition, and friendship.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class StoryParams:
    name: str
    friend: str
    seed: Optional[int] = None


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = None
    memes: dict[str, float] = None

    def __post_init__(self):
        if self.meters is None:
            self.meters = {}
        if self.memes is None:
            self.memes = {}


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.facts: dict[str, object] = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def say(self, line: str) -> None:
        if line:
            self.lines.append(line)

    def render(self) -> str:
        return "\n".join(self.lines)


NAMES = ["Mia", "Nora", "Lily", "Ruby", "Poppy", "Milo", "Theo", "Finn"]
FRIENDS = ["Pip", "Dot", "Bea", "Max", "Jules", "Kit"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A nursery-rhyme storyworld in a dentist office.")
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--friend", choices=FRIENDS)
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
    friend = args.friend or rng.choice([f for f in FRIENDS if f != name])
    if name == friend:
        raise StoryError("The friend must be a different child.")
    return StoryParams(name=name, friend=friend)


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("place", "dentist_office"),
        asp.fact("theme", "repetition"),
        asp.fact("theme", "friendship"),
        asp.fact("thing", "tapioca"),
        asp.fact("verb", "enter"),
    ]
    return "\n".join(lines)


ASP_RULES = r"""
story(P,N,F) :- place(P), theme(repetition), theme(friendship), thing(tapioca), verb(enter),
                child(N), friend(F), N != F.
#show story/3.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show story/3."))
    clingo_set = set(asp.atoms(model, "story"))
    python_set = set(valid_story_triples())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches Python ({len(clingo_set)} stories).")
        return 0
    print("MISMATCH between clingo and Python:")
    print("  only in clingo:", sorted(clingo_set - python_set))
    print("  only in python:", sorted(python_set - clingo_set))
    return 1


def valid_story_triples() -> list[tuple[str, str, str]]:
    return [("dentist_office", "repetition", "friendship")]


def build_world(params: StoryParams) -> World:
    w = World()
    child = w.add(Entity(id=params.name, kind="character", type="child", label=params.name))
    friend = w.add(Entity(id=params.friend, kind="character", type="child", label=params.friend))
    tapioca = w.add(Entity(id="tapioca", type="snack", label="tapioca", phrase="a cup of tapioca"))
    w.facts.update(child=child, friend=friend, tapioca=tapioca, place="dentist office")
    return w


def generate_story(world: World, params: StoryParams) -> str:
    name = params.name
    friend = params.friend
    w = world
    w.say(f"In the dentist office, {name} came in, came in, came in with a grin.")
    w.say(f"{friend} came too, for friendship is sweet, and friendship is true.")
    w.say(f"On the tidy blue chair sat a cup of tapioca, wobble, wobble, near the tray.")
    w.say(f"{name} wished to enter, to enter, to enter, but paused to wait and play it safe.")
    w.say(f"{friend} held a hand and said, 'First the dentist, then tapioca after, and we may cheer.'")
    w.say(f"So {name} and {friend} waited together, together, together, nice and clear.")
    w.say(f"When the checkup was done, they shared the tapioca by the window bright.")
    w.say(f"The dentist smiled, and the two friends went home with a happy, bouncy night.")
    return w.render()


def generation_prompts(world: World) -> list[str]:
    return [
        "Write a nursery-rhyme-style story about a child and a friend in a dentist office.",
        "Tell a gentle story that repeats words like a song and includes tapioca and enter.",
        "Write a short friendship story set in a dentist office with a safe little ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    child: Entity = world.facts["child"]
    friend: Entity = world.facts["friend"]
    return [
        QAItem(
            question=f"Where did {child.id} and {friend.id} go?",
            answer="They went to the dentist office.",
        ),
        QAItem(
            question=f"What sweet snack was in the story?",
            answer="A cup of tapioca was in the story.",
        ),
        QAItem(
            question=f"How did the story use repetition?",
            answer="It repeated words and sounds, like 'came in, came in, came in' and 'together, together, together.'",
        ),
        QAItem(
            question=f"What helped {child.id} wait patiently?",
            answer=f"{friend.id} helped by staying close and being a kind friend.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a dentist office?",
            answer="A dentist office is a place where a dentist checks teeth and helps keep them healthy.",
        ),
        QAItem(
            question="What is tapioca?",
            answer="Tapioca is a chewy food made from starch, often served as little pearls in a sweet snack or drink.",
        ),
        QAItem(
            question="What is repetition in a story?",
            answer="Repetition means saying a word, sound, or line again and again to make it catchy and easy to remember.",
        ),
        QAItem(
            question="What is friendship?",
            answer="Friendship means caring about someone, helping them, and staying kind to them.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(f"  {e.id:8} ({e.type:7})")
    lines.append("  facts: dentist office, tapioca, enter, repetition, friendship")
    return "\n".join(lines)


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


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    story = generate_story(world, params)
    return StorySample(
        params=params,
        story=story,
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show story/3."))
        print(f"{len(set(asp.atoms(model, 'story')))} compatible story pattern(s).")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        params_list = [StoryParams(name=n, friend=f) for n in NAMES[:3] for f in FRIENDS[:2] if n != f]
        for p in params_list[: max(1, args.n)]:
            samples.append(generate(p))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
