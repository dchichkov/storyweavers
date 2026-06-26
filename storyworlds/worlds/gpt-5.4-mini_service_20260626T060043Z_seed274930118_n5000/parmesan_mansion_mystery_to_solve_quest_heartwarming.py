#!/usr/bin/env python3
"""
A small heartwarming mystery-quest story world about a mansion, parmesan,
and a gentle search for what went missing.
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
    kind: str
    label: str
    type: str = "thing"
    owner: Optional[str] = None
    location: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Room:
    id: str
    label: str
    neighbors: list[str] = field(default_factory=list)


@dataclass
class World:
    rooms: dict[str, Room]
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

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
# Parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    seed: Optional[int] = None
    name: str = "Mina"
    child_type: str = "girl"
    companion: str = "cat"
    companion_name: str = "Pip"
    parent_name: str = "Nora"
    place: str = "mansion"


ROOMS = {
    "foyer": Room("foyer", "the foyer", ["kitchen", "hall"]),
    "kitchen": Room("kitchen", "the kitchen", ["foyer", "pantry"]),
    "pantry": Room("pantry", "the pantry", ["kitchen"]),
    "hall": Room("hall", "the long hall", ["foyer", "library", "dining"]),
    "library": Room("library", "the library", ["hall"]),
    "dining": Room("dining", "the dining room", ["hall"]),
    "garden": Room("garden", "the garden", ["kitchen"]),
}

VALID_COMBOS = [
    ("mansion", "foyer", "kitchen", "pantry"),
]


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------
def build_world() -> World:
    return World(rooms=ROOMS)


def _move(world: World, ent: Entity, room_id: str) -> None:
    ent.location = room_id


def _room_name(world: World, room_id: str) -> str:
    return world.rooms[room_id].label


def tell(params: StoryParams) -> World:
    world = build_world()

    child = world.add(Entity(
        id=params.name,
        kind="character",
        label=params.name,
        type=params.child_type,
        location="foyer",
        meters={"curiosity": 1.0, "joy": 1.0, "care": 0.0},
        memes={"hope": 1.0, "worry": 0.0},
    ))
    parent = world.add(Entity(
        id=params.parent_name,
        kind="character",
        label=params.parent_name,
        type="mother",
        location="hall",
        meters={"care": 1.0},
        memes={"warmth": 1.0},
    ))
    companion = world.add(Entity(
        id=params.companion_name,
        kind="character",
        label=params.companion_name,
        type=params.companion,
        location="foyer",
        meters={"curiosity": 1.0},
        memes={"trust": 1.0},
    ))
    parmesan = world.add(Entity(
        id="parmesan",
        kind="thing",
        label="parmesan",
        type="cheese",
        owner=params.name,
        location="kitchen",
        meters={"smell": 1.0, "precious": 1.0},
        memes={"value": 1.0},
    ))
    note = world.add(Entity(
        id="note",
        kind="thing",
        label="a tiny note",
        type="note",
        location="foyer",
        meters={"hidden": 1.0},
    ))

    # Act 1: a gentle mystery is noticed.
    world.say(
        f"{child.label} lived in a quiet mansion where every hallway had a creak and every room had a story."
    )
    world.say(
        f"One afternoon, {child.label} saw that the parmesan for supper was missing from the kitchen."
    )
    world.say(
        f"{companion.label} sat by the door as if it knew the house was asking for help."
    )

    world.para()

    # Act 2: the quest.
    _move(world, child, "kitchen")
    _move(world, companion, "kitchen")
    world.say(
        f"{child.label} began a little quest to solve the mystery, starting in {_room_name(world, child.location)}."
    )
    world.say(
        f"Behind a bowl, {child.pronoun('subject')} found a tiny note that said, 'Look where the cold air sleeps.'"
    )
    world.say(
        f"{child.label} smiled, because the clue felt kind, not scary."
    )

    world.para()

    # Turn: follow clue to pantry.
    _move(world, child, "pantry")
    _move(world, companion, "pantry")
    world.say(
        f"That clue led {child.label} to {_room_name(world, child.location)}, where the parmesan had been tucked beside the bread basket."
    )
    world.say(
        f"It was not stolen at all; {parent.label} had hidden it there to keep it safe for a surprise supper."
    )
    world.say(
        f"{child.label} laughed softly, and the whole mansion seemed to relax with relief."
    )

    world.para()

    # Act 3: warm ending and resolution.
    parmesan.location = "kitchen"
    note.location = "desk"
    child.meters["joy"] += 1.0
    child.memes["worry"] = 0.0
    parent.meters["care"] += 1.0

    world.say(
        f"Together they carried the parmesan back to the kitchen, and {child.label} helped grate it into a golden cloud over dinner."
    )
    world.say(
        f"At supper, the mansion felt full of comfort, and the mystery had turned into a happy family story."
    )

    world.facts.update(
        child=child,
        parent=parent,
        companion=companion,
        parmesan=parmesan,
        note=note,
        missing_room="kitchen",
        found_room="pantry",
        place=params.place,
    )
    return world


# ---------------------------------------------------------------------------
# Content and QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    return [
        "Write a heartwarming mystery story about a parmesan that goes missing in a mansion and is found through a gentle quest.",
        f"Tell a child-friendly story where {child.label} searches the mansion for parmesan and learns the mystery has a kind answer.",
        "Write a short, cozy tale with a clue, a quest, and a happy family ending in a mansion kitchen.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    companion = f["companion"]
    parmesan = f["parmesan"]
    return [
        QAItem(
            question=f"What mystery did {child.label} try to solve in the mansion?",
            answer=f"{child.label} tried to solve the mystery of the missing parmesan.",
        ),
        QAItem(
            question=f"Where did {child.label} find the parmesan after following the clue?",
            answer=f"{child.label} found the parmesan in the pantry beside the bread basket.",
        ),
        QAItem(
            question=f"Who had hidden the parmesan safely?",
            answer=f"{parent.label} had hidden the parmesan safely for a surprise supper.",
        ),
        QAItem(
            question=f"Who stayed beside {child.label} during the quest?",
            answer=f"{companion.label} stayed beside {child.label} during the quest.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"By the end, the missing parmesan was found, and the mansion felt warm and happy again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is parmesan?",
            answer="Parmesan is a hard, salty cheese often grated over pasta or soup.",
        ),
        QAItem(
            question="What is a mansion?",
            answer="A mansion is a large house with many rooms and long hallways.",
        ),
        QAItem(
            question="What is a mystery?",
            answer="A mystery is a puzzling question or problem that someone tries to understand.",
        ),
        QAItem(
            question="What is a quest?",
            answer="A quest is a search or adventure to find something or solve a problem.",
        ),
    ]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
child_mystery(C) :- child(C).
missing_item(parmesan).
quest(C) :- child_mystery(C), missing_item(parmesan).
resolved(C) :- quest(C), found(parmesan, pantry), hidden_by(parent).
#show child_mystery/1.
#show quest/1.
#show resolved/1.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = [
        asp.fact("child", "mina"),
        asp.fact("missing_item", "parmesan"),
        asp.fact("found", "parmesan", "pantry"),
        asp.fact("hidden_by", "parent"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_parity_ok() -> bool:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show child_mystery/1.\n#show quest/1.\n#show resolved/1."))
    atoms = set((s.name, tuple(a.name if hasattr(a, "name") else getattr(a, "string", getattr(a, "number", None)) for a in s.arguments)) for s in model)
    expected = {
        ("child_mystery", ("mina",)),
        ("quest", ("mina",)),
        ("resolved", ("mina",)),
    }
    return atoms == expected


# ---------------------------------------------------------------------------
# Parsers / generation
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming mansion mystery about parmesan and a quest.")
    ap.add_argument("--name", default="Mina")
    ap.add_argument("--child-type", choices=["girl", "boy"], default="girl")
    ap.add_argument("--companion", choices=["cat", "dog", "rabbit"], default="cat")
    ap.add_argument("--companion-name", default="Pip")
    ap.add_argument("--parent-name", default="Nora")
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
    return StoryParams(
        seed=args.seed,
        name=args.name or rng.choice(["Mina", "Lina", "Toby", "Hugo"]),
        child_type=args.child_type,
        companion=args.companion,
        companion_name=args.companion_name,
        parent_name=args.parent_name,
        place="mansion",
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


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts ==", *[f"{i+1}. {p}" for i, p in enumerate(sample.prompts)]]
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: {e.kind} {e.label} @ {e.location} meters={e.meters} memes={e.memes}")
    return "\n".join(lines)


CURATED = [StoryParams(name="Mina", child_type="girl", companion="cat", companion_name="Pip", parent_name="Nora")]


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
        print(asp_program("#show child_mystery/1.\n#show quest/1.\n#show resolved/1."))
        return

    if args.verify:
        import storyworlds.asp as asp
        ok = asp_parity_ok()
        if ok:
            print("OK: ASP parity matches the Python gate.")
            sys.exit(0)
        print("MISMATCH: ASP parity does not match the Python gate.")
        sys.exit(1)

    if args.asp:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show child_mystery/1.\n#show quest/1.\n#show resolved/1."))
        for atom in model:
            print(atom)
        return

    samples: list[StorySample] = []
    if args.all:
        for p in CURATED:
            samples.append(generate(p))
    else:
        base_seed = args.seed if args.seed is not None else random.randrange(2**31)
        for i in range(max(1, args.n)):
            params = resolve_params(args, random.Random(base_seed + i))
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
