#!/usr/bin/env python3
"""
storyworlds/worlds/profess_propose_nestle_problem_solving_adventure.py
======================================================================

A small adventure story world about a child who has to solve a problem with
careful words, a proposal, and a cozy nestle at the end.

Seed words: profess, propose, nestle
Style: Adventure
Feature: Problem Solving
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
class Actor:
    id: str
    kind: str = "character"
    type: str = "child"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.meters = dict(self.meters)
        self.memes = dict(self.memes)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Tool:
    id: str
    label: str
    help_text: str
    covers: set[str] = field(default_factory=set)


@dataclass
class Problem:
    id: str
    label: str
    place: str
    obstacle: str
    risk: str
    trouble_meter: str
    solved_by: str
    nestle_place: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    problem: str
    tool: str
    name: str
    gender: str
    helper: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self) -> None:
        self.entities: dict[str, object] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.trace: list[str] = []

    def add(self, ent):
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str):
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)
            self.trace.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


SETTINGS = {
    "cave": "the cave",
    "river": "the river",
    "forest": "the forest",
    "hill": "the hill",
    "harbor": "the harbor",
}

PROBLEMS = {
    "lost_map": Problem(
        id="lost_map",
        label="lost map",
        place="the forest",
        obstacle="could not find the path home",
        risk="getting turned around",
        trouble_meter="lostness",
        solved_by="follow the stars",
        nestle_place="a soft mossy hollow",
        tags={"map", "forest", "path"},
    ),
    "stuck_boat": Problem(
        id="stuck_boat",
        label="stuck boat",
        place="the harbor",
        obstacle="the little boat would not move",
        risk="missing the evening tide",
        trouble_meter="delay",
        solved_by="push together",
        nestle_place="a safe dock corner",
        tags={"boat", "harbor", "tide"},
    ),
    "blocked_path": Problem(
        id="blocked_path",
        label="blocked path",
        place="the cave",
        obstacle="a pile of stones blocked the way",
        risk="being unable to reach the light",
        trouble_meter="frustration",
        solved_by="make a careful tunnel",
        nestle_place="a warm blanket nook",
        tags={"stones", "cave", "path"},
    ),
    "high_branch": Problem(
        id="high_branch",
        label="high branch",
        place="the hill",
        obstacle="the fruit hung too high to reach",
        risk="going hungry",
        trouble_meter="worry",
        solved_by="build a small ladder",
        nestle_place="a grassy ledge",
        tags={"branch", "hill", "fruit"},
    ),
}

TOOLS = {
    "rope": Tool(id="rope", label="rope", help_text="tie things safely", covers={"pull"}),
    "lantern": Tool(id="lantern", label="lantern", help_text="light the dark path", covers={"light"}),
    "sticks": Tool(id="sticks", label="two sticks", help_text="make a bridge or support", covers={"build"}),
    "blanket": Tool(id="blanket", label="a blanket", help_text="make a cozy nest", covers={"warmth"}),
}

GIRL_NAMES = ["Mia", "Nora", "Ava", "Zoe", "Lily", "Ada", "Ivy", "Maya"]
BOY_NAMES = ["Leo", "Finn", "Noah", "Eli", "Theo", "Max", "Ben", "Jack"]
TRAITS = ["brave", "curious", "careful", "steady", "kind", "spirited"]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place_key, place in SETTINGS.items():
        for prob_id, prob in PROBLEMS.items():
            if prob.place != place:
                continue
            for tool_id in TOOLS:
                if prob_id == "blocked_path" and tool_id in {"rope", "sticks"}:
                    out.append((place_key, prob_id, tool_id))
                elif prob_id == "lost_map" and tool_id in {"lantern", "rope"}:
                    out.append((place_key, prob_id, tool_id))
                elif prob_id == "stuck_boat" and tool_id in {"rope", "sticks"}:
                    out.append((place_key, prob_id, tool_id))
                elif prob_id == "high_branch" and tool_id in {"sticks", "rope"}:
                    out.append((place_key, prob_id, tool_id))
    return out


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure problem-solving story world.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=["mother", "father"])
    ap.add_argument("--name")
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
    if args.place or args.problem or args.tool:
        combos = [
            c for c in combos
            if (args.place is None or c[0] == args.place)
            and (args.problem is None or c[1] == args.problem)
            and (args.tool is None or c[2] == args.tool)
        ]
    if not combos:
        raise StoryError("No valid adventure matches those choices.")
    place, problem, tool = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = args.helper or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, problem=problem, tool=tool, name=name, gender=gender, helper=helper, trait=trait)


def _solve(world: World, hero: Actor, helper: Actor, problem: Problem, tool: Tool) -> None:
    hero.memes["worry"] += 1
    world.say(f"{hero.id} was a {hero.role} who liked to explore {problem.place}.")
    world.say(f"{hero.pronoun().capitalize()} noticed {problem.label} and saw that {problem.obstacle}.")
    world.say(f"That made {hero.id} think hard about {problem.risk}.")

    world.para()
    world.say(f"{hero.id} softly professed, \"I can do this if I stay calm.\"")
    world.say(f"Then {hero.id} proposed, \"Let's use {tool.label} and solve it together.\"")
    helper.memes["hope"] += 1

    if problem.id in {"blocked_path", "stuck_boat"} and tool.id == "sticks":
        world.say(f"{helper.id} nodded and helped {hero.id} make a careful plan with the {tool.label}.")
    elif problem.id == "lost_map" and tool.id == "lantern":
        world.say(f"The {tool.label} lit the way, and the little path became easy to see.")
    elif problem.id == "lost_map" and tool.id == "rope":
        world.say(f"They tied the {tool.label} to marks on trees so they would not wander away.")
    else:
        world.say(f"Together they used the {tool.label} in a smart way, one careful step at a time.")

    hero.memes["courage"] += 1
    hero.meters[problem.trouble_meter] = 0.0
    hero.meters["progress"] = 1.0

    world.para()
    world.say(f"At last, the plan worked. {hero.id} reached the safe spot and the problem was gone.")
    world.say(f"{hero.id} could nestle in {problem.nestle_place}, and {helper.id} smiled nearby.")
    hero.memes["peace"] += 1


def tell_story(params: StoryParams) -> World:
    world = World()
    problem = PROBLEMS[params.problem]
    tool = TOOLS[params.tool]
    hero = world.add(Actor(id=params.name, type=params.gender, role=params.trait, traits=[params.trait, "adventurous"]))
    helper = world.add(Actor(id=params.helper, type=params.helper, role="helper", traits=["helpful"]))

    hero.meters[problem.trouble_meter] = 1.0
    _solve(world, hero, helper, problem, tool)

    world.facts.update(hero=hero, helper=helper, problem=problem, tool=tool, params=params)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    p: Problem = f["problem"]
    t: Tool = f["tool"]
    h: Actor = f["hero"]
    return [
        f"Write an adventure story where {h.id} uses {t.label} to solve the {p.label}.",
        f"Tell a child-friendly problem-solving tale with the words profess, propose, and nestle.",
        f"Make a short story about a brave child at {p.place} who thinks, proposes a fix, and ends in a cozy nestle.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Actor = f["hero"]
    helper: Actor = f["helper"]
    problem: Problem = f["problem"]
    tool: Tool = f["tool"]
    return [
        QAItem(
            question=f"What problem did {hero.id} need to solve?",
            answer=f"{hero.id} needed to solve the {problem.label} at {problem.place} because {problem.obstacle}.",
        ),
        QAItem(
            question=f"What did {hero.id} propose to use?",
            answer=f"{hero.id} proposed using {tool.label} so they could solve the problem together.",
        ),
        QAItem(
            question=f"Where did {hero.id} nestle at the end?",
            answer=f"At the end, {hero.id} could nestle in {problem.nestle_place} with {helper.id} nearby.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What does profess mean?", answer="To profess something means to say it clearly and honestly."),
        QAItem(question="What does propose mean?", answer="To propose means to suggest an idea or plan."),
        QAItem(question="What does nestle mean?", answer="To nestle means to settle in a cozy, snug way."),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== story qa ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== world qa ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


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
        print("--- trace ---")
        for line in sample.world.trace:
            print(line)
    if qa:
        print()
        print(format_qa(sample))


ASP_RULES = r"""
valid(Place, Problem, Tool) :- place(Place), problem(Problem), tool(Tool), compatible(Place, Problem, Tool).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for p in SETTINGS:
        lines.append(asp.fact("place", p))
    for p, prob in PROBLEMS.items():
        lines.append(asp.fact("problem", p))
        lines.append(asp.fact("problem_place", p, prob.place))
    for t in TOOLS:
        lines.append(asp.fact("tool", t))
    for place, prob, tool in valid_combos():
        lines.append(asp.fact("compatible", place, prob, tool))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/3."))
    clingo_set = set(asp.atoms(model, "valid"))
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and Python valid_combos().")
    print("only in clingo:", sorted(clingo_set - python_set))
    print("only in python:", sorted(python_set - clingo_set))
    return 1


CURATED = [
    StoryParams(place="forest", problem="lost_map", tool="lantern", name="Mia", gender="girl", helper="mother", trait="curious"),
    StoryParams(place="cave", problem="blocked_path", tool="sticks", name="Leo", gender="boy", helper="father", trait="brave"),
    StoryParams(place="harbor", problem="stuck_boat", tool="rope", name="Ava", gender="girl", helper="mother", trait="steady"),
    StoryParams(place="hill", problem="high_branch", tool="rope", name="Finn", gender="boy", helper="father", trait="kind"),
]


def _show_asp() -> None:
    print(asp_program("#show valid/3."))


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        _show_asp()
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show valid/3."))
        print(sorted(set(asp.atoms(model, "valid"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        for i in range(max(args.n * 50, 50)):
            if len(samples) >= args.n:
                break
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
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
