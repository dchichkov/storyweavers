#!/usr/bin/env python3
"""
A small Halloween detective storyworld.

Premise:
- A young detective follows a Halloween quest to recover a surprise.
- A "growned possum" may look suspicious, but the world proves otherwise.
- Magic clues and a surprise ending resolve the case.
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
# Domain registries
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Place:
    id: str
    label: str
    indoors: bool
    affords: set[str] = field(default_factory=set)


@dataclass(frozen=True)
class Case:
    id: str
    label: str
    clue: str
    reveal: str
    risk: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass(frozen=True)
class Charm:
    id: str
    label: str
    effect: str
    helps: set[str] = field(default_factory=set)


PLACES = {
    "street": Place(id="street", label="the lantern-lit street", indoors=False, affords={"search", "follow"}),
    "house": Place(id="house", label="the old house", indoors=True, affords={"search", "hide"}),
    "yard": Place(id="yard", label="the backyard", indoors=False, affords={"search", "follow", "hide"}),
    "museum": Place(id="museum", label="the tiny museum", indoors=True, affords={"search", "follow"}),
}

CASES = {
    "candy": Case(
        id="candy",
        label="a missing candy bag",
        clue="sweet wrappers",
        reveal="the candy bag had been tucked into a costume trunk",
        risk="the treats might be lost for the whole night",
        keyword="surprise",
        tags={"halloween", "surprise"},
    ),
    "mask": Case(
        id="mask",
        label="a missing mask",
        clue="a silver feather",
        reveal="the mask was hidden behind a magic poster",
        risk="the costume would not feel ready",
        keyword="magic",
        tags={"halloween", "magic"},
    ),
    "lantern": Case(
        id="lantern",
        label="a missing lantern",
        clue="sparkly dust",
        reveal="the lantern was waiting on the porch with a ribbon",
        risk="the dark path would stay gloomy",
        keyword="quest",
        tags={"halloween", "quest"},
    ),
}

CHARMS = {
    "glow": Charm(id="glow", label="a glow charm", effect="made little signs shine in the dark", helps={"search", "follow"}),
    "map": Charm(id="map", label="a moon map", effect="showed the next turn on the quest", helps={"follow"}),
    "bell": Charm(id="bell", label="a tiny bell charm", effect="helped the detective hear hiding places", helps={"search"}),
}

NAMES = ["Mina", "Toby", "June", "Nico", "Lena", "Owen", "Pia", "Rowan"]
SIDEKICKS = ["a growned possum", "a sleepy cat", "a small bat"]
MOODS = ["curious", "brave", "careful", "eager"]


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------

@dataclass
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    type: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def say(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class World:
    place: Place
    detective: Entity
    sidekick: Entity
    case: Case
    charm: Charm
    story: list[str] = field(default_factory=list)
    facts: dict = field(default_factory=dict)

    def add(self, line: str) -> None:
        if line:
            self.story.append(line)

    def render(self) -> str:
        return " ".join(self.story)


# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    case: str
    charm: str
    name: str
    mood: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _article(word: str) -> str:
    return "an" if word[:1].lower() in "aeiou" else "a"


def _base_title(case: Case) -> str:
    return {
        "candy": "the missing candy bag",
        "mask": "the missing mask",
        "lantern": "the missing lantern",
    }[case.id]


def build_world(params: StoryParams) -> World:
    place = PLACES[params.place]
    case = CASES[params.case]
    charm = CHARMS[params.charm]
    detective = Entity(id=params.name, kind="character", label=params.name, type="child", meters={"curiosity": 1.0}, memes={"mood": 1.0})
    sidekick = Entity(id="sidekick", kind="character", label="growned possum", type="possum", meters={"sneak": 1.0}, memes={"trust": 1.0})
    world = World(place=place, detective=detective, sidekick=sidekick, case=case, charm=charm)
    return world


def tell(world: World) -> None:
    d = world.detective
    s = world.sidekick
    c = world.case
    p = world.place
    ch = world.charm

    world.add(f"On Halloween night, {d.id} was a {world.facts['mood']} little detective at {p.label}.")
    world.add(f"{d.id} had a {_article(ch.label)} {ch.label} that {ch.effect}.")
    world.add(f"A clue said the case was about {_base_title(c)}.")

    world.add(f"Then {d.id} found {s.label} under a porch light, and the {s.label} looked growned and suspicious.")
    d.meters["doubt"] = 1.0
    s.memes["odd"] = 1.0
    world.add(f"{d.id} wanted to chase the trickiest lead, because {c.risk}.")

    world.add(f"The {ch.label} began to glow, and it pointed toward the next step of the {c.keyword} quest.")
    d.memes["hope"] = 1.0
    s.memes["helpful"] = 1.0
    world.add(f"The {s.label} tapped a wall, then showed a hidden spot with {c.clue} on it.")

    world.add(f"{d.id} peeked inside and found that {c.reveal}.")
    d.meters["doubt"] = 0.0
    d.memes["joy"] = 1.0
    s.memes["trust"] = 2.0

    world.add(f"It was not a spooky crime after all. The {s.label} had been guarding the surprise, not stealing it.")
    world.add(f"{d.id} smiled, and on Halloween night the detective, the {s.label}, and the {_article(ch.label)} {ch.label} all stayed together like a tiny team.")


def generation_prompts(world: World) -> list[str]:
    return [
        f"Write a short Halloween detective story with magic, a quest, and a surprise.",
        f"Tell a child-friendly mystery about {world.detective.id} and {world.sidekick.label} at {world.place.label}.",
        f"Make the story include the words halloween, growned, and possum.",
    ]


def story_qa(world: World) -> list[QAItem]:
    d = world.detective
    s = world.sidekick
    c = world.case
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about {d.id}, a little detective, and {s.label}, who seemed growned and suspicious at first.",
        ),
        QAItem(
            question=f"What made the detective keep following the clues?",
            answer=f"{d.id} kept going because {c.risk}, and the {world.charm.label} helped show the way.",
        ),
        QAItem(
            question=f"What was the surprise at the end?",
            answer=f"The surprise was that {c.reveal}, and the {s.label} was helping all along.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is Halloween?",
            answer="Halloween is a night when people wear costumes, tell spooky stories, and look for treats.",
        ),
        QAItem(
            question="What does a detective do?",
            answer="A detective looks for clues, asks careful questions, and tries to solve a mystery.",
        ),
        QAItem(
            question="What is a possum?",
            answer="A possum is a small animal that can live near houses and yards and often comes out at night.",
        ),
        QAItem(
            question="What does magic mean in a story?",
            answer="Magic means something strange and wonderful happens, like a charm glowing or a clue pointing the way.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    parts = ["== Prompts =="]
    parts.extend(sample.prompts)
    parts.append("")
    parts.append("== Story QA ==")
    for qa in sample.story_qa:
        parts.append(f"Q: {qa.question}")
        parts.append(f"A: {qa.answer}")
    parts.append("")
    parts.append("== World QA ==")
    for qa in sample.world_qa:
        parts.append(f"Q: {qa.question}")
        parts.append(f"A: {qa.answer}")
    return "\n".join(parts)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    lines.append(f"detective.curiosity={world.detective.meters.get('curiosity', 0)}")
    lines.append(f"detective.doubt={world.detective.meters.get('doubt', 0)}")
    lines.append(f"detective.joy={world.detective.memes.get('joy', 0)}")
    lines.append(f"sidekick.trust={world.sidekick.memes.get('trust', 0)}")
    lines.append(f"case={world.case.id}")
    lines.append(f"place={world.place.id}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
place(street). place(house). place(yard). place(museum).
case(candy). case(mask). case(lantern).
charm(glow). charm(map). charm(bell).

affords(street,search). affords(street,follow).
affords(house,search). affords(house,hide).
affords(yard,search). affords(yard,follow). affords(yard,hide).
affords(museum,search). affords(museum,follow).

keywords(candy,surprise).
keywords(mask,magic).
keywords(lantern,quest).

valid(Place,Case,Charm) :- affords(Place,search), keywords(Case,_), charm(Charm).
valid_story(Place,Case,Charm) :- valid(Place,Case,Charm), case(Case), place(Place), charm(Charm).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        for a in sorted(p.affords):
            lines.append(asp.fact("affords", pid, a))
    for cid, c in CASES.items():
        lines.append(asp.fact("case", cid))
        for t in sorted(c.tags):
            lines.append(asp.fact("tag", cid, t))
    for chid in CHARMS:
        lines.append(asp.fact("charm", chid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py == asp_set:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python")
    print("only in python:", sorted(py - asp_set))
    print("only in clingo:", sorted(asp_set - py))
    return 1


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in PLACES.values():
        for case in CASES.values():
            for charm in CHARMS.values():
                if "search" in place.affords and (charm.helps & {"search", "follow"}):
                    combos.append((place.id, case.id, charm.id))
    return combos


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Halloween detective storyworld with magic, quest, and surprise.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--case", choices=CASES)
    ap.add_argument("--charm", choices=CHARMS)
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--mood", choices=MOODS)
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
    choices = valid_combos()
    if args.place:
        choices = [c for c in choices if c[0] == args.place]
    if args.case:
        choices = [c for c in choices if c[1] == args.case]
    if args.charm:
        choices = [c for c in choices if c[2] == args.charm]
    if not choices:
        raise StoryError("No valid Halloween detective story matches those options.")
    place, case, charm = rng.choice(sorted(choices))
    return StoryParams(
        place=place,
        case=case,
        charm=charm,
        name=args.name or rng.choice(NAMES),
        mood=args.mood or rng.choice(MOODS),
    )


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    world.facts.update(mood=params.mood)
    tell(world)
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
        raise SystemExit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, case, charm) combos:")
        for combo in combos:
            print("  ", combo)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        curated = [
            StoryParams(place="street", case="lantern", charm="glow", name="Mina", mood="curious"),
            StoryParams(place="house", case="mask", charm="map", name="Toby", mood="careful"),
            StoryParams(place="yard", case="candy", charm="bell", name="June", mood="brave"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
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

    for idx, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.case} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
