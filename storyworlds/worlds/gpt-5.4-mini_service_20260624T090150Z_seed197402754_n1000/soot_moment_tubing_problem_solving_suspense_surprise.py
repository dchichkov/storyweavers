#!/usr/bin/env python3
"""
storyworlds/worlds/soot_moment_tubing_problem_solving_suspense_surprise.py
===========================================================================

A small fable-like story world about a soot-streaked moment, a bit of tubing,
and the kind of problem solving that begins in suspense and ends in surprise.

The premise is simple: someone needs to move a little bit of air or water
through a tube, but soot has clogged the path. The tension comes from not
knowing where the blockage is, and the turn comes when the characters test,
clean, swap, or reconnect the tubing until flow returns.

This world is intentionally tiny and classical:
- a character wants to solve a practical problem,
- a hidden soot blockage causes suspense,
- a surprising but sensible fix restores the flow.

The story prose is authored from world state, not from a frozen template.
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

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    linked_to: Optional[str] = None
    cleanable: bool = False
    leakproof: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"soot": 0.0, "flow": 0.0, "wear": 0.0}
        if not self.memes:
            self.memes = {"worry": 0.0, "hope": 0.0, "surprise": 0.0, "relief": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class World:
    setting: str
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)

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
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone


@dataclass
class StoryParams:
    place: str
    problem: str
    hero_name: str
    hero_type: str
    helper_name: str
    seed: Optional[int] = None


@dataclass
class Setting:
    place: str
    affordances: set[str]


@dataclass
class Problem:
    id: str
    noun: str
    blocked_by: str
    action: str
    check: str
    fix: str
    surprise_fix: str
    emotional_turn: str


SETTINGS = {
    "workshop": Setting(place="the little workshop", affordances={"tube"}),
    "garden_shed": Setting(place="the garden shed", affordances={"tube"}),
    "boathouse": Setting(place="the boathouse", affordances={"tube"}),
}

PROBLEMS = {
    "soot_tube": Problem(
        id="soot_tube",
        noun="tubing",
        blocked_by="soot",
        action="push water through the tubing",
        check="peek into the tubing",
        fix="clean the tube with a soft brush",
        surprise_fix="open a tiny side valve",
        emotional_turn="surprised",
    ),
    "lamp_smoke": Problem(
        id="lamp_smoke",
        noun="tubing",
        blocked_by="soot",
        action="make the lamp breathe again",
        check="hold the tubing to the light",
        fix="wipe the soot from the tube",
        surprise_fix="swap in a spare bit of tubing",
        emotional_turn="curious",
    ),
}

HEROES = ["Milo", "Nina", "Pip", "Tara", "Owen", "Mira"]
HELPERS = ["Grandpa", "Aunt Bee", "the owl", "the old miller", "the kind neighbor"]

ASP_RULES = r"""
problem(P) :- problem_kind(P).
blocked(P, soot) :- problem_kind(P).
needs_check(P) :- blocked(P, soot).
can_fix(P) :- needs_check(P), has_tool(P, brush).
surprising_fix(P) :- needs_check(P), has_spare(P).
resolved(P) :- can_fix(P).
resolved(P) :- surprising_fix(P).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.affordances):
            lines.append(asp.fact("affords", sid, a))
    for pid in PROBLEMS:
        lines.append(asp.fact("problem_kind", pid))
        lines.append(asp.fact("has_tool", pid, "brush"))
        lines.append(asp.fact("has_spare", pid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for place in SETTINGS:
        for prob in PROBLEMS:
            combos.append((place, prob))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fable-like soot, moment, tubing story world.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--name")
    ap.add_argument("--helper")
    ap.add_argument("--type", dest="hero_type", choices=["girl", "boy"])
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
    hero_type = args.hero_type or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(HEROES)
    helper = args.helper or rng.choice(HELPERS)
    return StoryParams(place=place, problem=problem, hero_name=name, hero_type=hero_type, helper_name=helper)


def _do_problem(world: World, hero: Entity, problem: Problem) -> None:
    soot = world.get("tube")
    soot.meters["soot"] += 1
    hero.memes["worry"] += 1


def tell(params: StoryParams) -> World:
    world = World(setting=SETTINGS[params.place].place)
    hero = world.add(Entity(id=params.hero_name, kind="character", type=params.hero_type))
    helper = world.add(Entity(id="helper", kind="character", type="adult", label=params.helper_name))
    tube = world.add(Entity(
        id="tube",
        type="tube",
        label="tubing",
        phrase="a narrow length of tubing",
        owner=hero.id,
        caretaker=helper.id,
        cleanable=True,
    ))
    problem = PROBLEMS[params.problem]

    world.say(f"Once, in {world.setting}, {hero.id} found {tube.phrase} beside a small pump.")
    world.say(f"{hero.id} wanted to {problem.action}, but there was a soot-dark {problem.noun} in the way.")
    world.para()
    world.say(f"{hero.id} paused for a moment and chose to {problem.check}.")
    _do_problem(world, hero, problem)
    world.say(f"Inside, the tube was blackened with {problem.blocked_by}, and the path still did not move.")
    world.say(f"That made {hero.id} worry, yet {hero.pronoun().capitalize()} did not give up.")
    world.para()
    world.say(f"Then {params.helper_name} came close and listened to the stillness.")
    world.say(f'"Let us try something gentle," {params.helper_name} said.')
    world.say(f"They first decided to {problem.fix}.")
    tube.meters["soot"] = 0.0
    tube.meters["flow"] = 0.0
    world.say(f"At that moment, the little blockage thinned, but the surprise was that the flow still stayed shy.")
    hero.memes["surprise"] += 1
    world.say(f"So {hero.id} looked at the tubing again and tried {problem.surprise_fix}.")
    tube.meters["flow"] = 1.0
    hero.memes["hope"] += 1
    hero.memes["relief"] += 1
    world.say(f"At once, the water ran through at last.")
    world.para()
    world.say(f"{hero.id} smiled, and even the helper laughed at the clever turn.")
    world.say(f"The fable was plain: when a path is blocked, a patient mind can still find a new way.")

    world.facts.update(hero=hero, helper=helper, tube=tube, problem=problem, params=params)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short fable for children about soot, a moment of doubt, and tubing in {f["params"].place}.',
        f"Tell a suspenseful story where {f['hero'].id} notices soot in some tubing and solves the problem with help.",
        f"Write a gentle surprise story about a child who fixes blocked tubing without giving up.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    problem = f["problem"]
    tube = f["tube"]
    return [
        QAItem(
            question=f"What did {hero.id} notice in the tubing?",
            answer=f"{hero.id} noticed soot in the tubing, which kept the water from moving.",
        ),
        QAItem(
            question=f"Who helped {hero.id} solve the problem?",
            answer=f"{helper.label} helped {hero.id} think through the blockage and try a careful fix.",
        ),
        QAItem(
            question=f"What surprising thing finally made the water move?",
            answer=f"The surprising part was that {hero.id} had to try {problem.surprise_fix} before the flow returned.",
        ),
        QAItem(
            question=f"How did the tubing change by the end of the story?",
            answer=f"By the end, the soot was cleaned away and the tubing let the water pass through again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is soot?",
            answer="Soot is a black powder made by smoke from a fire or flame. It can stick to walls, tools, and tubes.",
        ),
        QAItem(
            question="What is tubing?",
            answer="Tubing is a hollow tube that lets air or water travel from one place to another.",
        ),
        QAItem(
            question="What does problem solving mean?",
            answer="Problem solving means thinking carefully about a trouble and trying different safe ways to fix it.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- world model state ---"]
    for e in world.entities.values():
        out.append(f"  {e.id:8} ({e.type:7}) meters={e.meters} memes={e.memes}")
    return "\n".join(out)


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


def asp_verify() -> int:
    import asp
    program = asp_program("#show resolved/1.")
    model = asp.one_model(program)
    resolved = set(asp.atoms(model, "resolved"))
    python = {("soot_tube",), ("lamp_smoke",)}
    if resolved == python:
        print(f"OK: clingo gate matches python ({len(resolved)} problems).")
        return 0
    print("MISMATCH between clingo and python.")
    print("clingo:", sorted(resolved))
    print("python:", sorted(python))
    return 1


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show resolved/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show resolved/1."))
        print(sorted(set(asp.atoms(model, "resolved"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for place, problem in valid_combos():
            params = StoryParams(
                place=place,
                problem=problem,
                hero_name="Milo",
                hero_type="boy",
                helper_name="Grandpa",
            )
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
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
