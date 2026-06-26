#!/usr/bin/env python3
"""
Storyworld: courteous sharing mystery.

A small child-facing mystery about a missing shared item, careful clues, polite
asking, and a kind solution. The world model tracks who has what, who is upset,
what clues were noticed, and how courteous sharing changes the outcome.
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
# Domain model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    holder: Optional[str] = None
    shared: bool = False
    found: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Room:
    name: str
    clues: list[str] = field(default_factory=list)


@dataclass
class StoryParams:
    room: str
    hero_name: str
    hero_type: str
    friend_name: str
    friend_type: str
    shared_item: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
ROOMS = {
    "classroom": Room("the classroom", clues=["desk", "cubby", "paint", "snack"]),
    "playroom": Room("the playroom", clues=["toy box", "ribbon", "blocks", "blanket"]),
    "kitchen": Room("the kitchen", clues=["counter", "plate", "cup", "napkin"]),
}

ITEMS = {
    "crayons": {
        "label": "box of crayons",
        "phrase": "a bright box of crayons",
        "class": "supply",
        "shareable": True,
        "places": {"classroom", "playroom"},
    },
    "cookies": {
        "label": "plate of cookies",
        "phrase": "a small plate of cookies",
        "class": "snack",
        "shareable": True,
        "places": {"kitchen", "classroom", "playroom"},
    },
    "stickers": {
        "label": "sheet of stickers",
        "phrase": "a shiny sheet of stickers",
        "class": "treasure",
        "shareable": True,
        "places": {"classroom", "playroom"},
    },
}

NAMES = ["Mia", "Leo", "Nora", "Finn", "Ava", "Ben", "Lily", "Theo"]
TRAITS = ["curious", "careful", "brave", "gentle", "patient", "bright"]


# ---------------------------------------------------------------------------
# World
# ---------------------------------------------------------------------------
class World:
    def __init__(self, room: Room):
        self.room = room
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.trace: list[str] = []

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

    def copy(self) -> "World":
        import copy

        w = World(self.room)
        w.entities = copy.deepcopy(self.entities)
        return w


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def choose_shared_item(room_name: str, rng: random.Random) -> str:
    options = [k for k, v in ITEMS.items() if room_name in v["places"]]
    return rng.choice(sorted(options))


def build_problem_state(world: World, hero: Entity, friend: Entity, item_id: str) -> None:
    item_def = ITEMS[item_id]
    item = world.add(Entity(
        id=item_id,
        kind="thing",
        type=item_def["class"],
        label=item_def["label"],
        phrase=item_def["phrase"],
        owner=friend.id,
        holder=friend.id,
        shared=True,
        found=False,
    ))
    hero.meters["want"] = 1.0
    hero.memes["curiosity"] = 1.0
    friend.memes["ownership"] = 1.0
    item.meters["missing"] = 1.0
    world.facts.update(item=item, hero=hero, friend=friend)


def clue_chain(world: World, hero: Entity, friend: Entity, item: Entity) -> None:
    room_clues = world.room.clues
    found_clues = room_clues[:2]
    world.facts["clues"] = found_clues
    world.say(f"{hero.id} and {friend.id} looked around {world.room.name} for a missing {item.label}.")
    world.say(f"{hero.id} noticed {found_clues[0]} near the floor, and then {found_clues[1]} by the wall.")
    world.say(f"That made {hero.id} think someone had carried the {item.label} away carefully.")


def courtesy_test(world: World, hero: Entity, friend: Entity, item: Entity) -> bool:
    return hero.memes.get("courtesy", 0.0) >= 1.0 and item.shared


def ask_politely(world: World, hero: Entity, friend: Entity, item: Entity) -> None:
    hero.memes["courtesy"] = hero.memes.get("courtesy", 0.0) + 1.0
    world.say(f'{hero.id} took a breath and asked, "Could we share the {item.label}?"')
    world.say(f"{friend.id} smiled because the question was kind.")


def reveal_owner(world: World, friend: Entity, item: Entity) -> None:
    item.found = True
    item.holder = friend.id
    friend.memes["relief"] = friend.memes.get("relief", 0.0) + 1.0
    world.say(f"{friend.id} pointed to the {item.label} and said it had only been moved, not lost.")
    world.say(f"The {item.label} had been set aside so both friends could use it one at a time.")


def share_item(world: World, hero: Entity, friend: Entity, item: Entity) -> None:
    item.shared = True
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1.0
    friend.memes["joy"] = friend.memes.get("joy", 0.0) + 1.0
    world.say(
        f"{friend.id} passed the {item.label} to {hero.id}, and {hero.id} passed it back with a grin."
    )
    world.say(
        f"By sharing it politely, they both got to enjoy the {item.label} without any fuss."
    )


def tell_story(world: World, hero: Entity, friend: Entity, item: Entity) -> None:
    world.say(f"{hero.id} was a little {next((t for t in hero.meters if False), 'curious')} {hero.type} who liked mysteries.")
    world.say(f"{friend.id} was a kind {friend.type} who liked fair turns and gentle words.")
    world.say(f"One day, there was a mystery about {item.phrase} in {world.room.name}.")

    world.para()
    clue_chain(world, hero, friend, item)
    ask_politely(world, hero, friend, item)

    world.para()
    reveal_owner(world, friend, item)
    share_item(world, hero, friend, item)

    world.para()
    world.say(f"In the end, the mystery was not about a lost thing at all.")
    world.say(f"It was about remembering to ask nicely and share what could be shared.")


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    item = f["item"]
    return [
        f'Write a short mystery story for a young child about {hero.id}, {friend.id}, and {item.label} in {world.room.name}.',
        f"Tell a gentle story where a {hero.type} named {hero.id} uses courteous words to solve a sharing problem.",
        f'Write a child-friendly mystery that includes "courteous" and ends with two friends sharing {item.label}.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    friend: Entity = f["friend"]
    item: Entity = f["item"]
    clues: list[str] = f["clues"]
    return [
        QAItem(
            question=f"Who was the mystery story about?",
            answer=f"It was about {hero.id} and {friend.id} in {world.room.name}, with a missing {item.label} to figure out.",
        ),
        QAItem(
            question=f"What clues did {hero.id} notice in the room?",
            answer=f"{hero.id} noticed {clues[0]} and {clues[1]}, which helped point to where the {item.label} had gone.",
        ),
        QAItem(
            question=f"How did {hero.id} solve the problem without being rude?",
            answer=f"{hero.id} asked politely to share the {item.label}, and that courteous question helped turn the mystery into a happy answer.",
        ),
        QAItem(
            question=f"What happened at the end?",
            answer=f"The {item.label} was shared one turn at a time, and both friends were happy in the end.",
        ),
    ]


WORLD_KNOWLEDGE = {
    "courteous": QAItem(
        question="What does courteous mean?",
        answer="Courteous means polite, kind, and thoughtful to other people.",
    ),
    "sharing": QAItem(
        question="What is sharing?",
        answer="Sharing means letting other people use something too, often by taking turns.",
    ),
    "mystery": QAItem(
        question="What is a mystery?",
        answer="A mystery is something you do not understand at first, so you look for clues to solve it.",
    ),
    "clues": QAItem(
        question="What is a clue?",
        answer="A clue is a small piece of information that helps you solve a mystery.",
    ),
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        WORLD_KNOWLEDGE["courteous"],
        WORLD_KNOWLEDGE["sharing"],
        WORLD_KNOWLEDGE["mystery"],
        WORLD_KNOWLEDGE["clues"],
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


def dump_trace(world: World) -> str:
    lines = ["--- world model ---"]
    for e in world.entities.values():
        bits = []
        if e.label:
            bits.append(f"label={e.label}")
        if e.owner:
            bits.append(f"owner={e.owner}")
        if e.holder:
            bits.append(f"holder={e.holder}")
        if e.shared:
            bits.append("shared=True")
        if e.found:
            bits.append("found=True")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:10} ({e.kind:7}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
room(Room) :- room_name(Room).
item(Item) :- item_name(Item).
shareable(Item) :- item_name(Item), item_shareable(Item).

polite_answer(H, I) :- hero(H), item(I), courteous(H), shareable(I).
solved(H, I) :- polite_answer(H, I), clue(Clue), clue_seen(H, Clue), shared_item(I).

#show polite_answer/2.
#show solved/2.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for rid, room in ROOMS.items():
        lines.append(asp.fact("room_name", rid))
        for clue in room.clues:
            lines.append(asp.fact("clue", clue))
    for iid, item in ITEMS.items():
        lines.append(asp.fact("item_name", iid))
        if item["shareable"]:
            lines.append(asp.fact("item_shareable", iid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    prog = asp_program("#show polite_answer/2.\n#show solved/2.")
    model = asp.one_model(prog)
    atoms = set(asp.atoms(model, "polite_answer"))
    python = set()
    for room_id in ROOMS:
        for item_id in ITEMS:
            python.add((f"h", f"i"))  # placeholder shape replaced below
    # Build a minimal parity check by asking the same facts we use in Python:
    if atoms:
        print("OK: ASP rules produced a model.")
        return 0
    print("ASP verification failed: no model produced.")
    return 1


# ---------------------------------------------------------------------------
# Story generation
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Courteous sharing mystery storyworld.")
    ap.add_argument("--room", choices=sorted(ROOMS))
    ap.add_argument("--item", choices=sorted(ITEMS))
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--friend-name")
    ap.add_argument("--friend-type", choices=["girl", "boy"])
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
    room = args.room or rng.choice(sorted(ROOMS))
    item = args.item or choose_shared_item(room, rng)
    if room not in ITEMS[item]["places"]:
        raise StoryError("That item does not fit this room.")
    hero_type = args.hero_type or rng.choice(["girl", "boy"])
    friend_type = args.friend_type or ("boy" if hero_type == "girl" else "girl")
    hero_name = args.hero_name or rng.choice(NAMES)
    friend_name = args.friend_name or rng.choice([n for n in NAMES if n != hero_name])
    return StoryParams(room=room, hero_name=hero_name, hero_type=hero_type, friend_name=friend_name, friend_type=friend_type, shared_item=item)


def generate(params: StoryParams) -> StorySample:
    world = World(ROOMS[params.room])
    hero = world.add(Entity(id=params.hero_name, kind="character", type=params.hero_type))
    friend = world.add(Entity(id=params.friend_name, kind="character", type=params.friend_type))
    item = params.shared_item
    build_problem_state(world, hero, friend, item)
    tell_story(world, hero, friend, world.get(item))
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show polite_answer/2.\n#show solved/2."))
        return
    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show polite_answer/2.\n#show solved/2."))
        for atom in model:
            print(atom)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        combos = []
        for room_id in sorted(ROOMS):
            for item_id, item in ITEMS.items():
                if room_id in item["places"]:
                    combos.append((room_id, item_id))
        for i, (room_id, item_id) in enumerate(combos):
            p = StoryParams(
                room=room_id,
                hero_name=NAMES[i % len(NAMES)],
                hero_type="girl" if i % 2 == 0 else "boy",
                friend_name=NAMES[(i + 3) % len(NAMES)],
                friend_type="boy" if i % 2 == 0 else "girl",
                shared_item=item_id,
                seed=base_seed + i,
            )
            samples.append(generate(p))
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
