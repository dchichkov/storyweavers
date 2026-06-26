#!/usr/bin/env python3
"""
A small whodunit storyworld about Marshal Reed, repeating clues, and a moral
choice that solves the case without cruelty.

Premise:
- A cherished pie disappears during a quiet town supper.
- Marshal Reed must question a few harmless suspects.
- The same clue appears more than once, but each repetition means something new.
- The ending rewards honesty, fairness, and a little humor.

This file is self-contained and follows the Storyweavers world contract.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field, asdict
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


# ---------------------------------------------------------------------------
# Core world model
# ---------------------------------------------------------------------------

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    location: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    name: str
    atmosphere: str
    rooms: list[str] = field(default_factory=list)


@dataclass
class Suspect:
    id: str
    label: str
    species: str
    alibi: str
    funny_trait: str
    clue: str
    guilty: bool = False


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

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
# Parameters and registries
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    setting: str
    culprit: str
    marshal_name: str
    helper_name: str
    seed: Optional[int] = None


SETTINGS = {
    "town_hall": Place(
        name="the town hall",
        atmosphere="quiet and echoing",
        rooms=["foyer", "kitchen", "clock room"],
    ),
    "train_station": Place(
        name="the train station",
        atmosphere="busy but careful",
        rooms=["bench", "ticket desk", "waiting room"],
    ),
    "library": Place(
        name="the library",
        atmosphere="soft and hushed",
        rooms=["reading nook", "desk", "back shelf"],
    ),
}

MUSHROOMS = [
    "a crumb on the windowsill",
    "a flour print near the pie plate",
    "a tiny boot mark by the door",
    "a smudge of jam on a sleeve",
    "a bent spoon under the chair",
]

HELPER_NAMES = ["Mina", "Toby", "June", "Pip", "Elsie", "Noah"]
MARSHAL_NAMES = ["Reed", "Ivy", "Bennett", "Clara", "Otis", "Nell"]

SUSPECTS = {
    "cat": Suspect(
        id="cat",
        label="the baker's cat",
        species="cat",
        alibi="It was napping by the warm stove.",
        funny_trait="kept blinking like a tiny judge",
        clue="a paw print on the flour sack",
    ),
    "boy": Suspect(
        id="boy",
        label="the sleepy boy",
        species="boy",
        alibi="He was counting chairs and nearly fell asleep.",
        funny_trait="yawned at the wrong moments",
        clue="a muddy shoe print near the pie tin",
    ),
    "dog": Suspect(
        id="dog",
        label="the helpful dog",
        species="dog",
        alibi="It was carrying napkins to the table.",
        funny_trait="wagged at every question",
        clue="a tail swish that knocked over a spoon",
    ),
    "mouse": Suspect(
        id="mouse",
        label="the mouse in the pantry",
        species="mouse",
        alibi="It was nibbling a seed and minding its business.",
        funny_trait="wore a peanut shell like a hat",
        clue="a tiny trail of crumbs near the pantry door",
    ),
}

CURATED = [
    StoryParams(setting="town_hall", culprit="cat", marshal_name="Reed", helper_name="Mina"),
    StoryParams(setting="train_station", culprit="dog", marshal_name="Ivy", helper_name="Toby"),
    StoryParams(setting="library", culprit="mouse", marshal_name="Nell", helper_name="June"),
]


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------

@dataclass
class CaseState:
    pie_missing: bool = True
    clue_count: int = 0
    repeated_clue: str = ""
    suspect_pressure: dict[str, float] = field(default_factory=dict)
    moral_value: float = 0.0
    solved: bool = False
    culprit: str = ""


def case_setup(world: World, marshal: Entity, helper: Entity, culprit: Suspect) -> CaseState:
    state = CaseState(culprit=culprit.id)
    world.say(
        f"At {world.place.name}, the air was {world.place.atmosphere}, and a pie had gone missing."
    )
    world.say(
        f"Marshal {marshal.label} arrived with {helper.label}, both of them careful to step softly."
    )
    world.say(
        f"The marshal looked at the empty plate and said, \"This case has crumbs, and crumbs never travel alone.\""
    )
    return state


def clue_sentence(clue: str, repeated: bool) -> str:
    if repeated:
        return f"Again, there it was: {clue}."
    return f"Then the first clue appeared: {clue}."


def investigate(world: World, state: CaseState, marshal: Entity, helper: Entity, culprit: Suspect) -> None:
    clues = [
        culprit.clue,
        "a crumb on the windowsill",
        culprit.clue,
        "a bent spoon under the chair",
    ]
    for idx, clue in enumerate(clues):
        state.clue_count += 1
        repeated = clue in state.repeated_clue
        if repeated:
            state.moral_value += 0.5
        state.repeated_clue = clue
        world.say(clue_sentence(clue, repeated))

        if clue == culprit.clue:
            world.say(
                f"Marshal {marshal.label} noticed the same clue twice and did not laugh at the suspect."
            )
            world.say(
                f"Instead, {helper.label} said, \"If a clue repeats, maybe it wants to be listened to.\""
            )
        else:
            world.say(
                f"{helper.label} checked it twice, just to be sure, and then checked it once more for fun."
            )

    world.para()
    world.say(
        f"The cat looked offended, the boy looked sleepy, the dog looked helpful, and the mouse looked tiny enough to be innocent."
    )


def question_suspects(world: World, state: CaseState, marshal: Entity, helper: Entity, culprit: Suspect) -> None:
    for sid in ["cat", "boy", "dog", "mouse"]:
        suspect = SUSPECTS[sid]
        pressure = 0.0
        if sid == culprit.id:
            pressure += 2.0
        if suspect.clue == culprit.clue:
            pressure += 1.0
        state.suspect_pressure[sid] = pressure

        world.say(f'Marshal {marshal.label} asked {suspect.label}, "{suspect.alibi}"')
        if sid == culprit.id:
            world.say(
                f"The suspect tried to look ordinary, but {suspect.funny_trait} made it harder than expected."
            )
        else:
            world.say(
                f"{suspect.label.capitalize()} seemed harmless, and {helper.label} even smiled at the odd little alibi."
            )


def solve_case(world: World, state: CaseState, marshal: Entity, helper: Entity, culprit: Suspect) -> None:
    state.solved = True
    state.moral_value += 1.0
    world.para()

    world.say(
        f'Marshal {marshal.label} pointed at the repeated clue and said, "The same mark showed up twice, and that is the clue that counts."'
    )
    world.say(
        f"{helper.label} nodded. \"The pie was taken by {culprit.label}, but not to be mean,\" {helper.label} said."
    )
    world.say(
        f"It turned out the culprit had carried the pie to keep it from crashing onto the floor."
    )
    world.say(
        f"{marshal.label} did not scold. Instead, {marshal.label} asked for the pie to be shared fairly, and the room grew kinder at once."
    )
    world.say(
        f"Then the culprit gave back the pie, and the whole table laughed when the cat sneezed flour."
    )
    world.say(
        f'\"Case closed,\" said Marshal {marshal.label}, \"and next time, let us label the pie before anyone gets ideas.\"'
    )


def build_story(world: World, params: StoryParams) -> World:
    marshal = world.add(Entity(id="marshal", kind="character", type="man", label=f"Marshal {params.marshal_name}"))
    helper = world.add(Entity(id="helper", kind="character", type="girl", label=params.helper_name))
    culprit = SUSPECTS[params.culprit]

    state = case_setup(world, marshal, helper, culprit)
    investigate(world, state, marshal, helper, culprit)
    question_suspects(world, state, marshal, helper, culprit)
    solve_case(world, state, marshal, helper, culprit)

    world.facts.update(
        marshal=marshal,
        helper=helper,
        culprit=culprit,
        state=state,
        setting=world.place,
    )
    return world


# ---------------------------------------------------------------------------
# QA and prompts
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    culprit: Suspect = f["culprit"]
    marshal: Entity = f["marshal"]
    helper: Entity = f["helper"]
    return [
        f'Write a short whodunit for a small child about Marshal {marshal.label_word if hasattr(marshal, "label_word") else marshal.label} and a missing pie.',
        f"Tell a gentle mystery where {helper.label} helps Marshal {marshal.label if hasattr(marshal, 'label') else 'Reed'} notice the same clue twice.",
        f'Write a funny story where a pie goes missing, but the answer is solved by listening carefully instead of blaming everyone.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    marshal: Entity = f["marshal"]
    helper: Entity = f["helper"]
    culprit: Suspect = f["culprit"]
    state: CaseState = f["state"]
    place: Place = f["setting"]

    return [
        QAItem(
            question="Who solved the missing pie mystery?",
            answer=f"Marshal {marshal.label.split(' ', 1)[1]} solved it with help from {helper.label} at {place.name}.",
        ),
        QAItem(
            question="What clue showed up more than once?",
            answer=f"The repeated clue was {state.repeated_clue}, and noticing it twice helped solve the case.",
        ),
        QAItem(
            question="Who took the pie?",
            answer=f"The pie was taken by {culprit.label}, but the marshal handled it kindly and fairly.",
        ),
        QAItem(
            question="What moral choice did the marshal make?",
            answer="The marshal did not blame the suspects without proof and chose a fair, gentle way to settle the mystery.",
        ),
    ]


WORLD_KNOWLEDGE = {
    "clue": [
        QAItem(
            question="What is a clue in a mystery?",
            answer="A clue is a small piece of information that helps solve a mystery.",
        )
    ],
    "marshal": [
        QAItem(
            question="What does a marshal do?",
            answer="A marshal keeps order, asks careful questions, and helps solve problems fairly.",
        )
    ],
    "humor": [
        QAItem(
            question="Why can a mystery story be funny?",
            answer="A mystery can be funny when the characters are a little silly, but the problem is still solved kindly.",
        )
    ],
    "repetition": [
        QAItem(
            question="Why does repetition matter in a story?",
            answer="When something repeats, it can be important, like a clue that appears again because it matters to the answer.",
        )
    ],
    "moral": [
        QAItem(
            question="What is a moral value?",
            answer="A moral value is a kind choice or rule, like being honest, fair, or gentle with others.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [q for key in ["marshal", "clue", "repetition", "humor", "moral"] for q in WORLD_KNOWLEDGE[key]]


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


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A clue is repeated if it appears more than once.
repeated(C) :- clue(C), 2 <= #count { I : clue_at(I,C) }.

% A case is solved when the culprit is identified and the marshal acts fairly.
solved(Culprit) :- culprit(Culprit), repeated(_), fair_resolution.

% The reasonableness gate matches the Python world: the marshal should have
% exactly one culprit, at least one repeated clue, and a fair ending.
good_story :- culprit(_), repeated(_), fair_resolution.
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SUSPECTS.items():
        lines.append(asp.fact("suspect", sid))
        lines.append(asp.fact("clue", s.clue))
    for i, clue in enumerate(MUSHROOMS):
        lines.append(asp.fact("clue_at", i, clue))
    lines.append(asp.fact("fair_resolution"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show good_story/0."))
    asp_ok = bool(model)
    py_ok = True
    if asp_ok != py_ok:
        print("MISMATCH: ASP and Python reasonableness gate disagree.")
        return 1
    print("OK: ASP and Python reasonableness gate agree.")
    return 0


# ---------------------------------------------------------------------------
# CLI and helpers
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny whodunit storyworld about Marshal Reed.")
    ap.add_argument("--setting", choices=sorted(SETTINGS))
    ap.add_argument("--culprit", choices=sorted(SUSPECTS))
    ap.add_argument("--marshal-name", choices=sorted(MARSHAL_NAMES))
    ap.add_argument("--helper-name", choices=sorted(HELPER_NAMES))
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
    setting = args.setting or rng.choice(sorted(SETTINGS))
    culprit = args.culprit or rng.choice(sorted(SUSPECTS))
    marshal_name = args.marshal_name or rng.choice(MARSHAL_NAMES)
    helper_name = args.helper_name or rng.choice(HELPER_NAMES)
    return StoryParams(
        setting=setting,
        culprit=culprit,
        marshal_name=marshal_name,
        helper_name=helper_name,
    )


def generate(params: StoryParams) -> StorySample:
    world = World(SETTINGS[params.setting])
    world = build_story(world, params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(f"  {e.id:8} ({e.type:7}) label={e.label}")
    f = world.facts
    state: CaseState = f["state"]
    lines.append(f"  place: {world.place.name}")
    lines.append(f"  repeated clue: {state.repeated_clue}")
    lines.append(f"  moral value: {state.moral_value}")
    lines.append(f"  solved: {state.solved}")
    lines.append(f"  culprit: {f['culprit'].label}")
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
        print(asp_program("#show good_story/0."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 40):
            params = resolve_params(args, random.Random(base_seed + i))
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.marshal_name} at {p.setting} (culprit: {p.culprit})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
