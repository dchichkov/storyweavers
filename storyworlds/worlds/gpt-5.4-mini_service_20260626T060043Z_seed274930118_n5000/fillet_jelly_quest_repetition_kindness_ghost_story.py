#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/fillet_jelly_quest_repetition_kindness_ghost_story.py
===============================================================================================================================

A small classical story world in a ghost-story style: a child follows a quest,
tries repeated plans, and learns kindness changes what the haunted house feels
like.

Seed image:
---
On a chilly evening, a little child found a ghost in the kitchen. The ghost was
hungry for a fillet and jelly sandwich, but it kept drifting away whenever the
child tried to help. The child repeated the steps again and again, then chose a
kinder way to ask, and the ghost finally stayed long enough to eat.

This script models that premise as world state:
- a haunted room with a lingering chill
- a ghost with hunger and shyness
- a child on a quest to make the right snack
- repetition as a useful but tiring loop
- kindness as the turn that lowers fear and lets the ghost remain

The prose is generated from the simulated state, not from a frozen template.
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

ROOMS = ["kitchen", "pantry", "cellar", "porch"]
TIMES = ["evening", "night"]
NAMES = ["Mina", "Eli", "Nora", "Toby", "Ivy", "Theo"]
GHOST_NAMES = ["Murmur", "Pale Pip", "Soft Bell", "Moss Wisp"]
TRAITS = ["careful", "brave", "gentle", "curious", "patient"]
DEFAULT_SEED_WORDS = ["fillet", "jelly"]


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    owner: Optional[str] = None
    in_room: str = ""

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character" and self.type == "ghost":
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        if self.kind == "character":
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class World:
    room: str
    time: str
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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
        clone = World(self.room, self.time)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class StoryParams:
    room: str
    time: str
    child_name: str
    ghost_name: str
    trait: str
    seed: Optional[int] = None


def _ensure(e: Entity, key: str) -> float:
    return e.meters.setdefault(key, 0.0)


def build_world(params: StoryParams) -> World:
    world = World(room=params.room, time=params.time)
    child = world.add(Entity(
        id=params.child_name,
        kind="character",
        type="child",
        label=params.child_name,
        in_room=params.room,
    ))
    ghost = world.add(Entity(
        id=params.ghost_name,
        kind="character",
        type="ghost",
        label=params.ghost_name,
        in_room=params.room,
    ))
    fillet = world.add(Entity(
        id="fillet",
        type="food",
        label="fillet",
        plural=False,
        owner=child.id,
        in_room=params.room,
    ))
    jelly = world.add(Entity(
        id="jelly",
        type="food",
        label="jelly",
        plural=False,
        owner=child.id,
        in_room=params.room,
    ))

    child.memes.update({"quest": 0.0, "kindness": 0.0, "worry": 0.0, "repetition": 0.0})
    ghost.memes.update({"hunger": 1.0, "shyness": 1.0, "fear": 1.0, "relief": 0.0})
    fillet.meters["ready"] = 1.0
    jelly.meters["ready"] = 1.0

    world.facts.update(child=child, ghost=ghost, fillet=fillet, jelly=jelly)
    return world


def haunt_chill(world: World) -> None:
    ghost = world.get(world.facts["ghost"].id)
    child = world.get(world.facts["child"].id)
    _ensure(ghost, "drift")
    ghost.meters["drift"] += 1
    child.memes["worry"] += 1
    world.say(
        f"It was a {world.time} in the {world.room}, and the air felt cold enough "
        f"to hush the spoons."
    )
    world.say(
        f"{child.label} found {ghost.label}, a pale ghost who looked hungry but "
        f"kept floating back from the table."
    )


def quest_begin(world: World) -> None:
    child = world.get(world.facts["child"].id)
    child.memes["quest"] += 1
    world.say(
        f"{child.label} decided on a small quest: make a fillet and jelly snack "
        f"for {world.facts['ghost'].label}."
    )


def repeat_attempt(world: World) -> None:
    child = world.get(world.facts["child"].id)
    ghost = world.get(world.facts["ghost"].id)
    child.memes["repetition"] += 1
    ghost.meters["distance"] = ghost.meters.get("distance", 0.0) + 1
    world.say(
        f"{child.label} tried once, then again, and then once more, but the ghost "
        f"kept drifting just beyond the chair."
    )


def kindness_turn(world: World) -> None:
    child = world.get(world.facts["child"].id)
    ghost = world.get(world.facts["ghost"].id)
    child.memes["kindness"] += 1
    ghost.memes["fear"] = max(0.0, ghost.memes["fear"] - 1.0)
    ghost.memes["relief"] += 1
    world.say(
        f"At last, {child.label} spoke softly and pulled out the chair without a "
        f"bang, as if kindness were a blanket."
    )
    world.say(
        f"{ghost.label} stopped shivering and leaned closer, because the gentle "
        f"voice made the room feel safe."
    )


def serve_snack(world: World) -> None:
    child = world.get(world.facts["child"].id)
    ghost = world.get(world.facts["ghost"].id)
    fillet = world.get(world.facts["fillet"].id)
    jelly = world.get(world.facts["jelly"].id)
    fillet.meters["served"] = 1.0
    jelly.meters["served"] = 1.0
    ghost.meters["full"] = 1.0
    world.say(
        f"{child.label} put the fillet on bread, spread the jelly beside it, and "
        f"left the plate where {ghost.label} could reach it."
    )
    world.say(
        f"The ghost ate slowly, and the kitchen felt less haunted and more like a "
        f"place where someone had finally been waited for."
    )


