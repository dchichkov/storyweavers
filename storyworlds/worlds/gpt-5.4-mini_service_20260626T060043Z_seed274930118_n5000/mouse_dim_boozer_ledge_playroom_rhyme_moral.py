#!/usr/bin/env python3
"""
Stand-alone storyworld: a tiny detective tale set in a playroom.

Premise:
- A mouse-dim detective notices a puzzling problem near a ledge in the playroom.
- A boozer character makes a risky mess.
- The detective solves the problem with clues, a rhyme, and a moral choice.

The world is intentionally small and constraint-checked:
- A problem is only interesting if the ledge matters.
- A solution must be causal, not magical.
- The ending should prove what changed in the world state.
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
# Core world model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    location: str = ""
    size: str = ""
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=lambda: {"mess": 0.0, "safety": 0.0, "clue": 0.0, "order": 0.0})
    memes: dict[str, float] = field(default_factory=lambda: {"curiosity": 0.0, "worry": 0.0, "pride": 0.0, "kindness": 0.0})

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"detector", "child", "mouse"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def noun(self) -> str:
        return self.label or self.type


@dataclass
class StoryParams:
    name: str
    boozer_name: str
    seed: Optional[int] = None


@dataclass
class World:
    room: str = "the playroom"
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)

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
        clone = World(room=self.room)
        clone.entities = copy.deepcopy(self.entities)
        clone.facts = copy.deepcopy(self.facts)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
NAMES = ["Milo", "Nina", "Toby", "Pia", "Rory", "Ivy", "Jules", "Nora"]
BOOZER_NAMES = ["Bram", "Buzzy", "Boo", "Boris", "Mottle"]
TRAITS = ["careful", "curious", "brave", "steady"]

# The storyworld's tiny domain vocabulary.
LEDGE_LABEL = "ledge"
MOUSE_DIM = "mouse-dim"
BOOZER_WORD = "boozer"


# ---------------------------------------------------------------------------
# ASP twin / reasonableness gate
# ---------------------------------------------------------------------------
ASP_RULES = r"""
#show valid_story/2.
valid_story(P, B) :- person(P), boozer(B), different(P, B).
different(P, B) :- person(P), boozer(B), P != B.
"""

def asp_facts() -> str:
    import asp
    lines = [asp.fact("room", "playroom"), asp.fact("ledge", "ledge"), asp.fact("size", "mouse_dim")]
    for n in NAMES:
        lines.append(asp.fact("person", n))
    for n in BOOZER_NAMES:
        lines.append(asp.fact("boozer", n))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_pairs() -> list[tuple[str, str]]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = {(p.name, b) for p in valid_pairs() for b in BOOZER_NAMES if p.name != b}
    cl = set(asp_valid_pairs())
    if py == cl:
        print(f"OK: clingo gate matches python gate ({len(cl)} pairs).")
        return 0
    print("MISMATCH:")
    print("only in python:", sorted(py - cl))
    print("only in clingo:", sorted(cl - py))
    return 1


def valid_pairs() -> list[Entity]:
    return [Entity(id=n, type="person", label=n) for n in NAMES]


# ---------------------------------------------------------------------------
# Simulation
# ---------------------------------------------------------------------------
def rhyme_line() -> str:
    return "If the clue is small and the ledge is tall, think twice before you let things fall."


def moral_line() -> str:
    return "The moral was simple: a kind choice can stop a risky mess before it grows."


def setup_world(params: StoryParams) -> World:
    w = World()
    detective = w.add(Entity(
        id=params.name, kind="character", type="mouse", label=params.name,
        phrase=f"a {MOUSE_DIM} detective mouse",
        traits=["small", "clever", "patient"],
        meters={"mess": 0.0, "safety": 1.0, "clue": 0.0, "order": 1.0},
        memes={"curiosity": 1.0, "worry": 0.0, "pride": 0.0, "kindness": 1.0},
    ))
    boozer = w.add(Entity(
        id=params.boozer_name, kind="character", type="booze", label=params.boozer_name,
        phrase=f"the {BOOZER_WORD}",
        traits=["messy", "hasty"],
        meters={"mess": 1.0, "safety": 0.0, "clue": 0.0, "order": 0.0},
        memes={"curiosity": 0.0, "worry": 0.0, "pride": 0.0, "kindness": 0.0},
    ))
    ledge = w.add(Entity(
        id="ledge", kind="thing", type="ledge", label=LEDGE_LABEL,
        phrase="a low ledge beside the toy shelf",
        location="playroom",
        meters={"mess": 0.0, "safety": 0.0, "clue": 0.0, "order": 0.0},
    ))
    w.facts.update(detective=detective, boozer=boozer, ledge=ledge, room="playroom")
    return w


def observe_clue(w: World) -> None:
    d = w.facts["detective"]
    l = w.facts["ledge"]
    d.memes["curiosity"] += 1
    d.meters["clue"] += 1
    l.meters["clue"] += 1
    w.say(f"{d.id} was a {MOUSE_DIM} detective in the playroom, and he noticed a clue near the ledge.")


def establish_problem(w: World) -> None:
    d = w.facts["detective"]
    b = w.facts["boozer"]
    l = w.facts["ledge"]
    b.meters["mess"] += 1
    d.memes["worry"] += 1
    l.meters["order"] -= 1
    w.say(
        f"Then {b.id} splashed a sticky spill too close to the ledge, and {d.id} "
        f"knew the playroom would turn slippery."
    )


def solve_problem(w: World) -> None:
    d = w.facts["detective"]
    b = w.facts["boozer"]
    l = w.facts["ledge"]
    d.meters["order"] += 1
    d.memes["kindness"] += 1
    b.meters["mess"] = max(0.0, b.meters["mess"] - 1.0)
    l.meters["order"] += 2
    w.say(
        f"{d.id} followed the clue, asked {b.id} to slow down, and showed a safer way to tidy the spill."
    )
    w.say(
        f"Together they wiped the floor, moved the toys off the ledge, and made the playroom safe again."
    )
    w.say(rhyme_line())
    w.say(moral_line())


def tell_story(params: StoryParams) -> World:
    w = setup_world(params)
    observe_clue(w)
    w.para()
    establish_problem(w)
    w.para()
    solve_problem(w)
    w.facts["resolved"] = True
    return w


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def story_qa(w: World) -> list[QAItem]:
    d = w.facts["detective"]
    b = w.facts["boozer"]
    l = w.facts["ledge"]
    return [
        QAItem(
            question=f"Who was the mouse-dim detective in the playroom story?",
            answer=f"The {MOUSE_DIM} detective was {d.id}, the little mouse who noticed the clue near the ledge.",
        ),
        QAItem(
            question=f"What problem did {b.id} make near the ledge?",
            answer=f"{b.id} made a sticky spill near the ledge, which could make the playroom slippery.",
        ),
        QAItem(
            question=f"How did {d.id} solve the problem?",
            answer=f"{d.id} followed the clue, asked {b.id} to slow down, and helped clean the spill so the playroom was safe again.",
        ),
    ]


def world_qa(_: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a ledge?",
            answer="A ledge is a narrow shelf-like edge that things can rest on or fall from.",
        ),
        QAItem(
            question="What does it mean to solve a problem?",
            answer="To solve a problem means to find a way to fix what is wrong.",
        ),
        QAItem(
            question="What is a moral value?",
            answer="A moral value is a good way of choosing, like being kind, honest, or careful.",
        ),
        QAItem(
            question="Why can rhymes help in a story?",
            answer="Rhymes can make a story easier to remember and more fun to hear.",
        ),
    ]


def generation_prompts(_: World) -> list[str]:
    return [
        "Write a short detective story set in a playroom about a mouse-dim detective, a boozer, and a ledge.",
        "Tell a child-friendly mystery where a small detective solves a problem with clues, a rhyme, and a moral choice.",
        "Write a simple story in which the playroom becomes safe again after the detective figures out what happened near the ledge.",
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mouse-dim detective storyworld in a playroom.")
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--boozer-name", choices=BOOZER_NAMES)
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
    name = args.name or rng.choice(NAMES)
    boozer_name = args.boozer_name or rng.choice([b for b in BOOZER_NAMES if b != name] or BOOZER_NAMES)
    if name == boozer_name:
        raise StoryError("The detective and the boozer must be different characters.")
    return StoryParams(name=name, boozer_name=boozer_name, seed=args.seed)


def generate(params: StoryParams) -> StorySample:
    w = tell_story(params)
    return StorySample(
        params=params,
        story=w.render(),
        prompts=generation_prompts(w),
        story_qa=story_qa(w),
        world_qa=world_qa(w),
        world=w,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(
            f"  {e.id:12} kind={e.kind:8} type={e.type:7} "
            f"meters={{{', '.join(f'{k}: {v}' for k, v in e.meters.items() if v)}}} "
            f"memes={{{', '.join(f'{k}: {v}' for k, v in e.memes.items() if v)}}}"
        )
    return "\n".join(lines)


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
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        pairs = asp_valid_pairs()
        print(f"{len(pairs)} compatible detective-story pairs:")
        for p, b in pairs:
            print(f"  {p} / {b}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        for i, n in enumerate(NAMES[: min(len(NAMES), args.n)]):
            p = StoryParams(name=n, boozer_name=BOOZER_NAMES[i % len(BOOZER_NAMES)], seed=base_seed + i)
            if p.name == p.boozer_name:
                continue
            samples.append(generate(p))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
            rng = random.Random(base_seed + i)
            i += 1
            params = resolve_params(args, rng)
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
