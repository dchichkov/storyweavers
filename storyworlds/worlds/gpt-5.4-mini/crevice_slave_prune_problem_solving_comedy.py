#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/crevice_slave_prune_problem_solving_comedy.py
==============================================================================

A tiny standalone storyworld for a comic problem-solving tale in which a small
situation goes wrong, the characters try an obvious but clumsy idea, then solve
it with a better plan.

Seed words:
- crevice
- slave
- prune

Style:
- Comedy

Domain:
- A child, a helper robot, and a sticky prune treat stuck in a narrow crevice.
  The story stays small and physical: meters track where things are stuck, and
  memes track worry, silliness, and relief. The ending proves the problem was
  solved in a concrete way.

The script follows the Storyweavers contract:
- stdlib only
- StoryParams / build_parser / resolve_params / generate / emit / main
- --qa, --json, --trace, --all, --seed, --asp, --verify, --show-asp
- eager shared result import
- Python reasonableness gate plus inline ASP twin
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    attrs: dict = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.meters is None:
            self.meters = {}
        if self.memes is None:
            self.memes = {}

    def meter(self, key: str) -> float:
        return self.meters.get(key, 0.0)

    def meme(self, key: str) -> float:
        return self.memes.get(key, 0.0)

    def bump_meter(self, key: str, amount: float = 1.0) -> None:
        self.meters[key] = self.meter(key) + amount

    def bump_meme(self, key: str, amount: float = 1.0) -> None:
        self.memes[key] = self.meme(key) + amount

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
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Setting:
    id: str
    place: str
    dark_spot: str
    clutter: str
    room_name: str


@dataclass
class Problem:
    id: str
    label: str
    source: str
    stuck_in: str
    magnitude: int
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    action: str
    power: int
    silly: int
    sense: int
    tags: set[str] = field(default_factory=set)


@dataclass
class Solution:
    id: str
    label: str
    method: str
    power: int
    sense: int
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
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
        clone = World(self.setting)
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


