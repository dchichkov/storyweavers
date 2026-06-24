#!/usr/bin/env python3
"""
storyworlds/worlds/tend_rough_misunderstanding_repetition_sharing_ghost_story.py
===============================================================================

A small ghost-story world about tending a rough garden path, a misunderstanding
about a little ghost, repetition that slowly builds trust, and sharing that
turns fear into help.

A seed tale, imagined into a world model:
---
On a windy evening, Mina heard a soft bump-bump from the shed. She thought a
ghost had come to rattle the jars. But the sound was only Pip, a tiny friend
ghost trying to tend the rough path by carrying pebbles from one side to the
other.

Mina still felt scared, so Pip repeated the same gentle tap on the lantern
glass and pointed to the broken path. Mina finally understood. She shared her
gloves, Pip shared the pebble basket, and together they smoothed the path until
the moonlight shone cleanly over the garden.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
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
    role: str = ""
    ghosts: bool = False
    helper: bool = False
    shared: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        if self.ghosts:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Place:
    id: str
    label: str
    dark: bool = False
    rough: bool = False
    tendable: bool = False


@dataclass
class Problem:
    id: str
    label: str
    roughness: str
    misunderstanding: str
    repetition: str
    sharing_need: str


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    shared: bool = False


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

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
        c = World(self.place)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = dict(self.facts)
        return c


def propagate(world: World) -> None:
    changed = True
    while changed:
        changed = False
        if ("understand",) not in world.fired:
            if world.get("child").memes["understanding"] >= THRESHOLD:
                world.fired.add(("understand",))
                world.get("child").memes["fear"] = 0.0
                world.get("ghost").memes["lonely"] = 0.0
                changed = True
        if ("share",) not in world.fired:
            if world.get("child").memes["sharing"] >= THRESHOLD:
                world.fired.add(("share",))
                world.get("child").memes["trust"] += 1
                world.get("ghost").memes["trust"] += 1
                changed = True
        if ("tend",) not in world.fired:
            if world.get("child").meters["tending"] >= THRESHOLD and world.get("ghost").meters["tending"] >= THRESHOLD:
                world.fired.add(("tend",))
                world.get("path").meters["smooth"] += 1
                changed = True


def predict_misunderstanding(world: World) -> bool:
    sim = world.copy()
    sim.get("child").memes["fear"] += 1
    sim.get("ghost").meters["tap"] += 1
    return sim.get("child").memes["fear"] >= THRESHOLD


def tell(place: Place, problem: Problem, child_name: str = "Mina", ghost_name: str = "Pip") -> World:
    world = World(place)
    child = world.add(Entity(id="child", kind="character", type="girl", label=child_name))
    ghost = world.add(Entity(id="ghost", kind="character", type="thing", label=ghost_name, ghosts=True, helper=True))
    path = world.add(Entity(id="path", type="thing", label="the rough path"))
    lantern = world.add(Entity(id="lantern", type="thing", label="the lantern"))
    gloves = world.add(Entity(id="gloves", type="thing", label="the garden gloves", shared=True))
    pebbles = world.add(Entity(id="pebbles", type="thing", label="the pebble basket", shared=True))

    child.memes["fear"] += 1
    ghost.memes["lonely"] += 1

    world.say(f"At {place.label}, {child.label} heard a soft bump-bump in the dark shed.")
    world.say(f"{child.label} thought a ghost had come to rattle the jars.")
    world.para()
    world.say(f"But it was only {ghost.label}, a little ghost trying to {problem.id} {problem.roughness}.")
    world.say(f"{ghost.label} kept making the same gentle tap-tap on {lantern.label} because {problem.repetition}.")
    if predict_misunderstanding(world):
        world.say(f"{child.label} felt jumpy at first, since the sound was easy to misunderstand.")

    world.para()
    child.memes["fear"] += 1
    ghost.meters["tending"] += 1
    child.meters["tending"] += 1
    world.say(f"Again and again, {ghost.label} pointed to {path.label} and tapped the lantern glass.")
    world.say(f"Then {child.label} looked closer and understood that the ghost meant to {problem.id} it, not scare anyone.")
    child.memes["understanding"] += 1

    world.para()
    child.memes["sharing"] += 1
    ghost.memes["sharing"] += 1
    world.say(f"{child.label} shared {gloves.label}, and {ghost.label} shared {pebbles.label}.")
    world.say(f"Together they worked by moonlight, and by the end {path.label} was less rough and much easier to walk on.")
    propagate(world)

    world.para()
    world.say(f"The little ghost and the child stood side by side, quiet and pleased, while the garden felt safe again.")

    world.facts.update(
        child=child, ghost=ghost, path=path, lantern=lantern, gloves=gloves, pebbles=pebbles,
        place=place, problem=problem, resolved=True, misunderstood=True
    )
    return world


PLACES = {
    "garden": Place(id="garden", label="the garden", dark=True, rough=True, tendable=True),
    "yard": Place(id="yard", label="the backyard", dark=True, rough=True, tendable=True),
    "orchard": Place(id="orchard", label="the orchard", dark=True, rough=True, tendable=True),
}

PROBLEMS = {
    "tend": Problem(
        id="tend",
        label="tend",
        roughness="by moving pebbles aside and smoothing the edges",
        misunderstanding="the tapping meant only to help",
        repetition="the ghost had to repeat the same tap so the child would notice",
        sharing_need="the path needed gloves and a basket",
    ),
    "rough": Problem(
        id="rough",
        label="rough",
        roughness="by picking up stones and filling little holes",
        misunderstanding="the repeated taps were a clue, not a warning",
        repetition="the tapping had to happen three times before anyone understood",
        sharing_need="the work was easier when they shared tools",
    ),
}

GLOVE = Tool(id="gloves", label="gloves", phrase="garden gloves", shared=True)
BASKET = Tool(id="basket", label="basket", phrase="a pebble basket", shared=True)


def valid_combos() -> list[tuple[str, str]]:
    return [(p, pr) for p in PLACES for pr in PROBLEMS]


@dataclass
class StoryParams:
    place: str
    problem: str
    child: str
    ghost: str
    seed: Optional[int] = None


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a gentle ghost story for a 3-to-5-year-old set in {f["place"].label} about a misunderstanding that gets fixed by repetition and sharing.',
        f"Tell a small spooky-but-kind story where {f['child'].label} first thinks {f['ghost'].label} is scary, but learns the ghost is trying to {f['problem'].label}.",
        f'Write a short story that includes the words "tend", "rough", and "sharing", and ends with the child and ghost helping each other.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    c, g, p = f["child"], f["ghost"], f["problem"]
    return [
        QAItem(
            question=f"Why did {c.label} think the ghost was scary at first?",
            answer=f"{c.label} heard a bump-bump in the dark and misunderstood it. The sound seemed spooky until {g.label} repeated the tapping and showed that it was helping.",
        ),
        QAItem(
            question=f"What did {g.label} keep doing again and again?",
            answer=f"{g.label} repeated the same gentle tap and pointed to the rough path. That repetition helped {c.label} understand that the ghost meant to {p.label}, not frighten anyone.",
        ),
        QAItem(
            question=f"What did {c.label} and {g.label} share at the end?",
            answer=f"{c.label} shared the garden gloves, and {g.label} shared the pebble basket. Sharing made it easier for both of them to tend the rough path together.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is a ghost in a story?", answer="A ghost in a story is often a spooky-looking figure, but in a gentle story it can be a kind helper too."),
        QAItem(question="What does it mean to misunderstand something?", answer="To misunderstand something means to think it means one thing when it really means something else."),
        QAItem(question="Why does repetition help?", answer="Repetition helps because hearing or seeing the same clue again can make it easier to notice and understand."),
    ]


def format_qa(sample: StorySample) -> str:
    parts = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        parts.append(f"{i}. {p}")
    parts.append("")
    parts.append("== (2) Story questions ==")
    for q in sample.story_qa:
        parts.append(f"Q: {q.question}")
        parts.append(f"A: {q.answer}")
    parts.append("")
    parts.append("== (3) World questions ==")
    for q in sample.world_qa:
        parts.append(f"Q: {q.question}")
        parts.append(f"A: {q.answer}")
    return "\n".join(parts)


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
        if e.ghosts:
            bits.append("ghosts=True")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="garden", problem="tend", child="Mina", ghost="Pip"),
    StoryParams(place="yard", problem="rough", child="Ivy", ghost="Moss"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Ghost story world: misunderstanding, repetition, sharing, and tending a rough path.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--child")
    ap.add_argument("--ghost")
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
    if args.problem:
        combos = [c for c in combos if c[1] == args.problem]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, problem = rng.choice(combos)
    child = args.child or rng.choice(["Mina", "Ivy", "Nora", "Lena", "Ada"])
    ghost = args.ghost or rng.choice(["Pip", "Moss", "Wisp", "Mote"])
    return StoryParams(place=place, problem=problem, child=child, ghost=ghost)


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], PROBLEMS[params.problem], params.child, params.ghost)
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
valid(P, R) :- place(P), problem(R).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for r in PROBLEMS:
        lines.append(asp.fact("problem", r))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp
    a = set(asp_valid_combos())
    b = set(valid_combos())
    if a == b:
        print(f"OK: clingo gate matches valid_combos() ({len(a)} combos).")
        return 0
    print("MISMATCH between clingo and python.")
    return 1


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos")
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, s in enumerate(samples):
        emit(s, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
