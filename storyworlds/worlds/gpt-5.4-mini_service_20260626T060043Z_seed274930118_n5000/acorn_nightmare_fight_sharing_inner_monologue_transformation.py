#!/usr/bin/env python3
"""
A heartwarming storyworld about an acorn, a scary nightmare, and a fight that
turns into sharing.

Premise:
- A small character finds or treasures an acorn.
- A hurtful fight or misunderstanding makes the character worried.
- A nightmare brings those feelings to the surface in an inner monologue.
- A gentle act of sharing transforms the mood and the relationship.

This script keeps the world small and classical:
- one child character
- one peer/friend character
- one cherished acorn
- one rainy porch/garden-like setting
- one emotional turn from fear and anger into sharing and repair
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
# World model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    shared_with: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=lambda: {"brightness": 0.0})
    memes: dict[str, float] = field(default_factory=lambda: {"worry": 0.0, "anger": 0.0, "warmth": 0.0})

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "boy", "child"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Place:
    name: str
    detail: str


@dataclass
class StoryParams:
    place: str
    hero: str
    friend: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.events: list[str] = []

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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
PLACES = {
    "garden": Place("the garden", "The garden was quiet, with leaf shadows on the path."),
    "porch": Place("the porch", "The porch creaked softly in the evening wind."),
    "bedroom": Place("the bedroom", "The bedroom was dim and cozy, with a small lamp glowing."),
}

HEROES = {
    "Mina": {"type": "girl", "trait": "gentle"},
    "Owen": {"type": "boy", "trait": "thoughtful"},
    "Pip": {"type": "child", "trait": "small"},
}

FRIENDS = {
    "Taro": {"type": "boy"},
    "Nia": {"type": "girl"},
    "Milo": {"type": "boy"},
}

ASP_RULES = r"""
% The acorn becomes important when it is owned by the hero.
important(acorn) :- owns(hero, acorn).

% A fight creates hurt feelings.
hurt(friend) :- fight.
hurt(hero) :- fight.

% A nightmare happens when worry grows.
nightmare :- worry(hero).

