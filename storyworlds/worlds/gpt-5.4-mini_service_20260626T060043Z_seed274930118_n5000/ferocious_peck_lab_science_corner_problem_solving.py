#!/usr/bin/env python3
"""
A standalone story world for a tiny Superhero Story set in a science corner.

Seed inspiration:
- A brave child superhero in a science corner faces a ferocious pecking menace.
- The crisis is solved with careful problem solving, not force alone.
- The ending should prove bravery changed into a successful fix.
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
# Domain registries
# ---------------------------------------------------------------------------

HERO_NAMES = ["Milo", "Nia", "Tess", "Arlo", "Zuri", "Pip", "Juno", "Kai"]
HELPER_NAMES = ["Dr. Finch", "Ms. Echo", "Coach Vega", "Aunt Nova", "Mr. Ray"]

TOOLS = {
    "tape": "a roll of bright tape",
    "cardboard": "a flat piece of cardboard",
    "cup": "a clear plastic cup",
    "box": "a little paper box",
    "net": "a tiny net",
}

THREATS = {
    "peck": {
        "name": "pecking beak",
        "verb": "peck",
        "gerund": "pecking",
        "sound": "tap-tap-tap",
        "problem": "the beak kept pecking at the paper tower",
    }
}

PROJECTS = {
    "tower": "a tower of paper stars",
    "robot": "a cardboard robot",
    "bridge": "a bridge of craft sticks",
}

FEATURE_TAGS = {"problem_solving", "bravery", "science_corner", "superhero_story", "ferocious", "peck", "lab"}


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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman"}
        male = {"boy", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class StoryParams:
    hero_name: str
    hero_type: str
    helper_name: str
    project: str
    threat: str
    tool: str
    seed: Optional[int] = None


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[str] = set()
        self.trace: list[str] = []
        self.threat_active = False
        self.tool_used = False

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
        other = World()
        other.entities = copy.deepcopy(self.entities)
        other.paragraphs = [[]]
        other.facts = dict(self.facts)
        other.fired = set(self.fired)
        other.threat_active = self.threat_active
        other.tool_used = self.tool_used
        return other


# ---------------------------------------------------------------------------
# Simulation rules
# ---------------------------------------------------------------------------

def hero_intro(world: World, hero: Entity, helper: Entity, project: str) -> None:
    world.say(
        f"In the science corner, {hero.id} wore a tiny cape and a brave grin. "
        f"{hero.pronoun().capitalize()} loved building {project} with {helper.id}."
    )


def threat_arrives(world: World, hero: Entity, project: str, threat: str) -> None:
    world.threat_active = True
    world.get("threat").meters["danger"] = 1
    world.say(
        f"Then a ferocious bird swooped near the science corner and started to {threat} "
        f"at the {project}. The room filled with {THREATS[threat]['sound']}."
    )


def brave_pause(world: World, hero: Entity) -> None:
    hero.memes["bravery"] = hero.memes.get("bravery", 0) + 1
    world.say(
        f"{hero.id} felt a quick wobble in {hero.pronoun('possessive')} knees, "
        f"but {hero.pronoun()} stood still. That was bravery."
    )


def problem_solve(world: World, hero: Entity, helper: Entity, project: str, tool: str, threat: str) -> None:
    if tool not in TOOLS:
        raise StoryError("The chosen tool is not part of this science-corner story.")

    world.tool_used = True
    item = TOOLS[tool]
    world.get("tool").meters["help"] = 1
    world.say(
        f"{hero.id} had an idea. {hero.pronoun().capitalize()} and {helper.id} used {item} "
        f"to make a safe shield. The shield covered the {project} just in time."
    )
    if threat == "peck":
        world.say(
            f"The ferocious beak pecked at the shield instead of the {project}, and the "
            f"paper stars stayed safe."
        )


def ending(world: World, hero: Entity, helper: Entity, project: str) -> None:
    hero.memes["joy"] = hero.memes.get("joy", 0) + 1
    world.say(
        f"At last, the bird hopped away, and the science corner was calm again. "
        f"{hero.id} smiled at the finished {project}, proud that bravery and problem solving "
        f"had saved the day."
    )


# ---------------------------------------------------------------------------
# Story generation
# ---------------------------------------------------------------------------

def tell(params: StoryParams) -> World:
    world = World()
    hero = world.add(Entity(
        id=params.hero_name,
        kind="character",
        type=params.hero_type,
        meters={"courage": 0},
        memes={"bravery": 0, "joy": 0},
    ))
    helper = world.add(Entity(
        id=params.helper_name,
        kind="character",
        type="adult",
        meters={"calm": 1},
        memes={"support": 1},
    ))
    world.add(Entity(id="threat", kind="thing", type="bird", label=params.threat, meters={"danger": 0}))
    world.add(Entity(id="tool", kind="thing", type="tool", label=params.tool, meters={"help": 0}))

    hero_intro(world, hero, helper, PROJECTS[params.project])
    world.para()
    threat_arrives(world, hero, PROJECTS[params.project], params.threat)
    brave_pause(world, hero)
    world.para()
    problem_solve(world, hero, helper, PROJECTS[params.project], params.tool, params.threat)
    ending(world, hero, helper, PROJECTS[params.project])

    world.facts = {
        "hero": hero,
        "helper": helper,
        "project": params.project,
        "threat": params.threat,
        "tool": params.tool,
        "bravery": hero.memes.get("bravery", 0),
        "solved": world.tool_used,
    }
    return world


# ---------------------------------------------------------------------------
# QA and prompts
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a short superhero story set in a science corner about bravery and problem solving.',
        f"Tell a child-friendly story where {f['hero'].id} faces a ferocious {f['threat']} and saves a science project.",
        f"Write a story in which {f['hero'].id} and {f['helper'].id} use a clever tool to protect {PROJECTS[f['project']]}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    project = PROJECTS[f["project"]]
    tool = TOOLS[f["tool"]]
    return [
        QAItem(
            question=f"Where did {hero.id} and {helper.id} work on the project?",
            answer=f"They worked in the science corner, where the little superhero story happened.",
        ),
        QAItem(
            question=f"What problem did the ferocious bird cause?",
            answer=f"The bird kept pecking at {project}, so the project needed protection.",
        ),
        QAItem(
            question=f"What did {hero.id} use to solve the problem?",
            answer=f"{hero.id} and {helper.id} used {tool} as a shield to protect the project.",
        ),
        QAItem(
            question=f"How did {hero.id} show bravery?",
            answer=f"{hero.id} showed bravery by staying calm, thinking hard, and helping fix the problem instead of panicking.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is bravery?",
            answer="Bravery means staying steady and doing the right thing even when something feels scary.",
        ),
        QAItem(
            question="What is problem solving?",
            answer="Problem solving means thinking carefully and trying a smart way to fix a difficulty.",
        ),
        QAItem(
            question="What is a science corner?",
            answer="A science corner is a small place for experiments, tools, and building things.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
hero(H) :- hero_name(H).
helper(K) :- helper_name(K).
project(P) :- project_name(P).
threat(T) :- threat_name(T).
tool(U) :- tool_name(U).

brave(H) :- bravery_feature.
problem_solves(H) :- problem_solving_feature.

safe_project(H,P) :- brave(H), problem_solves(H), project(P), tool(U), threat(T), ferocious(T).
"""

