#!/usr/bin/env python3
"""
Storyworld: an eagle, a twine coil, and a small misunderstanding
with inner monologue, in a slice-of-life tone.

Premise:
- A practical bird gathers twine and little bits of forage for a nest.
- Another character misreads the twine as something dangerous or rude.
- The misunderstanding is resolved through a careful explanation and a small helping gesture.
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
    carries: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        mapping = {
            "eagle": {"subject": "she", "object": "her", "possessive": "her"},
            "person": {"subject": "they", "object": "them", "possessive": "their"},
        }
        return mapping.get(self.type, {"subject": "it", "object": "it", "possessive": "its"})[case]


@dataclass
class Place:
    name: str
    detail: str
    affords: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    eagle_name: str
    person_name: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def render(self) -> str:
        return " ".join(self.lines)


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

PLACES = {
    "courtyard": Place(
        name="the courtyard",
        detail="The courtyard was calm, with a low stone wall and a patch of dry grass.",
        affords={"forage", "twine"},
    ),
    "garden": Place(
        name="the garden",
        detail="The garden was tidy and bright, with little stems and scraps tucked near the beds.",
        affords={"forage", "twine"},
    ),
    "roof": Place(
        name="the roof garden",
        detail="The roof garden was breezy, with pots, pebbles, and a soft place to land.",
        affords={"forage", "twine"},
    ),
}

EAGLE_NAMES = ["Aster", "Brim", "Cora", "Dawn", "Kite", "Rill"]
PERSON_NAMES = ["Mina", "June", "Owen", "Pia", "Seth", "Lena"]


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------

def inner_monologue(eagle: Entity, thought: str) -> str:
    return f"{eagle.id} thought, “{thought}”"


def setup_world(params: StoryParams) -> World:
    place = PLACES[params.place]
    world = World(place)

    eagle = world.add(Entity(id=params.eagle_name, kind="character", type="eagle"))
    person = world.add(Entity(id=params.person_name, kind="character", type="person"))
    twine = world.add(Entity(
        id="twine",
        type="twine",
        label="twine",
        phrase="a small coil of twine",
        owner=eagle.id,
        carries="nest",
        meters={"length": 1.0},
    ))
    forage = world.add(Entity(
        id="forage",
        type="forage",
        label="forage",
        phrase="a little bundle of forage",
        owner=eagle.id,
        meters={"bits": 1.0},
    ))

    world.facts.update(place=place, eagle=eagle, person=person, twine=twine, forage=forage)
    return world


def tell_story(world: World) -> None:
    eagle = world.facts["eagle"]
    person = world.facts["person"]
    twine = world.facts["twine"]
    forage = world.facts["forage"]
    place: Place = world.facts["place"]

    world.say(f"{eagle.id} the eagle liked slow mornings at {place.name}.")
    world.say(place.detail)
    world.say(f"She was out to forage, gathering {forage.phrase} for a nest she liked to keep neat.")
    world.say(inner_monologue(eagle, "A little twine will hold the soft bits together. That will make the nest steadier."))

    world.lines.append("")
    world.say(f"Near the path, {person.id} noticed the twine in {eagle.id}'s beak and frowned.")
    world.say(f"{person.id} thought the twine looked tangled and strange, as if {eagle.id} had taken something that did not belong to her.")
    world.say(inner_monologue(person, "Maybe she is carrying that away on purpose. Maybe I should stop her."))

    world.lines.append("")
    world.say(f"{person.id} called out, and {eagle.id} landed on the low wall, surprised.")
    world.say(f"She blinked once and tilted her head, still holding the twine carefully.")
    world.say(inner_monologue(eagle, "Oh no. She thinks I am taking a treasure. I only want to fix the nest."))

    world.lines.append("")
    world.say(f"{eagle.id} set the twine down and nudged the forage beside it.")
    world.say(f"Then she showed how the twine could tie the little stems together instead of hurting anything.")
    world.say(inner_monologue(person, "Oh. It is not for trouble. It is for a nest. That makes perfect sense."))

    world.lines.append("")
    world.say(f"{person.id} laughed a little at the mistake and helped gather a few more soft bits from the ground.")
    world.say(f"{eagle.id} tucked the twine back into place, and the two of them shared the quiet work.")
    world.say(f"By the end of the morning, the twine was useful, the forage was sorted, and the misunderstanding had turned into a small kindness.")


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A place supports the little life actions if it affords them.
allowed(P, A) :- affords(P, A).

% A misunderstanding happens when one character sees twine and assumes it is a problem.
misunderstanding(E, X) :- sees(E, twine), thinks_problem(E, X), twine(X).

% Resolution is possible when twine is explained as nest material and shared.
resolved(E) :- explains(twine, nest), helps(E).

#show allowed/2.
#show misunderstanding/2.
#show resolved/1.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        for a in sorted(p.affords):
            lines.append(asp.fact("affords", pid, a))
    lines.append(asp.fact("twine", "twine"))
    lines.append(asp.fact("forage", "forage"))
    lines.append(asp.fact("sees", "person", "twine"))
    lines.append(asp.fact("thinks_problem", "person", "twine"))
    lines.append(asp.fact("explains", "twine", "nest"))
    lines.append(asp.fact("helps", "person"))
    return "\n".join(lines)


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program())
    atoms = set((s.name, len(s.arguments)) for s in model)
    expected = {("allowed", 2), ("misunderstanding", 2), ("resolved", 1)}
    if expected.issubset(atoms):
        print("OK: ASP twin emits the expected predicates.")
        return 0
    print("MISMATCH: ASP twin did not emit all expected predicates.")
    return 1


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------

def valid_places() -> list[str]:
    return [k for k, p in PLACES.items() if {"forage", "twine"} <= p.affords]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.place not in PLACES:
        raise StoryError("Unknown place.")
    place = args.place or rng.choice(valid_places())
    if place not in valid_places():
        raise StoryError("This place does not support twine-and-forage life.")
    return StoryParams(
        place=place,
        eagle_name=args.eagle_name or rng.choice(EAGLE_NAMES),
        person_name=args.person_name or rng.choice(PERSON_NAMES),
        seed=args.seed,
    )


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    p: Place = world.facts["place"]
    eagle: Entity = world.facts["eagle"]
    person: Entity = world.facts["person"]
    return [
        f"Write a slice-of-life story about {eagle.id} the eagle, twine, and forage at {p.name}.",
        f"Tell a gentle story where {person.id} misunderstands why {eagle.id} carries twine.",
        "Write a short child-friendly story that starts quietly, includes a misunderstanding, and ends with a small helpful fix.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p: Place = world.facts["place"]
    eagle: Entity = world.facts["eagle"]
    person: Entity = world.facts["person"]
    return [
        QAItem(
            question=f"Why was {eagle.id} carrying twine at {p.name}?",
            answer=f"{eagle.id} was using the twine as nest material while she foraged there.",
        ),
        QAItem(
            question=f"Why did {person.id} first think the twine was a problem?",
            answer=f"{person.id} misunderstood the twine and thought {eagle.id} might have taken something wrong, when it was really just for the nest.",
        ),
        QAItem(
            question="How did the misunderstanding end?",
            answer=f"{eagle.id} showed that the twine was for the nest, and {person.id} helped instead of worrying.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is twine?",
            answer="Twine is a thin string made by twisting fibers together. People and animals can use it to tie or bundle things.",
        ),
        QAItem(
            question="What does it mean to forage?",
            answer="To forage means to search for food or useful things in nature, like seeds, bits of plant, or small scraps.",
        ),
        QAItem(
            question="Why do birds use nest material?",
            answer="Birds use nest material to build a safe place for eggs or chicks, and soft pieces help the nest hold together.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for i, q in enumerate(sample.prompts, 1):
        out.append(f"{i}. {q}")
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
    for e in world.entities.values():
        lines.append(f"{e.id}: type={e.type}, meters={e.meters}, memes={e.memes}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Story generation
# ---------------------------------------------------------------------------

def generate(params: StoryParams) -> StorySample:
    world = setup_world(params)
    tell_story(world)
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


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life storyworld: eagle, twine, forage, and a misunderstanding.")
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--eagle-name", choices=EAGLE_NAMES)
    ap.add_argument("--person-name", choices=PERSON_NAMES)
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


def curated_params() -> list[StoryParams]:
    return [
        StoryParams(place="courtyard", eagle_name="Aster", person_name="Mina"),
        StoryParams(place="garden", eagle_name="Brim", person_name="Owen"),
        StoryParams(place="roof", eagle_name="Cora", person_name="Lena"),
    ]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in curated_params()]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
