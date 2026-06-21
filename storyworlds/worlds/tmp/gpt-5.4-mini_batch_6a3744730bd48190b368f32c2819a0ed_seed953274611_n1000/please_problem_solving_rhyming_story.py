#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/please_problem_solving_rhyming_story.py
=======================================================================

A small standalone storyworld about polite problem solving with a rhyming,
child-facing tale. The premise is simple: a child wants to play outside, meets
a small snag, says "please", and solves the problem with a helper and a safe
tool instead of a tantrum.

The world is intentionally tiny and simulation-driven:
- entities have physical meters and emotional memes
- a forward-chained rule nudges the scene from trouble to solution
- the rendered story is built from the evolving state, not a frozen template
- QA is generated from world facts, not by parsing the final English

Seed inspiration
----------------
The seed word is "please". The style is "Rhyming Story". The feature is
"Problem Solving". This script turns that into a tiny scene where politeness
helps a child get a needed object and finish play.

Run it
------
    python storyworlds/worlds/gpt-5.4-mini/please_problem_solving_rhyming_story.py
    python storyworlds/worlds/gpt-5.4-mini/please_problem_solving_rhyming_story.py --qa
    python storyworlds/worlds/gpt-5.4-mini/please_problem_solving_rhyming_story.py --verify
    python storyworlds/worlds/gpt-5.4-mini/please_problem_solving_rhyming_story.py --json
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
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
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Location:
    id: str
    label: str
    setting_line: str
    problem_line: str
    ending_line: str


@dataclass
class Problem:
    id: str
    label: str
    need: str
    snag: str
    rhyme: str
    help_word: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    solves: set[str]
    tags: set[str] = field(default_factory=set)


@dataclass
class Helper:
    id: str
    label: str
    type: str
    title: str
    has: set[str] = field(default_factory=set)


@dataclass
class World:
    location: Location
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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
        clone = World(self.location)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_relief(world: World) -> list[str]:
    out = []
    child = world.get("child")
    if child.meters["stuck"] >= THRESHOLD and ("relief", "child") not in world.fired:
        world.fired.add(("relief", "child"))
        child.memes["worry"] += 1
        out.append("__relief__")
    return out


def _r_shine(world: World) -> list[str]:
    out = []
    child = world.get("child")
    helper = world.get("helper")
    if child.meters["solved"] >= THRESHOLD and ("shine", "child") not in world.fired:
        world.fired.add(("shine", "child"))
        child.memes["joy"] += 1
        helper.memes["pride"] += 1
        out.append("__shine__")
    return out


CAUSAL_RULES = [Rule("relief", _r_relief), Rule("shine", _r_shine)]


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


def reasonableness_gate(problem: Problem, tool: Tool) -> bool:
    return problem.id in tool.solves


def choose_combo(rng: random.Random, args: argparse.Namespace) -> tuple[str, str, str, str]:
    locs = list(LOCATIONS)
    probs = [p for p in PROBLEMS if p != "empty"]
    tools = list(TOOLS)
    if args.location and args.location not in LOCATIONS:
        raise StoryError("(Unknown location.)")
    if args.problem and args.problem not in PROBLEMS:
        raise StoryError("(Unknown problem.)")
    if args.tool and args.tool not in TOOLS:
        raise StoryError("(Unknown tool.)")
    if args.problem and args.tool and not reasonableness_gate(PROBLEMS[args.problem], TOOLS[args.tool]):
        raise StoryError(f"(No story: {TOOLS[args.tool].label} cannot solve that problem.)")
    valid = [(l, p, t) for l in LOCATIONS for p in PROBLEMS if p != "empty" for t in TOOLS
             if (args.location is None or l == args.location)
             and (args.problem is None or p == args.problem)
             and (args.tool is None or t == args.tool)
             and reasonableness_gate(PROBLEMS[p], TOOLS[t])]
    if not valid:
        raise StoryError("(No valid combination matches the given options.)")
    return rng.choice(sorted(valid))


