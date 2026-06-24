#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260624T081143Z_seed2038046945_n100/furniture_flashback_whodunit.py
==============================================================================================================

A small standalone storyworld: a child-facing whodunit built around furniture,
with a flashback that explains the clue and resolves the mystery.

Premise:
- A familiar room has a missing, moved, or mismatched piece of furniture.
- The hero notices one strange clue.
- A flashback reveals the earlier cause.
- The culprit is not a villain; the answer is a practical fix.

The story is driven by world state:
- furniture pieces have physical state in meters (moved, hidden, scratched)
- characters have emotional state in memes (curiosity, worry, relief)
- a simple clue chain determines the culprit and the reveal

Contract notes:
- Exposes StoryParams, registries, build_parser, resolve_params, generate, emit, main
- Imports storyworlds/results.py eagerly
- Imports storyworlds/asp.py lazily inside ASP helpers
- Includes inline ASP_RULES and asp_facts()
- Supports --verify, --asp, --show-asp, --json, --qa, --trace, --all, -n, --seed
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

# Make shared result containers importable when run directly.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    moved_by: Optional[str] = None
    hidden_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self):
        self.meters.setdefault("moved", 0.0)
        self.meters.setdefault("scratched", 0.0)
        self.meters.setdefault("dusty", 0.0)
        self.memes.setdefault("curiosity", 0.0)
        self.memes.setdefault("worry", 0.0)
        self.memes.setdefault("relief", 0.0)

    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Room:
    name: str
    place_detail: str
    affordances: set[str] = field(default_factory=set)


@dataclass
class Furniture:
    id: str
    label: str
    phrase: str
    room: str
    movable: bool = True
    heavy: bool = False
    clueable: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Person:
    id: str
    kind: str = "character"
    type: str = "child"
    label: str = ""
    role: str = ""
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self):
        self.memes.setdefault("curiosity", 0.0)
        self.memes.setdefault("worry", 0.0)
        self.memes.setdefault("relief", 0.0)

    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "she", "object": "her", "possessive": "her"}[case]


@dataclass
class StoryParams:
    room: str
    furniture: str
    clue: str
    name: str
    helper: str
    seed: Optional[int] = None


ROOMS = {
    "living_room": Room(
        name="the living room",
        place_detail="The living room was quiet and cozy, with a rug, a lamp, and a little table near the sofa.",
        affordances={"moving", "hiding"},
    ),
    "bedroom": Room(
        name="the bedroom",
        place_detail="The bedroom was small and neat, with a bed, a dresser, and a toy chest by the wall.",
        affordances={"moving", "hiding"},
    ),
    "study": Room(
        name="the study",
        place_detail="The study was full of books, with a desk, a chair, and a shelf that cast a long shadow.",
        affordances={"moving", "hiding"},
    ),
}

FURNITURE = {
    "chair": Furniture(
        id="chair",
        label="chair",
        phrase="a little wooden chair",
        room="living_room",
        movable=True,
        clueable=True,
        tags={"scratch", "under"},
    ),
    "stool": Furniture(
        id="stool",
        label="stool",
        phrase="a round stool with one wobbly leg",
        room="study",
        movable=True,
        clueable=True,
        tags={"moved", "near"},
    ),
    "toy_chest": Furniture(
        id="toy_chest",
        label="toy chest",
        phrase="a painted toy chest",
        room="bedroom",
        movable=False,
        clueable=True,
        tags={"hidden", "inside"},
    ),
    "sofa": Furniture(
        id="sofa",
        label="sofa",
        phrase="a soft sofa with bright cushions",
        room="living_room",
        movable=False,
        clueable=False,
        tags={"under"},
    ),
    "desk": Furniture(
        id="desk",
        label="desk",
        phrase="a narrow desk with a green pencil cup",
        room="study",
        movable=False,
        clueable=False,
        tags={"dust"},
    ),
}

CLIUES = {
    "moved": "The clue is that a chair leg was not where it should have been.",
    "hidden": "The clue is that something small was tucked where no one first thought to look.",
    "scratch": "The clue is that a careful scratch marked the wood.",
    "dust": "The clue is that a clean stripe cut through the dust.",
}

HELPERS = {
    "cat": "cat",
    "dog": "dog",
    "wind": "wind",
}

GUEST_NAMES = ["Mia", "Nora", "Leo", "Ben", "Ava", "Milo", "Zoe", "Ivy"]
ROLES = ["curious", "careful", "gentle", "bright"]


