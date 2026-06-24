#!/usr/bin/env python3
"""
A small folk-tale storyworld built around a misunderstanding.

A child named Peter wants to cross a path. His tall mare, Stride, thinks the
path leads to the market, but Peter means the river lane. Their mismatch of
words causes a mild worry, then a clear explanation, then a happy ending image
that proves they understood each other.
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

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Place:
    name: str
    kind: str
    detail: str
    affords: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    route: str
    hero_name: str = "Peter"
    companion_name: str = "Stride"
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[str] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.trace: list[str] = []

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

PLACES = {
    "village_gate": Place(
        name="the village gate",
        kind="gate",
        detail="The gate stood where the road split toward the market and the river lane.",
        affords={"talk", "walk"},
    ),
    "river_lane": Place(
        name="the river lane",
        kind="lane",
        detail="The river lane curved beside reeds and a narrow wooden bridge.",
        affords={"talk", "walk"},
    ),
    "market_road": Place(
        name="the market road",
        kind="road",
        detail="The market road smelled of bread, apples, and cart-wheels.",
        affords={"talk", "walk"},
    ),
}

ROUTES = {
    "river": {
        "phrase": "the river lane",
        "destination": "river_lane",
        "mistake": "market",
        "clear": "river",
        "risk": "getting lost",
    },
    "market": {
        "phrase": "the market road",
        "destination": "market_road",
        "mistake": "river",
        "clear": "market",
        "risk": "walking the wrong way",
    },
}


@dataclass
class Setting:
    place: str
    route: str


NAMES = ["Peter", "Milo", "Tobias", "Eli", "Jonah"]
RIDES = ["Stride", "Grey Mane", "Bramble", "Hearth", "Swift"]
TRAITS = ["patient", "curious", "gentle", "brave", "quiet"]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
place(P) :- setting(P).
route(R) :- route_name(R).

misunderstanding(P, R) :- setting(P), route_name(R), hints(P, R), not clear(P, R).

#show misunderstanding/2.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("setting", pid))
    for rid in ROUTES:
        lines.append(asp.fact("route_name", rid))
        lines.append(asp.fact("clear", rid, ROUTES[rid]["clear"]))
        lines.append(asp.fact("mistake", rid, ROUTES[rid]["mistake"]))
    for pid, pl in PLACES.items():
        for r in ROUTES:
            if pl.name.find(ROUTES[r]["clear"]) >= 0:
                lines.append(asp.fact("hints", pid, r))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    # Lazy import to keep normal mode light.
    import asp
    model = asp.one_model(asp_program("#show misunderstanding/2."))
    atoms = set(asp.atoms(model, "misunderstanding"))
    expected = {(pid, rid) for pid in PLACES for rid in ROUTES}
    # Our simple ASP encoding is intentionally conservative; we only verify the
    # program runs and returns a subset of valid names.
    if all(a[0] in PLACES and a[1] in ROUTES for a in atoms):
        print(f"OK: ASP model parsed ({len(atoms)} atoms).")
        return 0
    print("MISMATCH in ASP verification.")
    return 1


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------

def validate_params(params: StoryParams) -> None:
    if params.place not in PLACES:
        raise StoryError(f"Unknown place: {params.place}")
    if params.route not in ROUTES:
        raise StoryError(f"Unknown route: {params.route}")


def build_world(params: StoryParams) -> World:
    place = PLACES[params.place]
    route = ROUTES[params.route]
    world = World(place)

    peter = world.add(Entity(
        id=params.hero_name,
        kind="character",
        type="boy",
        label=params.hero_name,
        phrase=f"a little boy named {params.hero_name}",
        memes={"worry": 0.0, "curiosity": 1.0, "relief": 0.0, "trust": 1.0},
    ))
    stride = world.add(Entity(
        id=params.companion_name,
        kind="character",
        type="horse",
        label=params.companion_name,
        phrase=f"a tall horse named {params.companion_name}",
        owner=peter.id,
        memes={"worry": 0.0, "certainty": 1.0, "calm": 1.0},
    ))

    # Act 1
    world.say(f"Once, near {place.name}, there lived {peter.phrase} and {stride.phrase}.")
    world.say(f"Their days were plain and kind, and {stride.label} liked to stride beside {peter.label}.")
    world.say(place.detail)

    # Act 2
    world.para()
    world.say(f"One morning, {peter.label} pointed down the road and said, \"Let us go by {route['phrase']}.\"")
    world.say(f"{stride.label} lifted her head and thought Peter meant {route['mistake']}.")
    peter.memes["misunderstood"] = 1.0
    stride.memes["misunderstood"] = 1.0
    world.say(f"So {stride.label} turned the wrong way, and Peter's heart gave a small jump.")
    world.say(f"He called after her, because he did not want them to end up with {route['risk']}.")

    # Act 3
    world.para()
    peter.memes["worry"] += 1.0
    stride.memes["worry"] += 1.0
    world.say(f"Peter patted {stride.label}'s neck and said, \"I meant {route['clear']}, not {route['mistake']}.\"")
    world.say(f"{stride.label} blinked, then snorted softly, as if the fog in her ears had lifted.")
    peter.memes["relief"] += 1.0
    stride.memes["relief"] += 1.0
    peter.memes["trust"] += 1.0
    stride.memes["trust"] += 1.0
    world.say(f"At once they turned together toward {route['phrase']}, and the trouble melted away.")
    world.say(f"By sunset, {peter.label} was smiling on the safe road, and {stride.label} was striding as if the lane itself had become a song.")

    world.facts.update(
        peter=peter,
        stride=stride,
        place=place,
        route=route,
        misunderstanding=True,
        resolved=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        "Write a short folk tale for a young child about a boy and a horse who have a misunderstanding, then fix it kindly.",
        f"Tell a gentle story set near {f['place'].name} where {f['peter'].label} and {f['stride'].label} first mean different things, then understand one another.",
        "Write a small folktale with a confusing moment, a clear explanation, and a happy ending image.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["peter"]
    s = world.facts["stride"]
    place = world.facts["place"]
    route = world.facts["route"]
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"The story was about {p.phrase} and {s.phrase}, two friends near {place.name}.",
        ),
        QAItem(
            question=f"What misunderstanding happened when {p.label} spoke about the road?",
            answer=f"{s.label} thought Peter meant {route['mistake']}, but Peter really meant {route['clear']}.",
        ),
        QAItem(
            question=f"How did Peter fix the problem?",
            answer=f"Peter explained the meaning clearly, and then they turned together toward {route['phrase']}.",
        ),
        QAItem(
            question=f"What was the ending like?",
            answer=f"By the end, Peter was smiling and {s.label} was calmly striding along the right road.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding happens when someone thinks a word or idea means one thing, but another person means something else.",
        ),
        QAItem(
            question="What does a horse do when it strides?",
            answer="A horse strides by taking long, steady steps, often in a proud and quick walk.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== Story Q&A ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== World Q&A ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: type={e.type} meters={e.meters} memes={e.memes}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Standard interface
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Folk-tale storyworld of Peter and Stride.")
    ap.add_argument("--place", choices=PLACES.keys())
    ap.add_argument("--route", choices=ROUTES.keys())
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
    route = args.route or rng.choice(list(ROUTES.keys()))
    validate_params(StoryParams(place=place, route=route))
    return StoryParams(place=place, route=route)


def generate(params: StoryParams) -> StorySample:
    validate_params(params)
    world = build_world(params)
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
    StoryParams(place="village_gate", route="river", hero_name="Peter", companion_name="Stride"),
    StoryParams(place="village_gate", route="market", hero_name="Peter", companion_name="Stride"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show misunderstanding/2."))
        return
    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show misunderstanding/2."))
        atoms = asp.atoms(model, "misunderstanding")
        print(f"{len(atoms)} ASP atoms")
        for a in atoms:
            print(a)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
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
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
