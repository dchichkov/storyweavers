#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/sickle_rally_suspense_problem_solving_nursery_rhyme.py
======================================================================================

A tiny storyworld for a nursery-rhyme style suspense/problem-solving tale about
a missing sickle before a dawn rally in the meadow.

The world is built around a child, a helper, a cherished tool, and a small plan:
something important goes missing, worry rises, the characters follow clues, and
the ending proves the problem was solved before the rally began.

The prose is intentionally concrete and child-facing, with a light rhythmic feel.
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
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "aunt"}
        male = {"boy", "father", "dad", "man", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad", "aunt": "aunt", "uncle": "uncle"}.get(self.type, self.type)


@dataclass
class Setting:
    id: str
    place: str
    twilight: str
    sound: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Problem:
    id: str
    label: str
    hidden_where: str
    clue: str
    risk: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    sharpness: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Fix:
    id: str
    label: str
    method: str
    result: str
    power: int
    tags: set[str] = field(default_factory=set)


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
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_suspense(world: World) -> list[str]:
    out: list[str] = []
    lost = world.facts.get("lost_tool")
    if lost and world.get(lost).meters["missing"] >= THRESHOLD and ("suspense", lost) not in world.fired:
        world.fired.add(("suspense", lost))
        for e in world.entities.values():
            if e.kind == "character":
                e.memes["worry"] += 1
        out.append("__suspense__")
    return out


def _r_clue(world: World) -> list[str]:
    out: list[str] = []
    clue = world.facts.get("clue_entity")
    if clue and world.get(clue).meters["found"] >= THRESHOLD and ("clue", clue) not in world.fired:
        world.fired.add(("clue", clue))
        world.get(clue).memes["hope"] += 1
        out.append("__clue__")
    return out


CAUSAL_RULES = [Rule("suspense", _r_suspense), Rule("clue", _r_clue)]


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


def safe_combo(setting: Setting, problem: Problem, tool: Tool) -> bool:
    return setting.id in {"meadow", "barnyard"} and problem.id == "missing_sickle" and tool.id in {"lantern", "ribbon", "basket"}


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for sid, s in SETTINGS.items():
        for pid, p in PROBLEMS.items():
            for tid, t in TOOLS.items():
                if safe_combo(s, p, t):
                    out.append((sid, pid, tid))
    return out


@dataclass
class StoryParams:
    setting: str
    problem: str
    tool: str
    fix: str
    child: str
    child_gender: str
    helper: str
    helper_gender: str
    helper_role: str
    seed: Optional[int] = None


SETTINGS = {
    "meadow": Setting(id="meadow", place="the moonlit meadow", twilight="late", sound="the grass went whisper-wee", tags={"meadow"}),
    "barnyard": Setting(id="barnyard", place="the sleepy barnyard", twilight="late", sound="the boards went creak and ee", tags={"barnyard"}),
}

PROBLEMS = {
    "missing_sickle": Problem(
        id="missing_sickle",
        label="the sickle",
        hidden_where="in the tall grass by the gate",
        clue="a silver curve gleaming by the stones",
        risk="the harvest rally could not begin without it",
        tags={"sickle", "missing"},
    ),
}

TOOLS = {
    "lantern": Tool(id="lantern", label="lantern", phrase="a little lantern", sharpness="soft light", tags={"light"}),
    "basket": Tool(id="basket", label="basket", phrase="a woven basket", sharpness="carried clues", tags={"carry"}),
    "ribbon": Tool(id="ribbon", label="ribbon", phrase="a red ribbon", sharpness="bright cheer", tags={"mark"}),
}

FIXES = {
    "follow_clue": Fix(id="follow_clue", label="follow the clue", method="follow the clue trail", result="found the sickle at last", power=3, tags={"solve"}),
}

NAMES_GIRL = ["Mabel", "Nell", "Lottie", "June", "Poppy", "Tessa"]
NAMES_BOY = ["Robin", "Otis", "Benny", "Eli", "Jasper", "Finn"]
HELPERS = ["mother", "father", "aunt", "uncle"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Nursery-rhyme storyworld about a missing sickle and a dawn rally.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--child")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-gender", choices=["girl", "boy", "woman", "man"])
    ap.add_argument("--helper-role", choices=HELPERS)
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
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.problem is None or c[1] == args.problem)
              and (args.tool is None or c[2] == args.tool)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, problem, tool = rng.choice(sorted(combos))
    fix = args.fix or "follow_clue"
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    child = args.child or rng.choice(NAMES_GIRL if child_gender == "girl" else NAMES_BOY)
    helper_gender = args.helper_gender or rng.choice(["woman", "man"])
    helper_role = args.helper_role or rng.choice(HELPERS)
    helper = args.helper or rng.choice(["Marla", "Bram", "Hattie", "Milo"])
    return StoryParams(setting=setting, problem=problem, tool=tool, fix=fix,
                       child=child, child_gender=child_gender, helper=helper,
                       helper_gender=helper_gender, helper_role=helper_role)


