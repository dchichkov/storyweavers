#!/usr/bin/env python3
"""
storyworlds/worlds/wicket_neighborhood_park_magic_conflict_fable.py
===================================================================

A small fable-style storyworld set in a neighborhood park, where a magic wicket
can stir up conflict before a wiser choice restores peace.

The seed image:
---
In a neighborhood park, a wicket was found that shimmered with magic. Two
friends wanted to use it for their game, but each thought the wicket should be
theirs. Their quarrel grew until a kinder idea showed that magic works best when
shared.
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
# Typed entities with meters and memes.
# ---------------------------------------------------------------------------

@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    held_by: Optional[str] = None
    location: str = ""
    magical: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for key in ("spark", "dust", "noise", "wear"):
            self.meters.setdefault(key, 0.0)
        for key in ("joy", "conflict", "pride", "kindness", "curiosity"):
            self.memes.setdefault(key, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "sister"}
        male = {"boy", "father", "man", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def name_word(self) -> str:
        return self.label or self.id


@dataclass
class StoryParams:
    name_a: str
    type_a: str
    name_b: str
    type_b: str
    helper: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# World state and narration.
# ---------------------------------------------------------------------------

class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.facts: dict[str, object] = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def para(self) -> None:
        if self.lines and self.lines[-1] != "":
            self.lines.append("")

    def render(self) -> str:
        chunks: list[str] = []
        buf: list[str] = []
        for line in self.lines:
            if line == "":
                if buf:
                    chunks.append(" ".join(buf))
                    buf = []
            else:
                buf.append(line)
        if buf:
            chunks.append(" ".join(buf))
        return "\n\n".join(chunks)


# ---------------------------------------------------------------------------
# Registries.
# ---------------------------------------------------------------------------

NAMES = [
    "Milo", "Tess", "June", "Arlo", "Nina", "Ollie", "Pip", "Luna", "Robin", "Bea"
]
KINDS = {
    "child": ["girl", "boy"],
    "animal": ["rabbit", "fox", "crow", "squirrel", "mouse"],
}
HELPERS = ["turtle", "owl", "dog", "cat", "hedgehog"]

LOCATION = "the neighborhood park"

# We keep the domain small and constraint-driven: the wicket is magical, and the
# conflict is about who may use it first.
@dataclass
class Wicket:
    label: str = "wicket"
    phrase: str = "a little wooden wicket that shimmered with magic"
    magical: bool = True
    location: str = LOCATION


# ---------------------------------------------------------------------------
# Reasonableness gate.
# ---------------------------------------------------------------------------

def valid_params(params: StoryParams) -> bool:
    return params.name_a != params.name_b and params.type_a != params.type_b


def explain_invalid(params: StoryParams) -> str:
    return "The story needs two different characters so the wicket can cause a real fable-style conflict."


# ---------------------------------------------------------------------------
# ASP twin.
# ---------------------------------------------------------------------------

ASP_RULES = r"""
#show valid/4.

