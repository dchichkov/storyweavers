#!/usr/bin/env python3
"""
storyworlds/worlds/lego_cautionary_rhyming_story.py
===================================================

A small story world about LEGO play, a careful warning, and a kinder choice.

This world is built to feel like a cautionary rhyming story:
- a child loves LEGO bricks,
- a parent warns about a risky choice,
- the child makes a mistake or resists at first,
- the world turns toward a safer ending,
- the final image proves what changed.

The simulation tracks physical state in meters and emotional state in memes.
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    held_by: Optional[str] = None
    on_floor: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"mess": 0.0, "hurt": 0.0, "tidy": 0.0}
        if not self.memes:
            self.memes = {"joy": 0.0, "worry": 0.0, "defiance": 0.0, "calm": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Room:
    name: str
    place: str
    floor_kind: str
    safe_box: str


@dataclass
class ToySet:
    name: str
    pieces: int
    build: str
    rhyme_line: str
    mess_word: str
    scatter_word: str


@dataclass
class StoryParams:
    room: str
    toy: str
    child_name: str
    child_gender: str
    parent_type: str
    trait: str
    seed: Optional[int] = None


ROOMS = {
    "bedroom": Room("bedroom", "the bedroom", "soft rug", "toy bin"),
    "playroom": Room("playroom", "the playroom", "hard floor", "bright basket"),
    "livingroom": Room("livingroom", "the living room", "wood floor", "blue box"),
}

TOYS = {
    "castle": ToySet(
        name="castle",
        pieces=18,
        build="tall tower",
        rhyme_line="Brick by brick and click by click, the tower grew up big and thick.",
        mess_word="scattered",
        scatter_word="spilled",
    ),
    "rocket": ToySet(
        name="rocket",
        pieces=16,
        build="rocket ship",
        rhyme_line="Snap by snap and tap by tap, the rocket stood up on the mat.",
        mess_word="scattered",
        scatter_word="spilled",
    ),
    "bridge": ToySet(
        name="bridge",
        pieces=14,
        build="little bridge",
        rhyme_line="Piece by piece and neat by neat, the bridge looked strong and sweet.",
        mess_word="scattered",
        scatter_word="spilled",
    ),
}

CHILD_NAMES = {
    "girl": ["Mia", "Lily", "Zoe", "Nora", "Ella"],
    "boy": ["Leo", "Finn", "Max", "Theo", "Ben"],
}
TRAITS = ["curious", "bright", "playful", "stubborn", "cheery"]

ASP_RULES = r"""
room(Room) :- setting(Room).
toy(T) :- toyset(T).

risky(T) :- toyset(T), lego_pieces(T, N), N > 0.
warned(Room, T) :- room(Room), toy(T), floor_kind(Room, hard_floor), risky(T).
safe_choice(Room, T) :- warned(Room, T), put_away(T), room_box(Room, _).
resolved(Room, T) :- safe_choice(Room, T), tidy_room(Room).

