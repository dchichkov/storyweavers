#!/usr/bin/env python3
"""
A tiny folk-tale storyworld about a village mystery solved through teamwork.

Premise:
- A small village has a puzzling problem: something honorable and important goes missing.
- A child and a helper notice clues, use a specific technique, and work together.
- The ending shows the mystery solved and the village made glad again.

This world is intentionally small, state-driven, and constraint-checked.
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
# Core world model
# ---------------------------------------------------------------------------

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    carried_by: Optional[str] = None
    protected: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Place:
    name: str
    misty: bool = False
    affords: set[str] = field(default_factory=set)


@dataclass
class Mystery:
    id: str
    missing_item: str
    clue_kind: str
    clue_phrase: str
    technique: str
    method_phrase: str
    solved_by: str
    team_phrase: str
    ending_image: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

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
    "village": Place(name="the village green", misty=False, affords={"search", "gather"}),
    "woods": Place(name="the whispering woods", misty=True, affords={"search", "gather"}),
    "bridge": Place(name="the old stone bridge", misty=False, affords={"search"}),
}

MYSTERIES = {
    "bell": Mystery(
        id="bell",
        missing_item="honorary bell",
        clue_kind="shine",
        clue_phrase="a tiny shine on a fern",
        technique="specific technique",
        method_phrase="a careful pattern of looking left, right, and down",
        solved_by="the bell hung where the moss had been brushed aside",
        team_phrase="the child and the elder",
        ending_image="the honorary bell ringing softly above the green",
        tags={"honorary", "specific", "technique"},
    ),
    "cake": Mystery(
        id="cake",
        missing_item="celebration cake",
        clue_kind="crumb",
        clue_phrase="a trail of crumbs by the brook",
        technique="specific technique",
        method_phrase="three slow circles, then a gentle pause to listen",
        solved_by="the cake waited under a cool basket cloth",
        team_phrase="the baker and the child",
        ending_image="the cake safe and smiling on the table",
        tags={"specific", "technique"},
    ),
    "key": Mystery(
        id="key",
        missing_item="honorary key",
        clue_kind="mud",
        clue_phrase="a little mud print near the gate",
        technique="specific technique",
        method_phrase="one person watching the ground while the other watched the trees",
        solved_by="the key was tucked inside the gatepost",
        team_phrase="the shepherd and the child",
        ending_image="the honorary key shining in the sun",
        tags={"honorary", "specific"},
    ),
}

HERO_NAMES = ["Mara", "Nia", "Toma", "Jori", "Lina", "Perrin", "Sera", "Eli"]
HELPER_NAMES = ["Grandma Ivo", "Old Bram", "Aunt Sol", "Farmer Jessa", "Nim the baker"]
TRAITS = ["curious", "kind", "brave", "gentle", "quick-eyed", "patient"]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
#show valid_story/2.
#show solved/2.

valid_story(Place, Mystery) :- place(Place), mystery(Mystery), affords(Place, search), clue_for(Mystery, _).

solved(Place, Mystery) :- valid_story(Place, Mystery), teamwork(Mystery), technique(Mystery).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        if p.misty:
            lines.append(asp.fact("misty", pid))
        for a in sorted(p.affords):
            lines.append(asp.fact("affords", pid, a))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        lines.append(asp.fact("clue_for", mid, m.clue_kind))
        lines.append(asp.fact("technique", mid))
        lines.append(asp.fact("teamwork", mid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2.\n#show solved/2."))
    return sorted(set(asp.atoms(model, "valid_story"))), sorted(set(asp.atoms(model, "solved")))


# ---------------------------------------------------------------------------
# Story params
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    mystery: str
    hero_name: str
    helper_name: str
    hero_trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------

def is_reasonable(place: Place, mystery: Mystery) -> bool:
    return "search" in place.affords and mystery.technique and mystery.team_phrase


def valid_combos() -> list[tuple[str, str]]:
    out = []
    for pid, place in PLACES.items():
        for mid, mystery in MYSTERIES.items():
            if is_reasonable(place, mystery):
                out.append((pid, mid))
    return out


def explain_rejection(place: Place, mystery: Mystery) -> str:
    return (
        f"(No story: {mystery.missing_item} needs a place where searching makes sense, "
        f"and this setting does not support the mystery in a folk-tale way.)"
    )


# ---------------------------------------------------------------------------
# Narration helpers
# ---------------------------------------------------------------------------

def choose(hero_name: str, helper_name: str, trait: str, place: Place, mystery: Mystery) -> World:
    world = World(place)
    hero = world.add(Entity(id=hero_name, kind="character", type="girl", traits=[trait, "little"]))
    helper = world.add(Entity(id=helper_name, kind="character", type="woman", traits=["wise"]))
    item = world.add(Entity(
        id=mystery.id,
        kind="thing",
        type="treasure",
        label=mystery.missing_item,
        phrase=f"the {mystery.missing_item}",
        caretaker=helper.id,
    ))
    world.facts.update(hero=hero, helper=helper, item=item, mystery=mystery, place=place)
    return world


def tell_story(params: StoryParams) -> World:
    place = PLACES[params.place]
    mystery = MYSTERIES[params.mystery]
    world = choose(params.hero_name, params.helper_name, params.hero_trait, place, mystery)

    hero = world.facts["hero"]
    helper = world.facts["helper"]

    world.say(
        f"In {place.name}, there lived a {params.hero_trait} child named {hero.id} "
        f"who loved stories about brave helpers and hidden things."
    )
    world.say(
        f"One morning, {helper.id} looked worried. The {mystery.missing_item} was gone, "
        f"and the whole village fell quiet."
    )
    world.say(
        f"{hero.id} listened closely and noticed {mystery.clue_phrase}. "
        f"That was the first little hint."
    )

    world.para()
    world.say(
        f"{helper.id} said, \"We will use a {mystery.technique}: {mystery.method_phrase}.\""
    )
    world.say(
        f"So {hero.id} and {helper.id} searched together, one watching one clue while the other watched another."
    )
    world.say(
        f"That teamwork mattered, because {mystery.team_phrase} could each see what the other missed."
    )

    world.para()
    world.say(
        f"At last, the search led them to the right place. {mystery.solved_by}."
    )
    world.say(
        f"The village cheered, and {hero.id} stood tall as the little mystery was solved."
    )
    world.say(
        f"In the end, there was {mystery.ending_image}."
    )

    return world


# ---------------------------------------------------------------------------
# QA generation
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    m = world.facts["mystery"]
    return [
        f"Write a folk tale about a child and an elder solving a mystery with teamwork in {world.place.name}.",
        f"Tell a gentle story that includes a {m.technique} and a hidden {m.missing_item}.",
        f"Write a short story for children where a clue leads two helpers to solve a village mystery.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.facts["hero"]
    helper = world.facts["helper"]
    mystery = world.facts["mystery"]
    place = world.place.name
    return [
        QAItem(
            question=f"Who helped {hero.id} solve the mystery in {place}?",
            answer=f"{helper.id} helped {hero.id}. They worked together to find the missing {mystery.missing_item}.",
        ),
        QAItem(
            question=f"What clue did {hero.id} notice first?",
            answer=f"{hero.id} noticed {mystery.clue_phrase} first.",
        ),
        QAItem(
            question=f"What technique did they use to search?",
            answer=f"They used {mystery.technique}, which meant {mystery.method_phrase}.",
        ),
        QAItem(
            question=f"What was found at the end?",
            answer=f"The mystery was solved when {mystery.solved_by}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is teamwork?",
            answer="Teamwork is when people help one another and share the work so they can do something harder together.",
        ),
        QAItem(
            question="Why do people use clues in a mystery?",
            answer="People use clues because clues are little bits of information that help them figure out what happened or where something went.",
        ),
        QAItem(
            question="What does it mean to solve a mystery?",
            answer="To solve a mystery means to find out the answer to a puzzling problem.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== World knowledge questions ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    parts = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.traits:
            bits.append(f"traits={e.traits}")
        if e.caretaker:
            bits.append(f"caretaker={e.caretaker}")
        parts.append(f"  {e.id} ({e.kind}/{e.type}) {' '.join(bits)}")
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------

def valid_story_choices(args: argparse.Namespace) -> list[tuple[str, str]]:
    combos = valid_combos()
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.mystery:
        combos = [c for c in combos if c[1] == args.mystery]
    return combos


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_story_choices(args)
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, mystery_id = rng.choice(sorted(combos))
    hero_name = args.name or rng.choice(HERO_NAMES)
    helper_name = args.helper or rng.choice(HELPER_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(
        place=place_id,
        mystery=mystery_id,
        hero_name=hero_name,
        helper_name=helper_name,
        hero_trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
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

CURATED = [
    StoryParams(place="village", mystery="bell", hero_name="Mara", helper_name="Grandma Ivo", hero_trait="curious"),
    StoryParams(place="woods", mystery="cake", hero_name="Lina", helper_name="Nim the baker", hero_trait="patient"),
    StoryParams(place="bridge", mystery="key", hero_name="Toma", helper_name="Old Bram", hero_trait="quick-eyed"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Folk-tale mystery storyworld: teamwork solves a village puzzle.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--name")
    ap.add_argument("--helper")
    ap.add_argument("--trait")
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


def asp_verify() -> int:
    import asp
    py = set(valid_combos())
    model, solved = asp_valid()
    asp_set = set(model)
    if py != asp_set:
        print("MISMATCH between Python and ASP valid story sets.")
        print("only in python:", sorted(py - asp_set))
        print("only in asp:", sorted(asp_set - py))
        return 1
    print(f"OK: ASP matches Python valid_combos() ({len(py)} combos).")
    return 0


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/2.\n#show solved/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        valid, solved = asp_valid()
        print(f"{len(valid)} valid stories; {len(solved)} solved story markers.\n")
        for item in valid:
            print(item)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero_name}: {p.mystery} in {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
