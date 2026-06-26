#!/usr/bin/env python3
"""
A small detective-story world about a surprise, a sophisticated brother, and a
child who decides to befriend him.

Premise:
- A child notices a distant, sophisticated brother.
- A small surprise threatens to spoil a carefully planned reveal.
- The child investigates the clue trail, learns the brother's habits, and
  chooses a kind approach.
- The surprise becomes the reason they finally connect.
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
    metros: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "brother"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Location:
    id: str
    label: str
    detail: str
    clue_kind: str


@dataclass
class Clue:
    id: str
    label: str
    text: str
    location: str
    reveals: str
    valid: bool = True


@dataclass
class Surprise:
    id: str
    label: str
    phrase: str
    hidden: bool = True
    revealed: bool = False


@dataclass
class StoryParams:
    place: str
    child_name: str
    child_type: str
    brother_name: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Location) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.clues: dict[str, Clue] = {}
        self.surprise: Optional[Surprise] = None
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.trace: list[str] = []

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

        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.clues = copy.deepcopy(self.clues)
        clone.surprise = copy.deepcopy(self.surprise)
        clone.paragraphs = [[]]
        return clone


LOCATIONS = {
    "library": Location("library", "the library", "rows of whispering books and brass lamps", "paper"),
    "station": Location("station", "the train station", "echoes, benches, and shiny rails", "ticket"),
    "garden": Location("garden", "the garden", "trim hedges, stone paths, and bright flowers", "petal"),
}

SURPRISES = {
    "birthday_note": Surprise("birthday_note", "a birthday note", "a folded note tied with blue ribbon"),
    "hidden_map": Surprise("hidden_map", "a hidden map", "a map tucked inside a book cover"),
    "secret_cookie": Surprise("secret_cookie", "a secret cookie", "a cookie wrapped in a napkin"),
}

CLUES = {
    "bookmark": Clue("bookmark", "a torn bookmark", "a torn bookmark with a neat corner fold", "library", "book"),
    "ticket_stub": Clue("ticket_stub", "a ticket stub", "a ticket stub with careful handwriting", "station", "ticket"),
    "petal_path": Clue("petal_path", "a petal trail", "a line of petals leading behind the hedge", "garden", "petal"),
}

BROTHER_TRAITS = ["sophisticated", "calm", "tidy", "careful", "serious"]
CHILD_TRAITS = ["curious", "brave", "gentle", "quiet", "smart"]


ASP_RULES = r"""
location(L) :- place(L).
clue(C) :- clue_kind(C,_).
surprise(S) :- surprise_kind(S).
relevant(C) :- clue_kind(C,K), reveals(S,K), surprise_kind(S).
valid_story(P, C, S) :- place(P), relevant(C), surprise_kind(S), fits(P,C,S).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for lid in LOCATIONS:
        lines.append(asp.fact("place", lid))
    for sid in SURPRISES:
        lines.append(asp.fact("surprise_kind", sid))
    for cid, clue in CLUES.items():
        lines.append(asp.fact("clue_kind", cid, clue.reveals))
        lines.append(asp.fact("fits", clue.location, cid, clue.location))
        lines.append(asp.fact("clue", cid))
    for sid, s in SURPRISES.items():
        lines.append(asp.fact("reveals", sid, "book"))
        lines.append(asp.fact("reveals", sid, "ticket"))
        lines.append(asp.fact("reveals", sid, "petal"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid())
    if py == cl:
        print(f"OK: clingo gate matches Python ({len(py)} combos).")
        return 0
    print("MISMATCH:")
    print("python only:", sorted(py - cl))
    print("clingo only:", sorted(cl - py))
    return 1


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in LOCATIONS:
        for clue in CLUES:
            for surprise in SURPRISES:
                if CLUES[clue].location == place:
                    combos.append((place, clue, surprise))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Detective story world: clues, surprise, and a brother.")
    ap.add_argument("--place", choices=LOCATIONS)
    ap.add_argument("--child-name")
    ap.add_argument("--child-type", choices=["girl", "boy"], default="girl")
    ap.add_argument("--brother-name")
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
    place = args.place or rng.choice(list(LOCATIONS))
    child_name = args.child_name or rng.choice(["Mia", "Nina", "Leah", "Owen", "Theo", "Eli"])
    child_type = args.child_type or "girl"
    brother_name = args.brother_name or rng.choice(["Max", "Noah", "Leo", "Ben", "Finn", "Iris"])
    if place not in LOCATIONS:
        raise StoryError("Unknown place.")
    return StoryParams(place=place, child_name=child_name, child_type=child_type, brother_name=brother_name)


def setup_world(params: StoryParams) -> World:
    world = World(LOCATIONS[params.place])
    child = world.add(Entity(id=params.child_name, kind="character", type=params.child_type, traits=["curious"]))
    brother = world.add(Entity(id=params.brother_name, kind="character", type="brother", traits=["sophisticated"]))
    clue = world.add(Entity(id="clue", kind="thing", type="clue", label="clue", phrase="a clue"))
    surprise = SURPRISES["hidden_map"] if params.place == "library" else SURPRISES["birthday_note"] if params.place == "garden" else SURPRISES["secret_cookie"]
    world.surprise = surprise
    world.clues = {clue.id: CLUES["bookmark"] if params.place == "library" else CLUES["petal_path"] if params.place == "garden" else CLUES["ticket_stub"]}
    world.facts.update(child=child, brother=brother, clue=world.clues["clue"], surprise=surprise, place=world.place, params=params)
    return world


def detect(world: World) -> None:
    child: Entity = world.facts["child"]
    brother: Entity = world.facts["brother"]
    clue: Clue = world.facts["clue"]
    surprise: Surprise = world.facts["surprise"]
    place = world.place

    world.say(f"{child.id} was a {child.traits[0]} little {child.type} who loved noticing tiny details.")
    world.say(f"At {place.label}, {child.id} saw {brother.id}, a {brother.traits[0]} brother with neat shoes and a quiet voice.")
    world.say(f"Something felt strange: {clue.text} sat where it did not belong, like it was waiting to be found.")
    world.para()
    world.say(f"{child.id} followed the clue through {place.detail}.")
    world.say(f"The trail pointed toward a surprise: {surprise.phrase}.")
    world.say(f"{child.id} realized {brother.id} had been planning it all along, and the careful brother had not meant to be distant.")
    world.para()
    world.say(f"{child.id} smiled, tucked the clue away, and chose to befriend {brother.id} instead of solving the mystery alone.")
    world.say(f"Together they opened {surprise.phrase}, and the surprise became the start of a new friendship.")
    child.memes["warmth"] = 1
    brother.memes["relief"] = 1
    surprise.revealed = True
    world.facts["resolved"] = True


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    return [
        f"Write a short detective story for a child named {p.child_name} about a sophisticated brother and a surprise.",
        f"Tell a gentle mystery where {p.child_name} follows a clue at {world.place.label} and learns to befriend {p.brother_name}.",
        f"Write a simple detective-style story that includes the words befriend, sophisticated, and brother.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    child: Entity = world.facts["child"]
    brother: Entity = world.facts["brother"]
    clue: Clue = world.facts["clue"]
    surprise: Surprise = world.facts["surprise"]
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about {p.child_name}, a curious little {p.child_type}, and {brother.id}, a sophisticated brother."
        ),
        QAItem(
            question=f"What clue did {p.child_name} notice at {world.place.label}?",
            answer=f"{p.child_name} noticed {clue.text}, which helped point toward the surprise."
        ),
        QAItem(
            question=f"What did {p.child_name} do after solving the mystery?",
            answer=f"{p.child_name} chose to befriend {brother.id}, and together they opened {surprise.phrase}."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does a clue do in a detective story?",
            answer="A clue is a small piece of information that helps someone figure out a mystery."
        ),
        QAItem(
            question="What is a surprise?",
            answer="A surprise is something unexpected that is discovered or given without warning."
        ),
        QAItem(
            question="What does sophisticated mean?",
            answer="Sophisticated means polished, careful, and stylish in a grown-up way."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== (3) World knowledge ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(f"  {e.id:12} {e.kind:8} {e.type:12} memes={dict(e.memes)}")
    lines.append(f"  place: {world.place.label}")
    lines.append(f"  surprise: {world.surprise.label if world.surprise else None}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="library", child_name="Mia", child_type="girl", brother_name="Noah"),
    StoryParams(place="station", child_name="Owen", child_type="boy", brother_name="Leo"),
    StoryParams(place="garden", child_name="Leah", child_type="girl", brother_name="Finn"),
]


def generate(params: StoryParams) -> StorySample:
    world = setup_world(params)
    detect(world)
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
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid())} valid detective-story combos:")
        for row in asp_valid():
            print(" ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
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
        if len(samples) > 1:
            print(f"### variant {i + 1}")
        emit(sample, trace=args.trace, qa=args.qa)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
