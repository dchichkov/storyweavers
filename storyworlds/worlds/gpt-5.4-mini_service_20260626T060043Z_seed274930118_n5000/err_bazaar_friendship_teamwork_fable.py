#!/usr/bin/env python3
"""
storyworlds/worlds/err_bazaar_friendship_teamwork_fable.py
===========================================================

A tiny fable-like story world about a bazaar, a small err, and the strength
of friendship and teamwork.

Premise:
- Two friends run a little stall in a busy bazaar.
- A small err makes the stall confusing or unfair.
- The friends notice the trouble, speak kindly, and fix it together.
- The ending proves that friendship and teamwork make the bazaar run better.

This world is intentionally small and classical: one setting, one problem, one
turn, one resolution.
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
    partner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "aunt"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "uncle"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def they(self) -> str:
        return "them"


@dataclass
class Setting:
    place: str = "the bazaar"
    ambiance: str = "bright and busy"
    affordance: str = "trade"


@dataclass
class Problem:
    id: str
    title: str
    mess: str
    harm: str
    turns_on: str
    clue: str
    keyword: str = "err"


@dataclass
class Remedy:
    id: str
    title: str
    method: str
    outcome: str
    shares: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.problem: Optional[Problem] = None
        self.remedy: Optional[Remedy] = None
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

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

        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.problem = self.problem
        c.remedy = self.remedy
        c.paragraphs = [[]]
        c.fired = set(self.fired)
        c.facts = dict(self.facts)
        return c


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "bazaar": Setting(place="the bazaar", ambiance="bright and busy", affordance="trade"),
}

PROBLEMS = {
    "err_sign": Problem(
        id="err_sign",
        title="a mistaken sign",
        mess="confusion",
        harm="the prices looked wrong",
        turns_on="the chalked numbers on the sign",
        clue="the sign said one price but meant another",
        keyword="err",
    ),
    "err_basket": Problem(
        id="err_basket",
        title="a mixed-up basket",
        mess="confusion",
        harm="buyers reached for the wrong fruit",
        turns_on="the fruit baskets by the cloth awning",
        clue="the apples and pears had been put in the wrong baskets",
        keyword="err",
    ),
}

REMEDIES = {
    "talk_and_sort": Remedy(
        id="talk_and_sort",
        title="kind talk and sorting together",
        method="speak kindly, sort the goods, and fix the stall",
        outcome="the stall became clear and fair again",
        shares={"talk", "sort", "kindness"},
    ),
    "split_tasks": Remedy(
        id="split_tasks",
        title="dividing the work",
        method="one friend called out prices while the other arranged the goods",
        outcome="the stall moved faster and made fewer mistakes",
        shares={"talk", "work", "teamwork"},
    ),
}

NAMES = ["Mira", "Tobin", "Sana", "Pip", "Lina", "Rafi", "Noor", "Joss"]
TYPES = {"girl", "boy"}
TRAITS = ["kind", "careful", "patient", "brave", "gentle", "steady"]


@dataclass
class StoryParams:
    place: str
    problem: str
    remedy: str
    name_a: str
    type_a: str
    name_b: str
    type_b: str
    trait_a: str
    trait_b: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A bazaar story is valid when a problem is present and the remedy can address it.
problem_ok(P) :- problem(P).
remedy_ok(R) :- remedy(R).

can_fix(P, R) :- problem(P), remedy(R), shares(R, teamwork), shares(R, kindness).
valid_story(Place, P, R) :- setting(Place), problem(P), remedy(R), can_fix(P, R).

#show valid_story/3.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for pid, p in PROBLEMS.items():
        lines.append(asp.fact("problem", pid))
        lines.append(asp.fact("problem_keyword", pid, p.keyword))
    for rid, r in REMEDIES.items():
        lines.append(asp.fact("remedy", rid))
        for s in sorted(r.shares):
            lines.append(asp.fact("shares", rid, s))
    return "\n".join(lines)


def asp_program(show: str = "#show valid_story/3.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_stories())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str, str]]:
    return [("bazaar", pid, rid) for pid in PROBLEMS for rid in REMEDIES]


def reasonableness_check(place: str, problem: Problem, remedy: Remedy) -> bool:
    return place in SETTINGS and problem.keyword == "err" and "teamwork" in remedy.shares


def predict_resolution(world: World, hero_a: Entity, hero_b: Entity, problem: Problem, remedy: Remedy) -> dict:
    sim = world.copy()
    sim.facts["problem_active"] = True
    if "sort" in remedy.shares:
        sim.facts["confusion"] = 0
    if "talk" in remedy.shares:
        sim.facts["friendship"] = 2
    return {
        "fixed": True,
        "calm": sim.facts.get("friendship", 0) >= 1,
    }


def _narrate_opening(world: World, a: Entity, b: Entity) -> None:
    world.say(
        f"At {world.setting.place}, {a.id} and {b.id} ran a little stall side by side."
    )
    world.say(
        f"{a.id} was {a.traits[0]} and {b.id} was {b.traits[0]}; they liked helping each other."
    )


def _narrate_problem(world: World, a: Entity, b: Entity, problem: Problem) -> None:
    world.para()
    world.say(
        f"One day, a small {problem.keyword} slipped into their work."
    )
    world.say(
        f"{problem.clue.capitalize()}, so {problem.harm}."
    )
    a.memes["worry"] = a.memes.get("worry", 0) + 1
    b.memes["worry"] = b.memes.get("worry", 0) + 1
    world.facts["problem_active"] = True


def _narrate_turn(world: World, a: Entity, b: Entity, problem: Problem) -> None:
    world.say(
        f"{a.id} noticed the mistake first, and {b.id} noticed it too."
    )
    world.say(
        f"Instead of blaming anyone, they shared a look and decided to fix the {problem.keyword} together."
    )
    a.memes["friendship"] = a.memes.get("friendship", 0) + 1
    b.memes["friendship"] = b.memes.get("friendship", 0) + 1
    a.memes["teamwork"] = a.memes.get("teamwork", 0) + 1
    b.memes["teamwork"] = b.memes.get("teamwork", 0) + 1


def _narrate_resolution(world: World, a: Entity, b: Entity, problem: Problem, remedy: Remedy) -> None:
    world.para()
    world.say(
        f"They {remedy.method}, and soon {remedy.outcome}."
    )
    world.say(
        f"The bazaar felt fair again, and the shoppers smiled."
    )
    world.say(
        f"At the end, {a.id} and {b.id} stood together beside their neat stall, glad they had listened and helped."
    )
    world.facts["problem_active"] = False
    world.facts["resolved"] = True


def tell(params: StoryParams) -> World:
    world = World(SETTINGS[params.place])
    a = world.add(Entity(
        id=params.name_a,
        kind="character",
        type=params.type_a,
        traits=[params.trait_a],
        meters={"order": 0.0},
        memes={"friendship": 1.0, "teamwork": 1.0},
    ))
    b = world.add(Entity(
        id=params.name_b,
        kind="character",
        type=params.type_b,
        traits=[params.trait_b],
        meters={"order": 0.0},
        memes={"friendship": 1.0, "teamwork": 1.0},
    ))
    problem = PROBLEMS[params.problem]
    remedy = REMEDIES[params.remedy]
    world.problem = problem
    world.remedy = remedy

    _narrate_opening(world, a, b)
    _narrate_problem(world, a, b, problem)
    _narrate_turn(world, a, b, problem)
    _narrate_resolution(world, a, b, problem, remedy)

    world.facts.update(
        a=a,
        b=b,
        problem=problem,
        remedy=remedy,
        place=params.place,
        friendship=True,
        teamwork=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    p = world.facts["problem"]
    r = world.facts["remedy"]
    a = world.facts["a"]
    b = world.facts["b"]
    return [
        f"Write a short fable about {a.id} and {b.id} in a bazaar, where an {p.keyword} causes trouble and teamwork fixes it.",
        f"Tell a gentle story about friendship at the bazaar, ending with {r.title}.",
        f"Write a child-friendly fable in which two friends notice an {p.keyword} and solve it together.",
    ]


def story_qa(world: World) -> list[QAItem]:
    a = world.facts["a"]
    b = world.facts["b"]
    p: Problem = world.facts["problem"]
    r: Remedy = world.facts["remedy"]
    return [
        QAItem(
            question=f"Who were the two friends in the bazaar story?",
            answer=f"The friends were {a.id} and {b.id}. They worked together at the bazaar.",
        ),
        QAItem(
            question=f"What was the small {p.keyword} that caused trouble?",
            answer=f"It was {p.title}, and it made the stall confusing because {p.harm}.",
        ),
        QAItem(
            question="How did the friends fix the problem?",
            answer=f"They used {r.title} and worked together until the stall was neat and fair again.",
        ),
        QAItem(
            question="What changed by the end of the story?",
            answer="The confusion was gone, the stall was clear, and the friends were still kind to each other.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a bazaar?",
            answer="A bazaar is a busy market where people buy and sell things from little stalls.",
        ),
        QAItem(
            question="What is teamwork?",
            answer="Teamwork means people help each other and do a job together.",
        ),
        QAItem(
            question="What is friendship?",
            answer="Friendship is when people care about each other, share, and help each other.",
        ),
        QAItem(
            question="Why is it good to fix an err kindly?",
            answer="It is good because kind talk can keep people calm while they solve the mistake together.",
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
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  problem: {world.problem.id if world.problem else None}")
    lines.append(f"  remedy: {world.remedy.id if world.remedy else None}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small fable world about a bazaar err, friendship, and teamwork.")
    ap.add_argument("--place", choices=SETTINGS.keys(), default="bazaar")
    ap.add_argument("--problem", choices=PROBLEMS.keys())
    ap.add_argument("--remedy", choices=REMEDIES.keys())
    ap.add_argument("--name-a")
    ap.add_argument("--type-a", choices=["girl", "boy"])
    ap.add_argument("--name-b")
    ap.add_argument("--type-b", choices=["girl", "boy"])
    ap.add_argument("--trait-a")
    ap.add_argument("--trait-b")
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
    place = args.place or "bazaar"
    problem = args.problem or rng.choice(list(PROBLEMS.keys()))
    remedy = args.remedy or rng.choice(list(REMEDIES.keys()))
    p = PROBLEMS[problem]
    r = REMEDIES[remedy]
    if not reasonableness_check(place, p, r):
        raise StoryError("No valid bazaar story matches the requested problem/remedy.")
    name_a = args.name_a or rng.choice(NAMES)
    name_b = args.name_b or rng.choice([n for n in NAMES if n != name_a])
    type_a = args.type_a or rng.choice(["girl", "boy"])
    type_b = args.type_b or rng.choice(["girl", "boy"])
    trait_a = args.trait_a or rng.choice(TRAITS)
    trait_b = args.trait_b or rng.choice([t for t in TRAITS if t != trait_a])
    return StoryParams(
        place=place,
        problem=problem,
        remedy=remedy,
        name_a=name_a,
        type_a=type_a,
        name_b=name_b,
        type_b=type_b,
        trait_a=trait_a,
        trait_b=trait_b,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
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


def valid_story_pairs() -> list[tuple]:
    return [("bazaar", pid, rid) for pid in PROBLEMS for rid in REMEDIES]


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible bazaar story combos:\n")
        for row in combos:
            print("  ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        params_list = [
            StoryParams("bazaar", "err_sign", "talk_and_sort", "Mira", "girl", "Tobin", "boy", "kind", "steady"),
            StoryParams("bazaar", "err_basket", "split_tasks", "Sana", "girl", "Rafi", "boy", "patient", "careful"),
        ]
        samples = [generate(p) for p in params_list]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            rng = random.Random(base_seed + i)
            i += 1
            try:
                params = resolve_params(args, rng)
            except StoryError as e:
                print(e)
                return
            params.seed = base_seed + i - 1
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

    for idx, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name_a} and {p.name_b} at the bazaar"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
