#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/material_ize_pupil_possessive_dialogue_inner_monologue.py
=========================================================================================

A standalone storyworld for a tiny space-adventure domain where a child explorer
uses a materializer, learns about a spaceship pupil window, and solves a tricky
problem with dialogue and inner monologue.

Seed words:
- material-ize
- pupil
- possessive

Features:
- Dialogue
- Inner Monologue
- Problem Solving

The world is built around a simple premise: a scout ship loses one tiny but
important part, the crew must think carefully, and a clever fix changes the
ending image.

This script follows the Storyweavers storyworld contract:
- self-contained stdlib-only script
- eager import of storyworlds/results.py
- StoryParams, build_parser, resolve_params, generate, emit, main
- -n, --all, --seed, --trace, --qa, --json, --asp, --verify, --show-asp
- Python reasonableness gate and inline ASP twin
- world-state-driven prose and QA
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    attrs: dict = field(default_factory=dict)
    material: bool = False
    transparent: bool = False
    critical: bool = False

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

@dataclass
class Setting:
    id: str
    phrase: str
    detail: str

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Tool:
    id: str
    label: str
    materializes: bool
    power: int
    safe: bool = True
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Problem:
    id: str
    label: str
    need: str
    severity: int
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Fix:
    id: str
    label: str
    method: str
    power: int
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
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
        w = World()
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = copy.deepcopy(self.facts)
        return w


@dataclass
@dataclass
class StoryParams:
    setting: str
    hero: str
    hero_type: str
    companion: str
    companion_type: str
    tool: str
    problem: str
    fix: str
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


SETTINGS = {
    "orbital_bay": Setting(
        "orbital_bay",
        "an orbital repair bay",
        "The station window looked down on a blue planet, and silver panels hummed softly.",
    ),
    "moon_dock": Setting(
        "moon_dock",
        "a moon dock",
        "The dock floated above a gray horizon, with stars hanging like tiny sparks.",
    ),
    "cargo_ring": Setting(
        "cargo_ring",
        "a cargo ring",
        "The ring curved around the station, full of crates, cables, and blinking lights.",
    ),
}

TOOLS = {
    "materializer": Tool(
        "materializer",
        "materializer",
        True,
        2,
        tags={"materialize"},
    ),
    "scanner": Tool(
        "scanner",
        "scanner",
        False,
        0,
        tags={"pupil"},
    ),
    "projector": Tool(
        "projector",
        "projector",
        True,
        1,
        tags={"materialize"},
    ),
}

PROBLEMS = {
    "pupil_shield": Problem(
        "pupil_shield",
        "the pupil shield",
        "a tiny clear pupil window",
        2,
        tags={"pupil"},
    ),
    "supply_crate": Problem(
        "supply_crate",
        "the supply crate",
        "a missing crate latch",
        1,
        tags={"possessive"},
    ),
    "star_map": Problem(
        "star_map",
        "the star map",
        "a torn star map panel",
        3,
        tags={"pupil", "materialize"},
    ),
}

FIXES = {
    "clone_lens": Fix(
        "clone_lens",
        "the clone lens",
        "materialize a new part",
        3,
        tags={"materialize"},
    ),
    "patch_kit": Fix(
        "patch_kit",
        "the patch kit",
        "seal the crack with a clear patch",
        2,
        tags={"pupil"},
    ),
    "lock_tab": Fix(
        "lock_tab",
        "the lock tab",
        "replace the broken latch with a strong tab",
        1,
        tags={"possessive"},
    ),
}

