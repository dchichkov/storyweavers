#!/usr/bin/env python3
"""
storyworlds/worlds/ramen_cant_midget_surprise_lesson_learned_problem.py
========================================================================

A small fairy-tale storyworld about a tiny castle kitchen, a bowl of ramen,
a canting bridge, and a surprising lesson about problem solving.

The seed tale behind this world:
---
In a little hill kingdom, a tiny midget miller named Pip lived near a crooked
wooden bridge that cant'ed over a stream. Pip loved making ramen in a brass pot,
but one morning the royal soup cart tipped and spilled noodles into the stream.

Pip was surprised, because the bridge bent, the water rushed, and the noodles
started floating away. The miller could have pouted, but instead he studied the
problem, gathered a ladle, a basket, and a reed rope, and learned that a small
kindness can solve a big mess.

He crossed the canting bridge, fished out the noodles, and shared the rescued
ramen with the whole village.
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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "queen", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "king", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    name: str
    details: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Problem:
    id: str
    noun: str
    verb: str
    description: str
    risk: str
    cause: str
    surprise: str
    lesson: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Solution:
    id: str
    tool: str
    phrase: str
    action: str
    result: str
    covers: set[str] = field(default_factory=set)
    helps: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting):
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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "hill_castle": Setting(
        name="the hill castle",
        details="A crooked bridge leaned over a bright stream below the castle wall.",
        affords={"spill", "cross", "share"},
    ),
    "sunny_village": Setting(
        name="the sunny village green",
        details="A little market path curved past flower carts and a well.",
        affords={"spill", "cross", "share"},
    ),
}

PROBLEMS = {
    "noodle_spill": Problem(
        id="noodle_spill",
        noun="ramen",
        verb="spill",
        description="a bowl of ramen tipped into the stream",
        risk="the noodles would float away",
        cause="the canting bridge shivered when the cart rolled over it",
        surprise="the soup splashed in a silver arc",
        lesson="small hands can still solve a big problem",
        tags={"ramen", "surprise", "lesson", "problem"},
    ),
    "broken_bridge": Problem(
        id="broken_bridge",
        noun="bridge",
        verb="cant",
        description="the bridge leaned so sharply that one side dipped low",
        risk="a person could wobble and drop what they carried",
        cause="a loose rope had slipped from the bridge post",
        surprise="the bridge gave a sudden little sway",
        lesson="slow steps and teamwork can steady a shaky path",
        tags={"cant", "surprise", "problem"},
    ),
    "lost_ladle": Problem(
        id="lost_ladle",
        noun="ladle",
        verb="lose",
        description="the soup ladle fell into the grass",
        risk="without a ladle, the ramen could not be served",
        cause="someone set it down beside the basket and forgot it",
        surprise="the shiny handle vanished into the clover",
        lesson="looking carefully can turn a mess into a fix",
        tags={"lesson", "problem"},
    ),
}

SOLUTIONS = {
    "reed_rope": Solution(
        id="reed_rope",
        tool="a reed rope",
        phrase="a long reed rope",
        action="tie the basket to the bridge rail",
        result="the basket could be pulled back safely",
        covers={"cross"},
        helps={"ramen", "problem"},
    ),
    "ladle_basket": Solution(
        id="ladle_basket",
        tool="a ladle and basket",
        phrase="a basket and a silver ladle",
        action="scoop the ramen from the stream",
        result="the noodles came home one warm bite at a time",
        covers={"spill"},
        helps={"ramen", "problem"},
    ),
    "tea_cloth": Solution(
        id="tea_cloth",
        tool="a tea cloth",
        phrase="a clean tea cloth",
        action="wrap the bowl so it would not tip again",
        result="the soup stayed tucked safely inside",
        covers={"spill"},
        helps={"surprise"},
    ),
}

# Fairy-tale flavored names and roles.
HERO_NAMES = ["Pip", "Milo", "Tia", "Nina", "Gus", "Wren"]
HELPER_NAMES = ["the baker", "the queen", "the miller", "the cook", "the lantern man"]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
problem(P) :- problem_kind(P).
surprise(P) :- problem_kind(P), surprise_kind(P).
lesson(P) :- problem_kind(P), lesson_kind(P).

can_solve(P, S) :- problem_kind(P), solution(S), solves(S, P).
valid_story(Setting, P, S) :- setting(Setting), problem_kind(P), solution(S),
                              affords(Setting, P), solves(S, P).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for pid, p in PROBLEMS.items():
        lines.append(asp.fact("problem_kind", pid))
        if "surprise" in p.tags:
            lines.append(asp.fact("surprise_kind", pid))
        if "lesson" in p.tags:
            lines.append(asp.fact("lesson_kind", pid))
        for t in sorted(p.tags):
            lines.append(asp.fact("tag", pid, t))
    for sid, s in SOLUTIONS.items():
        lines.append(asp.fact("solution", sid))
        for h in sorted(s.helps):
            lines.append(asp.fact("helps", sid, h))
        for c in sorted(s.covers):
            lines.append(asp.fact("covers", sid, c))
        for p in sorted(PROBLEMS):
            if p in s.helps:
                lines.append(asp.fact("solves", sid, p))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    python_set = set(valid_combos())
    asp_set = set(asp_valid_stories())
    # Convert valid_story(Setting, P, S) to same shape as python combos with chosen solution
    asp_pairs = {(a, b, c) for (a, b, c) in asp_set}
    if python_set == asp_pairs:
        print(f"OK: clingo gate matches valid_combos() ({len(python_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("python:", sorted(python_set - asp_pairs))
    print("asp:", sorted(asp_pairs - python_set))
    return 1


# ---------------------------------------------------------------------------
# Story parameters
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    setting: str
    problem: str
    solution: str
    name: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for pid, p in PROBLEMS.items():
            if p.id in {"noodle_spill", "broken_bridge", "lost_ladle"}:
                for sol_id, sol in SOLUTIONS.items():
                    if pid == "noodle_spill" and sol_id in {"reed_rope", "ladle_basket", "tea_cloth"}:
                        combos.append((sid, pid, sol_id))
                    elif pid == "broken_bridge" and sol_id in {"reed_rope"}:
                        combos.append((sid, pid, sol_id))
                    elif pid == "lost_ladle" and sol_id in {"ladle_basket"}:
                        combos.append((sid, pid, sol_id))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy-tale storyworld: ramen, cant, midget, surprise, lesson learned, problem solving.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--solution", choices=SOLUTIONS)
    ap.add_argument("--name")
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
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.problem is None or c[1] == args.problem)
              and (args.solution is None or c[2] == args.solution)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, problem, solution = rng.choice(sorted(combos))
    name = args.name or rng.choice(HERO_NAMES)
    return StoryParams(setting=setting, problem=problem, solution=solution, name=name)


# ---------------------------------------------------------------------------
# Story generation
# ---------------------------------------------------------------------------

def _title_case(s: str) -> str:
    return s[0].upper() + s[1:] if s else s


def tell(params: StoryParams) -> World:
    world = World(SETTINGS[params.setting])
    hero = world.add(Entity(id=params.name, kind="character", type="midget", label=params.name))
    helper = world.add(Entity(id="helper", kind="character", type="queen", label="the queen"))
    problem = PROBLEMS[params.problem]
    solution = SOLUTIONS[params.solution]

    hero.memes["curiosity"] = 1
    hero.memes["hope"] = 1

    # Act 1
    world.say(
        f"Once upon a time, a tiny midget named {hero.id} lived near {world.setting.name}."
    )
    world.say(
        f"{world.setting.details} {hero.id} loved the smell of ramen bubbling in a brass pot."
    )
    world.say(
        f"One bright morning, {hero.id} found {problem.description}."
    )

    # Act 2
    world.para()
    hero.memes["surprise"] = 1
    world.say(
        f"{_title_case(hero.id)} blinked in surprise. {problem.surprise.capitalize()}, and {problem.cause}."
    )
    world.say(
        f"The little midget could not just say cant and walk away, because {problem.risk}."
    )
    hero.memes["problem"] = 1

    # Act 3
    world.para()
    world.say(
        f"Then {hero.id} remembered a lesson learned from the wise folks of the hill: {problem.lesson}."
    )
    world.say(
        f"So {hero.id} gathered {solution.phrase}, chose to {solution.action}, and worked carefully with {helper.label}."
    )
    hero.memes["problem_solving"] = 1
    world.say(
        f"At last, {solution.result}. The ramen was safe again, and the village shared a warm bowl together."
    )
    hero.memes["joy"] = 1
    world.facts.update(hero=hero, problem=problem, solution=solution, helper=helper, setting=world.setting)
    return world


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


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a fairy-tale story for a young child that includes ramen, a canting bridge, and a surprise.',
        f'Write a gentle story about a tiny midget named {f["hero"].id} who solves a problem with ramen.',
        'Tell a child-facing fairy tale where a small problem becomes a lesson learned through problem solving.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    problem = f["problem"]
    solution = f["solution"]
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about a tiny midget named {hero.id} who lived near {world.setting.name}.",
        ),
        QAItem(
            question=f"What surprised {hero.id} in the story?",
            answer=f"{hero.id} was surprised when {problem.description}.",
        ),
        QAItem(
            question=f"What did {hero.id} use to solve the problem?",
            answer=f"{hero.id} used {solution.phrase} and careful work to solve the problem.",
        ),
        QAItem(
            question=f"What lesson was learned?",
            answer=f"The story learned that {problem.lesson}.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is ramen?",
            answer="Ramen is a warm noodle soup, often served in a bowl with broth and noodles.",
        ),
        QAItem(
            question="What does cant mean in this story?",
            answer="Here, cant means a bridge or path leaning at an angle instead of standing straight.",
        ),
        QAItem(
            question="What is a problem?",
            answer="A problem is something that is wrong or tricky and needs a solution.",
        ),
        QAItem(
            question="What does problem solving mean?",
            answer="Problem solving means thinking carefully and trying different safe ideas until something works.",
        ),
        QAItem(
            question="What is a surprise?",
            answer="A surprise is something unexpected that makes a person blink, gasp, or smile.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== (3) World knowledge ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(f"  {e.id:10} ({e.kind}/{e.type}) memes={dict(e.memes)} meters={dict(e.meters)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

CURATED = [
    StoryParams(setting="hill_castle", problem="noodle_spill", solution="ladle_basket", name="Pip"),
    StoryParams(setting="hill_castle", problem="broken_bridge", solution="reed_rope", name="Milo"),
    StoryParams(setting="sunny_village", problem="lost_ladle", solution="ladle_basket", name="Tia"),
]


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
        stories = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(stories)} compatible stories:")
        for row in stories:
            print(" ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.problem} at {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
