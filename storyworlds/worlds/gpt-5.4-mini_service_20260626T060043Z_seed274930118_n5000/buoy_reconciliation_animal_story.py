#!/usr/bin/env python3
"""
storyworlds/worlds/buoy_reconciliation_animal_story.py
======================================================

A small animal-story world about a lost buoy, a mild quarrel, and a gentle
reconciliation.

Premise:
- A child-facing animal friend group plays near a pond.
- A bright buoy is useful as a floating toy and marker.
- One animal takes the buoy without asking, causing hurt feelings.

Turn:
- The buoy drifts into reeds, the friends realize they both need it, and they
  notice the misunderstanding.

Resolution:
- An apology and a shared rescue bring them back together.
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
class Animal:
    id: str
    species: str
    name: str
    role: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def cap(self) -> str:
        return self.name


@dataclass
class Place:
    name: str
    water: bool = True
    reeds: bool = True


@dataclass
class Buoy:
    color: str
    size: str
    floating: bool = True
    in_water: bool = True
    in_reeds: bool = False
    owned_by: Optional[str] = None


@dataclass
class StoryParams:
    place: str
    buoy_color: str
    first_animal: str
    second_animal: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place, buoy: Buoy) -> None:
        self.place = place
        self.buoy = buoy
        self.animals: dict[str, Animal] = {}
        self.lines: list[str] = []
        self.facts: dict[str, object] = {}
        self.trace: list[str] = []

    def add(self, animal: Animal) -> Animal:
        self.animals[animal.id] = animal
        return animal

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def render(self) -> str:
        return " ".join(self.lines)


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
PLACES = {
    "pond": Place("the pond", water=True, reeds=True),
    "lake": Place("the lake", water=True, reeds=True),
    "stream": Place("the stream", water=True, reeds=True),
}

ANIMALS = {
    "duck": {"species": "duck", "name": "Daisy"},
    "frog": {"species": "frog", "name": "Finn"},
    "otter": {"species": "otter", "name": "Ollie"},
    "beaver": {"species": "beaver", "name": "Bram"},
    "turtle": {"species": "turtle", "name": "Tess"},
}

BUOY_COLORS = ["red", "yellow", "blue", "orange", "green"]


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------
def _meter(animal: Animal, key: str, amount: float = 1.0) -> None:
    animal.meters[key] = animal.meters.get(key, 0.0) + amount


def _meme(animal: Animal, key: str, amount: float = 1.0) -> None:
    animal.memes[key] = animal.memes.get(key, 0.0) + amount


def _setup(world: World) -> None:
    a = world.animals["first"]
    b = world.animals["second"]
    buoy = world.buoy

    world.say(
        f"At {world.place.name}, {a.name} the {a.species} and {b.name} the {b.species} "
        f"found a bright {buoy.color} buoy bobbing on the water."
    )
    world.say(
        f"{a.name} liked how the buoy floated like a tiny round boat, and {b.name} "
        f"liked that it made a good marker for a game."
    )
    world.facts["setup"] = True


def _take_buoy(world: World) -> None:
    a = world.animals["first"]
    b = world.animals["second"]
    buoy = world.buoy

    _meter(a, "want", 1)
    _meme(a, "eager", 1)
    buoy.owned_by = a.id
    world.say(
        f"{a.name} reached out first and dragged the buoy to the shore. "
        f"{b.name} blinked in surprise because they had wanted to use it too."
    )
    _meme(b, "hurt", 1)
    _meme(a, "sting", 1)
    world.facts["hurt"] = True


def _drift_to_reeds(world: World) -> None:
    a = world.animals["first"]
    b = world.animals["second"]
    buoy = world.buoy

    buoy.in_water = True
    buoy.in_reeds = True
    world.say(
        f"Before long, a little breeze nudged the buoy away from the shore and into the reeds. "
        f"Now neither {a.name} nor {b.name} could reach it easily."
    )
    _meter(a, "trouble", 1)
    _meter(b, "trouble", 1)
    world.facts["lost"] = True


def _reconcile(world: World) -> None:
    a = world.animals["first"]
    b = world.animals["second"]
    buoy = world.buoy

    _meme(a, "regret", 1)
    _meme(b, "regret", 1)

    world.say(
        f"{a.name} looked down and said, 'I should have asked first.' "
        f"{b.name} softeningly answered, 'I should have spoken up sooner.'"
    )
    world.say(
        f"Together they pushed a long stick into the reeds, hooked the {buoy.color} buoy, "
        f"and pulled it back to shore."
    )

    buoy.in_reeds = False
    buoy.in_water = False
    buoy.owned_by = None
    _meme(a, "reconciled", 1)
    _meme(b, "reconciled", 1)
    _meme(a, "joy", 1)
    _meme(b, "joy", 1)

    world.say(
        f"After that, {a.name} and {b.name} smiled, shared the buoy, and made a new rule: "
        f"friends ask before they grab."
    )
    world.facts["resolved"] = True


def tell_story(world: World) -> None:
    _setup(world)
    world.say("")
    _take_buoy(world)
    _drift_to_reeds(world)
    world.say("")
    _reconcile(world)


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    a = world.animals["first"]
    b = world.animals["second"]
    buoy = world.buoy
    return [
        f"Write a short animal story about {a.name} and {b.name} at {world.place.name} with a {buoy.color} buoy.",
        f"Tell a gentle story where two animals argue over a buoy and then reconcile.",
        f"Write a child-friendly story set by water that includes a buoy, a mistake, and an apology.",
    ]


def story_qa(world: World) -> list[QAItem]:
    a = world.animals["first"]
    b = world.animals["second"]
    buoy = world.buoy
    return [
        QAItem(
            question=f"Who found the buoy at {world.place.name}?",
            answer=f"{a.name} and {b.name} found the bright {buoy.color} buoy at {world.place.name}.",
        ),
        QAItem(
            question=f"Why did {b.name} feel hurt when the buoy was taken?",
            answer=f"{b.name} felt hurt because {a.name} grabbed the buoy first instead of asking.",
        ),
        QAItem(
            question="How did the animals fix the problem?",
            answer="They apologized, used a stick to pull the buoy out of the reeds, and shared it again.",
        ),
        QAItem(
            question="What changed by the end of the story?",
            answer="The friends went from upset to reconciled, and they made a new rule to ask first.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a buoy?",
            answer="A buoy is a floating object that can mark a place in the water.",
        ),
        QAItem(
            question="Why do reeds matter near water?",
            answer="Reeds can tangle things and make it harder to reach something floating nearby.",
        ),
        QAItem(
            question="What does reconciliation mean?",
            answer="Reconciliation means making peace again after a disagreement.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
#show compatible/3.
#show reconciles/2.

compatible(P, C, B) :- place(P), animal(C), buoy(B), at_water(P), color(B, C).
reconciles(A, B) :- apology(A), apology(B), shared_recovery(A, B).
"""

