#!/usr/bin/env python3
"""
storyworlds/worlds/moan_guide_mansion_sound_effects_myth.py
===========================================================

A small myth-style story world about a child guided through a mansion by
sound effects: a low moan in the halls, a creak in the stairs, a hush in the
library, and a bell at the end.

Seed premise:
---
A child enters an old mansion where every room has a sound, and a kind guide
helps them listen well enough to find the hidden lantern and calm the moaning
house.

World model:
---
- The mansion has rooms connected by doors.
- Each room has a sound effect and a mood.
- Sounds can echo, warn, or guide.
- The child carries bravery and can lose it or gain it based on the sounds.
- The guide can reveal the meaning of each sound.
- The moan is an important sign: it means the mansion is lonely until the
  lantern is returned to the hall.

The story is generated from simulated state, not from a fixed paragraph.
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
    plural: bool = False
    owner: Optional[str] = None
    location: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "queen"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "king"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Room:
    id: str
    label: str
    sound: str
    mood: str
    exits: list[str] = field(default_factory=list)


@dataclass
class StoryParams:
    name: str
    gender: str
    guide_name: str
    guide_gender: str
    starting_room: str
    seed: Optional[int] = None


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.rooms: dict[str, Room] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

    def add_entity(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def add_room(self, room: Room) -> Room:
        self.rooms[room.id] = room
        return room

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

    def copy(self) -> "World":
        import copy
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.rooms = copy.deepcopy(self.rooms)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


def join_clauses(*parts: str) -> str:
    return " ".join(p for p in parts if p)


ROOMS = {
    "front_hall": Room(
        id="front_hall",
        label="the front hall",
        sound="a long moan",
        mood="lonely",
        exits=["stair_landing", "gallery"],
    ),
    "stair_landing": Room(
        id="stair_landing",
        label="the stair landing",
        sound="a soft creak",
        mood="watchful",
        exits=["front_hall", "library"],
    ),
    "library": Room(
        id="library",
        label="the library",
        sound="a whispering hush",
        mood="secret",
        exits=["stair_landing", "music_room"],
    ),
    "music_room": Room(
        id="music_room",
        label="the music room",
        sound="a bright bell",
        mood="hopeful",
        exits=["library", "gallery"],
    ),
    "gallery": Room(
        id="gallery",
        label="the moonlit gallery",
        sound="a humming echo",
        mood="ancient",
        exits=["front_hall", "music_room"],
    ),
}

STARTING_ROOMS = list(ROOMS)


@dataclass
class Rule:
    name: str
    apply: callable


def _r_moan_guides(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities["child"]
    guide = world.entities["guide"]
    room = world.rooms[child.location]
    if room.sound == "a long moan" and ("moan_seen", room.id) not in world.fired:
        world.fired.add(("moan_seen", room.id))
        child.memes["unease"] = child.memes.get("unease", 0.0) + 1
        guide.memes["wisdom"] = guide.memes.get("wisdom", 0.0) + 1
        out.append(f"The moan in {room.label} was not a monster at all; it was a lonely house asking to be heard.")
    return out


def _r_lantern_sings(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities["child"]
    lantern = world.entities["lantern"]
    if lantern.location == "music_room" and child.location == "music_room" and ("lantern_found",) not in world.fired:
        world.fired.add(("lantern_found",))
        child.memes["bravery"] = child.memes.get("bravery", 0.0) + 1
        out.append("The bell in the music room rang as if it knew the lantern had been found.")
    return out


def _r_mansion_calm(world: World) -> list[str]:
    out: list[str] = []
    lantern = world.entities["lantern"]
    if lantern.location == "front_hall" and ("mansion_calm",) not in world.fired:
        world.fired.add(("mansion_calm",))
        out.append("The moan softened into a warm hush, and the mansion felt like a home again.")
    return out


CAUSAL_RULES = [
    Rule("moan_guides", _r_moan_guides),
    Rule("lantern_sings", _r_lantern_sings),
    Rule("mansion_calm", _r_mansion_calm),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            lines = rule.apply(world)
            if lines:
                changed = True
                produced.extend(lines)
    if narrate:
        for line in produced:
            world.say(line)
    return produced


def move_child(world: World, dest: str) -> None:
    child = world.entities["child"]
    room = world.rooms[child.location]
    if dest not in room.exits:
        raise StoryError(f"{room.label} does not lead to {world.rooms[dest].label}.")
    child.location = dest
    child.memes["courage"] = child.memes.get("courage", 0.0) + 0.5
    world.say(f"{world.entities['guide'].label} led the child toward {world.rooms[dest].label}, following the sound like a path of moonlight.")
    if world.rooms[dest].sound == "a soft creak":
        child.memes["listening"] = child.memes.get("listening", 0.0) + 1


def introduce(world: World) -> None:
    child = world.entities["child"]
    guide = world.entities["guide"]
    room = world.rooms[child.location]
    world.say(f"Long ago, a little {child.type} named {child.id} came to {room.label} where {room.sound} drifted from the dark beams.")
    world.say(f"Beside {child.pronoun('object')}, {guide.label} walked with a quiet smile, for {guide.pronoun('subject')} knew how to read a house by its sounds.")


def hear_sound(world: World) -> None:
    child = world.entities["child"]
    room = world.rooms[child.location]
    world.say(f"{child.id} paused and listened. {room.sound.capitalize()} floated through {room.label}, and the air felt {room.mood}.")
    propagate(world)


def ask_guide(world: World) -> None:
    child = world.entities["child"]
    guide = world.entities["guide"]
    room = world.rooms[child.location]
    world.say(f'"What does that sound mean?" {child.id} asked.')
    if room.sound == "a long moan":
        world.say(f'"It means the mansion is lonely," {guide.label} said. "We should find what it has lost."')
    elif room.sound == "a soft creak":
        world.say(f'"It means the stairs remember every footstep," {guide.label} said. "Walk gently and they will answer kindly."')
    elif room.sound == "a whispering hush":
        world.say(f'"It means the books are keeping a secret," {guide.label} said. "Secrets open to careful ears."')
    else:
        world.say(f'"It means we are near the bright place," {guide.label} said. "Follow it."')


def find_lantern(world: World) -> None:
    child = world.entities["child"]
    guide = world.entities["guide"]
    lantern = world.entities["lantern"]
    if child.location == "music_room" and lantern.location != "music_room":
        lantern.location = "music_room"
        child.memes["joy"] = child.memes.get("joy", 0.0) + 1
        world.say(f"In the music room, behind a velvet curtain, {child.id} found the lantern, small and gold as a captured star.")
        world.say(f"{guide.label} nodded. " + '"That is the sound the house wanted us to hear,"' + " " + f"{guide.label} said.")
        propagate(world)


def return_lantern(world: World) -> None:
    lantern = world.entities["lantern"]
    lantern.location = "front_hall"
    world.say("Together they carried the lantern back to the front hall.")
    propagate(world)


def tell_story(params: StoryParams) -> World:
    world = World()
    for room in ROOMS.values():
        world.add_room(room)
    child = world.add_entity(Entity(id=params.name, kind="character", type=params.gender, label=params.name, location=params.starting_room))
    guide = world.add_entity(Entity(id=params.guide_name, kind="character", type=params.guide_gender, label=params.guide_name, location=params.starting_room))
    lantern = world.add_entity(Entity(id="lantern", kind="thing", type="lantern", label="the lantern", location="front_hall"))
    child.memes["bravery"] = 0.0
    guide.memes["wisdom"] = 1.0
    world.facts.update(child=child, guide=guide, lantern=lantern, starting_room=params.starting_room)

    introduce(world)
    world.para()
    hear_sound(world)
    ask_guide(world)

    path = ["stair_landing", "library", "music_room"] if params.starting_room == "front_hall" else ["library", "music_room"]
    for dest in path:
        world.para()
        move_child(world, dest)
        hear_sound(world)
        ask_guide(world)
        if dest == "music_room":
            find_lantern(world)

    world.para()
    return_lantern(world)
    world.say(f"In the end, the moan was gone, the bell was quiet, and {child.id} left with a brave heart while the mansion slept peacefully.")
    world.facts["resolved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    child = world.facts["child"]
    guide = world.facts["guide"]
    return [
        "Write a short myth-like story for a young child about a mansion that speaks in sound effects.",
        f"Tell a gentle legend where {child.id} follows {guide.label} through a mansion by listening to moans, creaks, whispers, and bells.",
        "Create a child-facing story in which a mysterious moan turns out to be a lonely house that becomes calm again.",
    ]


def story_qa(world: World) -> list[QAItem]:
    child = world.facts["child"]
    guide = world.facts["guide"]
    lantern = world.facts["lantern"]
    start_room = world.rooms[world.facts["starting_room"]]
    return [
        QAItem(
            question=f"Who was the story about at first, and where did {child.id} begin?",
            answer=f"The story was about {child.id}, who began in {start_room.label} where {start_room.sound} drifted through the air.",
        ),
        QAItem(
            question=f"What did {guide.label} help {child.id} do in the mansion?",
            answer=f"{guide.label} helped {child.id} listen to the mansion's sounds and follow them to the hidden lantern.",
        ),
        QAItem(
            question="What happened when the lantern came back to the front hall?",
            answer="The lonely moan softened into a warm hush, and the mansion felt peaceful again.",
        ),
        QAItem(
            question=f"Where did {child.id} find {lantern.label}?",
            answer="The lantern was found in the music room, behind a velvet curtain, shining like a small star.",
        ),
    ]


KNOWLEDGE = {
    "moan": [
        QAItem(
            question="What is a moan sound?",
            answer="A moan is a long, low sound that can seem sad, tired, or lonely.",
        )
    ],
    "guide": [
        QAItem(
            question="What does a guide do?",
            answer="A guide helps someone find the way and understand what to do next.",
        )
    ],
    "mansion": [
        QAItem(
            question="What is a mansion?",
            answer="A mansion is a very large house with many rooms.",
        )
    ],
    "sound": [
        QAItem(
            question="How can sounds help us?",
            answer="Sounds can warn us, tell us where to go, or help us notice what is nearby.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [q for key in ["moan", "guide", "mansion", "sound"] for q in KNOWLEDGE[key]]


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
    out.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: location={e.location} meters={e.meters} memes={e.memes}")
    lines.append("Rooms:")
    for r in world.rooms.values():
        lines.append(f"{r.id}: {r.label}, sound={r.sound}, mood={r.mood}, exits={r.exits}")
    lines.append(f"Fired: {sorted(world.fired)}")
    return "\n".join(lines)


NAME_POOL = ["Mina", "Lio", "Nora", "Tavi", "Ari", "Eli"]
GUIDE_POOL = ["Hush", "Mara", "Sage", "Ori"]
GENDER_POOL = ["girl", "boy"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic mansion story world with sound effects.")
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=GENDER_POOL)
    ap.add_argument("--guide-name")
    ap.add_argument("--guide-gender", choices=GENDER_POOL)
    ap.add_argument("--starting-room", choices=STARTING_ROOMS)
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
    name = args.name or rng.choice(NAME_POOL)
    gender = args.gender or rng.choice(GENDER_POOL)
    guide_name = args.guide_name or rng.choice([n for n in GUIDE_POOL if n != name])
    guide_gender = args.guide_gender or rng.choice(GENDER_POOL)
    start = args.starting_room or rng.choice(STARTING_ROOMS)
    return StoryParams(name=name, gender=gender, guide_name=guide_name, guide_gender=guide_gender, starting_room=start)


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
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


ASP_RULES = r"""
room(front_hall). room(stair_landing). room(library). room(music_room). room(gallery).
sound(front_hall, moan). sound(stair_landing, creak). sound(library, hush). sound(music_room, bell). sound(gallery, echo).

