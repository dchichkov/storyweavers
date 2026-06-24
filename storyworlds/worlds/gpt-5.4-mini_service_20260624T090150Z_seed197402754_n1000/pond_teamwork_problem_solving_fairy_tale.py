#!/usr/bin/env python3
"""
A small fairy-tale storyworld about teamwork and problem solving at a pond.

A child-friendly seed tale:
---
Once upon a time, a little rabbit named Pippa lived near a quiet pond in the
forest. Pippa loved the pond because the lilies floated like tiny moons and the
fish flashed like silver ribbons.

One afternoon, Pippa and her friends the duck, the mouse, and the turtle found
that a fallen branch had jammed the little pond path. The water could not flow
well, and the duck's nest on the other side could not be reached safely. Pippa
felt worried, but the friends did not give up. The mouse noticed a small gap,
the turtle nudged the branch, and Pippa hopped in to pull the twigs free. The
duck carried away the lighter sticks, and together they opened the path.

By the time the sun turned gold, the pond was calm again. The duck reached the
nest, the lilies floated free, and Pippa smiled because the friends had solved
the problem together.
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "rabbit", "mouse"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "duck", "turtle"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def they(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the pond"
    details: str = "The pond lay in a green hollow under old willow trees."


@dataclass
class Problem:
    id: str
    title: str
    cause: str
    obstacle: str
    clue: str
    fix_action: str
    solved_image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    helps: set[str]
    used_for: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[str] = set()

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

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


def solve_problem(world: World, hero: Entity, friends: list[Entity], problem: Problem, tool: Optional[Tool]) -> None:
    hero.memes["worry"] = hero.memes.get("worry", 0.0) + 1
    world.say(
        f"{hero.id} loved the pond, but on that day {problem.cause}."
    )
    world.say(
        f"That made a small trouble: {problem.obstacle}."
    )
    if friends:
        names = ", ".join(f.id for f in friends[:-1]) + (f", and {friends[-1].id}" if len(friends) > 1 else friends[0].id)
        world.say(f"{names} came close and listened to the problem.")
    if tool is not None:
        world.say(
            f"The {tool.label} gave them an idea, because it was good for {tool.used_for}."
        )
    hero.memes["hope"] = hero.memes.get("hope", 0.0) + 1
    world.say(problem.clue)
    world.say(
        f"Together they used teamwork: {problem.fix_action}"
    )
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1
    world.say(problem.solved_image)


SETTING = Setting()

HEROES = [
    ("Pippa", "rabbit", "little rabbit"),
    ("Mina", "girl", "little girl"),
    ("Robin", "boy", "little boy"),
]

FRIENDS = [
    ("Ned", "mouse"),
    ("Toby", "turtle"),
    ("Daisy", "duck"),
    ("Wren", "squirrel"),
]

PROBLEMS = {
    "branch": Problem(
        id="branch",
        title="the fallen branch",
        cause="a storm had blown a heavy branch across the pond path",
        obstacle="the water could not flow freely, and the far bank was hard to reach",
        clue="The mouse saw that one end of the branch was loose and easy to lift.",
        fix_action="the turtle pushed, the mouse guided, the hero pulled, and the duck carried the light sticks away",
        solved_image="Soon the water slipped through again, and the pond path was open and clear.",
        tags={"pond", "teamwork", "problem_solving"},
    ),
    "lily_knot": Problem(
        id="lily_knot",
        title="the lily knot",
        cause="a ribbon of reeds had tangled the lily pads together",
        obstacle="the lilies were stuck, and the fish had less room to swim",
        clue="The duck noticed that the reeds floated apart when they were nudged gently.",
        fix_action="the friends held the pads steady while the rabbit and the mouse untied the reeds one soft strip at a time",
        solved_image="At last the lily pads drifted free, bobbing like green boats on quiet water.",
        tags={"pond", "teamwork", "problem_solving"},
    ),
    "frogstep": Problem(
        id="frogstep",
        title="the frog step",
        cause="a muddy little stepping stone had sunk near the bank",
        obstacle="the path across the pond was too wobbly for a safe hop",
        clue="The turtle found flat stones hidden in the grass by the willow roots.",
        fix_action="the friends placed the stones together, one careful step at a time, until a safe path appeared",
        solved_image="Then every hop became easy, and the pond looked brave again.",
        tags={"pond", "teamwork", "problem_solving"},
    ),
}

TOOLS = [
    Tool(id="rope", label="a thin rope", phrase="a thin rope", helps={"pull", "tie", "lift"}, used_for="pulling and tying"),
    Tool(id="stick", label="a long stick", phrase="a long stick", helps={"push", "nudge", "point"}, used_for="nudging and pushing"),
    Tool(id="basket", label="a woven basket", phrase="a woven basket", helps={"carry", "gather"}, used_for="carrying light sticks"),
]

CURATED = []


@dataclass
class StoryParams:
    hero: str
    hero_type: str
    hero_trait: str
    friends: list[str]
    problem: str
    tool: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy-tale pond storyworld about teamwork and problem solving.")
    ap.add_argument("--hero", choices=[h[0] for h in HEROES])
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--tool", choices=[t.id for t in TOOLS])
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
    hero_name, hero_type, hero_trait = rng.choice(HEROES)
    if args.hero:
        for h in HEROES:
            if h[0] == args.hero:
                hero_name, hero_type, hero_trait = h
    problem = args.problem or rng.choice(list(PROBLEMS))
    tool = args.tool or rng.choice([t.id for t in TOOLS])
    if problem == "frogstep" and tool == "basket":
        tool = "stick"
    friends = [rng.choice(FRIENDS)[0], rng.choice(FRIENDS)[0]]
    friends = list(dict.fromkeys(friends))
    return StoryParams(hero=hero_name, hero_type=hero_type, hero_trait=hero_trait, friends=friends, problem=problem, tool=tool)


def make_world(params: StoryParams) -> World:
    world = World(SETTING)
    hero = world.add(Entity(id=params.hero, kind="character", type=params.hero_type))
    friend_ents = []
    for name in params.friends:
        t = next(t for n, t in FRIENDS if n == name)
        friend_ents.append(world.add(Entity(id=name, kind="character", type=t)))
    problem = PROBLEMS[params.problem]
    tool = next((t for t in TOOLS if t.id == params.tool), None)

    world.say(f"Once upon a time, {hero.id} lived beside {world.setting.place}.")
    world.say(world.setting.details)
    world.say(f"{hero.id} loved the pond because {problem.title} made the day feel like a quest.")
    world.para()
    world.say(f"One morning, {problem.cause}.")
    world.say(problem.obstacle)
    solve_problem(world, hero, friend_ents, problem, tool)
    world.para()
    world.say(
        f"By sunset, {hero.id} smiled at the calm water. "
        f"With a little courage and a lot of teamwork, the pond was peaceful again."
    )
    world.facts.update(hero=hero, friends=friend_ents, problem=problem, tool=tool)
    return world


def generate(params: StoryParams) -> StorySample:
    world = make_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    p = world.facts["problem"]
    hero = world.facts["hero"]
    return [
        f"Write a short fairy tale about {hero.id} at the pond where teamwork solves {p.title}.",
        f"Tell a gentle story with the words pond, teamwork, and problem solving.",
        f"Create a child-friendly tale in which friends help {hero.id} fix a problem near the pond.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.facts["hero"]
    problem = world.facts["problem"]
    tool = world.facts["tool"]
    friend_names = ", ".join(f.id for f in world.facts["friends"])
    return [
        QAItem(
            question=f"Where did {hero.id} live?",
            answer=f"{hero.id} lived beside the pond in the forest.",
        ),
        QAItem(
            question=f"What was the problem in the story?",
            answer=f"The problem was {problem.obstacle}.",
        ),
        QAItem(
            question=f"Who helped {hero.id} solve the trouble?",
            answer=f"{friend_names} helped {hero.id}, and they worked together as a team.",
        ),
        QAItem(
            question=f"What useful thing did the friends use?",
            answer=f"They used {tool.label} to help solve the problem.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with the pond calm again and {hero.id} smiling because the problem was fixed.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is teamwork?",
            answer="Teamwork is when people or friends work together to do something or solve a problem.",
        ),
        QAItem(
            question="What is a pond?",
            answer="A pond is a small body of water, often home to ducks, fish, frogs, and water plants.",
        ),
        QAItem(
            question="What does problem solving mean?",
            answer="Problem solving means finding a way to fix a trouble or answer a hard question.",
        ),
    ]


def asp_facts() -> str:
    import asp
    lines = []
    lines.append(asp.fact("setting", "pond"))
    for pid, p in PROBLEMS.items():
        lines.append(asp.fact("problem", pid))
        lines.append(asp.fact("at_setting", pid, "pond"))
        for tag in sorted(p.tags):
            lines.append(asp.fact("tagged", pid, tag))
    for tid, t in [(t.id, t) for t in TOOLS]:
        lines.append(asp.fact("tool", tid))
        for h in sorted(t.helps):
            lines.append(asp.fact("helps", tid, h))
    return "\n".join(lines)


ASP_RULES = r"""
valid_problem(P) :- problem(P), at_setting(P, pond), tagged(P, teamwork), tagged(P, problem_solving).
usable_tool(T) :- tool(T), helps(T, pull); helps(T, push); helps(T, tie); helps(T, carry); helps(T, lift); helps(T, nudge).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for p in PROBLEMS:
        for t in TOOLS:
            out.append(("pond", p, t.id))
    return out


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_problem/1. #show usable_tool/1."))
    probs = {a[0] for a in asp.atoms(model, "valid_problem")}
    tools = {a[0] for a in asp.atoms(model, "usable_tool")}
    return [("pond", p, t) for p in sorted(probs) for t in sorted(tools)]


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(f"  {e.id:8} ({e.type}) memes={e.memes} meters={e.meters}")
    return "\n".join(lines)


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
        print(asp_program("#show valid_problem/1. #show usable_tool/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_valid_combos())
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        params_list = [StoryParams(hero=h[0], hero_type=h[1], hero_trait=h[2], friends=["Ned", "Toby"], problem=p, tool="rope") for h in HEROES for p in PROBLEMS]
        samples = [generate(p) for p in params_list]
    else:
        seen = set()
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
        if len(samples) > 1:
            print(f"### variant {i+1}")
        emit(sample, trace=args.trace, qa=args.qa)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