class World:
    def __init__(self, room: Room) -> None:
        self.room = room
        self.entities: dict[str, object] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.flashback_mode: bool = False

    def add(self, ent):
        self.entities[getattr(ent, "id")] = ent
        return ent

    def get(self, eid: str):
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy
        w = World(self.room)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


def _event_move(world: World, mover: Person, furniture: Entity, helper: str) -> None:
    key = ("move", furniture.id)
    if key in world.fired:
        return
    world.fired.add(key)
    furniture.meters["moved"] += 1
    furniture.moved_by = mover.id
    mover.memes["curiosity"] += 1
    world.say(f"Earlier that day, {mover.id} had helped move the {furniture.label} while the {helper} barked and the room felt busier than usual.")


def _event_hide(world: World, mover: Person, furniture: Entity) -> None:
    key = ("hide", furniture.id)
    if key in world.fired:
        return
    world.fired.add(key)
    furniture.hidden_by = mover.id
    furniture.meters["dusty"] += 0.5
    world.say(f"In the flashback, {mover.id} tucked the clue away to make floor space for a game, then forgot to put it back.")


def _event_scratch(world: World, furniture: Entity) -> None:
    key = ("scratch", furniture.id)
    if key in world.fired:
        return
    world.fired.add(key)
    furniture.meters["scratched"] += 1
    world.say("A tiny scratch on the wood became the sort of clue that only someone careful would notice.")