def _r_stuck(world: World) -> list[str]:
    out: list[str] = []
    problem = world.get("problem")
    if problem.meter("stuck") < THRESHOLD:
        return out
    sig = ("stuck", problem.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    for hero in world.characters():
        hero.bump_meme("worry", 1)
    out.append("__stuck__")
    return out


def _r_relief(world: World) -> list[str]:
    out: list[str] = []
    problem = world.get("problem")
    if problem.meter("solved") < THRESHOLD:
        return out
    sig = ("relief", problem.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    for hero in world.characters():
        hero.bump_meme("relief", 1)
        hero.memes["worry"] = max(0.0, hero.meme("worry") - 1)
    out.append("__relief__")
    return out


CAUSAL_RULES = [
    Rule("stuck", "physical", _r_stuck),
    Rule("relief", "social", _r_relief),
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


def problem_at_risk(problem: Problem, setting: Setting) -> bool:
    return problem.stuck_in in {"crevice", "narrow crevice"} and "crevice" in setting.dark_spot


def sensible_tools() -> list[Tool]:
    return [t for t in TOOLS.values() if t.sense >= SENSE_MIN]


def best_tool() -> Tool:
    return max(TOOLS.values(), key=lambda t: t.sense)


def solution_succeeds(tool: Tool, solution: Solution, problem: Problem) -> bool:
    return tool.power + solution.power >= problem.magnitude


def predict(world: World, tool: Tool, solution: Solution) -> dict:
    sim = world.copy()
    _attempt_fix(sim, sim.get("child"), sim.get("helper"), sim.get("problem"), tool, solution, narrate=False)
    return {
        "solved": sim.get("problem").meter("solved") >= THRESHOLD,
        "worry": sim.get("child").meme("worry"),
    }


def _attempt_fix(world: World, child: Entity, helper: Entity, problem: Entity,
                 tool: Tool, solution: Solution, narrate: bool = True) -> None:
    if tool.power >= 0:
        problem.bump_meter("attempted", 1)
    if solution_succeeds(tool, solution, problem.attrs["problem"]):
        problem.meters["solved"] = 1.0
        propagate(world, narrate=narrate)
    else:
        problem.bump_meter("worsened", 1)
        child.bump_meme("worry", 1)
        helper.bump_meme("worry", 1)


def introduce(world: World, child: Entity, helper: Entity, setting: Setting) -> None:
    world.say(
        f"On a bright afternoon, {child.id} and {helper.id} were in {setting.place}. "
        f"{setting.clutter} made the room feel like a tiny adventure."
    )
    world.say(
        f"{child.id} called it {setting.room_name}, because even the darkest corner could become part of a game."
    )


def show_problem(world: World, child: Entity, problem: Entity, setting: Setting) -> None:
    world.say(
        f"But then the snack got stuck in a {problem.attrs['stuck_in']}. "
        f"{problem.label.capitalize()} would not budge, and the narrow spot only made it wiggle farther in."
    )
    world.say(
        f'"Oh no," said {child.id}. "My {problem.label} is trapped in the {setting.dark_spot}."'
    )


def try_silly_fix(world: World, helper: Entity, tool: Tool, problem: Entity) -> None:
    helper.bump_meme("silliness", 1)
    world.say(
        f'{helper.id} got a funny idea. "{tool.action}!" {helper.pronoun().capitalize()} said, '
        f"as if a dramatic stunt could solve everything."
    )
    world.say(
        f"For one silly second, the plan sounded almost heroic."
    )


def warn(world: World, child: Entity, helper: Entity, tool: Tool, problem: Entity, solution: Solution) -> None:
    pred = predict(world, tool, solution)
    child.bump_meme("careful", 1)
    world.facts["predicted_worry"] = pred["worry"]
    world.say(
        f'{child.id} tilted {child.pronoun("possessive")} head. "{tool.label} is funny, '
        f'but it might make the {problem.label} more stuck. We need a smarter fix."'
    )


def solve(world: World, helper: Entity, tool: Tool, solution: Solution, problem: Entity) -> None:
    world.say(
        f'Then {helper.id} tried the better plan: {solution.method}. '
        f'{helper.pronoun().capitalize()} used {tool.label} exactly where the snack was wedged.'
    )
    problem.meters["solved"] = 1.0
    problem.meters["stuck"] = 0.0
    propagate(world, narrate=False)
    world.say(
        f"Pop! Out came the snack at last, as if the crevice had been holding it as a joke."
    )


def celebrate(world: World, child: Entity, helper: Entity, problem: Entity, setting: Setting) -> None:
    child.bump_meme("joy", 1)
    helper.bump_meme("joy", 1)
    world.say(
        f"{child.id} laughed so hard {child.pronoun('possessive')} shoulders shook. "
        f'"We solved it!" {child.id} cheered.'
    )
    world.say(
        f"After that, the {problem.label} sat safe on the table, and the {setting.dark_spot} looked much less mysterious."
    )


def tell(setting: Setting, problem_cfg: Problem, tool: Tool, solution: Solution,
         child_name: str = "Mia", child_gender: str = "girl",
         helper_name: str = "Robo", helper_gender: str = "thing",
         parent_name: str = "Dad") -> World:
    world = World(setting)
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender, role="helper"))
    parent = world.add(Entity(id=parent_name, kind="character", type="father", role="parent"))
    problem = world.add(Entity(id="problem", type="snack", label=problem_cfg.label, attrs={"problem": problem_cfg}))
    problem.meters["stuck"] = 1.0
    world.facts["setting"] = setting
    world.facts["problem_cfg"] = problem_cfg
    world.facts["tool"] = tool
    world.facts["solution"] = solution
    world.facts["child"] = child
    world.facts["helper"] = helper
    world.facts["parent"] = parent
    world.facts["problem"] = problem

    introduce(world, child, helper, setting)
    world.para()
    show_problem(world, child, problem, setting)
    try_silly_fix(world, helper, tool, problem)
    warn(world, child, helper, tool, problem, solution)
    world.para()
    solve(world, helper, tool, solution, problem)
    celebrate(world, child, helper, problem, setting)
    world.facts["outcome"] = "solved"
    return world


SETTINGS = {
    "kitchen": Setting("kitchen", "the kitchen", "the little crevice behind the stove", "The counters were crowded with bowls and spoons.", "the kitchen cave"),
    "pantry": Setting("pantry", "the pantry", "the skinny crevice between the shelves", "The jars stood in neat rows like sleepy soldiers.", "the pantry tunnel"),
    "workshop": Setting("workshop", "the workshop", "the crevice under the bench", "The bench was covered in sawdust and cheerful screws.", "the workshop burrow"),
}

PROBLEMS = {
    "prune": Problem("prune", "prune", "a prune", "crevice", 3, tags={"crevice", "prune"}),
    "toycar": Problem("toycar", "toy car", "a toy car", "crevice", 3, tags={"crevice"}),
    "cookie": Problem("cookie", "cookie", "a cookie", "crevice", 2, tags={"crevice"}),
}

TOOLS = {
    "spoon": Tool("spoon", "a spoon", "scoop out", 1, 2, 3, tags={"kitchen"}),
    "hook": Tool("hook", "a bent hook", "wiggle loose", 2, 1, 3, tags={"workshop"}),
    "tweezer": Tool("tweezer", "a pair of tweezers", "pinch free", 2, 1, 3, tags={"crevice"}),
    "blower": Tool("blower", "a tiny air blower", "blow it free", 1, 3, 2, tags={"crevice"}),
}

SOLUTIONS = {
    "pry": Solution("pry", "pry gently", "pry gently from both sides", 2, 3, tags={"crevice"}),
    "sweep": Solution("sweep", "sweep crumbs away first", "sweep the crumbs away first", 1, 3, tags={"kitchen"}),
    "wiggle": Solution("wiggle", "wiggle and tip", "wiggle the prize and tip the board", 1, 2, tags={"workshop"}),
}

CHILD_NAMES = ["Mia", "Nora", "Leo", "Ben", "Ava", "Max"]
HELPER_NAMES = ["Robo", "Beep", "Gizmo", "Milo", "Tess"]


@dataclass
class StoryParams:
    setting: str
    problem: str
    tool: str
    solution: str
    child_name: str
    child_gender: str
    helper_name: str
    helper_gender: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for pid, problem in PROBLEMS.items():
            if not problem_at_risk(problem, setting):
                continue
            for tid, tool in TOOLS.items():
                for sol_id, sol in SOLUTIONS.items():
                    if solution_succeeds(tool, sol, problem):
                        combos.append((sid, pid, tid, sol_id))
    return combos


def explain_rejection(setting: Setting, problem: Problem) -> str:
    return f"(No story: this setting doesn't naturally create a comic crevice problem with {problem.label}.)"


def explain_tool(tool: Tool) -> str:
    better = ", ".join(sorted(t.id for t in sensible_tools()))
    return f"(Refusing tool '{tool.id}': it scores too low on common sense. Try: {better}.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Comedy problem-solving storyworld about a crevice, a stuck snack, and a clever fix.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--solution", choices=SOLUTIONS)
    ap.add_argument("--child-name")
    ap.add_argument("--helper-name")
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
    if args.tool and TOOLS[args.tool].sense < SENSE_MIN:
        raise StoryError(explain_tool(TOOLS[args.tool]))
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.problem is None or c[1] == args.problem)
              and (args.tool is None or c[2] == args.tool)
              and (args.solution is None or c[3] == args.solution)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    sid, pid, tid, sol_id = rng.choice(sorted(combos))
    child_gender = "girl" if rng.random() < 0.5 else "boy"
    helper_gender = "thing"
    return StoryParams(
        sid, pid, tid, sol_id,
        args.child_name or rng.choice(CHILD_NAMES),
        child_gender,
        args.helper_name or rng.choice(HELPER_NAMES),
        helper_gender,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    setting = f["setting"]
    problem = f["problem_cfg"]
    tool = f["tool"]
    return [
        f'Write a funny story for a preschooler set in {setting.place} that uses the words "crevice" and "prune".',
        f"Tell a comedy story where {f['child'].id} and {f['helper'].id} try to get a {problem.label} out of a crevice with {tool.label}, then solve it more cleverly.",
        f'Write a small problem-solving story where a snack is stuck in a crevice and the characters eventually make a better plan.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    setting = f["setting"]
    problem = f["problem_cfg"]
    tool = f["tool"]
    sol = f["solution"]
    return [
        QAItem(
            question="What was the problem in the story?",
            answer=f"A {problem.label} was stuck in a crevice, so the children had to figure out how to free it.",
        ),
        QAItem(
            question="Why didn't the first idea work very well?",
            answer=f"{helper.id} tried {tool.label}, but that was more silly than useful. It made the moment funnier, yet the snack still needed a smarter plan.",
        ),
        QAItem(
            question="How did they solve the problem?",
            answer=f"They used {tool.label} together with the better plan to {sol.method}. That gave them enough careful force to pull the {problem.label} out.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a crevice?",
            answer="A crevice is a very narrow crack or gap where something small can get wedged.",
        ),
        QAItem(
            question="What does it mean to prune a plant?",
            answer="To prune a plant means to trim off small parts so it can grow neatly and stay healthy.",
        ),
        QAItem(
            question="Why can a narrow space be tricky?",
            answer="A narrow space can trap small things and make it hard to reach them with your fingers.",
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
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
problem_at_risk(P, S) :- problem(P), setting(S), crevice_setting(S), stuck_in(P, crevice).
sensible(T) :- tool(T), sense(T, S), sense_min(M), S >= M.
valid(S, P, T, L) :- problem_at_risk(P, S), tool(T), solution(L), tool_power(T, TP), sol_power(L, LP), mag(P, M), TP + LP >= M.
outcome(solved) :- valid(_, _, _, _).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
        lines.append(asp.fact("crevice_setting", sid))
    for pid, p in PROBLEMS.items():
        lines.append(asp.fact("problem", pid))
        lines.append(asp.fact("stuck_in", pid, p.stuck_in))
        lines.append(asp.fact("mag", pid, p.magnitude))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        lines.append(asp.fact("sense", tid, t.sense))
        lines.append(asp.fact("tool_power", tid, t.power))
    for lid, l in SOLUTIONS.items():
        lines.append(asp.fact("solution", lid))
        lines.append(asp.fact("sol_power", lid, l.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program("#show sensible/1."))
    return sorted(t for (t,) in asp.atoms(model, "sensible"))


def asp_verify() -> int:
    import asp
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        print("MISMATCH in gate.")
        rc = 1
    if set(asp_sensible()) == {t.id for t in sensible_tools()}:
        print("OK: sensible tools match.")
    else:
        print("MISMATCH in sensible tools.")
        rc = 1
    try:
        sample = generate(CURATED[0])
        assert sample.story
        print("OK: generate() smoke test passed.")
    except Exception as exc:
        print(f"FAIL: generate() smoke test crashed: {exc}")
        rc = 1
    return rc


CURATED = [
    StoryParams("kitchen", "prune", "tweezer", "pry", "Mia", "girl", "Robo", "thing"),
    StoryParams("pantry", "toycar", "hook", "wiggle", "Leo", "boy", "Beep", "thing"),
    StoryParams("workshop", "cookie", "blower", "pry", "Ava", "girl", "Gizmo", "thing"),
]


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.setting],
        PROBLEMS[params.problem],
        TOOLS[params.tool],
        SOLUTIONS[params.solution],
        params.child_name,
        params.child_gender,
        params.helper_name,
        params.helper_gender,
    )
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
        print(asp_program("#show valid/4.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible tools: {', '.join(asp_sensible())}\n")
        for row in asp_valid_combos():
            print("  ", row)
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
