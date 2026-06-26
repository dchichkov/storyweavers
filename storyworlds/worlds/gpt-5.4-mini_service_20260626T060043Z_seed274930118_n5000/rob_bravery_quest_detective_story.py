#!/usr/bin/env python3
"""
A standalone storyworld for a small detective tale about Rob, bravery, and a quest.

The world is intentionally compact: a child detective named Rob follows clues,
shows bravery when the case feels tricky, and finishes the quest by finding the
missing thing and naming what changed.
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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Location:
    id: str
    label: str
    mood: str
    clues: list[str] = field(default_factory=list)


@dataclass
class Case:
    id: str
    missing_item: str
    missing_phrase: str
    missing_location: str
    clue: str
    culprit: str
    culprit_reason: str
    ending_image: str
    prompt_word: str = "rob"


class World:
    def __init__(self, place: Location) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

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
# Story parameters
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    case: str
    name: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

LOCATIONS = {
    "alley": Location(
        id="alley",
        label="the narrow alley",
        mood="quiet",
        clues=["a shiny button", "muddy paw prints"],
    ),
    "pier": Location(
        id="pier",
        label="the wooden pier",
        mood="breezy",
        clues=["a loop of string", "salt on the boards"],
    ),
    "market": Location(
        id="market",
        label="the busy market",
        mood="loud",
        clues=["a torn ticket stub", "an apple peel trail"],
    ),
}

CASES = {
    "kite": Case(
        id="kite",
        missing_item="kite",
        missing_phrase="a red kite with a blue tail",
        missing_location="pier",
        clue="a loop of string",
        culprit="seagull",
        culprit_reason="it liked shiny string and flew toward the pier",
        ending_image="the red kite bobbing safely above the pier again",
        prompt_word="rob",
    ),
    "jar": Case(
        id="jar",
        missing_item="jar",
        missing_phrase="a jar of lemon jam",
        missing_location="market",
        clue="a torn ticket stub",
        culprit="pocketmouse",
        culprit_reason="it carried sweet crumbs through the market stalls",
        ending_image="the jar of lemon jam back on the stall, tied with twine",
        prompt_word="rob",
    ),
    "badge": Case(
        id="badge",
        missing_item="badge",
        missing_phrase="a silver badge",
        missing_location="alley",
        clue="a shiny button",
        culprit="cat",
        culprit_reason="it chased anything that glittered in the alley",
        ending_image="the silver badge pinned back on the detective board",
        prompt_word="rob",
    ),
}

NAMES = ["Rob", "Rory", "Ruby", "Rowan", "Remy"]
TRAIT_WORDS = ["brave", "steady", "keen", "patient", "bold"]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
case_valid(C) :- case(C), location(L), case_place(C, L), clue_at(L, Cl), case_clue(C, Cl).
show_valid(C) :- case_valid(C).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for loc in LOCATIONS.values():
        lines.append(asp.fact("location", loc.id))
        for clue in loc.clues:
            lines.append(asp.fact("clue_at", loc.id, clue))
    for case in CASES.values():
        lines.append(asp.fact("case", case.id))
        lines.append(asp.fact("case_place", case.id, case.missing_location))
        lines.append(asp.fact("case_clue", case.id, case.clue))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_cases() -> list[str]:
    import asp
    model = asp.one_model(asp_program("#show show_valid/1."))
    return sorted({case for (case,) in asp.atoms(model, "show_valid")})


# ---------------------------------------------------------------------------
# World logic
# ---------------------------------------------------------------------------

def build_world(params: StoryParams) -> World:
    case = CASES[params.case]
    world = World(LOCATIONS[case.missing_location])

    rob = world.add(Entity(
        id=params.name,
        kind="character",
        type="boy",
        label=params.name,
        meters={"meters": 0.0},
        memes={"bravery": 1.0, "quest": 1.0, "curiosity": 1.0},
    ))
    missing = world.add(Entity(
        id="missing",
        kind="thing",
        type=case.missing_item,
        label=case.missing_item,
        phrase=case.missing_phrase,
        location=case.missing_location,
        owner=params.name,
        meters={"lost": 1.0},
    ))
    culprit = world.add(Entity(
        id=case.culprit,
        kind="thing",
        type=case.culprit,
        label=case.culprit,
        meters={"sneaky": 1.0},
    ))

    world.facts.update(robot=rob, missing=missing, culprit=culprit, case=case)
    return world


def _intro(world: World) -> None:
    hero: Entity = world.facts["robot"]  # type: ignore[assignment]
    case: Case = world.facts["case"]  # type: ignore[assignment]
    world.say(
        f"{hero.id} was a brave little detective who liked a good quest."
    )
    world.say(
        f"One morning, {hero.id} heard that {case.missing_phrase} had gone missing."
    )


def _investigate(world: World) -> None:
    hero: Entity = world.facts["robot"]  # type: ignore[assignment]
    case: Case = world.facts["case"]  # type: ignore[assignment]
    place = world.place
    clue = case.clue

    hero.memes["quest"] += 1
    world.para()
    world.say(f"{hero.id} walked to {place.label} and looked very carefully.")
    world.say(f"The place felt {place.mood}, but {hero.id} kept going.")
    if clue in place.clues:
        hero.memes["bravery"] += 1
        hero.meters["meters"] = hero.meters.get("meters", 0.0) + 1.0
        world.say(
            f"Near the ground, {hero.id} found {clue}, and that made the case feel real."
        )
    else:
        raise StoryError("The chosen case does not fit the location clues.")


def _turn(world: World) -> None:
    hero: Entity = world.facts["robot"]  # type: ignore[assignment]
    case: Case = world.facts["case"]  # type: ignore[assignment]
    culprit: Entity = world.facts["culprit"]  # type: ignore[assignment]

    hero.memes["bravery"] += 1
    hero.memes["confidence"] = hero.memes.get("confidence", 0.0) + 1.0
    world.say(
        f"{hero.id} stayed brave and followed the clue to the quiet corner of the {world.place.id}."
    )
    world.say(
        f"There, {hero.id} saw the {culprit.label} with {case.culprit_reason}."
    )
    world.say(
        f"The {culprit.label} had not meant to be cruel; it had only been curious."
    )


def _resolve(world: World) -> None:
    hero: Entity = world.facts["robot"]  # type: ignore[assignment]
    case: Case = world.facts["case"]  # type: ignore[assignment]
    missing: Entity = world.facts["missing"]  # type: ignore[assignment]

    missing.meters["lost"] = 0.0
    missing.location = "with_owner"
    hero.memes["quest"] += 1
    hero.memes["bravery"] += 1
    world.para()
    world.say(
        f"{hero.id} lifted {case.missing_phrase} back where it belonged."
    )
    world.say(
        f"By the end of the quest, {case.ending_image} showed that the mystery was solved."
    )


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    case: Case = world.facts["case"]  # type: ignore[assignment]
    hero: Entity = world.facts["robot"]  # type: ignore[assignment]
    return [
        f"Write a short detective story about {hero.id}, bravery, and a quest to find {case.missing_phrase}.",
        f"Tell a child-friendly mystery where the word '{case.prompt_word}' appears and a brave detective follows clues.",
        f"Write a small story in which {hero.id} uses courage to solve a case at the {world.place.label}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero: Entity = world.facts["robot"]  # type: ignore[assignment]
    case: Case = world.facts["case"]  # type: ignore[assignment]
    place = world.place
    return [
        QAItem(
            question=f"Who went on the quest in this story?",
            answer=f"{hero.id} went on the quest as the brave little detective.",
        ),
        QAItem(
            question=f"What was missing from the story?",
            answer=f"{case.missing_phrase} was missing.",
        ),
        QAItem(
            question=f"Where did {hero.id} search for clues?",
            answer=f"{hero.id} searched at {place.label}.",
        ),
        QAItem(
            question=f"What clue helped {hero.id} solve the case?",
            answer=f"The clue was {case.clue}.",
        ),
        QAItem(
            question=f"What changed at the end of the story?",
            answer=f"The missing thing was found, and {case.ending_image} proved the quest was finished.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is bravery?",
            answer="Bravery is being able to keep going even when something feels a little scary.",
        ),
        QAItem(
            question="What is a quest?",
            answer="A quest is a journey or task where someone tries hard to find or do something important.",
        ),
        QAItem(
            question="What does a detective do?",
            answer="A detective looks for clues and tries to figure out a mystery.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    parts = ["== prompts =="]
    parts.extend(sample.prompts)
    parts.append("")
    parts.append("== story qa ==")
    for q in sample.story_qa:
        parts.append(f"Q: {q.question}")
        parts.append(f"A: {q.answer}")
    parts.append("")
    parts.append("== world qa ==")
    for q in sample.world_qa:
        parts.append(f"Q: {q.question}")
        parts.append(f"A: {q.answer}")
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def valid_cases() -> list[str]:
    return sorted(CASES)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.case and args.case not in CASES:
        raise StoryError(f"Unknown case: {args.case}")
    if args.name and not args.name.strip():
        raise StoryError("Name cannot be empty.")

    cases = [c for c in valid_cases() if args.case is None or c == args.case]
    if not cases:
        raise StoryError("No valid case matches the given options.")

    case = rng.choice(cases)
    name = args.name or rng.choice(NAMES)
    return StoryParams(case=case, name=name)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    _intro(world)
    _investigate(world)
    _turn(world)
    _resolve(world)
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
        print("--- trace ---")
        for e in sample.world.entities.values():
            print(f"{e.id}: meters={e.meters} memes={e.memes}")
    if qa:
        print()
        print(format_qa(sample))


# ---------------------------------------------------------------------------
# ASP verification
# ---------------------------------------------------------------------------

def asp_verify() -> int:
    import asp
    py = set(valid_cases())
    cl = set(asp_valid_cases())
    if py == cl:
        print(f"OK: ASP matches Python ({len(py)} cases).")
        return 0
    print("MISMATCH:")
    print("python only:", sorted(py - cl))
    print("asp only:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny detective storyworld about Rob, bravery, and a quest.")
    ap.add_argument("--case", choices=sorted(CASES))
    ap.add_argument("--name", choices=NAMES)
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


def asp_facts_and_rules() -> str:
    return asp_program("#show show_valid/1.")


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_facts_and_rules())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_cases())} valid cases:")
        for c in asp_valid_cases():
            print(" ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        for case in sorted(CASES):
            params = StoryParams(case=case, name="Rob")
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        for i in range(max(1, args.n * 50)):
            if len(samples) >= args.n:
                break
            params = resolve_params(args, random.Random(base_seed + i))
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

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            header = f"### {sample.params.case}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
