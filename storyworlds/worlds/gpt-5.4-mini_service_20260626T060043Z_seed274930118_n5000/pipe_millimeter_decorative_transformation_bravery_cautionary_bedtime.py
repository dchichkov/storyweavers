#!/usr/bin/env python3
"""
A small bedtime-story world about a tiny decorative pipe, a careful measurement in
millimeters, a brave transformation, and a cautionary lesson about trying things
without checking first.
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
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
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


@dataclass
class StoryParams:
    place: str
    name: str
    gender: str
    helper: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: str) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.facts: dict[str, object] = {}
        self.fired: set[str] = set()

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
# Registries
# ---------------------------------------------------------------------------

PLACES = {
    "workbench": "the little workbench by the window",
    "attic": "the quiet attic room",
    "bedroom": "the bedtime bedroom",
}

NAMES_GIRL = ["Mina", "Lila", "Nora", "Maya", "Ivy"]
NAMES_BOY = ["Theo", "Eli", "Finn", "Noah", "Pip"]
HELPERS = ["grandmother", "father", "big sister", "mother"]

# The small domain is about a decorative pipe model.
@dataclass
class Pipe:
    label: str = "pipe"
    phrase: str = "a tiny decorative pipe"
    length_mm: int = 48
    target_mm: int = 50
    decorative: bool = True


PIPE = Pipe()

# Emotional/physical thresholds.
BRAVERY_THRESHOLD = 1.0
CAUTION_THRESHOLD = 1.0
TRANSFORM_THRESHOLD = 1.0


# ---------------------------------------------------------------------------
# Narrative helpers
# ---------------------------------------------------------------------------

def intro(world: World, child: Entity, helper: Entity, pipe: Entity) -> None:
    world.say(
        f"At bedtime, {child.id} found {pipe.phrase} sitting on the shelf near "
        f"the lamp, and {child.pronoun('possessive')} {helper.type} smiled softly."
    )
    world.say(
        f"{child.id} loved how {pipe.label} looked so decorative, with a shiny curve "
        f"that caught the moonlight."
    )


def caution(world: World, child: Entity, pipe: Entity) -> None:
    child.memes["curiosity"] = child.memes.get("curiosity", 0.0) + 1.0
    child.memes["caution"] = child.memes.get("caution", 0.0) + 1.0
    world.say(
        f"{child.id} wanted to move it right away, but {child.pronoun('subject')} "
        f"remembered that a careful bedtime voice should check the size first."
    )
    world.say(
        f"The old note said, 'Measure twice before you touch something small.'"
    )


def measure(world: World, child: Entity, pipe: Entity) -> None:
    length = pipe.meters.get("length_mm", 0.0)
    target = pipe.meters.get("target_mm", 0.0)
    diff = abs(target - length)
    world.facts["millimeter_gap"] = diff
    world.say(
        f"{child.id} held a tiny ruler beside it and saw the pipe was {int(length)} "
        f"millimeters long, just {int(diff)} millimeters shy of the mark."
    )


def bravery(world: World, child: Entity, helper: Entity, pipe: Entity) -> None:
    child.memes["bravery"] = child.memes.get("bravery", 0.0) + 1.0
    world.say(
        f"{child.id} took a deep breath and was brave enough to try a gentle change, "
        f"with {helper.pronoun('subject')} watching kindly."
    )


def transform(world: World, child: Entity, pipe: Entity) -> None:
    if "transformed" in world.fired:
        return
    world.fired.add("transformed")
    old = pipe.phrase
    pipe.phrase = "a neatly fitted decorative pipe"
    pipe.meters["length_mm"] = pipe.meters.get("target_mm", 50.0)
    pipe.memes["pride"] = pipe.memes.get("pride", 0.0) + 1.0
    world.facts["transformed"] = True
    world.say(
        f"With patient hands, {child.id} adjusted the piece until the curve lined up "
        f"just right, and the {old} became {pipe.phrase}."
    )


def ending(world: World, child: Entity, helper: Entity, pipe: Entity) -> None:
    world.say(
        f"Then the room looked calm again. {child.id} yawned, and the little decorative "
        f"pipe rested safely on the shelf, ready for morning."
    )
    world.say(
        f"{helper.id} tucked the blanket higher and said, 'Brave hands are good, but "
        f"careful hands are better.'"
    )


def tell_story(params: StoryParams) -> World:
    if params.place not in PLACES:
        raise StoryError("Unknown bedtime place.")
    if params.gender not in {"girl", "boy"}:
        raise StoryError("Gender must be girl or boy.")

    world = World(params.place)

    child = world.add(
        Entity(
            id=params.name,
            kind="character",
            type=params.gender,
            memes={"curiosity": 0.0, "caution": 0.0, "bravery": 0.0},
        )
    )
    helper = world.add(
        Entity(
            id=params.helper,
            kind="character",
            type=params.helper,
            memes={"kindness": 1.0},
        )
    )
    pipe = world.add(
        Entity(
            id="pipe",
            kind="thing",
            type="pipe",
            label="pipe",
            phrase=PIPE.phrase,
            owner=None,
            meters={"length_mm": float(PIPE.length_mm), "target_mm": float(PIPE.target_mm)},
            memes={"decorative": 1.0},
        )
    )

    world.say(f"That night in {PLACES[params.place]}, everything felt quiet and warm.")
    intro(world, child, helper, pipe)
    caution(world, child, pipe)
    measure(world, child, pipe)
    bravery(world, child, helper, pipe)

    if abs(pipe.meters["length_mm"] - pipe.meters["target_mm"]) > 0:
        transform(world, child, pipe)

    world.facts.update(
        child=child,
        helper=helper,
        pipe=pipe,
        place=params.place,
        child_name=params.name,
        helper_name=params.helper,
    )
    ending(world, child, helper, pipe)
    return world


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
#show valid/2.
place(workbench).
place(attic).
place(bedroom).

child(girl).
child(boy).

valid(P, G) :- place(P), child(G).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for g in ["girl", "boy"]:
        lines.append(asp.fact("child", g))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def valid_combos() -> list[tuple[str, str]]:
    return sorted((p, g) for p in PLACES for g in ["girl", "boy"])


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python.")
    if py - cl:
        print("only in python:", sorted(py - cl))
    if cl - py:
        print("only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a bedtime story about a child and a decorative pipe, with a careful measurement in millimeters.',
        f"Tell a gentle story where {f['child_name']} notices a tiny pipe at {PLACES[f['place']]} and becomes brave enough to help.",
        "Write a short bedtime tale that includes bravery, caution, and a small transformation.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = f["child"]  # type: ignore[assignment]
    helper: Entity = f["helper"]  # type: ignore[assignment]
    pipe: Entity = f["pipe"]  # type: ignore[assignment]
    gap = int(world.facts["millimeter_gap"])
    return [
        QAItem(
            question=f"What did {child.id} find at {PLACES[f['place']]}, and what was special about it?",
            answer=f"{child.id} found {pipe.phrase}, and it was decorative and tiny enough to need careful measuring.",
        ),
        QAItem(
            question=f"How many millimeters short was the pipe before the change?",
            answer=f"It was {gap} millimeters short before {child.id} fixed it.",
        ),
        QAItem(
            question=f"Who watched kindly while {child.id} worked?",
            answer=f"{helper.id} watched kindly and helped {child.id} stay calm and careful.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"The pipe transformed from a tiny decorative piece into {pipe.phrase}, fitting the mark just right.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a millimeter?",
            answer="A millimeter is a very tiny unit of length, smaller than a centimeter.",
        ),
        QAItem(
            question="What does decorative mean?",
            answer="Decorative means something is made to look pretty or special, even if it is not used for work.",
        ),
        QAItem(
            question="What is bravery?",
            answer="Bravery is when someone does something careful and hard even though they feel a little scared.",
        ),
        QAItem(
            question="Why is caution important?",
            answer="Caution helps people slow down, check details, and avoid mistakes or accidents.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== Prompts =="]
    for p in sample.prompts:
        out.append(f"- {p}")
    out.append("")
    out.append("== Story QA ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== World QA ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Storyworld interface
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime story world about a decorative pipe.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=HELPERS)
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
    place = args.place or rng.choice(list(PLACES))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES_GIRL if gender == "girl" else NAMES_BOY)
    helper = args.helper or rng.choice(HELPERS)
    return StoryParams(place=place, name=name, gender=gender, helper=helper)


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
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


CURATED = [
    StoryParams(place="bedroom", name="Mina", gender="girl", helper="mother"),
    StoryParams(place="workbench", name="Theo", gender="boy", helper="father"),
    StoryParams(place="attic", name="Nora", gender="girl", helper="grandmother"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid()
        print(f"{len(combos)} valid combos")
        for p, g in combos:
            print(p, g)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
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
