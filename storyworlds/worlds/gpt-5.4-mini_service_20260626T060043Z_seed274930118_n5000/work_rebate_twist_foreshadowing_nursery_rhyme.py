#!/usr/bin/env python3
"""
A tiny storyworld about work, a rebate, a twist, and foreshadowing, told in a
nursery-rhyme style.

The seed tale premise:
A small worker wants to finish a job and earn a rebate at the market, but a
small twist changes what the rebate can buy. Gentle foreshadowing plants clues
early, and the ending pays off those clues with a tidy, child-friendly turn.
"""

from __future__ import annotations

import argparse
import dataclasses
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
    kind: str = "thing"  # character | thing | place
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    carries: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind != "character":
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Place:
    id: str
    label: str
    affordances: set[str] = field(default_factory=set)


@dataclass
class Task:
    id: str
    verb: str
    noun: str
    work: str
    outcome: str
    twist: str
    clue: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Reward:
    id: str
    label: str
    phrase: str
    amount: int
    condition: str
    can_buy: set[str] = field(default_factory=set)


@dataclass
class World:
    place: Place
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
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
        clone = World(self.place)
        clone.entities = dataclasses.deepcopy(self.entities) if hasattr(dataclasses, "deepcopy") else __import__("copy").deepcopy(self.entities)
        clone.facts = dict(self.facts)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

PLACES = {
    "mill": Place(id="mill", label="the little mill", affordances={"work"}),
    "market": Place(id="market", label="the bright market", affordances={"work", "buy"}),
    "barn": Place(id="barn", label="the red barn", affordances={"work"}),
}

TASKS = {
    "mend": Task(
        id="mend",
        verb="mend",
        noun="the torn hem",
        work="stitching",
        outcome="the hem was neat",
        twist="the thread was shorter than it seemed",
        clue="the spool gave a tiny rattle",
        tags={"thread", "cloth", "work"},
    ),
    "stack": Task(
        id="stack",
        verb="stack",
        noun="the boxes",
        work="lifting",
        outcome="the pile stood tall",
        twist="one box held a squeaky toy",
        clue="one box giggled when tapped",
        tags={"box", "work", "sound"},
    ),
    "sweep": Task(
        id="sweep",
        verb="sweep",
        noun="the floor",
        work="brooming",
        outcome="the floor was bright",
        twist="the dust made a moon-shaped mark",
        clue="the dust drew a pale curve",
        tags={"dust", "work", "moon"},
    ),
}

REBATES = {
    "coin": Reward(
        id="coin",
        label="a silver coin",
        phrase="one bright silver coin",
        amount=1,
        condition="finish the work neatly",
        can_buy={"seed-cake", "apple"},
    ),
    "purse": Reward(
        id="purse",
        label="a small purse rebate",
        phrase="a tiny purse with two coins",
        amount=2,
        condition="finish the work and bring it back tidy",
        can_buy={"apple", "ribbon", "jam"},
    ),
    "token": Reward(
        id="token",
        label="a gold token",
        phrase="one gold token with a star",
        amount=3,
        condition="finish the work with care",
        can_buy={"ribbon", "toy-boat", "jam"},
    ),
}

SHOP_GOODS = {
    "seed-cake": "a seed cake",
    "apple": "a round apple",
    "ribbon": "a red ribbon",
    "jam": "a little jar of jam",
    "toy-boat": "a wooden toy boat",
}

NAMES = ["Milly", "Nell", "Toby", "Pip", "Lina", "Jo", "Wren", "Kit"]
TRAITS = ["spry", "cheery", "curious", "merry", "gentle"]


@dataclass
class StoryParams:
    place: str
    task: str
    rebate: str
    name: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Story helpers
# ---------------------------------------------------------------------------

def nursery_line(world: World, text: str) -> None:
    world.say(text)