#show warned/2.
#show safe_choice/2.
#show resolved/2.
"""


class World:
    def __init__(self, room: Room, toy: ToySet) -> None:
        self.room = room
        self.toy = toy
        self.entities: dict[str, Entity] = {}
        self.events: list[str] = []
        self.facts: dict[str, object] = {}
        self.fired: set[str] = set()

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.events.append(text)

    def render(self) -> str:
        return " ".join(self.events)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Cautionary rhyming LEGO story world.")
    ap.add_argument("--room", choices=ROOMS)
    ap.add_argument("--toy", choices=TOYS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--trait", choices=TRAITS)
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


def valid_combo(room: Room, toy: ToySet) -> bool:
    return True


def valid_combos() -> list[tuple[str, str]]:
    return [(r, t) for r in ROOMS for t in TOYS if valid_combo(ROOMS[r], TOYS[t])]


def explain_rejection() -> str:
    return "(No story: the chosen LEGO scene did not make a clear cautionary choice.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.room is None or c[0] == args.room)
              and (args.toy is None or c[1] == args.toy)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    room, toy = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(CHILD_NAMES[gender])
    parent = args.parent or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(room=room, toy=toy, child_name=name, child_gender=gender, parent_type=parent, trait=trait)


def rhyme_open(name: str, trait: str, toy: ToySet, room: Room) -> str:
    return (
        f"{name} was a {trait} little builder who loved LEGO blocks with a happy glow. "
        f"{toy.rhyme_line} In {room.place}, the pieces could rise up high and go."
    )


def rhyme_warning(parent: Entity, child: Entity, room: Room, toy: ToySet) -> str:
    return (
        f'"Careful, {child.id}," said {parent.label}. "Those bricks on the {room.floor_kind} floor can go '
        f'pop and tumble, and little feet can slip and stumble."'
    )


def rhyme_turn(child: Entity, parent: Entity, toy: ToySet) -> str:
    return (
        f"{child.id} frowned, then paused, then looked down low. "
        f"The LEGO bricks were {toy.scatter_word} where toes might go. "
        f"{child.id} said, 'I want to keep on playing, but I do not want a sore toe swaying.'"
    )


def rhyme_resolution(child: Entity, parent: Entity, room: Room, toy: ToySet) -> str:
    return (
        f"Together they picked up every piece, click by click, and put them in the {room.safe_box}. "
        f"Then {child.id} smiled, and the room felt neat and bright; "
        f"the Lego lesson was learned just right."
    )


def simulate(params: StoryParams) -> World:
    room = ROOMS[params.room]
    toy = TOYS[params.toy]
    world = World(room, toy)

    child = world.add(Entity(
        id=params.child_name,
        kind="character",
        type=params.child_gender,
        traits=["little", params.trait],
        meters={"mess": 0.0, "hurt": 0.0, "tidy": 0.0},
        memes={"joy": 1.0, "worry": 0.0, "defiance": 0.0, "calm": 0.0},
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=params.parent_type,
        label=f"the {params.parent_type}",
        meters={"mess": 0.0, "hurt": 0.0, "tidy": 0.0},
        memes={"joy": 0.0, "worry": 1.0, "defiance": 0.0, "calm": 0.0},
    ))
    bricks = world.add(Entity(
        id="LEGO",
        kind="thing",
        type="lego",
        label="LEGO bricks",
        phrase=f"a pile of LEGO bricks for a {toy.name}",
        plural=True,
        owner=child.id,
        caretaker=parent.id,
        held_by=child.id,
        meters={"mess": 0.0, "hurt": 0.0, "tidy": 0.0},
        memes={"joy": 0.0, "worry": 0.0, "defiance": 0.0, "calm": 0.0},
    ))

    world.say(rhyme_open(child.id, params.trait, toy, room))
    world.say(f"{child.id} loved the bright blocks and wanted to build a {toy.build}.")

    world.say(f"One day in {room.place}, {child.id} took the LEGO bricks to the floor.")
    if room.floor_kind == "hard floor":
        child.meters["mess"] += 1.0
        child.memes["joy"] += 0.2
        child.memes["worry"] += 0.4
        world.say(f"The bricks went {toy.scatter_word} across the {room.floor_kind}.")
        world.say(rhyme_warning(parent, child, room, toy))
        child.memes["defiance"] += 0.8
        world.say(f"{child.id} wanted to keep going, but the warning felt strong and true.")
        child.meters["hurt"] += 1.0
        child.memes["worry"] += 1.0
        world.say(f"Then one loose brick slipped under a shoe, and a tiny cry went 'Ouch!'")
        world.say(f"{parent.label.capitalize()} knelt down and said, 'Let's gather them up, one by one.'")
        child.meters["tidy"] += 1.0
        child.memes["calm"] += 1.0
        bricks.meters["tidy"] += 1.0
        world.say(rhyme_resolution(child, parent, room, toy))
    else:
        world.say(f"The floor was soft, so the bricks stayed mostly in one place.")
        world.say(rhyme_warning(parent, child, room, toy))
        child.memes["defiance"] += 0.4
        world.say(f"{child.id} stopped to think and gave a small, wise nod.")
        child.meters["tidy"] += 1.0
        child.memes["calm"] += 1.0
        bricks.meters["tidy"] += 1.0
        world.say(f"{child.id} moved the LEGO pieces to the {room.safe_box}, neat as a song.")
        world.say(rhyme_resolution(child, parent, room, toy))

    world.facts.update(
        child=child,
        parent=parent,
        bricks=bricks,
        room=room,
        toy=toy,
        warned=True,
        resolved=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child: Entity = f["child"]  # type: ignore[assignment]
    toy: ToySet = f["toy"]  # type: ignore[assignment]
    room: Room = f["room"]  # type: ignore[assignment]
    return [
        f'Write a cautionary rhyming story about {child.id} and LEGO bricks in {room.place}.',
        f"Tell a short rhyming story where a {child.type} named {child.id} wants to build a {toy.name} but must listen to a warning.",
        f'Create a gentle story for young children that uses the word "lego" and ends with tidying up.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = f["child"]  # type: ignore[assignment]
    parent: Entity = f["parent"]  # type: ignore[assignment]
    room: Room = f["room"]  # type: ignore[assignment]
    toy: ToySet = f["toy"]  # type: ignore[assignment]
    qa = [
        QAItem(
            question=f"Who wanted to build with LEGO in {room.place}?",
            answer=f"{child.id} did. {child.id} was a little {child.traits[-1]} {child.type} who loved LEGO bricks.",
        ),
        QAItem(
            question=f"What did {parent.label} warn about in {room.place}?",
            answer=f"{parent.label.capitalize()} warned that the LEGO bricks could scatter on the {room.floor_kind} floor and cause a tumble.",
        ),
        QAItem(
            question=f"What did they do at the end?",
            answer=f"They picked up the LEGO pieces and put them in the {room.safe_box}, so the room ended neat and safe.",
        ),
    ]
    if room.floor_kind == "hard floor":
        qa.append(QAItem(
            question=f"Why was the LEGO play risky in {room.place}?",
            answer=f"It was risky because the LEGO bricks could slide or scatter on the {room.floor_kind} floor, and that could make a child slip or get a sore toe.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What are LEGO bricks?",
            answer="LEGO bricks are small building pieces that fit together, so children can make towers, cars, houses, and other fun creations.",
        ),
        QAItem(
            question="Why should you keep small bricks off the floor?",
            answer="Small bricks on the floor can be stepped on, and that can hurt feet or make someone stumble.",
        ),
        QAItem(
            question="What does tidying up mean?",
            answer="Tidying up means putting toys back where they belong so the room is safe, neat, and easy to use again.",
        ),
    ]


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


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        lines.append(
            f"{e.id}: kind={e.kind} type={e.type} meters={e.meters} memes={e.memes} held_by={e.held_by} on_floor={e.on_floor}"
        )
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for rname, room in ROOMS.items():
        lines.append(asp.fact("setting", rname))
        lines.append(asp.fact("floor_kind", rname, room.floor_kind.replace(" ", "_")))
        lines.append(asp.fact("room_box", rname, room.safe_box.replace(" ", "_")))
    for tname, toy in TOYS.items():
        lines.append(asp.fact("toyset", tname))
        lines.append(asp.fact("lego_pieces", tname, toy.pieces))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show warned/2.\n#show safe_choice/2.\n#show resolved/2."))
    shown = set()
    for sym in model:
        shown.add((sym.name, tuple(getattr(a, "name", getattr(a, "string", getattr(a, "number", None))) for a in sym.arguments)))
    if shown:
        print("OK: ASP program runs.")
        return 0
    print("OK: ASP program runs with empty model.")
    return 0


def build_all_params() -> list[StoryParams]:
    out: list[StoryParams] = []
    for room in ROOMS:
        for toy in TOYS:
            for gender in ("girl", "boy"):
                for parent in ("mother", "father"):
                    out.append(StoryParams(
                        room=room,
                        toy=toy,
                        child_name=CHILD_NAMES[gender][0],
                        child_gender=gender,
                        parent_type=parent,
                        trait=TRAITS[0],
                    ))
    return out


CURATED = [
    StoryParams(room="bedroom", toy="castle", child_name="Mia", child_gender="girl", parent_type="mother", trait="curious"),
    StoryParams(room="playroom", toy="rocket", child_name="Leo", child_gender="boy", parent_type="father", trait="playful"),
    StoryParams(room="livingroom", toy="bridge", child_name="Nora", child_gender="girl", parent_type="mother", trait="stubborn"),
]


def generate(params: StoryParams) -> StorySample:
    world = simulate(params)
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    room = args.room or rng.choice(list(ROOMS))
    toy = args.toy or rng.choice(list(TOYS))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(CHILD_NAMES[gender])
    parent = args.parent or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(room=room, toy=toy, child_name=name, child_gender=gender, parent_type=parent, trait=trait)


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show warned/2.\n#show safe_choice/2.\n#show resolved/2."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.child_name}: {p.toy} in {p.room}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
