#!/usr/bin/env python3
"""
Standalone storyworld: condo whodunit with discount, velvet, Twist, Curiosity,
and Rhyme.

A tiny detective tale lives in a condo building. Someone loses a discount coupon.
A velvet pouch, a twist of ribbon, and a curious note become clues. The story
should feel like a child-sized whodunit: a mystery, a few clues, a turn, and a
clear reveal.
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

@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    location: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character" and self.type in {"girl", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.kind == "character" and self.type in {"boy", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Condo:
    name: str = "the condo"
    floors: int = 8
    shops: tuple[str, ...] = ("lobby kiosk", "mail desk", "corner shelf")
    discount_kind: str = "coupon"


@dataclass
class StoryParams:
    place: str
    clue: str
    twist: str
    name: str
    seed: Optional[int] = None


class World:
    def __init__(self, condo: Condo):
        self.condo = condo
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()

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
        import copy
        w = World(self.condo)
        w.entities = copy.deepcopy(self.entities)
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

PLACES = {
    "lobby": "the condo lobby",
    "hall": "the long hall",
    "mailroom": "the mailroom",
    "balcony": "the balcony",
}

CLUES = {
    "discount": {
        "label": "discount coupon",
        "phrase": "a folded discount coupon",
        "mystery": "the missing coupon had gone to the wrong place",
        "surface": "paper",
    },
    "velvet": {
        "label": "velvet ribbon",
        "phrase": "a soft velvet ribbon",
        "mystery": "the velvet ribbon brushed the clue and hid a smear",
        "surface": "cloth",
    },
    "receipt": {
        "label": "receipt",
        "phrase": "a tiny receipt",
        "mystery": "the receipt showed who had last looked at the shelf",
        "surface": "paper",
    },
}

TWISTS = {
    "Twist": "Twist liked to tug loose ends until they told the truth.",
    "Curiosity": "Curiosity kept asking one more question, even when the answer seemed small.",
    "Rhyme": "Rhyme noticed patterns, because little repeats often matter in a mystery.",
}

NAMES = ["Mia", "Noah", "Lina", "Owen", "Zoe", "Eli", "Nora", "Theo"]


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------

def clue_color(clue: str) -> str:
    return {
        "discount": "yellow",
        "velvet": "deep red",
        "receipt": "white",
    }.get(clue, "plain")


def setup_world(params: StoryParams) -> World:
    world = World(Condo(name="the condo"))
    detective = world.add(Entity(id="Detective", kind="character", type="girl", label=params.name))
    twist = world.add(Entity(id="Twist", kind="character", type="girl", label="Twist"))
    curiosity = world.add(Entity(id="Curiosity", kind="character", type="girl", label="Curiosity"))
    rhyme = world.add(Entity(id="Rhyme", kind="character", type="girl", label="Rhyme"))

    coupon = world.add(Entity(
        id="coupon",
        type="coupon",
        label="discount coupon",
        phrase="a folded discount coupon",
        owner=detective.id,
        location=params.place,
    ))
    clue = world.add(Entity(
        id="clue",
        type=params.clue,
        label=CLUES[params.clue]["label"],
        phrase=CLUES[params.clue]["phrase"],
        location=params.place,
    ))
    twist_note = world.add(Entity(
        id="twist_note",
        type="note",
        label="twisted note",
        phrase="a note with a twist in the corner",
        location=params.place,
    ))

    world.facts.update(
        detective=detective,
        twist=twist,
        curiosity=curiosity,
        rhyme=rhyme,
        coupon=coupon,
        clue=clue,
        twist_note=twist_note,
        params=params,
    )
    return world


def reveal_path(world: World) -> None:
    detective = world.facts["detective"]
    twist = world.facts["twist"]
    curiosity = world.facts["curiosity"]
    rhyme = world.facts["rhyme"]
    coupon = world.facts["coupon"]
    clue = world.facts["clue"]
    twist_note = world.facts["twist_note"]
    params: StoryParams = world.facts["params"]

    # Act 1: setup
    world.say(
        f"{detective.label} lived in {world.condo.name}, where the hall smelled like clean carpet and mail."
    )
    world.say(
        f"One morning, {detective.label} found {coupon.phrase}, but by lunchtime it was gone from {params.place}."
    )
    world.say(
        f"{TWISTS['Twist']}"
    )

    world.para()

    # Act 2: clues
    world.say(
        f"{twist.label}, {curiosity.label}, and {rhyme.label} searched the place with small careful steps."
    )
    world.say(
        f"They found {clue.phrase} near the {params.place}, and the {clue_color(params.clue)} clue looked newly disturbed."
    )
    if params.clue == "discount":
        world.say("The coupon trail pointed toward the mail desk, because a sale card had slipped under a flyer.")
    elif params.clue == "velvet":
        world.say("The soft velvet brushed the shelf and left the kind of mark only cloth can make.")
    else:
        world.say("The tiny receipt sat by itself, as if somebody had checked a bargain and hurried away.")

    world.say(
        f"Then {curiosity.label} noticed {twist_note.phrase}, tucked where a breeze could not have reached it."
    )
    world.say(
        f"{TWISTS['Curiosity']} {TWISTS['Rhyme']}"
    )

    world.para()

    # Act 3: reveal
    if params.clue == "discount":
        culprit = "the mail carrier"
        reason = "had put the coupon beside a stack of flyers by mistake"
        ending = "The coupon had never been stolen at all"
    elif params.clue == "velvet":
        culprit = "the little cat"
        reason = "had dragged the velvet ribbon under the couch"
        ending = "The ribbon had only wandered off with the cat"
    else:
        culprit = "the caretaker"
        reason = "had saved the receipt to match the coupon"
        ending = "The receipt had been kept safe for a careful look"

    world.say(
        f"At last, the note made the answer plain: {culprit} {reason}."
    )
    world.say(
        f"{ending}, and {detective.label}'s missing discount coupon was found tucked behind the right door."
    )
    world.say(
        f"{detective.label} smiled, because the mystery had a gentle ending and the condo felt tidy again."
    )

    world.facts["culprit"] = culprit
    world.facts["ending"] = ending
    coupon.location = "found"
    clue.location = "noted"
    twist_note.location = "solved"


# ---------------------------------------------------------------------------
# ASP twin and reasonableness gate
# ---------------------------------------------------------------------------

ASP_RULES = r"""
place(lobby).
place(hall).
place(mailroom).
place(balcony).

