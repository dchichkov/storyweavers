#!/usr/bin/env python3
"""
A small storyworld about a humorous bee who solves a problem on a tiny adventure.

The bee's day starts with a snag: the path to the best flowers is blocked or a
needed item is missing. The bee notices, experiments, asks for help, and finds a
clever fix. The story is driven by the world state so the ending proves what
changed.
"""

from __future__ import annotations

import argparse
import copy
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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"bee"}:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    outside: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Problem:
    id: str
    noun: str
    verb: str
    hint: str
    risk: str
    fix_need: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Solution:
    id: str
    label: str
    prep: str
    result: str
    helps: set[str]
    requires: set[str]
    plural: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.problem: str = ""

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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.problem = self.problem
        return clone


def story_style(word: str) -> str:
    return f"humorus {word}"


SETTINGS = {
    "garden": Setting(place="the garden", outside=True, affords={"pollen", "path"}),
    "meadow": Setting(place="the meadow", outside=True, affords={"pollen", "path"}),
    "orchard": Setting(place="the orchard", outside=True, affords={"path"}),
}

PROBLEMS = {
    "sticky_path": Problem(
        id="sticky_path",
        noun="sticky sap",
        verb="get across the sticky sap",
        hint="the shiny path was blocked by sticky sap",
        risk="it would trap tiny feet and slow the bee down",
        fix_need="something small to step on",
        keyword="sap",
        tags={"sticky", "path"},
    ),
    "low_flower": Problem(
        id="low_flower",
        noun="a low flower",
        verb="reach the low flower",
        hint="the sweetest flower was just a little too low",
        risk="the bee could not reach the pollen",
        fix_need="something to lift the bee up",
        keyword="flower",
        tags={"flower", "pollen"},
    ),
    "windy_gap": Problem(
        id="windy_gap",
        noun="a windy gap",
        verb="cross the windy gap",
        hint="a gusty gap yawned between two patches of clover",
        risk="the bee might wobble and lose its way",
        fix_need="something steady to bridge the gap",
        keyword="gap",
        tags={"wind", "path"},
    ),
}

SOLUTIONS = [
    Solution(
        id="leaf_bridge",
        label="a flat leaf bridge",
        prep="lay down a flat leaf",
        result="the bee could walk across safely",
        helps={"sticky_path", "windy_gap"},
        requires={"path"},
    ),
    Solution(
        id="step_stone",
        label="a pebble stepping stone",
        prep="roll a smooth pebble into place",
        result="the bee could hop over the mess",
        helps={"sticky_path"},
        requires={"path"},
    ),
    Solution(
        id="ladder_blade",
        label="a grass-blade ladder",
        prep="tie together two grass blades",
        result="the bee could climb up to the pollen",
        helps={"low_flower"},
        requires={"pollen"},
    ),
]


BEE_NAMES = ["Buzz", "Milo", "Pip", "Luna", "Nico", "Zia"]


@dataclass
class StoryParams:
    setting: str
    problem: str
    bee_name: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for pid, prob in PROBLEMS.items():
            if any(sol for sol in SOLUTIONS if pid in sol.helps and sol.requires <= setting.affords):
                out.append((place, pid))
    return out


def reasonableness_gate(setting: Setting, problem: Problem) -> bool:
    return any(sol for sol in SOLUTIONS if problem.id in sol.helps and sol.requires <= setting.affords)


