#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/iris_suspense_problem_solving_space_adventure.py
=================================================================================================

A small standalone storyworld: Iris in a tense space-adventure problem-solving tale.

Premise:
- A young astronaut named Iris is on a tiny ship or station.
- Something important goes wrong in deep space.
- Iris feels suspense, thinks carefully, and solves the problem with tools and a helper.

The world is constrained so each sample reads like a complete little story:
beginning, middle tension, and ending image that proves what changed.
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
    worn_by: Optional[str] = None
    location: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
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
    kind: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Problem:
    id: str
    label: str
    phrase: str
    verb: str
    warning: str
    risk: str
    zone: set[str]
    clue: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    fixes: set[str]
    reaches: set[str]
    use: str
    outcome: str
    plural: bool = False


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
        import copy as _copy

        w = World(self.setting)
        w.entities = _copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "ship": Setting(place="the little starship", kind="ship", affords={"drift", "repair"}),
    "station": Setting(place="the science station", kind="station", affords={"drift", "repair"}),
    "moonbase": Setting(place="the moonbase", kind="base", affords={"drift", "repair"}),
}

PROBLEMS = {
    "drift": Problem(
        id="drift",
        label="drifting panel",
        phrase="a loose panel near the air lock",
        verb="drift loose",
        warning="the panel might bang the hull and send sparks everywhere",
        risk="sparks",
        zone={"hall", "airlock"},
        clue="a blinking red light",
        tags={"space", "suspense"},
    ),
    "signal": Problem(
        id="signal",
        label="silent antenna",
        phrase="the antenna that carried home messages",
        verb="go silent",
        warning="without the antenna, no rescue call could get through",
        risk="silence",
        zone={"roof", "control"},
        clue="a dead screen",
        tags={"space", "signal"},
    ),
    "drone": Problem(
        id="drone",
        label="stuck helper drone",
        phrase="a tiny helper drone with one jammed wheel",
        verb="get stuck",
        warning="the drone could not fetch the missing part if it stayed stuck",
        risk="delay",
        zone={"cargo", "bay"},
        clue="a squeaky wheel",
        tags={"robot", "rescue"},
    ),
}

TOOLS = {
    "tape": Tool(
        id="tape",
        label="silver tape",
        phrase="a roll of silver tape",
        fixes={"drift"},
        reaches={"hall", "airlock"},
        use="seal the loose panel",
        outcome="the panel sat still at last",
    ),
    "dish": Tool(
        id="dish",
        label="signal dish",
        phrase="a folded signal dish",
        fixes={"signal"},
        reaches={"roof", "control"},
        use="aim the signal dish",
        outcome="the screen lit up with a clear line",
    ),
    "wrench": Tool(
        id="wrench",
        label="little wrench",
        phrase="a little wrench with a bright handle",
        fixes={"drone", "drift"},
        reaches={"cargo", "bay", "airlock"},
        use="turn the stuck bolt or wheel",
        outcome="the wheel spun free",
    ),
}

HELPERS = {
    "bot": ("repair bot", "it"),
    "co": ("co-pilot", "they"),
    "mentor": ("mentor", "she"),
}

IRIS_NAMES = ["Iris"]  # seed word required
EXTRA_NAMES = ["Nova", "Mira", "Zed", "Pip", "Rae", "Luna"]


@dataclass
class StoryParams:
    setting: str
    problem: str
    tool: str
    helper: str
    name: str = "Iris"
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A problem is addressable when a tool reaches the same area and fixes the problem.
addressable(P, T) :- problem(P), tool(T), fixes(T, P), problem_zone(P, Z), tool_reaches(T, Z).

