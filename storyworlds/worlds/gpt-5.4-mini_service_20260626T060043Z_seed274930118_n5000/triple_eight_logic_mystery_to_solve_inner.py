#!/usr/bin/env python3
"""
storyworlds/worlds/triple_eight_logic_mystery_to_solve_inner.py
===============================================================

A small story world about a child solving a little mystery with logic,
an inner monologue, and a surprise reveal.

Seed image:
---
A child notices that a triple of clues points to one hidden answer: eight
glittering crumbs, a borrowed key, and a quiet cat. The child thinks it
through, follows the logic, and discovers who moved the lantern.

This world keeps the domain tiny and classical:
- one mystery to solve
- one clear line of reasoning
- one surprise reveal
- one ending image showing what changed
"""

from __future__ import annotations

import argparse
import copy
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
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    held_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

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
class Place:
    id: str
    label: str
    indoors: bool = True
    clues: tuple[str, ...] = ()


@dataclass
class Mystery:
    id: str
    label: str
    hidden_by: str
    clues: tuple[str, ...]
    surprise: str
    solved_by: str


@dataclass
class StoryParams:
    place: str
    mystery: str
    hero_name: str
    hero_gender: str
    sidekick: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place, mystery: Mystery) -> None:
        self.place = place
        self.mystery = mystery
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[str] = set()

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

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
        clone = World(self.place, self.mystery)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        clone.fired = set(self.fired)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

PLACES = {
    "attic": Place("attic", "the attic", indoors=True, clues=("dust", "box", "beam")),
    "kitchen": Place("kitchen", "the kitchen", indoors=True, clues=("crumbs", "cup", "drawer")),
    "library": Place("library", "the library corner", indoors=True, clues=("book", "label", "page")),
}

MYSTERIES = {
    "lantern": Mystery(
        id="lantern",
        label="the missing lantern",
        hidden_by="a scarf",
        clues=("triple", "eight", "logic"),
        surprise="the quiet cat had dragged it under the bench",
        solved_by="the child counted the clues and noticed the pattern",
    ),
    "keys": Mystery(
        id="keys",
        label="the lost keys",
        hidden_by="a bowl",
        clues=("triple", "eight", "logic"),
        surprise="the keys were tucked inside the bread box",
        solved_by="the child followed the tiny trail of shiny dust",
    ),
    "bell": Mystery(
        id="bell",
        label="the silver bell",
        hidden_by="a stack of books",
        clues=("triple", "eight", "logic"),
        surprise="the bell had rolled into a shoe",
        solved_by="the child matched the clues to the only place that made sense",
    ),
}

HERO_NAMES = ["Mina", "Toby", "Nia", "Arlo", "June", "Owen", "Lena", "Pip"]
SIDEKICKS = ["cat", "dog", "grandma", "brother", "sister"]
GENDERS = ["girl", "boy"]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A mystery is solvable when the three clues all point to one hidden place.
solvable(M) :- mystery(M), clue(M, triple), clue(M, eight), clue(M, logic).

% Surprise is available only when the hidden place is unique.
surprise(M) :- solvable(M), hidden(M, _).

#show solvable/1.
#show surprise/1.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        lines.append(asp.fact("hidden", mid, m.hidden_by))
        for clue in m.clues:
            lines.append(asp.fact("clue", mid, clue))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_solve_atoms(show: str) -> list[tuple]:
    import asp
    model = asp.one_model(asp_program(show))
    return sorted(set(asp.atoms(model, "solvable"))), sorted(set(asp.atoms(model, "surprise")))


# ---------------------------------------------------------------------------
# Story engine
# ---------------------------------------------------------------------------

def inner_monologue(hero: Entity, mystery: Mystery) -> str:
    return (
        f"{hero.pronoun('subject').capitalize()} looked at the clues and thought, "
        f"\"Three words keep showing up: triple, eight, logic. If they all matter, "
        f"then the answer has to be the only place that fits.\""
    )


def solve_mystery(world: World, hero: Entity) -> None:
    mystery = world.mystery
    hero.memes["curiosity"] = hero.memes.get("curiosity", 0.0) + 1.0
    hero.memes["focus"] = hero.memes.get("focus", 0.0) + 1.0

    world.say(
        f"{hero.id} was in {world.place.label} when {mystery.label} went missing."
    )
    world.say(
        f"On the floor were three clues: {mystery.clues[0]}, {mystery.clues[1]}, and {mystery.clues[2]}."
    )
    world.say(inner_monologue(hero, mystery))

    # Simulated reasoning state.
    world.facts["triple"] = 3
    world.facts["eight"] = 8
    world.facts["logic"] = True
    world.facts["path"] = "count the clues, compare the hiding spots, and test the one that fits"

    world.para()
    world.say(
        f"{hero.id} counted carefully, then checked each hiding place that could match all three clues."
    )
    world.say(
        f"{mystery.solved_by.capitalize()}, and the answer was simple: {mystery.label} had to be near {mystery.hidden_by}."
    )

    world.para()
    hero.memes["surprise"] = hero.memes.get("surprise", 0.0) + 1.0
    world.say(
        f"The surprise was that {mystery.surprise}."
    )
    world.say(
        f"{hero.id} laughed, because the mystery made perfect sense at last."
    )

    world.para()
    world.say(
        f"At the end, {hero.id} set {mystery.label} back in sight, and the room felt calm again."
    )
    world.facts["solved"] = True
    world.facts["surprise"] = mystery.surprise


