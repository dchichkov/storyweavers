#!/usr/bin/env python3
"""
storyworlds/worlds/tame_pajamas_mystery_to_solve_teamwork_problem.py
===================================================================

A small standalone storyworld for a ghost-story flavored mystery about
pajamas, a tame helper, teamwork, and problem solving.

Seed premise:
- A child has a favorite pair of pajamas.
- Something mysterious goes missing at bedtime.
- The child and a tame helper investigate together.
- They solve the problem by working as a team and discover a harmless cause.

The world is deliberately tiny and state-driven:
- physical meters track where things are, whether they are hidden, and whether
  the pajamas are clean, wrinkled, or worn;
- emotional memes track worry, courage, curiosity, and teamwork.

The prose aims for a gentle ghost-story mood without fear that is too intense.
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    location: str = ""
    hidden: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Room:
    id: str
    label: str
    eerie_detail: str
    clues: list[str] = field(default_factory=list)


@dataclass
class StoryParams:
    room: str
    child_name: str
    child_type: str
    helper_name: str
    helper_type: str
    seed: Optional[int] = None


class World:
    def __init__(self, room: Room):
        self.room = room
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
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
# Registry
# ---------------------------------------------------------------------------

ROOMS = {
    "attic": Room(
        id="attic",
        label="the attic",
        eerie_detail="The rafters made soft creaks like sleepy whispering.",
        clues=["a dusty trunk", "a tiny trail of footprints", "a folded note"],
    ),
    "hall": Room(
        id="hall",
        label="the hallway",
        eerie_detail="The hallway lamp cast long shadows that looked like tall ghosts.",
        clues=["a swaying coat", "a dropped button", "a creaky floorboard"],
    ),
    "nursery": Room(
        id="nursery",
        label="the nursery",
        eerie_detail="Moonlight shone on the wall and made gentle shapes from the curtains.",
        clues=["a rocking chair", "a toy chest", "a blanket on the floor"],
    ),
    "closet": Room(
        id="closet",
        label="the closet",
        eerie_detail="The closet door breathed out a cool little draft.",
        clues=["a laundry basket", "a shoe box", "a shelf of folded clothes"],
    ),
}

CHILD_NAMES = ["Mia", "Nora", "Eli", "Theo", "Luna", "Pip"]
HELPER_NAMES = ["Boo", "Moss", "Milo", "Wisp", "Penny", "Toby"]

CHILD_TYPES = ["girl", "boy"]
HELPER_TYPES = ["cat", "dog", "raccoon", "mouse"]

# ---------------------------------------------------------------------------
# Inline ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A room can hold a bedtime mystery if it has eerie clues.
mystery_room(R) :- room(R), clue(R, _).

% Teamwork solves the problem when child and helper both search, and the
% missing pajamas are found in a clue-location.
solved(R) :- mystery_room(R), child_searches(R), helper_searches(R), found_pajamas(R).

#show mystery_room/1.
#show solved/1.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for rid, room in ROOMS.items():
        lines.append(asp.fact("room", rid))
        for clue in room.clues:
            lines.append(asp.fact("clue", rid, clue))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_reasonable_rooms() -> list[str]:
    import asp

    model = asp.one_model(asp_program("#show mystery_room/1."))
    return sorted({rid for (rid,) in asp.atoms(model, "mystery_room")})


def asp_verify() -> int:
    python_set = {rid for rid, room in ROOMS.items() if room.clues}
    asp_set = set(asp_reasonable_rooms())
    if python_set == asp_set:
        print(f"OK: ASP matches Python room gate ({len(asp_set)} rooms).")
        return 0
    print("MISMATCH between ASP and Python room gate:")
    print("  only in ASP:", sorted(asp_set - python_set))
    print("  only in Python:", sorted(python_set - asp_set))
    return 1


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------

def validate_params(params: StoryParams) -> None:
    if params.room not in ROOMS:
        raise StoryError(f"Unknown room: {params.room}")
    if params.child_type not in CHILD_TYPES:
        raise StoryError(f"Unknown child type: {params.child_type}")
    if params.helper_type not in HELPER_TYPES:
        raise StoryError(f"Unknown helper type: {params.helper_type}")
    if params.child_name == params.helper_name:
        raise StoryError("The child and helper need different names.")


def build_world(params: StoryParams) -> World:
    validate_params(params)
    world = World(ROOMS[params.room])

    child = world.add(Entity(
        id="child",
        kind="character",
        type=params.child_type,
        label=params.child_name,
        traits=["curious", "sleepy"],
        meters={"location": 0.0},
        memes={"worry": 0.0, "courage": 0.0, "curiosity": 1.0, "joy": 0.0, "teamwork": 0.0},
    ))
    helper = world.add(Entity(
        id="helper",
        kind="character",
        type=params.helper_type,
        label=params.helper_name,
        traits=["tame", "gentle"],
        meters={"location": 0.0},
        memes={"worry": 0.0, "courage": 0.0, "curiosity": 1.0, "joy": 0.0, "teamwork": 0.0},
    ))
    pajamas = world.add(Entity(
        id="pajamas",
        kind="thing",
        type="pajamas",
        label="pajamas",
        phrase="soft striped pajamas",
        plural=True,
        owner=child.id,
        location=params.room,
        hidden=True,
        meters={"clean": 1.0, "wrinkled": 0.0, "found": 0.0},
    ))

    world.facts.update(child=child, helper=helper, pajamas=pajamas)
    return world


def narrate_setup(world: World) -> None:
    child: Entity = world.facts["child"]  # type: ignore[assignment]
    helper: Entity = world.facts["helper"]  # type: ignore[assignment]
    pajamas: Entity = world.facts["pajamas"]  # type: ignore[assignment]

    world.say(
        f"{child.label} had a favorite pair of pajamas: {pajamas.phrase}. "
        f"{child.pronoun().capitalize()} liked how soft they felt at bedtime."
    )
    world.say(
        f"That night, a tiny mystery waited in {world.room.label}. "
        f"{world.room.eerie_detail}"
    )
    world.say(
        f"{helper.label} was a tame little helper and stayed close by, ready to help."
    )


def hide_pajamas(world: World) -> None:
    pajamas: Entity = world.facts["pajamas"]  # type: ignore[assignment]
    if "hide" in world.fired:
        return
    world.fired.add("hide")
    pajamas.hidden = True
    pajamas.location = world.room.id
    pajamas.meters["found"] = 0.0
    world.say(
        f"But when it was time to get dressed, the pajamas were nowhere to be seen."
    )


def investigate(world: World) -> None:
    child: Entity = world.facts["child"]  # type: ignore[assignment]
    helper: Entity = world.facts["helper"]  # type: ignore[assignment]
    room = world.room

    child.memes["worry"] += 1
    child.memes["curiosity"] += 1
    helper.memes["teamwork"] += 1
    helper.memes["courage"] += 1

    world.para()
    world.say(
        f"{child.label} looked under a chair, behind a basket, and beside the bed."
    )
    world.say(
        f"{helper.label} sniffed the air and tapped each clue with a careful paw."
    )
    world.say(
        f"Together they checked {room.clues[0]}, then {room.clues[1]}, then {room.clues[2]}."
    )


def solve_mystery(world: World) -> None:
    child: Entity = world.facts["child"]  # type: ignore[assignment]
    helper: Entity = world.facts["helper"]  # type: ignore[assignment]
    pajamas: Entity = world.facts["pajamas"]  # type: ignore[assignment]

    if "solve" in world.fired:
        return
    world.fired.add("solve")

    pajamas.hidden = False
    pajamas.meters["found"] = 1.0
    pajamas.meters["wrinkled"] = 1.0
    child.memes["joy"] += 1
    child.memes["worry"] = 0.0
    child.memes["teamwork"] += 1
    helper.memes["joy"] += 1

    world.say(
        f"At last, they found the pajamas folded inside the laundry basket."
    )
    world.say(
        f"A coat had blown them there from the open window, so the mystery was only a sleepy little trick."
    )
    world.say(
        f"{child.label} and {helper.label} laughed, smoothed out the wrinkles, and carried the pajamas back."
    )
    world.say(
        f"By bedtime's end, {child.label} was cozy again, and the room felt quiet instead of spooky."
    )


def tell(params: StoryParams) -> World:
    world = build_world(params)
    narrate_setup(world)
    hide_pajamas(world)
    investigate(world)
    solve_mystery(world)
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    child: Entity = world.facts["child"]  # type: ignore[assignment]
    helper: Entity = world.facts["helper"]  # type: ignore[assignment]
    return [
        "Write a gentle ghost-story about a child whose pajamas go missing at bedtime.",
        f"Tell a mystery story where {child.label} and {helper.label} solve a problem by working together.",
        "Make the mood a little eerie, but end with a calm and happy surprise.",
    ]


def story_qa(world: World) -> list[QAItem]:
    child: Entity = world.facts["child"]  # type: ignore[assignment]
    helper: Entity = world.facts["helper"]  # type: ignore[assignment]
    pajamas: Entity = world.facts["pajamas"]  # type: ignore[assignment]

    return [
        QAItem(
            question=f"What mystery did {child.label} and {helper.label} try to solve?",
            answer=f"They tried to solve the mystery of the missing pajamas at bedtime.",
        ),
        QAItem(
            question=f"How did {child.label} and {helper.label} work together?",
            answer=f"They searched the room together, checked the clues one by one, and stayed calm while they looked.",
        ),
        QAItem(
            question=f"Where were the pajamas found in the end?",
            answer=f"The pajamas were found folded inside the laundry basket, and they only looked wrinkled.",
        ),
        QAItem(
            question=f"What changed after the problem was solved?",
            answer=f"{child.label} stopped worrying, felt cozy again, and the room stopped feeling spooky.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What are pajamas?",
            answer="Pajamas are soft clothes people wear to sleep in at bedtime.",
        ),
        QAItem(
            question="What does a tame helper mean?",
            answer="A tame helper is gentle and safe to be near, so it can help without causing trouble.",
        ),
        QAItem(
            question="What is teamwork?",
            answer="Teamwork means people help each other by doing a job together.",
        ),
        QAItem(
            question="What is a mystery?",
            answer="A mystery is a puzzle about something that is missing, hidden, or not understood yet.",
        ),
        QAItem(
            question="What does problem solving mean?",
            answer="Problem solving means looking carefully, thinking of a plan, and trying different steps until the problem is fixed.",
        ),
    ]


# ---------------------------------------------------------------------------
# Parameters and generation
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    room: str
    child_name: str
    child_type: str
    helper_name: str
    helper_type: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(room="attic", child_name="Mia", child_type="girl", helper_name="Wisp", helper_type="mouse"),
    StoryParams(room="hall", child_name="Eli", child_type="boy", helper_name="Boo", helper_type="cat"),
    StoryParams(room="nursery", child_name="Luna", child_type="girl", helper_name="Moss", helper_type="dog"),
    StoryParams(room="closet", child_name="Theo", child_type="boy", helper_name="Penny", helper_type="raccoon"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Gentle ghost-story mystery world about missing pajamas.")
    ap.add_argument("--room", choices=ROOMS)
    ap.add_argument("--name")
    ap.add_argument("--helper-name")
    ap.add_argument("--child-type", choices=CHILD_TYPES)
    ap.add_argument("--helper-type", choices=HELPER_TYPES)
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
    room = args.room or rng.choice(list(ROOMS))
    child_type = args.child_type or rng.choice(CHILD_TYPES)
    helper_type = args.helper_type or rng.choice(HELPER_TYPES)
    child_name = args.name or rng.choice(CHILD_NAMES)
    helper_name = args.helper_name or rng.choice(HELPER_NAMES)
    if child_name == helper_name:
        helper_name = rng.choice([n for n in HELPER_NAMES if n != child_name])
    return StoryParams(
        room=room,
        child_name=child_name,
        child_type=child_type,
        helper_name=helper_name,
        helper_type=helper_type,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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
        print("\n--- trace ---")
        for key, ent in sample.world.entities.items():
            print(f"{key}: {ent}")
    if qa:
        print("\n== prompts ==")
        for i, p in enumerate(sample.prompts, 1):
            print(f"{i}. {p}")
        print("\n== story qa ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}\nA: {item.answer}")
        print("\n== world qa ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}\nA: {item.answer}")


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show solved/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show mystery_room/1.\n#show solved/1."))
        print(asp.atoms(model, "mystery_room"))
        print(asp.atoms(model, "solved"))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
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
        if i + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
