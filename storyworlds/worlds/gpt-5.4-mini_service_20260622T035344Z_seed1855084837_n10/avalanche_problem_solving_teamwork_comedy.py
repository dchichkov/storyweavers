#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260622T035344Z_seed1855084837_n10/avalanche_problem_solving_teamwork_comedy.py
========================================================================================================================

A small story world about a goofy mountain rescue: a harmless avalanche blocks a
trail, a team of kids solves the problem together, and the ending proves their
plan worked.

The world is built around a comedic teamwork premise:
- a tiny avalanche blocks a path to a picnic lookout
- the children improvise with ropes, shovels, and a map
- each run ends with a clear state change and a playful payoff

This script follows the Storyweavers contract:
- standalone stdlib script
- imports storyworlds/results.py eagerly
- imports storyworlds/asp.py lazily inside ASP helpers
- exposes StoryParams, build_parser, resolve_params, generate, emit, main
- supports -n, --all, --seed, --trace, --qa, --json, --asp, --verify, --show-asp
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

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
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    plural: bool = False
    tags: set[str] = field(default_factory=set)
    attrs: dict[str, Any] = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "sister", "aunt"}
        male = {"boy", "father", "dad", "man", "brother", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def ref(self) -> str:
        return self.phrase or self.label or self.id


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
        clone.entities = {k: _deepcopy_entity(v) for k, v in self.entities.items()}
        clone.facts = json.loads(json.dumps(self.facts, ensure_ascii=False))
        clone.history = json.loads(json.dumps(self.history, ensure_ascii=False))
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        return clone


def _deepcopy_entity(ent: Entity) -> Entity:
    clone = Entity(
        id=ent.id,
        kind=ent.kind,
        type=ent.type,
        label=ent.label,
        phrase=ent.phrase,
        traits=list(ent.traits),
        role=ent.role,
        owner=ent.owner,
        caretaker=ent.caretaker,
        plural=ent.plural,
        tags=set(ent.tags),
        attrs=json.loads(json.dumps(ent.attrs, ensure_ascii=False)),
    )
    clone.meters = defaultdict(float, ent.meters)
    clone.memes = defaultdict(float, ent.memes)
    return clone


@dataclass
class Setting:
    place: str
    affordances: set[str] = field(default_factory=set)


@dataclass
class Problem:
    id: str
    label: str
    description: str
    hazard: str
    block_phrase: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    purpose: str
    tags: set[str] = field(default_factory=set)


@dataclass
class TeamMove:
    id: str
    name: str
    lead: str
    support: str
    effect: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    setting: str = "mountain_path"
    problem: str = "avalanche"
    tool: str = "rope"
    move: str = "spread_out"
    name_a: str = "Mia"
    gender_a: str = "girl"
    name_b: str = "Noah"
    gender_b: str = "boy"
    helper: str = "grandpa"
    seed: Optional[int] = None


SETTINGS = {
    "mountain_path": Setting(place="the mountain path", affordances={"avalanche"}),
    "ski_lodge": Setting(place="the snowy slope behind the ski lodge", affordances={"avalanche"}),
    "pine_trail": Setting(place="the pine trail", affordances={"avalanche"}),
}

PROBLEMS = {
    "avalanche": Problem(
        id="avalanche",
        label="avalanche",
        description="a small avalanche of snow and ice",
        hazard="snow piled across the trail",
        block_phrase="a white wall of snow",
        tags={"avalanche", "snow", "ice"},
    )
}

TOOLS = {
    "rope": Tool(id="rope", label="rope", phrase="a bright orange rope", purpose="pull people safely", tags={"rope"}),
    "shovel": Tool(id="shovel", label="shovel", phrase="a tiny shovel", purpose="dig snow away", tags={"shovel"}),
    "map": Tool(id="map", label="map", phrase="a crinkly trail map", purpose="find the safest way", tags={"map"}),
}

MOVES = {
    "spread_out": TeamMove(
        id="spread_out",
        name="spread out",
        lead="one kid marks the safe edge",
        support="the other clears a path",
        effect="they make the buried trail easier to cross",
        tags={"teamwork", "problem_solving"},
    ),
    "build_chain": TeamMove(
        id="build_chain",
        name="build a human chain",
        lead="one child anchors the rope",
        support="the other passes the shovel down the line",
        effect="they move snow without slipping",
        tags={"teamwork", "problem_solving"},
    ),
    "follow_tracks": TeamMove(
        id="follow_tracks",
        name="follow the tracks",
        lead="one child reads the map",
        support="the other watches the snowbank",
        effect="they avoid the risky drift and reach the lookout",
        tags={"teamwork", "problem_solving"},
    ),
}

GIRL_NAMES = ["Mia", "Zoe", "Ava", "Ella", "Nora", "Lily", "Ruby"]
BOY_NAMES = ["Noah", "Leo", "Ben", "Eli", "Theo", "Max", "Finn"]
TRAITS = ["cheerful", "curious", "lively", "funny", "brave", "careful"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for setting_id in SETTINGS:
        for problem_id in PROBLEMS:
            for tool_id in TOOLS:
                if problem_id == "avalanche" and tool_id in {"rope", "shovel", "map"}:
                    combos.append((setting_id, problem_id, tool_id))
    return combos


def explain_rejection(setting_id: str, problem_id: str, tool_id: str) -> str:
    setting = SETTINGS[setting_id]
    tool = TOOLS[tool_id]
    return (
        f"(No story: {tool.label} is a reasonable tool for an {problem_id}, and "
        f"{setting.place} can host the scene; the rejection path is reserved for invalid explicit filters.)"
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A comedic teamwork story world with a small avalanche.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--move", choices=MOVES)
    ap.add_argument("--name-a")
    ap.add_argument("--gender-a", choices=["girl", "boy"])
    ap.add_argument("--name-b")
    ap.add_argument("--gender-b", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=["grandpa", "aunt", "ranger"])
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
    setting_id = args.setting or rng.choice(sorted(SETTINGS))
    problem_id = args.problem or "avalanche"
    tool_id = args.tool or rng.choice(sorted(TOOLS))
    move_id = args.move or rng.choice(sorted(MOVES))
    if (setting_id, problem_id, tool_id) not in valid_combos():
        raise StoryError("No valid avalanche story matches those options.")
    name_a = args.name_a or rng.choice(GIRL_NAMES if (args.gender_a or rng.choice(["girl", "boy"])) == "girl" else BOY_NAMES)
    gender_a = args.gender_a or ("girl" if name_a in GIRL_NAMES else "boy")
    name_b = args.name_b or rng.choice([n for n in (GIRL_NAMES + BOY_NAMES) if n != name_a])
    gender_b = args.gender_b or ("girl" if name_b in GIRL_NAMES else "boy")
    helper = args.helper or rng.choice(["grandpa", "aunt", "ranger"])
    return StoryParams(
        setting=setting_id,
        problem=problem_id,
        tool=tool_id,
        move=move_id,
        name_a=name_a,
        gender_a=gender_a,
        name_b=name_b,
        gender_b=gender_b,
        helper=helper,
    )


def _pair_noun(a: Entity, b: Entity) -> str:
    if a.type == "girl" and b.type == "girl":
        return "two girls"
    if a.type == "boy" and b.type == "boy":
        return "two boys"
    return "two kids"


def _do_problem(world: World, problem: Entity, team: list[Entity]) -> None:
    problem.meters["blocked"] += 1
    for kid in team:
        kid.memes["surprise"] += 1
    world.event("problem", id=problem.id, blocked=True)


def _solve_problem(world: World, team: list[Entity], tool: Entity, move: TeamMove, helper: Entity) -> None:
    for kid in team:
        kid.memes["joy"] += 1
        kid.memes["teamwork"] += 1
    tool.meters["used"] += 1
    world.get("trail").meters["cleared"] += 1
    world.get("trail").memes["safe"] += 1
    world.event("solution", move=move.id, tool=tool.id, helper=helper.id)


def tell(setting: Setting, problem: Problem, tool: Tool, move: TeamMove, name_a: str, gender_a: str, name_b: str, gender_b: str, helper_name: str) -> World:
    world = World()
    a = world.add(Entity(id=name_a, kind="character", type=gender_a, role="kid"))
    b = world.add(Entity(id=name_b, kind="character", type=gender_b, role="kid"))
    helper = world.add(Entity(id=helper_name, kind="character", type="adult", role="helper", label=helper_name))
    trail = world.add(Entity(id="trail", kind="thing", type="trail", label=setting.place))
    problem_ent = world.add(Entity(id=problem.id, kind="thing", type="problem", label=problem.label, phrase=problem.description, tags=set(problem.tags)))
    tool_ent = world.add(Entity(id=tool.id, kind="thing", type="tool", label=tool.label, phrase=tool.phrase, tags=set(tool.tags)))
    world.facts.update(setting=setting, problem=problem, tool=tool, move=move, a=a, b=b, helper=helper, trail=trail, problem_ent=problem_ent, tool_ent=tool_ent)
    a.memes["curiosity"] += 1
    b.memes["curiosity"] += 1

    world.say(f"{a.id} and {b.id} were hiking along {setting.place} with {helper.label}.")
    world.say(f"They wanted to get to the lookout for snacks, but suddenly there was {problem.block_phrase} blocking the trail.")
    world.para()
    world.say(f"{a.id} stared at the snow and said, \"Well, that is a very rude pile.\"")
    world.say(f"{b.id} blinked. \"I think the mountain just sneezed.\"")
    _do_problem(world, problem_ent, [a, b])

    world.para()
    world.say(f"{helper.label.capitalize()} looked at the mess and said, \"Good news: we can fix this with {tool.phrase}.\"")
    world.say(f"{move.lead.capitalize()}, {move.support}, and together they {move.name}.")
    _solve_problem(world, [a, b], tool_ent, move, helper)

    world.para()
    world.say(f"After a lot of careful scooping and one heroic rope tug, the trail was clear again.")
    world.say(f"The children reached the lookout, laughed at their snow-flecked hats, and ate their snacks like mountain champions.")
    world.say(f"The avalanche had turned their hike into a silly team puzzle, and they won.")
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a funny story for a 3-to-5-year-old that includes the word "avalanche" and shows {f["a"].id} and {f["b"].id} solving a mountain problem together.',
        f"Tell a comedic teamwork story where {f['a'].id}, {f['b'].id}, and {f['helper'].label} handle an avalanche on {f['setting'].place} with {f['tool'].label}.",
        f'Write a short humorous adventure where a small avalanche blocks a trail, but the kids use teamwork and problem solving to reach the lookout.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    a, b, helper, setting, problem, tool, move = f["a"], f["b"], f["helper"], f["setting"], f["problem"], f["tool"], f["move"]
    qa = [
        QAItem(
            question=f"What blocked {a.id} and {b.id} on {setting.place}?",
            answer=f"A small avalanche blocked the trail with {problem.block_phrase}. It turned their walk into a snowy problem they had to solve together.",
        ),
        QAItem(
            question=f"How did {a.id}, {b.id}, and {helper.label} fix the problem?",
            answer=f"They used {tool.phrase} and {move.name}. {move.lead.capitalize()}, {move.support}, so the trail could be cleared safely.",
        ),
        QAItem(
            question=f"Why did the children laugh at the end?",
            answer=f"They laughed because the avalanche had looked serious, but their teamwork worked. By the end, the trail was open and the lookout snacks were waiting.",
        ),
    ]
    if world.get("trail").meters["cleared"] >= THRESHOLD:
        qa.append(
            QAItem(
                question=f"What changed on the trail after they worked together?",
                answer=f"The snow blockage was cleared and the trail became safe again. Their teamwork turned the avalanche into a solved puzzle instead of a disaster.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an avalanche?",
            answer="An avalanche is a lot of snow and ice sliding down a mountain at once. It can block trails and make travel risky.",
        ),
        QAItem(
            question="What is teamwork?",
            answer="Teamwork means people help each other and do different jobs toward the same goal. It works best when everyone shares the work.",
        ),
        QAItem(
            question="What is problem solving?",
            answer="Problem solving means figuring out what is wrong and choosing a good plan to fix it. Sometimes that plan uses tools and careful thinking.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
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
        bits = []
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  history: {world.history}")
    return "\n".join(lines)


CURATED = [
    StoryParams(setting="mountain_path", problem="avalanche", tool="rope", move="spread_out", name_a="Mia", gender_a="girl", name_b="Noah", gender_b="boy", helper="grandpa"),
    StoryParams(setting="ski_lodge", problem="avalanche", tool="shovel", move="build_chain", name_a="Ava", gender_a="girl", name_b="Leo", gender_b="boy", helper="ranger"),
    StoryParams(setting="pine_trail", problem="avalanche", tool="map", move="follow_tracks", name_a="Nora", gender_a="girl", name_b="Finn", gender_b="boy", helper="aunt"),
]


ASP_RULES = r"""
valid(S,P,T) :- setting(S), problem(P), tool(T), afford(S,P), solvable(P,T).
cleared :- used_tool(T), teamwork(M), problem(P), solvable(P,T), move(M).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for p in sorted(s.affordances):
            lines.append(asp.fact("afford", sid, p))
    for pid, p in PROBLEMS.items():
        lines.append(asp.fact("problem", pid))
        lines.append(asp.fact("hazard", pid, p.hazard))
        lines.append(asp.fact("block", pid, p.block_phrase))
        for t in sorted(p.tags):
            lines.append(asp.fact("tag", pid, t))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        lines.append(asp.fact("solvable", "avalanche", tid))
    for mid, m in MOVES.items():
        lines.append(asp.fact("move", mid))
        lines.append(asp.fact("teamwork", mid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import random as _random
    ok = set(asp_valid_combos()) == set(valid_combos())
    if not ok:
        print("MISMATCH between ASP and Python valid_combos().")
        return 1
    try:
        _ = generate(resolve_params(build_parser().parse_args([]), _random.Random(777)))
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    print(f"OK: ASP matches Python and generate() smoke test passed ({len(valid_combos())} combos).")
    return 0


def build_story(world: World) -> str:
    return world.render()


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.problem not in PROBLEMS or params.tool not in TOOLS or params.move not in MOVES:
        raise StoryError("Invalid story parameters.")
    world = tell(
        SETTINGS[params.setting],
        PROBLEMS[params.problem],
        TOOLS[params.tool],
        MOVES[params.move],
        params.name_a,
        params.gender_a,
        params.name_b,
        params.gender_b,
        params.helper,
    )
    return StorySample(
        params=params,
        story=build_story(world),
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting = args.setting or rng.choice(sorted(SETTINGS))
    problem = args.problem or "avalanche"
    tool = args.tool or rng.choice(sorted(TOOLS))
    move = args.move or rng.choice(sorted(MOVES))
    if (setting, problem, tool) not in valid_combos():
        raise StoryError("No valid combination matches the given filters.")
    return StoryParams(
        setting=setting,
        problem=problem,
        tool=tool,
        move=move,
        name_a=args.name_a or rng.choice(GIRL_NAMES),
        gender_a=args.gender_a or "girl",
        name_b=args.name_b or rng.choice(BOY_NAMES),
        gender_b=args.gender_b or "boy",
        helper=args.helper or rng.choice(["grandpa", "aunt", "ranger"]),
    )


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
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
        while len(samples) < args.n and i < max(50, args.n * 50):
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
            header = f"### {p.name_a} and {p.name_b}: {p.problem} at {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
