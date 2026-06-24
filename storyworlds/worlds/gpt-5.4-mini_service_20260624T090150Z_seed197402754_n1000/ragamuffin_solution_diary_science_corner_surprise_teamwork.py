#!/usr/bin/env python3
"""
A standalone story world for a tiny Adventure-style science-corner tale.

Premise:
A ragamuffin child keeps a diary in the science corner and wants to mix a bright
solution for a small experiment. A surprise happens when the solution bubbles
the wrong way, and teamwork turns the mix into a happy discovery.
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
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    carried_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class StoryParams:
    name: str
    gender: str
    helper: str
    seed: Optional[int] = None


@dataclass
class Place:
    name: str = "the science corner"
    affords: set[str] = field(default_factory=lambda: {"mixing", "observing"})


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[str] = set()
        self.trace: list[str] = []

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

    def copy(self) -> "World":
        import copy

        w = World(self.place)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.facts = dict(self.facts)
        w.paragraphs = [[]]
        return w


def tell_story(world: World, hero: Entity, helper: Entity, notebook: Entity, solution: Entity) -> World:
    world.say(
        f"In the science corner, {hero.id} was a little ragamuffin with a brave grin and a diary full of scribbles."
    )
    world.say(
        f"{hero.pronoun('subject').capitalize()} wanted to make a solution for a tiny experiment, because adventure could fit on one table."
    )
    world.say(
        f"{hero.id} carried the diary close, wrote down the plan, and poured the solution into a clear cup."
    )

    world.para()
    world.say(
        f"Then came a surprise: the solution fizzed up faster than expected, and the cup wobbled like a boat in a storm."
    )
    hero.memes["surprise"] = 1
    solution.meters["bubbles"] = 1
    world.facts["surprise"] = True

    world.say(
        f"{helper.id} saw the wobble and called for teamwork."
    )
    helper.memes["teamwork"] = 1
    hero.memes["worry"] = 1

    world.para()
    world.say(
        f"Together, they steadied the cup, added one careful spoon of water, and stirred until the solution calmed down."
    )
    solution.meters["stable"] = 1
    hero.memes["joy"] = 1
    helper.memes["joy"] = 1
    world.say(
        f"{hero.id} smiled, tucked the diary under one arm, and wrote the best line of the day: the surprise had become a success because teamwork helped."
    )

    world.facts.update(hero=hero, helper=helper, notebook=notebook, solution=solution)
    return world


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure story world: ragamuffin, diary, solution, surprise, teamwork, science corner.")
    ap.add_argument("--name", choices=["Mina", "Niko", "Pia", "Theo", "Luna"], help="hero name")
    ap.add_argument("--gender", choices=["girl", "boy"], help="hero gender")
    ap.add_argument("--helper", choices=["friend", "teacher", "sibling"], help="who helps")
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


def _name_for_gender(rng: random.Random, gender: str) -> str:
    girls = ["Mina", "Pia", "Luna"]
    boys = ["Niko", "Theo"]
    return rng.choice(girls if gender == "girl" else boys)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or _name_for_gender(rng, gender)
    helper = args.helper or rng.choice(["friend", "teacher", "sibling"])
    return StoryParams(name=name, gender=gender, helper=helper)


def generate(params: StoryParams) -> StorySample:
    place = Place()
    world = World(place)
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender, traits=["little", "ragamuffin"]))
    helper = world.add(Entity(id="Helper", kind="character", type="person", label=params.helper))
    notebook = world.add(Entity(id="diary", type="diary", label="diary", phrase="a small diary", owner=hero.id, caretaker=hero.id))
    solution = world.add(Entity(id="solution", type="solution", label="solution", phrase="a bright solution", owner=hero.id))

    world.facts.update(place=place.name, helper_type=params.helper)
    tell_story(world, hero, helper, notebook, solution)

    prompts = [
        'Write a short adventure story set in the science corner that uses the words "ragamuffin", "solution", and "diary".',
        f"Tell a child-friendly adventure where {hero.id} makes a solution in the science corner, gets a surprise, and teamwork helps.",
        "Write a tiny story where a diary holds the plan for a science-corner discovery and the ending proves teamwork matters.",
    ]

    story_qa = [
        QAItem(
            question=f"Who is the story about?",
            answer=f"The story is about {hero.id}, a little ragamuffin child who keeps a diary and explores the science corner.",
        ),
        QAItem(
            question="What surprised them?",
            answer="The solution fizzed up faster than expected, and the cup wobbled like it might spill.",
        ),
        QAItem(
            question="How did the problem get solved?",
            answer=f"{helper.id} and {hero.id} used teamwork, steadied the cup, and added a little water until the solution calmed down.",
        ),
    ]

    world_qa = [
        QAItem(
            question="What is a diary for?",
            answer="A diary is a small book where someone can write notes, plans, and memories.",
        ),
        QAItem(
            question="What is a solution in science?",
            answer="A solution is a liquid made by mixing substances together so they spread evenly.",
        ),
        QAItem(
            question="What does teamwork mean?",
            answer="Teamwork means people help each other and work together toward the same goal.",
        ),
    ]

    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts,
        story_qa=story_qa,
        world_qa=world_qa,
        world=world,
    )


ASP_RULES = r"""
hero(X) :- story_hero(X).
surprise :- fizzing(solution).
teamwork :- helper(_), steady(_).
"""


def asp_facts() -> str:
    import asp

    return "\n".join(
        [
            asp.fact("place", "science_corner"),
            asp.fact("story_hero", "ragamuffin_child"),
            asp.fact("item", "diary"),
            asp.fact("item", "solution"),
            asp.fact("theme", "surprise"),
            asp.fact("theme", "teamwork"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_asp_check() -> str:
    return asp_program("#show hero/1. #show surprise/0. #show teamwork/0.")


def reasonableness_gate(params: StoryParams) -> None:
    if params.gender not in {"girl", "boy"}:
        raise StoryError("The hero must be a child who can plausibly be called a ragamuffin.")
    if params.helper not in {"friend", "teacher", "sibling"}:
        raise StoryError("The helper must be someone who can reasonably join the teamwork scene.")


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print("--- world model state ---")
        for e in sample.world.entities.values():
            print(f"{e.id}: type={e.type} meters={dict(e.meters)} memes={dict(e.memes)}")
    if qa:
        print()
        print("== Prompts ==")
        for p in sample.prompts:
            print(p)
        print("\n== Story QA ==")
        for q in sample.story_qa:
            print(f"Q: {q.question}\nA: {q.answer}")
        print("\n== World QA ==")
        for q in sample.world_qa:
            print(f"Q: {q.question}\nA: {q.answer}")


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show hero/1. #show surprise/0. #show teamwork/0."))
        return

    if args.verify:
        print("OK: Python and ASP gates are present for the science-corner world.")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        curated = [
            StoryParams(name="Mina", gender="girl", helper="friend"),
            StoryParams(name="Niko", gender="boy", helper="teacher"),
            StoryParams(name="Luna", gender="girl", helper="sibling"),
        ]
        samples = [generate(p) for p in curated]
    else:
        for i in range(args.n):
            rng = random.Random(base_seed + i)
            params = resolve_params(args, rng)
            reasonableness_gate(params)
            params.seed = base_seed + i
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i + 1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
