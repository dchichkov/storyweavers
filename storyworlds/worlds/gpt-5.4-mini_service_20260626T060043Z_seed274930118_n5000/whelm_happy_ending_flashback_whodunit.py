#!/usr/bin/env python3
"""
A small whodunit-style storyworld with a happy ending and a flashback reveal.

Premise:
- A child notices something important is missing.
- The household investigates clues and suspects.
- A flashback reveals the true chain of events.
- The ending resolves with relief, fairness, and a warm image.

The word "whelm" is used as a story verb in the sense of being overcome by
feelings: the hero can be whelmed by worry, then whelmed by relief.
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
    plural: bool = False
    hidden: bool = False
    location: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Room:
    name: str
    spots: list[str]


@dataclass
class Clue:
    id: str
    label: str
    phrase: str
    location: str
    hints: list[str] = field(default_factory=list)


@dataclass
class StoryParams:
    room: str
    missing: str
    culprit: str
    child_name: str
    child_gender: str
    parent_type: str
    seed: Optional[int] = None


class World:
    def __init__(self, room: Room):
        self.room = room
        self.entities: dict[str, Entity] = {}
        self.clues: dict[str, Clue] = {}
        self.history: list[str] = []
        self.facts: dict[str, object] = {}
        self.fired: set[tuple] = set()

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def add_clue(self, c: Clue) -> Clue:
        self.clues[c.id] = c
        return c

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.history.append(text)

    def render(self) -> str:
        return " ".join(self.history)


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

ROOMS = {
    "kitchen": Room("the kitchen", ["table", "sink", "chair", "counter"]),
    "bedroom": Room("the bedroom", ["bed", "toy box", "lamp", "closet"]),
    "living_room": Room("the living room", ["sofa", "rug", "bookshelf", "basket"]),
    "back_porch": Room("the back porch", ["bench", "step", "bucket", "doormat"]),
}

MISSING_ITEMS = {
    "red_ball": (
        "a red rubber ball",
        "ball",
        ["under the table", "near the chair", "by the sink"],
    ),
    "blue_hat": (
        "a blue felt hat",
        "hat",
        ["on the sofa", "behind the cushion", "beside the bookshelf"],
    ),
    "silver_spoon": (
        "a small silver spoon",
        "spoon",
        ["in the toy box", "under a napkin", "on the counter"],
    ),
    "green_kite": (
        "a green paper kite",
        "kite",
        ["inside the closet", "behind the lamp", "under the bed"],
    ),
}

CULPRITS = {
    "dog": "The family dog had dragged the item around while chasing a crumb.",
    "wind": "A sudden breeze had pushed the item into a new spot.",
    "sibling": "A little sibling had borrowed it and forgotten to put it back.",
}

CHILD_NAMES = ["Mia", "Noah", "Luna", "Eli", "Zoe", "Theo", "Ava", "Ben"]
PARENTS = ["mother", "father"]
GENDERS = ["girl", "boy"]


# ---------------------------------------------------------------------------
# Pronoun helpers / narration
# ---------------------------------------------------------------------------

def a_or_an(text: str) -> str:
    return "an" if text[:1].lower() in "aeiou" else "a"


def hero_desc(name: str, gender: str) -> str:
    return f"{a_or_an('old')} little {gender} named {name}"


def parent_word(parent_type: str) -> str:
    return "mom" if parent_type == "mother" else "dad"


def clue_sentence(clue: Clue) -> str:
    return f"One clue was {clue.phrase} {clue.location}."


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------

def build_world(params: StoryParams) -> World:
    room = ROOMS[params.room]
    world = World(room)

    child = world.add(Entity(
        id=params.child_name,
        kind="character",
        type=params.child_gender,
        label=params.child_name,
    ))
    parent = world.add(Entity(
        id="parent",
        kind="character",
        type=params.parent_type,
        label=parent_word(params.parent_type),
    ))

    label, label_word, spots = MISSING_ITEMS[params.missing]
    missing = world.add(Entity(
        id="missing",
        kind="thing",
        type=label_word,
        label=label_word,
        phrase=label,
        owner=child.id,
        hidden=True,
        location=room.spots[0],
    ))

    culprit_reason = CULPRITS[params.culprit]
    world.facts["child"] = child
    world.facts["parent"] = parent
    world.facts["missing"] = missing
    world.facts["culprit"] = params.culprit
    world.facts["culprit_reason"] = culprit_reason
    world.facts["room"] = room
    world.facts["spots"] = spots
    return world


def narrate_setup(world: World) -> None:
    child: Entity = world.facts["child"]  # type: ignore[assignment]
    parent: Entity = world.facts["parent"]  # type: ignore[assignment]
    missing: Entity = world.facts["missing"]  # type: ignore[assignment]
    room: Room = world.facts["room"]  # type: ignore[assignment]

    world.say(
        f"{child.label} was {hero_desc(child.label, child.type)} who loved tidy rooms "
        f"and the little routines in {room.name}."
    )
    world.say(
        f"{child.label} had a special {missing.label} from the shelf, and {child.pronoun('possessive')} "
        f"{parent.label} had promised to help keep it safe."
    )


def suspect_and_whelm(world: World) -> None:
    child: Entity = world.facts["child"]  # type: ignore[assignment]
    parent: Entity = world.facts["parent"]  # type: ignore[assignment]
    missing: Entity = world.facts["missing"]  # type: ignore[assignment]
    room: Room = world.facts["room"]  # type: ignore[assignment]

    child.memes["worry"] = 1
    child.memes["whelm"] = 1
    world.say(
        f"Then one morning, the {missing.label} was gone, and {child.label} felt whelm with worry."
    )
    world.say(
        f"{child.label} and {parent.label} looked under the bed, inside baskets, and behind the door."
    )
    world.say(
        f"{parent.label} said, \"Let's follow the clues before we guess.\""
    )
    world.say(
        f"In {room.name}, every small mark could matter, so they looked closely."
    )


def add_clues(world: World) -> None:
    missing: Entity = world.facts["missing"]  # type: ignore[assignment]
    room: Room = world.facts["room"]  # type: ignore[assignment]
    spots: list[str] = world.facts["spots"]  # type: ignore[assignment]

    clue1 = world.add_clue(Clue(
        id="dust",
        label="dust line",
        phrase="a thin dust line",
        location=f"near {spots[0]}",
        hints=["Something had been moved recently."],
    ))
    clue2 = world.add_clue(Clue(
        id="crumb",
        label="crumb trail",
        phrase="a tiny crumb trail",
        location=f"by {spots[1] if len(spots) > 1 else room.spots[1]}",
        hints=["The clue pointed toward a small, fast-moving thing."],
    ))
    clue3 = world.add_clue(Clue(
        id="scratch",
        label="scratch mark",
        phrase="a little scratch mark",
        location=f"on {spots[2] if len(spots) > 2 else room.spots[2]}",
        hints=["It looked like the item had been nudged, not taken forever."],
    ))

    world.say(clue_sentence(clue1))
    world.say(clue_sentence(clue2))
    world.say(clue_sentence(clue3))
    world.say(
        f"{missing.label} had not vanished by magic; the clues said it had been moved."
    )


def flashback_reveal(world: World) -> None:
    child: Entity = world.facts["child"]  # type: ignore[assignment]
    parent: Entity = world.facts["parent"]  # type: ignore[assignment]
    missing: Entity = world.facts["missing"]  # type: ignore[assignment]
    culprit: str = world.facts["culprit"]  # type: ignore[assignment]
    reason: str = world.facts["culprit_reason"]  # type: ignore[assignment]

    child.memes["focus"] = 1
    world.say(
        f"Then {child.label} remembered a flashback: yesterday, {missing.label} had been left near the floor."
    )
    world.say(
        f"In the flashback, {reason}"
    )
    if culprit == "dog":
        world.say(
            f"The dog had not meant any trouble. It only wanted to chase something tasty."
        )
    elif culprit == "wind":
        world.say(
            f"The wind had slipped through the open window and given the item a quiet push."
        )
    else:
        world.say(
            f"The sibling had meant to be helpful, but the item got tucked away in the wrong place."
        )
    world.say(
        f"That was the answer: the missing thing was not stolen, only misplaced."
    )


def resolve_happy_ending(world: World) -> None:
    child: Entity = world.facts["child"]  # type: ignore[assignment]
    parent: Entity = world.facts["parent"]  # type: ignore[assignment]
    missing: Entity = world.facts["missing"]  # type: ignore[assignment]

    child.memes["whelm"] = 0
    child.memes["relief"] = 1
    missing.hidden = False
    missing.location = "back where it belonged"
    world.say(
        f"They found {missing.phrase} and set it back in its proper place."
    )
    world.say(
        f"{child.label} felt whelm again, but this time it was whelm with relief."
    )
    world.say(
        f"{parent.label} smiled and said, \"Good detectives notice the truth.\""
    )
    world.say(
        f"By bedtime, the room was calm, the clues made sense, and {child.label} slept beside the returned {missing.label}."
    )


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    child: Entity = world.facts["child"]  # type: ignore[assignment]
    missing: Entity = world.facts["missing"]  # type: ignore[assignment]
    room: Room = world.facts["room"]  # type: ignore[assignment]
    return [
        f"Write a child-friendly whodunit set in {room.name} about {child.label} and a missing {missing.label}.",
        f"Tell a short mystery story with a flashback clue and a happy ending that includes the word whelm.",
        f"Write a gentle detective story where the missing {missing.label} turns out to be misplaced, not stolen.",
    ]


def story_qa(world: World) -> list[QAItem]:
    child: Entity = world.facts["child"]  # type: ignore[assignment]
    parent: Entity = world.facts["parent"]  # type: ignore[assignment]
    missing: Entity = world.facts["missing"]  # type: ignore[assignment]
    room: Room = world.facts["room"]  # type: ignore[assignment]
    culprit: str = world.facts["culprit"]  # type: ignore[assignment]
    reason: str = world.facts["culprit_reason"]  # type: ignore[assignment]

    return [
        QAItem(
            question=f"What was the story about in {room.name}?",
            answer=(
                f"It was about {child.label}, {parent.label}, and a missing {missing.phrase}. "
                f"They tried to solve the mystery together."
            ),
        ),
        QAItem(
            question=f"How did {child.label} feel when the {missing.label} was gone?",
            answer=(
                f"{child.label} felt whelm with worry at first, because the {missing.label} was missing "
                f"and nobody knew where it had gone."
            ),
        ),
        QAItem(
            question="What helped them solve the mystery?",
            answer=(
                "A careful search and a flashback helped. The clues showed that the item had been moved, "
                f"and the flashback explained that {reason.lower()}"
            ),
        ),
        QAItem(
            question="What was the happy ending?",
            answer=(
                f"They found the {missing.label}, put it back where it belonged, and {child.label} felt "
                f"whelm with relief instead of worry."
            ),
        ),
        QAItem(
            question=f"Who did the family think might have caused the problem?",
            answer=(
                f"They followed the clues and considered the {culprit}, but the ending showed the item was "
                f"only misplaced rather than stolen."
            ),
        ),
    ]


WORLD_KNOWLEDGE = {
    "whodunit": [
        QAItem(
            question="What is a whodunit?",
            answer=(
                "A whodunit is a mystery story where the characters try to figure out who did something "
                "or what caused a problem."
            ),
        )
    ],
    "flashback": [
        QAItem(
            question="What is a flashback in a story?",
            answer=(
                "A flashback is a scene that shows something that happened earlier, so the reader can learn "
                "important background information."
            ),
        )
    ],
    "clue": [
        QAItem(
            question="What is a clue?",
            answer=(
                "A clue is a small piece of information that helps someone solve a mystery."
            ),
        )
    ],
    "whelm": [
        QAItem(
            question="What does it mean to feel whelm with relief?",
            answer=(
                "It means to feel strongly filled up by relief, like a big wave of calm after worry."
            ),
        )
    ],
}


def world_qa(world: World) -> list[QAItem]:
    return [item for key in ["whodunit", "flashback", "clue", "whelm"] if key in WORLD_KNOWLEDGE for item in WORLD_KNOWLEDGE[key]]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A story is valid when the chosen missing item can plausibly be misplaced in the room.
valid(Room, Missing, Culprit) :- room(Room), missing(Missing), culprit(Culprit),
                                 placeable(Room, Missing), culprit_plausible(Culprit).

% A happy ending is always tied to a reveal and a returned item.
happy_end(Room, Missing) :- valid(Room, Missing, _).

% A flashback is used whenever the mystery is solvable.
uses_flashback(Room, Missing) :- happy_end(Room, Missing).

#show valid/3.
#show happy_end/2.
#show uses_flashback/2.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for room_id in ROOMS:
        lines.append(asp.fact("room", room_id))
    for missing_id in MISSING_ITEMS:
        lines.append(asp.fact("missing", missing_id))
    for culprit_id in CULPRITS:
        lines.append(asp.fact("culprit", culprit_id))
        lines.append(asp.fact("culprit_plausible", culprit_id))
    for room_id, room in ROOMS.items():
        for spot in room.spots:
            lines.append(asp.fact("placeable", room_id, spot))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_triples() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_triples())
    if py == cl:
        print(f"OK: ASP parity holds for {len(py)} story combinations.")
        return 0
    print("Mismatch between Python and ASP:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in ASP:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Validation / generation
# ---------------------------------------------------------------------------

def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for room in ROOMS:
        for missing in MISSING_ITEMS:
            for culprit in CULPRITS:
                combos.append((room, missing, culprit))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny whodunit storyworld with flashback and happy ending.")
    ap.add_argument("--room", choices=sorted(ROOMS))
    ap.add_argument("--missing", choices=sorted(MISSING_ITEMS))
    ap.add_argument("--culprit", choices=sorted(CULPRITS))
    ap.add_argument("--name", choices=CHILD_NAMES)
    ap.add_argument("--gender", choices=GENDERS)
    ap.add_argument("--parent", choices=PARENTS)
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
    room = args.room or rng.choice(sorted(ROOMS))
    missing = args.missing or rng.choice(sorted(MISSING_ITEMS))
    culprit = args.culprit or rng.choice(sorted(CULPRITS))
    gender = args.gender or rng.choice(GENDERS)
    name = args.name or rng.choice(CHILD_NAMES)
    parent = args.parent or rng.choice(PARENTS)
    return StoryParams(
        room=room,
        missing=missing,
        culprit=culprit,
        child_name=name,
        child_gender=gender,
        parent_type=parent,
    )


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    narrate_setup(world)
    suspect_and_whelm(world)
    add_clues(world)
    flashback_reveal(world)
    resolve_happy_ending(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: hidden={e.hidden} location={e.location} memes={dict(e.memes)}")
    for c in world.clues.values():
        lines.append(f"clue {c.id}: {c.phrase} @ {c.location}")
    lines.append(f"history_len={len(world.history)}")
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
        print(asp_program("#show valid/3.\n#show happy_end/2.\n#show uses_flashback/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid/3."))
        print(f"{len(asp.atoms(model, 'valid'))} valid combos.")
        for atom in sorted(set(asp.atoms(model, "valid"))):
            print(atom)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        for room in ROOMS:
            for missing in MISSING_ITEMS:
                for culprit in CULPRITS:
                    params = StoryParams(
                        room=room,
                        missing=missing,
                        culprit=culprit,
                        child_name=CHILD_NAMES[(hash((room, missing, culprit)) % len(CHILD_NAMES))],
                        child_gender=GENDERS[(hash((culprit, missing)) % len(GENDERS))],
                        parent_type=PARENTS[(hash(room) % len(PARENTS))],
                        seed=base_seed,
                    )
                    samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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

    for idx, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.child_name}: {p.missing} in {p.room} with {p.culprit}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