valid_story(S, P, T, H) :- setting(S), problem(P), tool(T), helper(H), addressable(P, T).
"""

def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for pid, p in PROBLEMS.items():
        lines.append(asp.fact("problem", pid))
        for z in sorted(p.zone):
            lines.append(asp.fact("problem_zone", pid, z))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        for p in sorted(t.fixes):
            lines.append(asp.fact("fixes", tid, p))
        for z in sorted(t.reaches):
            lines.append(asp.fact("tool_reaches", tid, z))
    for hid in HELPERS:
        lines.append(asp.fact("helper", hid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set((s, p, t) for (s, p, t, _) in asp_valid_stories())
    if py == cl:
        print(f"OK: ASP matches Python ({len(py)} combos).")
        return 0
    print("MISMATCH between ASP and Python:")
    if cl - py:
        print("  only in ASP:", sorted(cl - py))
    if py - cl:
        print("  only in Python:", sorted(py - cl))
    return 1


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------

def problem_needs_tool(problem: Problem, tool: Tool) -> bool:
    return problem.id in tool.fixes


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, _setting in SETTINGS.items():
        for pid, p in PROBLEMS.items():
            for tid, t in TOOLS.items():
                if problem_needs_tool(p, t):
                    combos.append((sid, pid, tid))
    return combos


def explain_rejection(problem: Problem, tool: Tool) -> str:
    return (
        f"(No story: {tool.label} does not solve {problem.label}. "
        f"Try a tool that can really handle the problem.)"
    )


# ---------------------------------------------------------------------------
# Narrative helpers
# ---------------------------------------------------------------------------

def intro_line(hero: Entity) -> str:
    return f"{hero.id} was a little astronaut who loved looking for quiet stars."


def setting_line(setting: Setting) -> str:
    return {
        "ship": "The ship hummed softly as it floated through the dark.",
        "station": "The station blinked with tiny green lights in the long dark.",
        "moonbase": "The moonbase sat under a window of black sky and silver dust.",
    }[setting.kind]


def problem_line(problem: Problem) -> str:
    return f"Then came {problem.phrase}, and the whole place felt tense."


def suspense_line(problem: Problem) -> str:
    return f"{problem.clue} flashed nearby, and Iris knew something important was about to go wrong."


def solution_line(problem: Problem, tool: Tool) -> str:
    return f"Iris reached for {tool.phrase} and quietly got to work."


def ending_line(problem: Problem, tool: Tool) -> str:
    return f"At last, {tool.outcome}, and the ship felt safe again."


def helper_line(helper: Entity) -> str:
    return f"{helper.id} stayed close, ready to pass tools and watch the dark corridor."


def resolve_problem(world: World, hero: Entity, helper: Entity, problem: Problem, tool: Tool) -> None:
    hero.memes["courage"] = hero.memes.get("courage", 0.0) + 1
    hero.memes["focus"] = hero.memes.get("focus", 0.0) + 1
    helper.memes["trust"] = helper.memes.get("trust", 0.0) + 1
    world.say(solution_line(problem, tool))
    world.say(f"{hero.id} checked the marks, listened for the rattle, and used the tool to {tool.use}.")
    world.say(ending_line(problem, tool))
    world.say(f"{helper.id} smiled when the lights settled into a calm glow.")


def tell(setting: Setting, problem: Problem, tool: Tool, helper_kind: str, name: str = "Iris") -> World:
    world = World(setting)
    hero = world.add(Entity(id=name, kind="character", type="girl", label=name))
    helper_label, _ = HELPERS[helper_kind]
    helper = world.add(Entity(id=helper_label, kind="character", type="robot" if helper_kind == "bot" else "girl", label=helper_label))
    problem_ent = world.add(Entity(id=problem.id, type=problem.id, label=problem.label, phrase=problem.phrase))
    tool_ent = world.add(Entity(id=tool.id, type=tool.id, label=tool.label, phrase=tool.phrase, owner=hero.id))

    world.say(intro_line(hero))
    world.say(setting_line(setting))
    world.say(f"Iris noticed {problem.phrase} before anyone else did.")
    world.para()
    world.say(problem_line(problem))
    world.say(suspense_line(problem))
    world.say(f"The warning said {problem.warning}.")
    world.say(helper_line(helper))
    world.para()
    world.say(f"Iris took a slow breath, looked at the clues, and decided to fix it.")
    resolve_problem(world, hero, helper, problem, tool)

    world.facts.update(
        hero=hero,
        helper=helper,
        problem=problem_ent,
        tool=tool_ent,
        setting=setting,
        problem_cfg=problem,
        tool_cfg=tool,
        helper_kind=helper_kind,
    )
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short space-adventure story for a young child about {f["hero"].id} facing a sudden problem on {f["setting"].place}.',
        f"Tell a suspenseful but gentle story where {f['hero'].id} notices {f['problem_cfg'].label} and solves it with {f['tool_cfg'].label}.",
        f'Write a child-friendly story that includes the name "Iris", a tense problem, and a clever fix in space.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    p: Problem = f["problem_cfg"]
    t: Tool = f["tool_cfg"]
    s: Setting = f["setting"]
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"The story was about {hero.id}, a little astronaut who stayed calm in a space problem.",
        ),
        QAItem(
            question=f"What problem did Iris notice on {s.place}?",
            answer=f"Iris noticed {p.phrase}, which made the whole place feel tense.",
        ),
        QAItem(
            question=f"What did Iris use to fix the problem?",
            answer=f"Iris used {t.phrase} to solve the problem.",
        ),
        QAItem(
            question=f"Who stayed close while Iris worked?",
            answer=f"{helper.id} stayed close and helped by watching and passing tools.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with the problem fixed and the ship feeling safe again.",
        ),
    ]


WORLD_KNOWLEDGE = {
    "space": QAItem(
        question="Why do astronauts wear suits in space?",
        answer="Astronauts wear suits in space to help keep them safe, warm, and supplied with air.",
    ),
    "suspense": QAItem(
        question="What does suspense mean in a story?",
        answer="Suspense means the story makes you wonder what will happen next and feel a little worried or excited.",
    ),
    "rescue": QAItem(
        question="Why do spaceships have tools on board?",
        answer="Spaceships have tools on board so astronauts can fix small problems while they are far from home.",
    ),
    "robot": QAItem(
        question="What can a helper robot do on a ship?",
        answer="A helper robot can carry tools, watch for danger, and help fix small problems.",
    ),
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["problem_cfg"].tags)
    tags.add("space")
    if world.facts.get("helper_kind") == "bot":
        tags.add("robot")
    tags.add("rescue")
    tags.add("suspense")
    out: list[QAItem] = []
    for tag in ["space", "suspense", "rescue", "robot"]:
        if tag in tags:
            out.append(WORLD_KNOWLEDGE[tag])
    return out


# ---------------------------------------------------------------------------
# Params / generation
# ---------------------------------------------------------------------------

def valid_helper_for_problem(problem: Problem, tool: Tool) -> bool:
    return problem.id in tool.fixes


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Iris in a suspenseful space-adventure problem-solving story world.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--name", default="Iris")
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
    if args.problem and args.tool:
        if not valid_helper_for_problem(PROBLEMS[args.problem], TOOLS[args.tool]):
            raise StoryError(explain_rejection(PROBLEMS[args.problem], TOOLS[args.tool]))

    combos = [
        c for c in valid_combos()
        if (args.setting is None or c[0] == args.setting)
        and (args.problem is None or c[1] == args.problem)
        and (args.tool is None or c[2] == args.tool)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, problem, tool = rng.choice(sorted(combos))
    helper = args.helper or rng.choice(sorted(HELPERS))
    name = args.name or "Iris"
    return StoryParams(setting=setting, problem=problem, tool=tool, helper=helper, name=name)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.setting],
        PROBLEMS[params.problem],
        TOOLS[params.tool],
        params.helper,
        params.name,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.location:
            bits.append(f"location={e.location}")
        lines.append(f"  {e.id:12} ({e.kind:8}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP / output / CLI
# ---------------------------------------------------------------------------

def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify_python_parity() -> int:
    cl = set((s, p, t) for (s, p, t, _) in asp_valid_combos())
    py = set(valid_combos())
    if cl == py:
        print(f"OK: ASP gate matches Python ({len(py)} combos).")
        return 0
    print("MISMATCH between ASP and Python:")
    if cl - py:
        print("  only in ASP:", sorted(cl - py))
    if py - cl:
        print("  only in Python:", sorted(py - cl))
    return 1


def valid_combos_for_all() -> list[StoryParams]:
    out: list[StoryParams] = []
    for setting, problem, tool in valid_combos():
        out.append(StoryParams(setting=setting, problem=problem, tool=tool, helper="bot", name="Iris"))
    return out


CURATED = [
    StoryParams(setting="ship", problem="drift", tool="tape", helper="bot", name="Iris"),
    StoryParams(setting="station", problem="signal", tool="dish", helper="co", name="Iris"),
    StoryParams(setting="moonbase", problem="drone", tool="wrench", helper="mentor", name="Iris"),
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
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify_python_parity())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible stories:\n")
        for setting, problem, tool, helper in combos:
            print(f"  {setting:9} {problem:8} {tool:8} {helper}")
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
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