def foreshadow(world: World, task: Task) -> None:
    nursery_line(
        world,
        f"Before the day was old, {task.clue}, and a small hush hung in the air.",
    )


def setup(world: World, child: Entity, task: Task, rebate: Reward) -> None:
    child.memes["hope"] = child.memes.get("hope", 0) + 1
    nursery_line(
        world,
        f"{child.id} was a {child.memes.get('trait', 'bright')} little worker, quick with a grin and glad to do {task.work}.",
    )
    nursery_line(
        world,
        f"At {world.place.label}, {child.id} had a job to {task.verb} {task.noun}, and a rebate waited at the end.",
    )
    nursery_line(
        world,
        f"The promise was plain: {rebate.phrase}, if {child.id} could {rebate.condition}.",
    )


def do_work(world: World, child: Entity, task: Task) -> None:
    child.meters["work"] = child.meters.get("work", 0) + 1
    child.memes["pride"] = child.memes.get("pride", 0) + 1
    nursery_line(
        world,
        f"So {child.id} set to {task.work}, and the little work rang like a bell in a nursery rhyme.",
    )
    foreshadow(world, task)
    world.facts["task_started"] = task.id


def twist_turn(world: World, child: Entity, task: Task, rebate: Reward) -> None:
    child.memes["surprise"] = child.memes.get("surprise", 0) + 1
    world.facts["twist"] = task.twist
    nursery_line(
        world,
        f"But then came a twist: {task.twist}.",
    )
    nursery_line(
        world,
        f"{child.id} blinked twice, for the rebate was still real, yet it could not buy quite the same thing as before.",
    )


def resolve(world: World, child: Entity, task: Task, rebate: Reward) -> None:
    if rebate.id == "coin":
        choice = "seed-cake"
    elif rebate.id == "purse":
        choice = "apple"
    else:
        choice = "ribbon"
    world.facts["purchase"] = choice
    child.memes["joy"] = child.memes.get("joy", 0) + 1
    nursery_line(
        world,
        f"Then {child.id} chose {SHOP_GOODS[choice]}, for the small rebate was enough for that and not for the bigger dream.",
    )
    nursery_line(
        world,
        f"With care and cheer, {child.id} finished the work, kept the rebate, and laughed at the clever little change.",
    )
    nursery_line(
        world,
        f"So the day ended snug and neat: the work was done, the rebate was spent, and the twist had turned into a treat.",
    )


