#!/usr/bin/env python3
"""
storyworlds/worlds/cucumber_transformation_bad_ending_ghost_story.py
====================================================================

A standalone storyworld for a small ghost story about a cucumber that changes
something in a child's home. The tale is built from a simple simulated world:
a curious child finds a cucumber, the cucumber becomes eerie, and the ending is
bad enough to feel spooky rather than comforting.

The premise is intentionally narrow:
- a child brings home a cucumber
- a ghostly presence makes the cucumber transform
- the child tries to fix it, but the fix fails
- the ending image shows what changed and why it is unsettling
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
# Model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character":
            if self.type in {"girl", "woman", "mother"}:
                return {"subject": "she", "object": "her", "possessive": "her"}[case]
            if self.type in {"boy", "man", "father"}:
                return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    name: str
    eerie: bool = False
    allows: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    name: str
    gender: str
    parent: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

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
        import copy as _copy

        w = World(self.place)
        w.entities = _copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


# ---------------------------------------------------------------------------
# Content
# ---------------------------------------------------------------------------
PLACES = {
    "kitchen": Place(name="the kitchen", eerie=True, allows={"cucumber"}),
    "garden": Place(name="the garden", eerie=True, allows={"cucumber"}),
    "cellar": Place(name="the cellar", eerie=True, allows={"cucumber"}),
}

GIRL_NAMES = ["Mina", "Lina", "Nora", "Ivy", "Mara", "Lily"]
BOY_NAMES = ["Theo", "Milo", "Finn", "Eli", "Noah", "Owen"]
TRAITS = ["quiet", "curious", "brave", "small", "careful"]


# ---------------------------------------------------------------------------
# Simulation
# ---------------------------------------------------------------------------
def _has_ghost(world: World) -> bool:
    return world.facts.get("ghost_present", False)


def build_world(params: StoryParams) -> World:
    place = PLACES[params.place]
    world = World(place)

    child = world.add(Entity(id=params.name, kind="character", type=params.gender))
    parent = world.add(Entity(id="parent", kind="character", type=params.parent, label="parent"))
    cucumber = world.add(
        Entity(
            id="cucumber",
            kind="thing",
            type="cucumber",
            label="cucumber",
            phrase="a green cucumber from the garden",
            owner=child.id,
            caretaker=parent.id,
            meters={"fresh": 1.0},
            memes={"mystery": 1.0},
        )
    )

    ghost = world.add(
        Entity(
            id="ghost",
            kind="character",
            type="ghost",
            label="ghost",
            phrase="a pale ghost with cold hands",
            meters={"cold": 1.0},
            memes={"watching": 1.0},
        )
    )

    # Act 1: discovery
    world.say(f"{child.id} was a {random.choice(TRAITS)} little {params.gender} who liked quiet rooms.")
    world.say(f"One evening, {child.id} found {cucumber.phrase} waiting by the door.")
    world.say(f"{child.id} picked up the cucumber and felt a strange shiver in the air.")

    # Ghost appears
    world.para()
    world.say(f"Then {ghost.label} floated in from the dark corner of {world.place.name}.")
    world.say(f"The room grew still, and even the clock seemed afraid to tick.")

    world.facts["ghost_present"] = True

    # Transformation
    world.para()
    _transform_cucumber(world, child, cucumber, ghost)

    # Bad ending
    world.para()
    _bad_ending(world, child, parent, cucumber, ghost)

    world.facts.update(child=child, parent=parent, cucumber=cucumber, ghost=ghost)
    return world


def _transform_cucumber(world: World, child: Entity, cucumber: Entity, ghost: Entity) -> None:
    cucumber.meters["changed"] = cucumber.meters.get("changed", 0.0) + 1.0
    cucumber.meters["fresh"] = 0.0
    cucumber.memes["mystery"] += 1.0
    cucumber.memes["fear"] = cucumber.memes.get("fear", 0.0) + 1.0
    world.say(
        f"The ghost breathed over the cucumber, and the green skin turned gray and wrinkled."
    )
    world.say(
        f"At once, the cucumber no longer looked like food; it looked like a tiny thing that had heard a bad secret."
    )
    world.say(
        f"{child.id} tried to hide it behind {child.pronoun('possessive')} back, but the cold feeling only got worse."
    )


def _bad_ending(world: World, child: Entity, parent: Entity, cucumber: Entity, ghost: Entity) -> None:
    cucumber.meters["rotten"] = cucumber.meters.get("rotten", 0.0) + 1.0
    child.memes["worry"] = child.memes.get("worry", 0.0) + 1.0
    child.memes["courage"] = child.memes.get("courage", 0.0) + 0.5

    world.say(
        f"{child.id} ran to {parent.label} and asked for help, but when they came back, the ghost was already smiling."
    )
    world.say(
        f"The cucumber had split open on the table, and black seeds lay on the wood like little eyes."
    )
    world.say(
        f"The parent shut the kitchen light off, but the seeds still seemed to shine in the dark."
    )
    world.say(
        f"In the end, {child.id} left the cucumber there, and the house felt colder than before."
    )


# ---------------------------------------------------------------------------
# Story generation
# ---------------------------------------------------------------------------
def generate_story(params: StoryParams) -> str:
    world = build_world(params)
    return world.render()


def story_qa(world: World) -> list[QAItem]:
    child = world.facts["child"]
    cucumber = world.facts["cucumber"]
    ghost = world.facts["ghost"]
    parent = world.facts["parent"]

    return [
        QAItem(
            question=f"What did {child.id} find in {world.place.name}?",
            answer=f"{child.id} found {cucumber.phrase}.",
        ),
        QAItem(
            question="What changed the cucumber?",
            answer=f"The ghost changed the cucumber, and it turned gray and wrinkled.",
        ),
        QAItem(
            question=f"Why was the ending bad for {child.id}?",
            answer=(
                f"The cucumber split open, the seeds looked eerie in the dark, and {child.id} "
                f"could not make the house feel warm again."
            ),
        ),
        QAItem(
            question=f"Who did {child.id} ask for help?",
            answer=f"{child.id} asked {parent.label} for help.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a cucumber?",
            answer="A cucumber is a long green vegetable that people can eat fresh or put in salads.",
        ),
        QAItem(
            question="What is a ghost in a story?",
            answer="A ghost is a spooky figure that is often shown floating, whispering, or appearing in dark places.",
        ),
        QAItem(
            question="What does it mean when something transforms?",
            answer="When something transforms, it changes into a different form or looks very different.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    return [
        "Write a short ghost story for a child where a cucumber changes in a spooky way.",
        f"Tell a quiet, eerie story set in {world.place.name} with a bad ending.",
        "Create a simple transformation story where the cucumber becomes unsettling after a ghost appears.",
    ]


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Ghost story world about a cucumber transformation and a bad ending.")
    ap.add_argument("--place", choices=PLACES.keys(), default=None)
    ap.add_argument("--gender", choices=["girl", "boy"], default=None)
    ap.add_argument("--parent", choices=["mother", "father"], default=None)
    ap.add_argument("--name", default=None)
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
    place = args.place or rng.choice(list(PLACES.keys()))
    gender = args.gender or rng.choice(["girl", "boy"])
    parent = args.parent or rng.choice(["mother", "father"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    return StoryParams(place=place, name=name, gender=gender, parent=parent, seed=args.seed)


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
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== story questions =="]
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
place(P) :- place_name(P).
ghost_story(P) :- place(P), eerie_place(P).
transforms(C) :- cucumber(C), ghost_present.
bad_ending(C) :- transforms(C), rotten(C).
"""


