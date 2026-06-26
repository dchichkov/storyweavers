#!/usr/bin/env python3
"""
A standalone story world for a small mystery domain: a distant friendship,
spoken clues, and a twist ending.

The world follows a child-facing mystery structure:
- a nearby place becomes important because something is missing
- friends talk in dialogue and notice clues
- a mistaken suspicion turns into a twist
- the ending proves the friendship changed or deepened

This script is self-contained and uses only stdlib plus the shared
storyworld result containers. ASP is imported lazily only for ASP modes.
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
class Person:
    id: str
    role: str
    type: str = "person"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    knows: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Clue:
    id: str
    label: str
    location: str
    owner: str = ""
    hidden: bool = True
    meters: dict[str, float] = field(default_factory=dict)


@dataclass
class Place:
    id: str
    label: str
    detail: str
    hush: str


@dataclass
class World:
    place: Place
    people: dict[str, Person] = field(default_factory=dict)
    clues: dict[str, Clue] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[str] = field(default_factory=set)

    def add_person(self, p: Person) -> Person:
        self.people[p.id] = p
        return p

    def add_clue(self, c: Clue) -> Clue:
        self.clues[c.id] = c
        return c

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


# ---------------------------------------------------------------------------
# Parameters and registries
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    missing: str
    friend: str
    hero: str
    seed: Optional[int] = None


PLACES = {
    "library": Place("library", "the library", "rows of quiet books", "The room felt soft and hushed."),
    "garden": Place("garden", "the garden", "small paths and leaves", "The leaves barely moved."),
    "station": Place("station", "the train station", "echoing benches and signs", "The announcements sounded far away."),
    "museum": Place("museum", "the museum", "bright rooms and still exhibits", "Even the footsteps sounded careful."),
}

MISSING = {
    "note": {
        "label": "a folded note",
        "hint": "paper",
        "places": {"library", "museum"},
    },
    "button": {
        "label": "a shiny button",
        "hint": "tiny metal",
        "places": {"station", "museum"},
    },
    "key": {
        "label": "a small key",
        "hint": "metal",
        "places": {"garden", "library"},
    },
    "map": {
        "label": "a torn map corner",
        "hint": "paper",
        "places": {"station", "garden"},
    },
}

HERO_NAMES = ["Mina", "Owen", "Lila", "Noah", "Iris", "Eli", "Sage", "Maya"]
FRIEND_NAMES = ["Jun", "Pia", "Taro", "Nina", "Rafi", "Lea", "Zed", "Luca"]
TRAITS = ["quiet", "careful", "curious", "gentle", "brave"]


# ---------------------------------------------------------------------------
# Utility
# ---------------------------------------------------------------------------

def valid_combos() -> list[tuple[str, str]]:
    out = []
    for place_id, place in PLACES.items():
        for missing_id, miss in MISSING.items():
            if place_id in miss["places"]:
                out.append((place_id, missing_id))
    return out


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small mystery about a distant friendship and a twist.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--missing", choices=MISSING)
    ap.add_argument("--hero")
    ap.add_argument("--friend")
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
    combos = valid_combos()
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.missing:
        combos = [c for c in combos if c[1] == args.missing]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, missing = rng.choice(sorted(combos))
    hero = args.hero or rng.choice(HERO_NAMES)
    friend = args.friend or rng.choice(FRIEND_NAMES)
    if friend == hero:
        friend = rng.choice([n for n in FRIEND_NAMES if n != hero])
    return StoryParams(place=place, missing=missing, friend=friend, hero=hero)


# ---------------------------------------------------------------------------
# Story simulation
# ---------------------------------------------------------------------------

def build_world(params: StoryParams) -> World:
    place = PLACES[params.place]
    missing = MISSING[params.missing]
    world = World(place=place)
    hero = world.add_person(Person(
        id=params.hero,
        role="hero",
        traits=["curious", "careful"],
        meters={"distance": 1.0},
        memes={"worry": 0.0, "hope": 0.0, "friendship": 1.0},
    ))
    friend = world.add_person(Person(
        id=params.friend,
        role="friend",
        traits=["distant", "kind"],
        meters={"distance": 6.0},
        memes={"worry": 0.0, "friendship": 1.0},
    ))
    clue = world.add_clue(Clue(
        id=missing["label"],
        label=missing["label"],
        location=place.id,
        owner=friend.id,
        hidden=True,
        meters={"notice": 0.0},
    ))
    world.facts.update(hero=hero, friend=friend, clue=clue, missing=missing, place=place)
    return world


def tell(world: World) -> None:
    hero: Person = world.facts["hero"]
    friend: Person = world.facts["friend"]
    clue: Clue = world.facts["clue"]
    missing = world.facts["missing"]
    place = world.facts["place"]

    world.say(f"{hero.id} had come to {place.label}, and the hush there made every sound feel important.")
    world.say(f"{hero.id} was looking for {missing['label']}, because {friend.id} had sent a distant message that sounded worried.")
    world.say(f'"Did you lose {missing["label"]}?" {hero.id} asked.')
    world.say(f'"No," {friend.id} said. "But someone moved it, and I do not know who."')
    world.para()

    hero.memes["worry"] += 1.0
    friend.memes["worry"] += 1.0
    world.say(f"{place.detail.capitalize()} held still around them. {place.hush}")
    world.say(f"{hero.id} noticed a tiny clue near a bench: {clue.label}. It looked important, so {hero.id} picked it up carefully.")
    world.say(f'"That means someone was here," {hero.id} whispered.')
    world.say(f'"Yes," {friend.id} replied. "And I thought it might be you at first."')
    world.para()

    world.say(f"{hero.id} frowned. " + f'"Why would you think that?"')
    world.say(f'"Because we were far apart," {friend.id} said. "And when I got the note, I could not see the room clearly."')
    world.say(f"{hero.id} turned the clue over and found a twist: it was not missing at all. It was a spare piece left where {friend.id} had been sorting things for a surprise.")
    world.say(f'"I was making a trail for you," {friend.id} said. "I wanted you to find me in the quiet place."')
    world.para()

    hero.memes["worry"] = 0.0
    friend.memes["worry"] = 0.0
    hero.memes["friendship"] += 1.0
    friend.memes["friendship"] += 1.0
    clue.hidden = False

    world.say(f"{hero.id} laughed, and the distance between them seemed to shrink right away.")
    world.say(f'"I thought it was a mystery," {hero.id} said, "but it was really your way of saying hello."')
    world.say(f'"Exactly," {friend.id} said. "Now we can walk together."')
    world.say(f"By the end, the clue was no longer hidden, the worry was gone, and the two friends left {place.label} side by side.")


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short mystery for a child about distant friends, a clue, and a twist ending that includes the word "{f["place"].id}".',
        f"Tell a gentle dialogue-heavy story where {f['hero'].id} thinks something is missing, but {f['friend'].id} reveals a surprise instead.",
        f'Write a small story with friendship, a mistaken clue, and a twist at {f["place"].label}.',
    ]


def story_qa(world: World) -> list[QAItem]:
    hero: Person = world.facts["hero"]
    friend: Person = world.facts["friend"]
    clue: Clue = world.facts["clue"]
    missing = world.facts["missing"]
    place: Place = world.facts["place"]
    return [
        QAItem(
            question=f"What was {hero.id} looking for at {place.label}?",
            answer=f"{hero.id} was looking for {missing['label']}, because that was the thing the mystery seemed to be about.",
        ),
        QAItem(
            question=f"Why did {friend.id} seem distant at first?",
            answer=f"{friend.id} seemed distant because the message was worried and the two friends were not standing close together in {place.label}.",
        ),
        QAItem(
            question=f"What clue did {hero.id} notice?",
            answer=f"{hero.id} noticed {clue.label}, which helped show that someone had been there and that the mystery needed another look.",
        ),
        QAItem(
            question="What was the twist in the story?",
            answer=f"The twist was that the clue was not a theft at all. {friend.id} had been setting up a surprise and accidentally made it look mysterious.",
        ),
        QAItem(
            question=f"How did the story end for {hero.id} and {friend.id}?",
            answer=f"They ended together, laughing, with the worry gone and their friendship feeling closer than before.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    place: Place = world.facts["place"]
    return [
        QAItem(
            question="What is a clue in a mystery?",
            answer="A clue is a small piece of information that helps someone figure out what happened.",
        ),
        QAItem(
            question="What does distant mean?",
            answer="Distant means far away, or not very close together.",
        ),
        QAItem(
            question="Why do friends talk to each other?",
            answer="Friends talk to each other to share feelings, ask questions, and understand what is going on.",
        ),
        QAItem(
            question=f"What kind of place is {place.label} in this story?",
            answer=f"{place.label.capitalize()} is a quiet place with {place.detail}, which makes it feel like a good setting for noticing small clues.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for p in sample.prompts:
        out.append(p)
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


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
place(Place) :- setting(Place).
missing(M) :- clue(M,_).
valid(Place, Missing) :- setting(Place), clue(Missing,Place), compatible(Place,Missing).
"""