clue(discount).
clue(velvet).
clue(receipt).

points_to(discount, mailroom).
points_to(velvet, hall).
points_to(receipt, lobby).

valid_story(P, C) :- place(P), clue(C), points_to(C, P).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for c in CLUES:
        lines.append(asp.fact("clue", c))
    for c, p in {"discount": "mailroom", "velvet": "hall", "receipt": "lobby"}.items():
        lines.append(asp.fact("points_to", c, p))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple[str, str]]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def python_valid() -> list[tuple[str, str]]:
    return sorted((p, c) for p in PLACES for c in CLUES if {"discount": "mailroom", "velvet": "hall", "receipt": "lobby"}[c] == p)


def asp_verify() -> int:
    a = set(asp_valid())
    b = set(python_valid())
    if a == b:
        print(f"OK: ASP matches Python gate ({len(a)} combos).")
        return 0
    print("Mismatch:")
    print("only ASP:", sorted(a - b))
    print("only Python:", sorted(b - a))
    return 1


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    p: StoryParams = world.facts["params"]
    return [
        f"Write a child-friendly whodunit set in a condo where a discount coupon goes missing.",
        f"Tell a short mystery story with Twist, Curiosity, and Rhyme, using the clue word {p.clue}.",
        f"Write a gentle detective story about {p.name} in the condo, where velvet, a twist, and a clue help solve the mystery.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p: StoryParams = world.facts["params"]
    detective = world.facts["detective"]
    culprit = world.facts["culprit"]
    ending = world.facts["ending"]
    return [
        QAItem(
            question=f"What went missing from {detective.label}'s condo story?",
            answer=f"The missing thing was a discount coupon, and the mystery began when it could not be found.",
        ),
        QAItem(
            question=f"Who helped search for the answer in the condo?",
            answer=f"Twist, Curiosity, and Rhyme helped {detective.label} search and notice the clue.",
        ),
        QAItem(
            question=f"What clue mattered most in the story with {p.clue}?",
            answer=f"The {p.clue} clue helped point the search in the right direction and made the hidden pattern easier to see.",
        ),
        QAItem(
            question="Who turned out to be behind the mystery?",
            answer=f"It was {culprit}, whose small mistake explained the clue and made the ending clear.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"{ending}, so the condo felt calm again and the lost coupon was found safely.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a condo?",
            answer="A condo is a home in a larger building, where people live close together and share common spaces.",
        ),
        QAItem(
            question="What is a discount?",
            answer="A discount is a smaller price than usual, so something costs less.",
        ),
        QAItem(
            question="What is velvet?",
            answer="Velvet is a soft, smooth cloth that feels fancy and gentle to touch.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== Story questions ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== World knowledge questions ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.location:
            bits.append(f"location={e.location}")
        if e.owner:
            bits.append(f"owner={e.owner}")
        if e.carried_by:
            bits.append(f"carried_by={e.carried_by}")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:12} ({e.type}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Story generation
# ---------------------------------------------------------------------------

def build_story(params: StoryParams) -> StorySample:
    world = setup_world(params)
    reveal_path(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(list(PLACES))
    clue = args.clue or rng.choice(list(CLUES))
    twist = args.twist or rng.choice(list(TWISTS))
    name = args.name or rng.choice(NAMES)
    if place not in PLACES:
        raise StoryError("Unknown place.")
    if clue not in CLUES:
        raise StoryError("Unknown clue.")
    if twist not in TWISTS:
        raise StoryError("Unknown feature.")
    return StoryParams(place=place, clue=clue, twist=twist, name=name)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Whodunit storyworld in a condo.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--twist", choices=TWISTS)
    ap.add_argument("--name")
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
    StoryParams(place="mailroom", clue="discount", twist="Twist", name="Mia"),
    StoryParams(place="hall", clue="velvet", twist="Curiosity", name="Noah"),
    StoryParams(place="lobby", clue="receipt", twist="Rhyme", name="Lina"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        raise SystemExit(asp_verify())

    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/2."))
        items = sorted(set(asp.atoms(model, "valid_story")))
        for place, clue in items:
            print(place, clue)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(1 << 30)
    samples: list[StorySample] = []

    if args.all:
        samples = [build_story(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = build_story(params)
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

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.place} / {p.clue} / {p.twist}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
