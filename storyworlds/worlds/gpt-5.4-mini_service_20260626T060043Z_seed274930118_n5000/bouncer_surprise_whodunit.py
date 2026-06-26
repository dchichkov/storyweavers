#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/bouncer_surprise_whodunit.py
======================================================================================================

A small whodunit-style storyworld about a bouncer, a surprise, and a clue-led
reveal. The world simulates a tiny mystery at a child-friendly venue: someone
is hiding something, the bouncer notices the odd details, and the surprise turns
out to be kind rather than mean.

The domain seed word is "bouncer"; the narrative style leans toward Whodunit,
with concrete clues, suspicion, and a final reveal image proving what changed.
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
# Entities
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    carried_by: Optional[str] = None
    hidden: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Venue:
    place: str = "the community hall"
    crowd: str = "a line of children"
    afford: set[str] = field(default_factory=lambda: {"party", "surprise"})


@dataclass
class Mystery:
    id: str
    clue_word: str
    hidden_object: str
    reveal_object: str
    suspicious_sign: str
    surprise_kind: str


@dataclass
class StoryParams:
    place: str
    mystery: str
    hero_name: str
    hero_type: str
    host_name: str
    host_type: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------
class World:
    def __init__(self, venue: Venue):
        self.venue = venue
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.trace_notes: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

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
VENUES = {
    "hall": Venue(place="the community hall", crowd="a line of children"),
    "library": Venue(place="the little library", crowd="a row of quiet guests"),
    "gym": Venue(place="the school gym", crowd="parents and children"),
}

MYSTERIES = {
    "cake": Mystery(
        id="cake",
        clue_word="sprinkles",
        hidden_object="a birthday cake",
        reveal_object="a birthday cake",
        suspicious_sign="a trail of frosting",
        surprise_kind="surprise party",
    ),
    "gift": Mystery(
        id="gift",
        clue_word="ribbon",
        hidden_object="a wrapped gift",
        reveal_object="a wrapped gift",
        suspicious_sign="little bits of ribbon",
        surprise_kind="surprise gift",
    ),
    "banner": Mystery(
        id="banner",
        clue_word="glitter",
        hidden_object="a banner",
        reveal_object="a happy banner",
        suspicious_sign="sparkly dust",
        surprise_kind="surprise welcome",
    ),
}

HERO_NAMES = ["Maya", "Leo", "Nina", "Toby", "Ella", "Milo"]
HOST_NAMES = ["Mrs. Pine", "Mr. Bell", "Aunt June", "Coach Ray"]
TYPES = ["girl", "boy"]

KNOWLEDGE = {
    "bouncer": [
        ("What does a bouncer do?",
         "A bouncer stands near the door, checks who is coming in, and helps keep the place safe and calm.")
    ],
    "surprise": [
        ("What is a surprise?",
         "A surprise is something unexpected that people do not know about until the moment it is revealed.")
    ],
    "clue": [
        ("What is a clue?",
         "A clue is a little hint that helps someone figure something out.")
    ],
    "frosting": [
        ("What is frosting?",
         "Frosting is sweet, soft topping on a cake, often creamy and sugary.")
    ],
    "ribbon": [
        ("What is ribbon used for?",
         "Ribbon is a thin strip of fabric used to tie gifts or decorations.")
    ],
    "glitter": [
        ("What is glitter?",
         "Glitter is tiny sparkly pieces that shine and scatter light.")
    ],
}


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str]]:
    return [(place, mystery) for place in VENUES for mystery in MYSTERIES]


def explain_rejection(place: str, mystery: str) -> str:
    return f"(No story: the mystery '{mystery}' cannot happen at {place} in this tiny whodunit.)"


# ---------------------------------------------------------------------------
# Narrative helpers
# ---------------------------------------------------------------------------
def _start(world: World, hero: Entity, host: Entity, mystery: Mystery) -> None:
    world.say(
        f"{hero.id} was the bouncer at {world.venue.place}. "
        f"{hero.pronoun('subject').capitalize()} liked keeping the door calm and neat."
    )
    world.say(
        f"That evening, {host.id} smiled and said there would be a {mystery.surprise_kind}. "
        f"But something was missing, and everyone looked at the room as if it had hidden a secret."
    )


def _clue(world: World, hero: Entity, mystery: Mystery) -> None:
    hero.memes["curious"] = hero.memes.get("curious", 0) + 1
    world.say(
        f"{hero.id} noticed {mystery.suspicious_sign} near the door. "
        f"That was a clue, and {hero.pronoun('subject')} bent down to look closer."
    )


def _suspects(world: World, hero: Entity, host: Entity, mystery: Mystery) -> None:
    hero.memes["suspicion"] = hero.memes.get("suspicion", 0) + 1
    world.say(
        f"{hero.id} wondered if someone had taken {mystery.hidden_object}. "
        f"{hero.pronoun('subject').capitalize()} asked {host.id} who had come in first."
    )
    world.say(
        f"{host.id} pointed to the side table and said, "
        f"“I saw only a helper carrying {mystery.hidden_object.split()[1]} things and smiling very hard.”"
    )


def _reveal(world: World, hero: Entity, host: Entity, mystery: Mystery) -> None:
    hero.memes["relief"] = hero.memes.get("relief", 0) + 1
    world.say(
        f"Then the mystery opened wide: {mystery.hidden_object} was not stolen at all. "
        f"It had been hidden for the {mystery.surprise_kind}."
    )
    world.say(
        f"{hero.id} laughed, opened the door, and let the happy crowd in. "
        f"Under the bright lights, the {mystery.reveal_object} looked ready for everyone to see."
    )


