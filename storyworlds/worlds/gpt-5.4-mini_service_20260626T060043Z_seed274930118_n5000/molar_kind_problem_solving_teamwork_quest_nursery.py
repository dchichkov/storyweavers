#!/usr/bin/env python3
"""
Standalone story world: molar kind problem-solving teamwork quest nursery rhyme.

A small, simulated nursery-rhyme domain about a kind team on a quest to help a
molar with a problem. The story stays state-driven: the team notices a trouble,
tries a gentle fix, cooperates, and ends with a clear change in the world.

Seed words: molar, kind
Features: problem solving, teamwork, quest
Style: nursery rhyme
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
# Story model
# ---------------------------------------------------------------------------

@dataclass
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    partner: Optional[str] = None
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character":
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Place:
    id: str
    label: str
    mood: str
    supports: set[str] = field(default_factory=set)


@dataclass
class Problem:
    id: str
    label: str
    kind: str
    clue: str
    risk: str
    fix_tag: str


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    helps: set[str] = field(default_factory=set)
    covers: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    problem: str
    hero_name: str
    helper_name: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.items: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.lines: list[str] = []
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

    def add(self, ent: Entity) -> Entity:
        if ent.kind == "character":
            self.entities[ent.id] = ent
        else:
            self.items[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid in self.entities:
            return self.entities[eid]
        return self.items[eid]

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
        w = World(self.place)
        w.entities = copy.deepcopy(self.entities)
        w.items = copy.deepcopy(self.items)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

PLACES = {
    "nursery": Place(
        id="nursery",
        label="the nursery",
        mood="soft and bright",
        supports={"quest", "talk", "tool", "help"},
    ),
    "garden": Place(
        id="garden",
        label="the little garden",
        mood="green and warm",
        supports={"quest", "tool", "help"},
    ),
    "moonroom": Place(
        id="moonroom",
        label="the moonlit room",
        mood="quiet and silver",
        supports={"quest", "talk", "help"},
    ),
}

PROBLEMS = {
    "stuck_seed": Problem(
        id="stuck_seed",
        label="a stuck seed",
        kind="tiny trouble",
        clue="a tiny seed was stuck where it should not be",
        risk="it could stay stuck and make the molar grumpy",
        fix_tag="twist",
    ),
    "muddy_sparkle": Problem(
        id="muddy_sparkle",
        label="a muddy sparkle",
        kind="messy trouble",
        clue="a muddy speck had landed on the molar's shining face",
        risk="it could keep the molar from feeling neat and clean",
        fix_tag="wipe",
    ),
    "wobbly_molar": Problem(
        id="wobbly_molar",
        label="a wobbly molar",
        kind="gentle trouble",
        clue="the molar was wobbly and needed very kind care",
        risk="it could ache if nobody helped carefully",
        fix_tag="steady",
    ),
}

TOOLS = {
    "tiny_brush": Tool(
        id="tiny_brush",
        label="a tiny brush",
        phrase="a tiny brush with a bright blue handle",
        helps={"wipe", "steady"},
        covers={"small"},
    ),
    "mint_cup": Tool(
        id="mint_cup",
        label="a mint cup",
        phrase="a little cup of minty water",
        helps={"wipe"},
        covers={"fresh"},
    ),
    "gentle_string": Tool(
        id="gentle_string",
        label="gentle string",
        phrase="a soft piece of gentle string",
        helps={"twist"},
        covers={"reach"},
    ),
    "storybook_map": Tool(
        id="storybook_map",
        label="a storybook map",
        phrase="a storybook map with a dotted path",
        helps={"quest"},
        covers={"path"},
    ),
}

NAMES = ["Mia", "Noah", "Luna", "Theo", "Ivy", "Finn", "Ava", "Leo"]
HELPER_NAMES = ["Bee", "Pip", "June", "Dot", "Tess", "Milo"]
TRAITS = ["kind", "brave", "cheerful", "gentle", "patient"]


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------

def valid_combo(place: Place, problem: Problem) -> bool:
    if place.id == "nursery":
        return True
    if place.id == "garden":
        return problem.id in {"stuck_seed", "muddy_sparkle"}
    if place.id == "moonroom":
        return problem.id in {"wobbly_molar", "muddy_sparkle"}
    return False


def select_tool(problem: Problem) -> Optional[Tool]:
    for tool in TOOLS.values():
        if problem.fix_tag in tool.helps:
            return tool
    return None


def explain_rejection(place: Place, problem: Problem) -> str:
    return (
        f"(No story: {problem.label} does not fit well in {place.label} for a "
        f"gentle nursery-rhyme quest.)"
    )


# ---------------------------------------------------------------------------
# Simulation
# ---------------------------------------------------------------------------

def predict_fix(world: World, problem: Problem, tool: Tool) -> dict[str, object]:
    clone = world.copy()
    target = clone.get("molar")
    helper = clone.get("helper")
    target.meters["trouble"] = target.meters.get("trouble", 0.0) + 1.0
    if problem.fix_tag in tool.helps:
        target.meters["trouble"] = max(0.0, target.meters["trouble"] - 1.0)
        helper.memes["pride"] = helper.memes.get("pride", 0.0) + 1.0
    return {
        "resolved": target.meters.get("trouble", 0.0) < 1.0,
        "helper_pride": helper.memes.get("pride", 0.0),
    }


def tell(params: StoryParams) -> World:
    place = PLACES[params.place]
    problem = PROBLEMS[params.problem]
    world = World(place)

    hero = world.add(Entity(id="hero", kind="character", label=params.hero_name, role="child"))
    helper = world.add(Entity(id="helper", kind="character", label=params.helper_name, role="friend"))
    molar = world.add(Entity(id="molar", kind="thing", label="molar", role="tooth", owner=hero.id))
    quest = world.add(Entity(id="quest", kind="thing", label="quest", role="quest"))
    tool = select_tool(problem)
    if tool is None:
        raise StoryError("No tool can solve this problem kindly.")

    world.facts.update(hero=hero, helper=helper, molar=molar, quest=quest, problem=problem, tool=tool)

    # Act 1
    world.say(f"In {place.label}, under the {place.mood} glow, {hero.label} was a {hero.label and 'kind'} child on a little quest.")
    world.say(f"They found the {molar.label} and noticed {problem.clue}.")
    world.say(f"{helper.label} came along, and together they said, 'Let's think and help with care.'")

    # Act 2
    world.para()
    world.say(f"The quest needed a plan, so {hero.label} and {helper.label} shared the work.")
    world.say(f"They carried {tool.phrase} and walked the dotted path like a soft nursery rhyme.")
    world.say(f"One held the light while the other held still, because teamwork makes small steps easier.")

    # Act 3
    pred = predict_fix(world, problem, tool)
    world.para()
    if pred["resolved"]:
        molar.meters["trouble"] = 0.0
        hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1.0
        helper.memes["pride"] = helper.memes.get("pride", 0.0) + 1.0
        world.say(f"With {tool.label}, they helped the {molar.label} at last.")
        if problem.fix_tag == "twist":
            world.say(f"They gently twisted the tiny trouble free, and the {molar.label} felt much better.")
        elif problem.fix_tag == "wipe":
            world.say(f"They softly wiped the speck away, and the {molar.label} sparkled clean again.")
        else:
            world.say(f"They steadied the wobble with kind care, and the {molar.label} stood calm and snug.")
        world.say(f"Then {hero.label} and {helper.label} smiled, because their teamwork had done the trick.")
    else:
        raise StoryError("The chosen tool did not solve the problem.")

    world.facts["resolved"] = True
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    p = world.facts
    prob: Problem = p["problem"]
    return [
        f"Write a short nursery-rhyme story about a kind child and a helper on a quest to fix a {prob.kind} involving a molar.",
        f"Tell a gentle story where teamwork solves {prob.label} in {world.place.label}.",
        f"Write a child-friendly rhyme about a {p['hero'].label} and {p['helper'].label} helping a molar feel better.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.facts["hero"]
    helper = world.facts["helper"]
    molar = world.facts["molar"]
    problem: Problem = world.facts["problem"]
    tool: Tool = world.facts["tool"]
    return [
        QAItem(
            question=f"Who went on the quest in {world.place.label}?",
            answer=f"{hero.label} and {helper.label} went on the quest together.",
        ),
        QAItem(
            question=f"What trouble did the molar have?",
            answer=f"The molar had {problem.label}, which meant {problem.clue}.",
        ),
        QAItem(
            question=f"What tool helped fix the molar?",
            answer=f"{tool.label} helped the team solve the problem with gentle care.",
        ),
        QAItem(
            question=f"How did the story end for the molar?",
            answer=f"The {molar.label} ended calm and better, because the kind team solved the trouble.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a molar?",
            answer="A molar is a back tooth that helps chew food.",
        ),
        QAItem(
            question="What does kind mean?",
            answer="Kind means gentle, caring, and friendly.",
        ),
        QAItem(
            question="What is teamwork?",
            answer="Teamwork means people work together to do something better than one person could alone.",
        ),
        QAItem(
            question="What is a quest?",
            answer="A quest is a journey to find something or solve a problem.",
        ),
    ]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
place(nursery).
place(garden).
place(moonroom).

problem(stuck_seed).
problem(muddy_sparkle).
problem(wobbly_molar).

tool(tiny_brush).
tool(mint_cup).
tool(gentle_string).
tool(storybook_map).

fits(nursery, stuck_seed).
fits(nursery, muddy_sparkle).
fits(nursery, wobbly_molar).
fits(garden, stuck_seed).
fits(garden, muddy_sparkle).
fits(moonroom, wobbly_molar).
fits(moonroom, muddy_sparkle).

fixes(tiny_brush, wipe).
fixes(mint_cup, wipe).
fixes(gentle_string, twist).
fixes(storybook_map, quest).

problem_fix(stuck_seed, twist).
problem_fix(muddy_sparkle, wipe).
problem_fix(wobbly_molar, steady).

valid(Place, Problem) :- fits(Place, Problem).

supports_fix(Tool, Problem) :- fixes(Tool, Fix), problem_fix(Problem, Fix).
valid_story(Place, Problem, Tool) :- valid(Place, Problem), supports_fix(Tool, Problem).

#show valid/2.
#show valid_story/3.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for pid in PROBLEMS:
        lines.append(asp.fact("problem", pid))
    for tid in TOOLS:
        lines.append(asp.fact("tool", tid))
    for place in PLACES.values():
        for pid in PROBLEMS:
            if valid_combo(place, PROBLEMS[pid]):
                lines.append(asp.fact("fits", place.id, pid))
    for tid, tool in TOOLS.items():
        for tag in tool.helps:
            lines.append(asp.fact("fixes", tid, tag))
    for pid, prob in PROBLEMS.items():
        lines.append(asp.fact("problem_fix", pid, prob.fix_tag))
    return "\n".join(lines)


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = {(p, pr) for p in PLACES for pr in PROBLEMS if valid_combo(PLACES[p], PROBLEMS[pr])}
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP gate matches Python ({len(py)} valid pairs).")
        return 0
    print("MISMATCH between ASP and Python:")
    print("only in python:", sorted(py - cl))
    print("only in ASP:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Nursery-rhyme story world: a kind molar quest.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--problem", choices=PROBLEMS)
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    valid = [(p, pr) for p in PLACES for pr in PROBLEMS if valid_combo(PLACES[p], PROBLEMS[pr])]
    if args.place and args.problem and not valid_combo(PLACES[args.place], PROBLEMS[args.problem]):
        raise StoryError(explain_rejection(PLACES[args.place], PROBLEMS[args.problem]))
    candidates = [
        (p, pr) for p, pr in valid
        if (args.place is None or p == args.place) and (args.problem is None or pr == args.problem)
    ]
    if not candidates:
        raise StoryError("(No valid combination matches the given options.)")
    place, problem = rng.choice(sorted(candidates))
    return StoryParams(
        place=place,
        problem=problem,
        hero_name=rng.choice(NAMES),
        helper_name=rng.choice(HELPER_NAMES),
    )


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


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    lines.append(f"place: {world.place.label}")
    for ent in list(world.entities.values()) + list(world.items.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        lines.append(f"{ent.id}: kind={ent.kind} label={ent.label} meters={meters} memes={memes}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for p in sample.prompts:
        out.append(p)
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
    StoryParams(place="nursery", problem="stuck_seed", hero_name="Mia", helper_name="Dot"),
    StoryParams(place="garden", problem="muddy_sparkle", hero_name="Leo", helper_name="Pip"),
    StoryParams(place="moonroom", problem="wobbly_molar", hero_name="Ava", helper_name="Bee"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program())
        print(f"{len(asp.atoms(model, 'valid'))} valid pairs")
        return

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        base_seed = args.seed if args.seed is not None else random.randrange(2**31)
        samples: list[StorySample] = []
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1

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
            header = f"### {p.hero_name} and {p.helper_name}: {p.problem} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
