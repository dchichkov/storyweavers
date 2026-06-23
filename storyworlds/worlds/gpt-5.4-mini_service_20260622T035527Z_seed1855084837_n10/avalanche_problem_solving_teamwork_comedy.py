#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260622T035527Z_seed1855084837_n10/avalanche_problem_solving_teamwork_comedy.py
==============================================================================================================

A small storyworld about a silly avalanche problem that gets solved through teamwork.

The premise: a few children and a helper are stuck when a comic avalanche blocks
a mountain path, and they have to work together to clear a safe route.
The tone stays child-facing and funny, while the world state drives the story:
snow depth grows, the blockage changes, plans are tried, helpers cooperate, and
the ending proves the path is open again.

This script follows the Storyweavers storyworld contract:
- stdlib-only prose engine
- shared QAItem / StoryError / StorySample from results.py
- lazy ASP import through storyworlds/asp.py
- StoryParams, registries, build_parser, resolve_params, generate, emit, main
- default run, -n, --all, --seed, --trace, --qa, --json, --asp, --verify, --show-asp
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve()
for parent in (HERE.parent, *HERE.parents):
    if (parent / "results.py").exists():
        sys.path.insert(0, str(parent))
        break

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
    role: str = ""
    owner: str | None = None
    caretaker: str | None = None
    plural: bool = False
    tags: set[str] = field(default_factory=set)
    attrs: dict[str, Any] = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "sister"}
        male = {"boy", "father", "dad", "man", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def ref(self) -> str:
        return self.phrase or self.label or self.id


@dataclass
class StoryParams:
    route: str
    problem: str
    tool: str
    team: str
    name1: str
    gender1: str
    name2: str
    gender2: str
    helper: str
    helper_gender: str
    seed: int | None = None


@dataclass
class Route:
    id: str
    place: str
    terrain: str
    blocked_by: str
    image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Problem:
    id: str
    label: str
    phrase: str
    obstacle: str
    cause: str
    risk: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    action: str
    result: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, Any] = {}
        self.history: list[dict[str, Any]] = []
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple[str, str]] = set()

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def say(self, sentence: str) -> None:
        if sentence:
            self.paragraphs[-1].append(sentence)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def event(self, kind: str, **data: Any) -> None:
        self.history.append({"kind": kind, **data})

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World()
        clone.entities = {k: Entity(**{
            "id": e.id, "kind": e.kind, "type": e.type, "label": e.label, "phrase": e.phrase,
            "traits": list(e.traits), "role": e.role, "owner": e.owner, "caretaker": e.caretaker,
            "plural": e.plural, "tags": set(e.tags), "attrs": dict(e.attrs),
            "meters": defaultdict(float, dict(e.meters)), "memes": defaultdict(float, dict(e.memes)),
        }) for k, e in self.entities.items()}
        clone.facts = dict(self.facts)
        clone.history = [dict(x) for x in self.history]
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        return clone


def path_name(route: Route) -> str:
    return route.place


def route_is_blocked(route: Route, problem: Problem) -> bool:
    return problem.obstacle == route.blocked_by


