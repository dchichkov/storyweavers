#!/usr/bin/env python3
"""
storyworlds/worlds/consider_hen_dock_repetition_mystery_to_solve.py
===================================================================

A small whodunit-style story world set on a dock, centered on a curious child,
a hen, repetition, and a mystery to solve.

The seed idea:
- At a dock, a child keeps hearing the same soft cluck, over and over.
- The child considers possible causes, follows repeated clues, and solves the
  mystery with a gentle reveal.
- The hen is part of the answer, and curiosity drives the investigation.

This script follows the Storyworld Contract:
- self-contained stdlib storyworld
- typed entities with meters and memes
- inline ASP twin plus Python reasonableness gate
- story/QA/trace/json/asp/verify/show-asp CLI modes
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"dust": 0.0, "noise": 0.0, "significance": 0.0}
        if not self.memes:
            self.memes = {"curiosity": 0.0, "relief": 0.0, "worry": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "woman"}
        male = {"boy", "man", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Dock:
    name: str = "the dock"
    water: str = "dark water"
    affords: set[str] = field(default_factory=lambda: {"investigate", "feed_hen", "listen"})


@dataclass
class Clue:
    id: str
    kind: str
    text: str
    repeats: int = 1
    source: str = ""


@dataclass
class StoryParams:
    seed: Optional[int] = None
    name: str = "Mina"
    gender: str = "girl"
    guardian: str = "grandmother"


class World:
    def __init__(self, dock: Dock) -> None:
        self.dock = dock
        self.entities: dict[str, Entity] = {}
        self.clues: list[Clue] = []
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

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
        clone = World(self.dock)
        clone.entities = {k: Entity(**{
            "id": v.id, "kind": v.kind, "type": v.type, "label": v.label,
            "phrase": v.phrase, "owner": v.owner, "caretaker": v.caretaker,
            "plural": v.plural, "meters": dict(v.meters), "memes": dict(v.memes)
        }) for k, v in self.entities.items()}
        clone.clues = [Clue(**c.__dict__) for c in self.clues]
        clone.fired = set(self.fired)
        return clone


THRESHOLD = 1.0


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
DOCKS = {
    "dock": Dock(),
}

CLUES = {
    "repeated_cluck": Clue(
        id="repeated_cluck",
        kind="sound",
        text="a tiny cluck coming from under the planks",
        repeats=3,
        source="hen",
    ),
    "single_feather": Clue(
        id="single_feather",
        kind="object",
        text="one white feather stuck near a crate",
        repeats=1,
        source="hen",
    ),
    "scratch_marks": Clue(
        id="scratch_marks",
        kind="mark",
        text="small scratch marks by a feed pail",
        repeats=2,
        source="hen",
    ),
}

GENDERS = {"girl", "boy"}
GIRL_NAMES = ["Mina", "Nina", "Lila", "Aria", "Tess", "Maya"]
BOY_NAMES = ["Owen", "Finn", "Eli", "Noah", "Ben", "Theo"]


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------
def _repeated_clue(world: World, clue: Clue) -> bool:
    return clue.repeats >= 2


def _reasonableness_gate(world: World, params: StoryParams) -> None:
    if world.dock.name != "the dock":
        raise StoryError("This world is built for a dock setting.")
    if params.gender not in GENDERS:
        raise StoryError("Unsupported gender choice.")
    if not any(c.kind == "sound" and c.repeats >= 2 for c in world.clues):
        raise StoryError("The story needs a repeated clue so curiosity has something to follow.")


def investigate(world: World, child: Entity, guardian: Entity, hen: Entity) -> None:
    child.memes["curiosity"] += 1
    world.say(
        f"{child.id} stood on the dock and listened carefully. "
        f"Something was repeating in the air, and {child.pronoun('possessive')} curiosity grew."
    )
    world.say(
        f"{child.id} asked {guardian.id} to consider every sound, even the odd little cluck "
        f"that seemed to come again and again."
    )


def repeat_clue(world: World, child: Entity, clue: Clue) -> None:
    world.say(
        f"Again and again, {clue.text} reached {child.id}'s ears."
    )
    child.meters["noise"] += 1
    child.memes["curiosity"] += 1
    world.facts["repetition"] = clue.repeats


def follow_tracks(world: World, child: Entity, hen: Entity) -> None:
    world.say(
        f"{child.id} followed the clues past a crate, then past a feed pail, then back to the same spot. "
        f"The pattern felt like a riddle."
    )
    child.memes["curiosity"] += 1
    world.facts["pattern"] = "dock loop"


def solve_mystery(world: World, child: Entity, guardian: Entity, hen: Entity) -> None:
    hen.meters["significance"] += 1
    child.memes["relief"] += 1
    world.say(
        f"At last, {child.id} found the answer: the hen had been pecking at crumbs under the planks, "
        f"and the little cluck was her way of asking for more."
    )
    world.say(
        f"{guardian.id} laughed softly. It was not a spooky secret at all, just a hungry hen on the dock."
    )
    world.say(
        f"{child.id} offered a careful handful of seed, and the hen settled down beside the water."
    )
    world.facts["solved"] = True
    world.facts["reveal"] = "hungry hen"


def tell(params: StoryParams) -> World:
    world = World(DOCKS["dock"])
    child = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.gender,
        label=params.name,
        meters={"dust": 0.0, "noise": 0.0, "significance": 0.0},
        memes={"curiosity": 0.0, "relief": 0.0, "worry": 0.0},
    ))
    guardian = world.add(Entity(
        id=params.guardian.capitalize(),
        kind="character",
        type="woman" if params.guardian == "grandmother" else "man",
        label=params.guardian,
        meters={"dust": 0.0, "noise": 0.0, "significance": 0.0},
        memes={"curiosity": 0.0, "relief": 0.0, "worry": 0.0},
    ))
    hen = world.add(Entity(
        id="Hen",
        kind="character",
        type="hen",
        label="hen",
        phrase="a small spotted hen",
        meters={"dust": 0.0, "noise": 0.0, "significance": 0.0},
        memes={"curiosity": 0.0, "relief": 0.0, "worry": 0.0},
    ))

    world.clues = [CLUES["repeated_cluck"], CLUES["single_feather"], CLUES["scratch_marks"]]

    world.say(
        f"One morning at the dock, {child.id} noticed something strange."
    )
    world.say(
        f"A {hen.label} was nearby, and the same tiny clue seemed to happen more than once."
    )
    world.para()

    investigate(world, child, guardian, hen)
    repeat_clue(world, child, CLUES["repeated_cluck"])
    repeat_clue(world, child, CLUES["scratch_marks"])
    follow_tracks(world, child, hen)
    world.para()
    solve_mystery(world, child, guardian, hen)

    world.facts.update(
        child=child,
        guardian=guardian,
        hen=hen,
        dock=world.dock,
        params=params,
    )

    _reasonableness_gate(world, params)
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    child: Entity = world.facts["child"]  # type: ignore[assignment]
    return [
        'Write a short whodunit story for a young child set on a dock, where a repeated clue leads to a mystery being solved.',
        f"Tell a gentle mystery about {child.id}, a hen, and a clue that happens more than once.",
        "Write a dockside story with curiosity, repetition, and a friendly reveal at the end.",
    ]


def story_qa(world: World) -> list[QAItem]:
    child: Entity = world.facts["child"]  # type: ignore[assignment]
    guardian: Entity = world.facts["guardian"]  # type: ignore[assignment]
    hen: Entity = world.facts["hen"]  # type: ignore[assignment]
    rep = world.facts.get("repetition", 0)
    return [
        QAItem(
            question=f"Why did {child.id} keep listening so carefully on the dock?",
            answer=f"{child.id} heard a clue repeat more than once, so curiosity made {child.pronoun('object')} pay close attention.",
        ),
        QAItem(
            question=f"What mystery did {child.id} solve with {guardian.id}?",
            answer=f"{child.id} solved the mystery of the repeated cluck. The answer was a hungry hen pecking for crumbs under the planks.",
        ),
        QAItem(
            question=f"How many times did the most important clue repeat?",
            answer=f"It repeated {rep} times, which was enough to turn the sound into a real mystery to solve.",
        ),
        QAItem(
            question=f"What did {child.id} do at the end to help the hen?",
            answer=f"{child.id} offered seed to the hen, and the hen settled down beside the water on the dock.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a dock?",
            answer="A dock is a platform by the water where boats can stop and people can stand, walk, or work.",
        ),
        QAItem(
            question="What is curiosity?",
            answer="Curiosity is the feeling that makes someone want to look, listen, and learn more about something puzzling.",
        ),
        QAItem(
            question="What does repetition mean?",
            answer="Repetition means something happens or is said again and again.",
        ),
        QAItem(
            question="What is a hen?",
            answer="A hen is a female chicken. Hens cluck, peck at food, and can lay eggs.",
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
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(
            f"  {e.id:10} kind={e.kind:10} type={e.type:8} meters={e.meters} memes={e.memes}"
        )
    lines.append(f"  clues={[(c.id, c.kind, c.repeats) for c in world.clues]}")
    lines.append(f"  facts={{{', '.join(sorted(world.facts.keys()))}}}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% Repetition and curiosity are the key story mechanics.
repeated(C) :- clue(C), repeats(C,N), N >= 2.
mystery_to_solve(D) :- dock(D), repeated(_).
curious_child(P) :- person(P), curiosity(P), C > 0, curiosity_value(P,C).
solved :- clue(hard), repeated(_), hen_present, dock(_).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    lines.append(asp.fact("dock", "dock"))
    for cid, clue in CLUES.items():
        lines.append(asp.fact("clue", cid))
        lines.append(asp.fact("kind", cid, clue.kind))
        lines.append(asp.fact("repeats", cid, clue.repeats))
        lines.append(asp.fact("source", cid, clue.source))
    lines.append(asp.fact("person", "child"))
    lines.append(asp.fact("person", "guardian"))
    lines.append(asp.fact("hen_present"))
    lines.append(asp.fact("curiosity"))
    lines.append(asp.fact("curiosity_value", "child", 1))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    program = asp_program("#show repeated/1. #show mystery_to_solve/1.")
    model = asp.one_model(program)
    repeated = sorted(set(asp.atoms(model, "repeated")))
    mystery = sorted(set(asp.atoms(model, "mystery_to_solve")))
    py_repeated = [cid for cid, clue in CLUES.items() if clue.repeats >= 2]
    py_mystery = ["dock"] if py_repeated else []
    if repeated == [(cid,) for cid in py_repeated] and mystery == [(m,) for m in py_mystery]:
        print(f"OK: ASP parity matches Python reasonableness gate ({len(repeated)} repeated clues).")
        return 0
    print("MISMATCH between ASP and Python:")
    print("  ASP repeated:", repeated)
    print("  PY repeated:", py_repeated)
    print("  ASP mystery:", mystery)
    print("  PY mystery:", py_mystery)
    return 1


# ---------------------------------------------------------------------------
# Storyworld API
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A dockside whodunit about repetition, curiosity, and a hen.")
    ap.add_argument("--name", choices=sorted(GIRL_NAMES + BOY_NAMES))
    ap.add_argument("--gender", choices=sorted(GENDERS))
    ap.add_argument("--guardian", choices=["grandmother", "grandfather"])
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
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    guardian = args.guardian or rng.choice(["grandmother", "grandfather"])
    return StoryParams(seed=None, name=name, gender=gender, guardian=guardian)


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


CURATED = [
    StoryParams(name="Mina", gender="girl", guardian="grandmother"),
    StoryParams(name="Owen", gender="boy", guardian="grandfather"),
    StoryParams(name="Tess", gender="girl", guardian="grandmother"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show repeated/1. #show mystery_to_solve/1."))
        return
    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show repeated/1. #show mystery_to_solve/1."))
        print("repeated clues:", sorted(set(asp.atoms(model, "repeated"))))
        print("mysteries:", sorted(set(asp.atoms(model, "mystery_to_solve"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            i += 1
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
            header = f"### {p.name}: dock mystery"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
