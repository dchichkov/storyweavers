#!/usr/bin/env python3
"""
storyworlds/worlds/curve_kindness_mystery_to_solve_bedtime_story.py
===================================================================

A tiny bedtime-story world about a child, a curved path, a small mystery, and a
kind answer that helps everything feel safe again.

The premise is simple: a child notices a gentle curve in the world -- a bend in
a path, a river, a hallway, or a lane -- and that curve hides a clue. Something
is missing or unexplained at bedtime. The child uses kindness, patience, and a
soft question to solve the mystery without making anyone feel scared.

The world model tracks both physical state (meters) and emotional state (memes).
The story is not a frozen paragraph: the curve reveals clues, the mystery grows
into worry, kind actions lower fear, and the ending shows the solved secret.

Supported themes:
- curve
- kindness
- mystery to solve
- bedtime story style
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
# World entities
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    helper: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"curiosity": 0.0, "clue": 0.0, "comfort": 0.0}
        if not self.memes:
            self.memes = {"worry": 0.0, "kindness": 0.0, "relief": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        feminine = {"girl", "mother", "mom", "woman"}
        masculine = {"boy", "father", "dad", "man"}
        if self.type in feminine:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in masculine:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def noun(self) -> str:
        return self.label or self.type


@dataclass
class Place:
    id: str
    label: str
    curve_kind: str
    bedtime_hush: str
    clue_style: str
    mystery_kind: str
    answer_kind: str
    affords: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    child_name: str
    child_type: str
    parent_type: str
    clue: str
    mystery: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[tuple[str, ...]] = set()

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
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
PLACES = {
    "garden_path": Place(
        id="garden_path",
        label="the garden path",
        curve_kind="gentle curve",
        bedtime_hush="The garden was quiet, with night flowers sleeping under the moon.",
        clue_style="tiny silver pebbles",
        mystery_kind="a missing lantern",
        answer_kind="a lantern tucked by the curved rosebush",
        affords={"peek", "follow", "listen"},
    ),
    "river_bend": Place(
        id="river_bend",
        label="the river bend",
        curve_kind="soft bend",
        bedtime_hush="The river moved slowly and made a sleepy whisper on the stones.",
        clue_style="shining reeds",
        mystery_kind="a lost toy boat",
        answer_kind="a toy boat caught in the reeds",
        affords={"peek", "follow", "listen"},
    ),
    "hallway_turn": Place(
        id="hallway_turn",
        label="the hallway turn",
        curve_kind="rounded corner",
        bedtime_hush="The hallway was dim and cozy, with warm lamplight on the walls.",
        clue_style="little sock prints",
        mystery_kind="a missing bedtime note",
        answer_kind="a bedtime note slipped behind the basket",
        affords={"peek", "follow", "listen"},
    ),
    "sleepy_lane": Place(
        id="sleepy_lane",
        label="the sleepy lane",
        curve_kind="curving lane",
        bedtime_hush="The lane outside was hushed, and the windows held sleepy yellow glows.",
        clue_style="soft hoof marks",
        mystery_kind="a missing scarf",
        answer_kind="a scarf waiting on a low fence",
        affords={"peek", "follow", "listen"},
    ),
}

CHILD_NAMES = ["Mia", "Noah", "Lina", "Eli", "Nora", "Theo", "Ava", "Sam"]
CHILD_TYPES = ["girl", "boy"]
PARENT_TYPES = ["mother", "father"]

CLUES = {
    "pebbles": "tiny silver pebbles",
    "reeds": "shining reeds",
    "prints": "little sock prints",
    "hoofmarks": "soft hoof marks",
}


# ---------------------------------------------------------------------------
# Story engine
# ---------------------------------------------------------------------------
def _add_meter(ent: Entity, key: str, amount: float) -> None:
    ent.meters[key] = ent.meters.get(key, 0.0) + amount


def _add_meme(ent: Entity, key: str, amount: float) -> None:
    ent.memes[key] = ent.memes.get(key, 0.0) + amount


def _spend_meme(ent: Entity, key: str, amount: float) -> None:
    ent.memes[key] = max(0.0, ent.memes.get(key, 0.0) - amount)


def _soften(world: World, child: Entity, parent: Entity) -> None:
    if child.memes["worry"] < 1:
        return
    if ("soften", child.id) in world.fired:
        return
    world.fired.add(("soften", child.id))
    _spend_meme(child, "worry", 1)
    _add_meme(child, "kindness", 1)
    _add_meme(parent, "relief", 1)
    world.say(
        f"{child.pronoun().capitalize()} took a slow breath, held the worry gently, and asked in a kind voice."
    )


def _solve(world: World, child: Entity, parent: Entity, mystery: Entity, clue: Entity) -> None:
    if child.meters["clue"] < 1 or ("solve", mystery.id) in world.fired:
        return
    world.fired.add(("solve", mystery.id))
    _add_meme(child, "relief", 1)
    _add_meme(parent, "relief", 1)
    mystery.meters["clue"] = 1
    world.say(
        f"The clue led them to the answer, and the little mystery stopped feeling big."
    )


def _narrate_bedtime(world: World, child: Entity, parent: Entity, clue: Entity, mystery: Entity) -> None:
    world.say(
        f"{child.id} was a little {child.type} who loved bedtime stories and moonlit walks."
    )
    world.say(
        f"That night, {child.id} and {child.pronoun('possessive')} {parent.noun()} went to {world.place.label}."
    )
    world.say(world.place.bedtime_hush)
    world.say(
        f"The {world.place.curve_kind} was special, because it hid {world.place.clue_style} near the turn."
    )
    world.para()
    world.say(
        f"{child.id} noticed something missing: {mystery.phrase}. That made {child.pronoun('object')} feel curious and a little worried."
    )
    _add_meter(child, "curiosity", 1)
    _add_meme(child, "worry", 1)
    clue.meters["clue"] = 1
    world.say(
        f"Then {child.id} spotted {clue.label} beside the curve, as if the path itself wanted to help."
    )


def _ask_kindly(world: World, child: Entity, parent: Entity, mystery: Entity, clue: Entity) -> None:
    if ("ask_kindly", child.id) in world.fired:
        return
    world.fired.add(("ask_kindly", child.id))
    _add_meme(child, "kindness", 1)
    world.say(
        f'{child.id} did not rush. {child.pronoun().capitalize()} asked kindly, "Has anyone seen {mystery.label}?"'
    )
    world.say(
        f"That gentle question made the night feel safer, and even the shadows seemed to listen."
    )


def _reveal(world: World, child: Entity, parent: Entity, mystery: Entity, clue: Entity) -> None:
    if ("reveal", mystery.id) in world.fired:
        return
    world.fired.add(("reveal", mystery.id))
    world.say(
        f"A sleepy little answer appeared: {world.place.answer_kind}."
    )
    world.say(
        f"The clue matched the answer, and {child.id} could see that the mystery had only been hiding in a cozy place."
    )
    _add_meme(child, "relief", 1)
    _add_meme(parent, "relief", 1)


def tell(place: Place, child_name: str, child_type: str, parent_type: str, clue_key: str, mystery_key: str) -> World:
    world = World(place)
    child = world.add(Entity(id=child_name, kind="character", type=child_type, label=child_name))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label=f"the {parent_type}"))
    clue = world.add(Entity(id="clue", type="thing", label=CLUES[clue_key], phrase=CLUES[clue_key]))
    mystery = world.add(Entity(
        id="mystery",
        type="thing",
        label=mystery_key.replace("_", " "),
        phrase=f"a {mystery_key.replace('_', ' ')}",
    ))
    world.facts.update(child=child, parent=parent, clue=clue, mystery=mystery)
    _narrate_bedtime(world, child, parent, clue, mystery)
    world.para()
    _ask_kindly(world, child, parent, mystery, clue)
    _soften(world, child, parent)
    _reveal(world, child, parent, mystery, clue)
    _solve(world, child, parent, mystery, clue)
    world.para()
    world.say(
        f"In the end, {child.id} had found the answer, {mystery.label} was no longer missing, and the {place.curve_kind} looked like a smiling ribbon in the dark."
    )
    world.say(
        f"{child.id} and {parent.noun()} walked home feeling calm, with kindness shining brighter than the moon."
    )
    return world


# ---------------------------------------------------------------------------
# QA and prompts
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child: Entity = f["child"]
    parent: Entity = f["parent"]
    mystery: Entity = f["mystery"]
    return [
        f'Write a bedtime story for a small child about a "{world.place.curve_kind}" that helps solve a mystery with kindness.',
        f"Tell a gentle story where {child.id} and {parent.noun()} follow a curved path, ask a kind question, and find {mystery.phrase}.",
        f'Write a cozy story about "curve" and "kindness" where a child solves a small mystery before going to sleep.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = f["child"]
    parent: Entity = f["parent"]
    clue: Entity = f["clue"]
    mystery: Entity = f["mystery"]
    return [
        QAItem(
            question=f"Who went to {world.place.label} at bedtime?",
            answer=f"{child.id} and {parent.noun()} went to {world.place.label} together for a quiet bedtime walk.",
        ),
        QAItem(
            question=f"What clue helped {child.id} solve the mystery?",
            answer=f"{clue.label} helped {child.id} follow the curved place toward the answer.",
        ),
        QAItem(
            question=f"How did {child.id} solve the mystery kindly?",
            answer=f"{child.id} asked a gentle question instead of rushing, and that kindness made it easier to find {mystery.phrase}.",
        ),
        QAItem(
            question=f"What was the answer to the mystery?",
            answer=f"The answer was {world.place.answer_kind}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a curve?",
            answer="A curve is a shape that bends instead of going straight, like a bend in a path or river.",
        ),
        QAItem(
            question="Why is kindness helpful when something is confusing?",
            answer="Kindness helps because it makes people feel safe enough to talk, listen, and share clues.",
        ),
        QAItem(
            question="What is a mystery?",
            answer="A mystery is something that is not clear at first, so you need clues to understand it.",
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


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
place(P) :- setting(P).
child_name(N) :- named(N,_).

curved(P) :- curve_kind(P,_).
mystery_ready(P,M) :- place(P), mystery(P,M), clue_style(P,_).
kind_solution(P,M) :- mystery_ready(P,M), answer_kind(P,_).

valid_story(P,C,M) :- place(P), clue(P,C), mystery(P,M), curved(P), kind_solution(P,M).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("setting", pid))
        lines.append(asp.fact("curve_kind", pid, p.curve_kind))
        lines.append(asp.fact("bedtime_hush", pid, p.bedtime_hush))
        lines.append(asp.fact("clue_style", pid, p.clue_style))
        lines.append(asp.fact("mystery_kind", pid, p.mystery_kind))
        lines.append(asp.fact("answer_kind", pid, p.answer_kind))
        for a in sorted(p.affords):
            lines.append(asp.fact("affords", pid, a))
    for clue_id, clue in CLUES.items():
        lines.append(asp.fact("clue", clue_id, clue))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    python_set = {(p.id, clue_id, p.mystery_kind) for p in PLACES.values() for clue_id in CLUES}
    clingo_set = set(asp_valid_stories())
    if python_set == clingo_set:
        print(f"OK: clingo gate matches python reasoning ({len(clingo_set)} stories).")
        return 0
    print("MISMATCH between clingo and python:")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


# ---------------------------------------------------------------------------
# Standard interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A bedtime-story world about curve, kindness, and a mystery to solve.")
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--name")
    ap.add_argument("--child-type", choices=CHILD_TYPES)
    ap.add_argument("--parent", choices=PARENT_TYPES)
    ap.add_argument("--clue", choices=sorted(CLUES))
    ap.add_argument("--mystery")
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
    place = args.place or rng.choice(sorted(PLACES))
    p = PLACES[place]
    child_type = args.child_type or rng.choice(CHILD_TYPES)
    parent = args.parent or rng.choice(PARENT_TYPES)
    clue = args.clue or rng.choice(sorted(CLUES))
    mystery = args.mystery or p.mystery_kind
    name = args.name or rng.choice(CHILD_NAMES)
    return StoryParams(
        place=place,
        child_name=name,
        child_type=child_type,
        parent_type=parent,
        clue=clue,
        mystery=mystery,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(
        PLACES[params.place],
        params.child_name,
        params.child_type,
        params.parent_type,
        params.clue,
        params.mystery,
    )
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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        stories = asp_valid_stories()
        print(f"{len(stories)} compatible stories:\n")
        for row in stories:
            print("  ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for place in sorted(PLACES):
            params = StoryParams(
                place=place,
                child_name=CHILD_NAMES[0],
                child_type="girl",
                parent_type="mother",
                clue=next(iter(sorted(CLUES))),
                mystery=PLACES[place].mystery_kind,
            )
            samples.append(generate(params))
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
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
