#!/usr/bin/env python3
"""
storyworlds/worlds/odd_upturned_bongo_teamwork_twist_tall_tale.py
===================================================================

A small Tall Tale-style story world about an odd upturned bongo, a teamwork
problem, and a twist ending.

Seed premise:
---
On a blustery afternoon, a little crew found an odd upturned bongo stuck in the
middle of the town green. It was far too big for one child to move alone. The
crew tried to tug it, roll it, and tip it, but the bongo only rocked and wobbled
like a sleepy barrel.

Then they made a plan. One child fetched a rope, another propped a plank, and
the tallest helper counted out the lifts. Together they turned the bongo upright
with a great wobble and a grand whomp.

Twist:
---
Inside the upturned bongo, they found a tiny weather map that had been hiding
under the drumskin. The map showed where the next gust of wind would blow the
kite festival banner, so the crew could save the celebration in time.

This script turns that premise into a tiny, constraint-checked story domain with
physical meters and emotional memes, plus a Python/ASP reasonableness gate.
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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    outdoors: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Problem:
    id: str
    title: str
    verb: str
    tug: str
    twist_item: str
    twist_reveal: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    helper: str
    covers: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

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

        w = World(self.setting)
        w.entities = _copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.fired = set(self.fired)
        return w


def _say_many(world: World, lines: list[str]) -> None:
    for line in lines:
        world.say(line)


def setup_story(world: World, kids: list[Entity], bongo: Entity, problem: Problem) -> None:
    k1, k2, k3 = kids
    world.say(
        f"On an odd bright morning, {k1.id}, {k2.id}, and {k3.id} found "
        f"{bongo.phrase} in {world.setting.place}."
    )
    world.say(
        f"It was upturned like a bowl, and it sat there with a sleepy wobble."
    )
    world.say(
        f'The whole sight felt like a tall-tale prank, especially with the word "{problem.keyword}" '
        f"hanging over the day.'
    )
    for kid in kids:
        kid.memes["wonder"] += 1


def feel_problem(world: World, kids: list[Entity], problem: Problem, bongo: Entity) -> None:
    for kid in kids:
        kid.memes["curiosity"] += 1
    world.say(
        f"{kids[0].id} wanted to {problem.verb}, but the bongo was too big and too stuck."
    )
    world.say(
        f"{kids[1].id} gave it a tug, {kids[2].id} gave it a shove, and the bongo only rocked."
    )
    bongo.meters["stuck"] += 1
    bongo.memes["stubborn"] += 1


def teamwork_plan(world: World, kids: list[Entity], tool: Entity, bongo: Entity) -> None:
    k1, k2, k3 = kids
    k1.memes["hope"] += 1
    k2.memes["hope"] += 1
    k3.memes["hope"] += 1
    world.say(
        f"Then they made a teamwork plan: {k1.id} fetched {tool.phrase}, "
        f"{k2.id} braced the side, and {k3.id} counted the lift."
    )
    world.say(
        f"With the rope in hand and the plank under one edge, the crew leaned together."
    )
    bongo.meters["ready"] += 1


def twist_reveal(world: World, kids: list[Entity], bongo: Entity, problem: Problem) -> None:
    k1, k2, k3 = kids
    bongo.meters["upright"] += 1
    bongo.meters["stuck"] = 0
    for kid in kids:
        kid.memes["joy"] += 1
        kid.memes["pride"] += 1
    world.say(
        f"With one great heave, the odd upturned bongo tipped upright at last."
    )
    world.say(
        f"Then came the twist: inside it, under the drumskin, was {problem.twist_item}."
    )
    world.say(
        f"{problem.twist_reveal} Because of that, the crew could save the kite festival before the wind changed."
    )
    world.say(
        f"{k1.id}, {k2.id}, and {k3.id} laughed so hard that the green rang like a barn bell."
    )


def tell(setting: Setting, problem: Problem, tool: Tool, names: list[str]) -> World:
    world = World(setting)
    kids = [
        world.add(Entity(id=names[0], kind="character", type="boy")),
        world.add(Entity(id=names[1], kind="character", type="girl")),
        world.add(Entity(id=names[2], kind="character", type="boy")),
    ]
    bongo = world.add(Entity(
        id="bongo",
        type="thing",
        label="bongo",
        phrase="an odd upturned bongo",
        owner="none",
    ))
    rope = world.add(Entity(
        id=tool.id,
        type="thing",
        label=tool.label,
        phrase=tool.phrase,
        owner=kids[0].id,
    ))

    setup_story(world, kids, bongo, problem)
    world.para()
    feel_problem(world, kids, problem, bongo)
    world.para()
    teamwork_plan(world, kids, rope, bongo)
    world.para()
    twist_reveal(world, kids, bongo, problem)

    world.facts.update(
        setting=setting,
        problem=problem,
        tool=tool,
        kids=kids,
        bongo=bongo,
    )
    return world


SETTINGS = {
    "green": Setting(place="the town green", outdoors=True, affords={"lift", "twist"}),
    "fair": Setting(place="the windy fairground", outdoors=True, affords={"lift", "twist"}),
    "harbor": Setting(place="the harbor square", outdoors=True, affords={"lift", "twist"}),
}

PROBLEMS = {
    "bongo": Problem(
        id="bongo",
        title="odd upturned bongo",
        verb="turn the bongo upright",
        tug="tug",
        twist_item="a tiny weather map",
        twist_reveal="It showed the next gust of wind curling toward the kite festival banner.",
        keyword="bongo",
        tags={"odd", "upturned", "bongo", "twist", "teamwork"},
    ),
}

TOOLS = {
    "rope": Tool(
        id="rope",
        label="a long rope",
        phrase="a long rope",
        helper="rope",
        covers={"pull"},
    )
}

NAMES = ["Pip", "Mara", "Toby", "Nell", "Juno", "Otis", "Wren", "Gus"]
CURATED = [
    ("green", "bongo", "rope", ["Pip", "Mara", "Toby"]),
    ("fair", "bongo", "rope", ["Nell", "Juno", "Otis"]),
    ("harbor", "bongo", "rope", ["Wren", "Gus", "Pip"]),
]


@dataclass
class StoryParams:
    place: str
    problem: str
    tool: str
    name1: str
    name2: str
    name3: str
    seed: Optional[int] = None


def reasonableness_gate(params: StoryParams) -> None:
    if params.problem not in PROBLEMS:
        raise StoryError("Unknown problem.")
    if params.tool not in TOOLS:
        raise StoryError("Unknown tool.")
    if params.place not in SETTINGS:
        raise StoryError("Unknown place.")
    if params.problem == "bongo" and params.tool != "rope":
        raise StoryError("This tall tale needs a rope to move the odd upturned bongo.")


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    kids = f["kids"]
    problem = f["problem"]
    return [
        f'Write a tall tale for a small child about {problem.title} and teamwork.',
        f"Tell a story where {kids[0].id}, {kids[1].id}, and {kids[2].id} use teamwork to solve a strange problem.",
        f'Write a gentle story with the words "odd", "upturned", and "bongo", ending with a twist.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    kids = f["kids"]
    p = f["problem"]
    s = f["setting"]
    tool = f["tool"]
    return [
        QAItem(
            question=f"What did {kids[0].id}, {kids[1].id}, and {kids[2].id} find at {s.place}?",
            answer=f"They found {p.title} at {s.place}. It was odd, upturned, and too big for one child to move alone.",
        ),
        QAItem(
            question=f"How did the children solve the problem with the {p.keyword}?",
            answer=f"They used teamwork. One child brought {tool.phrase}, one braced the side, and one counted the lift.",
        ),
        QAItem(
            question=f"What was the twist inside the {p.keyword}?",
            answer=f"The twist was {p.twist_item}. It helped the children save the kite festival before the wind changed.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is teamwork?",
            answer="Teamwork is when people work together and each one helps with a job so the group can do something bigger than one person could do alone.",
        ),
        QAItem(
            question="What is a twist in a story?",
            answer="A twist is a surprising turn that changes what the characters expected.",
        ),
        QAItem(
            question="What is a bongo?",
            answer="A bongo is a small drum that people can tap with their hands to make a beat.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.phrase:
            bits.append(f"phrase={e.phrase}")
        out.append(f"  {e.id}: {e.kind}/{e.type} " + " ".join(bits))
    return "\n".join(out)


ASP_RULES = r"""
% A story is valid when the place affords the lift/twist setting,
% the odd upturned bongo is paired with a rope, and the twist exists.

