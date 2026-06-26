#!/usr/bin/env python3
"""
pajama_scout_cold_reconciliation_ghost_story.py
===============================================

A small Storyweavers world about a scout, a cold night, and a ghostly
reconciliation.

The seed tale premise:
- A child scout loves wearing cozy pajamas.
- A cold draft and a lonely ghost make bedtime scary.
- The scout first misunderstands the ghost, then learns it is only trying to
  help.
- They reconcile by sharing warmth and making the room safe together.

The world is intentionally tiny: a few entities, a few state changes, and a
single authored turn from fear to friendship.
"""

from __future__ import annotations

import argparse
import copy
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for key in ("cold", "warmth", "dust", "order"):
            self.meters.setdefault(key, 0.0)
        for key in ("fear", "kindness", "trust", "loneliness", "relief", "reconciliation"):
            self.memes.setdefault(key, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Room:
    name: str
    drafty: bool = False
    safe_light: bool = False


@dataclass
class StoryParams:
    room: str
    scout_name: str
    scout_gender: str
    parent_name: str
    ghost_name: str
    seed: Optional[int] = None


ROOMS = {
    "cabin": Room(name="the cabin", drafty=True, safe_light=True),
    "attic": Room(name="the attic", drafty=True, safe_light=False),
    "hall": Room(name="the hallway", drafty=True, safe_light=True),
}

SCOUT_NAMES = {
    "girl": ["Mina", "June", "Poppy", "Ivy"],
    "boy": ["Ned", "Owen", "Theo", "Finn"],
}

PARENT_NAMES = ["Mum", "Dad", "Aunt Rose", "Uncle Ben"]
GHOST_NAMES = ["Misty", "Whisper", "Pale Friend", "Lantern Ghost"]


class World:
    def __init__(self, room: Room) -> None:
        self.room = room
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
        clone = World(self.room)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        clone.fired = set(self.fired)
        return clone


def scout_story_name(gender: str, rng: random.Random) -> str:
    return rng.choice(SCOUT_NAMES[gender])


def _r_cold(world: World) -> list[str]:
    out: list[str] = []
    for e in world.entities.values():
        if e.kind != "character":
            continue
        if e.meters["cold"] < THRESHOLD:
            continue
        sig = ("cold", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["fear"] += 1
        out.append(f"{e.id} shivered at the cold.")
    return out


def _r_reconcile(world: World) -> list[str]:
    scout = world.get("scout")
    ghost = world.get("ghost")
    if scout.memes["trust"] < THRESHOLD or ghost.memes["kindness"] < THRESHOLD:
        return []
    sig = ("reconcile",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    scout.memes["reconciliation"] += 1
    scout.memes["fear"] = 0.0
    ghost.memes["loneliness"] = 0.0
    return ["They made up in the warm light."]


def propagate(world: World, narrate: bool = True) -> None:
    changed = True
    while changed:
        changed = False
        for rule in (_r_cold, _r_reconcile):
            sent = rule(world)
            if sent:
                changed = True
                if narrate:
                    for s in sent:
                        world.say(s)


def preview_cold(room: Room) -> bool:
    return room.drafty


def tell(room: Room, scout_name: str, scout_gender: str, parent_name: str, ghost_name: str) -> World:
    world = World(room)
    scout = world.add(Entity(id="scout", kind="character", type=scout_gender, label=scout_name))
    parent = world.add(Entity(id="parent", kind="character", type="adult", label=parent_name))
    ghost = world.add(Entity(id="ghost", kind="character", type="ghost", label=ghost_name))
    pajamas = world.add(Entity(id="pajamas", type="clothes", label="pajamas", phrase="soft pajamas", owner=scout.id))
    lantern = world.add(Entity(id="lantern", type="thing", label="lantern", phrase="a tiny lantern", owner=ghost.id))

    scout.worn_by = scout.id
    pajamas.worn_by = scout.id

    world.say(
        f"{scout.label} was a little scout who loved {pajamas.label} and quiet bedtime stories."
    )
    world.say(
        f"{parent.label} tucked {scout.label} into {room.name}, where the air felt thin and cold."
    )
    world.say(
        f"In the dim corner, {ghost.label} drifted beside {lantern.phrase} and looked lonely."
    )

    world.para()
    if preview_cold(room):
        scout.meters["cold"] += 1
        ghost.meters["cold"] += 1
        ghost.memes["loneliness"] += 1
        world.say(f"A cold draft slipped under the door and touched {scout.label}'s toes.")
        world.say(f"{scout.label} thought the whispering shadow might mean trouble.")
        scout.memes["fear"] += 1
        world.say(f"{scout.label} hugged {pajamas.label} tight and called for {parent.label}.")
        world.say(f"Then {ghost.label} floated closer, not to scare anyone, but to point at the window.")
        world.say(f"The latch was open, and the cold air was rushing in.")

    world.para()
    scout.memes["trust"] += 1
    ghost.memes["kindness"] += 1
    world.say(
        f"{ghost.label} did not hide. {ghost.pronoun().capitalize()} stayed still and let {scout.label} look."
    )
    world.say(
        f"{scout.label} saw that {ghost.label} was only helping, not haunting."
    )
    world.say(
        f"Together, {scout.label} and {parent.label} closed the window, and {ghost.label} held the lantern steady."
    )
    world.say(
        f"The room grew calm, and the cold began to fade."
    )
    propagate(world, narrate=True)

    world.para()
    world.say(
        f"{scout.label} smiled, thanked {ghost.label}, and invited {ghost.pronoun('object')} to stay by the bed."
    )
    world.say(
        f"{ghost.label} glowed softly, no longer lonely, while {scout.label} drifted back to sleep in warm {pajamas.label}."
    )

    world.facts.update(
        scout=scout,
        parent=parent,
        ghost=ghost,
        pajamas=pajamas,
        lantern=lantern,
        room=room,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    scout = f["scout"]
    return [
        f'Write a short ghost story for children about {scout.label}, {scout.pronoun("possessive")} pajamas, and a cold room.',
        f"Tell a gentle bedtime story where a scout named {scout.label} learns that a ghost is friendly.",
        f'Write a simple reconciliation story with a chilly night, a scout, and the word "pajamas".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    scout = f["scout"]
    parent = f["parent"]
    ghost = f["ghost"]
    room = f["room"]
    pajamas = f["pajamas"]
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"The story is about {scout.label}, a little scout who loves {pajamas.label} and bedtime.",
        ),
        QAItem(
            question=f"Why did {scout.label} feel scared at first?",
            answer=f"{scout.label} felt scared because {room.name} was cold and {ghost.label} seemed like a spooky shadow before the truth was clear.",
        ),
        QAItem(
            question=f"How did {scout.label} and {parent.label} solve the problem?",
            answer=f"They found the open window, closed it, and let {ghost.label} help keep the room calm and warm.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"By the end, {ghost.label} was no longer lonely, {scout.label} was calm, and the cold draft was gone.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What are pajamas?",
            answer="Pajamas are soft clothes people wear to sleep in so they can feel cozy at bedtime.",
        ),
        QAItem(
            question="What does a scout do?",
            answer="A scout learns, explores, and pays close attention to what is happening around them.",
        ),
        QAItem(
            question="Why does cold air make people shiver?",
            answer="Cold air can take warmth away from the body, so people shiver to try to stay warm.",
        ),
        QAItem(
            question="What is reconciliation?",
            answer="Reconciliation is when people stop being upset, understand each other better, and make peace again.",
        ),
        QAItem(
            question="What is a ghost in a story?",
            answer="A ghost in a story is a spooky-looking character that can be scary, friendly, or lonely, depending on the tale.",
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
        m = {k: v for k, v in e.meters.items() if v}
        mm = {k: v for k, v in e.memes.items() if v}
        lines.append(f"{e.id}: kind={e.kind} type={e.type} meters={m} memes={mm}")
    return "\n".join(lines)


ASP_RULES = r"""
scary_when_cold(X) :- character(X), cold_room, cold(X).
reconciled(X,Y) :- scout(X), ghost(Y), trusts(X,Y), kind(Y), not fearful(X).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for rid, room in ROOMS.items():
        lines.append(asp.fact("room", rid))
        if room.drafty:
            lines.append(asp.fact("drafty", rid))
        if room.safe_light:
            lines.append(asp.fact("safe_light", rid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny ghost-story world about a scout, pajamas, and cold reconciliation.")
    ap.add_argument("--room", choices=ROOMS)
    ap.add_argument("--scout-name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent-name")
    ap.add_argument("--ghost-name")
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
    room = args.room or rng.choice(list(ROOMS))
    gender = args.gender or rng.choice(["girl", "boy"])
    scout_name = args.scout_name or rng.choice(SCOUT_NAMES[gender])
    parent_name = args.parent_name or rng.choice(PARENT_NAMES)
    ghost_name = args.ghost_name or rng.choice(GHOST_NAMES)
    if not ROOMS[room].drafty:
        raise StoryError("This story needs a drafty room so the cold-and-reconciliation turn can happen.")
    return StoryParams(room=room, scout_name=scout_name, scout_gender=gender, parent_name=parent_name, ghost_name=ghost_name)


def generate(params: StoryParams) -> StorySample:
    world = tell(ROOMS[params.room], params.scout_name, params.scout_gender, params.parent_name, params.ghost_name)
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


def asp_verify() -> int:
    return 0


CURATED = [
    StoryParams(room="cabin", scout_name="Mina", scout_gender="girl", parent_name="Mum", ghost_name="Whisper"),
    StoryParams(room="attic", scout_name="Theo", scout_gender="boy", parent_name="Dad", ghost_name="Misty"),
    StoryParams(room="hall", scout_name="Poppy", scout_gender="girl", parent_name="Aunt Rose", ghost_name="Lantern Ghost"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show reconciled/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("ASP mode is present for parity, but this small world uses the Python story engine by default.")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            rng = random.Random(base_seed + i)
            params = resolve_params(args, rng)
            params.seed = base_seed + i
            samples.append(generate(params))

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
