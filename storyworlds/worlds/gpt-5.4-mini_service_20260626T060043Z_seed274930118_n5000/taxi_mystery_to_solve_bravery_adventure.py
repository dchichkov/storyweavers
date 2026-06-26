#!/usr/bin/env python3
"""
storyworlds/worlds/taxi_mystery_to_solve_bravery_adventure.py
==============================================================

A standalone story world about a taxi, a mystery to solve, and a brave ride
through a small adventure.

Premise:
- A child or small character needs a taxi ride.
- Something important is missing or strange.
- The rider must stay brave, ask good questions, and solve the mystery by the
  end of the trip.

The simulated world tracks physical state in meters and emotional state in
memes. The prose is built from those state changes rather than from a frozen
template.
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    rider: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self):
        if not self.meters:
            self.meters = {"speed": 0.0, "distance": 0.0, "missing": 0.0}
        if not self.memes:
            self.memes = {"worry": 0.0, "bravery": 0.0, "curiosity": 0.0, "relief": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Route:
    place: str
    hint: str
    length: int
    mystery: str
    obstacle: str


@dataclass
class Clue:
    id: str
    label: str
    where: str
    solves: str
    phrase: str


@dataclass
class StoryParams:
    route: str
    clue: str
    name: str
    gender: str
    driver: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, route: Route):
        self.route = route
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.trace: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)
            self.trace.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy as _copy
        w = World(self.route)
        w.entities = _copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


ROUTES = {
    "city": Route(
        place="the busy city streets",
        hint="The sidewalks glimmered, and cars hummed past the corners.",
        length=3,
        mystery="a missing yellow map",
        obstacle="a dark puddle blocking the curb",
    ),
    "market": Route(
        place="the market road",
        hint="Stalls were closing, and little lanterns swayed in the evening air.",
        length=4,
        mystery="a lost silver key",
        obstacle="a crate left in the lane",
    ),
    "harbor": Route(
        place="the harbor road",
        hint="The wind smelled like salt, and boats knocked softly at their ropes.",
        length=4,
        mystery="a dropped blue ticket",
        obstacle="a long hill with a steep bend",
    ),
}

CLUES = {
    "map": Clue(
        id="map",
        label="the yellow map",
        where="under the seat",
        solves="shows the right street",
        phrase="a folded yellow map with a red dot",
    ),
    "key": Clue(
        id="key",
        label="the silver key",
        where="in the taxi door pocket",
        solves="opens the little locker",
        phrase="a silver key with a tiny tag",
    ),
    "ticket": Clue(
        id="ticket",
        label="the blue ticket",
        where="wedged near the meter",
        solves="proves the right stop",
        phrase="a blue ticket with a stamped star",
    ),
}

GENDERS = {"girl", "boy"}
GIRL_NAMES = ["Mia", "Lina", "Nora", "Zoe", "Ava", "Maya"]
BOY_NAMES = ["Leo", "Finn", "Theo", "Max", "Eli", "Noah"]
TRAITS = ["curious", "brave", "gentle", "stubborn", "cheerful"]

KNOWLEDGE = {
    "taxi": ("What is a taxi?",
             "A taxi is a car that takes people where they need to go when they do not drive themselves."),
    "mystery": ("What is a mystery?",
                "A mystery is something puzzling that you do not understand yet, so you look for clues."),
    "bravery": ("What does it mean to be brave?",
                 "Being brave means doing something scary or hard while still trying your best."),
    "clue": ("What is a clue?",
             "A clue is a small hint that helps solve a mystery."),
    "map": ("What does a map do?",
            "A map shows where things are and helps people find the right way."),
    "ticket": ("What is a ticket?",
               "A ticket is a paper or card that can show you are allowed to go somewhere."),
}


def _say_intro(world: World, hero: Entity, driver: Entity, clue: Clue) -> None:
    world.say(f"{hero.id} was a {hero.traits[0]} {hero.type} who loved an adventure.")
    world.say(f"One day, {hero.id} climbed into a taxi with {driver.label} and found {clue.phrase}.")
    world.say(f"{hero.id} kept the clue safe because {clue.label} seemed important.")


def _say_setup(world: World, hero: Entity) -> None:
    route = world.route
    world.say(f"The taxi rolled toward {route.place}.")
    world.say(route.hint)
    hero.memes["curiosity"] += 1.0


def _drive_step(world: World, hero: Entity, clue: Clue) -> None:
    route = world.route
    sig = ("drive", route.place)
    if sig in world.fired:
        return
    world.fired.add(sig)
    hero.meters["distance"] += route.length
    hero.memes["worry"] += 1.0
    world.say(f"Then the taxi met {route.obstacle}, and the ride slowed down.")
    world.say(f"{hero.id} took a deep breath and looked for a clue.")


def _find_clue(world: World, hero: Entity, clue: Clue) -> None:
    sig = ("find", clue.id)
    if sig in world.fired:
        return
    world.fired.add(sig)
    hero.memes["bravery"] += 1.0
    hero.memes["worry"] = 0.0
    hero.memes["relief"] += 1.0
    world.say(f"With brave eyes, {hero.id} checked {clue.where}.")
    world.say(f"There it was: {clue.phrase}.")
    world.say(f"The clue {clue.solves}, and the taxi could keep going.")


def _resolve(world: World, hero: Entity, driver: Entity, clue: Clue) -> None:
    hero.meters["speed"] += 1.0
    world.say(f"{hero.id} showed {driver.pronoun('object')} the clue, and {driver.label} smiled.")
    world.say(f"Together they solved the mystery of {world.route.mystery}.")
    world.say(f"By the end, {hero.id} felt brave, and the taxi reached the right place at last.")


def tell(route: Route, clue: Clue, hero_name: str, hero_gender: str, driver_type: str, trait: str) -> World:
    world = World(route)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender, traits=[trait, "brave"]))
    driver = world.add(Entity(id="Driver", kind="character", type=driver_type, label="the driver"))
    clue_ent = world.add(Entity(id="Clue", type="thing", label=clue.label, phrase=clue.phrase))
    world.facts.update(hero=hero, driver=driver, clue=clue, clue_ent=clue_ent, route=route)
    _say_intro(world, hero, driver, clue)
    world.para()
    _say_setup(world, hero)
    _drive_step(world, hero, clue)
    _find_clue(world, hero, clue)
    world.para()
    _resolve(world, hero, driver, clue)
    return world


SETTINGS = {"city": ROUTES["city"], "market": ROUTES["market"], "harbor": ROUTES["harbor"]}
CLUE_SET = {"map": CLUES["map"], "key": CLUES["key"], "ticket": CLUES["ticket"]}


def reasonableness_gate(route: Route, clue: Clue) -> bool:
    return clue.solves in {"shows the right street", "opens the little locker", "proves the right stop"} and route.length >= 3


ASP_RULES = r"""
route(R) :- setting(R).
clue(C) :- clueitem(C).
compatible(R,C) :- route(R), clue(C).
#show compatible/2.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for rid in ROUTES:
        lines.append(asp.fact("setting", rid))
    for cid in CLUES:
        lines.append(asp.fact("clueitem", cid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for rid in SETTINGS:
        for cid in CLUE_SET:
            if reasonableness_gate(ROUTES[rid], CLUES[cid]):
                combos.append((rid, cid))
    return combos


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show compatible/2."))
    return sorted(set(asp.atoms(model, "compatible")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


@dataclass
class StoryParams:
    route: str
    clue: str
    name: str
    gender: str
    driver: str
    trait: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A taxi mystery story world with bravery and a small adventure.")
    ap.add_argument("--route", choices=ROUTES)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--driver", choices=["mother", "father", "driver"])
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
    combos = valid_combos()
    if args.route:
        combos = [c for c in combos if c[0] == args.route]
    if args.clue:
        combos = [c for c in combos if c[1] == args.clue]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    route, clue = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(sorted(GENDERS))
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    driver = args.driver or rng.choice(["mother", "father", "driver"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(route=route, clue=clue, name=name, gender=gender, driver=driver, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(ROUTES[params.route], CLUES[params.clue], params.name, params.gender, params.driver, params.trait)
    prompts = [
        "Write a short adventure story about a taxi ride with a mystery to solve and a brave child.",
        f"Tell a child-friendly story where {params.name} rides a taxi and solves a small mystery.",
        "Make the story feel like an adventure, with a clue, a worry, and a brave ending.",
    ]
    hero = world.facts["hero"]
    clue = world.facts["clue"]
    story_qa = [
        QAItem(
            question=f"Who took the taxi ride in this story?",
            answer=f"{hero.id} took the taxi ride and stayed brave while looking for the clue."
        ),
        QAItem(
            question=f"What mystery had to be solved?",
            answer=f"They had to solve {world.route.mystery} by following a clue in the taxi."
        ),
        QAItem(
            question=f"How did {hero.id} help?",
            answer=f"{hero.id} stayed calm, looked for {clue.label}, and showed it to the driver."
        ),
    ]
    world_qa = [
        QAItem(*KNOWLEDGE["taxi"]),
        QAItem(*KNOWLEDGE["mystery"]),
        QAItem(*KNOWLEDGE["bravery"]),
        QAItem(*KNOWLEDGE["clue"]),
    ]
    return StorySample(params=params, story=world.render(), prompts=prompts, story_qa=story_qa, world_qa=world_qa, world=world)


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
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"  {e.id:8} ({e.type:7}) meters={meters} memes={memes}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
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


def explain_rejection(route: Route, clue: Clue) -> str:
    return f"(No story: the route '{route.place}' and clue '{clue.label}' do not make a clear mystery.)"


def valid_story_combos() -> list[tuple[str, str]]:
    return valid_combos()


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show compatible/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible route/clue combos:\n")
        for route, clue in combos:
            print(f"  {route:8} {clue:8}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        curated = [
            StoryParams("city", "map", "Mia", "girl", "driver", "curious"),
            StoryParams("market", "key", "Leo", "boy", "mother", "brave"),
            StoryParams("harbor", "ticket", "Nora", "girl", "father", "cheerful"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
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
