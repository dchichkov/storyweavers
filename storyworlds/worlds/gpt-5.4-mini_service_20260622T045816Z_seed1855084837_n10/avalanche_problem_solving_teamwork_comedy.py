#!/usr/bin/env python3
"""
Standalone storyworld: avalanche teamwork comedy.

A small crew gets caught in a silly mountain avalanche problem and solves it
with teamwork, improvised problem-solving, and a cheerful ending image.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

# Robust import path discovery for nested repo output directories.
_THIS = Path(__file__).resolve()
for parent in [_THIS.parent, *_THIS.parents]:
    if (parent / "results.py").exists():
        sys.path.insert(0, str(parent))
        break
    if (parent / "storyworlds" / "results.py").exists():
        sys.path.insert(0, str(parent / "storyworlds"))
        break

from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict = field(default_factory=lambda: {"buried": 0.0, "slip": 0.0, "blocked": 0.0, "safe": 0.0})
    memes: dict = field(default_factory=lambda: {"worry": 0.0, "joy": 0.0, "teamwork": 0.0, "relief": 0.0})

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Setting:
    id: str
    place: str
    feature: str
    cliffside: bool = True


@dataclass
class Problem:
    id: str
    trigger: str
    blockage: str
    comic_detail: str
    fix_hint: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    use: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    setting: str
    problem: str
    tool1: str
    tool2: str
    hero: str
    sidekick: str
    parent: str
    seed: Optional[int] = None


SETTINGS = {
    "trail": Setting(id="trail", place="the mountain trail", feature="a narrow ledge"),
    "lodge": Setting(id="lodge", place="the ski lodge", feature="a snowy back door"),
    "ridge": Setting(id="ridge", place="the ridge path", feature="a steep turn"),
}

PROBLEMS = {
    "avalanche": Problem(
        id="avalanche",
        trigger="a rumble from above",
        blockage="a wall of snow",
        comic_detail="the snow kept landing in all the wrong places, including everybody's hats",
        fix_hint="they needed to move fast, stay together, and make one clear plan",
        tags={"avalanche", "snow", "problem_solving", "teamwork"},
    )
}

TOOLS = {
    "shovel": Tool(id="shovel", label="shovel", phrase="a bright orange shovel", use="dig"),
    "rope": Tool(id="rope", label="rope", phrase="a long climbing rope", use="pull"),
    "whistle": Tool(id="whistle", label="whistle", phrase="a loud whistle", use="signal"),
    "map": Tool(id="map", label="map", phrase="a crumpled trail map", use="plan"),
}

NAMES = ["Mina", "Jasper", "Noah", "Luna", "Toby", "Iris", "Pia", "Eli"]
KINDS = {"girl", "boy"}


class World:
    def __init__(self, setting: Setting):
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.facts: dict = {}
        self.history: list[str] = []
        self.fired: set[tuple] = set()

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.history.append(text)

    def render(self) -> str:
        return " ".join(self.history)

    def copy(self) -> "World":
        other = World(self.setting)
        import copy as _copy
        other.entities = _copy.deepcopy(self.entities)
        other.facts = _copy.deepcopy(self.facts)
        other.history = list(self.history)
        other.fired = set(self.fired)
        return other


def _r_burial(world: World) -> list[str]:
    out = []
    for ent in world.entities.values():
        if ent.meters.get("buried", 0.0) >= THRESHOLD:
            sig = ("buried", ent.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            ent.meters["blocked"] = ent.meters.get("blocked", 0.0) + 1
            out.append(f"{ent.id} got buried under the snow.")
    return out


def _r_worry(world: World) -> list[str]:
    out = []
    if world.facts.get("problem_started") and ("worry", "team") not in world.fired:
        world.fired.add(("worry", "team"))
        for e in world.entities.values():
            if e.kind == "character":
                e.memes["worry"] = e.memes.get("worry", 0.0) + 1
        out.append("Everyone gulped at once.")
    return out


def _r_relief(world: World) -> list[str]:
    out = []
    if world.facts.get("solved") and ("relief", "team") not in world.fired:
        world.fired.add(("relief", "team"))
        for e in world.entities.values():
            if e.kind == "character":
                e.memes["relief"] = e.memes.get("relief", 0.0) + 1
                e.memes["joy"] = e.memes.get("joy", 0.0) + 1
        out.append("Everyone laughed because the plan worked.")
    return out


def propagate(world: World) -> None:
    changed = True
    while changed:
        changed = False
        for rule in (_r_burial, _r_worry, _r_relief):
            sents = rule(world)
            if sents:
                changed = True
                world.history.extend(sents)


def problem_risky(problem: Problem, setting: Setting) -> bool:
    return problem.id == "avalanche" and setting.cliffside


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for pid in PROBLEMS:
            for t1 in TOOLS:
                for t2 in TOOLS:
                    if t1 == t2:
                        continue
                    combos.append((sid, pid, t1, t2))
    return combos


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for pid in PROBLEMS:
        lines.append(asp.fact("problem", pid))
    for tid in TOOLS:
        lines.append(asp.fact("tool", tid))
    for sid, s in SETTINGS.items():
        if s.cliffside:
            lines.append(asp.fact("cliffside", sid))
    for pid, p in PROBLEMS.items():
        lines.append(asp.fact("risky_problem", pid))
        for tag in sorted(p.tags):
            lines.append(asp.fact("tag", pid, tag))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,P,T1,T2) :- setting(S), problem(P), tool(T1), tool(T2), T1 != T2, cliffside(S), risky_problem(P).
teamwork(P) :- problem(P).
problem_solving(P) :- problem(P).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    p = set(valid_combos())
    a = set(asp_valid_combos())
    ok = True
    if p != a:
        ok = False
        print("MISMATCH in valid combos")
    sample = generate(resolve_params(argparse.Namespace(setting=None, problem=None, tool1=None, tool2=None, hero=None, sidekick=None, parent=None), random.Random(777)))
    if not sample.story or "avalanche" not in sample.story.lower():
        ok = False
        print("SMOKE TEST FAILED")
    if ok:
        print(f"OK: verify passed ({len(p)} combos).")
        return 0
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Comedy avalanche teamwork storyworld.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--tool1", choices=TOOLS)
    ap.add_argument("--tool2", choices=TOOLS)
    ap.add_argument("--hero")
    ap.add_argument("--sidekick")
    ap.add_argument("--parent")
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
              if (args.setting is None or c[0] == args.setting)
              and (args.problem is None or c[1] == args.problem)
              and (args.tool1 is None or c[2] == args.tool1)
              and (args.tool2 is None or c[3] == args.tool2)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, problem, tool1, tool2 = rng.choice(sorted(combos))
    return StoryParams(
        setting=setting,
        problem=problem,
        tool1=tool1,
        tool2=tool2,
        hero=args.hero or rng.choice(NAMES),
        sidekick=args.sidekick or rng.choice([n for n in NAMES if n != args.hero]),
        parent=args.parent or rng.choice(["mother", "father"]),
    )


def tell(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    problem = PROBLEMS[params.problem]
    t1 = TOOLS[params.tool1]
    t2 = TOOLS[params.tool2]
    world = World(setting)
    hero = world.add(Entity(id=params.hero, kind="character", type="boy" if params.hero in {"Noah", "Jasper", "Toby", "Eli"} else "girl", role="hero"))
    sidekick = world.add(Entity(id=params.sidekick, kind="character", type="girl" if params.sidekick in {"Mina", "Luna", "Iris", "Pia"} else "boy", role="sidekick"))
    parent = world.add(Entity(id="Parent", kind="character", type=params.parent, label=f"the {params.parent}", role="parent"))
    # Nearby contract fix: keep the problem fact available to prompt generation and verification.
    world.facts.update(problem_started=False, solved=False, problem=problem.id)
    world.say(f"{hero.id} and {sidekick.id} were having a silly day at {setting.place}.")
    world.say(f"They wanted to deal with {problem.id} at {setting.feature}, but {problem.comic_detail}.")
    world.say(f"Then there was {problem.trigger}, and a snowy avalanche tumbled in with all the grace of a sleepy pillow.")
    hero.meters["buried"] += 1
    sidekick.meters["buried"] += 1
    world.facts["problem_started"] = True
    propagate(world)
    world.say(f"{hero.id} grabbed {t1.phrase}, while {sidekick.id} grabbed {t2.phrase}.")
    world.say(f"{hero.id} shouted, 'I have a plan!' and {sidekick.id} replied, 'Great, because my plan is mostly yelling.'")
    hero.memes["teamwork"] += 1
    sidekick.memes["teamwork"] += 1
    world.say(f"Together they used the {t1.use}ing thing and the {t2.use}ing thing in a very serious way that looked deeply unserious.")
    hero.meters["buried"] = 0.0
    sidekick.meters["buried"] = 0.0
    parent.memes["relief"] += 1
    world.facts["solved"] = True
    propagate(world)
    world.say(f"At the end, the avalanche became a lumpy snow bank, and the trio waved from it like they had won a comedy contest.")
    world.say(f"{hero.id} wore a snow mustache, {sidekick.id} had one mitten on backward, and the {params.parent} was laughing so hard they snorted.")
    return world


def prompts_for(world: World) -> list[str]:
    p = world.facts["problem"]
    return [
        f"Write a funny story about an avalanche where friends solve a mountain problem together.",
        f"Tell a comedy about {p} and teamwork on a snowy trail.",
        f"Write a child-friendly story in which characters use problem solving to handle an avalanche.",
    ]


def story_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What problem did the friends face?", answer="They faced an avalanche that blocked their way with snow."),
        QAItem(question="How did they solve it?", answer="They worked together, made a quick plan, and used their tools to clear the snow and get free."),
        QAItem(question="Why was it funny?", answer="The situation was serious, but everyone kept acting a little silly, which made the teamwork feel playful instead of scary."),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is an avalanche?", answer="An avalanche is a big slide of snow rushing down a mountain."),
        QAItem(question="Why is teamwork useful in a problem like this?", answer="Teamwork helps because one person can spot the problem, another can fetch a tool, and together they can solve it faster."),
        QAItem(question="What is problem solving?", answer="Problem solving means thinking about a difficulty, choosing a useful plan, and trying it step by step."),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== Prompts =="]
    out.extend(f"- {p}" for p in sample.prompts)
    out.append("== Story QA ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("== World QA ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: meters={e.meters} memes={e.memes} role={e.role}")
    lines.append(f"facts={world.facts}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts_for(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


CURATED = [
    StoryParams(setting="trail", problem="avalanche", tool1="shovel", tool2="rope", hero="Mina", sidekick="Jasper", parent="mother"),
    StoryParams(setting="lodge", problem="avalanche", tool1="whistle", tool2="map", hero="Luna", sidekick="Eli", parent="father"),
    StoryParams(setting="ridge", problem="avalanche", tool1="rope", tool2="shovel", hero="Noah", sidekick="Iris", parent="mother"),
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


def _sample_to_obj(sample: StorySample) -> dict:
    # Prefer a stable stdlib-only JSON shape regardless of StorySample internals.
    if hasattr(sample, "to_dict"):
        return sample.to_dict()
    return {
        "params": getattr(sample, "params", None),
        "story": getattr(sample, "story", ""),
        "prompts": getattr(sample, "prompts", []),
        "story_qa": getattr(sample, "story_qa", []),
        "world_qa": getattr(sample, "world_qa", []),
        "world": getattr(sample, "world", None),
    }


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        print(asp_program("#show valid/4."))
        print(f"{len(asp_valid_combos())} valid combos")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            s = generate(params)
            if s.story not in seen:
                seen.add(s.story)
                samples.append(s)
            i += 1

    if args.json:
        payload = [_sample_to_obj(s) for s in samples]
        if len(payload) == 1:
            print(json.dumps(payload[0], indent=2, ensure_ascii=False, default=str))
        else:
            print(json.dumps(payload, indent=2, ensure_ascii=False, default=str))
        return

    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
