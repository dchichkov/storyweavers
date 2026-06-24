#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260623T074642Z_seed779406221_n50/factory_bazooka_surprise_curiosity_conflict_folk_tale.py
=================================================================================================

A small folk-tale style storyworld about a curious child, a loud factory, and a
bazooka-shaped surprise that turns out to be harmless and helpful.

Premise:
- A child loves to explore a factory.
- They find a bazooka, but in this world it is a comic, harmless launcher for
  launching bundles of confetti, not a weapon.
- Curiosity leads the child toward trouble; conflict appears when the parent
  worries about a machine mistake or an unsafe misuse.
- Surprise resolves the tension when the "bazooka" launches a helpful fix,
  proving the child can use it in a clever, safe way.

This file follows the Storyweavers contract:
- imports shared results eagerly
- imports shared asp lazily
- exposes StoryParams, registries, build_parser, resolve_params, generate, emit,
  and main
- supports default run, -n, --all, --seed, --trace, --qa, --json, --asp,
  --verify, and --show-asp
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
    kind: str = "thing"   # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Place:
    name: str
    indoors: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Gizmo:
    id: str
    label: str
    phrase: str
    purpose: str
    safe: bool = True
    surprise: str = ""
    impact: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    gizmo: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place):
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

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
        c = World(self.place)
        c.entities = copy.deepcopy(self.entities)
        c.paragraphs = [[]]
        c.facts = dict(self.facts)
        return c


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
PLACES = {
    "factory": Place("the factory", indoors=True, affords={"noise", "parts", "sweep"}),
    "mill": Place("the grain mill", indoors=True, affords={"noise", "parts"}),
    "workshop": Place("the workshop", indoors=True, affords={"parts", "sweep"}),
    "yard": Place("the yard", indoors=False, affords={"sweep", "noise"}),
}

GIZMOS = {
    "bazooka": Gizmo(
        id="bazooka",
        label="bazooka",
        phrase="a bright bazooka-shaped blower",
        purpose="launching confetti far across the floor",
        safe=True,
        surprise="Instead of fire, it blew a storm of paper stars.",
        impact="The paper stars swept dust into neat little piles.",
        tags={"bazooka", "surprise", "curiosity"},
    ),
    "sweeper": Gizmo(
        id="sweeper",
        label="floor sweeper",
        phrase="a long floor sweeper",
        purpose="pushing dust into a corner",
        safe=True,
        surprise="It hummed softly like a sleepy bee.",
        impact="It gathered crumbs and dust into one tidy heap.",
        tags={"factory"},
    ),
    "horn": Gizmo(
        id="horn",
        label="signal horn",
        phrase="a brass signal horn",
        purpose="calling workers to gather",
        safe=True,
        surprise="It gave a loud toot like a goose in boots.",
        impact="Everyone heard the call at once.",
        tags={"conflict", "factory"},
    ),
}

TRAITS = ["curious", "brave", "careful", "bright", "quick-witted"]
GIRL_NAMES = ["Mira", "Nina", "Tia", "Lina", "Rosa", "Ivy"]
BOY_NAMES = ["Owen", "Pip", "Rowan", "Eli", "Milo", "Noah"]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A place is compatible if it affords the gizmo's use.
compatible(Place,G) :- place(Place), gizmo(G), affords(Place, Need), needs(G, Need).

% A story is valid when the place supports the gizmo, and the gizmo is safe.
valid_story(Place,G) :- compatible(Place,G), safe(G).

