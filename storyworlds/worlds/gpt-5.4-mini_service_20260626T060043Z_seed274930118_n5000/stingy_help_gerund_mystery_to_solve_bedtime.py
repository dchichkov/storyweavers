#!/usr/bin/env python3
"""
Bedtime mystery storyworld: a small child, a stingy helper, and a gentle puzzle
to solve before sleep.

The seed premise:
- A child gets ready for bed.
- Something important goes missing or feels wrong.
- A stingy character is reluctant to help at first.
- The child and a helper solve the mystery together.
- The ending proves the bedtime change.

This world keeps the prose child-facing, concrete, and state-driven. It also
includes an ASP twin for the basic reasonableness gate and supports the shared
Storyweavers CLI contract.
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
# World data
# ---------------------------------------------------------------------------

@dataclass
class Person:
    id: str
    role: str
    name: str
    adjective: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    holds: list[str] = field(default_factory=list)

    def pronoun(self, case: str = "subject") -> str:
        if self.role in {"girl", "mother", "grandmother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.role in {"boy", "father", "grandfather", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def subj(self) -> str:
        return self.pronoun("subject").capitalize()


@dataclass
class Item:
    id: str
    label: str
    owner: str
    place: str = ""
    hidden: bool = False
    meters: dict[str, float] = field(default_factory=dict)


@dataclass
class Room:
    name: str
    cozy: bool = True
    affordances: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    room: str
    mystery: str
    child_name: str
    child_role: str
    helper_role: str
    stingy_role: str
    seed: Optional[int] = None


class World:
    def __init__(self, room: Room) -> None:
        self.room = room
        self.people: dict[str, Person] = {}
        self.items: dict[str, Item] = {}
        self.lines: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

    def add_person(self, p: Person) -> Person:
        self.people[p.id] = p
        return p

    def add_item(self, it: Item) -> Item:
        self.items[it.id] = it
        return it

    def say(self, text: str) -> None:
        if text:
            self.lines[-1].append(text)

    def para(self) -> None:
        if self.lines[-1]:
            self.lines.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.lines if p)

    def copy(self) -> "World":
        import copy as _copy
        w = World(self.room)
        w.people = _copy.deepcopy(self.people)
        w.items = _copy.deepcopy(self.items)
        w.lines = [[]]
        w.facts = dict(self.facts)
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

ROOMS = {
    "nursery": Room("the nursery", cozy=True, affordances={"search", "read", "listen"}),
    "bedroom": Room("the bedroom", cozy=True, affordances={"search", "read", "listen"}),
    "hall": Room("the hallway", cozy=True, affordances={"search", "read", "listen"}),
}

MYSTERIES = {
    "lost_blanket": {
        "label": "the blanket",
        "clue": "a fluffy thread",
        "missing": "under the bed",
        "solution": "found it tucked beside the pillow",
        "help_gerund": "helping search",
        "risk": "cold",
        "ending": "The blanket was back where it belonged, and the bed felt warm again.",
    },
    "missing_bunny": {
        "label": "the bunny toy",
        "clue": "a tiny button",
        "missing": "in the toy basket",
        "solution": "found it hiding behind a storybook",
        "help_gerund": "helping look",
        "risk": "worry",
        "ending": "The bunny toy was safe again, and the pillow looked friendly.",
    },
    "quiet_nightlight": {
        "label": "the nightlight",
        "clue": "a warm glow",
        "missing": "by the lamp cord",
        "solution": "found it switched on near the shelf",
        "help_gerund": "helping check",
        "risk": "darkness",
        "ending": "The nightlight glowed softly, and the room felt brave and calm.",
    },
}

GENTLE_NAMES = ["Mia", "Leo", "Nora", "Ben", "Lily", "Sam", "Ava", "Theo"]
HELPER_NAMES = ["Mum", "Dad", "Gran", "Auntie"]
TRAITS = ["sleepy", "curious", "gentle", "brave", "quiet"]

ASP_RULES = r"""
mystery(M) :- target(M).
help_gerund(M, G) :- target(M), helpword(M, G).
valid_story(Room, M) :- room(Room), mystery(M), afford(Room, search), afford(Room, read), afford(Room, listen).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for rid, room in ROOMS.items():
        lines.append(asp.fact("room", rid))
        for a in sorted(room.affordances):
            lines.append(asp.fact("afford", rid, a))
    for mid in MYSTERIES:
        lines.append(asp.fact("target", mid))
    for mid, myst in MYSTERIES.items():
        lines.append(asp.fact("helpword", mid, myst["help_gerund"]))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------

