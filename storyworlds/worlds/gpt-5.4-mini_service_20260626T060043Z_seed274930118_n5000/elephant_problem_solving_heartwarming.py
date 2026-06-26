#!/usr/bin/env python3
"""
A heartwarming story world about an elephant who solves a small problem by
thinking carefully, asking for help, and sharing a kind result.

Seed premise:
An elephant notices a friend is upset because something useful is stuck or
broken. The elephant tries a few gentle ideas, finds a better way, and leaves
everyone feeling cared for.
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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"elephant"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"child", "boy", "girl"}:
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the meadow"


@dataclass
class Problem:
    id: str
    noun: str
    phrase: str
    trouble: str
    fix_hint: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    helps: set[str]
    method: str
    result: str


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
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = dict(self.facts)
        return c


@dataclass
class StoryParams:
    setting: str
    problem: str
    tool: str
    name: str
    helper: str
    seed: Optional[int] = None


SETTINGS = {
    "meadow": Setting(place="the meadow"),
    "riverside": Setting(place="the riverside"),
    "orchard": Setting(place="the orchard"),
    "village": Setting(place="the village path"),
}

PROBLEMS = {
    "stuck_ball": Problem(
        id="stuck_ball",
        noun="ball",
        phrase="a bright red ball stuck in a low tree",
        trouble="stuck too high to reach",
        fix_hint="use a long stick and a careful push",
        tags={"tree", "ball", "stuck"},
    ),
    "dropped_lantern": Problem(
        id="dropped_lantern",
        noun="lantern",
        phrase="a paper lantern that blew under a bench",
        trouble="stuck in a dark, dusty corner",
        fix_hint="slide it out gently with a flat board",
        tags={"lantern", "dark", "stuck"},
    ),
    "broken_bridge": Problem(
        id="broken_bridge",
        noun="bridge",
        phrase="a small bridge with one loose plank",
        trouble="unsafe to step on",
        fix_hint="find a sturdy plank and ask for help carrying it",
        tags={"bridge", "repair", "help"},
    ),
    "lost_seeds": Problem(
        id="lost_seeds",
        noun="seeds",
        phrase="a pouch of flower seeds spilled in the dirt",
        trouble="spread everywhere in the mud",
        fix_hint="scoop them into a basket and clean the path",
        tags={"seeds", "mud", "gather"},
    ),
}

TOOLS = {
    "stick": Tool(
        id="stick",
        label="a long stick",
        helps={"stuck", "tree"},
        method="reached up and nudged the branch",
        result="the ball came down softly",
    ),
    "board": Tool(
        id="board",
        label="a flat board",
        helps={"dark", "stuck", "lantern"},
        method="slid the board under the lantern",
        result="the lantern rolled back into the light",
    ),
    "plank": Tool(
        id="plank",
        label="a sturdy plank",
        helps={"bridge", "repair", "help"},
        method="placed the plank across the gap",
        result="the bridge felt safe again",
    ),
    "basket": Tool(
        id="basket",
        label="a woven basket",
        helps={"seeds", "gather", "mud"},
        method="scooped the seeds up one careful handful at a time",
        result="the seeds were safe and tidy",
    ),
}

NAMES = ["Mina", "Tara", "Leah", "Nia", "Oona", "Ravi", "Noor", "Kito"]


class ReasoningError(StoryError):
    pass


def problem_needs_tool(problem: Problem, tool: Tool) -> bool:
    return bool(problem.tags & tool.helps)


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for sid in SETTINGS:
        for pid, prob in PROBLEMS.items():
            for tid, tool in TOOLS.items():
                if problem_needs_tool(prob, tool):
                    out.append((sid, pid, tid))
    return out


def explain_rejection(problem: Problem, tool: Tool) -> str:
    return (
        f"(No story: {tool.label} does not really solve {problem.phrase}. "
        f"Please choose a tool that can genuinely help.)"
    )


def introduce(world: World, elephant: Entity, helper: Entity, problem: Problem) -> None:
    world.say(
        f"{elephant.id} was a gentle elephant who noticed small troubles right away. "
        f"One day, {helper.id} looked worried because {problem.phrase}."
    )


def empathize(world: World, elephant: Entity, helper: Entity, problem: Problem) -> None:
    elephant.memes["care"] = elephant.memes.get("care", 0) + 1
    world.say(
        f"{elephant.id} walked closer and listened. {helper.id} explained that the problem was "
        f"{problem.trouble}."
    )


def try_one(world: World, elephant: Entity, tool: Tool, problem: Problem) -> None:
    elephant.memes["curiosity"] = elephant.memes.get("curiosity", 0) + 1
    world.say(
        f"{elephant.id} thought for a moment, then picked up {tool.label}. "
        f"{tool.method.capitalize()}."
    )
    world.say(
        f"But the first try did not finish the job the easy way, so {elephant.id} paused and tried again more carefully."
    )


def solve(world: World, elephant: Entity, helper: Entity, tool: Tool, problem: Problem) -> None:
    elephant.meters["effort"] = elephant.meters.get("effort", 0) + 1
    helper.memes["relief"] = helper.memes.get("relief", 0) + 1
    world.say(
        f"This time, {elephant.id} used {tool.label} just right. {tool.result.capitalize()}, and {helper.id} smiled."
    )
    world.say(
        f"Together they fixed the little trouble, and the {problem.noun} was ready to use again."
    )


def ending(world: World, elephant: Entity, helper: Entity, problem: Problem) -> None:
    world.say(
        f"{helper.id} thanked {elephant.id} with a warm hug around {elephant.id}'s trunk. "
        f"{elephant.id} felt proud, and the meadow felt peaceful again."
    )


def tell(setting: Setting, problem: Problem, tool: Tool, name: str, helper_name: str) -> World:
    world = World(setting)
    elephant = world.add(Entity(id=name, kind="character", type="elephant", label=name))
    helper = world.add(Entity(id=helper_name, kind="character", type="child", label=helper_name))
    item = world.add(Entity(id="problem", type=problem.noun, label=problem.noun, phrase=problem.phrase))

    introduce(world, elephant, helper, problem)
    world.para()
    empathize(world, elephant, helper, problem)
    try_one(world, elephant, tool, problem)
    solve(world, elephant, helper, tool, problem)
    world.para()
    ending(world, elephant, helper, problem)

    world.facts.update(
        elephant=elephant,
        helper=helper,
        problem=problem,
        tool=tool,
        item=item,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    prob: Problem = f["problem"]
    tool: Tool = f["tool"]
    elephant: Entity = f["elephant"]
    helper: Entity = f["helper"]
    return [
        f'Write a warm story about an elephant who helps a friend solve "{prob.noun}" trouble.',
        f"Tell a heartwarming story where {elephant.id} and {helper.id} work together with {tool.label}.",
        f"Write a simple story about kindness, patience, and fixing {prob.phrase}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    elephant: Entity = f["elephant"]
    helper: Entity = f["helper"]
    problem: Problem = f["problem"]
    tool: Tool = f["tool"]
    return [
        QAItem(
            question=f"Who helped solve the problem in the meadow?",
            answer=f"{elephant.id} helped {helper.id} by thinking carefully and using {tool.label}.",
        ),
        QAItem(
            question=f"What was the trouble that {helper.id} had?",
            answer=f"{helper.id} had {problem.phrase}, which was {problem.trouble}.",
        ),
        QAItem(
            question=f"What did {elephant.id} use to fix the problem?",
            answer=f"{elephant.id} used {tool.label}, because it could {tool.method.lower()}.",
        ),
        QAItem(
            question=f"How did everyone feel at the end?",
            answer=f"{helper.id} felt relieved, and {elephant.id} felt proud because the little problem was solved kindly.",
        ),
    ]


WORLD_KNOWLEDGE = {
    "elephant": (
        "What is an elephant?",
        "An elephant is a very big animal with a trunk, large ears, and a kind way of using its body to hold and carry things.",
    ),
    "stuck": (
        "What does stuck mean?",
        "Stuck means something cannot move easily and needs help to come free.",
    ),
    "help": (
        "Why is helping kind?",
        "Helping is kind because it makes a hard job easier for someone else.",
    ),
    "bridge": (
        "What is a bridge for?",
        "A bridge helps people cross over water, mud, or a gap safely.",
    ),
    "seed": (
        "Why do plants need seeds?",
        "Seeds can grow into new plants when they are planted in soil and cared for.",
    ),
}


def world_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["problem"].tags)
    tags.add("elephant")
    if "repair" in tags:
        tags.add("bridge")
    if "help" in tags:
        tags.add("help")
    if "gather" in tags:
        tags.add("seed")
    out: list[QAItem] = []
    for key in ["elephant", "stuck", "help", "bridge", "seed"]:
        if key in tags or key in {"elephant", "help"}:
            q, a = WORLD_KNOWLEDGE[key]
            out.append(QAItem(question=q, answer=a))
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
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(setting="meadow", problem="stuck_ball", tool="stick", name="Mina", helper="Pip"),
    StoryParams(setting="riverside", problem="dropped_lantern", tool="board", name="Tara", helper="Jo"),
    StoryParams(setting="village", problem="broken_bridge", tool="plank", name="Nia", helper="Sam"),
    StoryParams(setting="orchard", problem="lost_seeds", tool="basket", name="Oona", helper="Bea"),
]


ASP_RULES = r"""
problem_needs_tool(P,T) :- problem_tag(P,Tag), tool_helps(T,Tag).
valid_combo(S,P,T) :- setting(S), problem(P), tool(T), problem_needs_tool(P,T).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for pid, prob in PROBLEMS.items():
        lines.append(asp.fact("problem", pid))
        for tag in sorted(prob.tags):
            lines.append(asp.fact("problem_tag", pid, tag))
    for tid, tool in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        for tag in sorted(tool.helps):
            lines.append(asp.fact("tool_helps", tid, tag))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_combo/3."))
    return sorted(set(asp.atoms(model, "valid_combo")))


def asp_verify() -> int:
    a = set(asp_valid_combos())
    b = set(valid_combos())
    if a == b:
        print(f"OK: clingo gate matches valid_combos() ({len(a)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if a - b:
        print("  only in clingo:", sorted(a - b))
    if b - a:
        print("  only in python:", sorted(b - a))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming elephant problem-solving story world.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--name")
    ap.add_argument("--helper")
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
    if args.setting or args.problem or args.tool:
        combos = [
            c for c in combos
            if (args.setting is None or c[0] == args.setting)
            and (args.problem is None or c[1] == args.problem)
            and (args.tool is None or c[2] == args.tool)
        ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, problem, tool = rng.choice(sorted(combos))
    name = args.name or rng.choice(NAMES)
    helper = args.helper or rng.choice([n for n in NAMES if n != name])
    return StoryParams(setting=setting, problem=problem, tool=tool, name=name, helper=helper)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], PROBLEMS[params.problem], TOOLS[params.tool], params.name, params.helper)
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_combo/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, problem, tool) combos:")
        for setting, problem, tool in combos:
            print(f"  {setting:10} {problem:15} {tool}")
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
            header = f"### {p.name}: {p.problem} with {p.tool} in {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