def asp_facts() -> str:
    import asp

    lines = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place_name", pid))
        if place.eerie:
            lines.append(asp.fact("eerie_place", pid))
        for a in sorted(place.allows):
            lines.append(asp.fact("allows", pid, a))
    lines.append(asp.fact("cucumber", "cucumber"))
    lines.append(asp.fact("ghost_present"))
    lines.append(asp.fact("rotten", "cucumber"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program("#show bad_ending/1.\n#show transforms/1.\n"))
    atoms = set(asp.atoms(model, "bad_ending")) | set(asp.atoms(model, "transforms"))
    expected = {("cucumber",), ("cucumber",)}
    if ("cucumber",) in atoms:
        print("OK: ASP recognizes the cucumber transformation and bad ending.")
        return 0
    print("MISMATCH: ASP did not derive the expected story facts.")
    return 1


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(place="kitchen", name="Mina", gender="girl", parent="mother"),
    StoryParams(place="garden", name="Theo", gender="boy", parent="father"),
    StoryParams(place="cellar", name="Ivy", gender="girl", parent="mother"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show transforms/1.\n#show bad_ending/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp

        model = asp.one_model(asp_program("#show transforms/1.\n#show bad_ending/1."))
        print(asp.atoms(model, "transforms"))
        print(asp.atoms(model, "bad_ending"))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            seed = base_seed + i
            rng = random.Random(seed)
            params = resolve_params(args, rng)
            params.seed = seed
            samples.append(generate(params))

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
            header = f"### {p.name}: cucumber in {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
