#!/usr/bin/env python3
"""
Standalone storyworld: a tiny pirate tale about a neato seat and a bit of magic.

A small captain and crew discover a special seat on their ship. The seat is
neato because it is magical: when someone sits in it, it points the ship toward
a bright island, but only if the crew treats it kindly and solves the problem
of a wobbling plank. The story turns on a question of trust, handling, and a
friendly magical fix.
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


THRESHOLD = 1.0


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
    worn_by: Optional[str] = None
    seated_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"captain", "pirate", "boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Ship:
    name: str = "the little ship"
    place: str = "the sea"
    magic: bool = True
    deck_safe: bool = False


class World:
    def __init__(self, ship: Ship) -> None:
        self.ship = ship
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

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
        c = World(copy.deepcopy(self.ship))
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c


@dataclass
class StoryParams:
    name: str
    captain_type: str
    companion: str
    seat: str
    seed: Optional[int] = None


CAPTAIN_NAMES = ["Nia", "Pip", "Rory", "Mina", "Jules", "Tess", "Finn", "Cora"]
COMPANIONS = ["parrot", "mate", "small crab", "old map"]
SEATS = {
    "chair": ("a neato captain chair", "chair", False),
    "stool": ("a neato stool seat", "stool", False),
    "bench": ("a neato bench seat", "bench", True),
}
TRAITS = ["brave", "cheery", "curious", "bold", "kind"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny magical pirate tale storyworld.")
    ap.add_argument("--name", choices=CAPTAIN_NAMES)
    ap.add_argument("--captain-type", choices=["captain", "pirate"])
    ap.add_argument("--companion", choices=COMPANIONS)
    ap.add_argument("--seat", choices=SEATS)
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
    seat = args.seat or rng.choice(list(SEATS))
    name = args.name or rng.choice(CAPTAIN_NAMES)
    captain_type = args.captain_type or rng.choice(["captain", "pirate"])
    companion = args.companion or rng.choice(COMPANIONS)
    return StoryParams(name=name, captain_type=captain_type, companion=companion, seat=seat)


def generate(params: StoryParams) -> StorySample:
    world = World(Ship())
    captain = world.add(Entity(id=params.name, kind="character", type=params.captain_type))
    crew = world.add(Entity(id="crew", kind="character", type="pirate", label="the crew"))
    seat_phrase, seat_type, plural = SEATS[params.seat]
    seat = world.add(Entity(
        id="seat",
        type=seat_type,
        label="seat",
        phrase=seat_phrase,
        owner=captain.id,
        caretaker=crew.id,
        plural=plural,
    ))
    companion = world.add(Entity(id="companion", kind="character", type=params.companion if params.companion in {"pirate"} else "thing", label=params.companion))
    seat.meters["wobble"] = 1.0
    seat.memes["neato"] = 1.0
    seat.memes["magic"] = 1.0

    world.say(f"{captain.id} was a {rng_trait(params.seed)} {params.captain_type} aboard {world.ship.name}.")
    world.say(f"{captain.id} had found {seat.phrase}, and everyone called it neato because it was magic.")
    world.say(f"One calm morning, {captain.id} and {params.companion} went to the deck to see what the seat could do.")
    world.para()
    world.say(f"{captain.id} wanted to sit in the seat right away, but the deck plank beneath it wobbled.")
    world.say(f'"If the seat slips, we could lose its magic shine," said the crew, and {captain.id} frowned.')
    world.say(f"{captain.id} reached out anyway, but then the seat gave a soft blue glow and hummed like a tiny song.")
    world.para()

    if not world.ship.deck_safe:
        world.say(f"{captain.id} noticed the loose plank and asked the crew to hold the seat steady.")
        world.say(f'Together they wedged a stout rope under the plank and said, "Now the neato seat can rest safe."')
        world.ship.deck_safe = True

    captain.memes["joy"] = captain.memes.get("joy", 0) + 1
    seat.seated_by = captain.id
    world.say(f"{captain.id} sat down, and the magic seat pointed the ship toward a bright island.")
    world.say(f"{params.companion.capitalize()} cheered while the crew laughed, and the sea breeze felt warm and kind.")
    world.say(f"In the end, the seat stayed neato, the deck stayed steady, and {captain.id} sailed on with a happy grin.")

    world.facts.update(captain=captain, crew=crew, seat=seat, companion=companion, params=params)
    prompts = [
        f"Write a short pirate tale for a small child about a neato magic seat on a ship.",
        f"Tell a gentle story where {params.name} finds a magical seat and the crew helps make it safe.",
        f"Write a simple pirate story that includes the word 'neato' and ends with a happy sail to an island.",
    ]
    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts,
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def rng_trait(seed: Optional[int]) -> str:
    rng = random.Random(seed)
    return rng.choice(TRAITS)


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    captain = f["captain"]
    seat = f["seat"]
    companion = f["companion"]
    params = f["params"]
    return [
        QAItem(
            question=f"Who found the neato seat on the ship?",
            answer=f"{captain.id} found the neato seat, and it was magical.",
        ),
        QAItem(
            question=f"What made the seat hard to use at first?",
            answer=f"The deck plank under the seat wobbled, so the crew had to make it steady first.",
        ),
        QAItem(
            question=f"What happened after {captain.id} sat in the seat?",
            answer=f"The seat glowed and pointed the ship toward a bright island, and {params.companion} cheered.",
        ),
        QAItem(
            question=f"How did the crew help with the seat?",
            answer="They held the seat steady and wedged a stout rope under the plank so it would not slip.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does magic mean in a pirate tale?",
            answer="Magic means something special and surprising can happen, like a seat glowing or pointing the way.",
        ),
        QAItem(
            question="What is a seat for?",
            answer="A seat is something you sit on so you can rest, watch, or travel more comfortably.",
        ),
        QAItem(
            question="Why do pirates like a steady deck?",
            answer="Pirates like a steady deck because it is safer to walk, stand, and sit on a ship that does not wobble too much.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.phrase:
            bits.append(f"phrase={e.phrase}")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.seated_by:
            bits.append(f"seated_by={e.seated_by}")
        lines.append(f"  {e.id} ({e.type}) {' '.join(bits)}")
    lines.append(f"  ship_safe={world.ship.deck_safe}")
    return "\n".join(lines)


ASP_RULES = r"""
seat(S) :- seat_kind(S).
neato(S) :- magic(S).
needs_fix(S) :- wobble(S).
safe(S) :- seat(S), not needs_fix(S).
safe(S) :- seat(S), needs_fix(S), rope_fix(S).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for sid, (phrase, seat_type, plural) in SEATS.items():
        lines.append(asp.fact("seat_kind", sid))
        lines.append(asp.fact("magic", sid))
        lines.append(asp.fact("wobble", sid))
        if plural:
            lines.append(asp.fact("plural_seat", sid))
    lines.append(asp.fact("rope_fix", "seat"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show safe/1."))
    asp_safe = {t[0] for t in asp.atoms(model, "safe")}
    py_safe = {"seat"}
    if asp_safe == py_safe:
        print("OK: ASP and Python gate agree.")
        return 0
    print("MISMATCH:")
    print("ASP:", sorted(asp_safe))
    print("PY :", sorted(py_safe))
    return 1


def generate_world_params(seed: int, args: argparse.Namespace) -> StoryParams:
    rng = random.Random(seed)
    return resolve_params(args, rng)


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
    StoryParams(name="Pip", captain_type="captain", companion="parrot", seat="chair"),
    StoryParams(name="Mina", captain_type="pirate", companion="small crab", seat="bench"),
    StoryParams(name="Rory", captain_type="captain", companion="old map", seat="stool"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.verify:
        sys.exit(asp_verify())
    if args.show_asp:
        print(asp_program("#show safe/1."))
        return
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        base = args.seed if args.seed is not None else random.randrange(2**31)
        samples = []
        seen = set()
        i = 0
        while len(samples) < args.n and i < args.n * 50:
            p = generate_world_params(base + i, args)
            p.seed = base + i
            s = generate(p)
            if s.story not in seen:
                samples.append(s)
                seen.add(s.story)
            i += 1
    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
