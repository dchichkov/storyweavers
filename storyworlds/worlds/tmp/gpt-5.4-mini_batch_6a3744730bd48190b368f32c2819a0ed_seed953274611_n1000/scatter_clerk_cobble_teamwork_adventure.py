#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/scatter_clerk_cobble_teamwork_adventure.py
=========================================================================

A small, self-contained storyworld about a tiny adventure where a child and a
clerk work together, scattered pieces become a useful path, and a cobble
problem turns into a teamwork win.

The seed words are woven into the domain itself:
- scatter: loose trail pieces that can be gathered
- clerk: a helpful shop clerk who knows the place
- cobble: rough stones that block or patch the way

The stories are classical TinyStories-style adventures with a premise, a turn,
and a resolution driven by world state rather than a frozen paragraph swap.
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
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
HELP_MIN = 2
SCARED_MIN = 1.0


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
        female = {"girl", "mother", "mom", "woman", "clerk"}
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
class Setting:
    id: str
    place: str
    detail: str
    path: str
    quest: str
    ambient: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Problem:
    id: str
    label: str
    obstacle: str
    risk: str
    fix_need: str
    spread: int
    dangerous: bool = True


@dataclass
class Tool:
    id: str
    label: str
    helper: str
    use: str
    power: int
    supports: set[str] = field(default_factory=set)


@dataclass
class TeamRole:
    id: str
    label: str
    action: str
    promise: str
    bonus: int


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

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        return c


@dataclass
class StoryParams:
    setting: str
    problem: str
    tool: str
    team_role: str
    hero_name: str
    hero_gender: str
    clerk_name: str
    clerk_gender: str
    seed: Optional[int] = None


SETTINGS = {
    "market_lane": Setting(
        id="market_lane",
        place="the market lane",
        detail="The lane was busy, with bright stalls and a windy little archway.",
        path="a narrow cobbled path behind the stalls",
        quest="the far signpost",
        ambient="The breeze carried the smell of bread and apples.",
        affords={"scatter", "clerk", "cobble"},
    ),
    "harbor_row": Setting(
        id="harbor_row",
        place="the harbor row",
        detail="The row looked lively, with ropes, crates, and a gull calling overhead.",
        path="a slippery cobbled walk beside the docks",
        quest="the blue lamp post",
        ambient="The water flashed silver between the boats.",
        affords={"scatter", "clerk", "cobble"},
    ),
    "hill_gate": Setting(
        id="hill_gate",
        place="the hill gate",
        detail="The gate stood high, with stone steps and a small gatehouse door.",
        path="a steep cobbled stair",
        quest="the old watch bell",
        ambient="Clouds drifted past the sun like slow white sails.",
        affords={"scatter", "clerk", "cobble"},
    ),
}

PROBLEMS = {
    "scatter": Problem(
        id="scatter",
        label="scattered map pieces",
        obstacle="the map pieces had blown apart in the wind",
        risk="the path could not be found",
        fix_need="someone needed to gather the pieces before they disappeared",
        spread=2,
    ),
    "clerk": Problem(
        id="clerk",
        label="the clerk's shelf puzzle",
        obstacle="the clerk could not reach the right box on the high shelf",
        risk="the right key would stay hidden",
        fix_need="someone needed to fetch the box down together",
        spread=1,
    ),
    "cobble": Problem(
        id="cobble",
        label="a loose cobble",
        obstacle="one cobble had rocked loose in the path",
        risk="someone could trip on the step",
        fix_need="someone needed to press it back into place",
        spread=2,
    ),
}