guides(Room) :- sound(Room, moan).
guides(Room) :- sound(Room, creak).
guides(Room) :- sound(Room, hush).
guides(Room) :- sound(Room, bell).
guides(Room) :- sound(Room, echo).

% A good myth-path is one where the child can move from the starting room to the music room.
path(front_hall, stair_landing).
path(front_hall, gallery).
path(stair_landing, library).
path(library, music_room).
path(gallery, music_room).
path(stair_landing, front_hall).
path(library, stair_landing).
path(music_room, library).
path(music_room, gallery).
path(gallery, front_hall).

reach(A,B) :- path(A,B).
reach(A,C) :- path(A,B), reach(B,C).

valid_story(Start) :- room(Start), reach(Start, music_room).
#show valid_story/1.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for rid in ROOMS:
        lines.append(asp.fact("room", rid))
    for rid, room in ROOMS.items():
        lines.append(asp.fact("sound", rid, room.sound.split()[-1]))
    for rid, room in ROOMS.items():
        for ex in room.exits:
            lines.append(asp.fact("path", rid, ex))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/1."))
    clingo_starts = sorted(set(asp.atoms(model, "valid_story")))
    py_starts = [(s,) for s in STARTING_ROOMS if reachable_to_music(s)]
    if set(clingo_starts) == set(py_starts):
        print(f"OK: clingo gate matches Python reachability ({len(py_starts)} starts).")
        return 0
    print("MISMATCH between clingo and Python:")
    print("clingo:", clingo_starts)
    print("python:", py_starts)
    return 1


def reachable_to_music(start: str) -> bool:
    seen = {start}
    stack = [start]
    while stack:
        cur = stack.pop()
        if cur == "music_room":
            return True
        for nxt in ROOMS[cur].exits:
            if nxt not in seen:
                seen.add(nxt)
                stack.append(nxt)
    return False


CURATED = [
    StoryParams(name="Mina", gender="girl", guide_name="Hush", guide_gender="boy", starting_room="front_hall"),
    StoryParams(name="Ari", gender="boy", guide_name="Mara", guide_gender="girl", starting_room="stair_landing"),
    StoryParams(name="Nora", gender="girl", guide_name="Sage", guide_gender="boy", starting_room="gallery"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/1."))
        starts = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(starts)} valid starting rooms:")
        for (start,) in starts:
            print(f"  {start}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 40):
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
            header = f"### {p.name} in {p.starting_room}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
