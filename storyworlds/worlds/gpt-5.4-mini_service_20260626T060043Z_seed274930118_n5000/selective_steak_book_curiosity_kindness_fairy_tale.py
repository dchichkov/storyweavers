#!/usr/bin/env python3
"""
A standalone Storyweavers world: a fairy-tale of selective appetite, a steak
book, Curiosity, and Kindness.

The seed premise is a small fairy-tale scene:
- a selective young prince keeps refusing every supper except steak;
- a curious helper finds a book of good-feeling recipes;
- kindness turns the fussy dinner into a gentle choice;
- the ending proves the change with a happy meal and a calmer heart.

This script models the tale as world state with physical meters and emotional
memes, plus an inline ASP twin for the reasonableness gate.
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    used_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self):
        for k in ("hunger", "fullness", "tiredness", "delight", "heat"):
            self.meters.setdefault(k, 0.0)
        for k in ("curiosity", "kindness", "stubbornness", "peace", "worry", "joy"):
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "princess", "queen", "woman", "fairy"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "prince", "king", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Castle:
    name: str = "the little castle kitchen"
    place: str = "the kitchen hearth"
    quiet: bool = False
    affords: set[str] = field(default_factory=lambda: {"steak", "book"})


@dataclass
class StoryParams:
    name: str
    gender: str
    title: str
    trait: str
    dish: str
    book: str
    seed: Optional[int] = None


@dataclass
class Dish:
    id: str
    label: str
    phrase: str
    smell: str
    fuss: str
    satisfying: str


@dataclass
class Book:
    id: str
    label: str
    phrase: str
    insight: str
    pages: list[str] = field(default_factory=list)


@dataclass
class World:
    castle: Castle
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

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
        import copy as _copy
        c = World(self.castle)
        c.entities = _copy.deepcopy(self.entities)
        c.facts = _copy.deepcopy(self.facts)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        return c


THRESHOLD = 1.0


DISHES = {
    "steak": Dish(
        id="steak",
        label="steak",
        phrase="a tender steak with golden edges",
        smell="savory",
        fuss="refused every other supper and only wanted steak",
        satisfying="warm and full",
    ),
    "soup": Dish(
        id="soup",
        label="soup",
        phrase="a bowl of carrot soup",
        smell="sweet",
        fuss="frowned at the thin broth",
        satisfying="cozy and calm",
    ),
}

BOOKS = {
    "book": Book(
        id="book",
        label="book",
        phrase="a story book of gentle feasts",
        insight="a kind meal can be chosen instead of demanded",
        pages=[
            "One page showed a steak with a bright herb cloak.",
            "Another page showed a tiny feast that could be shared.",
        ],
    ),
    "recipe_book": Book(
        id="recipe_book",
        label="book",
        phrase="a recipe book tied with ribbon",
        insight="good food can be made with patience and care",
        pages=[
            "A page promised a soft crust and a careful fire.",
            "A page whispered that kindness makes supper easier.",
        ],
    ),
}

NAMES = ["Lily", "Milo", "Ella", "Nora", "Theo", "Finn"]
TRAITS = ["curious", "gentle", "selective", "brave", "kind"]


class Story:
    def __init__(self, params: StoryParams):
        self.params = params
        self.world = World(Castle())
        self.hero = self.world.add(Entity(
            id=params.name, kind="character", type="princess" if params.gender == "girl" else "prince",
            traits=[params.trait, "selective"]
        ))
        self.helper = self.world.add(Entity(
            id="Kindness", kind="character", type="fairy", label="Kindness",
            traits=["kind", "patient"]
        ))
        self.curiosity = self.world.add(Entity(
            id="Curiosity", kind="character", type="fairy", label="Curiosity",
            traits=["curious", "sparkly"]
        ))
        self.dish = self.world.add(Entity(
            id=params.dish, type=params.dish, label=DISHES[params.dish].label,
            phrase=DISHES[params.dish].phrase, caretaker="Kindness"
        ))
        self.book = self.world.add(Entity(
            id=params.book, type="book", label="book", phrase=BOOKS[params.book].phrase,
            caretaker="Curiosity"
        ))
        self.book.pages = BOOKS[params.book].pages[:]  # type: ignore[attr-defined]

    def tell(self) -> World:
        w = self.world
        h = self.hero
        d = self.dish
        b = self.book

        h.memes["curiosity"] += 1
        h.memes["stubbornness"] += 1

        w.say(f"Once in the little castle kitchen, {h.id} was a {self.params.trait} {h.type} who liked supper to be just so.")
        w.say(f"{h.pronoun().capitalize()} was selective at the table and kept asking for {d.label} again and again, because {DISHES[d.type].fuss}.")
        w.say(f"Near the hearth, Curiosity found {BOOKS[b.id].phrase} and opened it with shining eyes.")

        w.para()
        h.memes["worry"] += 1
        w.say(f"The smell of the food drifted through the room, but {h.id} still crossed {h.pronoun('possessive')} arms.")
        w.say(f"Then Kindness sat beside {h.id} and turned the pages, showing how a supper could be chosen with care instead of a loud demand.")
        h.memes["kindness"] += 1
        h.memes["curiosity"] += 1

        if self.params.dish == "steak":
            h.meters["hunger"] += 1
            w.say(f"On one page, the book promised {d.phrase}, and that made {h.id}'s eyes grow round with hope.")
        else:
            w.say(f"On one page, the book suggested a gentler supper than the one {h.id} had been refusing.")

        w.para()
        h.memes["stubbornness"] = max(0.0, h.memes["stubbornness"] - 1.0)
        h.memes["peace"] += 1
        h.memes["joy"] += 1
        h.meters["fullness"] += 1
        w.say(f"{h.id} chose the supper from the book at last, and {Kindness.id} smiled like a warm lamp.")
        w.say(f"At the end, {h.id} ate {d.label} until {DISHES[d.type].satisfying}, and the little castle kitchen felt quiet and bright.")

        w.facts.update(hero=h, helper=self.helper, curiosity=self.curiosity, dish=d, book=b, castle=w.castle)
        return w


def reasonableness_gate(dish: Dish, book: Book) -> bool:
    return dish.id == "steak" and book.id in {"book", "recipe_book"}


ASP_RULES = r"""
% A selective meal story is valid when there is a steak-like dish and a book
% that can guide the child from fuss to choice.
dish(steak).
dish(soup).
book(book).
book(recipe_book).

