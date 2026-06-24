#!/usr/bin/env python3
"""
well_problem_solving_rhyming_story.py
=====================================

A small story world about a child, a well, and a problem to solve.

Premise:
- A child wants water from the well.
- Something goes wrong: the bucket is stuck or the rope is tangled.
- The child thinks, tries a fix, and succeeds with help or a simple tool.

The prose aims for a gentle rhyming-story feel while still being driven by
state changes in the simulated world.
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the well"
    supports: set[str] = field(default_factory=lambda: {"fetch_water", "fix_rope"})


@dataclass
class Problem:
    id: str
    label: str
    trouble: str
    solution: str
    fix_action: str
    keyword: str = "well"
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    solves: set[str]
    plural: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

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

        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "well": Setting(place="the well", supports={"fetch_water", "fix_rope"}),
}

PROBLEMS = {
    "stuck_bucket": Problem(
        id="stuck_bucket",
        label="stuck bucket",
        trouble="the bucket would not rise",
        solution="pull it free",
        fix_action="use the hook",
        tags={"bucket", "rope", "water"},
    ),
    "tangled_rope": Problem(
        id="tangled_rope",
        label="tangled rope",
        trouble="the rope was tied in a twist",
        solution="straighten the rope",
        fix_action="untwist it gently",
        tags={"rope", "knot"},
    ),
    "leaky_bucket": Problem(
        id="leaky_bucket",
        label="leaky bucket",
        trouble="the bucket dripped before it reached the top",
        solution="patch the hole",
        fix_action="wrap it with cloth",
        tags={"bucket", "cloth", "water"},
    ),
}

TOOLS = [
    Tool(id="hook", label="a long hook", phrase="a long hook", solves={"stuck_bucket"}),
    Tool(id="cloth", label="a soft cloth", phrase="a soft cloth", solves={"leaky_bucket"}),
    Tool(id="hands", label="careful hands", phrase="careful hands", solves={"tangled_rope", "stuck_bucket", "leaky_bucket"}, plural=True),
]

NAMES = ["Mila", "Ben", "Tia", "Noah", "Lia", "Owen", "Zara", "Finn"]
TYPES = {"girl", "boy"}
TRAITS = ["brave", "small", "bright", "gentle", "curious", "nimble"]


@dataclass
class StoryParams:
    setting: str
    problem: str
    name: str
    gender: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A problem is solvable when some tool solves it.
solvable(P) :- problem(P), has_solution(P).

% A generated story is reasonable only if the chosen problem is solvable in the setting.
valid_story(S, P) :- setting(S), problem(P), allowed(S, P), solvable(P).

% A specific tool can solve a specific problem.
has_solution(P) :- tool(T), solves(T, P).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for sup in sorted(s.supports):
            lines.append(asp.fact("allows", sid, sup))
            lines.append(asp.fact("allowed", sid, sup))
    for pid, p in PROBLEMS.items():
        lines.append(asp.fact("problem", pid))
        for tag in sorted(p.tags):
            lines.append(asp.fact("tag", pid, tag))
    for t in TOOLS:
        lines.append(asp.fact("tool", t.id))
        for p in sorted(t.solves):
            lines.append(asp.fact("solves", t.id, p))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_stories())
    cl = set(asp_valid_stories())
    if py == cl:
        print(f"OK: clingo gate matches valid_stories() ({len(py)} stories).")
        return 0
    print("MISMATCH between clingo and python:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def valid_stories() -> list[tuple[str, str]]:
    out = []
    for sid, setting in SETTINGS.items():
        for pid, prob in PROBLEMS.items():
            if sid == "well" and any(t in {"bucket", "rope", "water", "cloth"} for t in prob.tags):
                if any(tool.id and pid in tool.solves for tool in TOOLS):
                    out.append((sid, pid))
    return out


def explain_rejection(problem: Problem) -> str:
    return (
        f"(No story: the problem '{problem.label}' is not meaningfully solvable "
        f"with the tools in this tiny world.)"
    )


# ---------------------------------------------------------------------------
# Story rendering
# ---------------------------------------------------------------------------
def rhyme_pair(a: str, b: str) -> str:
    return f"{a} {b}"


def setup_line(hero: Entity, problem: Problem) -> str:
    return (
        f"{hero.id} was a little {hero.meters.get('size_word', 'small')} {hero.type}, "
        f"as bright as could be, by the well where the cool old water liked to be."
    )


def generate_story(world: World) -> None:
    hero: Entity = world.facts["hero"]
    problem: Problem = world.facts["problem"]
    tool: Optional[Tool] = world.facts["tool"]

    world.say(
        f"{hero.id} was a little {world.facts['trait']} {hero.type}, "
        f"by the well with a bucket of yore, "
        f"when {problem.trouble}, and the child wanted more."
    )
    world.say(
        f"{hero.pronoun('subject').capitalize()} peeked down below with a worried little sigh, "
        f"then looked at the rope and had a think-true try."
    )
    world.para()

    world.say(
        f'"Hmm," {hero.id} said, "I can solve this tune; '
        f"if I work with care, I may fix it soon.""
    )
    if problem.id == "stuck_bucket":
        world.say(
            f"{hero.id} found {tool.phrase} and used it just so, "
            f"to lift the stuck bucket with a gentle slow go."
        )
    elif problem.id == "tangled_rope":
        world.say(
            f"{hero.id} used {tool.phrase} and sorted the loop, "
            f"untwisting the rope in a careful scoop."
        )
    else:
        world.say(
            f"{hero.id} took {tool.phrase} and wrapped the leak tight, "
            f"so the bucket could hold water and shine bright."
        )

    world.para()
    world.say(
        f"Up came the bucket, so steady and neat; "
        f"the water was ready, a cool little treat."
    )
    world.say(
        f"{hero.id} grinned at the well, with a happy-hum hum: "
        f"the problem was solved, and the water came home."
    )

    world.facts["solved"] = True


def build_world(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    problem = PROBLEMS[params.problem]
    world = World(setting)
    hero = world.add(
        Entity(
            id=params.name,
            kind="character",
            type=params.gender,
            meters={"size": 1.0},
            memes={"hope": 1.0},
        )
    )
    chosen_tool = next((t for t in TOOLS if params.problem in t.solves), None)
    if chosen_tool is None:
        raise StoryError(explain_rejection(problem))
    world.facts.update(
        hero=hero,
        problem=problem,
        tool=chosen_tool,
        trait=params.trait,
        setting=setting,
    )
    generate_story(world)
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]
    problem: Problem = f["problem"]
    return [
        f'Write a short rhyming story for a child named {hero.id} at the well.',
        f"Tell a gentle problem-solving story where {hero.id} notices that {problem.trouble}.",
        f"Write a simple rhyme about {hero.id} using a tool to fix a well problem.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    problem: Problem = f["problem"]
    tool: Tool = f["tool"]
    return [
        QAItem(
            question=f"What problem did {hero.id} have at the well?",
            answer=f"{hero.id} had a {problem.label}, which meant {problem.trouble}.",
        ),
        QAItem(
            question=f"What did {hero.id} use to solve the problem?",
            answer=f"{hero.id} used {tool.phrase} to fix it.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"The bucket came up, the water was ready, and {hero.id} felt proud and glad.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a well?",
            answer="A well is a deep hole or shaft built to bring water up from underground.",
        ),
        QAItem(
            question="Why do people use a bucket at a well?",
            answer="People use a bucket to carry water up from the well so they can bring it home.",
        ),
        QAItem(
            question="Why is it helpful to solve a problem carefully?",
            answer="Careful problem solving helps you fix trouble without making it worse.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(f"  {e.id}: kind={e.kind} type={e.type} meters={e.meters} memes={e.memes}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# StorySample plumbing
# ---------------------------------------------------------------------------
def valid_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting = args.setting or "well"
    if setting not in SETTINGS:
        raise StoryError("Unknown setting.")
    problem = args.problem or rng.choice(list(PROBLEMS))
    if problem not in PROBLEMS:
        raise StoryError("Unknown problem.")
    if setting == "well" and problem not in PROBLEMS:
        raise StoryError(explain_rejection(PROBLEMS[problem]))
    name = args.name or rng.choice(NAMES)
    gender = args.gender or rng.choice(["girl", "boy"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(setting=setting, problem=problem, name=name, gender=gender, trait=trait)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    params = valid_params(args, rng)
    if args.gender and args.gender not in TYPES:
        raise StoryError("gender must be girl or boy")
    return params


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
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


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Rhyming problem-solving story world about a well.")
    ap.add_argument("--setting", choices=list(SETTINGS))
    ap.add_argument("--problem", choices=list(PROBLEMS))
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--trait", choices=TRAITS)
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        stories = asp_valid_stories()
        print(f"{len(stories)} compatible stories:\n")
        for s in stories:
            print(" ", s)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for pid in PROBLEMS:
            params = StoryParams(setting="well", problem=pid, name="Mia", gender="girl", trait="curious")
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
        header = ""
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