TOOLS = {
    "bag": Tool(
        id="bag",
        label="a little cloth bag",
        helper="carry the scattered pieces",
        use="gather",
        power=2,
        supports={"scatter"},
    ),
    "hook": Tool(
        id="hook",
        label="a hooked pole",
        helper="reach the high shelf",
        use="lift",
        power=2,
        supports={"clerk"},
    ),
    "trowel": Tool(
        id="trowel",
        label="a small trowel",
        helper="press the cobble firmly",
        use="set",
        power=3,
        supports={"cobble"},
    ),
    "hands": Tool(
        id="hands",
        label="bare hands",
        helper="work side by side",
        use="hold",
        power=1,
        supports={"scatter", "clerk", "cobble"},
    ),
}

TEAMWORK = {
    "helpful_clerk": TeamRole(
        id="helpful_clerk",
        label="the clerk",
        action="helped",
        promise="we can do this together",
        bonus=2,
    ),
    "shared_plan": TeamRole(
        id="shared_plan",
        label="the team",
        action="planned",
        promise="one gathers, one steadies, and one watches",
        bonus=1,
    ),
    "steady_pair": TeamRole(
        id="steady_pair",
        label="the pair",
        action="held",
        promise="two hands are better than one on a rough path",
        bonus=2,
    ),
}