def tell_story(params: StoryParams) -> World:
    place = PLACES[params.place]
    task = TASKS[params.task]
    rebate = REBATES[params.rebate]
    world = World(place=place)
    child = world.add(Entity(
        id=params.name,
        kind="character",
        label=params.name,
        meters={"work": 0.0},
        memes={"trait": params.trait},
    ))
    world.facts.update(place=place.id, task=task.id, rebate=rebate.id, name=params.name)

    setup(world, child, task, rebate)
    world.para()
    do_work(world, child, task)
    twist_turn(world, child, task, rebate)
    world.para()
    resolve(world, child, task, rebate)
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    task = TASKS[f["task"]]
    rebate = REBATES[f["rebate"]]
    return [
        f"Write a short nursery-rhyme-style story about {f['name']} doing {task.work} for a rebate.",
        f"Tell a gentle story where a child works at the market, meets a twist, and uses a small rebate wisely.",
        f"Create a tiny story with foreshadowing, work, and a rebate that still ends happily for a child named {f['name']}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    task = TASKS[f["task"]]
    rebate = REBATES[f["rebate"]]
    return [
        QAItem(
            question=f"What work did {f['name']} do at {world.place.label}?",
            answer=f"{f['name']} did {task.work}; the job was to {task.verb} {task.noun}.",
        ),
        QAItem(
            question=f"What was the rebate in the story?",
            answer=f"The rebate was {rebate.phrase}, given after the work was finished neatly.",
        ),
        QAItem(
            question="What was the twist?",
            answer=f"The twist was that {task.twist}, which changed what the rebate could buy.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"{f['name']} finished the work, kept the rebate, and bought {SHOP_GOODS[world.facts['purchase']]}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is work?",
            answer="Work is something you do with effort to finish a job or help get something done.",
        ),
        QAItem(
            question="What is a rebate?",
            answer="A rebate is money or a reward you get back after doing something, like finishing a job or making a purchase.",
        ),
        QAItem(
            question="What is foreshadowing?",
            answer="Foreshadowing is when a story gives little clues early about something that will matter later.",
        ),
        QAItem(
            question="What is a twist in a story?",
            answer="A twist is a surprising change that turns the story in a new direction.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(f"- {p}")
    lines.append("")
    lines.append("== story q&a ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world q&a ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- world trace ---"]
    for e in world.entities.values():
        out.append(f"{e.id}: kind={e.kind} meters={e.meters} memes={e.memes}")
    out.append(f"place={world.place.id}")
    out.append(f"facts={world.facts}")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% facts:
% place(P). task(T). rebate(R). task_needs_work(T). rebate_amount(R,N).
% task_tags(T,Tag). purchase_ok(R,Good). twist(T).

valid_story(P,T,R) :- place(P), task(T), rebate(R), task_needs_work(T), rebate_amount(R,N), N > 0.
has_foreshadowing(T) :- task_tags(T, clue).
has_twist(T) :- twist(T).
has_payoff(T,R) :- valid_story(_,T,R), rebate_amount(R,N), N >= 1.
"""


def asp_facts() -> str:
    import asp  # lazy import
    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for tid, task in TASKS.items():
        lines.append(asp.fact("task", tid))
        lines.append(asp.fact("task_needs_work", tid))
        lines.append(asp.fact("twist", tid))
        for tag in sorted(task.tags | {"clue"}):
            lines.append(asp.fact("task_tags", tid, tag))
    for rid, rebate in REBATES.items():
        lines.append(asp.fact("rebate", rid))
        lines.append(asp.fact("rebate_amount", rid, rebate.amount))
        for good in sorted(rebate.can_buy):
            lines.append(asp.fact("purchase_ok", rid, good))
    return "\n".join(lines)


def asp_program(show: str = "#show valid_story/3.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp  # lazy import
    model = asp.one_model(asp_program("#show valid_story/3."))
    asp_set = set(asp.atoms(model, "valid_story"))
    py_set = set((p, t, r) for p in PLACES for t in TASKS for r in REBATES
                 if PLACES[p].affordances and REBATES[r].amount > 0)
    if asp_set == py_set:
        print(f"OK: ASP gate matches Python gate ({len(py_set)} combos).")
        return 0
    print("MISMATCH between ASP and Python:")
    print("only in ASP:", sorted(asp_set - py_set))
    print("only in Python:", sorted(py_set - asp_set))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A nursery-rhyme storyworld about work and a rebate.")
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--task", choices=sorted(TASKS))
    ap.add_argument("--rebate", choices=sorted(REBATES))
    ap.add_argument("--name")
    ap.add_argument("--trait", choices=sorted(TRAITS))
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for p in PLACES:
        for t in TASKS:
            for r in REBATES:
                combos.append((p, t, r))
    return combos


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    combos = [c for c in combos
              if (args.place is None or c[0] == args.place)
              and (args.task is None or c[1] == args.task)
              and (args.rebate is None or c[2] == args.rebate)]
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    place, task, rebate = rng.choice(sorted(combos))
    name = args.name or rng.choice(NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, task=task, rebate=rebate, name=name, trait=trait)


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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/3."))
        combos = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(combos)} compatible story combos:")
        for c in combos:
            print(" ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        for p in PLACES:
            for t in TASKS:
                for r in REBATES:
                    samples.append(generate(StoryParams(place=p, task=t, rebate=r, name="Milly", trait="merry")))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 25):
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
