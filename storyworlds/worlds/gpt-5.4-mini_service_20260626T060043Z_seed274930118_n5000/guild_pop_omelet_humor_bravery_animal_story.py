#!/usr/bin/env python3
"""
A small standalone story world: an animal guild, a popping skillet, and an omelet
that turns into a test of humor and bravery.

Premise:
- A young animal wants to help the guild make breakfast.
- The pan pops when the eggs hit the heat.
- The hero feels nervous, then uses humor and bravery to finish the omelet.
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    plural: bool = False

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"cat", "mouse", "fox", "rabbit", "bear", "dog"}:
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the guild kitchen"


@dataclass
class StoryParams:
    name: str
    species: str
    mentor: str
    seed: Optional[int] = None


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[str] = field(default_factory=set)
    pop_count: int = 0
    omelet_done: bool = False

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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTING = Setting()

ANIMALS = {
    "mouse": {"type": "mouse", "trait": "small"},
    "rabbit": {"type": "rabbit", "trait": "quick"},
    "fox": {"type": "fox", "trait": "clever"},
    "bear": {"type": "bear", "trait": "gentle"},
    "cat": {"type": "cat", "trait": "curious"},
    "dog": {"type": "dog", "trait": "loyal"},
}

NAMES = {
    "mouse": ["Milo", "Mina", "Moe"],
    "rabbit": ["Ruby", "Rory", "Nina"],
    "fox": ["Fenn", "Fia", "Luna"],
    "bear": ["Bram", "Bibi", "Otto"],
    "cat": ["Cleo", "Toby", "Pip"],
    "dog": ["Poppy", "Dale", "Bax"],
}

MENTORS = ["Captain Spoon", "Chef Willow", "Auntie Crumb"]

# ASP-compatible registry facts use these identifiers
SPECIES_IDS = {k: k for k in ANIMALS.keys()}


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A story is valid when a hero is in the guild, can make an omelet,
% and the 'pop' event is used as a harmless surprise that leads to humor
% and bravery before the omelet is finished.

hero(H) :- species(H, _).
valid_story(H, M) :- hero(H), mentor(M), omelet_task, pop_event, humor, bravery.

requires_bravery(omelet_task).
supports_humor(pop_event).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SPECIES_IDS:
        lines.append(asp.fact("species", sid, ANIMALS[sid]["type"]))
    for m in MENTORS:
        lines.append(asp.fact("mentor", m))
    lines.append(asp.fact("omelet_task"))
    lines.append(asp.fact("pop_event"))
    lines.append(asp.fact("humor"))
    lines.append(asp.fact("bravery"))
    return "\n".join(lines)

def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"

def asp_valid() -> bool:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return bool(model)


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------

def build_world(params: StoryParams) -> World:
    if params.species not in ANIMALS:
        raise StoryError(f"Unknown species: {params.species}")
    if not params.name:
        raise StoryError("A hero name is required.")

    world = World(SETTING)
    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.species,
        label=params.name,
        traits=[ANIMALS[params.species]["trait"], "kind"],
        meters={"nervous": 0.0, "skill": 0.0},
        memes={"humor": 0.0, "bravery": 0.0, "pride": 0.0},
    ))
    mentor = world.add(Entity(
        id="mentor",
        kind="character",
        type="mentor",
        label=params.mentor,
        meters={"patience": 1.0},
        memes={"humor": 0.0, "bravery": 0.0},
    ))
    pan = world.add(Entity(
        id="pan",
        type="pan",
        label="a little pan",
        phrase="a little pan",
    ))
    eggs = world.add(Entity(
        id="eggs",
        type="eggs",
        label="eggs",
        phrase="fresh eggs",
        plural=True,
    ))

    world.facts.update(hero=hero, mentor=mentor, pan=pan, eggs=eggs, params=params)
    return world


def _intro(world: World) -> None:
    hero: Entity = world.facts["hero"]
    mentor: Entity = world.facts["mentor"]
    world.say(
        f"At the guild kitchen, {hero.label} was a {hero.traits[0]} little {hero.type} who loved helping."
    )
    world.say(
        f"{mentor.label} smiled and said the guild was making breakfast, because an omelet fed everyone well."
    )

def _task(world: World) -> None:
    hero: Entity = world.facts["hero"]
    world.para()
    world.say(
        f"{hero.label} wanted to crack the eggs for the guild, but the hot pan made a tiny pop."
    )
    hero.meters["nervous"] += 1
    world.pop_count += 1
    world.say(
        f"The sound was silly and sharp, and {hero.label} jumped back with wide eyes."
    )

def _humor(world: World) -> None:
    hero: Entity = world.facts["hero"]
    mentor: Entity = world.facts["mentor"]
    if hero.meters["nervous"] < 1:
        return
    hero.memes["humor"] += 1
    world.say(
        f"{mentor.label} pointed at the pan and said, 'That pop was only the pan saying hello.'"
    )
    world.say(
        f"{hero.label} snorted a laugh, because even the eggs seemed to be wearing a funny voice."
    )

def _bravery(world: World) -> None:
    hero: Entity = world.facts["hero"]
    mentor: Entity = world.facts["mentor"]
    hero.memes["bravery"] += 1
    hero.meters["skill"] += 1
    world.say(
        f"Then {hero.label} took a deep breath, stood tall, and tried again."
    )
    world.say(
        f"{mentor.label} stayed close, and the little {hero.type} cracked the eggs neatly into the pan."
    )

def _finish(world: World) -> None:
    hero: Entity = world.facts["hero"]
    world.para()
    world.say(
        f"The eggs set soft and gold, and soon the omelet slid onto a plate without another pop."
    )
    world.say(
        f"{hero.label} carried it to the guild table, proud and smiling, because bravery had helped the breakfast finish."
    )
    world.omelet_done = True


def tell(params: StoryParams) -> World:
    world = build_world(params)
    _intro(world)
    _task(world)
    _humor(world)
    _bravery(world)
    _finish(world)
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]
    mentor: Entity = f["mentor"]
    return [
        f"Write a short animal story about {hero.label} joining a guild kitchen to make an omelet.",
        f"Tell a child-friendly tale where a pop in the pan leads to humor and bravery.",
        f"Write a gentle story about {hero.label} and {mentor.label} finishing breakfast together.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero: Entity = world.facts["hero"]
    mentor: Entity = world.facts["mentor"]
    return [
        QAItem(
            question=f"Where was {hero.label} when the breakfast story began?",
            answer=f"{hero.label} was at the guild kitchen with {mentor.label}, helping the guild make breakfast."
        ),
        QAItem(
            question=f"What noisy surprise made {hero.label} jump back?",
            answer=f"A tiny pop came from the hot pan, and that made {hero.label} feel nervous for a moment."
        ),
        QAItem(
            question=f"How did {hero.label} finish the omelet after feeling scared?",
            answer=f"{hero.label} laughed at the silly pop, found some bravery, and cracked the eggs into the pan again."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a guild?",
            answer="A guild is a group of helpers who work together at the same job."
        ),
        QAItem(
            question="What is an omelet?",
            answer="An omelet is a soft egg dish cooked in a pan and folded or served warm."
        ),
        QAItem(
            question="Why can humor help when something surprising happens?",
            answer="Humor can make a scary moment feel smaller and help everyone relax and try again."
        ),
        QAItem(
            question="What is bravery?",
            answer="Bravery means doing something hard or scary even when you feel nervous."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    lines.append(f"pop_count={world.pop_count}")
    lines.append(f"omelet_done={world.omelet_done}")
    for e in world.entities.values():
        lines.append(
            f"{e.id}: type={e.type} meters={{{', '.join(f'{k}:{v}' for k, v in e.meters.items() if v)}}} "
            f"memes={{{', '.join(f'{k}:{v}' for k, v in e.memes.items() if v)}}}"
        )
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Generation / CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal guild story world: pop, omelet, humor, bravery.")
    ap.add_argument("--name", choices=[n for names in NAMES.values() for n in names])
    ap.add_argument("--species", choices=sorted(ANIMALS))
    ap.add_argument("--mentor", choices=MENTORS)
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
    species = args.species or rng.choice(sorted(ANIMALS))
    name = args.name or rng.choice(NAMES[species])
    mentor = args.mentor or rng.choice(MENTORS)
    return StoryParams(name=name, species=species, mentor=mentor, seed=args.seed)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return

    if args.verify:
        if asp_valid():
            print("OK: ASP twin produced a valid story model.")
            return
        raise SystemExit(1)

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for species in sorted(ANIMALS):
            params = StoryParams(name=NAMES[species][0], species=species, mentor=MENTORS[0], seed=base_seed)
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        for i in range(max(1, args.n)):
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
