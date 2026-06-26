#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/sister_plop_concerted_repetition_superhero_story.py
===============================================================================================================================

A small superhero story world with a repeating sound, a sister hero, and a
concerted team response.

Seed image:
- A little sister hears a steady plop-plop-plop from the neighborhood roof.
- She follows the sound, finds a leaky water drum threatening a street fair.
- She calls for concerted help, and everyone repeats a simple rescue pattern:
  lift, pass, patch, and cheer.
- The story ends with the roof dry, the fair safe, and the sister proud.

This script models a tiny, classical domain with physical meters and emotional
memes, plus a reasonableness gate and an inline ASP twin.
"""

from __future__ import annotations

import argparse
import dataclasses
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
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "sister", "woman", "mother"}
        male = {"boy", "brother", "man", "father"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the rooftop garden"
    affords: set[str] = field(default_factory=set)


@dataclass
class Problem:
    id: str
    verb: str
    gerund: str
    sound: str
    repetition: str
    risk: str
    meter: str
    zone: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Solution:
    id: str
    label: str
    action: str
    repeat_line: str
    guards: set[str] = field(default_factory=set)
    covers: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    setting: str
    problem: str
    solution: str
    name: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.facts: dict[str, object] = {}
        self.fired: set[tuple] = set()
        self.trace: list[str] = []

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def render(self) -> str:
        return " ".join(self.lines)


SETTINGS = {
    "rooftop": Setting(place="the rooftop garden", affords={"plop"}),
    "alley": Setting(place="the bright alley", affords={"plop"}),
    "square": Setting(place="the city square", affords={"plop"}),
}

PROBLEMS = {
    "plop": Problem(
        id="plop",
        verb="track the plop sound",
        gerund="tracking the plop sound",
        sound="plop",
        repetition="plop-plop-plop",
        risk="soaked crates",
        meter="leak",
        zone="roof",
        tags={"water", "sound", "plop", "repetition"},
    )
}

SOLUTIONS = {
    "concerted": Solution(
        id="concerted",
        label="concerted team plan",
        action="work together in a careful chain",
        repeat_line="lift, pass, patch, and cheer",
        guards={"leak"},
        covers={"roof"},
    ),
    "patch": Solution(
        id="patch",
        label="patch kit",
        action="seal the leak with a shining patch",
        repeat_line="press, smooth, and hold",
        guards={"leak"},
        covers={"roof"},
    ),
}

NAMES = ["Mina", "Lina", "Tia", "Rosa", "Nina", "Aria", "Maya"]
TRAITS = ["brave", "quick-thinking", "kind", "bold"]


class Rule:
    def __init__(self, name: str, func):
        self.name = name
        self.func = func


def _r_leak(world: World) -> list[str]:
    out = []
    roof = world.entities.get("roof")
    water = world.entities.get("water")
    if not roof or not water:
        return out
    if water.meters.get("leak", 0) < THRESHOLD:
        return out
    sig = ("leak",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    roof.meters["wet"] = roof.meters.get("wet", 0) + 1
    out.append("The roof grew wet.")
    return out


def _r_risk(world: World) -> list[str]:
    out = []
    fair = world.entities.get("fair")
    roof = world.entities.get("roof")
    if not fair or not roof:
        return out
    if roof.meters.get("wet", 0) < THRESHOLD:
        return out
    sig = ("risk",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    fair.memes["worry"] = fair.memes.get("worry", 0) + 1
    out.append("That put the street fair at risk.")
    return out


RULES = [Rule("leak", _r_leak), Rule("risk", _r_risk)]


def propagate(world: World) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            bits = rule.func(world)
            if bits:
                changed = True
                produced.extend(bits)
    for line in produced:
        world.say(line)
    return produced


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s_id, setting in SETTINGS.items():
        for p_id, prob in PROBLEMS.items():
            if prob.sound in setting.affords:
                for sol_id, sol in SOLUTIONS.items():
                    if prob.meter in sol.guards and prob.zone in sol.covers:
                        combos.append((s_id, p_id, sol_id))
    return combos


def problem_at_risk(problem: Problem, solution: Solution) -> bool:
    return problem.meter in solution.guards and problem.zone in solution.covers


def explain_rejection(problem: Problem, solution: Solution) -> str:
    return (
        f"(No story: {solution.label} would not truly help with {problem.repetition}; "
        f"the fix must guard the leak and cover the roof.)"
    )


def build_world(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    prob = PROBLEMS[params.problem]
    sol = SOLUTIONS[params.solution]
    world = World(setting)

    sister = world.add(Entity(
        id=params.name, kind="character", type="sister", label=params.name,
        traits=["little", "bright", "stubborn"],
    ))
    helper = world.add(Entity(
        id="team", kind="character", type="sister", label="the team",
        traits=["concerted"],
    ))
    water = world.add(Entity(
        id="water", type="thing", label="water drum", phrase="a water drum",
        meters={"leak": 1.0},
    ))
    roof = world.add(Entity(
        id="roof", type="thing", label="roof", phrase="the roof",
        meters={"wet": 0.0},
    ))
    fair = world.add(Entity(
        id="fair", type="thing", label="street fair", phrase="the street fair",
        memes={"worry": 0.0},
    ))

    world.facts.update(
        sister=sister, helper=helper, water=water, roof=roof, fair=fair,
        problem=prob, solution=sol, setting=setting,
    )

    world.say(f"{params.name} was a little sister who loved being a hero.")
    world.say(f"She heard {prob.repetition} from {setting.place} and turned her head to listen.")
    world.say(f"The sound went {prob.sound}, {prob.sound}, {prob.sound}, like a tiny warning.")
    world.say(f"She followed it while the neighborhood held its breath.")

    world.say(f"At the roof, she saw {prob.risk} waiting under a leaking water drum.")
    world.say(f"{params.name} knew the leak could ruin the fair if nobody acted fast.")
    world.say(f"She called the others with a clear voice: 'We need a {sol.label}!'")
    world.say(f"Everyone moved in a concerted chain: {sol.repeat_line}.")
    world.say(f"Again and again, they repeated the same careful steps.")
    world.say(f"Again and again, the leak grew smaller.")
    water.meters["leak"] = 0.0
    roof.meters["wet"] = 0.0
    fair.memes["worry"] = 0.0
    propagate(world)

    sister.memes["pride"] = sister.memes.get("pride", 0) + 1
    helper.memes["teamwork"] = helper.memes.get("teamwork", 0) + 1
    world.say(
        f"In the end, {params.name} smiled because the roof stayed dry and the fair stayed safe."
    )
    world.say(
        f"The last thing she heard was a happy little plop of rainwater falling into a bucket."
    )
    return world


KNOWLEDGE = {
    "plop": [
        (
            "What does plop sound like?",
            "Plop is a soft sound, like a drop of water landing in a bucket or on the floor.",
        )
    ],
    "repetition": [
        (
            "What is repetition?",
            "Repetition means doing or saying the same thing again and again.",
        )
    ],
    "concerted": [
        (
            "What does concerted mean?",
            "Concerted means people are working together on the same plan.",
        )
    ],
    "water": [
        (
            "Why can a leak cause trouble?",
            "A leak can cause trouble because water can spread where it is not wanted and make things wet.",
        )
    ],
    "teamwork": [
        (
            "Why is teamwork helpful?",
            "Teamwork is helpful because many hands can finish a big job more safely and quickly.",
        )
    ],
}
KNOWLEDGE_ORDER = ["plop", "repetition", "concerted", "water", "teamwork"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    prob: Problem = f["problem"]  # type: ignore[assignment]
    sol: Solution = f["solution"]  # type: ignore[assignment]
    sister: Entity = f["sister"]  # type: ignore[assignment]
    return [
        f'Write a superhero story for a young child about {sister.label}, the word "{prob.sound}", and a concerted rescue.',
        f"Tell a simple hero story where a sister hears {prob.repetition} and helps with a {sol.label}.",
        f"Write a story that repeats the rescue steps and ends with the roof safe.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    sister: Entity = f["sister"]  # type: ignore[assignment]
    prob: Problem = f["problem"]  # type: ignore[assignment]
    sol: Solution = f["solution"]  # type: ignore[assignment]
    setting: Setting = f["setting"]  # type: ignore[assignment]
    qa = [
        QAItem(
            question=f"Who is the hero in the story?",
            answer=f"The hero is {sister.label}, a little sister who loves helping people.",
        ),
        QAItem(
            question=f"What repeating sound did {sister.label} hear?",
            answer=f"She heard {prob.repetition}, which sounded like a warning from the roof.",
        ),
        QAItem(
            question="What did the team do to fix the problem?",
            answer=f"They used a {sol.label} and worked together in a concerted chain at {setting.place}.",
        ),
        QAItem(
            question="What changed by the end of the story?",
            answer="The roof stayed dry, the fair was safe, and the sister felt proud.",
        ),
    ]
    if prob.sound == "plop":
        qa.append(
            QAItem(
                question="Why was the plop sound important?",
                answer="The plop sound was important because it led the sister to the leak before the water could cause more trouble.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    out: list[QAItem] = []
    tags = set()
    prob: Problem = world.facts["problem"]  # type: ignore[assignment]
    sol: Solution = world.facts["solution"]  # type: ignore[assignment]
    tags |= prob.tags
    tags |= sol.guards
    tags.add("concerted")
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[tag])
    return out


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
    lines.append("== (3) World-knowledge questions ==")
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
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for pid, p in PROBLEMS.items():
        lines.append(asp.fact("problem", pid))
        lines.append(asp.fact("sound", pid, p.sound))
        lines.append(asp.fact("meter", pid, p.meter))
        lines.append(asp.fact("zone", pid, p.zone))
        for t in sorted(p.tags):
            lines.append(asp.fact("tag", pid, t))
    for sid, s in SOLUTIONS.items():
        lines.append(asp.fact("solution", sid))
        for g in sorted(s.guards):
            lines.append(asp.fact("guards", sid, g))
        for c in sorted(s.covers):
            lines.append(asp.fact("covers", sid, c))
    return "\n".join(lines)


ASP_RULES = r"""
at_risk(P,S) :- meter(P,M), guards(S,M), zone(P,Z), covers(S,Z).
valid(Place,P,S) :- affords(Place,plop), at_risk(P,S).
#show valid/3.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero story world with plop and concerted repetition.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--solution", choices=SOLUTIONS)
    ap.add_argument("--name", choices=NAMES)
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
    if args.setting or args.problem or args.solution:
        filtered = [
            c for c in combos
            if (args.setting is None or c[0] == args.setting)
            and (args.problem is None or c[1] == args.problem)
            and (args.solution is None or c[2] == args.solution)
        ]
    else:
        filtered = combos
    if not filtered:
        raise StoryError("(No valid combination matches the given options.)")
    setting, problem, solution = rng.choice(sorted(filtered))
    name = args.name or rng.choice(NAMES)
    return StoryParams(setting=setting, problem=problem, solution=solution, name=name)


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


CURATED = [
    StoryParams(setting="rooftop", problem="plop", solution="concerted", name="Mina"),
    StoryParams(setting="alley", problem="plop", solution="patch", name="Lina"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_valid_combos())
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            rng = random.Random(base_seed + i)
            i += 1
            try:
                params = resolve_params(args, rng)
            except StoryError as e:
                print(e)
                return
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

    for idx, sample in enumerate(samples):
        if len(samples) > 1:
            print(f"### variant {idx + 1}")
        emit(sample, trace=args.trace, qa=args.qa)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
