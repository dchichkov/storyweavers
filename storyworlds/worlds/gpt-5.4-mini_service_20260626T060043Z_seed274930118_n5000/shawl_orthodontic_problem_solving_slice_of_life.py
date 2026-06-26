#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/shawl_orthodontic_problem_solving_slice_of_life.py
================================================================================

A small slice-of-life story world about a child, a shawl, and an orthodontic
problem that gets solved with care, noticing, and a few ordinary errands.

Premise:
- A child is proud of a soft shawl.
- Something about the orthodontic appointment or appliance is getting in the way.
- A parent, caregiver, or helper notices the problem and helps find a fix.
- The story ends with the child comfortable again, with the shawl still part of
  the day and the orthodontic problem solved.

The world is deliberately tiny and constraint-driven: only a few plausible
combinations are allowed, and invalid explicit choices raise StoryError.
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
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    region: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
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
    indoor: bool
    affords: set[str] = field(default_factory=set)


@dataclass
class Problem:
    id: str
    label: str
    phrase: str
    issue: str
    fix_hint: str
    region: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Solution:
    id: str
    label: str
    phrase: str
    method: str
    tail: str
    plural: bool = False
    covers: set[str] = field(default_factory=set)
    solves: set[str] = field(default_factory=set)


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
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


def _r_uncomfortable(world: World) -> list[str]:
    out: list[str] = []
    child = world.facts.get("child")
    problem = world.facts.get("problem")
    if not child or not problem:
        return out
    if child.meters.get(problem.id, 0.0) >= THRESHOLD and ("feel", problem.id) not in world.fired:
        world.fired.add(("feel", problem.id))
        child.memes["worry"] = child.memes.get("worry", 0.0) + 1
        out.append(f"{child.id} kept noticing that {problem.label} was bothering {child.pronoun('object')}.")
    return out


