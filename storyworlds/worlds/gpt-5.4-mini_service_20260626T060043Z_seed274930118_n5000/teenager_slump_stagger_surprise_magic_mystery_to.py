#!/usr/bin/env python3
"""
Standalone story world: a teenager in a slump, a stagger, and a small mystery
solved with surprise and a little magic, told in a fable-like style.

The seed image for this world:
- A teenager has fallen into a slump and moves through the day in a slow, low
  way.
- Something surprising interrupts that drift.
- A mystery is solved by noticing small clues and using a little magic.
- The ending should show a real change in motion, mood, and understanding.
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
    wearer: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "teenager"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Place:
    name: str
    mood: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Problem:
    id: str
    verb: str
    gerund: str
    rush: str
    slump_shift: str
    surprise_shift: str
    clue: str
    mystery: str
    solved_by: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Magic:
    id: str
    label: str
    method: str
    effect: str
    reveals: str


@dataclass
class World:
    place: Place
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    motion: float = 0.0
    surprise: float = 0.0
    mystery: float = 0.0
    magic: float = 0.0

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
        clone = World(self.place)
        clone.entities = {k: Entity(**{
            "id": e.id, "kind": e.kind, "type": e.type, "label": e.label,
            "phrase": e.phrase, "owner": e.owner, "wearer": e.wearer,
            "caretaker": e.caretaker, "meters": dict(e.meters), "memes": dict(e.memes),
        }) for k, e in self.entities.items()}
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        clone.motion = self.motion
        clone.surprise = self.surprise
        clone.mystery = self.mystery
        clone.magic = self.magic
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
PLACES = {
    "orchard": Place(name="the orchard", mood="quiet", affords={"walk", "listen", "find"}),
    "lantern_lane": Place(name="the lantern lane", mood="bright", affords={"walk", "look", "find"}),
    "riverside": Place(name="the riverside path", mood="soft", affords={"walk", "look", "find"}),
}

PROBLEMS = {
    "slump": Problem(
        id="slump",
        verb="shake off the slump",
        gerund="slumping along",
        rush="stagger past the path stones",
        slump_shift="slowed their step",
        surprise_shift="lifted their head",
        clue="a glint under the leaves",
        mystery="why the old bell had gone silent",
        solved_by="noticing the hidden key",
        tags={"slump", "stagger", "mystery"},
    ),
    "stagger": Problem(
        id="stagger",
        verb="steady themselves",
        gerund="staggering along",
        rush="stumble toward the lantern",
        slump_shift="made their knees feel heavy",
        surprise_shift="made them blink awake",
        clue="a footprint in the dust",
        mystery="who had moved the little gate",
        solved_by="following the small prints",
        tags={"stagger", "surprise", "mystery"},
    ),
}

MAGICS = {
    "spark": Magic(
        id="spark",
        label="a tiny spark of magic",
        method="touch the charm and whisper a wish",
        effect="a soft light spreads over the leaves",
        reveals="the hidden answer shines where no one thought to look",
    ),
    "mirror": Magic(
        id="mirror",
        label="a pocket mirror spell",
        method="tilt the mirror toward the dark corner",
        effect="the dark corner brightens with reflected light",
        reveals="the missing clue appears in the reflection",
    ),
    "whisper": Magic(
        id="whisper",
        label="a whispering spell",
        method="say the old words with a careful breath",
        effect="the wind goes still so tiny sounds can be heard",
        reveals="the mystery answer can be heard as a faint clue",
    ),
}

TEEN_NAMES = ["Mara", "Jonah", "Iris", "Nico", "Talia", "Rowan", "Zuri", "Eden"]
TRAITS = ["quiet", "curious", "restless", "thoughtful", "gentle", "brave"]


# ---------------------------------------------------------------------------
# Story parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    problem: str
    magic: str
    name: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place_id, place in PLACES.items():
        for prob_id in PROBLEMS:
            for magic_id in MAGICS:
                if "find" in place.affords and prob_id in {"slump", "stagger"} and magic_id in MAGICS:
                    combos.append((place_id, prob_id, magic_id))
    return combos


def explain_rejection(problem: Problem, magic: Magic) -> str:
    return (
        f"(No story: {problem.id} needs a mystery that can be solved by small clues, "
        f"but this magic would not fit the tale's gentle puzzle.)"
    )


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
place(P) :- setting(P).
problem(X) :- problem_name(X).
magic(M) :- magic_name(M).

valid(P, Pr, M) :- setting(P), problem_name(Pr), magic_name(M).

#show valid/3.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("setting", pid))
    for pid in PROBLEMS:
        lines.append(asp.fact("problem_name", pid))
    for mid in MAGICS:
        lines.append(asp.fact("magic_name", mid))
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
    print("MISMATCH between clingo and valid_combos():")
    if py - asp_set:
        print("  only in python:", sorted(py - asp_set))
    if asp_set - py:
        print("  only in clingo:", sorted(asp_set - py))
    return 1


# ---------------------------------------------------------------------------
# Narrative engine
# ---------------------------------------------------------------------------
def build_world(params: StoryParams) -> World:
    place = PLACES[params.place]
    world = World(place)
    teen = world.add(Entity(
        id=params.name,
        kind="character",
        type="teenager",
        label=params.name,
        meters={"motion": 0.0},
        memes={"slump": 0.0, "surprise": 0.0, "hope": 0.0},
    ))
    mentor = world.add(Entity(
        id="mentor",
        kind="character",
        type="elder",
        label="the old keeper",
        meters={"motion": 0.0},
        memes={"kindness": 1.0},
    ))
    mystery = PROBLEMS[params.problem]
    magic = MAGICS[params.magic]
    world.facts.update(teen=teen, mentor=mentor, mystery=mystery, magic=magic, params=params)
    return world


def _apply_slump(world: World, teen: Entity, problem: Problem) -> None:
    teen.meters["motion"] = teen.meters.get("motion", 0.0) + 0.2
    teen.memes["slump"] = teen.memes.get("slump", 0.0) + 1.0
    world.motion += 0.2
    world.say(
        f"{teen.id} was a teenager in a slump, and {teen.pronoun('possessive')} steps felt slow under {world.place.name}."
    )
    world.say(
        f"Each morning, {teen.id} went {problem.gerund}, as if the day had forgotten how to begin."
    )


def _apply_surprise(world: World, teen: Entity, problem: Problem) -> None:
    teen.memes["surprise"] = teen.memes.get("surprise", 0.0) + 1.0
    teen.meters["motion"] += 0.4
    world.surprise += 1.0
    world.motion += 0.4
    world.say(
        f"Then a surprise arrived: {problem.clue} flashed by the path, bright as a coin in shadow."
    )
    world.say(
        f"{teen.id} stopped, then staggered a step, because the little glint seemed to be asking for attention."
    )


def _apply_mystery(world: World, teen: Entity, mentor: Entity, problem: Problem, magic: Magic) -> None:
    world.mystery += 1.0
    world.magic += 1.0
    teen.memes["hope"] = teen.memes.get("hope", 0.0) + 1.0
    world.say(
        f"{mentor.label} smiled and offered {magic.label}; the kind old voice said, \"Use it gently, and look again.\""
    )
    world.say(
        f"{teen.id} followed the hint, and {magic.method}."
    )
    world.say(
        f"{magic.effect.capitalize()}; there, at last, was {problem.mystery}."
    )


def _apply_resolution(world: World, teen: Entity, problem: Problem, magic: Magic) -> None:
    teen.meters["motion"] += 0.8
    teen.memes["slump"] = 0.0
    teen.memes["hope"] += 1.0
    world.motion += 0.8
    world.say(
        f"With the clue found, {teen.id} solved the mystery by {problem.solved_by}, and the old hush gave way to relief."
    )
    world.say(
        f"By evening, {teen.id} was no longer {problem.gerund}; {teen.id} walked home with a lighter step, carrying {magic.label} like a small lantern in the heart."
    )


def tell(place: Place, problem: Problem, magic: Magic, name: str = "Mara", trait: str = "quiet") -> World:
    world = build_world(StoryParams(place=next(k for k, v in PLACES.items() if v is place),
                                    problem=problem.id, magic=magic.id, name=name, trait=trait))
    teen = world.get(name)
    mentor = world.get("mentor")

    world.say(
        f"Once in {place.name}, {teen.id} was a {trait} teenager who had slipped into a long slump."
    )
    world.say(
        f"The fable of the day was simple: when a heart grows heavy, a small surprise may open the road again."
    )

    world.para()
    _apply_slump(world, teen, problem)
    _apply_surprise(world, teen, problem)

    world.para()
    _apply_mystery(world, teen, mentor, problem, magic)

    world.para()
    _apply_resolution(world, teen, problem, magic)

    world.facts.update(place=place, problem=problem, magic=magic, teen=teen, mentor=mentor)
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    p = world.facts["problem"]
    m = world.facts["magic"]
    teen = world.facts["teen"]
    return [
        f"Write a short fable about a teenager in a slump who gets a surprise and solves a mystery with {m.label}.",
        f"Tell a gentle story where {teen.id} stops {p.gerund} after noticing a clue in a quiet place.",
        f"Write a child-friendly tale about a teenager, a stagger, and a hidden answer found through magic.",
    ]


def story_qa(world: World) -> list[QAItem]:
    teen = world.facts["teen"]
    problem = world.facts["problem"]
    magic = world.facts["magic"]
    place = world.facts["place"]
    return [
        QAItem(
            question=f"Who is the story about in {place.name}?",
            answer=f"It is about {teen.id}, a teenager who had fallen into a slump and needed a new beginning.",
        ),
        QAItem(
            question=f"What surprising thing first interrupted {teen.id}'s slump?",
            answer=f"{problem.clue.capitalize()} first caught {teen.id}'s eye, and that surprise made the story change direction.",
        ),
        QAItem(
            question=f"How was the mystery solved?",
            answer=f"The mystery was solved when {teen.id} used {magic.label} and followed the clue until the answer appeared.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"By the end, {teen.id} was walking with a lighter step instead of {problem.gerund}, and the heavy mood was gone.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a slump?",
            answer="A slump is a time when someone feels low, slow, or stuck and has trouble moving forward with energy.",
        ),
        QAItem(
            question="What does it mean to stagger?",
            answer="To stagger means to move unsteadily, as if your steps are uneven or hard to keep straight.",
        ),
        QAItem(
            question="What is a mystery?",
            answer="A mystery is something unknown that people try to understand by looking for clues.",
        ),
        QAItem(
            question="What does magic do in a fable?",
            answer="In a fable, magic often helps reveal a lesson or makes a hidden truth easier to see.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: meters={e.meters} memes={e.memes}")
    lines.append(f"motion={world.motion} surprise={world.surprise} mystery={world.mystery} magic={world.magic}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Public interface
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(place="orchard", problem="slump", magic="spark", name="Mara", trait="quiet"),
    StoryParams(place="lantern_lane", problem="stagger", magic="mirror", name="Nico", trait="curious"),
    StoryParams(place="riverside", problem="slump", magic="whisper", name="Talia", trait="thoughtful"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small fable-like world of slump, stagger, surprise, and magic.")
    ap.add_argument("--place", choices=PLACES.keys())
    ap.add_argument("--problem", choices=PROBLEMS.keys())
    ap.add_argument("--magic", choices=MAGICS.keys())
    ap.add_argument("--name", choices=TEEN_NAMES)
    ap.add_argument("--trait", choices=TRAITS)
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
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.problem is None or c[1] == args.problem)
              and (args.magic is None or c[2] == args.magic)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, problem, magic = rng.choice(sorted(combos))
    name = args.name or rng.choice(TEEN_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, problem=problem, magic=magic, name=name, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], PROBLEMS[params.problem], MAGICS[params.magic], params.name, params.trait)
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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid/3."))
        combos = sorted(set(asp.atoms(model, "valid")))
        print(f"{len(combos)} compatible combos:")
        for t in combos:
            print(" ", t)
        return

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        base_seed = args.seed if args.seed is not None else random.randrange(2**31)
        samples = []
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            i += 1
            try:
                params = resolve_params(args, random.Random(base_seed + i))
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

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.problem} at {p.place} with {p.magic}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