ASP_RULES = r"""
setting(garden). setting(meadow). setting(orchard).
affords(garden,path). affords(garden,pollen).
affords(meadow,path). affords(meadow,pollen).
affords(orchard,path).

problem(sticky_path). problem(low_flower). problem(windy_gap).
helps(leaf_bridge,sticky_path). helps(leaf_bridge,windy_gap).
helps(step_stone,sticky_path).
helps(ladder_blade,low_flower).
requires(leaf_bridge,path). requires(step_stone,path).
requires(ladder_blade,pollen).

valid(Place,Prob) :- setting(Place), problem(Prob),
    affords(Place,Need), requires(Sol,Need), helps(Sol,Prob).
#show valid/2.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place, setting in SETTINGS.items():
        lines.append(asp.fact("setting", place))
        for a in sorted(setting.affords):
            lines.append(asp.fact("affords", place, a))
    for pid in PROBLEMS:
        lines.append(asp.fact("problem", pid))
    for sol in SOLUTIONS:
        lines.append(asp.fact("solution", sol.id))
        for p in sorted(sol.helps):
            lines.append(asp.fact("helps", sol.id, p))
        for r in sorted(sol.requires):
            lines.append(asp.fact("requires", sol.id, r))
    return "\n".join(lines)


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_valid_combos() -> list[tuple[str, str]]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python.")
    if py - cl:
        print("only python:", sorted(py - cl))
    if cl - py:
        print("only clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Humorus bee problem-solving adventure.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--name", choices=BEE_NAMES)
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
              if (args.place is None or c[0] == args.place)
              and (args.problem is None or c[1] == args.problem)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, pid = rng.choice(sorted(combos))
    return StoryParams(
        setting=place,
        problem=pid,
        bee_name=args.name or rng.choice(BEE_NAMES),
    )


def choose_solution(problem: Problem, setting: Setting) -> Optional[Solution]:
    for sol in SOLUTIONS:
        if problem.id in sol.helps and sol.requires <= setting.affords:
            return sol
    return None


def tell(setting: Setting, problem: Problem, bee_name: str) -> World:
    world = World(setting)
    bee = world.add(Entity(id=bee_name, kind="character", type="bee", label=bee_name))
    helper = world.add(Entity(id="Helper", kind="character", type="friend", label="the little helper"))
    world.problem = problem.id

    bee.memes["curious"] = 1
    bee.memes["funny"] = 1

    world.say(f"{bee_name} was a {story_style('bee')} who loved little adventures.")
    world.say(f"One bright day, {bee_name} buzzed into {setting.place} looking for nectar and a new puzzle.")
    world.say(f"Then {problem.hint}, and that was a problem.")
    world.para()
    bee.memes["trouble"] = 1
    world.say(f"{bee_name} frowned for a tiny moment, then gave a funny little buzz as if to say, \"I can solve this.\"")
    solution = choose_solution(problem, setting)
    if solution is None:
        raise StoryError("No reasonable solution for this story.")
    if solution.id == "leaf_bridge":
        world.say(f"{bee_name} spotted a flat leaf and asked the helper to nudge it into place.")
    elif solution.id == "step_stone":
        world.say(f"{bee_name} found a pebble and asked the helper to roll it under the sticky spot.")
    else:
        world.say(f"{bee_name} noticed two grass blades and asked the helper to weave them into a tiny ladder.")

    world.para()
    bee.memes["relief"] = 1
    bee.meters["distance"] = 1
    world.say(f"Together they {solution.prep}, and {solution.result}.")
    world.say(f"At last, {bee_name} reached the flowers, collected the sweet pollen, and zipped home with a happy hum.")
    world.say(f"The tiny adventure ended with {bee_name} smiling at the clever fix that made the whole day work.")

    world.facts.update(bee=bee, helper=helper, problem=problem, solution=solution)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    bee = f["bee"]
    prob = f["problem"]
    return [
        f"Write a short adventure story about a humorous bee who solves a problem in {world.setting.place}.",
        f"Tell a child-friendly story where {bee.id} notices {prob.hint} and figures out a clever fix.",
        f"Write a tiny adventure about a bee named {bee.id} that uses a simple tool to solve {prob.risk}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    bee = f["bee"]
    problem = f["problem"]
    solution = f["solution"]
    place = world.setting.place
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"The story is about {bee.id}, a humorous bee who loves tiny adventures.",
        ),
        QAItem(
            question=f"What problem did {bee.id} face in {place}?",
            answer=f"{bee.id} faced a problem because {problem.hint}.",
        ),
        QAItem(
            question=f"How did {bee.id} solve the problem?",
            answer=f"{bee.id} solved it by using {solution.label}. They {solution.prep}, and that let them keep going safely.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="Why do bees visit flowers?",
            answer="Bees visit flowers to gather nectar and pollen, which help them make honey and feed their colonies.",
        ),
        QAItem(
            question="What is a problem-solving tool?",
            answer="A problem-solving tool is something that helps you fix a tricky situation, like a bridge, a ladder, or a stone.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"  {e.id:10} ({e.type:8}) meters={meters} memes={memes}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
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


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], PROBLEMS[params.problem], params.bee_name)
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


CURATED = [
    StoryParams(setting="garden", problem="sticky_path", bee_name="Buzz"),
    StoryParams(setting="meadow", problem="low_flower", bee_name="Pip"),
    StoryParams(setting="orchard", problem="windy_gap", bee_name="Luna"),
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
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, problem) combos:")
        for c in combos:
            print(" ", c)
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
        if args.all:
            p = sample.params
            header = f"### {p.bee_name}: {p.problem} at {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
