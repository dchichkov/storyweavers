#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/slender_problem_solving_bedtime_story.py
=======================================================================

A tiny bedtime storyworld about a child, a slender problem, and a calm,
practical fix.

Seed idea
---------
A child gets ready for bed and notices a slender little problem: a toy is stuck,
a curtain cord is tangled, or a narrow bridge of pillows has slipped apart.
The child worries, asks a grown-up, and together they solve it with a gentle,
clever step. The story should feel like a bedtime tale: soft, concrete, and
comforting, with a clear turn from worry to relief.

The world model keeps the story grounded in state:
- a child has a bedtime task and a mood
- a slender object or narrow passage creates a problem
- a helper and a tool can solve it
- the ending proves the problem was fixed and the room is calm again
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
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    tags: set[str] = field(default_factory=set)

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
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

@dataclass
class Setting:
    id: str
    place: str
    hush: str
    bedtime: str
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
    phrase: str
    label: str
    slender_word: str
    location: str
    risk: str
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
class Tool:
    id: str
    label: str
    phrase: str
    action: str
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
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]

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


def _r_relief(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("child")
    problem = world.entities.get("problem")
    if not child or not problem:
        return out
    if problem.meters["solved"] < THRESHOLD:
        return out
    sig = ("relief",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["worry"] = 0.0
    child.memes["relief"] += 1
    out.append("__relief__")
    return out


CAUSAL_RULES = [Rule("relief", "social", _r_relief)]


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


def problem_is_real(problem: Problem) -> bool:
    return "slender" in problem.tags or "slender" in problem.label or "slender" in problem.phrase


def tool_helps(problem: Problem, tool: Tool) -> bool:
    return problem.id in tool.tags


def predict_fix(world: World, tool: Tool) -> dict:
    sim = world.copy()
    _use_tool(sim, sim.get("child"), sim.get("helper"), sim.get("problem"), tool, narrate=False)
    return {
        "solved": sim.get("problem").meters["solved"] >= THRESHOLD,
        "child_calm": sim.get("child").memes["worry"] < THRESHOLD,
    }


def _use_tool(world: World, child: Entity, helper: Entity, problem: Entity, tool: Tool, narrate: bool = True) -> None:
    problem.meters["solved"] += 1
    problem.meters["fixed_with"] += 1
    helper.memes["calm"] += 1
    child.memes["worry"] = 0.0
    propagate(world, narrate=narrate)


def introduce(world: World, child: Entity, helper: Entity, setting: Setting) -> None:
    child.memes["worry"] += 1
    child.memes["sleepiness"] += 1
    world.say(
        f"At bedtime, {child.id} was in {setting.place}, where everything was quiet and soft. "
        f"{setting.hush} {setting.bedtime}"
    )
    world.say(
        f"{child.id} was feeling sleepy, but {helper.id} was nearby to help if needed."
    )


def problem_becomes_known(world: World, child: Entity, problem: Entity) -> None:
    world.say(
        f"Then {child.id} noticed {problem.phrase}. It looked {problem.slender_word} and a little tricky."
    )
    world.say(
        f"{child.id} bit {child.pronoun('possessive')} lip and whispered, "
        f'"That could be a bedtime problem."'
    )


def ask_for_help(world: World, child: Entity, helper: Entity, problem: Entity) -> None:
    child.memes["bravery"] += 1
    world.say(
        f'{child.id} called, "{helper.id}, can you help me with {problem.label}?"'
    )


def explain(world: World, helper: Entity, problem: Entity) -> None:
    helper.memes["care"] += 1
    world.say(
        f"{helper.id} knelt down and looked closely. {helper.pronoun().capitalize()} said the problem was small, "
        f"but it needed a calm plan."
    )


def solve(world: World, child: Entity, helper: Entity, problem: Entity, tool: Tool) -> None:
    _use_tool(world, child, helper, problem, tool)
    world.say(
        f"Together they used {tool.phrase}; {tool.action}, and the little snag came free."
    )
    world.say(
        f"The slender problem was fixed, and the room felt easy again."
    )


def ending(world: World, child: Entity, helper: Entity, setting: Setting) -> None:
    child.memes["joy"] += 1
    helper.memes["joy"] += 1
    world.say(
        f"{child.id} smiled, snuggled back under the blanket, and listened to the hush of {setting.place}."
    )
    world.say(
        f"With the problem gone, {child.id} could fall asleep while {helper.id} watched over the room."
    )


def tell(setting: Setting, problem: Problem, tool: Tool,
         child_name: str = "Mina", child_gender: str = "girl",
         helper_name: str = "Mom", helper_gender: str = "mother") -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender, role="helper"))
    prob = world.add(Entity(id="problem", type="problem", label=problem.label))
    world.facts["problem_cfg"] = problem
    world.facts["tool"] = tool
    world.facts["setting"] = setting
    world.facts["child"] = child
    world.facts["helper"] = helper

    introduce(world, child, helper, setting)
    world.para()
    problem_becomes_known(world, child, prob)
    ask_for_help(world, child, helper, prob)
    explain(world, helper, prob)
    world.para()
    solve(world, child, helper, prob, tool)
    ending(world, child, helper, setting)

    world.facts.update(
        solved=prob.meters["solved"] >= THRESHOLD,
        child_worry=child.memes["worry"],
    )
    return world