# ---------------------------------------------------------------------------
# Story construction
# ---------------------------------------------------------------------------
def tell(params: StoryParams) -> World:
    if params.place not in VENUES or params.mystery not in MYSTERIES:
        raise StoryError("Invalid place or mystery choice.")

    world = World(VENUES[params.place])
    mystery = MYSTERIES[params.mystery]
    hero = world.add(Entity(id=params.hero_name, kind="character", type=params.hero_type))
    host = world.add(Entity(id=params.host_name, kind="character", type=params.host_type))
    hidden = world.add(Entity(
        id="mystery_object",
        type=mystery.id,
        label=mystery.hidden_object,
        hidden=True,
        owner=host.id,
    ))

    world.facts.update(
        hero=hero,
        host=host,
        hidden=hidden,
        mystery=mystery,
        venue=world.venue,
    )

    _start(world, hero, host, mystery)
    world.para()
    _clue(world, hero, mystery)
    _suspects(world, hero, host, mystery)
    world.para()
    _reveal(world, hero, host, mystery)
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]
    host: Entity = f["host"]
    mystery: Mystery = f["mystery"]
    return [
        f'Write a child-friendly whodunit story about a bouncer named {hero.id} who notices a clue.',
        f"Tell a short mystery where {hero.id} works at {world.venue.place} and discovers that {mystery.hidden_object} is part of a {mystery.surprise_kind}.",
        f"Write a simple story with suspense, a clue, and a surprise ending at {world.venue.place}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    host: Entity = f["host"]
    mystery: Mystery = f["mystery"]
    return [
        QAItem(
            question=f"Who was the bouncer in the story?",
            answer=f"{hero.id} was the bouncer, and {hero.pronoun('subject')} stood by the door at {world.venue.place}.",
        ),
        QAItem(
            question=f"What clue did {hero.id} notice?",
            answer=f"{hero.id} noticed {mystery.suspicious_sign}, which helped make the mystery feel like a real whodunit.",
        ),
        QAItem(
            question=f"What was the surprise at the end?",
            answer=f"The surprise was that {mystery.hidden_object} had been hidden for a {mystery.surprise_kind}, not taken away.",
        ),
        QAItem(
            question=f"Who explained what was really happening?",
            answer=f"{host.id} explained that the item was being saved for the surprise, so the worry could turn into relief.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    keys = {"bouncer", "surprise", "clue"}
    if world.facts["mystery"].id == "cake":
        keys.add("frosting")
    if world.facts["mystery"].id == "gift":
        keys.add("ribbon")
    if world.facts["mystery"].id == "banner":
        keys.add("glitter")
    out: list[QAItem] = []
    for k in ["bouncer", "surprise", "clue", "frosting", "ribbon", "glitter"]:
        if k in keys:
            out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[k])
    return out


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
place_ok(P) :- venue(P).
mystery_ok(M) :- mystery(M).
valid_story(P, M) :- place_ok(P), mystery_ok(M).
#show valid_story/2.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place in VENUES:
        lines.append(asp.fact("venue", place))
    for mystery in MYSTERIES:
        lines.append(asp.fact("mystery", mystery))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple[str, str]]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Params and generation
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    mystery: str
    hero_name: str
    hero_type: str
    host_name: str
    host_type: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small bouncer-and-surprise whodunit storyworld.")
    ap.add_argument("--place", choices=VENUES)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-type", choices=TYPES)
    ap.add_argument("--host-name")
    ap.add_argument("--host-type", choices=["mother", "father", "woman", "man"])
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
    combos = valid_combos()
    if args.place and args.mystery:
        if (args.place, args.mystery) not in combos:
            raise StoryError(explain_rejection(args.place, args.mystery))
    place = args.place or rng.choice(sorted(VENUES))
    mystery = args.mystery or rng.choice(sorted(MYSTERIES))
    hero_type = args.hero_type or rng.choice(TYPES)
    hero_name = args.hero_name or rng.choice(HERO_NAMES)
    host_type = args.host_type or rng.choice(["mother", "father", "woman", "man"])
    host_name = args.host_name or rng.choice(HOST_NAMES)
    return StoryParams(place=place, mystery=mystery, hero_name=hero_name, hero_type=hero_type, host_name=host_name, host_type=host_type)


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


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print("--- world trace ---")
        for e in sample.world.entities.values():
            bits = []
            if e.hidden:
                bits.append("hidden")
            if e.meters:
                bits.append(f"meters={e.meters}")
            if e.memes:
                bits.append(f"memes={e.memes}")
            print(f"{e.id}: {e.type} {' '.join(bits)}")
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible stories:")
        for p, m in combos:
            print(f"  {p}  {m}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for place in sorted(VENUES):
            for mystery in sorted(MYSTERIES):
                params = StoryParams(
                    place=place,
                    mystery=mystery,
                    hero_name=HERO_NAMES[(len(samples) + 1) % len(HERO_NAMES)],
                    hero_type=TYPES[len(samples) % len(TYPES)],
                    host_name=HOST_NAMES[len(samples) % len(HOST_NAMES)],
                    host_type=["mother", "father", "woman", "man"][len(samples) % 4],
                )
                samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
        header = f"### variant {i + 1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