def build_world(params: StoryParams) -> World:
    if params.place not in PLACES:
        raise StoryError(f"Unknown place: {params.place}")
    if params.mystery not in MYSTERIES:
        raise StoryError(f"Unknown mystery: {params.mystery}")

    place = PLACES[params.place]
    mystery = MYSTERIES[params.mystery]
    world = World(place, mystery)

    hero = world.add(Entity(
        id=params.hero_name,
        kind="character",
        type=params.hero_gender,
    ))
    sidekick_type = params.sidekick
    sidekick = world.add(Entity(
        id="sidekick",
        kind="character",
        type=sidekick_type if sidekick_type in {"cat", "dog"} else "thing",
        label=f"the {params.sidekick}",
    ))
    item = world.add(Entity(
        id="mystery_item",
        type="thing",
        label=mystery.label,
        owner=hero.id,
        held_by=None,
    ))

    world.facts.update(
        hero=hero,
        sidekick=sidekick,
        mystery_item=item,
        place=place,
        mystery=mystery,
    )
    solve_mystery(world, hero)
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]
    mystery: Mystery = f["mystery"]
    return [
        f"Write a short mystery for a young child using the words triple, eight, and logic.",
        f"Tell a gentle story where {hero.id} uses careful thinking to solve {mystery.label}.",
        f"Write a surprise ending about a hidden object that is found by counting clues.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    mystery: Mystery = f["mystery"]
    place: Place = f["place"]
    sidekick: Entity = f["sidekick"]
    return [
        QAItem(
            question=f"Who solved the mystery in {place.label}?",
            answer=f"{hero.id} solved it by thinking carefully and following the clues.",
        ),
        QAItem(
            question=f"What three clues helped {hero.id} think it through?",
            answer=f"The clues were triple, eight, and logic.",
        ),
        QAItem(
            question=f"What was surprising about {mystery.label}?",
            answer=f"The surprise was that {mystery.surprise}.",
        ),
        QAItem(
            question=f"Who was nearby while {hero.id} looked for the answer?",
            answer=f"The {sidekick.type if sidekick.type != 'thing' else 'sidekick'} was nearby as {hero.id} searched.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is logic?",
            answer="Logic is careful thinking that helps you tell what makes sense and what does not.",
        ),
        QAItem(
            question="What does a mystery mean?",
            answer="A mystery is something puzzling that needs clues and careful thought to solve.",
        ),
        QAItem(
            question="What is a surprise?",
            answer="A surprise is something unexpected that makes you stop and look again.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Params / generation / output
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny logic mystery story world.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=GENDERS)
    ap.add_argument("--sidekick", choices=SIDEKICKS)
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


def valid_combos() -> list[tuple[str, str]]:
    return [(pid, mid) for pid in PLACES for mid in MYSTERIES]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.mystery:
        combos = [c for c in combos if c[1] == args.mystery]
    if not combos:
        raise StoryError("No valid combination matches the given options.")

    place, mystery = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(GENDERS)
    name = args.name or rng.choice(HERO_NAMES)
    sidekick = args.sidekick or rng.choice(SIDEKICKS)
    return StoryParams(place=place, mystery=mystery, hero_name=name, hero_gender=gender, sidekick=sidekick)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.label:
            bits.append(f"label={e.label}")
        if e.owner:
            bits.append(f"owner={e.owner}")
        if e.held_by:
            bits.append(f"held_by={e.held_by}")
        if e.memes:
            bits.append(f"memes={dict(e.memes)}")
        if e.meters:
            bits.append(f"meters={dict(e.meters)}")
        lines.append(f"  {e.id:10} ({e.kind}/{e.type}) {' '.join(bits)}")
    lines.append(f"  facts: {world.facts}")
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


def asp_verify() -> int:
    import asp
    program = asp_program("#show solvable/1.\n#show surprise/1.")
    model = asp.one_model(program)
    got_solvable = set(asp.atoms(model, "solvable"))
    got_surprise = set(asp.atoms(model, "surprise"))
    expected = {(mid,) for mid in MYSTERIES}
    if got_solvable == expected and got_surprise == expected:
        print(f"OK: ASP parity matches {len(expected)} mysteries.")
        return 0
    print("MISMATCH between ASP and Python registry facts.")
    print("solvable:", sorted(got_solvable))
    print("surprise:", sorted(got_surprise))
    return 1


def asp_list() -> None:
    import asp
    model = asp.one_model(asp_program("#show solvable/1.\n#show surprise/1."))
    print("solvable:", sorted(set(asp.atoms(model, "solvable"))))
    print("surprise:", sorted(set(asp.atoms(model, "surprise"))))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show solvable/1.\n#show surprise/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        asp_list()
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for i, (place, mystery) in enumerate(valid_combos()):
            params = StoryParams(
                place=place,
                mystery=mystery,
                hero_name=HERO_NAMES[i % len(HERO_NAMES)],
                hero_gender=GENDERS[i % len(GENDERS)],
                sidekick=SIDEKICKS[i % len(SIDEKICKS)],
                seed=base_seed + i,
            )
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            rng = random.Random(base_seed + i)
            i += 1
            params = resolve_params(args, rng)
            params.seed = base_seed + i
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
            header = f"### {p.hero_name}: {p.mystery} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
