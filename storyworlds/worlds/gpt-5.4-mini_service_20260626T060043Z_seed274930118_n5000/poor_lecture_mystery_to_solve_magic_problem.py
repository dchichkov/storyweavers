#!/usr/bin/env python3
"""
A standalone storyworld for a small whodunit-style mystery:
a poor child, a stern lecture, a magical clue, and a problem that gets solved.

The seed idea:
---
A poor child comes home after a lecture and finds a problem: a missing school
chalk box and a strange shimmer near the window. The grown-ups suspect trouble.
The child notices tiny clues, uses a little magic, and solves the mystery by
finding who moved the box and why.

The world is built so state changes matter:
- poor means the child has very little money, but can still notice useful clues
- lecture increases worry and shame
- magic reveals hidden traces or patterns
- problem solving turns suspicion into a fair answer
"""

from __future__ import annotations

import argparse
import json
import os
import random
import re
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

# ---------------------------------------------------------------------------
# World constants
# ---------------------------------------------------------------------------

THRESHOLD = 1.0

PLACES = {
    "school": "the school",
    "hall": "the hallway",
    "home": "the small home",
    "library": "the library",
    "garden": "the garden",
}

MYSTERIES = {
    "missing_chalk": "missing chalk",
    "lost_key": "lost key",
    "strange_note": "strange note",
    "vanished_cookie": "vanished cookie",
}

MAGICS = {
    "glow": "a soft glow",
    "spark": "a tiny spark",
    "mirror": "a mirror trick",
    "whisper": "a whisper spell",
}

PROBLEMS = {
    "who_moved_it": "who moved the thing",
    "what_left_trace": "what left the trace",
    "where_did_it_go": "where it went",
    "why_was_it_hidden": "why it was hidden",
}

SUSPECT_ROLES = ["janitor", "teacher", "neighbor", "classmate", "librarian"]
CHILD_NAMES = ["Mina", "Toby", "Iris", "Noah", "Nina", "Eli", "Maya", "Arlo"]
ADULT_NAMES = ["Ms. Reed", "Mr. Vale", "Mrs. Finch", "Mr. Gray"]
TRAITS = ["quiet", "curious", "careful", "brave", "poor", "patient"]

# ---------------------------------------------------------------------------
# Entities and world model
# ---------------------------------------------------------------------------

