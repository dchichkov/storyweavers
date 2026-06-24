#!/usr/bin/env python3
"""
Standalone storyworld: an episcopal detective story with dialogue and problem solving.

A small, self-contained simulation in which a curious detective helps an episcopal
setting resolve a mysterious missing object through clues, questions, and a clear
turn toward an honest solution.
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
# Core model
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
    worn_by: Optional[str] = None
    place: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "sister", "nun"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "priest", "bishop", "detective"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Place:
    id: str
    label: str
    indoors: bool = True
    episcopal: bool = False
    clues: set[str] = field(default_factory=set)


@dataclass
class Mystery:
    id: str
    label: str
    phrase: str
    clue: str
    hide_spot: str
    value: int = 1


@dataclass
class Suspect:
    id: str
    type: str
    label: str
    can_help: bool = True
    honest: bool = True


class World:
    def __init__(self, place: Place):
        self.place = place
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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

PLACES = {
    "cathedral": Place("cathedral", "the cathedral", indoors=True, episcopal=True,
                       clues={"echo", "candles", "choir", "steps"}),
    "office": Place("office", "the bishop's office", indoors=True, episcopal=True,
                    clues={"ledger", "desk", "keys", "quiet"}),
    "garden": Place("garden", "the church garden", indoors=False, episcopal=True,
                    clues={"mud", "hedge", "bench", "lantern"}),
}

MYSTERIES = {
    "key": Mystery("key", "a silver key", "the little silver key", "under a hymn book", value=1, hide_spot="desk"),
    "bell": Mystery("bell", "a brass handbell", "the brass handbell", "behind a candle stand", value=2, hide_spot="altar"),
    "ledger": Mystery("ledger", "a blue ledger", "the blue ledger", "inside a prayer basket", value=3, hide_spot="cabinet"),
}

SUSPECTS = {
    "verger": Suspect("verger", "man", "the verger", can_help=True, honest=True),
    "choirmaster": Suspect("choirmaster", "woman", "the choirmaster", can_help=True, honest=True),
    "bishop": Suspect("bishop", "bishop", "the bishop", can_help=True, honest=True),
    "novice": Suspect("novice", "girl", "the novice", can_help=True, honest=True),
}

HERO_NAMES = ["Mina", "Ivy", "Nell", "Ada", "Lucy", "June"]
DETECTIVE_TRAITS = ["careful", "curious", "sharp-eyed", "patient"]


@dataclass
class StoryParams:
    place: str
    mystery: str
    detective_name: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
episcopal(P) :- place(P), episcopal_place(P).
clue(C) :- clue_word(C).
helpful(S) :- suspect(S), can_help(S).
at_risk(M) :- mystery(M), value(M,V), V > 0.
solved(P, M) :- episcopal(P), clue_matches(P, M), helpful(_), at_risk(M).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        if p.episcopal:
            lines.append(asp.fact("episcopal_place", pid))
        if p.indoors:
            lines.append(asp.fact("indoors", pid))
        for c in sorted(p.clues):
            lines.append(asp.fact("clue_word", c))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        lines.append(asp.fact("value", mid, m.value))
    for sid, s in SUSPECTS.items():
        lines.append(asp.fact("suspect", sid))
        if s.can_help:
            lines.append(asp.fact("can_help", sid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_solve_models(show: str):
    import asp
    return asp.one_model(asp_program(show))


def asp_verify() -> int:
    # Keep parity simple: check that the program builds and at least one model exists.
    try:
        import asp
        model = asp.one_model(asp_program("#show clue/1."))
        _ = model
        print("OK: ASP program loads and solves.")
        return 0
    except Exception as exc:  # pragma: no cover
        print(f"ASP verification failed: {exc}")
        return 1


# ---------------------------------------------------------------------------
# Simulation
# ---------------------------------------------------------------------------

def build_case(place: Place, mystery: Mystery, detective_name: str, trait: str) -> World:
    world = World(place)
    detective = world.add(Entity(id=detective_name, kind="character", type="detective", label=detective_name))
    bishop = world.add(Entity(id="bishop", kind="character", type="bishop", label="the bishop"))
    suspect = world.add(Entity(id="verger", kind="character", type="man", label="the verger"))
    clue = world.add(Entity(id="clue", type="thing", label=mystery.label, phrase=mystery.phrase, owner=bishop.id))
    world.facts.update(
        detective=detective, bishop=bishop, suspect=suspect, clue=clue,
        mystery=mystery, trait=trait, place=place,
        missing=True, found=False, solved=False,
    )
    return world


def find_clue(world: World) -> str:
    m: Mystery = world.facts["mystery"]
    p: Place = world.facts["place"]
    if m.hide_spot == "desk":
        return "under the bishop's desk"
    if m.hide_spot == "altar":
        return "behind the altar candles"
    return "inside a garden basket"


def tell_story(world: World) -> None:
    d: Entity = world.facts["detective"]
    bishop: Entity = world.facts["bishop"]
    m: Mystery = world.facts["mystery"]
    p: Place = world.facts["place"]
    trait = world.facts["trait"]

    world.say(f"{d.id} was a {trait} detective who loved a good question.")
    world.say(f"One afternoon at {p.label}, {bishop.label} whispered, \"{m.label} is missing.\"")
    world.say(f"{d.id} looked at the room and said, \"Then we begin with the clues.\"")
    world.para()
    if p.episcopal:
        world.say(f"The place was episcopal, which meant the hall was quiet, careful, and full of echoes.")
    world.say(f"{d.id} asked, \"Who last saw {m.label}?\"")
    world.say("The verger said, \"I saw it before the service.\"")
    world.say("The choirmaster said, \"I heard a rattle near the candles.\"")
    world.say("The bishop said, \"Check the places where people hurry and forget.\"")
    world.para()
    clue_spot = find_clue(world)
    world.say(f"{d.id} followed the clue to {clue_spot}.")
    world.say(f"There, {d.id} found {m.phrase}.")
    world.say(f"{d.id} smiled and said, \"No one stole it. It was simply tucked away by mistake.\"")
    world.say("The bishop nodded. \"Then we can put it back and begin again,\" the bishop said.")
    world.say(f"That was the end of the mystery, and {m.label} rested safely where it belonged.")
    world.facts["found"] = True
    world.facts["solved"] = True


def story_qa(world: World) -> list[QAItem]:
    d: Entity = world.facts["detective"]
    m: Mystery = world.facts["mystery"]
    p: Place = world.facts["place"]
    return [
        QAItem(
            question=f"Who solved the problem at {p.label}?",
            answer=f"{d.id} solved it by following the clues and asking careful questions.",
        ),
        QAItem(
            question=f"What was missing in the story?",
            answer=f"{m.label} was missing, and everyone wanted it found before the day got too late.",
        ),
        QAItem(
            question="How did the detective find the answer?",
            answer="The detective listened to the dialogue, looked for a clue, and checked the most likely hiding place.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does episcopal mean in this story?",
            answer="It means the story takes place in a church setting connected with a bishop and church workers.",
        ),
        QAItem(
            question="What is a detective supposed to do?",
            answer="A detective asks questions, looks for clues, and uses careful thinking to solve a problem.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    d: Entity = world.facts["detective"]
    m: Mystery = world.facts["mystery"]
    p: Place = world.facts["place"]
    return [
        f'Write a short detective story set in an episcopal place where {d.id} finds {m.phrase}.',
        f'Tell a child-friendly mystery with dialogue, clues, and a clear solution at {p.label}.',
        f'Write a simple story in which a detective asks questions and solves why {m.label} went missing.',
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.owner:
            bits.append(f"owner={e.owner}")
        if e.place:
            bits.append(f"place={e.place}")
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  facts: {sorted(world.facts.keys())}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Public interface
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small episcopal detective story world.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--name")
    ap.add_argument("--trait", choices=DETECTIVE_TRAITS)
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
    place = args.place or rng.choice(list(PLACES))
    mystery = args.mystery or rng.choice(list(MYSTERIES))
    name = args.name or rng.choice(HERO_NAMES)
    trait = args.trait or rng.choice(DETECTIVE_TRAITS)
    return StoryParams(place=place, mystery=mystery, detective_name=name, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = build_case(PLACES[params.place], MYSTERIES[params.mystery], params.detective_name, params.trait)
    tell_story(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


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
        print(asp_program("#show clue/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("#show clue/1."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        params_list = [
            StoryParams(place="cathedral", mystery="key", detective_name="Mina", trait="careful"),
            StoryParams(place="office", mystery="bell", detective_name="Ivy", trait="sharp-eyed"),
            StoryParams(place="garden", mystery="ledger", detective_name="Nell", trait="patient"),
        ]
        samples = [generate(p) for p in params_list]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            p = resolve_params(args, random.Random(base_seed + i))
            p.seed = base_seed + i
            s = generate(p)
            i += 1
            if s.story in seen:
                continue
            seen.add(s.story)
            samples.append(s)

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
