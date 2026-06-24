#!/usr/bin/env python3
"""
storyworlds/worlds/factory_bazooka_surprise_curiosity_conflict_folk_tale.py
===========================================================================

A standalone folk-tale storyworld about a curious child in a tiny factory who
finds a bazooka-shaped surprise, stirs a conflict, and resolves it with a safer
use of the machine.

Premise seed:
- factory
- bazooka
- Surprise
- Curiosity
- Conflict
- Folk Tale style

The world is intentionally small and child-facing: a worker-child, a caretaker,
a factory with one loud machine, and one oversized "bazooka" prop that is not
for harm. The social turn comes from curiosity meeting a warning; the resolution
comes from changing the plan, not from frozen moralizing.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field, replace
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    plural: bool = False

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def obj(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return self.label or self.id


# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    village: str
    worker: str
    worker_gender: str
    caretaker: str
    caretaker_gender: str
    machine: str
    prop: str
    tone: str = "folk"
    seed: Optional[int] = None


CURATED: list[StoryParams] = [
    StoryParams(
        village="mill village",
        worker="Mina",
        worker_gender="girl",
        caretaker="Grandma Ruth",
        caretaker_gender="woman",
        machine="bellows",
        prop="bazooka",
        tone="folk",
    ),
    StoryParams(
        village="river village",
        worker="Bram",
        worker_gender="boy",
        caretaker="Uncle Jory",
        caretaker_gender="man",
        machine="loom",
        prop="bazooka",
        tone="folk",
    ),
]


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------
class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {
            "conflict": False,
            "resolved": False,
            "surprise": False,
            "curiosity": False,
        }
        self.lines: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def render(self) -> str:
        return " ".join(self.lines)


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str]]:
    return [
        ("factory", "bazooka"),
    ]


def combo_is_valid(params: StoryParams) -> bool:
    return (params.village == "mill village" or params.village == "river village") and params.prop == "bazooka"


# ---------------------------------------------------------------------------
# Inline ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
place(factory).
prop(bazooka).

valid(factory,bazooka).
"""


