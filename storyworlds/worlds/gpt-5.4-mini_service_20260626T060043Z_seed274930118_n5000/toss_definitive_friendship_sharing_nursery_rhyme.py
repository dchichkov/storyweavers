#!/usr/bin/env python3
"""
Story world: a nursery-rhyme tale of friendship, sharing, and a final toss.

Premise:
- Two small friends want the same bright toy.
- One child clutches it, then notices the other child feels left out.
- A gentle sharing plan is suggested.
- A decisive toss begins a game they can enjoy together.

World model:
- Each child has meters for closeness, joy, and longing.
- The toy has meters for held, tossed, and shared.
- Shared use raises friendship; a fair toss settles the moment into play.
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

ASP_RULES = r"""
friend_pair(A,B) :- friend(A,B), A < B.
needs_share(T) :- toy(T).
shared_story(A,B,T) :- friend_pair(A,B), shares(A,T), shares(B,T), needs_share(T).
definitive_turn(T) :- tossed(T), shared_story(_,_,T).
#show friend_pair/2.
#show shared_story/3.
#show definitive_turn/1.
"""


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    phrase: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def inc_meter(self, key: str, amt: float = 1.0) -> None:
        self.meters[key] = self.meters.get(key, 0.0) + amt

    def inc_meme(self, key: str, amt: float = 1.0) -> None:
        self.memes[key] = self.memes.get(key, 0.0) + amt


@dataclass
class World:
    setting: str
    entities: dict[str, Entity] = field(default_factory=dict)
    lines: list[str] = field(default_factory=list)
    facts: dict = field(default_factory=dict)

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def render(self) -> str:
        return " ".join(self.lines).strip()


@dataclass
class StoryParams:
    setting: str = "the nursery"
    first_name: str = "Mina"
    second_name: str = "Ned"
    toy: str = "the red ball"
    seed: Optional[int] = None


SETTINGS = {
    "the nursery": {"indoor": True},
    "the playroom": {"indoor": True},
    "the garden patch": {"indoor": False},
}

NAMES = ["Mina", "Ned", "Lena", "Ollie", "Pia", "Rory", "Tessa", "Finn"]
TOYS = [
    ("the red ball", "ball"),
    ("the blue hoop", "hoop"),
    ("the bright ribbon", "ribbon"),
    ("the soft kite", "kite"),
]


class WorldModel:
    def __init__(self, world: World) -> None:
        self.world = world

    def establish_friendship(self) -> None:
        a = self.world.get("A")
        b = self.world.get("B")
        a.inc_meme("friendship", 1)
        b.inc_meme("friendship", 1)
        self.world.say(f"{a.label} and {b.label} were friends in {self.world.setting}.")

    def dispute_toy(self) -> None:
        a = self.world.get("A")
        b = self.world.get("B")
        toy = self.world.get("T")
        a.inc_meme("want", 1)
        b.inc_meme("want", 1)
        toy.inc_meter("held", 1)
        self.world.say(f"Both little friends wanted {toy.label}, and the room grew still.")

    def share_and_toss(self) -> None:
        a = self.world.get("A")
        b = self.world.get("B")
        toy = self.world.get("T")
        a.inc_meme("kindness", 1)
        b.inc_meme("kindness", 1)
        a.inc_meme("joy", 1)
        b.inc_meme("joy", 1)
        toy.inc_meter("shared", 1)
        toy.inc_meter("tossed", 1)
        self.world.say(
            f"Then {a.label} smiled and said, 'Let's share.' "
            f"{b.label} nodded, and the toy was tossed in a merry, fair turn."
        )
        self.world.say(
            f"Up it went and down it came, and the two friends laughed together."
        )

    def end_image(self) -> None:
        a = self.world.get("A")
        b = self.world.get("B")
        toy = self.world.get("T")
        self.world.say(
            f"By the end, {toy.label} was shared, and {a.label} and {b.label} played side by side."
        )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A nursery-rhyme storyworld about friendship and sharing.")
    ap.add_argument("--setting", choices=sorted(SETTINGS))
    ap.add_argument("--first-name")
    ap.add_argument("--second-name")
    ap.add_argument("--toy", choices=[t[0] for t in TOYS])
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


def asp_facts() -> str:
    import storyworlds.asp as asp  # lazy
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for a, b in [("mina", "ned"), ("lena", "ollie"), ("pia", "rory")]:
        lines.append(asp.fact("friend", a, b))
        lines.append(asp.fact("friend", b, a))
    for toy_name, toy_id in TOYS:
        lines.append(asp.fact("toy", toy_id))
        lines.append(asp.fact("label", toy_id, toy_name))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp  # lazy
    model = asp.one_model(asp_program("#show friend_pair/2. #show shared_story/3. #show definitive_turn/1."))
    _ = model
    print("OK: ASP program loaded and solved.")
    return 0


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting = args.setting or rng.choice(sorted(SETTINGS))
    first_name = args.first_name or rng.choice(NAMES)
    second_name = args.second_name or rng.choice([n for n in NAMES if n != first_name])
    toy = args.toy or rng.choice([t[0] for t in TOYS])
    if first_name == second_name:
        raise StoryError("The two friends must be different children.")
    return StoryParams(setting=setting, first_name=first_name, second_name=second_name, toy=toy, seed=args.seed)


def generate(params: StoryParams) -> StorySample:
    world = World(setting=params.setting)
    a = world.add(Entity(id="A", kind="character", label=params.first_name))
    b = world.add(Entity(id="B", kind="character", label=params.second_name))
    toy = world.add(Entity(id="T", kind="thing", label=params.toy))
    model = WorldModel(world)

    world.say(f"In {params.setting}, {a.label} and {b.label} began the day.")
    world.say(f"They were friends, and they both loved {toy.label}.")
    world.say(f"But at first, one hand held the toy close.")

    model.establish_friendship()
    model.dispute_toy()
    world.say(f"That was not kind, and it made the other friend feel small.")
    model.share_and_toss()
    model.end_image()

    world.facts.update(
        first=a.label,
        second=b.label,
        toy=toy.label,
        shared=toy.meters.get("shared", 0.0) > 0,
        tossed=toy.meters.get("tossed", 0.0) > 0,
    )

    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a nursery-rhyme story about {f['first']} and {f['second']} sharing {f['toy']}.",
        f"Tell a short gentle tale where friendship grows when {f['toy']} is tossed fairly.",
        f"Create a child-friendly story with a clear turn from wanting to sharing in {world.setting}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    return [
        QAItem(
            question=f"Who were the two friends in the story?",
            answer=f"The two friends were {f['first']} and {f['second']}.",
        ),
        QAItem(
            question=f"What toy did they both want?",
            answer=f"They both wanted {f['toy']}.",
        ),
        QAItem(
            question="What changed the mood in the middle of the story?",
            answer="The mood changed when one friend chose sharing, and the toy was tossed fairly so they could play together.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended with {f['toy']} being shared and both friends playing side by side.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is friendship?",
            answer="Friendship is a kind bond between people who care about each other and like to spend time together.",
        ),
        QAItem(
            question="What does sharing mean?",
            answer="Sharing means letting someone else use or enjoy something too, so more than one person can take part.",
        ),
        QAItem(
            question="What is a toss?",
            answer="A toss is a quick throw, often a light one used to start a game or pass a toy to someone else.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: {e.label} meters={dict(e.meters)} memes={dict(e.memes)}")
    return "\n".join(lines)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        for i, item in enumerate(sample.story_qa, 1):
            print(f"Q{i}: {item.question}")
            print(f"A{i}: {item.answer}")
        for i, item in enumerate(sample.world_qa, 1):
            print(f"W{i}: {item.question}")
            print(f"A{i}: {item.answer}")


CURATED = [
    StoryParams(setting="the nursery", first_name="Mina", second_name="Ned", toy="the red ball"),
    StoryParams(setting="the playroom", first_name="Lena", second_name="Ollie", toy="the blue hoop"),
    StoryParams(setting="the garden patch", first_name="Pia", second_name="Rory", toy="the bright ribbon"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show friend_pair/2. #show shared_story/3. #show definitive_turn/1."))
        return
    if args.verify:
        sys.exit(asp_verify())

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
            print(json.dumps([s.to_dict() for s in samples], ensure_ascii=False, indent=2))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.first_name} and {p.second_name} at {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