def valid_combos() -> list[tuple[str, str]]:
    out = []
    for room_id, room in ROOMS.items():
        if {"search", "read", "listen"}.issubset(room.affordances):
            for mystery_id in MYSTERIES:
                out.append((room_id, mystery_id))
    return out


def explain_rejection(room: str, mystery: str) -> str:
    return f"(No story: the room '{room}' and mystery '{mystery}' do not make a bedtime mystery.)"


# ---------------------------------------------------------------------------
# Story generation
# ---------------------------------------------------------------------------

def build_story(world: World) -> None:
    child = world.people["child"]
    helper = world.people["helper"]
    stingy = world.people["stingy"]
    mystery = world.facts["mystery_data"]
    item = world.items["important"]

    world.say(
        f"{child.name} was a {child.adjective} little {child.role} getting ready for bed in {world.room.name}."
    )
    world.say(
        f"{child.subj()} loved the soft blanket, the low lamp, and the quiet hush before sleep."
    )
    world.say(
        f"But tonight, {child.pronoun('possessive')} {item.label} was missing, and that felt strange."
    )

    world.para()
    world.say(
        f"{child.name} peeked under the bed and behind the pillow, looking for a clue."
    )
    world.say(
        f"Near the sheets, {child.pronoun('subject')} found {mystery['clue']}, which meant someone had been close by."
    )
    world.say(
        f"{helper.name} came in and said, \"Let's keep {mystery['help_gerund']} until we solve the mystery.\""
    )
    world.say(
        f"{stingy.name}, who was a bit stingy with time and sharing, crossed {stingy.pronoun('possessive')} arms and said {mystery['help_gerund']} was too much work."
    )

    world.para()
    world.say(
        f"{child.name} still looked carefully. {child.subj()} checked the toy basket, the chair, and the shelf."
    )
    world.say(
        f"Then {child.pronoun('subject')} noticed {mystery['solution']}."
    )
    world.say(
        f"It was not lost at all; it had simply been moved during the bedtime tidy-up."
    )
    world.say(
        f"{helper.name} smiled, and even {stingy.name} had to admit the clue made sense."
    )

    world.para()
    world.say(
        f"At last, {child.name} climbed into bed with {item.label} in the right place."
    )
    world.say(mystery["ending"])
    world.say(
        f"{stingy.name} tucked the quilt a little closer, and the room grew still and sleepy."
    )


# ---------------------------------------------------------------------------
# Parameter resolution
# ---------------------------------------------------------------------------

@dataclass
class StorySetup:
    room: str
    mystery: str
    child_name: str
    child_role: str
    helper_role: str
    stingy_role: str
    trait: str


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    room = args.room or rng.choice(list(ROOMS))
    mystery = args.mystery or rng.choice(list(MYSTERIES))
    if room not in ROOMS:
        raise StoryError("Unknown room.")
    if mystery not in MYSTERIES:
        raise StoryError("Unknown mystery.")
    if (room, mystery) not in valid_combos():
        raise StoryError(explain_rejection(room, mystery))

    return StoryParams(
        room=room,
        mystery=mystery,
        child_name=args.name or rng.choice(GENTLE_NAMES),
        child_role=args.child_role or rng.choice(["girl", "boy"]),
        helper_role=args.helper_role or rng.choice(HELPER_NAMES),
        stingy_role=args.stingy_role or rng.choice(["cat", "sibling", "neighbor"]),
        seed=args.seed,
    )