def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("hero_name", "hero"),
        asp.fact("helper_name", "helper"),
        asp.fact("project_name", "project"),
        asp.fact("threat_name", "peck"),
        asp.fact("tool_name", "tape"),
        asp.fact("bravery_feature"),
        asp.fact("problem_solving_feature"),
        asp.fact("ferocious", "peck"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    try:
        model = asp.one_model(asp_program("#show safe_project/2."))
        atoms = set(asp.atoms(model, "safe_project"))
        expected = {("hero", "project")}
        if atoms == expected:
            print("OK: ASP twin matches Python reasonableness gate.")
            return 0
        print("MISMATCH: ASP twin does not match Python reasonableness gate.")
        print("ASP:", sorted(atoms))
        print("PY :", sorted(expected))
        return 1
    except Exception as e:
        print(f"ASP verification failed: {e}")
        return 1


# ---------------------------------------------------------------------------
# Validation / params
# ---------------------------------------------------------------------------

def is_reasonable(params: StoryParams) -> bool:
    return params.project in PROJECTS and params.threat in THREATS and params.tool in TOOLS


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero story world: science corner, bravery, and problem solving.")
    ap.add_argument("--hero-name", choices=HERO_NAMES)
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--helper-name", choices=HELPER_NAMES)
    ap.add_argument("--project", choices=PROJECTS)
    ap.add_argument("--threat", choices=THREATS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    hero_type = args.hero_type or rng.choice(["girl", "boy"])
    hero_name = args.hero_name or rng.choice(HERO_NAMES)
    helper_name = args.helper_name or rng.choice(HELPER_NAMES)
    project = args.project or rng.choice(list(PROJECTS))
    threat = args.threat or rng.choice(list(THREATS))
    tool = args.tool or rng.choice(list(TOOLS))
    params = StoryParams(
        hero_name=hero_name,
        hero_type=hero_type,
        helper_name=helper_name,
        project=project,
        threat=threat,
        tool=tool,
    )
    if not is_reasonable(params):
        raise StoryError("The requested story choices do not fit this science-corner superhero scene.")
    return params


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


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print()
        print("--- trace ---")
        for k, e in sample.world.entities.items():
            print(k, e.kind, e.type, e.label, e.meters, e.memes)
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show safe_project/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show safe_project/2."))
        print(set(asp.atoms(model, "safe_project")))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    curated = [
        StoryParams("Milo", "boy", "Dr. Finch", "tower", "peck", "tape"),
        StoryParams("Nia", "girl", "Ms. Echo", "robot", "peck", "cardboard"),
        StoryParams("Tess", "girl", "Coach Vega", "bridge", "peck", "cup"),
    ]

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1

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
            header = f"### {p.hero_name}: {p.project} / {p.threat} / {p.tool}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