different(A,B) :- name(A,_), name(B,_), A != B.
valid(A,T1,B,T2) :- name(A,T1), name(B,T2), different(A,B), T1 != T2.
"""

def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for n in NAMES:
        lines.append(asp.fact("name", n, "child"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/4."))
    asp_set = set(asp.atoms(model, "valid"))
    py_set = set()
    for a in NAMES:
        for b in NAMES:
            if a != b:
                py_set.add((a, "child", b, "child"))
    if asp_set == py_set:
        print(f"OK: clingo gate matches python gate ({len(py_set)} pairs).")
        return 0
    print("MISMATCH between clingo and python gate.")
    if asp_set - py_set:
        print("only in asp:", sorted(asp_set - py_set))
    if py_set - asp_set:
        print("only in python:", sorted(py_set - asp_set))
    return 1


# ---------------------------------------------------------------------------
# Story simulation.
# ---------------------------------------------------------------------------

def build_world(params: StoryParams) -> World:
    if not valid_params(params):
        raise StoryError(explain_invalid(params))

    w = World()
    a = w.add(Entity(id=params.name_a, kind="character", type=params.type_a, label=params.name_a))
    b = w.add(Entity(id=params.name_b, kind="character", type=params.type_b, label=params.name_b))
    helper = w.add(Entity(id=params.helper, kind="character", type="animal", label=params.helper))
    wicket = w.add(Entity(
        id="wicket",
        kind="thing",
        type="wicket",
        label="wicket",
        phrase="a little wooden wicket that shimmered with magic",
        magical=True,
        location=LOCATION,
    ))

    w.facts.update(a=a, b=b, helper=helper, wicket=wicket)
    return w


def opening(world: World) -> None:
    a: Entity = world.facts["a"]
    b: Entity = world.facts["b"]
    wicket: Entity = world.facts["wicket"]

    world.say(
        f"In {LOCATION}, {a.name_word} and {b.name_word} found {wicket.phrase} near the path."
    )
    world.say(
        f"It gave off a soft spark, and both of them felt curious at once."
    )
    a.memes["curiosity"] += 1
    b.memes["curiosity"] += 1
    wicket.meters["spark"] += 1


def conflict_turn(world: World) -> None:
    a: Entity = world.facts["a"]
    b: Entity = world.facts["b"]
    wicket: Entity = world.facts["wicket"]

    a.memes["pride"] += 1
    b.memes["pride"] += 1
    a.memes["conflict"] += 1
    b.memes["conflict"] += 1
    wicket.meters["noise"] += 1

    world.say(
        f"{a.name_word} said, \"I saw it first,\" and {b.name_word} said, \"But I know how to use it.\""
    )
    world.say(
        f"The magic wicket began to glow brighter, and their voices grew sharp as the game stopped."
    )


def helper_turn(world: World) -> None:
    a: Entity = world.facts["a"]
    b: Entity = world.facts["b"]
    helper: Entity = world.facts["helper"]
    wicket: Entity = world.facts["wicket"]

    helper.memes["kindness"] += 1
    world.say(
        f"Then {helper.name_word} hopped close and said, \"A wicket is happier when it helps a game, not a quarrel.\""
    )
    world.say(
        f"The little helper pointed to the open grass and suggested they take turns."
    )
    a.memes["conflict"] = max(0.0, a.memes["conflict"] - 1)
    b.memes["conflict"] = max(0.0, b.memes["conflict"] - 1)
    a.memes["joy"] += 1
    b.memes["joy"] += 1
    wicket.meters["spark"] += 1


def resolution(world: World) -> None:
    a: Entity = world.facts["a"]
    b: Entity = world.facts["b"]
    helper: Entity = world.facts["helper"]
    wicket: Entity = world.facts["wicket"]

    wicket.held_by = a.id
    world.say(
        f"{a.name_word} bowled first, then passed the wicket to {b.name_word}, and the game became fair."
    )
    world.say(
        f"After that, the wicket shone like a tiny star, because the magic had found a kind use."
    )
    world.say(
        f"{helper.name_word} watched the two friends laugh together, and the park felt peaceful again."
    )
    world.say("Moral: magic works best when friends share it.")


def simulate(params: StoryParams) -> World:
    world = build_world(params)
    opening(world)
    world.para()
    conflict_turn(world)
    world.para()
    helper_turn(world)
    resolution(world)
    return world


# ---------------------------------------------------------------------------
# Q&A.
# ---------------------------------------------------------------------------

def prompts(world: World) -> list[str]:
    a: Entity = world.facts["a"]
    b: Entity = world.facts["b"]
    return [
        f"Write a short fable for children set in {LOCATION} about {a.name_word}, {b.name_word}, and a magic wicket.",
        f"Tell a gentle story where two characters argue over a wicket and learn to share before the magic fades.",
        f"Write a neighborhood-park fable with a conflict, a kind helper, and a wicket that shines when used fairly.",
    ]


def story_qa(world: World) -> list[QAItem]:
    a: Entity = world.facts["a"]
    b: Entity = world.facts["b"]
    helper: Entity = world.facts["helper"]
    qs = [
        QAItem(
            question=f"Where did {a.name_word} and {b.name_word} find the wicket?",
            answer=f"They found the wicket in {LOCATION}, near the path and the open grass.",
        ),
        QAItem(
            question="Why did the two characters start arguing?",
            answer=f"They both wanted to use the magic wicket first, so pride turned their curiosity into conflict.",
        ),
        QAItem(
            question=f"Who helped them stop quarreling?",
            answer=f"{helper.name_word} helped them by suggesting that they take turns and share the wicket.",
        ),
        QAItem(
            question="What changed by the end of the story?",
            answer="The conflict settled, the game started again, and the wicket shone because it was being shared fairly.",
        ),
    ]
    return qs


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a wicket?",
            answer="A wicket is a small wooden target or gate used in some games, especially cricket, and it can be part of a play setup.",
        ),
        QAItem(
            question="What does magic mean in this story world?",
            answer="Magic means the wicket can sparkle, feel special, and change the mood of the game when people treat it well.",
        ),
        QAItem(
            question="Why is sharing important in the park?",
            answer="Sharing keeps the game fair, lowers conflict, and lets more than one friend enjoy the same toy or game piece.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for p in sample.prompts:
        lines.append(f"- {p}")
    lines.append("")
    lines.append("== Story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        meters = {k: round(v, 3) for k, v in e.meters.items() if v}
        memes = {k: round(v, 3) for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.magical:
            bits.append("magical=True")
        if e.held_by:
            bits.append(f"held_by={e.held_by}")
        if e.location:
            bits.append(f"location={e.location}")
        lines.append(f"  {e.id} ({e.type}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Generation and CLI.
# ---------------------------------------------------------------------------

def generate(params: StoryParams) -> StorySample:
    world = simulate(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fable-style neighborhood-park storyworld with a magic wicket and conflict.")
    ap.add_argument("--name-a", choices=NAMES, help="first character name")
    ap.add_argument("--type-a", choices=["girl", "boy", "rabbit", "fox", "crow", "squirrel", "mouse"], help="first character type")
    ap.add_argument("--name-b", choices=NAMES, help="second character name")
    ap.add_argument("--type-b", choices=["girl", "boy", "rabbit", "fox", "crow", "squirrel", "mouse"], help="second character type")
    ap.add_argument("--helper", choices=HELPERS, help="kind helper")
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
    name_a = args.name_a or rng.choice(NAMES)
    name_b = args.name_b or rng.choice([n for n in NAMES if n != name_a])
    type_a = args.type_a or rng.choice(["girl", "boy", "rabbit", "fox"])
    type_b = args.type_b or rng.choice([t for t in ["girl", "boy", "rabbit", "fox"] if t != type_a])
    helper = args.helper or rng.choice(HELPERS)
    params = StoryParams(name_a=name_a, type_a=type_a, name_b=name_b, type_b=type_b, helper=helper)
    if not valid_params(params):
        raise StoryError(explain_invalid(params))
    return params


CURATED = [
    StoryParams(name_a="Milo", type_a="boy", name_b="Tess", type_b="girl", helper="owl"),
    StoryParams(name_a="Nina", type_a="girl", name_b="Arlo", type_b="boy", helper="turtle"),
    StoryParams(name_a="Robin", type_a="rabbit", name_b="Bea", type_b="girl", helper="hedgehog"),
]


def asp_verify_modes() -> int:
    return asp_verify()


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify_modes())
    if args.asp:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show valid/4."))
        vals = sorted(set(asp.atoms(model, "valid")))
        print(f"{len(vals)} valid pairs:")
        for row in vals:
            print(" ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
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
            header = f"### {p.name_a} and {p.name_b}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