def generate(params: StoryParams) -> StorySample:
    world = World(ROOMS[params.room])

    mystery = MYSTERIES[params.mystery]
    child = world.add_person(Person(
        id="child",
        role=params.child_role,
        name=params.child_name,
        adjective=random.choice(TRAITS),
        meters={"sleepy": 1.0},
        memes={"curiosity": 1.0, "worry": 0.2},
    ))
    helper = world.add_person(Person(
        id="helper",
        role="adult",
        name=params.helper_role,
        adjective="kind",
        meters={"calm": 1.0},
        memes={"helpfulness": 1.0},
    ))
    stingy = world.add_person(Person(
        id="stingy",
        role=params.stingy_role,
        name=params.stingy_role.capitalize() if params.stingy_role != "sibling" else "Big Sib",
        adjective="stingy",
        meters={"stillness": 1.0},
        memes={"stingy": 1.0, "reluctance": 0.6},
    ))
    item = world.add_item(Item(
        id="important",
        label=mystery["label"],
        owner="child",
        place=mystery["missing"],
        hidden=True,
    ))

    world.facts.update(
        mystery=params.mystery,
        mystery_data=mystery,
        child=child,
        helper=helper,
        stingy=stingy,
        item=item,
    )

    build_story(world)

    prompts = [
        f"Write a bedtime story about a child solving a small mystery with {mystery['help_gerund']}.",
        f"Tell a gentle story where a stingy character does not help much at first, but the family still solves the mystery.",
        f"Make a quiet bedtime tale about {params.child_name}, {mystery['label']}, and a warm, reassuring ending.",
    ]

    story_qa = [
        QAItem(
            question=f"What was missing in the story?",
            answer=f"{mystery['label']} was missing at first, which made bedtime feel strange."
        ),
        QAItem(
            question=f"Who helped solve the mystery?",
            answer=f"{helper.name} helped {child.name} keep looking until the clue made sense."
        ),
        QAItem(
            question=f"Why was {stingy.name} called stingy?",
            answer=f"{stingy.name} did not want to spend much time helping at first, so {stingy.pronoun('subject')} seemed stingy."
        ),
        QAItem(
            question=f"What solved the mystery?",
            answer=f"The clue on the bed led to {mystery['solution']}, so the item was not really lost."
        ),
    ]

    world_qa = [
        QAItem(
            question="Why do children like bedtime routines?",
            answer="Bedtime routines feel calm and familiar, so they help children settle down for sleep."
        ),
        QAItem(
            question="What is a clue?",
            answer="A clue is a small piece of information that helps someone figure out a mystery."
        ),
        QAItem(
            question="What does it mean to be stingy?",
            answer="A stingy person does not like to share, give, or help as freely as others."
        ),
        QAItem(
            question="Why are quiet rooms nice at bedtime?",
            answer="Quiet rooms help the body slow down, which makes it easier to rest and fall asleep."
        ),
    ]

    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts,
        story_qa=story_qa,
        world_qa=world_qa,
        world=world,
    )


# ---------------------------------------------------------------------------
# ASP helpers and verification
# ---------------------------------------------------------------------------

def asp_valid_combos() -> list[tuple[str, str]]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    a = set(asp_valid_combos())
    b = set(valid_combos())
    if a == b:
        print(f"OK: clingo gate matches valid_combos() ({len(a)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print(" only in clingo:", sorted(a - b))
    print(" only in python:", sorted(b - a))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime mystery storyworld.")
    ap.add_argument("--room", choices=ROOMS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--name")
    ap.add_argument("--child-role", choices=["girl", "boy"])
    ap.add_argument("--helper-role", choices=HELPER_NAMES)
    ap.add_argument("--stingy-role", choices=["cat", "sibling", "neighbor"])
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
    lines = ["--- world trace ---"]
    for p in world.people.values():
        lines.append(
            f"{p.id}: role={p.role} name={p.name} meters={p.meters} memes={p.memes} holds={p.holds}"
        )
    for it in world.items.values():
        lines.append(f"{it.id}: label={it.label} place={it.place} hidden={it.hidden}")
    return "\n".join(lines)


CURATED = [
    StoryParams(room="nursery", mystery="lost_blanket", child_name="Mia", child_role="girl", helper_role="Mum", stingy_role="cat"),
    StoryParams(room="bedroom", mystery="missing_bunny", child_name="Leo", child_role="boy", helper_role="Dad", stingy_role="sibling"),
    StoryParams(room="hall", mystery="quiet_nightlight", child_name="Nora", child_role="girl", helper_role="Gran", stingy_role="neighbor"),
]


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
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid bedtime mystery combos:\n")
        for room, mystery in combos:
            print(f"  {room:8} {mystery}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        for p in CURATED:
            samples.append(generate(p))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            rng = random.Random(seed)
            try:
                params = resolve_params(args, rng)
            except StoryError as e:
                print(e)
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
            header = f"### {p.child_name}: {p.mystery} in {p.room}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