GIRL_NAMES = ["Luna", "Mira", "Nova", "Tia", "Zuri", "Ivy"]
BOY_NAMES = ["Kai", "Jett", "Arlo", "Finn", "Noel", "Milo"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for tid, tool in TOOLS.items():
            for pid, problem in PROBLEMS.items():
                if any(tag in tool.tags for tag in problem.tags):
                    for fid, fix in FIXES.items():
                        if any(tag in fix.tags for tag in problem.tags) and fix.power >= problem.severity:
                            combos.append((sid, tid, pid))
    return combos


def tool_reasonable(tool: Tool, problem: Problem) -> bool:
    return any(tag in tool.tags for tag in problem.tags)


def fix_reasonable(fix: Fix, problem: Problem) -> bool:
    return any(tag in fix.tags for tag in problem.tags) and fix.power >= problem.severity


def describe_rejection(tool: Tool, problem: Problem) -> str:
    return (
        f"(No story: {tool.label} does not fit {problem.label} well enough. "
        f"The world needs a problem that can honestly be solved by the tools.)"
    )


def describe_fix_rejection(fix: Fix, problem: Problem) -> str:
    return (
        f"(No story: {fix.label} is too weak for {problem.label}, so the ending "
        f"would not feel like a real problem solved.)"
    )


def _build_names(rng: random.Random) -> tuple[str, str, str, str]:
    hero_type = rng.choice(["girl", "boy"])
    companion_type = "boy" if hero_type == "girl" else "girl"
    hero = rng.choice(GIRL_NAMES if hero_type == "girl" else BOY_NAMES)
    companion = rng.choice([n for n in (BOY_NAMES if companion_type == "boy" else GIRL_NAMES) if n != hero])
    return hero, hero_type, companion, companion_type


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space-adventure storyworld with dialogue, inner monologue, and problem solving.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--hero")
    ap.add_argument("--companion")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--companion-type", choices=["girl", "boy"])
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
    setting = args.setting or rng.choice(list(SETTINGS))
    problem_id = args.problem or rng.choice(list(PROBLEMS))
    problem = PROBLEMS[problem_id]

    tool_id = args.tool or rng.choice([tid for tid, t in TOOLS.items() if tool_reasonable(t, problem)])
    tool = TOOLS[tool_id]
    if not tool_reasonable(tool, problem):
        raise StoryError(describe_rejection(tool, problem))

    fix_id = args.fix or rng.choice([fid for fid, f in FIXES.items() if fix_reasonable(f, problem)])
    fix = FIXES[fix_id]
    if not fix_reasonable(fix, problem):
        raise StoryError(describe_fix_rejection(fix, problem))

    hero = args.hero
    companion = args.companion
    hero_type = args.hero_type
    companion_type = args.companion_type
    if hero is None or companion is None or hero_type is None or companion_type is None:
        hr, ht, cp, ct = _build_names(rng)
        hero = hero or hr
        companion = companion or cp
        hero_type = hero_type or ht
        companion_type = companion_type or ct

    return StoryParams(setting, hero, hero_type, companion, companion_type, tool_id, problem_id, fix_id)


def reason_gate(params: StoryParams) -> None:
    if not tool_reasonable(TOOLS[params.tool], PROBLEMS[params.problem]):
        raise StoryError(describe_rejection(TOOLS[params.tool], PROBLEMS[params.problem]))
    if not fix_reasonable(FIXES[params.fix], PROBLEMS[params.problem]):
        raise StoryError(describe_fix_rejection(FIXES[params.fix], PROBLEMS[params.problem]))


def generate_story(world: World, params: StoryParams) -> None:
    setting = SETTINGS[params.setting]
    tool = TOOLS[params.tool]
    problem = PROBLEMS[params.problem]
    fix = FIXES[params.fix]

    hero = world.add(Entity(params.hero, "character", params.hero_type, role="hero"))
    companion = world.add(Entity(params.companion, "character", params.companion_type, role="companion"))
    bay = world.add(Entity("setting", "thing", "place", label=setting.phrase))
    issue = world.add(Entity("problem", "thing", "problem", label=problem.label, critical=True))
    tool_ent = world.add(Entity(tool.id, "thing", "tool", label=tool.label, material=tool.materializes))
    fix_ent = world.add(Entity(fix.id, "thing", "fix", label=fix.label, material=True))

    hero.memes["curiosity"] = 1.0
    companion.memes["care"] = 1.0
    issue.meters["severity"] = float(problem.severity)
    world.facts.update(setting=setting, tool=tool, problem=problem, fix=fix, hero=hero, companion=companion,
                       bay=bay, issue=issue, tool_ent=tool_ent, fix_ent=fix_ent)

    world.say(f"{hero.id} and {companion.id} drifted through {setting.phrase}. {setting.detail}")
    world.say(f'Their job was simple: keep the ship calm and check every little thing.')
    world.say(f'Inside {hero.id}\'s suit, a small inner voice whispered, "Today needs a careful fix."')
    world.say(f'"Do you see the {problem.label}?" {companion.id} asked.')
    world.say(f'"Yes," {hero.id} said, staring at the panel. "But I think we can solve it."')

    world.para()
    world.say(
        f"{hero.id} reached for the {tool.label}. "
        f"Material-ize was the word on the screen, and the machine could make a spare part appear from light."
    )
    world.say(
        f'"If I can material-ize a new piece," {hero.id} muttered, '
        f'"then the ship can be safe again."'
    )
    world.say(f'"Will it work?" {companion.id} asked.')
    world.say(f'"It should," {hero.id} said, "if I choose the right shape."')

    world.para()
    # Problem-solving turn: the chosen fix beats the severity.
    if fix.power >= problem.severity:
        issue.meters["fixed"] = 1.0
        issue.meters["severity"] = 0.0
        hero.memes["relief"] = 1.0
        companion.memes["relief"] = 1.0
        world.say(
            f"{hero.id} closed {hero.pronoun('possessive')} eyes for a second, then tried again. "
            f"With one bright buzz, the {fix.label} worked and the broken part was made whole."
        )
        world.say(
            f'"That did it!" {companion.id} grinned. '
            f'"You really did solve it."'
        )
        world.say(
            f'{hero.id} smiled back. "I just had to think, ask, and try the right thing."'
        )
        world.para()
        world.say(
            f"By the end, the pupil window gleamed clear again, and the ship sailed on under a field of stars."
        )
    else:
        issue.meters["fixed"] = 0.0
        hero.memes["worry"] = 1.0
        world.say(
            f"{hero.id} tried, but the fix was too small. The broken piece stayed broken, and the bay still felt tense."
        )
        world.say(
            f'"We need another plan," {companion.id} said softly, and {hero.id} nodded.'
        )
        world.say(
            f"Together they fetched the bigger tools and kept working until the station lights steadied."
        )

    world.facts["outcome"] = "fixed" if issue.meters.get("fixed", 0) >= THRESHOLD else "unfinished"


def story_text(world: World) -> str:
    return world.render()


def prompts_from_world(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a space-adventure story for a young child that includes the words "{f["tool"].label}", "material-ize", and "pupil".',
        f"Tell a story where {f['hero'].id} and {f['companion'].id} solve a ship problem by thinking carefully and talking it through.",
        f"Write a gentle problem-solving story in a space bay with dialogue and an inner monologue about choosing the right fix.",
    ]


def story_qa_from_world(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    comp = f["companion"]
    problem = f["problem"]
    fix = f["fix"]
    setting = f["setting"]
    return [
        QAItem(
            question="What was the story about?",
            answer=f"It was about {hero.id} and {comp.id} trying to solve a problem in {setting.phrase}. They had to use careful thinking instead of rushing.",
        ),
        QAItem(
            question="What did the hero want to do?",
            answer=f"{hero.id} wanted to material-ize a new part so the broken {problem.label} could be fixed. {hero.id} kept thinking about the right shape and the right way to help.",
        ),
        QAItem(
            question="How did they solve the problem?",
            answer=f"They used {fix.label} and kept working until the problem was fixed. The fix worked because it matched the need and made the ship safe again.",
        ),
    ]


def world_qa_from_world(world: World) -> list[QAItem]:
    return [
        QAItem("What does a materializer do?", "A materializer makes a new object appear or forms one from stored matter. It is a careful machine, not a toy."),
        QAItem("What is a pupil?", "A pupil can mean the dark center of an eye or, in a space window, a small clear opening that lets light through."),
        QAItem("What does possessive mean?", "Possessive means showing that something belongs to someone, like saying 'her tool' or 'his ship'."),
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


def generate(params: StoryParams) -> StorySample:
    reason_gate(params)
    world = World()
    generate_story(world, params)
    return StorySample(
        params=params,
        story=story_text(world),
        prompts=prompts_from_world(world),
        story_qa=story_qa_from_world(world),
        world_qa=world_qa_from_world(world),
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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.material:
            bits.append("material=True")
        if e.critical:
            bits.append("critical=True")
        lines.append(f"  {e.id:12} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("orbital_bay", "Luna", "girl", "Kai", "boy", "materializer", "pupil_shield", "clone_lens"),
    StoryParams("moon_dock", "Milo", "boy", "Mira", "girl", "projector", "star_map", "clone_lens"),
    StoryParams("cargo_ring", "Nova", "girl", "Finn", "boy", "scanner", "supply_crate", "lock_tab"),
]


def outcome_of(params: StoryParams) -> str:
    return "fixed" if FIXES[params.fix].power >= PROBLEMS[params.problem].severity else "unfinished"


ASP_RULES = r"""
valid(S, T, P) :- setting(S), tool(T), problem(P), tool_fit(T, P), fix_fit(P).
tool_fit(T, P) :- tool(T), problem(P), ttag(T, X), ptag(P, X).
fix_fit(P) :- fix(F), problem(P), ftag(F, X), ptag(P, X), power(F, W), severity(P, S), W >= S.
outcome(fixed) :- chosen_fix(F), chosen_problem(P), power(F, W), severity(P, S), W >= S.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        for tag in t.tags:
            lines.append(asp.fact("ttag", tid, tag))
        lines.append(asp.fact("power", tid, t.power))
    for pid, p in PROBLEMS.items():
        lines.append(asp.fact("problem", pid))
        for tag in p.tags:
            lines.append(asp.fact("ptag", pid, tag))
        lines.append(asp.fact("severity", pid, p.severity))
    for fid, f in FIXES.items():
        lines.append(asp.fact("fix", fid))
        for tag in f.tags:
            lines.append(asp.fact("ftag", fid, tag))
        lines.append(asp.fact("power", fid, f.power))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        rc = 1
        print("MISMATCH: ASP and Python valid_combos differ.")
    else:
        print(f"OK: ASP and Python valid_combos match ({len(valid_combos())} combos).")
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        print("OK: generate smoke test succeeded.")
    except Exception as exc:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.problem and args.tool and not tool_reasonable(TOOLS[args.tool], PROBLEMS[args.problem]):
        raise StoryError(describe_rejection(TOOLS[args.tool], PROBLEMS[args.problem]))
    if args.problem and args.fix and not fix_reasonable(FIXES[args.fix], PROBLEMS[args.problem]):
        raise StoryError(describe_fix_rejection(FIXES[args.fix], PROBLEMS[args.problem]))

    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.tool is None or c[1] == args.tool)
              and (args.problem is None or c[2] == args.problem)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, tool, problem = rng.choice(sorted(combos))
    fix = args.fix or rng.choice([fid for fid, fx in FIXES.items() if fix_reasonable(fx, PROBLEMS[problem])])
    hero = args.hero
    companion = args.companion
    hero_type = args.hero_type
    companion_type = args.companion_type
    if not all([hero, companion, hero_type, companion_type]):
        h, ht, c, ct = _build_names(rng)
        hero = hero or h
        companion = companion or c
        hero_type = hero_type or ht
        companion_type = companion_type or ct
    return StoryParams(setting, hero, hero_type, companion, companion_type, tool, problem, fix)


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("", "#show valid/3."))
        print("\n".join(str(a) for a in asp.atoms(model, "valid")))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            p = resolve_params(args, random.Random(base_seed + i))
            p.seed = base_seed + i
            s = generate(p)
            if s.story in seen:
                i += 1
                continue
            seen.add(s.story)
            samples.append(s)
            i += 1

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
