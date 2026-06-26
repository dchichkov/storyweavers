#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/haggis_surprise_mystery_to_solve_foreshadowing_slice.py
====================================================================================================

A small slice-of-life story world about an unexpected haggis, a gentle mystery
to solve, and a foreshadowed surprise that turns into a warm ending.
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


@dataclass
class Person:
    id: str
    kind: str = "character"
    type: str = "person"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=lambda: {"distance": 0.0})
    memes: dict[str, float] = field(default_factory=lambda: {"curiosity": 0.0, "joy": 0.0})
    holding: Optional[str] = None

    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Thing:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    hidden: bool = False
    meters: dict[str, float] = field(default_factory=lambda: {"distance": 0.0})
    memes: dict[str, float] = field(default_factory=lambda: {"mystery": 0.0, "surprise": 0.0})


@dataclass
class Place:
    name: str
    indoors: bool = True
    offers: set[str] = field(default_factory=set)


@dataclass
class Clue:
    text: str
    reveals: str


@dataclass
class StoryParams:
    place: str
    name: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, object] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[str] = set()

    def add(self, ent):
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str):
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
        w = World(self.place)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        return w


SETTINGS = {
    "kitchen": Place(name="the kitchen", indoors=True, offers={"tea", "snack", "haggis"}),
    "community_hall": Place(name="the community hall", indoors=True, offers={"tea", "haggis", "music"}),
    "garden_room": Place(name="the garden room", indoors=True, offers={"tea", "cake", "haggis"}),
}

TRAITS = ["quiet", "curious", "cheerful", "thoughtful", "patient"]

HERO_NAMES = ["Mina", "Rory", "Avery", "Noa", "Eli", "Ivy", "Jun", "Piper"]

FOOD = {
    "haggis": {
        "label": "haggis",
        "phrase": "a small warm haggis pie",
        "smell": "a rich, peppery smell",
        "surprise": "a covered dish on the table",
        "clue": "The lid was a little crooked.",
    }
}

