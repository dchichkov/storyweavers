#!/usr/bin/env python3
"""
A small detective-story world with rhyme clues, a sung ditty, and a lesson
learned ending.

The seed premise:
- A child detective follows a musical ditty to solve a little mystery.
- The clue is partly a rhyme, partly a practical observation.
- The ending should prove the lesson learned: listen carefully, check facts,
  and be kind when someone makes a mistake.

This file is self-contained and uses a tiny simulation to drive the prose.
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    hidden: bool = False
    found: bool = False
    lost: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def is_character(self) -> bool:
        return self.kind == "character"


@dataclass
class Case:
    mystery: str
    missing: str
    hide_place: str
    clue_rhyme: str
    clue_plain: str
    twist: str
    lesson: str


@dataclass
class StoryParams:
    case: str
    detective_name: str
    detective_type: str
    helper_name: str
    helper_type: str
    seed: Optional[int] = None


class World:
    def __init__(self, case: Case) -> None:
        self.case = case
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[str] = set()

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
# Registries
# ---------------------------------------------------------------------------

CASES = {
    "missing_cookie": Case(
        mystery="the missing cookie",
        missing="cookie",
        hide_place="under the blue teacup",
        clue_rhyme="If it's sweet and neat, check the seat; if it's crumbly, look where cups meet.",
        clue_plain="A few crumbs pointed toward the table corner near the teacup.",
        twist="the younger helper had moved it while setting the table",
        lesson="always look for real clues before blaming someone",
    ),
    "lost_key": Case(
        mystery="the lost key",
        missing="key",
        hide_place="inside the flowerpot",
        clue_rhyme="If it clicks and glints, check the plants; if it vanished quick, look where dirt can cling.",
        clue_plain="A muddy little mark led to the flowerpot by the porch.",
        twist="the key had slipped out of a pocket during play",
        lesson="a careful eye beats a rushed guess",
    ),
    "missing_toy": Case(
        mystery="the missing toy car",
        missing="toy car",
        hide_place="behind the storybook box",
        clue_rhyme="If it rolls and squeaks, check the shelves; if it disappears fast, look where boxes rest.",
        clue_plain="A tiny wheel mark curved toward the stack of books.",
        twist="the helper tucked it away so it would not get stepped on",
        lesson="kind questions solve more than loud accusations",
    ),
}

DETECTIVE_NAMES = ["Mia", "Leo", "Nora", "Ben", "Ava", "Zoe", "Finn", "Ella"]
HELPER_NAMES = ["Toby", "Mila", "Owen", "Ivy", "Max", "Ruby", "Noah", "Penny"]


# ---------------------------------------------------------------------------
# Core story simulation
# ---------------------------------------------------------------------------

def make_world(params: StoryParams) -> World:
    case = CASES[params.case]
    world = World(case)

    detective = world.add(Entity(
        id=params.detective_name,
        kind="character",
        type=params.detective_type,
        label="the detective",
    ))
    helper = world.add(Entity(
        id=params.helper_name,
        kind="character",
        type=params.helper_type,
        label="the helper",
    ))
    missing = world.add(Entity(
        id="missing_item",
        type="thing",
        label=case.missing,
        phrase=f"the missing {case.missing}",
        hidden=True,
        lost=True,
    ))

    world.facts.update(
        detective=detective,
        helper=helper,
        missing=missing,
        case=case,
    )

    # Act 1: setup
    world.say(f"{detective.id} was a little detective who loved solving small mysteries.")
    world.say(f"One afternoon, {detective.id} heard a tiny ditty drifting through the room:")
    world.say(f'"{case.clue_rhyme}"')

    world.para()
    world.say(f"That was the kind of rhyme {detective.id} liked best, because it could hide a clue.")
    world.say(f"{helper.id} frowned and said the {case.mystery} had gone missing.")

    # Act 2: investigation
    world.para()
    detective.memes["curiosity"] = 1
    detective.memes["focus"] = 1
    helper.memes["worry"] = 1

    world.say(f"{detective.id} listened again and looked around the room, not just at the noise.")
    world.say(case.clue_plain)
    world.say(f"Then {detective.id} followed the clue to {case.hide_place}.")

    # Solve the case
    if "flowerpot" in case.hide_place:
        missing.hidden = False
        missing.found = True
    elif "teacup" in case.hide_place:
        missing.hidden = False
        missing.found = True
    else:
        missing.hidden = False
        missing.found = True

    world.facts["found_place"] = case.hide_place
    world.facts["twist"] = case.twist

    world.para()
    world.say(f"There it was: {case.twist}.")
    world.say(f"The missing {case.missing} was found {case.hide_place}, safe and sound.")

    # Act 3: lesson learned
    detective.memes["joy"] = 1
    helper.memes["relief"] = 1
    detective.memes["lesson_learned"] = 1
    world.para()
    world.say(f"{detective.id} smiled and said, \"The best detective trick is to listen carefully and check the facts.\"")
    world.say(f"{helper.id} nodded, and both of them laughed because the mystery was small, but the lesson was big.")
    world.say(f"From then on, {detective.id} remembered to {case.lesson}.")

    world.facts["lesson"] = case.lesson
    return world


# ---------------------------------------------------------------------------
# Story text helpers
# ---------------------------------------------------------------------------

def story_intro_case(world: World) -> str:
    return f"{world.facts['detective'].id} heard a ditty about {world.facts['case'].mystery}."


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    detective = f["detective"]
    helper = f["helper"]
    case: Case = f["case"]
    return [
        f"Write a short detective story for a young child that includes a ditty and the word 'ditty'.",
        f"Tell a gentle mystery where {detective.id} follows a rhyme clue to find {case.mystery}.",
        f"Write a child-facing detective story with a clear clue, a simple twist, and a lesson learned ending.",
        f"Include a rhyme, a solved mystery, and a kind message for {helper.id} and {detective.id}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    detective = f["detective"]
    helper = f["helper"]
    case: Case = f["case"]
    found_place = f["found_place"]
    return [
        QAItem(
            question=f"What did {detective.id} hear that started the mystery?",
            answer=f"{detective.id} heard a tiny ditty with a rhyme clue about {case.mystery}.",
        ),
        QAItem(
            question=f"Where was the missing {case.missing} found?",
            answer=f"It was found {found_place}, where the clue had led {detective.id}.",
        ),
        QAItem(
            question=f"What did {detective.id} learn by the end of the story?",
            answer=f"{detective.id} learned that {case.lesson}.",
        ),
        QAItem(
            question=f"How did {helper.id} feel after the mystery was solved?",
            answer=f"{helper.id} felt relieved and happy when the missing {case.missing} was found.",
        ),
    ]


KNOWLEDGE = {
    "ditty": [
        QAItem(
            question="What is a ditty?",
            answer="A ditty is a short, simple song or tune that is easy to remember.",
        )
    ],
    "rhyme": [
        QAItem(
            question="What is a rhyme?",
            answer="A rhyme is when words sound alike at the end, like cat and hat.",
        )
    ],
    "detective": [
        QAItem(
            question="What does a detective do?",
            answer="A detective looks for clues, asks careful questions, and tries to solve a mystery.",
        )
    ],
    "lesson": [
        QAItem(
            question="What does it mean to learn a lesson?",
            answer="Learning a lesson means understanding something important that can help you do better next time.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    out: list[QAItem] = []
    out.extend(KNOWLEDGE["ditty"])
    out.extend(KNOWLEDGE["rhyme"])
    out.extend(KNOWLEDGE["detective"])
    out.extend(KNOWLEDGE["lesson"])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.hidden:
            bits.append("hidden=True")
        if e.found:
            bits.append("found=True")
        if e.lost:
            bits.append("lost=True")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:12} ({e.kind:9}) {' '.join(bits)}")
    lines.append(f"  facts: {sorted(world.facts.keys())}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
case(C) :- case_name(C).
solved(C) :- case(C), found(C).

has_rhyme(C) :- clue_rhyme(C, _).
has_lesson(C) :- lesson(C, _).

valid_story(C) :- case(C), has_rhyme(C), has_lesson(C), solved(C).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for cid, case in CASES.items():
        lines.append(asp.fact("case_name", cid))
        lines.append(asp.fact("clue_rhyme", cid, case.clue_rhyme))
        lines.append(asp.fact("lesson", cid, case.lesson))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_cases() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/1."))
    return sorted(set(asp.atoms(model, "valid_story")))


# ---------------------------------------------------------------------------
# Params and generation
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    case: str
    detective_name: str
    detective_type: str
    helper_name: str
    helper_type: str
    seed: Optional[int] = None


def valid_cases() -> list[str]:
    return sorted(CASES.keys())


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    case = args.case or rng.choice(valid_cases())
    detective_name = args.detective_name or rng.choice(DETECTIVE_NAMES)
    helper_name = args.helper_name or rng.choice([n for n in HELPER_NAMES if n != detective_name])

    if args.detective_type and args.detective_type not in {"girl", "boy"}:
        raise StoryError("detective type must be girl or boy")
    if args.helper_type and args.helper_type not in {"girl", "boy"}:
        raise StoryError("helper type must be girl or boy")

    detective_type = args.detective_type or rng.choice(["girl", "boy"])
    helper_type = args.helper_type or rng.choice(["girl", "boy"])

    if detective_name == helper_name:
        raise StoryError("detective and helper must be different characters")

    return StoryParams(
        case=case,
        detective_name=detective_name,
        detective_type=detective_type,
        helper_name=helper_name,
        helper_type=helper_type,
    )


def generate(params: StoryParams) -> StorySample:
    world = make_world(params)
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
    StoryParams(case="missing_cookie", detective_name="Mia", detective_type="girl", helper_name="Toby", helper_type="boy"),
    StoryParams(case="lost_key", detective_name="Leo", detective_type="boy", helper_name="Ivy", helper_type="girl"),
    StoryParams(case="missing_toy", detective_name="Nora", detective_type="girl", helper_name="Max", helper_type="boy"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Detective story world with a ditty, rhyme clues, and lesson learned.")
    ap.add_argument("--case", choices=valid_cases())
    ap.add_argument("--detective-name")
    ap.add_argument("--detective-type", choices=["girl", "boy"])
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-type", choices=["girl", "boy"])
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


def asp_verify() -> int:
    import asp
    py = {(cid,) for cid in valid_cases()}
    clingo = set(asp.atoms(asp.one_model(asp_program("#show valid_story/1.")), "valid_story"))
    if py == clingo:
        print(f"OK: clingo gate matches Python story cases ({len(py)} cases).")
        return 0
    print("MISMATCH between clingo and Python cases:")
    print("  only in python:", sorted(py - clingo))
    print("  only in clingo:", sorted(clingo - py))
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        stories = asp_valid_cases()
        print(f"{len(stories)} compatible story cases:\n")
        for (cid,) in stories:
            print(f"  {cid}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.case} — {p.detective_name} and {p.helper_name}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