@dataclass
class Entity:
    id: str
    kind: str = "thing"   # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    location: str = ""
    visible: bool = True
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)

    def __post_init__(self):
        if not self.meters:
            self.meters = {"dust": 0.0, "hidden": 0.0}
        if not self.memes:
            self.memes = {"worry": 0.0, "hope": 0.0, "confidence": 0.0, "shame": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "teacher", "librarian"}
        male = {"boy", "man", "father", "janitor", "neighbor", "classmate"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class World:
    place: str
    mystery: str
    magic: str
    problem: str
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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
    place: str
    mystery: str
    magic: str
    problem: str
    name: str
    child_type: str
    adult: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------

def mystery_is_plausible(place: str, mystery: str) -> bool:
    if place in {"school", "hall", "library"}:
        return mystery in {"missing_chalk", "lost_key", "strange_note"}
    if place in {"home", "garden"}:
        return mystery in {"lost_key", "vanished_cookie", "strange_note"}
    return True


def magic_can_help(mystery: str, magic: str) -> bool:
    pairs = {
        "missing_chalk": {"glow", "mirror"},
        "lost_key": {"glow", "whisper"},
        "strange_note": {"mirror", "whisper"},
        "vanished_cookie": {"spark", "whisper"},
    }
    return magic in pairs.get(mystery, set())


def problem_matches(mystery: str, problem: str) -> bool:
    pairs = {
        "missing_chalk": {"who_moved_it", "where_did_it_go"},
        "lost_key": {"where_did_it_go", "what_left_trace"},
        "strange_note": {"what_left_trace", "why_was_it_hidden"},
        "vanished_cookie": {"who_moved_it", "why_was_it_hidden"},
    }
    return problem in pairs.get(mystery, set())


def valid_combo(place: str, mystery: str, magic: str, problem: str) -> bool:
    return mystery_is_plausible(place, mystery) and magic_can_help(mystery, magic) and problem_matches(mystery, problem)


def explain_rejection(place: str, mystery: str, magic: str, problem: str) -> str:
    reasons = []
    if not mystery_is_plausible(place, mystery):
        reasons.append(f"{mystery.replace('_', ' ')} does not fit {place}")
    if not magic_can_help(mystery, magic):
        reasons.append(f"{magic} does not help with {mystery.replace('_', ' ')}")
    if not problem_matches(mystery, problem):
        reasons.append(f"{problem.replace('_', ' ')} does not match {mystery.replace('_', ' ')}")
    return "(No story: " + "; ".join(reasons) + ".)"


# ---------------------------------------------------------------------------
# World simulation
# ---------------------------------------------------------------------------

def build_world(params: StoryParams) -> World:
    world = World(params.place, params.mystery, params.magic, params.problem)

    child = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.child_type,
        location=params.place,
        traits=["poor", params.trait],
    ))
    adult = world.add(Entity(
        id="Adult",
        kind="character",
        type=params.adult,
        label=params.adult,
        location=params.place,
    ))

    clue = world.add(Entity(
        id="Clue",
        type="thing",
        label=params.mystery.replace("_", " "),
        phrase=params.mystery.replace("_", " "),
        location=params.place,
        visible=False,
    ))

    suspect = world.add(Entity(
        id="Suspect",
        kind="character",
        type=random.choice(SUSPECT_ROLES),
        label="the suspect",
        location=params.place,
    ))

    # hidden facts
    world.facts.update(
        child=child,
        adult=adult,
        clue=clue,
        suspect=suspect,
        place=params.place,
        mystery=params.mystery,
        magic=params.magic,
        problem=params.problem,
    )

    # Act 1: setup
    child.memes["worry"] += 1
    child.memes["shame"] += 1
    world.say(f"{child.id} was a poor {params.child_type} who kept careful count of every coin.")
    world.say(f"At {params.place}, {child.id} had just sat through a long lecture from {adult.label}.")

    if params.mystery == "missing_chalk":
        world.say("Then the school chalk box turned up missing, and everyone started whispering.")
    elif params.mystery == "lost_key":
        world.say("Then a little key went missing, and the room felt suddenly locked and tight.")
    elif params.mystery == "strange_note":
        world.say("Then a strange note appeared, and its neat letters made everybody stare.")
    else:
        world.say("Then a small cookie vanished, and crumbs near the sink told a tricky story.")

    world.para()

    # Act 2: tension and clues
    child.memes["confidence"] += 1
    world.say(f"{child.id} did not shout. {child.pronoun().capitalize()} looked down, then looked again.")
    world.say(f"A tiny trace near the window matched {params.magic.replace('_', ' ')} more than an accident.")
    if params.magic == "glow":
        clue.visible = True
        clue.meters["hidden"] = 0.0
        world.say("A soft glow lit the dust on the sill, showing a line nobody else had noticed.")
    elif params.magic == "mirror":
        clue.visible = True
        clue.meters["hidden"] = 0.0
        world.say("A hand mirror caught a hidden mark, and the mark pointed toward the door.")
    elif params.magic == "spark":
        clue.visible = True
        clue.meters["hidden"] = 0.0
        world.say("A tiny spark jumped over the crumbs and made a neat little trail shine.")
    else:
        clue.visible = True
        clue.meters["hidden"] = 0.0
        world.say("A whisper spell brushed the air, and the hidden clue seemed to answer back.")

    world.say(f"{params.adult} frowned, because the problem was still unsolved.")
    world.para()

    # Act 3: problem solving
    if params.problem == "who_moved_it":
        world.say(f"{child.id} asked who had moved it, and the answer came from the trail.")
    elif params.problem == "what_left_trace":
        world.say(f"{child.id} asked what had left the trace, and the clue answered first.")
    elif params.problem == "where_did_it_go":
        world.say(f"{child.id} asked where it had gone, and the path of dust gave away the way.")
    else:
        world.say(f"{child.id} asked why it was hidden, and the reason turned out to be kinder than anyone guessed.")

    # Reveal and solve
    suspect.visible = True
    child.memes["worry"] = 0.0
    child.memes["hope"] += 1
    child.memes["confidence"] += 1

    if params.mystery == "missing_chalk":
        world.say(f"It was the {suspect.type} who had moved the chalk box to clean the shelf.")
        world.say(f"{params.adult} had been strict, but {child.id}'s careful thinking found the honest answer.")
    elif params.mystery == "lost_key":
        world.say(f"The key had slipped behind a stack of books when {suspect.type} bumped the table.")
        world.say(f"{child.id} found it without blame, and the room could open again.")
    elif params.mystery == "strange_note":
        world.say(f"The note had been left by {suspect.type} as a clue for a surprise repair.")
        world.say(f"{child.id} read it aloud, and the mystery turned into a kind plan.")
    else:
        world.say(f"The cookie had been hidden by {suspect.type} to save it for tea.")
        world.say(f"{child.id} smiled, because the answer was small and fair, not cruel.")

    world.say(f"In the end, {child.id} solved the mystery with a little magic and a lot of problem solving.")
    world.say(f"The lecture was over, the question was answered, and the poor child stood a little taller.")
    world.facts["resolved"] = True
    return world