% Sharing reduces hurt and increases warmth.
warm(friend) :- share(hero, acorn, friend).
warm(hero) :- share(hero, acorn, friend).
"""


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("owns", "hero", "acorn"),
        asp.fact("has", "hero", "acorn"),
        asp.fact("friend", "friend"),
        asp.fact("fight"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------
def build_world(params: StoryParams) -> World:
    if params.place not in PLACES:
        raise StoryError(f"Unknown place: {params.place}")
    if params.hero not in HEROES:
        raise StoryError(f"Unknown hero: {params.hero}")
    if params.friend not in FRIENDS:
        raise StoryError(f"Unknown friend: {params.friend}")
    if params.hero == params.friend:
        raise StoryError("Hero and friend must be different characters.")

    world = World(PLACES[params.place])
    hero_cfg = HEROES[params.hero]
    friend_cfg = FRIENDS[params.friend]

    hero = world.add(Entity(
        id="hero",
        kind="character",
        type=hero_cfg["type"],
        label=params.hero,
    ))
    friend = world.add(Entity(
        id="friend",
        kind="character",
        type=friend_cfg["type"],
        label=params.friend,
    ))
    acorn = world.add(Entity(
        id="acorn",
        kind="thing",
        type="acorn",
        label="acorn",
        phrase="a small brown acorn with a smooth cap",
        owner=hero.id,
        meters={"brightness": 1.0},
    ))

    world.facts.update(
        hero=hero,
        friend=friend,
        acorn=acorn,
        place=world.place,
        hero_name=params.hero,
        friend_name=params.friend,
    )

    # Act 1: setup and love for the acorn.
    world.say(f"{hero.label} found {acorn.phrase} in {world.place.name}.")
    world.say(f"{hero.label} held it close because it felt like a tiny treasure.")
    world.say(f"{friend.label} came by to play, and the two of them smiled at the warm afternoon.")

    # Act 2: the fight and the nightmare.
    world.para()
    hero.memes["anger"] += 1
    friend.memes["anger"] += 1
    world.say(f"Then a small fight started over who should keep the acorn first.")
    world.say(f"{hero.label} walked away with a tight chest and a heavy face.")
    world.say(f"That night, {hero.label} had a nightmare about losing the acorn forever.")
    world.say(f"In the dream, {hero.pronoun('subject').capitalize()} thought, “What if the fight breaks our friendship?”")
    hero.memes["worry"] += 1

    # Act 3: inner monologue and transformation through sharing.
    world.para()
    world.say(f"When {hero.label} woke up, {hero.pronoun('subject')} listened to {hero.pronoun('possessive')} own thoughts.")
    world.say(f"“I was scared,” {hero.pronoun('subject')} thought, “and I got mad because I wanted to keep everything safe.”")
    world.say(f"{hero.label} looked at the acorn again and realized it could be shared instead of guarded.")
    hero.memes["warmth"] += 1
    friend.memes["warmth"] += 1
    acorn.shared_with.append(friend.id)
    hero.memes["anger"] = 0.0
    friend.memes["anger"] = 0.0
    hero.memes["worry"] = 0.0

    world.say(f"{hero.label} offered the acorn to {friend.label}, then suggested they take turns caring for it.")
    world.say(f"{friend.label} smiled, and the fight melted away.")
    world.say(f"By morning, the little acorn sat between them like a promise, and their friendship felt stronger than before.")

    world.facts["shared"] = True
    world.facts["resolved"] = True
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    hero = world.facts["hero_name"]
    friend = world.facts["friend_name"]
    place = world.facts["place"].name
    return [
        f"Write a heartwarming story about {hero}, an acorn, and a fight that ends in sharing at {place}.",
        f"Tell a gentle story where {hero} has a nightmare after a fight with {friend}, then thinks quietly and changes.",
        "Write a child-friendly story with an inner monologue, a tiny treasure, and a warm ending about friendship.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.facts["hero_name"]
    friend = world.facts["friend_name"]
    place = world.facts["place"].name
    return [
        QAItem(
            question=f"What did {hero} find in {place}?",
            answer=f"{hero} found a small acorn in {place}, and it felt like a tiny treasure.",
        ),
        QAItem(
            question=f"What happened between {hero} and {friend}?",
            answer=f"They had a small fight over the acorn, which made {hero} worry and feel upset.",
        ),
        QAItem(
            question=f"What changed after {hero} woke up from the nightmare?",
            answer=f"{hero} listened to inner thoughts, got calmer, and chose to share the acorn with {friend}.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"The fight ended, the acorn was shared, and their friendship felt stronger and warmer.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an acorn?",
            answer="An acorn is the seed of an oak tree. It is small, hard, and often found on the ground under trees.",
        ),
        QAItem(
            question="What is a nightmare?",
            answer="A nightmare is a very scary dream that can make someone wake up feeling worried or shaky.",
        ),
        QAItem(
            question="What does sharing mean?",
            answer="Sharing means letting someone else use or enjoy something too, which can help people feel kind and close.",
        ),
        QAItem(
            question="What is an inner monologue?",
            answer="An inner monologue is the quiet voice a person hears in their own mind when they think about feelings or choices.",
        ),
        QAItem(
            question="What can happen after a fight?",
            answer="After a fight, people can calm down, talk kindly, apologize, and choose to make peace again.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== Story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        lines.append(
            f"{e.id}: type={e.type}, owner={e.owner}, shared_with={e.shared_with}, "
            f"meters={e.meters}, memes={e.memes}"
        )
    lines.append(f"facts={world.facts}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP helpers
# ---------------------------------------------------------------------------
def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show warm/1. #show nightmare/0. #show hurt/1."))
    shown = set()
    for sym in model:
        if sym.name == "warm" and len(sym.arguments) == 1:
            shown.add(("warm", sym.arguments[0].name))
        elif sym.name == "nightmare" and not sym.arguments:
            shown.add(("nightmare",))
        elif sym.name == "hurt" and len(sym.arguments) == 1:
            shown.add(("hurt", sym.arguments[0].name))
    expected = {("nightmare",), ("hurt", "friend"), ("hurt", "hero")}
    if shown == expected:
        print("OK: ASP parity looks reasonable.")
        return 0
    print("ASP mismatch:", sorted(shown), "expected", sorted(expected))
    return 1


# ---------------------------------------------------------------------------
# Interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming acorn/nightmare/fight storyworld.")
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--hero", choices=sorted(HEROES))
    ap.add_argument("--friend", choices=sorted(FRIENDS))
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
    place = args.place or rng.choice(sorted(PLACES))
    hero = args.hero or rng.choice(sorted(HEROES))
    friends = [f for f in sorted(FRIENDS) if f != hero]
    friend = args.friend or rng.choice(friends)
    if hero == friend:
        raise StoryError("Hero and friend must be different.")
    return StoryParams(place=place, hero=hero, friend=friend)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
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
        print(asp_program("#show warm/1. #show nightmare/0. #show hurt/1."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        for place in sorted(PLACES):
            for hero in sorted(HEROES):
                for friend in sorted(FRIENDS):
                    if hero == friend:
                        continue
                    samples.append(generate(StoryParams(place=place, hero=hero, friend=friend)))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            i += 1
            params = resolve_params(args, random.Random(base_seed + i))
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

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
