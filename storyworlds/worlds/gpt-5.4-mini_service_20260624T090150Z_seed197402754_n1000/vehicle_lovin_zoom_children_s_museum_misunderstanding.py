#!/usr/bin/env python3
"""
A small storyworld about a children's museum visit with a pirate-tale feel:
a lovable vehicle, a zoomy mishap, a misunderstanding, some humor, and a
problem-solving turn that fixes the day.
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

MUSEUM_ROOMS = ["the ship room", "the wheel room", "the build room", "the map nook"]
VEHICLE_TYPES = ["car", "truck", "bus", "boat", "train"]
HERO_NAMES = ["Milo", "Nina", "Pip", "Tia", "Jules", "Rory", "Luna", "Benny"]
GROWNUP_NAMES = ["Captain Ada", "Mr. Finch", "Mara", "Captain Bea"]


@dataclass
class StoryParams:
    vehicle: str
    hero: str
    grownup: str
    room: str
    seed: Optional[int] = None


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    type: str = "thing"
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self) -> str:
        if self.kind == "character":
            return "they"
        return "it"


class World:
    def __init__(self, params: StoryParams):
        self.params = params
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Children's museum pirate-tale storyworld.")
    ap.add_argument("--vehicle", choices=VEHICLE_TYPES)
    ap.add_argument("--hero")
    ap.add_argument("--grownup")
    ap.add_argument("--room", choices=MUSEUM_ROOMS)
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
    vehicle = args.vehicle or rng.choice(VEHICLE_TYPES)
    hero = args.hero or rng.choice(HERO_NAMES)
    grownup = args.grownup or rng.choice(GROWNUP_NAMES)
    room = args.room or rng.choice(MUSEUM_ROOMS)
    return StoryParams(vehicle=vehicle, hero=hero, grownup=grownup, room=room)


def asp_facts() -> str:
    import asp
    lines = []
    for v in VEHICLE_TYPES:
        lines.append(asp.fact("vehicle", v))
    for r in MUSEUM_ROOMS:
        lines.append(asp.fact("room", r))
    lines.append(asp.fact("feature", "misunderstanding"))
    lines.append(asp.fact("feature", "humor"))
    lines.append(asp.fact("feature", "problem_solving"))
    return "\n".join(lines)


ASP_RULES = r"""
misunderstanding(V,R) :- vehicle(V), room(R).
humor(V) :- vehicle(V).
problem_solving(V,R) :- vehicle(V), room(R).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
    except Exception as exc:
        print(f"ASP unavailable: {exc}")
        return 1
    model = asp.one_model(asp_program("#show misunderstanding/2.\n#show humor/1.\n#show problem_solving/2."))
    got_m = set(asp.atoms(model, "misunderstanding"))
    got_h = set(asp.atoms(model, "humor"))
    got_p = set(asp.atoms(model, "problem_solving"))
    want_m = {(v, r) for v in VEHICLE_TYPES for r in MUSEUM_ROOMS}
    want_h = {(v,) for v in VEHICLE_TYPES}
    want_p = {(v, r) for v in VEHICLE_TYPES for r in MUSEUM_ROOMS}
    ok = got_m == want_m and got_h == want_h and got_p == want_p
    if ok:
        print("OK: ASP parity matches Python registries.")
        return 0
    print("Mismatch between ASP and Python registries.")
    return 1


def pirate_opening(hero: str, grownup: str, vehicle: str, room: str) -> list[str]:
    return [
        f"On a bright day, {hero} sailed into the children's museum with {grownup}, as bold as a tiny pirate on a treasure run.",
        f"In {room}, there stood a lovable {vehicle}, shiny as a captured coin and ready for adventure.",
        f"{hero} loved that {vehicle} and kept whisperin', 'Let's zoom!'",
    ]


def build_world(params: StoryParams) -> World:
    world = World(params)
    hero = world.add(Entity(id="hero", kind="character", label=params.hero, type="child", memes={"joy": 1.0}))
    grownup = world.add(Entity(id="grownup", kind="character", label=params.grownup, type="adult"))
    vehicle = world.add(Entity(id="vehicle", kind="thing", label=params.vehicle, type=params.vehicle, meters={"speed": 0.0}, memes={"lovin": 1.0}))
    return world