# ---------------------------------------------------------------------------
# Narration helpers
# ---------------------------------------------------------------------------

def choose(seq, rng):
    return seq[rng.randrange(len(seq))]


def build_storyparams(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or choose(list(PLACES), rng)
    mystery = args.mystery or choose(list(MYSTERIES), rng)
    magic = args.magic or choose(list(MAGICS), rng)
    problem = args.problem or choose(list(PROBLEMS), rng)

    if not valid_combo(place, mystery, magic, problem):
        raise StoryError(explain_rejection(place, mystery, magic, problem))

    gender = args.gender or choose(["girl", "boy"], rng)
    child_type = "girl" if gender == "girl" else "boy"
    adult = args.adult or choose(["teacher", "librarian", "neighbor"], rng)
    name = args.name or choose(CHILD_NAMES, rng)
    trait = args.trait or choose(TRAITS, rng)

    return StoryParams(
        place=place,
        mystery=mystery,
        magic=magic,
        problem=problem,
        name=name,
        child_type=child_type,
        adult=adult,
        trait=trait,
    )


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short whodunit story for a child named {f["child"].id} about a poor little {f["child"].type}, a lecture, and a mystery at {f["place"]}.',
        f"Tell a gentle mystery story where {f['child'].id} uses {f['magic'].replace('_', ' ')} to solve {f['mystery'].replace('_', ' ')}.",
        f"Write a child-friendly story that begins with a lecture, includes a clue, and ends with problem solving.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = f["child"]
    adult: Entity = f["adult"]
    mystery = f["mystery"].replace("_", " ")
    magic = f["magic"].replace("_", " ")
    problem = f["problem"].replace("_", " ")
    place = f["place"]

    return [
        QAItem(
            question=f"Who was the story mainly about at {place}?",
            answer=f"The story was about {child.id}, a poor little {child.type} who stayed thoughtful after the lecture.",
        ),
        QAItem(
            question=f"What happened after the lecture that made everyone wonder?",
            answer=f"After the lecture, the {mystery} became the mystery everyone had to solve.",
        ),
        QAItem(
            question=f"How did {child.id} help solve the problem?",
            answer=f"{child.id} used {magic} to find the clue and then used problem solving to explain what really happened.",
        ),
        QAItem(
            question=f"Why did {adult.label} stop worrying at the end?",
            answer=f"{adult.label} stopped worrying because the mystery was solved fairly and the answer made sense.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    magic = f["magic"]
    mystery = f["mystery"]

    qa = []
    if magic == "glow":
        qa.append(QAItem(
            question="What does a glow do in a dark room?",
            answer="A glow makes faint light that helps you see tiny things more clearly.",
        ))
    elif magic == "mirror":
        qa.append(QAItem(
            question="Why can a mirror help in a mystery?",
            answer="A mirror can show something hidden from a different angle.",
        ))
    elif magic == "spark":
        qa.append(QAItem(
            question="What can a spark show?",
            answer="A spark can make a small mark or trail stand out for a moment.",
        ))
    else:
        qa.append(QAItem(
            question="What does a whisper spell do in a story?",
            answer="A whisper spell can help a character notice a quiet clue without scaring anyone.",
        ))

    if mystery == "missing_chalk":
        qa.append(QAItem(
            question="What is chalk used for?",
            answer="Chalk is used to write or draw on a board, and it leaves pale marks.",
        ))
    elif mystery == "lost_key":
        qa.append(QAItem(
            question="What is a key used for?",
            answer="A key is used to open a lock, such as a door or box.",
        ))
    elif mystery == "strange_note":
        qa.append(QAItem(
            question="What is a note?",
            answer="A note is a short message someone writes for another person.",
        ))
    else:
        qa.append(QAItem(
            question="Why do people save cookies for later?",
            answer="People save cookies for later because they want a treat at another time.",
        ))
    return qa


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
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


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
        if e.location:
            bits.append(f"location={e.location}")
        if e.traits:
            bits.append(f"traits={e.traits}")
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
place(P) :- place_fact(P).
mystery(M) :- mystery_fact(M).
magic(G) :- magic_fact(G).
problem(R) :- problem_fact(R).

valid(P,M,G,R) :- place(P), mystery(M), magic(G), problem(R),
                  plausible(P,M), helps(G,M), matches(R,M).

plausible(school, missing_chalk).
plausible(school, lost_key).
plausible(school, strange_note).
plausible(hall, missing_chalk).
plausible(hall, lost_key).
plausible(hall, strange_note).
plausible(library, missing_chalk).
plausible(library, lost_key).
plausible(library, strange_note).
plausible(home, lost_key).
plausible(home, strange_note).
plausible(home, vanished_cookie).
plausible(garden, lost_key).
plausible(garden, strange_note).
plausible(garden, vanished_cookie).

helps(glow, missing_chalk).
helps(glow, lost_key).
helps(mirror, missing_chalk).
helps(mirror, strange_note).
helps(spark, vanished_cookie).
helps(whisper, lost_key).
helps(whisper, strange_note).
helps(whisper, vanished_cookie).

matches(who_moved_it, missing_chalk).
matches(who_moved_it, vanished_cookie).
matches(where_did_it_go, missing_chalk).
matches(where_did_it_go, lost_key).
matches(where_did_it_go, vanished_cookie).
matches(what_left_trace, lost_key).
matches(what_left_trace, strange_note).
matches(why_was_it_hidden, strange_note).
matches(why_was_it_hidden, vanished_cookie).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in PLACES:
        lines.append(asp.fact("place_fact", p))
    for m in MYSTERIES:
        lines.append(asp.fact("mystery_fact", m))
    for g in MAGICS:
        lines.append(asp.fact("magic_fact", g))
    for r in PROBLEMS:
        lines.append(asp.fact("problem_fact", r))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    clingo_set = set(asp_valid_combos())
    python_set = set(
        (p, m, g, r)
        for p in PLACES
        for m in MYSTERIES
        for g in MAGICS
        for r in PROBLEMS
        if valid_combo(p, m, g, r)
    )
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combo() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combo():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


# ---------------------------------------------------------------------------
# Core generation
# ---------------------------------------------------------------------------

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
# CLI
# ---------------------------------------------------------------------------

CURATED = [
    StoryParams(place="school", mystery="missing_chalk", magic="glow", problem="where_did_it_go", name="Mina", child_type="girl", adult="teacher", trait="curious"),
    StoryParams(place="library", mystery="strange_note", magic="mirror", problem="what_left_trace", name="Toby", child_type="boy", adult="librarian", trait="careful"),
    StoryParams(place="home", mystery="vanished_cookie", magic="spark", problem="why_was_it_hidden", name="Iris", child_type="girl", adult="neighbor", trait="brave"),
    StoryParams(place="hall", mystery="lost_key", magic="whisper", problem="who_moved_it", name="Noah", child_type="boy", adult="teacher", trait="patient"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Whodunit-style story world: poor child, lecture, magic, mystery, problem solving.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--magic", choices=MAGICS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--adult", choices=["teacher", "librarian", "neighbor"])
    ap.add_argument("--name")
    ap.add_argument("--trait", choices=TRAITS)
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
    place = args.place or rng.choice(list(PLACES))
    mystery = args.mystery or rng.choice(list(MYSTERIES))
    magic = args.magic or rng.choice(list(MAGICS))
    problem = args.problem or rng.choice(list(PROBLEMS))
    if not valid_combo(place, mystery, magic, problem):
        raise StoryError(explain_rejection(place, mystery, magic, problem))
    gender = args.gender or rng.choice(["girl", "boy"])
    child_type = "girl" if gender == "girl" else "boy"
    adult = args.adult or rng.choice(["teacher", "librarian", "neighbor"])
    name = args.name or rng.choice(CHILD_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, mystery=mystery, magic=magic, problem=problem, name=name, child_type=child_type, adult=adult, trait=trait)


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid combos:\n")
        for p, m, g, r in combos:
            print(f"  {p:8} {m:16} {g:8} {r}")
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.mystery} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
