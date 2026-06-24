#!/usr/bin/env python3
"""
Storyworld: a small whodunit with conflict, curiosity, and rhyme.

Premise:
A tiny animal group at a school recital notices a missing silver bell.
The children follow clues, argue a little, and use a rhyme to solve the case.
The story stays small: one setting, one missing object, one reveal, one repair.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field, asdict
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

SMALL_LIMIT = 3
ASP_RULES = r"""
small_case(case1).
feature(conflict).
feature(curiosity).
feature(rhyme).
solve(case1) :- small_case(case1), feature(conflict), feature(curiosity), feature(rhyme).
#show solve/1.
"""

NAMES = ["Mina", "Toby", "Pip", "Rosa", "Ned", "Ivy", "Jules", "Bea"]
SETTINGS = [
    ("music room", "the music room", "the stage"),
    ("library nook", "the library nook", "the reading rug"),
    ("garden shed", "the little shed", "the workbench"),
]
MISSING = [
    ("silver bell", "bell", "a silver bell"),
    ("tiny key", "key", "a tiny key"),
    ("red ribbon", "ribbon", "a red ribbon"),
]
RHYMES = [
    ("If it rings, it jingles; if it hides, it tingles.", "The rhyme meant the clue was near the thing itself."),
    ("Near the chair, under there, look with careful care.", "The rhyme pointed to a hiding spot close by."),
    ("When you hear a little chime, check the place that rhymes.", "The rhyme told them to search matching-sound places."),
]

@dataclass
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

@dataclass
class StoryParams:
    setting: str
    missing: str
    clue: str
    rhyme: str
    solver: str
    skeptic: str
    seed: Optional[int] = None

class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.facts: dict[str, object] = {}
        self.world = self  # keep trace-friendly

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def say(self, text: str) -> None:
        self.lines.append(text)

    def render(self) -> str:
        return " ".join(self.lines)

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small whodunit story world with conflict, curiosity, and rhyme.")
    ap.add_argument("--setting", choices=[s[0] for s in SETTINGS])
    ap.add_argument("--missing", choices=[m[0] for m in MISSING])
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap

def asp_facts() -> str:
    import storyworlds.asp as asp
    return "\n".join([
        asp.fact("small", "case1"),
        asp.fact("feature", "conflict"),
        asp.fact("feature", "curiosity"),
        asp.fact("feature", "rhyme"),
    ])

def asp_program(extra: str = "", show: str = "#show solve/1.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"

def asp_solve() -> list[str]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program())
    return [str(x) for x in asp.atoms(model, "solve")]

def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting = args.setting or rng.choice([s[0] for s in SETTINGS])
    missing = args.missing or rng.choice([m[0] for m in MISSING])
    if setting not in [s[0] for s in SETTINGS]:
        raise StoryError("Unknown setting.")
    if missing not in [m[0] for m in MISSING]:
        raise StoryError("Unknown missing object.")
    if SMALL_LIMIT < 1:
        raise StoryError("Story must stay small.")
    clue, rhyme = rng.choice(RHYMES)
    names = rng.sample(NAMES, 2)
    return StoryParams(setting=setting, missing=missing, clue=clue, rhyme=rhyme, solver=names[0], skeptic=names[1])

def generate(params: StoryParams) -> StorySample:
    world = World()
    place = next(x for x in SETTINGS if x[0] == params.setting)
    miss = next(x for x in MISSING if x[0] == params.missing)
    solver = world.add(Entity(params.solver, "character"))
    skeptic = world.add(Entity(params.skeptic, "character"))
    item = world.add(Entity("missing", "thing", miss[1]))
    solver.memes["curiosity"] = 2
    skeptic.memes["conflict"] = 1
    world.facts.update(params=asdict(params), setting=place, missing=miss, clue=params.clue, rhyme=params.rhyme)

    world.say(f"It was a small evening in the {place[0]}.")
    world.say(f"{solver.id} noticed that the {miss[2]} was gone from the {place[2]}.")
    world.say(f'"That is odd," {solver.id} said. "{params.clue}"')
    world.say(f'{skeptic.id} frowned. "Don’t poke around," {skeptic.id} warned, and the room grew tense.')
    world.say(f"But {solver.id} stayed curious and followed a soft rhyme: "{params.rhyme}".')
    world.say(f"Under the {place[2].split()[-1]}, they found the {miss[2]} tucked neatly in a cup.")
    world.say(f"No thief had done it; a breeze had nudged it away.")
    world.say(f"{skeptic.id} laughed, the worry faded, and the small mystery was solved.")
    world.say(f"To make peace, {solver.id} put the {miss[2]} back where it belonged.")
    world.say(f"The little room felt calm again, with only the rhyme left in the air.")

    world.facts["outcome"] = "solved"
    world.facts["item"] = item
    return StorySample(params=params, story=world.render(), prompts=generation_prompts(world), story_qa=story_qa(world), world_qa=world_qa(world), world=world)

def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    return [
        f"Write a small whodunit story in the {p['setting'][0]} about a missing {p['missing'][0]} and a curious clue.",
        f"Tell a child-facing mystery where conflict and curiosity lead to a rhyme that solves the case.",
        "Keep the setting small, the clues concrete, and the ending reassuring."
    ]

def story_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    return [
        QAItem(question="What went missing?", answer=f"The {p['missing'][2]} went missing."),
        QAItem(question="Who solved the mystery?", answer=f"{p['params']['solver']} solved it by staying curious."),
        QAItem(question="What helped them solve it?", answer=f"A rhyme helped them follow the clue and find the {p['missing'][2]}."),
    ]

def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is curiosity?", answer="Curiosity is the urge to look, ask, and find out what is true."),
        QAItem(question="What is a conflict?", answer="A conflict is a disagreement or tension between characters."),
        QAItem(question="What is a rhyme?", answer="A rhyme is a line with matching sounds that can help you remember a clue."),
    ]

def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world:
        print("--- trace ---")
        for eid, ent in sample.world.entities.items():
            print(eid, ent.kind, ent.label, ent.memes)
    if qa:
        print()
        for item in sample.story_qa:
            print(f"Q: {item.question}\nA: {item.answer}")
        print()
        for item in sample.world_qa:
            print(f"Q: {item.question}\nA: {item.answer}")

def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        import storyworlds.asp as asp
        ok = bool(asp_solve()) and "('case1',)" in asp_solve()
        print("OK" if ok else "MISMATCH")
        return
    if args.asp:
        print("\n".join(asp_solve()))
        return
    rng = random.Random(args.seed if args.seed is not None else random.randrange(2**31))
    samples: list[StorySample] = []
    if args.all:
        for s in SETTINGS:
            for m in MISSING:
                params = StoryParams(setting=s[0], missing=m[0], clue=RHYMES[0][0], rhyme=RHYMES[0][1], solver="Mina", skeptic="Toby")
                samples.append(generate(params))
    else:
        for _ in range(args.n):
            samples.append(generate(resolve_params(args, rng)))
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, s in enumerate(samples):
        emit(s, trace=args.trace, qa=args.qa, header=f"### variant {i+1}" if len(samples) > 1 else "")

if __name__ == "__main__":
    main()
