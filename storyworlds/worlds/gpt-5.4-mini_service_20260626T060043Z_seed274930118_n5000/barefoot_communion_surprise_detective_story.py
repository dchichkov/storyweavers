#!/usr/bin/env python3
"""
A small standalone story world for a barefoot communion surprise detective tale.

The world is built around a child detective, a quiet chapel-side mystery, and a
careful surprise ending. The prose stays concrete and state-driven, with a
detective-story rhythm: clue, search, reveal.
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    location: str = ""
    hidden: bool = False
    plural: bool = False
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "nun", "aunt"}
        male = {"boy", "father", "man", "priest", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    name: str
    indoor: bool = True
    quiet: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Case:
    id: str
    title: str
    clue: str
    reveal: str
    surprise: str
    trail: str
    risk: str
    fix: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[str] = set()

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy
        w = World(self.place)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

PLACES = {
    "chapel": Place(name="the chapel", indoor=True, quiet=True, affords={"communion"}),
    "hall": Place(name="the parish hall", indoor=True, quiet=True, affords={"communion"}),
}

CASES = {
    "missing_shoes": Case(
        id="missing_shoes",
        title="The Missing Shoes",
        clue="a pale ribbon under the bench",
        reveal="the shoes were waiting in a basket with a tiny card",
        surprise="a surprise pair of soft slippers",
        trail="small marks on the dusty floor",
        risk="bare feet on the cold stone",
        fix="soft slippers",
        tags={"barefoot", "communion", "surprise", "detective"},
    ),
    "hidden_note": Case(
        id="hidden_note",
        title="The Hidden Note",
        clue="a folded note behind the hymn book",
        reveal="the note led to a little surprise treat after communion",
        surprise="a small wrapped biscuit",
        trail="a crumb trail by the pew",
        risk="a child wandering away from the group",
        fix="holding hands with the guide",
        tags={"barefoot", "communion", "surprise", "detective"},
    ),
    "lost_card": Case(
        id="lost_card",
        title="The Lost Card",
        clue="a white card stuck to the offering table",
        reveal="the card named the child as the surprise helper",
        surprise="a surprise helper card",
        trail="a trail of careful footprints",
        risk="the surprise being missed",
        fix="following the clues slowly",
        tags={"barefoot", "communion", "surprise", "detective"},
    ),
}

GIRL_NAMES = ["Mina", "Lily", "Nora", "Ivy", "Maya"]
BOY_NAMES = ["Theo", "Finn", "Eli", "Noah", "Ben"]
TRAITS = ["curious", "careful", "brave", "quiet", "sharp-eyed"]


# ---------------------------------------------------------------------------
# Story params
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    case: str
    name: str
    gender: str
    guide: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
place_ok(P) :- place(P).
case_ok(C) :- case(C).

valid_story(P, C, G) :- place_ok(P), case_ok(C), guide(G).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for c in CASES:
        lines.append(asp.fact("case", c))
    lines.append(asp.fact("guide", "mother"))
    lines.append(asp.fact("guide", "father"))
    return "\n".join(lines)

def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"

def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    atoms = set(asp.atoms(model, "valid_story"))
    python = {(p, c, g) for p in PLACES for c in CASES for g in ("mother", "father")}
    if atoms == python:
        print(f"OK: clingo matches python gate ({len(python)} stories).")
        return 0
    print("MISMATCH between clingo and python gate.")
    print("only in clingo:", sorted(atoms - python))
    print("only in python:", sorted(python - atoms))
    return 1


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------

def is_reasonable(place: Place, case: Case) -> bool:
    return "communion" in place.affords and {"barefoot", "surprise", "detective"} <= case.tags


def choose_fix(case: Case) -> str:
    return case.fix


def choose_case(place: Place, rng: random.Random) -> Case:
    options = [c for c in CASES.values() if is_reasonable(place, c)]
    if not options:
        raise StoryError("No reasonable case matches the chosen place.")
    return rng.choice(options)


# ---------------------------------------------------------------------------
# Narrative engine
# ---------------------------------------------------------------------------

def _emphatic(title: str) -> str:
    return title[0].upper() + title[1:]

def tell(world: World, hero: Entity, guide: Entity, case: Case) -> None:
    place = world.place

    shoe = world.add(Entity(
        id="shoes",
        type="shoes",
        label="shoes",
        phrase="a pair of polished shoes",
        owner=hero.id,
        hidden=True,
    ))
    clue = world.add(Entity(
        id="clue",
        type="note",
        label="clue",
        phrase=case.clue,
        hidden=True,
    ))
    surprise = world.add(Entity(
        id="surprise",
        type="gift",
        label="surprise",
        phrase=case.surprise,
        hidden=True,
    ))

    # Act 1
    world.say(
        f"{hero.id} was a {hero.memes.get('trait', 'curious')} little detective who noticed every small thing."
    )
    world.say(
        f"On the morning of communion, {hero.id} was barefoot because {hero.pronoun('possessive')} shoes had gone missing."
    )
    world.say(
        f"{hero.id}'s {guide.label} stayed calm and said, 'Let's look for clues.'"
    )

    world.para()

    # Act 2
    world.say(
        f"The chapel was quiet, and the cold floor made {hero.id} step softly."
    )
    hero.memes["alert"] = 1
    world.say(
        f"Then {hero.id} spotted {case.clue}, a clue that looked almost too small to matter."
    )
    world.say(
        f"{hero.id} followed {case.trail} past the pews and toward the communion table."
    )
    world.say(
        f"The trail ended in a nook behind the bench, where something hidden was waiting."
    )

    world.para()

    # Act 3
    shoe.hidden = False
    clue.hidden = False
    surprise.hidden = False
    shoe.location = "basket"
    surprise.location = "basket"
    world.say(
        f"There, {case.reveal}."
    )
    world.say(
        f"Inside the basket were {shoe.phrase} and {case.surprise}."
    )
    world.say(
        f"{guide.id} smiled and explained it was a surprise for a child who had been brave all morning."
    )
    world.say(
        f"{hero.id} put on the {choose_fix(case)} and went to communion smiling, with the mystery solved at last."
    )
    world.say(
        f"By the time the service began, {hero.id} was no longer barefoot, and the chapel felt warm and bright."
    )

    world.facts.update(
        hero=hero,
        guide=guide,
        case=case,
        place=place,
        shoe=shoe,
        clue=clue,
        surprise=surprise,
        resolved=True,
    )


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]  # type: ignore[assignment]
    case: Case = f["case"]  # type: ignore[assignment]
    place: Place = f["place"]  # type: ignore[assignment]
    return [
        f'Write a short detective story for a young child about a barefoot child at {place.name} during communion.',
        f"Tell a gentle mystery where {hero.id} notices {case.clue} and finds a surprise before communion.",
        f"Write a child-friendly detective story with clues, a surprise, and a happy ending in {place.name}.",
    ]

def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]  # type: ignore[assignment]
    guide: Entity = f["guide"]  # type: ignore[assignment]
    case: Case = f["case"]  # type: ignore[assignment]
    place: Place = f["place"]  # type: ignore[assignment]
    return [
        QAItem(
            question=f"Why was {hero.id} barefoot at {place.name}?",
            answer=f"{hero.id} was barefoot because {hero.pronoun('possessive')} shoes had gone missing before communion, so {hero.id} had to look for them like a little detective.",
        ),
        QAItem(
            question=f"What clue did {hero.id} notice first?",
            answer=f"{hero.id} noticed {case.clue}, and that clue helped point the way toward the hidden basket.",
        ),
        QAItem(
            question=f"What was the surprise in the story?",
            answer=f"The surprise was {case.surprise}, and the missing shoes were waiting with it.",
        ),
        QAItem(
            question=f"How did {hero.id}'s {guide.label} help?",
            answer=f"{guide.id} stayed calm, asked {hero.id} to look for clues, and helped turn the search into a safe, happy mystery.",
        ),
        QAItem(
            question=f"What changed at the end of the communion morning?",
            answer=f"At the end, {hero.id} was wearing shoes again, the mystery was solved, and the chapel felt warm instead of chilly.",
        ),
    ]

def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is communion?",
            answer="Communion is a quiet Christian service where people gather, listen, pray, and take part in a special meal or blessing.",
        ),
        QAItem(
            question="What does barefoot mean?",
            answer="Barefoot means not wearing shoes or socks, so your feet touch the floor directly.",
        ),
        QAItem(
            question="What is a detective story?",
            answer="A detective story is a story about looking for clues, solving a mystery, and finding out what really happened.",
        ),
        QAItem(
            question="What is a surprise?",
            answer="A surprise is something you do not expect, like a hidden gift or a sudden happy discovery.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World knowledge questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Sampling / generation
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Barefoot communion surprise detective story world.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--case", choices=CASES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--guide", choices=["mother", "father"])
    ap.add_argument("--name")
    ap.add_argument("--trait", choices=TRAITS)
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
    place_key = args.place or rng.choice(list(PLACES))
    place = PLACES[place_key]
    case_key = args.case or choose_case(place, rng).id
    if args.case and not is_reasonable(place, CASES[args.case]):
        raise StoryError("That case does not fit the chosen place.")
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    guide = args.guide or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place_key, case=case_key, name=name, gender=gender, guide=guide, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = World(PLACES[params.place])
    hero_type = params.gender
    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type=hero_type,
        label=params.name,
        memes={"trait": 1.0, params.trait: 1.0},
    ))
    guide = world.add(Entity(
        id=params.guide,
        kind="character",
        type=params.guide,
        label=params.guide,
    ))
    case = CASES[params.case]
    tell(world, hero, guide, case)
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
        for e in sample.world.entities.values():
            bits = []
            if e.hidden:
                bits.append("hidden")
            if e.location:
                bits.append(f"location={e.location}")
            if e.memes:
                bits.append(f"memes={e.memes}")
            print(f"{e.id}: {e.type} {' '.join(bits)}")
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/3."))
        atoms = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(atoms)} valid stories:")
        for atom in atoms:
            print(" ", atom)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    if args.all:
        samples = []
        for place in PLACES:
            for case in CASES:
                for gender in ("girl", "boy"):
                    params = StoryParams(
                        place=place,
                        case=case,
                        name=GIRL_NAMES[0] if gender == "girl" else BOY_NAMES[0],
                        gender=gender,
                        guide="mother",
                        trait="curious",
                    )
                    samples.append(generate(params))
    else:
        samples = []
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