def generate_story(world: World) -> None:
    p = world.params
    hero = world.entities["hero"]
    grownup = world.entities["grownup"]
    vehicle = world.entities["vehicle"]

    world.say(pirate_opening(p.hero, p.grownup, p.vehicle, p.room)[0])
    world.say(pirate_opening(p.hero, p.grownup, p.vehicle, p.room)[1])
    world.say(pirate_opening(p.hero, p.grownup, p.vehicle, p.room)[2])

    world.para()
    world.say(f"{p.hero} gave the {p.vehicle} a push and it began to zoom across the room.")
    vehicle.meters["speed"] = 1.0
    hero.memes["excited"] = 1.0

    world.say(f"But the zoom made a funny whoosh, and {p.grownup} thought {p.hero} had broken a museum rule.")
    hero.memes["worry"] = 1.0
    grownup.memes["mistaken"] = 1.0
    world.facts["misunderstanding"] = True

    world.say(f"{p.hero} blinked and said, 'Nay, I was only showing how the {p.vehicle} rolls!'")
    world.say(f"{p.grownup} looked again and laughed, because the {p.vehicle} was not running wild at all.")

    world.para()
    world.say(f"Together they found a fix: a soft track in {p.room} where the {p.vehicle} could zoom without bumping anything.")
    world.say(f"{p.hero} helped guide it, {p.grownup} cheered, and the little ship of a day sailed on with jokes and smiles.")
    vehicle.meters["speed"] = 0.5
    hero.memes["proud"] = 1.0
    hero.memes["joy"] = 2.0
    grownup.memes["joy"] = 1.0
    world.facts["problem_solving"] = True
    world.facts["humor"] = True
    world.facts["settled"] = True


def generation_prompts(world: World) -> list[str]:
    p = world.params
    return [
        f"Write a pirate-style story for children about {p.hero}, a lovable {p.vehicle}, and a misunderstanding at {p.room}.",
        f"Tell a funny museum tale where a tiny pirate kid thinks a {p.vehicle} should zoom, but a grownup worries before they solve the problem.",
        f"Create a short story with the words vehicle, lovin, and zoom, set in a children's museum and ending in a happy fix.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.params
    return [
        QAItem(
            question=f"What was {p.hero} loving to play with in the museum?",
            answer=f"{p.hero} was loving the {p.vehicle}. It looked shiny and fun, like a tiny pirate's prize.",
        ),
        QAItem(
            question=f"Why did {p.grownup} first get worried about the zoom in {p.room}?",
            answer=f"{p.grownup} thought the fast zoom might be a problem in {p.room}, but it turned out to be only a harmless misunderstanding.",
        ),
        QAItem(
            question=f"How did {p.hero} and {p.grownup} fix the trouble?",
            answer=f"They found a soft track in {p.room} so the {p.vehicle} could zoom safely. That solved the problem and made everyone laugh.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a vehicle?",
            answer="A vehicle is something that helps people or things move from one place to another, like a car, truck, train, or boat.",
        ),
        QAItem(
            question="What does it mean to zoom?",
            answer="To zoom means to move very fast, like when a toy car races across the floor.",
        ),
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding happens when someone thinks something is happening, but they do not have the right idea at first.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:8} ({e.kind:8}) {e.label} {' '.join(bits)}")
    lines.append(f"  facts={world.facts}")
    return "\n".join(lines)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        for i, p in enumerate(sample.prompts, 1):
            print(f"P{i}: {p}")
        print()
        for item in sample.story_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
        print()
        for item in sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    generate_story(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


CURATED = [
    StoryParams(vehicle="boat", hero="Pip", grownup="Captain Ada", room="the ship room"),
    StoryParams(vehicle="car", hero="Milo", grownup="Mara", room="the wheel room"),
    StoryParams(vehicle="train", hero="Nina", grownup="Mr. Finch", room="the build room"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show misunderstanding/2.\n#show humor/1.\n#show problem_solving/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show misunderstanding/2.\n#show humor/1.\n#show problem_solving/2."))
        print(f"misunderstanding={len(asp.atoms(model, 'misunderstanding'))}")
        print(f"humor={len(asp.atoms(model, 'humor'))}")
        print(f"problem_solving={len(asp.atoms(model, 'problem_solving'))}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero} and the {p.vehicle} at {p.room}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
