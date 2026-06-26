#!/usr/bin/env python3
"""
storyworlds/worlds/tribal_cleat_inner_monologue_slice_of_life.py
=================================================================

A standalone story world for a small slice-of-life tale about a child, a lost
cleat, and the quiet hum of inner monologue that helps them solve a tiny
problem.

The seed premise:
---
A child is getting ready for an ordinary afternoon. One of their soccer cleats
is missing. They worry, think through the day in their head, notice a few small
clues, and find the cleat in a very normal place. Nothing huge happens, but the
day feels better because the child learns to pause, listen to their own thoughts,
and keep going.

World shape:
---
- A child is at home after school.
- They need their cleat for a neighborhood kickabout or practice.
- The missing cleat creates a small tension.
- Inner monologue drives the search.
- A found object, a helpful memory, or a small apology resolves the moment.

This script follows the storyworld contract:
- stdlib-only runtime path
- eager import of results.py
- lazy import of asp.py in ASP helpers
- StoryParams, registries, build_parser, resolve_params, generate, emit, main
- ASP twin with fact emission and verification
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    plural: bool = False
    location: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

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
    name: str
    mood: str
    affords: set[str] = field(default_factory=set)


@dataclass
class ObjectSpec:
    label: str
    phrase: str
    location: str
    tags: set[str] = field(default_factory=set)
    plural: bool = False
    special: bool = False


@dataclass
class StoryParams:
    room: str
    object_name: str
    child_name: str
    child_type: str
    parent_type: str
    clue: str
    seed: Optional[int] = None


class World:
    def __init__(self, room: Room) -> None:
        self.room = room
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.facts: dict = {}

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


ROOMS = {
    "kitchen": Room(name="the kitchen", mood="quiet", affords={"search", "snack"}),
    "entryway": Room(name="the entryway", mood="busy", affords={"search", "leave"}),
    "hallway": Room(name="the hallway", mood="small", affords={"search"}),
    "bedroom": Room(name="the bedroom", mood="soft", affords={"search", "rest"}),
}

OBJECTS = {
    "left_cleat": ObjectSpec(
        label="cleat",
        phrase="one black soccer cleat with a tribal stripe on the side",
        location="under the sofa",
        tags={"cleat", "tribal", "soccer"},
    ),
    "right_cleat": ObjectSpec(
        label="cleat",
        phrase="the matching soccer cleat",
        location="by the backpack",
        tags={"cleat", "soccer"},
    ),
    "library_card": ObjectSpec(
        label="card",
        phrase="a library card with a blue sticker",
        location="on the table",
        tags={"quiet", "search"},
    ),
    "water_bottle": ObjectSpec(
        label="bottle",
        phrase="a water bottle with tiny scratches",
        location="near the door",
        tags={"leave", "search"},
    ),
}

CHILD_NAMES = ["Maya", "Nico", "Ari", "Lena", "Owen", "Iris", "Noah", "Tess"]
CHILD_TYPES = ["girl", "boy"]
PARENT_TYPES = ["mother", "father"]
CLUES = ["under the sofa", "by the backpack", "beside the mat", "near the door"]


def room_detail(room: Room) -> str:
    return {
        "the kitchen": "The kitchen smelled faintly like toast and the afternoon felt a little too quiet.",
        "the entryway": "The entryway was full of shoes lined up like they were waiting for directions.",
        "the hallway": "The hallway had a narrow stripe of sunlight on the floor.",
        "the bedroom": "The bedroom was soft and still, with a blanket folded in a neat square.",
    }.get(room.name, f"{room.name.capitalize()} felt ordinary and calm.")


def searchable_objects() -> list[str]:
    return [k for k, v in OBJECTS.items() if "cleat" in v.tags]


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for room_key, room in ROOMS.items():
        for obj_key, obj in OBJECTS.items():
            if room_key in {"kitchen", "entryway", "hallway", "bedroom"} and "search" in room.affords:
                if "cleat" in obj.tags:
                    combos.append((room_key, obj_key))
    return combos


def path_reason(room: Room, obj: ObjectSpec) -> bool:
    return "search" in room.affords and "cleat" in obj.tags


def explain_rejection(room: Room, obj: ObjectSpec) -> str:
    return (
        f"(No story: {room.name} doesn't give a believable place for a missing cleat search "
        f"that can be solved in a small slice-of-life way.)"
    )


def choose_name(rng: random.Random, child_type: str) -> str:
    return rng.choice(CHILD_NAMES)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Slice-of-life story world: a child, a missing cleat, and a calm inner monologue."
    )
    ap.add_argument("--room", choices=ROOMS)
    ap.add_argument("--object", dest="object_name", choices=OBJECTS)
    ap.add_argument("--name")
    ap.add_argument("--gender", dest="child_type", choices=CHILD_TYPES)
    ap.add_argument("--parent", dest="parent_type", choices=PARENT_TYPES)
    ap.add_argument("--clue", choices=CLUES)
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
    room_key = args.room or rng.choice(list(ROOMS))
    obj_key = args.object_name or rng.choice(searchable_objects())
    room = ROOMS[room_key]
    obj = OBJECTS[obj_key]
    if not path_reason(room, obj):
        raise StoryError(explain_rejection(room, obj))
    child_type = args.child_type or rng.choice(CHILD_TYPES)
    parent_type = args.parent_type or rng.choice(PARENT_TYPES)
    child_name = args.name or choose_name(rng, child_type)
    clue = args.clue or rng.choice(CLUES)
    return StoryParams(
        room=room_key,
        object_name=obj_key,
        child_name=child_name,
        child_type=child_type,
        parent_type=parent_type,
        clue=clue,
    )


def _make_world(params: StoryParams) -> World:
    room = ROOMS[params.room]
    world = World(room)
    child = world.add(Entity(
        id=params.child_name,
        kind="character",
        type=params.child_type,
        meters={"tired": 0.0, "search": 0.0},
        memes={"worry": 0.0, "relief": 0.0, "focus": 0.0, "hope": 0.0},
    ))
    parent = world.add(Entity(
        id="parent",
        kind="character",
        type=params.parent_type,
        label=f"the {params.parent_type}",
        meters={"tired": 0.0},
        memes={"patience": 1.0, "warmth": 1.0},
    ))
    obj_spec = OBJECTS[params.object_name]
    item = world.add(Entity(
        id="cleat",
        type="cleat",
        label="cleat",
        phrase=obj_spec.phrase,
        owner=child.id,
        caretaker=parent.id,
        location=obj_spec.location,
        plural=False,
        meters={"lost": 1.0},
        memes={"importance": 1.0},
    ))
    world.facts.update(child=child, parent=parent, item=item, obj_spec=obj_spec)
    return world


def _inner_monologue(world: World, child: Entity, item: Entity, params: StoryParams) -> None:
    child.memes["worry"] += 1.0
    child.memes["focus"] += 1.0
    world.say(
        f"{child.id} stood still for a moment and listened to the little voice in {child.pronoun('possessive')} head: "
        f'"Okay. Think. You were just wearing the cleat. That means it has to be somewhere normal."'
    )


def _setup(world: World, child: Entity, parent: Entity, item: Entity, params: StoryParams) -> None:
    world.say(f"{child.id} came home after school and dropped {child.pronoun('possessive')} bag by the door.")
    world.say(room_detail(world.room))
    world.say(
        f"{child.id} needed {child.pronoun('possessive')} cleat for later, but one shoe was missing."
    )
    world.say(
        f'The only bright thing about it was the tribal stripe on the side, so {child.id} kept looking for that first.'
    )


def _search(world: World, child: Entity, parent: Entity, item: Entity, params: StoryParams) -> None:
    child.meters["search"] += 1.0
    if params.room == "entryway":
        world.say(
            f"{child.id} checked the shoes by the mat and then the shelf near the coats, thinking, "
            f'"If I were a cleat, where would I hide?"'
        )
    elif params.room == "kitchen":
        world.say(
            f"{child.id} peeked under the table, then into the corner by the fruit bowl, and thought, "
            f'"Not there. Keep going. Ordinary places. Ordinary places."'
        )
    elif params.room == "hallway":
        world.say(
            f"{child.id} slid a hand along the wall and looked under the bench, telling {child.pronoun('object')}self, "
            f'"Slow down. The answer is probably close.'"
        )
    else:
        world.say(
            f"{child.id} knelt beside the bed and glanced under the blanket edge, thinking, "
            f'"I always forget the obvious place.'"
        )
    world.say(
        f"Then {child.id} noticed {item.phrase} {item.location}."
    )
    item.meters["found"] = 1.0


def _resolve(world: World, child: Entity, parent: Entity, item: Entity, params: StoryParams) -> None:
    child.memes["worry"] = 0.0
    child.memes["relief"] += 1.0
    child.memes["hope"] += 1.0
    item.meters["lost"] = 0.0
    world.say(
        f'{child.id} smiled so hard it felt like a little light switched on inside. '
        f'"There you are," {child.id} whispered to the cleat, as if the shoe could hear."
    )
    world.say(
        f"The {params.parent_type} looked over and laughed gently. "
        f'"Good job checking the small places," {parent.id} said.'
    )
    world.say(
        f"So {child.id} laced up both cleats, took one deep breath, and felt ready to head back out."
    )


def tell(params: StoryParams) -> World:
    world = _make_world(params)
    child = world.get(params.child_name)
    parent = world.get("parent")
    item = world.get("cleat")

    _setup(world, child, parent, item, params)
    world.say("")
    _inner_monologue(world, child, item, params)
    _search(world, child, parent, item, params)
    world.say("")
    _resolve(world, child, parent, item, params)

    world.facts.update(params=params, resolved=True)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    item = f["item"]
    return [
        "Write a gentle slice-of-life story where a child quietly thinks through a missing cleat problem.",
        f"Tell a short story about {child.id} finding {item.phrase} by listening to an inner monologue.",
        "Write a child-facing story that begins with an ordinary afternoon and ends with a small, satisfying discovery.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    item = f["item"]
    params: StoryParams = f["params"]
    return [
        QAItem(
            question=f"What was missing when {child.id} came home?",
            answer=f"One of {child.pronoun('possessive')} cleats was missing, so {child.id} had to look carefully for it.",
        ),
        QAItem(
            question=f"What did {child.id} think about while searching?",
            answer=(
                f"{child.id} listened to an inner monologue that told {child.pronoun('object')} to slow down and check "
                f"ordinary places first, because the cleat was probably nearby."
            ),
        ),
        QAItem(
            question=f"Where did {child.id} find the cleat?",
            answer=f"{child.id} found {item.phrase} {item.location}. That small clue matched the thought that it had to be somewhere normal.",
        ),
        QAItem(
            question=f"How did the {params.parent_type} respond when the cleat turned up?",
            answer=f"The {params.parent_type} smiled and praised {child.id} for checking the little places instead of panicking.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a cleat used for?",
            answer="A cleat is a shoe with a grippy sole that helps someone run and keep their footing on grass or other playing fields.",
        ),
        QAItem(
            question="What does inner monologue mean?",
            answer="Inner monologue means the thoughts a person says to themselves in their head, even when nobody else can hear them.",
        ),
        QAItem(
            question="What does a slice-of-life story usually show?",
            answer="A slice-of-life story usually shows a small ordinary moment from daily life, like getting ready, searching, or talking at home.",
        ),
        QAItem(
            question="Why might a tribal stripe matter in a story like this?",
            answer="A small pattern like a tribal stripe can help someone notice an object quickly because it gives the object a clear detail to remember.",
        ),
    ]


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
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(
            f"  {e.id}: type={e.type}, meters={{{', '.join(f'{k}={v}' for k, v in e.meters.items())}}}, "
            f"memes={{{', '.join(f'{k}={v}' for k, v in e.memes.items())}}}"
        )
    lines.append(f"  room={world.room.name}")
    lines.append(f"  facts={list(world.facts.keys())}")
    return "\n".join(lines)


ASP_RULES = r"""
has_cleat(C) :- cleat(C).
valid_story(R, O) :- room(R), object(O), searchable(R), has_cleat(O).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for rk, room in ROOMS.items():
        lines.append(asp.fact("room", rk))
        lines.append(asp.fact("searchable", rk))
    for ok, obj in OBJECTS.items():
        lines.append(asp.fact("object", ok))
        if "cleat" in obj.tags:
            lines.append(asp.fact("cleat", ok))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    import asp
    py = set(valid_combos())
    cl = set(asp_valid())
    if py == cl:
        print(f"OK: ASP matches Python gate ({len(py)} combos).")
        return 0
    print("MISMATCH between ASP and Python.")
    print("python only:", sorted(py - cl))
    print("asp only:", sorted(cl - py))
    return 1


def build_story_sample(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generate(params: StoryParams) -> StorySample:
    return build_story_sample(params)


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
    StoryParams(room="entryway", object_name="left_cleat", child_name="Maya", child_type="girl", parent_type="mother", clue="under the sofa"),
    StoryParams(room="hallway", object_name="left_cleat", child_name="Nico", child_type="boy", parent_type="father", clue="beside the mat"),
    StoryParams(room="kitchen", object_name="left_cleat", child_name="Iris", child_type="girl", parent_type="mother", clue="near the door"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("#show valid_story/2."))
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
            except StoryError as err:
                print(err)
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
            header = f"### {p.child_name}: missing {p.object_name} in {p.room}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
