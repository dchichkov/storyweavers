#!/usr/bin/env python3
"""
A tiny pirate-tale story world: a crew on an especial train must solve a mystery
about a missing plank before the ship can sail.
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

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"captain", "pirate", "boy", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"girl", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    id: str
    label: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Mystery:
    id: str
    clue: str
    missing: str
    reveal: str
    solution: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Gear:
    id: str
    label: str
    prep: str
    tail: str


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
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

PLACES = {
    "harbor": Place("harbor", "the harbor", {"sail", "search"}),
    "dock": Place("dock", "the dock", {"search"}),
    "train": Place("train", "the especial train", {"ride", "search"}),
}

MYSTERIES = {
    "missing_plank": Mystery(
        id="missing_plank",
        clue="a gap by the ship rail",
        missing="the plank",
        reveal="the plank was moved for repairs",
        solution="The carpenter had taken it to mend the gangway.",
        tags={"plank", "train", "pirate"},
    ),
    "whistle": Mystery(
        id="whistle",
        clue="a lonely whistle under the moon",
        missing="the train whistle",
        reveal="the whistle was tucked in a sack",
        solution="A tiny deckhand had hidden it to make a game of clues.",
        tags={"train"},
    ),
}

GEAR = {
    "lantern": Gear("lantern", "a brass lantern", "lift the lantern high", "lit the way"),
    "spyglass": Gear("spyglass", "a spyglass", "peek through the spyglass", "helped them search"),
    "rope": Gear("rope", "a coil of rope", "tie on a rope and climb carefully", "kept them safe"),
}

PIRATE_NAMES = ["Nell", "Jory", "Mina", "Beck", "Tom", "Liza"]
CREW_TITLES = ["pirate", "captain", "mate", "deckhand"]


@dataclass
class StoryParams:
    place: str
    mystery: str
    hero: str
    title: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Narrative helpers
# ---------------------------------------------------------------------------

def _hero_label(ent: Entity) -> str:
    return ent.label or ent.id


def _do_search(world: World, hero: Entity, mystery: Mystery) -> None:
    hero.memes["curiosity"] = hero.memes.get("curiosity", 0.0) + 1
    hero.meters["search"] = hero.meters.get("search", 0.0) + 1
    if mystery.id == "missing_plank":
        hero.meters["mystery"] = hero.meters.get("mystery", 0.0) + 1


def _reveal_solution(world: World, mystery: Mystery) -> None:
    world.facts["solved"] = True
    world.facts["solution"] = mystery.solution


def tell(place: Place, mystery: Mystery, hero_name: str, title: str) -> World:
    world = World(place)
    hero = world.add(Entity(id=hero_name, kind="character", type=title, label=hero_name))
    crew = world.add(Entity(id="crew", kind="character", type="pirate", label="the crew", plural=True))
    plank = world.add(Entity(id="plank", type="plank", label="the plank", phrase="an especial plank"))
    train = world.add(Entity(id="train", type="train", label="the especial train", phrase="an especial train"))
    world.facts.update(hero=hero, crew=crew, plank=plank, train=train, mystery=mystery, place=place)

    world.say(
        f"On the especial train, {hero_name} was a {title} who liked to keep one eye on the rails "
        f"and one eye on the sea."
    )
    world.say(
        f"The crew had come to {place.label}, where {mystery.clue} made everyone whisper about {mystery.missing}."
    )

    world.para()
    _do_search(world, hero, mystery)
    world.say(
        f"{hero_name} listened to the clack of the train and looked for signs of the missing thing."
    )
    world.say(
        f"At last, {hero_name} found {mystery.reveal}, but that did not yet answer why it was gone."
    )

    world.para()
    gear = GEAR["spyglass"] if mystery.id == "missing_plank" else GEAR["lantern"]
    world.say(f"Then {hero_name} chose {gear.label}; {gear.prep}, and the shadows grew smaller.")
    if mystery.id == "missing_plank":
        world.say(
            f"{hero_name} spotted fresh sawdust near the rail, and the trail led to the carpenter's cart."
        )
    else:
        world.say(
            f"{hero_name} spotted a tiny sack beside a crate, and the clue trail led straight to a laughing deckhand."
        )
    _reveal_solution(world, mystery)

    world.para()
    world.say(
        f"The mystery was solved: {world.facts['solution']} {gear.tail}."
    )
    world.say(
        f"In the end, the crew smiled, the especial train rolled on, and {mystery.missing} was back where it belonged."
    )
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]  # type: ignore[assignment]
    mystery: Mystery = f["mystery"]  # type: ignore[assignment]
    return [
        'Write a pirate tale for a young child about an especial train, a missing plank, and a mystery to solve.',
        f"Tell a short story where {hero.label} on the especial train solves a mystery about {mystery.missing}.",
        f"Write a gentle pirate story with a clue, a search, and a happy ending near {f['place'].label}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]  # type: ignore[assignment]
    mystery: Mystery = f["mystery"]  # type: ignore[assignment]
    place: Place = f["place"]  # type: ignore[assignment]
    return [
        QAItem(
            question=f"Who solved the mystery in the story?",
            answer=f"{hero.label} solved the mystery on the especial train at {place.label}.",
        ),
        QAItem(
            question=f"What was missing?",
            answer=f"{mystery.missing} was missing, and that was the mystery everyone wanted to solve.",
        ),
        QAItem(
            question=f"Where did the clue lead?",
            answer=f"The clue led the crew to a solution at {place.label}, and the mystery was finally understood.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a plank?",
            answer="A plank is a long, flat piece of wood that can be used to make part of a floor, a deck, or a bridge.",
        ),
        QAItem(
            question="What is a train?",
            answer="A train is a long vehicle with cars that travel along rails.",
        ),
        QAItem(
            question="What does especial mean?",
            answer="Especial means extra special or especially important.",
        ),
        QAItem(
            question="What is a mystery?",
            answer="A mystery is something puzzling that people try to figure out by finding clues.",
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
    lines.append("== (3) World questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        out.append(f"  {e.id} ({e.type}) {' '.join(bits)}")
    out.append(f"  facts: {sorted(world.facts.keys())}")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
place(harbor).
place(dock).
place(train).

mystery(missing_plank).
mystery(whistle).

hero(pirate).
hero(captain).
hero(mate).
hero(deckhand).

relevant(missing_plank, plank).
relevant(whistle, train).

compatible(Place, Mystery) :- place(Place), mystery(Mystery), not blocked(Place, Mystery).
blocked(Place, Mystery) :- Place = dock, Mystery = whistle.
valid_story(Place, Mystery, Hero) :- compatible(Place, Mystery), hero(Hero).
#show valid_story/3.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for m in MYSTERIES:
        lines.append(asp.fact("mystery", m))
        lines.append(asp.fact("relevant", m, MYSTERIES[m].missing.replace("the ", "")))
    for h in CREW_TITLES:
        lines.append(asp.fact("hero", h))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = {(p, m, h) for p in PLACES for m in MYSTERIES for h in CREW_TITLES}
    py = {x for x in py if not (x[0] == "dock" and x[1] == "whistle")}
    cl = set(asp_valid_stories())
    if cl == py:
        print(f"OK: clingo gate matches Python gate ({len(cl)} stories).")
        return 0
    print("MISMATCH between clingo and Python gate:")
    print("only in clingo:", sorted(cl - py))
    print("only in python:", sorted(py - cl))
    return 1


# ---------------------------------------------------------------------------
# Params / generation
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate mystery story world with an especial train and a missing plank.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--name")
    ap.add_argument("--title", choices=CREW_TITLES)
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
    title = args.title or rng.choice(CREW_TITLES)
    name = args.name or rng.choice(PIRATE_NAMES)
    if place == "dock" and mystery == "whistle":
        raise StoryError("That mystery does not fit the dock in this little world.")
    return StoryParams(place=place, mystery=mystery, hero=name, title=title)


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], MYSTERIES[params.mystery], params.hero, params.title)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts(world),
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


CURATED = [
    StoryParams(place="harbor", mystery="missing_plank", hero="Nell", title="captain"),
    StoryParams(place="train", mystery="missing_plank", hero="Jory", title="pirate"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        stories = asp_valid_stories()
        print(f"{len(stories)} compatible (place, mystery, hero) combos:\n")
        for p, m, h in stories:
            print(f"  {p:8} {m:14} {h}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
