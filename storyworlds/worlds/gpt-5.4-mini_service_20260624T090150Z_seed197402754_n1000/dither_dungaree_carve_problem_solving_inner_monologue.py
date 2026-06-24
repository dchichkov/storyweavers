#!/usr/bin/env python3
"""
Standalone storyworld: a child in a ghostly shed, a stubborn task, and a
small problem solved by thinking through the fear.

This world is intentionally compact:
- one child
- one eerie place
- one spooky object
- one helper ghost
- one practical fix

The story style is ghost-story flavored, but child-friendly and gentle.
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
# Core data model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    type: str = "thing"
    plural: bool = False
    owner: Optional[str] = None
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
class StoryParams:
    place: str
    task: str
    garment: str
    child_name: str
    child_type: str
    seed: Optional[int] = None


@dataclass
class Place:
    id: str
    label: str
    eerie: bool
    keyword: str
    task_suitable: set[str] = field(default_factory=set)


@dataclass
class Task:
    id: str
    verb: str
    gerund: str
    obstacle: str
    success_image: str
    keyword: str
    risk: str


@dataclass
class Garment:
    id: str
    label: str
    phrase: str
    protects: set[str]
    kind: str = "clothing"


@dataclass
class World:
    place: Place
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


# ---------------------------------------------------------------------------
# Content registries
# ---------------------------------------------------------------------------
PLACES = {
    "attic": Place(id="attic", label="the attic", eerie=True, keyword="dust",
                   task_suitable={"carve"}),
    "shed": Place(id="shed", label="the old shed", eerie=True, keyword="rain",
                  task_suitable={"carve"}),
    "porch": Place(id="porch", label="the porch", eerie=True, keyword="wind",
                   task_suitable={"carve"}),
}

TASKS = {
    "carve": Task(
        id="carve",
        verb="carve a lantern",
        gerund="carving a lantern",
        obstacle="the knife kept slipping on the stubborn rind",
        success_image="the lantern face shone warmly",
        keyword="carve",
        risk="a crooked cut",
    ),
    "fix": Task(
        id="fix",
        verb="fix the creaky sign",
        gerund="fixing the creaky sign",
        obstacle="the nail would not stay in the wood",
        success_image="the sign hung straight at last",
        keyword="fix",
        risk="a bent nail",
    ),
}

GARMENTS = {
    "dungaree": Garment(
        id="dungaree",
        label="dungarees",
        phrase="sturdy dungarees",
        protects={"legs", "torso"},
        kind="clothing",
    ),
    "apron": Garment(
        id="apron",
        label="an apron",
        phrase="a long apron",
        protects={"torso"},
        kind="clothing",
    ),
}

NAMES = ["Milo", "Nina", "Toby", "June", "Pia", "Eli"]
CHILD_TYPES = ["boy", "girl"]
FEARS = ["shadowy corners", "soft creaks", "the dark window", "a whisper in the rafters"]


# ---------------------------------------------------------------------------
# World simulation
# ---------------------------------------------------------------------------
def build_world(params: StoryParams) -> World:
    place = PLACES[params.place]
    task = TASKS[params.task]
    garment = GARMENTS[params.garment]
    world = World(place=place)

    child = world.add(Entity(
        id=params.child_name,
        kind="character",
        type=params.child_type,
        meters={"nervous": 0.0, "bold": 0.0, "mess": 0.0},
        memes={"dither": 0.0, "hope": 0.0, "relief": 0.0, "focus": 0.0},
    ))
    ghost = world.add(Entity(
        id="ghost",
        kind="character",
        type="ghost",
        label="a small ghost",
        meters={"glow": 1.0},
        memes={"mystery": 1.0},
    ))
    wear = world.add(Entity(
        id=garment.id,
        kind="thing",
        label=garment.label,
        type="garment",
        plural=(garment.id == "dungaree"),
        owner=child.id,
        worn_by=child.id,
        meters={"clean": 1.0},
    ))
    lantern = world.add(Entity(
        id="lantern",
        kind="thing",
        label="lantern",
        type="object",
        owner=child.id,
        meters={"unfinished": 1.0},
    ))

    # Act 1: setup.
    world.say(f"{child.id} stood in {place.label}, where the air felt cool and a little strange.")
    world.say(f"{child.pronoun().capitalize()} wore {wear.label} and wanted to {task.verb}.")
    world.say(f"Somewhere nearby, {ghost.label} drifted past the rafters without making a sound.")
    world.say(f"{child.id} liked the idea, but {child.pronoun('possessive')} mind began to dither.")
    child.memes["dither"] += 1
    child.meters["nervous"] += 1

    # Act 2: inner monologue and obstacle.
    world.para()
    world.say(
        f'"What if {task.risk} ruins the whole shape?" {child.id} thought. '
        f'"What if I make it look silly? What if the dark is worse after I start?"'
    )
    world.say(f"{child.id} looked down at the work, then back at {ghost.label}, and took one careful breath.")
    child.memes["focus"] += 1
    child.meters["bold"] += 1
    world.say(f"Inside {child.pronoun('possessive')} head, a quieter thought answered: 'Start small. Make one good cut.'")

    # Ghost helps without taking over.
    world.say(
        f"{ghost.label} lifted a little hand and pointed at the safest line to carve, "
        f"as if to say the problem had a gentle edge."
    )
    child.memes["hope"] += 1
    world.say(f"{child.id} nodded and began to {task.verb} along the line.")

    # Resolution.
    world.para()
    world.say(f"It took patience, but {task.obstacle} slowly stopped mattering.")
    world.say(f"{child.id} kept thinking one step at a time, and the task finally worked.")
    world.say(f"At last, {task.success_image}, and the room no longer felt so cold.")
    child.memes["relief"] += 1
    child.meters["nervous"] = max(0.0, child.meters["nervous"] - 1.0)
    world.say(f"{child.id} smiled at {ghost.label}, and the little ghost flickered like a candle in thanks.")
    world.say(f"In {child.pronoun('possessive')} {garment.label}, {child.id} held up the finished work and felt braver than before.")

    world.facts.update(
        child=child,
        ghost=ghost,
        garment=wear,
        lantern=lantern,
        task=task,
        place=place,
    )
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    task = f["task"]
    place = f["place"]
    return [
        f'Write a gentle ghost story for preschoolers about {child.id} in {place.label} who wants to {task.verb}.',
        f'Write a story with inner monologue where a child thinks through a spooky problem and keeps going.',
        f'Write a small problem-solving story that includes "{task.keyword}" and a child wearing dungarees.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    task = f["task"]
    place = f["place"]
    garment = f["garment"]
    ghost = f["ghost"]
    return [
        QAItem(
            question=f"What did {child.id} want to do in {place.label}?",
            answer=f"{child.id} wanted to {task.verb}.",
        ),
        QAItem(
            question=f"What did {child.id} wear while getting ready to work?",
            answer=f"{child.id} wore {garment.label}.",
        ),
        QAItem(
            question=f"How did the story show {child.id}'s feelings before the work got easier?",
            answer=f"It showed {child.id} dithering, feeling nervous, and worrying in an inner monologue about making a mistake.",
        ),
        QAItem(
            question=f"Who helped {child.id} without taking over the job?",
            answer=f"A small ghost helped by pointing out the safest line to follow.",
        ),
        QAItem(
            question=f"What changed at the end of the story?",
            answer=f"{child.id} solved the problem, finished the task, and felt braver at the end.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What are dungarees?",
            answer="Dungarees are sturdy clothes with straps that can protect your outfit while you work or play.",
        ),
        QAItem(
            question="What does it mean to dither?",
            answer="To dither means to hesitate and keep wavering instead of choosing right away.",
        ),
        QAItem(
            question="What does it mean to carve?",
            answer="To carve means to cut a shape into something, often with a tool.",
        ),
        QAItem(
            question="Why can a ghost story still be gentle for children?",
            answer="A gentle ghost story can be spooky in mood but still safe, friendly, and calm enough for children.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== generation prompts =="]
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


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
place(attic). place(shed). place(porch).
task(carve). task(fix).
garment(dungaree). garment(apron).

eerie(attic). eerie(shed). eerie(porch).
suitable(attic,carve). suitable(shed,carve). suitable(porch,carve).

protects(dungaree,legs). protects(dungaree,torso).
protects(apron,torso).

compatible(P,T,G) :- suitable(P,T), protects(G,torso).
compatible(P,T,G) :- suitable(P,T), protects(G,legs).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        if p.eerie:
            lines.append(asp.fact("eerie", pid))
        for t in sorted(p.task_suitable):
            lines.append(asp.fact("suitable", pid, t))
    for tid in TASKS:
        lines.append(asp.fact("task", tid))
    for gid, g in GARMENTS.items():
        lines.append(asp.fact("garment", gid))
        for part in sorted(g.protects):
            lines.append(asp.fact("protects", gid, part))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show compatible/3."))
    return sorted(set(asp.atoms(model, "compatible")))


def asp_verify() -> int:
    py = {(p, t, g) for p in PLACES for t in TASKS for g in GARMENTS if p in {"attic", "shed", "porch"} and t == "carve"}
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches python ({len(cl)} combos).")
        return 0
    print("MISMATCH:")
    print("python-only:", sorted(py - cl))
    print("clingo-only:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Validation / generation
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for p in PLACES:
        for t in TASKS:
            for g in GARMENTS:
                if t == "carve":
                    combos.append((p, t, g))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Ghost-story world with dither, dungarees, carving, and gentle problem solving.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--garment", choices=GARMENTS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=CHILD_TYPES)
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
    combos = valid_combos()
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.task:
        combos = [c for c in combos if c[1] == args.task]
    if args.garment:
        combos = [c for c in combos if c[2] == args.garment]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, task, garment = rng.choice(combos)
    name = args.name or rng.choice(NAMES)
    gender = args.gender or rng.choice(CHILD_TYPES)
    return StoryParams(place=place, task=task, garment=garment, child_name=name, child_type=gender)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
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
        print()
        print("--- trace ---")
        for e in sample.world.entities.values():
            print(e.id, e.kind, e.type, e.meters, e.memes)
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show compatible/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid_combos()
        for p, t, g in triples:
            print(p, t, g)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for p in PLACES:
            samples.append(generate(StoryParams(place=p, task="carve", garment="dungaree", child_name="Milo", child_type="boy")))
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
            seed = base_seed + i
            i += 1
            rng = random.Random(seed)
            try:
                params = resolve_params(args, rng)
            except StoryError as err:
                print(err)
                return
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
