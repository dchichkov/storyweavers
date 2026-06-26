#!/usr/bin/env python3
"""
storyworlds/worlds/humongous_friendship_mystery_to_solve_animal_story.py
========================================================================

A small animal-story world about friendship, a puzzling mystery, and a
humongous helper that turns out to matter more than anyone expected.

Premise:
- A small animal notices a mystery in its home place.
- The friend worries, asks questions, and looks for clues.
- A very large animal/tool/object sometimes seems scary at first.
- The mystery is solved through cooperation, not force.

The story model tracks:
- physical meters: size, distance moved, carried objects, clues found
- emotional memes: worry, trust, curiosity, relief, friendship

This world deliberately keeps the cast and action small so the prose can stay
clear, concrete, and child-facing.
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
# Core data model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # animal | thing
    species: str = "thing"
    label: str = ""
    size: str = "small"  # small | medium | humongous
    plural: bool = False
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    id: str
    label: str
    indoors: bool = False
    notes: str = ""


@dataclass
class Mystery:
    id: str
    question: str
    lost_item: str
    likely_holder: str
    clue_kind: str
    solved_by: str
    solution: str


@dataclass
class StoryParams:
    place: str
    hero: str
    friend: str
    humongous: str
    mystery: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
PLACES = {
    "farmyard": Place("farmyard", "the farmyard", indoors=False, notes="muddy tracks and hay"),
    "pond": Place("pond", "the pond bank", indoors=False, notes="reeds, stones, and ripples"),
    "wood": Place("wood", "the little wood", indoors=False, notes="soft moss and tangled roots"),
    "barn": Place("barn", "the barn loft", indoors=True, notes="dusty beams and straw"),
}

MYSTERIES = {
    "bell": Mystery(
        id="bell",
        question="Who made the tiny bell go missing?",
        lost_item="a tiny bell",
        likely_holder="nest",
        clue_kind="shiny feather",
        solved_by="the bird nest behind the hay",
        solution="the bell had rolled into a nest of soft feathers",
    ),
    "berry": Mystery(
        id="berry",
        question="Who ate the berry pile?",
        lost_item="a berry basket",
        likely_holder="burrow",
        clue_kind="purple smudge",
        solved_by="the rabbit burrow under the roots",
        solution="the basket had been tucked beside the burrow, where berries were being shared",
    ),
    "map": Mystery(
        id="map",
        question="Who took the chalk map?",
        lost_item="a chalk map",
        likely_holder="loft",
        clue_kind="dusty pawprint",
        solved_by="the barn loft beam",
        solution="the map had blown up onto a beam and stuck there",
    ),
}

ANIMALS = {
    "mouse": {"species": "mouse", "size": "small", "kind": "animal"},
    "rabbit": {"species": "rabbit", "size": "small", "kind": "animal"},
    "fox": {"species": "fox", "size": "small", "kind": "animal"},
    "bear": {"species": "bear", "size": "humongous", "kind": "animal"},
    "goat": {"species": "goat", "size": "humongous", "kind": "animal"},
}

HERO_NAMES = {
    "mouse": ["Milo", "Mina", "Mori"],
    "rabbit": ["Bunny", "Ruby", "Rae"],
    "fox": ["Finn", "Faye", "Flint"],
    "bear": ["Bram", "Bruno", "Bess"],
    "goat": ["Gigi", "Gus", "Glen"],
}

FRIEND_NAMES = {
    "mouse": ["Dot", "Pip", "Nina"],
    "rabbit": ["Nell", "Toto", "Puddle"],
    "fox": ["Juno", "Tess", "Wren"],
    "bear": ["Moss", "Otis", "Bela"],
    "goat": ["Lark", "Penny", "Nori"],
}

HUMONGOUS_OPTIONS = ["bear", "goat"]


# ---------------------------------------------------------------------------
# World state
# ---------------------------------------------------------------------------
@dataclass
class World:
    place: Place
    hero: Entity
    friend: Entity
    humongous: Entity
    mystery: Mystery
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def add_meter(self, entity: Entity, key: str, amount: float = 1.0) -> None:
        entity.meters[key] = entity.meters.get(key, 0.0) + amount

    def add_meme(self, entity: Entity, key: str, amount: float = 1.0) -> None:
        entity.memes[key] = entity.memes.get(key, 0.0) + amount


# ---------------------------------------------------------------------------
# Story engine
# ---------------------------------------------------------------------------
def build_world(params: StoryParams) -> World:
    place = PLACES[params.place]
    mystery = MYSTERIES[params.mystery]

    hero_species = params.hero
    friend_species = params.friend
    big_species = params.humongous

    hero_name = random.choice(HERO_NAMES[hero_species])
    friend_name = random.choice(FRIEND_NAMES[friend_species])
    big_name = random.choice(FRIEND_NAMES[big_species])

    hero = Entity(
        id=hero_name,
        kind="animal",
        species=hero_species,
        size=ANIMALS[hero_species]["size"],
        meters={"steps": 0.0, "clues": 0.0},
        memes={"curiosity": 1.0, "worry": 0.0, "trust": 1.0, "relief": 0.0, "friendship": 1.0},
    )
    friend = Entity(
        id=friend_name,
        kind="animal",
        species=friend_species,
        size=ANIMALS[friend_species]["size"],
        meters={"steps": 0.0},
        memes={"curiosity": 1.0, "worry": 0.0, "trust": 1.0, "relief": 0.0, "friendship": 1.0},
    )
    humongous = Entity(
        id=big_name,
        kind="animal",
        species=big_species,
        size="humongous",
        meters={"steps": 0.0, "helped": 0.0},
        memes={"worry": 0.0, "kindness": 1.0, "friendship": 1.0},
    )
    return World(place=place, hero=hero, friend=friend, humongous=humongous, mystery=mystery)


def tell_story(world: World) -> None:
    h, f, g, m, place = world.hero, world.friend, world.humongous, world.mystery, world.place

    world.say(
        f"In {place.label}, {h.id} was a tiny {h.species} who loved poking around for clues."
    )
    world.say(
        f"{f.id} was {h.id}'s friend, and together they had a warm little habit of helping each other."
    )
    world.say(
        f"One morning, they found a mystery: {m.question} "
        f"The missing thing was {m.lost_item}, and the first clue was a {m.clue_kind}."
    )

    world.para()
    world.add_meme(h, "worry", 1.0)
    world.add_meme(f, "worry", 1.0)
    world.add_meter(h, "steps", 2.0)
    world.add_meter(f, "steps", 2.0)
    world.say(
        f"They searched under leaves, beside stones, and through the soft grass. "
        f"{h.id} stayed curious, but {h.id} also felt a little worried because the clue did not make sense yet."
    )
    world.say(
        f"Then they heard a heavy thump-thump. A humongous {g.species} named {g.id} came walking by."
    )
    world.say(
        f"{h.id} stepped back at first, because {g.id} looked very big beside {h.id}'s little paws."
    )

    world.para()
    world.add_meme(g, "kindness", 1.0)
    world.add_meme(g, "friendship", 1.0)
    world.add_meme(h, "trust", 1.0)
    world.add_meme(f, "trust", 1.0)
    world.say(
        f"But {g.id} did not push or rush. {g.id} lowered a gentle head and said, "
        f'"I can help look where small feet cannot reach."'
    )
    world.say(
        f"That sounded brave and friendly, so {h.id} and {f.id} nodded. "
        f"The three of them followed the {m.clue_kind} to {m.solved_by}."
    )
    world.say(
        f"There, they found the answer: {m.solution}."
    )

    world.para()
    world.add_meter(g, "helped", 1.0)
    world.add_meter(h, "clues", 1.0)
    world.add_meme(h, "relief", 1.0)
    world.add_meme(f, "relief", 1.0)
    world.add_meme(h, "friendship", 1.0)
    world.add_meme(f, "friendship", 1.0)
    world.say(
        f"{h.id} laughed with relief, and {f.id} laughed too. "
        f"With {g.id}'s help, the mystery was solved, and the missing thing was no longer missing."
    )
    world.say(
        f"By evening, the little friends were walking home together, and even the humongous helper looked happy to belong."
    )

    world.facts.update(
        place=place,
        hero=h,
        friend=f,
        humongous=g,
        mystery=m,
        solved=True,
        clue=m.clue_kind,
        answer=m.solution,
    )


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    h, f, g, m, place = world.facts["hero"], world.facts["friend"], world.facts["humongous"], world.facts["mystery"], world.facts["place"]
    return [
        f"Write a short animal story about {h.species} and {f.species} who solve a mystery at {place.label}, and include a humongous {g.species}.",
        f"Tell a gentle friendship story where {h.id} and {f.id} find a clue and discover what happened to {m.lost_item}.",
        f"Write a child-friendly mystery story in which a humongous helper turns out to be kind and useful.",
    ]


def story_qa(world: World) -> list[QAItem]:
    h, f, g, m, place = world.facts["hero"], world.facts["friend"], world.facts["humongous"], world.facts["mystery"], world.facts["place"]
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about {h.id}, a small {h.species}, and {f.id}, {h.id}'s friend, in {place.label}.",
        ),
        QAItem(
            question=f"What mystery did they try to solve?",
            answer=f"They tried to solve the mystery of {m.question.lower()} The missing thing was {m.lost_item}.",
        ),
        QAItem(
            question=f"Why did {h.id} feel a little worried at first?",
            answer=f"{h.id} felt worried because the clue did not make sense yet, and the humongous {g.species} looked very big at first.",
        ),
        QAItem(
            question=f"How was the mystery solved?",
            answer=f"It was solved when {g.id} helped them follow the clue to {m.solved_by}, where they found that {m.solution}.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with the friends feeling happy and relieved because the mystery was solved and they walked home together.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a mystery?",
            answer="A mystery is something puzzling or unknown that people or animals try to figure out.",
        ),
        QAItem(
            question="What does a friend do?",
            answer="A friend helps, shares, and stays kind during hard moments or happy ones.",
        ),
        QAItem(
            question="What does humongous mean?",
            answer="Humongous means very, very big.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== Generation prompts ==", *[f"- {p}" for p in sample.prompts], "", "== Story Q&A =="]
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== World Q&A ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
#show valid_story/4.
animal(mouse).
animal(rabbit).
animal(fox).
animal(bear).
animal(goat).

size(mouse, small).
size(rabbit, small).
size(fox, small).
size(bear, humongous).
size(goat, humongous).

place(farmyard).
place(pond).
place(wood).
place(barn).

mystery(bell).
mystery(berry).
mystery(map).

friendly(A) :- animal(A).
humongous(A) :- size(A, humongous).

solve_story(P, H, F, G, M) :- place(P), animal(H), animal(F), humongous(G), mystery(M), H != F, H != G, F != G.
valid_story(P, H, F, G) :- place(P), animal(H), animal(F), humongous(G), H != F, H != G, F != G.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for mid in MYSTERIES:
        lines.append(asp.fact("mystery", mid))
    for aid, ad in ANIMALS.items():
        lines.append(asp.fact("animal", aid))
        lines.append(asp.fact("size", aid, ad["size"]))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_stories())
    cl = set(asp_valid_stories())
    if py == cl:
        print(f"OK: ASP matches Python ({len(py)} valid stories).")
        return 0
    print("MISMATCH between ASP and Python:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in ASP:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Python reasonableness gate
# ---------------------------------------------------------------------------
def valid_stories() -> list[tuple[str, str, str, str]]:
    out = []
    for place in PLACES:
        for hero in ANIMALS:
            for friend in ANIMALS:
                for big in HUMONGOUS_OPTIONS:
                    if hero != friend and hero != big and friend != big:
                        out.append((place, hero, friend, big))
    return out


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal story world: friendship, mystery, and a humongous helper.")
    ap.add_argument("--place", choices=PLACES.keys())
    ap.add_argument("--hero", choices=ANIMALS.keys())
    ap.add_argument("--friend", choices=ANIMALS.keys())
    ap.add_argument("--humongous", choices=HUMONGOUS_OPTIONS)
    ap.add_argument("--mystery", choices=MYSTERIES.keys())
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
    choices = []
    for place in (args.place,) if args.place else tuple(PLACES.keys()):
        for hero in (args.hero,) if args.hero else tuple(ANIMALS.keys()):
            for friend in (args.friend,) if args.friend else tuple(ANIMALS.keys()):
                for hum in (args.humongous,) if args.humongous else tuple(HUMONGOUS_OPTIONS):
                    for mystery in (args.mystery,) if args.mystery else tuple(MYSTERIES.keys()):
                        if hero == friend or hero == hum or friend == hum:
                            continue
                        choices.append((place, hero, friend, hum, mystery))
    if not choices:
        raise StoryError("No valid story matches those options.")
    place, hero, friend, hum, mystery = rng.choice(sorted(choices))
    return StoryParams(place=place, hero=hero, friend=friend, humongous=hum, mystery=mystery)


def generate(params: StoryParams) -> StorySample:
    rng = random.Random(params.seed if params.seed is not None else 0)
    random_state = random.getstate()
    random.setstate(rng.getstate())
    try:
        world = build_world(params)
        tell_story(world)
    finally:
        random.setstate(random_state)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in [world.hero, world.friend, world.humongous]:
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"{e.id} ({e.species}, {e.size}) meters={meters} memes={memes}")
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


CURATED = [
    StoryParams(place="farmyard", hero="mouse", friend="rabbit", humongous="bear", mystery="bell"),
    StoryParams(place="pond", hero="fox", friend="mouse", humongous="goat", mystery="berry"),
    StoryParams(place="barn", hero="rabbit", friend="fox", humongous="bear", mystery="map"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program(""))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(valid_stories())} valid stories")
        for row in valid_stories():
            print(" ".join(row))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
