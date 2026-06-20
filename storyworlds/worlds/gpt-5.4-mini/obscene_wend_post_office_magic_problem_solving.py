#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/obscene_wend_post_office_magic_problem_solving.py
=================================================================================

A standalone story world for a small slice-of-life tale set in a post office:
a child has a tiny magical mishap at the counter, feels embarrassed, and uses
calm problem-solving with a clerk's help to fix it. The world keeps the action
grounded in physical meters and emotional memes, with the story driven by state
changes rather than a frozen paragraph.

Seed words and prompt features:
- obscene
- wend
- Magic
- Problem Solving
- post office
- slice of life

This script follows the Storyweavers contract:
- stdlib only
- StoryParams, build_parser, resolve_params, generate, emit, main
- QAItem, StoryError, StorySample imported eagerly from storyworlds/results.py
- lazy import of storyworlds/asp.py only in ASP helpers
- --verify checks Python/ASP parity and runs a normal generation smoke test
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    owner: str = ""
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict = field(default_factory=dict)

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
        return {"mother": "mom", "father": "dad", "clerk": "clerk"}.get(self.type, self.type)


@dataclass
class Place:
    id: str
    label: str
    calm: str
    shelves: str
    line: str


@dataclass
class MagicTool:
    id: str
    label: str
    phrase: str
    effect: str
    risk: str
    allowed: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Problem:
    id: str
    label: str
    trouble: str
    fix: str
    result: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
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
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_spill(world: World) -> list[str]:
    out: list[str] = []
    for e in world.entities.values():
        if e.meters["sparkle"] < THRESHOLD:
            continue
        sig = ("spill", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.meters["mess"] += 1
        if "counter" in world.entities:
            world.get("counter").meters["glow"] += 0.5
        out.append("__sparkle__")
    return out


def _r_embarrass(world: World) -> list[str]:
    out: list[str] = []
    if "child" not in world.entities:
        return out
    child = world.get("child")
    if child.meters["mess"] < THRESHOLD:
        return out
    sig = ("embarrass", child.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["embarrassment"] += 1
    out.append("__feel__")
    return out


CAUSAL_RULES = [Rule("spill", "physical", _r_spill), Rule("embarrass", "social", _r_embarrass)]


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


def hazard_at_risk(tool: MagicTool, problem: Problem) -> bool:
    return tool.allowed and "mess" in problem.tags


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for t in TOOLS:
        for p in PROBLEMS:
            if hazard_at_risk(TOOLS[t], PROBLEMS[p]):
                combos.append((t, p))
    return combos


@dataclass
class StoryParams:
    place: str
    tool: str
    problem: str
    child: str
    child_gender: str
    clerk: str
    clerk_gender: str
    seed: Optional[int] = None


def _maybe_obscene_word(world: World, child: Entity, tool: MagicTool) -> None:
    child.memes["embarrassment"] += 0.5
    world.say(
        f"{child.id} tried a small magic trick at the post office, and the result "
        f"was embarrassingly obscene to look at."
    )
    world.say(
        f"The {tool.label} glittered, then wobbled as if it could not decide where to wend."
    )


def _setup(world: World, child: Entity, clerk: Entity, place: Place) -> None:
    child.memes["curiosity"] += 1
    clerk.memes["calm"] += 1
    world.say(
        f"On a quiet morning, {child.id} and {clerk.id} stood in the post office. "
        f"{place.calm} {place.shelves} {place.line}"
    )


def _trouble(world: World, child: Entity, tool: MagicTool, problem: Problem) -> None:
    world.say(
        f"{child.id} wanted to use {tool.phrase}, but {problem.trouble}. "
        f"The little magic felt helpful at first."
    )
    child.memes["hope"] += 1


def _predict_fix(world: World, problem: Problem) -> bool:
    sim = world.copy()
    sim.get("child").meters["mess"] += 1
    propagate(sim, narrate=False)
    return True


def _warn(world: World, clerk: Entity, child: Entity, problem: Problem, tool: MagicTool) -> None:
    _predict_fix(world, problem)
    child.memes["uncertainty"] += 1
    world.say(
        f"{clerk.id} noticed the mess and said, "
        f'"Let\'s solve it gently. We can wipe this up, sort the letters, and keep going."'
    )


def _fix(world: World, clerk: Entity, child: Entity, problem: Problem) -> None:
    child.meters["mess"] = 0
    child.memes["embarrassment"] = 0
    child.memes["relief"] += 1
    world.say(
        f"{clerk.id} showed {child.id} how to fix it: {problem.fix}. "
        f"Together they made the counter neat again."
    )
    world.say(
        f"By the time the next customer wended to the front of the line, "
        f"{problem.result}."
    )


def tell(place: Place, tool: MagicTool, problem: Problem, child_name: str, child_gender: str,
         clerk_name: str, clerk_gender: str) -> World:
    world = World(place)
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    clerk = world.add(Entity(id=clerk_name, kind="character", type=clerk_gender, role="clerk"))
    counter = world.add(Entity(id="counter", label="the counter"))
    world.add(counter)

    _setup(world, child, clerk, place)
    world.para()
    _trouble(world, child, tool, problem)
    _maybe_obscene_word(world, child, tool)
    _warn(world, clerk, child, problem, tool)
    child.meters["sparkle"] += 1
    propagate(world, narrate=True)
    world.para()
    _fix(world, clerk, child, problem)
    world.facts.update(child=child, clerk=clerk, place=place, tool=tool, problem=problem, counter=counter)
    return world


PLACES = {
    "post_office": Place(
        "post_office",
        "the post office",
        "The room was calm, with soft footsteps and neat little stamps.",
        "The shelves were full of envelopes and postcards.",
        "A small line of customers waited by the desk.",
    )
}

TOOLS = {
    "stamp_spark": MagicTool(
        "stamp_spark",
        "sparkling stamp",
        "a sparkling stamp",
        "made tiny stars pop out of the ink pad",
        "might leave a shiny mess on the counter",
        allowed=True,
        tags={"magic", "mess"},
    ),
    "glitter_tap": MagicTool(
        "glitter_tap",
        "glitter tap",
        "a glitter tap",
        "made a ribbon of light hop across the paper",
        "could scatter sparkles everywhere",
        allowed=True,
        tags={"magic", "mess"},
    ),
}

PROBLEMS = {
    "ink_spot": Problem(
        "ink_spot",
        "ink spot",
        "an ink spot spread across the receipt",
        "first blot the spot, then replace the paper",
        "the receipt would look clean again",
        tags={"mess"},
    ),
    "stuck_stamp": Problem(
        "stuck_stamp",
        "stuck stamp",
        "a stamp had stuck to the envelope",
        "moisten the corner and peel it up slowly",
        "the envelope would be ready to mail",
        tags={"mess"},
    ),
}

GIRL_NAMES = ["Mia", "Lily", "Nora", "Ava", "Zoe", "Ella"]
BOY_NAMES = ["Theo", "Leo", "Finn", "Max", "Sam", "Eli"]
CLERK_NAMES = ["Mr. Reed", "Ms. Hall", "Mrs. Lane", "Mr. Brooks"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a slice-of-life story set in a post office that includes the word "{f["tool"].label}".',
        f"Tell a gentle story where {f['child'].id} makes a small magical mess at the post office and a clerk helps solve the problem.",
        'Write a calm story about magic, embarrassment, and problem solving, and include the word "wend".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = f["child"]
    clerk: Entity = f["clerk"]
    tool: MagicTool = f["tool"]
    problem: Problem = f["problem"]
    return [
        QAItem(
            question="What kind of place is the story set in?",
            answer="It is set in a post office, where people mail letters and pick up packages. The quiet setting makes the little problem feel manageable instead of huge.",
        ),
        QAItem(
            question=f"What happened when {child.id} used the magic tool?",
            answer=f"{child.id} made a small magical mess, and the {tool.label} left the counter looking wrong. That is why the child felt embarrassed before the clerk helped.",
        ),
        QAItem(
            question="How did they solve the problem?",
            answer=f"They solved it by {problem.fix}. The clerk stayed calm, and the child helped clean up so everything could go back to normal.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a post office for?",
            answer="A post office is a place where people mail letters, postcards, and packages. People also buy stamps there and sometimes get help from a clerk.",
        ),
        QAItem(
            question="What does problem solving mean?",
            answer="Problem solving means noticing what went wrong and then choosing a sensible way to fix it. Often that means staying calm, asking for help, and trying one step at a time.",
        ),
        QAItem(
            question="What does magic mean in a story like this?",
            answer="Magic in a story can mean something surprising or special that seems to happen by wonder. In a slice-of-life tale, it can stay small and gentle, like a little sparkle or glow.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- world model state ---"]
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
        out.append(f"  {e.id:10} ({e.type}) {' '.join(bits)}")
    out.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(out)


CURATED = [
    StoryParams("post_office", "stamp_spark", "ink_spot", "Mina", "girl", "Ms. Hall", "girl"),
    StoryParams("post_office", "glitter_tap", "stuck_stamp", "Noah", "boy", "Mr. Reed", "boy"),
]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.tool and args.problem:
        if not hazard_at_risk(TOOLS[args.tool], PROBLEMS[args.problem]):
            raise StoryError("(No story: that magic tool doesn't create a useful problem to solve.)")
    combos = [c for c in valid_combos()
              if (args.tool is None or c[0] == args.tool)
              and (args.problem is None or c[1] == args.problem)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    tool, problem = rng.choice(sorted(combos))
    child_gender = args.gender or rng.choice(["girl", "boy"])
    child = args.child or rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES)
    clerk_gender = args.clerk_gender or rng.choice(["girl", "boy"])
    clerk = args.clerk or rng.choice(CLERK_NAMES)
    return StoryParams("post_office", tool, problem, child, child_gender, clerk, clerk_gender)


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], TOOLS[params.tool], PROBLEMS[params.problem],
                 params.child, params.child_gender, params.clerk, params.clerk_gender)
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life post office magic problem-solving world.")
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--child")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--clerk")
    ap.add_argument("--clerk-gender", choices=["girl", "boy"])
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


ASP_RULES = r"""
hazard(T, P) :- tool(T), problem(P), allowed(T), messy(P).
valid(T, P) :- hazard(T, P).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        if t.allowed:
            lines.append(asp.fact("allowed", tid))
    for pid, p in PROBLEMS.items():
        lines.append(asp.fact("problem", pid))
        if "mess" in p.tags:
            lines.append(asp.fact("messy", pid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import io
    from contextlib import redirect_stdout

    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        rc = 1
        print("MISMATCH in valid_combos()")
    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise RuntimeError("empty story")
        buf = io.StringIO()
        with redirect_stdout(buf):
            emit(sample, trace=True, qa=True)
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    else:
        print("OK: generate/emit smoke test passed.")
    return rc


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
        for t, p in asp_valid_combos():
            print(f"  {t} {p}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            i += 1
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
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
        header = "### curated story" if args.all else (f"### variant {i + 1}" if len(samples) > 1 else "")
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
