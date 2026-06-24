#!/usr/bin/env python3
"""
A tiny fable world about a weasel, a bum, and a fellow.

The seed tale behind this world is simple:
a weasel wants a warm, dry burrow; a bum wants a quiet place to rest;
a fellow tries to keep peace. Their conflict is not solved by force, but by
careful problem solving and a shared plan.

The world is intentionally small and classical:
- typed entities
- physical meters and emotional memes
- a state-driven plot with setup, conflict, turn, and resolution
- a matching inline ASP twin for reasonableness checks
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
    kind: str = "character"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"weasel", "fellow", "bum"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Place:
    id: str
    label: str
    shelter: bool = False
    affords: set[str] = field(default_factory=set)


@dataclass
class Need:
    id: str
    verb: str
    noun: str
    risk: str
    fix_kind: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Fix:
    id: str
    label: str
    prep: str
    tail: str
    helps: set[str] = field(default_factory=set)


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.trace_lines: list[str] = []

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
        import copy as _copy
        clone = World(self.place)
        clone.entities = _copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

PLACES = {
    "lane": Place("lane", "the lane", shelter=False, affords={"rest", "share"}),
    "barn": Place("barn", "the barn", shelter=True, affords={"rest", "share"}),
    "grove": Place("grove", "the grove", shelter=True, affords={"rest", "share"}),
}

NEEDS = {
    "warmth": Need(
        id="warmth",
        verb="find a warm place to rest",
        noun="warmth",
        risk="get cold",
        fix_kind="blanket",
        keyword="warm",
        tags={"cold", "shelter"},
    ),
    "dryness": Need(
        id="dryness",
        verb="stay dry during the rain",
        noun="dryness",
        risk="get soaked",
        fix_kind="roof",
        keyword="rain",
        tags={"rain", "shelter"},
    ),
    "peace": Need(
        id="peace",
        verb="share a quiet place to sit",
        noun="peace",
        risk="start an argument",
        fix_kind="bench",
        keyword="peace",
        tags={"share", "peace"},
    ),
}

FIXES = [
    Fix(
        id="straw",
        label="a straw blanket",
        prep="lay down a straw blanket first",
        tail="laid down the straw blanket and made a softer nest",
        helps={"cold"},
    ),
    Fix(
        id="roof",
        label="a dry roof beam",
        prep="move under the roof beam",
        tail="moved under the roof beam and stayed out of the rain",
        helps={"rain"},
    ),
    Fix(
        id="bench",
        label="a long bench",
        prep="sit together on the long bench",
        tail="sat together on the long bench and shared the shade",
        helps={"share", "peace"},
    ),
]

WEASEL_NAMES = ["Wren", "Milo", "Nell", "Pip"]
BUM_NAMES = ["Bram", "Bert", "Bobo", "Tate"]
FELLOW_NAMES = ["Owen", "Jules", "Rowan", "Evan"]
TRAITS = ["small", "quick", "gentle", "clever"]


# ---------------------------------------------------------------------------
# Params
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    need: str
    name_weasel: str
    name_bum: str
    name_fellow: str
    trait_weasel: str
    trait_bum: str
    trait_fellow: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A need is at risk if the place does not already support it.
at_risk(N, P) :- need(N), place(P), need_keyword(N, K), not place_supports(P, K).

% A fix is reasonable if it helps the need's risk and the place can hold it.
has_fix(N, F) :- at_risk(N, _), fix(F), need_risk(N, R), fix_helps(F, R).

valid(P, N) :- place(P), need(N), at_risk(N, P), has_fix(N, _).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        if place.shelter:
            lines.append(asp.fact("place_supports", pid, "rain"))
            lines.append(asp.fact("place_supports", pid, "cold"))
            lines.append(asp.fact("place_supports", pid, "share"))
        for a in sorted(place.affords):
            lines.append(asp.fact("affords", pid, a))
    for nid, need in NEEDS.items():
        lines.append(asp.fact("need", nid))
        lines.append(asp.fact("need_keyword", nid, need.keyword))
        lines.append(asp.fact("need_risk", nid, need.risk))
    for fx in FIXES:
        lines.append(asp.fact("fix", fx.id))
        for h in sorted(fx.helps):
            lines.append(asp.fact("fix_helps", fx.id, h))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------

def reasonableness_gate(place: Place, need: Need) -> None:
    if place.id == "lane" and need.id == "dryness":
        raise StoryError("The lane is too open for a rain-shelter story; choose a sheltered place.")


def best_fix(place: Place, need: Need) -> Optional[Fix]:
    for fx in FIXES:
        if need.risk in fx.helps and (place.shelter or fx.id == "bench"):
            return fx
    return None


def build_world(params: StoryParams) -> World:
    place = PLACES[params.place]
    need = NEEDS[params.need]
    reasonableness_gate(place, need)

    world = World(place)
    weasel = world.add(Entity(
        id=params.name_weasel, type="weasel", label="weasel",
        meters={"hunger": 0.0, "effort": 0.0}, memes={"desire": 0.0, "worry": 0.0, "hope": 0.0},
    ))
    bum = world.add(Entity(
        id=params.name_bum, type="bum", label="bum",
        meters={"tired": 0.0, "dust": 0.0}, memes={"worry": 0.0, "grumble": 0.0, "hope": 0.0},
    ))
    fellow = world.add(Entity(
        id=params.name_fellow, type="fellow", label="fellow",
        meters={"effort": 0.0}, memes={"calm": 0.0, "wisdom": 0.0, "hope": 0.0},
    ))

    fix = best_fix(place, need)

    # Act 1
    world.say(f"{weasel.id} was a {params.trait_weasel} weasel who liked to solve little troubles.")
    world.say(f"{bum.id} was a {params.trait_bum} bum who needed rest more than noise.")
    world.say(f"{fellow.id} was a {params.trait_fellow} fellow who tried to keep things fair.")
    world.say(f"One day, the three of them came to {place.label}.")

    world.para()

    # Act 2: conflict
    if need.id == "warmth":
        world.say(f"{weasel.id} wanted to {need.verb}, but the air was sharp and cold.")
        world.say(f"{bum.id} wanted the same spot, because he did not want to {need.risk}.")
    elif need.id == "dryness":
        world.say(f"Dark clouds gathered, and {weasel.id} wanted to {need.verb}.")
        world.say(f"{bum.id} wanted the same dry corner, because rain was starting to fall.")
    else:
        world.say(f"{weasel.id} wanted to {need.verb}, and {bum.id} wanted peace too.")
        world.say(f"They both reached for the same place, and their wanting turned into a quarrel.")

    weasel.memes["worry"] += 1
    bum.memes["worry"] += 1
    weasel.meters["effort"] += 1
    bum.meters["dust"] += 1

    world.say(f"Their voices grew sharp for a moment, and the little conflict made the lane feel smaller.")

    world.para()

    # Act 3: problem solving
    fellow.memes["wisdom"] += 1
    fellow.memes["calm"] += 1
    if fix is None:
        raise StoryError("No sensible fix exists for this need and place.")

    world.say(f"{fellow.id} looked around and thought carefully.")
    world.say(f'"{fix.prep}," said {fellow.id}, "and we can make room for everyone."')
    world.say(f"The others listened.")
    world.say(f"They {fix.tail}.")

    weasel.memes["hope"] += 1
    bum.memes["hope"] += 1
    fellow.memes["hope"] += 1
    weasel.memes["worry"] = 0.0
    bum.memes["worry"] = 0.0

    if need.id == "warmth":
        world.say(f"{weasel.id} curled into the straw and felt warm at last.")
        world.say(f"{bum.id} settled nearby, and the hard day seemed less hard.")
    elif need.id == "dryness":
        world.say(f"{weasel.id} stayed under the roof beam and kept dry.")
        world.say(f"{bum.id} sat beside him, listening to the rain without fear.")
    else:
        world.say(f"{weasel.id} and {bum.id} shared the bench without pushing.")
        world.say(f"The little quarrel faded, and the place grew peaceful again.")

    world.say(f"So the weasel, the bum, and the fellow all found a better way.")
    world.say("And the lesson was plain: a small mind can make a big problem smaller by thinking first.")

    world.facts.update(
        place=place,
        need=need,
        fix=fix,
        weasel=weasel,
        bum=bum,
        fellow=fellow,
    )
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    need = f["need"]
    return [
        f'Write a short fable about a weasel, a bum, and a fellow who face a {need.keyword} problem.',
        f"Tell a child-friendly story where three travelers disagree at {world.place.label} and solve the trouble kindly.",
        f'Write a fable that includes the words "weasel", "bum", and "fellow" and ends with a wise lesson.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    need: Need = f["need"]
    fix: Fix = f["fix"]
    weasel: Entity = f["weasel"]
    bum: Entity = f["bum"]
    fellow: Entity = f["fellow"]
    return [
        QAItem(
            question=f"Who was the story mainly about at {world.place.label}?",
            answer=f"It was about {weasel.id}, {bum.id}, and {fellow.id}, who each had a part in the little conflict and its solution.",
        ),
        QAItem(
            question=f"What problem did {weasel.id} and {bum.id} have?",
            answer=f"They both wanted the same place for {need.verb}, but that would not work well until they solved the problem together.",
        ),
        QAItem(
            question=f"How did {fellow.id} help?",
            answer=f"{fellow.id} noticed the trouble and suggested {fix.prep}, which gave them a peaceful and sensible plan.",
        ),
        QAItem(
            question="What changed by the end?",
            answer=f"The conflict cooled down, everyone had a safer and kinder arrangement, and the three of them were no longer arguing.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a fable?",
            answer="A fable is a short story that often uses animals or simple characters to teach a lesson.",
        ),
        QAItem(
            question="What does it mean to solve a problem?",
            answer="To solve a problem means to think carefully and find a way to make things better.",
        ),
        QAItem(
            question="Why is conflict sometimes useful in a story?",
            answer="Conflict makes a story interesting because it shows a hard problem that the characters must face and fix.",
        ),
    ]


# ---------------------------------------------------------------------------
# Output helpers
# ---------------------------------------------------------------------------

def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story Q&A ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World Q&A ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Standard interface
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny fable world about a weasel, a bum, and a fellow.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--need", choices=NEEDS)
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
    place = args.place or rng.choice(list(PLACES))
    need = args.need or rng.choice(list(NEEDS))
    return StoryParams(
        place=place,
        need=need,
        name_weasel=rng.choice(WEASEL_NAMES),
        name_bum=rng.choice(BUM_NAMES),
        name_fellow=rng.choice(FELLOW_NAMES),
        trait_weasel=rng.choice(TRAITS),
        trait_bum=rng.choice(TRAITS),
        trait_fellow=rng.choice(TRAITS),
    )


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
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


# ---------------------------------------------------------------------------
# ASP verify
# ---------------------------------------------------------------------------

def asp_valid_pairs() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = {(p, n) for p in PLACES for n in NEEDS if (PLACES[p].shelter or NEEDS[n].id != "dryness")}
    cl = set(asp_valid_pairs())
    if cl == py:
        print(f"OK: clingo gate matches Python gate ({len(cl)} pairs).")
        return 0
    print("MISMATCH between clingo and Python gate:")
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    if py - cl:
        print("  only in python:", sorted(py - cl))
    return 1


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

CURATED = [
    StoryParams("barn", "warmth", "Wren", "Bram", "Owen", "small", "tired", "clever"),
    StoryParams("grove", "dryness", "Milo", "Bert", "Jules", "quick", "grumpy", "gentle"),
    StoryParams("lane", "peace", "Nell", "Bobo", "Rowan", "gentle", "dusty", "wise"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        pairs = asp_valid_pairs()
        print(f"{len(pairs)} valid (place, need) pairs:\n")
        for p, n in pairs:
            print(f"  {p:8} {n}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