def asp_facts() -> str:
    import asp

    return "\n".join(
        [
            asp.fact("place", "factory"),
            asp.fact("prop", "bazooka"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


# ---------------------------------------------------------------------------
# Story building
# ---------------------------------------------------------------------------
def build_world(params: StoryParams) -> World:
    if not combo_is_valid(params):
        raise StoryError("This tiny folk tale only grows in the factory with the bazooka surprise.")

    world = World()
    worker = world.add(
        Entity(
            id=params.worker,
            kind="character",
            type=params.worker_gender,
            label=params.worker,
            attrs={"role": "worker"},
            meters={"duty": 1.0},
            memes={"curiosity": 2.0, "joy": 1.0},
        )
    )
    caretaker = world.add(
        Entity(
            id=params.caretaker,
            kind="character",
            type=params.caretaker_gender,
            label=params.caretaker,
            attrs={"role": "caretaker"},
            meters={"duty": 1.0},
            memes={"care": 2.0, "calm": 1.0},
        )
    )
    factory = world.add(
        Entity(
            id="factory",
            kind="place",
            type="factory",
            label="the little factory",
            tags={"factory"},
            meters={"hum": 3.0},
        )
    )
    machine = world.add(
        Entity(
            id="machine",
            kind="thing",
            type="machine",
            label="the old machine",
            tags={params.machine},
            meters={"noise": 1.0},
        )
    )
    prop = world.add(
        Entity(
            id="prop",
            kind="thing",
            type="prop",
            label="the bazooka surprise",
            tags={"bazooka", "surprise"},
            meters={"weight": 2.0},
            memes={"surprise": 2.0},
        )
    )

    world.facts.update(
        worker=worker,
        caretaker=caretaker,
        factory=factory,
        machine=machine,
        prop=prop,
        village=params.village,
        machine_name=params.machine,
        prop_name=params.prop,
    )

    # Setup
    world.say(
        f"In the {params.village}, there stood a little factory where {worker.id} "
        f"liked to listen to the warm hum of the machines."
    )
    world.say(
        f"One morning, {worker.id} found a strange surprise near the worktable: a "
        f"great bazooka-shaped toy wrapped in blue cloth."
    )
    world.say(
        f"{worker.id} did not know what it was for, and that only made {worker.pronoun('possessive')} "
        f"curiosity grow brighter."
    )
    world.facts["curiosity"] = True
    worker.memes["curiosity"] += 2.0
    prop.memes["surprise"] += 1.0

    # Turn
    world.say(
        f"{worker.id} wanted to lift it, tap it, and make it speak its secret, but "
        f"{caretaker.id} raised a hand and said, 'Easy now. Some surprises are loud, "
        f"and some loud things do not belong in small hands.'"
    )
    world.facts["conflict"] = True
    worker.memes["conflict"] = 2.0
    caretaker.memes["conflict"] = 1.0

    world.say(
        f"{worker.id} frowned. {worker.pronoun().capitalize()} was curious, and a little "
        f"stubborn too. For a moment, the whole factory felt like a tug-of-war."
    )

    # Resolution
    world.say(
        f"Then {caretaker.id} laughed softly and showed {worker.id} a better use for the toy: "
        f"they could roll it to the packing room and use its long tube to carry bright ribbons "
        f"from one basket to another."
    )
    world.facts["resolved"] = True
    worker.memes["conflict"] = 0.0
    worker.memes["joy"] += 2.0
    caretaker.memes["care"] += 1.0

    world.say(
        f"So {worker.id} and {caretaker.id} carried the bazooka surprise together, and the old "
        f"factory filled with cheerful clacks instead of a quarrel."
    )
    world.say(
        f"By evening, the ribbons were stacked neat and fair, and the bazooka surprise rested "
        f"by the window like a strange treasure that had found its proper home."
    )

    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    worker: Entity = f["worker"]  # type: ignore[assignment]
    caretaker: Entity = f["caretaker"]  # type: ignore[assignment]
    return [
        f"Write a folk-tale story for a small child about {worker.id} in a factory, a bazooka-shaped surprise, and a kind grown-up who solves a problem gently.",
        f"Tell a child-friendly story where {worker.id}'s curiosity causes conflict in the factory, but {caretaker.id} turns the surprise into a safe helper.",
        f"Write a simple folk tale with a factory, a bazooka, curiosity, surprise, conflict, and a happy ending image.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    worker: Entity = f["worker"]  # type: ignore[assignment]
    caretaker: Entity = f["caretaker"]  # type: ignore[assignment]
    village = f["village"]
    return [
        QAItem(
            question=f"Where did {worker.id} find the strange surprise?",
            answer=f"{worker.id} found it in the little factory in the {village}. It was wrapped in blue cloth near the worktable.",
        ),
        QAItem(
            question=f"Why did {worker.id} and {caretaker.id} have a conflict?",
            answer=f"They had a conflict because {worker.id} was very curious about the bazooka surprise, while {caretaker.id} wanted to keep things calm and safe.",
        ),
        QAItem(
            question=f"How was the conflict solved?",
            answer=f"{caretaker.id} showed {worker.id} a safe use for the bazooka surprise, and together they used it to carry ribbons instead of making trouble.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"At the end, the factory was peaceful again, the ribbons were packed neatly, and the bazooka surprise had found a proper home by the window.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a factory?",
            answer="A factory is a place where people make or pack things, often with machines that hum and clack.",
        ),
        QAItem(
            question="What is curiosity?",
            answer="Curiosity is the feeling that makes you want to look, ask, and learn about something new.",
        ),
        QAItem(
            question="What is a surprise?",
            answer="A surprise is something unexpected that makes people pause and look twice.",
        ),
        QAItem(
            question="What is conflict?",
            answer="Conflict is when two wishes pull against each other and people need a gentler plan.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    parts = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        parts.append(f"{i}. {p}")
    parts.append("")
    parts.append("== story qa ==")
    for item in sample.story_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    parts.append("")
    parts.append("== world qa ==")
    for item in sample.world_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    return "\n".join(parts)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for ent in world.entities.values():
        lines.append(f"{ent.id}: meters={ent.meters} memes={ent.memes} attrs={ent.attrs}")
    lines.append(f"facts={world.facts}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------
def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.prop and args.prop != "bazooka":
        raise StoryError("This world only supports the bazooka surprise.")
    village = args.village or rng.choice(["mill village", "river village"])
    worker = args.worker or rng.choice(["Mina", "Bram", "Ivo", "Tessa"])
    worker_gender = args.worker_gender or ("girl" if worker in {"Mina", "Tessa"} else "boy")
    caretaker = args.caretaker or rng.choice(["Grandma Ruth", "Uncle Jory", "Aunt Nella"])
    caretaker_gender = args.caretaker_gender or ("woman" if caretaker.startswith("Grandma") or caretaker.startswith("Aunt") else "man")
    machine = args.machine or rng.choice(["bellows", "loom", "press"])
    prop = args.prop or "bazooka"
    return StoryParams(
        village=village,
        worker=worker,
        worker_gender=worker_gender,
        caretaker=caretaker,
        caretaker_gender=caretaker_gender,
        machine=machine,
        prop=prop,
    )


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
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


# ---------------------------------------------------------------------------
# ASP
# ---------------------------------------------------------------------------
def asp_verify() -> int:
    import asp

    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py != cl:
        print("ASP mismatch")
        print("python:", sorted(py))
        print("clingo:", sorted(cl))
        return 1
    print(f"OK: ASP matches Python for {len(py)} combo(s).")
    return 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Folk tale storyworld: factory, bazooka, surprise, curiosity, conflict.")
    ap.add_argument("--village")
    ap.add_argument("--worker")
    ap.add_argument("--worker-gender", dest="worker_gender")
    ap.add_argument("--caretaker")
    ap.add_argument("--caretaker-gender", dest="caretaker_gender")
    ap.add_argument("--machine")
    ap.add_argument("--prop")
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        # smoke test normal generation
        sample = generate(resolve_params(argparse.Namespace(
            village=None, worker=None, worker_gender=None, caretaker=None,
            caretaker_gender=None, machine=None, prop=None
        ), random.Random(7)))
        if not sample.story:
            raise SystemExit(1)
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("#show valid/2."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        for i in range(max(args.n, 1)):
            params = resolve_params(args, random.Random(base_seed + i))
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
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {i + 1}" if len(samples) > 1 else "")
        if i + 1 < len(samples):
            print("\n" + "=" * 72 + "\n")


if __name__ == "__main__":
    main()