def tool_can_help(tool: Tool, problem: Problem, route: Route) -> bool:
    return problem.id in tool.tags and route.id in tool.tags


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for rid, route in ROUTES.items():
        for pid, problem in PROBLEMS.items():
            for tid, tool in TOOLS.items():
                if route_is_blocked(route, problem) and tool_can_help(tool, problem, route):
                    combos.append((rid, pid, tid))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Avalanche teamwork comedy storyworld.")
    ap.add_argument("--route", choices=ROUTES)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--team", choices=["siblings", "friends"])
    ap.add_argument("--name1")
    ap.add_argument("--gender1", choices=["girl", "boy"])
    ap.add_argument("--name2")
    ap.add_argument("--gender2", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=["ranger", "parent", "neighbor"])
    ap.add_argument("--helper-gender", choices=["woman", "man"])
    ap.add_argument("-n", "--n", type=int, default=1)
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
    combos = [c for c in valid_combos()
              if (args.route is None or c[0] == args.route)
              and (args.problem is None or c[1] == args.problem)
              and (args.tool is None or c[2] == args.tool)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    route, problem, tool = rng.choice(sorted(combos))
    team = args.team or rng.choice(["siblings", "friends"])
    gender1 = args.gender1 or rng.choice(["girl", "boy"])
    gender2 = args.gender2 or ("boy" if gender1 == "girl" else "girl")
    name1 = args.name1 or rng.choice(GIRL_NAMES if gender1 == "girl" else BOY_NAMES)
    name2 = args.name2 or rng.choice([n for n in (GIRL_NAMES if gender2 == "girl" else BOY_NAMES) if n != name1])
    helper = args.helper or rng.choice(["ranger", "parent", "neighbor"])
    helper_gender = args.helper_gender or ("woman" if helper != "neighbor" else rng.choice(["woman", "man"]))
    return StoryParams(route=route, problem=problem, tool=tool, team=team,
                       name1=name1, gender1=gender1, name2=name2, gender2=gender2,
                       helper=helper, helper_gender=helper_gender)


def predict_clear(world: World, route: Entity, problem: Entity, tool: Entity) -> bool:
    return bool(route.meters["blocked"] >= THRESHOLD and tool.meters["helpful"] >= THRESHOLD and problem.meters["avalanche"] >= THRESHOLD)


def setup_world(params: StoryParams) -> World:
    world = World()
    route = world.add(Entity(id="route", kind="thing", type="route", label=ROUTES[params.route].place,
                             phrase=ROUTES[params.route].place, tags=set(ROUTES[params.route].tags)))
    problem = world.add(Entity(id="problem", kind="thing", type="problem", label=PROBLEMS[params.problem].label,
                               phrase=PROBLEMS[params.problem].phrase, tags=set(PROBLEMS[params.problem].tags)))
    tool = world.add(Entity(id="tool", kind="thing", type="tool", label=TOOLS[params.tool].label,
                            phrase=TOOLS[params.tool].phrase, tags=set(TOOLS[params.tool].tags)))
    route.meters["blocked"] = 1.0
    problem.meters["avalanche"] = 1.0
    tool.meters["helpful"] = 1.0
    world.facts.update(route=route, problem=problem, tool=tool)
    return world


def story_opening(world: World, c1: Entity, c2: Entity, helper: Entity, route: Route, problem: Problem) -> None:
    world.say(f"{c1.id} and {c2.id} came to {route.place} with big boots and even bigger opinions.")
    world.say(f"The path looked fine until the {problem.label} sat in the way like a giant sleepy pillow.")
    world.say(f"{problem.risk.capitalize()}, and the mountain made a very rude rumble.")


def teamwork_turn(world: World, c1: Entity, c2: Entity, helper: Entity, problem: Problem, tool: Tool) -> None:
    c1.memes["worry"] += 1
    c2.memes["worry"] += 1
    helper.memes["calm"] += 1
    world.say(f'"An avalanche," said {c1.id}, who sounded brave only for the first half of the sentence.')
    world.say(f'{c2.id} peered up. "I vote we do not get bonked by the mountain," {c2.pronoun()} said.')
    world.say(f"{helper.id} arrived with a grin and {tool.phrase}.")
    world.say(f'"Let\'s solve this together," {helper.pronoun()} said. "You two can handle the small jobs."')


def clear_path(world: World, c1: Entity, c2: Entity, helper: Entity, route: Route, problem: Problem, tool: Tool) -> None:
    c1.memes["joy"] += 1
    c2.memes["joy"] += 1
    helper.memes["pride"] += 1
    route.meters["blocked"] = 0.0
    problem.meters["avalanche"] = 0.0
    world.say(f"{c1.id} shoveled the left side, {c2.id} dragged branches away, and {helper.id} packed the snow into a silly wall.")
    world.say(f"Then {tool.action}, and the giant snowy mess gave up with a soft poof.")
    world.say(f"The path opened wide, and the only thing left of the avalanche was a lopsided snow lump wearing the shape of a hat.")


def ending_image(world: World, c1: Entity, c2: Entity, helper: Entity, route: Route) -> None:
    world.say(f"At the end, {c1.id}, {c2.id}, and {helper.id} marched down {route.place} in a careful line, all laughing.")
    world.say(f"The mountain stayed quiet, the sun glittered on the fresh snow, and the cleared path looked proud of itself.")


def tell(params: StoryParams) -> World:
    world = setup_world(params)
    route_cfg = ROUTES[params.route]
    problem_cfg = PROBLEMS[params.problem]
    tool_cfg = TOOLS[params.tool]
    c1 = world.add(Entity(id=params.name1, kind="character", type=params.gender1, role="child"))
    c2 = world.add(Entity(id=params.name2, kind="character", type=params.gender2, role="child"))
    helper = world.add(Entity(id=params.helper, kind="character", type=params.helper_gender, role="helper"))
    story_opening(world, c1, c2, helper, route_cfg, problem_cfg)
    world.para()
    teamwork_turn(world, c1, c2, helper, problem_cfg, tool_cfg)
    world.para()
    clear_path(world, c1, c2, helper, route_cfg, problem_cfg, tool_cfg)
    world.para()
    ending_image(world, c1, c2, helper, route_cfg)
    world.facts.update(c1=c1, c2=c2, helper=helper, route_cfg=route_cfg, problem_cfg=problem_cfg, tool_cfg=tool_cfg)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a funny short story for a young child about an avalanche blocking {f["route_cfg"].place} that gets solved by teamwork.',
        f"Tell a comedic problem-solving story where {f['c1'].id} and {f['c2'].id} help {f['helper'].id} clear an avalanche with {f['tool_cfg'].phrase}.",
        f'Write a child-friendly story that uses the word "avalanche" and ends with a cleared mountain path and a joke-like snow image.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    route_cfg = f["route_cfg"]
    problem_cfg = f["problem_cfg"]
    tool_cfg = f["tool_cfg"]
    c1 = f["c1"]
    c2 = f["c2"]
    helper = f["helper"]
    return [
        QAItem(
            question=f"Why did {c1.id} and {c2.id} need a plan at {route_cfg.place}?",
            answer=f"They needed a plan because the avalanche blocked the path. The snow was piled up too high for a quick walk, so they had to solve the problem together.",
        ),
        QAItem(
            question=f"What did {helper.id} bring to help with the avalanche?",
            answer=f"{helper.id} brought {tool_cfg.phrase}. It gave the group a practical way to move the snow instead of just staring at it.",
        ),
        QAItem(
            question=f"How did {c1.id}, {c2.id}, and {helper.id} work together?",
            answer=f"{c1.id} shoveled, {c2.id} moved the loose pieces, and {helper.id} kept the plan on track. Each one did a different job, and that teamwork made the solution work.",
        ),
        QAItem(
            question=f"What changed at the end of the story?",
            answer=f"The avalanche was cleared and {route_cfg.place} was open again. The ending shows the path safe and the children laughing, which proves their problem solving worked.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an avalanche?",
            answer="An avalanche is a lot of snow sliding down a mountain all at once. It can block a path and make travel hard until people clear it safely.",
        ),
        QAItem(
            question="Why is teamwork useful during a problem?",
            answer="Teamwork helps because different people can do different jobs at the same time. That makes a big problem feel smaller and often gets the job done faster.",
        ),
        QAItem(
            question="What is a safe thing to do if snow blocks a trail?",
            answer="A safe thing to do is stop, stay calm, and work with a grown-up or helper to clear the way or choose another route. Nobody should rush into dangerous snow.",
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
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if any(v for v in e.meters.values()):
            bits.append(f"meters={dict(e.meters)}")
        if any(v for v in e.memes.values()):
            bits.append(f"memes={dict(e.memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  history events: {len(world.history)}")
    return "\n".join(lines)


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


ROUTES = {
    "ridge": Route(id="ridge", place="the ski ridge", terrain="snowy ridge", blocked_by="snowbank",
                   image="a bright ridge", tags={"ridge", "avalanche"}),
    "cabin": Route(id="cabin", place="the cabin trail", terrain="pine trail", blocked_by="snowdrift",
                   image="a warm trail", tags={"cabin", "avalanche"}),
    "bridge": Route(id="bridge", place="the bridge path", terrain="narrow bridge", blocked_by="snowpile",
                    image="a narrow path", tags={"bridge", "avalanche"}),
}

PROBLEMS = {
    "snowbank": Problem(id="snowbank", label="snowbank", phrase="a huge snowbank", obstacle="snowbank",
                        cause="the mountain let out a boom", risk="The snow could slide again", tags={"snowbank", "avalanche"}),
    "snowdrift": Problem(id="snowdrift", label="snowdrift", phrase="a crooked snowdrift", obstacle="snowdrift",
                         cause="the wind had piled snow high", risk="The drift made the trail slippery", tags={"snowdrift", "avalanche"}),
    "snowpile": Problem(id="snowpile", label="snowpile", phrase="a tall snowpile", obstacle="snowpile",
                        cause="the slope had dumped snow onto the path", risk="The pile blocked every careful step", tags={"snowpile", "avalanche"}),
}

TOOLS = {
    "shovel": Tool(id="shovel", label="shovel", phrase="a bright red shovel", action="the shovel scooped away one heavy scoop after another", result="cleared snow", tags={"snowbank", "snowdrift", "snowpile", "avalanche"}),
    "rope": Tool(id="rope", label="rope", phrase="a long rope", action="the rope helped them pull loose snow out in a tidy line", result="moved snow", tags={"snowbank", "snowdrift", "snowpile", "avalanche"}),
    "sled": Tool(id="sled", label="sled", phrase="a silly blue sled", action="the sled carried snow like a goofy delivery cart", result="moved snow", tags={"snowbank", "snowdrift", "snowpile", "avalanche"}),
}

GIRL_NAMES = ["Maya", "Lina", "Zoe", "Pia", "Nora"]
BOY_NAMES = ["Ben", "Leo", "Max", "Owen", "Toby"]


CURATED = [
    StoryParams(route="ridge", problem="snowbank", tool="shovel", team="siblings", name1="Maya", gender1="girl", name2="Ben", gender2="boy", helper="ranger", helper_gender="woman"),
    StoryParams(route="cabin", problem="snowdrift", tool="rope", team="friends", name1="Leo", gender1="boy", name2="Nora", gender2="girl", helper="parent", helper_gender="man"),
    StoryParams(route="bridge", problem="snowpile", tool="sled", team="siblings", name1="Zoe", gender1="girl", name2="Toby", gender2="boy", helper="neighbor", helper_gender="woman"),
]


ASP_RULES = r"""
blocked(R,P) :- route(R), problem(P), blocks(P,RB), route_block(R,RB).
helps(T,P,R) :- tool(T), problem(P), route(R), tool_for(T,P), tool_for(T,R).
valid(R,P,T) :- route(R), problem(P), tool(T), blocked(R,P), helps(T,P,R).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for rid, r in ROUTES.items():
        lines.append(asp.fact("route", rid))
        lines.append(asp.fact("route_block", rid, r.blocked_by))
    for pid, p in PROBLEMS.items():
        lines.append(asp.fact("problem", pid))
        lines.append(asp.fact("blocks", pid, p.obstacle))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        lines.append(asp.fact("tool_for", tid, "avalanche"))
        lines.append(asp.fact("tool_for", tid, t.tags and next(iter(sorted(t.tags)))))
        for tag in sorted(t.tags):
            lines.append(asp.fact("tool_for", tid, tag))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import io
    import contextlib
    import asp
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    ok = 0
    if py != cl:
        ok = 1
        print("MISMATCH between ASP and Python valid_combos().")
        print("python-only:", sorted(py - cl))
        print("asp-only:", sorted(cl - py))
    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise RuntimeError("empty story")
    except Exception as exc:
        print(f"Smoke test failed: {exc}")
        return 1
    try:
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            emit(sample, trace=False, qa=False)
    except Exception as exc:
        print(f"Emit smoke test failed: {exc}")
        return 1
    if ok == 0:
        print(f"OK: ASP matches Python on {len(py)} combos; generation and emit succeeded.")
    return ok


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def asp_solve_list() -> list[tuple]:
    return asp_valid_combos()


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_solve_list()
        print(f"{len(combos)} compatible combos:")
        for row in combos:
            print("  ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 40):
            i += 1
            seed = base_seed + i
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