def _r_fix(world: World) -> list[str]:
    out: list[str] = []
    child = world.facts.get("child")
    helper = world.facts.get("helper")
    problem = world.facts.get("problem")
    solution = world.facts.get("solution")
    if not child or not helper or not problem or not solution:
        return out
    if child.meters.get(solution.id, 0.0) >= THRESHOLD and child.meters.get(problem.id, 0.0) >= THRESHOLD:
        sig = ("fix", solution.id)
        if sig in world.fired:
            return out
        world.fired.add(sig)
        child.memes["relief"] = child.memes.get("relief", 0.0) + 1
        child.memes["joy"] = child.memes.get("joy", 0.0) + 1
        out.append(f"With {solution.label}, the problem finally settled down.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in (_r_uncomfortable, _r_fix):
            sents = rule(world)
            if sents:
                changed = True
                out.extend(sents)
    if narrate:
        for s in out:
            world.say(s)
    return out


def can_solve(problem: Problem, solution: Solution) -> bool:
    return problem.region in solution.covers and problem.id in solution.solves


def choose_solution(problem: Problem) -> Optional[Solution]:
    for sol in SOLUTIONS:
        if can_solve(problem, sol):
            return sol
    return None


def predict_fix(world: World, child: Entity, problem: Problem, solution: Solution) -> dict:
    sim = world.copy()
    sim_child = sim.get(child.id)
    sim_child.meters[problem.id] = 1.0
    sim_child.meters[solution.id] = 1.0
    sim.facts = dict(world.facts)
    sim.facts["child"] = sim_child
    sim.facts["problem"] = problem
    sim.facts["solution"] = solution
    propagate(sim, narrate=False)
    return {
        "solved": sim_child.memes.get("relief", 0.0) >= THRESHOLD,
        "worry": sim_child.memes.get("worry", 0.0),
    }


def activity_detail(problem: Problem) -> str:
    return {
        "brace": "The metal brace felt too tight after lunch.",
        "gap": "A gap in the teeth made speaking feel funny.",
        "band": "One little band kept slipping out of place.",
        "tray": "The clear tray felt awkward and needed a careful fix.",
    }.get(problem.id, "Something in the mouth needed a gentle solution.")


SETTINGS = {
    "kitchen": Setting(place="the kitchen", indoor=True, affords={"brace", "gap", "band", "tray"}),
    "living_room": Setting(place="the living room", indoor=True, affords={"brace", "gap", "band"}),
    "porch": Setting(place="the porch", indoor=False, affords={"band", "tray"}),
}

PROBLEMS = {
    "brace": Problem(
        id="brace",
        label="braces",
        phrase="a set of shiny braces",
        issue="felt too tight",
        fix_hint="the child needed wax and a careful bite of soft food",
        region="mouth",
        tags={"orthodontic", "metal"},
    ),
    "gap": Problem(
        id="gap",
        label="gap",
        phrase="a small gap between two teeth",
        issue="made speaking feel lisped and shy",
        fix_hint="the child needed practice and a patient checkup",
        region="mouth",
        tags={"orthodontic"},
    ),
    "band": Problem(
        id="band",
        label="rubber band",
        phrase="a tiny rubber band on the braces",
        issue="kept slipping loose",
        fix_hint="the helper needed tweezers and a steady hand",
        region="mouth",
        tags={"orthodontic", "small"},
    ),
    "tray": Problem(
        id="tray",
        label="clear tray",
        phrase="a clear orthodontic tray",
        issue="felt awkward and pinchy",
        fix_hint="the tray needed a rinse and a better fit",
        region="mouth",
        tags={"orthodontic", "clear"},
    ),
}

SOLUTIONS = [
    Solution(
        id="wax",
        label="orthodontic wax",
        phrase="a little bit of soft orthodontic wax",
        method="press it over the sharp edge",
        tail="carefully pressed the wax in place",
        covers={"mouth"},
        solves={"brace"},
    ),
    Solution(
        id="tweezers",
        label="tiny tweezers",
        phrase="a pair of tiny tweezers",
        method="lift the slipping band back where it belonged",
        tail="used the tweezers to lift the band back on",
        covers={"mouth"},
        solves={"band"},
    ),
    Solution(
        id="checkup",
        label="a quick checkup",
        phrase="a quick orthodontic checkup",
        method="let the helper adjust what was bothering the child",
        tail="went for a quick checkup",
        covers={"mouth"},
        solves={"gap", "tray"},
    ),
]

NAMES = ["Maya", "Noah", "Lena", "Eli", "Iris", "Theo", "Ruby", "Finn"]
TRAITS = ["quiet", "curious", "patient", "careful", "gentle", "bright"]


@dataclass
class StoryParams:
    place: str
    problem: str
    solution: str
    name: str
    gender: str
    helper: str
    trait: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for pid in setting.affords:
            prob = PROBLEMS[pid]
            for sol in SOLUTIONS:
                if can_solve(prob, sol):
                    out.append((place, pid, sol.id))
    return out


def introduce(world: World, child: Entity) -> None:
    world.say(f"{child.id} was a little {child.memes.get('trait_word', 'careful')} child who liked quiet mornings and warm snacks.")


def start_problem(world: World, child: Entity, problem: Problem) -> None:
    child.meters[problem.id] = 1.0
    world.say(f"{child.id} had {problem.phrase}, and it {problem.issue}.")
    world.say(activity_detail(problem))


def helper_notices(world: World, helper: Entity, child: Entity, problem: Problem) -> None:
    helper.memes["attention"] = helper.memes.get("attention", 0.0) + 1
    world.say(f"{helper.pronoun().capitalize()} noticed right away that {child.id} was frowning.")
    world.say(f'"That looks hard," {helper.id} said. "Let\'s find a small fix."')


def try_solution(world: World, child: Entity, helper: Entity, problem: Problem, solution: Solution) -> bool:
    child.meters[solution.id] = 1.0
    pred = predict_fix(world, child, problem, solution)
    if not pred["solved"]:
        return False
    world.say(f"{helper.id} found {solution.phrase} and showed {child.id} {solution.method}.")
    return True


def resolve(world: World, child: Entity, helper: Entity, problem: Problem, solution: Solution) -> None:
    child.memes["worry"] = 0.0
    child.memes["relief"] = child.memes.get("relief", 0.0) + 1
    propagate(world, narrate=True)
    world.say(f"{helper.id} {solution.tail}, and the trouble with {problem.label} got much easier.")
    world.say(f"{child.id} gave a small smile and touched {child.pronoun('possessive')} shawl, glad the day was smooth again.")


def tell(setting: Setting, problem: Problem, solution: Solution, name: str, gender: str, helper_type: str, trait: str) -> World:
    world = World(setting)
    child = world.add(Entity(id=name, kind="character", type=gender, meters={}, memes={"trait_word": trait}))
    helper = world.add(Entity(id="Helper", kind="character", type=helper_type, label="the helper"))
    shawl = world.add(Entity(id="shawl", type="shawl", label="shawl", phrase="a soft blue shawl", owner=child.id, worn_by=child.id))
    world.facts.update(child=child, helper=helper, shawl=shawl, problem=problem, solution=solution)
    introduce(world, child)
    world.say(f"{child.id} loved {child.pronoun('possessive')} shawl because it felt cozy and a little fancy.")
    world.para()
    world.say(f"One afternoon in {setting.place}, {child.id} noticed that {problem.label} was the real problem.")
    start_problem(world, child, problem)
    helper_notices(world, helper, child, problem)
    world.say(f"{child.id} wanted the problem fixed before supper.")
    world.para()
    if try_solution(world, child, helper, problem, solution):
        resolve(world, child, helper, problem, solution)
    world.facts.update(resolved=True)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    problem = f["problem"]
    return [
        'Write a short slice-of-life story for a young child about a shawl and an orthodontic problem that gets solved kindly.',
        f"Tell a gentle story about {child.id} in {world.setting.place} where {problem.label} causes a small worry and a helper fixes it.",
        f'Write a simple story that includes the words "shawl" and "orthodontic" and ends with relief after a practical solution.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    problem = f["problem"]
    solution = f["solution"]
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about {child.id}, a little {child.memes.get('trait_word', 'careful')} child, and {helper.label}.",
        ),
        QAItem(
            question=f"What orthodontic problem bothered {child.id}?",
            answer=f"{child.id} had {problem.phrase}, and it {problem.issue}.",
        ),
        QAItem(
            question=f"How did {helper.id} help fix the problem?",
            answer=f"{helper.id} used {solution.label} to help with the trouble, and that made the orthodontic problem easier.",
        ),
        QAItem(
            question=f"What stayed important to {child.id} during the day?",
            answer=f"{child.id} still loved {child.pronoun('possessive')} shawl and felt better once the problem was handled.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a shawl?",
            answer="A shawl is a soft cloth you can wear around your shoulders to feel warm and cozy.",
        ),
        QAItem(
            question="What does orthodontic mean?",
            answer="Orthodontic means something is about teeth, like braces, trays, or other tools that help teeth line up better.",
        ),
        QAItem(
            question="Why do people use orthodontic wax?",
            answer="People use orthodontic wax to cover a sharp brace part so it feels less pokey.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== story qa ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== world qa ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v and k != "trait_word"}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.worn_by:
            bits.append(f"worn_by={e.worn_by}")
        lines.append(f"  {e.id} ({e.type}) {' '.join(bits)}")
    lines.append(f"  fired={sorted(world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="kitchen", problem="brace", solution="wax", name="Maya", gender="girl", helper="mother", trait="careful"),
    StoryParams(place="living_room", problem="band", solution="tweezers", name="Noah", gender="boy", helper="father", trait="patient"),
    StoryParams(place="kitchen", problem="tray", solution="checkup", name="Iris", gender="girl", helper="mother", trait="gentle"),
]


ASP_RULES = r"""
problem_at_risk(P, mouth) :- problem(P), region(P, mouth).
can_solve(P, S) :- problem_at_risk(P, mouth), solution(S), covers(S, mouth), solves(S, P).
valid_story(Place, P, S) :- affords(Place, P), can_solve(P, S).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.indoor:
            lines.append(asp.fact("indoor", sid))
        for p in sorted(s.affords):
            lines.append(asp.fact("affords", sid, p))
    for pid, p in PROBLEMS.items():
        lines.append(asp.fact("problem", pid))
        lines.append(asp.fact("region", pid, p.region))
    for sid, s in enumerate(SOLUTIONS):
        lines.append(asp.fact("solution", s.id))
        for c in sorted(s.covers):
            lines.append(asp.fact("covers", s.id, c))
        for p in sorted(s.solves):
            lines.append(asp.fact("solves", s.id, p))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    import asp
    py = set(valid_combos())
    cl = set(asp_valid_stories())
    if py == cl:
        print(f"OK: ASP matches Python ({len(py)} stories).")
        return 0
    print("MISMATCH between ASP and Python:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in asp:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life story world: shawl + orthodontic problem solving.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--solution", choices=[s.id for s in SOLUTIONS])
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=["mother", "father"])
    ap.add_argument("--name")
    ap.add_argument("--trait", choices=["quiet", "curious", "patient", "careful", "gentle", "bright"])
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


def explain_rejection(problem: Problem, solution: Solution) -> str:
    return f"(No story: {solution.label} does not solve {problem.label} in this tiny world.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.problem and args.solution:
        if not can_solve(PROBLEMS[args.problem], next(s for s in SOLUTIONS if s.id == args.solution)):
            raise StoryError(explain_rejection(PROBLEMS[args.problem], next(s for s in SOLUTIONS if s.id == args.solution)))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.problem is None or c[1] == args.problem)
              and (args.solution is None or c[2] == args.solution)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, problem, solution = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES)
    helper = args.helper or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, problem=problem, solution=solution, name=name, gender=gender, helper=helper, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], PROBLEMS[params.problem], next(s for s in SOLUTIONS if s.id == params.solution), params.name, params.gender, params.helper, params.trait)
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
        stories = asp_valid_stories()
        print(f"{len(stories)} valid stories:\n")
        for place, problem, solution in stories:
            print(f"  {place:12} {problem:8} {solution:8}")
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
            header = f"### {p.name}: {p.problem} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
