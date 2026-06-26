#!/usr/bin/env python3
"""
A small standalone storyworld: a space-adventure misunderstanding around a stair
covered in crud, ending in a happy transformation.

Seed premise:
- In a space station, a child-sized helper sees crud on a stair and thinks it is
  a dangerous alien sign.
- A pilot explains it is only engine crud from a repair, then they clean and
  transform the stair into a bright, safe passage.
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


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    name: str = "the space station"
    setting: str = "orbit"
    features: set[str] = field(default_factory=lambda: {"stair", "crud"})


@dataclass
class StoryParams:
    place: str
    hero_name: str
    hero_type: str
    helper_name: str
    helper_type: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
PLACES = {
    "station": Place(name="the space station", setting="orbit", features={"stair", "crud"}),
    "dock": Place(name="the docking bay", setting="orbit", features={"stair", "crud"}),
}

HEROES = [
    ("Milo", "boy"),
    ("Luna", "girl"),
    ("Nova", "girl"),
    ("Taj", "boy"),
]

HELPERS = [
    ("Captain Reed", "adult"),
    ("Pilot Ora", "adult"),
    ("Tech Finn", "adult"),
]

TRAITS = ["curious", "brave", "tiny", "bright", "careful"]


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def story_is_reasonable(params: StoryParams) -> bool:
    return params.place in PLACES


# ---------------------------------------------------------------------------
# Narrative helpers
# ---------------------------------------------------------------------------
def intro(world: World, hero: Entity, helper: Entity) -> None:
    world.say(
        f"{hero.id} was a {hero.type} helper aboard {world.place.name}, and "
        f"{helper.id} was the ship's steady guide."
    )
    world.say(
        f"{hero.pronoun().capitalize()} loved the quiet hum of engines, the silver rails, "
        f"and every shiny stair that led up through the station."
    )


def misunderstanding(world: World, hero: Entity) -> None:
    world.say(
        f"One day, {hero.id} spotted dark crud smeared on a stair and gasped. "
        f'"It looks like an alien trail!" {hero.pronoun()} said.'
    )
    hero.memes["fear"] = hero.memes.get("fear", 0) + 1
    hero.memes["misunderstanding"] = hero.memes.get("misunderstanding", 0) + 1


def explain(world: World, helper: Entity, hero: Entity) -> None:
    world.say(
        f"{helper.id} knelt beside {hero.id} and laughed softly. "
        f'"No, that is only engine crud from the repair pods. It is messy, but it is safe."'
    )
    hero.memes["fear"] = max(0, hero.memes.get("fear", 0) - 1)
    hero.memes["understanding"] = hero.memes.get("understanding", 0) + 1


def clean_and_transform(world: World, hero: Entity, helper: Entity) -> None:
    stair = world.get("stair")
    stair.meters["crud"] = 0
    stair.meters["clean"] = 1
    stair.meters["shine"] = 1
    hero.meters["help"] = hero.meters.get("help", 0) + 1
    world.say(
        f"Together they wiped the stair until the black smudge was gone. "
        f"The old step changed from grubby and dull into a bright silver path."
    )
    world.say(
        f"{hero.id} grinned, because the stair no longer looked scary at all; "
        f"it looked like a safe ladder into the stars."
    )


def happy_ending(world: World, hero: Entity, helper: Entity) -> None:
    hero.memes["joy"] = hero.memes.get("joy", 0) + 1
    helper.memes["pride"] = helper.memes.get("pride", 0) + 1
    world.say(
        f"At last, {hero.id} climbed the cleaned stair with a bounce in {hero.pronoun('possessive')} step, "
        f"and {helper.id} walked beside {hero.pronoun('object')}, smiling."
    )
    world.say(
        f"The station felt different now: what had seemed like a problem had turned into a sparkling way forward."
    )


def tell(params: StoryParams) -> World:
    if params.place not in PLACES:
        raise StoryError("Unknown place.")
    world = World(PLACES[params.place])

    hero = world.add(Entity(id=params.hero_name, kind="character", type=params.hero_type))
    helper = world.add(Entity(id=params.helper_name, kind="character", type=params.helper_type))
    stair = world.add(Entity(id="stair", type="stair", label="stair"))
    crud = world.add(Entity(id="crud", type="crud", label="crud", plural=False))
    stair.meters["crud"] = 1
    crud.meters["present"] = 1

    intro(world, hero, helper)
    world.para()
    misunderstanding(world, hero)
    explain(world, helper, hero)
    world.para()
    clean_and_transform(world, hero, helper)
    happy_ending(world, hero, helper)

    world.facts.update(
        hero=hero,
        helper=helper,
        stair=stair,
        crud=crud,
        misunderstood=True,
        transformed=True,
        happy_ending=True,
    )
    return world


# ---------------------------------------------------------------------------
# Story quality / QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    return [
        "Write a short space adventure story about a child helper who mistakes crud on a stair for danger, then learns the truth.",
        f"Tell a gentle story where {hero.id} sees crud on a stair in {world.place.name} and {helper.id} explains what it really is.",
        "Write a simple story with a misunderstanding, a cleanup, and a happy ending aboard a space station.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    return [
        QAItem(
            question=f"What did {hero.id} think the crud on the stair was?",
            answer=f"{hero.id} thought it was an alien trail, but it was only engine crud from a repair.",
        ),
        QAItem(
            question=f"Who explained the truth to {hero.id}?",
            answer=f"{helper.id} explained that the dark mark was just messy engine crud and nothing dangerous.",
        ),
        QAItem(
            question="What changed after they cleaned the stair?",
            answer="The stair changed from grubby and dull into a bright, safe silver path.",
        ),
        QAItem(
            question=f"How did the story end for {hero.id}?",
            answer=f"It ended happily, with {hero.id} climbing the cleaned stair beside {helper.id}.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is crud?",
            answer="Crud is sticky dirt or grime that can build up on a surface and make it look messy.",
        ),
        QAItem(
            question="What is a stair?",
            answer="A stair is one step in a staircase that helps people move up or down.",
        ),
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding happens when someone thinks something means one thing, but it really means something else.",
        ),
        QAItem(
            question="What does transformation mean?",
            answer="Transformation means something changes from one state into another, like a dirty stair becoming clean and bright.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== (3) World knowledge questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
#show valid/1.
#show valid_story/3.

valid(P) :- place(P), safe_story(P).
valid_story(P,H,L) :- valid(P), hero(H), helper(L).
safe_story(P) :- place(P), has(stair,P), has(crud,P), misunderstanding(P), happy_ending(P), transformation(P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
        lines.append(asp.fact("has", "stair", pid))
        lines.append(asp.fact("has", "crud", pid))
        lines.append(asp.fact("misunderstanding", pid))
        lines.append(asp.fact("happy_ending", pid))
        lines.append(asp.fact("transformation", pid))
    for hid, _ in HEROES:
        lines.append(asp.fact("hero", hid))
    for lid, _ in HELPERS:
        lines.append(asp.fact("helper", lid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/1."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = {(pid,) for pid in PLACES}
    cl = set(asp_valid())
    if py == cl:
        print(f"OK: clingo gate matches Python gate ({len(py)} places).")
        return 0
    print("MISMATCH between clingo and Python:")
    if cl - py:
        print(" only in clingo:", sorted(cl - py))
    if py - cl:
        print(" only in python:", sorted(py - cl))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space-adventure storyworld with a stair-crud misunderstanding.")
    ap.add_argument("--place", choices=PLACES.keys())
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(list(PLACES.keys()))
    if place not in PLACES:
        raise StoryError("Unknown place.")
    hero_name, hero_type = rng.choice(HEROES)
    helper_name, helper_type = rng.choice(HELPERS)
    return StoryParams(
        place=place,
        hero_name=hero_name,
        hero_type=hero_type,
        helper_name=helper_name,
        helper_type=helper_type,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid/1.\n#show valid_story/3."))
        vals = sorted(set(asp.atoms(model, "valid")))
        stories = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(vals)} valid places; {len(stories)} valid story tuples.")
        for x in vals:
            print(x)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        for pid in PLACES:
            params = StoryParams(
                place=pid,
                hero_name=HEROES[0][0],
                hero_type=HEROES[0][1],
                helper_name=HELPERS[0][0],
                helper_type=HELPERS[0][1],
                seed=base_seed,
            )
            samples.append(generate(params))
    else:
        for i in range(args.n):
            rng = random.Random(base_seed + i)
            params = resolve_params(args, rng)
            params.seed = base_seed + i
            samples.append(generate(params))

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
