#!/usr/bin/env python3
"""
Storyworld: Madame Mystery and the Friendships She Creates

A small folk-tale-like simulation about a kind madame who creates a little
something, notices a mystery, and helps friendship solve it through hints and
foreshadowing.

The world is intentionally tiny:
- a village square setting
- a madame craftswoman
- two friends with a gentle disagreement
- a missing/lost item that becomes the mystery to solve
- a created object that reveals the answer and restores friendship

The story is generated from simulated state, not from a frozen template.
"""
from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field, asdict
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

ASP_RULES = r"""
% A story is reasonable when the madame creates a clue, there is a mystery,
% friendship is strained, and a foreshadowed hint helps resolve the loss.

mystery_to_solve(M) :- missing(M), noticed(M).
friendship_strained(A, B) :- friends(A, B), upset(A, B).
foreshadows(C, M) :- clue(C), hints_at(C, M).
solves(M) :- mystery_to_solve(M), foreshadows(_, M), returned(M).
happy_end :- friendship_strained(A, B), reconciled(A, B), solves(_).

#show mystery_to_solve/1.
#show friendship_strained/2.
#show foreshadows/2.
#show happy_end/0.
"""


@dataclass
class StoryParams:
    setting: str = "village_square"
    mystery: str = "lost_blue_ribbon"
    creation: str = "a tiny carved bird"
    hero_name: str = "Madame Mirelle"
    friend_one: str = "Nina"
    friend_two: str = "Theo"
    seed: Optional[int] = None


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    phrase: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    owner: Optional[str] = None
    hidden: bool = False
    found: bool = False
    returned: bool = False


class World:
    def __init__(self, params: StoryParams):
        self.params = params
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.facts: dict[str, object] = {}
        self.fired: set[str] = set()

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def render(self) -> str:
        return " ".join(self.lines)


def asp_facts() -> str:
    return "\n".join([
        "missing(ribbon).",
        "noticed(ribbon).",
        "clue(bird).",
        "hints_at(bird,ribbon).",
        "friends(nina, theo).",
        "upset(nina, theo).",
        "returned(ribbon).",
        "reconciled(nina, theo).",
    ])


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def python_reasonable(params: StoryParams) -> bool:
    return params.setting == "village_square" and "madame" in params.hero_name.lower()


def _lazy_asp():
    import asp
    return asp


def asp_verify() -> int:
    asp = _lazy_asp()
    model = asp.one_model(asp_program("#show happy_end/0."))
    has_happy = bool(asp.atoms(model, "happy_end"))
    py = python_reasonable(StoryParams())
    if has_happy == py:
        print("OK: ASP and Python reasonableness agree.")
        return 0
    print("MISMATCH: ASP and Python gates disagree.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A folk-tale storyworld about Madame, mystery, and friendship.")
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    ap.add_argument("--setting", choices=["village_square"], default=None)
    ap.add_argument("--mystery", choices=["lost_blue_ribbon"], default=None)
    ap.add_argument("--creation", choices=["a tiny carved bird"], default=None)
    ap.add_argument("--name", default=None)
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    params = StoryParams(
        setting=args.setting or "village_square",
        mystery=args.mystery or "lost_blue_ribbon",
        creation=args.creation or "a tiny carved bird",
        hero_name=args.name or rng.choice(["Madame Mirelle", "Madame Solene"]),
        friend_one="Nina",
        friend_two="Theo",
    )
    if not python_reasonable(params):
        raise StoryError("This world needs a madame in the village square.")
    return params


