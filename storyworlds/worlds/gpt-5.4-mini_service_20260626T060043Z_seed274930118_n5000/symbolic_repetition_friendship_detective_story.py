#!/usr/bin/env python3
"""
storyworlds/worlds/symbolic_repetition_friendship_detective_story.py
===================================================================

A small detective story world built from the seed word "symbolic", with
repetition and friendship as the main narrative instruments.

Premise:
- A small town notices a pattern of repeated symbols appearing at different
  places.
- A child detective and a friend follow the clues.
- The repeated symbol is not a threat; it is a friendly signal that leads them
  to a hidden surprise and a repaired misunderstanding.

The world is intentionally tiny and classical:
- One setting.
- One detective.
- One friend.
- One repeated symbol.
- One short investigation.
- One resolution that changes the emotional state of the characters.

The simulation keeps track of physical meters and emotional memes, and the
story is generated from that state instead of from a frozen template.
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
    location: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother"}
        male = {"boy", "man", "father"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Place:
    name: str
    kind: str = "street"
    clues: list[str] = field(default_factory=list)


@dataclass
class Symbol:
    id: str
    name: str
    visible_name: str
    meaning: str
    places: list[str]
    repeated: bool = True


@dataclass
class StoryParams:
    place: str
    symbol: str
    detective_name: str
    detective_type: str
    friend_name: str
    friend_type: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
        self.paragraphs: list[list[str]] = [[]]

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
PLACES = {
    "library": Place("the library", "building", clues=["stacks", "desk", "window"]),
    "park": Place("the park", "outdoor", clues=["bench", "path", "tree"]),
    "market": Place("the market", "street", clues=["stall", "crate", "lamp"]),
}

SYMBOLS = {
    "star": Symbol("star", "star", "a small star", "someone was trying to guide a friend home", ["window", "bench", "stall"]),
    "key": Symbol("key", "key", "a tiny key", "someone was leaving a friendly hint", ["desk", "crate", "path"]),
    "heart": Symbol("heart", "heart", "a red heart", "someone wanted to say sorry", ["bench", "window", "lamp"]),
}

GIRL_NAMES = ["Mina", "Ivy", "Nora", "Luna", "Tess", "June"]
BOY_NAMES = ["Theo", "Eli", "Finn", "Leo", "Owen", "Miles"]


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------
def story_focus(place: Place, symbol: Symbol) -> str:
    return f"{place.name} kept showing {symbol.visible_name} again and again."


def build_world(params: StoryParams) -> World:
    place = PLACES[params.place]
    symbol = SYMBOLS[params.symbol]
    world = World(place)

    detective = world.add(Entity(
        id=params.detective_name,
        kind="character",
        type=params.detective_type,
        label="detective",
        location=place.name,
        meters={"attention": 1.0},
        memes={"curiosity": 1.0, "confidence": 0.5},
    ))
    friend = world.add(Entity(
        id=params.friend_name,
        kind="character",
        type=params.friend_type,
        label="friend",
        location=place.name,
        meters={"attention": 1.0},
        memes={"friendship": 1.0, "worry": 0.5},
    ))
    clue = world.add(Entity(
        id="clue",
        kind="thing",
        type="symbol",
        label=symbol.name,
        phrase=symbol.visible_name,
        location=place.name,
        meters={"seen": 0.0, "repeated": 0.0},
        memes={"meaning": 0.0},
    ))

    world.facts.update(
        detective=detective,
        friend=friend,
        clue=clue,
        symbol=symbol,
        place=place,
    )

    # Setup
    world.say(
        f"At {place.name}, {params.detective_name} was a little {params.detective_type} detective "
        f"who liked to notice small things."
    )
    world.say(
        f"{params.friend_name} stayed close, because good friends made even quiet places feel braver."
    )
    world.say(
        f"{story_focus(place, symbol)}"
    )

    # Investigation
    world.para()
    clue.meters["seen"] += 1
    clue.meters["repeated"] += 1
    detective.memes["curiosity"] += 1
    friend.memes["worry"] += 0.5
    world.say(
        f"The first {symbol.name} was near the {symbol.places[0]}. {params.detective_name} copied the mark in a small notebook."
    )
    world.say(
        f"Then the same {symbol.name} appeared again near the {symbol.places[1]}, and {params.friend_name} pointed at it with a grin."
    )
    clue.meters["seen"] += 1
    clue.meters["repeated"] += 1
    detective.meters["attention"] += 1
    world.say(
        f"That was no accident. The repeating sign meant the trail was asking to be followed."
    )

    # Turn
    world.para()
    friend.memes["friendship"] += 1
    detective.memes["confidence"] += 1
    world.say(
        f"{params.detective_name} and {params.friend_name} followed the last {symbol.name} to the {symbol.places[2]}."
    )
    world.say(
        f"There they found a note hidden under a small box. It said the repeated symbol was a code for a surprise, not a crime."
    )
    clue.memes["meaning"] += 1
    world.say(
        f"The code led them to a lost parcel that had been set aside for {params.friend_name} all along."
    )

    # Resolution
    world.para()
    detective.memes["joy"] = detective.memes.get("joy", 0.0) + 1
    friend.memes["joy"] = friend.memes.get("joy", 0.0) + 1
    friend.memes["worry"] = 0.0
    world.say(
        f"{params.detective_name} smiled and handed over the parcel. {params.friend_name} laughed and said the repeated signs had been a friendly plan."
    )
    world.say(
        f"The two friends walked home together, and the little {symbol.name} marks no longer felt strange; they felt like a secret wave from one friend to another."
    )

    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    symbol: Symbol = f["symbol"]  # type: ignore[assignment]
    place: Place = f["place"]  # type: ignore[assignment]
    detective: Entity = f["detective"]  # type: ignore[assignment]
    friend: Entity = f["friend"]  # type: ignore[assignment]
    return [
        f'Write a short detective story for young children about a repeated "{symbol.name}" symbol at {place.name}.',
        f"Tell a friendly mystery where {detective.id} and {friend.id} solve the meaning of a repeated sign together.",
        f"Write a simple story about a symbolic clue that looks suspicious at first but turns out to be kind.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    detective: Entity = f["detective"]  # type: ignore[assignment]
    friend: Entity = f["friend"]  # type: ignore[assignment]
    symbol: Symbol = f["symbol"]  # type: ignore[assignment]
    place: Place = f["place"]  # type: ignore[assignment]

    return [
        QAItem(
            question=f"Who was the detective in the story at {place.name}?",
            answer=f"{detective.id} was the little detective who paid close attention to the repeated clues.",
        ),
        QAItem(
            question=f"Who helped {detective.id} follow the repeated {symbol.name} signs?",
            answer=f"{friend.id} helped by noticing the signs too and staying close as a good friend.",
        ),
        QAItem(
            question=f"What did the repeated {symbol.name} really mean?",
            answer=f"It meant a friendly plan was waiting, not a crime. The repeated symbol was a code for a surprise.",
        ),
        QAItem(
            question=f"Why did the detective stop worrying near the end?",
            answer=f"Because the clues led to a harmless surprise and the friends realized the repeating marks were trying to help them.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    symbol: Symbol = f["symbol"]  # type: ignore[assignment]
    return [
        QAItem(
            question="What is a clue in a detective story?",
            answer="A clue is a small piece of information that helps a detective understand what is happening.",
        ),
        QAItem(
            question="Why can repetition be useful?",
            answer="Repetition can be useful because when the same sign appears again and again, it can tell you to pay attention.",
        ),
        QAItem(
            question="What does a friend do in a hard moment?",
            answer="A friend helps, listens, and makes the hard moment feel less scary.",
        ),
        QAItem(
            question=f"What kind of symbol was the repeated sign in this world?",
            answer=f"It was a {symbol.name}, which stood for a message that someone wanted to share.",
        ),
    ]


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
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
place(P) :- setting(P).
symbol(S) :- clue_symbol(S).
repeated_sign(S) :- symbol(S), repeated(S).
meaningful(S) :- repeated_sign(S), friendly_message(S).
solves(D,F,S) :- detective(D), friend(F), repeated_sign(S), together(D,F).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("setting", pid))
        for clue in place.clues:
            lines.append(asp.fact("has_clue_spot", pid, clue))
    for sid, sym in SYMBOLS.items():
        lines.append(asp.fact("clue_symbol", sid))
        if sym.repeated:
            lines.append(asp.fact("repeated", sid))
        for p in sym.places:
            lines.append(asp.fact("symbol_place", sid, p))
        lines.append(asp.fact("friendly_message", sid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_reasonable_symbols() -> set[str]:
    return set(SYMBOLS.keys())


def asp_verify() -> int:
    try:
        import asp
    except Exception as e:
        print(f"ASP unavailable: {e}")
        return 1
    model = asp.one_model(asp_program("#show repeated_sign/1."))
    asp_syms = {a[0] for a in asp.atoms(model, "repeated_sign")}
    py_syms = asp_reasonable_symbols()
    if asp_syms == py_syms:
        print(f"OK: ASP matches Python ({len(py_syms)} symbols).")
        return 0
    print("MISMATCH between ASP and Python.")
    print("only ASP:", sorted(asp_syms - py_syms))
    print("only Python:", sorted(py_syms - asp_syms))
    return 1


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny detective story world with repeated symbolic clues and friendship.")
    ap.add_argument("--place", choices=PLACES.keys())
    ap.add_argument("--symbol", choices=SYMBOLS.keys())
    ap.add_argument("--detective-name")
    ap.add_argument("--detective-type", choices=["girl", "boy"])
    ap.add_argument("--friend-name")
    ap.add_argument("--friend-type", choices=["girl", "boy"])
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
    place = args.place or rng.choice(list(PLACES.keys()))
    symbol = args.symbol or rng.choice(list(SYMBOLS.keys()))
    detective_type = args.detective_type or rng.choice(["girl", "boy"])
    friend_type = args.friend_type or ("boy" if detective_type == "girl" else "girl")
    detective_name = args.detective_name or rng.choice(GIRL_NAMES if detective_type == "girl" else BOY_NAMES)
    friend_name = args.friend_name or rng.choice([n for n in (GIRL_NAMES if friend_type == "girl" else BOY_NAMES) if n != detective_name])

    return StoryParams(
        place=place,
        symbol=symbol,
        detective_name=detective_name,
        detective_type=detective_type,
        friend_name=friend_name,
        friend_type=friend_type,
    )


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


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print()
        print("--- world trace ---")
        w = sample.world
        for e in w.entities.values():
            print(f"{e.id}: kind={e.kind} type={e.type} meters={e.meters} memes={e.memes}")
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show repeated_sign/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show repeated_sign/1."))
        syms = sorted(set(asp.atoms(model, "repeated_sign")))
        print(f"{len(syms)} repeated symbols:")
        for s in syms:
            print(f"  {s[0]}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    if args.all:
        params_list = [
            StoryParams("library", "star", "Mina", "girl", "Theo", "boy"),
            StoryParams("park", "key", "Eli", "boy", "Ivy", "girl"),
            StoryParams("market", "heart", "Nora", "girl", "Finn", "boy"),
        ]
        samples = [generate(p) for p in params_list]
    else:
        samples = []
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
