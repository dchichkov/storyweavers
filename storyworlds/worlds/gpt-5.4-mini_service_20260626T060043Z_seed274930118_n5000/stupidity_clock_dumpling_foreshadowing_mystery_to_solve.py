#!/usr/bin/env python3
"""
storyworlds/worlds/stupidity_clock_dumpling_foreshadowing_mystery_to_solve.py
==============================================================================

A small story world about a puzzling clock, a missing dumpling, and a quest
that begins with a silly mistake and ends with a tidy, kind resolution.

The story style aims for a gentle rhyming feel, while still being state-driven:
a clue appears, a mystery becomes clear, and the hero's quest changes the world.
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
# World entities
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    location: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    name: str
    indoor: bool = True
    mood: str = "cozy"


@dataclass
class Clue:
    text: str
    hint: str
    reveals: str


@dataclass
class QuestStep:
    action: str
    result: str


@dataclass
class World:
    place: Place
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[tuple] = field(default_factory=set)
    clues_seen: list[str] = field(default_factory=list)

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
        clone.facts = copy.deepcopy(self.facts)
        clone.fired = set(self.fired)
        clone.clues_seen = list(self.clues_seen)
        clone.paragraphs = [[]]
        return clone


# ---------------------------------------------------------------------------
# Story model knobs
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    hero: str
    hero_type: str
    helper: str
    helper_type: str
    clock_kind: str
    dumpling_kind: str
    seed: Optional[int] = None


PLACES = {
    "market": Place("the market", indoor=False, mood="busy"),
    "kitchen": Place("the kitchen", indoor=True, mood="warm"),
    "square": Place("the town square", indoor=False, mood="bright"),
    "bakery": Place("the bakery", indoor=True, mood="sweet"),
}

HEROES = {
    "Mina": "girl",
    "Toby": "boy",
    "Lena": "girl",
    "Finn": "boy",
    "Pia": "girl",
    "Owen": "boy",
}

HELPERS = {
    "Aunt Tia": "woman",
    "Uncle Roe": "man",
    "Nia": "girl",
    "Pip": "boy",
}

CLOCKS = {
    "grand clock": "a grand clock with a silver hand",
    "tin clock": "a tin clock with a squeaky bell",
    "tower clock": "a tower clock with a golden face",
}

DUMPLINGS = {
    "pea dumpling": "a warm pea dumpling",
    "sweet dumpling": "a sweet dumpling with jam",
    "bean dumpling": "a bean dumpling in a soft wrapper",
}


# ---------------------------------------------------------------------------
# Rhyming-ish narration helpers
# ---------------------------------------------------------------------------
def opening_line(hero: Entity, place: Place, clock: Entity, dumpling: Entity) -> str:
    return (
        f"{hero.id} was a bright little child, quick and keen, "
        f"in {place.name} where the lamps were clean. "
        f"There stood {clock.phrase}, neat and tall, "
        f"and {hero.pronoun('possessive')} {dumpling.label} was the tastiest of all."
    )


def foreshadow_line(clock: Entity, dumpling: Entity) -> str:
    return (
        f"The clock gave a tick with a nervous sound, "
        f"and a tiny crumb lay on the ground. "
        f"That little crumb was a clue in sight, "
        f"like a wink from the day that said, 'Look right!'"
    )


def mystery_line(hero: Entity) -> str:
    return (
        f"Then the dumpling was missing, gone from the tray, "
        f"and {hero.id} frowned in a puzzled way. "
        f'"Who took my snack?" {hero.pronoun()} cried with care, '
        f"and the quest began in the open air."
    )


def quest_line(hero: Entity, helper: Entity, place: Place) -> str:
    return (
        f"{helper.id} said, 'Let's follow the crumbs so small; "
        f"the truth will tumble and answer all.' "
        f"So they went past stalls and under the arch, "
        f"on a careful quest and a listening march."
    )


def ending_line(hero: Entity, dumpling: Entity, clock: Entity, helper: Entity) -> str:
    return (
        f"At last they found the dumpling, snug and near, "
        f"with a silly mistake made plain and clear. "
        f"The clock chimed once, then twice, then three, "
        f"and {hero.id} laughed, 'Oh, that was me!' "
        f"{hero.pronoun().capitalize()} had set it down by the flower stand, "
        f"and {helper.id} smiled, warm and grand. "
        f"With the mystery solved, the night felt bright, "
        f"and the dumpling was eaten in happy light."
    )


# ---------------------------------------------------------------------------
# World logic
# ---------------------------------------------------------------------------
def build_world(params: StoryParams) -> World:
    place = PLACES[params.place]
    world = World(place)

    hero = world.add(Entity(
        id=params.hero,
        kind="character",
        type=params.hero_type,
        meters={"hunger": 1.0},
        memes={"worry": 0.0, "curiosity": 1.0, "joy": 0.0, "stupidity": 0.0},
    ))
    helper = world.add(Entity(
        id=params.helper,
        kind="character",
        type=params.helper_type,
        meters={"walk": 0.0},
        memes={"calm": 1.0, "joy": 0.0},
    ))
    clock = world.add(Entity(
        id="clock",
        type="clock",
        label="clock",
        phrase=CLOCKS[params.clock_kind],
        location=place.name,
        meters={"time": 1.0, "tick": 1.0},
        memes={"mystery": 0.0},
    ))
    dumpling = world.add(Entity(
        id="dumpling",
        type="dumpling",
        label="dumpling",
        phrase=DUMPLINGS[params.dumpling_kind],
        owner=hero.id,
        location="tray",
        meters={"warmth": 1.0},
        memes={"value": 1.0},
    ))
    clue = world.add(Entity(
        id="crumb",
        type="clue",
        label="crumb",
        phrase="a crumb near the flower stand",
        location="flower stand",
        meters={"smallness": 1.0},
        memes={"hint": 1.0},
    ))

    world.facts.update(hero=hero, helper=helper, clock=clock, dumpling=dumpling, clue=clue)
    return world


def apply_clue(world: World) -> None:
    hero: Entity = world.facts["hero"]
    clock: Entity = world.facts["clock"]
    clue: Entity = world.facts["clue"]

    world.say(opening_line(hero, world.place, clock, world.facts["dumpling"]))
    world.say(foreshadow_line(clock, world.facts["dumpling"]))
    world.clues_seen.append(clue.label)
    hero.memes["curiosity"] += 1.0
    clock.memes["mystery"] += 1.0


def apply_mystery(world: World) -> None:
    hero: Entity = world.facts["hero"]
    dumpling: Entity = world.facts["dumpling"]
    helper: Entity = world.facts["helper"]
    hero.memes["worry"] += 1.0
    dumpling.location = "missing"
    world.say(mystery_line(hero))
    world.para()
    world.say(quest_line(hero, helper, world.place))


def apply_quest(world: World) -> None:
    hero: Entity = world.facts["hero"]
    helper: Entity = world.facts["helper"]
    dumpling: Entity = world.facts["dumpling"]
    clock: Entity = world.facts["clock"]

    hero.meters["walk"] = hero.meters.get("walk", 0.0) + 1.0
    helper.meters["walk"] = helper.meters.get("walk", 0.0) + 1.0
    clock.meters["tick"] += 1.0

    dumpling.location = "flower stand"
    hero.memes["joy"] += 1.0
    hero.memes["worry"] = 0.0
    helper.memes["joy"] += 1.0
    world.para()
    world.say(ending_line(hero, dumpling, clock, helper))


def tell_story(params: StoryParams) -> World:
    world = build_world(params)
    apply_clue(world)
    apply_mystery(world)
    apply_quest(world)
    world.facts["resolved"] = True
    return world


# ---------------------------------------------------------------------------
# Validity / reasonableness
# ---------------------------------------------------------------------------
def valid_combo(place: str, clock_kind: str, dumpling_kind: str) -> bool:
    # Any place can host the tale, but the story is only interesting if it has
    # both a clock and a dumpling, and the quest can plausibly unfold.
    return place in PLACES and clock_kind in CLOCKS and dumpling_kind in DUMPLINGS


def explain_rejection() -> str:
    return "(No story: the requested story needs a place, a clock, and a dumpling.)"


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
place(P) :- setting(P).
clock(C) :- clock_kind(C).
dumpling(D) :- dumpling_kind(D).

valid_story(P,C,D) :- place(P), clock(C), dumpling(D).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p in PLACES:
        lines.append(asp.fact("setting", p))
    for c in CLOCKS:
        lines.append(asp.fact("clock_kind", c))
    for d in DUMPLINGS:
        lines.append(asp.fact("dumpling_kind", d))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = {(p, c, d) for p in PLACES for c in CLOCKS for d in DUMPLINGS if valid_combo(p, c, d)}
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches Python ({len(py)} combos).")
        return 0
    print("MISMATCH between Python and clingo.")
    print("only in python:", sorted(py - cl))
    print("only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    clock: Entity = f["clock"]
    dumpling: Entity = f["dumpling"]
    return [
        f"Write a short rhyming story about {hero.id}, {clock.phrase}, and a missing dumpling.",
        f"Tell a gentle mystery-to-solve quest where {helper.id} helps {hero.id} find {dumpling.phrase}.",
        f"Write a child-friendly story with foreshadowing, a clue, and a happy ending in {world.place.name}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    clock: Entity = f["clock"]
    dumpling: Entity = f["dumpling"]
    return [
        QAItem(
            question=f"What was the mystery in the story?",
            answer=f"The mystery was that {hero.id}'s {dumpling.label} went missing, and everyone had to solve the puzzle.",
        ),
        QAItem(
            question=f"What clue helped them begin the quest?",
            answer=f"A small crumb near the flower stand helped point the way and foreshadow where the dumpling might be.",
        ),
        QAItem(
            question=f"Who helped {hero.id} solve the problem?",
            answer=f"{helper.id} helped {hero.id} follow the crumbs and finish the quest.",
        ),
        QAItem(
            question=f"What finally happened to the dumpling?",
            answer=f"The dumpling was found near the flower stand, and the silly mistake was fixed.",
        ),
        QAItem(
            question=f"Why did the clock matter in the story?",
            answer=f"The clock gave the story its ticking clue, and its chime marked the moment the mystery became clear.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a clock for?",
            answer="A clock helps people tell time by showing or counting the hours and minutes.",
        ),
        QAItem(
            question="What is a dumpling?",
            answer="A dumpling is a small lump of dough or filling that is cooked and eaten as food.",
        ),
        QAItem(
            question="What is foreshadowing in a story?",
            answer="Foreshadowing is when a story drops a clue early so readers can guess that something important may happen later.",
        ),
        QAItem(
            question="What is a mystery to solve?",
            answer="A mystery to solve is a puzzle where someone needs to find out what happened or where something went.",
        ),
        QAItem(
            question="What is a quest?",
            answer="A quest is a journey or search to find something important or fix a problem.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== Story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        bits = []
        if e.location:
            bits.append(f"location={e.location}")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
    lines.append(f"clues_seen={world.clues_seen}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------
def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(list(PLACES))
    hero = args.name or rng.choice(list(HEROES))
    hero_type = args.hero_type or HEROES[hero]
    helper = args.helper or rng.choice(list(HELPERS))
    helper_type = HELPERS[helper]
    clock_kind = args.clock_kind or rng.choice(list(CLOCKS))
    dumpling_kind = args.dumpling_kind or rng.choice(list(DUMPLINGS))
    if not valid_combo(place, clock_kind, dumpling_kind):
        raise StoryError(explain_rejection())
    return StoryParams(
        place=place,
        hero=hero,
        hero_type=hero_type,
        helper=helper,
        helper_type=helper_type,
        clock_kind=clock_kind,
        dumpling_kind=dumpling_kind,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A rhyming story world of clock, dumpling, foreshadowing, and quest.")
    ap.add_argument("--place", choices=list(PLACES))
    ap.add_argument("--name")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--clock-kind", choices=list(CLOCKS))
    ap.add_argument("--dumpling-kind", choices=list(DUMPLINGS))
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


CURATED = [
    StoryParams(place="market", hero="Mina", hero_type="girl", helper="Aunt Tia", helper_type="woman", clock_kind="tower clock", dumpling_kind="pea dumpling"),
    StoryParams(place="bakery", hero="Toby", hero_type="boy", helper="Pip", helper_type="boy", clock_kind="tin clock", dumpling_kind="sweet dumpling"),
    StoryParams(place="square", hero="Lena", hero_type="girl", helper="Nia", helper_type="girl", clock_kind="grand clock", dumpling_kind="bean dumpling"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/3."))
        print(sorted(set(asp.atoms(model, "valid_story"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            i += 1
            rng = random.Random(base_seed + i)
            try:
                params = resolve_params(args, rng)
            except StoryError as e:
                print(e)
                return
            params.seed = base_seed + i
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

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        if args.all:
            p = sample.params
            header = f"### {p.name} at {p.place}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
