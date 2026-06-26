#!/usr/bin/env python3
"""
storyworlds/worlds/grief_flashback_repetition_ghost_story.py
=============================================================

A small ghost-story world about grief, a repeated haunting pattern, and a
memory that keeps returning until it is named.

The domain is intentionally narrow:
- one child or adult grieving someone they loved
- one place that still carries a memory
- one ghostly sign that repeats
- one flashback that reveals what was lost
- one ending in which the living person changes how they carry the grief

The simulated world tracks physical meters and emotional memes, and the story is
written from state changes rather than from a frozen paragraph template.
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


# ---------------------------------------------------------------------------
# Core world model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "ghost" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Place:
    id: str
    label: str
    details: str


@dataclass
class MemoryItem:
    id: str
    label: str
    owner: str
    ghost_tied: bool = False


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.memory_items: dict[str, MemoryItem] = {}
        self.fired: set[tuple] = set()
        self.lines: list[str] = []
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def add_memory(self, mem: MemoryItem) -> MemoryItem:
        self.memory_items[mem.id] = mem
        return mem

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
# Parameters and registries
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    grieving: str
    ghost: str
    memory: str
    name: str
    age: str
    relation: str
    seed: Optional[int] = None


PLACES = {
    "attic": Place("attic", "the attic", "dusty beams and a small round window"),
    "hallway": Place("hallway", "the hallway", "a long wooden floor and a stubborn draft"),
    "bedroom": Place("bedroom", "the bedroom", "a bed with a quilt and a moonlit wall"),
    "garden": Place("garden", "the garden", "wet grass, a fence, and a quiet gate"),
}

GRIEVING_WORDS = {
    "missing": "missing",
    "lonely": "lonely",
    "heavy": "heavy",
    "empty": "empty",
}

GHOSTS = {
    "grandma": "Grandma's ghost",
    "brother": "the brother's ghost",
    "mother": "Mother's ghost",
    "dog": "the dog's ghost",
}

MEMORIES = {
    "song": "a humming song",
    "scarf": "a striped scarf",
    "lantern": "a little lantern",
    "chair": "a rocking chair",
}

NAMES = ["Mina", "Nora", "Eli", "June", "Theo", "Maya", "Iris", "Leo"]


# ---------------------------------------------------------------------------
# Narrative logic
# ---------------------------------------------------------------------------
def build_world(params: StoryParams) -> World:
    place = PLACES[params.place]
    world = World(place)

    child = world.add(Entity(
        id=params.name,
        kind="character",
        type="girl" if params.age == "young" else "boy",
        label=params.name,
        meters={"fear": 0.0, "bravery": 0.0},
        memes={"grief": 2.0, "longing": 1.0},
    ))

    ghost = world.add(Entity(
        id="ghost",
        kind="ghost",
        type="ghost",
        label=params.ghost,
        meters={"flicker": 1.0},
        memes={"sadness": 1.0, "memory": 2.0},
    ))

    memory = world.add_memory(MemoryItem(
        id="memory",
        label=params.memory,
        owner=child.id,
        ghost_tied=True,
    ))

    world.facts.update(
        child=child,
        ghost=ghost,
        memory=memory,
        place=place,
        grieving=params.grieving,
        relation=params.relation,
    )

    # Setup
    world.say(
        f"{child.id} lived near {place.label}, and {child.pronoun('possessive')} heart felt {params.grieving} "
        f"after {params.relation} was gone."
    )
    world.say(
        f"Inside the old place, one small thing kept the memory alive: {params.memory}."
    )

    # First haunting beat
    world.para()
    ghost_repetition(world, child, ghost, memory)

    # Flashback
    world.para()
    flashback(world, child, memory, params.relation)

    # Second haunting beat, now more personal
    world.para()
    ghost_repetition(world, child, ghost, memory)

    # Resolution
    world.para()
    resolve_grief(world, child, ghost, memory, place)

    return world


def ghost_repetition(world: World, child: Entity, ghost: Entity, memory: MemoryItem) -> None:
    key = ("repeat", ghost.id, memory.id)
    if key in world.fired:
        return
    world.fired.add(key)
    child.meters["fear"] += 1.0
    ghost.meters["flicker"] += 1.0
    child.memes["grief"] += 0.5
    world.say(
        f"At night, {memory.label} moved by itself. Then the same soft knock came again, "
        f"three slow taps from the same corner."
    )
    world.say(
        f"{child.id} looked up, and {ghost.label} was there, pale as window fog, then gone, then there again."
    )
    world.say(
        f"It was the kind of haunting that did not hurry. It simply returned, and returned, and returned."
    )


def flashback(world: World, child: Entity, memory: MemoryItem, relation: str) -> None:
    key = ("flashback", memory.id)
    if key in world.fired:
        return
    world.fired.add(key)
    child.meters["fear"] = max(0.0, child.meters.get("fear", 0.0) - 0.25)
    child.memes["grief"] += 1.0
    world.say(
        f"That sound pulled {child.id} back to the day {relation} smiled and set {memory.label} down carefully."
    )
    world.say(
        f"For a moment, the room was not cold and old at all. It was warm, and there was laughter in it."
    )
    world.say(
        f"{child.id} remembered how {relation} used to say the little thing would keep the house from feeling alone."
    )


def resolve_grief(world: World, child: Entity, ghost: Entity, memory: MemoryItem, place: Place) -> None:
    key = ("resolve", child.id)
    if key in world.fired:
        return
    world.fired.add(key)
    child.meters["bravery"] += 1.5
    child.meters["fear"] = max(0.0, child.meters.get("fear", 0.0) - 0.75)
    child.memes["grief"] = max(0.0, child.memes.get("grief", 0.0) - 1.0)
    child.memes["longing"] = max(0.0, child.memes.get("longing", 0.0) - 0.5)
    world.say(
        f"At last, {child.id} whispered, 'I know you are only a memory now.'"
    )
    world.say(
        f"The ghost did not answer with words, but the air felt less sharp."
    )
    world.say(
        f"{child.id} placed {memory.label} on the shelf by the window, where {place.label} could hold it gently."
    )
    world.say(
        f"And after that, the knocking did not ask to come in anymore. It stayed in the memory, where it belonged."
    )


# ---------------------------------------------------------------------------
# Story text helpers
# ---------------------------------------------------------------------------
def choose_name(rng: random.Random) -> str:
    return rng.choice(NAMES)


def choose_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(sorted(PLACES))
    grief = args.grief or rng.choice(sorted(GRIEVING_WORDS))
    ghost = args.ghost or rng.choice(sorted(GHOSTS))
    memory = args.memory or rng.choice(sorted(MEMORIES))
    name = args.name or choose_name(rng)
    age = args.age or rng.choice(["young", "older"])
    relation = args.relation or {
        "grandma": "Grandma",
        "mother": "Mother",
        "brother": "an older brother",
        "dog": "a beloved dog",
    }[ghost]
    return StoryParams(
        place=place,
        grieving=grief,
        ghost=ghost,
        memory=memory,
        name=name,
        age=age,
        relation=relation,
    )


def generate_story(params: StoryParams) -> StorySample:
    world = build_world(params)
    story = world.render()
    prompts = generation_prompts(world)
    return StorySample(
        params=params,
        story=story,
        prompts=prompts,
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child: Entity = f["child"]  # type: ignore[assignment]
    place: Place = f["place"]  # type: ignore[assignment]
    ghost: Entity = f["ghost"]  # type: ignore[assignment]
    memory: MemoryItem = f["memory"]  # type: ignore[assignment]
    return [
        f"Write a short ghost story for children about {child.id} at {place.label} with a repeating knock and a sad memory.",
        f"Tell a gentle story where {child.id} keeps seeing {ghost.label} and slowly learns what the knocking means.",
        f"Write a simple story that includes {memory.label}, a flashback, and the same spooky sign happening more than once.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = f["child"]  # type: ignore[assignment]
    ghost: Entity = f["ghost"]  # type: ignore[assignment]
    memory: MemoryItem = f["memory"]  # type: ignore[assignment]
    place: Place = f["place"]  # type: ignore[assignment]
    relation = f["relation"]
    return [
        QAItem(
            question=f"Where did {child.id} keep hearing the repeated knocking?",
            answer=f"{child.id} kept hearing it in {place.label}, where the air felt old and quiet.",
        ),
        QAItem(
            question=f"What made {child.id} remember the person who was gone?",
            answer=f"{memory.label} brought back the memory of {relation}, and that memory opened the flashback.",
        ),
        QAItem(
            question=f"Why did the ghost seem less frightening at the end?",
            answer=f"Because {child.id} understood the ghost was tied to grief and memory, not to harm, and that made the haunting gentler.",
        ),
        QAItem(
            question=f"What happened again and again in the story?",
            answer=f"The same soft knocking and the ghostly appearance happened more than once, which made the haunting feel like a repetition.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is grief?",
            answer="Grief is the sad feeling people have when someone they love is gone.",
        ),
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is a scene that shows something that happened before the present moment.",
        ),
        QAItem(
            question="What does repetition do in a ghost story?",
            answer="Repetition makes a haunting feel stronger because the same sign returns again and again.",
        ),
        QAItem(
            question="Why do stories about ghosts often feel quiet?",
            answer="Ghost stories often feel quiet because they use still rooms, little sounds, and lonely places to make the spooky feeling grow.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        lines.append(
            f"{e.id}: kind={e.kind} type={e.type} meters={dict(e.meters)} memes={dict(e.memes)}"
        )
    for m in world.memory_items.values():
        lines.append(f"{m.id}: label={m.label} owner={m.owner} ghost_tied={m.ghost_tied}")
    lines.append(f"fired={sorted(world.fired)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
place(attic;hallway;bedroom;garden).
grief_word(missing;lonely;heavy;empty).
ghost_word(grandma;brother;mother;dog).
memory_word(song;scarf;lantern;chair).

valid(P,G,H,M) :- place(P), grief_word(G), ghost_word(H), memory_word(M).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for g in GRIEVING_WORDS:
        lines.append(asp.fact("grief_word", g))
    for h in GHOSTS:
        lines.append(asp.fact("ghost_word", h))
    for m in MEMORIES:
        lines.append(asp.fact("memory_word", m))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def python_valid() -> list[tuple]:
    return sorted((p, g, h, m) for p in PLACES for g in GRIEVING_WORDS for h in GHOSTS for m in MEMORIES)


def asp_verify() -> int:
    a, b = set(asp_valid()), set(python_valid())
    if a == b:
        print(f"OK: ASP and Python agree on {len(a)} combinations.")
        return 0
    print("Mismatch:")
    print("only in ASP:", sorted(a - b))
    print("only in Python:", sorted(b - a))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Ghost story world with grief, flashback, and repetition.")
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--grief", choices=sorted(GRIEVING_WORDS))
    ap.add_argument("--ghost", choices=sorted(GHOSTS))
    ap.add_argument("--memory", choices=sorted(MEMORIES))
    ap.add_argument("--name")
    ap.add_argument("--age", choices=["young", "older"])
    ap.add_argument("--relation")
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
    return choose_params(args, rng)


def generate(params: StoryParams) -> StorySample:
    return generate_story(params)


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
    StoryParams(place="attic", grieving="heavy", ghost="grandma", memory="scarf", name="Mina", age="young", relation="Grandma"),
    StoryParams(place="hallway", grieving="empty", ghost="mother", memory="lantern", name="Eli", age="older", relation="Mother"),
    StoryParams(place="bedroom", grieving="lonely", ghost="brother", memory="song", name="June", age="young", relation="an older brother"),
    StoryParams(place="garden", grieving="missing", ghost="dog", memory="chair", name="Theo", age="older", relation="a beloved dog"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid/4."))
        vals = sorted(set(asp.atoms(model, "valid")))
        for row in vals:
            print(" ".join(map(str, row)))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        for i in range(max(args.n * 20, 20)):
            if len(samples) >= args.n:
                break
            rng = random.Random(base_seed + i)
            params = resolve_params(args, rng)
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

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
