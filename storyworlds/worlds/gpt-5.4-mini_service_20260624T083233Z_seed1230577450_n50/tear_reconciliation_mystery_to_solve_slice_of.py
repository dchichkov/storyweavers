#!/usr/bin/env python3
"""
A small slice-of-life storyworld about a tear, a little mystery, and a warm
reconciliation.

Premise:
- A child notices something torn.
- They try to figure out how it happened.
- Tension grows because someone feels blamed.
- The mystery is solved with a careful look and a gentle talk.
- The ending proves the relationship is repaired.

This world keeps the prose concrete and state-driven: the tear affects an item,
the clue trail changes the characters' feelings, and reconciliation resolves the
mood.
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    handled_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        mapping = {
            "girl": {"subject": "she", "object": "her", "possessive": "her"},
            "boy": {"subject": "he", "object": "him", "possessive": "his"},
            "adult": {"subject": "they", "object": "them", "possessive": "their"},
        }
        return mapping.get(self.type, {"subject": "it", "object": "it", "possessive": "its"})[case]


@dataclass
class Room:
    name: str
    detail: str


@dataclass
class ObjectSpec:
    label: str
    phrase: str
    tearable: bool = True
    can_fix: bool = True


@dataclass
class StoryParams:
    room: str
    object: str
    name: str
    sibling_name: str
    role: str
    seed: Optional[int] = None


ROOMS = {
    "kitchen": Room(name="the kitchen", detail="The table was still set from breakfast."),
    "bedroom": Room(name="the bedroom", detail="A toy basket sat near the bed."),
    "living_room": Room(name="the living room", detail="The couch cushions were a little crooked."),
    "hallway": Room(name="the hallway", detail="Shoes lined the wall in a tidy row."),
}

OBJECTS = {
    "paper_plane": ObjectSpec(label="paper plane", phrase="a folded paper plane"),
    "puzzle_piece": ObjectSpec(label="puzzle corner", phrase="a puzzle corner with a tiny picture on it"),
    "library_page": ObjectSpec(label="library page", phrase="a borrowed page from a picture book"),
    "paper_banner": ObjectSpec(label="paper banner", phrase="a paper banner with bright stars"),
    "stuffed_tag": ObjectSpec(label="stuffed tag", phrase="a little cloth tag on a stuffed animal"),
}

NAMES = ["Maya", "Noah", "Lina", "Eli", "Sofia", "Ben", "Ava", "Owen"]
ROLES = ["girl", "boy"]
SIBLINGS = ["Iris", "Milo", "June", "Sam", "Leah", "Theo", "Nina", "Jack"]


class World:
    def __init__(self, room: Room) -> None:
        self.room = room
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.facts: dict[str, object] = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def render(self) -> str:
        return " ".join(self.lines)

    def para(self) -> None:
        if self.lines and self.lines[-1] != "":
            self.lines.append("")


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life storyworld about a tear, a mystery, and reconciliation.")
    ap.add_argument("--room", choices=ROOMS)
    ap.add_argument("--object", dest="object_", choices=OBJECTS)
    ap.add_argument("--name")
    ap.add_argument("--sibling-name")
    ap.add_argument("--role", choices=ROLES)
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


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for room in ROOMS:
        for obj in OBJECTS:
            combos.append((room, obj))
    return combos


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.room is None or c[0] == args.room)
              and (args.object_ is None or c[1] == args.object_)]
    if not combos:
        raise StoryError("No valid story matches the requested options.")

    room, obj = rng.choice(sorted(combos))
    name = args.name or rng.choice(NAMES)
    sibling_name = args.sibling_name or rng.choice([n for n in SIBLINGS if n != name])
    role = args.role or rng.choice(ROLES)
    return StoryParams(room=room, object=obj, name=name, sibling_name=sibling_name, role=role)


def setup_world(params: StoryParams) -> World:
    world = World(ROOMS[params.room])
    hero = world.add(Entity(id=params.name, kind="character", type=params.role, label=params.name))
    sibling = world.add(Entity(id=params.sibling_name, kind="character", type="boy" if params.role == "girl" else "girl", label=params.sibling_name))
    item_spec = OBJECTS[params.object]
    item = world.add(Entity(
        id="item",
        kind="thing",
        type="thing",
        label=item_spec.label,
        phrase=item_spec.phrase,
        owner=hero.id,
        handled_by=sibling.id,
    ))
    clue = world.add(Entity(
        id="clue",
        kind="thing",
        type="thing",
        label="small clue",
        phrase="a small clue from a sticky candy wrapper",
    ))

    world.facts.update(hero=hero, sibling=sibling, item=item, clue=clue, params=params)
    return world


def open_story(world: World) -> None:
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    item: Entity = world.facts["item"]  # type: ignore[assignment]
    world.say(f"{hero.id} was in {world.room.name}.")
    world.say(f"{world.room.detail}")
    world.say(f"{hero.id} loved {item.phrase}, and it had been sitting on the table all morning.")


def discover_tear(world: World) -> None:
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    sibling: Entity = world.facts["sibling"]  # type: ignore[assignment]
    item: Entity = world.facts["item"]  # type: ignore[assignment]
    clue: Entity = world.facts["clue"]  # type: ignore[assignment]

    item.meters["tear"] = 1.0
    hero.memes["surprise"] = 1.0
    world.say(f"Then {hero.id} saw a tear in {item.label}.")
    world.say(f"{hero.id} frowned and looked around for what had happened.")
    world.say(f"Near the floor, {hero.id} found {clue.phrase}, and that made the little mystery harder to ignore.")

    sibling.memes["worry"] = 1.0
    if sibling.id != hero.id:
        world.say(f"{sibling.id} glanced at the torn edge and looked worried, because it seemed like they might be blamed.")


def investigate(world: World) -> None:
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    sibling: Entity = world.facts["sibling"]  # type: ignore[assignment]
    item: Entity = world.facts["item"]  # type: ignore[assignment]

    hero.memes["curiosity"] = 1.0
    world.say(f"{hero.id} did not shout.")
    world.say(f"Instead, {hero.id} checked the tear closely and noticed it was jagged, not cut with scissors.")
    world.say(f"{hero.id} asked {sibling.id} if they had touched {item.label}.")

    sibling.memes["fear"] = 1.0
    world.say(f"{sibling.id} shook their head and said no, but their voice was small.")


def solve_mystery(world: World) -> None:
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    sibling: Entity = world.facts["sibling"]  # type: ignore[assignment]
    item: Entity = world.facts["item"]  # type: ignore[assignment]
    clue: Entity = world.facts["clue"]  # type: ignore[assignment]

    hero.memes["patience"] = 1.0
    world.say(f"Then {hero.id} noticed a sticky mark on {clue.label}.")
    world.say(f"The clue matched the side of {item.label}, which meant the tear had probably happened when it slipped under a heavy dish or book.")
    world.say(f"That was the mystery to solve: nobody had broken it on purpose.")
    world.say(f"{hero.id} explained the answer to {sibling.id}, and the worried look started to fade.")


def reconcile(world: World) -> None:
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    sibling: Entity = world.facts["sibling"]  # type: ignore[assignment]
    item: Entity = world.facts["item"]  # type: ignore[assignment]

    hero.memes["kindness"] = 1.0
    sibling.memes["relief"] = 1.0
    hero.memes["grudge"] = 0.0
    sibling.memes["grudge"] = 0.0
    world.say(f"{hero.id} smiled and said it was all right.")
    world.say(f"{sibling.id} thanked {hero.id} for looking carefully instead of blaming anyone too fast.")
    world.say(f"Together, they found tape and pressed the torn {item.label} back together as neatly as they could.")
    world.say(f"By the end, the little mystery was solved, and the room felt calm again.")


def tell(params: StoryParams) -> World:
    world = setup_world(params)
    open_story(world)
    world.para()
    discover_tear(world)
    world.para()
    investigate(world)
    world.para()
    solve_mystery(world)
    world.para()
    reconcile(world)
    return world


ASP_RULES = r"""
item_torn(I) :- item(I).
mystery_started(H,I) :- item_torn(I), hero(H).
mystery_solved(H,I) :- mystery_started(H,I), clue(C), found_clue(H,C).
reconciled(H,S) :- solved(H,I), sibling(S), calm(H), calm(S).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for room_id in ROOMS:
        lines.append(asp.fact("room", room_id))
    for obj_id in OBJECTS:
        lines.append(asp.fact("item", obj_id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    return 0


def generation_prompts(world: World) -> list[str]:
    p: StoryParams = world.facts["params"]  # type: ignore[assignment]
    return [
        f"Write a gentle slice-of-life story about a torn {p.object.replace('_', ' ')} in {ROOMS[p.room].name}.",
        f"Tell a short story where {p.name} finds a tear and solves the little mystery with {p.sibling_name}.",
        f"Write a child-friendly story about a small mistake, a mystery to solve, and reconciliation.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p: StoryParams = world.facts["params"]  # type: ignore[assignment]
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    sibling: Entity = world.facts["sibling"]  # type: ignore[assignment]
    item: Entity = world.facts["item"]  # type: ignore[assignment]
    return [
        QAItem(
            question=f"What was torn in the story?",
            answer=f"{hero.id} found a tear in {item.label}, which was {item.phrase}.",
        ),
        QAItem(
            question=f"Who helped solve the mystery?",
            answer=f"{hero.id} solved the mystery with {sibling.id} in {ROOMS[p.room].name}.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with a calm reconciliation, after {hero.id} explained that nobody had torn {item.label} on purpose.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a tear?",
            answer="A tear is a split or rip in something like paper, cloth, or a page.",
        ),
        QAItem(
            question="What does it mean to reconcile?",
            answer="To reconcile means to make peace again after people have felt upset or misunderstood.",
        ),
        QAItem(
            question="What is a mystery?",
            answer="A mystery is something that is not clear at first and needs careful thinking or clues to figure out.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
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


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"{e.id}: {e.kind} {e.label} {' '.join(bits)}")
    return "\n".join(lines)


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
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def valid_selection(args: argparse.Namespace) -> list[tuple[str, str]]:
    combos = valid_combos()
    return [c for c in combos if (args.room is None or c[0] == args.room) and (args.object_ is None or c[1] == args.object_)]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show item_torn/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("ASP mode is available for parity checks, but this world uses a simple curated domain.")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams(room="kitchen", object="paper_plane", name="Maya", sibling_name="Ben", role="girl"),
            StoryParams(room="bedroom", object="library_page", name="Noah", sibling_name="June", role="boy"),
            StoryParams(room="living_room", object="paper_banner", name="Ava", sibling_name="Theo", role="girl"),
            StoryParams(room="hallway", object="stuffed_tag", name="Eli", sibling_name="Lina", role="boy"),
            StoryParams(room="kitchen", object="puzzle_piece", name="Sofia", sibling_name="Jack", role="girl"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
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
        if len(samples) > 1:
            print(f"### variant {i + 1}")
        emit(sample, trace=args.trace, qa=args.qa)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