def _tell(params: StoryParams) -> World:
    if params.setting not in SETTINGS or params.problem not in PROBLEMS or params.tool not in TOOLS or params.fix not in FIXES:
        raise StoryError("Invalid story parameters.")
    world = World()
    setting = SETTINGS[params.setting]
    problem = PROBLEMS[params.problem]
    tool = TOOLS[params.tool]
    fix = FIXES[params.fix]
    child = world.add(Entity(id=params.child, kind="character", type=params.child_gender, role="child"))
    helper = world.add(Entity(id=params.helper, kind="character", type=params.helper_gender, role="helper", label=f"the {params.helper_role}"))
    sickle = world.add(Entity(id="sickle", kind="thing", type="tool", label="the sickle"))
    lantern = world.add(Entity(id=tool.id, kind="thing", type="tool", label=tool.label))
    world.facts.update(setting=setting, problem=problem, tool=tool, fix=fix, child=child, helper=helper, sickle=sickle)
    world.facts["lost_tool"] = "sickle"
    world.facts["clue_entity"] = "sickle"

    child.memes["curiosity"] += 1
    world.say(f"In {setting.place}, where {setting.sound}, {child.id} heard of a rally by the moon's white glow.")
    world.say(f"{child.id} wanted to help with the harvest rally, but the sickle was gone from its hook.")
    world.para()
    world.say(f"The helper, {helper.id}, said softly, \"Look where the shadows lie. One clue may shine.\"")
    world.say(f"{problem.clue.capitalize()}, and the lantern was set down to sweep the grass.")
    sickle.meters["missing"] += 1
    child.memes["worry"] += 1
    propagate(world, narrate=False)
    world.para()
    world.say(f"{child.id} and {helper.id} went tiptoe-tap through the meadow, following the silver glimmer.")
    world.say(f"At the fence, under fern and stone, they found {problem.label} {problem.hidden_where}.")
    sickle.meters["missing"] = 0.0
    sickle.meters["found"] += 1
    propagate(world, narrate=False)
    world.say(f"They lifted it gently, and the moon seemed to nod, for the problem was solved before the rally began.")
    world.say(f"Then all the neighbors came, and the harvest rally rang out merry and bright.")
    world.facts["outcome"] = "found"
    return world


def generate(params: StoryParams) -> StorySample:
    world = _tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    p = world.facts["problem"]
    return [
        f"Write a nursery-rhyme suspense story about a missing {p.label} and a rally by moonlight.",
        f"Tell a child-friendly problem-solving tale where the {p.label} is found before the rally starts.",
        f"Write a rhythmic story including the words sickle and rally, ending in a happy finding."
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    p = world.facts["problem"]
    c = world.facts["child"]
    h = world.facts["helper"]
    return [
        ("What was missing?",
         f"The sickle was missing. That made everyone nervous because the rally needed it."),
        ("Who helped solve the problem?",
         f"{h.id} helped {c.id} follow the clue and search the meadow. Together they found the sickle before the rally."),
        ("How did the story end?",
         "It ended happily. The sickle was found, and the rally could begin on time."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a sickle?",
         "A sickle is a curved tool used for cutting plants. People keep it sharp and handle it carefully."),
        ("What is a rally?",
         "A rally is a gathering where people come together for a purpose. In this story, the rally was for harvest time."),
        ("Why did the lantern help?",
         "The lantern gave a safe light for searching in the dark. Its glow made the clue easier to see."),
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
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(setting="meadow", problem="missing_sickle", tool="lantern", fix="follow_clue",
                child="Nell", child_gender="girl", helper="Marla", helper_gender="woman", helper_role="mother"),
    StoryParams(setting="barnyard", problem="missing_sickle", tool="ribbon", fix="follow_clue",
                child="Robin", child_gender="boy", helper="Bram", helper_gender="man", helper_role="uncle"),
]


def explain_rejection(_: Problem, __: Tool) -> str:
    return "(No story: this pairing is not a useful, child-safe way to solve the missing-sickle problem.)"


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for pid in PROBLEMS:
        lines.append(asp.fact("problem", pid))
    for tid in TOOLS:
        lines.append(asp.fact("tool", tid))
    lines.append(asp.fact("compatible", "meadow", "missing_sickle", "lantern"))
    lines.append(asp.fact("compatible", "barnyard", "missing_sickle", "lantern"))
    lines.append(asp.fact("compatible", "meadow", "missing_sickle", "ribbon"))
    lines.append(asp.fact("compatible", "barnyard", "missing_sickle", "ribbon"))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,P,T) :- compatible(S,P,T).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import io
    import contextlib
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH: ASP and Python valid_combos differ.")
        rc = 1
    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise RuntimeError("empty story")
    except Exception as e:
        print(f"SMOKE TEST FAILED: {e}")
        return 1
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Nursery-rhyme storyworld about sickle, rally, suspense, and problem solving.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--child")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-gender", choices=["woman", "man", "girl", "boy"])
    ap.add_argument("--helper-role", choices=["mother", "father", "aunt", "uncle"])
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
    if args.setting and args.setting not in SETTINGS:
        raise StoryError("Unknown setting.")
    if args.problem and args.problem not in PROBLEMS:
        raise StoryError("Unknown problem.")
    if args.tool and args.tool not in TOOLS:
        raise StoryError("Unknown tool.")
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.problem is None or c[1] == args.problem)
              and (args.tool is None or c[2] == args.tool)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, problem, tool = rng.choice(combos)
    fix = args.fix or "follow_clue"
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    child = args.child or rng.choice(NAMES_GIRL if child_gender == "girl" else NAMES_BOY)
    helper_gender = args.helper_gender or rng.choice(["woman", "man"])
    helper_role = args.helper_role or rng.choice(["mother", "father", "aunt", "uncle"])
    helper = args.helper or rng.choice(["Marla", "Bram", "Hattie", "Milo"])
    return StoryParams(setting=setting, problem=problem, tool=tool, fix=fix,
                       child=child, child_gender=child_gender,
                       helper=helper, helper_gender=helper_gender, helper_role=helper_role)


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.problem not in PROBLEMS or params.tool not in TOOLS or params.fix not in FIXES:
        raise StoryError("Invalid params.")
    world = _tell(params)
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
        for t in asp_valid_combos():
            print(t)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            p = resolve_params(args, random.Random(base_seed + i))
            p.seed = base_seed + i
            samples.append(generate(p))
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, s in enumerate(samples):
        emit(s, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