good_pair(D,B) :- dish(D), book(B), D = steak, (B = book; B = recipe_book).
valid_story(D,B) :- good_pair(D,B).
#show valid_story/2.
"""


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("dish", "steak"),
        asp.fact("dish", "soup"),
        asp.fact("book", "book"),
        asp.fact("book", "recipe_book"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = {("steak", "book"), ("steak", "recipe_book")}
    cl = set(asp_valid())
    if cl == py:
        print(f"OK: clingo gate matches Python gate ({len(cl)} pairs).")
        return 0
    print("MISMATCH:")
    print("only in clingo:", sorted(cl - py))
    print("only in python:", sorted(py - cl))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fairy-tale world of selective supper, Curiosity, and Kindness.")
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--title", choices=["princess", "prince"])
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("--dish", choices=DISHES)
    ap.add_argument("--book", choices=BOOKS)
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
    dish = args.dish or "steak"
    book = args.book or rng.choice(list(BOOKS))
    if not reasonableness_gate(DISHES[dish], BOOKS[book]):
        raise StoryError("This fairy-tale only works when the selective supper is steak and the book can guide it.")
    gender = args.gender or rng.choice(["girl", "boy"])
    title = args.title or ("princess" if gender == "girl" else "prince")
    name = args.name or rng.choice(NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(name=name, gender=gender, title=title, trait=trait, dish=dish, book=book)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    dish = f["dish"]
    return [
        f'Write a short fairy tale about a selective {hero.type} named {hero.id}, Curiosity, Kindness, and a {dish.label}.',
        f'Tell a gentle story where {hero.id} keeps asking for {dish.label} until a book helps choose supper wisely.',
        'Write a child-friendly fairy tale with a book, a hungry child, and a kind ending.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    dish = f["dish"]
    return [
        QAItem(
            question=f"Why was {hero.id} so selective at supper?",
            answer=f"{hero.id} wanted {dish.label} and kept refusing the other food, so supper felt fussy at first.",
        ),
        QAItem(
            question="Who helped turn the supper into a calmer choice?",
            answer="Kindness helped by sitting beside the child, opening the book, and guiding the choice gently.",
        ),
        QAItem(
            question="What did the book show?",
            answer=f"The book showed a kind way to choose supper, and it included {dish.label} as the meal the child finally accepted.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is curiosity?",
            answer="Curiosity is the feeling that makes someone want to look, ask, and learn more.",
        ),
        QAItem(
            question="What is kindness?",
            answer="Kindness means being gentle and helpful to others.",
        ),
        QAItem(
            question="Why can a book help in a story?",
            answer="A book can give ideas, teach something, or help a character make a wiser choice.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== story qa ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== world qa ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        parts = []
        if meters:
            parts.append(f"meters={meters}")
        if memes:
            parts.append(f"memes={memes}")
        lines.append(f"{e.id}: {e.type} {' '.join(parts)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    story = Story(params).tell()
    return StorySample(
        params=params,
        story=story.render(),
        prompts=generation_prompts(story),
        story_qa=story_qa(story),
        world_qa=world_knowledge_qa(story),
        world=story,
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
    StoryParams(name="Lily", gender="girl", title="princess", trait="curious", dish="steak", book="book"),
    StoryParams(name="Theo", gender="boy", title="prince", trait="gentle", dish="steak", book="recipe_book"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/2."))
        vals = sorted(set(asp.atoms(model, "valid_story")))
        print(vals)
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
            except StoryError as e:
                print(e)
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
        header = f"### variant {i + 1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