def tell(location: Location, problem: Problem, tool: Tool, helper: Helper,
         child_name: str, child_gender: str, parent_title: str) -> World:
    world = World(location)
    child = world.add(Entity(id="child", kind="character", type=child_gender, label=child_name, role="hero"))
    parent = world.add(Entity(id="parent", kind="character", type=parent_title, label=f"the {parent_title}", role="helper"))
    guide = world.add(Entity(id="helper", kind="character", type=helper.type, label=helper.label, role=helper.title, has=set(helper.has)))
    child.memes["hope"] += 1
    child.meters["stuck"] += 1

    world.say(f"{child_name} went out to play, in a spot that was bright and light.")
    world.say(f"{location.setting_line} But then came a snag, and that snag was not right.")

    world.para()
    world.say(f'{child_name} wanted {problem.need}, but {problem.snag} made a tight little fight.')
    world.say(f'{child_name} took a breath and said, "Can you help me, please?"')
    world.say(f"That tiny word rang soft and sweet, like a breeze in the trees.")

    if tool.id == "none":
        raise StoryError("(No story: this problem needs a tool.)")

    world.say(f"The {helper.title} heard the plea, and walked over to see.")
    world.say(f'"We can use {tool.phrase}," said {helper.label}. "That ought to be the key."')
    world.say(f"Together they {problem.help_word}, and the snag came undone with ease.")

    child.meters["solved"] += 1
    parent.memes["relief"] += 1
    guide.memes["calm"] += 1
    propagate(world, narrate=False)

    world.para()
    world.say(f"{location.ending_line}")
    world.say(f"{child_name} laughed, and the day felt right.")
    world.say(f"With a kind word and a clever plan, the whole world shone bright.")

    world.facts.update(
        location=location,
        problem=problem,
        tool=tool,
        helper=helper,
        child_name=child_name,
        child_gender=child_gender,
        parent_title=parent_title,
        solved=child.meters["solved"] >= THRESHOLD,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a rhyming story for a young child that includes the word "please" and shows {f["child_name"]} solving a small problem kindly.',
        f"Tell a short rhyming story where {f['child_name']} asks for help with a snag, says please, and finds a safe fix.",
        f'Write a cheerful problem-solving story in rhyme about {f["child_name"]}, a helper, and the word "please".',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child_name"]
    problem = f["problem"]
    tool = f["tool"]
    helper = f["helper"]
    return [
        ("Who is the story about?",
         f"It is about {child}, who meets a small problem and solves it with help."),
        (f"What did {child} need to do?",
         f"{child} needed to {problem.need}. {problem.snag.capitalize()} got in the way, so {child} asked nicely for help."),
        ("How was the problem solved?",
         f"They used {tool.phrase} and worked together. That fixed the snag without making the day worse."),
        ("What important word did the child say?",
         'The child said "please". That polite word helped the helper know they were being kind and ready to work together.'),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What does please mean?",
         "Please is a polite word people use when they ask for help or ask for something kindly."),
        ("Why is it nice to ask politely?",
         "Polite words help other people feel respected. That makes it easier to work together and solve problems."),
        ("What is a problem-solver?",
         "A problem-solver is someone who stays calm, thinks, and finds a useful way to fix a trouble."),
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
    lines.append("== (3) World knowledge ==")
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
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


LOCATIONS = {
    "yard": Location("yard", "the yard", "The yard was open, with sun on the ground.", "A small snag sat by the gate.", "The path was clear again."),
    "garden": Location("garden", "the garden", "The garden was green, with flowers in a row.", "A string had twisted up low.", "The little lane could flow."),
    "porch": Location("porch", "the porch", "The porch was neat, with shoes in a line.", "A box lid had tipped, and the light could not shine.", "The lid stood straight, just fine."),
}

PROBLEMS = {
    "snagged_kite": Problem("snagged_kite", "snagged kite", "free the kite string", "a branch held it tight", "kite-light / sky-bright", "untie the string from the branch", tags={"kite", "wind"}),
    "stuck_box": Problem("stuck_box", "stuck box", "open the toy box", "the lid would not lift", "box-top / pop-stop", "lift the lid and smooth the hinge", tags={"box", "toy"}),
    "missing_ball": Problem("missing_ball", "missing ball", "find the ball", "the grass hid it well", "grass-mass / find-fast", "peek under the bench and roll the leaves aside", tags={"ball", "search"}),
    "empty": Problem("empty", "empty", "nothing", "nothing", "empty", "nothing"),
}

TOOLS = {
    "stick": Tool("stick", "a long stick", "a long stick", solves={"snagged_kite"}, tags={"kite"}),
    "key": Tool("key", "the little key", "the little key", solves={"stuck_box"}, tags={"box"}),
    "broom": Tool("broom", "a broom", "a broom", solves={"missing_ball"}, tags={"search"}),
}

HELPERS = {
    "mom": Helper("mom", "Mom", "mother", "mom", has={"stick", "broom", "key"}),
    "dad": Helper("dad", "Dad", "father", "dad", has={"stick", "broom", "key"}),
}

CURATED = [
    StoryParams(location="yard", problem="snagged_kite", tool="stick", child_name="Lily", child_gender="girl", parent_title="mother"),
    StoryParams(location="garden", problem="missing_ball", tool="broom", child_name="Tom", child_gender="boy", parent_title="father"),
    StoryParams(location="porch", problem="stuck_box", tool="key", child_name="Mia", child_gender="girl", parent_title="mother"),
]


@dataclass
class StoryParams:
    location: str
    problem: str
    tool: str
    child_name: str
    child_gender: str
    parent_title: str
    helper: str = "mom"
    seed: Optional[int] = None


def asp_facts() -> str:
    import asp
    lines = []
    for lid in LOCATIONS:
        lines.append(asp.fact("location", lid))
    for pid, p in PROBLEMS.items():
        lines.append(asp.fact("problem", pid))
        for tag in sorted(p.tags):
            lines.append(asp.fact("problem_tag", pid, tag))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        for s in sorted(t.solves):
            lines.append(asp.fact("solves", tid, s))
    return "\n".join(lines)


ASP_RULES = r"""
valid(L,P,T) :- location(L), problem(P), tool(T), solves(T,P).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str, str]]:
    return sorted((l, p, t) for l in LOCATIONS for p in PROBLEMS if p != "empty" for t in TOOLS if reasonableness_gate(PROBLEMS[p], TOOLS[t]))


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: ASP matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH between ASP and Python.")
    try:
        sample = generate(resolve_params(argparse.Namespace(location=None, problem=None, tool=None), random.Random(7)))
        _ = sample.story
        print("OK: normal story generation smoke test passed.")
    except Exception as e:
        rc = 1
        print(f"SMOKE TEST FAILED: {e}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny rhyming problem-solving storyworld with please.")
    ap.add_argument("--location", choices=LOCATIONS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--tool", choices=TOOLS)
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
    valid = valid_combos()
    if args.location and args.problem and args.tool and (args.location, args.problem, args.tool) not in valid:
        raise StoryError("(That combination does not make a reasonable problem-solving story.)")
    combos = [c for c in valid
              if (args.location is None or c[0] == args.location)
              and (args.problem is None or c[1] == args.problem)
              and (args.tool is None or c[2] == args.tool)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    loc, prob, tool = rng.choice(combos)
    child_name = rng.choice(["Lily", "Mia", "Tom", "Ben", "Zoe"])
    child_gender = rng.choice(["girl", "boy"])
    parent_title = rng.choice(["mother", "father"])
    helper = rng.choice(list(HELPERS))
    return StoryParams(location=loc, problem=prob, tool=tool, child_name=child_name, child_gender=child_gender, parent_title=parent_title, helper=helper)


def generate(params: StoryParams) -> StorySample:
    if params.location not in LOCATIONS or params.problem not in PROBLEMS or params.tool not in TOOLS or params.helper not in HELPERS:
        raise StoryError("(Invalid params.)")
    loc = LOCATIONS[params.location]
    prob = PROBLEMS[params.problem]
    tool = TOOLS[params.tool]
    helper = HELPERS[params.helper]
    world = tell(loc, prob, tool, helper, params.child_name, params.child_gender, params.parent_title)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} valid combos:")
        for row in asp_valid_combos():
            print(" ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
            i += 1
            try:
                params = resolve_params(args, random.Random(base_seed + i))
                params.seed = base_seed + i
                sample = generate(params)
                if sample.story in seen:
                    continue
                seen.add(sample.story)
                samples.append(sample)
            except StoryError as e:
                print(e)
                return

    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {i+1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
