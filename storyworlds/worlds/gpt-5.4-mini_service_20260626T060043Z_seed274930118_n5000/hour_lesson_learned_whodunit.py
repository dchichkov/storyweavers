#!/usr/bin/env python3
"""
A small whodunit story world about a missing hour and a lesson learned.

Premise:
- A careful child notices that one hour from a schedule has gone missing.
- The story follows clue gathering, a mistaken suspicion, and a reveal.
- The lesson learned is that checking the obvious place and asking kindly
  solves the mystery faster than blaming someone.

This world is intentionally compact and state-driven: the same cast, objects,
and clues produce a narrow set of plausible stories with good causal shape.
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
# Core world model
# ---------------------------------------------------------------------------

@dataclass
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    type: str = "thing"
    owner: Optional[str] = None
    location: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "sister"}
        male = {"boy", "father", "man", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class World:
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

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


# ---------------------------------------------------------------------------
# Parameters and registries
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    child_name: str
    child_type: str
    helper_name: str
    helper_type: str
    hour_label: str
    clue_label: str
    seed: Optional[int] = None


PLACES = {
    "kitchen": "the kitchen",
    "classroom": "the classroom",
    "library": "the library",
    "hallway": "the hallway",
}

CHILDREN = {
    "girl": ["Mina", "Lina", "Nora", "Tia"],
    "boy": ["Owen", "Milo", "Eli", "Noah"],
}

HELPERS = {
    "mother": "mother",
    "father": "father",
    "teacher": "teacher",
    "librarian": "librarian",
}

HOURS = [
    "the missing hour",
    "the late hour",
    "the quiet hour",
]

CLUES = {
    "clock": "clock",
    "drawer": "drawer",
    "chair": "chair",
    "bookmark": "bookmark",
}

DEFAULT_TRAIT = "careful"


# ---------------------------------------------------------------------------
# Helper text
# ---------------------------------------------------------------------------

def setting_line(place: str) -> str:
    return {
        "kitchen": "The room smelled like toast and paper, and a wall clock ticked softly.",
        "classroom": "The desks were neat, and the clock over the board looked very important.",
        "library": "The shelves stood straight and quiet, and even the clock seemed to whisper.",
        "hallway": "The hallway was long and bright, with a clock at the far end and doors on each side.",
    }[place]


def hour_phrase(label: str) -> str:
    return {
        "the missing hour": "one whole hour from the plan",
        "the late hour": "the hour that made the schedule slip",
        "the quiet hour": "the calm hour everyone expected",
    }[label]


# ---------------------------------------------------------------------------
# Story engine
# ---------------------------------------------------------------------------

def tell(world: World, params: StoryParams) -> World:
    child = world.add(Entity(
        id=params.child_name,
        kind="character",
        label=params.child_name,
        type=params.child_type,
        location=world.place,
        memes={"worry": 0.0, "hope": 0.0, "relief": 0.0, "suspicion": 0.0},
    ))
    helper = world.add(Entity(
        id=params.helper_name,
        kind="character",
        label=params.helper_name,
        type=params.helper_type,
        location=world.place,
        memes={"calm": 0.0, "help": 0.0},
    ))
    schedule = world.add(Entity(
        id="schedule",
        kind="thing",
        label="schedule page",
        type="paper",
        owner=child.id,
        location=world.place,
        meters={"order": 1.0},
    ))
    clock = world.add(Entity(
        id="clock",
        kind="thing",
        label="clock",
        type="clock",
        location=world.place,
        meters={"tick": 1.0},
    ))
    clue = world.add(Entity(
        id=params.clue_label,
        kind="thing",
        label=params.clue_label,
        type=params.clue_label,
        location=world.place,
    ))

    world.facts.update(child=child, helper=helper, schedule=schedule, clock=clock, clue=clue, params=params)

    world.say(
        f"{child.id} was a careful child who liked to keep every minute in place. "
        f"{setting_line(world.place)}"
    )
    world.say(
        f"One afternoon, {child.id} looked at {child.pronoun('possessive')} page and frowned. "
        f"{hour_phrase(params.hour_label).capitalize()} was not where it should have been."
    )

    world.para()
    child.memes["worry"] += 1.0
    child.memes["suspicion"] += 1.0
    world.say(
        f"{child.id} checked the desk, the chair, and the floor. "
        f"{child.pronoun().capitalize()} saw a {params.clue_label} near the clock and thought, "
        f"for a moment, that someone had taken the hour on purpose."
    )
    world.say(
        f"But {helper.id} came closer and said, "
        f'"Let us not accuse anyone yet. A mystery is easier when we follow the clues."'
    )
    helper.memes["calm"] += 1.0

    world.para()
    world.say(
        f"They looked under the {params.clue_label}, behind the schedule page, and beside the clock. "
        f"There, tucked in the safest corner, was the missing hour."
    )
    child.memes["hope"] += 1.0
    child.memes["worry"] = 0.0
    child.memes["relief"] += 1.0
    helper.memes["help"] += 1.0
    world.say(
        f"It had never been stolen at all; it had simply slipped out of sight when the page turned. "
        f"{child.id} felt {child.pronoun('possessive')} cheeks grow warm."
    )
    world.say(
        f"{child.id} apologized for the quick blame, and {helper.id} smiled. "
        f'"The lesson learned," {helper.pronoun().capitalize()} said, '
        f'"is to look carefully and ask kindly before making a guess."'
    )

    world.para()
    world.say(
        f"After that, {child.id} put the hour back into the plan. "
        f"The clock kept ticking, the page stayed tidy, and the whole room felt lighter."
    )
    world.say(
        f"{child.id} remembered that a good detective does not just search fast; "
        f"{child.pronoun().capitalize()} searches fair."
    )
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    return [
        f'Write a whodunit story for a young child about {p.hour_label} in {world.place}.',
        f"Tell a mystery where {p.child_name} thinks someone stole an hour, but the truth is simple.",
        f'Write a gentle detective story with the phrase "lesson learned" and the word "hour".',
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    child: Entity = world.facts["child"]
    helper: Entity = world.facts["helper"]
    clue: Entity = world.facts["clue"]

    return [
        QAItem(
            question=f"What was missing in the story?",
            answer=f"One hour was missing from the plan, and {child.id} worried it had been taken away.",
        ),
        QAItem(
            question=f"Who helped {child.id} solve the mystery?",
            answer=f"{helper.id} helped by staying calm and telling {child.id} to follow the clues.",
        ),
        QAItem(
            question=f"What clue did {child.id} notice near the clock?",
            answer=f"{child.id} noticed a {clue.label} near the clock, which helped point the search in the right place.",
        ),
        QAItem(
            question=f"What lesson did {child.id} learn?",
            answer="The lesson learned was to look carefully and ask kindly before blaming anyone.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an hour?",
            answer="An hour is a unit of time. It is a little longer than a short story and much shorter than a day.",
        ),
        QAItem(
            question="What does a clock do?",
            answer="A clock helps people tell time by counting minutes and hours.",
        ),
        QAItem(
            question="Why should people ask kindly when they are unsure?",
            answer="Asking kindly helps people find the truth without hurting feelings or making a wrong guess too fast.",
        ),
    ]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
place(kitchen; classroom; library; hallway).
child(girl; boy).
helper(mother; father; teacher; librarian).
hour(missing; late; quiet).
clue(clock; drawer; chair; bookmark).

valid(P, C, H, L) :- place(P), child(C), helper(H), clue(L).
#show valid/4.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for c in CHILDREN:
        lines.append(asp.fact("child", c))
    for h in HELPERS:
        lines.append(asp.fact("helper", h))
    for hr in HOURS:
        lines.append(asp.fact("hour", hr.replace("the ", "").replace(" ", "_")))
    for cl in CLUES:
        lines.append(asp.fact("clue", cl))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def reasonableness_gate(params: StoryParams) -> None:
    if params.place not in PLACES:
        raise StoryError("Unknown place.")
    if params.child_type not in CHILDREN:
        raise StoryError("Unknown child type.")
    if params.helper_type not in HELPERS:
        raise StoryError("Unknown helper type.")
    if params.hour_label not in HOURS:
        raise StoryError("Unknown hour label.")
    if params.clue_label not in CLUES:
        raise StoryError("Unknown clue label.")


def asp_verify() -> int:
    py = set((p, c, h, l) for p in PLACES for c in CHILDREN for h in HELPERS for l in CLUES)
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches Python gate ({len(py)} combos).")
        return 0
    print("MISMATCH between ASP and Python:")
    print("only in ASP:", sorted(cl - py))
    print("only in Python:", sorted(py - cl))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Whodunit story world about a missing hour and a lesson learned.")
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--child-type", choices=sorted(CHILDREN))
    ap.add_argument("--helper-type", choices=sorted(HELPERS))
    ap.add_argument("--hour-label", choices=HOURS)
    ap.add_argument("--clue-label", choices=sorted(CLUES))
    ap.add_argument("--name")
    ap.add_argument("--helper-name")
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
    child_type = args.child_type or rng.choice(list(CHILDREN))
    helper_type = args.helper_type or rng.choice(list(HELPERS))
    hour_label = args.hour_label or rng.choice(HOURS)
    clue_label = args.clue_label or rng.choice(list(CLUES))
    child_name = args.name or rng.choice(CHILDREN[child_type])
    helper_name = args.helper_name or helper_type.capitalize()

    params = StoryParams(
        place=place,
        child_name=child_name,
        child_type=child_type,
        helper_name=helper_name,
        helper_type=helper_type,
        hour_label=hour_label,
        clue_label=clue_label,
    )
    reasonableness_gate(params)
    return params


def generate(params: StoryParams) -> StorySample:
    world = World(place=PLACES[params.place])
    world = tell(world, params)
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
    for e in world.entities.values():
        bits = []
        if e.location:
            bits.append(f"location={e.location}")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== generation prompts =="]
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


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams("library", "Mina", "girl", "Librarian", "librarian", "the missing hour", "bookmark"),
    StoryParams("classroom", "Owen", "boy", "Teacher", "teacher", "the quiet hour", "drawer"),
    StoryParams("kitchen", "Lina", "girl", "Mother", "mother", "the late hour", "clock"),
    StoryParams("hallway", "Eli", "boy", "Father", "father", "the missing hour", "chair"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible story skeletons:")
        for c in combos:
            print(" ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(100, args.n * 50):
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
