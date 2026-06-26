#!/usr/bin/env python3
"""
spaz_mystery_to_solve_lesson_learned_flashback.py

A small animal-story world about a mystery, a flashback clue, and a lesson
learned at the end.
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
    kind: str = "thing"  # character | thing
    species: str = "animal"
    name: str = ""
    role: str = ""
    place: str = ""
    owner: Optional[str] = None
    hidden: bool = False
    carried_by: Optional[str] = None
    discovered: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def display(self) -> str:
        return self.name or self.id


@dataclass
class Place:
    id: str
    label: str
    kind: str
    clue: str


@dataclass
class StoryParams:
    place: str
    seeker: str
    friend: str
    mystery: str
    lesson: str
    seed: Optional[int] = None


@dataclass
class World:
    place: Place
    seeker: Entity
    friend: Entity
    missing: Entity
    clue_spot: str
    flashback_done: bool = False
    solved: bool = False
    lesson_learned: bool = False
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    entities: dict[str, Entity] = field(default_factory=dict)

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

PLACES = {
    "barn": Place("barn", "the barn", "farm", "a loose hay stack"),
    "pond": Place("pond", "the pond", "water", "a muddy bank"),
    "orchard": Place("orchard", "the orchard", "trees", "a crooked apple crate"),
    "garden": Place("garden", "the garden", "plants", "a small fence post"),
}

ANIMALS = [
    ("milo", "mouse"),
    ("pippa", "pigeon"),
    ("rusty", "rabbit"),
    ("nora", "newt"),
    ("toby", "turtle"),
    ("spaz", "fox"),
    ("luna", "otter"),
    ("bea", "bear cub"),
]

MYSTERIES = {
    "bell": ("tiny bell", "jingled"),
    "hat": ("blue hat", "flew off"),
    "carrot": ("favorite carrot", "went missing"),
    "bookmark": ("paper bookmark", "got lost"),
}

LESSONS = {
    "ask": "ask for help instead of guessing",
    "share": "share the truth even when it feels awkward",
    "slow": "slow down and look carefully before worrying",
}

CURATED = [
    ("barn", "spaz", "rusty", "bell", "ask"),
    ("pond", "luna", "spaz", "hat", "slow"),
    ("orchard", "bea", "milo", "carrot", "share"),
    ("garden", "pippa", "toby", "bookmark", "ask"),
]


# ---------------------------------------------------------------------------
# Story helpers
# ---------------------------------------------------------------------------

def build_world(params: StoryParams) -> World:
    place = PLACES[params.place]
    seeker_name, seeker_species = next((n, s) for n, s in ANIMALS if n == params.seeker)
    friend_name, friend_species = next((n, s) for n, s in ANIMALS if n == params.friend)
    mystery_label, mystery_verb = MYSTERIES[params.mystery]

    seeker = Entity(id="seeker", kind="character", species=seeker_species, name=seeker_name)
    friend = Entity(id="friend", kind="character", species=friend_species, name=friend_name)
    missing = Entity(
        id="missing",
        kind="thing",
        species="thing",
        name=mystery_label,
        owner=seeker.id,
        hidden=True,
        place=place.label,
    )

    clue_spot = place.clue
    world = World(place=place, seeker=seeker, friend=friend, missing=missing, clue_spot=clue_spot)
    world.add(seeker)
    world.add(friend)
    world.add(missing)
    world.facts.update(
        place=place,
        mystery_label=mystery_label,
        mystery_verb=mystery_verb,
        lesson=params.lesson,
    )
    return world


def intro(world: World) -> None:
    s, f = world.seeker, world.friend
    p = world.place
    world.say(
        f"At {p.label}, a little {s.species} named {s.display} was having a busy day with "
        f"{f.display}, a curious {f.species} who loved to look for clues."
    )
    world.say(
        f"{s.display} carried a special little {world.missing.name} everywhere, because it "
        f"made the morning feel safer and brighter."
    )


def mystery_turn(world: World) -> None:
    s, f, m = world.seeker, world.friend, world.missing
    world.para()
    world.say(
        f"Then one moment, the {m.name} was there, and the next moment it was gone."
    )
    s.memes["worry"] = 1
    s.memes["fear"] = 1
    world.say(
        f"{s.display} looked under leaves and behind stones, but {m.display} was nowhere to be seen."
    )
    world.say(
        f"{s.display} asked, \"Where could it be?\" and {f.display} tried to help."
    )


def flashback(world: World) -> None:
    s, m = world.seeker, world.missing
    world.para()
    world.flashback_done = True
    world.say(
        f"Then {s.display} remembered something from earlier."
    )
    world.say(
        f"In the flashback, {s.display} had rushed past {world.clue_spot} after hearing a loud rustle."
    )
    world.say(
        f"The little {m.name} had slipped away during the hurry, right when {s.display} stopped paying attention."
    )


def solve_mystery(world: World) -> None:
    s, f, m = world.seeker, world.friend, world.missing
    world.para()
    world.say(
        f"{f.display} followed the memory back to {world.clue_spot} and found a tiny glint tucked in the corner."
    )
    m.hidden = False
    m.discovered = True
    m.carried_by = s.id
    world.solved = True
    s.memes["relief"] = 1
    f.memes["pride"] = 1
    world.say(
        f"It was the {m.name}."
    )
    world.say(
        f"{s.display} smiled and said thank you, because the mystery was solved without blaming anyone."
    )


def lesson_end(world: World, lesson_key: str) -> None:
    world.para()
    world.lesson_learned = True
    lesson = LESSONS[lesson_key]
    if lesson_key == "ask":
        world.say(
            f"{safename(world.seeker)} learned to {lesson}, and that made the answer easier to find."
        )
    elif lesson_key == "share":
        world.say(
            f"{safename(world.seeker)} learned to {lesson}, and honesty helped the friends feel close again."
        )
    else:
        world.say(
            f"{safename(world.seeker)} learned to {lesson}, and the answer was waiting in plain sight."
        )
    world.say(
        f"By evening, {world.seeker.display} was holding {world.missing.name} again, and the barn-quiet world felt friendly and safe."
    )


def safename(e: Entity) -> str:
    return e.display


def tell(params: StoryParams) -> World:
    world = build_world(params)
    intro(world)
    mystery_turn(world)
    flashback(world)
    solve_mystery(world)
    lesson_end(world, params.lesson)
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        "Write a short animal story about a mystery, a flashback, and a lesson learned.",
        f"Tell a gentle story set at {f['place'].label} where {world.seeker.display} loses a {f['mystery_label']}, remembers a clue, and solves the mystery with a friend.",
        f"Write a child-friendly story where the lesson is to {f['lesson']}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question=f"Who was the story mainly about?",
            answer=f"The story was mainly about {world.seeker.display}, a little {world.seeker.species} who lost the {world.missing.name}."
        ),
        QAItem(
            question=f"What mystery did {world.seeker.display} have to solve?",
            answer=f"{world.seeker.display} had to solve the mystery of the missing {world.missing.name}."
        ),
        QAItem(
            question=f"What did the flashback help {world.seeker.display} remember?",
            answer=f"The flashback helped {world.seeker.display} remember rushing past {world.clue_spot}, where the {world.missing.name} slipped away."
        ),
        QAItem(
            question="How was the mystery solved?",
            answer=f"{world.friend.display} followed the clue back to {world.clue_spot} and found the {world.missing.name} tucked in the corner."
        ),
        QAItem(
            question="What lesson was learned?",
            answer=f"The lesson learned was to {LESSONS[world.facts['lesson']] }."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is when a story pauses to remember something that happened earlier."
        ),
        QAItem(
            question="What is a mystery?",
            answer="A mystery is a problem where someone does not know what happened and has to look for clues."
        ),
        QAItem(
            question="Why do clues matter?",
            answer="Clues matter because they can help someone figure out what happened and solve the mystery."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
place(P) :- place_fact(P).
character(C) :- character_fact(C).
mystery(M) :- mystery_fact(M).
lesson(L) :- lesson_fact(L).

compatible(P, S, F, M, L) :- place(P), character(S), character(F), mystery(M), lesson(L), S != F.
#show compatible/5.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp  # lazy
    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place_fact", pid))
    for name, _species in ANIMALS:
        lines.append(asp.fact("character_fact", name))
    for mid in MYSTERIES:
        lines.append(asp.fact("mystery_fact", mid))
    for lid in LESSONS:
        lines.append(asp.fact("lesson_fact", lid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_combos() -> set[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show compatible/5."))
    return set(asp.atoms(model, "compatible"))


def python_combos() -> set[tuple]:
    out = set()
    for p in PLACES:
        for s, _ in ANIMALS:
            for f, _ in ANIMALS:
                if s == f:
                    continue
                for m in MYSTERIES:
                    for l in LESSONS:
                        out.add((p, s, f, m, l))
    return out


def asp_verify() -> int:
    a = asp_combos()
    p = python_combos()
    if a == p:
        print(f"OK: ASP and Python agree on {len(a)} combinations.")
        return 0
    print("MISMATCH between ASP and Python:")
    if a - p:
        print("  only in ASP:", sorted(a - p)[:10])
    if p - a:
        print("  only in Python:", sorted(p - a)[:10])
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal mystery story with flashback and lesson learned.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--seeker", choices=[n for n, _ in ANIMALS])
    ap.add_argument("--friend", choices=[n for n, _ in ANIMALS])
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--lesson", choices=LESSONS)
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
    seekers = [n for n, _ in ANIMALS]
    friends = [n for n, _ in ANIMALS]
    places = list(PLACES)
    mysteries = list(MYSTERIES)
    lessons = list(LESSONS)

    place = args.place or rng.choice(places)
    seeker = args.seeker or rng.choice(seekers)
    friend = args.friend or rng.choice([n for n in friends if n != seeker])
    mystery = args.mystery or rng.choice(mysteries)
    lesson = args.lesson or rng.choice(lessons)

    if args.seeker and args.friend and args.seeker == args.friend:
        raise StoryError("The seeker and the friend must be different characters.")
    return StoryParams(place=place, seeker=seeker, friend=friend, mystery=mystery, lesson=lesson)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    lines.append(f"place: {world.place.label}")
    lines.append(f"seeker: {world.seeker.display} ({world.seeker.species})")
    lines.append(f"friend: {world.friend.display} ({world.friend.species})")
    lines.append(f"missing: {world.missing.name}, hidden={world.missing.hidden}, discovered={world.missing.discovered}")
    lines.append(f"clue_spot: {world.clue_spot}")
    lines.append(f"flashback_done: {world.flashback_done}")
    lines.append(f"solved: {world.solved}")
    lines.append(f"lesson_learned: {world.lesson_learned}")
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show compatible/5."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = sorted(asp_combos())
        print(f"{len(combos)} compatible combinations")
        for c in combos[:20]:
            print(c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for p, s, f, m, l in CURATED:
            params = StoryParams(place=p, seeker=s, friend=f, mystery=m, lesson=l, seed=base_seed)
            samples.append(generate(params))
    else:
        seen: set[str] = set()
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

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