valid_place(P) :- place(P).
valid_problem(bongo) :- problem(bongo).
valid_tool(rope) :- tool(rope).

reasonable(P, bongo, rope) :- place(P), problem(bongo), tool(rope).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid in SETTINGS:
        lines.append(asp.fact("place", pid))
    for pid in PROBLEMS:
        lines.append(asp.fact("problem", pid))
    for tid in TOOLS:
        lines.append(asp.fact("tool", tid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program("#show reasonable/3."))
    found = set(asp.atoms(model, "reasonable"))
    expected = {(p, "bongo", "rope") for p in SETTINGS}
    if found == expected:
        print(f"OK: ASP gate matches Python gate ({len(found)} combos).")
        return 0
    print("MISMATCH:")
    print("  asp:", sorted(found))
    print("  python:", sorted(expected))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall tale story world about an odd upturned bongo and teamwork.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--name1")
    ap.add_argument("--name2")
    ap.add_argument("--name3")
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
    place = args.place or rng.choice(list(SETTINGS))
    problem = args.problem or "bongo"
    tool = args.tool or "rope"
    reasonableness_gate(StoryParams(place, problem, tool, "A", "B", "C"))
    names = [args.name1 or rng.choice(NAMES), args.name2 or rng.choice(NAMES), args.name3 or rng.choice(NAMES)]
    return StoryParams(place=place, problem=problem, tool=tool, name1=names[0], name2=names[1], name3=names[2])


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.place],
        PROBLEMS[params.problem],
        TOOLS[params.tool],
        [params.name1, params.name2, params.name3],
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show reasonable/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp

        model = asp.one_model(asp_program("#show reasonable/3."))
        items = sorted(set(asp.atoms(model, "reasonable")))
        for item in items:
            print(item)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for place, problem, tool, names in CURATED:
            params = StoryParams(place, problem, tool, *names)
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            rng = random.Random(seed)
            try:
                params = resolve_params(args, rng)
            except StoryError as e:
                print(e)
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.place} / {p.problem} / {p.tool}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