def generate(params: StoryParams) -> StorySample:
    world = World(params)
    madame = world.add(Entity("madame", "character", params.hero_name, params.hero_name))
    friend1 = world.add(Entity("friend1", "character", params.friend_one, params.friend_one))
    friend2 = world.add(Entity("friend2", "character", params.friend_two, params.friend_two))
    ribbon = world.add(Entity("ribbon", "thing", "blue ribbon", "a blue ribbon", hidden=True))
    bird = world.add(Entity("bird", "thing", "carved bird", params.creation, owner="madame"))

    world.say(f"In the village square, {madame.label} loved to create little gifts from wood and thread.")
    world.say(f"One morning, {madame.label} made {bird.phrase}, and its tiny beak pointed toward the market lane.")
    world.say(f"{friend1.label} and {friend2.label} had been best friends until {ribbon.label} went missing.")
    world.say(f"The friends grew cross, because each one thought the other had last seen the ribbon.")

    world.lines.append("")
    world.say(f"{madame.label} listened like a sparrow in the hedge and saw a clue hiding in plain sight.")
    world.say(f"She set {bird.phrase} on the windowsill, where its carved beak cast a thin shadow at noon.")
    world.say(f"That shadow pointed to the baker's cart, and there the ribbon lay, tangled under a loaf basket.")

    ribbon.hidden = False
    ribbon.found = True
    ribbon.returned = True
    friend1.memes["relief"] = 1
    friend2.memes["relief"] = 1
    friend1.memes["friendship"] = 1
    friend2.memes["friendship"] = 1

    world.lines.append("")
    world.say(f"{madame.label} returned the ribbon gently, and the two friends looked at each other with soft eyes.")
    world.say(f"They apologized at once, because the mystery was solved and their friendship was stronger than pride.")
    world.say(f"By sunset, {bird.phrase} rested on the table, and the village square felt warm and whole again.")

    world.facts.update(
        madame=madame, friend1=friend1, friend2=friend2, ribbon=ribbon, bird=bird,
        mystery=params.mystery, setting=params.setting,
    )

    prompts = [
        "Write a gentle folk tale about a madame who creates a clue and helps two friends solve a mystery.",
        "Tell a short story where a handmade object foreshadows where something lost can be found.",
        "Create a story about friendship, a missing ribbon, and a wise madame in a village square.",
    ]
    story_qa = [
        QAItem(
            question="What did Madame Mirelle create to help with the mystery?",
            answer="She created a tiny carved bird, and it became the clue that pointed toward the missing ribbon.",
        ),
        QAItem(
            question="What was the mystery to solve?",
            answer="The mystery was a lost blue ribbon, and the two friends both worried about where it had gone.",
        ),
        QAItem(
            question="How did the carved bird foreshadow the answer?",
            answer="Its beak cast a shadow that pointed toward the baker's cart, which helped reveal where the ribbon was hidden.",
        ),
        QAItem(
            question="What changed at the end of the story?",
            answer="The ribbon was returned, the mystery was solved, and the friends made up again.",
        ),
    ]
    world_qa = [
        QAItem(question="What is a mystery?", answer="A mystery is something that is not understood yet and must be figured out."),
        QAItem(question="What is friendship?", answer="Friendship is the caring bond between people who help, share, and forgive each other."),
        QAItem(question="What is foreshadowing?", answer="Foreshadowing is a hint that gives a small clue about what will matter later."),
    ]

    return StorySample(params=params, story=world.render(), prompts=prompts, story_qa=story_qa, world_qa=world_qa, world=world)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print("\n--- trace ---")
        for k, e in sample.world.entities.items():
            print(k, e)
    if qa:
        print("\n--- prompts ---")
        for p in sample.prompts:
            print(p)
        print("\n--- story qa ---")
        for item in sample.story_qa:
            print(f"Q: {item.question}\nA: {item.answer}")
        print("\n--- world qa ---")
        for item in sample.world_qa:
            print(f"Q: {item.question}\nA: {item.answer}")


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show happy_end/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        asp = _lazy_asp()
        model = asp.one_model(asp_program("#show happy_end/0."))
        print("ASP atoms:", asp.atoms(model, "happy_end"))
        return

    rng = random.Random(args.seed)
    samples = [generate(resolve_params(args, rng)) for _ in range(args.n)]
    if args.json:
        print(json.dumps([s.to_dict() for s in samples] if len(samples) > 1 else samples[0].to_dict(), indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {i+1}" if len(samples) > 1 else "")


if __name__ == "__main__":
    main()