def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for pid in PLACES:
        lines.append(asp.fact("setting", pid))
    for mid, info in MISSING.items():
        lines.append(asp.fact("clue", mid, sorted(info["places"])[0]))
        for p in info["places"]:
            lines.append(asp.fact("compatible", p, mid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py == asp_set:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - asp_set:
        print("  only in python:", sorted(py - asp_set))
    if asp_set - py:
        print("  only in clingo:", sorted(asp_set - py))
    return 1


# ---------------------------------------------------------------------------
# Sample generation / emit
# ---------------------------------------------------------------------------

def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    tell(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for p in world.people.values():
        lines.append(f"  {p.id:10} role={p.role:6} meters={p.meters} memes={p.memes} knows={sorted(p.knows)}")
    for c in world.clues.values():
        lines.append(f"  clue={c.label:20} hidden={c.hidden} owner={c.owner} location={c.location}")
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


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

CURATED = [
    StoryParams(place="library", missing="note", hero="Mina", friend="Jun"),
    StoryParams(place="garden", missing="key", hero="Owen", friend="Pia"),
    StoryParams(place="station", missing="map", hero="Iris", friend="Rafi"),
    StoryParams(place="museum", missing="button", hero="Lila", friend="Nina"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for place, missing in combos:
            print(f"  {place:10} {missing}")
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
            rng = random.Random(seed)
            try:
                params = resolve_params(args, rng)
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero} / {p.friend}: {p.missing} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