% Factories and mills are the only places where curiosity should meet noise or parts.
interesting(Place) :- place(Place), affords(Place, noise).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        if p.indoors:
            lines.append(asp.fact("indoors", pid))
        for a in sorted(p.affords):
            lines.append(asp.fact("affords", pid, a))
    for gid, g in GIZMOS.items():
        lines.append(asp.fact("gizmo", gid))
        lines.append(asp.fact("needs", gid, "parts" if gid == "bazooka" else "sweep"))
        if g.safe:
            lines.append(asp.fact("safe", gid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    python_set = {(p, g) for p in PLACES for g in GIZMOS if p in {"factory", "mill", "workshop", "yard"} and GIZMOS[g].safe}
    clingo_set = set(asp_valid_stories())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches python ({len(clingo_set)} stories).")
        return 0
    print("MISMATCH:")
    print("only in clingo:", sorted(clingo_set - python_set))
    print("only in python:", sorted(python_set - clingo_set))
    return 1


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------
def reasonableness_gate(place: Place, gizmo: Gizmo) -> bool:
    return gizmo.safe and place.name in {"the factory", "the grain mill", "the workshop", "the yard"}


def predict(world: World, hero: Entity, gizmo: Gizmo) -> dict:
    sim = world.copy()
    sim.facts["used"] = gizmo.id
    surprise = gizmo.surprise
    return {"surprise": surprise, "calm": True}


def _do_use(world: World, hero: Entity, gizmo: Gizmo) -> None:
    hero.memes["curiosity"] = hero.memes.get("curiosity", 0) + 1
    hero.meters["noise"] = hero.meters.get("noise", 0) + 1
    if gizmo.id == "bazooka":
        hero.memes["surprise"] = hero.memes.get("surprise", 0) + 1


def tell(place: Place, gizmo: Gizmo, name: str, gender: str, trait: str, parent: str) -> World:
    world = World(place)
    hero = world.add(Entity(id=name, kind="character", type=gender, meters={}, memes={}))
    adult = world.add(Entity(id="Parent", kind="character", type=parent, label=f"the {parent}"))
    tool = world.add(Entity(id=gizmo.id, type="thing", label=gizmo.label, phrase=gizmo.phrase, owner=hero.id))
    world.facts.update(hero=hero, adult=adult, tool=tool, gizmo=gizmo, place=place, trait=trait)

    world.say(f"Once, in {place.name}, there lived a {trait} child named {name}.")
    world.say(f"{name} loved to wander where the gears clinked and the lamps glowed, because {hero.pronoun()} was full of curiosity.")
    world.say(f"One day, {name} found {gizmo.phrase} beside the big iron doors.")
    world.para()
    world.say(f"{name} wanted to try the {gizmo.label}, but {adult.label} frowned and worried about the noise.")
    world.say(f'"A {gizmo.label} in a factory can mean trouble," {adult.label} said, "unless we know what it really does."')
    world.say(f"{name} held still, then looked again, wondering if the strange machine was a trick or a treasure.")
    world.para()
    world.say(gizmo.surprise)
    world.say(f"It was not a weapon at all; it was a harmless maker of {gizmo.purpose}.")
    _do_use(world, hero, gizmo)
    world.say(gizmo.impact)
    world.say(f"{name} laughed, and {adult.label} laughed too, because the old factory floor ended up cleaner than before.")
    world.facts["resolved"] = True
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short folk tale about a child named {f["hero"].id} who finds a bazooka in a factory and learns what it really does.',
        f"Tell a gentle story where curiosity, surprise, and conflict all happen around {f['place'].name}.",
        "Write a simple tale with a strange machine, a worried parent, and a happy ending that proves the machine was harmless.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    adult: Entity = f["adult"]
    tool: Entity = f["tool"]
    place: Place = f["place"]
    trait = f["trait"]
    return [
        QAItem(
            question=f"Who found the {tool.label} in {place.name}?",
            answer=f"{hero.id}, the {trait} child, found the {tool.label} in {place.name}.",
        ),
        QAItem(
            question=f"Why did {adult.label} worry about the {tool.label}?",
            answer=f"{adult.label} worried because a bazooka sounds dangerous, and the factory was already full of clinks and bangs.",
        ),
        QAItem(
            question=f"What changed after the {tool.label} was used?",
            answer=f"The {tool.label} turned out to be harmless, and it blew confetti and dust into neat little piles, so the factory grew tidy instead of scary.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a factory?",
            answer="A factory is a place where people make things, often with machines that clink, hum, and roll.",
        ),
        QAItem(
            question="What does curiosity mean?",
            answer="Curiosity is the feeling that makes someone want to look, ask, and learn about something new.",
        ),
        QAItem(
            question="What does conflict mean in a story?",
            answer="Conflict is the trouble or worry that makes characters disagree before they find a way forward.",
        ),
        QAItem(
            question="What is surprise in a story?",
            answer="Surprise is the sudden unexpected change that makes a moment feel new or exciting.",
        ),
    ]


# ---------------------------------------------------------------------------
# CLI and generation
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A folk tale storyworld about a factory, a bazooka, and a harmless surprise.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--gizmo", choices=GIZMOS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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
    place = args.place or rng.choice(list(PLACES))
    gizmo = args.gizmo or rng.choice(list(GIZMOS))
    gender = args.gender or rng.choice(["girl", "boy"])
    if args.name:
        name = args.name
    else:
        name = rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS)
    if not reasonableness_gate(PLACES[place], GIZMOS[gizmo]):
        raise StoryError("This world only tells stories where the gizmo is safe and the place can host it.")
    return StoryParams(place=place, gizmo=gizmo, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], GIZMOS[params.gizmo], params.name, params.gender, params.trait, params.parent)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


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
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- trace ---"]
    for e in world.entities.values():
        out.append(f"{e.id}: kind={e.kind} type={e.type} meters={dict(e.meters)} memes={dict(e.memes)}")
    return "\n".join(out)


CURATED = [
    StoryParams(place="factory", gizmo="bazooka", name="Mira", gender="girl", parent="mother", trait="curious"),
    StoryParams(place="workshop", gizmo="sweeper", name="Owen", gender="boy", parent="father", trait="careful"),
    StoryParams(place="mill", gizmo="horn", name="Tia", gender="girl", parent="mother", trait="bright"),
]


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_valid_combos())
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
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
        print(sample.story)
        if args.trace and sample.world is not None:
            print(dump_trace(sample.world))
        if args.qa:
            print()
            print(format_qa(sample))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