def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        if place.water:
            lines.append(asp.fact("at_water", pid))
        if place.reeds:
            lines.append(asp.fact("has_reeds", pid))
    for aid, info in ANIMALS.items():
        lines.append(asp.fact("animal", aid))
        lines.append(asp.fact("species", aid, info["species"]))
    for color in BUOY_COLORS:
        lines.append(asp.fact("color", "buoy", color))
    return "\n".join(lines)


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal story about a buoy and reconciliation.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--buoy-color", choices=BUOY_COLORS)
    ap.add_argument("--first", choices=ANIMALS)
    ap.add_argument("--second", choices=ANIMALS)
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


def valid_combo(place: str, first: str, second: str) -> bool:
    return place in PLACES and first in ANIMALS and second in ANIMALS and first != second


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    places = [args.place] if args.place else list(PLACES)
    firsts = [args.first] if args.first else list(ANIMALS)
    seconds = [args.second] if args.second else list(ANIMALS)
    colors = [args.buoy_color] if args.buoy_color else BUOY_COLORS

    combos = []
    for p in places:
        for a in firsts:
            for b in seconds:
                if a == b:
                    continue
                for c in colors:
                    combos.append((p, a, b, c))
    if not combos:
        raise StoryError("No valid animal pairing matched the given options.")
    place, first, second, color = rng.choice(sorted(combos))
    return StoryParams(place=place, buoy_color=color, first_animal=first, second_animal=second)


def make_world(params: StoryParams) -> World:
    place = PLACES[params.place]
    buoy = Buoy(color=params.buoy_color, size="small")
    world = World(place, buoy)
    world.add(Animal(id="first", species=ANIMALS[params.first_animal]["species"], name=ANIMALS[params.first_animal]["name"]))
    world.add(Animal(id="second", species=ANIMALS[params.second_animal]["species"], name=ANIMALS[params.second_animal]["name"]))
    tell_story(world)
    world.facts.update(
        place=params.place,
        buoy_color=params.buoy_color,
        first=params.first_animal,
        second=params.second_animal,
    )
    return world


def generate(params: StoryParams) -> StorySample:
    world = make_world(params)
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
        print()
        print("--- trace ---")
        for line in sample.world.trace:
            print(line)
    if qa:
        print()
        print(format_qa(sample))


def asp_verify() -> int:
    try:
        import storyworlds.asp as asp
    except Exception as exc:  # pragma: no cover
        print(f"ASP unavailable: {exc}")
        return 1
    program = asp_program()
    models = asp.solve(program, models=1)
    if models is None:
        print("No ASP model found.")
        return 1
    print("OK: ASP program solved.")
    return 0


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())

    if args.all:
        samples = [
            generate(StoryParams(place="pond", buoy_color="red", first_animal="duck", second_animal="frog")),
            generate(StoryParams(place="lake", buoy_color="yellow", first_animal="otter", second_animal="beaver")),
            generate(StoryParams(place="stream", buoy_color="blue", first_animal="turtle", second_animal="duck")),
        ]
    else:
        base_seed = args.seed if args.seed is not None else random.randrange(2**31)
        samples = []
        seen: set[str] = set()
        for i in range(max(args.n, 1)):
            rng = random.Random(base_seed + i)
            params = resolve_params(args, rng)
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