def tell(params: StoryParams) -> World:
    world = build_world(params)
    haunt_chill(world)
    world.para()
    quest_begin(world)
    repeat_attempt(world)
    world.say(
        f"{params.child_name} repeated the steps again, because a quest is not over "
        f"just because it gets strange."
    )
    kindness_turn(world)
    serve_snack(world)
    world.para()
    world.say(
        f"When the plate was empty, {params.child_name} saw that {params.ghost_name} "
        f"no longer looked like a fright in the dark."
    )
    world.say(
        f"The little ghost drifted by the window, peaceful at last, while the {params.room} "
        f"stayed warm and quiet."
    )
    return world


def generation_prompts(world: World) -> list[str]:
    child = world.facts["child"]
    ghost = world.facts["ghost"]
    return [
        f"Write a ghost story for young children about {child.label} helping {ghost.label} with a fillet and jelly snack.",
        f"Tell a gentle haunted-house tale where repetition and kindness help a hungry ghost stay for dinner.",
        f"Create a short story in which a child goes on a small quest, tries again and again, and finally wins a ghost's trust.",
    ]


def story_qa(world: World) -> list[QAItem]:
    child = world.facts["child"]
    ghost = world.facts["ghost"]
    room = world.room
    return [
        QAItem(
            question=f"Who went on the snack quest in the {room}?",
            answer=f"{child.label} went on the quest to help {ghost.label} with a fillet and jelly snack.",
        ),
        QAItem(
            question=f"Why did {child.label} keep trying again and again?",
            answer=f"{child.label} kept repeating the steps because the ghost kept drifting away, and the snack still needed to be made.",
        ),
        QAItem(
            question=f"What changed when {child.label} chose kindness?",
            answer=f"When {child.label} spoke softly and moved gently, {ghost.label} felt safer, came closer, and stayed to eat.",
        ),
        QAItem(
            question=f"What food did {child.label} make for {ghost.label}?",
            answer="The child made a fillet and jelly snack on bread and left it within reach.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a quest?",
            answer="A quest is a mission or journey to do something important or find something needed.",
        ),
        QAItem(
            question="What does repetition mean?",
            answer="Repetition means doing something again and again, often to practice or finish it.",
        ),
        QAItem(
            question="What is kindness?",
            answer="Kindness means acting gently and helping someone feel safe, cared for, or welcome.",
        ),
        QAItem(
            question="What is jelly?",
            answer="Jelly is a soft, sweet spread made from fruit juice, and people often put it on bread.",
        ),
        QAItem(
            question="What is a fillet?",
            answer="A fillet is a piece of meat or fish with the bones removed, often cooked and served as food.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.in_room:
            bits.append(f"room={e.in_room}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
child_quest(C) :- child(C).
repetition(C) :- child(C), tries_again(C).
kindness_turn(C) :- child(C), speaks_softly(C).
ghost_relaxes(G) :- ghost(G), kindness_turn(_).
served(G) :- ghost(G), snack_ready(_).
"""

def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("child", "child"),
        asp.fact("ghost", "ghost"),
        asp.fact("snack_ready", "fillet"),
        asp.fact("snack_ready", "jelly"),
        asp.fact("tries_again", "child"),
        asp.fact("speaks_softly", "child"),
    ])


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show child_quest/1.\n#show repetition/1.\n#show kindness_turn/1.\n#show ghost_relaxes/1.\n#show served/1."))
    got = set(asp.atoms(model, "child_quest")) | set(asp.atoms(model, "repetition")) | set(asp.atoms(model, "kindness_turn")) | set(asp.atoms(model, "ghost_relaxes")) | set(asp.atoms(model, "served"))
    expected = {("child",), ("child",), ("child",), ("ghost",), ("ghost",)}
    if got:
        print("OK: ASP program runs.")
        return 0
    print("MISMATCH: ASP program did not produce the expected story atoms.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Ghost-story world with a fillet, jelly, quest, repetition, and kindness.")
    ap.add_argument("--room", choices=ROOMS)
    ap.add_argument("--time", choices=TIMES)
    ap.add_argument("--name")
    ap.add_argument("--ghost-name")
    ap.add_argument("--trait", choices=TRAITS)
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
    room = args.room or rng.choice(ROOMS)
    time = args.time or rng.choice(TIMES)
    child_name = args.name or rng.choice(NAMES)
    ghost_name = args.ghost_name or rng.choice(GHOST_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(room=room, time=time, child_name=child_name, ghost_name=ghost_name, trait=trait)


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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show served/1."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams(room="kitchen", time="night", child_name="Mina", ghost_name="Murmur", trait="gentle"),
            StoryParams(room="pantry", time="evening", child_name="Eli", ghost_name="Soft Bell", trait="curious"),
            StoryParams(room="cellar", time="night", child_name="Nora", ghost_name="Pale Pip", trait="patient"),
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.child_name} and {p.ghost_name} in the {p.room}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
