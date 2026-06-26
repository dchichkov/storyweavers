#!/usr/bin/env python3
"""
A small storyworld about a bashful actor on a space adventure who finds a happy ending.

Premise:
- A bashful actor wants to perform on a tiny space stage.
- Something about the ship makes the performance hard: a broken spotlight, a stuck visor, or a missing prop.
- A helper or captain notices the problem and offers a simple fix.
- The actor overcomes shyness, performs, and the crew ends happy.

This world keeps the prose concrete and state-driven: emotional memes track bashfulness,
courage, delight, and crew warmth; physical meters track stage readiness, prop condition,
and ship stability.
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

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"   # "character" or "thing"
    label: str = ""
    type: str = ""
    plural: bool = False
    owner: Optional[str] = None
    helper: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def meter(self, key: str) -> float:
        return self.meters.get(key, 0.0)

    def meme(self, key: str) -> float:
        return self.memes.get(key, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Stage:
    place: str = "the tiny starship stage"
    has_spotlight: bool = True
    has_microphone: bool = True
    has_curtain: bool = True


@dataclass
class Problem:
    id: str
    label: str
    issue: str
    fix: str
    physical: str
    emotion: str
    resolution_prop: str


@dataclass
class StoryParams:
    problem: str
    name: str
    gender: str
    captain: str
    seed: Optional[int] = None


class World:
    def __init__(self, stage: Stage) -> None:
        self.stage = stage
        self.entities: dict[str, Entity] = {}
        self.lines: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[tuple] = set()

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.lines[-1].append(text)

    def para(self) -> None:
        if self.lines[-1]:
            self.lines.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.lines if p)

    def copy(self) -> "World":
        import copy
        w = World(copy.deepcopy(self.stage))
        w.entities = copy.deepcopy(self.entities)
        w.lines = [[]]
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

STAGE = Stage()

PROBLEMS = {
    "spotlight": Problem(
        id="spotlight",
        label="spotlight",
        issue="flickered out",
        fix="a fresh power cell",
        physical="dark",
        emotion="nervous",
        resolution_prop="spotlight",
    ),
    "microphone": Problem(
        id="microphone",
        label="microphone",
        issue="stopped humming",
        fix="a taped wire",
        physical="quiet",
        emotion="bashful",
        resolution_prop="microphone",
    ),
    "curtain": Problem(
        id="curtain",
        label="curtain",
        issue="got stuck",
        fix="a careful tug",
        physical="stuck",
        emotion="worried",
        resolution_prop="curtain",
    ),
}

NAMES_GIRL = ["Nova", "Mina", "Luna", "Iris", "Zara", "Ada"]
NAMES_BOY = ["Orion", "Finn", "Jace", "Kai", "Leo", "Niko"]
CAPTAINS = ["captain", "pilot", "commander"]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A problem is available when the stage has a broken feature.
problem(P) :- broken(P).

% A fix is reasonable if it matches the problem.
fixable(P) :- broken(P), has_fix(P).

% Happy ending means the actor performs and the crew cheers.
happy_ending(A, P) :- actor(A), problem(P), solved(P), performed(A).

#show happy_ending/2.
#show fixable/1.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    lines.append(asp.fact("stage", "ship_stage"))
    lines.append(asp.fact("actor_type", "actor"))
    for pid, p in PROBLEMS.items():
        lines.append(asp.fact("problem", pid))
        lines.append(asp.fact("broken", pid))
        lines.append(asp.fact("has_fix", pid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show fixable/1."))
    clingo_fixable = sorted(set(asp.atoms(model, "fixable")))
    python_fixable = [(pid,) for pid in sorted(PROBLEMS)]
    if clingo_fixable == python_fixable:
        print(f"OK: clingo gate matches Python registry ({len(clingo_fixable)} problems).")
        return 0
    print("MISMATCH between clingo and Python registry:")
    print("  clingo:", clingo_fixable)
    print("  python:", python_fixable)
    return 1


# ---------------------------------------------------------------------------
# Simulation helpers
# ---------------------------------------------------------------------------

def build_problem(problem_id: str) -> Problem:
    if problem_id not in PROBLEMS:
        raise StoryError(f"Unknown problem: {problem_id}")
    return PROBLEMS[problem_id]


def _perform(world: World, actor: Entity, problem: Problem, narrate: bool = True) -> None:
    if world.facts.get("solved"):
        return
    if problem.id in world.fired:
        return
    world.fired.add((problem.id, "attempt"))
    actor.memes["bashful"] = max(0.0, actor.memes.get("bashful", 0.0) - 0.5)
    actor.memes["courage"] = actor.memes.get("courage", 0.0) + 1.0
    world.facts["performed"] = True
    if narrate:
        world.say(f"{actor.id} stepped onto the little stage and tried to speak anyway.")


def _solve(world: World, actor: Entity, captain: Entity, problem: Problem, narrate: bool = True) -> None:
    if world.facts.get("solved"):
        return
    world.facts["solved"] = True
    actor.memes["joy"] = actor.memes.get("joy", 0.0) + 1.0
    actor.memes["bashful"] = max(0.0, actor.memes.get("bashful", 0.0) - 1.0)
    captain.memes["warmth"] = captain.memes.get("warmth", 0.0) + 1.0
    world.stage.has_spotlight = True
    world.stage.has_microphone = True
    world.stage.has_curtain = True
    if narrate:
        world.say(
            f"{captain.id} fixed the {problem.label} with {problem.fix}, and the stage felt ready again."
        )


def predict_outcome(world: World, actor: Entity, captain: Entity, problem: Problem) -> bool:
    sim = world.copy()
    _perform(sim, sim.get(actor.id), problem, narrate=False)
    _solve(sim, sim.get(actor.id), sim.get(captain.id), problem, narrate=False)
    return bool(sim.facts.get("solved") and sim.entities[actor.id].memes.get("joy", 0.0) >= THRESHOLD)


# ---------------------------------------------------------------------------
# Narrative
# ---------------------------------------------------------------------------

def intro(world: World, actor: Entity, captain: Entity, problem: Problem) -> None:
    world.say(
        f"{actor.id} was a bashful actor who loved the quiet glow of the ship at night."
    )
    world.say(
        f"{actor.pronoun().capitalize()} wanted to perform for {captain.label}, but the {problem.label} had {problem.issue}."
    )


def tension(world: World, actor: Entity, captain: Entity, problem: Problem) -> None:
    actor.memes["bashful"] = actor.memes.get("bashful", 0.0) + 1.0
    world.say(
        f"The broken {problem.label} made the stage feel {problem.physical}, and {actor.id} went very still."
    )
    if predict_outcome(world, actor, captain, problem):
        world.say(
            f"{captain.id} noticed the worry and said they could make it work together."
        )


def turn(world: World, actor: Entity, captain: Entity, problem: Problem) -> None:
    _solve(world, actor, captain, problem, narrate=True)
    _perform(world, actor, problem, narrate=True)


def ending(world: World, actor: Entity, captain: Entity, problem: Problem) -> None:
    world.say(
        f"In the end, {actor.id} smiled, {captain.id} clapped, and the little ship glowed bright and kind."
    )
    world.say(
        f"The {problem.label} stayed fixed, and the bashful actor finished the night with a happy ending."
    )


def tell(problem: Problem, name: str, gender: str, captain_role: str) -> World:
    world = World(STAGE)
    actor = world.add(
        Entity(
            id=name,
            kind="character",
            type=gender,
            label="actor",
            meters={"stage_ready": 0.0},
            memes={"bashful": 1.5, "hope": 0.5},
        )
    )
    captain = world.add(
        Entity(
            id=captain_role.capitalize(),
            kind="character",
            type="adult",
            label=captain_role,
            meters={"ship_order": 1.0},
            memes={"warmth": 0.5},
        )
    )
    prop = world.add(
        Entity(
            id=problem.id,
            kind="thing",
            label=problem.label,
            owner=actor.id,
            meters={"broken": 1.0},
        )
    )

    world.facts.update(actor=actor, captain=captain, problem=problem, prop=prop)

    intro(world, actor, captain, problem)
    world.para()
    tension(world, actor, captain, problem)
    world.para()
    turn(world, actor, captain, problem)
    world.para()
    ending(world, actor, captain, problem)
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def prompts(world: World) -> list[str]:
    f = world.facts
    actor = f["actor"]
    problem = f["problem"]
    captain = f["captain"]
    return [
        f'Write a short space adventure about a bashful actor named {actor.id} who needs help with a {problem.label}.',
        f"Tell a child-friendly story where {captain.label} helps {actor.id} fix the {problem.label} on a tiny ship stage.",
        f"Write a happy-ending story about an actor, a broken {problem.label}, and a kind repair on a starship.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    actor = f["actor"]
    captain = f["captain"]
    problem = f["problem"]
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"It is about {actor.id}, a bashful actor on a small starship stage, and {captain.label} helps out."
        ),
        QAItem(
            question=f"What was wrong with the {problem.label}?",
            answer=f"The {problem.label} had {problem.issue}, so the stage was not ready at first."
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended happily: {captain.id} fixed the {problem.label}, {actor.id} performed, and everyone felt proud and warm."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an actor?",
            answer="An actor is a person who performs a role in a play, show, or story."
        ),
        QAItem(
            question="What does bashful mean?",
            answer="Bashful means shy or a little nervous around others."
        ),
        QAItem(
            question="What is a happy ending?",
            answer="A happy ending is when the problem gets fixed and the characters finish feeling safe, glad, or proud."
        ),
        QAItem(
            question="What is a space adventure?",
            answer="A space adventure is a story about traveling in space, often with ships, stars, and exciting problems to solve."
        ),
    ]


# ---------------------------------------------------------------------------
# Output helpers
# ---------------------------------------------------------------------------

def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        parts = []
        if meters:
            parts.append(f"meters={meters}")
        if memes:
            parts.append(f"memes={memes}")
        lines.append(f"{e.id} ({e.kind}/{e.type}) {' '.join(parts)}")
    lines.append(f"stage: spotlight={world.stage.has_spotlight} microphone={world.stage.has_microphone} curtain={world.stage.has_curtain}")
    lines.append(f"facts: solved={world.facts.get('solved', False)} performed={world.facts.get('performed', False)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Core interface
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small space-adventure storyworld with a bashful actor and a happy ending.")
    ap.add_argument("--problem", choices=sorted(PROBLEMS))
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--captain", choices=CAPTAINS)
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
    if args.problem:
        problem = build_problem(args.problem)
    else:
        problem = rng.choice(list(PROBLEMS.values()))
    gender = args.gender or rng.choice(["girl", "boy"])
    if gender == "girl":
        name = args.name or rng.choice(NAMES_GIRL)
    else:
        name = args.name or rng.choice(NAMES_BOY)
    captain = args.captain or rng.choice(CAPTAINS)
    return StoryParams(problem=problem.id, name=name, gender=gender, captain=captain)


def generate(params: StoryParams) -> StorySample:
    world = tell(PROBLEMS[params.problem], params.name, params.gender, params.captain)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts(world),
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
# ASP query helpers
# ---------------------------------------------------------------------------

def asp_show_program() -> str:
    return asp_program("#show happy_ending/2.\n#show fixable/1.")


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_show_program())
        return
    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show fixable/1.\n#show happy_ending/2."))
        print("fixable:", sorted(set(asp.atoms(model, "fixable"))))
        print("happy_ending:", sorted(set(asp.atoms(model, "happy_ending"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for i, pid in enumerate(sorted(PROBLEMS)):
            p = StoryParams(
                problem=pid,
                name=NAMES_GIRL[i % len(NAMES_GIRL)],
                gender="girl" if i % 2 == 0 else "boy",
                captain=CAPTAINS[i % len(CAPTAINS)],
                seed=base_seed + i,
            )
            samples.append(generate(p))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            p = resolve_params(args, random.Random(base_seed + i))
            p.seed = base_seed + i
            s = generate(p)
            if s.story not in seen:
                seen.add(s.story)
                samples.append(s)
            i += 1

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
