#!/usr/bin/env python3
"""
storyworlds/worlds/poem_trade_student_school_library_reconciliation_bravery.py
=============================================================================

A small heartwarming storyworld set in a school library.

Seed premise:
- A student loves a poem and wants to trade something for a better way to share it.
- A misunderstanding causes a little hurt.
- Bravery helps the student speak honestly.
- Reconciliation turns the library into a kinder place by the end.

This script is self-contained and follows the Storyweavers storyworld contract.
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
# Domain data
# ---------------------------------------------------------------------------

@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Setting:
    place: str = "the school library"
    afford_trade: bool = True
    afford_reading: bool = True


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    mess: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    region: str = "torso"


@dataclass
class TradeItem:
    label: str
    phrase: str
    value: str
    kind: str = "gift"


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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
# Registries
# ---------------------------------------------------------------------------

SETTING = Setting(place="the school library")

ACTIVITIES = {
    "poem": Activity(
        id="poem",
        verb="share a poem",
        gerund="sharing a poem",
        mess="quiet",
        keyword="poem",
        tags={"poem", "reading"},
    ),
    "trade": Activity(
        id="trade",
        verb="make a trade",
        gerund="trading carefully",
        mess="tension",
        keyword="trade",
        tags={"trade"},
    ),
}

PRIZES = {
    "book": Prize(
        label="library book",
        phrase="a borrowed library book",
        type="book",
        region="torso",
    ),
    "poem_card": Prize(
        label="poem card",
        phrase="a neat poem card with glittery letters",
        type="card",
        region="torso",
    ),
}

TRADE_ITEMS = {
    "bookmark": TradeItem(
        label="bookmark",
        phrase="a handmade paper bookmark",
        value="small and kind",
    ),
    "sticker": TradeItem(
        label="sticker",
        phrase="a shiny star sticker",
        value="bright and cheerful",
    ),
    "pencil": TradeItem(
        label="pencil",
        phrase="a perfectly sharpened pencil",
        value="useful and neat",
    ),
}

NAMES = ["Maya", "Noah", "Lina", "Eli", "Ava", "Theo", "Nina", "Sam"]
FRIEND_NAMES = ["Jun", "Iris", "Owen", "Tess", "Milo", "Zara"]
TRAITS = ["quiet", "curious", "gentle", "nervous", "brave", "kind"]


# ---------------------------------------------------------------------------
# Story parameters
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    friend: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------

def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place_key, setting in {"library": SETTING}.items():
        for act in ACTIVITIES:
            for prize in PRIZES:
                if place_key == "library" and act in {"poem", "trade"}:
                    combos.append((place_key, act, prize))
    return combos


def explain_rejection(activity: Activity, prize: Prize) -> str:
    return (
        f"(No story: {activity.verb} does not fit this school library setup with "
        f"{prize.phrase}. Try a poem or trade scene in the library instead.)"
    )


# ---------------------------------------------------------------------------
# World simulation
# ---------------------------------------------------------------------------

def build_world(params: StoryParams) -> World:
    world = World(SETTING)
    student = world.add(Entity(
        id=params.name,
        kind="character",
        type="student",
        label="student",
        memes={"hope": 0.0, "bravery": 0.0, "hurt": 0.0, "care": 0.0, "reconciliation": 0.0},
    ))
    friend = world.add(Entity(
        id=params.friend,
        kind="character",
        type="student",
        label="friend",
        memes={"hope": 0.0, "bravery": 0.0, "hurt": 0.0, "care": 0.0, "reconciliation": 0.0},
    ))
    prize = world.add(Entity(
        id="prize",
        type=PRIZES[params.prize].type,
        label=PRIZES[params.prize].label,
        phrase=PRIZES[params.prize].phrase,
        owner=student.id,
        caretaker="librarian",
    ))
    librarian = world.add(Entity(
        id="librarian",
        kind="character",
        type="adult",
        label="the librarian",
        memes={"calm": 1.0, "care": 1.0},
    ))
    trade_item = world.add(Entity(
        id="trade_item",
        type="thing",
        label=TRADE_ITEMS["bookmark"].label,
        phrase=TRADE_ITEMS["bookmark"].phrase,
        owner=friend.id,
    ))
    world.facts.update(student=student, friend=friend, prize=prize, librarian=librarian, trade_item=trade_item)
    return world


def tell_story(world: World, params: StoryParams) -> None:
    student: Entity = world.facts["student"]
    friend: Entity = world.facts["friend"]
    prize: Entity = world.facts["prize"]
    librarian: Entity = world.facts["librarian"]
    trade_item: Entity = world.facts["trade_item"]
    act = ACTIVITIES[params.activity]

    student.memes["hope"] += 1
    world.say(
        f"{student.id} was a {params.trait} student who loved the quiet of {world.setting.place}."
    )
    world.say(
        f"One afternoon, {student.id} wanted to {act.verb} and make something special for {prize.label} day."
    )
    world.say(
        f"{student.id} also liked how {trade_item.phrase} could be traded between friends like a small promise."
    )

    world.para()
    friend.memes["hurt"] += 1
    student.memes["hope"] += 1
    world.say(
        f"At a reading table, {student.id} and {friend.id} reached for the same poem card at once."
    )
    world.say(
        f"{friend.id} thought {student.id} had taken it on purpose, and the room felt suddenly too still."
    )
    world.say(
        f"The librarian looked up gently, because even a tiny mix-up can make a big feeling."
    )

    world.para()
    student.memes["bravery"] += 1
    world.say(
        f"{student.id} took a slow breath and found brave words."
    )
    world.say(
        f'"I did not mean to take it away," {student.id} said. "I wanted to trade, not to hurt {friend.pronoun("object")}."'
    )
    friend.memes["care"] += 1
    friend.memes["hurt"] = 0.0
    world.say(
        f"{friend.id}'s face softened, because honest words can open a closed heart."
    )
    world.say(
        f"{friend.id} nodded and offered the {trade_item.label}, and the two students shared the poem together."
    )

    world.para()
    student.memes["reconciliation"] += 1
    friend.memes["reconciliation"] += 1
    world.say(
        f"The librarian smiled when the students decided to read the poem aloud as a team."
    )
    world.say(
        f"{student.id} read the first lines, {friend.id} read the next ones, and the words sounded warmer than before."
    )
    world.say(
        f"In the end, the {trade_item.label} sat tucked into the borrowed book, and both students left the school library with lighter steps and kinder hearts."
    )

    world.facts["resolved"] = True
    world.facts["activity"] = act


# ---------------------------------------------------------------------------
# Question answering
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    student = f["student"]
    friend = f["friend"]
    return [
        "Write a heartwarming story set in a school library where a student and a friend repair a misunderstanding with bravery.",
        f"Tell a gentle story about {student.id} and {friend.id} in the school library, including a poem and a trade.",
        "Write a child-friendly reconciliation story where honest words make two students friends again.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    student = f["student"]
    friend = f["friend"]
    prize = f["prize"]
    trade_item = f["trade_item"]
    return [
        QAItem(
            question=f"Where does the story take place?",
            answer=f"It takes place in the school library, where the shelves are quiet and the tables are neat.",
        ),
        QAItem(
            question=f"What did {student.id} want to do at first?",
            answer=f"{student.id} wanted to share a poem and make a small trade in the library.",
        ),
        QAItem(
            question=f"What caused the hurt feeling between {student.id} and {friend.id}?",
            answer=f"They both reached for the poem card at the same time, and {friend.id} thought {student.id} had taken it on purpose.",
        ),
        QAItem(
            question=f"How did {student.id} show bravery?",
            answer=f"{student.id} showed bravery by speaking honestly and saying it was a mistake, not an act of hurting anyone.",
        ),
        QAItem(
            question=f"What helped the students reconcile?",
            answer=f"Honest words, gentle listening, and sharing the poem together helped them reconcile.",
        ),
        QAItem(
            question=f"What trade item was offered?",
            answer=f"{friend.id} offered {trade_item.phrase}, which helped turn the moment into a kinder one.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a poem?",
            answer="A poem is a piece of writing that can use rhythm, rhyme, and careful words to share a feeling or picture.",
        ),
        QAItem(
            question="What does it mean to trade something?",
            answer="To trade means to give one thing and get another thing in return, usually by agreeing with someone else.",
        ),
        QAItem(
            question="What is bravery?",
            answer="Bravery means doing something difficult or scary in a careful, honest way.",
        ),
        QAItem(
            question="What is reconciliation?",
            answer="Reconciliation is when people who had a problem make peace again and feel kind toward each other.",
        ),
    ]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
place(library).
activity(poem).
activity(trade).
prize(book).
prize(poem_card).

story_ok(P, A, R) :- place(P), activity(A), prize(R).
featured(A) :- activity(A), A = poem.
featured(A) :- activity(A), A = trade.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = [
        asp.fact("place", "library"),
        asp.fact("setting", "school_library"),
        asp.fact("activity", "poem"),
        asp.fact("activity", "trade"),
        asp.fact("prize", "book"),
        asp.fact("prize", "poem_card"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show story_ok/3."))
    return sorted(set(asp.atoms(model, "story_ok")))


def asp_verify() -> int:
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


# ---------------------------------------------------------------------------
# Standard interface
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming school-library storyworld.")
    ap.add_argument("--place", choices=["library"])
    ap.add_argument("--activity", choices=sorted(ACTIVITIES))
    ap.add_argument("--prize", choices=sorted(PRIZES))
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--friend", choices=FRIEND_NAMES)
    ap.add_argument("--trait", choices=TRAITS)
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
    if args.activity and args.activity not in ACTIVITIES:
        raise StoryError("Unknown activity.")
    if args.prize and args.prize not in PRIZES:
        raise StoryError("Unknown prize.")

    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == "library")
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    _, activity, prize = rng.choice(sorted(combos))
    name = args.name or rng.choice(NAMES)
    friend = args.friend or rng.choice(FRIEND_NAMES)
    while friend == name:
        friend = rng.choice(FRIEND_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(
        place="library",
        activity=activity,
        prize=prize,
        name=name,
        friend=friend,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    tell_story(world, params)
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
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


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
    StoryParams(place="library", activity="poem", prize="poem_card", name="Maya", friend="Jun", trait="brave"),
    StoryParams(place="library", activity="trade", prize="book", name="Noah", friend="Iris", trait="gentle"),
    StoryParams(place="library", activity="poem", prize="book", name="Lina", friend="Tess", trait="nervous"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show story_ok/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible story combos:\n")
        for p, a, r in combos:
            print(f"  {p:8} {a:8} {r:10}")
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
            header = f"### {p.name}: {p.activity} in the school library"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