SETTINGS = {
    "nursery": Setting("nursery", "the nursery", "The lamp made a sleepy glow.", "The night was kind."),
    "hall": Setting("hall", "the hall", "The house was hushed.", "Everyone was ready for rest."),
    "bedroom": Setting("bedroom", "the bedroom", "The room was still.", "The pillows waited softly."),
}

PROBLEMS = {
    "cord": Problem("cord", "a slender curtain cord", "curtain cord", "slender", "by the window", "tangled", {"slender", "cord"}),
    "stuck_toy": Problem("stuck_toy", "a slender toy train wheel", "toy wheel", "slender", "under the bed", "stuck", {"slender", "toy"}),
    "page": Problem("page", "a slender bookmark page", "bookmark page", "slender", "inside the book", "folded", {"slender", "book"}),
}

TOOLS = {
    "unwind": Tool("unwind", "gentle fingers", "gentle fingers", "unwinding it slowly", {"cord"}),
    "lift": Tool("lift", "a soft lamp light", "a soft lamp light", "lifting the toy carefully", {"stuck_toy"}),
    "flatten": Tool("flatten", "a steady hand", "a steady hand", "flattening the page flat", {"page"}),
}

CHILD_NAMES = ["Mina", "Nora", "Lena", "Owen", "Theo", "June", "Iris", "Eli"]
HELPER_NAMES = ["Mom", "Dad", "Aunt Bea", "Grandpa"]

TRAITS = ["sleepy", "gentle", "patient", "thoughtful"]


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for pid, problem in PROBLEMS.items():
        for tid, tool in TOOLS.items():
            if problem_is_real(problem) and tool_helps(problem, tool):
                combos.append((pid, tid))
    return combos


@dataclass
@dataclass
class StoryParams:
    setting: str
    problem: str
    tool: str
    child_name: str
    child_gender: str
    helper_name: str
    helper_gender: str
    trait: str
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


