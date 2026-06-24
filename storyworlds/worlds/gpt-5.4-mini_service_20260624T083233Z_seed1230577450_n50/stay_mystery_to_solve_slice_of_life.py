#!/usr/bin/env python3
"""
A small slice-of-life mystery storyworld: someone stays in one place long enough
to notice a missing everyday item, follows clues, and solves it with a gentle
helping hand.
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
# Data model
# ---------------------------------------------------------------------------
@dataclass
class Person:
    id: str
    role: str
    name: str
    pronoun_subject: str
    pronoun_object: str
    pronoun_possessive: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def subj(self) -> str:
        return self.pronoun_subject

    def obj(self) -> str:
        return self.pronoun_object

    def pos(self) -> str:
        return self.pronoun_possessive


@dataclass
class Item:
    id: str
    label: str
    owner: Optional[str] = None
    hidden_in: Optional[str] = None
    found: bool = False
    meters: dict[str, float] = field(default_factory=dict)


@dataclass
class Place:
    id: str
    label: str
    cozy: bool = True
    clues: list[str] = field(default_factory=list)


@dataclass
class StoryParams:
    place: str
    missing_item: str
    seeker_name: str
    seeker_role: str
    helper_name: str
    helper_role: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# World state
# ---------------------------------------------------------------------------
class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.people: dict[str, Person] = {}
        self.items: dict[str, Item] = {}
        self.facts: dict[str, object] = {}
        self.trace: list[str] = []

    def add_person(self, p: Person) -> Person:
        self.people[p.id] = p
        return p

    def add_item(self, item: Item) -> Item:
        self.items[item.id] = item
        return item

    def person(self, pid: str) -> Person:
        return self.people[pid]

    def item(self, iid: str) -> Item:
        return self.items[iid]

    def say(self, text: str) -> None:
        self.trace.append(text)

    def render(self) -> str:
        return " ".join(self.trace)

    def copy(self) -> "World":
        import copy as _copy
        w = World(self.place)
        w.people = _copy.deepcopy(self.people)
        w.items = _copy.deepcopy(self.items)
        w.facts = _copy.deepcopy(self.facts)
        return w


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------
PLACES = {
    "kitchen": Place("kitchen", "the kitchen", cozy=True, clues=["under the table", "near the sink"]),
    "living_room": Place("living_room", "the living room", cozy=True, clues=["behind the sofa", "under a cushion"]),
    "bedroom": Place("bedroom", "the bedroom", cozy=True, clues=["under the bed", "inside a toy box"]),
    "porch": Place("porch", "the porch", cozy=True, clues=["by the shoes", "next to the mat"]),
}

ITEMS = {
    "spoon": Item("spoon", "silver spoon"),
    "sock": Item("sock", "striped sock"),
    "book": Item("book", "picture book"),
    "key": Item("key", "little key"),
}

SEEKER_ROLES = ["child", "mom", "dad", "grandma"]
HELPER_ROLES = ["mom", "dad", "grandma", "neighbor"]

NAMES = ["Mina", "Leo", "Nora", "Finn", "Ivy", "Owen", "Maya", "Theo", "Ruby", "Noah"]


# ---------------------------------------------------------------------------
# Narrative helpers
# ---------------------------------------------------------------------------
def pronouns(role: str) -> tuple[str, str, str]:
    if role in {"mom", "grandma", "aunt"}:
        return "she", "her", "her"
    if role in {"dad", "grandpa", "uncle"}:
        return "he", "him", "his"
    return "they", "them", "their"


def article(word: str) -> str:
    return "an" if word[:1].lower() in "aeiou" else "a"


def story_intro(world: World, seeker: Person, helper: Person, item: Item) -> None:
    world.say(
        f"{seeker.name} was staying home at {world.place.label} with {helper.name}, "
        f"enjoying a quiet, ordinary day."
    )
    world.say(
        f"{seeker.name} liked little routines, like tidying the table and keeping "
        f"{seeker.pos()} things in the same spot."
    )
    world.say(
        f"That morning, {seeker.name} noticed {article(item.label)} {item.label} was missing."
    )


def add_mystery(world: World, seeker: Person, item: Item) -> None:
    seeker.memes["curious"] = seeker.memes.get("curious", 0) + 1
    seeker.memes["worry"] = seeker.memes.get("worry", 0) + 1
    world.say(
        f"{seeker.name} looked on the shelf, under the blanket, and in the basket, "
        f"but the {item.label} was not there."
    )
    world.say(
        f"That made {seeker.name} pause and say, \"Where could it have gone?\""
    )


def follow_clue(world: World, seeker: Person, helper: Person, item: Item) -> str:
    clue = random.choice(world.place.clues)
    seeker.meters["searching"] = seeker.meters.get("searching", 0) + 1
    world.say(
        f"{helper.name} stayed nearby and helped look in {clue}, because a small mystery "
        f"is easier when two people look together."
    )
    return clue


def solve_mystery(world: World, seeker: Person, helper: Person, item: Item, clue: str) -> None:
    item.found = True
    seeker.memes["relief"] = seeker.memes.get("relief", 0) + 1
    helper.memes["pride"] = helper.memes.get("pride", 0) + 1
    world.say(
        f"At last, {seeker.name} found the {item.label} in {clue}, where it had slipped "
        f"after the morning rush."
    )
    world.say(
        f"{seeker.name} laughed, and {helper.name} smiled, because the mystery was small "
        f"but real, and now the day could go on."
    )
    world.say(
        f"{seeker.name} stayed calm, put the {item.label} back where it belonged, and "
        f"the room felt tidy again."
    )


def build_story(world: World, seeker: Person, helper: Person, item: Item) -> None:
    story_intro(world, seeker, helper, item)
    world.say("The day stayed gentle and slow, with only one thing to figure out.")
    add_mystery(world, seeker, item)
    clue = follow_clue(world, seeker, helper, item)
    solve_mystery(world, seeker, helper, item, clue)


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def valid_combo(place: str, missing_item: str) -> bool:
    if place not in PLACES:
        return False
    if missing_item not in ITEMS:
        return False
    # Slice-of-life mystery: the item must plausibly be found in a cozy indoor place.
    return PLACES[place].cozy


def explain_rejection(place: str, missing_item: str) -> str:
    if place not in PLACES:
        return "(No story: that place is not in this small home world.)"
    if missing_item not in ITEMS:
        return "(No story: that item is not in this small home world.)"
    return "(No story: this mystery needs a cozy everyday place where a small missing item could reasonably be found.)"


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
place(kitchen). place(living_room). place(bedroom). place(porch).

cozy(kitchen). cozy(living_room). cozy(bedroom). cozy(porch).

item(spoon). item(sock). item(book). item(key).

valid(P, I) :- place(P), cozy(P), item(I).

#show valid/2.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
        if PLACES[pid].cozy:
            lines.append(asp.fact("cozy", pid))
    for iid in ITEMS:
        lines.append(asp.fact("item", iid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple[str, str]]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = sorted((p, i) for p in PLACES for i in ITEMS if valid_combo(p, i))
    asp_set = asp_valid_combos()
    if py == asp_set:
        print(f"OK: clingo gate matches valid_combo() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combo():")
    if set(py) - set(asp_set):
        print("  only in python:", sorted(set(py) - set(asp_set)))
    if set(asp_set) - set(py):
        print("  only in clingo:", sorted(set(asp_set) - set(py)))
    return 1


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    p = world.facts
    return [
        f'Write a short slice-of-life mystery story about someone who stays home at {p["place"].label} and tries to find a missing {p["item"].label}.',
        f"Tell a gentle story where {p['seeker'].name} notices that {p['seeker'].pos()} {p['item'].label} has gone missing and {p['helper'].name} helps solve it.",
        f'Write a simple story that includes the word "stay" and ends with a small missing item being found in a cozy room.',
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.facts
    seeker: Person = p["seeker"]
    helper: Person = p["helper"]
    item: Item = p["item"]
    place: Place = p["place"]
    return [
        QAItem(
            question=f"Why did {seeker.name} stay at {place.label} instead of rushing off?",
            answer=(
                f"{seeker.name} stayed because it was a quiet day at {place.label}, "
                f"and {seeker.name} wanted to solve the little mystery first."
            ),
        ),
        QAItem(
            question=f"What was missing from {seeker.name}'s things?",
            answer=f"The missing thing was {article(item.label)} {item.label}.",
        ),
        QAItem(
            question=f"Who helped {seeker.name} look for the missing {item.label}?",
            answer=f"{helper.name} helped {seeker.name} search and stayed nearby the whole time.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean to stay somewhere?",
            answer=(
                "To stay somewhere means to remain there instead of leaving right away. "
                "People often stay when they are resting, waiting, or finishing a small task."
            ),
        ),
        QAItem(
            question="Why do people look in likely places first when something is missing?",
            answer=(
                "People look in likely places first because it saves time. If something slipped "
                "out of sight, it is often found near where it was last used."
            ),
        ),
        QAItem(
            question="What is a mystery to solve?",
            answer=(
                "A mystery to solve is a problem where someone does not know what happened yet. "
                "They follow clues and think carefully until they find an answer."
            ),
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {prompt}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A slice-of-life mystery storyworld where someone stays home "
        "and solves a small missing-item puzzle."
    )
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--missing-item", choices=sorted(ITEMS))
    ap.add_argument("--seeker-name")
    ap.add_argument("--seeker-role", choices=SEEKER_ROLES)
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-role", choices=HELPER_ROLES)
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
    item = args.missing_item or rng.choice(list(ITEMS))
    if not valid_combo(place, item):
        raise StoryError(explain_rejection(place, item))
    seeker_role = args.seeker_role or rng.choice(SEEKER_ROLES)
    helper_role = args.helper_role or rng.choice(HELPER_ROLES)
    seeker_name = args.seeker_name or rng.choice(NAMES)
    helper_name = args.helper_name or rng.choice([n for n in NAMES if n != seeker_name])
    return StoryParams(
        place=place,
        missing_item=item,
        seeker_name=seeker_name,
        seeker_role=seeker_role,
        helper_name=helper_name,
        helper_role=helper_role,
    )


def make_world(params: StoryParams) -> World:
    world = World(PLACES[params.place])
    s_subj, s_obj, s_pos = pronouns(params.seeker_role)
    h_subj, h_obj, h_pos = pronouns(params.helper_role)
    seeker = world.add_person(Person(
        id="seeker",
        role=params.seeker_role,
        name=params.seeker_name,
        pronoun_subject=s_subj,
        pronoun_object=s_obj,
        pronoun_possessive=s_pos,
    ))
    helper = world.add_person(Person(
        id="helper",
        role=params.helper_role,
        name=params.helper_name,
        pronoun_subject=h_subj,
        pronoun_object=h_obj,
        pronoun_possessive=h_pos,
    ))
    item = world.add_item(Item(
        id="item",
        label=ITEMS[params.missing_item].label,
        owner=seeker.id,
        hidden_in=random.choice(world.place.clues),
    ))
    world.facts = {"seeker": seeker, "helper": helper, "item": item, "place": world.place}
    build_story(world, seeker, helper, item)
    return world


def generate(params: StoryParams) -> StorySample:
    world = make_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for p in world.people.values():
        meters = {k: v for k, v in p.meters.items() if v}
        memes = {k: v for k, v in p.memes.items() if v}
        lines.append(f"  {p.name:10} ({p.role:8}) meters={meters} memes={memes}")
    for item in world.items.values():
        lines.append(
            f"  item={item.label:12} owner={item.owner} hidden_in={item.hidden_in} found={item.found}"
        )
    return "\n".join(lines)


CURATED = [
    StoryParams(place="kitchen", missing_item="spoon", seeker_name="Mina", seeker_role="child", helper_name="Grandma", helper_role="grandma"),
    StoryParams(place="living_room", missing_item="book", seeker_name="Leo", seeker_role="child", helper_name="Dad", helper_role="dad"),
    StoryParams(place="bedroom", missing_item="sock", seeker_name="Ivy", seeker_role="child", helper_name="Mom", helper_role="mom"),
    StoryParams(place="porch", missing_item="key", seeker_name="Nora", seeker_role="child", helper_name="Grandma", helper_role="grandma"),
]


def asp_program_full(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify_full() -> int:
    return asp_verify()


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program_full("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify_full())
    if args.asp:
        import asp
        model = asp.one_model(asp_program_full("#show valid/2."))
        combos = sorted(set(asp.atoms(model, "valid")))
        print(f"{len(combos)} valid (place, item) combos:")
        for c in combos:
            print(f"  {c[0]} / {c[1]}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            rng = random.Random(base_seed + i)
            i += 1
            try:
                params = resolve_params(args, rng)
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

    for idx, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.seeker_name}: missing {p.missing_item} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
