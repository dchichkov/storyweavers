#!/usr/bin/env python3
"""
A tiny nursery-rhyme storyworld about a stew mystery that gets solved.

Seed tale:
---
In a little kitchen by the hill, there was a pot of stew that no one could explain.
The spoon went missing, the carrot floated, and the clock kept ticking.
Mina the mouse wanted supper, but Gran said, "Not until we find what made the stew go strange."
So Mina looked under the table, the cat looked in the cupboard, and the little mystery finally turned out to be a dropped berry from the pie bowl.
They fished it out, stirred the pot, and the stew smelled sweet and warm again.

This world keeps the story close to a nursery rhyme: simple, sing-song, concrete,
and centered on one small mystery that changes the meal.
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
    label: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    owner: Optional[str] = None

    def name(self) -> str:
        return self.label or self.id


@dataclass
class Kitchen:
    place: str = "the little kitchen"
    mood: str = "soft"
    rhyme_level: int = 1


@dataclass
class Clue:
    id: str
    label: str
    hidden_in: str
    reveals: str
    tasty: bool = False


@dataclass
class StoryParams:
    seed: Optional[int] = None
    kitchen: str = "little_kitchen"
    hero: str = "Mina"
    helper: str = "Gran"
    animal: str = "mouse"
    mystery: str = "stew"
    clue: str = "berry"
    rhyme_style: str = "nursery"


class World:
    def __init__(self, kitchen: Kitchen):
        self.kitchen = kitchen
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
        self.trace: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.trace.append(text)

    def render(self) -> str:
        return " ".join(self.trace).strip()


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
KITCHENS = {
    "little_kitchen": Kitchen(place="the little kitchen", mood="soft", rhyme_level=1),
}

HEROES = ["Mina", "Nina", "Lila", "Pippa", "Tilly"]
HELPERS = ["Gran", "Aunt May", "Mum", "Dad", "Old Ben"]
ANIMALS = ["mouse", "cat", "duck", "dog", "sparrow"]

CLUES = {
    "berry": Clue(id="berry", label="a berry", hidden_in="pie bowl", reveals="a sweet red stain", tasty=True),
    "pea": Clue(id="pea", label="a pea", hidden_in="spoon drawer", reveals="a round green pea", tasty=True),
    "leaf": Clue(id="leaf", label="a leaf", hidden_in="window sill", reveals="a dry brown leaf", tasty=False),
    "crumb": Clue(id="crumb", label="a crumb", hidden_in="bread basket", reveals="a tiny bread crumb", tasty=True),
}

MYSTERIES = {
    "stew": {
        "label": "stew",
        "image": "a pot of stew",
        "problem": "the stew looked strange",
        "turn": "the spoon went missing",
        "fix": "the mystery was solved",
    }
}


# ---------------------------------------------------------------------------
# Reasonableness gates
# ---------------------------------------------------------------------------
def valid_combo(hero: str, helper: str, animal: str, clue: str) -> bool:
    return hero != helper and clue in CLUES and animal in ANIMALS


def explain_invalid(hero: str, helper: str, animal: str, clue: str) -> str:
    if hero == helper:
        return "(No story: the hero and helper need to be different voices in the rhyme.)"
    if clue not in CLUES:
        return "(No story: that clue is not in the little kitchen.)"
    if animal not in ANIMALS:
        return "(No story: that animal does not belong in this nursery-rhyme kitchen.)"
    return "(No story: the requested parts do not make a tidy mystery.)"


# ---------------------------------------------------------------------------
# Story mechanics
# ---------------------------------------------------------------------------
def introduce(world: World, hero: Entity, helper: Entity, animal: Entity, stew: Entity) -> None:
    world.say(f"In {world.kitchen.place}, {hero.name()} was small and bright,")
    world.say(f"and {helper.name()} kept the pot in gentle sight.")
    world.say(f"{animal.name().capitalize()} peeped close by the chair,")
    world.say(f"while {stew.name()} puffed warm smells into the air.")


def trouble(world: World, hero: Entity, helper: Entity, stew: Entity, clue: Clue) -> None:
    stew.memes["mystery"] = 1
    hero.memes["curious"] = 1
    world.say(f"But oh dear me, the stew looked wrong,")
    world.say(f"too odd, too dark, and not quite strong.")
    world.say(f"{helper.name()} said, “We must not guess;")
    world.say(f"let's find the thing that caused this mess.”")
    world.facts["problem"] = f"{stew.name()} looked strange"
    world.facts["clue_hidden_in"] = clue.hidden_in


def search(world: World, hero: Entity, animal: Entity, clue: Clue) -> None:
    hero.memes["searching"] = 1
    animal.memes["helpful"] = 1
    world.say(f"{hero.name()} peeked below the stool,")
    world.say(f"{animal.name().capitalize()} looked in the spoon and bowl.")
    world.say(f"They found {clue.label} tucked away,")
    world.say(f"the very thing to save the day.")


def solve(world: World, helper: Entity, stew: Entity, clue: Clue) -> None:
    stew.meters["sweetness"] = 1 if clue.tasty else 0
    stew.meters["clean"] = 1
    stew.memes["mystery"] = 0
    world.say(f"{helper.name()} fished it out with care,")
    world.say(f"and stirred the pot with a little flair.")
    if clue.tasty:
        world.say(f"The stew grew sweet, and warm, and mild,")
    else:
        world.say(f"The stew grew clear and kind and mild,")
    world.say(f"and everyone smiled, each grown-up and child.")
    world.say(f"The mystery solved, the day felt bright,")
    world.say(f"and supper was ready by candlelight.")
    world.facts["solution"] = clue.reveals
    world.facts["resolved"] = True


def tell_story(params: StoryParams) -> World:
    kitchen = KITCHENS[params.kitchen]
    world = World(kitchen)

    hero = world.add(Entity(id=params.hero, kind="character", label=params.hero))
    helper = world.add(Entity(id=params.helper, kind="character", label=params.helper))
    animal = world.add(Entity(id=params.animal, kind="character", label=params.animal))
    stew = world.add(Entity(id=params.mystery, kind="thing", label=params.mystery))
    clue = CLUES[params.clue]

    world.facts.update(
        hero=hero,
        helper=helper,
        animal=animal,
        stew=stew,
        clue=clue,
        kitchen=kitchen,
    )

    introduce(world, hero, helper, animal, stew)
    world.say("")
    trouble(world, hero, helper, stew, clue)
    world.say("")
    search(world, hero, animal, clue)
    world.say("")
    solve(world, helper, stew, clue)
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    clue: Clue = f["clue"]
    return [
        f"Write a short nursery-rhyme story about {hero.name()} and {helper.name()} solving a stew mystery.",
        f"Tell a simple rhyming tale in which a child finds {clue.label} and helps make the stew right again.",
        "Write a gentle story with a tiny mystery, a search, and a warm supper at the end.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    clue: Clue = f["clue"]
    stew: Entity = f["stew"]
    return [
        QAItem(
            question=f"Who looked for the clue in the little kitchen?",
            answer=f"{hero.name()} looked for the clue, and {helper.name()} helped by guiding the search.",
        ),
        QAItem(
            question=f"What was strange about the stew?",
            answer=f"{stew.name().capitalize()} looked strange, so the kitchen team had to solve the mystery before supper.",
        ),
        QAItem(
            question=f"What clue did they find?",
            answer=f"They found {clue.label} hidden in the {clue.hidden_in}, which showed what had made the stew odd.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer="The clue was taken out, the stew was stirred again, and the supper became warm and happy.",
        ),
    ]


WORLD_KNOWLEDGE = [
    QAItem(
        question="What is stew?",
        answer="Stew is a warm food cooked slowly in a pot with vegetables, broth, and sometimes meat or beans.",
    ),
    QAItem(
        question="Why do people stir stew?",
        answer="People stir stew so the food cooks evenly and the flavors mix together well.",
    ),
    QAItem(
        question="What is a clue?",
        answer="A clue is a small bit of information that helps solve a mystery.",
    ),
]


def world_qa(world: World) -> list[QAItem]:
    return list(WORLD_KNOWLEDGE)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
hero(H) :- hero_name(H).
helper(H) :- helper_name(H).
animal(A) :- animal_name(A).
clue(C) :- clue_name(C).

valid_story(H, He, A, C) :- hero(H), helper(He), animal(A), clue(C), H != He.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for name in HEROES:
        lines.append(asp.fact("hero_name", name))
    for name in HELPERS:
        lines.append(asp.fact("helper_name", name))
    for name in ANIMALS:
        lines.append(asp.fact("animal_name", name))
    for name in CLUES:
        lines.append(asp.fact("clue_name", name))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> set[tuple[str, str, str, str]]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return set(asp.atoms(model, "valid_story"))


def asp_verify() -> int:
    py = set()
    for h in HEROES:
        for he in HELPERS:
            for a in ANIMALS:
                for c in CLUES:
                    if valid_combo(h, he, a, c):
                        py.add((h, he, a, c))
    cl = asp_valid_stories()
    if py == cl:
        print(f"OK: ASP and Python agree on {len(py)} valid story tuples.")
        return 0
    print("MISMATCH between ASP and Python.")
    if py - cl:
        print("Only in Python:", sorted(py - cl))
    if cl - py:
        print("Only in ASP:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------
def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.hero and args.helper and args.hero == args.helper:
        raise StoryError("(No story: the hero and helper must be different.)")
    hero = args.hero or rng.choice(HEROES)
    helper = args.helper or rng.choice([h for h in HELPERS if h != hero])
    animal = args.animal or rng.choice(ANIMALS)
    clue = args.clue or rng.choice(list(CLUES))
    if not valid_combo(hero, helper, animal, clue):
        raise StoryError(explain_invalid(hero, helper, animal, clue))
    return StoryParams(
        seed=args.seed,
        kitchen="little_kitchen",
        hero=hero,
        helper=helper,
        animal=animal,
        mystery="stew",
        clue=clue,
        rhyme_style="nursery",
    )


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
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
        print()
        print("--- world trace ---")
        for k, v in sample.world.facts.items():
            if isinstance(v, Entity):
                print(f"{k}: {v.name()}")
            elif isinstance(v, Clue):
                print(f"{k}: {v.label}")
            elif isinstance(v, Kitchen):
                print(f"{k}: {v.place}")
            else:
                print(f"{k}: {v}")
    if qa:
        print()
        print("== prompts ==")
        for i, p in enumerate(sample.prompts, 1):
            print(f"{i}. {p}")
        print()
        print("== story q&a ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
        print()
        print("== world q&a ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Nursery-rhyme stew mystery storyworld.")
    ap.add_argument("--hero", choices=HEROES)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--animal", choices=ANIMALS)
    ap.add_argument("--clue", choices=list(CLUES))
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


CURATED = [
    StoryParams(hero="Mina", helper="Gran", animal="mouse", clue="berry"),
    StoryParams(hero="Nina", helper="Dad", animal="cat", clue="crumb"),
    StoryParams(hero="Lila", helper="Aunt May", animal="duck", clue="pea"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show valid_story/4."))
        print(sorted(set(asp.atoms(model, "valid_story"))))
        return

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        base = args.seed if args.seed is not None else random.randrange(2**31)
        samples = []
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
                return
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