def tell(room: Room, furniture: Furniture, clue: str, name: str, helper: str, role: str) -> World:
    world = World(room)
    hero = world.add(Person(id=name, label=name, role=role))
    culprit = world.add(Person(id="helper", label=helper, role="helper"))
    piece = world.add(Entity(id=furniture.id, type="furniture", label=furniture.label, phrase=furniture.phrase))
    piece.meters["moved"] = 0.0

    world.say(f"{hero.id} was a {role} child who liked noticing things other people missed.")
    world.say(f"{room.place_detail}")
    world.say(f"That afternoon, {hero.id} saw that the {piece.label} looked slightly wrong, as if the room itself had blinked.")
    world.say(CLIUES[clue])

    world.para()
    world.say(f"{hero.id} frowned and looked under, over, and beside the furniture.")
    if clue == "moved":
        _event_move(world, culprit, piece, helper)
    elif clue == "hidden":
        _event_hide(world, culprit, piece)
    elif clue == "scratch":
        _event_scratch(world, piece)
    else:
        piece.meters["dusty"] += 1
        world.say("The dust was brushed in one narrow line, like a secret trail across the shelf.")

    world.para()
    world.flashback_mode = True
    world.say(f"Then came a flashback: {hero.id} remembered what had happened before lunch.")
    if clue in {"moved", "hidden"}:
        world.say(f"{helper.capitalize()} had chased a toy, and the {piece.label} had been shifted aside to clear a path.")
    if clue == "moved":
        world.say(f"That was why one leg of the {piece.label} no longer lined up with the rug.")
    elif clue == "hidden":
        world.say(f"That was why the clue had been tucked out of sight in the {furniture.room.replace('_', ' ')}.")
    elif clue == "scratch":
        world.say(f"That was why the scratch sat at the same height as a stubborn buckle on a game box.")
    else:
        world.say("That was why the clean stripe in the dust pointed straight to the shelf edge.")

    world.para()
    hero.memes["worry"] += 1
    world.say(f"{hero.id} realized there was no thief at all, only a small mix-up.")
    world.say(f"{hero.id} put the {piece.label} back where it belonged, and the room looked steady again.")
    world.say(f"When {hero.id} smiled, the mystery felt solved and the house felt calm.")

    world.facts.update(hero=hero, culprit=culprit, piece=piece, room=room, clue=clue, helper=helper)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a short whodunit for a young child about furniture in {f['room'].name}, with one clue and a flashback.",
        f"Tell a cozy mystery where {f['hero'].id} notices the {f['piece'].label} is odd, remembers an earlier moment, and solves the puzzle.",
        f"Write a simple story about a misplaced piece of furniture and reveal the answer through a flashback.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    piece = f["piece"]
    room = f["room"]
    culprit = f["culprit"]
    clue = f["clue"]
    return [
        QAItem(
            question=f"What did {hero.id} notice first in {room.name}?",
            answer=f"{hero.id} noticed that the {piece.label} looked a little wrong, like it had been moved or hidden after someone used the room.",
        ),
        QAItem(
            question=f"What clue helped solve the mystery?",
            answer=f"The clue was that {CLIUES[clue].lower().replace('the clue is that ', '')}",
        ),
        QAItem(
            question=f"What did the flashback show happened earlier?",
            answer=f"The flashback showed that {culprit.id} had moved things around while helping in the room, which explained why the {piece.label} did not look right at first.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is furniture?",
            answer="Furniture is the things in a room that people use, like chairs, tables, beds, and sofas.",
        ),
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is a part of the story that shows something that happened earlier, before the main moment.",
        ),
        QAItem(
            question="What is a whodunit?",
            answer="A whodunit is a mystery story where someone tries to figure out what happened and who caused it.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        if isinstance(e, Entity):
            lines.append(f"{e.id}: meters={dict(e.meters)} memes={dict(e.memes)} moved_by={e.moved_by} hidden_by={e.hidden_by}")
        elif isinstance(e, Person):
            lines.append(f"{e.id}: role={e.role} memes={dict(e.memes)}")
    lines.append(f"fired={sorted(world.fired)}")
    return "\n".join(lines)


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for room_id in ROOMS:
        for furniture_id, furniture in FURNITURE.items():
            if furniture.room != room_id:
                continue
            for clue in CLIUES:
                combos.append((room_id, furniture_id, clue))
    return combos


@dataclass
class RegistryRow:
    room: str
    furniture: str
    clue: str


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A cozy furniture whodunit with a flashback.")
    ap.add_argument("--room", choices=sorted(ROOMS))
    ap.add_argument("--furniture", choices=sorted(FURNITURE))
    ap.add_argument("--clue", choices=sorted(CLIUES))
    ap.add_argument("--name")
    ap.add_argument("--helper", choices=sorted(HELPERS))
    ap.add_argument("--role", choices=sorted(ROLES))
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
    if args.furniture and args.room and FURNITURE[args.furniture].room != args.room:
        raise StoryError("The chosen furniture does not belong in that room.")
    combos = valid_combos()
    if args.room:
        combos = [c for c in combos if c[0] == args.room]
    if args.furniture:
        combos = [c for c in combos if c[1] == args.furniture]
    if args.clue:
        combos = [c for c in combos if c[2] == args.clue]
    if not combos:
        raise StoryError("No valid furniture mystery matches those options.")
    room_id, furniture_id, clue = rng.choice(sorted(combos))
    name = args.name or rng.choice(GUEST_NAMES)
    helper = args.helper or rng.choice(list(HELPERS))
    role = args.role or rng.choice(ROLES)
    return StoryParams(room=room_id, furniture=furniture_id, clue=clue, name=name, helper=helper, seed=None)


def generate(params: StoryParams) -> StorySample:
    room = ROOMS[params.room]
    furniture = FURNITURE[params.furniture]
    world = tell(room, furniture, params.clue, params.name, params.helper, random.choice(ROLES) if False else "curious")
    # overwrite role with params if provided through resolve
    world.facts["hero"].role = "curious"
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


ASP_RULES = r"""
room(R) :- room_fact(R).
furniture(F) :- furniture_fact(F).
clue(C) :- clue_fact(C).

mystery(R,F,C) :- room_has(R,F), clue_fact(C), furniture_fact(F), room_fact(R).
compatible(R,F) :- room_has(R,F).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for rid in ROOMS:
        lines.append(asp.fact("room_fact", rid))
    for fid, f in FURNITURE.items():
        lines.append(asp.fact("furniture_fact", fid))
        lines.append(asp.fact("room_has", f.room, fid))
    for c in CLIUES:
        lines.append(asp.fact("clue_fact", c))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show compatible/2."))
    asp_set = set(asp.atoms(model, "compatible"))
    py_set = {(r, f) for (r, f, _) in valid_combos()}
    if asp_set == py_set:
        print(f"OK: ASP matches Python ({len(py_set)} room/furniture pairs).")
        return 0
    print("MISMATCH between ASP and Python")
    print("only asp:", sorted(asp_set - py_set))
    print("only py:", sorted(py_set - asp_set))
    return 1


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
        print(asp_program("#show compatible/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show compatible/2."))
        print(sorted(asp.atoms(model, "compatible")))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for room_id, furniture_id, clue in valid_combos():
            p = StoryParams(room=room_id, furniture=furniture_id, clue=clue, name="Mia", helper="cat", seed=base_seed)
            samples.append(generate(p))
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            rng = random.Random(base_seed + i)
            i += 1
            try:
                p = resolve_params(args, rng)
            except StoryError as err:
                print(err)
                return
            p.seed = base_seed + i
            s = generate(p)
            if s.story in seen:
                continue
            seen.add(s.story)
            samples.append(s)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