GIRL_NAMES = ["Mia", "Lina", "Tara", "Nora", "Zoe", "Ava", "Leah", "Ivy"]
BOY_NAMES = ["Leo", "Owen", "Finn", "Milo", "Theo", "Jude", "Nate", "Ezra"]
CLERK_NAMES = ["Mrs. Vale", "Mr. Pike", "Ms. Reed", "Mr. Lane"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for pid, p in PROBLEMS.items():
            for tid, t in TOOLS.items():
                if pid in t.supports and p.dangerous:
                    combos.append((sid, pid, tid))
    return combos


def reasonableness_gate(problem: Problem, tool: Tool) -> bool:
    return problem.id in tool.supports and problem.dangerous


def best_tool(problem: Problem) -> Tool:
    matches = [t for t in TOOLS.values() if problem.id in t.supports]
    return max(matches, key=lambda t: t.power)


def severity(problem: Problem, delay: int) -> int:
    return problem.spread + delay


def can_fix(problem: Problem, tool: Tool, delay: int) -> bool:
    return tool.power >= severity(problem, delay)


def build_person(world: World, name: str, gender: str, kind: str, role: str = "") -> Entity:
    return world.add(Entity(id=name, kind="character", type=gender, label=name, role=role))


def tell(setting: Setting, problem: Problem, tool: Tool, team_role: TeamRole,
         hero_name: str, hero_gender: str, clerk_name: str, clerk_gender: str,
         delay: int = 0) -> World:
    world = World()
    hero = build_person(world, hero_name, hero_gender, "character", role="hero")
    clerk = build_person(world, clerk_name, clerk_gender, "character", role="clerk")
    hero.memes["curiosity"] = 1.0
    clerk.memes["calm"] = 1.0

    world.say(
        f"{hero.id} set out along {setting.place} on a bright adventure. "
        f"{setting.detail} {setting.ambient}"
    )
    world.say(
        f"Near {setting.path}, {hero.id} noticed {problem.obstacle}. "
        f"{problem.fix_need.capitalize()}."
    )

    world.para()
    hero.memes["worry"] += 1
    world.say(
        f"{hero.id} searched for {problem.label}, but the trail had {problem.risk}. "
        f"Then {clerk.id} stepped out from the shop door."
    )
    world.say(
        f'"{team_role.promise.capitalize()}," said {clerk.id}. '
        f'"If you bring {tool.label}, we can solve this together."'
    )

    if problem.id == "scatter":
        hero.meters["pieces"] += 1
        clerk.meters["pieces"] += 1
        world.say(
            f"{hero.id} chased the scattered pieces while {clerk.id} kept them from "
            f"blowing farther away. Soon the bits were back in one place."
        )
    elif problem.id == "clerk":
        hero.meters["reach"] += 1
        clerk.meters["reach"] += 1
        world.say(
            f"{hero.id} braced the crate while {clerk.id} guided the hooked pole. "
            f"Together they lowered the box from the high shelf."
        )
    else:
        hero.meters["steady"] += 1
        clerk.meters["steady"] += 1
        world.say(
            f"{hero.id} held the stone steady while {clerk.id} pressed the loose "
            f"cobble into place with the trowel."
        )

    world.para()
    if can_fix(problem, tool, delay):
        hero.memes["joy"] += 2
        clerk.memes["joy"] += 1
        world.say(
            f"With {tool.helper}, the job was done. The path grew safe again, "
            f"and the two of them could go on."
        )
        world.say(
            f"At last {hero.id} and {clerk.id} crossed the cobbled way together, "
            f"smiling at how teamwork had turned a hard spot into an easy step."
        )
        outcome = "fixed"
    else:
        hero.memes["worry"] += 1
        world.say(
            f"{tool.label.capitalize()} was not enough. The problem stayed open, "
            f"and the rough path still looked too risky."
        )
        world.say(
            f"{clerk.id} sent for a stronger helper, because the adventure needed "
            f"a safer finish."
        )
        outcome = "stalled"

    world.facts.update(
        hero=hero,
        clerk=clerk,
        setting=setting,
        problem=problem,
        tool=tool,
        team_role=team_role,
        delay=delay,
        outcome=outcome,
        fixed=(outcome == "fixed"),
        severity=severity(problem, delay),
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a child-friendly adventure story that includes the words "scatter", "clerk", and "cobble".',
        f"Tell a teamwork story where {f['hero'].id} meets {f['clerk'].id} at {f['setting'].place} and they solve a {f['problem'].label} together.",
        f"Write a short adventure where a helpful clerk and a young explorer fix a rough cobbled path by working as a team.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    clerk = f["clerk"]
    problem = f["problem"]
    setting = f["setting"]
    tool = f["tool"]
    qs = [
        QAItem(
            question="Who went on the adventure?",
            answer=f"{hero.id} went on the adventure, and {clerk.id} joined in to help. They became a small team and faced the trouble together.",
        ),
        QAItem(
            question="What problem did they find?",
            answer=f"They found {problem.obstacle}. That made the adventure pause until someone could help solve it.",
        ),
        QAItem(
            question="How did they work together?",
            answer=f"{hero.id} and {clerk.id} used {tool.label} and both did their part. One person steadied things while the other fixed the problem, so teamwork made the answer possible.",
        ),
    ]
    if f["fixed"]:
        qs.append(QAItem(
            question="What changed by the end of the story?",
            answer=f"The trouble was fixed, and the path at {setting.place} was safe again. The adventure could continue because the problem was solved together.",
        ))
    else:
        qs.append(QAItem(
            question="What happened when the first fix was not enough?",
            answer=f"The first try did not solve it, so {clerk.id} called for stronger help. The story ended with the problem still waiting, but the team stayed calm and careful.",
        ))
    return qs


def world_knowledge_qa(world: World) -> list[QAItem]:
    qs = [
        QAItem(
            question="What is a clerk?",
            answer="A clerk is a helpful worker in a shop or office who can answer questions and find things.",
        ),
        QAItem(
            question="What are cobbles?",
            answer="Cobbles are rough round stones used to make old streets and paths.",
        ),
        QAItem(
            question="What does teamwork mean?",
            answer="Teamwork means people help each other and do different jobs to reach the same goal.",
        ),
        QAItem(
            question="What does it mean to scatter things?",
            answer="To scatter things means to spread them apart so they are no longer in one neat pile.",
        ),
    ]
    if world.facts["problem"].id == "cobble":
        qs.append(QAItem(
            question="Why can a loose cobble be risky?",
            answer="A loose cobble can make someone trip or stumble if they step on it the wrong way.",
        ))
    return qs


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts ==", *[f"{i+1}. {p}" for i, p in enumerate(sample.prompts)], ""]
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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        parts = []
        if meters:
            parts.append(f"meters={dict(meters)}")
        if memes:
            parts.append(f"memes={dict(memes)}")
        if e.role:
            parts.append(f"role={e.role}")
        lines.append(f"  {e.id:12} ({e.type:7}) {' '.join(parts)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(setting="market_lane", problem="scatter", tool="bag", team_role="helpful_clerk",
                hero_name="Mia", hero_gender="girl", clerk_name="Mrs. Vale", clerk_gender="woman"),
    StoryParams(setting="harbor_row", problem="clerk", tool="hook", team_role="shared_plan",
                hero_name="Leo", hero_gender="boy", clerk_name="Mr. Pike", clerk_gender="man"),
    StoryParams(setting="hill_gate", problem="cobble", tool="trowel", team_role="steady_pair",
                hero_name="Nora", hero_gender="girl", clerk_name="Ms. Reed", clerk_gender="woman"),
]


def explain_rejection(problem: Problem, tool: Tool) -> str:
    return (
        f"(No story: {tool.label} does not solve {problem.label} well enough for this adventure. "
        f"The world only tells teamwork stories when the chosen helper can really fix the trouble.)"
    )


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.problem and args.tool:
        problem = PROBLEMS[args.problem]
        tool = TOOLS[args.tool]
        if not reasonableness_gate(problem, tool):
            raise StoryError(explain_rejection(problem, tool))

    combos = [
        c for c in valid_combos()
        if (args.setting is None or c[0] == args.setting)
        and (args.problem is None or c[1] == args.problem)
        and (args.tool is None or c[2] == args.tool)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting_id, problem_id, tool_id = rng.choice(sorted(combos))
    setting = SETTINGS[setting_id]
    problem = PROBLEMS[problem_id]
    tool = TOOLS[tool_id]
    team_role = rng.choice(list(TEAMWORK))
    gender = args.gender or rng.choice(["girl", "boy"])
    hero_name = args.hero or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    clerk_gender = args.clerk_gender or rng.choice(["woman", "man"])
    clerk_name = args.clerk or rng.choice(CLERK_NAMES)
    return StoryParams(
        setting=setting.id,
        problem=problem.id,
        tool=tool.id,
        team_role=team_role,
        hero_name=hero_name,
        hero_gender=gender,
        clerk_name=clerk_name,
        clerk_gender=clerk_gender,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"Unknown setting: {params.setting}")
    if params.problem not in PROBLEMS:
        raise StoryError(f"Unknown problem: {params.problem}")
    if params.tool not in TOOLS:
        raise StoryError(f"Unknown tool: {params.tool}")
    if params.team_role not in TEAMWORK:
        raise StoryError(f"Unknown teamwork role: {params.team_role}")
    setting = SETTINGS[params.setting]
    problem = PROBLEMS[params.problem]
    tool = TOOLS[params.tool]
    team_role = TEAMWORK[params.team_role]
    world = tell(setting, problem, tool, team_role,
                 params.hero_name, params.hero_gender,
                 params.clerk_name, params.clerk_gender)
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


def ASP_RULES = r"""
reasonably_valid(S, P, T) :- setting(S), problem(P), tool(T),
    supports(T, P), dangerous(P).
#show valid/3.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for pid, p in PROBLEMS.items():
        lines.append(asp.fact("problem", pid))
        if p.dangerous:
            lines.append(asp.fact("dangerous", pid))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        for sup in sorted(t.supports):
            lines.append(asp.fact("supports", tid, sup))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: ASP gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH between ASP and valid_combos().")
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        print("OK: generate() smoke test passed.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Teamwork adventure storyworld with scatter, clerk, and cobble.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--hero")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--clerk")
    ap.add_argument("--clerk-gender", choices=["woman", "man"])
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
        for s, p, t in asp_valid_combos():
            print(f"  {s:12} {p:10} {t}")
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
            header = f"### {p.hero_name} with {p.clerk_name}: {p.problem} at {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