ASP_RULES = r"""
place(kitchen).
place(community_hall).
place(garden_room).

offer(kitchen,tea). offer(kitchen,snack). offer(kitchen,haggis).
offer(community_hall,tea). offer(community_hall,haggis). offer(community_hall,music).
offer(garden_room,tea). offer(garden_room,cake). offer(garden_room,haggis).

surprise(Place, haggis) :- offer(Place, haggis).
clue(Place, haggis) :- surprise(Place, haggis).
mystery_to_solve(Place, haggis) :- surprise(Place, haggis), clue(Place, haggis).
foreshadowing(Place, haggis) :- clue(Place, haggis).
#show surprise/2.
#show mystery_to_solve/2.
#show foreshadowing/2.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid, p in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        for item in sorted(p.offers):
            lines.append(asp.fact("offer", pid, item))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show surprise/2.\n#show mystery_to_solve/2.\n#show foreshadowing/2."))
    shown = set((sym.name, tuple(arg.name if arg.type != arg.type.Number and arg.type != arg.type.String else (arg.number if arg.type == arg.type.Number else arg.string) for arg in sym.arguments)) for sym in model)
    expected = {
        ("surprise", ("kitchen", "haggis")),
        ("surprise", ("community_hall", "haggis")),
        ("surprise", ("garden_room", "haggis")),
        ("mystery_to_solve", ("kitchen", "haggis")),
        ("mystery_to_solve", ("community_hall", "haggis")),
        ("mystery_to_solve", ("garden_room", "haggis")),
        ("foreshadowing", ("kitchen", "haggis")),
        ("foreshadowing", ("community_hall", "haggis")),
        ("foreshadowing", ("garden_room", "haggis")),
    }
    if shown == expected:
        print("OK: ASP parity verified.")
        return 0
    print("MISMATCH")
    print("shown:", sorted(shown))
    print("expected:", sorted(expected))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life story world: haggis, surprise, mystery, foreshadowing.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--name")
    ap.add_argument("--trait", choices=TRAITS)
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
    place = args.place or rng.choice(list(SETTINGS))
    name = args.name or rng.choice(HERO_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, name=name, trait=trait)


def _story_intro(world: World, hero: Person, haggis: Thing) -> None:
    world.say(f"{hero.id} was a {hero.traits[0]} person who liked quiet afternoons in {world.place.name}.")
    world.say(f"On the table, there was {haggis.phrase}. It gave off {FOOD['haggis']['smell']}, and that made {hero.id} curious.")


def _foreshadow(world: World, haggis: Thing) -> None:
    if "foreshadowed" in world.fired:
        return
    world.fired.add("foreshadowed")
    world.say(f"{FOOD['haggis']['clue']} {hero_name_from_world(world)} noticed it before anyone lifted the lid.")


def hero_name_from_world(world: World) -> str:
    return world.facts["hero"].id


def _mystery_turn(world: World, hero: Person, haggis: Thing) -> None:
    hero.memes["curiosity"] += 1
    haggis.memes["mystery"] += 1
    world.say(f"{hero.id} leaned closer and wondered who the haggis was for.")
    world.say(f"That was the little mystery to solve, and {hero.pronoun('subject')} decided to ask instead of guessing.")


def _surprise_reveal(world: World, hero: Person, haggis: Thing) -> None:
    if "reveal" in world.fired:
        return
    world.fired.add("reveal")
    world.say(f"Then the host smiled and lifted the lid. The haggis was the surprise for the shared supper.")
    world.say(f"{hero.id} laughed, because the smell had seemed mysterious only until the plate was announced.")


def _closing(world: World, hero: Person, haggis: Thing) -> None:
    hero.memes["joy"] += 1
    world.say(f"{hero.id} stayed at the table, warm and happy, while everyone passed around small bites and tea.")
    world.say(f"By the end, the haggis was no longer a mystery at all; it had become part of a calm, ordinary evening.")


def generate_world(params: StoryParams) -> World:
    place = SETTINGS[params.place]
    world = World(place)
    hero = world.add(Person(id=params.name, traits=[params.trait]))
    haggis = world.add(Thing(id="haggis", label="haggis", phrase=FOOD["haggis"]["phrase"]))
    world.facts["hero"] = hero
    world.facts["haggis"] = haggis
    _story_intro(world, hero, haggis)
    world.para()
    _foreshadow(world, haggis)
    _mystery_turn(world, hero, haggis)
    world.para()
    _surprise_reveal(world, hero, haggis)
    _closing(world, hero, haggis)
    return world


def generation_prompts(world: World) -> list[str]:
    hero = world.facts["hero"]
    place = world.place.name
    return [
        f"Write a slice-of-life story about {hero.id} at {place} with a gentle haggis surprise.",
        f"Tell a short child-friendly story that uses foreshadowing, a mystery to solve, and the word haggis.",
        f"Write an ordinary-feeling story where a quiet moment turns into a warm surprise around haggis.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.facts["hero"]
    place = world.place.name
    return [
        QAItem(
            question=f"Where was {hero.id} when the haggis surprise happened?",
            answer=f"{hero.id} was at {place}, where a shared supper was taking place."
        ),
        QAItem(
            question=f"What was the mystery to solve in the story?",
            answer="The mystery was who the haggis was meant for and why it had been covered up."
        ),
        QAItem(
            question=f"What clue foreshadowed the surprise?",
            answer="The slightly crooked lid was a small clue that hinted something special was waiting underneath."
        ),
        QAItem(
            question=f"How did the story end for {hero.id}?",
            answer=f"It ended with {hero.id} feeling happy and settled at the table after the haggis surprise was revealed."
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is haggis?",
            answer="Haggis is a traditional savory dish that can be served warm at a meal."
        ),
        QAItem(
            question="What is foreshadowing?",
            answer="Foreshadowing is when a story gives a small hint early on about something that will matter later."
        ),
        QAItem(
            question="What is a mystery to solve in a story?",
            answer="A mystery to solve is a question the characters need to figure out before the story can fully make sense."
        ),
        QAItem(
            question="What makes a slice-of-life story feel ordinary?",
            answer="A slice-of-life story focuses on everyday moments, small worries, and gentle changes instead of big adventures."
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(f"  {e.id:8} ({e.kind})")
        if getattr(e, "traits", None):
            lines.append(f"    traits={e.traits}")
        if getattr(e, "phrase", ""):
            lines.append(f"    phrase={e.phrase}")
        if getattr(e, "memes", None):
            lines.append(f"    memes={dict(e.memes)}")
    lines.append(f"  fired={sorted(world.fired)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World questions ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def generate(params: StoryParams) -> StorySample:
    world = generate_world(params)
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


CURATED = [
    StoryParams(place="kitchen", name="Mina", trait="curious"),
    StoryParams(place="community_hall", name="Rory", trait="thoughtful"),
    StoryParams(place="garden_room", name="Ivy", trait="cheerful"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show surprise/2.\n#show mystery_to_solve/2.\n#show foreshadowing/2."))
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
        while len(samples) < args.n and i < max(50, args.n * 50):
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
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
