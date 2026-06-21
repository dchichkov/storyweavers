#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/mental_friendship_problem_solving_animal_story.py
=================================================================================

A small animal storyworld about friendship, a worried or overwhelmed feeling,
and a problem that gets solved with a calm plan.

Seed idea:
- A young animal friend feels mentally tangled up about a problem.
- A friend notices, listens, and helps think through the issue.
- They work together, use a simple tool or strategy, and finish with a
  visible change in the world and in the friendship.

This world keeps the story child-facing, concrete, and state-driven.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
MENTAL_MIN = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Place:
    id: str
    label: str
    cozy: bool = False
    noisy: bool = False
    hidden_spot: str = ""
    setting_line: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Problem:
    id: str
    label: str
    trouble_line: str
    risk_line: str
    solved_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    method_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Solution:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.characters():
        if ent.memes["worry"] < THRESHOLD or ent.id in world.fired:
            continue
        sig = ("worry", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.memes["mental"] += 1
        out.append("__worry__")
    return out


def _r_comfort(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.characters():
        if ent.memes["calm"] < THRESHOLD:
            continue
        sig = ("calm", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.memes["support"] += 1
        out.append("__support__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule("worry", "mental", _r_worry),
    Rule("comfort", "social", _r_comfort),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def problem_risky(problem: Problem) -> bool:
    return True


def sensible_solutions() -> list[Solution]:
    return [s for s in SOLUTIONS.values() if s.sense >= 2]


def solve_power(problem: Problem, delay: int) -> int:
    return problem_power(problem) + delay


def problem_power(problem: Problem) -> int:
    return 2


def resolved(solution: Solution, problem: Problem, delay: int) -> bool:
    return solution.power >= solve_power(problem, delay)


def predict(world: World, protagonist_id: str, problem_id: str, solution_id: str) -> dict:
    sim = world.copy()
    _do_problem(sim, sim.get(protagonist_id), PROBLEMS[problem_id], narrate=False)
    return {
        "trouble": sim.get(protagonist_id).memes["worry"],
        "stress": sim.get(protagonist_id).meters["stress"],
        "solved": resolved(SOLUTIONS[solution_id], PROBLEMS[problem_id], 0),
    }


def _do_problem(world: World, protagonist: Entity, problem: Problem, narrate: bool = True) -> None:
    protagonist.meters["stress"] += 1
    protagonist.memes["worry"] += 1
    propagate(world, narrate=narrate)


def introduce(world: World, a: Entity, b: Entity, place: Place) -> None:
    for k in (a, b):
        k.memes["joy"] += 1
    world.say(
        f"On a quiet day at {place.label}, {a.id} and {b.id} went exploring together."
    )
    world.say(
        f"They were the kind of animal friends who liked to stay close and help each other."
    )


def problem_scene(world: World, a: Entity, place: Place, problem: Problem) -> None:
    world.say(
        f"{place.setting_line} Then {a.id} found {problem.trouble_line}."
    )
    if place.hidden_spot:
        world.say(
            f"It made the little {place.hidden_spot} feel extra hard to think about."
        )


def ask_for_help(world: World, a: Entity) -> None:
    a.memes["worry"] += 1
    world.say(
        f"{a.id} felt mental and mixed up. {a.pronoun().capitalize()} took a deep breath and looked for help."
    )


def friend_notices(world: World, b: Entity, a: Entity, problem: Problem) -> None:
    b.memes["calm"] += 1
    world.say(
        f"{b.id} noticed right away. \"Let's think about it together,\" {b.pronoun()} said."
    )
    world.say(
        f"{b.id} listened first, because good friends help with feelings as well as with chores."
    )


def plan(world: World, a: Entity, b: Entity, tool: Tool, problem: Problem) -> None:
    a.memes["calm"] += 1
    b.memes["calm"] += 1
    world.say(
        f"Then {b.id} suggested {tool.phrase}. {tool.method_line}"
    )
    world.say(
        f"{a.id} nodded. The plan felt small enough to do, one step at a time."
    )


def act(world: World, a: Entity, b: Entity, tool: Tool, problem: Problem) -> None:
    a.meters["progress"] += 1
    b.meters["progress"] += 1
    world.say(
        f"Together they used {tool.label} and kept going until the problem changed shape."
    )
    world.say(problem.solved_line)


def success_end(world: World, a: Entity, b: Entity, place: Place) -> None:
    a.memes["joy"] += 1
    b.memes["joy"] += 1
    a.memes["worry"] = 0.0
    world.say(
        f"At the end, {a.id} looked brighter, and {b.id} was smiling beside {a.pronoun('object')}."
    )
    world.say(
        f"The little {place.label_word if hasattr(place, 'label_word') else place.label} place felt peaceful again."
    )


def fail_end(world: World, a: Entity, b: Entity, problem: Problem, solution: Solution) -> None:
    world.say(
        f"{solution.fail} The friends had to stop and call a grown-up."
    )
    world.say(
        f"Even so, they stayed together, and that made the scary moment easier to bear."
    )


def tell(place: Place, problem: Problem, tool: Tool, solution: Solution,
         a_name: str = "Milo", a_type: str = "boy",
         b_name: str = "Tia", b_type: str = "girl",
         delay: int = 0) -> World:
    world = World()
    a = world.add(Entity(id=a_name, kind="character", type=a_type, role="problem-solver"))
    b = world.add(Entity(id=b_name, kind="character", type=b_type, role="friend"))
    world.add(Entity(id="place", type="place", label=place.label))
    world.add(Entity(id="problem", type="problem", label=problem.label))
    introduce(world, a, b, place)
    world.para()
    problem_scene(world, a, place, problem)
    ask_for_help(world, a)
    friend_notices(world, b, a, problem)
    world.para()
    plan(world, a, b, tool, problem)
    _do_problem(world, a, problem)
    if resolved(solution, problem, delay):
        act(world, a, b, tool, problem)
        world.para()
        success_end(world, a, b, place)
        outcome = "solved"
    else:
        fail_end(world, a, b, problem, solution)
        outcome = "stuck"
    world.facts.update(
        place=place, problem=problem, tool=tool, solution=solution,
        protagonist=a, friend=b, delay=delay, outcome=outcome,
        worried=a.memes["worry"] >= THRESHOLD,
    )
    return world


@dataclass
class StoryParams:
    place: str
    problem: str
    tool: str
    solution: str
    protagonist: str
    protagonist_type: str
    friend: str
    friend_type: str
    delay: int = 0
    seed: Optional[int] = None


PLACES = {
    "barn": Place("barn", "the barn", cozy=True, hidden_spot="hayloft", setting_line="The barn was warm and full of straw.", tags={"barn"}),
    "forest": Place("forest", "the forest path", hidden_spot="trail", setting_line="The forest path was quiet under the trees.", tags={"forest"}),
    "pond": Place("pond", "the pond bank", noisy=False, hidden_spot="reed patch", setting_line="The pond bank glittered in the sun.", tags={"pond"}),
}

PROBLEMS = {
    "lost": Problem("lost", "a lost seed pouch", "a lost seed pouch under a pile of straw", "Without it, the baby plants would have nothing to grow from.", "Soon the seed pouch was back in the basket.", tags={"lost"}),
    "tangled": Problem("tangled", "a tangled kite string", "a kite string knotted around a branch", "If it stayed there, the kite could not fly.", "The string came loose and the kite rose high.", tags={"tangled"}),
    "stuck": Problem("stuck", "a stuck wagon wheel", "a wagon wheel stuck in a muddy rut", "The cart could not roll forward at all.", "With a little push, the wheel rolled free.", tags={"stuck"}),
}

TOOLS = {
    "list": Tool("list", "a tiny plan list", "a tiny plan list", "They made three little steps and tried them one by one.", tags={"plan"}),
    "rope": Tool("rope", "a short rope", "a short rope", "They used the rope to reach and tug carefully.", tags={"rope"}),
    "map": Tool("map", "a simple map", "a simple map", "They followed the map and looked in the right places.", tags={"map"}),
}

SOLUTIONS = {
    "quick": Solution("quick", 3, 2, "Their careful idea worked before the trouble could grow bigger.", "The quick idea was not enough and the trouble stayed messy.", "solved it with a quick careful idea", tags={"quick"}),
    "patient": Solution("patient", 2, 3, "They kept trying patiently until the problem was fixed.", "Patience alone was not enough, and the problem stayed stuck.", "solved it by being patient", tags={"patient"}),
    "helper": Solution("helper", 3, 4, "They asked the right help and used it gently until the job was done.", "The helper plan did not work fast enough.", "solved it by asking for the right help", tags={"helper"}),
}

ANIMAL_NAMES = ["Milo", "Tia", "Pip", "Luna", "Otto", "Nina", "Bram", "Penny"]
ANIMAL_TYPES = ["fox", "rabbit", "bear", "beaver", "mouse", "otter", "deer", "cat"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for pid in PLACES:
        for prob in PROBLEMS:
            for tool in TOOLS:
                for sol in SOLUTIONS:
                    combos.append((pid, prob, tool))
    return combos


def explain_rejection(problem: Problem, solution: Solution) -> str:
    return f"(No story: the chosen solution '{solution.id}' is not a sensible enough way to solve this animal problem.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal friendship and problem-solving storyworld.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--solution", choices=SOLUTIONS)
    ap.add_argument("--protagonist")
    ap.add_argument("--protagonist-type", choices=ANIMAL_TYPES)
    ap.add_argument("--friend")
    ap.add_argument("--friend-type", choices=ANIMAL_TYPES)
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
    if args.solution and args.solution not in SOLUTIONS:
        raise StoryError("(Unknown solution.)")
    if args.solution and SOLUTIONS[args.solution].sense < 2:
        raise StoryError(explain_rejection(PROBLEMS[args.problem or "lost"], SOLUTIONS[args.solution]))
    place = args.place or rng.choice(list(PLACES))
    problem = args.problem or rng.choice(list(PROBLEMS))
    tool = args.tool or rng.choice(list(TOOLS))
    solution = args.solution or rng.choice([s.id for s in sensible_solutions()])
    protagonist_type = args.protagonist_type or rng.choice(ANIMAL_TYPES)
    friend_type = args.friend_type or rng.choice(ANIMAL_TYPES)
    protagonist = args.protagonist or rng.choice(ANIMAL_NAMES)
    friend = args.friend or rng.choice([n for n in ANIMAL_NAMES if n != protagonist])
    delay = 0 if args.seed is None else rng.randint(0, 1)
    return StoryParams(
        place=place, problem=problem, tool=tool, solution=solution,
        protagonist=protagonist, protagonist_type=protagonist_type,
        friend=friend, friend_type=friend_type, delay=delay,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write an animal story for a young child that includes the word "mental" and shows friendship.',
        f"Tell a gentle story where {f['protagonist'].id} feels mental about {f['problem'].label}, and a friend helps solve it.",
        f"Write a story about two animal friends who stay calm, think together, and use {f['tool'].label} to fix a problem.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a, b = f["protagonist"], f["friend"]
    place, problem, tool, sol = f["place"], f["problem"], f["tool"], f["solution"]
    qa = [
        ("Who is the story about?", f"It is about {a.id} and {b.id}, two animal friends who stay together and help each other."),
        ("What problem did they have?", f"They had {problem.trouble_line}. That was the thing they needed to solve together."),
        ("What did they use to help?", f"They used {tool.label}. {tool.method_line}"),
        ("How did the story end?", f"It ended with the problem fixed and the friends feeling proud and calm."),
    ]
    if f["outcome"] == "solved":
        qa.append((f"How did {a.id} feel after the problem was solved?",
                   f"{a.id} felt less mental and much calmer. The hard part was over, and {b.id} was still beside {a.id}."))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What does it mean to feel mental?", "It can mean feeling overwhelmed, tangled up, or having too many thoughts at once. A calm friend can help by listening and making a simple plan."),
        ("Why do friends help with problems?", "Friends can share ideas, stay calm, and make hard things feel smaller. Working together often helps a problem get solved more easily."),
        ("What is a plan?", "A plan is a set of simple steps that helps you know what to do next. Plans can make a problem easier to handle."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story ==", *[f"{i}. {p}" for i, p in enumerate(sample.prompts, 1)], "", "== (2) Story questions -- answerable from the story text =="]
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="barn", problem="lost", tool="list", solution="quick", protagonist="Milo", protagonist_type="fox", friend="Tia", friend_type="rabbit", delay=0),
    StoryParams(place="forest", problem="tangled", tool="rope", solution="patient", protagonist="Pip", protagonist_type="beaver", friend="Luna", friend_type="otter", delay=0),
    StoryParams(place="pond", problem="stuck", tool="map", solution="helper", protagonist="Nina", protagonist_type="mouse", friend="Bram", friend_type="bear", delay=0),
]


ASP_RULES = r"""
sensible(S) :- solution(S), sense(S, N), N >= 2.
valid(P, Pr, T) :- place(P), problem(Pr), tool(T).
outcome(solved) :- chosen_solution(S), solution(S), power(S, P), severity(V), P >= V.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for prid, pr in PROBLEMS.items():
        lines.append(asp.fact("problem", prid))
        lines.append(asp.fact("severity", prid, 2))
    for tid in TOOLS:
        lines.append(asp.fact("tool", tid))
    for sid, s in SOLUTIONS.items():
        lines.append(asp.fact("solution", sid))
        lines.append(asp.fact("sense", sid, s.sense))
        lines.append(asp.fact("power", sid, s.power))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("", "#show sensible/1."))
    cset = set(asp.atoms(model, "sensible"))
    pset = { (sid,) for sid, s in SOLUTIONS.items() if s.sense >= 2}
    rc = 0 if cset == pset else 1
    print("OK: ASP gate matches." if rc == 0 else "MISMATCH: ASP gate differs.")
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        print("OK: generate() smoke test succeeded.")
    except Exception as ex:
        print(f"SMOKE TEST FAILED: {ex}")
        return 1
    return rc


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES or params.problem not in PROBLEMS or params.tool not in TOOLS or params.solution not in SOLUTIONS:
        raise StoryError("Invalid parameters.")
    world = tell(PLACES[params.place], PROBLEMS[params.problem], TOOLS[params.tool], SOLUTIONS[params.solution],
                 a_name=params.protagonist, a_type=params.protagonist_type,
                 b_name=params.friend, b_type=params.friend_type, delay=params.delay)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
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
        print(asp_program("", "#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("sensible solutions:", ", ".join(s.id for s in sensible_solutions()))
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
