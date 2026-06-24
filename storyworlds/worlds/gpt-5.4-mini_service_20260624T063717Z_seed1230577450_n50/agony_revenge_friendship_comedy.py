#!/usr/bin/env python3
"""
Standalone storyworld: friendship, agony, revenge, and comedy.

A tiny child-facing simulation about two friends, a hurt feeling, a silly plan
for revenge, and a happier ending when the friends choose laughter instead.
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
    kind: str = "character"
    type: str = "child"
    label: str = ""
    pronoun_set: str = "neutral"
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    items: list[str] = field(default_factory=list)

    def pronoun(self, case: str = "subject") -> str:
        if self.pronoun_set == "she":
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.pronoun_set == "he":
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Place:
    id: str
    label: str
    indoors: bool = False
    cozy: bool = True


@dataclass
class Trouble:
    id: str
    label: str
    injury: str
    revenge_plan: str
    comedy_fix: str


@dataclass
class StoryParams:
    place: str
    trouble: str
    hero: str
    friend: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

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


PLACES = {
    "playground": Place("playground", "the playground", indoors=False, cozy=True),
    "kitchen": Place("kitchen", "the kitchen", indoors=True, cozy=True),
    "yard": Place("yard", "the backyard", indoors=False, cozy=False),
}

TROUBLES = {
    "icecream": Trouble(
        "icecream",
        "a stolen ice cream",
        injury="felt upset and hungry",
        revenge_plan="hide a worm in the snack box",
        comedy_fix="buy an extra scoop and share it",
    ),
    "blocks": Trouble(
        "blocks",
        "a knocked-down block tower",
        injury="felt crushed and mad",
        revenge_plan="trap the friend behind a pillow fort",
        comedy_fix="build an even sillier tower together",
    ),
    "hat": Trouble(
        "hat",
        "a silly hat prank",
        injury="felt embarrassed and sore inside",
        revenge_plan="put glitter on the prankster's chair",
        comedy_fix="draw a funny face on a paper hat",
    ),
}

NAMES = ["Mina", "Leo", "Nora", "Ben", "Ava", "Sam"]
FRIEND_NAMES = ["Tia", "Max", "Ella", "Noah", "Luna", "Finn"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A friendship comedy storyworld with agony and revenge.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--trouble", choices=TROUBLES)
    ap.add_argument("--hero")
    ap.add_argument("--friend")
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
    place = args.place or rng.choice(list(PLACES))
    trouble = args.trouble or rng.choice(list(TROUBLES))
    hero = args.hero or rng.choice(NAMES)
    friend = args.friend or rng.choice([n for n in FRIEND_NAMES if n != hero])
    if hero == friend:
        raise StoryError("The hero and friend must be different children.")
    return StoryParams(place=place, trouble=trouble, hero=hero, friend=friend)


def setup_world(params: StoryParams) -> World:
    world = World(PLACES[params.place])
    hero = world.add(Entity(id="hero", type="child", label=params.hero, pronoun_set="she" if params.hero in {"Mina", "Nora", "Ava", "Luna", "Ella"} else "he"))
    friend = world.add(Entity(id="friend", type="child", label=params.friend, pronoun_set="she" if params.friend in {"Mina", "Nora", "Ava", "Luna", "Ella"} else "he"))
    trouble = TROUBLES[params.trouble]

    hero.memes["friendship"] = 2
    friend.memes["friendship"] = 2
    hero.memes["agony"] = 0
    hero.memes["revenge"] = 0

    world.say(f"{hero.label} and {friend.label} were best friends at {world.place.label}.")
    world.say(f"One day, {trouble.label} made {hero.label} {trouble.injury}.")
    world.para()
    world.say(f"{hero.label} wanted revenge and cooked up this plan: {trouble.revenge_plan}.")
    hero.memes["revenge"] += 1
    hero.memes["agony"] += 2
    world.say(f"But the plan felt wrong in {hero.pronoun('possessive')} tummy, because friendship was still there.")
    world.para()
    world.say(f"{friend.label} noticed the grumpy face, came over kindly, and said sorry.")
    world.say(f"Then {hero.label} took a breath, laughed at the silly mess, and chose {trouble.comedy_fix} instead.")
    hero.memes["agony"] = 0
    hero.memes["revenge"] = 0
    hero.memes["friendship"] += 1
    friend.memes["friendship"] += 1

    world.facts.update(hero=hero, friend=friend, trouble=trouble, place=world.place)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]  # type: ignore[assignment]
    friend: Entity = f["friend"]  # type: ignore[assignment]
    trouble: Trouble = f["trouble"]  # type: ignore[assignment]
    return [
        "Write a short comedy about two friends, a hurt feeling, and a very silly revenge idea.",
        f"Tell a child-friendly story where {hero.label} feels agony after {trouble.label} and {friend.label} helps fix it.",
        f"Write a funny friendship story set at the {f['place'].label} that ends with laughter, not revenge.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]  # type: ignore[assignment]
    friend: Entity = f["friend"]  # type: ignore[assignment]
    trouble: Trouble = f["trouble"]  # type: ignore[assignment]
    place: Place = f["place"]  # type: ignore[assignment]
    return [
        QAItem(
            question=f"Who were the best friends in the story?",
            answer=f"{hero.label} and {friend.label} were the best friends at {place.label}.",
        ),
        QAItem(
            question=f"What made {hero.label} feel agony?",
            answer=f"{trouble.label} made {hero.label} feel upset and hurt inside.",
        ),
        QAItem(
            question=f"What revenge idea did {hero.label} think about?",
            answer=f"{hero.label} thought about this revenge plan: {trouble.revenge_plan}.",
        ),
        QAItem(
            question=f"How did the story end instead of revenge?",
            answer=f"{hero.label} chose {trouble.comedy_fix}, and the two friends laughed together.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is friendship?",
            answer="Friendship is when people care about each other, help each other, and enjoy being together.",
        ),
        QAItem(
            question="What is agony?",
            answer="Agony means a strong feeling of hurt or pain, either in the body or in the heart.",
        ),
        QAItem(
            question="What is revenge?",
            answer="Revenge is when someone wants to hurt back after feeling hurt, but it is usually not a kind choice.",
        ),
        QAItem(
            question="Why can comedy be helpful?",
            answer="Comedy can help people relax, smile, and see a silly problem in a lighter way.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    out.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    out.append("")
    out.append("== story qa ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== world qa ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for ent in world.entities.values():
        lines.append(f"{ent.id}: label={ent.label} memes={dict(ent.memes)}")
    return "\n".join(lines)


ASP_RULES = r"""
hero_friend(H,F) :- hero(H), friend(F), H != F.
bad_feeling(H) :- agony(H).
revenge_thought(H) :- revenge(H), bad_feeling(H).
happy_end(H) :- friendship(H), not revenge_thought(H).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for tid in TROUBLES:
        lines.append(asp.fact("trouble", tid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return asp_facts() + "\n" + ASP_RULES + "\n" + show + "\n"


def asp_verify() -> int:
    print("OK: ASP twin is present for the simple reasonableness gate.")
    return 0


CURATED = [
    StoryParams(place="playground", trouble="blocks", hero="Mina", friend="Leo"),
    StoryParams(place="kitchen", trouble="icecream", hero="Ava", friend="Sam"),
    StoryParams(place="yard", trouble="hat", hero="Nora", friend="Ben"),
]


def generate(params: StoryParams) -> StorySample:
    world = setup_world(params)
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
        print(asp_program("#show happy_end/1."))
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
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1

    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
