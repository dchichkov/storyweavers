#!/usr/bin/env python3
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
    kind: str = "animal"
    species: str = "animal"
    name: str = ""
    role: str = ""
    place: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def subject(self) -> str:
        return self.name or self.id

    def possessive(self) -> str:
        return f"{self.subject()}'s"


@dataclass
class Place:
    id: str
    label: str
    kind: str = "school"
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    protagonist: str
    helper: str
    name: str
    helper_name: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
        self.paragraphs: list[list[str]] = [[]]

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
    "schoolyard": Place(id="schoolyard", label="the schoolyard", tags={"school", "outside"}),
    "hallway": Place(id="hallway", label="the hallway", tags={"school", "inside"}),
    "library": Place(id="library", label="the library corner", tags={"school", "quiet"}),
}

SPECIES = {
    "rabbit": "rabbit",
    "fox": "fox",
    "bear": "bear",
    "cat": "cat",
    "dog": "dog",
    "mouse": "mouse",
}

NAMES = {
    "rabbit": ["Nina", "Milo", "Pip", "Ruby", "Luna"],
    "fox": ["Tara", "Finn", "Sage", "Junie", "Perry"],
    "bear": ["Ollie", "Benny", "Hazel", "Marta", "Toby"],
    "cat": ["Mina", "Cleo", "Iris", "Sunny", "Niko"],
    "dog": ["Remy", "Barkley", "Moss", "Penny", "Daisy"],
    "mouse": ["Tia", "Momo", "Bea", "Nell", "Wren"],
}

TRAITS = ["kind", "shy", "brave", "gentle", "curious", "patient"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal Story world: kindness, experience, and a sophomore animal at school.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--protagonist", choices=SPECIES)
    ap.add_argument("--helper", choices=SPECIES)
    ap.add_argument("--name")
    ap.add_argument("--helper-name")
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
    protagonist = args.protagonist or rng.choice(list(SPECIES))
    helper = args.helper or rng.choice([s for s in SPECIES if s != protagonist])
    name = args.name or rng.choice(NAMES[protagonist])
    helper_name = args.helper_name or rng.choice(NAMES[helper])
    return StoryParams(place=place, protagonist=protagonist, helper=helper, name=name, helper_name=helper_name)


def select_name(species: str, used: set[str], rng: random.Random) -> str:
    options = [n for n in NAMES[species] if n not in used]
    if not options:
        options = NAMES[species]
    choice = rng.choice(options)
    used.add(choice)
    return choice


def generate_story(world: World, params: StoryParams) -> None:
    hero = world.add(Entity(id="hero", species=params.protagonist, name=params.name, role="sophomore"))
    helper = world.add(Entity(id="helper", species=params.helper, name=params.helper_name, role="friend"))
    new_student = world.add(Entity(id="new_student", species="mouse", name="Mimi", role="new student"))

    hero.meters["experience"] = 2.0
    hero.memes["kindness"] = 1.0
    helper.memes["worry"] = 1.0
    new_student.memes["nervous"] = 2.0

    world.say(
        f"{hero.subject()} was a sophomore {hero.species} who had a little experience with school, "
        f"but {hero.possessive()} heart was full of kindness."
    )
    world.say(
        f"At {world.place.label}, {hero.subject()} saw {new_student.subject()} standing alone with a too-big bag and droopy ears."
    )
    world.say(
        f"{hero.subject()} remembered how scary the first days of school could feel, so {hero.subject()} walked over and said hello in a soft voice."
    )
    world.para()

    hero.memes["kindness"] += 1.0
    helper.meters["experience"] = 1.0
    new_student.memes["nervous"] -= 1.5
    new_student.memes["hope"] = 1.0

    world.say(
        f"First {hero.subject()} showed {new_student.subject()} where to hang the bag, then {hero.subject()} shared a pencil and a smile."
    )
    world.say(
        f"{helper.subject()} watched from nearby and noticed that {hero.subject()} made the whole corner feel less lonely."
    )
    world.para()

    hero.meters["experience"] += 1.0
    new_student.memes["safe"] = 1.0
    helper.memes["admiration"] = 1.0

    world.say(
        f"When the bell rang, {new_student.subject()} walked beside {hero.subject()} instead of behind."
    )
    world.say(
        f"{hero.subject()} felt proud, because a little kindness had turned an ordinary school day into a good experience for everyone."
    )

    world.facts.update(
        hero=hero,
        helper=helper,
        new_student=new_student,
        place=world.place,
    )


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    new_student = f["new_student"]
    place = f["place"]
    return [
        QAItem(
            question=f"Who was the sophomore in the story?",
            answer=f"{hero.subject()} was the sophomore {hero.species} in the story.",
        ),
        QAItem(
            question=f"Why did {hero.subject()} help {new_student.subject()} at {place.label}?",
            answer=f"{hero.subject()} helped because {hero.subject()} remembered an experience with school that felt scary and wanted to show kindness.",
        ),
        QAItem(
            question=f"What changed after {hero.subject()} was kind?",
            answer=f"{new_student.subject()} felt less nervous, and the school day turned into a better experience for everyone.",
        ),
        QAItem(
            question=f"What did {helper.subject()} notice about {hero.subject()}?",
            answer=f"{helper.subject()} noticed that {hero.subject()} made the corner feel less lonely by being kind.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does kindness mean?",
            answer="Kindness means being gentle, caring, and helpful to someone else.",
        ),
        QAItem(
            question="What is a sophomore?",
            answer="A sophomore is a student in the second year of school at that level.",
        ),
        QAItem(
            question="What is experience?",
            answer="Experience is what you learn by doing something or being part of it.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    place = f["place"]
    return [
        f"Write an animal story about a sophomore {hero.species} at {place.label} who uses kindness to help a new student.",
        f"Tell a child-friendly story where experience helps {hero.subject()} notice someone who feels shy.",
        f"Write a gentle school story with animals, a sophomore, and a kind choice that makes the day better.",
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for ent in world.entities.values():
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        lines.append(f"  {ent.id}: species={ent.species} role={ent.role} meters={meters} memes={memes}")
    return "\n".join(lines)


ASP_RULES = r"""
hero_kind(H) :- hero(H), kindness(H, K), K > 0.
helped(New) :- hero(H), new_student(New), kindness(H, K), K > 0.
good_experience(H) :- experience(H, E), E > 0, kindness(H, K), K > 0.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for sp in SPECIES:
        lines.append(asp.fact("species", sp))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    return 0


def select_story_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return resolve_params(args, rng)


def generate(params: StoryParams) -> StorySample:
    world = World(PLACES[params.place])
    generate_story(world, params)
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
        print("== (1) Generation prompts -- asks that would produce this story ==")
        for i, p in enumerate(sample.prompts, 1):
            print(f"{i}. {p}")
        print()
        print("== (2) Story questions -- answerable from the story text ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
        print()
        print("== (3) World-knowledge questions -- child level, no story needed ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show hero_kind/1.\n#show helped/1.\n#show good_experience/1."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        curated = [
            StoryParams(place="schoolyard", protagonist="rabbit", helper="cat", name="Nina", helper_name="Cleo"),
            StoryParams(place="hallway", protagonist="fox", helper="dog", name="Sage", helper_name="Remy"),
            StoryParams(place="library", protagonist="bear", helper="mouse", name="Hazel", helper_name="Tia"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            i += 1
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
            header = f"### {p.name}: {p.protagonist} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
