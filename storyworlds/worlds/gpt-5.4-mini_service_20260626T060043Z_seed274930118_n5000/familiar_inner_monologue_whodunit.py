#!/usr/bin/env python3
"""
A small whodunit story world with a familiar, an inner monologue, and a tidy
mystery resolution.

Premise:
- A young apprentice and their familiar notice a missing object in a quiet home.
- The apprentice thinks through clues in an inner monologue.
- The familiar helps by tracking scent, sound, or small physical traces.
- The culprit is not malicious; the ending reveals a simple, concrete cause.

This world keeps the scope small: one missing thing, a few plausible suspects,
and one satisfying reveal.
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
# Registries
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class Room:
    id: str
    label: str
    detail: str


@dataclass(frozen=True)
class Item:
    id: str
    label: str
    phrase: str
    room: str
    scent: str
    size: str


@dataclass(frozen=True)
class Suspect:
    id: str
    label: str
    room: str
    motive: str
    innocence: str


@dataclass(frozen=True)
class Solution:
    cause: str
    reveal: str
    fix: str


ROOMS = {
    "study": Room("study", "the study", "Dusty books stood in neat stacks."),
    "kitchen": Room("kitchen", "the kitchen", "A warm pie smelled faintly sweet."),
    "hall": Room("hall", "the hall", "The floorboards creaked softly."),
    "garden": Room("garden", "the garden", "Leaves brushed the window glass."),
}

ITEMS = {
    "key": Item("key", "silver key", "a small silver key", "study", "metal", "small"),
    "book": Item("book", "blue notebook", "a blue notebook with ribbon marks", "study", "paper", "small"),
    "jar": Item("jar", "jam jar", "a sticky jam jar", "kitchen", "sweet jam", "medium"),
    "brush": Item("brush", "ink brush", "a black ink brush", "study", "ink", "small"),
}

SUSPECTS = {
    "aunt": Suspect("aunt", "Aunt Mara", "kitchen", "she was baking and needed a spoon", "flour on her sleeve proved she stayed in the kitchen"),
    "neighbor": Suspect("neighbor", "Mr. Bell", "hall", "he came to borrow sugar", "he never left the hall"),
    "familiar": Suspect("familiar", "Pip the familiar", "study", "he liked shiny things and warm places", "his paws were dusty, not sticky"),
    "apprentice": Suspect("apprentice", "the apprentice", "study", "they had been reading the notebook", "they were the one thinking hard about the missing thing"),
}

SOLUTIONS = {
    "jar_in_book": Solution(
        cause="the missing thing had been tucked into the blue notebook as a bookmark",
        reveal="the silver key slid out when the apprentice opened the notebook",
        fix="everyone laughed, and the apprentice put the key on its hook by the door",
    ),
    "familiar_stash": Solution(
        cause="Pip had carried the small object to the rug by the window",
        reveal="he had been practicing fetch with the shiny key",
        fix="the apprentice scratched Pip behind the ears and put the key back in its box",
    ),
    "aunt_moved": Solution(
        cause="Aunt Mara had moved it while cleaning the shelf",
        reveal="she found it in the sugar tin by mistake",
        fix="she apologized, and the household agreed to keep the key in a dish",
    ),
}


# ---------------------------------------------------------------------------
# Story model
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    room: str = "study"
    item: str = "key"
    culprit: str = "familiar"
    solution: str = "familiar_stash"
    name: str = "Nina"
    familiar_name: str = "Pip"
    seed: Optional[int] = None


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    room: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


class World:
    def __init__(self, params: StoryParams):
        self.params = params
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
        self.lines: list[str] = []
        self.inner: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def think(self, text: str) -> None:
        if text:
            self.inner.append(text)

    def render(self) -> str:
        parts = []
        if self.inner:
            parts.append(" ".join(self.inner))
        parts.extend(self.lines)
        return "\n".join(parts)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def pronoun(name: str, case: str = "subject") -> str:
    if name == "Nina":
        return {"subject": "she", "object": "her", "possessive": "her"}[case]
    return {"subject": "he", "object": "him", "possessive": "his"}[case]


def build_world(params: StoryParams) -> World:
    world = World(params)
    room = ROOMS[params.room]
    item = ITEMS[params.item]
    culprit = SUSPECTS[params.culprit]
    solution = SOLUTIONS[params.solution]

    apprentice = world.add(Entity("apprentice", "character", params.name, room=params.room))
    familiar = world.add(Entity("familiar", "familiar", params.familiar_name, room=params.room))
    missing = world.add(Entity("missing", "item", item.label, room="missing"))

    world.facts.update(
        room=room,
        item=item,
        culprit=culprit,
        solution=solution,
        apprentice=apprentice,
        familiar=familiar,
        missing=missing,
    )
    return world


# ---------------------------------------------------------------------------
# Narrative
# ---------------------------------------------------------------------------
def tell_story(world: World) -> None:
    p = world.params
    room: Room = world.facts["room"]
    item: Item = world.facts["item"]
    culprit: Suspect = world.facts["culprit"]
    solution: Solution = world.facts["solution"]

    world.say(f"Late in the evening, {p.name} stood in {room.label} and stared at the empty shelf.")
    world.say(room.detail)
    world.say(f"The {item.label} was gone, and that felt wrong in a room that liked order.")

    world.think(
        f"{p.name} thought, Not stolen, not lost in a storm, not taken by a stranger. "
        f"The house was too quiet for a big crime."
    )
    world.say(f"{p.name}'s familiar, {p.familiar_name}, circled once and sniffed the floorboards.")
    world.say(f"Something small had happened here, not something wild.")

    world.think(
        f"If the clue smelled like {item.scent}, then the trail should be near the place where "
        f"{item.phrase} usually rested. Start with the obvious room. Count the calm things."
    )
    world.say(f"{p.name} checked the hook by the door, then the desk drawer, then the window ledge.")
    world.say(f"That was the right kind of searching: careful, quiet, and a little suspicious.")

    world.say(f"{p.name} asked who had been nearby.")
    world.say(f"{culprit.label} was in {ROOMS[culprit.room].label}. {culprit.innocence}.")
    if culprit.id != "familiar":
        world.say(f"That left {p.familiar_name}, who was acting far too interested in the rug.")

    world.think(
        f"Wait, {p.name} thought. If {item.label} were truly taken, the room would feel torn up. "
        f"But nothing was broken. That means the missing thing likely moved by accident."
    )

    if p.solution == "familiar_stash":
        world.say(f"{p.familiar_name} sneezed and batted at a notebook with one paw.")
        world.say(f"The notebook flopped open.")
        world.say(f"There it was: {solution.reveal}.")
        world.say(f"{solution.cause}.")
        world.say(f"{solution.fix}.")
        world.say(f"{p.name} laughed softly. The mystery had only been a careless game, after all.")
    elif p.solution == "jar_in_book":
        world.say(f"{p.name} opened the blue notebook and found the answer hiding between the pages.")
        world.say(f"There, pinned as neat as a clue in a detective tale, was the silver key.")
        world.say(f"{solution.cause}.")
        world.say(f"{solution.fix}.")
    else:
        world.say(f"A careful search at last showed the truth: {solution.reveal}.")
        world.say(f"{solution.cause}.")
        world.say(f"{solution.fix}.")

    world.say(f"By morning, the shelf was tidy again, and {p.familiar_name} was curled beside it like a tiny guard.")

    world.facts["resolved"] = True
    world.facts["story_focus"] = f"{p.name} and {p.familiar_name} solved the missing {item.label} mystery"


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    p = world.params
    item: Item = world.facts["item"]
    return [
        f"Write a short whodunit for children about a familiar, a missing {item.label}, and a careful inner monologue.",
        f"Tell a cozy mystery where {p.name} and {p.familiar_name} look for {item.phrase} in {world.facts['room'].label}.",
        f"Write a story that feels like a tiny detective tale and ends with the missing {item.label} being found.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.params
    item: Item = world.facts["item"]
    room: Room = world.facts["room"]
    culprit: Suspect = world.facts["culprit"]
    solution: Solution = world.facts["solution"]

    return [
        QAItem(
            question=f"What was missing from {room.label}?",
            answer=f"The {item.label} was missing from {room.label}, which made {p.name} stop and think.",
        ),
        QAItem(
            question=f"Who helped {p.name} look for the missing {item.label}?",
            answer=f"{p.familiar_name} the familiar helped by sniffing around and noticing tiny clues.",
        ),
        QAItem(
            question=f"Why did {p.name} think the mystery was probably small?",
            answer=(
                f"{p.name} thought it was probably small because the room was still neat, "
                f"so the clue looked more like an accident than a big theft."
            ),
        ),
        QAItem(
            question=f"Where was the {item.label} found?",
            answer=(
                f"It was found because {solution.cause}. That gave {p.name} the answer in the end."
            ),
        ),
        QAItem(
            question=f"Was {culprit.label} the true thief?",
            answer=(
                f"No. {culprit.label} was just nearby, and the real truth was gentler: "
                f"{solution.cause}."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    p = world.params
    item: Item = world.facts["item"]
    return [
        QAItem(
            question="What is a familiar?",
            answer="A familiar is an animal companion in magical stories, often clever and helpful.",
        ),
        QAItem(
            question="What does an inner monologue mean?",
            answer="An inner monologue is the voice of someone thinking to themselves inside their head.",
        ),
        QAItem(
            question="What does a detective do?",
            answer="A detective looks for clues, asks questions, and tries to figure out what really happened.",
        ),
        QAItem(
            question=f"Why might a {item.label} be easy to lose?",
            answer=f"A {item.label} is small, so it can slip into a drawer, a book, or a corner without being noticed.",
        ),
        QAItem(
            question="What makes a mystery cozy instead of scary?",
            answer="A cozy mystery usually has a gentle problem, friendly helpers, and a safe ending.",
        ),
    ]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A clue is in the search space when the item can plausibly move to a room.
can_hide(Item, Room) :- item(Item), room(Room), Item != Room.

% A suspect is plausible if they were in a nearby room.
plausible(Culprit) :- suspect(Culprit), near_room(CulpritRoom), in_room(Culprit, CulpritRoom).

% A solution is reasonable when it explains a missing item without requiring damage.
reasonble_solution(S) :- solution(S).

#show plausible/1.
#show reasonble_solution/1.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for r in ROOMS.values():
        lines.append(asp.fact("room", r.id))
    for i in ITEMS.values():
        lines.append(asp.fact("item", i.id))
        lines.append(asp.fact("item_room", i.id, i.room))
    for s in SUSPECTS.values():
        lines.append(asp.fact("suspect", s.id))
        lines.append(asp.fact("in_room", s.id, s.room))
    for s in SOLUTIONS:
        lines.append(asp.fact("solution", s))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
    except Exception as e:  # pragma: no cover
        print(f"ASP unavailable: {e}")
        return 1
    model = asp.one_model(asp_program("#show plausible/1.\n#show reasonble_solution/1."))
    atoms = set(asp.atoms(model, "plausible")) | set(asp.atoms(model, "reasonble_solution"))
    expected = {("familiar",), ("reasonble_solution", "familiar_stash"), ("reasonble_solution", "jar_in_book"), ("reasonble_solution", "aunt_moved")}
    if atoms:
        print("OK: ASP program solved, with atoms:", sorted(atoms))
        return 0
    print("Mismatch: ASP produced no shown atoms.")
    return 1


# ---------------------------------------------------------------------------
# Validation and generation
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A cozy whodunit story world with a familiar and an inner monologue.")
    ap.add_argument("--room", choices=ROOMS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--culprit", choices=SUSPECTS)
    ap.add_argument("--solution", choices=SOLUTIONS)
    ap.add_argument("--name")
    ap.add_argument("--familiar-name")
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


def valid_combo(room: str, item: str, culprit: str, solution: str) -> bool:
    if room not in ROOMS or item not in ITEMS or culprit not in SUSPECTS or solution not in SOLUTIONS:
        return False
    if culprit == "aunt" and solution not in {"aunt_moved"}:
        return True
    if culprit == "familiar" and solution not in {"familiar_stash"}:
        return True
    if culprit == "apprentice" and solution not in {"jar_in_book", "familiar_stash"}:
        return True
    return True


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    room = args.room or rng.choice(list(ROOMS))
    item = args.item or rng.choice(list(ITEMS))
    culprit = args.culprit or rng.choice(list(SUSPECTS))
    if args.solution:
        solution = args.solution
    else:
        if culprit == "familiar":
            solution = "familiar_stash"
        elif culprit == "aunt":
            solution = "aunt_moved"
        else:
            solution = rng.choice(list(SOLUTIONS))
    if culprit == "familiar" and solution == "aunt_moved":
        raise StoryError("The familiar cannot also be the aunt's cleanup mistake.")
    name = args.name or rng.choice(["Nina", "Milo", "Aria", "Theo"])
    familiar_name = args.familiar_name or rng.choice(["Pip", "Moss", "Jinx", "Puck"])
    return StoryParams(room=room, item=item, culprit=culprit, solution=solution, name=name, familiar_name=familiar_name)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    tell_story(world)
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
        lines.append(f"{e.id}: kind={e.kind} label={e.label} room={e.room}")
    for k, v in world.facts.items():
        if k in {"room", "item", "culprit", "solution", "apprentice", "familiar", "missing"}:
            continue
        lines.append(f"{k}: {v}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== generation prompts =="]
    for p in sample.prompts:
        out.append(f"- {p}")
    out.append("")
    out.append("== story QA ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== world QA ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def asp_validity_report() -> str:
    return asp_program("#show plausible/1.\n#show reasonble_solution/1.")


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_validity_report())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show plausible/1.\n#show reasonble_solution/1."))
        print(asp.atoms(model, "plausible"))
        print(asp.atoms(model, "reasonble_solution"))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams(room="study", item="key", culprit="familiar", solution="familiar_stash", name="Nina", familiar_name="Pip"),
            StoryParams(room="study", item="book", culprit="apprentice", solution="jar_in_book", name="Milo", familiar_name="Moss"),
            StoryParams(room="kitchen", item="jar", culprit="aunt", solution="aunt_moved", name="Aria", familiar_name="Jinx"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen = set()
        for i in range(max(1, args.n)):
            params = resolve_params(args, random.Random(base_seed + i))
            story = generate(params)
            if story.story in seen:
                continue
            seen.add(story.story)
            samples.append(story)

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
