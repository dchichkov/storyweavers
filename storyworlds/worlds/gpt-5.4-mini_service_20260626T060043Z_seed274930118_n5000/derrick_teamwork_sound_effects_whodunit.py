#!/usr/bin/env python3
"""
storyworlds/worlds/derrick_teamwork_sound_effects_whodunit.py
==============================================================

A small whodunit story world about Derrick, teamwork, and noisy clues.

The seed tale behind this world is simple:
A little detective-minded child named Derrick hears strange sound effects in a quiet
house. Something goes missing, everyone gets suspicious, but the friends work together,
follow the sounds, and find the true cause. The ending should feel like a solved mystery,
with a concrete change in the world proving the teamwork paid off.

This script models:
- a child hero with feelings and a few physical belongings
- a small set of rooms with sound sources and hiding places
- clues that can be discovered through shared effort
- a culprit revealed by reasoning, not by a random twist

The story style stays close to a child-friendly whodunit:
clear clues, a little tension, a sensible reveal, and a final image of relief.
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
    carried_by: Optional[str] = None
    hidden_in: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character":
            male = {"boy", "man", "father", "dad"}
            female = {"girl", "woman", "mother", "mom"}
            if self.type in male:
                return {"subject": "he", "object": "him", "possessive": "his"}[case]
            if self.type in female:
                return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Room:
    id: str
    label: str
    sound: str
    clue: str
    contains: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    seed: Optional[int] = None
    name: str = "Derrick"
    friend_name: str = "Mina"
    helper_name: str = "Pip"
    culprit_name: str = "the cat"
    room: str = "hallway"
    missing_item: str = "red key"


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.rooms: dict[str, Room] = {}
        self.paragraphs: list[list[str]] = [[]]
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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
ROOMS = {
    "hallway": Room(
        id="hallway",
        label="the hallway",
        sound="tap-tap-tap",
        clue="tiny muddy paw prints",
    ),
    "kitchen": Room(
        id="kitchen",
        label="the kitchen",
        sound="clink-clink",
        clue="a chair pushed slightly askew",
    ),
    "attic": Room(
        id="attic",
        label="the attic",
        sound="creak-creak",
        clue="a ribbon caught on a box latch",
    ),
    "porch": Room(
        id="porch",
        label="the porch",
        sound="thump-thump",
        clue="a trail of crumbs near the step",
    ),
}

MISSING_ITEMS = {
    "red key": "a small red key",
    "silver spoon": "a shiny silver spoon",
    "blue badge": "a blue badge with a star on it",
}

CULPRITS = {
    "the cat": "cat",
    "the puppy": "puppy",
    "the wind": "wind",
    "the robot toy": "robot toy",
}

GIRL_NAMES = ["Mina", "Lena", "Ada", "Ruby", "Nina"]
BOY_NAMES = ["Derrick", "Theo", "Noah", "Eli", "Finn"]
HELPERS = ["Pip", "June", "Toby", "Mara", "Kit"]


# ---------------------------------------------------------------------------
# Story helpers
# ---------------------------------------------------------------------------
def intro(world: World, hero: Entity, friend: Entity, item: Entity) -> None:
    world.say(
        f"Derrick loved solving tiny mysteries, especially when he could listen for clues."
        if hero.id == "Derrick"
        else f"{hero.id} loved solving tiny mysteries, especially when {hero.pronoun('subject')} could listen for clues."
    )
    world.say(
        f"One afternoon, {hero.id} noticed that {item.phrase} was gone from the table, and "
        f"{friend.id} said, 'Uh-oh, that looks like a case for teamwork.'"
    )


def build_clues(world: World, room_ids: list[str]) -> None:
    for rid in room_ids:
        room = world.rooms[rid]
        world.say(
            f"In {room.label}, they heard {room.sound}, and they found {room.clue}."
        )


def clue_reasoning(world: World, hero: Entity, friend: Entity, helper: Entity, culprit: Entity, item: Entity) -> None:
    world.say(
        f"{hero.id} frowned and listened carefully. '{room_sound_line(world)}' {friend.id} whispered, "
        f"and {helper.id} pointed to the next room."
    )
    world.say(
        f"Working together, the three of them followed the sounds, matched each clue, and figured out "
        f"that {culprit.label} had nudged the {item.label} under the couch."
    )


def room_sound_line(world: World) -> str:
    sounds = [room.sound for room in world.rooms.values()]
    return ", ".join(sounds[:-1]) + ", and " + sounds[-1]


def resolve(world: World, hero: Entity, friend: Entity, helper: Entity, culprit: Entity, item: Entity) -> None:
    hero.memes["relief"] = hero.memes.get("relief", 0) + 1
    friend.memes["pride"] = friend.memes.get("pride", 0) + 1
    helper.memes["joy"] = helper.memes.get("joy", 0) + 1
    item.hidden_in = None
    item.carried_by = hero.id
    world.say(
        f"{helper.id} lifted the couch cushion, and there it was: {item.phrase}."
    )
    world.say(
        f"{hero.id} grinned. '{culprit.label.capitalize()} didn't steal it on purpose,' "
        f"{hero.id} said. 'We just had to follow the clues.'"
    )
    world.say(
        f"By the end, the friends laughed together while the little mystery was solved and the room felt bright again."
    )


def tell(params: StoryParams) -> World:
    if params.room not in ROOMS:
        raise StoryError(f"Unknown room: {params.room}")
    if params.missing_item not in MISSING_ITEMS:
        raise StoryError(f"Unknown missing item: {params.missing_item}")
    if params.culprit_name not in CULPRITS:
        raise StoryError(f"Unknown culprit: {params.culprit_name}")

    world = World()
    for room in ROOMS.values():
        world.add_room(room)

    hero = world.add_entity(Entity(id=params.name, kind="character", type="boy", label=params.name))
    friend = world.add_entity(Entity(id=params.friend_name, kind="character", type="girl", label=params.friend_name))
    helper = world.add_entity(Entity(id=params.helper_name, kind="character", type="boy", label=params.helper_name))
    culprit = world.add_entity(Entity(id=params.culprit_name, kind="thing", type=CULPRITS[params.culprit_name], label=params.culprit_name))
    item = world.add_entity(Entity(
        id="missing_item",
        kind="thing",
        type=params.missing_item,
        label=params.missing_item,
        phrase=MISSING_ITEMS[params.missing_item],
        owner=hero.id,
        hidden_in=params.room,
    ))

    world.facts.update(
        hero=hero,
        friend=friend,
        helper=helper,
        culprit=culprit,
        item=item,
        room=world.rooms[params.room],
        room_id=params.room,
    )

    intro(world, hero, friend, item)
    world.para()
    build_clues(world, [params.room, "kitchen", "porch"])
    world.para()
    clue_reasoning(world, hero, friend, helper, culprit, item)
    resolve(world, hero, friend, helper, culprit, item)
    world.facts["solved"] = True
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    item = f["item"]
    return [
        f"Write a short whodunit for a child named {hero.id} that uses sound effects and teamwork to find {item.phrase}.",
        f"Tell a gentle mystery where {hero.id} and {friend.id} follow clue sounds like tap-tap-tap and creak-creak.",
        "Write a child-friendly detective story where friends solve the case by listening closely together.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, friend, helper, culprit, item, room = f["hero"], f["friend"], f["helper"], f["culprit"], f["item"], f["room"]
    return [
        QAItem(
            question=f"What was missing in the story?",
            answer=f"{item.phrase} was missing, and Derrick and the others wanted to find it.",
        ),
        QAItem(
            question=f"Who worked together to solve the mystery?",
            answer=f"{hero.id}, {friend.id}, and {helper.id} worked together to follow the clues.",
        ),
        QAItem(
            question=f"What sound helped them notice the clue in {room.label}?",
            answer=f"They heard {room.sound} in {room.label}, and that helped them look more closely.",
        ),
        QAItem(
            question=f"Who turned out to be the reason the item was hidden away?",
            answer=f"{culprit.label} was the cause of the trouble, but it was an accident rather than a mean trick.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a clue?",
            answer="A clue is a small piece of information that helps someone solve a mystery.",
        ),
        QAItem(
            question="Why do people listen carefully in a whodunit?",
            answer="People listen carefully because sounds and little details can point them toward the answer.",
        ),
        QAItem(
            question="What is teamwork?",
            answer="Teamwork is when people help each other and do a job together.",
        ),
        QAItem(
            question="What are sound effects in a story?",
            answer="Sound effects are words that help the reader imagine noises, like tap-tap-tap or creak-creak.",
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
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
room(R) :- room_fact(R).
item(I) :- item_fact(I).
character(C) :- character_fact(C).
sound(S) :- sound_fact(S).

clue_room(R) :- room(R), clue_fact(R,_).
has_teamwork_story :- character(derrick), character(F), character(H), F != H, F != derrick, H != derrick.
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for rid, room in ROOMS.items():
        lines.append(asp.fact("room_fact", rid))
        lines.append(asp.fact("sound_fact", room.sound))
        lines.append(asp.fact("clue_fact", rid, room.clue))
    for iid in MISSING_ITEMS:
        lines.append(asp.fact("item_fact", iid.replace(" ", "_")))
    lines.append(asp.fact("character_fact", "derrick"))
    for name in BOY_NAMES[1:] + GIRL_NAMES:
        lines.append(asp.fact("character_fact", name.lower()))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show room/1."))
    if model is None:
        print("MISMATCH: no ASP model")
        return 1
    print("OK: ASP program loads and solves.")
    return 0


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------
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


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A child-friendly whodunit story world about Derrick, teamwork, and sound clues.")
    ap.add_argument("--name", choices=GIRL_NAMES + BOY_NAMES, default="Derrick")
    ap.add_argument("--friend-name", choices=GIRL_NAMES + BOY_NAMES, default="Mina")
    ap.add_argument("--helper-name", choices=HELPERS, default="Pip")
    ap.add_argument("--culprit-name", choices=list(CULPRITS), default="the cat")
    ap.add_argument("--room", choices=list(ROOMS), default="hallway")
    ap.add_argument("--missing-item", choices=list(MISSING_ITEMS), default="red key")
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
    return StoryParams(
        seed=args.seed,
        name=args.name if args.name else rng.choice(BOY_NAMES),
        friend_name=args.friend_name or rng.choice(GIRL_NAMES + BOY_NAMES),
        helper_name=args.helper_name or rng.choice(HELPERS),
        culprit_name=args.culprit_name or rng.choice(list(CULPRITS)),
        room=args.room or rng.choice(list(ROOMS)),
        missing_item=args.missing_item or rng.choice(list(MISSING_ITEMS)),
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.carried_by:
            bits.append(f"carried_by={e.carried_by}")
        if e.hidden_in:
            bits.append(f"hidden_in={e.hidden_in}")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:14} ({e.kind:9}) {' '.join(bits)}")
    for r in world.rooms.values():
        lines.append(f"  room {r.id:10} sound={r.sound} clue={r.clue}")
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


CURATED = [
    StoryParams(name="Derrick", friend_name="Mina", helper_name="Pip", culprit_name="the cat", room="hallway", missing_item="red key"),
    StoryParams(name="Derrick", friend_name="Ada", helper_name="Toby", culprit_name="the puppy", room="kitchen", missing_item="silver spoon"),
    StoryParams(name="Derrick", friend_name="Ruby", helper_name="Mara", culprit_name="the wind", room="porch", missing_item="blue badge"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show room/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show room/1."))
        print(model)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(base_seed + i))
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
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