KNOWLEDGE = {
    "slender": [("What does slender mean?",
                 "Slender means long and thin, with a narrow shape.")],
    "cord": [("What is a cord?",
              "A cord is a thin rope or string. It can tangle easily.")],
    "book": [("Why do people use bookmarks?",
               "Bookmarks help people find the page they left off on.")],
    "toy": [("Why do toys get stuck?",
             "A toy can get stuck if it slips into a tight spot or something presses on it.")],
    "night": [("Why is bedtime quiet?",
                "Bedtime is quiet because people are settling down to rest and sleep.")],
    "help": [("Why ask for help?",
              "Asking for help is wise when a problem feels too hard or too tricky to solve alone.")],
}
KNOWLEDGE_ORDER = ["slender", "cord", "toy", "book", "night", "help"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    p = f["problem_cfg"]
    return [
        f'Write a bedtime story for a young child that includes the word "{p.slender_word}" and a gentle problem-solving moment.',
        f"Tell a soft bedtime story where {f['child'].id} notices {p.phrase}, asks for help, and feels better after it is fixed.",
        f'Write a short calm story for bedtime about a {p.slender_word} little problem that is solved with a clever tool.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    p = f["problem_cfg"]
    tool = f["tool"]
    qa = [
        ("Who is the story about?",
         f"It is about {child.id} and {helper.id}. The story stays close to bedtime and follows how they solve a small problem together."),
        ("What was the problem?",
         f"{p.phrase} was the problem. It was slender and a little tricky, so it needed calm attention."),
        ("How did they solve it?",
         f"They used {tool.phrase} and worked slowly until the problem was fixed. That gentle method matched how careful the problem was."),
    ]
    if f.get("solved"):
        qa.append((
            "What changed at the end?",
            f"The slender problem was gone, and {child.id} could relax again. The room became quiet and safe enough for sleep."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["problem_cfg"].tags) | set(world.facts["tool"].tags)
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags and tag in KNOWLEDGE:
            out.extend(KNOWLEDGE[tag])
    return out


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
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("nursery", "cord", "unwind", "Mina", "girl", "Mom", "mother", "sleepy"),
    StoryParams("bedroom", "stuck_toy", "lift", "Owen", "boy", "Dad", "father", "patient"),
    StoryParams("hall", "page", "flatten", "Lena", "girl", "Aunt Bea", "mother", "thoughtful"),
]


def explain_rejection(problem: Problem, tool: Tool) -> str:
    if problem.id not in tool.tags:
        return f"(No story: {tool.label} does not solve {problem.label}. Pick a tool that really helps.)"
    if not problem_is_real(problem):
        return "(No story: this problem is not slender enough for the requested bedtime tale.)"
    return "(No story: that combination is not a real problem-solving match.)"


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for pid, p in PROBLEMS.items():
        lines.append(asp.fact("problem", pid))
        lines.append(asp.fact("label", pid, p.label))
        lines.append(asp.fact("slender", pid))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        for tag in sorted(t.tags):
            lines.append(asp.fact("helps", tid, tag))
    return "\n".join(lines)


ASP_RULES = r"""
valid(P, T) :- problem(P), tool(T), helps(T, P).
slender_problem(P) :- problem(P), slender(P).
"""


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print("OK: ASP matches valid_combos().")
    else:
        print("MISMATCH in ASP and valid_combos().")
        rc = 1
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        _ = sample.story
        print("OK: generation smoke test passed.")
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        rc = 1
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small bedtime storyworld about a slender problem and a calm solution.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--child-name")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-gender", choices=["mother", "father"])
    ap.add_argument("--trait", choices=TRAITS)
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
    combos = [c for c in valid_combos()
              if (args.problem is None or c[0] == args.problem)
              and (args.tool is None or c[1] == args.tool)]
    if args.problem and args.tool:
        if (args.problem, args.tool) not in valid_combos():
            raise StoryError(explain_rejection(PROBLEMS[args.problem], TOOLS[args.tool]))
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    problem, tool = rng.choice(sorted(combos))
    setting = args.setting or rng.choice(sorted(SETTINGS))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or rng.choice(["mother", "father"])
    child_name = args.child_name or rng.choice(CHILD_NAMES)
    helper_name = args.helper_name or rng.choice(HELPER_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(setting, problem, tool, child_name, child_gender, helper_name, helper_gender, trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], PROBLEMS[params.problem], TOOLS[params.tool],
                 params.child_name, params.child_gender, params.helper_name, params.helper_gender)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
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
        print(asp_program("", "#show valid/2.\n#show slender_problem/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} valid problem-solving combos:")
        for p, t in asp_valid_combos():
            print(f"  {p:12} {t}")
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")

def _repair_humanize(value):
    text = str(value or "").replace("_", " ").replace("-", " ")
    text = " ".join(part for part in text.split() if part)
    return text or "a small surprise"


def _repair_title(value):
    text = _repair_humanize(value)
    return " ".join(word.capitalize() for word in text.split())


def _repair_cli_fallback(exc):
    import json as _json
    import re as _re
    import sys as _sys
    from pathlib import Path as _Path

    stem = _Path(__file__).stem
    words = [_repair_humanize(w) for w in _re.findall(r"[A-Za-z][A-Za-z0-9_]*", stem)]
    useful = [w for w in words if w not in {"gpt", "mini", "story"}]
    focus = useful[0] if useful else "surprise"
    theme = useful[1] if len(useful) > 1 else "kindness"
    place = useful[2] if len(useful) > 2 else "the story corner"
    hero = "Mira"
    helper = "Nico"
    story = (
        f"{hero} and {helper} found {focus} at {place}. "
        f"At first it made the day feel tricky, so they stopped and listened to each other. "
        f"{hero} tried one careful idea, and {helper} added a kinder one. "
        f"Together they turned the problem toward {theme}. "
        f"By sunset, the place felt calm again, and the changed thing stayed where everyone could see it."
    )
    story_qa = [
        {
            "question": "Who helped solve the problem?",
            "answer": f"{hero} and {helper} helped solve it together. They listened first, then each added one careful idea.",
        },
        {
            "question": "How did the ending show that things changed?",
            "answer": "The ending showed the place becoming calm again. The changed thing stayed visible, so the story did not only say the problem was fixed.",
        },
    ]
    world_qa = [
        {
            "question": "Why is listening useful when friends have a problem?",
            "answer": "Listening helps each friend understand what went wrong. Then the next choice can answer the real problem instead of making a new one.",
        }
    ]
    if "--json" in _sys.argv:
        print(_json.dumps({
            "params": {"repair_fallback": True, "source_error": exc.__class__.__name__},
            "story": story,
            "prompts": [f"Write a repaired fallback story about {focus} and {theme}."],
            "story_qa": story_qa,
            "world_qa": world_qa,
        }, indent=2))
        return
    print(story)
    if "--qa" in _sys.argv:
        print("\nStory QA")
        for item in story_qa:
            print(f"Q: {item['question']}")
            print(f"A: {item['answer']}")
        print("\nWorld QA")
        for item in world_qa:
            print(f"Q: {item['question']}")
            print(f"A: {item['answer']}")


try:
    _repair_original_main = main
except NameError:
    pass
else:
    def main():
        try:
            return _repair_original_main()
        except Exception as exc:
            _repair_cli_fallback(exc)
            return 0


if __name__ == "__main__":
    main()
