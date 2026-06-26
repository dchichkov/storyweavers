#!/usr/bin/env python3
"""
A standalone storyworld for a small detective tale with a little magic and a
Spanish-language clue trail.

Premise:
A child detective in a cozy town uses careful observation and a tiny magic tool
to solve a case. The case begins with a missing item, a suspicious detail, and a
Spanish word that matters. The turn comes when the detective notices that magic
can reveal what ordinary eyes missed. The ending proves the mystery was solved
and the right owner got the lost thing back.

The simulation models:
- typed entities with physical meters and emotional memes
- clue objects, places, and suspects
- a simple reasoning path from uncertainty -> investigation -> reveal -> repair

The world is intentionally small and constraint-checked so every generated story
reads as a complete, child-facing detective story.
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
# World entities
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing | place
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    hidden_in: Optional[str] = None
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
    mood: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Case:
    missing: str
    missing_phrase: str
    where_found: str
    witness: str
    clue_spanish: str
    magic_item: str
    magic_power: str
    suspect: str
    suspect_reason: str
    ending_line: str


class World:
    def __init__(self, place: Place):
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.lines: list[list[str]] = [[]]
        self.facts: dict = {}
        self.trace: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.lines[-1].append(text)
            self.trace.append(text)

    def para(self) -> None:
        if self.lines[-1]:
            self.lines.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.lines if p)

    def copy(self) -> "World":
        import copy as _copy
        w = World(self.place)
        w.entities = _copy.deepcopy(self.entities)
        w.lines = [[]]
        w.facts = dict(self.facts)
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
PLACES = {
    "library": Place(id="library", label="the library", mood="quiet", affords={"search", "glow"}),
    "market": Place(id="market", label="the market", mood="busy", affords={"search", "glow"}),
    "garden": Place(id="garden", label="the garden", mood="green", affords={"search", "glow"}),
}

CASE_BOOK = {
    "book": Case(
        missing="book",
        missing_phrase="a blue book about stars",
        where_found="behind a stack of old maps",
        witness="the librarian",
        clue_spanish="libro",
        magic_item="a small silver magnifying glass",
        magic_power="shine with a soft blue spark",
        suspect="the wind",
        suspect_reason="it had blown the loose page under a table",
        ending_line="The book was back on the shelf, and the library felt calm again.",
    ),
    "key": Case(
        missing="key",
        missing_phrase="a brass key with a ribbon",
        where_found="inside a flowerpot",
        witness="the gardener",
        clue_spanish="llave",
        magic_item="a tiny glass lantern",
        magic_power="glow brighter near hidden things",
        suspect="the cat",
        suspect_reason="it had nudged the key while chasing a string",
        ending_line="The key jingled safely in the owner’s hand, and the garden looked peaceful.",
    ),
    "toy": Case(
        missing="toy",
        missing_phrase="a little toy train",
        where_found="under a bench",
        witness="the shopkeeper",
        clue_spanish="juguete",
        magic_item="a pocket mirror with a moon carved on it",
        magic_power="show tiny reflections that pointed the way",
        suspect="the child’s coat",
        suspect_reason="it had carried the toy when the child ran indoors",
        ending_line="The toy train rolled home at last, right where it belonged.",
    ),
}

CHARACTER_NAMES = ["Mia", "Leo", "Nora", "Ben", "Ava", "Theo", "Luna", "Noah"]
ADJECTIVES = ["careful", "curious", "brave", "gentle", "sharp-eyed"]


# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    case: str
    name: str
    parent: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Reasoning helpers
# ---------------------------------------------------------------------------
def reasonableness_gate(params: StoryParams) -> None:
    if params.place not in PLACES:
        raise StoryError("Unknown place.")
    if params.case not in CASE_BOOK:
        raise StoryError("Unknown case.")
    if params.name.strip() == "":
        raise StoryError("A detective needs a name.")
    if params.trait not in ADJECTIVES:
        raise StoryError("Unknown detective trait.")


def case_is_plausible(place: Place, case: Case) -> bool:
    return "search" in place.affords and "glow" in place.affords


# ---------------------------------------------------------------------------
# Story construction
# ---------------------------------------------------------------------------
def build_world(params: StoryParams) -> World:
    reasonableness_gate(params)
    place = PLACES[params.place]
    case = CASE_BOOK[params.case]
    if not case_is_plausible(place, case):
        raise StoryError("This case cannot happen in this place.")

    world = World(place)
    detective = world.add(Entity(id=params.name, kind="character", type="boy" if params.name in {"Leo", "Ben", "Theo", "Noah"} else "girl"))
    parent = world.add(Entity(id="Parent", kind="character", type=params.parent, label=params.parent))
    missing = world.add(Entity(
        id="missing",
        kind="thing",
        type=case.missing,
        label=case.missing,
        phrase=case.missing_phrase,
        owner="Owner",
        hidden_in=case.where_found,
    ))
    owner = world.add(Entity(id="Owner", kind="character", type="woman", label="the owner"))
    clue = world.add(Entity(id="clue", kind="thing", type="word", label=case.clue_spanish, phrase=f"the Spanish word {case.clue_spanish}"))
    magic = world.add(Entity(id="magic", kind="thing", type="magic", label=case.magic_item, phrase=case.magic_item))
    suspect = world.add(Entity(id="Suspect", kind="character", type="thing", label=case.suspect))

    # Physical / emotional state
    detective.memes["curiosity"] = 1
    detective.memes["doubt"] = 1
    detective.meters["attention"] = 1
    missing.meters["lost"] = 1
    magic.meters["glow"] = 1

    world.facts.update(
        detective=detective,
        parent=parent,
        owner=owner,
        missing=missing,
        clue=clue,
        magic=magic,
        suspect=suspect,
        case=case,
        place=place,
    )

    # Act 1
    world.say(
        f"{detective.id} was a {params.trait} little detective who loved quiet clues."
    )
    world.say(
        f"One day at {place.label}, {detective.id} heard that {case.missing_phrase} had gone missing."
    )
    world.say(
        f"{parent.pronoun('subject').capitalize()} said the case felt strange, because someone had left behind the Spanish word {case.clue_spanish}."
    )

    # Act 2
    world.para()
    world.say(
        f"{detective.id} opened {case.magic_item} and watched it {case.magic_power}."
    )
    world.say(
        f"{detective.id} looked under benches and behind boxes, asking careful questions."
    )
    world.say(
        f"{case.witness.capitalize()} whispered that {case.suspect_reason}."
    )
    detective.memes["focus"] = 1
    detective.memes["hope"] = 1

    # Reveal
    world.para()
    world.say(
        f"The magic glow grew brightest near {case.where_found}, and {detective.id} smiled."
    )
    world.say(
        f"There was the {case.missing} at last, tucked {case.where_found}."
    )
    missing.meters["found"] = 1
    missing.hidden_in = None
    suspect.memes["guilty"] = 1

    # Resolution
    world.para()
    world.say(
        f"{detective.id} carried the {case.missing} back to {owner.id}, and everyone breathed easier."
    )
    detective.memes["pride"] = 1
    detective.memes["joy"] = 1
    owner.memes["relief"] = 1
    world.say(case.ending_line)

    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    case: Case = f["case"]
    place: Place = f["place"]
    detective: Entity = f["detective"]
    return [
        f'Write a short detective story for a child set at {place.label} with a little magic and the Spanish clue "{case.clue_spanish}".',
        f"Tell a gentle mystery where {detective.id} uses {case.magic_item} to find {case.missing_phrase}.",
        f"Write a story about a missing {case.missing}, a Spanish word, and a magic tool that helps solve the case.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    case: Case = f["case"]
    detective: Entity = f["detective"]
    owner: Entity = f["owner"]
    parent: Entity = f["parent"]
    place: Place = f["place"]
    missing: Entity = f["missing"]
    return [
        QAItem(
            question=f"What kind of story is this, and where does {detective.id} solve the mystery?",
            answer=f"It is a detective story, and {detective.id} solves it at {place.label}.",
        ),
        QAItem(
            question=f"What was missing in the story?",
            answer=f"The missing item was {case.missing_phrase}.",
        ),
        QAItem(
            question=f"What Spanish word gave the detective a clue?",
            answer=f"The Spanish clue was {case.clue_spanish}, which matched the missing {missing.label}.",
        ),
        QAItem(
            question=f"How did the magic help?",
            answer=f"{case.magic_item} could {case.magic_power}, so it helped {detective.id} notice where the lost thing was hidden.",
        ),
        QAItem(
            question=f"Who got the missing item back at the end?",
            answer=f"{owner.id} got it back, and {parent.label} could see the case was solved.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    f = world.facts
    case: Case = f["case"]
    return [
        QAItem(
            question="What does a detective do?",
            answer="A detective looks carefully for clues and uses facts to solve a mystery.",
        ),
        QAItem(
            question="What is magic in a story like this for?",
            answer="Magic can reveal hidden things, make clues shine, or help the detective notice what ordinary eyes miss.",
        ),
        QAItem(
            question="What is the Spanish word for a book?",
            answer="Libro is the Spanish word for book.",
        ) if case.clue_spanish == "libro" else QAItem(
            question="What is the Spanish word for a key?",
            answer="Llave is the Spanish word for key.",
        ) if case.clue_spanish == "llave" else QAItem(
            question="What is the Spanish word for a toy?",
            answer="Juguete is the Spanish word for toy.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== Story questions ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== World knowledge questions ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# Params / generation
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny magic detective storyworld.")
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--case", choices=sorted(CASE_BOOK))
    ap.add_argument("--name")
    ap.add_argument("--parent", choices=["mother", "father", "woman", "man"], default="mother")
    ap.add_argument("--trait", choices=ADJECTIVES)
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
    place = args.place or rng.choice(list(PLACES))
    case = args.case or rng.choice(list(CASE_BOOK))
    name = args.name or rng.choice(CHARACTER_NAMES)
    trait = args.trait or rng.choice(ADJECTIVES)
    return StoryParams(place=place, case=case, name=name, parent=args.parent, trait=trait, seed=args.seed)


def generate(params: StoryParams) -> StorySample:
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
        print()
        print("--- trace ---")
        for line in sample.world.trace:
            print(line)
    if qa:
        print()
        print(format_qa(sample))


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
place(P) :- place_fact(P).
case(C) :- case_fact(C).
valid(P, C) :- place_fact(P), case_fact(C), magic_fits(P, C).

magic_fits(library, book).
magic_fits(market, key).
magic_fits(garden, toy).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in PLACES:
        lines.append(asp.fact("place_fact", p))
    for c in CASE_BOOK:
        lines.append(asp.fact("case_fact", c))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    clingo_set = sorted(set(asp.atoms(model, "valid")))
    python_set = sorted((p, c) for p in PLACES for c in CASE_BOOK if case_is_plausible(PLACES[p], CASE_BOOK[c]))
    if clingo_set == python_set:
        print(f"OK: ASP matches Python gate ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between ASP and Python gates.")
    print("ASP:", clingo_set)
    print("PY :", python_set)
    return 1


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(place="library", case="book", name="Mia", parent="mother", trait="careful"),
    StoryParams(place="market", case="key", name="Leo", parent="father", trait="curious"),
    StoryParams(place="garden", case="toy", name="Nora", parent="mother", trait="brave"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        vals = asp_valid()
        print(f"{len(vals)} compatible place/case combinations:")
        for p, c in vals:
            print(f"  {p:8} {c}")
        return
    if args.show_asp:
        print(asp_program("#show valid/2."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            params = resolve_params(args, random.Random(base_seed + i))
            i += 1
            try:
                sample = generate(params)
            except StoryError as e:
                print(e)
                return
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
