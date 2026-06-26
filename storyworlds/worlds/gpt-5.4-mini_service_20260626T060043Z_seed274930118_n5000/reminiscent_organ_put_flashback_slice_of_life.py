#!/usr/bin/env python3
"""
A small story world about a remembered afternoon, an old organ, and the gentle
work of putting things back in order.

The source premise:
- A child finds an old organ in a quiet room.
- The sound brings back a flashback of a loved one.
- Someone helps put the room, the bench, and the music back into place.
- The ending is calm, slice-of-life, and emotionally warm.
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

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing" | "place"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    plural: bool = False
    worn_by: Optional[str] = None
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
    has_organ: bool = True
    tidy: bool = False
    quiet: bool = True


@dataclass
class StoryParams:
    name: str
    gender: str
    parent: str
    room: str
    seed: Optional[int] = None


NAMES_GIRL = ["Mia", "Lina", "Nora", "June", "Ava", "Ella", "Ruby", "Iris"]
NAMES_BOY = ["Eli", "Noah", "Theo", "Finn", "Owen", "Leo", "Milo", "Jack"]
PARENTS = {"mother": "mother", "father": "father"}
ROOMS = [
    "the music room",
    "the sunroom",
    "the front parlor",
    "the old family room",
]


class World:
    def __init__(self, room: Room) -> None:
        self.room = room
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.facts: dict = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def render(self) -> str:
        return " ".join(self.lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Slice-of-life flashback story world about an organ and a remembered afternoon."
    )
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--room", choices=ROOMS)
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
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES_GIRL if gender == "girl" else NAMES_BOY)
    parent = args.parent or rng.choice(["mother", "father"])
    room = args.room or rng.choice(ROOMS)
    return StoryParams(name=name, gender=gender, parent=parent, room=room)


def _article(word: str) -> str:
    return "an" if word[:1].lower() in "aeiou" else "a"


def tell(params: StoryParams) -> World:
    room = Room(name=params.room)
    world = World(room)

    child = world.add(Entity(id="child", kind="character", type=params.gender, label=params.name))
    parent = world.add(Entity(id="parent", kind="character", type=params.parent, label=f"the {params.parent}"))
    organ = world.add(Entity(
        id="organ",
        type="organ",
        label="organ",
        phrase="an old wooden organ with yellowed keys",
        caretaker=parent.id,
    ))
    bench = world.add(Entity(
        id="bench",
        type="bench",
        label="bench",
        phrase="a narrow bench with a soft cushion",
        caretaker=parent.id,
    ))

    child.memes["curious"] = 1
    child.memes["warmth"] = 1
    parent.memes["care"] = 1

    world.say(
        f"{child.label} wandered into {world.room.name} and noticed {organ.phrase}."
    )
    world.say(
        f"{child.pronoun().capitalize()} sat on the {bench.label} and touched the keys with careful fingers."
    )
    world.say(
        f"The first note sounded soft and a little dusty, which made {child.label} pause."
    )

    # Flashback beat
    child.memes["reminiscent"] = 1
    world.facts["flashback"] = True
    world.say(
        f"That sound felt reminiscent of a summer afternoon long ago, and the room seemed to open into a flashback."
    )
    world.say(
        f"{child.label} remembered standing beside {child.pronoun('possessive')} {params.parent} while someone sang nearby."
    )

    # Gentle slice-of-life tension: the organ is out of place and needs care.
    organ.meters["dust"] = 1
    room.tidy = False
    world.say(
        f"The organ had been left with a thin layer of dust, and the room looked like it needed a little putting back together."
    )
    world.say(
        f"{params.parent.capitalize()} smiled and said they could put things right after dinner."
    )

    # Resolution
    bench.meters["placed"] = 1
    organ.meters["dusted"] = 1
    room.tidy = True
    room.quiet = False
    child.memes["joy"] = 1
    parent.memes["joy"] = 1

    world.say(
        f"Together they dusted the organ, put the bench straight, and opened the curtains for the late light."
    )
    world.say(
        f"{child.label} played one more small melody, and the flashback turned sweet instead of far away."
    )
    world.say(
        f"By the end, the room felt calm again, and the old organ looked ready for tomorrow."
    )

    world.facts.update(
        child=child,
        parent=parent,
        organ=organ,
        bench=bench,
        room=room,
    )
    return world


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    prompts = [
        f'Write a gentle slice-of-life story about a child named {params.name}, an organ, and a flashback.',
        f"Tell a calm story where someone finds an old organ in {params.room} and puts the room back in order.",
        f'Write a child-friendly story that uses the words "reminiscent", "organ", and "put".',
    ]
    story_qa = [
        QAItem(
            question=f"Why did the room feel reminiscent of an older day?",
            answer="The organ's soft sound brought back a flashback of a summer afternoon from before, so the room felt full of memory.",
        ),
        QAItem(
            question=f"What did {params.name} and {params.parent} put back in place?",
            answer="They put the bench straight and helped the old organ get dusted and ready again.",
        ),
    ]
    world_qa = [
        QAItem(
            question="What is an organ?",
            answer="An organ is a keyboard instrument that makes music when someone plays its keys and pedals.",
        ),
        QAItem(
            question="What does reminiscent mean?",
            answer="Reminiscent means something makes you think of a memory or reminds you of something from before.",
        ),
        QAItem(
            question="What does it mean to put something back in order?",
            answer="It means to arrange things neatly again so the place feels tidy and settled.",
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


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    lines.append(f"room: {world.room.name} tidy={world.room.tidy} quiet={world.room.quiet}")
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        parts = []
        if meters:
            parts.append(f"meters={meters}")
        if memes:
            parts.append(f"memes={memes}")
        if e.phrase:
            parts.append(f"phrase={e.phrase}")
        lines.append(f"  {e.id}: ({e.type}) {' '.join(parts)}")
    return "\n".join(lines)


ASP_RULES = r"""
% Minimal declarative twin for story selection.
valid_story(Name, Gender, Parent, Room) :- gender_ok(Gender), parent_ok(Parent), room_ok(Room), name_ok(Name, Gender).
gender_ok(girl). gender_ok(boy).
parent_ok(mother). parent_ok(father).
room_ok(music_room). room_ok(sunroom). room_ok(front_parlor). room_ok(old_family_room).
name_ok(mia, girl). name_ok(lina, girl). name_ok(nora, girl). name_ok(june, girl).
name_ok(ava, girl). name_ok(ella, girl). name_ok(ruby, girl). name_ok(iris, girl).
name_ok(eli, boy). name_ok(noah, boy). name_ok(theo, boy). name_ok(finn, boy).
name_ok(owen, boy). name_ok(leo, boy). name_ok(milo, boy). name_ok(jack, boy).
#show valid_story/4.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for g in ["girl", "boy"]:
        lines.append(asp.fact("gender_ok", g))
    for p in ["mother", "father"]:
        lines.append(asp.fact("parent_ok", p))
    for r in ["music_room", "sunroom", "front_parlor", "old_family_room"]:
        lines.append(asp.fact("room_ok", r))
    for n in NAMES_GIRL:
        lines.append(asp.fact("name_ok", n.lower(), "girl"))
    for n in NAMES_BOY:
        lines.append(asp.fact("name_ok", n.lower(), "boy"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    return 0


def generate_one(args: argparse.Namespace, rng: random.Random) -> StorySample:
    params = resolve_params(args, rng)
    return generate(params)


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program(""))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for i, room in enumerate(ROOMS):
            params = StoryParams(
                name=NAMES_GIRL[i % len(NAMES_GIRL)],
                gender="girl" if i % 2 == 0 else "boy",
                parent="mother" if i % 2 == 0 else "father",
                room=room,
                seed=base_seed + i,
            )
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        for i in range(max(1, args.n) * 20):
            sample = generate_one(args, random.Random(base_seed + i))
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)
            if len(samples) >= max(1, args.n):
                break

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
